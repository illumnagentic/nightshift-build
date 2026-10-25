"""GET /deck: serve unswiped cards first, then new ones ranked by one curator call over a seeded sample of the pool."""
import asyncio
import json
import logging
import random
import secrets
from datetime import datetime, timezone

import chips
import curator
import filters
import mubit

SAMPLE_SIZE = 30
EXPLORE_EVERY = 5  # the 5th, 10th, ... card a user is served is an exploration card
BAND = (0.5, 0.8)  # exploration cards come from this share of the curator's ranking, by rank / length
ONBOARDING_CARDS = 15
CURATOR_TIMEOUT_SECONDS = 60
EMPTY_PROFILE_VERSION = 0  # no taste profile exists yet, so the request carries {} and no feedback
COMMUTE_ASSUMPTIONS = "weekday, arrive 08:30, public transport"

LISTING_COLUMNS = ("id", "price_gbp", "price_qualifier", "bedrooms", "bathrooms", "property_type", "address", "postcode",
                   "lat", "lon", "tenure", "lease_years_remaining", "service_charge_gbp_pa", "epc_current", "floor_level")
CARD_LISTING_KEYS = LISTING_COLUMNS[:11] + LISTING_COLUMNS[13:] + ("key_features", "photos")


class PrefsMissing(Exception):
    pass


class CuratorFailed(Exception):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


async def _all(db, sql, *args):
    statement = db.prepare(sql)
    return (await (statement.bind(*args) if args else statement).all()).results


def _marks(values) -> str:
    return ",".join("?" * len(values))


async def _load_listings(db, ids):
    """Listing id to listing dict: the card columns, key_features as a list, stations as mappings, photos in order."""
    listings = {}
    for row in await _all(db, f"SELECT {', '.join(LISTING_COLUMNS)}, key_features FROM listings WHERE id IN ({_marks(ids)})", *ids):
        listing = {c: row[c] for c in LISTING_COLUMNS}
        listing.update(key_features=json.loads(row["key_features"]), stations=[], photos=[])
        listings[row["id"]] = listing
    for row in await _all(db, f"SELECT listing_id, name, distance_km, types FROM listing_stations WHERE listing_id IN ({_marks(ids)}) ORDER BY listing_id, position", *ids):
        listings[row["listing_id"]]["stations"].append(
            {"name": row["name"], "distance_km": row["distance_km"], "types": json.loads(row["types"])})
    for row in await _all(db, f"SELECT listing_id, url FROM listing_media WHERE kind = 'photo' AND listing_id IN ({_marks(ids)}) ORDER BY listing_id, position", *ids):
        listings[row["listing_id"]]["photos"].append(row["url"])
    return listings


async def _load_flags(db, ids):
    flags = {}
    for row in await _all(db, f"SELECT listing_id, field, value, confidence, room, corrected_text FROM photo_flags WHERE listing_id IN ({_marks(ids)}) ORDER BY rowid", *ids):
        flags.setdefault(row["listing_id"], []).append(row)
    return flags


def place(ranking, first_slot, need, user_id):
    """(listing id, source, 1-based rank) for up to `need` new cards. A slot whose number is 4 modulo 5 takes a
    seeded pick from the band; if the band is empty or used up, or the slot is any other, it takes the best unused rank."""
    total = len(ranking)
    unused = list(range(1, total + 1))
    picks = []
    for i in range(min(need, total)):
        slot = first_slot + i
        band = [r for r in unused if BAND[0] <= r / total <= BAND[1]]
        if slot % EXPLORE_EVERY == EXPLORE_EVERY - 1 and band:
            rank, source = random.Random(f"{user_id}:{slot}").choice(band), "exploration"
        else:
            rank, source = unused[0], "ranked"
        unused.remove(rank)
        picks.append((ranking[rank - 1], source, rank))
    return picks


async def _outstanding(db, user_id, n):
    return await _all(db, "SELECT * FROM decisions WHERE user_id = ? AND swiped_at IS NULL ORDER BY served_at, position LIMIT ?", user_id, n)


async def _ask_curator(env, user_id, prefs, parsed, sample, listings, flags, commutes):
    """One curator call over `sample`, recorded whatever happens. Returns (call_id, ranking); raises CuratorFailed."""
    db = env.DB
    body = curator.build_body({"text": prefs["text"], "soft": parsed["soft"]}, {}, [],
                              [curator.candidate_summary(listings[i], flags.get(i, []), commutes.get(i)) for i in sample])
    request_id, ranking, status, usage, error = None, None, "failed", None, None
    try:
        result = await asyncio.wait_for(mubit.generate_content(
            env.MUBIT_API_KEY, curator.MODEL, body, getattr(env, "GEMINI_BASE", None) or mubit.GEMINI_BASE), CURATOR_TIMEOUT_SECONDS)
        request_id = result.request_id
        ranking, status, usage = curator.parse_ranking(result.data, sample)
    except mubit.MubitError as exc:
        request_id, error = exc.request_id, str(exc)[:300]
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"[:300]
    usage = usage or {}
    call_id = "c_" + secrets.token_hex(8)
    await db.prepare(
        "INSERT INTO curator_calls (call_id, user_id, created_at, model, profile_version, prefs_updated_at, candidate_ids, ranking,"
        " status, mreq_id, error, prompt_tokens, output_tokens, thought_tokens) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    ).bind(call_id, user_id, _now(), curator.MODEL, EMPTY_PROFILE_VERSION, prefs["updated_at"], json.dumps(sample),
           None if ranking is None else json.dumps(ranking), status, request_id, error,
           usage.get("prompt"), usage.get("candidates"), usage.get("thoughts")).run()
    if ranking is None:
        logging.warning("Curator call failed, call_id=%s request_id=%s: %s", call_id, request_id, error)
        raise CuratorFailed(error)
    return call_id, ranking


async def _serve_new(env, user_id, prefs, parsed, available, need, first_position):
    db = env.DB
    count = (await _all(db, "SELECT COUNT(*) AS n FROM curator_calls WHERE user_id = ?", user_id))[0]["n"]
    sample = random.Random(f"{user_id}:{count}").sample(available, min(SAMPLE_SIZE, len(available)))
    listings, flags = await _load_listings(db, sample), await _load_flags(db, sample)
    commutes = await filters.load_commutes(db, prefs["commute_postcode"]) if prefs["commute_postcode"] else {}
    call_id, ranking = await _ask_curator(env, user_id, prefs, parsed, sample, listings, flags, commutes)
    first_slot = (await _all(db, "SELECT COUNT(*) AS n FROM decisions WHERE user_id = ?", user_id))[0]["n"]
    served_at = _now()
    for i, (listing_id, source, rank) in enumerate(place(ranking, first_slot, need, user_id)):
        offered = chips.chip_ids_for(listings[listing_id], flags.get(listing_id, []), commutes.get(listing_id))
        # A concurrent request may have served the same listing: the unique pair wins and this row is skipped.
        await db.prepare(
            "INSERT INTO decisions (decision_id, user_id, listing_id, source, served_at, position, rank, curator_call_id,"
            " profile_version, offered_chips) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT (user_id, listing_id) DO NOTHING"
        ).bind("d_" + secrets.token_hex(8), user_id, listing_id, source, served_at, first_position + i, rank, call_id,
               EMPTY_PROFILE_VERSION, json.dumps(offered)).run()


async def _cards(db, user_id, rows, postcode):
    swiped = (await _all(db, "SELECT COUNT(*) AS n FROM decisions WHERE user_id = ? AND swiped_at IS NOT NULL", user_id))[0]["n"]
    if not rows:
        return []
    ids = [r["listing_id"] for r in rows]
    listings = await _load_listings(db, ids)
    commutes = await filters.load_commutes(db, postcode) if postcode else {}
    return [{
        "decision_id": row["decision_id"],
        "source": row["source"],
        "feedback_required": swiped + position < ONBOARDING_CARDS,
        "listing": {k: listings[row["listing_id"]][k] for k in CARD_LISTING_KEYS},
        "commute": None if not postcode else {
            "minutes": commutes.get(row["listing_id"]), "postcode": postcode, "assumptions": COMMUTE_ASSUMPTIONS},
        "chips": chips.chip_objects(json.loads(row["offered_chips"])),
    } for position, row in enumerate(rows)]


async def serve(env, user_id, n):
    """The GET /deck body. Raises PrefsMissing, or CuratorFailed when there is nothing outstanding to serve instead."""
    db = env.DB
    rows = await _all(db, "SELECT * FROM prefs WHERE user_id = ?", user_id)
    if not rows:
        raise PrefsMissing()
    prefs, empty_reason = rows[0], None
    parsed = json.loads(prefs["parsed_json"])
    outstanding = await _outstanding(db, user_id, n)
    if len(outstanding) < n:
        hard, postcode = parsed["hard"], prefs["commute_postcode"]
        matching = await (filters.matching_listing_ids_for_postcode(db, hard, postcode) if postcode else filters.matching_listing_ids(db, hard))
        train = {r["id"] for r in await _all(db, "SELECT id FROM listings WHERE split = 'train'")}
        pool = [i for i in matching if i in train]
        used = {r["listing_id"] for r in await _all(db, "SELECT listing_id FROM decisions WHERE user_id = ?", user_id)}
        available = [i for i in pool if i not in used]
        if available:
            try:
                await _serve_new(env, user_id, prefs, parsed, available, n - len(outstanding), len(outstanding))
            except CuratorFailed:
                if not outstanding:
                    raise
            outstanding = await _outstanding(db, user_id, n)
        elif not outstanding:
            empty_reason = "exhausted" if pool else "no_matches"
    return {"empty_reason": empty_reason, "cards": await _cards(db, user_id, outstanding, prefs["commute_postcode"])}
