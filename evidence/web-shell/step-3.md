# Mock client evidence: in-memory mock client

Date: 2026-10-24

## Commands (from `web/`)

| Command | Exit |
| ------- | ---- |
| `npm run typecheck` | 0 |
| `npm test` | 0 |
| `npm run build` | 0 |
| process-reference check script (repo root) | 0 |

`npm test`: 3 files, 50 tests passed (mock.test.ts 39, http.test.ts 10, smoke.test.ts 1).

## Fixtures

20 listings in `web/src/api/fixtures.ts`, trimmed from rows in `dataset/listings.jsonl`
(contract field names; at most 4 photos, 1 floorplan, 2 stations, description cut to about
240 characters). Twenty rather than the 12 minimum, because the onboarding test needs more
than 15 swipes from one user.

Chips are computed when the module loads by a local function that applies the contract's
Chip catalogue (offered rules, featured-first then priority order, cap of 8, labels and
phrases from the Preset phrases table). It runs once with and once without the commute
chip. The flag clauses ("once flags exist") are applied to the three listings that carry
sample photo flags: rm-170560346, rm-172366775, rm-94639683. One flag (f_00003 on
rm-172366775) has a `corrected_text`; the rest are `null` and can be corrected.
Chips for five listings were worked out by hand from the contract and are asserted in
mock.test.ts, independently of the function: rm-172366775 (flat, no commute minutes),
rm-174367916 (semi-detached, no commute minutes), rm-170906828 (end-of-terrace house, with
commute), rm-91380246 (share-of-freehold flat with floor level, lease and service charge,
with commute) and rm-171802127 (maisonette, nine featured chips with commute so the cap of
8 cuts `building_style`). The mock gives commute minutes per listing, not per postcode, so
each listing is only ever seen in one of the two forms. All hand-derived lists matched the
function; none needed changing. Preset phrases for garden, parking, floor_level, lease,
service_charge and building_style are asserted against text copied from the contract.

Chips per listing (without commute; with commute the `commute` chip is inserted at its
priority place and the lowest chip drops if that makes nine):

- `rm-163949006` | flat | flags 0 | parking, price_value, station_access, space, kitchen, layout, condition, bathrooms
- `rm-170560346` | flat | flags 2 | natural_light, price_value, space, condition, floor_level, building_style, station_access, area_busyness
- `rm-170906828` | end_of_terrace | flags 0 | garden, price_value, station_access, condition, natural_light, area_busyness, space, kitchen
- `rm-171802127` | maisonette | flags 0 | garden, parking, natural_light, price_value, station_access, lease, service_charge, building_style
- `rm-172366775` | flat | flags 2 | parking, balcony_terrace, price_value, space, kitchen, layout, condition, bathrooms
- `rm-174032522` | detached | flags 0 | garden, parking, price_value, station_access, space, bathrooms, natural_light, area_busyness
- `rm-174367916` | semi_detached | flags 0 | garden, parking, price_value, station_access, kitchen, natural_light, area_busyness, space
- `rm-89042490` | flat | flags 0 | garden, parking, natural_light, balcony_terrace, price_value, station_access, space, bathrooms
- `rm-89124552` | bungalow | flags 0 | garden, price_value, area_busyness, home_office, natural_light, station_access, space, kitchen
- `rm-89554128` | terraced | flags 0 | price_value, station_access, kitchen, bathrooms, building_style, garden, natural_light, area_busyness
- `rm-94639683` | other | flags 2 | natural_light, balcony_terrace, price_value, station_access, kitchen, bathrooms, floor_level, lease
- `rm-87459600` | null | flags 0 | price_value, station_access, space, kitchen, condition, bathrooms, natural_light, area_busyness
- `rm-90476601` | house | flags 0 | price_value, garden, natural_light, station_access, area_busyness, space, kitchen, layout
- `rm-167642897` | flat | flags 0 | parking, price_value, station_access, space, kitchen, condition, bathrooms, building_amenities
- `rm-90819174` | terraced | flags 0 | garden, parking, price_value, area_busyness, kitchen, condition, bathrooms, natural_light
- `rm-92824431` | terraced | flags 0 | garden, price_value, kitchen, bathrooms, building_style, natural_light, station_access, area_busyness
- `rm-94648950` | flat | flags 0 | price_value, station_access, space, layout, bathrooms, lease, service_charge, energy_efficiency
- `rm-94672293` | flat | flags 0 | price_value, station_access, space, condition, floor_level, lease, service_charge, energy_efficiency
- `rm-91380246` | flat | flags 0 | price_value, station_access, floor_level, lease, service_charge, natural_light, area_busyness, space
- `rm-93699291` | terraced | flags 0 | parking, natural_light, price_value, station_access, space, condition, garden, area_busyness
