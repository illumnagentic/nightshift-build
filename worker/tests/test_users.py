"""Black-box tests for /api/users against a running `pywrangler dev`."""
import json
import os
import secrets
import urllib.error
import urllib.request

import pytest

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8787").rstrip("/")


def call(method, path, raw=None, body=None):
    """Return (status, parsed JSON). `raw` sends bytes as given; `body` is JSON-encoded."""
    data = raw if raw is not None else (None if body is None else json.dumps(body).encode())
    req = urllib.request.Request(
        BASE_URL + path, data=data, method=method, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.load(resp)
    except urllib.error.HTTPError as err:
        return err.code, json.load(err)
    except urllib.error.URLError as err:
        pytest.fail(f"Backend not reachable at {BASE_URL}: {err.reason}. Start `pywrangler dev` in worker/.")


def name():
    return "t_" + secrets.token_hex(6)


def assert_error(status, payload, expected_status, code):
    assert status == expected_status
    assert set(payload) == {"error"}
    assert set(payload["error"]) == {"code", "message"}
    assert payload["error"]["code"] == code
    assert isinstance(payload["error"]["message"], str) and payload["error"]["message"]


def test_create_returns_201_and_lists():
    username = name()
    status, created = call("POST", "/api/users", body={"username": username})
    assert status == 201
    assert set(created) == {"user_id", "username"}
    assert created["username"] == username
    assert isinstance(created["user_id"], str) and created["user_id"]

    status, listing = call("GET", "/api/users")
    assert status == 200
    assert {"user_id": created["user_id"], "username": username} in listing["users"]


def test_username_is_trimmed():
    username = name()
    status, created = call("POST", "/api/users", body={"username": f"  {username}\t"})
    assert status == 201
    assert created["username"] == username


def test_user_ids_are_distinct():
    _, a = call("POST", "/api/users", body={"username": name()})
    _, b = call("POST", "/api/users", body={"username": name()})
    assert a["user_id"] != b["user_id"]


def test_list_is_in_creation_order():
    first, second = name(), name()
    call("POST", "/api/users", body={"username": first})
    call("POST", "/api/users", body={"username": second})
    _, listing = call("GET", "/api/users")
    names = [u["username"] for u in listing["users"]]
    assert names.index(first) < names.index(second)


@pytest.mark.parametrize("variant", [str.upper, str.lower, str.swapcase, lambda s: f" {s} "])
def test_duplicate_is_409_ignoring_case(variant):
    username = name()
    assert call("POST", "/api/users", body={"username": username})[0] == 201
    status, payload = call("POST", "/api/users", body={"username": variant(username)})
    assert_error(status, payload, 409, "username_taken")


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"username": ""},
        {"username": "   "},
        {"username": "a" * 33},
        {"username": "has space"},
        {"username": "bad!char"},
        {"username": "café"},
        {"username": 123},
        {"username": None},
        {"username": ["a"]},
        ["alex"],
        "alex",
    ],
)
def test_invalid_body_is_422(body):
    status, payload = call("POST", "/api/users", body=body)
    assert_error(status, payload, 422, "invalid_request")


@pytest.mark.parametrize("raw", [b"{not json", b"", b'{"username": '])
def test_malformed_json_is_422(raw):
    status, payload = call("POST", "/api/users", raw=raw)
    assert_error(status, payload, 422, "invalid_request")


def test_length_boundaries_accepted():
    assert call("POST", "/api/users", body={"username": "a" + secrets.token_hex(16)[:31]})[0] == 201
    assert call("POST", "/api/users", body={"username": "A-_" + secrets.token_hex(4)})[0] == 201


def test_unknown_path_is_404_contract_shape():
    status, payload = call("GET", "/api/nope")
    assert_error(status, payload, 404, "not_found")


def test_wrong_method_is_405_contract_shape():
    status, payload = call("DELETE", "/api/users")
    assert_error(status, payload, 405, "method_not_allowed")
