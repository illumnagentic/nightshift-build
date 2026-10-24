# Clear the favourites note on continue

Date: 2026-10-24

## Change

- `web/src/deck/deckState.ts`: the `continue` action now clears `favourited` as well as `pendingFeedback`, so "Added to favourites" does not reappear above the next card after the feedback screen.
- `web/src/deck/deckState.test.ts`: two tests added.
  - Superlike opens feedback with `favourited` set; after `continue`, `favourited` is false and the next card shows.
  - A swipe that opens no feedback screen keeps `favourited` until the next swipe starts.

## Changed existing tests

None. The existing "keeps favourited from the response and clears it on the next swipe" test still passes unchanged.

## Commands (run from `web/`)

- `npm run typecheck`: exit 0
- `npm test`: exit 0, 6 files, 162 tests passed
- `npm run build`: exit 0
