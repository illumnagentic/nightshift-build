"""TfL commute batches, polled through GET /api/prefs against `pywrangler dev` in test mode.

TfL is the fake in fake_upstream.py, chosen by the outward code of the commute postcode.
Each test uses a fresh random inward code, so the commute cache never carries over between runs.
"""
import math
import secrets
import sqlite3
import string
from datetime import datetime, timezone
import sys
from pathlib import Path

import pytest

from conftest import call
from fake_upstream import GOOD, TIGHT

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import filters  # noqa: E402
import tfl  # noqa: E402

# No test here may PUT /api/prefs before the fake fixture's probe has passed.
pytestmark = pytest.mark.usefixtures("fake")

LISTINGS_DB = Path(__file__).resolve().parents[2] / "dataset" / "listings.sqlite"
PREFS_KEYS = {"text", "commute_postcode", "max_commute_min", "parsed", "commute_status"}


def pool_size(parsed) -> int:
    """Listings with coordinates that pass the other hard filters, worked out straight from the dump."""
    hard = {**parsed["hard"], "max_commute_min": None}
    conn = sqlite3.connect(f"file:{LISTINGS_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("SELECT * FROM listings WHERE lat IS NOT NULL AND lon IS NOT NULL").fetchall()
    finally:
        conn.close()
    return sum(1 for r in rows if filters.passes(r, hard, None))


def fresh_postcode(outward: str) -> str:
    return f"{outward} {secrets.randbelow(10)}{''.join(secrets.choice(string.ascii_uppercase) for _ in range(2))}"


def new_user() -> str:
    status, created = call("POST", "/api/users", body={"username": "t_" + secrets.token_hex(6)})
    assert status == 201
    return created["user_id"]


def save(user, postcode, text="a flat"):
    status, saved = call("PUT", "/api/prefs", user_id=user, body={"text": text, "commute_postcode": postcode})
    assert status == 200 and saved["commute_status"] == "pending"
    return saved


def poll(user, limit=30) -> list[str]:
    """Statuses from GET /api/prefs until one is ready or failed."""
    seen = []
    for _ in range(limit):
        status, body = call("GET", "/api/prefs", user_id=user)
        assert status == 200 and set(body) == PREFS_KEYS
        seen.append(body["commute_status"])
        if seen[-1] != "pending":
            return seen
    pytest.fail(f"Still pending after {limit} polls: {seen}")


def tfl_calls(fake, postcode) -> int:
    return sum(1 for p in fake.tfl_requests if f"/to/{postcode.replace(' ', '')}?" in p)


def test_pending_then_ready_after_several_polls(fake):
    postcode, user = fresh_postcode("WC2"), new_user()
    save(user, postcode)
    pool = pool_size(GOOD)
    assert pool > tfl.BATCH_SIZE
    assert poll(user) == ["pending"] * (math.ceil(pool / tfl.BATCH_SIZE) - 1) + ["ready"]
    assert tfl_calls(fake, postcode) == pool  # only listings passing the other filters, each once
    sent = next(p for p in fake.tfl_requests if f"/to/{postcode.replace(' ', '')}?" in p)
    assert sent.endswith("&time=0830&timeIs=Arriving")
    on = datetime.strptime(sent.split("date=")[1][:8], "%Y%m%d").date()
    assert on.weekday() == 1 and 0 < (on - datetime.now(timezone.utc).date()).days <= 8  # a coming Tuesday
    assert call("GET", "/api/prefs", user_id=user)[1]["commute_status"] == "ready"
    assert tfl_calls(fake, postcode) == pool


def test_second_user_with_same_postcode_makes_no_tfl_calls(fake):
    postcode, first, second = fresh_postcode("WC2"), new_user(), new_user()
    save(first, postcode, "[[tight]]")
    assert poll(first) == ["ready"]
    calls = tfl_calls(fake, postcode)
    assert calls == pool_size(TIGHT) < tfl.BATCH_SIZE
    save(second, postcode, "[[tight]]")
    assert poll(second) == ["ready"]
    assert tfl_calls(fake, postcode) == calls


def test_no_journey_is_cached_and_status_is_ready(fake):
    postcode, first, second = fresh_postcode("E1"), new_user(), new_user()
    save(first, postcode, "[[tight]]")
    assert poll(first) == ["ready"]
    calls = tfl_calls(fake, postcode)
    assert calls == pool_size(TIGHT)
    # A cached "no journey" is an answer: the next user does not ask TfL again.
    save(second, postcode, "[[tight]]")
    assert poll(second) == ["ready"]
    assert tfl_calls(fake, postcode) == calls


@pytest.mark.parametrize("outward", ["SE1", "SW1"])
def test_transient_errors_are_not_cached_and_are_retried(fake, outward):
    postcode, user = fresh_postcode(outward), new_user()
    save(user, postcode, "[[tight]]")
    seen = poll(user)
    assert seen[0] == "pending" and seen[-1] == "ready"
    assert "failed" not in seen
    # Every listing got an answer, and at least one was asked twice: the error was not cached.
    assert tfl_calls(fake, postcode) > pool_size(TIGHT)


def test_persistent_failure_ends_failed_after_three_polls(fake):
    postcode, user = fresh_postcode("N1"), new_user()
    save(user, postcode, "[[tight]]")
    assert poll(user) == ["pending", "pending", "failed"]
    calls = tfl_calls(fake, postcode)
    assert calls > 0
    # Failed is final until the user saves again: no more TfL calls.
    assert call("GET", "/api/prefs", user_id=user)[1]["commute_status"] == "failed"
    assert tfl_calls(fake, postcode) == calls
    save(user, fresh_postcode("WC2"), "[[tight]]")
    assert poll(user) == ["ready"]


def test_classify_answers():
    assert tfl.classify(200, '{"journeys": [{"duration": 41}, {"duration": 33}, {"duration": 50}]}') == ("ok", 33)
    assert tfl.classify(404, "{}") == ("no_journey", None)
    assert tfl.classify(200, '{"journeys": []}') == ("no_journey", None)
    assert tfl.classify(200, '{}') == ("no_journey", None)
    for status in (400, 429, 500, 503, 300):
        assert tfl.classify(status, "{}") == ("transient", None)
    assert tfl.classify(200, "<html>") == ("transient", None)
    assert tfl.classify(200, "[1]") == ("transient", None)
    assert tfl.classify(200, '{"journeys": [{"duration": "x"}]}') == ("transient", None)
    assert tfl.classify(200, '{"toLocationDisambiguation": {"matchStatus": "list"}}') == ("transient", None)


def test_url_and_next_tuesday():
    from datetime import date
    assert tfl.next_tuesday(date(2026, 10, 24)) == date(2026, 10, 27)  # Saturday
    assert tfl.next_tuesday(date(2026, 10, 27)) == date(2026, 11, 3)  # a Tuesday gives the following one
    assert tfl.next_tuesday(date(2026, 10, 26)) == date(2026, 10, 27)
    assert tfl.build_url("http://x", 51.5, -0.1, "EC2N 2DB", date(2026, 10, 27)) == (
        "http://x/Journey/JourneyResults/51.5,-0.1/to/EC2N2DB?date=20261027&time=0830&timeIs=Arriving")


def test_rate_limit_alone_never_fails_the_commute(fake):
    # W1 answers 429 to every request. Five polls is more than the fail streak allows.
    postcode, user = fresh_postcode("W1"), new_user()
    save(user, postcode, "[[tight]]")
    seen = []
    for _ in range(tfl.FAIL_STREAK_LIMIT + 2):
        status, body = call("GET", "/api/prefs", user_id=user)
        seen.append(body["commute_status"])
    assert seen == ["pending"] * (tfl.FAIL_STREAK_LIMIT + 2)
