"""TfL Journey Planner commute times, calculated in small batches and cached per (listing, postcode).

Weekday, arrive 08:30, public transport. TfL needs no key for this volume.
Modes are sent explicitly, because the product promises public transport and the Journey Planner documents no
default: the ids below are the public-service modes from /Journey/Meta/Modes plus walking, with no cycle, taxi,
car or coach.
"""
import asyncio
import json
import logging
import time
from datetime import date, datetime, timedelta, timezone

import filters

TFL_BASE = "https://api.tfl.gov.uk"
BATCH_SIZE = 12
CONCURRENCY = 6
BUDGET_SECONDS = 5.0
FAIL_STREAK_LIMIT = 3
MODES = "bus,cable-car,dlr,elizabeth-line,national-rail,overground,replacement-bus,river-bus,tram,tube,walking"


def next_tuesday(today: date) -> date:
    """The first Tuesday after `today`."""
    return today + timedelta(days=(1 - today.weekday()) % 7 or 7)


def london_today() -> date:
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Europe/London")).date()
    except Exception:
        # No tz database in this runtime: UTC is at most an hour off, which never moves a Tuesday.
        return datetime.now(timezone.utc).date()


def build_url(base: str, lat: float, lon: float, postcode: str, on: date) -> str:
    """Journey from a listing's coordinates to a normalised postcode, arriving 08:30 on `on`."""
    return (f"{base}/Journey/JourneyResults/{lat},{lon}/to/{postcode.replace(' ', '')}"
            f"?date={on:%Y%m%d}&time=0830&timeIs=Arriving&mode={MODES}")


def classify(status: int, body: str) -> tuple[str, int | None]:
    """('ok', minutes) | ('no_journey', None) | ('transient', None) for a TfL answer."""
    if status == 404:
        return "no_journey", None
    if status != 200:
        return "transient", None
    try:
        data = json.loads(body)
    except ValueError:
        return "transient", None
    if not isinstance(data, dict):
        return "transient", None
    journeys = data.get("journeys")
    if not journeys:
        # A 200 that offers place candidates instead of journeys is a disambiguation, not an answer.
        return ("transient", None) if data.get("toLocationDisambiguation") or data.get("fromLocationDisambiguation") else ("no_journey", None)
    durations = [j.get("duration") for j in journeys if isinstance(j, dict)]
    durations = [d for d in durations if isinstance(d, int) and not isinstance(d, bool) and d >= 0]
    return ("ok", min(durations)) if durations else ("transient", None)


async def fetch_journey(base: str, lat: float, lon: float, postcode: str, on: date) -> tuple[str, int | None, int | None]:
    """(kind, minutes, http status). A network error or timeout is transient with status None."""
    from workers import fetch  # only exists inside the Workers runtime

    try:
        response = await asyncio.wait_for(fetch(build_url(base, lat, lon, postcode, on)), BUDGET_SECONDS)
        status = response.status
        kind, minutes = classify(status, await response.text())
    except Exception as exc:
        logging.warning("TfL call failed: %s: %s", type(exc).__name__, exc)
        return "transient", None, None
    logging.debug("TfL status=%s ratelimit=%s", status, {k: v for k, v in ((h, response.headers.get(h)) for h in ("x-rate-limit-limit", "x-rate-limit-remaining", "retry-after")) if v})
    return kind, minutes, status


async def missing_listings(db, hard: dict, postcode: str) -> list[tuple[str, float, float]]:
    """(id, lat, lon) of listings passing the other hard filters that have coordinates and no cache row."""
    ids = set(await filters.matching_listing_ids(db, hard))
    placed = (await db.prepare("SELECT id, lat, lon FROM listings WHERE lat IS NOT NULL AND lon IS NOT NULL ORDER BY id").all()).results
    cached = {r["listing_id"] for r in (await db.prepare("SELECT listing_id FROM commute_cache WHERE postcode = ?").bind(postcode).all()).results}
    return [(r["id"], r["lat"], r["lon"]) for r in placed if r["id"] in ids and r["id"] not in cached]


async def run_batch(db, base: str, hard: dict, postcode: str, streak: int) -> tuple[str, int]:
    """One bounded batch for a pending commute. Returns the new (commute_status, fail streak).

    After a fully failed, non-rate-limited batch at the streak limit, a postcode with cached rows gets one control call
    for an already-cached listing: TfL still failing means an outage (failed); TfL answering means the failing listings
    are unroutable (ready once all have been tried)."""
    todo = await missing_listings(db, hard, postcode)
    if not todo:
        return "ready", 0
    on = next_tuesday(london_today())
    semaphore = asyncio.Semaphore(CONCURRENCY)
    deadline = time.monotonic() + BUDGET_SECONDS
    rate_limited = False
    cached = 0

    async def one(listing_id, lat, lon):
        nonlocal rate_limited, cached
        async with semaphore:
            if rate_limited or time.monotonic() > deadline:
                return
            kind, minutes, status = await fetch_journey(base, lat, lon, postcode, on)
            rate_limited = rate_limited or status == 429
            if kind == "transient":
                return
            await db.prepare(
                "INSERT OR REPLACE INTO commute_cache (listing_id, postcode, minutes, fetched_at) VALUES (?, ?, ?, ?)"
            ).bind(listing_id, postcode, minutes, datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")).run()
            cached += 1

    # After a batch with no answers, start further along, so listings TfL keeps failing at the head of the order cannot stall the rest.
    start = (streak * BATCH_SIZE) % len(todo)
    batch = (todo[start:] + todo[:start])[:BATCH_SIZE]
    await asyncio.gather(*(one(*item) for item in batch))
    if cached == len(todo):
        return "ready", 0
    if cached:
        return "pending", 0
    if rate_limited:
        # Anonymous TfL answers 429 with Retry-After after a burst. That is the pace of the quota, not a bad postcode.
        return "pending", streak
    streak += 1
    if streak < FAIL_STREAK_LIMIT:
        return "pending", streak
    # Every listing in this batch failed, FAIL_STREAK_LIMIT batches running. A cached row alone does not show TfL is up
    # (an outage after progress looks the same), so ask TfL once more about a listing it has already answered.
    row = (await db.prepare(
        "SELECT c.listing_id, l.lat, l.lon FROM commute_cache c JOIN listings l ON l.id = c.listing_id "
        "WHERE c.postcode = ? ORDER BY c.minutes IS NULL, c.listing_id LIMIT 1"
    ).bind(postcode).all()).results
    if not row:
        return "failed", streak
    kind, _, status = await fetch_journey(base, row[0]["lat"], row[0]["lon"], postcode, on)  # not written to the cache
    if status == 429:
        return "pending", streak
    if kind == "transient":
        return "failed", streak
    # TfL answers again, so these listings are ones it cannot route. Ready only once every listing still uncached has
    # been in a failing batch; until then the rotation goes on.
    return ("ready", 0) if streak * BATCH_SIZE >= len(todo) else ("pending", streak)
