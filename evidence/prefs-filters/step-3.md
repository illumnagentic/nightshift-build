# TfL commute, cached and batched per poll

Date: 2026-10-24. Metadata only. No keys.

## Test mode

The dev server runs with the fake key and both upstream bases on the fake in the pytest
process (port 8799, one server for Gemini and TfL):

```
worker/scripts/seed.sh
cd worker
nohup setsid uvx --from workers-py pywrangler dev --port 8788 --inspector-port 9239 \
  --var MUBIT_API_KEY:test-key-not-a-real-key --var GEMINI_BASE:http://127.0.0.1:8799 \
  --var TFL_BASE:http://127.0.0.1:8799 > dev.log 2>&1 &
BASE_URL=http://localhost:8788 uv run --group dev pytest tests -q
```

The guard probe now also does one `GET /api/prefs` and stops the run unless the fake saw a
TfL request, so a server started without `TFL_BASE` is caught after its first batch.

## Results

- Full suite, three consecutive runs against one seeded database: 171 passed each time
  (7.3 s), then a fourth with exit 0.
- Unit modules alone, no server (`test_filters.py`, `test_prefs_unit.py`, `test_mubit.py`):
  97 passed, exit 0.

The prefs tests save `EC2N 2DB` and `SW1A 1AA`. The fake answers those two with 500 so
their commute stays pending and nothing is cached, however often the suite runs without
re-seeding. The commute tests use a random inward code per test for the same reason.

## Pilot against real TfL

Postcode EC2N 2DB, no key, through `pywrangler dev` (fake Gemini only, fake Mubit key, no
`TFL_BASE`, so the app used `https://api.tfl.gov.uk`). Pref text "two bed flat under 550k",
which the fake parses to a pool of 96 listings.

- Pool: 96 listings with coordinates passing the other hard filters.
- First run (batch of 12, concurrency 6): polls 1 to 5 took 3.4, 4.2, 5.2, 3.7 and 1.6 s and
  cached 54 results. Polls 6 to 8 took about 0.15 s each and cached nothing: TfL answered
  429. With the first version of the fail streak, three such polls ended `failed`.
- A direct curl then confirmed the block: HTTP 429, `Retry-After: 31`, body
  `{"message":...}` from Cloudflare. About 30 s later the same request returned 200.
- Rate-limit headers: none on 200 or 429 except `Retry-After` on 429. No `x-rate-limit-*`.
- Limit: 54 calls in about 17 s tripped it (about 190 per minute). A separate sequential
  run of 70 calls over 95 s (about 45 per minute) saw no 429. Exact limit not measured.
- A Python `urllib` default User-Agent gets Cloudflare error 1010 from TfL; the Workers
  `fetch` and curl are not blocked.
- Change made after the pilot: a batch that caches nothing and hit a 429 does not add to
  the fail streak. Second run on the same user data (54 already cached): polls took 3.4,
  3.6, 4.5 and 2.6 s and the status went `ready` on poll 4 (42 remaining: 12, 12, 12, 6).
- Result rows after both runs: 96 cached, 2 with null minutes (TfL had no journey), the
  rest 24 to 122 minutes, mean 50.
- TfL calls in total for the pilot and probing: about 200.

## Postcode that does not exist

Direct curl, `ZZ999ZZ` (well-formed, not real), from central London coordinates: HTTP 300
with a `DisambiguationResult` body (`toLocationDisambiguation`), not a 4xx. The classifier
treats 300 as transient, so such a postcode ends `failed` after three polls with no
mapping needed. No 4xx short-cut was added.
