# Fetch run

Metadata only: no response bodies, no key. Counts come from `dataset/raw/rapidapi/_calls.log`
(gitignored) and the provider's `x-ratelimit-requests-remaining` header. All runs used
`fetch_rapidapi.py --cap 300`, one search page per area with the script's existing filters
(GBP 250,000 to 1,200,000, no retirement homes, no buying schemes, any property type, no `--flats`).

## Per area

Cards seen = results on search page 1. Passing = cards that pass the card rules. Details ok = detail
calls that returned 200 (saved). Autocomplete was one call per area; Brighton's was made earlier and is cached.

| Area | Query | Identifier | displayName | Swap | Autocomplete calls | Search calls | Cards seen | Passing | Detail calls | Detail failures |
| ---- | ----- | ---------- | ----------- | ---- | ------------------ | ------------ | ---------- | ------- | ------------ | --------------- |
| Brighton | Brighton | REGION^93554 | Brighton, East Sussex | none | 1 (earlier, cached) | 1 | 25 | 25 | 20 | 0 |
| Cambridge | Cambridge | REGION^274 | Cambridge, Cambridgeshire | none | 1 | 1 | 25 | 25 | 20 | 0 |
| Croydon | Croydon | REGION^93944 | Croydon (London Borough) | none | 1 | 1 | 25 | 25 | 20 | 0 |
| Kingston upon Thames | Kingston upon Thames | REGION^93968 | Kingston upon Thames (Royal Borough) | none | 1 | 1 | 25 | 25 | 20 | 0 |
| Oxford | Oxford | REGION^1036 | Oxford, Oxfordshire | none | 1 | 1 | 25 | 25 | 20 | 0 |
| Chelmsford | Chelmsford | REGION^307 | Chelmsford, Essex | none | 1 | 1 | 25 | 24 (23 distinct ids) | 20 | 0 |
| Sevenoaks | Sevenoaks | REGION^1191 | Sevenoaks, Kent | none | 1 | 1 | 25 | 25 | 20 | 1 (HTTP 400, id 94155597) |
| Greenwich | Greenwich | REGION^61226 | Greenwich (London Borough) | none | 1 | 1 | 25 | 25 | 10 | 0 |
| Haringey | Haringey | REGION^61227 | Haringey (London Borough) | none | 1 | 1 | 25 | 24 | 10 | 0 |
| Hammersmith and Fulham | Hammersmith and Fulham | REGION^61407 | Hammersmith And Fulham (London Borough) | none | 1 | 1 | 25 | 22 | 10 | 0 |
| **Total** | | | | | 10 | 10 | 250 | 244 distinct | 170 | 1 |

Detail files saved: 169 (all distinct). Each area has only its first search page, so every area could
supply at most 25 cards; the 20-per-town targets were met from that one page.
The identifier chosen for Croydon, Kingston, Greenwich, Haringey and Hammersmith and Fulham is the borough
entry; Brighton, Cambridge, Oxford, Chelmsford and Sevenoaks use the town entry (not a station, not a street).

## Totals

| Endpoint | Calls | Status |
| -------- | ----- | ------ |
| /auto-complete | 10 | 10 x 200 |
| /buy/property-for-sale (search) | 10 | 10 x 200 |
| /buy/property-for-sale/detail | 170 | 169 x 200, 1 x 400 |
| **Total, whole feature so far** | **190** | cap 300 |

- Provider's last `x-ratelimit-requests-remaining`: 108 (at the last logged call).
- First call (UTC): 2026-10-24T10:00:16+00:00. Last call: 2026-10-24T10:19:50+00:00.
- One detail run (Cambridge, after 16 of 20) died on a connection error before the call was logged. The
  provider count (297 after the first call, 108 after 190 logged calls) matches the log, so no unlogged call
  was billed. The run was repeated and fetched the remaining 4 Cambridge details; saved details are skipped.

## Top-up (redo 2)

Metadata only. Purpose: the 24 Oct page-1 searches returned each area's highest-priced cards (52 at
exactly GBP 1.2m), so this run asks for the GBP 250,000 to 700,000 band. All runs used `--cap 300`.
Run 2026-10-24T10:50:58Z to 10:57:12Z (UTC) for the calls below.

### Sort probe

Brighton (REGION^93554), band 250000-700000, two calls:

| `--sort` (sent as `sort_by`) | Prices on the 25 cards returned | Order observed |
| ---------------------------- | ------------------------------- | -------------- |
| `1` | 680000 then 24 x 700000 | highest first (unchanged) |
| `2` | 675000 then 24 x 700000 | highest first (unchanged) |

Neither value changed the order, so no usable sort was found. No further probe: the budget did not allow
one. The fallback was used: two bands per area (250000-450000 and 450000-700000), default sort.
Each band's page 1 is again highest-first, so 24 of 25 cards sit at exactly the band's upper limit
(450000 or 700000); the exceptions are Sevenoaks (8 and 5 of 25) and the upper bands of Cambridge (17),
Oxford (14) and Chelmsford (15).

### Per area

Search calls = 2 band searches per area (Brighton also had the 2 probe searches above, which are in its
upper-band candidate pool). Cards seen 25 per search. Details: lower band (250-450k) / upper band
(450-700k), both with `--min-price`/`--max-price` set to the band. Detail failures: none. The upper-band run
accepts cards at exactly 450000, so those can come from either band's file.

| Area | Identifier | Search calls | Cards seen | Detail calls (low/high) | Failures | Price range of fetched cards (GBP) |
| ---- | ---------- | ------------ | ---------- | ----------------------- | -------- | ---------------------------------- |
| Brighton | REGION^93554 | 2 (+2 probe) | 100 | 9 (5/4) | 0 | 375,000 to 700,000 |
| Cambridge | REGION^274 | 2 | 50 | 9 (5/4) | 0 | 350,000 to 450,000 |
| Croydon | REGION^93944 | 2 | 50 | 9 (5/4) | 0 | 265,000 to 700,000 |
| Kingston upon Thames | REGION^93968 | 2 | 50 | 9 (5/4) | 0 | 350,000 to 700,000 |
| Oxford | REGION^1036 | 2 | 50 | 9 (5/4) | 0 | 300,000 to 700,000 |
| Chelmsford | REGION^307 | 2 | 50 | 9 (5/4) | 0 | 290,000 to 700,000 |
| Sevenoaks | REGION^1191 | 2 | 50 | 9 (5/4) | 0 | 400,000 to 700,000 |
| Greenwich | REGION^61226 | 2 | 50 | 6 (3/3) | 0 | 425,000 to 700,000 |
| Haringey | REGION^61227 | 2 | 50 | 6 (3/3) | 0 | 439,950 to 700,000 |
| Hammersmith and Fulham | REGION^61407 | 2 | 50 | 5 (3/2) | 0 | 375,000 to 450,000 |
| **Total** | | 20 (+2 probe) | 550 | 80 | 0 | 265,000 to 700,000 |

Price spread of the 80 new detail candidates (card prices, GBP): min 265,000, median 450,000, max 700,000.
By 50k bucket: 250k: 2, 300k: 1, 350k: 4, 400k: 3, 450k: 40, 500k: 2, 550k: 1, 600k: 1, 650k: 3, 700k: 23.
Exactly 450,000: 40; exactly 700,000: 23 (63 of 80 at a band limit, 17 spread below).

### Totals for the top-up

| Endpoint | Calls | Status |
| -------- | ----- | ------ |
| /buy/property-for-sale (search) | 22 | 22 x 200 |
| /buy/property-for-sale/detail | 80 | 80 x 200 |
| **Top-up total** | **102** | |
| **Whole feature (log lines)** | **292** | cap 300 |

- Provider's last `x-ratelimit-requests-remaining`: 6 (at the last logged call, 2026-10-24T10:57:12+00:00).
- Log lines 1-190 are the earlier run; lines 191-292 are this top-up. Provider count went 108 to 6 for 102
  calls, matching the log.
