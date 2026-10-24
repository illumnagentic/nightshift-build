# TfL unit tests moved to a server-less module

Date: 2026-10-24. Metadata only. No keys.

## Change

`test_classify_answers` and `test_url_and_next_tuesday` moved unchanged from
`worker/tests/test_commute.py` to the new `worker/tests/test_tfl_unit.py`. Only the
imports differ (the new module needs `sys`, `Path` and `tfl`). `test_commute.py` keeps its
`pytestmark = pytest.mark.usefixtures("fake")`. The worker README lists the new module
on the server-less test line.

## Commands and results

1. Server-less run:
   `cd worker && uv run --group dev pytest tests/test_filters.py tests/test_prefs_unit.py tests/test_mubit.py tests/test_tfl_unit.py -q`:
   99 passed, exit 0 (97 before, plus the two moved tests).
2. Test-mode server on port 8790, inspector 9241, with the fake upstream on 8801
   (`GEMINI_BASE` and `TFL_BASE` pointing at it), no re-seed. Ports 8787, 9229 and 9239
   were left alone.
3. `FAKE_PORT=8801 BASE_URL=http://localhost:8790 uv run --group dev pytest tests -q`:
   171 passed in 7.69 s, exit 0.
4. The test-mode server was stopped by its process ids; port 8790 no longer listens.
5. Process-reference check: exit 0, no hits.
