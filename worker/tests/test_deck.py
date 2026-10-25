"""GET /api/deck against `pywrangler dev` in test mode (see worker/README.md), plus unit tests of the card picker.

The curator is the fake in fake_upstream.py: a deterministic score per listing id. Swipes do not exist yet, so a deck
can never run out through the API: the `exhausted` reason and the picker's handling of swiped listings are covered by
the unit tests on `deck.pick_new` only.
"""
import hashlib
import math
import secrets
import sqlite3
import string
import sys
from pathlib import Path

import pytest

from conftest import call
import fake_upstream

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import curator  # noqa: E402
import deck  # noqa: E402
import filters  # noqa: E402

LISTINGS_DB = Path(__file__).resolve().parents[2] / "dataset" / "listings.sqlite"
CARD_KEYS = {"decision_id", "source", "feedback_required", "listing", "commute", "chips"}
LISTING_KEYS = {"id", "price_gbp", "price_qualifier", "bedrooms", "bathrooms", "property_type", "address", "postcode", "lat",
                "lon", "tenure", "epc_current", "floor_level", "key_features", "photos"}


@pytest.fixture
def user(fake):
    status, created = call("POST", "/api/users", body={"username": "t_" + secrets.token_hex(6)})
    assert status == 201
    return created["user_id"]


def save_prefs(user_id, **extra):
    status, saved = call("PUT", "/api/prefs", user_id=user_id, body={"text": "a flat", **extra})
    assert status == 200
    return saved


def saved_user(user_id):
    save_prefs(user_id)
    return user_id


def new_saved_user():
    status, created = call("POST", "/api/users", body={"username": "t_" + secrets.token_hex(6)})
    assert status == 201
    return saved_user(created["user_id"])


def deck_of(user_id, n=10):
    status, payload = call("GET", f"/api/deck?n={n}", user_id=user_id)
    assert status == 200, payload
    return payload


def curator_calls(fake) -> int:
    return sum(1 for r in fake.requests if r["body"].get("systemInstruction", {}).get("parts", [{}])[0].get("text") == curator.SYSTEM_PROMPT)


def listings_by_split():
    conn = sqlite3.connect(f"file:{LISTINGS_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute("SELECT * FROM listings").fetchall()
    finally:
        conn.close()


def fake_pool():
    """Train listings that pass the fake prefs answer's hard limits, best fake score first, as the deck ranks them."""
    hard = {**fake_upstream.GOOD["hard"], "max_commute_min": None}
    pool = [r["id"] for r in listings_by_split() if r["split"] == "train" and filters.passes(r, hard, None)]
    return sorted(pool, key=lambda i: (-(int(hashlib.sha256(i.encode()).hexdigest(), 16) % 101), i))


def assert_error(status, payload, expected_status, code):
    assert status == expected_status
    assert set(payload) == {"error"} and set(payload["error"]) == {"code", "message"}
    assert payload["error"]["code"] == code


def test_missing_header_is_401(fake):
    assert_error(*call("GET", "/api/deck"), 401, "unknown_user")


def test_no_prefs_is_409(user):
    assert_error(*call("GET", "/api/deck", user_id=user), 409, "prefs_missing")


@pytest.mark.parametrize("n", ["0", "11", "-1", "abc", "1.5", "", "%2B5", "10000000000"])
def test_bad_n_is_422(user, n):
    save_prefs(user)
    assert_error(*call("GET", f"/api/deck?n={n}", user_id=user), 422, "invalid_request")


def test_n_defaults_to_ten_and_accepts_one(user):
    saved_user(user)
    status, payload = call("GET", "/api/deck", user_id=user)
    assert status == 200 and len(payload["cards"]) == 10
    assert len(deck_of(user, 1)["cards"]) == 1


def test_first_deck_shape(user):
    saved_user(user)
    payload = deck_of(user)
    assert set(payload) == {"empty_reason", "cards"} and payload["empty_reason"] is None
    cards = payload["cards"]
    assert len(cards) == 10
    assert len({c["decision_id"] for c in cards}) == 10 and len({c["listing"]["id"] for c in cards}) == 10
    for card in cards:
        assert set(card) == CARD_KEYS
        assert card["decision_id"].startswith("d_")
        assert card["source"] in ("ranked", "exploration")
        assert card["feedback_required"] is True
        assert card["commute"] is None
        assert set(card["listing"]) == LISTING_KEYS
        assert isinstance(card["listing"]["key_features"], list)
        assert card["listing"]["photos"] and all(p.startswith("http") for p in card["listing"]["photos"])
        assert 1 <= len(card["chips"]) <= 8
        for chip in card["chips"]:
            assert set(chip) == {"chip_id", "label", "phrases"} and len(chip["phrases"]) == 4
        assert len({c["chip_id"] for c in card["chips"]}) == len(card["chips"])


def test_ranked_cards_come_in_score_order(user):
    saved_user(user)
    position = {listing_id: i for i, listing_id in enumerate(fake_pool())}
    ranked = [position[c["listing"]["id"]] for c in deck_of(user)["cards"] if c["source"] == "ranked"]
    assert ranked == sorted(ranked)


def test_served_cards_come_back_first_with_the_same_ids(user):
    saved_user(user)
    first = deck_of(user)["cards"]
    again = deck_of(user)["cards"]
    assert [c["decision_id"] for c in again] == [c["decision_id"] for c in first]
    assert [c for c in again] == [c for c in first]
    assert [c["decision_id"] for c in deck_of(user, 4)["cards"]] == [c["decision_id"] for c in first[:4]]


def test_scores_are_cached_between_calls(user, fake):
    saved_user(user)
    before = curator_calls(fake)
    deck_of(user)
    after_first = curator_calls(fake)
    assert after_first - before == math.ceil(len(fake_pool()) / curator.CHUNK_SIZE)
    deck_of(user)
    assert curator_calls(fake) == after_first


def test_every_served_listing_is_train_split(fake):
    train = {r["id"] for r in listings_by_split() if r["split"] == "train"}
    assert train and len(train) < len(listings_by_split())
    for _ in range(3):
        user_id = new_saved_user()
        assert {c["listing"]["id"] for c in deck_of(user_id)["cards"]} <= train


def test_about_one_in_five_is_exploration_from_the_band(fake):
    pool = fake_pool()
    lo, hi = math.floor(0.5 * len(pool)), math.floor(0.8 * len(pool))
    sources = []
    for _ in range(6):  # one deck holds at most 10 unswiped cards, so a larger sample comes from several users
        for card in deck_of(new_saved_user())["cards"]:
            sources.append(card["source"])
            if card["source"] == "exploration":
                assert lo <= pool.index(card["listing"]["id"]) < hi
    assert len(sources) == 60
    assert 2 <= sources.count("exploration") <= 25


def test_resave_drops_served_cards_and_rescored(user, fake):
    saved_user(user)
    first = deck_of(user)["cards"]
    before = curator_calls(fake)
    save_prefs(user)
    second = deck_of(user)["cards"]
    assert len(second) == 10
    assert not {c["decision_id"] for c in first} & {c["decision_id"] for c in second}
    assert curator_calls(fake) - before == math.ceil(len(fake_pool()) / curator.CHUNK_SIZE)


def test_commute_block_with_a_postcode(user):
    postcode = f"EC2N {secrets.randbelow(10)}{''.join(secrets.choice(string.ascii_uppercase) for _ in range(2))}"
    saved = save_prefs(user, commute_postcode=postcode)
    cards = deck_of(user)["cards"]
    assert cards
    for card in cards:
        assert card["commute"] == {"minutes": None, "postcode": saved["commute_postcode"], "assumptions": "weekday, arrive 08:30, public transport"}
        assert "commute" not in {c["chip_id"] for c in card["chips"]}


def test_commute_limit_with_nothing_cached_is_no_matches(user):
    postcode = f"EC2N {secrets.randbelow(10)}{''.join(secrets.choice(string.ascii_uppercase) for _ in range(2))}"
    save_prefs(user, commute_postcode=postcode, max_commute_min=1)
    assert deck_of(user) == {"empty_reason": "no_matches", "cards": []}


def test_every_chunk_failing_is_502(user, monkeypatch):
    with monkeypatch.context() as patch:  # the marker reaches the curator through the saved soft preferences
        patch.setitem(fake_upstream.GOOD, "soft", fake_upstream.GOOD["soft"] + ["[[curator_500]]"])
        save_prefs(user)
    assert_error(*call("GET", "/api/deck", user_id=user), 502, "curator_failed")
    # Nothing was served, so the next try starts clean.
    assert_error(*call("GET", "/api/deck", user_id=user), 502, "curator_failed")


# --- the picker, no server needed ---

ORDER = [f"l{i}" for i in range(20)]  # best first; the exploration band is positions 10 to 15


def test_pick_new_is_seeded_per_user_and_count():
    assert deck.pick_new(ORDER, set(), 0, "u_a", 10) == deck.pick_new(ORDER, set(), 0, "u_a", 10)
    assert deck.pick_new(ORDER, set(), 0, "u_a", 10) != deck.pick_new(ORDER, set(), 0, "u_b", 10)
    # Continuing from k gives the same cards as one long run.
    whole = deck.pick_new(ORDER, set(), 0, "u_a", 10)
    first = deck.pick_new(ORDER, set(), 0, "u_a", 4)
    rest = deck.pick_new(ORDER, {i for i, _ in first}, 4, "u_a", 6)
    assert first + rest == whole


def test_pick_new_ranked_take_the_best_and_exploration_the_band():
    picked = deck.pick_new(ORDER, set(), 0, "u_a", 20)
    assert len({i for i, _ in picked}) == 20
    for listing_id, source in picked:
        if source == "exploration":
            assert 10 <= ORDER.index(listing_id) < 16
    ranked = [ORDER.index(i) for i, s in picked if s == "ranked"]
    assert ranked == sorted(ranked)


def test_pick_new_skips_unavailable_and_stops_when_empty():
    picked = deck.pick_new(ORDER, {"l0", "l1", "l12"}, 0, "u_a", 50)
    assert {i for i, _ in picked} == set(ORDER) - {"l0", "l1", "l12"}
    assert deck.pick_new(ORDER, set(ORDER), 0, "u_a", 5) == []
    assert deck.pick_new([], set(), 0, "u_a", 5) == []


def test_pick_new_falls_back_to_ranked_when_the_band_is_used_up():
    unavailable = {ORDER[i] for i in range(10, 16)}
    picked = deck.pick_new(ORDER, unavailable, 0, "u_a", 14)
    assert {s for _, s in picked} == {"ranked"}
