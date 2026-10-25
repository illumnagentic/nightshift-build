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

- [ ] Implemented
- [ ] Tested — evidence: (date)
- [ ] Best practices met — evidence: (date)
- [ ] Matches locked requirements — evidence: (date)
- [ ] No scope drift — evidence: (date)

### Step 4 — Live check, contract and README

**Goal**: one real curator call through Mubit from the endpoint, `mreq_` stored,
tokens, latency and cost measured; the ruled contract additions and README notes.

**Files in scope**: `docs/api-contract.md` (Deck errors; Server-side only note on
train-only decks), `worker/README.md` (curator, paid call, cost note),
`evidence/curator-deck/step-4.md`.

**Done when**: one `GET /deck` against the normal dev server returns cards; the
`curator_calls` row carries the same `mreq_` id as the response header; usage tokens
recorded; evidence gives cost per call at stated price assumptions and a persona-batch
projection; the prefs row for the test is inserted locally so the parse call is not
paid.

**Evidence location**: `evidence/curator-deck/step-4.md`

- [ ] Implemented
- [ ] Tested — evidence: (date)
- [ ] Best practices met — evidence: (date)
- [ ] Matches locked requirements — evidence: (date)
- [ ] No scope drift — evidence: (date)

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

---

## SPOTTED, NOT FIXED

- docs/api-contract.md (Chip catalogue, `natural_light` and `space` featured rules) | With flags, `natural_light` is featured on 635 of 635 listings and `space` on 623 of 635, so "featured" no longer separates listings and the cap cuts by priority number instead (featured chips exceed 8 on 254 of 635 cards, was 117). Evidence: `evidence/curator-deck/step-1.md` | low to medium (product quality of chip choice, not correctness) — FIX_NOW by arbiter 2026-10-25: Step 5 (arbiter) in AMENDMENTS.
- worker/src/curator.py:63 (light tie-break, step-reviewer note on Step 2) | A corrected free-text light value not in `_LIGHT_ORDER` gets key 1 and wins every tie (above `none`), untested. Wider problem found by the arbiter: a single corrected light flag is dropped whenever the room has more uncorrected readings (e.g. three `bright` and one corrected "not bright at all" gives `bright`), so the curator never reads the correction, against decisions.md (Photo flags: "the curator reads the corrected text") | medium (B5 corrections would be invisible to the curator) — FIX_NOW by arbiter 2026-10-25: redo of Step 2 within its files; a corrected light value in a room wins over uncorrected readings, ties among enum readings still go to the worse one; must land before the first persona run.

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
