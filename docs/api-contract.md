# API contract

HTTP contract between the Python Worker backend (FastAPI, run locally with
`pywrangler dev`) and the Vite + React frontend. Frontend mocks are built from this
file. Decisions behind it: [decisions.md](decisions.md). Listing and media field names
and enums are those of `dataset/d1/schema.sql`. Photo flag fields are defined by this
contract (see Enums and nullability).

## General

- Base URL: `http://localhost:8787/api`. Endpoint paths below are written without the
  `/api` prefix.
- In development the Vite dev server proxies `/api` to `:8787`, so the browser only
  calls its own origin. There is no CORS setup and no preflight to handle.
- JSON in, JSON out. `Content-Type: application/json` on every request with a body.
- The user is identified by the header `X-User-Id: <user_id>` on every endpoint except
  `GET /users`, `POST /users` and `GET /stats`. A missing or unknown id returns 401
  `unknown_user`. There are no passwords and no tokens.
- Errors always have this shape, with an HTTP status that matches the code:

  ```json
  {"error": {"code": "unknown_user", "message": "No user with that id."}}
  ```

  `code` is snake_case and stable. `message` is for humans and may change.
  Every endpoint can also return 401 `unknown_user` (where the header applies) and
  422 `invalid_request` (body or query does not match the shape given here). These two
  are not repeated per endpoint.
- The backend owns validation details: formats such as postcode, number ranges,
  username rules, and which error wins when several apply. The frontend shows
  `error.message` for any 4xx and does not replicate these checks.
- Unknown values are `null`, never `0` or `""`. This matches the schema.
- The frontend never calls an LLM, Mubit or TfL. All of that is backend only.
- Simulated personas call this same API. There is no persona, batch or train endpoint.
  Training happens in the Mubit console.

## Server-side only

Not part of the frontend contract:

- Mubit's `x-middleware-request-id` (`mreq_...`) and the profile version used are stored
  per decision in D1.
- The chips offered on each card are logged when the deck is served (see `GET /deck`).
- The listing `split` column (train / eval) is never exposed.

The only place these surface is `GET /profile`, whose `history` references decisions.

## Users

### `GET /users`

No header needed.

```json
{"users": [{"user_id": "u_01", "username": "alex"}, {"user_id": "u_02", "username": "jordan"}]}
```

### `POST /users`

No header needed. Username only.

Request:

```json
{"username": "alex"}
```

Response 201:

```json
{"user_id": "u_01", "username": "alex"}
```

Errors: 409 `username_taken`.

## Preferences

### `GET /prefs`

Response 200. If the user has never saved prefs, all fields are `null`, including
`parsed` (it is `null`, not an object with empty fields), and `commute_status` is `null`.

```json
{"text": null, "commute_postcode": null, "max_commute_min": null, "parsed": null, "commute_status": null}
```

After prefs are saved:

```json
{
  "text": "Two bed flat under 550k, near a tube station, bright rooms, no ground floor.",
  "commute_postcode": "EC2N 2DB",
  "max_commute_min": 45,
  "parsed": {
    "hard": {
      "max_price_gbp": 550000,
      "min_bedrooms": 2,
      "property_types": ["flat", "maisonette"],
      "min_epc": "D",
      "tenure": null,
      "min_lease_years": null,
      "max_commute_min": 45
    },
    "soft": ["near a tube station", "bright rooms", "not on the ground floor"]
  },
  "commute_status": "ready"
}
```

- `hard` fields are `null` when unstated. `property_types` uses the schema enum.
  `min_epc` and `tenure` use the schema enums.
- `max_commute_min` inside `hard` is the value from the request field, not parsed from
  text. It is a hard filter enforced in code.
- `soft` is a list of short text preferences passed to the curator.
- `commute_status`: `pending` while TfL times are being calculated, `ready` when done,
  `failed` if the calculation as a whole failed. On `failed` the frontend shows an
  error and lets the user re-save prefs. A TfL failure for a single listing is not
  `failed`: that card has `commute.minutes: null` and the status stays `ready`.

### `PUT /prefs`

Replaces the stored prefs. Returns at once; the backend then calculates the TfL commute
for every listing that passes the other hard filters. Poll `GET /prefs` until
`commute_status` is `ready`.

Request:

```json
{
  "text": "Two bed flat under 550k, near a tube station, bright rooms, no ground floor.",
  "commute_postcode": "EC2N 2DB",
  "max_commute_min": 45
}
```

`commute_postcode` is required and is a postcode only. `max_commute_min` is optional.
A missing `commute_postcode` returns 422 `invalid_request`. A malformed one, including a
free-text place name, returns 422 `invalid_postcode`.

`text` is required and must be non-empty. A missing, `null`, empty or whitespace-only
`text` returns 422 `invalid_request`.

Response 200: same shape as `GET /prefs`, with `commute_status: "pending"`. `parsed` is
filled in the response; only the TfL commute step runs after. Poll `GET /prefs` until
the status is `ready` or `failed`.

Re-saving prefs mid-session discards every served card that has not been swiped. Their
`decision_id`s are dropped, and swiping or sending feedback on one returns 404
`decision_not_found`. Already swiped decisions are kept. The frontend should discard its
local deck and fetch a new one once `commute_status` is `ready`. The dropped cards
return to the pool and can be served again.

Errors: 422 `invalid_postcode`.

## Deck

### `GET /deck?n=10`

Returns a batch of cards. `n` defaults to 10. An `n` outside 1–10, or one that is
not an integer, returns 422 `invalid_request`. The frontend refetches when it runs low.

- Unswiped cards that were already served come first, with the same `decision_id`s, then
  new cards. A listing is never served twice at once. Cards dropped by a prefs re-save
  return to the pool. A listing the user has swiped is never served to them again.
- A `decision_id` is created for each card when it is first served. One per served card.
- About 1 in 5 cards has `source: "exploration"`, drawn from a percentile band of the
  pool that passes the hard filters, seeded per user.
- **`source` is in the payload and the logs. It must never be shown on the card face.**
- The chips offered on each card are logged server side at the moment the deck is
  served. Offered-versus-chosen ratios do not depend on the frontend.
- `feedback_required` on a card is a hint, the server's prediction at serve time
  (onboarding, see Feedback). It is `true` only for cards within the user's first 15
  swipes. It can differ from the real value, for example after a refetch or a prefs
  re-save, so the swipe response is authoritative and the frontend obeys that.
- Compulsory feedback is not enforced server side. No endpoint refuses a swipe because
  feedback is missing. The frontend obeys `feedback_required` itself.
- When there is nothing to serve, the response is 200 with an empty `cards` list and an
  `empty_reason`. It is not an error. `exhausted`: every matching listing has been
  swiped. `no_matches`: nothing passes the hard filters. `empty_reason` is `null` when
  `cards` is non-empty, and is always present.

Response 200 (`empty_reason` is `null` here; an empty deck is
`{"cards": [], "empty_reason": "exhausted"}`):

```json
{
  "empty_reason": null,
  "cards": [
    {
      "decision_id": "d_000231",
      "source": "ranked",
      "feedback_required": true,
      "listing": {
        "id": "rm-123456789",
        "price_gbp": 525000,
        "price_qualifier": "offers_over",
        "bedrooms": 2,
        "bathrooms": 1,
        "property_type": "flat",
        "address": "14 Example Road, London",
        "postcode": "E8 1AA",
        "lat": 51.545,
        "lon": -0.062,
        "tenure": "leasehold",
        "epc_current": "C",
        "floor_level": "second floor",
        "key_features": ["Balcony", "Close to station"],
        "photos": [
          "https://example.invalid/photos/1.jpg",
          "https://example.invalid/photos/2.jpg"
        ]
      },
      "commute": {
        "minutes": 32,
        "postcode": "EC2N 2DB",
        "assumptions": "weekday, arrive 08:30, public transport"
      },
      "chips": [
        {
          "chip_id": "natural_light",
          "label": "Natural light inside",
          "phrases": ["Bright and airy, I love it", "A bit dark for me"]
        },
        {
          "chip_id": "parking",
          "label": "Parking",
          "phrases": ["Parking is a must", "Fine without parking"]
        }
      ]
    }
  ]
}
```

- `commute.minutes` is `null` if TfL had no answer.
- `chips[]` is filtered per listing from the photo flags and listing fields. A garden
  chip is not shown on a flat with no garden. `phrases` are preset suggestions for the
  chip dialog.
- `photos` is an ordered list of URLs.

Errors: 409 `prefs_missing` (no prefs saved), 409 `commute_pending`
(`commute_status` is `pending`), 409 `commute_failed` (`commute_status` is `failed`;
the user must re-save prefs), 422 `invalid_request` (`n` out of range or not an integer).

## Listings

### `GET /listings/{id}`

Full detail for one listing. Includes all fields of the card's `listing` object, plus
the fields below.

```json
{
  "id": "rm-123456789",
  "price_gbp": 525000,
  "price_qualifier": "offers_over",
  "bedrooms": 2,
  "bathrooms": 1,
  "property_type": "flat",
  "address": "14 Example Road, London",
  "postcode": "E8 1AA",
  "lat": 51.545,
  "lon": -0.062,
  "tenure": "leasehold",
  "epc_current": "C",
  "floor_level": "second floor",
  "key_features": ["Balcony", "Close to station"],
  "photos": ["https://example.invalid/photos/1.jpg", "https://example.invalid/photos/2.jpg"],
  "lease_years_remaining": 87,
  "service_charge_gbp_pa": 1800.0,
  "ground_rent_gbp_pa": 250.0,
  "council_tax_band": "D",
  "epc_potential": "B",
  "description": "A bright two bedroom flat close to the station.",
  "agent_name": "Example Agents, Hackney",
  "listed_date": "2026-09-30T00:00:00Z",
  "floorplans": ["https://example.invalid/floorplans/1.jpg"],
  "stations": [
    {"name": "Hackney Central", "distance_km": 0.4, "types": ["NATIONAL_TRAIN"]}
  ],
  "photo_flags": [
    {
      "flag_id": "f_00812",
      "scope": "photo",
      "field": "light",
      "value": "bright",
      "observation": "Large south-facing window, daylight reaches the back wall.",
      "source_photo": "https://example.invalid/photos/1.jpg",
      "confidence": "high",
      "uncertainty": null,
      "room": "living_room",
      "corrected_text": null
    },
    {
      "flag_id": "f_00813",
      "scope": "photo",
      "field": "defects",
      "value": "mould on ceiling",
      "observation": "Dark patches in the corner above the shower.",
      "source_photo": "https://example.invalid/photos/4.jpg",
      "confidence": "medium",
      "uncertainty": "Could be shadow or staining.",
      "room": "bathroom",
      "corrected_text": "Not damp, it is a shadow from the light fitting."
    },
    {
      "flag_id": "f_00820",
      "scope": "listing",
      "field": "sqm_estimate",
      "value": 58,
      "observation": "Scaled from the stated room dimensions on the floorplan.",
      "source_photo": "https://example.invalid/floorplans/1.jpg",
      "confidence": "medium",
      "uncertainty": "Wall thickness not shown.",
      "room": null,
      "corrected_text": null
    }
  ]
}
```

Field notes:

- Names and enums for listing fields are exactly those in `schema.sql`, written out in
  [Enums and nullability](#enums-and-nullability) below. Nullable fields are `null`
  when unknown. `listed_date` is ISO 8601 UTC.
- `floorplans` is an ordered list of URLs. `stations` is ordered nearest first.
- The schema columns `listings.url`, `listings.source`, `listings.fetched_at` and
  `listings.parsed_fields` are left out on purpose. They are source-system and pipeline
  bookkeeping, not for display. (`listings.source` is not the card's `source` field,
  which means ranked or exploration.)
- Each entry in `photo_flags` is one flag with its own `flag_id`.
  - `scope`: `photo` or `listing`.
  - `field` for `photo` scope: `room`, `light`, `size_tricks`, `defects`, `missing`.
    `light` values: `none`, `poor`, `ok`, `bright`. The other values are short text.
  - `field` for `listing` scope: `floorplan_notes`, `sqm_estimate`.
  - `value` is the flag itself. `observation` is what the model saw. `source_photo` is
    the URL of the photo or floorplan it came from. `confidence` is `high`, `medium` or
    `low`. `uncertainty` is free text or `null`. These are separate fields.
  - `room` is always set (never `null`) on photo-scope flags and is `null` on
    listing-scope flags. When set, it is one of
    `living_room`, `kitchen`, `bedroom`, `bathroom`, `hallway`, `garden`, `exterior`,
    `other` (see Enums and nullability).
  - `corrected_text` is `null` unless the user corrected the flag. When set, the curator
    reads it instead of `value`.
- Photos the pipeline marked `skip` (agent logos, duplicates) do not appear in `photos`
  or `photo_flags`.

Errors: 404 `listing_not_found`.

A listing that appears in favourites can be fetched here even after the deck dropped it.
The response has no `commute` and no `chips`; those only come with a card.

### Enums and nullability

Listing and media rows come from `dataset/d1/schema.sql`. The photo flag rows (`scope`,
`field`, `light`, `confidence`, `room`) are defined by this contract, because no flag
table exists yet. Every value is a string, written exactly as shown
(case matters).

| Field | Allowed values | Null? |
| ----- | -------------- | ----- |
| `price_qualifier` | `guide_price`, `offers_over`, `offers_in_region`, `fixed_price` | yes (no qualifier shown) |
| `property_type` | `flat`, `maisonette`, `house`, `terraced`, `semi_detached`, `end_of_terrace`, `detached`, `bungalow`, `other` | yes |
| `tenure` | `freehold`, `leasehold`, `share_of_freehold` | yes |
| `epc_current` | `A`, `B`, `C`, `D`, `E`, `F`, `G` | yes |
| `epc_potential` | `A`, `B`, `C`, `D`, `E`, `F`, `G` | yes |
| `council_tax_band` | `A`, `B`, `C`, `D`, `E`, `F`, `G`, `H` | yes |
| `floor_level` | free text as the agent wrote it, lowercase, no enum | yes |
| `stations[].types` | array of free-text strings, e.g. `NATIONAL_TRAIN`, no enum; `[]` if none | no (empty array) |
| `key_features` | array of strings; `[]` if none | no (empty array) |
| `photos`, `floorplans` | array of URLs; media kinds are `photo` and `floorplan` | no (empty array) |
| photo flag `scope` | `photo`, `listing` | no |
| photo flag `field` | `room`, `light`, `size_tricks`, `defects`, `missing` (scope `photo`); `floorplan_notes`, `sqm_estimate` (scope `listing`) | no |
| photo flag `light` value | `none`, `poor`, `ok`, `bright` | no |
| photo flag `confidence` | `high`, `medium`, `low` | no |
| photo flag `room` | `living_room`, `kitchen`, `bedroom`, `bathroom`, `hallway`, `garden`, `exterior`, `other` | yes (`null` for listing scope, never null for photo scope) |

Nullability of the other listing fields, from the schema:

- Never null: `id`, `price_gbp`, `key_features`.
- Null when unknown: `bedrooms`, `bathrooms`, `address`, `postcode`, `lat`, `lon`,
  `lease_years_remaining`, `service_charge_gbp_pa`, `ground_rent_gbp_pa`, `description`,
  `agent_name`, `listed_date`, and every field marked "yes" above.
- `stations[].name` is never null. `stations[].distance_km` is null when unknown.
- Photo flag `value` (a string, or a number for `sqm_estimate`), `observation`,
  `source_photo` and `confidence` are never null. `uncertainty` and `corrected_text`
  are null when absent.

## Swipe and feedback

### `POST /decisions/{decision_id}/swipe`

Request:

```json
{"action": "right"}
```

`action` is `left`, `right` or `superlike`. A superlike adds the listing to favourites
automatically. A right swipe does not. A `decision_id` that belongs to another user
returns 404 `decision_not_found`.

Response 200:

```json
{
  "decision_id": "d_000231",
  "action": "right",
  "feedback_required": true,
  "favourited": false,
  "profile_version": 12
}
```

`feedback_required` here is authoritative; the value on the card was only a hint. If
`true`, the frontend must collect feedback before showing the next card. It is `true`
for each of the user's first 15 swipes (onboarding), whatever the action. The
count does not reset when prefs are re-saved. After that it is always `false`: left
swipes show no feedback screen, and right swipes may show an optional one. After
onboarding a superlike behaves as a right swipe for feedback (the optional screen), and
still adds the favourite. Feedback sent for a post-onboarding left swipe is still
accepted.

The server does not enforce compulsory feedback. A swipe is never refused because the
previous card has no feedback. The frontend obeys `feedback_required`.

Every swipe bumps the taste profile version. `profile_version` is the new version. A
superlike bumps it once, although it both records the swipe and adds the favourite.

A `decision_id` dropped by a prefs re-save (see `PUT /prefs`) returns 404
`decision_not_found`.

Errors: 404 `decision_not_found`, 409 `already_swiped`.

### `PUT /decisions/{decision_id}/feedback`

Replaces the whole feedback for the decision, so an existing answer can be edited.
`chips` and `free_text` are both required keys: `chips` may be `[]` and `free_text` may
be `null`, but a missing key returns 422 `invalid_request`. To clear the feedback, send
`"chips": []` and `"free_text": null`. A `decision_id` that belongs to another user
returns 404 `decision_not_found`. An empty or whitespace-only
`free_text` or chip `text` is stored as `null`, with no error. The server returns `null`,
never `""`. A `chip_id` repeated within one request returns 422 `invalid_request`.

Request:

```json
{
  "chips": [
    {"chip_id": "natural_light", "strength": "must_have", "text": "Bright and airy, I love it"},
    {"chip_id": "parking", "strength": "would_prefer_not", "text": null}
  ],
  "free_text": "Lovely kitchen, but the street felt noisy."
}
```

- Chips are optional, any number of them.
- `strength` is required on every chip and is one of `must_have`, `nice_to_have`,
  `would_prefer_not`, `deal_breaker`. Preset `phrases` carry no strength: tapping one
  fills `text` only, and the user picks the strength separately.
- `text` is optional free text. A preset phrase from the chip's `phrases` can fill it.
  Use `null` for none.
- A chip answer is about this property's version of the feature, not a general
  preference. The general preference is derived server side across cards.
- Feedback is compulsory for the user's first 15 swiped cards (onboarding), on any
  action. After that it is optional on right swipes, and left swipes show no feedback
  screen. The server sets `feedback_required`; the frontend obeys it. The server does not
  enforce it (see swipe).
- Every feedback PUT bumps the profile version, including an edit that changes nothing
  and a clear. `profile_version` in the response is the new version.

Response 200:

```json
{
  "decision_id": "d_000231",
  "chips": [
    {"chip_id": "natural_light", "strength": "must_have", "text": "Bright and airy, I love it"},
    {"chip_id": "parking", "strength": "would_prefer_not", "text": null}
  ],
  "free_text": "Lovely kitchen, but the street felt noisy.",
  "profile_version": 14
}
```

A decision dropped by a prefs re-save (see `PUT /prefs`) returns 404
`decision_not_found`.

Errors: 404 `decision_not_found`, 409 `not_swiped` (no swipe yet),
422 `chip_not_offered` (the chip was not on that card).

## Flag corrections

### `POST /flags/{flag_id}/correction`

Writes the user's correction onto the cached flag record. The curator reads the
corrected text from then on.

The correction is shared across users: it is a fact about the photo, so every user sees
it in `corrected_text`. It also bumps the correcting user's profile version. There is no
undo. Empty or missing `text` returns 422 `invalid_request`.

Request:

```json
{"text": "Not damp, it is a shadow from the light fitting."}
```

Response 200: the updated flag, same shape as one entry of `photo_flags`, plus
`profile_version`, the correcting user's new profile version.

```json
{
  "profile_version": 13,
  "flag_id": "f_00813",
  "scope": "photo",
  "field": "defects",
  "value": "mould on ceiling",
  "observation": "Dark patches in the corner above the shower.",
  "source_photo": "https://example.invalid/photos/4.jpg",
  "confidence": "medium",
  "uncertainty": "Could be shadow or staining.",
  "room": "bathroom",
  "corrected_text": "Not damp, it is a shadow from the light fitting."
}
```

Errors: 404 `flag_not_found`.

## Favourites

### `GET /favourites`

```json
{
  "favourites": [
    {
      "added_at": "2026-10-24T14:02:11Z",
      "listing": {
        "id": "rm-123456789",
        "price_gbp": 525000,
        "price_qualifier": "offers_over",
        "bedrooms": 2,
        "bathrooms": 1,
        "property_type": "flat",
        "address": "14 Example Road, London",
        "postcode": "E8 1AA",
        "lat": 51.545,
        "lon": -0.062,
        "tenure": "leasehold",
        "epc_current": "C",
        "floor_level": "second floor",
        "key_features": ["Balcony", "Close to station"],
        "photos": ["https://example.invalid/photos/1.jpg"]
      }
    }
  ]
}
```

### `DELETE /favourites/{listing_id}`

The request carries a JSON body. A reason is required.

The reason is treated as free-text feedback and feeds the taste profile. Every removal
bumps the profile version, and `GET /profile` then shows a `favourite_removed` cause.
A missing, `null` or empty `reason` returns 422 `reason_required`, not `invalid_request`.

Request:

```json
{"reason": "Too far from the station once I looked at the map."}
```

Response 200:

```json
{"listing_id": "rm-123456789", "removed": true}
```

Errors: 422 `reason_required`, 404 `not_favourited`.

## Profile

### `GET /profile`

The current taste profile. It exists so the recording can show the correction trail.
`weight` is 0 to 1. `direction` is text describing where the user sits on the factor.
Every swipe, feedback PUT, favourite removal and flag correction bumps `version` by one
and adds a `history` entry.

```json
{
  "version": 14,
  "factors": [
    {"factor": "natural_light", "direction": "wants bright rooms", "weight": 0.82},
    {"factor": "area_busyness", "direction": "prefers a quiet street", "weight": 0.35}
  ],
  "history": [
    {
      "version": 14,
      "created_at": "2026-10-24T14:05:40Z",
      "cause": {"type": "feedback", "decision_id": "d_000231", "flag_id": null, "listing_id": null}
    },
    {
      "version": 13,
      "created_at": "2026-10-24T14:01:02Z",
      "cause": {"type": "flag_correction", "decision_id": null, "flag_id": "f_00813", "listing_id": null}
    }
  ]
}
```

- `history` lists the most recent versions only, newest first, at most 10 entries.
- `cause.type` is `swipe`, `feedback`, `flag_correction` or `favourite_removed`. The ids
  that do not apply are `null`. `listing_id` is set only for `favourite_removed`.
- `factor` values come from a fixed list, seeded from the chip ids (`natural_light`,
  `parking` and so on). They are never free text. The list may also hold factors with no
  chip, such as `area_busyness`.
- A user with no activity has `version: 0`, empty `factors` and empty `history`.

## Stats

### `GET /stats`

No header needed. Not per user. Feeds the dashboard graph.

```json
{
  "arms": {
    "base": {
      "hits_top5": {"mean": 2.2, "sd": 0.8, "n_personas": 5},
      "false_exclude_rate": {"mean": 0.31, "sd": 0.09, "n_personas": 5}
    },
    "base_memory": {
      "hits_top5": {"mean": 3.1, "sd": 0.7, "n_personas": 5},
      "false_exclude_rate": {"mean": 0.22, "sd": 0.07, "n_personas": 5}
    },
    "updated_memory": {
      "hits_top5": {"mean": 3.8, "sd": 0.6, "n_personas": 5},
      "false_exclude_rate": {"mean": 0.15, "sd": 0.06, "n_personas": 5}
    }
  }
}
```

- `hits_top5`: of the curator's five highest-ranked held-out listings, how many the
  persona's hidden rules count as good. Mean and standard deviation across held-out
  personas.
- `false_exclude_rate`: share of rule-good listings ranked below the cut.
- `updated_memory` is `null` if no adapter route works (fallback D in decisions.md).
- Before any eval has run, all three arms are `null` and the response is still 200:
  `{"arms": {"base": null, "base_memory": null, "updated_memory": null}}`. The dashboard
  shows an empty state.

## Schema baseline

The contract is written against `main` at `7597e7f`. That commit already drops `epc`
media from the D1 build and fills demo EPC ratings, so EPC is carried only by
`epc_current` and `epc_potential`. Uncommitted work on `feat/dataset-extend` adds
`listings.split`, an evaluation holdout column. The contract never exposes it.

## Open points

Everything not settled lives here.

1. **Chip catalogue.** The preset chip list, each chip's `chip_id`, `phrases`, and the
   filter rule that decides when a chip is offered.
2. **Flag confidence scale.** `high | medium | low` is assumed. The photo pipeline
   may use another scale.
3. **Flag value types.** `value` is text for most fields, a string enum for `light` and
   a number for `sqm_estimate`. The photo pipeline may want a stricter split.
4. **Id formats.** `user_id`, `decision_id`, `flag_id` shown as prefixed strings in the
   examples. The backend picks the format.
