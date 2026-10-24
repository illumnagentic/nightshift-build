# API contract mock test

- **Date**: 2026-10-24
- **Test**: an Opus subagent was given only `docs/api-contract.md`. From it alone it built
  fixtures and an in-memory plain-Node mock, then ran a full user journey against the mock
  (`node run.mjs`, exit 0).
- **Verdict**: enough with gaps. The examples and prose agree; the gaps below are places
  where frontend and backend could disagree.
- **Resolution**: 8 cosmetic gaps were skipped on purpose and the rest were
  settled on 2026-10-24 and written into
  `docs/api-contract.md`. Line numbers below refer to the contract before that edit.

Severity: B = blocks mocks, M = would cause a frontend-backend mismatch, C = cosmetic.

## Gaps found

1. GET /prefs (l.73) "all fields are null" — is `parsed` null, or `{hard:{all null}, soft:[]}`? Guess: `parsed: null`. M.
2. PUT /prefs (l.120) only says `max_commute_min` is optional; implies `commute_postcode` is required but never says. No postcode → commute_status? card `commute` null? Guess: required. M.
3. Deck `feedback_required` (l.145–147) is a prediction made at serve time; on a refetch with unswiped cards outstanding, or after a re-save drops cards, the card value and swipe value can differ. Contract says swipe wins but not what the UI does before the swipe (e.g. show "required" badge?). Guess: prediction = swipes + outstanding + index < 15; obey swipe response. M.
4. After onboarding (l.339–340, 370–372): superlike not mentioned (only "right swipes may show an optional one"). Can feedback be PUT on a post-onboarding left swipe — accepted or rejected, which code? Guess: superlike = right; left accepted. M.
5. `strength` (l.365) — required or nullable? Chip `phrases` carry no strength, so the UI has no defined way to derive it from a tapped phrase. Guess: required, separate picker. M (UI design depends on it).
6. Chip catalogue (Open point 1): unknown chip_ids/labels/phrases. Mock reuses the two example chips. C for mocks, M later.
7. Clearing feedback (l.350) says "empty `free_text`", which reads as `""`, but l.25 says unknown values are `null`, never `""`. Guess: accept `null`. M.
8. Profile version bumps (l.384, 508): `cause.type: swipe` exists, so swipes bump the version, but the swipe response has no `profile_version`. Does every feedback PUT bump (including a no-op edit or a clear)? Guess: every swipe and every feedback PUT bumps. M (profile trail in recording).
9. `GET /deck?n=` (l.136): n>10 "capped" (clamp, not 422); n=0, negative, non-integer undefined. Guess: clamp >10, 422 invalid_request for <1. C.
10. Deck refetch (l.137) — does a later GET /deck re-serve already-served unswiped cards, or only new ones? Does "pool used up" count served-unswiped? Does a re-save make previously served-and-dropped listings servable again? Guess: only never-served listings; re-save frees dropped listings. M (duplicate cards or lost cards).
11. Deck ordering / exploration ratio: "about 1 in 5" per batch or overall; whether order within a batch is rank order. Guess: overall, no ordering promise. C.
12. Feedback with the same chip_id twice — undefined. Guess: 422 invalid_request. C.
13. Favourites (l.428–455): order unspecified; superlike on an already-favourited listing (added_at kept or reset?); can a removed listing come back in the deck. Guess: newest first; keep added_at. C.
14. DELETE /favourites (l.461) "can bump the profile version" — when does it not? Guess: always bumps. M (recording relies on favourite_removed cause).
15. Flag correction (l.396–424): is the correction per user or global on the shared cached flag (other users would see it)? Does it bump the profile (history example says yes, but the response carries no `profile_version`)? Empty text / undo undefined. Guess: global record, bumps profile, empty text 422 invalid_request. M.
16. 422 code overlap (l.22–24 vs 130, 392, 476): missing `reason` field is both a shape mismatch (`invalid_request`) and `reason_required`; same for `commute_postcode` missing vs `invalid_postcode`. Guess: reason_required for missing/empty reason; invalid_request for missing postcode, invalid_postcode for a bad one. M.
17. Listing fields (l.6, 290): "names and enums exactly those in `schema.sql`" — the contract does not list enums for `property_type`, `tenure`, `price_qualifier`, `epc_current`, `council_tax_band`, `floor_level` (text or enum?), `stations[].types`, `room`, nor which card fields are nullable. Frontend types cannot be written from this file alone. Guess: strings, everything except `id` nullable. M (blocks strict TS types; not the mock itself).
18. GET /listings/{id} returns no `commute` and no chips; card and detail views must merge. Fine but undocumented whether `listing_id` from favourites can be fetched after the deck dropped it. Guess: yes. C.
19. GET /stats before any eval has run — `arms` null? 404? only `updated_memory` is said to be nullable. Guess: fixture values. M (dashboard empty state).
20. POST /users validation: allowed characters, case sensitivity of `username_taken`, trimming. Guess: trimmed, case sensitive, empty → invalid_request. C.
21. Unknown route / method error code not defined (e.g. 404 `not_found`, 405). Guess: 404 not_found. C.
22. `commute_status` has only null/pending/ready (l.102). No failure state if TfL errors for the whole batch — the frontend would poll forever. Guess: none. M.
23. Polling interval / timeout for commute_status not given; nor typical duration. C.
24. Base path: endpoints are written without `/api` while base URL includes it. Read as prefixed. C.
25. CORS: Vite dev server (different port) sending custom header `X-User-Id` triggers a preflight; the contract does not say the backend allows it, or whether Vite proxies `/api`. Not a mock issue. M at integration.
26. Onboarding count (l.146, 338, 370): "first 15 swipes" — do swipes on decisions later dropped by a re-save never count (not swiped, so no) and do swipes before a re-save still count (yes)? Not stated. Guess: count all swipes ever. C.
27. Swiped-but-feedback-pending card when the user re-saves prefs: kept (swiped), feedback still allowed — consistent but unstated whether `feedback_required` is enforced server side at all (no error code exists for "next swipe before required feedback"). Guess: not enforced. M.

Example vs prose checks: examples agree with prose. Favourites listing example has one photo where the card has two — illustrative only. `cause.flag_id`/`listing_id` present in every history example, consistent. No error code used but undefined, except the implicit routing 404 (21).

---

# Second mock test

- **Date**: 2026-10-24
- **Test**: an Opus subagent was given only `docs/api-contract.md`. It wrote strict TS
  types, fixtures and an in-memory plain-Node mock, then ran a full journey against it
  (`node run.mjs`): 198 assertions passed, 0 failed, exit 0. Nothing blocked the mock.
- **Verdict**: enough with gaps.
- **Resolution**: points 1, 6, 7, 8, 10, 11, 15 and 17 settled on 2026-10-24 and written
  into the contract. Gaps 3, 4, 13, 18 and 19 are covered by the new General rule (the
  backend owns validation details; the frontend shows `error.message`). The rest are
  known minor items, not changed. Line numbers in the gap list refer to the contract
  before that edit.

## Gaps found

1. `parsed` in the PUT /prefs response: filled at once or null until the parse ends. Settled.
2. Is `text` required in PUT /prefs. Settled: required and non-empty.
3. `max_commute_min` validation (integer, range, null). Covered by the general rule.
4. Postcode validity and normalisation. Covered by the general rule.
5. Null versus empty array in `parsed.hard` and `soft`. Known minor item.
6. Are `chips` and `free_text` required keys in the feedback PUT. Settled.
7. Can a swiped listing be served again. Settled.
8. Empty deck cannot tell "exhausted" from "no matches". Settled.
9. How the per-card `feedback_required` hint is computed in a batch. Known minor item.
10. Does the onboarding count survive a prefs re-save. Settled.
11. `room` nullability on photo-scope flags. Settled. The sub-question (value of a `room`-field flag) is a known minor item.
12. Whitespace-only flag correction text, re-correction, correcting an unserved listing's flag. Known minor item.
13. Whitespace or non-string `reason`; order against `not_favourited`. Covered by the general rule.
14. `decision_id` on a `favourite_removed` cause. Known minor item.
15. Superlike bumps the version once or twice. Settled.
16. Which listings GET /listings/{id} can return. Known minor item.
17. Another user's `decision_id`. Settled.
18. Error precedence in feedback PUT and GET /deck. Covered by the general rule.
19. Username rules and case sensitivity of `username_taken`. Covered by the general rule.
20. Card and favourite listing field set defined only by example. Known minor item.
21. `commute` never null; `minutes` integer. Known minor item.
22. Listing with `commute.minutes: null` when a max commute is set. Known minor item (backend concern).
23. Re-saving prefs while `pending` or with identical values. Known minor item.
24. Chips on a re-served card: same list, logged once. Known minor item (server side).
25. A removed favourite cannot come back. Known minor item.
26. Which wins if `schema.sql` and the contract enum tables diverge. Known minor item (cosmetic).
27. Media kinds line is schema detail. Known minor item (cosmetic).
28. `invalid_request` repeated on GET /deck despite the General note. Known minor item (cosmetic).
29. `sqm_estimate` integer or float. Known minor item (cosmetic).
30. No poll interval or timeout for `pending`. Known minor item (cosmetic).
31. Timestamp format of `added_at` and `created_at` shown only by example. Known minor item (cosmetic).
32. Order of GET /users and GET /favourites. Known minor item (cosmetic).
33. "About 1 in 5" exploration, per batch or overall. Known minor item (cosmetic).
34. Nullability of `base`, `base_memory` and `sd` in stats. Known minor item (cosmetic).
35. Missing `Content-Type` and unknown route status. Known minor item (cosmetic).
36. Chip catalogue unknown, so mock chip ids were invented. Known minor item (Open point 1).
37. The mock needed its own hook to force `failed` and finish `pending`. Known minor item (correct behaviour).
