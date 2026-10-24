# Feature: F4 Prefs and favourites (frontend)

- **Slug**: web-prefs-favourites
- **Owner**: Yewen
- **Started**: 2026-10-24
- **Branch**: feat/web-prefs-favourites (stacked on feat/web-feedback, PR #13)
- **BASE_SHA**: 914735a (rebased onto `main` after F3's squash merge; kickoff base was a4d0c48e8fbee1a74b7bc4bed97cd5cad77fcf32 — see AMENDMENTS 2026-10-25)
- **Status**: in progress

---

## REQUIREMENTS (LOCKED)

Human, in session, 2026-10-24: "Go ahead" (to kicking off F4 after the F3 retro).

Binding line from `docs/plan.md` (Frontend — Yewen):

> "**F4 Prefs and favourites** — `feat/web-prefs-favourites` — prefs input with
> workplace postcode, favourites with remove-with-reason."

Binding lines from `docs/decisions.md` (Commute):

> "The user enters one location (workplace or anywhere else)."

> "**Input:** postcode. Free-text place names make TfL return candidate matches
> instead of a journey."

> "**Max commute:** if the user states a limit, it is a hard filter enforced in code.
> Otherwise commute is a factor the curator weighs."

Binding lines from `docs/api-contract.md`:

> "`PUT /prefs` Replaces the stored prefs. Returns at once; the backend then calculates
> the TfL commute for every listing that passes the other hard filters. Poll
> `GET /prefs` until `commute_status` is `ready`."

> "On `failed` the frontend shows an error and lets the user re-save prefs."

> "Re-saving prefs mid-session discards every served card that has not been swiped.
> ... The frontend should discard its local deck and fetch a new one once
> `commute_status` is `ready`."

> "`commute_postcode` is required and is a postcode only. `max_commute_min` is
> optional."

> "`text` is required and must be non-empty."

> "`DELETE /favourites/{listing_id}` The request carries a JSON body. A reason is
> required. The reason is treated as free-text feedback and feeds the taste profile."

> "The frontend shows `error.message` for any 4xx and does not replicate these checks."

Delegation, human, 2026-10-24: "For F4, use advisor to make decision automatically instead
of asking me for approval. I'll come back at the end". Read as: the orchestrator locks
the plan, settles decisions (with the advisor) and approves step commits on the human's
behalf for this feature. Left for the human at the end: tradeoff sign-off, the eye
test, and any push or PR.

Answers to kickoff questions, human, 2026-10-24:

1. Branch base: "Stack on F3" — branch from `feat/web-feedback`; the PR waits for F3.
2. Navigation: "Simple tabs" — three buttons in the header switching a state value in
   App. No router.
3. Prefs entry: "Auto + tab" — a user with 409 `prefs_missing` is taken to the form
   automatically; anyone can open it from the Preferences tab to edit and re-save.
4. Real API: "Not in F4" — F4 stays on the mock.

### Source

This session's conversation, quoted above. `docs/plan.md`, `docs/decisions.md`,
`docs/api-contract.md` on `main` at `0755bcb` (unchanged on `feat/web-feedback`).

### Merge note

F3 will be squash-merged, so its commits will not exist on `main`. When F3 is merged,
rebase with `git rebase --onto main a4d0c48 feat/web-prefs-favourites` (not a plain
`git rebase main`), and record the new base as an amendment, because the stamped
BASE_SHA will stop being an ancestor.

### Explicitly out of scope

- Connecting to the real Worker backend, for users or anything else.
- A router, state library, CSS framework, Testing Library, jsdom or component tests.
- Any new dependency.
- Showing the parsed prefs as editable structured fields (the form edits the text,
  postcode and limit only; the parsed result is shown read-only).
- Listing detail view, flag corrections, the profile view.
- Dashboard (F5), recording (F6).
- Any backend, `worker/` or `dataset/` change; any edit to the contract or decisions.
- The queued `web/src` formatting commit (after F3 merges).
- Ticking `docs/plan.md` — done in the merging PR.

---

## AMENDMENTS

- 2026-10-25, orchestrator with the advisor, under the human's F4 delegation, after the
  first QA gate (FAIL): the contract line "discard its local deck and fetch a new one once
  `commute_status` is `ready`" was only met while the user stayed on Preferences. Leaving
  the tab mid-calculation left the deck stuck (new user) or stale (re-save → 404 on swipe).
  Decision: (1) PrefsScreen stays mounted for a signed-in user, hidden when another tab is
  open, keyed by user, so polling continues; (2) PrefsScreen gains `onSaved()`, called
  once per successful PUT; (3) App discards the local deck on `onSaved` (deckKey bump) and
  again on `onReady`, and `onReady` changes tab only when the user is on Preferences;
  (4) DeckScreen's `commute_failed` block gets a "Set preferences" button. This replaces
  Step 4's "PrefsScreen and FavouritesScreen rendered only when their tab is active" for
  PrefsScreen only. Done as a redo of Step 2, then a redo of Step 4.
- 2026-10-25, orchestrator, per the Merge note: F3 (PR #13) was squash-merged as 914735a.
  The branch was rebased with `git rebase --onto origin/main a4d0c48
  feat/web-prefs-favourites`, with no conflicts. F4's web and evidence files are
  unchanged by the rebase (the only new files are backend evidence from `main`).
  typecheck, 178 tests and build exit 0 after the rebase. New base: 914735a.

---

## RULES IN FORCE

| Rule                                                                                                                                                                | Source                                       | Applies to              |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- | ----------------------- |
| Commits only via `.claude/scripts/safe-commit.sh`, title only, no signature, human approves                                                                         | `.claude/CLAUDE.md`                          | commits                 |
| Commit title `type(scope): message`; scope `web` (progress-only commits `kit`)                                                                                      | `.claude/CLAUDE.md`, `.claude/kit-config.md` | commits                 |
| Plain British English, short sentences, banned marketing words                                                                                                      | `.claude/CLAUDE.md`                          | docs, comments, UI text |
| No scope creep: touch only the step's declared files                                                                                                                | `.claude/CLAUDE.md` #1                       | code, docs              |
| No new dependencies                                                                                                                                                 | `.claude/CLAUDE.md` #2                       | code                    |
| Never weaken a test to make it pass                                                                                                                                 | `.claude/CLAUDE.md` #3                       | tests                   |
| No speculative generalisation; walk the ladder                                                                                                                      | `.claude/CLAUDE.md` #4                       | code                    |
| Every tradeoff inserted as the last entry of TRADEOFFS (above `## SPOTTED, NOT FIXED`) when made, and the report says so                                            | `.claude/CLAUDE.md` #5; F3 retro             | progress file           |
| Implementer never ticks its own boxes                                                                                                                               | `.claude/CLAUDE.md` #6                       | progress file           |
| Evidence has no process wording; the process-wording check runs last and exits 0                                                                                    | kit check script                             | evidence                |
| This laptop runs Prettier on every Edit/Write: check `git diff` and keep only intended hunks; use shell edits if needed                                             | F3 retro (kit-config brief note, PR #14)     | code                    |
| Use the existing `api` client, types, deck and feedback components and `format.ts`; do not duplicate them                                                           | `.claude/CLAUDE.md` ladder rung 2            | code                    |
| `commute_postcode` required; `max_commute_min` optional; `text` required and non-empty — but no client copy of backend formats (postcode format is the backend's)   | `docs/api-contract.md` (Preferences)         | code                    |
| After saving prefs, poll `GET /prefs` until `ready` or `failed`; on `ready` discard the local deck and fetch a new one; on `failed` show an error and allow re-save | `docs/api-contract.md` (Preferences)         | code                    |
| Favourite removal always sends a reason; show `error.message` for 4xx                                                                                               | `docs/api-contract.md` (Favourites, General) | code                    |
| `source` is never shown except the existing mock-only test tag                                                                                                      | `docs/decisions.md`; F3 amendment            | code                    |
| Done-when checks for lists go past the first batch; rules a step depends on are restated                                                                            | F3 retro                                     | plan                    |
| Human eye test is in VERIFICATION, not in step done-whens                                                                                                           | F1 and F3 retros                             | plan                    |
| `docs/plan.md` changes only to tick F4, in the merging PR                                                                                                           | `docs/decisions.md` (Overview)               | docs                    |

---

## PLAN

All paths are relative to the repo root. Each step leaves the app working in mock mode.

### Step 1 — Prefs form logic

**Goal**: A pure, tested module that holds the prefs form and builds the `PUT /prefs`
request.

**Files in scope**: `web/src/prefs/prefsForm.ts`, `web/src/prefs/prefsForm.test.ts`,
`evidence/web-prefs-favourites/step-1.md`.

**Done when**: it builds a form from a `PrefsResponse` (all-null prefs give empty
fields); `canSave` is true only when trimmed text and trimmed postcode are non-empty
(presence only, no format check); the request trims text and postcode, sends
`max_commute_min` as a whole number when given and omits it when blank, and never sends
`""`; a limit entry that does not parse as a whole number is reported by a pure check so the UI can say so and block Save (only the parse needed to put a number in the JSON; zero, negative or out-of-range values are left to the backend's 422); tests cover each;
typecheck and tests exit 0; the process-wording check exits 0.

**Evidence location**: `evidence/web-prefs-favourites/step-1.md`.

- [x] Implemented — web/src/prefs/prefsForm.ts exports formFromPrefs, limitError, canSave, toRequest (2026-10-24)
- [x] Tested — evidence: prefsForm.test.ts 15 tests; typecheck, npm test, build exit 0 (2026-10-24)
- [x] Best practices met — evidence: pure functions, no postcode/range check, no "" sent, no new deps (2026-10-24)
- [x] Matches locked requirements — evidence: presence-only canSave, blank limit omitted, non-integer blocks Save (2026-10-24)
- [x] No scope drift — evidence: only prefs/, evidence/step-1.md new; no tracked file modified (git status) (2026-10-24)

### Step 2 — Prefs screen

**Goal**: The Preferences screen loads, edits and saves prefs, then waits for commute
times.

**Files in scope**: `web/src/prefs/PrefsScreen.tsx`, `web/src/prefs/prefs.css`,
`evidence/web-prefs-favourites/step-2.md`.

**Done when**: props `{ userId, onReady() }`; it loads `api.getPrefs` and pre-fills the
form; labelled fields for preferences text (textarea), workplace postcode and an optional
"Maximum commute (minutes)"; Save calls `api.putPrefs` (disabled until `canSave`, and
while saving); after save it shows the parsed result read-only (hard limits that are not
`null`, and the soft list) and "Working out commute times…", polls `api.getPrefs` about
every 1.5 seconds until `commute_status` is `ready` (then calls `onReady()`) or `failed`
(then shows "Commute times could not be worked out. Check the postcode and save again.");
polling stops on unmount; a 4xx shows `error.message`; a user who already has prefs and opens the screen sees their saved values; if `commute_status` is `pending` on open it starts polling at once, and if it is `failed` it shows the failed message at once; styles scoped
under a prefs root class; typecheck, tests and build exit 0; the process-wording check
exits 0. Not wired into the app yet.

**Evidence location**: `evidence/web-prefs-favourites/step-2.md`.

- [x] Implemented — PrefsScreen.tsx, prefs.css; save() guarded by pollId generation against unmount/userId races (2026-10-24)
- [x] Tested — evidence: typecheck, npm test (178), build, process-refs all exit 0, re-run by reviewer; no component test env per scope (2026-10-24)
- [x] Best practices met — evidence: stale responses ignored, timers cleared on unmount, Save disabled while saving, 4xx shows error.message (2026-10-24)
- [x] Matches locked requirements — evidence: 1500 ms poll, pending/failed on open handled, onReady once, no postcode check, no source (2026-10-24)
- [x] No scope drift — evidence: only prefs/PrefsScreen.tsx, prefs.css, evidence/step-2.md new; progress file edits only (2026-10-24)

#### Redo of Step 2 — onSaved callback

**Goal**: PrefsScreen tells its parent each time a save succeeds.

**Files in scope**: `web/src/prefs/PrefsScreen.tsx`, `evidence/web-prefs-favourites/step-2-redo.md`.

**Done when**: PrefsScreen takes a required `onSaved: () => void` prop, called exactly once per successful `putPrefs`, after the generation guard passes and before `applyStatus`; polling, the unmount guard and all other behaviour unchanged; shell edit, diff contains only intended hunks; typecheck, tests and build exit 0 (App may need a temporary no-op `onSaved` only if typecheck requires it — if so, declare and limit it to that one prop); the process-wording check exits 0.

**Evidence location**: `evidence/web-prefs-favourites/step-2-redo.md`.

- [x] Implemented — PrefsScreen.tsx save(): onSaved() after generation guard, before applyStatus; required prop (2026-10-25)
- [x] Tested — npm run typecheck 0, npm test 0 (178 passed), npm run build 0; no component-test harness in repo, call order verified by code read (2026-10-25)
- [x] Best practices met — check-process-refs.sh exit 0; guard and error paths untouched (2026-10-25)
- [x] Matches locked requirements — matches AMENDMENTS 2026-10-25 item (2): once per successful PUT (2026-10-25)
- [x] No scope drift — diff is the prop, one call, and App onSaved={() => {}} only; evidence/web-prefs-favourites/step-2-redo.md present (2026-10-25)

### Step 3 — Favourites screen

**Goal**: The Favourites screen lists favourites and removes one with a reason.

**Files in scope**: `web/src/favourites/FavouritesScreen.tsx`,
`web/src/favourites/favourites.css`, `evidence/web-prefs-favourites/step-3.md`.

**Done when**: props `{ userId }`; it loads `api.getFavourites` and lists every
favourite (no paging; all entries shown) with the first photo as a thumbnail (a neutral placeholder when `photos` is empty; other null fields omitted, never shown as `0` or `""`), price with
qualifier and address line from `format.ts`, and the date added; an empty list shows
"No favourites yet. Love a property to save it here."; each entry has a Remove button
that opens a native `<dialog>` asking "Why are you removing it?" with a required text
box; Confirm is disabled while the box is blank and while sending; Confirm calls
`api.removeFavourite(userId, listing.id, { reason })` and removes the entry on success;
a 4xx shows `error.message` in the dialog and keeps it open; Escape and Cancel close it
and return focus to the Remove button; styles scoped under a favourites root class;
typecheck, tests and build exit 0; the process-wording check exits 0. Not wired into
the app yet.

**Evidence location**: `evidence/web-prefs-favourites/step-3.md`.

- [x] Implemented — FavouritesScreen.tsx, favourites.css; sending lifted to screen, Cancel disabled and Escape blocked while sending (2026-10-24)
- [x] Tested — evidence: reviewer re-run typecheck, npm test (178 passed), build, process-refs all exit 0; no component test env per scope (2026-10-24)
- [x] Best practices met — evidence: sending cleared on success, error and userId change; late responses ignored; no new deps (2026-10-24)
- [x] Matches locked requirements — evidence: DELETE via removeFavourite with trimmed reason, error.message shown, placeholder for empty photos, exact empty text (2026-10-24)
- [x] No scope drift — evidence: only favourites/ files, evidence/step-3.md, progress file (2026-10-24)

### Step 4 — Tabs and wiring

**Goal**: Signed-in users switch between Deck, Preferences and Favourites; a user with no
prefs is taken to Preferences; saving prefs gives a fresh deck.

**Files in scope**: `web/src/App.tsx`, `web/src/deck/DeckScreen.tsx`, `web/src/nav.css`,
`evidence/web-prefs-favourites/step-4.md`.

**Done when**: the signed-in header shows three tab buttons (Deck, Preferences,
Favourites) with the current one marked (`aria-current` or `aria-pressed`), plus the
existing "Signed in as" and Switch user; DeckScreen gains a callback prop that it calls
when the deck is blocked with `prefs_missing`, and App then switches to Preferences
(auto entry); the `prefs_missing` message in DeckScreen also offers a button to open
Preferences; DeckScreen stays mounted while another tab is shown (hidden, not unmounted), so a pending compulsory feedback screen cannot be escaped by switching tabs; it gains an `active` prop and its arrow-key listener runs only while `active` is true; when PrefsScreen calls `onReady()`, App remounts DeckScreen with a new key (discarding the local deck and any pending feedback, logged as a tradeoff) and switches to Deck; Favourites reloads its list each time
the tab opens; switching user returns to Deck; no other DeckScreen behaviour changes;
diffs contain no unrelated reformatting; typecheck, tests and build exit 0; the
process-wording check exits 0.

**Evidence location**: `evidence/web-prefs-favourites/step-4.md`.

- [x] Implemented — App.tsx tabs with aria-current, hidden DeckScreen wrapper keyed user:deckKey, active-gated keydown, onNeedPrefs + Set preferences button, nav.css (2026-10-24)
- [x] Tested — evidence: reviewer re-run typecheck, npm test, build, check-process-refs all exit 0; smoke.test.ts unchanged; no component test env per scope (2026-10-24)
- [x] Best practices met — evidence: onNeedPrefs omitted from deps is safe (App's callback only calls stable setTab); no CSS overrides hidden wrapper; no new deps (2026-10-24)
- [x] Matches locked requirements — evidence: onReady bumps deckKey and sets Deck tab; switchUser resets tab; Prefs/Favourites mount only when active; no source shown (2026-10-24)
- [x] No scope drift — evidence: only App.tsx, DeckScreen.tsx, nav.css, evidence/step-4.md plus progress file; minimal hunks (2026-10-24)

#### Redo of Step 4 — deck refresh wherever the user is

**Goal**: The local deck is discarded at save and refreshed on ready whichever tab is open; the tab changes only from Preferences.

**Files in scope**: `web/src/App.tsx`, `web/src/deck/DeckScreen.tsx`, `evidence/web-prefs-favourites/step-4-redo.md`.

**Done when**: PrefsScreen is rendered for a signed-in user at all times, hidden when its tab is not active, keyed by `user_id` (FavouritesScreen still renders only on its tab); App's `onSaved` bumps `deckKey`; App's `onReady` bumps `deckKey` and calls `setTab(t => t === "prefs" ? "deck" : t)`; DeckScreen's `commute_failed` block shows a "Set preferences" button calling `onNeedPrefs`; restated rule: the local deck is discarded at save, refreshed on ready wherever the user is, and the tab changes only from Preferences; browser reproductions by the orchestrator, before and after — Path A (new user, save, open Deck at once: "still being worked out", then cards appear with no action), Path B (alex with a loaded deck saves `FAIL 1AA`, opens Deck: no stale card, no 404; then saves `EC2N 2DB`: a fresh deck appears), ready while on Favourites leaves the user on Favourites; shell edits, diffs contain only intended hunks; typecheck, tests and build exit 0; the process-wording check exits 0.

**Evidence location**: `evidence/web-prefs-favourites/step-4-redo.md`.

- [x] Implemented — App.tsx hidden-wrapper PrefsScreen keyed by user_id, onSaved/onReady as specified; DeckScreen commute_failed button (2026-10-25)
- [x] Tested — typecheck 0, npm test 0, build 0 re-run by reviewer; before/after browser reproductions in evidence/web-prefs-favourites/step-4-redo.md for Path A, Path B, ready-on-Favourites (2026-10-25)
- [x] Best practices met — check-process-refs.sh exit 0; hidden-prefs polling stops on unmount/key change/save; no spurious bump on ready-at-mount; tradeoffs logged (2026-10-25)
- [x] Matches locked requirements — matches AMENDMENTS 2026-10-25 items (1),(3),(4); FavouritesScreen still tab-only (2026-10-25)
- [x] No scope drift — only App.tsx (4+/3-), DeckScreen.tsx (2+/1-), evidence file; smoke.test.ts unchanged (2026-10-25)

---

## TRADEOFFS

- Step 1 | The client accepts zero and negative whole numbers as a commute limit and rejects an explicit plus sign ("+5") | the backend owns range checks (422); the form only parses what it can put in the JSON | add a range check or accept "+" if the backend contract defines one | accepted by human 2026-10-25
- Step 2 | Polling has no time limit and keeps retrying after any error, including a 4xx, while the status is pending | the contract defines no timeout and a transient failure should not strand the user; leaving the screen or saving again stops it | add a cap with a visible 'taking too long' message once the backend gives an expected time | accepted by human 2026-10-25
- Step 2 | The parsed result is shown only when it has at least one hard limit or soft preference, and a failed load shows the error with empty fields | nothing useful to show otherwise | none needed unless the eye test finds it confusing | accepted by human 2026-10-25
- Step 3 | After a successful removal focus is not moved anywhere (the Remove button is gone) | no next target was specified | move focus to the next entry's Remove button or the screen heading | accepted by human 2026-10-25
- Step 3 | The thumbnail shows only the first photo, with no handling for an image that fails to load | brief asks for the first photo only | add an onError fallback to the placeholder | accepted by human 2026-10-25
- Step 4 | Saving preferences discards the deck at save time (onSaved remounts it), and again when `onReady` fires (including from polling on the hidden Preferences screen), so a feedback screen left pending (including compulsory onboarding feedback) is dropped and that card's feedback is lost | the contract says to discard the local deck after a re-save, and a remount is the simplest way to do it | persist pending feedback in App or the API, or only remount once no feedback is pending | accepted by human 2026-10-25
- Step 4 | The deck is kept mounted while hidden, so a prefs_missing redirect and its Set preferences button fire from a hidden screen, and the onNeedPrefs effect ignores callback changes | needed to keep the local deck and pending feedback across tab switches | none needed unless the hidden deck causes trouble | accepted by human 2026-10-25
- Redo of Step 4 | On a failed commute the deck shows its blocked state and needs Retry or a re-save; no onFailed callback | kept minimal | add onFailed to refresh the deck on failure | accepted by human 2026-10-25

---

## SPOTTED, NOT FIXED

- `.claude/worktrees/` | untracked and not gitignored | low
- `web/src/deck/useDeck.ts` | `swipeBusy` ref race on a rapid user switch mid-swipe (from F2) | low
- `web/src/feedback/ChipDialog.tsx`, `FeedbackScreen.tsx` | strength labels written out in both files (from F3, logged by the human's choice) | low
- `web/src/deck/deck.css` | orphaned `.deck-feedback` rules after the stub was deleted (from F3) | low
- `web/src/prefs/PrefsScreen.tsx` | form, parsed and status are not reset on a userId change; needs `key={userId}` or a reset when wired | low — resolved: PrefsScreen is now keyed by user_id (Redo of Step 4)

---

## VERIFICATION

- [x] All step checkboxes ticked with evidence — 30 of 30 (Steps 1 to 4 and the redos of Steps 2 and 4). Steps 1 to 4 dated 2026-10-24; both redos dated 2026-10-25, done after Step 4 as the redo rule in `.claude/CLAUDE.md` (Step order) allows (2026-10-25)
- [x] Every evidence path in this file exists — evidence/web-prefs-favourites/step-1.md, step-2.md, step-2-redo.md, step-3.md, step-4.md, step-4-redo.md all present (2026-10-25)
- [x] Test suite run — result: `npm test` in a clean `git archive` copy of HEAD 9f41390, 7 files, 178 passed, exit 0 (2026-10-25)
- [ ] Lint run — result: not configured in kit-config, not run (2026-10-25)
- [x] Typecheck run — result: `npm run typecheck`, exit 0 (2026-10-25)
- [x] Build run — result: `npm run build`, exit 0 (2026-10-25)
- [ ] Diff contains no files outside declared scope — every code and evidence file is declared at branch level; this progress file is in no step's scope (waiver proposed: it is the tracking file, and kit-config commits progress files) — left for the human (2026-10-25)
- [x] Tradeoff ledger reviewed and signed off by human — all 8 entries accepted, "sign off the F4 tradeoff" (2026-10-25)
- [ ] Human eye test completed

QA-GATE: FAIL 2026-10-25 — only human sign-offs outstanding: 8 unsigned tradeoffs, eye test, progress-file scope waiver (and confirmation of the 2026-10-25 amendment made under delegation)

---

## HANDOVER

Written 2026-10-25, second gate. Verdict: FAIL, but only because the human sign-offs
are outstanding. Install, tests, typecheck and build pass in a clean copy. Every locked
requirement maps to the diff. The stale deck found by the first gate is fixed. What is
left: sign the 8 tradeoffs, do the eye test below, waive the progress file's scope, and
confirm the 2026-10-25 amendment (made under your F4 delegation, not on your direct
instruction).

### What was built

A signed-in user now sees three tabs: Deck, Preferences and Favourites. Preferences
holds a free-text description, a workplace postcode and an optional maximum commute in
minutes. Saving shows what was understood, throws away the old deck at once, and loads
a fresh deck when commute times are ready, whichever tab the user is on. A new user
with no preferences is sent to Preferences on their own. Favourites lists saved
properties, and each one can be removed with a written reason. It all runs against the
mock API. Nothing talks to the real backend yet.

### What to check yourself

The mock dev server may already be on http://localhost:5183. If not, start one with
`cd web && VITE_API_MODE=mock npm run dev` and open the port it prints. Plain
`npm run dev` talks to the real backend on :8787 instead. Mock data lives in the page,
so reloading the page wipes users, swipes and favourites.

1. Create a new user. You should land on Preferences, not Deck.
2. Leave the text box or the postcode empty. Save should stay disabled. Type `abc` in
   "Maximum commute". You should see "Enter a whole number of minutes." and Save stays
   disabled.
3. Enter some text, postcode `EC2N 2DB`, no limit. Press Save. You should see "What we
   understood", then the Deck tab with cards.
4. Leaving early. Create another new user. Fill in Preferences, press Save, then press
   the Deck tab at once, within a second and a half. You may see "Commute times are
   still being worked out." Cards should then appear without you doing anything.
5. Re-save with a bad postcode. With a user who has cards on the deck, open
   Preferences, change the postcode to `FAIL 1AA` and save. You should see "Commute
   times could not be worked out. Check the postcode and save again." Open Deck. The
   old cards must be gone. Known weakness: the deck says "Commute times are still being
   worked out." even though they have failed. Press Retry. It should now say they could
   not be worked out, with a "Set preferences" button. Press it, set the postcode back
   to `EC2N 2DB` and save. A fresh deck should appear on the Deck tab.
6. Ready while elsewhere. Open Preferences, save, then open Favourites at once. When
   commute times are ready you should stay on Favourites. Open Deck: it should be a
   fresh deck, not the old cards.
7. Superlike (Love) a card. Open Favourites. The property should be listed with
   photo, price, address and "Added <today>".
8. Press Remove. A dialog asks "Why are you removing it?". Confirm should stay
   disabled while the box is empty. Press Cancel: the dialog closes and focus returns
   to that Remove button. Open it again and press Escape: same result.
9. Open Remove again, type a reason, press Confirm. The entry should disappear.
   Reopen the Favourites tab: it should still be gone.
10. With a new user, swipe any of the first cards (the first 15 are compulsory). The
    feedback screen opens. Switch to Favourites and back. The feedback screen should
    still be there. On Favourites, the arrow keys should not swipe the deck card.
11. While on Preferences or Favourites, press "Switch user" and pick a user. You
    should land on Deck, and Preferences should show that user's own saved values.
12. Narrow the browser to phone width (about 375 px) in devtools. Check that the three
    tabs, the Preferences form and the Favourites list are usable without sideways
    scrolling.

### Tools that will help

- Browser devtools, Elements panel: the current tab button carries
  `aria-current="page"`. The Deck and Preferences screens sit inside `hidden` divs
  while another tab is open. They are hidden, not removed, which is why polling and
  pending feedback survive a tab switch. Favourites is removed and rebuilt each time.
- Browser devtools, device toolbar: for the narrow-width check in step 12.
- The Network panel shows no API calls in mock mode: `VITE_API_MODE=mock` swaps in an
  in-memory client (`web/src/api/index.ts`). Once the real backend is connected, watch
  `PUT /prefs`, then `GET /deck` straight after it, the repeated `GET /prefs` every
  1.5 seconds, a second `GET /deck` when the status turns `ready`, and
  `DELETE /favourites/{listing_id}` with its `reason` body.

### What is not done

Tradeoffs, all unsigned (8):

1. Step 1: zero and negative commute limits are accepted, and "+5" is rejected. The
   backend owns range checks.
2. Step 2: polling has no time limit and keeps retrying after any error, including a
   4xx, while the status is pending.
3. Step 2: "What we understood" only appears when there is at least one limit or soft
   preference. A failed load shows the error with empty fields.
4. Step 3: after a removal, focus goes nowhere, because the Remove button has gone.
5. Step 3: the thumbnail uses the first photo only, with no fallback if it fails to
   load.
6. Step 4: saving preferences throws away the deck at save, and again when commute
   times are ready. A pending feedback screen, including compulsory onboarding
   feedback, is dropped and that card's feedback is lost. This entry was reworded by
   the redo; the first gate saw an earlier wording.
7. Step 4: the deck stays mounted while hidden. The "go to Preferences" redirect can
   fire from a hidden screen, and that effect ignores changes to its callback.
8. Redo of Step 4: when commute times fail, nothing tells the deck. It keeps saying
   "still being worked out" until Retry or a re-save (check step 5).

Spotted, not fixed:

- `.claude/worktrees/` is untracked and not gitignored.
- `useDeck.ts`: the `swipeBusy` race on a fast user switch mid-swipe (from F2).
- Strength labels are written out in both `ChipDialog.tsx` and `FeedbackScreen.tsx`
  (from F3).
- `deck.css` has orphaned `.deck-feedback` rules (from F3).
- `PrefsScreen.tsx` not resetting on a user change: resolved, it is now keyed by user.

Also not done: no lint command is configured, so lint was not run. There are no
component tests, because no DOM test setup is in scope. The real API is not connected.
`PrefsScreen.tsx` and `FavouritesScreen.tsx` each write out "Could not reach the server.
Try again." instead of reusing `GENERIC_ERROR_MESSAGE` from `web/src/deck/deckState.ts`.
`UserPicker.tsx` and `FeedbackScreen.tsx` already did the same, so this follows an
existing habit, but it is duplication.

### What could bite you

- Failed commute while on Deck. On the real backend TfL can fail after the user has
  left Preferences. The deck then says commute times are "still being worked out" when
  they have failed, until the user presses Retry. Nothing is broken, but the message is
  wrong and a user may wait for nothing.
- Lost onboarding feedback. Re-saving preferences while a compulsory feedback screen
  is open drops it. During the persona or recording runs this means a missing
  feedback row, with no error shown.
- Endless polling. If the backend never leaves `pending`, the screen says "Working out
  commute times…" for ever, with no message to say something is wrong. Preferences now
  stays mounted while hidden, so this polling also carries on while the user is on
  another tab, until they switch user or save again.
