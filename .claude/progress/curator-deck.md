# Feature: B4 Curator and deck

- **Slug**: curator-deck
- **Started**: 2026-10-25
- **Branch**: feat/curator-deck
- **BASE_SHA**: 9805b51ae68b34e633180448228a5d6b58cb0304
- **Status**: in progress
- **Owner**: Yewen (plan.md assigns B4 to Zsolt; Yewen took it on 2026-10-25 while Zsolt was asleep, close to submission)

---

## REQUIREMENTS (LOCKED)

From `docs/plan.md`, B4 line, verbatim:

> **B4 Curator and deck** — `feat/curator-deck` — fixed-prompt curator on
> `gemini-3.8-flash`, deck with percentile-band exploration (seeded per user), decision
> IDs and `mreq_` IDs stored.

From `docs/decisions.md`, binding lines, verbatim:

> **Curator task shape.** The system prompt is one fixed string, never templated
> with anything but numbers or IDs. Everything per user — stated prefs, taste profile,
> lessons, past swipes, the listing — goes in the user message. Model ID and output
> schema are fixed before the first persona run; changing either restarts the count.
> Requests kept compact: structured listing fields, not raw API dumps.

> **Band:** a percentile band of the pool that passes the hard filters, never fixed
> ranks.

> **Flag:** each card carries a source flag, `ranked` or `exploration`, in the API
> payload and the logs. Never shown on the card face

> Every curator decision stores Mubit's `x-middleware-request-id` (`mreq_…`) and the
> profile version in D1

> **`gemini-3.8-flash`, frozen.** ... Fixed with the model: a low thinking setting, never
> changed, and one response schema.

> A user's correction to a flag ("not damp") is written onto the cached flag record, and the
> curator reads the corrected text.

From `docs/api-contract.md`: the `GET /deck?n=10` section (lines 166–293) and the Chip
catalogue section (lines 440–566) are binding as written, including: unswiped served cards
first with the same `decision_id`s; a listing never served twice at once; a swiped listing
never served again; about 1 in 5 cards `exploration`; chips logged at serve time;
`feedback_required` true only within the user's first 15 swipes; `empty_reason`
`exhausted` / `no_matches`; 409 `prefs_missing`; `n` an integer 1–10; re-saving prefs
drops every served, unswiped card (`PUT /prefs` section, lines 155–162).

Human answers at kickoff, 2026-10-25:

- Curator shape: "Chunked scoring (Recommended)" — each call scores a fixed 20 listings
  (0–100 + short reason); the whole filtered pool is scored once per (user, profile
  version), cached in D1.
- Split: "Train split only (Recommended)" — the deck serves only `split = 'train'`.
- Paid call: "Yes, one smoke run" — one user, one deck request, metadata only to
  `evidence/`.
- "now go build."

### Source

`docs/plan.md`, `docs/decisions.md`, `docs/api-contract.md`, human answers in chat
2026-10-25.

### Explicitly out of scope

- Swipe, feedback, favourites, flag-correction and profile endpoints (B5). B4 creates the
  `decisions` table with a nullable `swiped_at` that B5 fills; until then the swipe count
  is 0.
- The taste profile itself (B5). B4 sends an empty profile at version 0.
- Personas, batch runner, eval scoring (B6, B7).
- Any change under `web/`.
- Commute fetching (B3 owns it); B4 only reads `commute_cache`.
- Retrying failed curator chunks within one request; prompt tuning beyond a first fixed
  prompt.

---

## AMENDMENTS

- 2026-10-25, Step 4, by Yewen in chat: "Yes, amend step 4: token totals are measured
  later by storing usageMetadata; the estimate stays, labelled as one. Then re-review,
  qa-gate and commit." Step 4's done-when no longer requires measured
  prompt/output/thinking token totals; the evidence file keeps its estimate, labelled as
  an estimate. Measured totals come from a later change that stores `usageMetadata` per
  curator call (not part of B4).

---

## RULES IN FORCE

| Rule                                                                                                                                                | Source                                                | Applies to               |
| --------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- | ------------------------ |
| Commits only via `.claude/scripts/safe-commit.sh`, title only, no attribution                                                                       | `.claude/CLAUDE.md`                                   | commits                  |
| `type(scope): message` titles; scopes worker, db, api, kit                                                                                          | `.claude/CLAUDE.md`, kit-config                       | commits, PR              |
| Touch only the step's declared files                                                                                                                | `.claude/CLAUDE.md` prohibition 1                     | code, docs               |
| No new dependencies                                                                                                                                 | `.claude/CLAUDE.md` prohibition 2                     | code                     |
| Never weaken a test                                                                                                                                 | `.claude/CLAUDE.md` prohibition 3                     | tests                    |
| The ladder: write as little code as possible, reuse `mubit.py`, `filters.py`, `prefs.py`                                                            | `.claude/CLAUDE.md`                                   | code                     |
| Tradeoffs logged at the moment they are made                                                                                                        | `.claude/CLAUDE.md` prohibition 5                     | progress file            |
| Plain British English, banned words list                                                                                                            | `.claude/CLAUDE.md`                                   | comments, docs, evidence |
| Curator system prompt one fixed string; per-user data only in the user message; model `gemini-3.8-flash`; `thinkingLevel: low`; one response schema | `docs/decisions.md`, `mubit-task-design` skill        | curator code             |
| Only the Mubit key is sent; never the Gemini key                                                                                                    | `docs/decisions.md`                                   | code                     |
| Tests never reach Mubit: fake upstream on `FAKE_PORT`                                                                                               | `worker/README.md`                                    | tests                    |
| Unknown is `null`, never 0 or ""                                                                                                                    | `docs/api-contract.md`                                | API output               |
| `source` never on the card face; listing `split` never exposed                                                                                      | `docs/api-contract.md`                                | API output               |
| Evidence: metadata only, no raw response bodies                                                                                                     | `docs/decisions.md`                                   | `evidence/`              |
| Prettier hook may reformat edited files; check `git diff`                                                                                           | kit-config                                            | all edits                |
| Servers in this worktree run off the recording's ports: dev 8790 (inspector 9240), test 8791 (inspector 9241), `FAKE_PORT` 8802                     | human instruction "parallel to the current recording" | running servers          |

---

## PLAN

### Step 1 — App tables and chip selection

**Goal**: Add the `decisions`, `offered_chips` and `curator_scores` tables and a pure
`chips.py` that builds a card's `chips[]` exactly per the contract's Chip catalogue.

**Files in scope**: `worker/schema.sql`, `worker/src/chips.py`,
`worker/tests/test_chips_unit.py`

**Done when**:

- `schema.sql` has `decisions` (decision_id PK, user_id, listing_id, source in
  ranked/exploration, score, curator_request_id, profile_version, served_at, swiped_at
  NULL), `offered_chips` (decision_id, chip_id, position), `curator_scores` (user_id,
  listing_id, profile_version, score 0–100, reason, request_id, scored_at; PK user,
  listing, version). `worker/scripts/seed.sh` builds a DB with them without error.
- `chips.select(listing, stations, flags, commute_minutes)` returns at most 8 chips with
  the catalogue's exact `chip_id`, label and phrases, featured first then by priority,
  with the "once flags exist" clauses active (photo flags are in D1).
- Unit tests cover every offered rule, the terrace rule, the commute rule, the flag
  clauses and the cap/order, and pass with `uv run --group dev pytest tests/test_chips_unit.py -q`.

**Evidence location**: the diff and the unit test run output in the review note.

- [x] Implemented — worker/schema.sql tables, worker/src/chips.py, seed.sh exit 0 with 3 new tables present (2026-10-25)
- [x] Tested — evidence: uv run pytest chips/filters/prefs/mubit/tfl unit files: 150 passed, exit 0; offered/featured counts on 635 real listings match evidence/chip-catalogue/coverage.md (2026-10-25)
- [x] Best practices met — evidence: pure function, no I/O, stdlib only, reuses filters.HOUSE_TYPES; check-process-refs.sh exit 0 (2026-10-25)
- [x] Matches locked requirements — evidence: all 20 chip_ids, labels, phrases, rules, cap 8, featured-first order checked line by line against api-contract.md Chip catalogue (2026-10-25)
- [x] No scope drift — evidence: git status shows only schema.sql, chips.py, test_chips_unit.py plus the progress file (2026-10-25)

### Step 2 — Curator call

**Goal**: A `curator.py` with the one fixed system prompt, the fixed response schema,
the request body for a chunk of exactly up to 20 listings, and reply validation, plus a
curator answer in the fake upstream.

**Files in scope**: `worker/src/curator.py`, `worker/tests/fake_upstream.py`,
`worker/tests/test_curator_unit.py`

**Done when**:

- `SYSTEM_PROMPT` is a module constant with no per-user text; model is `prefs.MODEL`
  (`gemini-3.8-flash`); `generationConfig` has `temperature: 0`,
  `thinkingConfig.thinkingLevel: "low"`, JSON mime type and one `RESPONSE_SCHEMA`
  (`{scores: [{listing_id, score 0–100 integer, reason}]}`).
- The user message is JSON holding stated prefs (`hard`, `soft`), the profile
  (`{version: 0, factors: []}` until B5) and compact listings: structured fields,
  key_features, nearest stations, commute minutes, and photo flags with
  `corrected_text` used in place of the observation when set. No description dump, no
  photo URLs, no `split`.
- `parse_reply` accepts only a reply scoring every listing in the chunk exactly once with
  integer scores 0–100, else returns None.
- The fake upstream recognises a curator request (by its system prompt) and answers with
  a deterministic valid score per listing; existing prefs answers unchanged.
- Unit tests pass for body shape (system prompt identical across two different users),
  compaction, and parse_reply accept/reject cases.

**Evidence location**: the diff and the unit test run output in the review note.

- [x] Implemented — worker/src/curator.py (SYSTEM_PROMPT, RESPONSE_SCHEMA, compact_listing, build_score_body, parse_reply), fake_upstream.curator_answer (2026-10-25)
- [x] Tested — evidence: uv run pytest curator/chips/filters/prefs/mubit/tfl unit files: 173 passed, exit 0; reject cases cover bool, float, str, dup, missing, out-of-range (2026-10-25)
- [x] Best practices met — evidence: strict validation, reuses prefs.MODEL/reply_text/_int_in, stdlib only; check-process-refs.sh exit 0 (2026-10-25)
- [x] Matches locked requirements — evidence: constant system prompt, temperature 0, thinkingLevel low, one schema, corrected_text over observation, no description/URL/split/address (test_compact_listing, test_system_prompt_is_the_same_for_every_user) (2026-10-25)
- [x] No scope drift — evidence: git status shows only curator.py, fake_upstream.py, test_curator_unit.py for step 2 (2026-10-25)

### Step 3 — `GET /deck` and prefs re-save

**Goal**: Serve the deck per the contract from cached curator scores, and make `PUT
/prefs` drop unswiped decisions and the user's cached scores.

**Files in scope**: `worker/src/deck.py`, `worker/src/entry.py`,
`worker/tests/test_deck.py`, `worker/README.md`, `docs/api-contract.md` (only to add
the 502 `curator_failed` error line to `GET /deck`)

**Done when**:

- Pool = `split = 'train'` listings passing `filters.passes` (commute limit via
  `filters.load_commutes` when a postcode is saved).
- Pool listings with no `curator_scores` row for (user, profile version 0) are scored in
  chunks of 20, calls run concurrently, each score row storing its chunk's `mreq_` id. A
  failed chunk leaves its listings unscored for this request (scored on the next). If the
  pool is non-empty and nothing is scored, 502 `curator_failed`.
- Unswiped served cards come first with the same `decision_id`s; new cards fill up to `n`.
  Each new card is exploration with probability 1/5 from `random.Random(f"{user_id}:{k}")`
  where k is the user's count of decisions ever created; an exploration card is drawn
  (same RNG) from eligible listings whose rank sits between the 50th and 80th percentile
  of the scored pool, best first; else the highest-scored eligible listing. Eligible = in
  pool, scored, not swiped, not currently served.
- Each new card inserts a `decisions` row (score, `curator_request_id`, profile_version 0,
  source) and its chips into `offered_chips`.
- `feedback_required` = swiped count + card index < 15. `commute` is null with no
  postcode, else `{minutes, postcode, assumptions: "weekday, arrive 08:30, public
transport"}`. Listing object has the contract's fields; photos ordered by position.
- `empty_reason`: `no_matches` when the pool is empty, `exhausted` when every pool listing
  is swiped and none is served-unswiped, else null. 409 `prefs_missing`; 422 for `n`
  outside 1–10 or not an integer.
- `PUT /prefs` success deletes the user's unswiped decisions (and their offered chips) and
  their `curator_scores`.
- API tests against the test-mode server on 8791 with `FAKE_PORT=8802` pass, covering a
  second and third `GET /deck` call (same ids first, no duplicates, more cards past the
  first batch), the 1-in-5 share over a larger deck, the band, prefs re-save, empty
  reasons and errors; the existing suite still passes.

**Evidence location**: the diff and the pytest run output in the review note.

- [x] Implemented — worker/src/deck.py, entry.py GET /deck and drop_unswiped in PUT /prefs, 502 line in api-contract (2026-10-25)
- [x] Tested — evidence: unit 173 passed exit 0; full API suite on 8791/FAKE_PORT 8802: 282 passed exit 0; direct D1 check: 160 decisions all mreq_ and matching curator_scores.request_id, 1280 offered_chips, no orphans (2026-10-25)
- [x] Best practices met — evidence: reuses filters.passes/load_commutes, mubit.generate_content, chips.select; json_each batch queries; gather with return_exceptions; check-process-refs.sh exit 0 (2026-10-25)
- [x] Matches locked requirements — evidence: train split, chunks of 20, exploration 1/5 seeded random.Random(f"{user_id}:{k}") from 50-80% band, feedback_required, commute object, empty_reason, 409/422/502 checked in deck.py and test_deck.py (2026-10-25)
- [x] No scope drift — evidence: git status shows only deck.py, entry.py, test_deck.py, README.md, api-contract.md (502 line only) plus steps 1-2 files (2026-10-25)

### Step 4 — Real smoke run

**Goal**: One real user, one prefs save and one `GET /deck` against the real Mubit key on
port 8790, recording what it cost.

**Files in scope**: `evidence/curator-deck-smoke.md`

**Done when**: the evidence file records the date, number of curator calls, every
`mreq_` id, prompt/output/thinking token totals from `usageMetadata` (read from D1 or the
server log, not raw bodies), an estimated cost, the card count and exploration count
returned, and any chunk failures. No raw response bodies.

**Evidence location**: `evidence/curator-deck-smoke.md`

- [x] Implemented — evidence/curator-deck-smoke.md written: date, 4 curator calls (2 ok, 2 x 503), 5 mreq ids, 10 cards (2 exploration), labelled estimate (2026-10-25)
- [x] Tested — evidence: D1 re-query matches file: 40 curator_scores rows, 2 distinct request ids equal to the two success ids listed, 10 decisions, 2 exploration; check-process-refs.sh exit 0 (2026-10-25)
- [x] Best practices met — evidence: metadata only, no response bodies, grep for keys/bearer finds none; price and token sizes labelled as assumptions (2026-10-25)
- [x] Matches locked requirements — evidence: done-when as amended 2026-10-25 (token totals no longer required; estimate kept and labelled) (2026-10-25)
- [x] No scope drift — evidence: only evidence/curator-deck-smoke.md added for this step (2026-10-25)

---

## TRADEOFFS

- 2026-10-25 | all | Built by Yewen against plan.md's ownership (Zsolt) without his
  review | submission deadline, Zsolt asleep | Zsolt reviews the PR before merge.
- 2026-10-25 | 3 | First `GET /deck` for a user waits on up to 25 concurrent curator calls
  | whole-pool scores are needed for the percentile band and B7 | background scoring, if
  latency hurts the recording.
- 2026-10-25 | 3 | Adds 502 `curator_failed` to the `GET /deck` contract (additive) | the
  contract has no error for a curator outage | none needed; frontend shows `error.message`.
- 2026-10-25 | 2 | `compact_listing` reads flag and station dicts by D1 column names and
  accepts `key_features` as a list or a JSON string | the caller (step 3) has not been
  written, so the row shape is assumed from `dataset/d1/schema.sql` | step 3 passes rows
  as read from D1; adjust if it reshapes them.
- 2026-10-25 | 3 | `k` (the exploration seed counter) is the count of decisions rows that
  exist, not decisions ever created | a prefs re-save deletes unswiped rows, so the count
  drops and the same seeds repeat for the new deck | a counter column on `users`.
- 2026-10-25 | 3 | Two simultaneous `GET /deck` calls for one user can serve the same
  listing twice and score the same chunk twice | no locking from the Worker; the frontend
  asks one at a time | a unique index on (user_id, listing_id) for unswiped rows.
- 2026-10-25 | 3 | A served, unswiped card stays served even if its listing later leaves
  the pool (for example a commute limit) | it was valid when served | re-check against the
  pool on every call.
- 2026-10-25 | 3 | No API test of `exhausted` or of a deck past the first batch | no swipe
  endpoint exists until B5, so a deck stops at `n` unswiped cards; the picker's handling of
  swiped listings is unit tested instead, and the 1-in-5 share is sampled over six users |
  add API tests once swipes exist.
- 2026-10-25 | step 4 | Token totals not in the evidence; cost is an estimate from assumed sizes and price | the app stores no usageMetadata, and the approved run was a single deck request | Read exact tokens per mreq id from Mubit's Requests page, or store usageMetadata per call.

Signed off by Yewen in chat, 2026-10-25: "I sign off all 9 tradeoffs as listed."

---

## SPOTTED, NOT FIXED

- worker/src/deck.py:60-76 | Smoke run: 2 of 4 curator chunks got provider 503 and were left unscored; no retry, so a deck is built from half the pool until the next GET /deck | medium
- worker/src/entry.py PUT /prefs | Smoke run: the prefs parse call took 142 s | medium

---

## VERIFICATION

- [x] All step checkboxes ticked with evidence — 20 of 20 ticked, all dated 2026-10-25, so no order problem. Steps 1–3 give "the diff and the review note" as evidence location, which is not a durable path (`.claude/CLAUDE.md`, Progress file discipline). Their counts were reproduced by qa-gate on 2026-10-25 (173 unit, 282 API, 160 decisions with mreq_ ids). (qa-gate 2026-10-25)
- [x] Every evidence path in this file exists — `evidence/curator-deck-smoke.md`, `evidence/chip-catalogue/coverage.md` (qa-gate 2026-10-25)
- [x] Test suite run — result: backend unit 173 passed, exit 0; backend API suite on 8791 / FAKE_PORT 8802 after a fresh seed, 282 passed, exit 0; D1 after the run: 160 decisions, 0 without an mreq_ id, 35 exploration (21.9%), 1280 offered_chips, 0 orphans, 0 duplicate unswiped listings per user. Web: n/a, no web changes. (qa-gate 2026-10-25)
- [x] Lint run — result: none configured (qa-gate 2026-10-25)
- [x] Typecheck run — result: n/a, no web changes (qa-gate 2026-10-25)
- [x] Build run — result: n/a, no web changes (qa-gate 2026-10-25)
- [x] Diff contains no files outside declared scope — all 12 changed or new files are in a step's Files in scope, plus this progress file (qa-gate 2026-10-25)
- [x] Tradeoff ledger reviewed and signed off by human — all 9 signed off by Yewen in chat, 2026-10-25
- [ ] Human eye test completed — not done by a human. Yewen chose to skip it for now, 2026-10-25. Steps are in HANDOVER.

QA-GATE: FAIL 2026-10-25 — the tradeoff ledger is unsigned and the eye test is not done. No command failed.
Update 2026-10-25: ledger signed off by Yewen; eye test skipped at Yewen's choice and recorded as not human-verified.

---

## HANDOVER

**What was built**

The backend now serves a real deck. `GET /api/deck?n=10` takes a user's saved prefs,
filters the train-split listings, has the Gemini curator score the whole pool once (in
chunks of 20, through Mubit), caches the scores, and returns up to 10 cards. About one
card in five is an exploration card from the 50–80% band of the ranking. Every served
card is stored in `decisions` with its score, the `mreq_` id of the curator call, profile
version 0 and its chips. Re-saving prefs drops unswiped cards and the cached scores.

**What to check yourself**

This uses the real Mubit key from `worker/.dev.vars`, so every step below is paid.
Expect about 4 curator calls per new deck, plus one prefs parse.

1. Stop any server running from this worktree. From the worktree root run
   `worker/scripts/seed.sh`. (The qa-gate run re-seeded this D1, so the smoke run's rows
   are gone; the evidence file is the only record of them now.)
2. In `worker/`, run
   `uvx --from workers-py pywrangler dev --port 8790 --inspector-port 9240`
   with no `--var` flags. Wait for "Ready on http://localhost:8790".
3. Create a user:
   `curl -s -X POST http://localhost:8790/api/users -H 'Content-Type: application/json' -d '{"username":"eye_b4"}'`
   Note the `user_id` (`u_…`).
4. Save prefs:
   `curl -s -X PUT http://localhost:8790/api/prefs -H 'Content-Type: application/json' -H 'X-User-Id: <user_id>' -d '{"text":"2 bed flat under 600k, EPC C or better, near a tube station, bright rooms, quiet street"}'`
   This took 142 s in the smoke run. Expect 200 with `parsed.hard` and `parsed.soft`.
5. Ask for a deck:
   `curl -s 'http://localhost:8790/api/deck?n=10' -H 'X-User-Id: <user_id>' | python3 -m json.tool`
   Expect 30 s or so. You should see `empty_reason: null`, 10 cards, `decision_id`s
   starting `d_`, roughly 2 with `source: "exploration"`, `commute: null`,
   `feedback_required: true` on every card, at most 8 chips per card, photos as URLs,
   and no `split` field. Read a few listings: do the top cards fit the prefs?
6. Run step 5 again. The same 10 `decision_id`s must come back in the same order, with
   no new curator calls in the server log unless some chunks failed the first time.
7. Check D1 (in `worker/`):
   `npx wrangler d1 execute haka --local --command "SELECT source, score, curator_request_id, profile_version FROM decisions WHERE user_id='<user_id>'"`
   Every row should have an `mreq_` id and `profile_version` 0. Then
   `npx wrangler d1 execute haka --local --command "SELECT count(*), count(DISTINCT request_id), min(score), max(score) FROM curator_scores WHERE user_id='<user_id>'"`.
8. Try the errors: `?n=0`, `?n=11`, `?n=abc` should give 422 `invalid_request`; a new
   user with no prefs should give 409 `prefs_missing`.
9. Stop the server with Ctrl-C.
10. Read the 9 TRADEOFFS entries and sign or reject each one.

**Tools that will help**

- curl plus `python3 -m json.tool` for the requests above. Look at `source`, `chips`
  and `decision_id`.
- The `pywrangler dev` terminal. "Curator chunk failed" or "Curator reply unusable"
  lines show which chunks were dropped and their request ids.
- Mubit console, Requests page. Search the `mreq_` ids from step 7 for real token counts
  and cost; the app does not store them.
- `npx wrangler d1 execute haka --local --command …` for the `decisions`,
  `offered_chips` and `curator_scores` tables.

**What is not done**

- All 9 tradeoff entries are unsigned:
  1. Built by Yewen, not Zsolt (the plan's owner); Zsolt should review the PR before merge.
  2. The first deck for a user waits on up to 25 concurrent curator calls.
  3. 502 `curator_failed` added to the contract.
  4. `compact_listing` row-shape assumption. Now out of date: step 3 passes D1 rows as
     they are, so this can be closed.
  5. The exploration seed counter `k` counts existing decision rows, so after a prefs
     re-save the same seeds repeat.
  6. Two simultaneous deck calls for one user can serve a listing twice and pay to score
     a chunk twice.
  7. A served, unswiped card stays served even if its listing leaves the pool.
  8. No API test of `exhausted` or of a deck past the first batch. Step 3's done-when
     asked for both; only unit tests on the picker cover them, and no amendment records
     the change. Decide whether to accept this or amend step 3.
  9. Step 4 has no measured token totals; the cost is an estimate.
- SPOTTED, NOT FIXED: failed curator chunks are not retried (2 of 4 failed with 503 in
  the smoke run); the prefs parse took 142 s.
- No swipe, feedback or profile endpoints (B5). Until they exist a user's deck never
  moves past the first `n` cards, and the profile is always empty at version 0.
- `usageMetadata` is not stored, so cost per curator call is not known from the app.
- `worker/README.md` still lists only the four old unit files in the plain unit-test
  command; the two new unit files are mentioned in the list below it but not added to
  the command.

**What could bite you**

1. Provider 503s. Half the smoke run's chunks failed. Those listings are left out of
   the ranking and the exploration band until the next `GET /deck`, and the band is then
   cut from a partial pool, not the whole filtered pool. If every chunk fails, the user
   gets a 502. On a bad day the recording could show a thin or odd deck.
2. Cost and wait on every prefs save. A save clears all the user's cached scores, so the
   next deck rescores the whole pool: up to 25 paid calls and tens of seconds. Editing
   prefs during the recording or the persona batch pays this each time.
3. `empty_reason` can say `exhausted` when it is not true: once swipes exist (B5), a user
   who has swiped every scored listing while some chunks never scored gets `exhausted`
   instead of a retry. Not reachable until B5 lands.
