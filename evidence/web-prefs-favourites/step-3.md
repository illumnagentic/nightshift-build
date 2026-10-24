# Favourites screen

Date: 2026-10-24

Files: `web/src/favourites/FavouritesScreen.tsx`, `web/src/favourites/favourites.css`. Not wired into the app.

## Behaviour by state

- Loading: "Loading favourites…".
- Load error: the backend message (or "Could not reach the server. Try again.") and a Retry button that reloads.
- Empty: "No favourites yet. Love a property to save it here."
- List: every favourite, no paging. Each entry has the first photo as a fixed-size thumbnail
  (alt text from the address, else "Property photo"), or a plain block when there are no photos;
  price with qualifier, the address line, and "Added <short en-GB date>". Missing values are left out.
- Remove: opens a native dialog titled "Remove from favourites" with the price and address and a
  required "Why are you removing it?" box. Confirm is disabled while the trimmed reason is blank
  and while sending. While sending, Cancel is disabled and Escape does nothing. Otherwise Escape and Cancel close it and return focus to that entry's Remove button.
- Confirm: sends the trimmed reason. On success the dialog closes and the entry leaves the list.
  On error the dialog stays open with the reason kept, showing the backend message or
  "Could not reach the server. Try again."
- Responses that arrive after the screen or dialog is gone are ignored. `source` is never shown.

## Commands (from `web/`)

- `npm run typecheck` exit 0
- `npm test` exit 0, 7 files, 178 tests passed (no component tests: none exist for screens in this repo)
- `npm run build` exit 0

Not tried in a browser: no way to click here. Dialog focus, layout and styling are unexercised
beyond type checking.
