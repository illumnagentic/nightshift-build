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

## Explicit TfL modes (supersedes "no mode= added" above)
- Every journey request now sends `&mode=` with a fixed comma-separated list, taken from Meta/Modes (2026-10-24):
  bus, cable-car, dlr, elizabeth-line, national-rail, overground, replacement-bus, river-bus, tram, tube, walking.
- Left out: cycle, cycle-hire, taxi, black-cab, private-car, electric-car, private-hire, coach, plane, international-rail,
  river-tour and the other non-public or non-scheduled modes.
- One anonymous call, 51.545,-0.062 to EC2N2DB, 2026-10-27 0830 Arriving: HTTP 200, 3 journeys, leg modes seen:
  overground, walking (all within the list). TfL accepted the list first time, no retry.
- Results with the mode list: full suite in test mode (server 8790, inspector 9241, fake upstream 8801) 174 passed;
  server-less modules (filters, prefs_unit, mubit, tfl_unit) 99 passed. The commute test now expects the exact mode suffix.
