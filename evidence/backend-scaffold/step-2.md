# Username-only accounts: test run

Date: 2026-10-24

Commands (from `worker/`):

1. `bash scripts/seed.sh` — exit 0 (fresh local D1, users empty).
2. `uvx --from workers-py pywrangler dev` in the background (http://localhost:8787); `GET /api/users` returned `{"users":[]}` before the tests.
3. `uv run --group dev pytest tests -q`

Result: `24 passed in 0.62s`, exit 0.

Covered: 201 create, list includes it, trim, distinct ids, creation order, 409 `username_taken` for upper/lower/swapcase/padded variants, 422 `invalid_request` for missing, empty, whitespace, 33 chars, space, `!`, non-ASCII, wrong types, non-object bodies and malformed JSON; every error body has exactly `error.code` and `error.message`.

Server stopped by PID after the run. No Mubit call made.
