"""A stand-in for the Mubit Gemini route and the TfL Journey Planner, so tests never reach either.

TfL behaviour is chosen by the outward code of the destination postcode: E1 has no journey (404),
N1, EC2N and SW1A always answer 500, N7 always answers 300 (what TfL says for a postcode that does not exist),
a journey from any start in FAILING_STARTS answers 500, W1 always answers 429, SE1 answers 503 and SW1 answers 429 once per journey and then succeeds,
anything else gets a journey.
DESTINATION_STATUS maps a compact destination postcode (e.g. "EC1A1BB") to a status that every journey to it
answers with body {}; it is checked first, so a test can start and end an outage on a postcode it chose. EC2N and SW1A are the postcodes the prefs tests save: failing them keeps their
commute pending, and caches nothing, however often the suite is run against one database.
Both routes are served on one port.

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
# (lat, lon) of listings whose journeys always answer 500, whatever the postcode. Tests fill and clear it.
FAILING_STARTS: set[tuple[float, float]] = set()
# Compact destination postcode to the status every journey to it answers with. Tests fill and clear it.
DESTINATION_STATUS: dict[str, int] = {}
BAD_VALUES = {
    "hard": {"max_price_gbp": 5, "min_bedrooms": True, "property_types": ["flat", "castle", "flat"],
             "min_epc": "H", "tenure": "commonhold", "min_lease_years": "99"},
    "soft": ["  quiet street  ", "", 5, "x" * 121],
}


TIGHT = {"hard": {**GOOD["hard"], "max_price_gbp": 300000}, "soft": []}


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
    if "[[tight]]" in user_text:
        return 200, json.dumps(_wrap(json.dumps(TIGHT)))
    if "[[bad_values]]" in user_text:
        return 200, json.dumps(_wrap(json.dumps(BAD_VALUES)))
    return 200, json.dumps(_wrap(json.dumps(GOOD)))


class FakeUpstream(HTTPServer):
    def __init__(self, port: int):
        super().__init__(("127.0.0.1", port), _Handler)
        self.requests: list[dict] = []  # one per Gemini call: path, key, body
        self.tfl_requests: list[str] = []  # one per TfL call: the request path and query
        self._tfl_seen: set[str] = set()

    def start(self) -> None:
        threading.Thread(target=self.serve_forever, daemon=True).start()

    def stop(self) -> None:
        self.shutdown()
        self.server_close()


def tfl_answer(path: str, first_time: bool) -> tuple[int, str]:
    """(status, body) for a TfL journey request. Minutes come from the start latitude, so they are stable."""
    start, destination = path.split("?")[0].split("/JourneyResults/")[1].split("/to/")
    outward = destination[:-3]
    if destination in DESTINATION_STATUS:
        return DESTINATION_STATUS[destination], "{}"
    if outward == "E1":
        return 404, json.dumps({"message": "no journey"})
    if outward in ("N1", "EC2N", "SW1A"):
        return 500, "{}"
    if outward == "N7":
        return 300, "{}"
    if tuple(float(v) for v in start.split(",")) in FAILING_STARTS:
        return 500, "{}"
    if outward == "W1":
        return 429, "{}"
    if first_time and outward in ("SE1", "SW1"):
        return (503 if outward == "SE1" else 429), "{}"
    return 200, json.dumps({"journeys": [{"duration": 90}, {"duration": fake_minutes(start)}]})


def fake_minutes(start: str) -> int:
    return 25 + int(abs(float(start.split(",")[0])) * 10000) % 30


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.server.tfl_requests.append(self.path)
        first_time = self.path not in self.server._tfl_seen
        self.server._tfl_seen.add(self.path)
        status, text = tfl_answer(self.path, first_time) if "/JourneyResults/" in self.path else (404, "{}")
        payload = text.encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

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
