# Seeded prefs in the mock

Date: 2026-10-24

## Seeded values

| User | Text | Postcode | max_commute_min | commute_status |
| ---- | ---- | -------- | --------------- | -------------- |
| alex (u_01) | Two bed flat under 550k, near a tube station, bright rooms, no ground floor. | EC2N 2DB | 45 | ready |
| jordan (u_02) | Two bed flat, near a station, bright rooms, no ground floor. | N1C 4AG | null | ready |

`parsed` is built by the same function `putPrefs` uses. Users created later have no prefs.

## Changed tests

- "returns the all-null shape before anything is saved": before, read alex; after, reads a newly created user. Same assertion.
- "returns 409 prefs_missing, commute_pending and commute_failed": before, used alex; after, uses a newly created user. Same assertions.

## Added tests

- "serves cards to seeded users without a prefs call"
- "gives seeded users saved prefs with commute_status ready"

## Commands (from web/)

- `npm run typecheck`: exit 0
- `npm test`: exit 0, 3 files, 52 tests passed
- `npm run build`: exit 0
