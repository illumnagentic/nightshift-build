# Deck ignores stale fetch responses

Date: 2026-10-24

## Cause

In development, React StrictMode runs effects twice, so the deck requested its first batch twice. The first response was still accepted after the second reset, and the second response carried the same unswiped cards. The reducer then saw a batch with nothing new while cards were queued, set `emptyReason`, and `needsRefetch` stayed false. The deck ended after 10 cards.

## Fix

- `web/src/deck/useDeck.ts`: a generation ref replaces the "live user" ref. It is bumped in the effect cleanup (reset, user change, unmount). Each deck and swipe request captures the generation when it starts and dispatches its result only if the generation is unchanged. Swipe responses use the same guard.
- `web/src/deck/deckState.ts`: `fetchOk` sets `emptyReason` for a batch with nothing new only when the queue is at or below the refetch threshold. A refetch only starts at or below the threshold, so the loop guard still stops repeat requests, and a stray duplicate batch with plenty queued no longer blocks later refetches.

## Tests added

- `deckState.test.ts`: a duplicate batch of known ids arriving with 10 cards queued leaves `emptyReason` null; after 7 swipes the queue is at 3 and `needsRefetch` is true.
- The existing "stops refetching when a batch adds nothing new" test is unchanged and passes.
- The generation guard lives in the hook and has no unit test (no hook test setup in the repo). The orchestrator checks in the browser.

## Commands (from web/)

- `npm run typecheck` exit 0
- `npm test` exit 0, 6 files, 163 tests passed
- `npm run build` exit 0
