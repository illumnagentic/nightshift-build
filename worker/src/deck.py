"""GET /deck: score the filtered pool with the curator once per buyer, then serve cards from the cached scores."""
import asyncio
import json
import logging
import math
import random
import secrets
from datetime import datetime, timezone

import chips
import curator
import filters
import mubit

EXPLORATION_SHARE = 0.2
BAND = (0.5, 0.8)  # exploration cards come from this percentile band of the scored pool, best first
ONBOARDING_SWIPES = 15
COMMUTE_ASSUMPTIONS = "weekday, arrive 08:30, public transport"
PROFILE_VERSION = 0

# The filter columns plus what the card and the chips read. No description: it is never sent anywhere.
LISTING_COLUMNS = (f"{filters.FILTER_COLUMNS}, price_qualifier, bathrooms, address, postcode, lat, lon, service_charge_gbp_pa,"
                   " council_tax_band, floor_level, key_features")


class CuratorFailed(Exception):
    """The pool has listings but the curator scored none of them."""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


async def rows_for(db, sql: str, ids: list[str], *params) -> list:
    """Rows of `sql`, which must hold one `IN (SELECT value FROM json_each(?))` placeholder, last, for `ids`."""
    return (await db.prepare(sql).bind(*params, json.dumps(ids)).all()).results


def group_by_listing(rows) -> dict[str, list]:
    grouped: dict[str, list] = {}
    for row in rows:
        grouped.setdefault(row["listing_id"], []).append(row)
    return grouped


async def score_unscored(env, user_id: str, stated: dict, listings: list[dict], commutes) -> None:
    """Score `listings` in concurrent chunks and store the good answers. A bad chunk is logged and left unscored."""
    ids = [r["id"] for r in listings]
    stations = group_by_listing(await rows_for(
        env.DB, "SELECT listing_id, name, distance_km FROM listing_stations WHERE listing_id IN (SELECT value FROM json_each(?))"
        " ORDER BY listing_id, position", ids))
    flags = group_by_listing(await rows_for(
        env.DB, "SELECT listing_id, field, value, room, confidence, observation, corrected_text FROM photo_flags"
        " WHERE listing_id IN (SELECT value FROM json_each(?)) ORDER BY flag_id", ids))
    compact = {r["id"]: curator.compact_listing(r, stations.get(r["id"], []), flags.get(r["id"], []),
                                                commutes.get(r["id"]) if commutes is not None else None) for r in listings}
    profile = {"version": PROFILE_VERSION, "factors": []}
    base = getattr(env, "GEMINI_BASE", None) or mubit.GEMINI_BASE
    chunks = [ids[i:i + curator.CHUNK_SIZE] for i in range(0, len(ids), curator.CHUNK_SIZE)]
    results = await asyncio.gather(*(
        mubit.generate_content(env.MUBIT_API_KEY, curator.MODEL, curator.build_score_body(stated, profile, [compact[i] for i in chunk]), base)
        for chunk in chunks), return_exceptions=True)
    for chunk, result in zip(chunks, results):
        if isinstance(result, BaseException):
            logging.warning("Curator chunk failed, request_id=%s: %s: %s", getattr(result, "request_id", None), type(result).__name__, result)
            continue
        scores = curator.parse_reply(result.data, chunk)
        if scores is None:
            logging.warning("Curator reply unusable, request_id=%s", result.request_id)
            continue
        await env.DB.prepare(
            "INSERT OR IGNORE INTO curator_scores (user_id, listing_id, profile_version, score, reason, request_id, scored_at)"
            " SELECT ?, json_extract(value, '$[0]'), ?, json_extract(value, '$[1]'), json_extract(value, '$[2]'), ?, ?"
            " FROM json_each(?)"
        ).bind(user_id, PROFILE_VERSION, result.request_id, now(),
               json.dumps([[lid, score, reason] for lid, (score, reason) in scores.items()])).run()


def pick_new(order: list[str], unavailable: set[str], k: int, user_id: str, count: int) -> list[tuple[str, str]]:
    """(listing_id, source) for up to `count` new cards. `order` is the scored pool, best first; k counts decisions ever made."""
    lo, hi = (math.floor(share * len(order)) for share in BAND)
    band = set(order[lo:hi])
    picked = []
    while len(picked) < count:
        eligible = [i for i in order if i not in unavailable]
        if not eligible:
            break
        rng = random.Random(f"{user_id}:{k}")
        exploration = [i for i in eligible if i in band] if rng.random() < EXPLORATION_SHARE else []
        if exploration:
            picked.append((rng.choice(exploration), "exploration"))
        else:
            picked.append((eligible[0], "ranked"))
        unavailable.add(picked[-1][0])
        k += 1
    return picked


async def get_deck(env, user_id: str, n: int, prefs_row) -> dict:
    """The GET /deck body. Raises CuratorFailed when the pool is non-empty and the curator scored none of it."""
    db = env.DB
    parsed = json.loads(prefs_row["parsed_json"])
    hard, postcode = parsed["hard"], prefs_row["commute_postcode"]
    commutes = await filters.load_commutes(db, postcode) if postcode else None

    train = {r["id"]: r for r in (await db.prepare(f"SELECT {LISTING_COLUMNS} FROM listings WHERE split = 'train' ORDER BY id").all()).results}
    # With no postcode there is no commute to limit on, as in filters.matching_listing_ids.
    pool = [r for r in train.values() if filters.passes(r, hard if commutes is not None else {**hard, "max_commute_min": None},
                                                       commutes.get(r["id"]) if commutes is not None else None)]
    scores = {r["listing_id"]: r for r in (await db.prepare(
        "SELECT listing_id, score, request_id FROM curator_scores WHERE user_id = ? AND profile_version = ?"
    ).bind(user_id, PROFILE_VERSION).all()).results}
    unscored = [r for r in pool if r["id"] not in scores]
    if unscored:
        await score_unscored(env, user_id, {"hard": hard, "soft": parsed["soft"]}, unscored, commutes)
        scores = {r["listing_id"]: r for r in (await db.prepare(
            "SELECT listing_id, score, request_id FROM curator_scores WHERE user_id = ? AND profile_version = ?"
        ).bind(user_id, PROFILE_VERSION).all()).results}
    order = [r["id"] for r in sorted((r for r in pool if r["id"] in scores), key=lambda r: (-scores[r["id"]]["score"], r["id"]))]
    if pool and not order:
        raise CuratorFailed()

    decisions = (await db.prepare(
        "SELECT decision_id, listing_id, source, swiped_at FROM decisions WHERE user_id = ? ORDER BY served_at, rowid"
    ).bind(user_id).all()).results
    served = [d for d in decisions if d["swiped_at"] is None][:n]
    swiped = {d["listing_id"] for d in decisions if d["swiped_at"] is not None}
    swiped_count = len(swiped)  # one swipe per listing, as a listing is never served again once swiped
    unavailable = swiped | {d["listing_id"] for d in decisions if d["swiped_at"] is None}
    new = pick_new(order, unavailable, len(decisions), user_id, n - len(served)) if order else []

    cards = [(d["decision_id"], d["source"], d["listing_id"], False) for d in served]
    cards += [("d_" + secrets.token_hex(8), source, listing_id, True) for listing_id, source in new]
    ids = [c[2] for c in cards]
    stations = group_by_listing(await rows_for(
        db, "SELECT listing_id, name, distance_km FROM listing_stations WHERE listing_id IN (SELECT value FROM json_each(?))"
        " ORDER BY listing_id, position", ids))
    flags = group_by_listing(await rows_for(
        db, "SELECT listing_id, field, value, room, confidence, observation, corrected_text FROM photo_flags"
        " WHERE listing_id IN (SELECT value FROM json_each(?))", ids))
    photos = group_by_listing(await rows_for(
        db, "SELECT listing_id, url FROM listing_media WHERE kind = 'photo' AND listing_id IN (SELECT value FROM json_each(?))"
        " ORDER BY listing_id, position", ids))

    out = []
    for index, (decision_id, source, listing_id, is_new) in enumerate(cards):
        row = train[listing_id]
        minutes = commutes.get(listing_id) if commutes is not None else None
        card_chips = chips.select(row, stations.get(listing_id, []), flags.get(listing_id, []), minutes)
        if is_new:  # a newly served card: log it and the chips offered
            await db.prepare(
                "INSERT INTO decisions (decision_id, user_id, listing_id, source, score, curator_request_id, profile_version, served_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
            ).bind(decision_id, user_id, listing_id, source, scores[listing_id]["score"], scores[listing_id]["request_id"],
                   PROFILE_VERSION, now()).run()
            await db.prepare(
                "INSERT INTO offered_chips (decision_id, chip_id, position) SELECT ?, json_extract(value, '$[0]'), json_extract(value, '$[1]')"
                " FROM json_each(?)"
            ).bind(decision_id, json.dumps([[c["chip_id"], p] for p, c in enumerate(card_chips)])).run()
        out.append({
            "decision_id": decision_id,
            "source": source,
            "feedback_required": swiped_count + index < ONBOARDING_SWIPES,
            "listing": {
                **{k: row[k] for k in ("id", "price_gbp", "price_qualifier", "bedrooms", "bathrooms", "property_type", "address",
                                       "postcode", "lat", "lon", "tenure", "epc_current", "floor_level")},
                "key_features": json.loads(row["key_features"]),
                "photos": [p["url"] for p in photos.get(listing_id, [])],
            },
            "commute": None if not postcode else {"minutes": minutes, "postcode": postcode, "assumptions": COMMUTE_ASSUMPTIONS},
            "chips": card_chips,
        })
    return {"empty_reason": None if out else ("exhausted" if pool else "no_matches"), "cards": out}


async def drop_unswiped(db, user_id: str) -> None:
    """After a prefs re-save: forget served cards not yet swiped, and the scores made under the old prefs."""
    unswiped = "SELECT decision_id FROM decisions WHERE user_id = ? AND swiped_at IS NULL"
    await db.prepare(f"DELETE FROM offered_chips WHERE decision_id IN ({unswiped})").bind(user_id).run()
    await db.prepare("DELETE FROM decisions WHERE user_id = ? AND swiped_at IS NULL").bind(user_id).run()
    await db.prepare("DELETE FROM curator_scores WHERE user_id = ?").bind(user_id).run()
