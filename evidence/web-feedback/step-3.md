# Evidence: feedback form logic

Date: 2026-10-24

Module `web/src/feedback/feedbackForm.ts`, tests in `web/src/feedback/feedbackForm.test.ts`.
Pure functions over an immutable `FeedbackForm` (`answers` keyed by `chip_id`, `freeText`).

| function        | covered by                                                                                                              |
| --------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `emptyForm`     | empty answers and free text                                                                                             |
| `setAnswer`     | stores strength and text; same chip replaces (edit); input form not mutated                                             |
| `removeAnswer`  | removes one chip, keeps others; no-op for an unanswered chip                                                            |
| `setFreeText`   | sets card free text                                                                                                     |
| `canSubmit`     | optional always true; compulsory false when empty or whitespace-only free text; true with free text or a chip answer; false again after the only answer is removed |
| `toRequest`     | card order not insertion order; text and free text trimmed, blank to `null`; stale answer for a chip not on the card ignored; empty form gives `{ chips: [], free_text: null }` with no `skipped` key; no repeated `chip_id` |
| `skipRequest`   | exact body `{ chips: [], free_text: null, skipped: true }` (strict equality)                                            |

## Commands (from `web/`)

| command             | exit | result                         |
| ------------------- | ---- | ------------------------------ |
| `npm run typecheck` | 0    | clean                          |
| `npm test`          | 0    | 6 files, 160 tests passed (20 new) |
| `npm run build`     | 0    | built                          |
