# Hard filter function

Command: `cd worker && uv run --group dev pytest tests/test_filters.py tests/test_prefs_unit.py tests/test_mubit.py -q`

Result: 94 passed in 0.08s, exit 0. No server needed.

## Pool sizes on the real listings (635 in dataset/listings.sqlite, read-only)

| Pref set | Hard limits | Listings passing |
| -------- | ----------- | ---------------- |
| price only | max price 500000 | 209 |
| family house | max price 900000, 3+ bedrooms, house | 138 |
| flat good epc | flat or maisonette, EPC C or better, max price 600000 | 126 |
| freehold detached | freehold, detached or bungalow | 109 |
| long lease flat | flat, 1+ bedroom, lease 100+ years | 202 |
| everything | max 750000, 2+ beds, terraced or semi-detached, EPC D+, freehold, lease 50+ | 80 |
| leasehold 90 | leasehold, lease 90+ years | 173 |
| share of freehold lease | share of freehold, lease 80+ years | 60 |

Each set is checked listing by listing with a plainly written check that does not call
`passes`: every returned listing meets every set limit, and every excluded one breaks a
limit or has an unknown field for a set limit.

Commute is not part of these pools: the commute cache does not exist yet.
