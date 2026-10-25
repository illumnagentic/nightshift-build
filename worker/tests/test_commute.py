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
import fake_upstream
from fake_upstream import GOOD, TIGHT

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import filters  # noqa: E402
import tfl  # noqa: E402

# No test here may PUT /api/prefs before the fake fixture's probe has passed.
pytestmark = pytest.mark.usefixtures("fake")

LISTINGS_DB = Path(__file__).resolve().parents[2] / "dataset" / "listings.sqlite"
PREFS_KEYS = {"text", "commute_postcode", "max_commute_min", "parsed", "commute_status"}


def pool_rows(parsed) -> list[tuple[str, float, float]]:
    """(id, lat, lon) in id order of listings with coordinates that pass the other hard filters, worked out straight from the dump."""
    hard = {**parsed["hard"], "max_commute_min": None}
    conn = sqlite3.connect(f"file:{LISTINGS_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("SELECT * FROM listings WHERE lat IS NOT NULL AND lon IS NOT NULL").fetchall()
    finally:
        conn.close()
    return sorted((r["id"], r["lat"], r["lon"]) for r in rows if filters.passes(r, hard, None))


def pool_size(parsed) -> int:
    return len(pool_rows(parsed))


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
    assert sent.endswith(f"&time=0830&timeIs=Arriving&mode={tfl.MODES}")
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


def test_rate_limit_alone_never_fails_the_commute(fake):
    # W1 answers 429 to every request. Five polls is more than the fail streak allows.
    postcode, user = fresh_postcode("W1"), new_user()
    save(user, postcode, "[[tight]]")
    seen = []
    for _ in range(tfl.FAIL_STREAK_LIMIT + 2):
        status, body = call("GET", "/api/prefs", user_id=user)
        seen.append(body["commute_status"])
    assert seen == ["pending"] * (tfl.FAIL_STREAK_LIMIT + 2)


@pytest.fixture
def failing_starts():
    fake_upstream.FAILING_STARTS.clear()
    yield fake_upstream.FAILING_STARTS
    fake_upstream.FAILING_STARTS.clear()


@pytest.fixture
def destination_status():
    fake_upstream.DESTINATION_STATUS.clear()
    yield fake_upstream.DESTINATION_STATUS
    fake_upstream.DESTINATION_STATUS.clear()


@pytest.fixture
def start_status():
    fake_upstream.START_STATUS.clear()
    yield fake_upstream.START_STATUS
    fake_upstream.START_STATUS.clear()


def starts_asked(fake, postcode) -> list[tuple[float, float]]:
    """The start coordinates of every TfL call for this postcode, in order."""
    marker = f"/to/{postcode.replace(' ', '')}?"
    return [tuple(float(v) for v in p.split("/JourneyResults/")[1].split("/to/")[0].split(",")) for p in fake.tfl_requests if marker in p]


def check_unknown_listings_left(fake, postcode, bad, polls):
    """Polls ended ready; every pool listing outside `bad` was asked exactly once (so it was cached, as an
    answered listing is never asked again) and the bad ones were asked and never answered."""
    assert polls[-1] == "ready" and "failed" not in polls
    asked = starts_asked(fake, postcode)
    good = [(lat, lon) for _, lat, lon in pool_rows(GOOD) if (lat, lon) not in bad]
    assert sorted(a for a in asked if a not in bad) == sorted(good + [good[0]])
    assert any(a in bad for a in asked)


def test_one_listing_that_always_fails_is_left_unknown(fake, failing_starts):
    rows = pool_rows(GOOD)
    failing_starts.add(rows[len(rows) // 2][1:])
    postcode, user = fresh_postcode("WC2"), new_user()
    save(user, postcode)
    polls = poll(user)
    check_unknown_listings_left(fake, postcode, set(failing_starts), polls)
    assert call("GET", "/api/prefs", user_id=user)[1]["commute_status"] == "ready"


def test_a_head_of_failing_listings_larger_than_a_batch_does_not_stall(fake, failing_starts):
    failing_starts.update(r[1:] for r in pool_rows(GOOD)[: tfl.BATCH_SIZE + 1])
    postcode, user = fresh_postcode("WC2"), new_user()
    save(user, postcode)
    polls = poll(user, limit=60)
    check_unknown_listings_left(fake, postcode, set(failing_starts), polls)


def test_postcode_tfl_cannot_resolve_ends_failed(fake):
    # N7 answers every journey with HTTP 300, which TfL gives for a postcode that does not exist.
    postcode, user = fresh_postcode("N7"), new_user()
    save(user, postcode, "[[tight]]")
    assert poll(user) == ["pending", "pending", "failed"]


def poll_n(user, n) -> list[str]:
    return [call("GET", "/api/prefs", user_id=user)[1]["commute_status"] for _ in range(n)]


def test_outage_after_progress_ends_failed(fake, destination_status):
    postcode, user = fresh_postcode("EC1A"), new_user()
    compact = postcode.replace(" ", "")
    save(user, postcode)
    pool = pool_size(GOOD)
    assert poll_n(user, 1) == ["pending"]
    destination_status[compact] = 500
    assert poll_n(user, 3) == ["pending", "pending", "failed"]
    calls = tfl_calls(fake, postcode)
    assert poll_n(user, 1) == ["failed"]
    assert tfl_calls(fake, postcode) == calls
    destination_status.clear()
    save(user, postcode)
    before = tfl_calls(fake, postcode)
    assert poll(user)[-1] == "ready"
    assert tfl_calls(fake, postcode) - before == pool - tfl.BATCH_SIZE  # cached listings are not asked again


def test_outage_with_a_last_batch_left_ends_failed(fake, destination_status):
    postcode, user = fresh_postcode("EC1A"), new_user()
    save(user, postcode)
    pool = pool_size(GOOD)
    assert poll_n(user, math.ceil(pool / tfl.BATCH_SIZE) - 1) == ["pending"] * (math.ceil(pool / tfl.BATCH_SIZE) - 1)
    destination_status[postcode.replace(" ", "")] = 500
    assert poll_n(user, 3) == ["pending", "pending", "failed"]


def test_rate_limit_after_progress_never_fails_the_commute(fake, destination_status):
    postcode, user = fresh_postcode("EC1A"), new_user()
    save(user, postcode)
    assert poll_n(user, 1) == ["pending"]
    destination_status[postcode.replace(" ", "")] = 429
    assert poll_n(user, tfl.FAIL_STREAK_LIMIT + 2) == ["pending"] * (tfl.FAIL_STREAK_LIMIT + 2)


def test_rate_limited_control_call_never_fails_the_commute(fake, failing_starts, start_status):
    postcode, user = fresh_postcode("EC1A"), new_user()
    save(user, postcode)
    rows = pool_rows(GOOD)
    assert poll_n(user, 1) == ["pending"]
    # Listings are tried in id order, so the first batch cached the first rows; the control call re-asks the lowest id.
    control, uncached = rows[0][1:], {r[1:] for r in rows[tfl.BATCH_SIZE:]}
    assert control not in uncached  # listings sharing coordinates would make the control start fail with the rest
    assert sorted(starts_asked(fake, postcode)[:tfl.BATCH_SIZE]) == sorted(r[1:] for r in rows[:tfl.BATCH_SIZE])
    asked_before = starts_asked(fake, postcode).count(control)
    failing_starts.update(uncached)
    start_status[control] = 429
    assert poll_n(user, tfl.FAIL_STREAK_LIMIT + 2) == ["pending"] * (tfl.FAIL_STREAK_LIMIT + 2)
    assert starts_asked(fake, postcode).count(control) > asked_before  # the control call ran, and was rate limited
    start_status.clear()
    failing_starts.add(control)
    assert poll_n(user, 1) == ["failed"]


def test_empty_200_answers_are_not_cached_and_are_asked_again(fake, destination_status):
    postcode, user = fresh_postcode("EC1A"), new_user()
    save(user, postcode)
    rows = pool_rows(GOOD)
    assert poll_n(user, 1) == ["pending"]
    first_batch = starts_asked(fake, postcode)
    assert sorted(first_batch) == sorted(r[1:] for r in rows[:tfl.BATCH_SIZE])
    destination_status[postcode.replace(" ", "")] = 200  # every journey answers 200 with body {}
    assert poll_n(user, 3) == ["pending", "pending", "failed"]
    during = starts_asked(fake, postcode)[len(first_batch):]
    assert during
    destination_status.clear()
    save(user, postcode)
    assert poll(user)[-1] == "ready"
    after = starts_asked(fake, postcode)[len(first_batch) + len(during):]
    # The control call during the outage re-asks one cached listing; every other one asked was uncached.
    assert set(during) - set(first_batch) <= set(after)  # never cached, so asked again
    assert set(during) - set(first_batch)
    assert not set(first_batch) & set(after)  # cached, so not asked again
