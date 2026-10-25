# README run from a clean state

Date: 2026-10-24. Metadata only. No keys.

## Method

The README sequence was run in a throwaway git worktree of HEAD, so its local D1 was
empty and nothing else on the machine was touched (a normal dev server on 8787 and
another test-mode server on 8788 were already running and were left alone). Two values
differ from the README, only to avoid those running servers: server port 8790, inspector
port 9241, fake upstream port 8801 (`FAKE_PORT=8801`, and the same port in the `GEMINI_BASE`
and `TFL_BASE` vars). Everything else is the README command.

## Commands and results

1. `worker/scripts/seed.sh` in the fresh worktree: exit 0.
2. Test-mode server: `uvx --from workers-py pywrangler dev --port 8790 --inspector-port 9241
   --var MUBIT_API_KEY:test-key-not-a-real-key --var GEMINI_BASE:http://127.0.0.1:8801
   --var TFL_BASE:http://127.0.0.1:8801`, started in the background. Log ended
   `Ready on http://localhost:8790`.
3. `FAKE_PORT=8801 BASE_URL=http://localhost:8790 uv run --group dev pytest tests -q`:
   171 passed in 7.83 s, exit 0.
4. Unit modules alone, no server:
   `uv run --group dev pytest tests/test_filters.py tests/test_prefs_unit.py tests/test_mubit.py -q`:
   97 passed, exit 0.
5. The test-mode server was stopped by its process ids (the processes whose command line
   named port 8790, plus the workerd listener); port 8790 no longer listened. The worktree
   was removed.
6. Process-reference check: exit 0, no hits.

No call reached Mubit or TfL: the key was the fake key and both bases pointed at the fake.

## Notes

`test_tfl_unit.py` does not exist yet; the README lists three server-less modules, and
`test_commute.py` still holds the two pure TfL tests, which need the server. The
server-less module list is to be extended when that move is made.
