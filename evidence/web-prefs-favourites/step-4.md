# Navigation and wiring

Date: 2026-10-24

## Behaviour

- Signed-in header: "Signed in as X", Switch user, and three tab buttons (Deck, Preferences, Favourites). The current tab has `aria-current="page"`. Default tab is Deck. Switch user returns to Deck.
- The deck stays mounted while another tab is shown (wrapped in a `hidden` element), keyed by user and a deck counter. Its arrow-key listener is attached only while the Deck tab is active.
- Preferences and Favourites mount only while their tab is active, so Favourites reloads each time it opens.
- A deck blocked with `prefs_missing` calls `onNeedPrefs` once, which opens Preferences. The blocked message also has a "Set preferences" button.
- Preferences `onReady` bumps the deck counter (new deck, pending feedback dropped) and switches to Deck.
- Styles in `web/src/nav.css`, scoped under `.app-nav`: 44px targets, visible focus, bold and bordered current tab.

## Commands (from `web/`)

- `npm run typecheck`: exit 0
- `npm test`: exit 0, 7 files, 178 tests passed
- `npm run build`: exit 0
- `web/src/smoke.test.ts`: unchanged, passing

Not clicked in a browser.

## By-eye list

- A new user lands on Preferences.
- Save, "working out", then Deck with fresh cards.
- Favourites shows a card after a Love.
- Arrow keys do nothing on the other tabs.
- A compulsory feedback screen survives a tab switch.
- Switch user returns to Deck.
