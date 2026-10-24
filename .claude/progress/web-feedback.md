# Feature: F3 Feedback screen (frontend)

- **Slug**: web-feedback
- **Owner**: Yewen
- **Started**: 2026-10-24
- **Branch**: feat/web-feedback
- **BASE_SHA**: dc0e819d63a39330b6e1c9aef38eef28f8100499
- **Status**: in progress

---

## REQUIREMENTS (LOCKED)

Human, in session, 2026-10-24: "We will have to move on to the next step without
backend for now. run F3"

Binding line from `docs/plan.md` (Frontend — Yewen):

> "**F3 Feedback screen** — `feat/web-feedback` — filtered chips, phrase dialog with
> preset suggestions, free-text box, compulsory for the first 15–20 cards."

Binding lines from `docs/decisions.md` (Core interaction):

> "2. Feedback screen after the decision. A preset list of feature chips (e.g. lush
> garden, natural light inside, parking), plus a free-text box for the card as a
> whole."

> "3. Tapping a chip opens a dialog: free text only, with preset suggested phrases.
> No numeric rating. Chips are optional, any number of them, and an existing
> answer can be edited."

> "4. Done closes the screen and the next card appears."

Binding lines from `docs/api-contract.md` (Swipe and feedback, Chip catalogue):

> "The frontend renders `chips[]` as sent, in the order sent, and never filters, adds or
> reorders chips."

> "`strength` is required on every chip and is one of `must_have`, `nice_to_have`,
> `would_prefer_not`, `deal_breaker`. Preset `phrases` carry no strength: tapping one
> fills `text` only, and the user picks the strength separately."

> "`feedback_required` here is authoritative; the value on the card was only a hint. If
> `true`, the frontend must collect feedback before showing the next card."

> "Replaces the whole feedback for the decision, so an existing answer can be edited.
> `chips` and `free_text` are both required keys"

Answers to kickoff questions, human, 2026-10-24:

1. Onboarding: "Need one answer" — during onboarding Done stays disabled until at least
   one chip answer or some free text is given.
2. After onboarding (human, relaying the backend agent's proposal and agreeing it):

   > "Ranked card: feedback on both left and right swipes, with a skip button.
   > Exploration card: left swipe, no feedback (the curator was right, nothing to
   > learn). Right swipe, feedback with a skip button (a false exclude, which is exactly
   > the reason we want).
   > Superlike: feedback with skip, same as a right swipe.
   > Three things to keep:
   > Onboarding stays compulsory. For the first 15–20 cards there's no skip, on any
   > swipe. That's where the cold-start signal comes from. ... I'd ask on every card
   > during onboarding, exploration ones included.
   > A skip has to be logged as a skip. ... So the frontend sends an explicit
   > skipped: true, and I leave skipped screens out of the offered counts.
   > Small leak: if left swipes on exploration cards never show feedback, a sharp user
   > could work out which cards are exploration. It only shows after they've swiped, so
   > it doesn't bias that swipe. I think it's fine for a recording, just noting it.
   > If you're happy, I'll update decisions.md and add skipped to the API contract."

   Human: "We will update the API contract".

### Source

This session's conversation, quoted above. `docs/plan.md`, `docs/decisions.md`,
`docs/api-contract.md` on `main` at `dc0e819`.

### Dependency on a contract change

`docs/decisions.md` and `docs/api-contract.md` on `dc0e819` do not yet carry the
post-onboarding rule or `skipped`. The backend side will add them. Until that lands this
feature assumes: `PUT /decisions/{id}/feedback` accepts `"skipped": true` with
`"chips": []` and `"free_text": null`; `skipped` is optional and false when absent; the
response echoes `skipped`. If the merged contract differs, the API step is redone to
match before this feature merges.

### Explicitly out of scope

- Editing `docs/decisions.md` or `docs/api-contract.md` (backend side updates them).
- Flag corrections (`POST /flags/{id}/correction`), listing detail, photo flags.
- Editing feedback after leaving the screen (e.g. from favourites).
- Prefs form, favourites screen (F4); dashboard (F5).
- Any backend, `worker/` or `dataset/` change.
- Showing `source` anywhere, or styling by it.
- Numeric ratings; agent-generated chips; filtering, adding or reordering chips.
- A router, state library, CSS framework, Testing Library, jsdom, component tests.
- Any new dependency. The dialog uses the native `<dialog>` element.
- Ticking `docs/plan.md` — done in the merging PR.

---

## AMENDMENTS

_None._

---

## RULES IN FORCE

| Rule                                                                                                                         | Source                                                        | Applies to              |
| ---------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- | ----------------------- |
| Commits only via `.claude/scripts/safe-commit.sh`, title only, no signature, human approves                                  | `.claude/CLAUDE.md`                                           | commits                 |
| Commit title `type(scope): message`; scope `web` (progress-only commits `kit`)                                               | `.claude/CLAUDE.md`, `.claude/kit-config.md`, commit-composer | commits                 |
| Plain British English, short sentences, banned marketing words                                                               | `.claude/CLAUDE.md`                                           | docs, comments, UI text |
| No scope creep: touch only the step's declared files                                                                         | `.claude/CLAUDE.md` #1                                        | code, docs              |
| No new dependencies                                                                                                          | `.claude/CLAUDE.md` #2                                        | code                    |
| Never weaken a test to make it pass                                                                                          | `.claude/CLAUDE.md` #3                                        | tests                   |
| No speculative generalisation; walk the ladder                                                                               | `.claude/CLAUDE.md` #4                                        | code                    |
| Every tradeoff written into TRADEOFFS when made, not only reported                                                           | `.claude/CLAUDE.md` #5; missed twice in F2                    | progress file           |
| Implementer never ticks its own boxes                                                                                        | `.claude/CLAUDE.md` #6                                        | progress file           |
| Evidence has no process wording; the process-wording check runs last and exits 0                                             | kit check script; F1 and F2 failures                          | evidence                |
| Use the existing `api` client, types, `useDeck` and deck components; do not duplicate them                                   | `.claude/CLAUDE.md` ladder rung 2                             | code                    |
| `source` may be read only to decide whether the feedback screen opens and whether Skip is offered; never shown, never styled | `docs/decisions.md`, human answer 2026-10-24                  | code                    |
| Swipe response `feedback_required: true` means compulsory screen, no Skip, Done needs one answer                             | `docs/api-contract.md`, human answers 1–2                     | code                    |
| Chips rendered as sent, in order sent; never filtered, added or reordered                                                    | `docs/api-contract.md` (Chip catalogue)                       | code                    |
| Strength required on every chip answer; phrases fill text only                                                               | `docs/api-contract.md` (Feedback)                             | code                    |
| Empty or whitespace text sent as `null`, never `""`; no repeated `chip_id`                                                   | `docs/api-contract.md` (Feedback)                             | code                    |
| A skip is sent as `skipped: true`, never as empty feedback                                                                   | human answer 2                                                | code                    |
| Show `error.message` for any 4xx; no client copy of backend validation formats                                               | `docs/api-contract.md` (General)                              | code                    |
| Every action reachable by keyboard; dialog focus handled; clear accessible names                                             | house practice                                                | code                    |
| Human eye test is in VERIFICATION, not in step done-whens                                                                    | F1 retro                                                      | plan                    |
| `docs/plan.md` changes only to tick F3, in the merging PR                                                                    | `docs/decisions.md` (Overview)                                | docs                    |

---

## PLAN

All paths are relative to the repo root. Each step leaves the app working in mock mode.

### Step 1 — Feedback `skipped` in types, client and mock

**Goal**: The feedback request and response carry an optional `skipped`, the HTTP client
sends it, and the mock stores it and leaves skipped screens out of offered counts.

**Files in scope**: `web/src/api/types.ts`, `web/src/api/http.test.ts`,
`web/src/api/mock.ts`, `web/src/api/mock.test.ts`, `evidence/web-feedback/step-1.md`.

**Done when**: `FeedbackRequest` has optional `skipped?: boolean` and `FeedbackResponse`
has `skipped: boolean`; an HTTP client test shows `skipped: true` is sent in the PUT
body; the mock accepts `skipped: true` only with `chips: []` and `free_text: null`
(otherwise 422 `invalid_request`), returns `skipped: true`, still bumps the profile
version, and does not count that card's chips as offered in its profile weights; the
mock returns `skipped: false` for normal feedback; existing tests pass unweakened;
typecheck, tests and build exit 0; the process-wording check exits 0.

**Evidence location**: `evidence/web-feedback/step-1.md`.

- [x] Implemented — types.ts, mock.ts diff; http.ts untouched (2026-10-24)
- [x] Tested — evidence: npm test exit 0, 127 passed; 6 new tests incl. http body and skip weight (2026-10-24)
- [x] Best practices met — evidence: typecheck/build exit 0; mock validates skipped type and shape (2026-10-24)
- [x] Matches locked requirements — evidence: done-when met; check-process-refs.sh exit 0 (2026-10-24)
- [x] No scope drift — evidence: git diff touches only the 4 declared files plus evidence/web-feedback/step-1.md (2026-10-24)

### Step 2 — When the feedback screen opens

**Goal**: The deck decides after each swipe whether to open the feedback screen and
whether it is compulsory, by the rule in the locked requirements.

**Files in scope**: `web/src/deck/deckState.ts`, `web/src/deck/deckState.test.ts`,
`web/src/deck/useDeck.ts`, `evidence/web-feedback/step-2.md`.

**Done when**: a pure function decides the outcome from the swipe response, the card's
`source` and the action: `feedback_required: true` → screen, compulsory (any source,
any action); otherwise ranked + any action → screen, optional; exploration + `left` → no
screen, next card; exploration + `right` or `superlike` → screen, optional. The pending
feedback state carries `compulsory: boolean`. A test covers every row (including
exploration + left during onboarding → compulsory). `source` is read only here; typecheck,
tests and build exit 0; the process-wording check exits 0.

**Evidence location**: `evidence/web-feedback/step-2.md`.

- [x] Implemented — feedbackOutcome + PendingFeedback.compulsory in deckState.ts; source read only at deckState.ts:24 (2026-10-24)
- [x] Tested — evidence: npm test exit 0, 140 passed; feedbackOutcome describe covers every row (2026-10-24)
- [x] Best practices met — evidence: typecheck and build exit 0; pure function, no new deps (2026-10-24)
- [x] Matches locked requirements — evidence: outcome table matches answer 2; check-process-refs.sh exit 0 (2026-10-24)
- [x] No scope drift — evidence: diff touches only deckState.ts, deckState.test.ts, step-2.md; useDeck.ts untouched (2026-10-24)

### Step 3 — Feedback form logic

**Goal**: A pure, tested module that holds the answers on one feedback screen and builds
the request.

**Files in scope**: `web/src/feedback/feedbackForm.ts`,
`web/src/feedback/feedbackForm.test.ts`, `evidence/web-feedback/step-3.md`.

**Done when**: it supports setting, editing and removing one answer per `chip_id`
(strength required, text optional), setting card free text, `canSubmit(compulsory)`
(compulsory needs at least one chip answer or non-blank free text; optional always
true), building the PUT body (trimmed text, blank → `null`, chips in the order the card
sent them, no repeats, `skipped` absent), and building the skip body (`chips: []`,
`free_text: null`, `skipped: true`); tests cover each; typecheck and tests exit 0; the
process-wording check exits 0.

**Evidence location**: `evidence/web-feedback/step-3.md`.

- [x] Implemented — feedbackForm.ts: set/edit/remove, canSubmit, toRequest, skipRequest, all pure (2026-10-24)
- [x] Tested — evidence: npm test exit 0, 160 passed; feedbackForm.test.ts 20 tests cover each function (2026-10-24)
- [x] Best practices met — evidence: typecheck and build exit 0; immutable updates, reuses api types (2026-10-24)
- [x] Matches locked requirements — evidence: done-when met; check-process-refs.sh exit 0 (2026-10-24)
- [x] No scope drift — evidence: only feedbackForm.ts, its test, step-3.md plus two TRADEOFFS lines (2026-10-24)

### Step 4 — Chip dialog

**Goal**: Tapping a chip opens a dialog to give or edit that chip's answer: preset
phrases, free text and a strength.

**Files in scope**: `web/src/feedback/ChipDialog.tsx`, `web/src/feedback/feedback.css`,
`evidence/web-feedback/step-4.md`.

**Done when**: a native `<dialog>` shows the chip label, the chip's `phrases` as buttons
that fill the text field, a text field, and the four strengths as a required radio group
(labels "Must have", "Nice to have", "Would prefer not", "Deal-breaker"); Save is
disabled until a strength is chosen; Cancel closes without change; Remove clears an
existing answer; it opens pre-filled when editing; Escape closes; focus moves into the
dialog and back to the chip on close; no numeric rating; styles scoped under a feedback
root class; typecheck, tests and build exit 0; the process-wording check exits 0. Not
wired into the app yet.

**Evidence location**: `evidence/web-feedback/step-4.md`.

- [x] Implemented — ChipDialog.tsx, feedback.css, evidence/web-feedback/step-4.md present (2026-10-24)
- [x] Tested — evidence: typecheck/test (160)/build/process-refs all exit 0; no component test (no jsdom), logged as tradeoff, eye test pending (2026-10-24)
- [x] Best practices met — evidence: native dialog, aria-labelledby, labelled fields, fieldset/legend, 44px targets, focus-visible, reduced motion (2026-10-24)
- [x] Matches locked requirements — evidence: four strengths map to contract strings, phrases fill text only, no numeric rating (2026-10-24)
- [x] No scope drift — evidence: only the three in-scope files plus progress tradeoff lines; not imported anywhere, no new deps (2026-10-24)

### Step 5 — Feedback screen in the deck

**Goal**: The real feedback screen replaces the placeholder: chips, the dialog, card free
text, Done, and Skip when optional.

**Files in scope**: `web/src/feedback/FeedbackScreen.tsx`, `web/src/feedback/feedback.css`,
`web/src/deck/DeckScreen.tsx`, `web/src/deck/FeedbackStub.tsx` (deleted),
`evidence/web-feedback/step-5.md`.

**Done when**: after a swipe that opens feedback, the screen shows a short summary of the
swiped listing (price and address), the card's `chips` as sent and in order with answered
chips marked, a free-text box for the card, and Done; Skip appears only when the screen
is optional; Done is disabled when compulsory and nothing is answered; Done sends
`api.putFeedback` with the built body, Skip sends the skip body, and on success the next
card appears; a 4xx shows `error.message` and keeps the screen open; buttons are disabled
while sending; "Added to favourites" still shows after Love; no `source` shown;
`FeedbackStub.tsx` is removed; typecheck, tests and build exit 0; the process-wording
check exits 0.

**Evidence location**: `evidence/web-feedback/step-5.md`.

- [x] Implemented — evidence: FeedbackScreen.tsx added, FeedbackStub.tsx deleted, DeckScreen renders it keyed by decision_id (2026-10-24)
- [x] Tested — evidence: typecheck 0, npm test 0 (160 pass), build 0, check-process-refs 0; request builders covered by feedbackForm tests; screen wiring has no component test, logged as tradeoff, eye test at wrap-up (2026-10-24)
- [x] Best practices met — evidence: error.message shown with role=alert, answers kept, controls disabled while sending, heading focus, aria-pressed, chips limited to card.chips via toRequest (2026-10-24)
- [x] Matches locked requirements — evidence: compulsory: no Skip, Done gated by canSubmit; optional: Skip sends skipRequest(); blank to null via toRequest; source unread (2026-10-24)
- [x] No scope drift — evidence: diff limited to declared files plus progress tradeoffs; ChipDialog, useDeck, deckState, feedbackForm untouched (2026-10-24)

---

## TRADEOFFS

- Kickoff | The post-onboarding rule means left swipes on exploration cards never open feedback, so a sharp user could work out which cards are exploration after swiping. Noted and accepted by the human and the backend side for the recording. | Show the same optional screen on every swipe.
- Step 1 | The mock also returns 422 `invalid_request` for a non-boolean `skipped`. The contract does not yet say this, so it is the mock's own guess. | Match whatever the merged contract says about malformed `skipped`.
- Step 1 | Mock weights still count every non-skipped decision that offered a chip, including cards never answered; only skipped screens are left out. | The real backend's offered counting rules, once the contract states them.
- Step 2 | `feedbackOutcome` treats any action other than exploration + `left` as optional, so an unknown future action would open optional feedback rather than none. | A closed action union is already typed; revisit only if the contract adds actions.
- Step 2 | Four existing deck tests changed expectations or flow because a ranked right swipe now opens optional feedback (listed in the step evidence). Assertions kept; two now call `continue` before the next step. | None.
- Step 3 | `toRequest` trusts the card's `chips` to have unique `chip_id`s; if a card repeated one, the body would repeat it. The contract says chips are unique per card. | Dedupe by `chip_id` in `toRequest` if the backend ever sends repeats.
- Step 3 | `setAnswer` keeps raw text untrimmed in the form and trims only when building the request, so the text box can hold trailing spaces while typing. | None needed.
- Step 4 | Not browser-tested and no component test exists (node test env, no jsdom), so focus return, Escape and the `showModal()` effect are unverified until the eye test. | A jsdom or browser test setup, which needs a dependency.
- Step 4 | Focus return is done by hand in an effect (stored opener, `.focus()` after `close()`) rather than relying on the browser's own restore. If the opener is removed from the page it is silently skipped. | None needed unless the screen unmounts chips on save.
- Step 4 | Backdrop click does not close the dialog; only Cancel and Escape do. | Add a click-outside handler if wanted.
- Step 4 | Saved text is passed to `onSave` untrimmed (the form trims on build); Save is allowed with empty text. | None needed.
- Step 5 | Not browser-tested and no component test for the screen (node test env, no jsdom), so heading focus, the dialog hand-off and error display are unverified until the eye test. | A jsdom or browser test setup, which needs a dependency.
- Step 5 | The "Added to favourites" note moved from DeckScreen into the feedback screen for that phase; the card-phase note in DeckScreen is unchanged. | None.
- Step 5 | On a failed send the chips and text box are disabled only while sending, then re-enabled; the typed answers stay in screen state. A user switch or unmount mid-send drops them. | None needed.
- Step 5 | The compulsory hint shows only while nothing is answered and is linked to Done with `aria-describedby`; no other validation text. | None.

---

## SPOTTED, NOT FIXED

- `web/src/deck/deck.css` | `.deck-feedback` rules now orphaned after FeedbackStub removal (step 5) | low
- `.claude/worktrees/` | untracked and not gitignored on `main` | low
- `.claude/kit-config.md` Project type | still says "No code yet" | low
- `web/src/deck/useDeck.ts` | `swipeBusy` ref race on a rapid user switch mid-swipe (from F2) | low
- `web/src/deck/deckState.ts`, `deckState.test.ts` | `npx prettier --check` warns; not known whether pre-existing; prettier is not a configured check (step 2 implementer) | low

---

## VERIFICATION

- [ ] All step checkboxes ticked with evidence
- [ ] Every evidence path in this file exists
- [ ] Test suite run — result:
- [ ] Lint run — result:
- [ ] Typecheck run — result:
- [ ] Build run — result:
- [ ] Diff contains no files outside declared scope
- [ ] Tradeoff ledger reviewed and signed off by human
- [ ] Human eye test completed

---

## HANDOVER
