# Feedback and the taste profile factors: test evidence

Run (re-run after the ordered-query fix) 2026-10-25 in a throwaway git worktree (detached at 12e9460 plus the files for this feature), local D1 seeded with `worker/scripts/seed.sh`.
Test-mode server on port 8840 (inspector 9270), fake upstream on 8841, fake Mubit key. No paid calls; :8787 untouched. Worktree and server removed afterwards.

## Built
- `PUT /api/decisions/{id}/feedback`: both keys required; `strength` enum; repeated `chip_id` 422 `invalid_request`; chip not in `offered_chips` 422 `chip_not_offered`; blank texts stored and returned as `null`; `skipped` only with `[]` and `null`; 404 `decision_not_found`; 409 `not_swiped`. Body shape is checked before the decision lookup (as the swipe endpoint does). A chip with no `text` key is read as `null`.
- New `feedback` table keyed by `decision_id` (user_id, chips_json, free_text, skipped, updated_at). Upsert replaces the whole row. New table only.
- Every PUT calls `taste.bump(..., "feedback", decision_id=...)`: one version, including a no-op edit, a clear and a skip.
- `taste.compute_factors(rows)`: pure. `taste.current_factors(db, user_id)` loads the user's feedback rows joined to swiped decisions. `taste.bump` now stores the freshly computed factors as that version's `factors_json` (swipes too), so the latest row is the only source for `GET /profile`.
- A favourite-removal reason (added later) is one more row with its reason as `free_text`, no chips, and that decision's `offered`; `compute_factors` needs no change for it.

## Formula as implemented
Per catalogue factor, over non-skipped feedback rows of swiped decisions:
- `offered` = rows whose decision's `offered_chips` holds the chip.
- `mentioned_only` = rows where the chip was not offered but the factor's term matched `free_text`.
- `chosen` = rows where the chip was answered or the term matched `free_text` (once per row).
- `weight = round(chosen / (offered + mentioned_only + 1), 2)`.
- Listed only when `chosen >= 1`; sorted by weight descending, then `chip_id`.
- A cleared row (`chips: []`, `free_text: null`, `skipped` false) counts as offered with nothing chosen. A skipped row counts nowhere.
- Direction: the factor's chip answers, newest `updated_at` first, at most 3, `<strength words> "<text>"` (or `<strength words> (no comment)`), joined by `; `. Strength words: `must have`, `nice to have`, `would prefer not`, `deal-breaker`. A factor with no chip answer reads `mentioned in comments`.

## Term table (case-insensitive, word-bounded; matches move weight only)
| factor | regex |
| --- | --- |
| `garden` | `\bgardens?\b` |
| `parking` | `\b(parking|garage|driveway|car ?port|car ?park)\b` |
| `natural_light` | `\b(natural light|daylight|sunlight|sunny|bright|dark|gloomy)\b` |
| `balcony_terrace` | `\b(balcon(y|ies)|terrace)\b` |
| `price_value` | `\b(price[sd]?|overpriced|value|budget|expensive|cheap|afford\w*)\b` |
| `commute` | `\b(commute|commuting)\b` |
| `station_access` | `\b(station|tube|underground|dlr|overground)\b` |
| `area_busyness` | `\b(quiet|noisy|noise|busy|lively|peaceful|traffic)\b` |
| `space` | `\b(spacious|cramped|roomy|tiny|room sizes?|plenty of room|enough space)\b` |
| `kitchen` | `\bkitchens?\b` |
| `layout` | `\b(layout|open[- ]plan)\b` |
| `condition` | `\b(condition|dated|renovat\w*|refurb\w*|decor|modernis\w*)\b` |
| `bathrooms` | `\b(bathrooms?|en[- ]?suite|shower room|wet room)\b` |
| `floor_level` | `\b(ground floor|top floor|upper floor|stairs|floor level)\b` |
| `building_amenities` | `\b(concierge|porter|gym|communal|lifts?)\b` |
| `lease` | `\b(lease|leasehold|freehold)\b` |
| `service_charge` | `\b(service charges?|ground rent)\b` |
| `energy_efficiency` | `\b(epc|energy rating|energy efficien\w*|insulation|heating bills?)\b` |
| `home_office` | `\b(home office|study|work(ing)? from home|wfh)\b` |
| `building_style` | `\b(period|victorian|georgian|edwardian|character|new[- ]build)\b` |

Each term has a matching and a non-matching sentence in `worker/tests/test_profile_unit.py` (`TERM_SENTENCES`).

## Commands and results (from `worker/` in the worktree)
- `FAKE_PORT=8841 BASE_URL=http://localhost:8840 uv run --group dev pytest tests -q`: 373 passed, exit=0.
- `uv run --group dev pytest tests/test_filters.py tests/test_prefs_unit.py tests/test_mubit.py tests/test_tfl_unit.py tests/test_chips.py tests/test_curator_unit.py tests/test_profile_unit.py -q`: 204 passed, exit=0.
- `tests/test_profile_unit.py` 36 tests; `tests/test_feedback.py` 38 tests (74 collected together).

The feedback query is read `ORDER BY f.updated_at DESC, f.decision_id`; a unit test fixes the order of rows with an equal `updated_at`.
