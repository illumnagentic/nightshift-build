"""Client for Gemini's native generateContent API through the Mubit gateway.

The app sends only the Mubit key. Every Mubit answer carries x-middleware-request-id,
the only link from our rows back to the call on Mubit's Requests page.
"""
import json
from dataclasses import dataclass

GEMINI_BASE = "https://api.mubit.ai/gemini"
REQUEST_ID_HEADER = "x-middleware-request-id"
GATEWAY_ERROR_TYPES = ("middleware_gateway_error", "middleware_error")


@dataclass
class MubitResult:
    data: dict
    request_id: str | None


class MubitError(Exception):
    def __init__(self, status: int, request_id: str | None, gateway: bool, code: str | None, message: str):
        super().__init__(f"Mubit call failed: status={status} request_id={request_id} "
                         f"{'gateway' if gateway else 'provider'} code={code} message={message}")
        self.status, self.request_id, self.gateway, self.code, self.message = status, request_id, gateway, code, message


def build_request(api_key: str, model: str, body: dict, base: str = GEMINI_BASE) -> tuple[str, dict, str]:
    url = f"{base}/v1beta/models/{model}:generateContent"
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
    return url, headers, json.dumps(body)


def parse_response(status: int, headers, text: str) -> MubitResult:
    request_id = next((v for k, v in headers.items() if k.lower() == REQUEST_ID_HEADER), None)
    try:
        data = json.loads(text)
    except ValueError:
        data = None
    if 200 <= status < 300 and isinstance(data, dict):
        return MubitResult(data, request_id)
    error = data.get("error") if isinstance(data, dict) else None
    if not isinstance(error, dict):
        error = {}
    # Gemini puts the Mubit code in the ErrorInfo detail's "reason"; OpenAI-style bodies carry "code".
    code, err_type = error.get("code") if isinstance(error.get("code"), str) else None, error.get("type")
    for detail in error.get("details") or []:
        if isinstance(detail, dict):
            code = code or detail.get("reason")
            err_type = err_type or (detail.get("metadata") or {}).get("type")
    message = error.get("message") or text[:200]
    raise MubitError(status, request_id, err_type in GATEWAY_ERROR_TYPES, code, message)


async def generate_content(api_key: str, model: str, body: dict, base: str = GEMINI_BASE) -> MubitResult:
    from workers import fetch  # only exists inside the Workers runtime

    url, headers, payload = build_request(api_key, model, body, base)
    response = await fetch(url, method="POST", headers=headers, body=payload)
    # Only this header is read, via .get(), which works on the runtime's Headers object.
    request_id = response.headers.get(REQUEST_ID_HEADER)
    return parse_response(response.status, {REQUEST_ID_HEADER: request_id} if request_id else {}, await response.text())
