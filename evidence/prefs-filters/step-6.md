# One failing listing does not fail the postcode; TfL modes; FAKE_PORT

## Rule
`tfl.run_batch`: with a fail streak above 0 the batch starts at `(streak * BATCH_SIZE) % len(todo)`,
wrapping. At `FAIL_STREAK_LIMIT` the commute ends `ready` (streak 0) if `commute_cache` holds any row for
the postcode, else `failed`. A 429-only batch still does not count. No schema change.

## Tests (fake upstream on 8801, server 8790, inspector 9241, existing local D1)
- Full suite: `FAKE_PORT=8801 BASE_URL=http://localhost:8790 uv run --group dev pytest tests -q`: 174 passed, exit 0.
- Server-less modules (filters, prefs_unit, mubit, tfl_unit): 99 passed, exit 0.
- Cache read straight from the local D1 afterwards (pool is 96 listings): one postcode holds 95 rows
  (one listing failing), one holds 83 rows (first 13 failing); full postcodes hold 96.
- New tests: one failing listing, a failing head of BATCH_SIZE + 1, and a postcode answering HTTP 300
  (`pending, pending, failed`). Existing tests unchanged and passing.

## TfL modes
- Meta/Modes lists cycle, taxi and car modes, and the Journey Planner `mode` parameter documents no default.
- Observed (four anonymous calls in all: a modes list, the API description, two journeys; the brief allowed one journey
  call): two journeys requests in this URL shape returned six journeys; leg modes were only
  walking, bus and tube.
- Conclusion: no `mode=` added; the finding is in the `tfl.py` docstring. The sample is small, and the
  default is not documented, so a journey with a cycle or taxi leg is not ruled out.
