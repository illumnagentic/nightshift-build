# Listings dataset

A frozen, offline dump of 635 London and commuter-belt homes **for sale**, built for the
Property Swipe Agent hackathon app. The app reads these files. It never calls the
sources live.

Files in git:

- `listings.jsonl` - one JSON object per listing, as written by `normalise.py`. Media and
  stations are nested lists. It keeps the scraped EPC values (see Demo EPC values).
- `listings.csv` - the same rows. List fields are JSON-encoded strings. Scraped EPC values.
- `listings.sqlite` - the D1-ready database, built from `d1/schema.sql` by
  `scripts/build_d1.py`. Three tables; see Schema below. It carries demo EPC values.
- `d1/schema.sql` - the table definitions, the single source of truth for the data shape.
- `d1/seed.sql` - plain `INSERT` statements for every row, generated from the same data.
  It carries the same demo EPC values as `listings.sqlite`.
- `reports/normalise-report.txt` and `reports/d1-build-report.txt` - counts from the last
  run of each script.
- `scripts/` - the fetch, normalise, sanitise and build scripts. Python standard library
  only.
- `tests/test_sanitise.py` - unit tests for the sanitise rules.
- `tests/test_build_d1.py` - tests for the demo EPC pass, the D1 build, the train/eval
  split and the duplicate guard.
- `tests/test_normalise_append.py` - tests for append mode: existing records kept
  unchanged, each dedupe rule, and the refusal to shrink `listings.jsonl`.
- `tests/test_fetch_rapidapi.py` - tests for the fetch script's known-id skip and price
  band options.
- `requirements.txt`, `.env.example`.

Not in git:

- `raw/` - every response as downloaded, ignored by `.gitignore`. It exists only on the
  machine that ran the fetch. When the 24 Oct additions were built, `raw/rightmove` was not
  there and `raw/rapidapi` held only the 24 Oct 2026 responses, so the 398 older
  listings were kept from `listings.jsonl` (append mode) and a full rebuild from `raw/`
  was not possible. A fresh clone can still rebuild `listings.sqlite` and `seed.sql` from
  `listings.jsonl` with `build_d1.py`.
- `.env` - your RapidAPI key (`RAPID_API_KEY`). Never committed. It can sit in `dataset/`
  or in the repository root.

## Sources

Both sources are Rightmove. Neither is an official or licensed feed.

| Source                                                       | `source` value                      | Listings | How it was accessed                                                                                             | Terms of service                                                                                                                                                                                                              |
| ------------------------------------------------------------ | ----------------------------------- | -------- | --------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| rightmove.co.uk, direct                                      | `rightmove`                         | 372      | `scripts/fetch_rightmove.py` downloads public search and property pages and reads the JSON embedded in them.    | **Against Rightmove's terms.** Their terms forbid automated access and copying of listing data. robots.txt was checked before every URL and every fetched path was allowed, but robots.txt is not permission under the terms. |
| "UK Real Estate Rightmove" API on RapidAPI (provider ntd119) | `rapidapi_uk_real_estate_rightmove` | 263      | `scripts/fetch_rapidapi.py`, endpoints `/auto-complete`, `/buy/property-for-sale` and `/buy/property-for-sale/detail`. Quota about 300 calls a month; 6 were left on 24 Oct. | **Unofficial.** A third party resells data taken from Rightmove's app. Rightmove has not licensed it. RapidAPI's own terms apply to the key holder.                                                                           |

Rules followed when scraping: about one request every 2.5 s (the script refuses a delay
under 2 s), one request at a time, a descriptive User-Agent, no login, no cookies kept,
no CAPTCHA handling, and the script stops on HTTP 403/429 or a challenge page instead of
retrying. No Rightmove request was blocked or challenged: all 423 logged page requests returned
HTTP 200. Of the 292 RapidAPI calls made on 24 Oct, one detail call returned HTTP 400
(a permanent answer, not retried); the other 291 returned 200.

Zoopla and OnTheMarket were looked at (their robots.txt responses are in `raw/robots/`)
but not used. Zoopla answered robots.txt with a Cloudflare challenge page, so it was
left alone.

Use this data for the hackathon demo only. Do not publish it. The photos, floorplans and
descriptions belong to the agents and Rightmove. Only image URLs are stored; no image
was downloaded.

## When it was pulled, and API calls used

Three pulls. The first, on 23 October 2026 between 22:51 and 23:17 UTC, gave the original
398 listings: 372 Rightmove direct and 26 RapidAPI. The second, on 24 October 2026 from
10:00:16 to 10:19:50 UTC (first and last logged call), added 161 RapidAPI listings. The
third, the same day from 10:50:58 to 10:57:12 UTC, was a top-up for cheaper homes and
added 76 more. All three together give 635.

- Rightmove direct (23 Oct): 423 logged page requests (`raw/rightmove/_manifest.jsonl`),
  plus one unlogged robots.txt fetch per script run. That manifest is not on every
  machine.
- RapidAPI, 23 Oct: 28 calls (2 search, 26 detail) on `RAPIDAPI_KEY`, logged in
  `raw/rapidapi/_calls.log` (metadata only, no key). That log no longer exists on the
  machine that made the 24 Oct pulls.
- RapidAPI, 24 Oct: 292 calls on `RAPID_API_KEY`, logged in a fresh
  `raw/rapidapi/_calls.log`: 190 in the first pull and 102 in the top-up. Per-area counts
  are in `evidence/dataset-extend/fetch.md`.

| Pull          | Key              | Endpoint                          | Calls |
| ------------- | ---------------- | --------------------------------- | ----- |
| 23 Oct        | `RAPIDAPI_KEY`   | `/buy/property-for-sale`          | 2     |
| 23 Oct        | `RAPIDAPI_KEY`   | `/buy/property-for-sale/detail`   | 26    |
| 24 Oct first  | `RAPID_API_KEY`  | `/auto-complete`                  | 10    |
| 24 Oct first  | `RAPID_API_KEY`  | `/buy/property-for-sale`          | 10    |
| 24 Oct first  | `RAPID_API_KEY`  | `/buy/property-for-sale/detail`   | 170 (169 returned 200, 1 returned 400) |
| 24 Oct top-up | `RAPID_API_KEY`  | `/buy/property-for-sale`          | 22 (20 band searches and 2 sort probes) |
| 24 Oct top-up | `RAPID_API_KEY`  | `/buy/property-for-sale/detail`   | 80    |
| -             | `RAPIDAPI_KEY_2` | none                              | 0, never used |

The 24 Oct calls add up to 292 (10 + 10 + 170 + 22 + 80), 8 under the cap of 300 set for
this work. The provider's rate-limit header (`x-ratelimit-requests-remaining`) reported 272
left after the last call on 23 Oct (`RAPIDAPI_KEY`). On 24 Oct it reported 297 after the
first call, 108 after the last call of the first pull and **6 after the last logged call**
(`RAPID_API_KEY`). The drops match the logged counts (190, then 102). The provider
header, not the script's own count, is the real balance. **This month's quota is nearly
spent: 6 calls are left**, so nothing more can be fetched until it resets. Whether
`RAPID_API_KEY` and `RAPIDAPI_KEY` are the same account is not recorded.

The scripts stop a key at 250 calls a month by their own count (`--cap`, default 250).
The 24 Oct pulls ran with `--cap 300`. The counter reads `_calls.log`, which held only the
24 Oct calls, so it could not see the 28 from 23 Oct.

## Selection rules

Applied in `scripts/rm_common.py` and `scripts/normalise.py`:

- for sale only; no auctions, shared ownership, retirement homes or archived listings;
- price £250,000 to £1,200,000;
- at least 6 photos and at least 1 floorplan;
- tenure known;
- latitude and longitude present.

Rightmove searches (`fetch_rightmove.py`, `PLAN`, 23 Oct), first page of results, sorted
newest first (`sortType` 6):

- 1-3 bed flats, up to £800k: Islington, Hackney, Lambeth, Camden, Southwark, Tower
  Hamlets, Wandsworth, Lewisham;
- houses, up to £1.2m: Lewisham, Waltham Forest, Ealing;
- any type, up to £1.2m: St Albans, Watford, Reading.

RapidAPI searches, 23 Oct: Islington 1-3 bed flats (one search, one detail call, from
the first probe) and Guildford, any type (one search, 25 detail calls). The order those two
searches came back in was not recorded; their log is gone.

RapidAPI searches, 24 Oct, first pull: page 1 only, price £250,000 to £1,200,000, any
property type, no retirement homes, no buying schemes, no flats-only filter. Each place
name went through `/auto-complete`, and `data[i].locationIdentifier` was used as the
identifier. Seven commuter towns got up to 20 detail calls each, three London boroughs up
to 10 each.

| Area                   | Identifier       | Detail calls |
| ---------------------- | ---------------- | ------------ |
| Brighton               | `REGION^93554`   | 20           |
| Cambridge              | `REGION^274`     | 20           |
| Croydon (borough)      | `REGION^93944`   | 20           |
| Kingston upon Thames (borough) | `REGION^93968` | 20     |
| Oxford                 | `REGION^1036`    | 20           |
| Chelmsford             | `REGION^307`     | 20           |
| Sevenoaks              | `REGION^1191`    | 20 (1 returned HTTP 400) |
| Greenwich (borough)    | `REGION^61226`   | 10           |
| Haringey (borough)     | `REGION^61227`   | 10           |
| Hammersmith and Fulham (borough) | `REGION^61407` | 10   |

Croydon and Kingston are in the commuter-town group because that is how the plan counted
them, but their identifiers are the London borough entries. No area was swapped.

RapidAPI searches, 24 Oct, top-up: the first pull turned out to be expensive homes (see
Search order and price skew), so each of the same ten areas was searched again in two
price bands, £250,000 to £450,000 and £450,000 to £700,000, page 1 each (20 searches).
Brighton also had two probe searches that tried the `sort_by` values 1 and 2. 80 detail
calls followed: 9 per commuter town (5 from the lower band, 4 from the upper), 6 per
borough except Hammersmith and Fulham with 5. All 80 returned 200.

### Search order and price skew

Neither source is a random sample, and they are ordered differently.

- **Rightmove direct (23 Oct)** was sorted newest first.
- **RapidAPI (24 Oct)** came back **highest price first** on every search page: in all 32
  saved search files, cards 2 to 25 are in falling price order, and card 1 (one featured
  card) is cheaper than card 2. Setting `sort_by` to 1 or to 2 did not change this
  (Brighton, £250k to £700k: 24 of 25 cards at exactly £700,000 either way). No other
  `sort_by` value was tried because the calls were nearly gone. The accepted values are
  not documented.
- **First 24 Oct pull.** Each area's page 1 is therefore its top-priced 25 cards under
  £1.2m, and the detail calls took 10 or 20 of them. Of the 161 homes this added, 52 are
  at exactly £1,200,000, 33 at £1,150,000 and 19 at £1,100,000 (104 of 161). Their median is
  £1,150,000.
- **Top-up.** Each band's page 1 is again its highest-priced cards, so the fetched cards
  bunch at the band edges: of the 80 fetched cards, 40 were at exactly £450,000 and 23 at
  exactly £700,000 (`evidence/dataset-extend/fetch.md`). Of the 76 records that reached the
  dataset (4 of the 80 dropped for no tenure), 37 are at £450,000 and 22 at £700,000, and 17
  are elsewhere (lowest £265,000). Their median is £450,000.
- **Are the prices real?** Yes. For all 237 homes added on 24 Oct (161 + 76), the price in
  `listings.jsonl` equals the price on the saved detail page (checked by script, 237 of
  237). Round figures like £450,000 and £700,000 are asking prices; the skew comes from
  which cards the search returns, not from wrong prices.

The result is a dataset heavy at £1.2m and thin elsewhere (see Distributions). It is not a
sample of the market and each area's mid-priced homes are under-represented.

### What was dropped

First pull (23 Oct, the original 398 listings):

| Stage                                | Reason                         | Count |
| ------------------------------------ | ------------------------------ | ----- |
| Search card, before fetching details | auction                        | 14    |
| Search card                          | fewer than 6 photos            | 9     |
| Search card                          | no floorplan                   | 5     |
| Search card                          | same property in two searches  | 5     |
| Detail page                          | tenure not stated anywhere     | 6     |
| Dedupe                               | same home listed by two agents | 14    |

That is 20 thin listings dropped (photos, floorplan, tenure) and 14 auctions. No
RapidAPI record was dropped in that pull. Of the 50 RapidAPI search results, 23 Islington
flats were never fetched in detail, to save calls, and 1 failed the selection rules on its
card.

Append run 1 (24 Oct, first pull; `evidence/dataset-extend/append-runs.md` and
`evidence/dataset-extend/fetch.md`):

| Stage                       | Reason                                                  | Count |
| --------------------------- | ------------------------------------------------------- | ----- |
| Search card                 | not passing the card rules, or a repeated card (250 cards seen, 244 distinct passed) | 6 |
| Detail call                 | HTTP 400 (Sevenoaks, id 94155597), not retried          | 1     |
| Search card                 | passed the card rules but not fetched in detail (call budget; the script also skips ids already in `listings.jsonl`) | 74 |
| Build, thin rules           | tenure not stated anywhere                              | 6     |
| Append dedupe               | same coordinates, bedrooms and price                    | 2     |
| Append dedupe               | same id, same delivery point id, shared photo URL       | 0     |
| Sanitise                    | missing required field                                  | 0     |

That is 169 detail files saved, 163 records built, 2 dropped as duplicates and **161
added**: 398 + 161 = 559. The report does not say whether each of the 2 geo duplicates
matched an existing or a new record.

Append run 2 (24 Oct, after the top-up; `reports/normalise-report.txt`):

| Stage                       | Reason                                                  | Count |
| --------------------------- | ------------------------------------------------------- | ----- |
| Build, thin rules           | tenure not stated anywhere (6 from run 1 and 4 more)    | 10    |
| Append dedupe               | same id as a record already in `listings.jsonl` (the 161 from run 1, rebuilt from `raw/`) | 161 |
| Append dedupe               | same coordinates, bedrooms and price                    | 2     |
| Append dedupe               | same delivery point id, shared photo URL                | 0     |
| Sanitise                    | missing required field                                  | 0     |

249 detail files (169 + 80) gave 239 built records; 161 of them were already in the file,
2 were dropped on coordinates, bedrooms and price, and **76 were added**: 559 + 76 = 635.
By arithmetic the 2 coordinate duplicates are the same two dropped in run 1 (239 = 161 + 2
+ 76, and the 80 top-up files = 76 + 4 thin), so the top-up itself lost 4 files to the
tenure rule and none to dedupe. The report does not state this directly. Each run
overwrites `reports/normalise-report.txt`; run 1's counts are kept in
`evidence/dataset-extend/append-runs.md`.

Deduplication (full rebuild) links two records if they share a Rightmove id, a Royal Mail
delivery point id, or the same coordinates (4 decimal places), bedrooms and price. The
record with the most filled fields is kept. Two records from the same agent are never
linked on delivery point or coordinates, because developers list several units of one
new-build under one placeholder address. This keeps 6 Taylor Wimpey homes on Chiswell
Green Lane, St Albans, as separate listings: they share no photo URLs, but two pairs have
the same price and bedrooms, so the app will show similar cards. There were no
duplicates across the two sources in the first pull, because `details` skips homes already
scraped.

Two more rules came with the 24 Oct pull:

- **Shared photo URL.** Two listings that share any photo URL are one home. There is no
  same-agent exception. It dropped 0 records on this data. The comparison is on exact URL
  strings. It is in append mode and in the D1 build guard; the full-rebuild `dedupe()` in
  `normalise.py` does not have it.
- **Append mode.** `normalise.py --append` keeps `listings.jsonl` as it is (the first 398
  lines are byte-identical to the original file, and the first 559 to the output of run 1)
  and builds new records from `raw/rapidapi`. It was run twice, once per fetch (see above). It is a single greedy pass: the existing records are registered first,
  so on a clash the existing record is kept; the new records then go in richest first, and
  each is dropped if it matches anything already registered by id, delivery point id,
  coordinates + bedrooms + price, or photo URL. The same-agent waiver applies to the
  delivery-point and coordinates rules only. A chain of matches through a dropped record
  is not followed. Existing records carry no delivery point id, so that rule only catches
  new against new.

The D1 build repeats the check as a guard. `build_d1.py` aborts (exit 1, naming the two
ids) if two listings share an id, share a photo URL (floorplans do not count), or share
coordinates (4 dp) + bedrooms + price. The coordinates rule is waived when the same agent
listed both, the same waiver as above, which is why the two Taylor Wimpey pairs pass.
A shared id or a shared photo URL is never waived.

## Schema

`d1/schema.sql` is the source of truth. Read it for exact columns, types, CHECK bounds and
a comment on each column giving its unit and what NULL means. In brief:

- `listings` - one row per listing (id `rm-<Rightmove id>`). Flat scalar columns: price,
  bedrooms, bathrooms, property type, address, postcode, lat/lon, tenure, lease, service
  charge, ground rent, council tax band, EPC rating, floor level, description, agent,
  dates, and `split`. `key_features` and `parsed_fields` are JSON arrays of strings held
  as text. `split` is `'train'` or `'eval'` (`NOT NULL`, with a CHECK); `build_d1.py`
  assigns it, so it is in `listings.sqlite` and `seed.sql` but not in `listings.jsonl`
  or `listings.csv` (see Train/eval split).
- `listing_media` - one row per image: `(listing_id, kind, position, url)` with `kind` one
  of `photo`, `floorplan`, `epc`. The primary key is `(listing_id, kind, position)`;
  `position` is 0-based within the listing and kind. Later photo flags are meant to join
  on that key. The schema still allows `epc`, but the built database has no `epc` rows
  (see Demo EPC values).
- `listing_stations` - one row per nearby station: `(listing_id, position, name,
  distance_km, types)`, nearest first. `types` is a JSON array.

Both child tables have a foreign key to `listings.id` with `ON DELETE CASCADE`. The old
columns `photo_urls`, `floorplan_urls`, `epc_image_urls` and `nearest_stations` no longer
exist as columns; the child tables replace them.

## Sanitise rules

`scripts/sanitise.py` runs as the last pass of `normalise.py`. Its bounds repeat the CHECKs
in `schema.sql` by hand, and a test checks the two agree. A value that breaks a bound is
set to NULL and counted in `reports/normalise-report.txt`, never altered to fit.

- **Unknown is NULL.** Never `0` and never an empty string. Blank text becomes NULL.
- **A real 0 stays 0.** A 0 in service charge, ground rent, bathrooms or any other money
  or count field means zero, not unknown.
- **Lease of 0 becomes NULL.** Rightmove fills `yearsRemainingOnLease` with 0 when no
  lease is given, and the schema allows 1 to 999.
- **Enums.** Property type maps to a fixed set (`flat`, `maisonette`, `house`, `terraced`,
  `semi_detached`, `end_of_terrace`, `detached`, `bungalow`, `other`). "Apartment",
  "Penthouse" and "Ground Flat" become `flat`; "Not Specified" becomes NULL; "Block of
  Apartments" becomes `other`. Tenure is `freehold`, `leasehold` or `share_of_freehold`.
  Council tax band is A to H and EPC rating A to G, upper case; "TBC" becomes NULL.
  Price qualifier is `guide_price`, `offers_over`, `offers_in_region` or `fixed_price`.
- **Distances in km.** Rightmove shows station distances in miles. The web pages say so.
  The RapidAPI response gives no unit, and a distance with no unit is read as miles.
  Every distance is converted to `distance_km` (rounded to 3 places).
- **Clean text.** HTML tags are removed and entities decoded (`&amp;` becomes `&`) in the
  description and key features. Whitespace is collapsed; paragraph breaks in the
  description are kept. Floor level is lower case.
- **Dates.** `listed_date` and `fetched_at` are ISO 8601 UTC, `YYYY-MM-DDTHH:MM:SSZ`. A
  value that is not a date becomes NULL (for `fetched_at`, the row is dropped). A time
  with no zone is read as UTC.
- **Ranges.** Price 10,000 to 50,000,000; bedrooms and bathrooms 0 to 10; lease 1 to 999
  years; service charge and ground rent 0 to 100,000 a year; distance 0 to 100 km; lat
  50.5 to 52.5; lon -2.5 to 1.5 (South East England). A row missing a required field
  (`id`, `source`, `source_id`, `url`, `price_gbp`, `fetched_at`) is dropped and counted.
  The last run dropped none: 635 in, 635 kept.

## Demo EPC values

`listings.sqlite` and `d1/seed.sql` hold demo EPC data, added by `build_d1.py` when it
reads `listings.jsonl`. `listings.jsonl` and `listings.csv` are not changed and keep the
scraped values.

- **Chart images and PDFs are gone from the D1 outputs.** Every `epc` media row is
  dropped, so `listing_media` has no `epc` rows. The scraped URLs (515 listings, 542
  rows) remain in `listings.jsonl`.
- **`epc_current`.** The 148 letters found in agent text are kept. Each of the other 487
  listings gets a made-up letter, drawn at random with a fixed seed (`EPC_SEED`,
  20261024) and weighted to the spread of the 148 real letters (C 65, D 43, B 33, E 6, A 1).
- **`epc_potential`.** Made up for all 635 listings: the current letter improved by 0, 1
  or 2 bands (weights 20, 50 and 30), never better than A. The scraped data has none.
- **No marker.** Nothing in the database says which letters are made up. The only way to
  tell is to compare with `listings.jsonl`: where `epc_current` is NULL there, the letter
  in the database is made up. Every `epc_potential` is made up.
- **Repeatable.** The same input gives byte-identical outputs. Listings are drawn in id
  order from one seeded generator, so adding, removing or renaming any listing changes
  every made-up letter after it. Growing the set (398, then 559, then 635 listings)
  therefore changed many of the made-up letters of the earlier builds. The train/eval
  split does not have this problem (see Train/eval split).

This is demo data. Do not treat it as the real rating of any home.

## Coverage

635 listings. Percentages are of all 635 unless stated. Counted from `listings.sqlite`,
except the two scraped EPC lines and the EPC chart image line, which are counted from
`listings.jsonl`. The counts match `reports/normalise-report.txt` and
`reports/d1-build-report.txt`.

| Field                                         | Count                                    | %    | Notes                                                                                           |
| --------------------------------------------- | ---------------------------------------- | ---- | ----------------------------------------------------------------------------------------------- |
| `epc_current` in `listings.sqlite`            | 635                                      | 100% | 148 real, from the agent's own text, e.g. "EPC Rating: C", not checked against the certificate. 487 made up. |
| `epc_potential` in `listings.sqlite`          | 635                                      | 100% | All made up.                                                                                    |
| `epc_current` in `listings.jsonl` (scraped)   | 148                                      | 23%  | 487 are NULL.                                                                                   |
| `epc_potential` in `listings.jsonl` (scraped) | 0                                        | 0%   | Never found in text. Always NULL in the scraped files.                                          |
| EPC chart image (`epc` media rows)            | 0 in `listings.sqlite`; 515 listings (542 rows) in `listings.jsonl` | 81% scraped | The chart Rightmove shows. A few are PDFs. The rating in the image was **not** read. |
| floorplan (at least 1)             | 635 (672 rows)                           | 100% | Required.                                                                                       |
| `tenure`                           | 635                                      | 100% | Required. 2 taken from text.                                                                    |
| `lease_years_remaining`            | 225 of 296 leasehold / share of freehold | 76%  | 5 from text. 1 freehold listing also carries a lease (see limitations).                         |
| `service_charge_gbp_pa`            | 207 of 296 leasehold / share of freehold | 70%  | 10 from text. 13 of these are 0.                                                                |
| `ground_rent_gbp_pa`               | 159 of 296 leasehold / share of freehold | 54%  | 8 from text. 31 of these are 0.                                                                 |
| `council_tax_band`                 | 506                                      | 80%  | The rest are NULL, including "TBC".                                                             |
| `floor_level`                      | 212                                      | 33%  |                                                                                                 |
| `bathrooms`                        | 621                                      | 98%  |                                                                                                 |
| `property_type`                    | 632                                      | 100% | 3 are NULL: "Not Specified", "Cottage" and "Barn Conversion" (the last two are not in the enum). |
| 6 or more photos                   | 635                                      | 100% | Required. 548 (86%) have 10 or more; at most 10 URLs are kept (6,169 `photo` rows).             |
| `lat` / `lon`                      | 635                                      | 100% | Required.                                                                                       |
| full postcode                      | 635                                      | 100% |                                                                                                 |
| `listed_date`                      | 635                                      | 100% |                                                                                                 |
| stations (`listing_stations`)      | 635 listings (1,889 rows)                | 100% | Every row has a `distance_km`. 1,116 have a transport type; the 773 RapidAPI rows (263 listings) have none. |

Row counts in `listings.sqlite`: `listings` 635, `listing_media` 6,841 (photo 6,169,
floorplan 672, epc 0), `listing_stations` 1,889.

`epc_current` counts in `listings.sqlite`: A 4, B 143, C 281, D 184, E 23.
`epc_potential` counts: A 200, B 227, C 159, D 43, E 6. Both include made-up values.

Scraped `epc_current` counts in `listings.jsonl`: C 65, D 43, B 33, E 6, A 1, none 487.

`parsed_fields` on each row lists every field that was taken from free text rather than
a structured field, so the app can treat those values with less trust.

## Distributions

Counted with `python3 -I` from `listings.jsonl` and `listings.sqlite` (635 rows each);
the figures agree with `reports/normalise-report.txt` and `reports/d1-build-report.txt`.

Price: minimum £250,000, median £700,000, maximum £1,200,000.

| Price band  | Listings |
| ----------- | -------- |
| £250k-£400k | 74       |
| £400k-£550k | 142      |
| £550k-£700k | 79       |
| £700k-£900k | 150      |
| £900k-£1.2m | 190      |

Each band includes its lower bound; the top band includes £1.2m itself, where 52
listings sit exactly (583 are below it). These figures carry the price skew described in
Search order and price skew. By pull:

| Pull                          | Listings | Median     | Notes                                                    |
| ----------------------------- | -------- | ---------- | -------------------------------------------------------- |
| Original (23 Oct)             | 398      | £600,000   | Highest £1,195,000; none at £1.2m.                       |
| 24 Oct first pull             | 161      | £1,150,000 | 52 at £1.2m, 33 at £1.15m, 19 at £1.1m.                  |
| 24 Oct top-up                 | 76       | £450,000   | 37 at £450,000, 22 at £700,000, 17 elsewhere.            |

Across all 635, 47 sit at exactly £450,000 and 33 at exactly £700,000. The top-up figures
are for the records that were appended; the 80 fetched cards were 40 at £450,000 and 23
at £700,000.

Bedrooms: studio (0) 1, 1 bed 73, 2 bed 196, 3 bed 168, 4 bed 117, 5 bed 64, 6 bed 14,
7 bed 1, 8 bed 1.

Type (`property_type`): flat 279, detached 102, semi_detached 80, terraced 77,
end_of_terrace 36, house 29, maisonette 17, bungalow 7, other 5, NULL 3.

Tenure: freehold 339, leasehold 236, share of freehold 60.

Area (postcode area, counted from `listings.sqlite`). London here means the postcode
areas used by the split: E, EC, N, NW, SE, SW, W, WC, BR, IG, CR and KT.

| Area      | Postcode areas                                                                    | Listings |
| --------- | --------------------------------------------------------------------------------- | -------- |
| London    | SE 92, N 69, E 66, SW 64, W 30, KT 26, NW 17, EC 15, CR 15, WC 3, BR 2, IG 2       | 401      |
| Cambridge | CB                                                                                | 29       |
| Chelmsford | CM                                                                               | 28       |
| Sevenoaks | TN                                                                                | 28       |
| Brighton  | BN                                                                                | 28       |
| Oxford    | OX                                                                                | 27       |
| Guildford | GU                                                                                | 25       |
| St Albans | AL                                                                                | 24       |
| Reading   | RG                                                                                | 24       |
| Watford   | WD                                                                                | 21       |

## Train/eval split

Every listing in `listings.sqlite` and `seed.sql` has a `split` of `train` or `eval`,
aiming at 25% eval. It is assigned only in the D1 build (`build_d1.py`), never in
`listings.jsonl` or `listings.csv`.

- **Method.** Listings at the same coordinates, rounded to 4 decimal places, form a group
  (a listing with no coordinates is a group of one, keyed by its id). Each group's side
  comes from `sha256("<SPLIT_SEED>|<group key>")`: the first 8 bytes, read as a number
  between 0 and 1, put the group in `eval` if it is below 0.25 (`EVAL_SHARE`) and in `train`
  otherwise. `SPLIT_SEED` is 20261025, separate from `EPC_SEED` (20261024).
- **Stable.** The decision uses only the seed and the group's own coordinates, so adding
  listings never moves an existing one. Building the first 559 lines of `listings.jsonl`
  and all 635 gives the same side for each of those 559 listings. Changing the seed, the
  threshold or the key format would reassign every listing.
- **Not exactly balanced.** Because each group is decided alone, the eval share is about
  25% by chance. It is not forced. There is no London versus outside balancing any more.
- **Groups.** Near-identical new-build units at one address never straddle the split. The
  largest group is 6 listings; 6 groups hold more than one listing.
- **Result** (from `reports/d1-build-report.txt`). London here means the postcode areas
  E, EC, N, NW, SE, SW, W, WC, BR, IG, CR and KT; a listing with no postcode would count
  as outside London (none in the data).

| Group          | Listings | Train | Eval | Eval share |
| -------------- | -------- | ----- | ---- | ---------- |
| All            | 635      | 488   | 147  | 23.1%      |
| London         | 401      | 301   | 100  | 24.9%      |
| Outside London | 234      | 187   | 47   | 20.1%      |

The tests check the split against 25% plus or minus 2 points overall and plus or minus 5
points for London and for outside London. All three are inside, but **outside London is
only 0.1 of a point from its bound** (20.1% against a floor of 20%). A later append can
push it below, and the share test would then fail.

- **Per postcode area the share is not balanced.** It runs from 0% (BR and IG: 0 of 2
  each) to 66.7% (WC: 2 of 3). Among areas with 20 or more listings it runs from 12.5% (AL:
  3 of 24) to 34.8% (SE: 32 of 92). The split is not stratified on price, bedrooms or type.
- The build report has the full per-area table.

## Known limitations and shortcuts

- **EPC rating is the weak field in the scraped source.** The database fills the gaps
  with made-up demo values (see Demo EPC values). Neither source has a structured EPC rating. The
  Rightmove page and the RapidAPI detail response both give only the chart image URL
  (`epcGraphs` and `epcs`), so spending API calls on existing listings would not have
  added a single rating. Ratings come only from agent text. Reading the letter from the
  chart image would need OCR or a vision model, which is out of scope here. The other
  route is the government EPC register, matched by address; that is a new service and
  was not used.
- **Text parsing.** Tenure, lease, service charge, ground rent, council tax, floor level
  and EPC fall back to regular expressions over the description when the structured
  field is empty. The EPC matches were spot-checked by eye; the others were not checked
  one by one.
- **Lease of 0.** Rightmove fills `yearsRemainingOnLease` with 0 when no lease applies.
  0 is stored as null. One freehold apartment still carries a 114-year lease because
  the agent entered both.
- **Zero money values** are kept as 0, as the agent stated them. 8 freehold listings have
  a service charge of 0 and 5 a ground rent of 0; some may be filler rather than fact.
  Two RapidAPI listings have 0 bathrooms. For the 4-bed house `rm-94396305` the description
  mentions an en suite bathroom; the other (`rm-94529214`, a flat) was not checked.
- **Scraped EPC rating coverage is low.** Only 148 of 635 (23%) have a real letter in
  `listings.jsonl`; see the first point. `listings.sqlite` has a letter on every listing,
  but 487 are made up.
- **The data is unofficial and against Rightmove's terms** (see Sources). Demo use only.
- **`seed.sql` is not idempotent.** It needs empty tables. A second import fails on the
  primary keys.
- **Station types.** RapidAPI's station `type` code is not decoded, so those 773 stations
  (263 listings) have `types` = `[]`, meaning "none given".
- **Some bounds are judgement calls.** Price, bedroom, lease and money limits in the
  schema catch obvious bad data with wide margins. A listing outside the South East is
  rejected until the lat/lon bounds change.
- **Dates:** the schema checks the shape of a date, not that it is a real calendar day.
- **Every search is the first page only.** Rightmove direct was sorted newest first. The
  RapidAPI searches took page 1 as returned, which was highest price first (see Search
  order and price skew), so the RapidAPI listings are not a snapshot of recent listings
  and not a sample of the market. A separate exception in the Rightmove direct data is
  three files from an earlier run, `raw/rightmove/search/{Hackney,Islington,Lambeth}_flats_0.html.gz`,
  which used Rightmove's default sort (highest price). Their listings are included. A
  fresh re-run will not reproduce them, because `PLAN` no longer requests them.
- **Flats were capped at £800k** in the Rightmove direct flat searches, so expensive
  flats from that source are missing. The 24 Oct RapidAPI searches had no flat filter and
  no cap. Of the 210 listings over £800k, 193 are not flats (192 houses and other types, 1 with
  no type) and 17 are flats, all from RapidAPI.
- **4 or more bed homes are 31%** (197 listings), from the house and commuter-belt
  searches. The brief asked for mostly 1-3 beds; 69% (438, counting one studio) are.
- **London is 63% of the data** (401 of 635, by the postcode areas above). The commuter
  belt is nine places: St Albans, Watford, Reading, Guildford, Cambridge, Brighton,
  Chelmsford, Sevenoaks and Oxford, 234 listings in all. Postcodes in CR and KT count as
  London, so a CR or KT postcode outside Croydon or Kingston (for example Caterham or
  Esher) would be counted as London by the split. Every CR and KT listing in the data is
  in Croydon or Kingston.
- **The 24 Oct pulls are thin per area.** Each area got one first-pull search page and
  one top-up search per price band, and 10 to 20 first-pull plus 5 to 9 top-up detail
  calls, so each new area holds at most 29 listings (Cambridge). The quota (6 calls
  left) rules out fetching more this month.
- **Price is skewed.** The 161 first-pull listings are each area's top-priced slice and
  the 76 top-up listings bunch at £450,000 and £700,000. See Search order and price skew.
  Anything that assumes a spread of prices (a price-based eval, a price-band filter test)
  will see this. The `sort_by` values 1 and 2 did nothing; no other value was tried.
- **Prices are as advertised**, including "Guide Price" and "Offers in Excess of"
  (`price_qualifier`).
- **RapidAPI rows** have no floor level from structured data and no station distance
  unit. The API does not say whether its distances are miles or km. They are read as
  miles; the evidence is three stations that appear in both feeds, where the API figure
  matched the web page's miles within 0.01 and not as km.
- **Dedupe is heuristic.** It may merge two different homes or miss a duplicate listed
  with different coordinates. The photo rule compares exact URLs, so the same image at
  another size or path would not match, and it has no same-agent exception. Append mode is
  one greedy pass and does not follow a chain of matches through a dropped record. The
  full-rebuild `dedupe()` has no photo rule.
- **Odd property types:** five listings are `other` (one is a "Block of Apartments"; the
  source type of the other four is not kept in `listings.jsonl`); three are NULL
  ("Not Specified", "Cottage" and "Barn Conversion").
- **The split is not balanced.** It is a hash per coordinate group, stable when listings
  are added but only about 25% by chance (23.1% overall, outside London 20.1%, 0.1 of a
  point above the test's floor). Per postcode area the eval share ranges from 0% to 66.7%
  (see Train/eval split).
- **Stale listings.** Homes sell. Some URLs will 404 within weeks.
- The fetch scripts make one robots.txt request per run that is not written to the
  manifest.

## What could bite

- **The split can break its own bound.** It is a hash, so it is stable when listings are
  added but not balanced. Outside London is 20.1% eval, 0.1 of a point above its 20%
  floor. A later append can push it below, and then someone must choose a new seed, a
  wider bound, or accept it. See Train/eval split.
- **Cheap homes outside London are thin.** Only 37 of the 234 outside-London listings are
  under £450,000 (114 of 635 overall). Budget personas below about £450k may get short
  decks. Check the pool size per persona after the hard filters, before the persona
  batch. See Search order and price skew.
- **`normalise.py --append` overwrites its report.** On the real data it adds nothing but
  still rewrites `reports/normalise-report.txt`. The counts of both append runs are in
  `evidence/dataset-extend/append-runs.md`. A plain run without `--append` is refused
  here because `raw/rightmove` is gone. See Re-running.
- **Some photo URLs repeat inside one listing.** Eight URLs repeat, in 7 listings, never
  across listings. The duplicate guard is unaffected, but a photo count can include
  repeats.

## Re-running

From the repository root:

```bash
cd dataset
cp -n .env.example .env       # -n: never overwrites an existing .env; then paste your RapidAPI key into it
```

The key is `RAPID_API_KEY`. The old names `RAPIDAPI_KEY` and `RAPIDAPI_KEY_2` are still
read. The fetch script looks in the environment first, then `dataset/.env`, then the
`.env` in the repository root.

A virtual environment is optional. The scripts use the Python standard library only
(run with Python 3.14), and `requirements.txt` lists no packages. If
you want one anyway:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # installs nothing
```

Rebuild the outputs. Run the three steps in this order:

```bash
cd dataset

# 1. raw/ -> listings.jsonl, listings.csv, reports/normalise-report.txt
#    Full rebuild: needs raw/rightmove and raw/rapidapi.
python3 -I -B scripts/normalise.py --dataset .
#    Append mode: keeps listings.jsonl, adds new records from raw/rapidapi only.
python3 -I -B scripts/normalise.py --dataset . --append

# 2. tests
python3 -I -B -m unittest discover -s tests

# 3. listings.jsonl -> listings.sqlite, d1/seed.sql, reports/d1-build-report.txt
python3 -I -B scripts/build_d1.py --dataset .
```

Run the commands from `dataset/`. Of the two `normalise.py` lines, use one, not both.

Without `raw/rightmove`, a plain run builds fewer listings than `listings.jsonl` holds,
so it is refused ("refusing to write ... use --append") and the file is left alone. Use
`--append` there. `--append` was run twice on this data, once after each 24 Oct fetch; the
counts of both runs are in `evidence/dataset-extend/append-runs.md`. A run with nothing
new leaves `listings.jsonl` and `listings.csv` unchanged, but it overwrites
`reports/normalise-report.txt` with a report that adds nothing (every new record is
dropped as a duplicate by id), so copy the report first if you want to keep the counts of
the real run.

`unittest discover` runs every test file in `dataset/tests`. `build_d1.py` loads
`d1/schema.sql` with foreign keys on, so the schema's constraints are the validation. It
stops at the first violation and names the listing id and constraint. It also aborts on
a duplicate (see Deduplication). It does not need `raw/`.

Fetch again. Each script skips files already in `raw/`, so a re-run only fetches what
is missing. Delete the relevant `raw/` files first to refresh them.

```bash
# Rightmove direct (whole plan; about 2.5 s per request)
python3 -I -B scripts/fetch_rightmove.py --raw raw/rightmove
python3 -I -B scripts/fetch_rightmove.py --raw raw/rightmove --list-plan
python3 -I -B scripts/fetch_rightmove.py --raw raw/rightmove --resolve Guildford

# RapidAPI (the quota is nearly spent: 6 calls were left on 24 Oct)
python3 -I -B scripts/fetch_rapidapi.py --dataset . budget
# find the identifier for a place name (one call; prints each locationIdentifier)
python3 -I -B scripts/fetch_rapidapi.py --dataset . --cap 300 autocomplete --query Brighton
python3 -I -B scripts/fetch_rapidapi.py --dataset . --cap 300 search --identifier 'REGION^93554' --pages 1
python3 -I -B scripts/fetch_rapidapi.py --dataset . --cap 300 details --max 20 --identifier 'REGION^93554'
# a price band: search takes --min-price/--max-price (and --sort, passed on as sort_by,
# whose accepted values are not documented; 1 and 2 changed nothing)
python3 -I -B scripts/fetch_rapidapi.py --dataset . --cap 300 search --identifier 'REGION^93554' --pages 1 --min-price 250000 --max-price 450000
# details takes the same two options and skips cards outside the band
python3 -I -B scripts/fetch_rapidapi.py --dataset . --cap 300 details --max 5 --identifier 'REGION^93554' --min-price 250000 --max-price 450000
python3 -I -B scripts/fetch_rapidapi.py --dataset . search --identifier 'REGION^93965' --pages 1 --flats

python3 -I -B scripts/normalise.py --dataset . --append
python3 -I -B scripts/build_d1.py --dataset .
```

`-I` keeps Python from importing anything from the current directory. `-B` stops it
writing `__pycache__`. Real environment variables take precedence over `.env`. The
`details` command skips search results that fail the selection rules and homes already
in `listings.jsonl`, because the detail response holds the same data.

## Downloading the images

Photos and floorplans are fetched once from the Rightmove CDN, so later steps read local
files and never call Rightmove again. From `dataset/`:

```bash
python3 -I -B scripts/fetch_images.py --dataset .
```

Files land in `photos/<listing_id>/<kind>-<position>.<ext>`. `photos/` is gitignored
(about 6,800 images). Existing files are skipped, so an interrupted run resumes and a
second run downloads nothing. `images-manifest.csv` is committed: one row per image with
`listing_id, kind, position, url, path, sha256, bytes, status`. A failed image has status
`failed: <reason>` and an empty path; the script lists failures and carries on. The
manifest is the same after a re-run unless a failed image is fetched on the retry.

## Loading into D1

**Not yet run.** No D1 database exists yet, so these commands have not been tried. Create
the database first, then load the schema and the data:

```bash
wrangler d1 execute <db> --file dataset/d1/schema.sql
wrangler d1 execute <db> --file dataset/d1/seed.sql
```

Untested: adding `--remote` should target the hosted database rather than the local one.

Known limits:

- `seed.sql` needs empty tables. It is plain `INSERT`s with no `BEGIN`/`COMMIT` (D1 rejects
  them), so a second import fails on the primary keys. Drop and recreate the tables before
  re-seeding.
- `seed.sql` is 3.7 MB (3,655,077 bytes) in 9,365 statements, the largest 13,327 bytes against D1's limit of
  about 100 KB per statement. An import of that size has not been tried. If D1 rejects it,
  split the file.
