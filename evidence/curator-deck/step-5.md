# Chips per card after narrowing the photo-flag featured rules

- Date: 2026-10-25
- Source: `dataset/listings.sqlite` (635 listings, flags on all 635), read-only.
- Code: `worker/src/chips.py`. Metadata only, no listing rows reproduced.

## What changed

- `natural_light` is featured on a text mention, or a `light` flag with value `poor` and confidence `high` or `medium`. The `bright` value no longer counts (a high-confidence `bright` flag exists on every listing).
- `space` is featured on a text mention only. The `sqm_estimate` clause is dropped (an estimate exists on 609 listings and says nothing about size).
- `garden` and `condition` are unchanged. Chip ids, labels, phrases, priorities, the cap of 8 and the `chips[]` shape are unchanged.

## Featured counts, before and after (with flags)

| chip_id | featured before | featured after |
| ------- | --: | --: |
| `natural_light` | 635 | 128 |
| `space` | 623 | 283 |

Without flags the figures are 108 and 283, unchanged and still asserted by a test. So flags add 20 `natural_light` listings (a `poor` light flag) and none for `space`.

## Featured chips per card (with flags)

| | min | median | max | cards with more than 8 |
| --- | --: | --: | --: | --: |
| Before, no commute chip | 3 | 8 | 15 | 254 |
| Before, with commute chip | - | - | - | 376 |
| Now, no commute chip | 1 | 7 | 14 | 142 |
| Now, with commute chip (20 min) | 2 | 8 | 15 | 212 |

Without flags the more-than-8 figure was 117 (182 with commute).

## Chips in the 8, with flags, no commute chip

| chip_id | in the 8 before | in the 8 now |
| ------- | --: | --: |
| `garden` | 486 | 493 |
| `parking` | 264 | 264 |
| `natural_light` | 635 | 503 |
| `balcony_terrace` | 124 | 124 |
| `price_value` | 635 | 635 |
| `station_access` | 522 | 547 |
| `area_busyness` | 253 | 309 |
| `space` | 628 | 415 |
| `kitchen` | 350 | 350 |
| `layout` | 150 | 152 |
| `condition` | 252 | 261 |
| `bathrooms` | 243 | 290 |
| `floor_level` | 98 | 116 |
| `building_amenities` | 53 | 76 |
| `lease` | 128 | 171 |
| `service_charge` | 87 | 130 |
| `energy_efficiency` | 82 | 118 |
| `home_office` | 32 | 42 |
| `building_style` | 58 | 84 |

Offered and featured counts for the other chips are unchanged from `evidence/curator-deck/step-1.md`. Every card still sends exactly 8 chips.

## Reading of the change

The with-flags figures in the earlier evidence were a ruled spec change, not a loosening: `test_recount_with_flags` now asserts the new figures exactly, and `test_recount_without_flags_matches_earlier_coverage` is untouched.

## Commands

```
cd worker && uv run --group dev pytest tests/test_chips.py tests/test_curator_unit.py tests/test_filters.py tests/test_prefs_unit.py tests/test_mubit.py tests/test_tfl_unit.py -q
```
