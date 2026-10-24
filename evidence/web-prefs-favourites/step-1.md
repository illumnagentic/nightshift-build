# Prefs form logic

Date: 2026-10-24

## Functions (`web/src/prefs/prefsForm.ts`)

- `formFromPrefs`: nulls become `""`; a numeric limit becomes its string (zero included).
- `limitError`: `null` for a blank or whole-number limit (padded, zero and negative allowed); otherwise "Enter a whole number of minutes." Rejects `45.5`, `abc`, `4 5`, `45min`, `1e3`, `-`, `+5`.
- `canSave`: true only with non-blank trimmed text and postcode and no limit error. No postcode format or range check.
- `toRequest`: trimmed text and postcode; `max_commute_min` as a number when given (zero kept), key omitted when blank; never an empty string.

## Tests (`web/src/prefs/prefsForm.test.ts`)

Each function has cases for the behaviour above: all-null prefs, saved values, blank and padded limits, rejected parse cases, blank and whitespace-only fields, no format or range check, trimming, omitted key, zero kept, no `""` values.

## Commands (from web/)

- `npm run typecheck`: exit 0
- `npm test`: exit 0, 7 files, 178 tests passed (prefs file: 15 tests)
- `npm run build`: exit 0
