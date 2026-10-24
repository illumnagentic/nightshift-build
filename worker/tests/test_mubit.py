import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import mubit  # noqa: E402

KEY = "mbt_secretkey123"
RID = "mreq_01a16b49bb7479d1aa83b7df659a7740"


def test_build_request_url_headers_body():
    url, headers, body = mubit.build_request(KEY, "gemini-3.8-flash", {"contents": []})
    assert url == "https://api.mubit.ai/gemini/v1beta/models/gemini-3.8-flash:generateContent"
    assert "?" not in url and "key=" not in url
    assert headers == {"x-goog-api-key": KEY, "Content-Type": "application/json"}
    assert json.loads(body) == {"contents": []}


@pytest.mark.parametrize("name", ["x-middleware-request-id", "X-Middleware-Request-Id", "X-MIDDLEWARE-REQUEST-ID"])
def test_success_parse_and_request_id_any_case(name):
    result = mubit.parse_response(200, {name: RID, "content-type": "application/json"}, '{"modelVersion": "m"}')
    assert result.data == {"modelVersion": "m"}
    assert result.request_id == RID


def test_success_without_request_id():
    assert mubit.parse_response(200, {}, "{}").request_id is None


def test_gateway_error_openai_style_body():
    body = json.dumps({"error": {"type": "middleware_gateway_error", "code": "invalid_key", "message": "bad key"}})
    with pytest.raises(mubit.MubitError) as info:
        mubit.parse_response(401, {"x-middleware-request-id": RID}, body)
    err = info.value
    assert (err.status, err.request_id, err.gateway, err.code, err.message) == (401, RID, True, "invalid_key", "bad key")


def test_gateway_error_gemini_style_body():
    body = json.dumps({"error": {"code": 403, "message": "no key", "status": "PERMISSION_DENIED", "details": [
        {"@type": "type.googleapis.com/google.rpc.ErrorInfo", "reason": "provider_key_missing",
         "metadata": {"type": "middleware_gateway_error"}}]}})
    with pytest.raises(mubit.MubitError) as info:
        mubit.parse_response(403, {"x-middleware-request-id": RID}, body)
    assert info.value.gateway is True
    assert info.value.code == "provider_key_missing"


def test_provider_error():
    body = json.dumps({"error": {"code": 400, "message": "API key not valid", "status": "INVALID_ARGUMENT"}})
    with pytest.raises(mubit.MubitError) as info:
        mubit.parse_response(400, {"X-Middleware-Request-Id": RID}, body)
    err = info.value
    assert (err.status, err.request_id, err.gateway, err.code) == (400, RID, False, None)
    assert err.message == "API key not valid"


def test_error_missing_request_id_and_non_json_body():
    with pytest.raises(mubit.MubitError) as info:
        mubit.parse_response(502, {}, "<html>bad gateway</html>")
    assert info.value.request_id is None
    assert info.value.gateway is False
    assert "bad gateway" in info.value.message


def test_key_never_in_error():
    # An echoed key in a provider message is not ours to scrub, but our own text must not add it.
    body = json.dumps({"error": {"type": "middleware_gateway_error", "code": "invalid_key", "message": "bad key"}})
    with pytest.raises(mubit.MubitError) as info:
        mubit.parse_response(401, {}, body)
    assert KEY not in str(info.value)
    assert KEY not in repr(info.value)
