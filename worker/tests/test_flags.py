"""Black-box tests for POST /api/flags/{flag_id}/correction and GET /api/listings/{id}, against `pywrangler dev` in
test mode (see worker/README.md). Expected values are read from the local D1. A correction is shared and stays in
the D1, so each test asserts on the text it has just written."""
import secrets

import pytest

from conftest import call
from test_deck import assert_error, get_deck, new_user, save, d1_rows
from test_swipe import profile, swipe_ok

# No test here may call the API before the fake fixture's probe has passed.
pytestmark = pytest.mark.usefixtures("fake")

FLAG_KEYS = {"flag_id", "scope", "field", "value", "observation", "source_photo", "confidence", "uncertainty", "room", "corrected_text"}
DETAIL_KEYS = {
    "id", "price_gbp", "price_qualifier", "bedrooms", "bathrooms", "property_type", "address", "postcode", "lat", "lon",
    "tenure", "epc_current", "floor_level", "key_features", "photos", "lease_years_remaining", "service_charge_gbp_pa",
    "ground_rent_gbp_pa", "council_tax_band", "epc_potential", "description", "agent_name", "listed_date", "floorplans",
    "stations", "photo_flags"}


@pytest.fixture
def user():
    uid = new_user()
    save(uid)
    return uid


def correct(user, flag_id, body):
    return call("POST", f"/api/flags/{flag_id}/correction", user_id=user, body=body)


def a_flag(split, field="defects"):
    """(flag_id, listing_id) of a stored flag on a listing in that split; a different one per call of the same field."""
    rows = d1_rows(f"SELECT f.flag_id, f.listing_id FROM photo_flags f JOIN listings l ON l.id = f.listing_id"
                   f" WHERE l.split = '{split}' AND f.field = '{field}' ORDER BY f.flag_id LIMIT 50")
    row = rows[secrets.randbelow(len(rows))]
    return row["flag_id"], row["listing_id"]


def stored_text(flag_id):
    return d1_rows(f"SELECT corrected_text FROM photo_flags WHERE flag_id = '{flag_id}'")[0]["corrected_text"]


def detail(user, listing_id):
    status, payload = call("GET", f"/api/listings/{listing_id}", user_id=user)
    assert status == 200, payload
    return payload


def new_text():
    return "Not damp, a shadow. " + secrets.token_hex(4)


def test_missing_user_is_401():
    assert_error(*call("POST", "/api/flags/x/correction", body={"text": "x"}), 401, "unknown_user")
    assert_error(*call("GET", "/api/listings/rm-1"), 401, "unknown_user")


@pytest.mark.parametrize("body", [{}, {"text": ""}, {"text": "   "}, {"text": None}, {"text": 5}, [], {"txt": "x"}])
def test_blank_or_missing_text_is_422_and_changes_nothing(user, body):
    flag_id, _ = a_flag("train")
    before = stored_text(flag_id)
    assert_error(*correct(user, flag_id, body), 422, "invalid_request")
    assert stored_text(flag_id) == before and profile(user)["version"] == 0


def test_no_body_is_422(user):
    flag_id, _ = a_flag("train")
    assert_error(*call("POST", f"/api/flags/{flag_id}/correction", user_id=user), 422, "invalid_request")


def test_unknown_flag_is_404_and_changes_nothing(user):
    assert_error(*correct(user, "rm-0:nothing:defects:0", {"text": "x"}), 404, "flag_not_found")
    assert profile(user)["version"] == 0


def test_flag_on_an_eval_listing_is_404_and_left_unchanged(user):
    flag_id, _ = a_flag("eval")
    before = stored_text(flag_id)
    assert_error(*correct(user, flag_id, {"text": new_text()}), 404, "flag_not_found")
    assert stored_text(flag_id) == before and profile(user)["version"] == 0


def test_correction_returns_the_flag_and_version_and_another_user_sees_it(user):
    flag_id, listing_id = a_flag("train")
    text = new_text()
    status, payload = correct(user, flag_id, {"text": f"  {text}  "})
    assert status == 200
    assert set(payload) == FLAG_KEYS | {"profile_version"}
    assert payload["flag_id"] == flag_id and payload["corrected_text"] == text and payload["profile_version"] == 1
    assert stored_text(flag_id) == text
    now = profile(user)
    assert now["version"] == 1
    assert now["history"][0]["cause"] == {"type": "flag_correction", "decision_id": None, "flag_id": flag_id, "listing_id": None}
    seen = {f["flag_id"]: f for f in detail(new_user(), listing_id)["photo_flags"]}
    assert seen[flag_id]["corrected_text"] == text


def test_latest_correction_wins_and_each_bumps_the_correcting_users_version(user):
    flag_id, listing_id = a_flag("train")
    first, second = new_text(), new_text()
    assert correct(user, flag_id, {"text": first})[1]["profile_version"] == 1
    other = new_user()
    assert correct(other, flag_id, {"text": second})[1]["profile_version"] == 1
    assert correct(user, flag_id, {"text": second})[1]["profile_version"] == 2
    assert stored_text(flag_id) == second


def test_listing_detail_has_every_contract_field_and_nothing_else(user):
    row = d1_rows("SELECT l.id FROM listings l WHERE l.split = 'train' AND l.id IN (SELECT listing_id FROM listing_media WHERE kind = 'floorplan')"
                  " AND l.id IN (SELECT listing_id FROM photo_flags WHERE field = 'sqm_estimate') ORDER BY l.id LIMIT 1")[0]
    listing_id = row["id"]
    payload = detail(user, listing_id)
    assert set(payload) == DETAIL_KEYS
    stored = d1_rows(f"SELECT * FROM listings WHERE id = '{listing_id}'")[0]
    for key in DETAIL_KEYS - {"key_features", "photos", "floorplans", "stations", "photo_flags"}:
        assert payload[key] == stored[key], key
    media = d1_rows(f"SELECT kind, url FROM listing_media WHERE listing_id = '{listing_id}' ORDER BY kind, position")
    assert payload["photos"] == [m["url"] for m in media if m["kind"] == "photo"]
    assert payload["floorplans"] == [m["url"] for m in media if m["kind"] == "floorplan"] and payload["floorplans"]
    stations = d1_rows(f"SELECT name, distance_km FROM listing_stations WHERE listing_id = '{listing_id}' ORDER BY position")
    assert [(s["name"], s["distance_km"]) for s in payload["stations"]] == [(s["name"], s["distance_km"]) for s in stations]
    for station in payload["stations"]:
        assert set(station) == {"name", "distance_km", "types"} and isinstance(station["types"], list)
    flags = d1_rows(f"SELECT * FROM photo_flags WHERE listing_id = '{listing_id}' ORDER BY rowid")
    assert [f["flag_id"] for f in payload["photo_flags"]] == [f["flag_id"] for f in flags]
    for flag, source in zip(payload["photo_flags"], flags):
        assert set(flag) == FLAG_KEYS
        assert all(flag[k] == source[k] for k in FLAG_KEYS)
    sqm = [f for f in payload["photo_flags"] if f["field"] == "sqm_estimate"]
    assert sqm and all(isinstance(f["value"], (int, float)) and not isinstance(f["value"], bool) for f in sqm)
    assert payload["listed_date"] is None or payload["listed_date"].endswith("Z")


def test_unknown_and_eval_listings_are_404(user):
    eval_id = d1_rows("SELECT id FROM listings WHERE split = 'eval' ORDER BY id LIMIT 1")[0]["id"]
    assert_error(*call("GET", f"/api/listings/{eval_id}", user_id=user), 404, "listing_not_found")
    assert_error(*call("GET", "/api/listings/rm-0", user_id=user), 404, "listing_not_found")


def test_a_favourited_listing_is_still_returned_after_a_prefs_resave(user):
    (card,) = get_deck(user, 1)["cards"]
    swipe_ok(user, card["decision_id"], "superlike")
    save(user)
    assert detail(user, card["listing"]["id"])["id"] == card["listing"]["id"]
