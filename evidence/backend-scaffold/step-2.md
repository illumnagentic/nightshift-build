# Username-only accounts: test run

Date: 2026-10-24

Commands (from `worker/`):

1. `bash scripts/seed.sh` — exit 0 (fresh local D1, users empty).
2. `uvx --from workers-py pywrangler dev` in the background (http://localhost:8787); `GET /api/users` returned `{"users":[]}` before the tests.
3. `uv run --group dev pytest tests -q`

Result: `24 passed in 0.62s`, exit 0.

Covered: 201 create, list includes it, trim, distinct ids, creation order, 409 `username_taken` for upper/lower/swapcase/padded variants, 422 `invalid_request` for missing, empty, whitespace, 33 chars, space, `!`, non-ASCII, wrong types, non-object bodies and malformed JSON; every error body has exactly `error.code` and `error.message`.

Server stopped by PID after the run. No Mubit call made.

## Error shape for unknown paths, wrong methods and server errors

Date: 2026-10-24

From `worker/`: `bash scripts/seed.sh` (exit 0), `pywrangler dev` in the background, then `uv run --group dev pytest tests -q`.

Result: `36 passed in 0.75s`, exit 0. New cases: `GET /api/nope` is 404 `not_found`; `DELETE /api/users` is 405 `method_not_allowed`; both have exactly `error.code` and `error.message`.

Manual 500 check: dropped `users` in the local D1 (`wrangler d1 execute haka --local --command "DROP TABLE users"`), then `curl -i /api/users` returned `HTTP/1.1 500` with `{"error":{"code":"internal_error","message":"Something went wrong on the server."}}`. No exception text in the body; the D1 error is in the dev-server log. The body reaches the client through the `@app.middleware("http")` guard. The `Exception` handler route was not tried.

Re-seeded afterwards (exit 0). The still-running server kept returning 500 after the re-seed (it had not picked up the recreated table), so it was stopped; a direct `SELECT count(*) FROM users` on the local D1 then returned 0, confirming the table is back. A fresh server start is needed after re-seeding. Server stopped by PID. No Mubit call made.
