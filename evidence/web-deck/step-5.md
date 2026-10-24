# Drag to swipe

Date: 2026-10-24

## What changed

- Added `motion` 14.6.0 (installed version), imported from `motion/react`. No other package.
- `SwipeableCard.tsx` wraps the card in a `motion.div` with `drag="x"`. Release past 30% of card width, or faster than 600 px/s, calls `onSwipe("left" | "right")`; otherwise it springs back. The card tilts with the drag and a faint Like / Dislike label fades in.
- `DeckScreen` passes the same `swipe` function the buttons use, and `disabled={busy}`.
- Drag starts from a pointer-down handler on the wrapper that ignores any target inside a `button`, so the photo arrows never start a drag.
- Reduced motion removes the tilt; drag still works.
- The keydown handler now ignores events whose target is a button inside `.deck-card`.

## Commands (from `web/`, direct exit codes)

| Command             | Exit | Result                      |
| ------------------- | ---- | --------------------------- |
| `npm run typecheck` | 0    | clean                       |
| `npm test`          | 0    | 5 files, 121 tests passed   |
| `npm run build`     | 0    | built                       |

Dev server in mock mode on port 5181: `curl http://localhost:5181/` returned 200; server stopped.

No browser was available, so nothing was dragged or clicked. The drag has no automated test.

## Check by eye

- Drag the card past about a third of its width left: it dislikes. Right: it likes.
- A short drag springs back and nothing is sent.
- Pressing on the Previous / Next photo buttons does not drag; they still change the photo.
- With focus on a photo button, Left / Right / Up do nothing; elsewhere they still swipe.
- Dislike, Love and Like buttons still work, and are disabled while a swipe is in flight.
- With reduced motion on, the card does not tilt, and dragging still works.
