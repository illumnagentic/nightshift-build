# Property card

Date: 2026-10-24

## Commands (from `web/`, exit codes captured directly)

| Command | Exit |
| ------- | ---- |
| `npm run typecheck` | 0 |
| `npm test` | 0 (5 files, 106 tests passed) |
| `npm run build` | 0 |

`format.test.ts` covers every value of `price_qualifier` (4), `property_type` (9) and
`tenure` (3), null handling, price formatting in `en-GB` with no pence, floor level and
the commute line.

## What the card shows, and null handling

| Item | Shown as | When null or empty |
| ---- | -------- | ------------------ |
| Photo | current photo, 4:3, `object-fit: cover`, alt is the address or "Property photo n of m" | "No photos" placeholder block |
| Photo controls | Previous / Next buttons and "n of m" | hidden when there is one photo or none |
| Price | "£525,000", preceded by the qualifier in words | no qualifier: price only |
| Bedrooms, bathrooms, type | "2 bed · 1 bath · Flat" | each omitted |
| Address, postcode | "14 Example Road, London, E8 1AA" | each omitted; line omitted if both are |
| EPC, tenure, floor level | "EPC C · Leasehold · Second floor" | each omitted; line omitted if all are |
| Key features | first 4 as a list | list omitted when empty |
| Commute | pill "32 min to EC2N 2DB" plus assumptions in small type | `minutes: null` gives "Commute unknown", no assumptions text |

The card does not read `source`, `chips` or `feedback_required`. All styles in
`web/src/deck/deck.css` sit under `.deck-card`.
