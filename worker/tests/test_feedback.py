"""Black-box tests for PUT /api/decisions/{id}/feedback and the factors in GET /api/profile, against `pywrangler dev`
in test mode (see worker/README.md). Stored rows are read from the local D1."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import chips as chip_module  # noqa: E402
import taste  # noqa: E402
from conftest import call  # noqa: E402
from test_deck import assert_error, get_deck, new_user, save, stored_rows  # noqa: E402
from test_swipe import profile, swipe_ok  # noqa: E402

# No test here may call the API before the fake fixture's probe has passed.
pytestmark = pytest.mark.usefixtures("fake")

ALL_CHIPS = [row[0] for row in chip_module.CATALOGUE]


@pytest.fixture
def user():
    uid = new_user()
    save(uid)
    return uid


def put(user, decision_id, body):
    return call("PUT", f"/api/decisions/{decision_id}/feedback", user_id=user, body=body)


def put_ok(user, decision_id, body):
    status, payload = put(user, decision_id, body)
    assert status == 200, payload
    return payload


def swiped_card(user, action="right"):
    card = get_deck(user, 1)["cards"][0]
    swipe_ok(user, card["decision_id"], action)
    return card


def answer(chip_id, strength="must_have", text=None):
    return {"chip_id": chip_id, "strength": strength, "text": text}


def test_response_echoes_the_feedback_with_the_new_version(user):
    card = swiped_card(user)
    first, second = [c["chip_id"] for c in card["chips"][:2]]
    body = {"chips": [answer(first, "must_have", "Bright and airy"), answer(second, "would_prefer_not")],
            "free_text": "Lovely kitchen, but the street felt noisy."}
    assert put_ok(user, card["decision_id"], body) == {
        "decision_id": card["decision_id"], "chips": body["chips"], "free_text": body["free_text"], "skipped": False,
        "profile_version": 2}


@pytest.mark.parametrize("body", [
    {"free_text": None}, {"chips": []}, {}, {"chips": None, "free_text": None}, {"chips": {}, "free_text": None},
    {"chips": [], "free_text": 5}, {"chips": [], "free_text": ["x"]},
    {"chips": ["garden"], "free_text": None}, {"chips": [{"strength": "must_have", "text": None}], "free_text": None},
    {"chips": [{"chip_id": 1, "strength": "must_have", "text": None}], "free_text": None},
    {"chips": [{"chip_id": "garden", "text": None}], "free_text": None},
    {"chips": [{"chip_id": "garden", "strength": "love_it", "text": None}], "free_text": None},
    {"chips": [{"chip_id": "garden", "strength": "MUST_HAVE", "text": None}], "free_text": None},
    {"chips": [{"chip_id": "garden", "strength": 3, "text": None}], "free_text": None},
    {"chips": [{"chip_id": "garden", "strength": "must_have", "text": 7}], "free_text": None},
    {"chips": [], "free_text": None, "skipped": "yes"}, {"chips": [], "free_text": None, "skipped": 1},
    {"chips": [], "free_text": None, "skipped": None},
])
def test_malformed_body_is_422_and_changes_nothing(user, body):
    card = swiped_card(user)
    assert_error(*put(user, card["decision_id"], body), 422, "invalid_request")
    assert profile(user)["version"] == 1 and stored_rows(user, "feedback") == []


def test_body_that_is_not_an_object_is_422(user):
    card = swiped_card(user)
    assert_error(*call("PUT", f"/api/decisions/{card['decision_id']}/feedback", user_id=user, raw=b"not json"), 422, "invalid_request")
    assert_error(*put(user, card["decision_id"], []), 422, "invalid_request")


def test_repeated_chip_id_is_422(user):
    card = swiped_card(user)
    chip = card["chips"][0]["chip_id"]
    body = {"chips": [answer(chip), answer(chip, "deal_breaker", "again")], "free_text": None}
    assert_error(*put(user, card["decision_id"], body), 422, "invalid_request")
    assert stored_rows(user, "feedback") == []


def test_chip_not_offered_on_that_card_is_422_and_changes_nothing(user):
    card = swiped_card(user)
    offered = [c["chip_id"] for c in card["chips"]]
    not_offered = next(c for c in ALL_CHIPS if c not in offered)
    body = {"chips": [answer(offered[0]), answer(not_offered)], "free_text": None}
    assert_error(*put(user, card["decision_id"], body), 422, "chip_not_offered")
    assert_error(*put(user, card["decision_id"], {"chips": [answer("no_such_chip")], "free_text": None}), 422, "chip_not_offered")
    assert profile(user)["version"] == 1 and stored_rows(user, "feedback") == []


def test_blank_texts_are_stored_and_returned_as_null(user):
    card = swiped_card(user)
    chip = card["chips"][0]["chip_id"]
    body = {"chips": [answer(chip, "nice_to_have", "  \t ")], "free_text": " \n "}
    result = put_ok(user, card["decision_id"], body)
    assert result["free_text"] is None and result["chips"] == [answer(chip, "nice_to_have", None)]
    (row,) = stored_rows(user, "feedback")
    assert row["free_text"] is None and json.loads(row["chips_json"]) == [answer(chip, "nice_to_have", None)]
    assert put_ok(user, card["decision_id"], {"chips": [{"chip_id": chip, "strength": "nice_to_have"}], "free_text": ""})["chips"] == [
        answer(chip, "nice_to_have", None)]


@pytest.mark.parametrize("extra", [
    {"chips": [answer("garden")], "free_text": None}, {"chips": [], "free_text": "a note"},
    {"chips": [answer("garden")], "free_text": "a note"}])
def test_skipped_true_needs_no_chips_and_no_free_text(user, extra):
    card = swiped_card(user)
    assert_error(*put(user, card["decision_id"], {**extra, "skipped": True}), 422, "invalid_request")
    assert stored_rows(user, "feedback") == []


def test_skipped_true_with_blank_free_text_is_a_skip(user):
    card = swiped_card(user)
    result = put_ok(user, card["decision_id"], {"chips": [], "free_text": "  ", "skipped": True})
    assert result == {"decision_id": card["decision_id"], "chips": [], "free_text": None, "skipped": True, "profile_version": 2}
    (row,) = stored_rows(user, "feedback")
    assert row["skipped"] == 1


def test_a_later_put_without_skipped_replaces_the_skip(user):
    card = swiped_card(user)
    chip = card["chips"][0]["chip_id"]
    put_ok(user, card["decision_id"], {"chips": [], "free_text": None, "skipped": True})
    result = put_ok(user, card["decision_id"], {"chips": [answer(chip)], "free_text": None})
    assert result["skipped"] is False
    (row,) = stored_rows(user, "feedback")
    assert row["skipped"] == 0 and json.loads(row["chips_json"]) == [answer(chip)]


def test_unknown_decision_is_404(user):
    assert_error(*put(user, "d_0000000000000000", {"chips": [], "free_text": None}), 404, "decision_not_found")


def test_another_users_decision_is_404_and_stores_nothing(user):
    card = swiped_card(user)
    other = new_user()
    assert_error(*put(other, card["decision_id"], {"chips": [], "free_text": None}), 404, "decision_not_found")
    assert profile(other)["version"] == 0 and stored_rows(other, "feedback") == [] and stored_rows(user, "feedback") == []


def test_decision_dropped_by_a_prefs_resave_is_404(user):
    card = get_deck(user, 1)["cards"][0]
    save(user)
    assert_error(*put(user, card["decision_id"], {"chips": [], "free_text": None}), 404, "decision_not_found")


def test_not_swiped_yet_is_409(user):
    card = get_deck(user, 1)["cards"][0]
    assert_error(*put(user, card["decision_id"], {"chips": [], "free_text": None}), 409, "not_swiped")
    assert profile(user)["version"] == 0 and stored_rows(user, "feedback") == []


def test_missing_user_is_401(user):
    card = swiped_card(user)
    assert_error(*call("PUT", f"/api/decisions/{card['decision_id']}/feedback", body={"chips": [], "free_text": None}), 401, "unknown_user")


def test_feedback_is_accepted_after_onboarding_on_any_action(user):
    for action in ("left", "superlike"):
        card = swiped_card(user, action)
        assert put_ok(user, card["decision_id"], {"chips": [], "free_text": "fine"})["skipped"] is False


def test_put_replaces_the_whole_feedback_and_a_clear_empties_it(user):
    card = swiped_card(user)
    first, second = [c["chip_id"] for c in card["chips"][:2]]
    put_ok(user, card["decision_id"], {"chips": [answer(first), answer(second)], "free_text": "one"})
    edited = put_ok(user, card["decision_id"], {"chips": [answer(second, "deal_breaker", "no")], "free_text": "two"})
    assert edited["chips"] == [answer(second, "deal_breaker", "no")] and edited["free_text"] == "two"
    (row,) = stored_rows(user, "feedback")
    assert json.loads(row["chips_json"]) == edited["chips"] and row["free_text"] == "two"
    cleared = put_ok(user, card["decision_id"], {"chips": [], "free_text": None})
    assert cleared == {"decision_id": card["decision_id"], "chips": [], "free_text": None, "skipped": False, "profile_version": 4}
    (row,) = stored_rows(user, "feedback")
    assert row["chips_json"] == "[]" and row["free_text"] is None and row["skipped"] == 0


def test_every_put_bumps_the_version_once_with_cause_feedback(user):
    card = swiped_card(user)
    body = {"chips": [answer(card["chips"][0]["chip_id"])], "free_text": None}
    versions = [put_ok(user, card["decision_id"], body)["profile_version"] for _ in range(2)]  # the second changes nothing
    versions.append(put_ok(user, card["decision_id"], {"chips": [], "free_text": None})["profile_version"])  # a clear
    versions.append(put_ok(user, card["decision_id"], {"chips": [], "free_text": None, "skipped": True})["profile_version"])
    assert versions == [2, 3, 4, 5]
    history = profile(user)["history"]
    assert [h["version"] for h in history] == [5, 4, 3, 2, 1]
    assert [h["cause"] for h in history[:4]] == [{"type": "feedback", "decision_id": card["decision_id"], "flag_id": None, "listing_id": None}] * 4
    assert history[4]["cause"]["type"] == "swipe"


def test_profile_factors_follow_the_feedback_and_match_the_unit_function(user):
    cards = get_deck(user, 3)["cards"]
    for card in cards:
        swipe_ok(user, card["decision_id"], "left")
    first, second, third = cards
    shared = first["chips"][0]["chip_id"]
    put_ok(user, first["decision_id"], {"chips": [answer(shared, "must_have", "Big")], "free_text": "The kitchen felt dated"})
    put_ok(user, second["decision_id"], {"chips": [answer(second["chips"][1]["chip_id"], "deal_breaker")], "free_text": None})
    put_ok(user, third["decision_id"], {"chips": [], "free_text": None, "skipped": True})
    body = profile(user)
    assert body["version"] == 6 and body["factors"]
    rows = []
    stored = {d["decision_id"]: d for d in stored_rows(user, "decisions")}
    for f in stored_rows(user, "feedback"):
        rows.append({"offered": json.loads(stored[f["decision_id"]]["offered_chips"]), "chips": json.loads(f["chips_json"]),
                     "free_text": f["free_text"], "skipped": bool(f["skipped"]), "updated_at": f["updated_at"]})
    assert body["factors"] == taste.compute_factors(rows)
    names = {f["factor"] for f in body["factors"]}
    assert shared in names and names <= set(ALL_CHIPS)
    assert all(set(f) == {"factor", "direction", "weight"} and 0 < f["weight"] < 1 for f in body["factors"])


def test_a_skip_leaves_factors_as_they_were(user):
    first, second = get_deck(user, 2)["cards"]
    for card in (first, second):
        swipe_ok(user, card["decision_id"], "right")
    chip = first["chips"][0]["chip_id"]
    put_ok(user, first["decision_id"], {"chips": [answer(chip)], "free_text": None})
    before = profile(user)["factors"]
    put_ok(user, second["decision_id"], {"chips": [], "free_text": None, "skipped": True})
    assert profile(user)["factors"] == before and before
