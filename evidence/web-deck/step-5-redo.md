# Drag up to love

Date: 2026-10-24

## What changed

- `SwipeableCard.tsx`: `drag` on both axes. On release the dominant axis decides, so a diagonal drag fires at most one action. Horizontal is unchanged (30% of card width or 600 px/s, left or right). Upward calls `onSwipe("superlike")` past 25% of card height or faster than 600 px/s upward. Downward and short drags spring back.
- `onSwipe` type now includes `"superlike"`. `DeckScreen` already passes the same `swipe` the buttons use, so it needed no change.
- A faint aria-hidden "Love" cue with a heart fades in while dragging up, styled like the Like and Dislike cues.
- `deck.css`: `touch-action: none` on the card (was `pan-y`) and the Love cue position and colour.
- Kept: no drag from buttons, disabled while busy, reduced motion removes the tilt.

## Thresholds

- Up: 25% of card height, or 600 px/s upward.
- Left and right: 30% of card width, or 600 px/s.

## Commands (from `web/`, direct exit codes)

| Command             | Exit | Result |
| ------------------- | ---- | ------ |
| `npm run typecheck` | 0    | clean  |
| `npm test`          | 0    | 5 files, 121 tests passed |
| `npm run build`     | 0    | built  |

No browser was available, so nothing was dragged or clicked. The drag has no automated test.

## Check by eye

- Drag the card up past about a quarter of its height, or flick up: it loves, same as the Love button.
- A diagonal drag fires one action only, the dominant direction.
- Drag down, or a short drag in any direction: it springs back, nothing is sent.
- Left and right drags still dislike and like.
- Pressing on the photo arrows or the Love button does not start a drag.
- A touch that starts on the card no longer scrolls the page.
