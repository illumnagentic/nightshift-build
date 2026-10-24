# Love button and light page

Date: 2026-10-24

## What changed

- The superlike button is now an inline SVG heart (hidden from assistive technology) with `aria-label="Love"` and a matching `title`. No visible text. It still calls `swipe("superlike")`, is disabled during a swipe, and ArrowUp still superlikes. Dislike and Like keep their text labels.
- `web/src/index.css` sets `color-scheme: light` on `:root`, and a white background with dark text on `body`.
- `deck.css` centres the heart in the button; the button keeps its 44px minimum height.

## Commands (from `web/`, direct exit codes)

| Command             | Exit | Result                                              |
| ------------------- | ---- | --------------------------------------------------- |
| `npm run typecheck` | 0    | clean                                               |
| `npm test`          | 0    | 5 files, 121 tests passed; `smoke.test.ts` unchanged |
| `npm run build`     | 0    | built                                               |

No browser was available, so nothing was clicked. The deck screen has no automated test.

## Check by eye

- The middle button shows a heart and no text; a screen reader announces "Love".
- With the browser set to dark, the heading and "Signed in as" line are dark on white.
