# Feedback `skipped` in types, client and mock

Date: 2026-10-24

## Changes

- `FeedbackRequest` gains optional `skipped`; `FeedbackResponse` has `skipped: boolean`.
- The HTTP client already sends the whole request object as the PUT body, so `http.ts` is unchanged.
- Mock `putFeedback`: `skipped: true` is accepted only with `chips: []` and `free_text: null` (after blank text becomes `null`), otherwise 422 `invalid_request`. A non-boolean `skipped` is also 422 `invalid_request`.
- A skip is stored on the decision, returned with `skipped: true`, and bumps the profile version (cause `feedback`).
- Profile weights leave out decisions whose feedback is a skip when counting offered. A later non-skipped PUT replaces the skip.
- Normal feedback returns `skipped: false`.

## Changed existing assertions

None. No existing test compares a whole feedback response object, so none needed `skipped: false`.

## Added tests

- http: "sends skipped in the PUT feedback body"
- mock: "returns skipped false for normal feedback"
- mock: "stores a skip, returns it and bumps the profile version"
- mock: "returns 422 invalid_request for a skip with chips or free text"
- mock: "lets a later non-skipped answer replace a skip"
- mock: "does not lower a factor's weight when another card with that chip was skipped"

## Commands (from web/)

- `npm run typecheck`: exit 0
- `npm test`: exit 0, 5 files, 127 tests passed
- `npm run build`: exit 0
