"""Black-box tests for GET /api/deck and the deck drop on PUT /api/prefs, against `pywrangler dev` in test mode
(see worker/README.md). The fake upstream answers the curator by sorting the candidate ids."""
import json
import re
import secrets
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import deck
import fake_upstream
from conftest import call

# No test here may call the API before the fake fixture's probe has passed.
pytestmark = pytest.mark.usefixtures("fake")

LISTINGS_DB = Path(__file__).resolve().parents[2] / "dataset" / "listings.sqlite"
TEXT = "Two bed flat under 550k, near a tube station, bright rooms, no ground floor."
# What the fake's parsed reply asks for: price, bedrooms, type and EPC limits.
GOOD_POOL_SQL = ("SELECT id FROM listings WHERE split = ? AND price_gbp <= 550000 AND bedrooms >= 2"
                 " AND property_type IN ('flat', 'maisonette') AND epc_current IN ('A', 'B', 'C', 'D')")
CARD_KEYS = {"decision_id", "source", "feedback_required", "listing", "commute", "chips"}
LISTING_KEYS = {"id", "price_gbp", "price_qualifier", "bedrooms", "bathrooms", "property_type", "address", "postcode",
                "lat", "lon", "tenure", "epc_current", "floor_level", "key_features", "photos"}


def new_user():
    status, created = call("POST", "/api/users", body={"username": "t_" + secrets.token_hex(6)})
    assert status == 201
    return created["user_id"]


def save(user, text=TEXT, postcode=None, max_commute=None):
    body = {"text": text, "commute_postcode": postcode, "max_commute_min": max_commute}
    status, saved = call("PUT", "/api/prefs", user_id=user, body=body)
    assert status == 200, saved


@pytest.fixture
def user():
    uid = new_user()
    save(uid)
    return uid


def get_deck(user, n=10):
    status, payload = call("GET", f"/api/deck?n={n}", user_id=user)
    assert status == 200, payload
    return payload


def assert_error(status, payload, expected_status, code):
    assert status == expected_status
    assert set(payload) == {"error"} and set(payload["error"]) == {"code", "message"}
    assert payload["error"]["code"] == code


def ids(payload):
    return [c["decision_id"] for c in payload["cards"]]


def test_missing_header_is_401():
    assert_error(*call("GET", "/api/deck"), 401, "unknown_user")


def test_no_prefs_is_409_prefs_missing():
    assert_error(*call("GET", "/api/deck", user_id=new_user()), 409, "prefs_missing")


@pytest.mark.parametrize("n", ["0", "11", "abc", "", "-1", "2.5"])
def test_n_outside_one_to_ten_or_not_an_integer_is_422(user, n):
    assert_error(*call("GET", f"/api/deck?n={n}", user_id=user), 422, "invalid_request")


def test_n_defaults_to_ten(user):
    status, payload = call("GET", "/api/deck", user_id=user)
    assert status == 200 and len(payload["cards"]) == 10


def test_ten_cards_with_exploration_at_positions_five_and_ten(user, fake):
    before = len(fake.curator_requests)
    payload = get_deck(user)
    assert len(fake.curator_requests) == before + 1
    cards = payload["cards"]
    assert payload["empty_reason"] is None and len(cards) == 10
    assert [c["source"] for c in cards] == ["ranked"] * 4 + ["exploration"] + ["ranked"] * 4 + ["exploration"]
    returned = fake.curator_requests[-1]["returned"]
    assert len(returned) == 30
    for position in (4, 9):
        share = (returned.index(cards[position]["listing"]["id"]) + 1) / len(returned)
        assert 0.5 <= share <= 0.8
    # Ranked slots take the best ranks the exploration picks left free.
    ranked = [returned.index(c["listing"]["id"]) + 1 for c in cards if c["source"] == "ranked"]
    assert ranked == sorted(ranked) and ranked[:4] == [1, 2, 3, 4]


def test_card_shape_without_a_postcode(user):
    for card in get_deck(user)["cards"]:
        assert set(card) == CARD_KEYS
        assert card["decision_id"].startswith("d_") and card["source"] in ("ranked", "exploration")
        assert set(card["listing"]) == LISTING_KEYS
        assert isinstance(card["listing"]["key_features"], list) and card["listing"]["photos"]
        assert card["commute"] is None
        assert 1 <= len(card["chips"]) <= 8
        for chip in card["chips"]:
            assert set(chip) == {"chip_id", "label", "phrases"} and len(chip["phrases"]) == 4
        assert "commute" not in [c["chip_id"] for c in card["chips"]]


def test_feedback_required_for_the_first_fifteen_positions(user):
    assert all(c["feedback_required"] is True for c in get_deck(user)["cards"])


def test_commute_with_a_postcode_has_null_minutes_until_cached():
    uid = new_user()
    save(uid, postcode="EC2N 2DB")  # the fake always fails this postcode, so nothing is cached for it
    cards = get_deck(uid)["cards"]
    assert len(cards) == 10
    for card in cards:
        assert card["commute"] == {"minutes": None, "postcode": "EC2N 2DB", "assumptions": "weekday, arrive 08:30, public transport"}
        assert "commute" not in [c["chip_id"] for c in card["chips"]]


def test_commute_limit_while_pending_gives_an_empty_no_matches_deck(fake):
    uid = new_user()
    save(uid, postcode="EC2N 2DB", max_commute=45)
    before = len(fake.curator_requests)
    assert call("GET", "/api/deck", user_id=uid) == (200, {"empty_reason": "no_matches", "cards": []})
    assert len(fake.curator_requests) == before


def test_refetch_returns_the_same_decisions_first_without_a_curator_call(user, fake):
    first = get_deck(user)
    before = len(fake.curator_requests)
    assert get_deck(user) == first
    assert ids(get_deck(user, 3)) == ids(first)[:3]
    assert len(fake.curator_requests) == before


def test_second_batch_follows_the_first_with_no_repeats(user, fake):
    first = get_deck(user, 4)
    both = get_deck(user, 10)
    assert ids(both)[:4] == ids(first)
    assert len({c["listing"]["id"] for c in both["cards"]}) == 10
    # Slots 4 and 9 are exploration whichever request serves them.
    assert both["cards"][4]["source"] == "exploration" and both["cards"][9]["source"] == "exploration"


def test_resave_drops_unswiped_cards(user):
    old = set(ids(get_deck(user)))
    save(user)
    new = get_deck(user)
    assert len(new["cards"]) == 10
    assert not old & set(ids(new))


def pool_ids(sql_where, split):
    con = sqlite3.connect(f"file:{LISTINGS_DB}?mode=ro", uri=True)
    return {r[0] for r in con.execute(sql_where, (split,))}


def test_the_pool_is_train_only_and_a_listing_is_served_once_per_user():
    train, evaluation = pool_ids(GOOD_POOL_SQL, "train"), pool_ids(GOOD_POOL_SQL, "eval")
    assert train and evaluation
    seen = set()
    for _ in range(6):
        uid = new_user()
        save(uid)
        served = [c["listing"]["id"] for c in get_deck(uid)["cards"]]
        assert len(served) == len(set(served)) == 10
        seen |= set(served)
    assert seen <= train and not seen & evaluation
    assert len(seen) > 10  # the seeded sample differs between users


def test_a_pool_smaller_than_the_page_gives_a_short_deck():
    uid = new_user()
    save(uid, text=f"{TEXT} [[tight]]")
    cards = get_deck(uid)["cards"]
    expected = pool_ids(GOOD_POOL_SQL.replace("550000", "300000"), "train")
    assert len(expected) == 7
    assert {c["listing"]["id"] for c in cards} == expected
    assert [c["source"] for c in cards] == ["ranked"] * 4 + ["exploration"] + ["ranked"] * 2


@pytest.mark.parametrize("marker", ["[[curator_http_500]]", "[[curator_not_json]]", "[[curator_bad_ids]]"])
def test_curator_failure_with_nothing_outstanding_is_502(marker, fake):
    uid = new_user()
    save(uid, text=f"{TEXT} {marker}")
    before = len(fake.curator_requests)
    assert_error(*call("GET", "/api/deck", user_id=uid), 502, "curator_failed")
    assert len(fake.curator_requests) == before + 1


def test_curator_failure_with_outstanding_cards_serves_only_those(user, fake, monkeypatch):
    first = get_deck(user, 3)
    monkeypatch.setattr(fake_upstream, "curator_answer", lambda message: (500, "{}", []))
    before = len(fake.requests)
    served = get_deck(user, 10)
    assert len(fake.requests) == before + 1  # the failing call was made
    assert served == first and served["empty_reason"] is None


def test_a_failed_call_creates_no_decisions(fake, monkeypatch):
    uid = new_user()
    save(uid)
    with monkeypatch.context() as patch:
        patch.setattr(fake_upstream, "curator_answer", lambda message: (500, "{}", []))
        assert_error(*call("GET", "/api/deck", user_id=uid), 502, "curator_failed")
    # With nothing left behind by the failure, the next serve starts at slot 0 again.
    cards = get_deck(uid)["cards"]
    assert len(cards) == 10 and [c["source"] for c in cards].count("exploration") == 2


def test_place_gives_a_ranked_card_when_the_band_is_empty_or_used_up():
    ranking = ["a"]
    assert deck.place(ranking, 4, 1, "u") == [("a", "ranked", 1)]
    ranking = ["a", "b", "c"]
    # Slot 4 draws from the band (only rank 2 of 3 lies in it once rank 1 is taken); slots 3 and 5 take the best unused rank.
    picks = deck.place(ranking, 3, 3, "u")
    assert [p[1] for p in picks] == ["ranked", "exploration", "ranked"]
    assert sorted(p[0] for p in picks) == ["a", "b", "c"]


WORKER_DIR = Path(__file__).resolve().parent.parent


def d1_rows(sql):
    """Rows of a SELECT against the local D1 in worker/.wrangler. This reads the database of the server under test
    only when that server was started from this same worker directory (the BASE_URL server)."""
    run = subprocess.run(["npx", "--yes", "wrangler", "d1", "execute", "haka", "--local", "--json", "--command", sql],
                         cwd=WORKER_DIR, capture_output=True, check=True)
    return json.loads(run.stdout)[0]["results"]


def stored_rows(user, table):
    assert re.fullmatch(r"u_[0-9a-f]+", user)
    return d1_rows(f"SELECT * FROM {table} WHERE user_id = '{user}'")


def test_stored_mreq_id_is_the_id_the_curator_call_returned(fake):
    first, second = new_user(), new_user()
    save(first), save(second)
    before = len(fake.curator_requests)
    get_deck(first)
    sent = fake.curator_requests[before]["request_id"]
    get_deck(second)
    other = fake.curator_requests[before + 1]["request_id"]
    assert len(fake.curator_requests) == before + 2 and sent != other
    (row,) = stored_rows(first, "curator_calls")
    assert row["mreq_id"] == sent and sent.startswith("mreq_")
    assert row["profile_version"] == deck.EMPTY_PROFILE_VERSION
    decisions = stored_rows(first, "decisions")
    assert len(decisions) == 10
    assert {d["curator_call_id"] for d in decisions} == {row["call_id"]}
    assert {d["profile_version"] for d in decisions} == {row["profile_version"]}
    (row_two,) = stored_rows(second, "curator_calls")
    assert row_two["mreq_id"] == other
    assert other not in json.dumps([row, *decisions])


def test_failed_curator_call_stores_the_id_it_returned(fake):
    user = new_user()
    save(user, text="[[curator_http_500]] " + TEXT)
    before = len(fake.curator_requests)
    status, payload = call("GET", "/api/deck?n=10", user_id=user)
    assert status == 502, payload
    (row,) = stored_rows(user, "curator_calls")
    assert row["status"] == "failed"
    assert row["mreq_id"] == fake.curator_requests[before]["request_id"]
