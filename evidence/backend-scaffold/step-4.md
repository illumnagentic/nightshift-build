# README run-through: seed, dev server, tests (2026-10-24)

Metadata only. Local state was reset by seed.sh before the run.

| README command | Result |
| -------------- | ------ |
| `worker/scripts/seed.sh` (repo root) | exit 0 |
| count check via `npx wrangler d1 execute haka --local` | listings 635, users 0 |
| `uvx --from workers-py pywrangler dev` (in `worker/`, background) | up on :8787; `GET /api/users` 200 `{"users":[]}` |
| `uv run --group dev pytest tests -q` (in `worker/`) | 34 passed, exit 0 |
| `uv run --group dev pytest tests/test_mubit.py -q` (kit-config single-file line) | 10 passed, exit 0 |
| `uv sync --group dev` (kit-config install line) | 18 resolved, 16 checked, exit 0 |
| server stopped by PID (uvx process and its children) | `GET /api/users` then returned no response; nothing listening on 8787 |
| `python3 -I worker/scripts/mubit_ping.py` | not run (paid call) |

The README sequence was also repeated from a clean clone of the branch: seed exit 0,
34 tests passed.

Not observed: cold-cache first-run downloads (npx wrangler, uv packages), because
caches were warm on both runs.
