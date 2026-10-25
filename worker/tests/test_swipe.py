"""Black-box tests for POST /api/decisions/{id}/swipe and GET /api/profile, against `pywrangler dev` in test mode
(see worker/README.md). Favourite rows are read from the local D1."""
import pytest

from conftest import call
from test_deck import TEXT, assert_error, get_deck, new_user, save, stored_rows

# No test here may call the API before the fake fixture's probe has passed.
pytestmark = pytest.mark.usefixtures("fake")


@pytest.fixture
def user():
    uid = new_user()
    save(uid)
    return uid


def swipe(user, decision_id, action="right"):
    return call("POST", f"/api/decisions/{decision_id}/swipe", user_id=user, body={"action": action})


def swipe_ok(user, decision_id, action="right"):
    status, payload = swipe(user, decision_id, action)
    assert status == 200, payload
    return payload


def profile(user):
    status, payload = call("GET", "/api/profile", user_id=user)
    assert status == 200, payload
    return payload


def test_response_body_for_each_action(user):
    cards = get_deck(user, 3)["cards"]
    for card, action in zip(cards, ["left", "right", "superlike"]):
        assert swipe_ok(user, card["decision_id"], action) == {
            "decision_id": card["decision_id"], "action": action, "feedback_required": True,
            "favourited": action == "superlike", "profile_version": cards.index(card) + 1}


def test_missing_user_is_401(user):
    decision = get_deck(user, 1)["cards"][0]["decision_id"]
    assert_error(*call("POST", f"/api/decisions/{decision}/swipe", body={"action": "left"}), 401, "unknown_user")


@pytest.mark.parametrize("body", [{"action": "up"}, {"action": "LEFT"}, {"action": None}, {"action": 1}, {"action": ["left"]}, {}])
def test_other_action_is_422(user, body):
    decision = get_deck(user, 1)["cards"][0]["decision_id"]
    assert_error(*call("POST", f"/api/decisions/{decision}/swipe", user_id=user, body=body), 422, "invalid_request")
    assert profile(user)["version"] == 0


def test_body_that_is_not_an_object_is_422(user):
    decision = get_deck(user, 1)["cards"][0]["decision_id"]
    assert_error(*call("POST", f"/api/decisions/{decision}/swipe", user_id=user, raw=b"not json"), 422, "invalid_request")
    assert_error(*call("POST", f"/api/decisions/{decision}/swipe", user_id=user, body=["left"]), 422, "invalid_request")


def test_unknown_id_is_404(user):
    assert_error(*swipe(user, "d_0000000000000000"), 404, "decision_not_found")


def test_another_users_decision_is_404_and_stays_unswiped(user):
    decision = get_deck(user, 1)["cards"][0]["decision_id"]
    assert_error(*swipe(new_user(), decision), 404, "decision_not_found")
    assert swipe_ok(user, decision)["profile_version"] == 1


def test_decision_dropped_by_a_prefs_resave_is_404(user):
    decision = get_deck(user, 1)["cards"][0]["decision_id"]
    save(user)
    assert_error(*swipe(user, decision), 404, "decision_not_found")
    assert profile(user)["version"] == 0


def test_second_swipe_is_409_and_changes_nothing(user):
    decision = get_deck(user, 1)["cards"][0]["decision_id"]
    swipe_ok(user, decision, "left")
    assert_error(*swipe(user, decision, "superlike"), 409, "already_swiped")
    assert profile(user)["version"] == 1
    assert stored_rows(user, "favourites") == []
    (row,) = [d for d in stored_rows(user, "decisions") if d["decision_id"] == decision]
    assert row["action"] == "left"


def test_superlike_adds_one_favourite_and_right_does_not(user):
    liked, superliked = get_deck(user, 2)["cards"]
    assert swipe_ok(user, liked["decision_id"], "right")["favourited"] is False
    assert stored_rows(user, "favourites") == []
    result = swipe_ok(user, superliked["decision_id"], "superlike")
    assert result["favourited"] is True and result["profile_version"] == 2  # one bump for the swipe and the favourite
    (fav,) = stored_rows(user, "favourites")
    assert fav["listing_id"] == superliked["listing"]["id"] and fav["decision_id"] == superliked["decision_id"]
    assert fav["added_at"].endswith("Z")


def test_new_user_profile_is_empty():
    assert profile(new_user()) == {"version": 0, "factors": [], "history": []}


def test_feedback_required_and_profile_history_over_sixteen_swipes(user):
    first = get_deck(user, 10)["cards"]
    results = [swipe_ok(user, c["decision_id"], ["left", "right", "superlike"][i % 3]) for i, c in enumerate(first)]
    second = get_deck(user, 10)["cards"]
    results += [swipe_ok(user, c["decision_id"]) for c in second[:5]]
    assert [r["feedback_required"] for r in results] == [True] * 15
    assert [r["profile_version"] for r in results] == list(range(1, 16))
    # A prefs re-save drops the unswiped cards but not the swipe count.
    save(user)
    fresh = get_deck(user, 3)["cards"]
    sixteenth = swipe_ok(user, fresh[0]["decision_id"])
    assert sixteenth["feedback_required"] is False and sixteenth["profile_version"] == 16
    body = profile(user)
    assert body["version"] == 16 and body["factors"] == []
    assert [h["version"] for h in body["history"]] == list(range(16, 6, -1))
    swiped = [r["decision_id"] for r in results] + [fresh[0]["decision_id"]]
    for entry, decision in zip(body["history"], reversed(swiped)):
        assert entry["cause"] == {"type": "swipe", "decision_id": decision, "flag_id": None, "listing_id": None}
        assert entry["created_at"].endswith("Z")
    assert [h["created_at"] for h in body["history"]] == sorted((h["created_at"] for h in body["history"]), reverse=True)


def test_every_card_served_after_fifteen_swipes_is_not_required(user):
    for card in get_deck(user, 10)["cards"]:
        swipe_ok(user, card["decision_id"], "left")
    for card in get_deck(user, 10)["cards"][:5]:
        swipe_ok(user, card["decision_id"], "left")
    cards = get_deck(user, 10)["cards"]
    assert len(cards) == 10 and all(c["feedback_required"] is False for c in cards)


def test_page_served_after_twelve_swipes_changes_at_position_three(user):
    for card in get_deck(user, 10)["cards"]:
        swipe_ok(user, card["decision_id"], "left")
    for card in get_deck(user, 10)["cards"][:2]:
        swipe_ok(user, card["decision_id"], "left")
    cards = get_deck(user, 10)["cards"]
    assert len(cards) == 10
    assert [c["feedback_required"] for c in cards] == [True] * 3 + [False] * 7


def test_swiping_the_whole_train_pool_gives_exhausted_without_a_curator_call(fake):
    uid = new_user()
    save(uid, text=f"{TEXT} [[tight]]")
    cards = get_deck(uid)["cards"]
    assert len(cards) == 7  # the whole train pool for these prefs
    for card in cards:
        swipe_ok(uid, card["decision_id"], "left")
    before = len(fake.curator_requests)
    assert call("GET", "/api/deck", user_id=uid) == (200, {"empty_reason": "exhausted", "cards": []})
    assert len(fake.curator_requests) == before


def test_prefs_that_match_nothing_give_no_matches_not_exhausted():
    uid = new_user()
    save(uid, postcode="EC2N 2DB", max_commute=45)  # the fake never finishes this commute, so the limit leaves no pool
    assert call("GET", "/api/deck", user_id=uid) == (200, {"empty_reason": "no_matches", "cards": []})
