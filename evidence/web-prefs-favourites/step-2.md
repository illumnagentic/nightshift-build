# Prefs screen

Date: 2026-10-24

Files: `web/src/prefs/PrefsScreen.tsx`, `web/src/prefs/prefs.css`. Not wired into the app.

## Behaviour by state

- Loading: fields disabled until `getPrefs` returns, then filled from the saved prefs.
  New users get empty fields.
- Status `pending` on open: polls `getPrefs` every 1.5 s and shows "Working out commute times…".
- Status `failed` on open: shows "Commute times could not be worked out. Check the postcode and save again."
- Status `ready` or none on open: no polling.
- Save: disabled until text and postcode are non-empty and the limit is blank or a whole
  number, and while saving. A bad limit shows "Enter a whole number of minutes." under the field.
- After a save: shows the non-null hard limits in plain words and the soft list, read-only,
  then polls. `ready` calls `onReady()`. `failed` shows the failed message and Save stays usable.
- A new save, or leaving the screen, stops the poll timer. Responses that arrive after
  that are ignored.
- A save still in flight when the screen is left (or the user changes) is cancelled too:
  its response is ignored and no polling starts.
- A 4xx on save shows the backend's message. Any other error shows
  "Could not reach the server. Try again." Typed values are kept.
- `source` is never shown.

## Commands (from `web/`)

- `npm run typecheck` exit 0
- `npm test` exit 0, 7 files, 178 tests passed (no component tests: none exist for screens in this repo)
- `npm run build` exit 0

Not tried in a browser: no way to click here. Polling, error and styling behaviour are
unexercised beyond type checking.
