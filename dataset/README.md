# Listings dataset

A frozen, offline dump of 398 London and commuter-belt homes **for sale**, built for the
Property Swipe Agent hackathon app. The app reads these files. It never calls the
sources live.

Files in git:

- `listings.jsonl` - one JSON object per listing, as written by `normalise.py`. Media and
  stations are nested lists.
- `listings.csv` - the same rows. List fields are JSON-encoded strings.
- `listings.sqlite` - the D1-ready database, built from `d1/schema.sql` by
  `scripts/build_d1.py`. Three tables; see Schema below.
- `d1/schema.sql` - the table definitions, the single source of truth for the data shape.
- `d1/seed.sql` - plain `INSERT` statements for every row, generated from the same data.
- `reports/normalise-report.txt` and `reports/d1-build-report.txt` - counts from the last
  run of each script.
- `scripts/` - the fetch, normalise, sanitise and build scripts. Python standard library
  only.
- `tests/test_sanitise.py` - unit tests for the sanitise rules.
- `requirements.txt`, `.env.example`.

Not in git:

- `raw/` - every response as downloaded. 48 MB, ignored by `.gitignore`. It exists only on
  the machine that ran the fetch, so a fresh clone cannot rebuild the outputs offline; it
  would have to fetch again. A fresh clone can still rebuild `listings.sqlite` and
  `seed.sql` from `listings.jsonl` with `build_d1.py`.
- `.env` - your RapidAPI keys. Never committed.

## Sources

Both sources are Rightmove. Neither is an official or licensed feed.

| Source                                                       | `source` value                      | Listings | How it was accessed                                                                                             | Terms of service                                                                                                                                                                                                              |
| ------------------------------------------------------------ | ----------------------------------- | -------- | --------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| rightmove.co.uk, direct                                      | `rightmove`                         | 372      | `scripts/fetch_rightmove.py` downloads public search and property pages and reads the JSON embedded in them.    | **Against Rightmove's terms.** Their terms forbid automated access and copying of listing data. robots.txt was checked before every URL and every fetched path was allowed, but robots.txt is not permission under the terms. |
| "UK Real Estate Rightmove" API on RapidAPI (provider ntd119) | `rapidapi_uk_real_estate_rightmove` | 26       | `scripts/fetch_rapidapi.py`, endpoints `/buy/property-for-sale` and `/buy/property-for-sale/detail`, free tier. | **Unofficial.** A third party resells data taken from Rightmove's app. Rightmove has not licensed it. RapidAPI's own terms apply to the key holder.                                                                           |

Rules followed when scraping: about one request every 2.5 s (the script refuses a delay
under 2 s), one request at a time, a descriptive User-Agent, no login, no cookies kept,
no CAPTCHA handling, and the script stops on HTTP 403/429 or a challenge page instead of
retrying. No request was blocked or challenged: all 423 logged page requests returned
HTTP 200.

Zoopla and OnTheMarket were looked at (their robots.txt responses are in `raw/robots/`)
but not used. Zoopla answered robots.txt with a Cloudflare challenge page, so it was
left alone.

Use this data for the hackathon demo only. Do not publish it. The photos, floorplans and
descriptions belong to the agents and Rightmove. Only image URLs are stored; no image
was downloaded.

## When it was pulled, and API calls used

All data was pulled on 23 October 2026, between 22:51 and 23:17 UTC.

- Rightmove direct: 423 logged page requests (`raw/rightmove/_manifest.jsonl`), plus one
  unlogged robots.txt fetch per script run.
- RapidAPI: 28 calls, every one logged in `raw/rapidapi/_calls.log` (metadata only, no
  key).

| Key              | Calls used (Oct 2026)    | Left on the 300/month free tier                                       |
| ---------------- | ------------------------ | --------------------------------------------------------------------- |
| `RAPIDAPI_KEY`   | 28 (2 search, 26 detail) | 272, as reported by the provider's rate-limit header on the last call |
| `RAPIDAPI_KEY_2` | 0                        | 300 (not checked; the key was never used)                             |

The scripts stop a key at 250 calls a month by their own count (`--cap`).

## Selection rules

Applied in `scripts/rm_common.py` and `scripts/normalise.py`:

- for sale only; no auctions, shared ownership, retirement homes or archived listings;
- price £250,000 to £1,200,000;
- at least 6 photos and at least 1 floorplan;
- tenure known;
- latitude and longitude present.

Rightmove searches (`fetch_rightmove.py`, `PLAN`), first page of results, newest first:

- 1-3 bed flats, up to £800k: Islington, Hackney, Lambeth, Camden, Southwark, Tower
  Hamlets, Wandsworth, Lewisham;
- houses, up to £1.2m: Lewisham, Waltham Forest, Ealing;
- any type, up to £1.2m: St Albans, Watford, Reading.

RapidAPI searches: Islington 1-3 bed flats (one search, one detail call, from the first
probe) and Guildford, any type (one search, 25 detail calls).

### What was dropped

| Stage                                | Reason                         | Count |
| ------------------------------------ | ------------------------------ | ----- |
| Search card, before fetching details | auction                        | 14    |
| Search card                          | fewer than 6 photos            | 9     |
| Search card                          | no floorplan                   | 5     |
| Search card                          | same property in two searches  | 5     |
| Detail page                          | tenure not stated anywhere     | 6     |
| Dedupe                               | same home listed by two agents | 14    |

That is 20 thin listings dropped (photos, floorplan, tenure) and 14 auctions. No
RapidAPI record was dropped. Of the 50 RapidAPI search results, 23 Islington flats were
never fetched in detail, to save calls, and 1 failed the selection rules on its card.

Deduplication links two records if they share a Rightmove id, a Royal Mail delivery
point id, or the same coordinates (4 decimal places), bedrooms and price. The record
with the most filled fields is kept. Two records from the same agent are never linked
on delivery point or coordinates, because developers list several units of one
new-build under one placeholder address. This keeps 6 Taylor Wimpey homes on Chiswell
Green Lane, St Albans, as separate listings: they share no photo URLs, but two pairs have
the same price and bedrooms, so the app will show similar cards. There were no
duplicates across the two sources, because `details` skips homes already scraped.

## Schema

`d1/schema.sql` is the source of truth. Read it for exact columns, types, CHECK bounds and
a comment on each column giving its unit and what NULL means. In brief:

- `listings` - one row per listing (id `rm-<Rightmove id>`). Flat scalar columns: price,
  bedrooms, bathrooms, property type, address, postcode, lat/lon, tenure, lease, service
  charge, ground rent, council tax band, EPC rating, floor level, description, agent,
  dates. `key_features` and `parsed_fields` are JSON arrays of strings held as text.
- `listing_media` - one row per image: `(listing_id, kind, position, url)` with `kind` one
  of `photo`, `floorplan`, `epc`. The primary key is `(listing_id, kind, position)`;
  `position` is 0-based within the listing and kind. Later photo flags are meant to join
  on that key.
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
  The last run dropped none: 398 in, 398 kept.

## Coverage

398 listings. Percentages are of all 398 unless stated. Counted from `listings.sqlite`.

| Field                              | Count                                    | %    | Notes                                                                                           |
| ---------------------------------- | ---------------------------------------- | ---- | ----------------------------------------------------------------------------------------------- |
| `epc_current` (rating letter)      | 93                                       | 23%  | All taken from the agent's own text, e.g. "EPC Rating: C". Not checked against the certificate. |
| EPC chart image (`epc` media rows) | 313 listings (329 rows)                  | 79%  | The chart Rightmove shows. A few are PDFs. The rating in the image was **not** read.            |
| either of the two EPC fields       | 317                                      | 80%  | 81 listings have no EPC information at all.                                                     |
| `epc_potential`                    | 0                                        | 0%   | Never found in text. The column is always NULL.                                                 |
| floorplan (at least 1)             | 398 (416 rows)                           | 100% | Required.                                                                                       |
| `tenure`                           | 398                                      | 100% | Required. 2 taken from text.                                                                    |
| `lease_years_remaining`            | 193 of 257 leasehold / share of freehold | 75%  | 5 from text. 1 freehold listing also carries a lease (see limitations).                         |
| `service_charge_gbp_pa`            | 175 of 257 leasehold / share of freehold | 68%  | 7 from text. 13 of these are 0.                                                                 |
| `ground_rent_gbp_pa`               | 138 of 257 leasehold / share of freehold | 54%  | 6 from text. 29 of these are 0.                                                                 |
| `council_tax_band`                 | 302                                      | 76%  | 52 more said "TBC" and are NULL.                                                                |
| `floor_level`                      | 147                                      | 37%  |                                                                                                 |
| `bathrooms`                        | 384                                      | 96%  |                                                                                                 |
| `property_type`                    | 397                                      | 100% | 1 "Not Specified" is NULL.                                                                      |
| 6 or more photos                   | 398                                      | 100% | Required. 329 have 10 or more; at most 10 URLs are kept (3,832 `photo` rows).                   |
| `lat` / `lon`                      | 398                                      | 100% | Required.                                                                                       |
| full postcode                      | 398                                      | 100% |                                                                                                 |
| `listed_date`                      | 398                                      | 100% |                                                                                                 |
| stations (`listing_stations`)      | 398 listings (1,194 rows)                | 100% | Every row has a `distance_km`. 1,116 have a transport type; the 78 RapidAPI rows have none.     |

Row counts: `listings` 398, `listing_media` 4,577, `listing_stations` 1,194.

EPC rating counts: C 43, D 26, B 20, E 3, A 1, none 305.

`parsed_fields` on each row lists every field that was taken from free text rather than
a structured field, so the app can treat those values with less trust.

## Distributions

Price: minimum £250,000, median £600,000, maximum £1,195,000.

| Price band  | Listings |
| ----------- | -------- |
| £250k-£400k | 63       |
| £400k-£550k | 99       |
| £550k-£700k | 74       |
| £700k-£900k | 125      |
| £900k-£1.2m | 37       |

Bedrooms: 1 bed 67, 2 bed 161, 3 bed 106, 4 bed 47, 5 bed 17.

Type (`property_type`): flat 240, terraced 41, semi_detached 35, detached 31,
end_of_terrace 20, maisonette 16, house 11, bungalow 2, other 1, NULL 1.

Tenure: leasehold 205, freehold 141, share of freehold 52.

Area:

| Area      | Postcode areas                                                 | Listings |
| --------- | -------------------------------------------------------------- | -------- |
| London    | SE 72, E 66, SW 53, N 53, W 21, NW 17, EC 15, WC 3, BR 2, IG 2 | 304      |
| Guildford | GU                                                             | 25       |
| St Albans | AL                                                             | 24       |
| Reading   | RG                                                             | 24       |
| Watford   | WD                                                             | 21       |

## Known limitations and shortcuts

- **EPC rating is the weak field.** Neither source has a structured EPC rating. The
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
  One RapidAPI 4-bed house (`rm-94396305`) has 0 bathrooms though its description mentions
  an en suite bathroom.
- **EPC rating coverage is low.** Only 93 of 398 (23%) have a letter; see the first point.
- **The data is unofficial and against Rightmove's terms** (see Sources). Demo use only.
- **`seed.sql` is not idempotent.** It needs empty tables. A second import fails on the
  primary keys.
- **Station types.** RapidAPI's station `type` code is not decoded, so those 78 stations
  have `types` = `[]`, meaning "none given".
- **Some bounds are judgement calls.** Price, bedroom, lease and money limits in the
  schema catch obvious bad data with wide margins. A listing outside the South East is
  rejected until the lat/lon bounds change.
- **Dates:** the schema checks the shape of a date, not that it is a real calendar day.
- **Every search is the first page only**, newest first. The data is a recent snapshot
  of each area, not a sample of the market. The exception is three files from an
  earlier run, `raw/rightmove/search/{Hackney,Islington,Lambeth}_flats_0.html.gz`,
  which used Rightmove's default sort (highest price). Their listings are included. A
  fresh re-run will not reproduce them, because `PLAN` no longer requests them.
- **Flats were capped at £800k** in the Rightmove flat searches, so expensive flats are
  missing. Everything over £800k is a house or comes from Guildford.
- **4 and 5 bed homes are 16%** (64 listings), from the house and commuter-belt
  searches. The brief asked for mostly 1-3 beds; 84% are.
- **London is 76% of the data.** The commuter belt is four towns only: St Albans,
  Watford, Reading and Guildford.
- **Prices are as advertised**, including "Guide Price" and "Offers in Excess of"
  (`price_qualifier`).
- **RapidAPI rows** have no floor level from structured data and no station distance
  unit. The API does not say whether its distances are miles or km. They are read as
  miles; the evidence is three stations that appear in both feeds, where the API figure
  matched the web page's miles within 0.01 and not as km.
- **Dedupe is heuristic.** It may merge two different homes or miss a duplicate listed
  with different coordinates.
- **Odd property types:** one "Block of Apartments" is `other`, one "Not Specified" is
  NULL.
- **Stale listings.** Homes sell. Some URLs will 404 within weeks.
- The fetch scripts make one robots.txt request per run that is not written to the
  manifest.

## Re-running

From the repository root:

```bash
cd dataset
cp -n .env.example .env       # -n: never overwrites an existing .env; then paste your RapidAPI keys into it
```

A virtual environment is optional. The scripts use the Python standard library only
(run with Python 3.14), and `requirements.txt` lists no packages. If
you want one anyway:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # installs nothing
```

Rebuild the outputs from `raw/` with no network access (only where `raw/` exists locally).
Run the three steps in this order:

```bash
# 1. raw/ -> listings.jsonl, listings.csv, reports/normalise-report.txt  (from dataset/)
cd dataset && python3 -I -B scripts/normalise.py --dataset .

# 2. tests  (from the repository root)
python3 -I -B -m unittest discover -s dataset/tests

# 3. listings.jsonl -> listings.sqlite, d1/seed.sql, reports/d1-build-report.txt  (from dataset/)
cd dataset && python3 -I -B scripts/build_d1.py --dataset .
```

`build_d1.py` loads `d1/schema.sql` with foreign keys on, so the schema's constraints are
the validation. It stops at the first violation and names the listing id and constraint.
It does not need `raw/`.

Fetch again. Each script skips files already in `raw/`, so a re-run only fetches what
is missing. Delete the relevant `raw/` files first to refresh them.

```bash
# Rightmove direct (whole plan; about 2.5 s per request)
python3 -I -B scripts/fetch_rightmove.py --raw raw/rightmove
python3 -I -B scripts/fetch_rightmove.py --raw raw/rightmove --list-plan
python3 -I -B scripts/fetch_rightmove.py --raw raw/rightmove --resolve Guildford

# RapidAPI
python3 -I -B scripts/fetch_rapidapi.py --dataset . budget
python3 -I -B scripts/fetch_rapidapi.py --dataset . search --identifier 'REGION^580' --pages 1
python3 -I -B scripts/fetch_rapidapi.py --dataset . details --max 25 --identifier 'REGION^580'
python3 -I -B scripts/fetch_rapidapi.py --dataset . search --identifier 'REGION^93965' --pages 1 --flats

python3 -I -B scripts/normalise.py --dataset .
python3 -I -B scripts/build_d1.py --dataset .
```

`-I` keeps Python from importing anything from the current directory. `-B` stops it
writing `__pycache__`. Real environment variables take precedence over `.env`. The
`details` command skips search results that fail the selection rules and homes already
scraped directly, because the detail response holds the same data.

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
- `seed.sql` is 2.2 MB in 6,169 statements, the largest 11,006 bytes against D1's limit of
  about 100 KB per statement. An import of that size has not been tried. If D1 rejects it,
  split the file.
