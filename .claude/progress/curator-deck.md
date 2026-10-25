# Feature: B4 Curator and deck

- **Slug**: curator-deck
- **Owner**: Zsolt
- **Started**: 2026-10-25
- **Branch**: feat/curator-deck
- **BASE_SHA**: 882efc0838383ac87a4025eb19df00d940cbc754
- **Status**: in progress
- **Mode**: full automation (on since 2026-10-24)

---

## REQUIREMENTS (LOCKED)

Human, in session, 2026-10-25: "Start" (after being offered B4).

`docs/plan.md`, Backend — Zsolt:

> **B4 Curator and deck** — `feat/curator-deck` — fixed-prompt curator on
> `gemini-3.8-flash`, deck with percentile-band exploration (seeded per user), decision
> IDs and `mreq_` IDs stored.

> **Sat 13:00** — a user can be created, swipe a real deck (with at least one
> exploration card) and give chip feedback. Curator calls show in Mubit under one task.

`docs/decisions.md`, binding lines:

> **Exploration cards.** [...] in the cut. [...] **Band:** a percentile band of the
> pool that passes the hard filters, never fixed ranks. [...] **Flag:** each card
> carries a source flag, `ranked` or `exploration`, in the API payload and the logs.
> Never shown on the card face.

> **Curator task shape.** The system prompt is one fixed string, never templated with
> anything but numbers or IDs. Everything per user — stated prefs, taste profile,
> lessons, past swipes, the listing — goes in the user message. Model ID and output
> schema are fixed before the first persona run; changing either restarts the count.
> Requests kept compact: structured listing fields, not raw API dumps.

> **Correction → model update path.** [...] Every curator decision stores Mubit's
> `x-middleware-request-id` (`mreq_…`) and the profile version in D1 [...]

> **Curator model.** [...] **`gemini-3.8-flash`, frozen.** [...] Fixed with the model:
> a low thinking setting, never changed, and one response schema. [...] Check real
> cost after the first 50 curator calls, before the persona batch.

> **Training vs evaluation split.** [...] About 25% of listings held out [...]

> **Commute (TfL).** [...] stretch goal [...] (2026-10-25)

`docs/api-contract.md`, binding sections: General, Deck (`GET /deck?n=10`, cards,
`decision_id`, `source`, `feedback_required`, chips logged at serve time,
`empty_reason`, errors), Chip catalogue (rules, chips per card, preset phrases), and
the Server-side only notes (`mreq_` and profile version per decision; `split` never
exposed).

B3 handover (`.claude/progress/prefs-filters.md`, `### B4 HOOKS`): drop unswiped served
cards on `PUT /prefs`; never wait on `commute_status`; card `commute` null without a
postcode; `matching_listing_ids_for_postcode` only with a postcode, else
`matching_listing_ids(db, hard)`; with a commute limit the deck is short or empty.

### Source

Quoted above. Plan by the `Plan` agent, 2026-10-25, checked against these lines by the
main agent. Arbiter rulings on its open questions are in KICKOFF RULINGS.

### Explicitly out of scope

- Swipe and feedback endpoints, offered-versus-chosen weighting, taste profile and its
  versions, `GET /profile`, flag corrections, favourites (B5).
- `GET /listings/{id}` (unless ruled in).
- Personas and the batch runner (B6); eval runner, eval no-store header, `/stats` (B7).
- Any change under `web/`, including the stale commute mock (already escalated).
- A commute-specific `empty_reason` value; a TfL poll cap.
- Starting Mubit training; deploy.
- Any paid Mubit call beyond one live curator test call (unless ruled otherwise).
- New dependencies.

---

## AMENDMENTS

2026-10-25 (arbiter): Step 5 added from the SPOTTED, NOT FIXED entry on `natural_light`
and `space` being featured almost everywhere once flags apply. Not a REQUIREMENTS change.

### Step 5 — Chip featured rules that separate listings (arbiter)

**Goal**: drop the two photo-flag featured clauses that match nearly every listing, so
"featured" again means the listing clearly has the feature. `natural_light` featured
when it mentions the light pattern, or a `light` flag with value `poor` and confidence
`high` or `medium` (the `bright` value is dropped: a high-confidence `bright` flag is on
all 635 listings). `space` featured on the text mention only (the `sqm_estimate` clause
is dropped: an estimate on 609 listings says nothing about size). `garden` and
`condition` flag clauses unchanged. No `chip_id`, label, phrase, priority, cap or shape
changes, so not a breaking contract change and no `web/` change.

**Files in scope**: `docs/api-contract.md` (Chip catalogue only: Chips table rows 3
and 9, and the `natural_light` and `space` rows of Photo-flag-dependent chips),
`worker/src/chips.py`, `worker/tests/test_chips.py`, `evidence/curator-deck/step-5.md`.

**Done when**: chips.py rules match the edited contract rows (the contract-table test
still passes); unit tests show a `bright` high flag alone does not feature
`natural_light`, a `poor` medium flag does, a `poor` low flag does not, and a
`sqm_estimate` flag alone does not feature `space`; the exact recount over 635 listings
with flags is re-asserted in tests and written to step-5 evidence next to the step-1
figures (featured counts for `natural_light` and `space`, featured chips per card
min/median/max, cards with more than 8 featured with and without commute); the chips
test module and the other unit modules from step 1 pass.

**Evidence location**: `evidence/curator-deck/step-5.md`

- [ ] Implemented
- [ ] Tested — evidence: (date)
- [ ] Best practices met — evidence: (date)
- [ ] Matches locked requirements — evidence: (date)
- [ ] No scope drift — evidence: (date)

2026-10-25 (arbiter): Step 6 added from the SPOTTED, NOT FIXED entry on `curator_calls.mreq_id`
having no automated test. Not a REQUIREMENTS change.

### Step 6 — Test that the stored `mreq_` id is the call's header id (arbiter)

**Goal**: an API test proves each `curator_calls` row stores the `x-middleware-request-id`
the fake upstream sent for that call, and that each decision row points at that call.
The fake sends a distinct id per curator response (e.g. `mreq_fake` + a counter or
`secrets.token_hex`) and records it in `curator_requests`, so a stored id can be matched
to its own call. The test reads the local D1 from the test process with
`subprocess.run(["npx", "--yes", "wrangler", "d1", "execute", "haka", "--local", "--json",
"--command", <SELECT with the user_id inlined after checking it is the API's id format>],
cwd=<worker dir>)` and `json.loads` — the same route `worker/scripts/seed.sh` uses. No
change to `worker/src/`, no new endpoint, no new dependency. If `wrangler` is not on the
path, the test fails with a clear message (no skip).

**Files in scope**: `worker/tests/fake_upstream.py` (distinct request id per curator
response, recorded), `worker/tests/test_deck.py` (new test(s) and a small D1-read helper),
`worker/README.md` (one line in the test list that `test_deck.py` reads the local D1 and
needs the server's D1 state in the same `worker/` directory),
`evidence/curator-deck/step-6.md`.

**Done when**: a new user's first `GET /api/deck?n=10` → exactly one `curator_calls` row
for that user, its `mreq_id` equals the id the fake sent for that call and starts `mreq_`,
its `profile_version` equals the empty-profile value from Step 3, and all 10 `decisions`
rows for the user have `curator_call_id` equal to that row's `call_id` and the same
`profile_version`; a second user's call gets a different id that does not appear on the
first user's rows; a curator-failure-marker call whose fake response carries an id stores
that id with status `failed`; the test fails when `request_id` is replaced with `None`
in the `deck.py` insert (checked once by hand, reverted, recorded in evidence); the full
suite passes in test mode on one seeded D1.

**Evidence location**: `evidence/curator-deck/step-6.md`

- [ ] Implemented
- [ ] Tested — evidence: (date)
- [ ] Best practices met — evidence: (date)
- [ ] Matches locked requirements — evidence: (date)
- [ ] No scope drift — evidence: (date)

---

## RULES IN FORCE

| Rule | Source | Applies to |
| ---- | ------ | ---------- |
| Commits only via `.claude/scripts/safe-commit.sh`, title only, no signature | `.claude/CLAUDE.md` | commits |
| Commit/PR title `type(scope): message`; scopes: worker, web, db, prep, kit, api | `.claude/CLAUDE.md`, kit-config | commits, PR |
| No scope creep: touch only the step's declared files | `.claude/CLAUDE.md` #1 | code, docs |
| Dependencies: only `fastapi`, `google-genai`, `pytest` | `.claude/CLAUDE.md` #2, kit-config | code |
| Never weaken a test to pass | `.claude/CLAUDE.md` #3 | tests |
| Walk the ladder; no speculative generalisation | `.claude/CLAUDE.md` #4 | code |
| Tradeoffs logged inside `## TRADEOFFS` when made; arbiter rules | `.claude/CLAUDE.md` #5, Modes | progress file |
| Only step-reviewer ticks, with evidence and date | `.claude/CLAUDE.md` #6 | progress file |
| Out-of-scope problems go in SPOTTED, NOT FIXED | `.claude/CLAUDE.md` #7 | progress file |
| Plain British English, no banned marketing words | `.claude/CLAUDE.md` | docs, comments |
| Error body `{"error": {"code", "message"}}`; unknown is `null`; `split` never exposed | `docs/api-contract.md` | code |
| A breaking change to the contract escalates; any change under `web/` escalates | `.claude/CLAUDE.md` Modes | docs, code |
| Curator system prompt is one fixed string; per-user data only in the user message; model, schema and thinking fixed | decisions (Curator task shape, Curator model) | code |
| `mreq_` and profile version stored per decision | decisions (Correction path) | code |
| Automated tests never reach Mubit: API test modules use the `fake` fixture (probe guard) | prefs-filters TRADEOFFS (arbiter) | tests |
| No paid call beyond one live curator test call | `.claude/CLAUDE.md` Modes | commands |
| Evidence is metadata only, under `evidence/curator-deck/`, subject-language headings | `.claude/CLAUDE.md`, decisions (Evidence) | evidence |
| Stop only processes you started, by PID; no pkill patterns | session (permission denial, 2026-10-24) | commands |
| Run the merge guard from `main`, never from a feature branch checkout | session (2026-10-25) | merge |

---

## PLAN

All paths relative to the repo root. Design detail is in the Plan agent's report,
quoted in each brief.

### Step 1 — Chips per card

**Goal**: implement the Chip catalogue rules with the photo-flag clauses active; output
the ordered `chips[]` for a listing (cap 8, featured first, then priority; commute chip
only when minutes are not null).

**Files in scope**: `worker/src/chips.py` (new), `worker/tests/test_chips.py` (new),
`docs/api-contract.md` ("Photo-flag-dependent chips" wording only),
`evidence/curator-deck/step-1.md`.

**Done when**: unit tests (no server) cover every chip's offered and featured rule, the
bare-`terrace` rule, the cap and ordering, and that `corrected_text` never changes the
chips; a recount over all 635 listings with flags is in evidence, next to the
pre-flag numbers in `evidence/chip-catalogue/coverage.md`.

**Evidence location**: `evidence/curator-deck/step-1.md`

- [x] Implemented — worker/src/chips.py rules match contract Chips table row by row; test_catalogue_matches_contract_chip_table (2026-10-25)
- [x] Tested — evidence: pytest chips+filters+prefs+mubit+tfl 137 passed exit 0; test_chips.py per-rule, cap, order, corrected_text, exact recounts over 635 (2026-10-25)
- [x] Best practices met — evidence: pure functions, no I/O, no new deps, check-process-refs.sh exit 0 (2026-10-25)
- [x] Matches locked requirements — evidence: contract Chip catalogue rules and Chips per card (featured first, priority, cap 8, commute only if minutes not None) (2026-10-25)
- [x] No scope drift — evidence: diff = chips.py, test_chips.py, contract Photo-flag-dependent hunk only, evidence/curator-deck/step-1.md (2026-10-25)

### Step 2 — Curator request and reply (pure), fake curator

**Goal**: the fixed curator call — system prompt, response schema, low thinking,
user-message builder — plus reply parsing and repair; the fake upstream answers
curator calls.

**Files in scope**: `worker/src/curator.py` (new), `worker/tests/test_curator_unit.py`
(new), `worker/tests/fake_upstream.py`, `evidence/curator-deck/step-2.md`.

**Done when**: unit tests prove two different users produce byte-identical
`systemInstruction` and `generationConfig`; `thinkingConfig` explicit; repair drops
unknown and duplicate ids and appends missing candidates last, marking the call
incomplete; corrected flag text replaces the value; evidence has the SHA-256 of the
frozen prompt and schema and request-size figures over 3–4 real train pools.

**Evidence location**: `evidence/curator-deck/step-2.md`

- [x] Implemented — curator.py: fixed SYSTEM_PROMPT, RESPONSE_SCHEMA, GENERATION_CONFIG, build_body, parse_ranking; fake answers curator calls (2026-10-25)
- [x] Tested — evidence: pytest 6 pure modules 163 passed exit 0; full suite 247 passed exit 0 in fresh worktree on :8792, fake :8801; SHA-256s recomputed 9b5a064b.../10a031b5... match (2026-10-25)
- [x] Best practices met — evidence: pure functions, CuratorError on unusable reply, half-valid rule, no new deps, check-process-refs.sh exit 0 (2026-10-25)
- [x] Matches locked requirements — evidence: test_two_users_share_system_instruction_and_generation_config_byte_for_byte, test_thinking_is_explicit_low, test_schema_is_a_plain_string_array_with_no_enum, repair tests match Q3 (2026-10-25)
- [x] No scope drift — evidence: diff = curator.py, test_curator_unit.py, fake_upstream.py (curator branch only), evidence/curator-deck/step-2.md, progress tradeoffs (2026-10-25)

**Redo (arbiter FIX_NOW, 2026-10-25)**: corrected light flags win their room. Files:
`worker/src/curator.py`, `worker/tests/test_curator_unit.py`,
`evidence/curator-deck/step-2.md`. In `_flag_digest`, a light flag with
`corrected_text` wins its room over uncorrected readings; several corrections → most
frequent corrected value, then first in flag order; no corrections → current rule.
SYSTEM_PROMPT, RESPONSE_SCHEMA and GENERATION_CONFIG unchanged (hashes still match).

- [x] Redo implemented — _flag_digest pick(room, values): corrected light wins its room; test_correction_wins_its_room_over_more_numerous_readings, test_several_corrections_take_the_most_frequent_then_the_first (2026-10-25)
- [x] Redo reviewed — evidence: 6 pure modules 166 passed exit 0; new tests fail on HEAD curator.py (2 failed), uncorrected tie test passes both; SHA-256 9b5a064b/10a031b5 recomputed; dataset 14684/14684 corrected_text null; check-process-refs exit 0 (2026-10-25)


### Step 3 — `GET /deck` end to end, `PUT /prefs` drop hook

**Goal**: a user with prefs gets a real deck: decisions and curator-call rows with the
`mreq_` id, offered chips logged, exploration cards in the band, unswiped cards
re-served first; a re-save drops unswiped cards.

**Files in scope**: `worker/schema.sql`, `worker/src/deck.py` (new),
`worker/src/entry.py`, `worker/tests/test_deck.py` (new), `worker/README.md` (test
list and layout), `evidence/curator-deck/step-3.md`.

**Done when**: API tests (test mode, `fake` fixture) show 409 `prefs_missing`; 422 for
`n` = 0, 11, `abc`; `n=10` gives 10 cards with exactly 2 exploration at positions 5
and 10, each in the band of the fake's ranking; no eval-split listing served across
many users; no listing served twice to a user; a refetch returns the same
`decision_id`s first with no new curator call; after a re-save no old `decision_id`
reappears; the curator failure marker gives the ruled failure response and no
decisions (or a 200 with only outstanding cards); `commute` null with no postcode;
with a postcode, limit and pending status the deck is short or empty `no_matches`; at
most 8 chips per card; `feedback_required` true for the first 15 positions; the full
suite passes twice on one seeded D1.

**Evidence location**: `evidence/curator-deck/step-3.md`

- [x] Implemented — deck.py serve/place/_ask_curator, schema curator_calls+decisions, GET /api/deck, drop hook after upsert in put_prefs; diff read (2026-10-25)
- [x] Tested — evidence: fresh worktree+seed, :8794 fake :8803: 6 pure modules 166 passed exit 0; full suite 275 passed exit 0 twice on one D1; test_deck.py 25 tests cover each Done-when item except exhausted and post-15 feedback_required (logged tradeoff, unreachable pre-swipe) (2026-10-25)
- [x] Best practices met — evidence: bound params throughout, train-only pool in SQL, CuratorError path recorded with mreq_id, split/commute_status absent from responses, monkeypatch undone by pytest, probe-guard pytestmark present, check-process-refs exit 0 (2026-10-25)
- [x] Matches locked requirements — evidence: card keys match contract example; Q1-Q11 and exploration-slot ruling implemented (deck.py place, BAND, K=30); mreq_ and profile_version 0 stored per call and decision; curator.py unchanged, prompt SHA 9b5a064b matches (2026-10-25)
- [x] No scope drift — evidence: diff = schema.sql, deck.py, entry.py, test_deck.py, README.md, step-3 evidence, progress tradeoffs (2026-10-25)

**Redo (arbiter FIX_NOW, 2026-10-25)**: one deck build per user at a time. Files:
`worker/src/deck.py`, `worker/tests/test_deck.py`, `evidence/curator-deck/step-3.md`.
A module-level per-user `asyncio.Lock` held for the whole of `serve`, so overlapping
requests for one user make at most one curator call. — withdrawn by arbiter 2026-10-25:
the lock cannot work on workerd (a request cannot await a promise resolved in another
request's I/O context; the waiting request is cancelled and returns 500), and the
working alternative, a D1 claim row with polling and stale-claim expiry, is a schema
change plus a polling loop for a dev-only cost. The duplicate is about £0.005–0.008 per
deck load that needs new cards, only under React StrictMode in dev; no duplicate card is
served (unique pair); the persona batch, which supplies most kept examples, is
serialised by B6. Nothing in the plan or a checkpoint is blocked. Code reverted to the
reviewed Step 3; its boxes removed by the arbiter (nothing was built, so nothing to
verify, and open boxes would block Step 4). The tested attempt is not in the repo.


### Step 4 — Live check, contract and README

**Goal**: one real curator call through Mubit from the endpoint, `mreq_` stored,
tokens, latency and cost measured; the ruled contract additions and README notes.

**Files in scope**: `docs/api-contract.md` (Deck errors; Server-side only note on
train-only decks), `worker/README.md` (curator, paid call, cost note),
`evidence/curator-deck/step-4.md`, this progress file (`## HANDOVER` notes only:
rulings Q4, Q8 and the Step 3 concurrency conditions).

**Done when**: one `GET /deck` against the normal dev server returns cards; the
`curator_calls` row carries the same `mreq_` id as the response header; usage tokens
recorded; evidence gives cost per call at stated price assumptions and a persona-batch
projection; the prefs row for the test is inserted locally so the parse call is not
paid.

**Evidence location**: `evidence/curator-deck/step-4.md`

- [x] Implemented — evidence: contract (Deck errors 502, Server-side only), worker/README.md 'Curator and deck', HANDOVER notes, evidence/curator-deck/step-4.md present (2026-10-25)
- [x] Tested — evidence: one live GET /api/deck?n=10 200 in 5.29s, 1 curator_calls row ok, mreq_ stored (read from x-middleware-request-id, src/mubit.py:34,60), tokens 6995/335; test_curator_unit 29 pass, offline modules 38 pass; check-process-refs exit 0 (2026-10-25)
- [x] Best practices met — evidence: evidence is metadata only, no key or bodies; contract change additive; no web/ change (2026-10-25)
- [x] Matches locked requirements — evidence: Done-when met in intent (stored mreq_ is header-sourced; endpoint does not expose the header; console not opened); cost per call at two price assumptions plus 150/1000 projection (2026-10-25)
- [x] No scope drift — evidence: git diff HEAD = contract, README, progress file (HANDOVER, arbiter edits only), untracked step-4.md; REQUIREMENTS and ticked boxes untouched (2026-10-25)

---

## KICKOFF RULINGS

Q1: Candidate set K=30, a per-user seeded sample of the train-only hard-filter pool minus every listing the user has a live decision for; one curator call per `GET /deck` that needs new cards, none when outstanding cards cover `n`; K is a constant, revisited only before the first persona run — arbiter 2026-10-25: train pools are 59–145, so ranking the whole pool per call would blow request size against "Requests kept compact"; K only changes the user message, so it never splits the Mubit task. The band is then a percentile of a random sample of the pool, an estimate of the pool's band; log that as a TRADEOFF in step 3.
Q2: Yes, eval-split listings are never served to any user — arbiter 2026-10-25: decisions.md (Training vs evaluation split) holds them out of training, and every live curator call is a potential kept example; team swipes feed training. B7 must keep eval-time curator calls out of the kept examples (record-off header if Mubit supports it, or run after training) — B7 work, not B4.
Q3: Failed call recorded in `curator_calls` with no `mreq_` if none came back; 200 with only outstanding cards if any, else 502 `curator_failed`; no retry, no random fallback. A reply is repaired (unknown and duplicate ids dropped, missing candidates appended last, call marked incomplete) only if at least half the candidates came back valid; below that it counts as failed — arbiter 2026-10-25: a new error code is additive, not breaking, and web shows any contract-shaped message, so no `web/` change; random cards labelled `ranked` would poison the logs; the half threshold stops a near-empty reply filling the exploration band with unranked cards.
Q4: No `GET /listings/{id}` in B4 — arbiter 2026-10-25: not in the B4 plan line, not needed for Sat 13:00, and no web component calls `getListing` yet (only `web/src/api/http.ts` defines it). Neither the B4 nor the B5 plan line names it, so the B5 kickoff must decide it; step 4 writes this into HANDOVER.
Q5: `feedback_required` = (count of the user's decisions with `swiped_at` set) + (0-based position in this response) < 15 — arbiter 2026-10-25: matches the contract ("first 15 swipes"; a hint, swipe response authoritative); 15 sits inside decisions.md's 15–20.
Q6: Output schema frozen as an ordered list of listing id strings only, no reasons or scores. The schema is static: a plain string array, never a per-call enum of candidate ids — arbiter 2026-10-25: nothing in the cut needs reasons (rejection-reason accuracy is stretch), short output is cheaper and easier for the adapter to match; a per-call enum would change the output format on every call and split the task (mubit-task-design, "What makes one task").
Q7: 50th–80th percentile of the curator's ranking of the sampled candidates, recomputed per call by the live curator, is a reversible default and does not settle the decisions.md open item — arbiter 2026-10-25: the open item concerns how the live exploration metric is read, not how cards are drawn, and the headline eval uses no exploration cards. Condition that keeps it open: every `curator_calls` row stores the sampled candidate ids and the full returned order, so a fixed-baseline-band metric can still be computed later. If the band is empty (tiny pool, e.g. under a commute limit), the slot gets a ranked card.
Q8: No extra live calls in B4. Step 4 makes exactly one live curator call. The "one task in Mubit" check is not verified live in B4; step 2's byte-identical `systemInstruction` and `generationConfig` test is the code-level proof. Step 4 writes into HANDOVER that a human must open Mubit Tasks after the first few real curator calls and confirm one curator task before the persona batch starts — arbiter 2026-10-25: more than one paid test call is an escalation trigger and nothing in B4 depends on it; the persona batch escalates to the human anyway (spend), so the console check rides on that sign-off.
Q9: Hard delete of the user's unswiped decisions inside `PUT /prefs`, with their offered-chip log rows deleted with them (no orphans) — arbiter 2026-10-25: settled by B3 ruling Q10; the contract returns dropped cards to the pool; `curator_calls` keeps the ranking provenance; a chip offered on a card never swiped had no chance to be chosen, so dropping it from the offered count is the honest denominator for B5.
Q10: Yes, `description` is left out of the candidate payload; `key_features`, structured fields and a photo-flag digest only — arbiter 2026-10-25: decisions.md "Requests kept compact: structured listing fields, not raw API dumps"; 30 × 2.1k chars would add about 16k tokens per call. It lives in the user message, so it can be revisited without restarting the task count.
Q11: Yes, the user message carries `taste_profile` and `recent_feedback` slots, empty in B4, and the frozen system prompt describes them now. Each decision row stores the profile version used (empty-profile value fixed in step 3 and stated in evidence) — arbiter 2026-10-25: the system prompt is frozen with the schema, so if it does not mention these inputs now, B5 would need a prompt change and restart the task count; profile version per decision is a binding decisions.md line.
Exploration slots: a new card is `exploration` when (user's decision count before it + its index among new cards) % 5 == 4; re-served outstanding cards keep their stored `source`; the pick within the band is seeded per user — arbiter 2026-10-25: fits "about 1 in 5", "percentile band", "seeded per user" and the source flag in decisions.md and the contract. Knock-on for B6 (not B4): the persona swiper must never pass `source` to the persona LLM, since the fixed slot would otherwise be a tell.

---

## TRADEOFFS

2026-10-25 | step 1 | Chip rules read flags loosely where the contract is silent: any flag row with room `garden`, any `defects` or `sqm_estimate` row regardless of value or confidence | The contract gives a confidence condition only for `light`; adding others would invent rules | Tighten the contract wording (for example ignore `low` confidence or a defects value of none) and update the two rules and tests; about 20 lines. — accepted by arbiter 2026-10-25: the readings are the literal contract text, and the data shows tightening would change almost nothing (garden: 335 listings either way when restricted to `field` `room` with high/medium confidence; defects: 159 to 155 listings when `low` is dropped, and no defects value means "none"). Not worth a contract change.

2026-10-25 | step 2 | The light digest keeps one value per room (the most frequent, a tie going to the worse reading), and defects, size tricks and missing items are listed without their confidence; low-confidence flags are not filtered | The brief asked for a compact digest and the contract sets no confidence rule for the curator | Add a confidence filter or counts per room and update the digest tests; about 15 lines. The prompt would not change, but the user message would. — accepted by arbiter 2026-10-25: in `dataset/photo_flags.jsonl` only 36 of about 15,000 flags are `low` (33 defects, 2 size tricks, 1 missing) and no `light` flag is, so a confidence filter would change almost nothing; one light value per room is the compact digest asked for. The one real gap, a user correction being outvoted in its room, is ruled FIX_NOW under the SPOTTED row for curator.py:63.

2026-10-25 | step 2 | Request size is about 6,000 tokens per call at K=30 before any taste profile or feedback; measured on characters divided by four, not a tokeniser | Compactness was asked for and 6k is lean for 30 candidates, but the real count is only known from `usageMetadata` | Step 4's live call records the true prompt tokens; shrink K or the digest if the cost projection is too high. — accepted by arbiter 2026-10-25: an estimate is enough to build on; Step 4 already must record `usageMetadata` tokens and a persona-batch cost projection, and K and the digest live in the user message, so shrinking them later does not split the Mubit task.

2026-10-25 | step 3 | The exploration band is a percentile (50th to 80th) of the curator's ranking of a K=30 random sample of the pool, not of the whole pool (arbiter ruling Q1) | Ranking the whole pool (59 to 145 train listings) per call would blow the request size; the band is an estimate of the pool's band | Rank the whole pool in chunks and merge, or fix the band from a baseline ranking; needs a prompt-visible design change and a decision on the open exploration-metric item. — accepted by arbiter 2026-10-25: this is kickoff ruling Q1 as ruled; the fix would need the open exploration-metric item in decisions.md settled (an escalation), the headline eval uses no exploration cards, and Q7's condition holds (every `curator_calls` row stores the sampled ids and full ranking, so a whole-pool or fixed-baseline band can be computed later).

2026-10-25 | step 3 | `exhausted` and `feedback_required` false after 15 swipes have no API-level test | Unswiped cards are re-served and a page holds 10, so no user can empty the pool or pass 15 swipes before the swipe endpoint exists | Add both tests with the swipe step; `empty_reason` logic is three lines in `deck.serve`. — accepted by arbiter 2026-10-25: genuinely unreachable before the swipe endpoint, and nothing in B4 depends on it. B5's kickoff must require, as Done-when items of its swipe step: (1) an API test that swipes through a user's whole train pool and then gets `exhausted` with no cards and no curator call, distinct from `no_matches`; (2) an API test that after 15 swipes every card has `feedback_required` false, and a boundary test where a page served after 12 swipes has true at positions 0–2 and false from position 3; (3) both in `worker/tests/test_deck.py` or the B5 swipe test module, with the `fake` fixture.

2026-10-25 | step 3 | A `GET /deck` that fails part-way through inserting a page leaves the cards inserted so far, and two concurrent requests for one user can each make a curator call (the unique pair keeps one row per listing, so no duplicate is served) | D1 writes here are sequential `run()` calls; a batch or transaction API is not used | Insert the page in one D1 batch; serialise per user if the persona batch fires concurrent deck requests. — FIX_NOW by arbiter 2026-10-25: redo of Step 3 within its files. Not because of B6 but because of `web/`: `web/src/main.tsx` wraps the app in `StrictMode` and `web/src/deck/useDeck.ts` fetches the deck from an effect, so every deck load in dev fires two concurrent `GET /deck` for one user — two paid curator calls, near-duplicate kept examples in the Mubit task, and overlapping `first_slot`/positions. Fix is a per-user `asyncio.Lock` around `deck.serve`'s read-then-write; the partial-page-on-failure half is accepted (rows are individually valid, re-served next time, one extra call at worst; a D1 batch through Pyodide is not worth the risk). B6's kickoff must require the persona swiper to keep at most one `GET /deck` in flight per persona. — FIX_NOW withdrawn; accepted by arbiter 2026-10-25: the per-user `asyncio.Lock` fails on workerd (the waiting request is cancelled as hung, 500), and a D1 claim row with polling is a schema change and new failure modes for a dev-only cost of about £0.005–0.008 per StrictMode double fetch that needs new cards. No duplicate card is ever served (unique pair); the second build only adds extra outstanding cards that are served later. Near-identical kept examples from team dev use are few next to the persona batch. Conditions: (1) B6's kickoff must require one `GET /deck` in flight per persona (unchanged); (2) Step 4's HANDOVER must state that a dev-mode deck load can make two curator calls and that the recording should be run with this in mind; (3) the fix, if ever wanted, is in `web/` (dedupe the doubled effect), which is Yewen's and escalates in automation.

---

## SPOTTED, NOT FIXED

- docs/api-contract.md (Chip catalogue, `natural_light` and `space` featured rules) | With flags, `natural_light` is featured on 635 of 635 listings and `space` on 623 of 635, so "featured" no longer separates listings and the cap cuts by priority number instead (featured chips exceed 8 on 254 of 635 cards, was 117). Evidence: `evidence/curator-deck/step-1.md` | low to medium (product quality of chip choice, not correctness) — FIX_NOW by arbiter 2026-10-25: Step 5 (arbiter) in AMENDMENTS.
- worker/src/curator.py:63 (light tie-break, step-reviewer note on Step 2) | A corrected free-text light value not in `_LIGHT_ORDER` gets key 1 and wins every tie (above `none`), untested. Wider problem found by the arbiter: a single corrected light flag is dropped whenever the room has more uncorrected readings (e.g. three `bright` and one corrected "not bright at all" gives `bright`), so the curator never reads the correction, against decisions.md (Photo flags: "the curator reads the corrected text") | medium (B5 corrections would be invisible to the curator) — resolved by Step 2 redo 2026-10-25 — FIX_NOW by arbiter 2026-10-25: redo of Step 2 within its files; a corrected light value in a room wins over uncorrected readings, ties among enum readings still go to the worse one; must land before the first persona run.
- worker/src/deck.py:108–113 (`curator_calls.mreq_id` write, step-reviewer note on Step 4) | No pytest asserts that `curator_calls.mreq_id` holds the `x-middleware-request-id` of the curator call that produced it. `tests/test_mubit.py` covers reading the header; the write in `deck._ask_curator` is covered only by a manual D1 inspection (Step 3 evidence) and the one live row (Step 4 evidence). The fake sends one constant id, so even a D1 read could not tell one call's id from another's. The line is in REQUIREMENTS (LOCKED) and the B4 plan line ("`mreq_` IDs stored"), and the correction trail for the recording and B7 depends on it | medium (an unguarded locked requirement; a later edit to `deck.py` could drop or misattribute the id silently) — FIX_NOW by arbiter 2026-10-25: Step 6 (arbiter) in AMENDMENTS. About 40 lines, stdlib plus the `npx wrangler d1 execute haka --local` route `worker/scripts/seed.sh` already uses; no new dependency, no new endpoint.

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

### Notes for later features

- Q4: `GET /listings/{id}` is not built in B4. The B5 kickoff decides it (neither the B4 nor the B5 plan line names it; only `web/src/api/http.ts` defines `getListing`).
- Q8: before the persona batch, a human opens Mubit's Tasks page after the first few real curator calls and confirms there is ONE curator task. The live check in B4 made one call and did not look at the console.
- A dev deck load can make two curator calls: `web/src/main.tsx` uses StrictMode and the deck is fetched from an effect, so two concurrent `GET /deck` fire for one user. Both are paid and both become kept examples. Keep this in mind when recording. The fix, if wanted, is in `web/` (Yewen's, escalates in automation).
- B6 must keep at most one `GET /deck` in flight per persona and never pass `source` to the persona LLM (the fixed exploration slot would be a tell).
- B5 kickoff must add the `exhausted` and post-15 `feedback_required` tests listed in the Step 3 TRADEOFFS row.
- Measured in B4: one live call is 6,995 prompt and 335 output tokens, about 0.002 GBP at an assumed price (evidence/curator-deck/step-4.md). Read the real price from the bill after the first 50 calls.
