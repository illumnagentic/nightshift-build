# Feature: F2 Swipe deck (frontend)

- **Slug**: web-deck
- **Owner**: Yewen
- **Started**: 2026-10-24
- **Branch**: feat/web-deck
- **BASE_SHA**: 628a2c711b4095d4f342a03dfc50b9244e6960ed
- **Status**: in progress

---

## REQUIREMENTS (LOCKED)

Human, in session, 2026-10-24: "let's do the retro before F2", then after the retro
"continue to the next step".

Binding line from `docs/plan.md` (Frontend — Yewen):

> "**F2 Swipe deck** — `feat/web-deck` — property card, swipe left / right,
> superlike."

Binding lines from `docs/decisions.md` (Core interaction):

> "1. Property card with three actions: swipe left (dislike), swipe right (like),
> superlike button."

> "4. Done closes the screen and the next card appears."

> "**Flag:** each card carries a source flag, `ranked` or `exploration`, in the API
> payload and the logs. Never shown on the card face — a user who can see a card is
> exploratory swipes differently."

Binding lines from `docs/api-contract.md`:

> "`GET /deck?n=10` Returns a batch of cards. ... The frontend refetches when it runs
> low."

> "**`source` is in the payload and the logs. It must never be shown on the card face.**"

> "When there is nothing to serve, the response is 200 with an empty `cards` list and an
> `empty_reason`. It is not an error."

> "`feedback_required` here is authoritative; the value on the card was only a hint. If
> `true`, the frontend must collect feedback before showing the next card."

> "A superlike adds the listing to favourites automatically. A right swipe does not."

> "Errors: 409 `prefs_missing` (no prefs saved), 409 `commute_pending` ... 409
> `commute_failed`"

> "`commute.minutes` is `null` if TfL had no answer."

Answers to kickoff questions, human, 2026-10-24:

1. Prefs gap: "Mock seeds prefs" — the mock gives the seeded users (alex, jordan) saved
   prefs so the deck works in mock mode. F2 shows a plain message for `prefs_missing`,
   `commute_pending` and `commute_failed`. The prefs form stays in F4.
2. Feedback: "Stub screen" — when the swipe response says `feedback_required: true`,
   show a placeholder feedback panel with a Continue button. F3 replaces it.
3. Gestures: "Gesture library" — drag to swipe using a library, as well as buttons.
   Package approved separately: "yes" to adding `motion` (14.6) to `web/`, one package.
4. Design: "Clean, deliberate card" — one focused design pass on the card; styling local
   to the deck; no CSS framework.

### Source

This session's conversation, quoted above. `docs/plan.md`, `docs/decisions.md`,
`docs/api-contract.md` on `main` at `628a2c7`.

### Explicitly out of scope

- Feedback screen, chips, phrase dialog, onboarding enforcement beyond the stub (F3).
  Chips are not rendered on the card in F2.
- Prefs form, commute polling UI, favourites screen (F4).
- Listing detail view (`GET /listings/{id}`), floorplans, photo flags, flag correction.
- Dashboard (F5), recording (F6).
- Any backend, `worker/` or `dataset/` change. Any change to `docs/api-contract.md` or
  `docs/decisions.md`.
- Showing `source` anywhere in the UI, or styling cards differently by source.
- Undo of a swipe.
- A router, state library, CSS framework, Testing Library or jsdom.
- Component tests. UI is checked by eye at wrap-up.
- Any dependency other than `motion`.
- Ticking `docs/plan.md` — done in the merging PR.

---

## AMENDMENTS

- 2026-10-24, human, after seeing the deck in the browser. Answers to four points:
  1. "arraow keys are fine: left for dislike, right for like. I would change the
     superlike to love, for display name, and use heart shape instead of texts for the
     actual user interface." Read as: arrow keys stay as built (the photo-button key
     overlap is accepted); the superlike button shows a heart instead of text, with the
     display/accessible name "Love". The API action stays `superlike`. Dislike and Like
     keep text labels unless the human says otherwise.
  2. Floor level shown as "First": "fix now".
  3. Postcode shown twice in the address: "fix now".
  4. Dark-mode contrast on the page heading: "add it to F2, use bright mode by default.
     we will do styling later on." `web/src/index.css` is added to F2's scope for this
     only.
  Points 2–3 are a redo of Step 3; points 1 and 4 a redo of Step 4. Both redos are
  reviewed in order before Step 5 is briefed.
- 2026-10-24, human: "add the amendment: Arrow keys on the photo buttons. Right now, if
  focus is on the card's Next photo button, pressing → swipes the card instead of
  changing the photo. The reviewer wants a decision for Step 5: (a) Recommended: arrow
  keys do nothing while focus is on the photo buttons. Swipe keys work everywhere else."
  Decision (a) is taken. It replaces the "arrow keys are fine" reading in point 1 above
  for the photo-button overlap only; left = dislike, right = like stay as built. Done
  in Step 5.
- 2026-10-24, human, eye test at wrap-up, check 6: "drag left and right works but there
  should be a drag up for favorite. add to amendment". Dragging the card up past a
  threshold loves it (API action `superlike`, which adds the favourite), through the
  same code path as the Love button. Done as a redo of Step 5.

---

## RULES IN FORCE

| Rule                                                                                                      | Source                                                 | Applies to              |
| --------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ | ----------------------- |
| Commits only via `.claude/scripts/safe-commit.sh`, title only, no signature, human approves               | `.claude/CLAUDE.md`                                    | commits                 |
| Commit title `type(scope): message`; scope `web`                                                          | `.claude/CLAUDE.md`, `.claude/kit-config.md`           | commits                 |
| Plain British English, short sentences, banned marketing words                                            | `.claude/CLAUDE.md`                                    | docs, comments, UI text |
| No scope creep: touch only the step's declared files                                                      | `.claude/CLAUDE.md` #1                                 | code, docs              |
| No new dependencies beyond `motion`, approved for step 5 only                                              | `.claude/CLAUDE.md` #2, kickoff answers                | code                    |
| Never weaken a test to make it pass                                                                       | `.claude/CLAUDE.md` #3                                 | tests                   |
| No speculative generalisation; walk the ladder                                                            | `.claude/CLAUDE.md` #4                                 | code                    |
| Tradeoffs written into TRADEOFFS when made; out-of-scope problems in SPOTTED                              | `.claude/CLAUDE.md` #5, #7                             | progress file           |
| Implementer never ticks its own boxes                                                                     | `.claude/CLAUDE.md` #6                                 | progress file           |
| Evidence files carry no process wording; `.claude/scripts/check-process-refs.sh` exits 0 before reporting | kit check script, F1 retro                             | evidence                |
| Use the existing `api` client and types from `web/src/api`; do not duplicate them                         | `.claude/CLAUDE.md` ladder rung 2                      | code                    |
| Card `source` is never shown and never changes styling                                                    | `docs/decisions.md`, `docs/api-contract.md` (Deck)     | code                    |
| Swipe response `feedback_required` is authoritative over the card hint                                    | `docs/api-contract.md` (Swipe)                         | code                    |
| Show `error.message` for any 4xx; no client copy of backend validation                                    | `docs/api-contract.md` (General)                       | code                    |
| Unknown values are `null`; render "unknown" or omit, never `0` or `""`                                    | `docs/api-contract.md` (General)                       | code                    |
| Frontend never calls an LLM, Mubit or TfL                                                                 | `docs/api-contract.md`, `docs/decisions.md`            | code                    |
| Accessible: every swipe action reachable by button and keyboard, not drag only                            | house practice (ladder: accessibility is not optional) | code                    |
| `docs/plan.md` changes only to tick F2, in the merging PR                                                 | `docs/decisions.md` (Overview)                         | docs                    |

---

## PLAN

All paths are relative to the repo root. Each step leaves the app working in mock mode.

### Step 1 — Mock seeds prefs for alex and jordan

**Goal**: In the mock, seeded users alex and jordan start with saved prefs and
`commute_status: "ready"`, so `GET /deck` serves cards without a prefs form.

**Files in scope**: `web/src/api/mock.ts`, `web/src/api/mock.test.ts`,
`evidence/web-deck/step-1.md`.

**Done when**: a fresh mock client returns cards from `getDeck` for alex and jordan
with no `putPrefs` call; a newly created user still gets 409 `prefs_missing`; existing
mock tests still pass unweakened (tests that relied on alex having no prefs are changed
only to use a newly created user, and each such change is listed in the evidence);
typecheck, tests and build exit 0.

**Evidence location**: `evidence/web-deck/step-1.md`.

- [x] Implemented — web/src/api/mock.ts SEED_PREFS + savedPrefs (2026-10-24)
- [x] Tested — evidence: npm test exit 0, 52 passed; new tests "gives seeded users saved prefs..." and "serves cards to seeded users..." (2026-10-24)
- [x] Best practices met — evidence: factories give per-client isolation, getPrefs structuredClone; typecheck and build exit 0 (2026-10-24)
- [x] Matches locked requirements — evidence: seeded u_01/u_02 contract-shaped, commute_status ready; new user still prefs_missing (2026-10-24)
- [x] No scope drift — evidence: git status shows only mock.ts, mock.test.ts, evidence/web-deck; check-process-refs exit 0 (2026-10-24)

### Step 2 — Deck state logic

**Goal**: A pure, tested module that holds the deck queue and decides what to show
next, plus a small React hook that drives it with the `api` client.

**Files in scope**: `web/src/deck/deckState.ts`, `web/src/deck/deckState.test.ts`,
`web/src/deck/useDeck.ts`, `evidence/web-deck/step-2.md`.

**Done when**: `deckState.ts` is pure (no React, no fetch) and covers: appending a
fetched batch without duplicating a `decision_id`; needing a refetch when 3 or fewer
cards remain; the empty state with `empty_reason`; the blocked states for
`prefs_missing`, `commute_pending`, `commute_failed`; after a swipe, moving to the next
card, or to a "feedback pending" state when the swipe response says
`feedback_required: true` (the response, not the card hint), then to the next card on
continue. `useDeck.ts` calls `api.getDeck` and `api.swipe` with the user id and feeds
results into the module; API errors surface `error.message`. Tests cover each
transition; typecheck and tests exit 0.

**Evidence location**: `evidence/web-deck/step-2.md`.

- [x] Implemented — web/src/deck/deckState.ts (pure reducer), useDeck.ts (2026-10-24)
- [x] Tested — evidence: npm test exit 0, 81 passed; 29 deckState tests cover each transition; typecheck and build exit 0 (2026-10-24)
- [x] Best practices met — evidence: stale-user guard, in-flight ref, no refetch loop on failure/exhausted; getDeck default n=10 so no-new-cards inference is sound (2026-10-24)
- [x] Matches locked requirements — evidence: only swipe response feedback_required read (deckState.ts:125); source never read; empty_reason and blocked codes handled (2026-10-24)
- [x] No scope drift — evidence: only deckState.ts, deckState.test.ts, useDeck.ts, evidence/web-deck/step-2.md plus progress file; check-process-refs exit 0 (2026-10-24)

### Step 3 — Property card

**Goal**: A presentational card for one deck card: photos, price, key facts, commute.

**Files in scope**: `web/src/deck/PropertyCard.tsx`, `web/src/deck/format.ts`,
`web/src/deck/format.test.ts`, `web/src/deck/deck.css`, `evidence/web-deck/step-3.md`.

**Done when**: the card shows the first photo with a way to step through `photos`
(buttons, keyboard reachable), price with its qualifier in words, bedrooms, bathrooms,
property type, address and postcode, EPC, tenure, floor level, up to a few
`key_features`, and commute minutes with the assumptions text, or "Commute unknown"
when `minutes` is `null`; `null` fields are omitted or shown as unknown, never as `0`
or `""`; `source` is not read; `format.ts` (price, qualifier, enum labels) is pure and
tested; styles live in `deck.css` imported by the deck components only; typecheck,
tests and build exit 0. The card is not wired into the app yet.

**Evidence location**: `evidence/web-deck/step-3.md`.

- [x] Implemented — web/src/deck/PropertyCard.tsx, format.ts, deck.css; not imported anywhere else (2026-10-24)
- [x] Tested — evidence: npm test exit 0; format.test.ts covers 4 qualifiers, 9 property types, 3 tenures, nulls, commute line; typecheck and build exit 0 (2026-10-24)
- [x] Best practices met — evidence: real buttons with aria-labels, focus-visible outline, aria-live count, reduced-motion rule, draggable=false, clamped index (2026-10-24)
- [x] Matches locked requirements — evidence: card never reads source/chips/feedback_required; nulls omitted or "Commute unknown"; features capped at 4; enum labels match contract (2026-10-24)
- [x] No scope drift — evidence: only declared files plus progress file; index.css untouched; deck.css all under .deck-card; check-process-refs exit 0 (2026-10-24)

#### Redo of Step 3 — floor and postcode wording

**Goal**: Floor level reads as a floor ("First floor"), and the postcode is not shown twice when the address already contains it or its outward code.

**Files in scope**: `web/src/deck/format.ts`, `web/src/deck/format.test.ts`, `web/src/deck/PropertyCard.tsx`, `evidence/web-deck/step-3-redo.md`.

**Done when**: a floor level without the word "floor" gets " floor" appended and the first letter capitalised ("first" → "First floor"; "second floor" → "Second floor"), with sensible handling of values that are not floors (checked against the distinct `floor_level` values in `dataset/listings.jsonl`, read only); the address line shows the full postcode once: if the address already contains the full postcode it is not appended, and if the address ends with the postcode's outward code that trailing code is replaced by the full postcode ("…, Bushey, Hertfordshire, WD23" + "WD23 2PL" → "…, Bushey, Hertfordshire, WD23 2PL"); both rules are pure functions in `format.ts` with tests; nulls still omitted; typecheck, tests and build exit 0; the process-wording check exits 0.

**Evidence location**: `evidence/web-deck/step-3-redo.md`.

- [x] Implemented — floorLevelLabel and addressLine in format.ts, used by PropertyCard.tsx (2026-10-24)
- [x] Tested — evidence: typecheck, npm test (121 passed), build all exit 0; floor table covers dataset values, addressLine tests incl. WD23 case, full-postcode, append, nulls (2026-10-24)
- [x] Best practices met — evidence: regex-escaped outward code, anchored by non-alphanumeric lead, pure functions, empty address omitted via `address &&` at PropertyCard.tsx:78 (2026-10-24)
- [x] Matches locked requirements — evidence: distinct floor_level values in evidence match dataset/listings.jsonl; unknowns omitted, never "" in DOM (2026-10-24)
- [x] No scope drift — evidence: only format.ts, format.test.ts, PropertyCard.tsx, evidence file changed; old assertions kept; process-refs exit 0 (2026-10-24)

### Step 4 — Deck screen with buttons, keys and feedback stub

**Goal**: After sign-in the user sees the deck and can dislike, like or superlike each
card by button or arrow key; a feedback placeholder appears when required.

**Files in scope**: `web/src/deck/DeckScreen.tsx`, `web/src/deck/FeedbackStub.tsx`,
`web/src/deck/deck.css`, `web/src/App.tsx`, `evidence/web-deck/step-4.md`.

**Done when**: signed in as alex in mock mode, the deck screen shows the top card;
Dislike / Like / Superlike buttons and Left / Right / Up arrow keys call
`api.swipe` with `left` / `right` / `superlike`; buttons are disabled while a swipe is
in flight; when the response has `feedback_required: true` the stub panel shows with a
Continue button and the next card appears only after Continue; superlike shows a short
"Added to favourites" note when the response has `favourited: true`; the deck refetches
when low; empty and blocked states show plain messages (`error.message` for errors);
"Switch user" still works; typecheck, tests and build exit 0.

**Evidence location**: `evidence/web-deck/step-4.md`.

- [x] Implemented — web/src/deck/DeckScreen.tsx, FeedbackStub.tsx, App.tsx wired, deck.css (2026-10-24)
- [x] Tested — evidence: typecheck, npm test (106 passed), build all exit 0; no component test, logged tradeoff (2026-10-24)
- [x] Best practices met — evidence: buttons disabled in flight, repeat/text-input guards, focus to Continue, 44px targets, reduced-motion, listener cleanup (2026-10-24)
- [x] Matches locked requirements — evidence: feedback driven by swipe response, favourites note both paths, key on decision_id, source never read, error.message shown (2026-10-24)
- [x] No scope drift — evidence: only declared files changed; useDeck/deckState/smoke.test untouched; process-refs exit 0 (2026-10-24)

#### Redo of Step 4 — Love button and light page

**Goal**: The superlike button is shown as a heart with the accessible name "Love", and the page renders light by default whatever the browser's colour scheme.

**Files in scope**: `web/src/deck/DeckScreen.tsx`, `web/src/deck/deck.css`, `web/src/index.css`, `evidence/web-deck/step-4-redo.md`.

**Done when**: the superlike button shows a heart shape (inline SVG or a heart character, no icon library, no new dependency) and no visible text; its accessible name is "Love"; it still calls `swipe("superlike")`; ArrowUp still superlikes; Dislike and Like keep their text labels; any user-facing "Superlike" wording in the deck screen reads "Love" instead (the "Added to favourites" note is unchanged); `web/src/index.css` sets `color-scheme: light` and an explicit light background and dark text on the page, so the heading and "Signed in as" line are readable in a dark-mode browser; no other styling changes; typecheck, tests and build exit 0; the process-wording check exits 0.

**Evidence location**: `evidence/web-deck/step-4-redo.md`.

- [x] Implemented — DeckScreen.tsx SVG heart, aria-label "Love", swipe("superlike") unchanged; index.css light scheme (2026-10-24)
- [x] Tested — evidence: typecheck 0, npm test 0 (smoke.test.ts unchanged), build 0, check-process-refs 0; button checked by eye only, logged in TRADEOFFS (2026-10-24)
- [x] Best practices met — evidence: svg aria-hidden + focusable=false, button keeps accessible name, disabled while busy (2026-10-24)
- [x] Matches locked requirements — evidence: heart, no text, name "Love", no remaining user-facing "Superlike" in web/src (2026-10-24)
- [x] No scope drift — evidence: diff touches only the 3 declared web files plus evidence file; no deps (2026-10-24)

### Step 5 — Drag to swipe

**Goal**: The top card can be dragged left or right to dislike or like, using the
approved `motion` package, with the same outcome as the buttons.

**Files in scope**: `web/package.json`, `web/package-lock.json`,
`web/src/deck/DeckScreen.tsx`, `web/src/deck/SwipeableCard.tsx`, `web/src/deck/deck.css`,
`evidence/web-deck/step-5.md`.

**Done when**: arrow keys are ignored while focus is on the card's photo buttons (Previous / Next photo) and still swipe everywhere else (AMENDMENTS 2026-10-24, decision (a)); only the approved package is added; dragging past a threshold left or
right swipes `left` / `right` through the same code path as the buttons; a short drag
springs back with no swipe; buttons and keys still work; the photo controls on the card
still work and do not start a drag; typecheck, tests and build exit 0.

**Evidence location**: `evidence/web-deck/step-5.md`.

- [x] Implemented — web/src/deck/SwipeableCard.tsx, DeckScreen.tsx wiring, deck.css (2026-10-24)
- [x] Tested — evidence: typecheck 0, npm test 0, build 0, check-process-refs 0; drag has no automated test, logged tradeoff, eye test at wrap-up (2026-10-24)
- [x] Best practices met — evidence: drag disabled while busy, button pointer-down guard, reduced-motion removes tilt, dragSnapToOrigin, aria-hidden cues (2026-10-24)
- [x] Matches locked requirements — evidence: onSwipe={swipe} same fn as buttons; isPhotoButton guard in keydown; source unread; only motion added (lock shows motion, framer-motion, motion-dom, motion-utils, tslib) (2026-10-24)
- [x] No scope drift — evidence: diff limited to declared files plus progress file; PropertyCard/useDeck/deckState untouched (2026-10-24)

#### Redo of Step 5 — drag up to love

**Goal**: Dragging the top card up past a threshold loves it, using the same `swipe("superlike")` call as the Love button.

**Files in scope**: `web/src/deck/SwipeableCard.tsx`, `web/src/deck/DeckScreen.tsx`, `web/src/deck/deck.css`, `evidence/web-deck/step-5-redo.md`.

**Done when**: an upward drag past a threshold (or a clear upward flick) calls the same swipe function with `superlike`; left and right drags behave as before; a downward or short drag springs back; the drag direction is decided by the dominant axis so a diagonal drag does not fire two actions; a faint "Love" cue appears while dragging up (aria-hidden), consistent with the existing Like/Dislike cues; drag still never starts from a button inside the card; reduced motion still removes rotation; vertical page scrolling on touch is considered and any loss is logged as a tradeoff; no new dependency; typecheck, tests and build exit 0; the process-wording check exits 0.

**Evidence location**: `evidence/web-deck/step-5-redo.md`.

- [x] Implemented — evidence: SwipeableCard.tsx drag on both axes, dominant-axis onDragEnd, superlike past 25% height or 600 px/s up; Love cue aria-hidden (2026-10-24)
- [x] Tested — evidence: typecheck exit 0, npm test exit 0, build exit 0, check-process-refs.sh exit 0; drag has no automated test, logged tradeoff (2026-10-24)
- [x] Best practices met — evidence: disabled-while-busy and button-drag guard kept, reduced-motion rotation kept, no new dependency, css scoped, cue aria-hidden (2026-10-24)
- [x] Matches locked requirements — evidence: AMENDMENTS 2026-10-24 drag up = superlike via same onSwipe/swipe; card.source untouched (2026-10-24)
- [x] No scope drift — evidence: diff limited to SwipeableCard.tsx, deck.css, step-5-redo.md, progress file; DeckScreen.tsx and package files unchanged (2026-10-24)

---

## TRADEOFFS

- Step 2 | `useDeck.ts` has no automated test (node env, no jsdom or hook renderer, both out of scope). Typecheck and build only; exercised by eye in step 4. | Proper cover needs a DOM test environment.
- Step 2 | A failed swipe (for example 404 `decision_not_found` after a prefs re-save) leaves the same card on top, so Retry repeats the failing call. No handling for discarding stale cards. | Needs the contract's re-save flow, which belongs with the prefs form (F4).
- Step 2 | When a fetch adds no new cards the deck is marked `exhausted` even if the server gave no `empty_reason`, to avoid a refetch loop. | Would need the server to say when it has nothing further.
- Step 2 | Responses for a previous user are dropped, but the in-flight request itself is not aborted (the client has no abort support). | Add `AbortSignal` to `ApiClient`.
- Step 3 | `PropertyCard` has no component test (node env, no jsdom; out of scope). Only `format.ts` is tested; the card is checked by eye. | Needs a DOM test environment.
- Step 3 | Photo position is local state, so the parent must give the card `key={card.decision_id}` or the next card keeps the previous index (it is clamped, not wrong, but not reset). | Lift the index into deck state or reset in an effect.
- Step 4 | `DeckScreen` and `FeedbackStub` have no component test (node env, no jsdom; out of scope). Checked by eye. | Needs a DOM test environment.
- Step 4 | `commute_pending` Retry refetches once per click; there is no polling. | Polling belongs with the prefs/commute UI (F4).
- Step 4 | Arrow keys are listened for on `window`, so they also fire when focus is on a button such as Switch user or a photo arrow. Only text inputs are exempt, as briefed. | Scope the listener to the deck root, which needs focus management.
- Step 3 redo | `addressLine` treats the postcode as present if its whitespace-stripped form appears anywhere in the stripped address, so it could in theory match inside a longer run of characters. | Needs a word-boundary check on the stripped form; unlikely in real addresses.
- Step 3 redo | `floorLevelLabel` only appends " floor" to ordinals ("22nd floor"); it does not reword them ("22nd" stays an ordinal). | Fine for every value in the dataset.
- Step 4 redo | The Love button is an inline SVG heart with `aria-label` and `title`; it is checked by eye only (no DOM test environment, out of scope). | Needs a DOM test environment.
- Step 4 redo | The light page is fixed: `color-scheme: light` with a white background and dark text, so there is no dark mode. Other deck colours were already fixed. | Add a dark theme when styling is done.

---
- Step 5 | Drag has no automated test (node env, no jsdom; out of scope). Drag, spring-back and photo-button behaviour are checked by eye only. | Needs a DOM test environment.
- Step 5 | The card always springs back to centre on release, including when it triggers a swipe; there is no fly-off animation. The next card replaces it once the swipe response arrives. | Animate the card off screen, which needs exit handling around the deck key.
- Step 5 | Distance threshold is 30% of card width or 600 px/s release velocity; both are untuned guesses. | Tune by hand on a real touch device.
- Step 5 | Arrow keys are ignored only when the event target is a button inside `.deck-card`. Focus on other buttons (Switch user, action buttons) still lets arrows swipe. | Scope the listener to the deck root, with focus management.
- Step 5 | Reduced motion removes only the rotation; the drag offset and the Like / Dislike cue fade remain, since the drag itself must still work. | Hide the cue when reduced, if wanted.

## SPOTTED, NOT FIXED

- `.claude/worktrees/` | untracked and not gitignored on `main` | low
- `.claude/kit-config.md` Project type | still says "No code yet" | low
- `web/src/deck/useDeck.ts` | an old user's swipe callback resets the shared `swipeBusy` ref even if a new user's swipe has started; only on a rapid user switch mid-swipe; a per-request token would fix it (step 2 reviewer) | low
- `web/src/deck/PropertyCard.tsx` | photo `alt` is the address on every photo, so screen readers repeat it per photo; the "n of m" live region partly offsets this (step 3 reviewer) | low

---

## VERIFICATION

- [x] All step checkboxes ticked with evidence (35 of 35 across Steps 1-5 and both redos, 2026-10-24)
- [x] Every evidence path in this file exists (`evidence/web-deck/` holds step-1, step-2, step-3, step-3-redo, step-4, step-4-redo, step-5)
- [x] Test suite run — result: `cd web && npm test` exit 0, 5 files, 121 passed (2026-10-24)
- [x] Lint run — result: not configured in `.claude/kit-config.md`, not run
- [x] Typecheck run — result: `cd web && npm run typecheck` exit 0 (2026-10-24)
- [x] Build run — result: `cd web && npm run build` exit 0, 449 modules, JS 416.02 kB (2026-10-24)
- [x] Diff contains no files outside declared scope (checked file by file against steps and redos; `check-process-refs.sh` exit 0)
- [ ] Tradeoff ledger reviewed and signed off by human (18 entries, none signed)
- [ ] Human eye test completed

---

## HANDOVER

**What was built.** After signing in as alex or jordan in mock mode, you now see a deck of property cards. Each card shows photos you can step through, price, key facts, EPC, tenure, floor and commute time. You can Dislike, Love (heart) or Like a card by button, by arrow key, or by dragging the card left or right. When the swipe response says feedback is needed, a placeholder panel with a Continue button appears before the next card. Empty and blocked states show plain messages.

**What to check yourself.**

1. In `web/`, run `npm run dev` (serves http://localhost:5173). If the orchestrator's server is still on :5173, use that one.
2. Pick alex. A card should appear with no prefs form. The page should be light even if your system is in dark mode.
3. Read the card. Floor should read like "First floor". The postcode should appear once in the address. No source or "exploration" label should appear anywhere.
4. Click Next photo: the photo changes ("2 of 4"). With focus still on it, press the right arrow key: nothing happens, no swipe and no photo change (AMENDMENTS decision (a); corrected by the orchestrator, the gate's first wording said the photo would change).
5. Click on the page body, then press Left arrow. The card should be disliked and the next one appear. Press Up arrow: a "Added to favourites" note should appear.
6. Click Like. If the stub panel appears, press Continue and check the next card appears only then.
7. Drag a card slowly about 40 px right and release. It should spring back with no swipe. This was not tested. The browser tool drags instantly, so the speed rule fired on a short drag.
8. Drag slowly past about a third of the card width. It should swipe. Do the same left.
9. Press the mouse down on Next photo and drag. Nothing should move.
10. On a touch device or touch emulation, repeat steps 7 to 9. The thresholds are untuned.
11. Create a new user. You should see the `prefs_missing` message, not a crash.
12. Switch user. The deck should reset for the new user.

**Tools that will help.** Browser devtools network tab: each swipe should be one `POST` to the swipe route with `action` of `left`, `right` or `superlike`, and the deck should refetch with `GET /deck` when 3 or fewer cards remain. Device emulation in devtools for touch drags. In mock mode no network calls leave the page, so use the console and React behaviour only. Against the real backend, check the logs for the `source` flag, not the UI.

**What is not done.**

All 18 ledger entries are unsigned:
- Step 2 (4): `useDeck` has no test; a failed swipe leaves the same card and Retry repeats it; an empty fetch with no `empty_reason` is treated as exhausted; stale-user responses are dropped but requests are not aborted.
- Step 3 (2): `PropertyCard` has no component test; photo index relies on the parent setting `key`.
- Step 4 (3): `DeckScreen` and `FeedbackStub` have no component test; `commute_pending` Retry is one refetch per click, no polling; arrow keys listen on `window`.
- Step 3 redo (2): `addressLine` could match the postcode inside a longer character run; `floorLevelLabel` appends "floor" to ordinals only.
- Step 4 redo (2): heart button checked by eye only; the page is light only, no dark mode.
- Step 5 (5): drag has no automated test; the card springs back instead of flying off; thresholds (30% width, 600 px/s) are guesses; arrows still swipe when focus is on buttons outside the card; reduced motion removes rotation only.

Other limits: the feedback panel is a stub (F3). No prefs form, no favourites screen (F4). No undo. `motion` pulled in four more packages (`framer-motion`, `motion-dom`, `motion-utils`, `tslib`). The tradeoff ledger has a stray `---` rule in the middle, splitting the Step 5 entries from the rest.

SPOTTED, NOT FIXED: `.claude/worktrees/` is untracked and not gitignored; `kit-config.md` Project type still says "No code yet"; `useDeck` swipe callback can reset the shared busy flag on a rapid user switch; every photo `alt` is the address.

Not ticked: `docs/plan.md` (done in the merging PR).

**What could bite you.**

1. Drag release speed. A 600 px/s velocity alone triggers a swipe, with no distance needed. A quick flick or a jittery trackpad could swipe by accident, and there is no undo.
2. The card does not fly off. It springs to centre while the request is in flight, then the next card replaces it. On a slow backend this looks like a failed swipe, and the user may swipe again. Buttons are disabled while busy, but a second drag is also blocked, so it only looks wrong, not double-counted.
3. Arrow keys listen on the whole window. Focus on Switch user or Retry plus an arrow key still swipes. A keyboard user tabbing around can swipe by accident.

The feature is not complete until the human has done the eye test and signed the tradeoff ledger.
- Step 5 redo | `touch-action: none` on the card, so a touch that starts on the card no longer scrolls the page; the page scrolls only from outside the card. Vertical drag needs this. | Scroll from the card would need a drag-direction lock before claiming the gesture.
- Step 5 redo | Up threshold is 25% of card height or 600 px/s upward, untuned; direction is the dominant axis at release (ties go horizontal). Drag up has no automated test (node env, no jsdom). Checked by eye only. | Tune on a real touch device; needs a DOM test environment.
- Step 5 redo | The Love cue follows upward y alone, so a diagonal drag can show the Love cue with Like or Dislike while only the dominant axis fires. | Fade each cue by its dominance over the other axis.
