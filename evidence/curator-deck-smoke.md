# Curator deck smoke run

Date: 2026-10-25. One run against the real Mubit gateway, local dev server on port 8790,
local D1 freshly seeded. Metadata only: no response bodies, no keys.

## What was run

1. `worker/scripts/seed.sh`, then `pywrangler dev --port 8790 --inspector-port 9240`.
2. `POST /api/users` with `smoke_b4` (201).
3. `PUT /api/prefs`, text "2 bed flat under 600k, EPC C or better, near a tube station,
   bright rooms, quiet street", no postcode (so no TfL work). 200 after 142 s.
   Parsed hard limits: max price 600000, min 2 bedrooms, flats, EPC C. Soft: near a tube
   station, bright rooms, quiet street. Parse request id: `mreq_01a17240f058762090c01f6d4832f755`.
4. One `GET /api/deck?n=10`. 200 after 30.8 s wall clock.

## Numbers

- Train listings: 488. Pool after hard filters: between 61 and 80 listings (four chunks of
  20 were sent; the exact pool size is not stored). A SQL count of train flats with 2+
  bedrooms and price at or under 600000, before the EPC filter, gives 83.
- Curator calls: 4 sent, 2 succeeded, 2 failed. `curator_scores` rows: 40, from 2 distinct
  request ids (20 each).
- Scores: min 35, median 70, max 92, mean 68.9.
- Cards returned: 10, of which 2 exploration and 8 ranked. `empty_reason` null.
  `decisions` rows: 10.

## Request ids

Successful curator calls:

- `mreq_01a17243306375c0992b4866d5d20f5c`
- `mreq_01a17243306d794080d993a027ec862b`

Failed curator calls (both HTTP 503 from the provider, "high demand", logged as chunk
failures, 40 or fewer listings left unscored):

- `mreq_01a172432f3a7b73ac447a337c661c71`
- `mreq_01a17243306d7301a45459c4bf8969d0`

Prefs parse call: `mreq_01a17240f058762090c01f6d4832f755`.

## Cost (estimate)

The app does not store token counts, so the `usageMetadata` totals the step asks for are
not recorded here. Exact prompt, output and thinking tokens per call are on Mubit's
Requests page under the ids above.

Rough estimate: 2 successful chunks of 20 listings, each listing a compact JSON object with
photo flags, assumed 1,000 to 2,000 tokens per listing, so about 40k to 80k input tokens in
total, plus about 2k output and some thinking tokens. The prefs parse is small. At an
assumed Gemini Flash price of $0.30 per million input and $2.50 per million output tokens,
that is roughly $0.02 to $0.03. This is an estimate from assumed sizes and an assumed price,
not a measurement. The two 503 calls were probably not billed; unchecked.

## Failures

Two of four chunks failed with provider 503, so half the pool was unscored on this run.
The deck still served 10 cards from the 40 scored listings, as designed. A second
`GET /api/deck` would score the remaining chunks (scores are cached per listing).
Not repeated, because only one deck request was approved.

## Sample rows

| listing_id  | score | source      | reason |
| ----------- | ----- | ----------- | ------ |
| rm-92673858 | 92    | ranked      | Ideally located just moments from Arsenal tube station, featuring bright mezzanine living in a quiet gated development. |
| rm-94592364 | 63    | exploration | Features bright rooms and a balcony, but transport links are primarily London Overground rather than the tube. |
| rm-93565308 | 35    | not served  | Situated in Reading far from any London Underground network, though the living room offers decent brightness. |

The reasons name the stated wishes (tube, bright rooms, quiet) and match the scores.
Note that rm-93565308, in Reading, passed the hard filters because the buyer gave no
location limit; the curator marked it down on the tube wish.
