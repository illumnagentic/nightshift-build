# Evidence: when the feedback screen opens

Date: 2026-10-24

## Outcome table

`feedbackOutcome(response, card)` in `web/src/deck/deckState.ts`. Tests in
`web/src/deck/deckState.test.ts`, describe "feedbackOutcome".

| feedback_required | source      | action             | outcome    | test                                           |
| ----------------- | ----------- | ------------------ | ---------- | ---------------------------------------------- |
| true              | ranked      | left/right/superlike | compulsory | "is compulsory when required, ranked, %s"      |
| true              | exploration | left/right/superlike | compulsory | "is compulsory when required, exploration, %s" |
| false             | ranked      | left/right/superlike | optional   | "is optional for ranked, %s"                   |
| false             | exploration | left               | none       | "is none for exploration, left"                |
| false             | exploration | right/superlike    | optional   | "is optional for exploration, %s"              |

Reducer tests: "moves to the next card when the outcome is none" (next card shown, no
pending feedback); "drops the swiped card and opens optional feedback when none is
required" (`compulsory: false`); the existing required-feedback test now also asserts
`compulsory: true`. `PendingFeedback` gains `compulsory: boolean`. `source` is read only
inside `feedbackOutcome`.

## Changed existing tests

Each followed from the rule that a ranked card opens optional feedback on any action.

1. "drops the swiped card and shows the next when no feedback is required" renamed
   "drops the swiped card and opens optional feedback when none is required". Before:
   expected phase `card` and `pendingFeedback` null. After: phase `feedback`,
   `compulsory` false. Queue and `swiping` assertions unchanged.
2. "does not pause when the response says false even if the card hint is true" renamed
   "does not make feedback compulsory when the response says false even if the card hint
   is true". Before: phase `card`, no pending feedback, current card `b`. After: phase
   `feedback`, `compulsory` false. The hint is still ignored.
3. "keeps favourited from the response and clears it on the next swipe". Superlike now
   opens feedback, which blocks swiping. Added a `continue` before the next
   `swipeStart`. Assertions unchanged.
4. "empties the deck after the last swipe once exhausted". Added a `continue` after the
   swipe. The `empty` assertion is unchanged.

The test helper `card` gained an optional `source` argument.

## Commands (from web/)

- `npm run typecheck`: exit 0
- `npm test`: 5 files, 140 tests passed (127 before, 13 added), exit 0
- `npm run build`: exit 0
