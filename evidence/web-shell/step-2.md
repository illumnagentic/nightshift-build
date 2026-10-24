# Contract types and HTTP client: test evidence

Date: 2026-10-24. Run from `web/`.

| Command | Exit |
| ------- | ---- |
| `npm run typecheck` | 0 |
| `npm test` | 0 |

Test summary: 2 files, 11 tests passed (1 smoke, 10 in `src/api/http.test.ts`).

## Endpoint to method

| Endpoint | Method on `ApiClient` | User header |
| -------- | --------------------- | ----------- |
| GET /users | `listUsers()` | no |
| POST /users | `createUser(req)` | no |
| GET /prefs | `getPrefs(userId)` | yes |
| PUT /prefs | `putPrefs(userId, req)` | yes |
| GET /deck?n | `getDeck(userId, n?)` | yes |
| GET /listings/{id} | `getListing(userId, listingId)` | yes |
| POST /decisions/{id}/swipe | `swipe(userId, decisionId, req)` | yes |
| PUT /decisions/{id}/feedback | `putFeedback(userId, decisionId, req)` | yes |
| POST /flags/{id}/correction | `correctFlag(userId, flagId, req)` | yes |
| GET /favourites | `getFavourites(userId)` | yes |
| DELETE /favourites/{listing_id} | `removeFavourite(userId, listingId, req)` | yes |
| GET /profile | `getProfile(userId)` | yes |
| GET /stats | `getStats()` | no |
