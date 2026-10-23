# Listings dataset

A frozen, offline dump of 398 London and commuter-belt homes **for sale**, built for the
Property Swipe Agent hackathon app. The app reads these files. It never calls the
sources live.

Files:

- `listings.jsonl` - one JSON object per listing. This is the main output.
- `listings.csv` - the same rows. List fields are JSON-encoded strings.
- `listings.sqlite` - not committed yet. The current file is an ad-hoc single table; a
  D1-ready database built from a fixed schema replaces it (work in progress).
- `raw/` - every response as downloaded. **Not in git** (48 MB, ignored by `.gitignore`).
  It exists only on the machine that ran the fetch, so a fresh clone cannot rebuild the
  outputs offline; it would have to fetch again.
- `scripts/` - the fetch and normalise scripts. Python standard library only.

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

## Coverage

398 listings. Percentages are of all 398 unless stated.

| Field                              | Count                                    | %    | Notes                                                                                           |
| ---------------------------------- | ---------------------------------------- | ---- | ----------------------------------------------------------------------------------------------- |
| `epc_current` (rating letter)      | 93                                       | 23%  | All taken from the agent's own text, e.g. "EPC Rating: C". Not checked against the certificate. |
| `epc_image_urls` (EPC chart image) | 313                                      | 79%  | The chart Rightmove shows. A few are PDFs. The rating in the image was **not** read.            |
| either of the two EPC fields       | 317                                      | 80%  | 81 listings have no EPC information at all.                                                     |
| `epc_potential`                    | 0                                        | 0%   | Never found in text. The column is always null.                                                 |
| `floorplan_urls` (at least 1)      | 398                                      | 100% | Required.                                                                                       |
| `tenure`                           | 398                                      | 100% | Required. 2 taken from text.                                                                    |
| `lease_years_remaining`            | 193 of 257 leasehold / share of freehold | 75%  | 5 from text.                                                                                    |
| `service_charge_gbp_pa`            | 175 of 257 leasehold / share of freehold | 68%  | 7 from text.                                                                                    |
| `ground_rent_gbp_pa`               | 138 of 257 leasehold / share of freehold | 54%  | 6 from text.                                                                                    |
| `council_tax_band`                 | 354                                      | 89%  |                                                                                                 |
| `floor_level`                      | 147                                      | 37%  |                                                                                                 |
| 6 or more photos                   | 398                                      | 100% | Required. 329 have 10 or more; at most 10 URLs are kept.                                        |
| `lat` / `lon`                      | 398                                      | 100% | Required.                                                                                       |
| full postcode                      | 398                                      | 100% |                                                                                                 |
| `nearest_stations`                 | 398                                      | 100% |                                                                                                 |

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

Type: 257 flats (Flat 134, Apartment 103, Maisonette 15, other flat types 5) and 141
houses (Terraced 41, Semi-Detached 35, Detached 29, End of Terrace 20, House 10, other
6). Tenure: leasehold 205, freehold 141, share of freehold 52.

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
- **Service charge of 0** on some freehold houses is kept as 0, as the agent stated it.
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
  unit (the API does not say whether it is miles or km, so `unit` is null).
- **Dedupe is heuristic.** It may merge two different homes or miss a duplicate listed
  with different coordinates.
- **Odd property types** come straight from the agent: one "Block of Apartments", one
  "Not Specified".
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

Rebuild the outputs from `raw/` with no network access (only where `raw/` exists locally):

```bash
python3 -I -B scripts/normalise.py --dataset .
```

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
```

`-I` keeps Python from importing anything from the current directory. `-B` stops it
writing `__pycache__`. Real environment variables take precedence over `.env`. The
`details` command skips search results that fail the selection rules and homes already
scraped directly, because the detail response holds the same data.
