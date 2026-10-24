"""Black-box tests for /api/prefs against `pywrangler dev` in test mode (see worker/README.md).

The server must point at the fake upstream: GEMINI_BASE=http://127.0.0.1:FAKE_PORT and the
fake key as MUBIT_API_KEY. The fake runs inside this test process.
"""
import json
import os
import secrets
import urllib.error
import urllib.request

import pytest

from fake_upstream import FAKE_KEY, FakeUpstream

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8787").rstrip("/")
FAKE_PORT = int(os.environ.get("FAKE_PORT", "8799"))


def call(method, path, user_id=None, body=None, raw=None):
    headers = {"Content-Type": "application/json"}
    if user_id is not None:
        headers["X-User-Id"] = user_id
    data = raw if raw is not None else (None if body is None else json.dumps(body).encode())
    req = urllib.request.Request(BASE_URL + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, json.load(resp)
    except urllib.error.HTTPError as err:
        return err.code, json.load(err)
    except urllib.error.URLError as err:
        pytest.fail(f"Backend not reachable at {BASE_URL}: {err.reason}. Start `pywrangler dev` in test mode.")


def assert_error(status, payload, expected_status, code):
    assert status == expected_status
    assert set(payload) == {"error"}
    assert set(payload["error"]) == {"code", "message"}
    assert payload["error"]["code"] == code
    assert isinstance(payload["error"]["message"], str) and payload["error"]["message"]


@pytest.fixture(scope="module")
def fake():
    server = FakeUpstream(FAKE_PORT)
    server.start()
    yield server
    server.stop()


@pytest.fixture
def user(fake):
    status, created = call("POST", "/api/users", body={"username": "t_" + secrets.token_hex(6)})
    assert status == 201
    return created["user_id"]


ALL_NULL = {"text": None, "commute_postcode": None, "max_commute_min": None, "parsed": None, "commute_status": None}
TEXT = "Two bed flat under 550k, near a tube station, bright rooms, no ground floor."


def test_missing_header_is_401():
    for method, body in (("GET", None), ("PUT", {"text": TEXT, "commute_postcode": "EC2N 2DB"})):
        assert_error(*call(method, "/api/prefs", body=body), 401, "unknown_user")


@pytest.mark.parametrize("header", ["", "u_doesnotexist", "' OR 1=1 --"])
def test_empty_or_unknown_header_is_401(header):
    assert_error(*call("GET", "/api/prefs", user_id=header), 401, "unknown_user")
    assert_error(*call("PUT", "/api/prefs", user_id=header, body={"text": TEXT, "commute_postcode": "EC2N 2DB"}), 401, "unknown_user")


def test_never_saved_is_all_null(user):
    assert call("GET", "/api/prefs", user_id=user) == (200, ALL_NULL)


def test_put_happy_path_and_get(user, fake):
    before = len(fake.requests)
    status, saved = call("PUT", "/api/prefs", user_id=user, body={"text": TEXT, "commute_postcode": "ec2n2db", "max_commute_min": 45})
    assert status == 200
    assert saved == {
        "text": TEXT,
        "commute_postcode": "EC2N 2DB",
        "max_commute_min": 45,
        "parsed": {
            "hard": {"max_price_gbp": 550000, "min_bedrooms": 2, "property_types": ["flat", "maisonette"], "min_epc": "D",
                     "tenure": None, "min_lease_years": None, "max_commute_min": 45},
            "soft": ["near a tube station", "bright rooms", "not on the ground floor"],
        },
        "commute_status": "pending",
    }
    assert call("GET", "/api/prefs", user_id=user) == (200, saved)

    # The call went through the Workers fetch in mubit.py, to the fake, with only the fake key.
    sent = fake.requests[before:]
    assert len(sent) == 1
    assert sent[0]["path"] == "/v1beta/models/gemini-3.8-flash:generateContent"
    assert sent[0]["key"] == FAKE_KEY
    assert sent[0]["body"]["contents"][0]["parts"][0]["text"] == TEXT
    assert TEXT not in json.dumps(sent[0]["body"]["systemInstruction"])


def test_max_commute_is_optional_and_null_allowed(user):
    for body in ({"text": TEXT, "commute_postcode": "EC2N 2DB"}, {"text": TEXT, "commute_postcode": "EC2N 2DB", "max_commute_min": None}):
        status, saved = call("PUT", "/api/prefs", user_id=user, body=body)
        assert status == 200
        assert saved["max_commute_min"] is None
        assert saved["parsed"]["hard"]["max_commute_min"] is None


def test_max_commute_boundaries_accepted(user):
    for value in (1, 180):
        status, saved = call("PUT", "/api/prefs", user_id=user, body={"text": TEXT, "commute_postcode": "EC2N 2DB", "max_commute_min": value})
        assert status == 200 and saved["max_commute_min"] == value


def test_resave_replaces(user):
    call("PUT", "/api/prefs", user_id=user, body={"text": TEXT, "commute_postcode": "EC2N 2DB", "max_commute_min": 45})
    second = {"text": "Any house you like", "commute_postcode": "SW1A 1AA"}
    status, saved = call("PUT", "/api/prefs", user_id=user, body=second)
    assert status == 200
    assert call("GET", "/api/prefs", user_id=user) == (200, saved)
    assert saved["text"] == "Any house you like" and saved["commute_postcode"] == "SW1A 1AA" and saved["max_commute_min"] is None


def test_prefs_are_per_user(user):
    _, other = call("POST", "/api/users", body={"username": "t_" + secrets.token_hex(6)})
    call("PUT", "/api/prefs", user_id=user, body={"text": TEXT, "commute_postcode": "EC2N 2DB"})
    assert call("GET", "/api/prefs", user_id=other["user_id"]) == (200, ALL_NULL)


@pytest.mark.parametrize("postcode", ["Liverpool Street", "EC2N", "EC2N 2D", "", "   "])
def test_invalid_postcode_is_422(user, postcode):
    status, payload = call("PUT", "/api/prefs", user_id=user, body={"text": TEXT, "commute_postcode": postcode})
    assert_error(status, payload, 422, "invalid_postcode")


@pytest.mark.parametrize("body", [
    {"commute_postcode": "EC2N 2DB"},
    {"text": "", "commute_postcode": "EC2N 2DB"},
    {"text": "   \n", "commute_postcode": "EC2N 2DB"},
    {"text": None, "commute_postcode": "EC2N 2DB"},
    {"text": 5, "commute_postcode": "EC2N 2DB"},
    {"text": TEXT},
    {"text": TEXT, "commute_postcode": None},
    {"text": TEXT, "commute_postcode": 12345},
    {"text": TEXT, "commute_postcode": "EC2N 2DB", "max_commute_min": 0},
    {"text": TEXT, "commute_postcode": "EC2N 2DB", "max_commute_min": 181},
    {"text": TEXT, "commute_postcode": "EC2N 2DB", "max_commute_min": -5},
    {"text": TEXT, "commute_postcode": "EC2N 2DB", "max_commute_min": True},
    {"text": TEXT, "commute_postcode": "EC2N 2DB", "max_commute_min": "45"},
    {"text": TEXT, "commute_postcode": "EC2N 2DB", "max_commute_min": 45.5},
    ["not", "an", "object"],
])
def test_invalid_request_is_422_and_never_calls_the_parser(user, fake, body):
    before = len(fake.requests)
    status, payload = call("PUT", "/api/prefs", user_id=user, body=body)
    assert_error(status, payload, 422, "invalid_request")
    assert len(fake.requests) == before
    assert call("GET", "/api/prefs", user_id=user) == (200, ALL_NULL)


def test_malformed_json_is_422(user):
    assert_error(*call("PUT", "/api/prefs", user_id=user, raw=b"{nope"), 422, "invalid_request")


def test_bad_llm_values_are_stored_as_null(user):
    status, saved = call("PUT", "/api/prefs", user_id=user, body={"text": "[[bad_values]] odd flat", "commute_postcode": "EC2N 2DB"})
    assert status == 200
    assert saved["parsed"] == {
        "hard": {"max_price_gbp": None, "min_bedrooms": None, "property_types": ["flat"], "min_epc": None,
                 "tenure": None, "min_lease_years": None, "max_commute_min": None},
        "soft": ["quiet street"],
    }
    assert call("GET", "/api/prefs", user_id=user) == (200, saved)


@pytest.mark.parametrize("marker", ["http_500", "not_json_body", "no_candidates", "reply_not_json", "reply_not_object"])
def test_parser_failure_is_502_and_prefs_unchanged(user, marker):
    first_status, first = call("PUT", "/api/prefs", user_id=user, body={"text": TEXT, "commute_postcode": "EC2N 2DB", "max_commute_min": 45})
    assert first_status == 200
    status, payload = call("PUT", "/api/prefs", user_id=user, body={"text": f"[[{marker}]] different", "commute_postcode": "SW1A 1AA"})
    assert_error(status, payload, 502, "parse_failed")
    assert call("GET", "/api/prefs", user_id=user) == (200, first)


def test_parser_failure_on_first_save_leaves_nothing(user):
    status, payload = call("PUT", "/api/prefs", user_id=user, body={"text": "[[http_500]]", "commute_postcode": "EC2N 2DB"})
    assert_error(status, payload, 502, "parse_failed")
    assert call("GET", "/api/prefs", user_id=user) == (200, ALL_NULL)


def test_only_the_fake_key_was_ever_sent(fake):
    assert fake.requests, "no request reached the fake: is the server in test mode?"
    assert {r["key"] for r in fake.requests} == {FAKE_KEY}
