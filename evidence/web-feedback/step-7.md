# Exploration tag in mock mode (2026-10-24)

## What renders when

- `VITE_API_MODE=mock` and the top card's `source` is `exploration`: a small dashed
  tag reading "Exploration (test only)" above the swipeable card, outside the drag area.
- Any other mode, or a ranked card: nothing extra. The card itself is not styled by source.

## Bundle check

- `VITE_API_MODE=mock npm run build`: the string appears once in `dist/assets/*.js`.
- Plain `npm run build` (no mode set) and `VITE_API_MODE=http npm run build`: the string
  is absent from `dist`. Vite inlines the env comparison as false and the branch is
  removed, so it is tree-shaken, not merely unreachable.

## Commands (from `web/`)

- `npm run typecheck`: exit 0
- `npm test`: exit 0, 6 files, 163 tests passed
- `npm run build`: exit 0

Not checked in a browser.
