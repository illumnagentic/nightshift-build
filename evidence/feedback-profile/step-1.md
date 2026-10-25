# Swipe, profile versions and GET /profile: test evidence

Run 2026-10-25 in a throwaway git worktree, local D1 seeded with `worker/scripts/seed.sh`.
Test-mode server on port 8820 (inspector 9250), fake upstream on 8821, fake Mubit key. No paid calls; :8787 untouched.

## Built
- `POST /api/decisions/{id}/swipe`: 422 `invalid_request`, 404 `decision_not_found`, 409 `already_swiped`; the update is conditional on `swiped_at IS NULL` and its `meta.changes` is checked.
- Superlike inserts a `favourites` row (primary key user, listing). Right swipe does not.
- `profile_versions` table; `taste.bump` takes the next version in one `INSERT ... SELECT COALESCE(MAX(version),0)+1 ... RETURNING version`. Factors are copied forward (`[]` for now).
- `GET /api/profile`: `{version, factors, history}`, ten newest, newest first.
- Module is `worker/src/taste.py`: a file named `profile.py` is shadowed by the standard library module in the Worker runtime.
- New tables only: `favourites`, `profile_versions`.

## Commands and results
- `FAKE_PORT=8821 BASE_URL=http://localhost:8820 uv run --group dev pytest tests -q` (from `worker/`): 299 passed, exit=0.
- `uv run --group dev pytest tests/test_filters.py tests/test_prefs_unit.py tests/test_mubit.py tests/test_tfl_unit.py -q`: 99 passed, exit=0.
- `tests/test_swipe.py` alone: 20 passed.
- README schema-apply command, verified: `npx wrangler d1 execute haka --local --file schema.sql` from `worker/`, exit 0, users table still held 143 rows afterwards.
- `meta.changes` and `RETURNING` both work in D1 under Pyodide; no fallback needed.
