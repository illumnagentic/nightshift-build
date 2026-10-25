# Feature: B5 Feedback and taste profile

- **Slug**: feedback-profile
- **Owner**: Zsolt
- **Started**: 2026-10-25
- **Branch**: feat/feedback-profile
- **BASE_SHA**: d080bd1f4683c37c8d9e93f11eb9817048a724ce
- **Status**: in progress
- **Mode**: full automation (on since 2026-10-24)

---

## REQUIREMENTS (LOCKED)

Human, in session, 2026-10-25: "start working on B5".

`docs/plan.md`, Backend — Zsolt:

> **B5 Feedback and taste profile** — `feat/feedback-profile` — swipe / superlike /
> chip feedback endpoints, offered-vs-chosen logging, versioned profile (direction +
> weight), flag corrections, favourites.

> **Sat 13:00** — a user can be created, swipe a real deck (with at least one
> exploration card) and give chip feedback. Curator calls show in Mubit under one task.

> **Sat evening** — first adapter training done (or waiting on the daily cap).
> Full loop works end to end on one laptop.

`docs/decisions.md`, binding lines:

> **Core interaction.** [...] 1. Property card with three actions: swipe left
> (dislike), swipe right (like), superlike button. 2. Feedback screen after the
> decision. A preset list of feature chips [...] plus a free-text box for the card as a
> whole. 3. Tapping a chip opens a dialog: free text only, with preset suggested
> phrases. No numeric rating. Chips are optional, any number of them, and an existing
> answer can be edited. [...] A skip is recorded as a skip (`skipped: true`) and left
> out of the offered counts, so it never lowers a factor's weight. [...] A chip answer
> is about **this property's** version of that feature, phrased as how much the user
> likes or dislikes it. The general preference is derived from these answers across
> cards.

> **Two metrics per factor.** Every factor [...] carries two separate things:
> 1. **Direction** — where on that factor the user sits. [...] 2. **Weight** — how much
> that factor matters to this person at all. [...] Both are learned, and both feed the
> curator. A factor with a strong direction and a low weight should not drive a
> decision.

> **How the two are inferred.** No numeric input from the user. Instead:
> - **Weight** from how often a factor comes up. A chip chosen repeatedly, or a term
>   recurring in the free-text box, means the factor matters. Chips that are available
>   but consistently left alone suggest it matters less.
> - **Direction** from reading what was written. For or against, and how strongly, is
>   in the user's words, not in a counter.
> [...] Proposed fix: log how often each chip was *offered* as well as chosen, and
> weight on the ratio, not the raw count. Build this in from the start [...]
> [...] Proposed fix: the preset phrases carry the strength, e.g. must-have / nice to
> have / would prefer not / deal-breaker.

> **Memory is ours.** The taste profile (factor, direction, weight) lives in D1, built
> from swipes and chip feedback. This is Layer 1. Not Mubit's memory API.

> **Correction → model update path.** Correction → our profile updates (versioned)
> → next curator call carries that profile in its user message → provider gives the
> corrected answer → Mubit keeps the call as an example → the adapter trains on it.
> Every curator decision stores Mubit's `x-middleware-request-id` (`mreq_…`) and the
> profile version in D1, so the recording can show the trail: correction → profile
> version → curator call → adapter version.

> **Curator task shape.** The system prompt is one fixed string, never templated with
> anything but numbers or IDs. Everything per user — stated prefs, taste profile,
> lessons, past swipes, the listing — goes in the user message. [...]

> **Photo flags.** [...] A user's correction to a flag ("not damp") is written onto the
> cached flag record, and the curator reads the corrected text.

`docs/api-contract.md`, binding sections: General; Server-side only; Listings
(`GET /listings/{id}`, if ruled in); Chip catalogue (factor = `chip_id`, offered =
`chips[]` as logged); Swipe and feedback (`POST /decisions/{id}/swipe`,
`PUT /decisions/{id}/feedback`); Flag corrections; Favourites; Profile.

B4 carry-overs (`.claude/progress/curator-deck.md`, TRADEOFFS step 3 and Q4):

> B5's kickoff must require, as Done-when items of its swipe step: (1) an API test that
> swipes through a user's whole train pool and then gets `exhausted` with no cards and
> no curator call, distinct from `no_matches`; (2) an API test that after 15 swipes
> every card has `feedback_required` false, and a boundary test where a page served
> after 12 swipes has true at positions 0–2 and false from position 3; (3) both in
> `worker/tests/test_deck.py` or the B5 swipe test module, with the `fake` fixture.

> Q4: [...] Neither the B4 nor the B5 plan line names it [`GET /listings/{id}`], so the
> B5 kickoff must decide it.

### Source

Quoted above. Plan by the main agent, 2026-10-25, checked against these lines. Arbiter
rulings on the open questions are in KICKOFF RULINGS.

### Explicitly out of scope

- Any change under `web/`. Any breaking change to `docs/api-contract.md`.
- Any change to the curator `SYSTEM_PROMPT`, `RESPONSE_SCHEMA`, `GENERATION_CONFIG` or
  model (frozen; SHA-256s in `curator-deck.md`).
- An LLM call to summarise feedback or infer direction (unless ruled in).
- Personas, persona CSV, batch runner (B6). Eval runner, `/stats` (B7).
- User-initiated comparison, lesson receipts, A-vs-B (decisions.md: not in the cut).
- Server-side enforcement of compulsory feedback (contract: not enforced).
- Undo of a flag correction; re-adding a removed favourite.
- Starting Mubit training; deploy; any paid Mubit call.
- New dependencies.

---

## AMENDMENTS

- 2026-10-25 (arbiter) — rename `worker/src/profile.py` to `worker/src/taste.py`. Goal: the taste-profile module imports in the Python Worker runtime (`import profile` resolves to the stdlib `profile` module). Files: `worker/src/taste.py` replaces `worker/src/profile.py` in the Files in scope of Steps 1–4 (edited in PLAN); `worker/src/entry.py` imports `taste`. KICKOFF RULINGS references to `profile.py` (Q5) now mean `taste.py`. Done when: `worker/src/profile.py` no longer exists, `entry.py` imports `taste`, and the Step 1 API tests run against the test-mode server with no `AttributeError`. No REQUIREMENTS, contract or dependency change; checked `import taste` fails under python3 and no `taste` module exists in `worker/python_modules`, `.venv` or `.venv-workers`.
- 2026-10-25 (arbiter) — swipe race returns 404, not 409. Goal: a swipe on a decision dropped by a concurrent prefs re-save returns the contract's 404 `decision_not_found` (TRADEOFFS step 1). Files: `worker/src/entry.py` (already in Step 3 scope). Done when: the extra Step 3 Done-when line holds. Folded into Step 3, not a redo of committed Step 1.
- 2026-10-25 (arbiter) — README test lists. Goal: `worker/README.md` Tests lists name `tests/test_feedback.py` and `tests/test_profile_unit.py` (SPOTTED step 2), plus Step 3's new test modules. Files: `worker/README.md` (already in Step 4 scope). Done when: the extra Step 4 Done-when line holds.

---

## RULES IN FORCE

| Rule | Source | Applies to |
| ---- | ------ | ---------- |
| Plain British English, no banned words, no padding | `.claude/CLAUDE.md` Language and tone | docs, comments, evidence, commits |
| Commits via `safe-commit.sh` only, title only, no attribution | `.claude/CLAUDE.md` Committing | commits |
| `type(scope): message`; scopes worker, web, db, prep, kit, api | `.claude/CLAUDE.md`, `kit-config.md` | commits, PR title |
| No scope creep; touch only the step's declared files | `.claude/CLAUDE.md` prohibition 1 | code, docs |
| No new dependencies | `.claude/CLAUDE.md` prohibition 2 | code |
| Never weaken a test | `.claude/CLAUDE.md` prohibition 3 | tests |
| The ladder: least code, reuse what exists | `.claude/CLAUDE.md` The ladder | code |
| Tradeoffs and spotted items logged in this file | `.claude/CLAUDE.md` prohibitions 5, 7 | this file |
| Only step-reviewer ticks boxes | `.claude/CLAUDE.md` prohibition 6 | this file |
| Evidence durable, metadata only | `.claude/CLAUDE.md` Progress file discipline; decisions.md Evidence | `evidence/feedback-profile/` |
| Endpoint shapes, errors and codes exactly as the contract | `docs/api-contract.md` | code, tests |
| Errors `{"error": {"code", "message"}}`; unknown values `null` | `docs/api-contract.md` General | code |
| Factors are exactly the catalogue `chip_id`s; free text never adds a factor | `docs/api-contract.md` Chip catalogue, Profile | code |
| Offered = chips logged at serve (`decisions.offered_chips`); skips never lower weight | decisions.md Core interaction, How the two are inferred | code |
| Curator system prompt and config frozen; per-user data in the user message only | decisions.md Curator task shape | code |
| `mreq_` id and profile version stored per curator decision | decisions.md Correction path | code |
| API tests run only against the test-mode server with the fake upstream | `worker/README.md` Tests | tests |
| Python Worker runtime: no extra packages; D1 via `env.DB` | decisions.md Stack | code |

---

## PLAN

### Step 1 — Swipe, profile versions and `GET /profile` history

**Goal**: `POST /decisions/{decision_id}/swipe` records the action, adds a favourite on
superlike, bumps the profile version once, and `GET /profile` returns the version and
history; the two B4 carry-over deck tests are added.

**Files in scope**: `worker/schema.sql`, `worker/src/entry.py`, `worker/src/taste.py`
(new), `worker/tests/test_swipe.py` (new), `worker/README.md`,
`evidence/feedback-profile/step-1.md` (new).

**Done when**:
- Swipe returns the contract body; `action` other than `left`/`right`/`superlike` is
  422 `invalid_request`; unknown id, another user's id and an id dropped by a prefs
  re-save are 404 `decision_not_found`; a second swipe is 409 `already_swiped`.
- `feedback_required` in the response is true for each of the user's first 15 swipes,
  whatever the action, and false from the 16th; a prefs re-save does not reset it.
- A superlike adds a favourite row; a right swipe does not; `favourited` says which.
- Every swipe bumps the version by exactly one (superlike once); `GET /profile` shows
  that version, `history` newest first, at most 10 entries, cause `swipe` with
  `decision_id` set and the other ids `null`; a new user gets `version: 0`, empty
  `factors`, empty `history`.
- B4 carry-overs, with the `fake` fixture: (1) swipe through a user's whole train pool,
  then `GET /deck` gives `cards: []`, `empty_reason: "exhausted"` and no new curator
  request, distinct from a `no_matches` user; (2) after 15 swipes every served card has
  `feedback_required` false; a page served after 12 swipes has true at positions 0–2
  and false from position 3.
- Versions live in a `profile_versions` table; the new version is assigned inside one
  `INSERT ... SELECT` statement (Q8). B5 adds new tables only, no column on an existing
  table (Q10).
- `worker/README.md` says how to get the new tables onto an existing local D1.

**Evidence location**: `evidence/feedback-profile/step-1.md`

- [x] Implemented — worker/src/taste.py, entry.py swipe and /profile routes, schema.sql favourites + profile_versions (2026-10-25)
- [x] Tested — evidence: reviewer run in throwaway worktree, seeded, port 8830: full suite 299 passed exit 0; server-less 99 passed exit 0; test_swipe.py covers the carry-over tests (2026-10-25)
- [x] Best practices met — evidence: conditional UPDATE checks meta.changes, single INSERT...SELECT RETURNING for version, ON CONFLICT DO NOTHING for favourite, check-process-refs exit 0 (2026-10-25)
- [x] Matches locked requirements — evidence: contract Swipe and Profile sections vs test_response_body_for_each_action, test_feedback_required_and_profile_history_over_sixteen_swipes, test_new_user_profile_is_empty; Q8, Q10 met (2026-10-25)
- [x] No scope drift — evidence: diff files are exactly Step 1 scope (README, schema.sql, entry.py, taste.py, test_swipe.py, evidence step-1.md) plus the progress file (2026-10-25)

### Step 2 — Feedback and the taste profile factors

**Goal**: `PUT /decisions/{decision_id}/feedback` stores, edits, clears or skips
feedback, and the profile's factors (direction + weight) are computed from it on the
offered-versus-chosen ratio.

**Files in scope**: `worker/schema.sql`, `worker/src/entry.py`, `worker/src/taste.py`,
`worker/tests/test_feedback.py` (new), `worker/tests/test_profile_unit.py` (new),
`evidence/feedback-profile/step-2.md` (new).

**Done when**:
- Every validation rule in the contract's feedback section holds, each with a test:
  both keys required; `strength` enum; repeated `chip_id` 422 `invalid_request`; a chip
  not in that decision's `offered_chips` 422 `chip_not_offered`; blank text stored and
  returned as `null`; `skipped: true` only with `[]` and `null`; 404
  `decision_not_found` (unknown, other user, dropped); 409 `not_swiped`.
- A PUT replaces the whole feedback; the response echoes it with `skipped` and the new
  `profile_version`; every PUT bumps the version (including a no-op edit and a clear),
  cause `feedback`.
- `GET /profile` `factors` follow the KICKOFF RULINGS formula (Q3, Q5, Q6) and are the
  latest `profile_versions` snapshot (Q8): `offered` counts come only from
  `decisions.offered_chips`, free-text-only matches only from the Q5 term list, both on
  swiped decisions with a non-skipped feedback row; the term list is in the evidence
  file and each term has a match and a non-match unit test; a skip
  never lowers a weight (unit test); a factor offered rarely but chosen each time
  outweighs one offered often and chosen rarely (unit test); every factor name is a
  catalogue `chip_id`; free text can move a weight but never adds a factor.
- Direction text is built from the chip answers' strengths and texts as ruled.

**Evidence location**: `evidence/feedback-profile/step-2.md`

- [x] Implemented — evidence: PUT /decisions/{id}/feedback in worker/src/entry.py, taste.compute_factors/current_factors (ORDER BY f.updated_at DESC, f.decision_id), feedback table in worker/schema.sql; redo items done (2026-10-25)
- [x] Tested — evidence: full suite 373 passed exit=0, server-less 7 modules exit=0 (reviewer run in throwaway worktree, :8850); tests/test_feedback.py, tests/test_profile_unit.py incl. equal-updated_at test (2026-10-25)
- [x] Best practices met — evidence: body validated before lookup, 404/409/422 per contract, upsert single statement, check-process-refs.sh exit 0 (2026-10-25)
- [x] Matches locked requirements — evidence: Q3 weight formula, Q4 direction, Q5 TERMS regexes listed in evidence/feedback-profile/step-2.md, Q6 chosen>=1, Q8 snapshot via bump (2026-10-25)
- [x] No scope drift — evidence: diff vs 12e9460 touches only the six declared Step 2 files plus the progress file (2026-10-25)

**Review FAIL 2026-10-25 (step-reviewer):** `check-process-refs.sh` exit 1, two hits in `evidence/feedback-profile/step-2.md`: line 3 "the Step 2 files" and line 11 "(Step 3)". Reword both without step numbers, then re-review. Everything else passed: code matches Q3/Q4/Q5/Q6/Q8, 372 and 203 tests pass (exit 0 each), no scope drift.

**REDO OF STEP 2 (arbiter 2026-10-25):** (1) reword `evidence/feedback-profile/step-2.md` line 3 "the Step 2 files" and line 11 "(Step 3)" with no step numbers, so `check-process-refs.sh` exits 0; (2) make `taste.current_factors` read feedback in a fixed order: `ORDER BY f.updated_at DESC, f.decision_id` on its query, plus a unit test in `worker/tests/test_profile_unit.py` that two rows with equal `updated_at` give direction text in input order. Files: `evidence/feedback-profile/step-2.md`, `worker/src/taste.py`, `worker/tests/test_profile_unit.py` (all in Step 2 scope). Done when: `check-process-refs.sh` exits 0, full suite and server-less suite pass, then step-reviewer re-reviews Step 2. Review FAILs on Step 2 so far: 1.

### Step 3 — Favourites, flag corrections and listing detail

**Goal**: `GET /favourites`, `DELETE /favourites/{listing_id}` with a reason,
`POST /flags/{flag_id}/correction`, and `GET /listings/{id}` (if ruled in), each per
the contract and each bumping the profile version where the contract says so.

**Files in scope**: `worker/schema.sql`, `worker/src/entry.py`, `worker/src/taste.py`,
`worker/src/deck.py` (imported only, to reuse `_load_listings` and `CARD_LISTING_KEYS`;
no edit), `worker/tests/test_favourites.py` (new), `worker/tests/test_flags.py`
(new), `evidence/feedback-profile/step-3.md` (new).

**Done when**:
- `GET /favourites` lists superliked listings with `added_at` and the card `listing`
  object, newest first.
- `DELETE /favourites/{listing_id}`: missing/`null`/blank `reason` is 422
  `reason_required`; not a favourite is 404 `not_favourited`; success returns
  `{"listing_id", "removed": true}`, stores the reason, bumps the version with cause
  `favourite_removed` and `listing_id` set; the reason feeds the factors as ruled.
- Flag correction: blank or missing `text` 422 `invalid_request`; unknown id 404
  `flag_not_found`; success writes `corrected_text` on the shared flag row, returns the
  flag plus the correcting user's new `profile_version`, cause `flag_correction` with
  `flag_id` set; another user then sees the correction; a flag on an `eval`-split
  listing is 404 `flag_not_found` and is left unchanged.
- `GET /listings/{id}` returns every contract field, photo flags with `flag_id` and
  `corrected_text`, no `split`, no `commute`, no `chips`; unknown id and an `eval`-split
  id are 404 `listing_not_found`; a favourited listing dropped from the deck still
  returns 200.
- (arbiter 2026-10-25) In `POST /decisions/{id}/swipe`, when the conditional update
  changes no row, the decision is re-read and a row gone (dropped by a concurrent prefs
  re-save) returns 404 `decision_not_found`, not 409; a still-present swiped row stays
  409 `already_swiped`. Checked by reading the code; the existing `test_swipe.py`
  404/409 tests still pass.

**Evidence location**: `evidence/feedback-profile/step-3.md`

- [ ] Implemented
- [ ] Tested — evidence: (date)
- [ ] Best practices met — evidence: (date)
- [ ] Matches locked requirements — evidence: (date)
- [ ] No scope drift — evidence: (date)

### Step 4 — The curator reads the profile

**Goal**: every new curator call carries the user's current taste profile and recent
feedback in its user message, and stores that profile version on the call and on
every decision it creates.

**Files in scope**: `worker/src/deck.py`, `worker/src/taste.py`,
`worker/tests/test_deck.py`, `worker/README.md`, `evidence/feedback-profile/step-4.md`
(new).

**Done when**:
- After feedback, the next `GET /deck` that needs new cards sends a user message whose
  `taste_profile` is an object `{<factor>: {"direction", "weight"}}` with exactly the
  entries of `GET /profile` `factors`, and whose `recent_feedback` holds the
  ruled entries (Q7); `curator_calls.profile_version` and every new
  `decisions.profile_version` equal `GET /profile` `version` at that moment.
- `systemInstruction` and `generationConfig` are byte-identical to before (the B4
  SHA-256s still match); `worker/src/curator.py` is unchanged.
- A new user's first call still sends `{}`, `[]` and version 0.
- After a flag correction, the next curator request's candidate digest for that listing
  carries the corrected text (decisions.md Photo flags).
- The trail correction → profile version → curator call → `mreq_` id can be read from
  D1 for one user; the query is written in the evidence file.
- (arbiter 2026-10-25) `worker/README.md` Tests lists include `tests/test_feedback.py`
  and `tests/test_profile_unit.py`, plus any test module Step 3 adds.

**Evidence location**: `evidence/feedback-profile/step-4.md`

- [ ] Implemented
- [ ] Tested — evidence: (date)
- [ ] Best practices met — evidence: (date)
- [ ] Matches locked requirements — evidence: (date)
- [ ] No scope drift — evidence: (date)

---

## KICKOFF QUESTIONS (for the arbiter)

Q1: Build `GET /listings/{id}` in B5 (step 3)? Proposed: yes. Flag corrections need a
`flag_id`, and the contract exposes flag ids only through this endpoint, so without it
flag corrections cannot be used by anyone. The contract already defines it fully.

Q2: Profile computed in code, no LLM call? Proposed: yes. Strength is a field on every
chip answer, so "for or against, and how strongly" is already in the user's own
choice; the raw words reach the curator through `recent_feedback`. No extra spend, no
second Mubit task, testable.

Q3: Weight formula. Proposed: per factor, over the user's swiped decisions that have
non-skipped feedback, `offered` = decisions where the chip was in `offered_chips` or
the factor's terms appear in that decision's free text; `chosen` = decisions where the
chip was answered or its terms appear in the free text. `weight = round(chosen /
(offered + 1), 2)`, so one mention out of one offer is 0.5, not 1. Decisions swiped
with no feedback PUT at all are left out of both counts.

Q4: Direction text. Proposed: built from the factor's chip answers, newest first, at
most 3, as `<strength in words> "<text>"` joined by `; ` (e.g. `must have "Bright and
airy"; would prefer not "A bit dark"`), with `(no comment)` for a null text. A factor
known only from free text has direction `mentioned in comments`.

Q5: Free-text terms. Proposed: one fixed case-insensitive regex per factor in
`profile.py` (reusing the chip catalogue's mention patterns where they read as buyer
words). A match counts towards weight only; direction is not inferred from free text in
code. The same applies to a favourite-removal reason, counted as one extra offered and
chosen for each matching factor.

Q6: Which factors `GET /profile` lists. Proposed: those with `chosen` ≥ 1. A factor
offered but never chosen is left out (and so is absent from the curator's
`taste_profile`).

Q7: `recent_feedback` sent to the curator. Proposed: the user's last 10 non-skipped,
non-empty feedback entries and favourite removals, newest last, each
`{"listing_id", "action", "chips": [{"chip_id", "strength", "text"}], "free_text"}` or
`{"listing_id", "favourite_removed": "<reason>"}`. Flag corrections are not repeated
there: they already reach the curator through the candidate photo digest.

Q8: Version storage. Proposed: a `profile_versions` table, one row per bump
`(user_id, version, created_at, cause_type, decision_id, flag_id, listing_id,
factors_json)`, `UNIQUE (user_id, version)`, the new version being the user's max + 1.
The factor snapshot is stored with each version so a curator call's
`profile_version` maps to exactly what it was sent. Two concurrent writes for one user
can collide on the unique key and one returns 500; accepted as a tradeoff since
personas keep one request in flight.

Q9: Flag correction storage. Proposed: overwrite `photo_flags.corrected_text` (latest
wins) and append `(flag_id, user_id, text, created_at)` to a `flag_corrections` table
for the trail. A re-seed drops corrections; accepted.

Q10: New tables reach existing laptops how? Proposed: `CREATE TABLE IF NOT EXISTS` in
`worker/schema.sql`; README gives the one `wrangler d1 execute --local --file
schema.sql` command (keeps users) and notes `seed.sh` also works (wipes users).

Q11: Any live paid call in B5? Proposed: none. The fake upstream records request
bodies, which is the proof for step 4.

---

## KICKOFF RULINGS

Q1: Yes, build `GET /listings/{id}` in Step 3, exactly as the contract defines it, with one addition: an `eval`-split id returns 404 `listing_not_found`, and a correction to a flag on an `eval`-split listing returns 404 `flag_not_found` — arbiter 2026-10-25: the contract exposes `flag_id` only here, so flag corrections (a plan-line item) are unusable without it, and `web/src/api/http.ts` already calls it; the 404s follow the contract's "no held-out listing reaches any user" and stop a user correction changing what the curator reads about a held-out listing during the eval (decisions.md Training vs evaluation split). Not a contract break: the split stays unexposed and the error code is the documented one.
Q2: Accept — profile computed in code, no LLM call — arbiter 2026-10-25: `strength` is a required contract field, so "for or against, and how strongly" is the user's own choice, not a counter; the user's words reach the curator verbatim through the direction text and `recent_feedback`; no spend, no second Mubit task, testable. The decisions.md open item on wording strength is already answered by the contract's `strength` enum, so nothing open is settled here.
Q3: Accept the formula, renamed to keep the contract's meaning of "offered": per factor, over the user's swiped decisions that have a feedback row with `skipped` false, `offered` = decisions whose `offered_chips` holds the chip (exactly the contract's offered set), `mentioned_only` = decisions where the factor's term matched the free text but the chip was not offered, `chosen` = decisions where the chip was answered or its term matched the free text (once per decision, however many matches); `weight = round(chosen / (offered + mentioned_only + 1), 2)`. A feedback row with `chips: []` and `free_text: null` and `skipped` false (a clear, or "nothing to say") counts as offered with nothing chosen. Decisions with no feedback row, and skipped ones, are in neither count — arbiter 2026-10-25: this is the ratio decisions.md asks to build in from the start; the contract says only `chips[]` count as offered, so free-text-only opportunities are counted separately rather than called offered; the +1 keeps one-of-one at 0.5 and the weight below 1; leaving alone an offered chip lowering weight is the decided text ("available but consistently left alone suggest it matters less").
Q4: Accept — direction text from the factor's chip answers, newest first, at most 3, `<strength in words> "<text>"` joined by `; `, `(no comment)` for a null text, `mentioned in comments` for a free-text-only factor; strength words are exactly `must have`, `nice to have`, `would prefer not`, `deal-breaker` — arbiter 2026-10-25: keeps the user's words and their chosen strength together, which is decisions.md's "direction from reading what was written"; the contract example strings are illustrative, and the curator, not code, interprets the words.
Q5: Accept, with the terms pinned: one fixed case-insensitive regex per catalogue factor in `profile.py`, written with word boundaries, listed in the Step 2 evidence file, each with a unit test showing one matching and one non-matching sentence; a factor may have no regex (then free text never touches it). Free-text matches move weight only. A favourite-removal reason counts once as `mentioned_only` (or `offered` if that decision offered the chip) and once as `chosen` for each matching factor — arbiter 2026-10-25: the contract says free text can move weight but never adds a factor, which fixed regexes over catalogue ids guarantee; pinning the list in evidence lets the reviewer check it instead of trusting an unwritten term set.
Q6: Accept — `GET /profile` lists factors with `chosen` ≥ 1, ordered by weight descending then `chip_id` — arbiter 2026-10-25: a factor never chosen has no direction to report, and twenty zero-weight entries would bloat every curator request for no signal; a fixed order keeps the user message deterministic.
Q7: Accept — the last 10 non-skipped, non-empty feedback entries and favourite removals, newest last, in the proposed shapes; ordered by the time the feedback or removal was last written — arbiter 2026-10-25: matches the frozen prompt's description ("latest comments ... newest last"); flag corrections already reach the curator through the candidate digest (B4 Step 2 redo), so repeating them would double-count.
Q8: Accept the `profile_versions` table, changed on two points: (1) the new version is taken inside one `INSERT ... SELECT COALESCE(MAX(version), 0) + 1 ...` statement, not read then written, so D1's serial statement execution leaves no read-then-write window; (2) the latest row's `factors_json` is the single source: `GET /profile` returns its factors and Step 4's curator call sends exactly that row's factors and version. A new user with no row is version 0 and `{}` — arbiter 2026-10-25: removes the collision the proposal accepted at no extra cost, and one source makes "curator call version ↔ what it was sent" true by construction, which is the decisions.md correction trail.
Q9: Replace — overwrite `photo_flags.corrected_text` (latest wins); no `flag_corrections` table. The trail is the `profile_versions` row (cause `flag_correction`, `flag_id`, user, time). A re-seed drops corrections; accepted — arbiter 2026-10-25: the ladder, rung 1: nothing in the plan reads earlier correction texts, and the contract's trail (correction → profile version → curator call) is already carried by `profile_versions`.
Q10: Accept, with one constraint: B5 adds new tables only and never a column to an existing table (`users`, `prefs`, `decisions`, `curator_calls`, `photo_flags`), so `CREATE TABLE IF NOT EXISTS` plus the one `wrangler d1 execute --local --file schema.sql` command is enough on an existing D1 — arbiter 2026-10-25: `IF NOT EXISTS` cannot add a column, so an `ALTER` would break Yewen's laptop silently; feedback, favourites and versions fit as new tables keyed by `decision_id` / `user_id`.
Q11: Accept — no live paid call in B5; the fake upstream's recorded request bodies are the proof for Step 4 — arbiter 2026-10-25: B4 already proved the live route and task; B5 changes only the user message, which does not split the Mubit task; the cost check after 50 calls belongs to the persona batch (B6).

Plan check — arbiter 2026-10-25: 4 steps, coarse vertical slices, within 3–5. Requirements all mapped: swipe/superlike (S1), chip feedback and offered-vs-chosen (S2), versioned profile (S1–S2), flag corrections and favourites (S3), profile into the curator and version per decision (S4). One requirement was missing — decisions.md Photo flags "the curator reads the corrected text" had no Done-when; added to Step 4. Step 2's offered wording and Step 4's `taste_profile` shape edited to match Q3, Q8 and the frozen prompt ("maps a factor to a direction and a weight", `{}` when empty). Step 3's `deck.py` scope narrowed to imports only. Nothing escalates.

---

## TRADEOFFS

2026-10-25 | step 1 | A swipe whose decision row is deleted by a concurrent prefs re-save, between the swipe's lookup and its conditional update, returns 409 `already_swiped` instead of 404 `decision_not_found` | The window is one request wide and needs the same user to re-save prefs while a swipe is in flight; the frontend and personas do not do that | Re-read the row after a zero-change update and return 404 if it is gone (about 3 lines in `entry.py`). — FIX_NOW by arbiter 2026-10-25: cheap (about 3 lines) and the contract fixes 404 for a dropped id; folded into Step 3's Done-when (`entry.py` is in its scope) via AMENDMENTS (arbiter), not a redo of committed Step 1.
2026-10-25 | step 2 | Free-text term matching ignores negation and context: "no garden" counts as a mention of `garden` and raises its weight | Q5 fixes direction to the chips' strengths and texts; code only counts mentions, and a regex list cannot read sentences | Have the model read free text for direction as well as mention (ruled out in Q2), or accept the noise. — accepted by arbiter 2026-10-25: decisions.md makes weight a count of mentions and "no garden" does show the factor matters; direction stays with chip strengths (Q4, Q5), and reading negation needs the LLM call ruled out in Q2.
2026-10-25 | step 2 | Every swipe and feedback bump recomputes the factors from all the user's feedback rows (one extra query, work grows with swipes) | Q8 stores the fresh snapshot per version; a user has tens to a few hundred rows | Keep the aggregate counts in a table and update them per PUT. — accepted by arbiter 2026-10-25: at tens to a few hundred rows per user the cost is negligible, and a fresh snapshot per version is what Q8 asks for; an aggregate table would be extra state to keep consistent.
2026-10-25 | step 2 | A body with the wrong shape returns 422 before a missing or foreign decision returns 404 | Same order as the swipe endpoint; the contract fixes no order | Look the decision up first. — accepted by arbiter 2026-10-25: contract General says the backend owns which error wins when several apply; consistent with the swipe endpoint.

---

## SPOTTED, NOT FIXED

- 2026-10-25 | step 1 | `worker/src/profile.py` is shadowed by the standard library `profile` module in the Python Worker runtime: `import profile` in `entry.py` returns the stdlib module (`module 'profile' has no attribute 'bump'`, seen in the test-mode server log). Step 1 is blocked until the module is renamed in the plan (Steps 2-4 also name `profile.py`). — FIX_NOW by arbiter 2026-10-25: blocks Step 1 and every later step; renamed to `worker/src/taste.py` via AMENDMENTS (arbiter).

- 2026-10-25 | step 2 | `worker/README.md` Tests lists do not yet include `tests/test_feedback.py` and `tests/test_profile_unit.py`, and README is outside Step 2's scope. Step 4's scope has README. — minor. — FIX_NOW by arbiter 2026-10-25: a two-line doc edit; folded into Step 4's Done-when (README in its scope) via AMENDMENTS (arbiter).

- 2026-10-25 | step 2 | `worker/src/taste.py:73` | `current_factors` reads feedback rows with no `ORDER BY`; `compute_factors` sorts by `updated_at` only (stable sort), so rows with an equal `updated_at` keep D1's unspecified order and direction text (newest first, capped) may vary. `updated_at` comes from `deck._now()` (microseconds, `entry.py:272`), so a tie is unlikely in practice | low. — FIX_NOW by arbiter 2026-10-25: one line plus one unit test, inside Step 2's files; folded into the REDO OF STEP 2 under Step 2's heading.

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
