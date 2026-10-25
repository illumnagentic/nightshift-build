# Stored request id test

2026-10-25. Throwaway git worktree of HEAD (4d56dca) plus the three changed worker files, freshly seeded with
`worker/scripts/seed.sh`. Server started from that worktree's `worker/` directory (so the test's `wrangler d1 execute`
reads the same local D1): `pywrangler dev --port 8796 --inspector-port 9247` with the fake key and
`GEMINI_BASE` / `TFL_BASE` at `http://127.0.0.1:8805`. Run with `BASE_URL=http://localhost:8796 FAKE_PORT=8805`.
No paid calls. Worktree removed and the server stopped by PID afterwards.

## Full suite

`uv run --group dev pytest tests -q` on the fresh seed: 279 passed in 35.56s, exit 0.

## What the new tests check

- `test_stored_mreq_id_is_the_id_the_curator_call_returned`: a new user's first `GET /api/deck?n=10` gives exactly one
  `curator_calls` row, `mreq_id` equal to the id the fake sent for that call (the fake sends a different
  `mreq_` + 32 hex id per curator response, recorded in `curator_requests`), `profile_version` 0, and all 10 `decisions`
  rows carry that row's `call_id` and `profile_version`. A second user's call has a different id that appears on none
  of the first user's rows.
- `test_failed_curator_call_stores_the_id_it_returned`: with `[[curator_http_500]]`, the deck answers 502 and the row has
  status `failed` and the id the fake sent. The fake already sent the header on every response, failures included.

## Mutation check

In the worktree, the `request_id` argument in the `curator_calls` insert in `worker/src/deck.py` was replaced with
`None`; the file was restored with `git checkout` afterwards (worktree since deleted). With the server reloaded, both
new tests failed:

```
AssertionError: assert None == 'mreq_00000000000000000000000000000003'
FAILED tests/test_deck.py::test_stored_mreq_id_is_the_id_the_curator_call_returned
FAILED tests/test_deck.py::test_failed_curator_call_stores_the_id_it_returned
2 failed, 25 deselected
```
