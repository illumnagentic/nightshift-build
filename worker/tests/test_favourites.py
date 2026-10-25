"""Black-box tests for GET /api/favourites and DELETE /api/favourites/{listing_id}, against `pywrangler dev` in test
mode (see worker/README.md). Stored rows are read from the local D1."""
import pytest

from conftest import call
from test_deck import LISTING_KEYS, assert_error, get_deck, new_user, save, stored_rows
from test_swipe import profile, swipe_ok

# No test here may call the API before the fake fixture's probe has passed.
pytestmark = pytest.mark.usefixtures("fake")


@pytest.fixture
def user():
    uid = new_user()
    save(uid)
    return uid


def favourite(user, n=1):
    """Superlike the next n cards; return them in the order swiped."""
    cards = get_deck(user, n)["cards"]
    for card in cards:
        swipe_ok(user, card["decision_id"], "superlike")
    return cards


def remove(user, listing_id, body=None, raw=None):
    return call("DELETE", f"/api/favourites/{listing_id}", user_id=user, body=body, raw=raw)


def favourites(user):
    status, payload = call("GET", "/api/favourites", user_id=user)
    assert status == 200, payload
    return payload["favourites"]


def test_missing_user_is_401():
    assert_error(*call("GET", "/api/favourites"), 401, "unknown_user")
    assert_error(*call("DELETE", "/api/favourites/rm-1", body={"reason": "x"}), 401, "unknown_user")


def test_new_user_has_no_favourites(user):
    assert favourites(user) == []


def test_lists_superliked_cards_newest_first_with_the_card_listing_object(user):
    cards = favourite(user, 3)
    listed = favourites(user)
    assert [f["listing"] for f in listed] == [c["listing"] for c in reversed(cards)]
    for entry in listed:
        assert set(entry) == {"added_at", "listing"} and set(entry["listing"]) == LISTING_KEYS
        assert entry["added_at"].endswith("Z")
    assert [f["added_at"] for f in listed] == sorted((f["added_at"] for f in listed), reverse=True)


def test_a_right_swipe_is_not_a_favourite_and_users_do_not_share(user):
    liked, superliked = get_deck(user, 2)["cards"]
    swipe_ok(user, liked["decision_id"], "right")
    swipe_ok(user, superliked["decision_id"], "superlike")
    assert [f["listing"]["id"] for f in favourites(user)] == [superliked["listing"]["id"]]
    assert favourites(new_user()) == []


@pytest.mark.parametrize("body, raw", [
    (None, None), (None, b""), (None, b"not json"), ({}, None), ({"reason": None}, None), ({"reason": 5}, None),
    ({"reason": ["x"]}, None), ({"reason": ""}, None), ({"reason": "   "}, None), ([], None), (None, b"[]"),
])
def test_missing_null_non_string_or_blank_reason_is_422_reason_required(user, body, raw):
    (card,) = favourite(user)
    before = profile(user)["version"]
    assert_error(*remove(user, card["listing"]["id"], body=body, raw=raw), 422, "reason_required")
    assert len(favourites(user)) == 1 and profile(user)["version"] == before
    assert stored_rows(user, "favourite_removals") == []


def test_reason_required_wins_over_not_favourited(user):
    assert_error(*remove(user, "rm-0", body={}), 422, "reason_required")


def test_not_a_favourite_is_404_and_changes_nothing(user):
    liked, other = get_deck(user, 2)["cards"]
    swipe_ok(user, liked["decision_id"], "right")
    before = profile(user)["version"]
    assert_error(*remove(user, "rm-0", {"reason": "gone"}), 404, "not_favourited")
    assert_error(*remove(user, liked["listing"]["id"], {"reason": "gone"}), 404, "not_favourited")
    assert_error(*remove(user, other["listing"]["id"], {"reason": "gone"}), 404, "not_favourited")
    assert profile(user)["version"] == before and stored_rows(user, "favourite_removals") == []


def test_another_users_favourite_is_404_and_stays(user):
    (card,) = favourite(user)
    assert_error(*remove(new_user(), card["listing"]["id"], {"reason": "gone"}), 404, "not_favourited")
    assert len(favourites(user)) == 1


def test_removal_returns_the_body_stores_the_reason_and_bumps_the_version_once(user):
    kept, gone = favourite(user, 2)
    before = profile(user)["version"]
    listing_id = gone["listing"]["id"]
    assert remove(user, listing_id, {"reason": "  Too far from the station.  "}) == (200, {"listing_id": listing_id, "removed": True})
    assert [f["listing"]["id"] for f in favourites(user)] == [kept["listing"]["id"]]
    (stored,) = stored_rows(user, "favourite_removals")
    assert stored["listing_id"] == listing_id and stored["reason"] == "Too far from the station."
    assert stored["decision_id"] == gone["decision_id"]
    now = profile(user)
    assert now["version"] == before + 1
    assert now["history"][0]["cause"] == {"type": "favourite_removed", "decision_id": None, "flag_id": None, "listing_id": listing_id}
    assert_error(*remove(user, listing_id, {"reason": "again"}), 404, "not_favourited")
    assert profile(user)["version"] == before + 1


def test_the_reason_feeds_matching_factors_in_the_new_versions_snapshot(user):
    kept, gone = favourite(user, 2)
    assert profile(user)["factors"] == []
    remove(user, gone["listing"]["id"], {"reason": "No garden and the kitchen is tiny."})
    factors = {f["factor"]: f for f in profile(user)["factors"]}
    assert set(factors) == {"garden", "kitchen", "space"}
    assert factors["garden"] == {"factor": "garden", "direction": "mentioned in comments", "weight": 0.5}


def test_a_reason_with_no_matching_term_adds_no_factor_but_still_bumps(user):
    (card,) = favourite(user)
    before = profile(user)["version"]
    remove(user, card["listing"]["id"], {"reason": "Changed my mind."})
    now = profile(user)
    assert now["factors"] == [] and now["version"] == before + 1
