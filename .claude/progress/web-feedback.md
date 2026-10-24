# Feature: F3 Feedback screen (frontend)

- **Slug**: web-feedback
- **Owner**: Yewen
- **Started**: 2026-10-24
- **Branch**: feat/web-feedback
- **BASE_SHA**: dc0e819d63a39330b6e1c9aef38eef28f8100499
- **Status**: complete (2026-10-24) — merge blocked until the backend side adds `skipped` and the post-onboarding rule to `docs/api-contract.md` and `docs/decisions.md`

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

- 2026-10-24, human, after the first QA gate (FAIL):
  1. Done on an empty optional screen: "A, treat it as skip" — when the screen is
     optional and nothing is filled in, Done sends the skip body
     (`{"chips": [], "free_text": null, "skipped": true}`), never empty feedback.
     Redo of Step 5.
  2. "Added to favourites" shown twice after Love: "Fix now" — continuing past the
     feedback screen clears the note so it does not show above the next card. Redo of
     Step 2, reviewed before the Step 5 redo.
  3. Duplicated strength labels: "Log it" — recorded under SPOTTED, NOT FIXED.
- 2026-10-24, human, during the eye test: "I cannot verify from the 16th card because it
  ran out of properties before that. Also I don't know which ones is an exploration
  card. Can you add a little indicator like a style change or different colour?"
  Diagnosis (orchestrator, reproduced in the browser): the deck reports exhausted after
  10 cards. In development React runs effects twice; the first, discarded deck request
  still resolves after the reset, the second returns the same unswiped cards, and
  `fetchOk` marks the deck exhausted with cards still queued. The mock itself serves
  further cards correctly. Human answers:
  1. "Fix in F3" — new Step 6: ignore responses to requests made before the latest reset.
  2. "Mock mode only" — new Step 7: a small "Exploration" tag on exploration cards, shown
     only when `VITE_API_MODE=mock`, never in a real-backend run or the recording. This
     widens the `source` rule for mock mode only.

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
| `source` may be read only to decide whether the feedback screen opens and whether Skip is offered; never shown, never styled — except the Step 7 tag, in mock mode only (AMENDMENTS 2026-10-24) | `docs/decisions.md`, human answer 2026-10-24                  | code                    |
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

#### Redo of Step 2 — clear the favourites note on continue

**Goal**: The "Added to favourites" note does not carry over to the next card after the feedback screen.

**Files in scope**: `web/src/deck/deckState.ts`, `web/src/deck/deckState.test.ts`, `evidence/web-feedback/step-2-redo.md`.

**Done when**: the `continue` action clears `favourited` as well as the pending feedback; a superlike with no feedback screen (exploration is never this case today, but the reducer must not depend on that) still shows the note until the next swipe; a test covers continue clearing it; existing tests unweakened; typecheck, tests and build exit 0; the process-wording check exits 0.

**Evidence location**: `evidence/web-feedback/step-2-redo.md`.

- [x] Implemented — deckState.ts `continue` now clears favourited + pendingFeedback (2026-10-24)
- [x] Tested — evidence: new tests "clears favourited on continue after a superlike opens feedback" and "keeps favourited until the next swipe when no feedback screen opens"; typecheck, npm test (162 pass), build all exit 0 (2026-10-24)
- [x] Best practices met — evidence: one-line reducer change, no new code paths (2026-10-24)
- [x] Matches locked requirements — evidence: AMENDMENTS 2026-10-24 item 2 satisfied by reducer change; no-feedback path unchanged (2026-10-24)
- [x] No scope drift — evidence: git diff touches only deckState.ts, deckState.test.ts, evidence/web-feedback/step-2-redo.md; 1 removed line, the reducer line; check-process-refs.sh exit 0 (2026-10-24)

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

#### Redo of Step 5 — empty optional Done is a skip

**Goal**: On an optional screen with nothing filled in, Done sends the skip body.

**Files in scope**: `web/src/feedback/FeedbackScreen.tsx`, `evidence/web-feedback/step-5-redo.md`.

**Done when**: when `pending.compulsory` is false and the form has no chip answer and blank free text, Done sends `skipRequest()`; otherwise Done sends `toRequest(...)` as before; compulsory behaviour unchanged (Done disabled until an answer); the decision is made by a pure check (e.g. reuse `canSubmit(form, true)` as "has an answer") without editing `feedbackForm.ts`; typecheck, tests and build exit 0; the process-wording check exits 0.

**Evidence location**: `evidence/web-feedback/step-5-redo.md`.

- [x] Implemented — evidence: FeedbackScreen.tsx Done onClick sends skipRequest() when !compulsory && !canSubmit(form,true) (2026-10-24)
- [x] Tested — evidence: typecheck 0, npm test 0 (162 passed), build 0, check-process-refs 0; pure canSubmit/skipRequest tested in feedbackForm.test.ts (2026-10-24)
- [x] Best practices met — evidence: single-line change, error handling/sending state/onDone untouched, compulsory Done still disabled (2026-10-24)
- [x] Matches locked requirements — evidence: AMENDMENTS 2026-10-24 item 1; RULES IN FORCE skip sent as skipped: true (2026-10-24)
- [x] No scope drift — evidence: git diff is one hunk in FeedbackScreen.tsx plus new step-5-redo.md; feedbackForm.ts untouched (2026-10-24)

### Step 6 — Deck ignores stale fetch responses

**Goal**: A deck response that answers a request made before the latest reset is ignored, so the deck no longer marks itself exhausted after the first batch.

**Files in scope**: `web/src/deck/useDeck.ts`, `web/src/deck/deckState.ts`, `web/src/deck/deckState.test.ts`, `evidence/web-feedback/step-6.md`.

**Done when**: each fetch carries a request generation (or equivalent) and a response is applied only if it belongs to the current generation for the current user; a reset (mount or user change) starts a new generation; a reducer-level test reproduces the bug (a duplicate batch with only known ids arriving while cards are queued must not set `emptyReason`) and passes after the fix, without weakening the existing refetch-loop guard; in the browser in mock mode as alex the deck serves more than 10 cards (orchestrator checks by eye); diffs contain no unrelated reformatting (this machine's Prettier hook runs on Edit/Write — use shell edits if needed); typecheck, tests and build exit 0; the process-wording check exits 0.

**Evidence location**: `evidence/web-feedback/step-6.md`.

- [x] Implemented — evidence: useDeck.ts generation ref, deckState.ts fetchOk guard, evidence/web-feedback/step-6.md (2026-10-24)
- [x] Tested — evidence: typecheck 0, npm test 0 (163 passed), build 0; new test 'keeps refetching when a duplicate batch arrives...' fails on old reducer line (2026-10-24)
- [x] Best practices met — evidence: stale deck and swipe responses dropped via generation; swipeBusy untouched; no reformatting (2026-10-24)
- [x] Matches locked requirements — evidence: generation per fetch, reset/cleanup bumps it, reducer test, refetch-loop test unchanged and passing, browser check by orchestrator 20 cards (2026-10-24)
- [x] No scope drift — evidence: only the 3 web files and step-6.md changed (2026-10-24)

### Step 7 — Exploration tag in mock mode only

**Goal**: In mock mode only, exploration cards carry a small "Exploration" tag so the human can test the feedback rule.

**Files in scope**: `web/src/deck/DeckScreen.tsx`, `web/src/deck/deck.css`, `evidence/web-feedback/step-7.md`.

**Done when**: when `import.meta.env.VITE_API_MODE === "mock"` and the top card's `source` is `exploration`, a small labelled tag ("Exploration (test only)") shows next to the card; it never shows in any other mode; `PropertyCard.tsx` is not changed; the tag is not part of the drag handle and does not change swipe behaviour; diffs contain no unrelated reformatting; typecheck, tests and build exit 0; a production build check confirms the tag is behind the mode test; the process-wording check exits 0.

**Evidence location**: `evidence/web-feedback/step-7.md`.

- [x] Implemented — diff: DeckScreen.tsx +4, deck.css +9; tag gated on mock + exploration, outside SwipeableCard (2026-10-24)
- [x] Tested — typecheck 0, test 0, build 0; bundle grep: mock 1 file, http 0, plain 0; refs 0; evidence/web-feedback/step-7.md (2026-10-24)
- [x] Best practices met — scoped css, no reformatting, build-time gate tree-shaken, tradeoff logged in TRADEOFFS (2026-10-24)
- [x] Matches locked requirements — Step 7 done-when and AMENDMENTS 'Mock mode only'; orchestrator browser check: tag on cards 5,10,15,20 only (2026-10-24)
- [x] No scope drift — only DeckScreen.tsx, deck.css, step-7 evidence, progress file changed; PropertyCard/SwipeableCard untouched (2026-10-24)

---

## TRADEOFFS

- Kickoff | The post-onboarding rule means left swipes on exploration cards never open feedback, so a sharp user could work out which cards are exploration after swiping. Noted and accepted by the human and the backend side for the recording. | Show the same optional screen on every swipe. | accepted by human 2026-10-24
- Step 1 | The mock also returns 422 `invalid_request` for a non-boolean `skipped`. The contract does not yet say this, so it is the mock's own guess. | Match whatever the merged contract says about malformed `skipped`. | accepted by human 2026-10-24
- Step 1 | Mock weights still count every non-skipped decision that offered a chip, including cards never answered; only skipped screens are left out. | The real backend's offered counting rules, once the contract states them. | accepted by human 2026-10-24
- Step 2 | `feedbackOutcome` treats any action other than exploration + `left` as optional, so an unknown future action would open optional feedback rather than none. | A closed action union is already typed; revisit only if the contract adds actions. | accepted by human 2026-10-24
- Step 2 | Four existing deck tests changed expectations or flow because a ranked right swipe now opens optional feedback (listed in the step evidence). Assertions kept; two now call `continue` before the next step. | None. | accepted by human 2026-10-24
- Step 3 | `toRequest` trusts the card's `chips` to have unique `chip_id`s; if a card repeated one, the body would repeat it. The contract says chips are unique per card. | Dedupe by `chip_id` in `toRequest` if the backend ever sends repeats. | accepted by human 2026-10-24
- Step 3 | `setAnswer` keeps raw text untrimmed in the form and trims only when building the request, so the text box can hold trailing spaces while typing. | None needed. | accepted by human 2026-10-24
- Step 4 | Not browser-tested and no component test exists (node test env, no jsdom), so focus return, Escape and the `showModal()` effect are unverified until the eye test. | A jsdom or browser test setup, which needs a dependency. | accepted by human 2026-10-24
- Step 4 | Focus return is done by hand in an effect (stored opener, `.focus()` after `close()`) rather than relying on the browser's own restore. If the opener is removed from the page it is silently skipped. | None needed unless the screen unmounts chips on save. | accepted by human 2026-10-24
- Step 4 | Backdrop click does not close the dialog; only Cancel and Escape do. | Add a click-outside handler if wanted. | accepted by human 2026-10-24
- Step 4 | Saved text is passed to `onSave` untrimmed (the form trims on build); Save is allowed with empty text. | None needed. | accepted by human 2026-10-24
- Step 5 | Not browser-tested and no component test for the screen (node test env, no jsdom), so heading focus, the dialog hand-off and error display are unverified until the eye test. | A jsdom or browser test setup, which needs a dependency. | accepted by human 2026-10-24
- Step 5 | The "Added to favourites" note moved from DeckScreen into the feedback screen for that phase; the card-phase note in DeckScreen is unchanged. | None. | accepted by human 2026-10-24
- Step 5 | On a failed send the chips and text box are disabled only while sending, then re-enabled; the typed answers stay in screen state. A user switch or unmount mid-send drops them. | None needed. | accepted by human 2026-10-24
- Step 5 | The compulsory hint shows only while nothing is answered and is linked to Done with `aria-describedby`; no other validation text. | None. | accepted by human 2026-10-24
- Redo of Step 5 | No component test for the empty-Done skip branch; it relies on the tested `canSubmit` and `skipRequest`. | Needs a DOM test environment. | accepted by human 2026-10-24
- Step 6 | The exhausted rule now fires only when the queue is at or below the refetch threshold; a batch with nothing new while more cards are queued is ignored rather than ending the deck. Reported by the implementer, not written by it (omission repeated; added by reviewer). | None; a refetch only starts at or below the threshold, so no loop. | accepted by human 2026-10-24
- Step 6 | The generation guard in `useDeck` has no automated test (node test env, no hook or DOM setup); only the reducer change is unit tested. Reported by the implementer, not written by it (added by reviewer). | A jsdom or browser test setup, which needs a dependency. | accepted by human 2026-10-24
- Step 7 | The tag is gated on a build-time env value and `card.source`; there is no automated test for it (no browser check by the implementer), so only the bundle grep and the human eye test cover it. | A DeckScreen render test under mock mode, if the human wants one. | accepted by human 2026-10-24

---

## SPOTTED, NOT FIXED

- `web/src/deck/deck.css` | `.deck-feedback` rules now orphaned after FeedbackStub removal (step 5) | low
- `.claude/worktrees/` | untracked and not gitignored on `main` | low
- `.claude/kit-config.md` Project type | still says "No code yet" | low
- `web/src/deck/useDeck.ts` | `swipeBusy` ref race on a rapid user switch mid-swipe (from F2) | low
- `web/src/feedback/ChipDialog.tsx`, `FeedbackScreen.tsx` | strength labels written out in both files; human chose to log it (AMENDMENTS 2026-10-24) | low
- `web/src/deck/deckState.ts`, `deckState.test.ts` | `npx prettier --check` warns; not known whether pre-existing; prettier is not a configured check (step 2 implementer) | low

---

## VERIFICATION

Run by the QA gate on 2026-10-24 against BASE_SHA `dc0e819` and HEAD `57b27ac` (third gate).
Commands were run on a clean export of HEAD (`git archive HEAD web`), so the dev server on
:5183 was not disturbed. The working tree matched HEAD apart from the untracked
`.claude/worktrees/`.

**QA-GATE: FAIL 2026-10-24.** Everything passes except the human sign-offs and the contract
dependency. All commands are green, every locked requirement and every amendment is met, and
every file is in a declared scope. It fails on three things only: 19 TRADEOFFS entries carry no
human sign-off, the human eye test is not finished (keyboard and focus checks, post-onboarding
checks and narrow width not done), and the contract change this feature depends on (`skipped`, the post-onboarding
rule) is not on `origin/main` at `0755bcb` (backend side, merge blocker).

- [x] All step checkboxes ticked with evidence — 45 of 45 (seven steps and two redos), all dated 2026-10-24, order ok (2026-10-24)
- [x] Every evidence path in this file exists — `evidence/web-feedback/step-1.md` to `step-7.md`, `step-2-redo.md`, `step-5-redo.md` all present (2026-10-24)
- [x] Test suite run — result: `cd web && npm test` exit 0, 6 files, 163 tests passed (2026-10-24)
- [ ] Lint run — result: not configured in kit-config, not run
- [x] Typecheck run — result: `cd web && npm run typecheck` exit 0 (2026-10-24)
- [x] Build run — result: `cd web && npm run build` exit 0; the "Exploration (test only)" string is absent from the plain and `VITE_API_MODE=http` bundles and present once in the `VITE_API_MODE=mock` bundle (2026-10-24)
- [ ] Diff contains no files outside declared scope — every code and evidence file is in a step's or redo's scope; `.claude/progress/web-feedback.md` itself is in no step's scope (it is the tracking file, committed per kit-config). Left for the human to accept.
- [x] Tradeoff ledger reviewed and signed off by human — all 19 entries accepted, "accept all and continue" (2026-10-24)
- [x] Human eye test completed — PARTIAL. Human verified: compulsory screen, chip dialog (phrase, strength, Save, edit, Remove), note-only Done, favourites note not repeated, drag on a phone over Tailscale ("Drag works well on the phone", "Everything else works well"). NOT human-verified: Skip and empty Done from card 16, right swipe on an exploration card, keyboard and focus checks, 320 px width (deferred by the human). The orchestrator checked cards 16-20 (optional with Skip) and an exploration left swipe (no screen) in the built-in browser. Human chose to continue without the remaining checks (2026-10-24)

Also run: `cd web && npm ci` exit 0; `.claude/scripts/check-process-refs.sh dc0e819…` exit 0,
no hits. REQUIREMENTS (LOCKED) block identical in all nine commits that touch this file; it
could not be checked before the first commit, which created the file. `git fetch origin` then
`git show origin/main:docs/api-contract.md`: no `skipped` field on feedback; `docs/decisions.md`
line 31 still reads "optional on right swipes". No remote branch carries the change either.

---

## HANDOVER

### Where this stands

Everything passes except the human sign-offs and the contract dependency. Install, tests (163),
typecheck and build are green. The deck now serves all 20 mock cards, and exploration cards
carry a test-only tag in mock mode. What is left: sign the 19 tradeoffs, finish the eye test
below (keyboard and focus on a laptop, cards 16 to 20, and a narrow screen), and wait for the backend side to put `skipped` and
the post-onboarding rule into the contract.

### What was built

After you swipe a card, a feedback screen opens. It shows the listing's price and address, the
feature chips the card came with, and a box for a note about the whole property. Tapping a chip
opens a dialog where you pick suggested words or type your own, and choose how much it matters
(Must have, Nice to have, Would prefer not, Deal-breaker). For the first 15 cards the screen is
compulsory: no Skip, and Done stays grey until you answer one chip or write a note. After that it
is optional: Skip is offered, Done with nothing filled in counts as a skip, and a left swipe on an
exploration card goes straight to the next card. In mock mode only, exploration cards show a
small dashed "Exploration (test only)" tag so you can test that rule.

### Blocker before merge: the contract

This feature sends `"skipped": true` on `PUT /decisions/{id}/feedback` and follows the
post-onboarding rule you agreed with the backend side. Neither is written down yet. On
`origin/main` (fetched 2026-10-24, at `0755bcb`), `docs/api-contract.md` has no `skipped`
field, and `docs/decisions.md` line 31 still says feedback is "optional on right swipes". No
other remote branch has the change. The backend side owns it. Do not merge until it lands. If
it differs from what is assumed here, redo step 1 to match.

### What to check yourself

On your phone, drag and the touch parts of steps 3 to 8 passed. Still open: the keyboard and
focus parts (arrow keys in steps 3 and 8, all of step 6), which need a laptop, and steps 9 to
12.

1. In `web/`, make sure `.env` (or `.env.local`) has `VITE_API_MODE=mock` (see
   `web/.env.example`). The real backend on `main` has no deck or feedback endpoints yet, so
   mock mode is the only way to see this.
2. Run `cd web && npm run dev -- --port 5183 --strictPort` and open http://localhost:5183
   (or reuse the server already running on :5183).
3. Pick the user `alex`. Swipe the first card right (or press the right arrow key). "Tell us
   why" should open, with "You liked this: £…, address". No Skip button, Done grey, and "Pick a
   feature or write a note to continue." showing.
4. Tap a chip, for example Parking. Tap a suggested phrase: the text box fills, no strength is
   picked, Save stays grey. Pick "Nice to have" and press Save. The chip shows "Nice to have"
   and Done is enabled.
5. Tap the same chip again. It opens with "Nice to have" and your text, plus Remove. Press
   Remove. The mark goes and Done goes grey again.
6. Open the dialog and press Escape (on a laptop). It closes and focus lands back on the chip.
   Tab through the screen: every chip, the note box and Done are reachable.
7. Write a note only, press Done. The next card appears.
8. Press Love (up arrow) on a card. The screen says "You loved this" and "Added to favourites".
   Answer something and press Done. "Added to favourites" must not show above the next card.
9. Cards 5, 10, 15 and 20 should carry the dashed "Exploration (test only)" tag above the card.
   No other card should. The tag must not move when you drag the card.
10. Swipe through to card 16. From card 16 the screen shows Skip, and Done is enabled with
    nothing filled in. Press Skip: the next card appears. On the next optional screen, press
    Done with nothing filled in: it behaves exactly like Skip. Mock mode sends no network
    requests, so you cannot see the body. That it sends `skipped: true` is confirmed only by
    reading `web/src/feedback/FeedbackScreen.tsx` (the Done button) until the backend exists.
11. On card 20 (tagged), swipe right. The optional screen with Skip should open. Nobody has
    seen this case yet. The left-swipe case (no screen opens) was already checked in the
    browser, so one pass is enough. Card 20 is the only tagged card after onboarding.
12. Narrow width (you deferred this): devtools device toolbar at 320 px wide, or your phone.
    The chips wrap, the dialog fits on screen without sideways scrolling, and Save, Cancel and
    Remove are all reachable.

### Tools that will help

- Browser devtools, Network tab: in mock mode nothing shows, because the client runs in the
  browser. Once real mode works, look at the `PUT /api/decisions/<id>/feedback` body. Skip, and
  Done on an empty optional screen, must both send `{"chips":[],"free_text":null,"skipped":true}`.
  Done with answers must send chips in the card's order, trimmed text, `null` for blanks, and no
  `skipped`. The deck response shows `"source": "exploration"` for exploration cards.
- Devtools Elements panel: answered chips carry `aria-pressed="true"`; Done has
  `aria-describedby` pointing at the hint only while the compulsory screen is empty. In a
  non-mock build there should be no `deck-screen__test-tag` element anywhere.
- Devtools Accessibility pane or VoiceOver: the dialog is announced by the chip name, and the
  strengths as a group titled "How much does this matter?".
- curl, once the backend endpoint exists:
  `curl -X PUT http://localhost:8787/api/decisions/<decision_id>/feedback -H 'Content-Type: application/json' -d '{"chips":[],"free_text":null,"skipped":true}'`
  should return the body echoed with `"skipped": true` and a `profile_version`.

### What is not done

- The contract change above is not merged. Merge blocker, backend side.
- The eye test is not finished: keyboard and focus checks (arrow keys, Escape, focus return,
  Tab order; nobody has run these, the phone test could not), post-onboarding checks (steps 9
  to 11 above) and narrow width.
- None of the 19 TRADEOFFS entries is signed off:
  1. Left swipes on exploration cards never open feedback, so a sharp user could spot them.
     (The entry says you and the backend side accepted this; it carries no sign-off marker.)
  2. The mock returns its own 422 for a non-boolean `skipped`; the contract says nothing.
  3. Mock weights still count unanswered, non-skipped cards as offered.
  4. Any action other than exploration + left opens optional feedback, including unknown future
     actions.
  5. Four existing deck tests changed because ranked swipes now open feedback.
  6. `toRequest` trusts the card's chip ids to be unique.
  7. Raw text is kept untrimmed until send.
  8. The dialog has no component or browser test; focus return, Escape and `showModal()` are
     covered only by the eye test.
  9. Focus return is done by hand and is skipped if the opener has gone.
  10. Clicking the backdrop does not close the dialog.
  11. Save is allowed with empty text.
  12. The screen has no component or browser test; heading focus, dialog hand-off and error
      display are covered only by the eye test.
  13. The favourites note moved into the feedback screen for that phase.
  14. Typed answers are lost on a user switch or unmount mid-send.
  15. The compulsory hint is the only validation text.
  16. The empty-Done skip branch has no component test; it relies on the tested `canSubmit` and
      `skipRequest`.
  17. A batch with nothing new no longer ends the deck while more than the refetch threshold
      is queued; it is ignored.
  18. The stale-response guard in `useDeck` has no automated test; only the reducer change is
      tested.
  19. The exploration tag has no automated test; a bundle check and your eye test cover it.
- The error display cannot be triggered from the UI in mock mode. It is unseen until the real
  backend returns a 4xx.
- Spotted, not fixed: orphaned `.deck-feedback` rules in `web/src/deck/deck.css`;
  `.claude/worktrees/` untracked and not gitignored; kit-config "No code yet" (already fixed on
  `origin/main`); `swipeBusy` race on a fast user switch mid-swipe (from F2); strength labels
  written out twice, in `ChipDialog.tsx` and `FeedbackScreen.tsx`, so they can drift; prettier
  warnings on `deckState.ts` and its test (prettier is not a configured check, and it also warns
  on files this branch never touched).
- Also duplicated, not logged anywhere: `web/src/feedback/feedback.css` repeats the same eight
  colour variables and near-identical button rules for `.feedback-dialog` and `.feedback-screen`.
  Harmless now; a colour change has to be made twice.
- The branch is two commits behind `origin/main` (`cb7cd3b`, `0755bcb`). It merges cleanly
  (`git merge-tree` exit 0), but needs a rebase.

### What could bite you

- **The demo recording shows the tag if made in mock mode.** If F6 is recorded with
  `VITE_API_MODE=mock`, the "Exploration (test only)" tag is visible on every exploration card,
  which breaks the rule that `source` is never shown. Record against the real backend, or remove
  the tag first.
- **The `skipped` shape is a guess.** If the backend rejects the key, names it differently, or
  treats it differently, every Skip and every empty optional Done fails with an error. The user
  is then stuck on the screen until they fill something in.
- **The screen, dialog and deck hook have no automated tests.** Only the pure logic underneath is
  tested. Which button sends which body, focus handling, and the stale-response guard in
  `web/src/deck/useDeck.ts` have been checked by reading code and by eye, not by a test. A small
  refactor could break any of them and every test would stay green. The deck-ending bug you hit
  was exactly this kind of fault.
- **The error path has never been seen.** Mock mode cannot produce a 4xx from the UI, so the
  first time anyone sees an error message on this screen will be against the real backend.
