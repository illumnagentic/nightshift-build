# Feature: API contract

- **Slug**: api-contract
- **Started**: 2026-10-24
- **Branch**: docs/api-contract (worktree `.claude/worktrees/api-contract`)
- **BASE_SHA**: 7597e7f21650d51514ef99fee0424595db254f4f
- **Status**: complete (2026-10-24)

---

## REQUIREMENTS (LOCKED)

Human, in session, 2026-10-24:

> "help to work out the api contract. should we use worktree for this?"

> "I take your recommendations let's start"

The recommendations accepted by that answer, as proposed in session:

1. Strength phrases: a fixed set (must-have / nice to have / would prefer not /
   deal-breaker) plus optional free text.
2. Superlike adds to favourites automatically; a right swipe does not.
3. `PUT /prefs` returns at once with `commute_status: pending|ready`; the deck waits
   until ready.
4. Deck served in batches of 10, refetched when it runs low.
5. Endpoint list as proposed: `GET/POST /users`, `GET/PUT /prefs`, `GET /deck?n=10`,
   `GET /listings/{id}`, `POST /decisions/{id}/swipe`, `PUT /decisions/{id}/feedback`,
   `POST /flags/{flag_id}/correction`, `GET /favourites`,
   `DELETE /favourites/{listing_id} {reason}`, `GET /profile`, `GET /stats`.
   JSON over `http://localhost:8787/api`, user in an `X-User-Id` header, errors as
   `{"error": {"code", "message"}}`. No train or batch endpoint.
6. Offered chips are logged server side when the deck is served, not on feedback.
7. Written against `main`; the uncommitted `schema.sql` change on
   `feat/dataset-extend` is noted, not assumed.

Binding line from `docs/plan.md`:

> "**API contract** — Zsolt + Yewen — `docs/api-contract.md`: endpoints, request and
> response shapes, `decision_id`, card `source` flag. Frontend mocks come from it."

### Source

This session's conversation, quoted above. Background: `docs/decisions.md`,
`docs/plan.md`, `docs/product-idea-high-level.md` ("Key endpoints", photo flag schema),
`dataset/d1/schema.sql` on `main`.

### Explicitly out of scope

- Any backend or frontend code, mocks, OpenAPI/JSON Schema files or generated types.
- D1 schema changes for app tables (users, decisions, feedback, favourites, profile).
  The contract names fields; the schema is B1's job.
- Prompt design for the curator, preference parser or photo flags.
- Persona batch, training and Mubit console steps.
- Auth beyond username only.
- Changing `docs/decisions.md`. Where the contract needs a decision changed, it is
  reported, not edited.
- Anything on `feat/dataset-extend`.

---

## AMENDMENTS

- 2026-10-24, human: "I take your advice" — settles six open points in
  `docs/api-contract.md` as proposed in session:
  1. Onboarding: the first 15 cards have compulsory feedback.
  2. Left swipes after onboarding: no feedback screen (`feedback_required` false).
  3. Favourite removal reason feeds the taste profile, treated as free-text feedback.
  7. Profile `factor` values come from a fixed list, seeded from the chip names.
  8. Deck exhausted: `GET /deck` returns 200 with an empty `cards` list.
  10. Prefs re-saved: unswiped served cards are discarded and their `decision_id`s
      dropped.
  Points 4, 5, 6 and 9 stay open. Point 11 is resolved: the contract follows
  `docs/decisions.md`.

- 2026-10-24, human: "accept all" — gaps found by the isolated mock test (Opus,
  contract only; log in `evidence/api-contract-mock-test.md`) settled as proposed:
  1. `GET /prefs` before prefs saved: `parsed: null`.
  2. `commute_postcode` is required on `PUT /prefs`.
  3. Card `feedback_required` is a hint; the swipe response is authoritative.
  4. After onboarding, superlike behaves as right swipe; feedback on a left swipe is
     still accepted if sent.
  5. `strength` is required; chip phrases fill `text` only.
  6. Cleared feedback is `chips: []`, `free_text: null` (never `""`).
  7. Every swipe, feedback PUT, favourite removal and flag correction bumps the profile
     version; swipe and flag-correction responses also return `profile_version`.
  8. `GET /deck` re-serves unswiped served cards first (same `decision_id`), then new
     ones, never duplicates; cards dropped by a prefs re-save return to the pool.
  9. Removing a favourite always bumps the profile version.
  10. Flag corrections are shared across users (a fact about the photo) and bump the
      correcting user's profile; empty text → 422 `invalid_request`; no undo.
  11. Missing or empty reason → `reason_required`; missing postcode →
      `invalid_request`; malformed postcode → `invalid_postcode`.
  12. Listing and flag enums copied into the contract so strict types can be written
      from it alone.
  13. `GET /stats` before any eval: all three arms `null`.
  14. `commute_status` gains `"failed"`; a TfL failure for one listing gives
      `minutes: null` only.
  15. Compulsory feedback is not enforced server side; the frontend obeys
      `feedback_required`.
  16. The Vite dev server proxies `/api` to `:8787`; no CORS.
  Also: `n` on `GET /deck` is clamped to 1–10. Other cosmetic items skipped.

- 2026-10-24, human (step 3 review follow-up): keep the `GET /listings/{id}` rule that a
  favourited listing can be fetched after the deck dropped it, with no `commute` or
  `chips`; and `GET /deck` returns 409 `commute_failed` when `commute_status` is
  `"failed"`.

- 2026-10-24, human (second QA gate follow-up), answers to the five Step 3 tradeoffs:
  1. Photo flag `room` gets a fixed list: `living_room`, `kitchen`, `bedroom`,
     `bathroom`, `hallway`, `garden`, `exterior`, `other` ("Fix it then").
  2. Photo flag nullability accepted; B2 must build the flag table to match it or
     update the contract ("fair").
  3. `GET /deck` `n` outside 1–10 or non-integer → 422 `invalid_request`; no clamp.
     Replaces the "`n` clamped to 1–10" line of the "accept all" amendment.
  4. A `chip_id` repeated within one feedback PUT → 422 `invalid_request`.
  5. Server treats `""` and whitespace-only `free_text` and chip `text` as `null`;
     no 422 for them. Flag-correction empty text stays 422 `invalid_request`.
  Also fix: enums intro must not claim photo flag rows come from schema.sql; the
  evidence log must say 8 cosmetic gaps were skipped; the Step 3 `room` tradeoff's
  open-point reference is replaced by this amendment.

- 2026-10-24, human: "8 fixes + rule, commit" — second isolated mock test (log appended
  to `evidence/api-contract-mock-test.md`) settled as proposed:
  1. `parsed` is filled in the `PUT /prefs` response; only the TfL step runs after.
  6. `chips` and `free_text` are both required keys in the feedback PUT (may be empty).
  7. A swiped listing is never served again to that user.
  8. An empty deck carries `"empty_reason": "exhausted" | "no_matches"`.
  10. The onboarding count does not reset on a prefs re-save.
  11. `room` is set on photo-scope flags and `null` on listing-scope flags.
  15. A superlike bumps the profile version once.
  17. Another user's `decision_id` → 404 `decision_not_found`.
  General rule: the backend owns validation details (formats, ranges, username rules,
  error precedence); the frontend shows `error.message` for any 4xx. The other gaps from
  the second test are logged as known minor items. No third mock test.

- 2026-10-24, human: "Yes, required" — `text` is a required, non-empty field in
  `PUT /prefs`; missing → 422 `invalid_request`. Settles gap 2 of the second mock test.

---

## RULES IN FORCE

| Rule | Source | Applies to |
| ---- | ------ | ---------- |
| Commits only via `.claude/scripts/safe-commit.sh`, title only, no signature, human approves | `.claude/CLAUDE.md` | commits |
| Commit title `type(scope): message`; type `docs`, scope `api` (new scope) | `.claude/CLAUDE.md`, `.claude/kit-config.md` | commits |
| Plain British English, short sentences, banned marketing words | `.claude/CLAUDE.md` | docs |
| No scope creep: touch only declared files | `.claude/CLAUDE.md` #1 | docs |
| No speculative generalisation: only endpoints and fields a decision or plan line needs | `.claude/CLAUDE.md` #4 | docs |
| Contract must not contradict `docs/decisions.md`; conflicts are reported | `docs/decisions.md` | docs |
| Card `source` flag is in the payload but never shown on the card face | `docs/decisions.md` (Exploration cards) | docs |
| Listing field names and enums match `dataset/d1/schema.sql` on `main` | `dataset/d1/schema.sql` | docs |
| Frontend never calls an LLM or Mubit; all LLM calls are backend only | `mubit-gateway` skill, `docs/decisions.md` (Mubit) | docs |
| `docs/plan.md` changes only to tick its own line, in the merging PR | `docs/plan.md` | docs |

---

## PLAN

### Step 1 — Write the API contract

**Goal**: Write `docs/api-contract.md` with every endpoint in requirement 5, each with
method, path, request and response JSON examples, and error codes.

**Files in scope**: `docs/api-contract.md` (new), `docs/plan.md` (tick the API
contract line only), `.claude/progress/api-contract.md` (TRADEOFFS / SPOTTED only).

**Done when**:
- Every endpoint in requirement 5 is present with request and response examples.
- Requirements 1–4 and 6 are stated explicitly in the endpoints they affect.
- Card payload carries `decision_id`, `source` (`ranked` | `exploration`) and the
  filtered `chips[]`, with the "never on card face" rule stated.
- Listing fields use the names and enums of `dataset/d1/schema.sql` on `main`.
- Open points are listed in one section, not scattered.
- No contradiction with `docs/decisions.md`, or each one is listed for the human.

**Evidence location**: the diff.

- [x] Implemented — docs/api-contract.md has all 11 endpoint groups from req 5 with examples and errors (2026-10-24)
- [x] Tested — all 19 json blocks parse; check-process-refs.sh exit 0; field names/enums compared to schema.sql at 7597e7f (2026-10-24)
- [x] Best practices met — British English, no banned words (grep empty), no pagination/tokens/versioning, invented details logged in TRADEOFFS (2026-10-24)
- [x] Matches locked requirements — reqs 1-4, 6 in Swipe/Feedback/PUT /prefs/GET /deck; source never on card face stated; Open points section (2026-10-24)
- [x] No scope drift — git status: only docs/api-contract.md, docs/plan.md (one-line tick), progress file (2026-10-24)

#### Redo of step 1 (2026-10-24, qa-gate findings, human approved: "ok accept")

**Goal**: Correct the "Differences from feat/dataset-extend" note, state which schema
columns the listing leaves out on purpose, and fix stale open-point numbers in TRADEOFFS.

**Files in scope**: `docs/api-contract.md` (that note, plus one line in the listing
section), `.claude/progress/api-contract.md` (the open-point references in TRADEOFFS
entries 1 and 5 only).

**Done when**:
- The note says the contract is written against `main` at `7597e7f` (which already
  drops `epc` media and fills demo EPC ratings), and that uncommitted work on
  `feat/dataset-extend` adds a `listings.split` column, which the contract never exposes.
- The listing section says `url`, `source`, `fetched_at` and `parsed_fields` are
  omitted deliberately.
- TRADEOFFS entry 1 cites Open points 2, 3; entry 5 cites Open point 1. No other edits.
- All JSON blocks still parse.

**Evidence location**: the diff.

- [x] Implemented — docs/api-contract.md 'Schema baseline' section, line-293 omitted-columns note, TRADEOFFS refs updated (2026-10-24)
- [x] Tested — evidence: 19 json blocks parse under python3 -I; check-process-refs.sh exit 0; main==feat/dataset-extend==7597e7f (2026-10-24)
- [x] Best practices met — evidence: banned words absent; no listing example contains url/source(fetched)/fetched_at/parsed_fields; card source only at line 158 (2026-10-24)
- [x] Matches locked requirements — evidence: Done-when 4 items verified: baseline note, omitted columns line, Open points 2,3 / 1 in TRADEOFFS, JSON parses (2026-10-24)
- [x] No scope drift — evidence: only api-contract.md note+1 line and TRADEOFFS refs; schema.sql identical to main (2026-10-24)

### Step 2 — Apply settled open points

**Goal**: Update `docs/api-contract.md` so the six points settled in the 2026-10-24
amendment are stated in the endpoints they affect and removed from Open points.

**Files in scope**: `docs/api-contract.md`, `.claude/progress/api-contract.md`
(TRADEOFFS / SPOTTED only).

**Done when**:
- Each of amendment points 1, 2, 3, 7, 8, 10 is stated in the endpoint section it
  affects, with examples updated where they show that behaviour.
- Open points keeps only 4, 5, 6 and 9 (renumbered or not, consistently); point 11 is
  gone or recorded as resolved outside Open points.
- All JSON blocks still parse; no other content changed.

**Evidence location**: the diff.

- [x] Implemented — evidence: docs/api-contract.md diff, amendment points applied (2026-10-24)
- [x] Tested — evidence: 19 json blocks parse (python3 -I), re-review (2026-10-24)
- [x] Best practices met — evidence: TRADEOFFS entries each on own line, wording unchanged (2026-10-24)
- [x] Matches locked requirements — evidence: amendment points 1,2,3,7,8,10 applied, Open points has 4 items (2026-10-24)
- [x] No scope drift — evidence: git status shows only api-contract.md, plan.md, progress file (2026-10-24)

### Step 3 — Close mock-test gaps

**Goal**: Apply the 16 points of the second 2026-10-24 amendment to
`docs/api-contract.md`, and store the mock-test gap log as durable evidence.

**Files in scope**: `docs/api-contract.md`, `evidence/api-contract-mock-test.md` (new,
copied from the session scratchpad), `.claude/progress/api-contract.md` (TRADEOFFS /
SPOTTED only).

**Done when**:
- Each of amendment points 1–16 and the `n` clamp is stated in the section it affects,
  with JSON examples updated where they show that behaviour.
- Listing and flag enums are written out in the contract and match
  `dataset/d1/schema.sql` on `main`.
- `evidence/api-contract-mock-test.md` holds the mock-test gap log (metadata only, no
  code).
- All JSON blocks still parse; no unrelated content changed.

**Evidence location**: `evidence/api-contract-mock-test.md` and the diff.

- [x] Implemented — docs/api-contract.md Step 3 changes present; evidence/api-contract-mock-test.md exists (2026-10-24)
- [x] Tested — evidence: 20 json blocks parse with python3 -I, exit 0; check-process-refs.sh exit 0 (2026-10-24)
- [x] Best practices met — evidence: GET /deck 409 commute_failed agrees with GET/PUT /prefs `failed` wording (api-contract.md lines 112, 137, 230); no banned words (2026-10-24)
- [x] Matches locked requirements — evidence: GET /listings/{id} favourites sentences (line 337) covered by AMENDMENTS "step 3 review follow-up" (2026-10-24)
- [x] No scope drift — evidence: git status shows only docs/plan.md, progress file, docs/api-contract.md, evidence/api-contract-mock-test.md (2026-10-24)

#### Redo of step 3 (2026-10-24, second QA gate follow-up, human approved)

**Goal**: Apply the second QA gate follow-up amendment and fix the two wording errors.

**Files in scope**: `docs/api-contract.md`, `evidence/api-contract-mock-test.md`,
`.claude/progress/api-contract.md` (TRADEOFFS / SPOTTED only).

**Done when**:
- `room` has the fixed list in the enums table and the photo flag section.
- `GET /deck` says `n` outside 1–10 or non-integer → 422 `invalid_request`; no clamp
  wording remains.
- Feedback PUT says a repeated `chip_id` → 422 `invalid_request`, and that `""` or
  whitespace-only `free_text` / chip `text` is stored as `null`; no text says `""` is
  rejected for feedback. Flag-correction empty text still → 422.
- Enums intro distinguishes schema-sourced rows from contract-defined photo flag rows.
- Evidence log says 8 cosmetic gaps were skipped on purpose.
- All JSON blocks parse; no other changes.

**Evidence location**: the diff; `evidence/api-contract-mock-test.md`.

- [x] Implemented — evidence: room list l.329-330,365; deck 422 l.152,232; feedback null/422 l.424-426; enums intro l.344; evidence l.9-10 (2026-10-24)
- [x] Tested — evidence: 20 json blocks parse under python3 -I; greps for clamp/"" /room clean (2026-10-24)
- [x] Best practices met — evidence: check-process-refs.sh exit 0; banned words none (2026-10-24)
- [x] Matches locked requirements — evidence: each Done-when bullet checked against docs/api-contract.md and amendment points 1-5 (2026-10-24)
- [x] No scope drift — evidence: git status: only api-contract.md, plan.md, evidence/, progress file; opening-paragraph reword justified by same schema.sql claim (2026-10-24)

### Step 4 — Close second mock-test gaps

**Goal**: Apply the "8 fixes + rule" amendment to `docs/api-contract.md` and append the
second mock-test log to the evidence file.

**Files in scope**: `docs/api-contract.md`, `evidence/api-contract-mock-test.md`,
`.claude/progress/api-contract.md` (TRADEOFFS / SPOTTED only).

**Done when**:
- Amendment points 1, 6, 7, 8, 10, 11, 15, 17 and the general validation rule are each
  stated in the section they affect; examples updated where they show that behaviour
  (e.g. the empty-deck example carries `empty_reason`).
- The evidence file has a second section for the second test (verdict, 198/198
  assertions, exit 0) with its gap list, marking which were settled and which are
  known minor items.
- All JSON blocks parse; no other changes.

**Evidence location**: `evidence/api-contract-mock-test.md` and the diff.

- [x] Implemented — evidence: docs/api-contract.md and evidence/api-contract-mock-test.md updated; gap 2 re-tagged known minor (2026-10-24)
- [x] Tested — evidence: 20 json blocks parse under python3 -I; check-process-refs.sh exit 0 (2026-10-24)
- [x] Best practices met — evidence: banned words absent; l.416 paragraph reflowed, wording unchanged (2026-10-24)
- [x] Matches locked requirements — evidence: general rule l.29-31, empty_reason l.175-184, superlike once l.426, other-user decision_id l.398/438 present; resolution line lists 3, 4, 13, 18, 19 only (2026-10-24)
- [x] No scope drift — evidence: git status: only api-contract.md, plan.md, evidence file, progress file (2026-10-24)

#### Redo of step 4 (2026-10-24, human: `text` required)

**Goal**: State that `text` is required in `PUT /prefs`, and mark gap 2 settled in the
evidence log.

**Files in scope**: `docs/api-contract.md` (PUT /prefs only),
`evidence/api-contract-mock-test.md` (gap 2 line only).

**Done when**: PUT /prefs says `text` is required and non-empty, missing or empty →
422 `invalid_request`; evidence gap 2 reads settled; JSON blocks parse; no other edits.

**Evidence location**: the diff.

- [x] Implemented — evidence: docs/api-contract.md l.140-141, evidence l.65 gap 2 'Settled: required and non-empty' (2026-10-24)
- [x] Tested — evidence: 20 json blocks parse under python3 -I, exit 0 (2026-10-24)
- [x] Best practices met — evidence: check-process-refs.sh exit 0; banned-word grep clean (2026-10-24)
- [x] Matches locked requirements — evidence: amendment: text required; 422 invalid_request for missing/null/empty/whitespace; no other text implies optional (only l.462 is chip text, unrelated) (2026-10-24)
- [x] No scope drift — evidence: git status: only plan.md, api-contract.md, evidence/api-contract-mock-test.md, progress file (2026-10-24)

---

## TRADEOFFS

- 2026-10-24 | Flag `confidence` scale (`high|medium|low`), flag `value` types and the flat `photo_flags` list shape were chosen by the contract author; the brief only said each flag carries a source photo and confidence | Needed concrete examples for mocks | Agree with the photo pipeline owner when flags are produced (Open points 2, 3). | **Accepted by human, 2026-10-24** ("ok accept").
- 2026-10-24 | `GET /profile` `history` capped at 10 entries, `cause.type` set (`swipe|feedback|flag_correction`) invented | Brief said "short history, if it stays small" | Confirm what the recording needs. | **Accepted by human, 2026-10-24** ("ok accept").
- 2026-10-24 | Added unrequested error codes `flag_not_found`, `invalid_request` and `GET /prefs` null-state | Mocks need them | Trim if unwanted. | **Accepted by human, 2026-10-24** ("ok accept").
- 2026-10-24 | Added `listing_id` to `GET /profile` `history[].cause` (set only for `favourite_removed`), since the cause needs a reference and neither existing id fits | Amendment point 3 | Drop if the recording does not need to show favourite removals. | **Accepted by human, 2026-10-24** ("ok accept").
- 2026-10-24 | "First 15 cards" read as the user's first 15 swipes; dropped cards do not count. The factor list is said to be seeded from chip ids but may include factors without a chip (e.g. `area_busyness`, already in the example) | Amendment wording is silent on both | Confirm with the human; exact factor list waits on the chip catalogue (Open point 1). | **Accepted by human, 2026-10-24** ("ok accept").
- 2026-10-24 | Swiping or sending feedback on a dropped `decision_id` reuses 404 `decision_not_found`; no new code | Amendment point 10 | Add a dedicated code if the frontend must tell "dropped" from "never existed". | **Accepted by human, 2026-10-24** ("ok accept").
- 2026-10-24 | Step 3: flag `room` has no fixed list; written as free snake_case text (e.g. `living_room`, `bathroom`) | Neither the contract nor schema.sql defines room values | Fix a room list with the photo pipeline owner (Open point 3). | **Rejected by human, 2026-10-24** — fixed list, see amendment.
- 2026-10-24 | Step 3: nullability stated for photo flag fields with no source (`value`, `observation`, `source_photo`, `confidence` never null; `uncertainty`, `corrected_text` null when absent; `room` null for listing scope) | Brief asked for nullability; no photo flag table exists yet | Check against the real table when B2 defines it. | **Accepted by human, 2026-10-24** — dependency on B2 flag table.
- 2026-10-24 | Step 3: `n` below 1 clamps to 1; non-integer `n` → 422 `invalid_request` | Amendment says "clamped to 1–10" only | Confirm. | **Rejected by human, 2026-10-24** — 422 outside 1–10, see amendment.
- 2026-10-24 | Step 3: a `chip_id` repeated in one feedback PUT is not addressed | Skipped as cosmetic | Add a rule if wanted. | **Rejected by human, 2026-10-24** — 422, see amendment.
- 2026-10-24 | Step 3: `GET /listings/{id}` stated to fetch any favourited listing, with no `commute` or `chips` | Closes a skipped cosmetic gap | Drop the two sentences if unwanted. | **Approved by human, 2026-10-24** (kept; now an amendment).
- 2026-10-24 | Step 3: `free_text: ""` → 422 `invalid_request`, extending the flag-correction rule | Amendment names that code for flag correction only | Confirm. | **Rejected by human, 2026-10-24** — normalised to null, see amendment.
- 2026-10-24 | Step 4: `empty_reason` is always present in the `GET /deck` response, `null` when `cards` is non-empty (spec allowed absent or null) | Keeps the TS type simple | Make it optional if the backend prefers. | **Accepted by human, 2026-10-24** ("Accept all three").
- 2026-10-24 | Step 4: photo-scope `room` is never `null` (spec said "set"); an unplaceable photo uses `other` | Closes the table/prose mismatch | Allow null on photo scope if the pipeline cannot always tell. | **Accepted by human, 2026-10-24** ("Accept all three").
- 2026-10-24 | Step 4: the evidence resolution line says "validation-detail gaps covered by the general rule" for gaps 3, 4, 13, 18, 19 (gap 2 re-tagged as known minor after review) | Spec said "the validation-detail ones" without listing them | Re-sort if the human disagrees. | **Accepted by human, 2026-10-24** ("Accept all three").

---

## SPOTTED, NOT FIXED

- docs/product-idea-high-level.md (Exploration cards) | Allows an "exploratory pick" label in the detail view and says a rising exploration hit rate proves improvement; decisions.md says source is never shown and the rate should fall | low (decisions.md already lists the second as open)
- docs/product-idea-high-level.md (photo schema) | Single `confidence` per photo; decisions.md wants one per flag | low
- docs/api-contract.md Open points 2 and 3 | overlap with the new photo flag enum rows, which state the confidence and value-type guesses as fixed | low
- docs/api-contract.md Schema baseline | mentions only `listings.split` | low
- docs/api-contract.md PUT /prefs (~l.122) | says poll until `ready`; l.115 and l.145 say `ready` or `failed` | low
- docs/api-contract.md enums table | media kinds listed as `photo`, `floorplan` only; schema.sql on main still allows `epc` (the build no longer emits it) — not stated | low

---

## VERIFICATION

- [x] All step checkboxes ticked with evidence (2026-10-24, qa-gate third pass; steps 1, redo 1, 2, 3, redo 3, 4, redo 4 all 5/5; five steps give "the diff" as evidence location, which is uncommitted)
- [x] Every evidence path in this file exists (2026-10-24: evidence/api-contract-mock-test.md, docs/api-contract.md)
- [x] Test suite run — result: not configured in kit-config
- [x] Lint run — result: not configured
- [x] Typecheck run — result: not configured
- [x] Build run — result: not configured
- [x] Diff contains no files outside declared scope (2026-10-24: docs/api-contract.md, docs/plan.md, evidence/api-contract-mock-test.md, this file)
- [x] Tradeoff ledger reviewed and signed off by human — all entries accepted, rejected-and-replaced, or approved by the human, 2026-10-24 (last: Step 4 entries, "Accept all three")
- [x] Human eye test completed — confirmed by the human, 2026-10-24 ("Yes, confirm"): human read the contract ("looks good"); two isolated Opus mock tests from the contract alone (second: 198/198 assertions, exit 0), log in `evidence/api-contract-mock-test.md`. Final `text`-required edit made after the tests.

---

## HANDOVER

**What was built.** `docs/api-contract.md` (675 lines): the HTTP contract between the
Worker and the frontend. It covers all 11 endpoint groups, request and response shapes,
error codes, the card (`decision_id`, `source`, filtered chips), feedback with strengths,
favourites, profile and stats, plus allowed values for listing and photo flag fields.
No running code exists. Yewen can build mocks from it. Zsolt can build the Worker to it.

**What to check yourself.**
1. Run `grep -n '^### ' docs/api-contract.md`. You should see all 11 endpoint groups.
2. Read "Deck". `source` is in the card and the file says it is never shown on the face.
3. Read "Swipe and feedback". Superlike adds a favourite, right swipe does not, the first
   15 swipes need feedback, and the swipe response overrides the card's hint.
4. Commit through `.claude/scripts/safe-commit.sh` (title `docs(api): ...`). Nothing is
   committed yet, so the work is not durable.

**Tools that will help.** `python3 -m json.tool` for the 20 JSON examples (all parse).
`dataset/d1/schema.sql` for field names. `evidence/api-contract-mock-test.md` for gaps
already found and settled.

**What is not done.** Open points: chip catalogue, flag confidence scale, flag value
types, id formats. Eight small mock-test gaps skipped on purpose, and further minor gaps
from the second test logged but not changed. SPOTTED, NOT FIXED: `product-idea-high-level.md`
disagrees with `decisions.md` on an exploration label, hit-rate direction and per-flag
confidence; Schema baseline mentions only `listings.split`; Open points 2 and 3 overlap
the photo flag enum rows. No schema, mocks or types exist. All tradeoffs are signed.

**What could bite you.** (1) The chip catalogue is undefined, so `chip_id`, `phrases` and
the `factor` list are guesses. Agree them before F3 and B5. (2) Photo flag enums are
invented here, not taken from a table. B2 may differ. (3) The server does not enforce
compulsory feedback or the first-15 rule, so a frontend that counts for itself will
drift. A prefs re-save drops unswiped decision ids, so a frontend holding a local deck
gets 404s.
