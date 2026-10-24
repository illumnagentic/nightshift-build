# Floor and postcode wording

Date: 2026-10-24

## Distinct floor_level values in dataset/listings.jsonl (read only)

null (423), first (67), ground (53), second (23), top (15), fourth (10), third (7), fifth (6), 1st (5), sixth (4), lower ground (3), 5th (2), 7th (2), 2nd (2), 22nd (2), 19th, tenth, 23rd, raised ground, 24th, 31st, ninth, 10th, 3rd, 11th (1 each), "higher than 2nd floor (with lift)" (1).

## Rules chosen

- Null or blank: omitted.
- Contains "floor" (any case): only the first letter is capitalised ("higher than 2nd floor (with lift)" becomes "Higher than 2nd floor (with lift)").
- Anything else, including "top", "lower ground", "raised ground" and ordinals such as "1st": " floor" is appended, then the first letter capitalised ("Top floor", "Lower ground floor", "22nd floor"). No special case was needed for any value seen.
- Address line: full postcode already in the address (ignoring case and spaces) leaves it unchanged; trailing outward code (optionally followed by space or , . ;) is replaced by the full postcode; otherwise "address, postcode"; one part missing gives the other; both missing gives no line.

## Changed assertions

- floorLevelLabel "capitalises the first letter and keeps the rest": input "second floor" expected "Second floor", unchanged. The test is now a table of cases; the old assertion is among them.
- Null/blank assertions unchanged. No assertion changed from before to after.

## Commands (from web/)

- npm run typecheck: exit 0
- npm test: exit 0, 121 passed (5 files)
- npm run build: exit 0
