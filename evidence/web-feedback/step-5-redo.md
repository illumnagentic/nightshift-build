# Evidence: empty Done on an optional feedback screen is a skip

Date: 2026-10-24

## Change

`web/src/feedback/FeedbackScreen.tsx`: the Done button now sends `skipRequest()` when the screen
is optional and `canSubmit(form, true)` is false (no chip answer, blank free text). Otherwise it
sends `toRequest(form, card.chips)` as before. Compulsory screens are unchanged: Done stays
disabled until there is an answer. Error handling, sending state and `onDone` are unchanged.
`feedbackForm.ts` is not edited.

## Commands (from `web/`)

| Command | Exit |
| --- | --- |
| `npm run typecheck` | 0 |
| `npm test` (6 files, 162 tests passed) | 0 |
| `npm run build` | 0 |

## Check by eye

Read from the code, not clicked in a browser (no browser available here). After onboarding, on an
optional screen with nothing answered and an empty or whitespace-only note, Done calls
`send(skipRequest())`, the same body Skip sends. With a chip answer or non-blank note, Done sends
the built body. On a compulsory screen the empty case cannot reach the click, as Done is disabled.

## Formatting

An automatic Prettier pass had reformatted four unrelated hunks in the same file. The file was
restored and the Done change reapplied as a one-line replacement, so the diff is that single line.
Exit codes below are from the final run.
