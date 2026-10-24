"""Shared helpers and the fake upstream for the API tests that run against `pywrangler dev`.

Unit test modules do not use the `fake` fixture and run without any server.
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

NOT_IN_TEST_MODE = (
    f"The server at {BASE_URL} is not in test mode: the probe PUT /api/prefs did not reach the fake "
    f"upstream on port {FAKE_PORT} with the fake key. Stopping before any other test runs. "
    f"Start it as: pywrangler dev --var MUBIT_API_KEY:{FAKE_KEY} --var GEMINI_BASE:http://127.0.0.1:{FAKE_PORT}"
)


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


@pytest.fixture(scope="session")
def fake():
    server = FakeUpstream(FAKE_PORT)
    server.start()
    try:
        _probe(server)
        yield server
    finally:
        server.stop()


def _probe(server):
    """One PUT /api/prefs. If the fake did not record exactly it, with the fake key, stop the run."""
    try:
        status, created = call("POST", "/api/users", body={"username": "probe_" + secrets.token_hex(6)})
        if status != 201:
            pytest.exit(NOT_IN_TEST_MODE, returncode=3)
        status, _ = call("PUT", "/api/prefs", user_id=created["user_id"], body={"text": "any flat", "commute_postcode": "EC2N 2DB"})
    except pytest.fail.Exception:
        pytest.exit(NOT_IN_TEST_MODE, returncode=3)
    if status != 200 or len(server.requests) != 1 or server.requests[0]["key"] != FAKE_KEY:
        pytest.exit(NOT_IN_TEST_MODE, returncode=3)
