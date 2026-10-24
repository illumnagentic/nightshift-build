# Deck state logic

Date: 2026-10-24

## Commands (from `web/`, direct exit codes)

- `npm run typecheck` exit 0
- `npm test` exit 0, 4 files, 81 tests passed (29 new, in `src/deck/deckState.test.ts`)
- `npm run build` exit 0

## Transitions and the tests that cover them

| Transition | Test |
| --- | --- |
| Initial state loads and asks for a batch | "starts in the loading phase and asks for a first batch" |
| No second fetch while one is in flight | "does not ask again while a fetch is in flight" |
| Batch appended in order | "appends a batch in order and shows the first card" |
| Duplicate `decision_id` not appended | "does not append a decision_id already in the queue" |
| Swiped decision not restored by a late fetch | "does not bring back a decision swiped while a fetch was in flight" |
| Batch with nothing new stops refetching | "stops refetching when a batch adds nothing new" |
| Refetch at exactly 3 cards | "asks for more at exactly 3 cards" |
| No refetch at 4 cards | "does not ask for more at 4 cards" |
| No refetch once exhausted | "does not ask for more once the deck is exhausted" |
| Empty state `exhausted` / `no_matches` | "carries exhausted", "carries no_matches" |
| Cards left shown before empty | "shows the cards left before the empty state" |
| Blocked: `prefs_missing`, `commute_pending`, `commute_failed`, message kept | "blocks on %s and keeps the server message" (x3) |
| Other ApiError shows its message | "shows the message of any other ApiError as a generic error" |
| Network failure uses fixed message | "uses the fixed message for a network failure" |
| Failed state stops refetch, retry resumes | "does not refetch while failed, and does again after retry" |
| Swipe failure keeps the card | "keeps the card and shows the message when a swipe fails" |
| In-flight flag blocks a second swipe | "sets the in-flight flag and ignores a second swipe" |
| No swipe without a card | "does not start a swipe with no card" |
| Next card when response says no feedback | "drops the swiped card and shows the next when no feedback is required" |
| Response true, card hint false: pauses | "pauses when the response requires feedback even if the card hint is false" |
| Response false, card hint true: no pause | "does not pause when the response says false even if the card hint is true" |
| Continue shows next card | "moves to the next card on continue" |
| `favourited` kept, cleared on next swipe | "keeps favourited from the response and clears it on the next swipe" |
| Right swipe not favourited | "does not favourite on a right swipe" |
| Empty after last swipe | "empties the deck after the last swipe once exhausted" |
| Reset | "returns to the initial state" |

`useDeck.ts` has no test: the test environment has no DOM and no hook renderer. It is
checked by typecheck and build only.
