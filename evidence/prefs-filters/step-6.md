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

## Commute status after an outage (supersedes the "any cached row ends ready" rule above)
- Rule in `tfl.run_batch`: after a fully failed, non-rate-limited batch at `FAIL_STREAK_LIMIT`: no cache row for the
  postcode gives `failed`. Otherwise one control `fetch_journey` re-asks the cached listing picked by
  `ORDER BY minutes IS NULL, listing_id LIMIT 1`: HTTP 429 gives `pending` (streak kept); a transient failure gives
  `failed`; an answer (journey or no journey) gives `ready` (streak 0) when `streak * BATCH_SIZE >= len(todo)`, else
  `pending` (streak kept, rotation goes on). The control answer is not cached. No schema change.
- The fake gains `DESTINATION_STATUS` (compact postcode to status, body `{}`, checked first). New tests: outage after one
  poll (`pending, pending, failed`, no TfL calls on a further GET, re-save after recovery asks only pool minus 12),
  outage with the last batch left, and a 429 after progress (five polls, all pending).
- One ruled change to an existing assertion: in `check_unknown_listings_left` the expected list is now
  `sorted(good + [good[0]])`, because the control re-asks the lowest-id good listing; the tests with a failing
  listing pass with it (good[0] is the lowest-id cached listing, the one the SQL picks).
- Server-less modules (filters, prefs_unit, mubit, tfl_unit): 99 passed, exit 0.
- Full suite in test mode (server 8790, inspector 9241, fake upstream 8801): 177 passed, exit 0.
- Smoke script against the same server (fake only, no real TfL or Mubit): one failing listing ends `ready`
  (`pending, pending, ready`, 104 TfL calls); outage after the first poll now ends
  `pending, pending, pending, failed` (earlier result: `ready` with 12 of 96 cached). The fake saw only the fake key.

## Rate-limited control call (test-only)
- The fake gains `START_STATUS` (start coordinates to status, body `{}`, checked after `DESTINATION_STATUS`, before the
  other rules). New test `test_rate_limited_control_call_never_fails_the_commute` on a fresh EC1A postcode: one poll
  caches the first 12 listings; every uncached pool start answers 500; the lowest-id cached listing (the control) answers
  429; `FAIL_STREAK_LIMIT + 2` polls are all `pending`; the fake's log shows the control start asked again; then the
  control answers 500 and the next poll is `failed`.
- Coordinate collisions: 635 listings share 626 distinct coordinates, so the test asserts the control start is not shared
  by any uncached listing (a shared start would take the 429 and stop the batch before the control call). It holds for
  the current pool. It also asserts the first batch asked exactly the first 12 pool rows (compared sorted, as requests run concurrently).
- Mutation check: with the control-call `if status == 429: return "pending", streak` removed from `tfl.run_batch` (dev server
  confirmed reloaded), the new test failed (`pending, pending, failed`, expected all pending). The two lines were restored;
  `git diff` of `worker/src/tfl.py` is empty.
- Server-less modules (filters, prefs_unit, mubit, tfl_unit): 99 passed, exit 0.
- Full suite in test mode (server 8790, inspector 9241, fake upstream 8801): 178 passed, exit 0.
