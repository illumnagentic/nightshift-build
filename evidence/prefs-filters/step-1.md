# Prefs round trip, parser call and test seam

Date: 2026-10-24. Metadata only. No keys.

## Test mode

The dev server runs against a fake Mubit route, never the real gateway. The fake lives in
`worker/tests/fake_upstream.py` and runs inside the pytest process on 127.0.0.1:8799.

Two Worker vars are injected on the command line:

- `MUBIT_API_KEY` is set to the fake key `test-key-not-a-real-key`.
- `GEMINI_BASE` is set to `http://127.0.0.1:8799`.

`wrangler dev --var` is used rather than `--env-file` or `-e test`. Wrangler 4.152.0 still
prints "Using secrets defined in .dev.vars" in this mode, so the precedence was checked
rather than assumed: a probe run with the real `worker/.dev.vars` present showed the key
that reached the fake matched the fake key and did not match the real one (compared by
hash prefix, nothing printed). So `--var` wins over `.dev.vars` in this version. The fake
also returns 401 for any other key and the suite ends with a test that every key it
received was the fake key. No test vars file exists, so nothing new is gitignored.

Commands, from the repo root:

```
worker/scripts/seed.sh
cd worker
nohup setsid uvx --from workers-py pywrangler dev --port 8788 --inspector-port 9239 \
  --var MUBIT_API_KEY:test-key-not-a-real-key --var GEMINI_BASE:http://127.0.0.1:8799 \
  > dev.log 2>&1 &
BASE_URL=http://localhost:8788 uv run --group dev pytest tests -q
```

Stop the server by its PID (and its child processes) afterwards, and stop it before
re-seeding. A port other than 8787 was used because an older dev server was already
running.

## Results

- Full suite against the test-mode server: 128 passed, exit 0.
- After adding a base-URL test to `test_mubit.py`: `tests/test_mubit.py` and
  `tests/test_prefs_unit.py` alone, 64 passed, exit 0.
- The row stored after a save has `commute_status` pending, fail streak 0, the parser's
  request id in `parse_request_id` and `max_commute_min` copied from the request.

## Workers fetch path

`mubit.generate_content` uses the Workers runtime `fetch`. Under `pywrangler dev` it
reached the fake on every PUT, with path
`/v1beta/models/gemini-3.8-flash:generateContent`, the `x-goog-api-key` header and the
user's text as the only user message. The `x-middleware-request-id` header the fake sets
was read back and stored. This closes the earlier gap that the fetch wrapper had never run
against anything.

## Live parser call

One call, through the real gateway with the real key, from a stdlib script that reuses
`prefs.build_parse_body`, `mubit.build_request`, `mubit.parse_response` and
`prefs.parse_reply`. It is not saved in the repo. Run from the repo root as
`python3 -I <script>`; it reads `MUBIT_API_KEY` from the root `.env`, as
`worker/scripts/mubit_ping.py` does.

- Input text: the contract example, "Two bed flat under 550k, near a tube station, bright
  rooms, no ground floor."
- status 200, no retry needed
- modelVersion `gemini-3.8-flash`
- promptTokenCount 404, candidatesTokenCount 63, totalTokenCount 467, no thought tokens
  reported
- request id `mreq_01a16f66b9fb7ec3bfd4836b56681a41`
- parsed, with `max_commute_min` 45 passed in as the request value:

```
hard: max_price_gbp 550000, min_bedrooms 2, property_types ["flat"], min_epc null,
      tenure null, min_lease_years null, max_commute_min 45
soft: ["near a tube station", "bright rooms", "no ground floor"]
```

Observation: the model did not add `maisonette`, which the contract example shows. "No
ground floor" went to `soft`, as there is no hard field for floor level.

## Ruling follow-through

- 502 `parse_failed` for a Mubit error, non-2xx, non-JSON body, reply with no candidate
  text, reply text that is not JSON, and reply that is not an object. Prefs unchanged in
  each case; tested.
- Unusable output from the model is checked per field in `worker/src/prefs.py`; any
  invalid value becomes null.
