# Deck refresh wherever the user is

Date: 2026-10-25

Change:
- `App.tsx` renders `PrefsScreen` for a signed-in user at all times, inside a hidden-when-inactive wrapper, keyed by `user_id`.
- `onSaved` bumps the deck key, so the deck is discarded at save time.
- `onReady` bumps the deck key and switches to Deck only if the user is still on Preferences.
- `DeckScreen` blocked state shows the "Set preferences" button for `commute_failed` as well as `prefs_missing`.

Rule: the deck is discarded at save, refreshed when the commute is ready wherever the user is, and the tab changes only from Preferences.

## Commands (from `web/`)

- `npm run typecheck` exit 0
- `npm test` exit 0, 7 files, 178 tests passed
- `npm run build` exit 0

## Browser reproductions

Results, 2026-10-25, built-in browser against the mock (scripted clicks, so the 1.5-second race is reproduced). "Before" ran the pre-change commit 33441b4 in a separate worktree on its own port; "after" ran this change on port 5183.

### Path A (new user)

- Before: new user "tess" landed on Preferences; saved and opened Deck at once. Deck showed "Save your preferences to see properties." and was still blocked 3.5 seconds later; no cards appeared.
- After: new user "tess" landed on Preferences; saved and opened Deck at once. Deck showed "Commute times are still being worked out.", then cards appeared with no action.

### Path B (alex with a loaded deck)

- Before: saved postcode `FAIL 1AA`, opened Deck at once. The old card was still shown; a swipe gave "No decision with that id." and Retry did not move on.
- After: no old card. Deck showed "Commute times are still being worked out." with Retry. After the failed status it stayed on that block until Retry (logged tradeoff). Saving `EC2N 2DB` brought a fresh deck and the Deck tab.

### Ready while on Favourites

- Before: saved prefs, switched to Favourites, waited until commute times were ready. The user stayed on Favourites, but on returning the deck was still blocked ("Save your preferences to see properties.").
- After: saved prefs, switched to Favourites before commute times were ready. The user stayed on Favourites when ready; the deck was fresh when opened.
