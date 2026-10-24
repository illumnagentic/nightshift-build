# Deck screen, buttons, keys and feedback stub

Date: 2026-10-24

## Commands (from `web/`, direct exit codes)

| Command                                                                                          | Exit    | Result                                               |
| ------------------------------------------------------------------------------------------------ | ------- | ---------------------------------------------------- |
| `npm run typecheck`                                                                              | 0       | clean                                                |
| `npm test`                                                                                       | 0       | 5 files, 106 tests passed; `smoke.test.ts` unchanged |
| `npm run build`                                                                                  | 0       | built                                                |
| `VITE_API_MODE=mock npm run dev -- --port 5180 --strictPort`, then `curl http://localhost:5180/` | n/a     | HTTP 200; server stopped, port 5180 free             |
| process-wording check (repo root)                                                                | 0 | none                                                 |

No browser was available, so nothing was clicked. The deck screen has no automated test.

## Check by eye (mock mode, `VITE_API_MODE=mock npm run dev`)

| Check                                                                                      | Result |
| ------------------------------------------------------------------------------------------ | ------ |
| Sign in as alex: the deck shows a card under "Signed in as alex"                           |        |
| Dislike, Superlike and Like buttons sit in a row under the card; Superlike looks different |        |
| Buttons are disabled while a swipe is in flight                                            |        |
| ArrowLeft, ArrowRight, ArrowUp swipe left, right, superlike                                |        |
| Arrow keys do nothing while typing in a text field; holding a key swipes once              |        |
| First swipes show the Feedback panel; focus is on Continue; next card only after Continue  |        |
| Superlike shows "Added to favourites" (above the next card, or on the feedback panel)      |        |
| The note clears on the following swipe                                                     |        |
| Photo arrows on the card still work and the photo index resets on each new card            |        |
| Card face never shows whether a card is ranked or exploration                              |        |
| Swipe through the whole deck: the empty message appears                                    |        |
| Switch user returns to the picker; signing in as jordan loads a fresh deck                 |        |
| A new user (no prefs) shows the prefs-missing message                                      |        |
| Tab order and focus outlines are visible; reduced-motion setting removes transitions       |        |
