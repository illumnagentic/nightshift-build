# TfL answers with no journeys list

## Behaviour change

`classify` in `worker/src/tfl.py` now treats a 200 JSON object whose `journeys` is missing, null or not a list as transient (retried, never cached). 404 and 200 with an explicit `"journeys": []` stay `no_journey`; a disambiguation stays transient.

## Tests

- Server-less run (test_filters, test_prefs_unit, test_mubit, test_tfl_unit): 99 passed, exit 0.
- Full suite in test mode (server 8790, inspector 9241, fake upstream 8801, fake Mubit key, no real Mubit or TfL): 179 passed, exit 0.
- `test_classify_answers`: `classify(200, '{}')` is now `("transient", None)`; new exact assertions for `'{"journeys": null}'` and `'{"message": "x"}'`. All other assertions unchanged.
- New `test_empty_200_answers_are_not_cached_and_are_asked_again`: after one normal batch, every journey answers 200 `{}`; polls give pending, pending, failed. After the outage is cleared and the postcode saved again, polling reaches ready. Listings asked during the outage (bar the one control call, which re-asks a cached listing) are asked again; none of the first batch's listings are.

## README

The TfL commute times section says `ready` means every listing has a cached time or TfL was asked and could not route it, so a few listings can be left unknown.
