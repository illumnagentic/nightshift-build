# Evidence: feedback screen in the deck

Date: 2026-10-24

Component `web/src/feedback/FeedbackScreen.tsx`, styles in `web/src/feedback/feedback.css`
(all under `.feedback-screen`). `DeckScreen.tsx` renders it in the feedback phase, keyed by
`decision_id`. `web/src/deck/FeedbackStub.tsx` is deleted. `web/src/smoke.test.ts` is unchanged.

## What the screen shows

- Heading "Tell us why", focused when the screen opens.
- One-line summary: "You liked / passed on / loved this", price with qualifier, address line.
- "Added to favourites" note after Love.
- The card's chips as pill buttons, in the order sent. An answered chip has `aria-pressed="true"`,
  a filled style and its strength label. Clicking opens the chip dialog, pre-filled when answered.
- Labelled free-text box for the card as a whole.
- Done: disabled while sending, and when compulsory with nothing answered. Sends the built body,
  then moves to the next card.
- Skip: rendered only when optional. Sends the skip body, then moves to the next card.
- Compulsory with nothing answered: hint "Pick a feature or write a note to continue."
- Error: the server message for an API error, otherwise "Could not reach the server. Try again."
  The screen and answers stay and the buttons are enabled again.
- `source` is not read or shown.

## Commands (from `web/`)

| Command | Exit |
| --- | --- |
| `npm run typecheck` | 0 |
| `npm test` (6 files, 160 tests passed) | 0 |
| `npm run build` | 0 |
| `VITE_API_MODE=mock npm run dev -- --port 5182 --strictPort`, then curl `http://localhost:5182/` | HTTP 200 |

The dev server was stopped afterwards. No component tests exist (node test environment, no jsdom).
This was not clicked through in a browser.

## By-eye list (not yet done)

- Compulsory card: no Skip, Done disabled until a chip answer or text, hint shown.
- Optional card: Skip shown, Done always enabled.
- Chip dialog: save marks the chip with its strength; reopening pre-fills; Remove clears the mark.
- Error: a failed send shows the message, keeps answers, buttons work again.
- Done or Skip shows the next card.
- Exploration card swiped left (after onboarding) goes straight to the next card.
- Tab reaches every control; focus starts on the heading; focus returns to the chip after the dialog.
