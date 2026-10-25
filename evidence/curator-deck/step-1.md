# Chips per card with photo flags

- Date: 2026-10-25
- Source: `dataset/listings.sqlite` (635 listings, 14,684 photo flag rows, flags on all 635 listings), read-only.
- Code: `worker/src/chips.py`. Metadata only, no listing rows reproduced.

## Counts per chip, before and after photo flags

"offered" is the listings whose rule offers the chip, before the cap. "featured" is the
listings where the chip counts as a feature the listing clearly has. "in the 8" is the
listings where the chip survives the cap of 8, with no commute chip. The "no flags"
columns equal `evidence/chip-catalogue/coverage.md` and are asserted by a test.

| chip_id | offered (no flags) | featured (no flags) | in the 8 (no flags) | offered (flags) | featured (flags) | in the 8 (flags) |
| ------- | --: | --: | --: | --: | --: | --: |
| `garden` | 418 | 312 | 412 | 496 | 448 | 486 |
| `parking` | 264 | 264 | 264 | 264 | 264 | 264 |
| `natural_light` | 635 | 108 | 515 | 635 | 635 | 635 |
| `balcony_terrace` | 124 | 124 | 124 | 124 | 124 | 124 |
| `price_value` | 635 | 635 | 635 | 635 | 635 | 635 |
| `commute` | per user | per user | per user | per user | per user | per user |
| `station_access` | 635 | 383 | 558 | 635 | 383 | 522 |
| `area_busyness` | 635 | 68 | 343 | 635 | 68 | 253 |
| `space` | 635 | 283 | 438 | 635 | 623 | 628 |
| `kitchen` | 635 | 257 | 381 | 635 | 257 | 350 |
| `layout` | 635 | 123 | 172 | 635 | 123 | 150 |
| `condition` | 635 | 147 | 148 | 635 | 267 | 252 |
| `bathrooms` | 635 | 310 | 296 | 635 | 310 | 243 |
| `floor_level` | 135 | 135 | 123 | 135 | 135 | 98 |
| `building_amenities` | 99 | 99 | 81 | 99 | 99 | 53 |
| `lease` | 225 | 225 | 183 | 225 | 225 | 128 |
| `service_charge` | 207 | 207 | 143 | 207 | 207 | 87 |
| `energy_efficiency` | 635 | 170 | 128 | 635 | 170 | 82 |
| `home_office` | 561 | 57 | 43 | 561 | 57 | 32 |
| `building_style` | 140 | 140 | 93 | 140 | 140 | 58 |

## What the flags change

- `garden` is offered on 78 more listings (418 to 496) only because a photo flag has room `garden`.
- `natural_light` is featured on all 635 listings. At least one `light` flag with value
  `bright` or `poor` and confidence `high` or `medium` exists on every listing, so the
  featured rule no longer separates listings.
- `space` is featured on 623 of 635 (a `sqm_estimate` flag exists on 609 listings, plus text mentions).
- `condition` is featured on 267 (a `defects` flag of any value and confidence exists on 159 listings).
- With flags, featured chips per card (no commute chip): min 3, median 8, max 15; more than 8 on 254 of 635 cards
  (376 with a commute chip). Without flags the figure was 117 (182 with commute). More cards now cut featured chips at the cap.
- Every card still offers 10 to 18 chips before the cap (11 to 19 with commute), so every card sends exactly 8.

## Reading of the contract

- Flag clauses read the `value`, `field`, `confidence` and `room` columns only. `corrected_text` is never read, so a correction cannot change which chips are offered.
- "a photo flag has `room` `garden`" is read as any flag row whose `room` column is `garden`, whatever its `field`.
- "a `defects` flag exists" and "a `sqm_estimate` flag exists" are read as any row of that field, whatever its value or confidence.
- Only the `light` clause carries a confidence condition (`high` or `medium`), as written.

## Commands

```
cd worker && uv run --group dev pytest tests/test_chips.py tests/test_filters.py tests/test_prefs_unit.py tests/test_mubit.py tests/test_tfl_unit.py -q
```

Result: 137 passed in 0.45s, exit 0. The recount tables come from `_counts` in `worker/tests/test_chips.py`
(`test_recount_without_flags_matches_earlier_coverage` and `test_recount_with_flags` assert them exactly).
