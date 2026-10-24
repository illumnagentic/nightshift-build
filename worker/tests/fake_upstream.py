"""A stand-in for the Mubit Gemini route, so tests never reach the real gateway.

The answer is chosen by a marker in the user's text, e.g. "[[bad_values]]". It refuses any
key other than FAKE_KEY, so a real key sent by mistake shows up as a 401 and a recorded request.
"""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

FAKE_KEY = "test-key-not-a-real-key"
FAKE_REQUEST_ID = "mreq_fake0000000000000000000000000001"

GOOD = {
    "hard": {"max_price_gbp": 550000, "min_bedrooms": 2, "property_types": ["flat", "maisonette"],
             "min_epc": "D", "tenure": None, "min_lease_years": None},
    "soft": ["near a tube station", "bright rooms", "not on the ground floor"],
}
BAD_VALUES = {
    "hard": {"max_price_gbp": 5, "min_bedrooms": True, "property_types": ["flat", "castle", "flat"],
             "min_epc": "H", "tenure": "commonhold", "min_lease_years": "99"},
    "soft": ["  quiet street  ", "", 5, "x" * 121],
}


def _wrap(text) -> dict:
    return {"modelVersion": "fake-model", "candidates": [{"content": {"role": "model", "parts": [{"text": text}]}}]}


def answer_for(user_text: str) -> tuple[int, str]:
    """(status, body) for the marker in the user's text."""
    if "[[http_500]]" in user_text:
        return 500, json.dumps({"error": {"code": 500, "message": "upstream broke", "status": "INTERNAL"}})
    if "[[not_json_body]]" in user_text:
        return 200, "<html>not json</html>"
    if "[[no_candidates]]" in user_text:
        return 200, json.dumps({"modelVersion": "fake-model", "candidates": []})
    if "[[reply_not_json]]" in user_text:
        return 200, json.dumps(_wrap("this is not json"))
    if "[[reply_not_object]]" in user_text:
        return 200, json.dumps(_wrap("[1, 2]"))
    if "[[bad_values]]" in user_text:
        return 200, json.dumps(_wrap(json.dumps(BAD_VALUES)))
    return 200, json.dumps(_wrap(json.dumps(GOOD)))


class FakeUpstream(HTTPServer):
    def __init__(self, port: int):
        super().__init__(("127.0.0.1", port), _Handler)
        self.requests: list[dict] = []  # one per call: path, key, body

    def start(self) -> None:
        threading.Thread(target=self.serve_forever, daemon=True).start()

    def stop(self) -> None:
        self.shutdown()
        self.server_close()


class _Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        key = self.headers.get("x-goog-api-key")
        self.server.requests.append({"path": self.path, "key": key, "body": body})
        if key != FAKE_KEY:
            status, text = 401, json.dumps({"error": {"type": "middleware_gateway_error", "code": "invalid_key", "message": "bad key"}})
        else:
            status, text = answer_for(body["contents"][0]["parts"][0]["text"])
        payload = text.encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("x-middleware-request-id", FAKE_REQUEST_ID)
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass
