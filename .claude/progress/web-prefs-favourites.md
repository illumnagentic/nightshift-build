# Feature: F4 Prefs and favourites (frontend)

- **Slug**: web-prefs-favourites
- **Owner**: Yewen
- **Started**: 2026-10-24
- **Branch**: feat/web-prefs-favourites (stacked on feat/web-feedback, PR #13)
- **BASE_SHA**: a4d0c48e8fbee1a74b7bc4bed97cd5cad77fcf32
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

_None._

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

- [ ] Implemented
- [ ] Tested — evidence: (date)
- [ ] Best practices met — evidence: (date)
- [ ] Matches locked requirements — evidence: (date)
- [ ] No scope drift — evidence: (date)

---

## TRADEOFFS

- Step 1 | The client accepts zero and negative whole numbers as a commute limit and rejects an explicit plus sign ("+5") | the backend owns range checks (422); the form only parses what it can put in the JSON | add a range check or accept "+" if the backend contract defines one
- Step 2 | Polling has no time limit and keeps retrying after any error, including a 4xx, while the status is pending | the contract defines no timeout and a transient failure should not strand the user; leaving the screen or saving again stops it | add a cap with a visible 'taking too long' message once the backend gives an expected time
- Step 2 | The parsed result is shown only when it has at least one hard limit or soft preference, and a failed load shows the error with empty fields | nothing useful to show otherwise | none needed unless the eye test finds it confusing
- Step 3 | After a successful removal focus is not moved anywhere (the Remove button is gone) | no next target was specified | move focus to the next entry's Remove button or the screen heading
- Step 3 | The thumbnail shows only the first photo, with no handling for an image that fails to load | brief asks for the first photo only | add an onError fallback to the placeholder

---

## SPOTTED, NOT FIXED

- `.claude/worktrees/` | untracked and not gitignored | low
- `web/src/deck/useDeck.ts` | `swipeBusy` ref race on a rapid user switch mid-swipe (from F2) | low
- `web/src/feedback/ChipDialog.tsx`, `FeedbackScreen.tsx` | strength labels written out in both files (from F3, logged by the human's choice) | low
- `web/src/deck/deck.css` | orphaned `.deck-feedback` rules after the stub was deleted (from F3) | low
- `web/src/prefs/PrefsScreen.tsx` | form, parsed and status are not reset on a userId change; needs `key={userId}` or a reset when wired | low

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
