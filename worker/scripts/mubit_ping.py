"""One live call to gemini-3.8-flash through Mubit. Prints metadata only, never the key or the reply text."""
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import mubit  # noqa: E402

env_file = Path(__file__).resolve().parents[2] / ".env"
env = dict(line.split("=", 1) for line in env_file.read_text().splitlines() if "=" in line and not line.startswith("#"))
api_key = env["MUBIT_API_KEY"].strip().strip("\"'")

body = {
    "contents": [{"role": "user", "parts": [{"text": "Reply with the single word OK."}]}],
    "generationConfig": {"thinkingConfig": {"thinkingLevel": "low"}},
}
url, headers, payload = mubit.build_request(api_key, "gemini-3.8-flash", body)
request = urllib.request.Request(url, data=payload.encode(), headers=headers, method="POST")
try:
    with urllib.request.urlopen(request, timeout=60) as response:
        status, response_headers, text = response.status, dict(response.headers), response.read().decode()
except urllib.error.HTTPError as exc:
    status, response_headers, text = exc.code, dict(exc.headers), exc.read().decode()

try:
    result = mubit.parse_response(status, response_headers, text)
except mubit.MubitError as exc:
    print(f"status={exc.status} request_id={exc.request_id} gateway={exc.gateway} code={exc.code} message={exc.message}")
    sys.exit(1)

usage = result.data.get("usageMetadata", {})
print(f"status={status}")
print(f"modelVersion={result.data.get('modelVersion')}")
print(f"promptTokenCount={usage.get('promptTokenCount')}")
print(f"candidatesTokenCount={usage.get('candidatesTokenCount')}")
print(f"thoughtsTokenCount={usage.get('thoughtsTokenCount')}")
print(f"request_id={result.request_id}")
