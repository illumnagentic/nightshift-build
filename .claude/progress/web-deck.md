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

_None._

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

- [ ] Implemented
- [ ] Tested — evidence: (date)
- [ ] Best practices met — evidence: (date)
- [ ] Matches locked requirements — evidence: (date)
- [ ] No scope drift — evidence: (date)

### Step 5 — Drag to swipe

**Goal**: The top card can be dragged left or right to dislike or like, using the
approved `motion` package, with the same outcome as the buttons.

**Files in scope**: `web/package.json`, `web/package-lock.json`,
`web/src/deck/DeckScreen.tsx`, `web/src/deck/SwipeableCard.tsx`, `web/src/deck/deck.css`,
`evidence/web-deck/step-5.md`.

**Done when**: only the approved package is added; dragging past a threshold left or
right swipes `left` / `right` through the same code path as the buttons; a short drag
springs back with no swipe; buttons and keys still work; the photo controls on the card
still work and do not start a drag; typecheck, tests and build exit 0.

**Evidence location**: `evidence/web-deck/step-5.md`.

- [ ] Implemented
- [ ] Tested — evidence: (date)
- [ ] Best practices met — evidence: (date)
- [ ] Matches locked requirements — evidence: (date)
- [ ] No scope drift — evidence: (date)

---

## TRADEOFFS

- Step 2 | `useDeck.ts` has no automated test (node env, no jsdom or hook renderer, both out of scope). Typecheck and build only; exercised by eye in step 4. | Proper cover needs a DOM test environment.
- Step 2 | A failed swipe (for example 404 `decision_not_found` after a prefs re-save) leaves the same card on top, so Retry repeats the failing call. No handling for discarding stale cards. | Needs the contract's re-save flow, which belongs with the prefs form (F4).
- Step 2 | When a fetch adds no new cards the deck is marked `exhausted` even if the server gave no `empty_reason`, to avoid a refetch loop. | Would need the server to say when it has nothing further.
- Step 2 | Responses for a previous user are dropped, but the in-flight request itself is not aborted (the client has no abort support). | Add `AbortSignal` to `ApiClient`.
- Step 3 | `PropertyCard` has no component test (node env, no jsdom; out of scope). Only `format.ts` is tested; the card is checked by eye. | Needs a DOM test environment.
- Step 3 | Photo position is local state, so the parent must give the card `key={card.decision_id}` or the next card keeps the previous index (it is clamped, not wrong, but not reset). | Lift the index into deck state or reset in an effect.

---

## SPOTTED, NOT FIXED

- `.claude/worktrees/` | untracked and not gitignored on `main` | low
- `.claude/kit-config.md` Project type | still says "No code yet" | low
- `web/src/deck/useDeck.ts` | an old user's swipe callback resets the shared `swipeBusy` ref even if a new user's swipe has started; only on a rapid user switch mid-swipe; a per-request token would fix it (step 2 reviewer) | low
- `web/src/deck/PropertyCard.tsx` | photo `alt` is the address on every photo, so screen readers repeat it per photo; the "n of m" live region partly offsets this (step 3 reviewer) | low

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
