# Commute optional (2026-10-25)

TfL commute is a stretch goal. `PUT /api/prefs` accepts a missing or null `commute_postcode`.

## Behaviour checked

- No postcode (missing, or null): 200, `commute_postcode: null`, `commute_status: null`,
  `max_commute_min: null`, `parsed.hard.max_commute_min: null`. Three GETs return the same
  body and the fake TfL log gains no request.
- `max_commute_min` non-null with no postcode (missing or null): 422 `invalid_request`.
- Non-string postcode: still 422 `invalid_request`; malformed string: still 422 `invalid_postcode`.
- Re-save adding a postcode after a postcode-less save: `pending`, then `ready` on the fake,
  with TfL requests for that postcode.
- With a postcode: unchanged (all existing commute tests pass).

## Schema

`prefs.commute_postcode` and `commute_status` are nullable, with a CHECK that they are NULL
together. No migration: `worker/scripts/seed.sh` rebuilds the local D1.

## Existing assertions changed

In `worker/tests/test_prefs.py`, the parametrised 422 list in
`test_invalid_request_is_422_and_never_calls_the_parser` had two cases that expected 422 for
a missing and a null `commute_postcode`: `{"text": TEXT}` and
`{"text": TEXT, "commute_postcode": None}`. They are replaced by
`{"text": TEXT, "max_commute_min": 45}` and
`{"text": TEXT, "commute_postcode": None, "max_commute_min": 45}` (still 422), and the two
removed shapes are now asserted as 200 in `test_no_postcode_is_saved_with_null_commute_and_no_tfl_work`.

## Runs (throwaway worktree, fresh seed, test mode, server 8790, fake 8801)

- Server-less modules (test_filters, test_prefs_unit, test_mubit, test_tfl_unit): 99 passed, exit 0.
- Full suite `FAKE_PORT=8801 BASE_URL=http://localhost:8790 uv run --group dev pytest tests -q`:
  183 passed (179 before, plus 4 new), exit 0.

## Contract wording on commute and the deck

With `max_commute_min` set, a listing with no cached time does not pass the hard filters
(`passes` in `worker/src/filters.py`), so the deck is short while the status is `pending`
and empty on `failed`. The contract now says so, and says the frontend refetches the deck
at once after a re-save instead of waiting for `commute_status`. No error code or enum value
changed.
