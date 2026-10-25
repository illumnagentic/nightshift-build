# Feature: B3 Preferences and filters

- **Slug**: prefs-filters
- **Owner**: Zsolt
- **Started**: 2026-10-24
- **Branch**: feat/prefs-filters
- **BASE_SHA**: 0755bcb39f9d837b2b4285cd495adf7101cea35d
- **Status**: complete (2026-10-25)
- **Mode**: full automation (on since 2026-10-24)

---

## REQUIREMENTS (LOCKED)

Human, in session, 2026-10-24: "start backend build, with full auto mode", then
"Continue" after B1 merged.

`docs/plan.md`, Backend — Zsolt:

> **B3 Preferences and filters** — `feat/prefs-filters` — natural-language prefs
> to hard limits + soft prefs, hard filters in code, TfL commute cached per
> (listing, postcode).

`docs/decisions.md`, binding lines:

> **Commute (TfL).** [...] The user enters one location (workplace or anywhere else).
> The TfL Journey Planner API returns the commute time between that location and each
> property. A calculated fact, not an LLM guess.
> - **Input:** postcode. Free-text place names make TfL return candidate matches
>   instead of a journey.
> - **Assumptions:** weekday, arrive 08:30, public transport. Shown next to the time
>   on the card.
> - **When:** once when the location is saved, for every listing that passes the other
>   hard filters, cached in D1 per (listing, location) pair. Never during a swipe.
> - **Max commute:** if the user states a limit, it is a hard filter enforced in code.
>   Otherwise commute is a factor the curator weighs.
> - **Volume:** personas share about 5 destinations so the cache does most of the work.

> **Accounts.** [...] **Username only, no passwords.** Pick or create a user; the API
> takes the user_id.

> **Which calls go through Mubit.** Every LLM call: curator, photo flags, preference
> parsing, personas, lesson summariser. Only the **curator** is trained.

> **Headline metric.** [...] **Hard-constraint violations:** enforced in code, asserted
> zero, one line in the pitch, not charted.

`docs/api-contract.md`, binding sections: General (`X-User-Id` on every endpoint except
`GET /users`, `POST /users`, `GET /stats`; missing or unknown id → 401 `unknown_user`;
error shape; unknown is `null`), Preferences (`GET /prefs`, `PUT /prefs`, the `parsed`
shape with `hard` and `soft`, `commute_status` `pending` / `ready` / `failed`, 422
`invalid_postcode`, 422 `invalid_request` for missing or blank `text` or missing
`commute_postcode`), Enums and nullability.

### Source

Quoted above. Contract: `docs/api-contract.md` on `main` at `0755bcb`. Plan by the
`Plan` agent, 2026-10-24, checked against these lines by the main agent.

### Explicitly out of scope

- `GET /deck`, the curator, exploration bands, `decision_id`s, the decisions table,
  and the deck's 409 `prefs_missing` / `commute_pending` / `commute_failed` (B4).
- "Re-saving prefs drops unswiped served cards": needs B4's decisions table. B4 adds
  it to `PUT /prefs`.
- The card `commute` object, chips and chip logging (B4).
- Photo flags and flag corrections (B2 photo-flags, B5).
- Swipes, feedback, profile, favourites (B5). Personas, eval, stats (B6, B7).
- Anything under `web/`.
- Pre-warming the commute cache for persona destinations.
- A TfL app key (a new secret; escalates if the pilot shows it is needed).
- New dependencies. No httpx, no `google-genai`.
- Any paid LLM call beyond one live parser test call.

---

## AMENDMENTS

2026-10-24 — Step 5 (arbiter) — move the pure tfl.py unit tests to a server-less module.
- **Goal**: `test_classify_answers` and `test_url_and_next_tuesday` run without a dev
  server, so the unit-only run covers `tfl.py`.
- **Files**: `worker/tests/test_tfl_unit.py` (new), `worker/tests/test_commute.py`,
  `worker/README.md` (only the unit-only test line, to list the new module).
- **Done when**: the two tests live in `test_tfl_unit.py` unchanged (no assertion
  removed or loosened) and are gone from `test_commute.py`; `test_commute.py` keeps
  `pytestmark = pytest.mark.usefixtures("fake")`; the unit-only run (`test_filters.py`,
  `test_prefs_unit.py`, `test_mubit.py`, `test_tfl_unit.py`) passes with no server;
  the full suite passes in test mode; README's unit-only line lists the new module.
- **Evidence location**: `evidence/prefs-filters/step-5.md`

  Tracked as `### Step 5` in PLAN, where its boxes live (the step-order hook reads PLAN headings).

2026-10-24 — Step 6 (arbiter) — one failing listing must not fail the postcode; TfL modes; FAKE_PORT in README.
- **Goal**: a listing TfL keeps failing is left unknown and the postcode still reaches
  `ready` (contract, Preferences: "A TfL failure for a single listing is not `failed`"),
  while a non-existent postcode still ends `failed` (ruling Q7) and a 429 never counts
  (step 3 tradeoff). Rule, in `tfl.run_batch`: (a) when the poll's fail streak is above
  0, the batch starts at offset `(streak * BATCH_SIZE) % len(todo)`, wrapping, so
  persistently bad listings at the head of the id order cannot stall the batch; (b) when
  the streak reaches `FAIL_STREAK_LIMIT`, `failed` if `commute_cache` has no row for
  this postcode; otherwise one control call re-asks the cached listing for this postcode
  (lowest `listing_id`, non-null minutes first): 429 → `pending`; transient → `failed`
  (TfL is down, not the listings); answered → `ready` (streak 0) once every remaining
  listing has been in a failing batch (`streak * BATCH_SIZE >= len(todo)`), else
  `pending` and the rotation continues. No per-listing counters, no schema change.
  (Rule (b) replaced by arbiter 2026-10-24 after the second QA-GATE FAIL: the earlier
  "ready if any cached row" ended `ready` during a TfL outage. See Step 6, Redo 2.) Also: record what TfL's default modes are (TfL API docs or
  one free anonymous TfL call reading the leg modes); add an explicit `mode=` parameter
  to `build_url` only if the default includes non-public modes (cycle, taxi, car);
  otherwise state the check in the module docstring. README test-mode section names
  the `FAKE_PORT` override that `conftest.py` reads (default 8799).
- **Files**: `worker/src/tfl.py`, `worker/tests/fake_upstream.py`,
  `worker/tests/test_commute.py`, `worker/tests/test_tfl_unit.py` (only if the URL
  changes), `worker/README.md` (test-mode section only).
- **Done when**: new tests in `test_commute.py` against the fake, each on a fresh
  postcode, show: (1) one listing in the pool that always answers 500 → polls end
  `ready`, that listing has no cache row (or a null) and every other pool listing is
  cached; (2) the first `BATCH_SIZE + 1` pool listings in id order (GOOD pool) always
  answer 500 → polls end `ready` and every other pool listing is cached; (3) an outward
  code whose every journey answers HTTP 300 (the pilot's non-existent postcode answer)
  → `["pending", "pending", "failed"]`. Existing tests pass unchanged, including
  `test_persistent_failure_ends_failed_after_three_polls` and
  `test_rate_limit_alone_never_fails_the_commute`; no assertion removed or loosened.
  The fake's per-listing failure is keyed on the start coordinates and reset after each
  test. Full suite passes in test mode; server-less run passes; TfL mode finding
  recorded in the evidence file; README mentions `FAKE_PORT`. HANDOVER "What could
  bite you" items 1 and 3 are then out of date and are rewritten by the main agent.
- **Evidence location**: `evidence/prefs-filters/step-6.md`

  Tracked as `### Step 6` in PLAN, where its boxes live (the step-order hook reads PLAN headings).

2026-10-24 — Step 7 (arbiter) — a TfL 200 with no `journeys` key is transient, not "no journey"; README `ready` sentence.
- **Goal**: an unrecognised 200 from TfL never writes a permanent null. In `tfl.classify`,
  a 200 JSON object with no `journeys` key (or `journeys` not a list) and no
  disambiguation is `transient`; 404 and a 200 with an explicit empty list
  (`"journeys": []`) stay `no_journey`; everything else is unchanged. A persistent
  degraded reply is then handled by the existing streak and control-call rule (Step 6
  Redo 2). `worker/README.md` stops saying `ready` means every listing has a cached time.
- **Files**: `worker/src/tfl.py` (`classify` only), `worker/tests/test_tfl_unit.py`,
  `worker/tests/fake_upstream.py` (only if a 200 `{}` destination answer needs a hook;
  `DESTINATION_STATUS` already returns body `{}`), `worker/tests/test_commute.py`,
  `worker/README.md` (TfL commute times section only).
- **Done when**: in `test_tfl_unit.py` the assertion `classify(200, '{}') == ("no_journey",
  None)` becomes `== ("transient", None)`. This is a ruled spec change (arbiter
  2026-10-24), not a loosening: it is still an exact equality and the new answer caches
  less. Add exact assertions for `classify(200, '{"journeys": null}')` and
  `classify(200, '{"message": "x"}')` → transient; every other existing assertion
  unchanged. A new test in `test_commute.py` on a fresh postcode: first poll answered
  normally, then every journey to that destination answers 200 `{}` → statuses end
  `failed` (expected `pending, pending, pending, failed` or the control-call equivalent)
  and the fake log shows no null was cached for the listings asked after the switch
  (the outage listings are asked again after the outage clears and a re-save). README:
  the sentence says `ready` once every listing has a cached time or TfL has been asked
  and could not route it, and that a few listings can be left unknown (see HANDOVER).
  Full suite passes in test mode; server-less run passes; check-process-refs exit 0.
- **Evidence location**: `evidence/prefs-filters/step-7.md`

  Tracked as `### Step 7` in PLAN, where its boxes live (the step-order hook reads PLAN headings).

2026-10-25 — human instruction — TfL commute becomes a stretch goal.
Human: "carry on, but leave tlf commute feature as strech goal because I can't get the
api key for it." Asked how, the human chose: "Keep it, make it optional" — merge the
commute code as built (it works without a key, slowly); nothing depends on it:
`commute_postcode` becomes optional on `PUT /prefs`, and B4 serves decks without
waiting for commute (minutes stay null until ready); `docs/decisions.md` and the
contract are updated (loosening only). Tracked as `### Step 8` in PLAN.

---

## RULES IN FORCE

| Rule | Source | Applies to |
| ---- | ------ | ---------- |
| Commits only via `.claude/scripts/safe-commit.sh`, title only, no signature | `.claude/CLAUDE.md` | commits |
| Commit/PR title `type(scope): message`; scopes: worker, web, db, prep, kit, api | `.claude/CLAUDE.md`, kit-config | commits, PR |
| No scope creep: touch only the step's declared files | `.claude/CLAUDE.md` #1 | code, docs |
| Dependencies: only `fastapi`, `google-genai`, `pytest`; anything else escalates | `.claude/CLAUDE.md` #2, kit-config | code, pyproject |
| Never weaken a test to pass | `.claude/CLAUDE.md` #3 | tests |
| Walk the ladder; no speculative generalisation | `.claude/CLAUDE.md` #4 | code |
| Tradeoffs logged when made; arbiter rules on them | `.claude/CLAUDE.md` #5, Modes | progress file |
| Only step-reviewer ticks, with evidence and date | `.claude/CLAUDE.md` #6 | progress file |
| Out-of-scope problems go in SPOTTED, NOT FIXED | `.claude/CLAUDE.md` #7 | progress file |
| Plain British English, no banned marketing words | `.claude/CLAUDE.md` | docs, comments |
| Error body `{"error": {"code", "message"}}`, status matches code; unknown is `null` | `docs/api-contract.md` General | code |
| A breaking change to `docs/api-contract.md` escalates; any change under `web/` escalates | `.claude/CLAUDE.md` Modes | docs, code |
| App sends only the Mubit key; keys never printed, logged or committed | mubit-gateway skill, decisions (Secrets) | code, evidence |
| Parser system prompt is one fixed string; user text only in the user message | mubit-task-design skill, decisions (Curator task shape) | code |
| Hard filters enforced in code; zero hard-constraint violations | decisions (Headline metric, Commute) | code, tests |
| No paid LLM call beyond one live parser test call; automated tests never reach Mubit | `.claude/CLAUDE.md` Modes | tests, commands |
| Evidence is metadata only, under `evidence/prefs-filters/` | `.claude/CLAUDE.md`, decisions (Evidence) | evidence |
| Stop only processes you started, by PID | session (permission denial, 2026-10-24) | commands |

---

## PLAN

All paths relative to the repo root. Design detail (tables, postcode rule, parser
call, NULL handling, TfL batching, test seam) is in the Plan agent's report, quoted in
each brief. Arbiter rulings on open questions are in KICKOFF RULINGS below.

### Step 1 — User header, prefs round trip, parser through Mubit, test seam

**Goal**: `X-User-Id` dependency (401 `unknown_user`); `prefs` table; `GET /prefs` and
`PUT /prefs` with input validation, postcode normalisation, a parser call through
Mubit, output checked in code, `commute_status` stored as `pending`; Gemini base URL
overridable from a Worker var for tests.

**Files in scope**: `worker/src/entry.py`, `worker/src/mubit.py`, `worker/src/prefs.py`
(new), `worker/schema.sql`, `worker/tests/fake_upstream.py` (new),
`worker/tests/test_prefs.py` (new), `worker/tests/test_prefs_unit.py` (new),
`worker/tests/test_mubit.py`, `worker/tests/conftest.py` (new, only if needed),
`worker/.gitignore` (only for a test env file), `docs/api-contract.md` (only the
additive parser-failure line, if ruled so).

**Done when**: pytest passes against `pywrangler dev` started with the fake-upstream
vars, covering 401 missing/unknown header; `GET` all-null shape; postcode
normalisation (`ec2n2db` → `EC2N 2DB`); 422 `invalid_postcode` for a place name and an
outward code only; 422 `invalid_request` for blank text and out-of-range
`max_commute_min`; bad LLM values stored as null; the ruled parser-failure response;
prefs unchanged after a failed parse. The real Workers `fetch` path in `mubit.py`
reaches the fake. One live parser call made by hand, status, `modelVersion` and
`mreq_` recorded.

**Evidence location**: `evidence/prefs-filters/step-1.md`

- [x] Implemented — diff read, all hunks trace to Step 1 and sit in declared scope (2026-10-24)
- [x] Tested — evidence: reviewer re-ran seed.sh, test-mode server :8788, pytest 129 passed, exit 0; evidence/prefs-filters/step-1.md (2026-10-24)
- [x] Best practices met — evidence: bound params in entry.py, fixed SYSTEM_PROMPT, per-field output checks in prefs.py, no key in repo/evidence, check-process-refs exit 0 (2026-10-24)
- [x] Matches locked requirements — evidence: Q1/Q2/Q8/Q13 followed; contract diff is only the additive parse_failed line; test_prefs.py covers every Done-when case; live call mreq_01a16f66b9fb7ec3bfd4836b56681a41 recorded (2026-10-24)
- [x] No scope drift — evidence: git status shows only declared files (2026-10-24)

**Redo (arbiter FIX_NOW, 2026-10-24)**: test-mode guard. Files: `worker/tests/conftest.py`
(new), `worker/tests/test_prefs.py`. A session-scoped fake fixture in `conftest.py`
sends one probe PUT and stops the run (`pytest.exit`, non-zero) unless the fake
recorded it with the fake key. Done when the suite passes in test mode, a run against
a server with `GEMINI_BASE` on a dead port stops after the probe with a non-zero exit,
and both runs are recorded in `evidence/prefs-filters/step-1.md`.

- [x] Redo implemented — conftest.py session `fake` fixture + probe, test_prefs.py `pytestmark`; diff read, in declared scope (2026-10-24)
- [x] Redo reviewed — evidence: reviewer re-ran: test mode 129 passed exit 0; GEMINI_BASE dead port exit 3, 11 passed then pytest.exit, no key printed; unit-only 64 passed exit 0; check-process-refs exit 0 (2026-10-24)

### Step 2 — Hard filter function

**Goal**: `passes(listing, hard, commute_minutes) -> bool`, a pure predicate, and
`matching_listing_ids(db, prefs, use_commute=True)` that loads the filter columns,
left-joins the commute cache on the user's postcode, and applies `passes`. B4 calls
it; Step 3 calls it with the commute check off.

**Files in scope**: `worker/src/filters.py` (new), `worker/tests/test_filters.py` (new).

**Done when**: unit tests (no server) cover every hard field: a NULL listing field
with that limit set is excluded; a NULL limit ignores the field; EPC ordering;
property-type rule; null commute with a max set is excluded. A test runs the predicate
over the real listings (read-only from `dataset/listings.sqlite` or `seed.sql`) for
several pref sets and asserts every returned listing meets every limit and every
excluded one breaks at least one.

**Evidence location**: `evidence/prefs-filters/step-2.md`

- [x] Implemented — filters.py passes/matching_listing_ids, only declared files, hunks trace to Step 2 (2026-10-24)
- [x] Tested — evidence: reviewer re-ran pytest test_filters+test_prefs_unit+test_mubit 94 passed exit 0; mutations (EPC direction, lease >=, bedrooms NULL) each fail tests (2026-10-24)
- [x] Best practices met — evidence: pure predicate, unknown never passes a set limit, real DB opened mode=ro, no new deps, check-process-refs exit 0 (2026-10-24)
- [x] Matches locked requirements — evidence: Q3 NULLs, Q4 _lease_ok, Q6 HOUSE_TYPES, EPC A best, independent meets_every_limit oracle over 8 pref sets on 635 real listings (2026-10-24)
- [x] No scope drift — evidence: git status shows filters.py, test_filters.py, evidence step-2.md, progress file only (2026-10-24)

### Step 3 — TfL commute, cached, batched per poll

**Goal**: `commute_cache` table; `tfl.py` builds the URL, parses minimum
`journeys[].duration`, classifies ok / no journey / transient; each `GET /prefs` while
`pending` runs one bounded batch and works out `ready` or `failed`; TfL base URL
overridable for tests.

**Files in scope**: `worker/src/entry.py`, `worker/src/tfl.py` (new),
`worker/src/filters.py` (only if needed), `worker/schema.sql`,
`worker/tests/fake_upstream.py`, `worker/tests/test_commute.py` (new).

**Done when**: against the fake TfL, pytest shows `pending` → `ready` after polling; 404
cached as null with status `ready`; 429/5xx not cached and retried next poll;
persistent failure → `failed`; a second user with the same postcode reaches `ready`
with no TfL calls (fake counts requests); only listings passing the other hard filters
are requested. A live pilot through `pywrangler dev` against real TfL with one London
postcode is recorded: listings computed, time per poll, 429s, rate-limit headers seen,
and what TfL answers for a well-formed postcode that does not exist.

**Evidence location**: `evidence/prefs-filters/step-3.md`

- [x] Implemented — tfl.py, commute_cache, GET /prefs batch, filters postcode entry point; diff read, hunks trace to Step 3 and carry-over (a)-(d) (2026-10-24)
- [x] Tested — evidence: reviewer re-ran seed.sh, test-mode server :8788 with TFL_BASE, pytest 171 passed exit 0, second run exit 0, unit-only exit 0; test_commute.py has pytestmark usefixtures("fake"); probe now requires a fake TfL request (2026-10-24)
- [x] Best practices met — evidence: bound params in entry.py/tfl.py/filters.py, bounded batch (12 pairs, 5 s, concurrency 6), transient never cached, status write guarded on updated_at and pending, check-process-refs exit 0 (2026-10-24)
- [x] Matches locked requirements — evidence: Q5 no key support, Q7 nonexistent postcode (HTTP 300) ends failed after 3-poll streak, Q11 pool is other-hard-filter matches via matching_listing_ids, Q12 poll-driven, Q13 TFL_BASE var; contract GET shape asserted on every poll (PREFS_KEYS); pilot in evidence/prefs-filters/step-3.md (2026-10-24)
- [x] No scope drift — evidence: git status shows entry.py, tfl.py, filters.py, schema.sql, fake_upstream.py, test_commute.py plus permitted conftest.py/test_filters.py, evidence, progress file (2026-10-24)

### Step 4 — README and B4 handover

**Goal**: anyone can run the backend and its tests in test mode; B4 knows the hooks.

**Files in scope**: `worker/README.md`, `.claude/kit-config.md` (Commands lines only,
if the test command changes), this progress file (a `B4 HOOKS` note under HANDOVER).

**Done when**: the README sequence (seed → dev server in test mode → pytest) is run
from a clean state and passes; the B4 hooks are written down: the
`matching_listing_ids` signature, and that the drop-unswiped-cards delete belongs in
`PUT /prefs` once B4 creates the decisions table.

**Evidence location**: `evidence/prefs-filters/step-4.md`

- [x] Implemented — worker/README.md rewritten, kit-config Test line, B4 HOOKS in this file; diff read (2026-10-24)
- [x] Tested — evidence: README sequence in fresh worktree, 171 passed twice, server-less 97 passed, guard exit 3 (evidence/prefs-filters/step-4.md) (2026-10-24)
- [x] Best practices met — evidence: no banned words, guard documented, check-process-refs exit 0 (2026-10-24)
- [x] Matches locked requirements — evidence: README sequence passes clean; B4 HOOKS has matching_listing_ids signatures and PUT /prefs delete note (2026-10-24)
- [x] No scope drift — evidence: diff touches only README, kit-config Test line, progress file, evidence file (2026-10-24)

**Redo (arbiter FIX_NOW, 2026-10-24)**: step-reviewer FAIL. Files:
`evidence/prefs-filters/step-4.md` (reword the line naming the kit script) and the B4
HOOKS note (NULL-lease exception per Q4). Done when the process-reference check exits
0 and the B4 HOOKS sentence matches `_lease_ok` in `worker/src/filters.py`.

- [x] Redo implemented — evidence line reworded, B4 HOOKS NULL-lease exception added; diff read (2026-10-24)
- [x] Redo reviewed — evidence: check-process-refs exit 0; no .claude path in evidence file; HOOKS matches _lease_ok (filters.py:9-14) (2026-10-24)

### Step 5 — Move the pure tfl.py unit tests to a server-less module (arbiter amendment)

See AMENDMENTS, 2026-10-24.

- **Goal**: `test_classify_answers` and `test_url_and_next_tuesday` run without a dev
  server, so the unit-only run covers `tfl.py`.
- **Files**: `worker/tests/test_tfl_unit.py` (new), `worker/tests/test_commute.py`,
  `worker/README.md` (only the unit-only test line, to list the new module).
- **Done when**: the two tests live in `test_tfl_unit.py` unchanged (no assertion
  removed or loosened) and are gone from `test_commute.py`; `test_commute.py` keeps
  `pytestmark = pytest.mark.usefixtures("fake")`; the unit-only run (`test_filters.py`,
  `test_prefs_unit.py`, `test_mubit.py`, `test_tfl_unit.py`) passes with no server;
  the full suite passes in test mode; README's unit-only line lists the new module.
- **Evidence location**: `evidence/prefs-filters/step-5.md`

- [x] Implemented — test_tfl_unit.py new, two tests moved byte-identical, removed from test_commute.py; README line updated (2026-10-24)
- [x] Tested — evidence: server-less run 99 passed exit 0; full suite on :8790 171 passed exit 0 (2026-10-24)
- [x] Best practices met — evidence: pure move, no code added; check-process-refs exit 0 (2026-10-24)
- [x] Matches locked requirements — evidence: unit-only run now covers tfl.py; REQUIREMENTS block untouched in diff (2026-10-24)
- [x] No scope drift — evidence: diff touches only declared files plus progress/evidence (2026-10-24)

### Step 6 — One failing listing does not fail the postcode; TfL modes; FAKE_PORT (arbiter amendment)

See AMENDMENTS, 2026-10-24, Step 6. Raised by QA-GATE FAIL 2026-10-24.

**Files in scope**: `worker/src/tfl.py`, `worker/tests/fake_upstream.py`,
`worker/tests/test_commute.py`, `worker/tests/test_tfl_unit.py` (only if the URL
changes), `worker/README.md` (test-mode section only).

**Evidence location**: `evidence/prefs-filters/step-6.md`

- [x] Implemented — worker/src/tfl.py run_batch rotation + cache-row ready rule; fake FAILING_STARTS and N7 -> 300 (2026-10-24)
- [x] Tested — 174 passed (server 8790, FAKE_PORT 8801, exit 0); server-less 99 passed; 3 new tests in test_commute.py (2026-10-24)
- [x] Best practices met — bound SQL param in tfl.py; no existing assertion changed; 429 rule and Q7 intact (2026-10-24)
- [x] Matches locked requirements — contract line "single listing failure is not failed" held by test_one_listing_that_always_fails_is_left_unknown (2026-10-24)
- [x] No scope drift — diff limited to declared files; README change only test-mode FAKE_PORT paragraph; check-process-refs exit 0 (2026-10-24)

**Redo (arbiter FIX_NOW, 2026-10-24)**: explicit TfL modes. Files: `worker/src/tfl.py`,
`worker/tests/test_tfl_unit.py`, `worker/tests/test_commute.py` (line 87 only: expect the mode suffix — stricter; it is in Step 6's declared files), `evidence/prefs-filters/step-6.md`. `build_url` sends
one fixed `&mode=` list (scheduled public-service modes plus walking; no cycle, taxi,
car, coach). Done when one free TfL call in the new shape returns journeys whose leg
modes are all in the list, the stricter URL assertion passes, and both test runs pass.

- [x] Redo implemented — tfl.py MODES + `&mode=`; test_tfl_unit.py and test_commute.py:87 stricter; server-less 99 passed, full suite test mode 174 passed, check-process-refs exit 0 (2026-10-24)
- [x] Redo reviewed — MODES checked against live Meta/Modes: public-service modes plus walking only; no assertion loosened; fake_upstream.py unchanged; evidence section supersedes old text (2026-10-24)

**Redo 2 (arbiter FIX_NOW, 2026-10-24)**: a TfL outage must not end `ready`. Raised by
the second QA-GATE FAIL (smoke item 9: `EC1A 1BB` ended `ready` with 12 of 96 cached).
Rule (b) in AMENDMENTS is replaced. Files: `worker/src/tfl.py`,
`worker/tests/fake_upstream.py`, `worker/tests/test_commute.py`,
`evidence/prefs-filters/step-6.md`. No schema change, so `worker/schema.sql` stays out.
In `run_batch`, after a fully failed batch that was not rate-limited, once the streak
reaches `FAIL_STREAK_LIMIT`: no `commute_cache` row for the postcode → `failed`
(unchanged); otherwise one control call through `fetch_journey` re-asks the cached
listing chosen by `ORDER BY minutes IS NULL, listing_id LIMIT 1` (coordinates from
`listings`): status 429 → `pending`, streak kept; transient → `failed`; `ok` or
`no_journey` → `ready` with streak 0 if `streak * BATCH_SIZE >= len(todo)`, else
`pending` with the streak kept, so the rotation goes on until every remaining listing has
been in a failing batch. The control answer is not written to the cache. Done when the
tests in the FIX BRIEF pass in test mode, the server-less run passes, and the evidence
file records both runs and the new smoke expectation (outage after progress →
`pending, pending, failed`). Counts as the second failure on this area; one more FAIL
(qa-gate or step-reviewer) on Step 6's commute-status rule escalates.

- [x] Redo 2 implemented — worker/src/tfl.py run_batch control call; server-less 99 passed exit 0; full suite test mode 177 passed exit 0 (2026-10-24)
- [x] Redo 2 reviewed — step-reviewer PASS: rule matches block, tests test_outage_after_progress_ends_failed / test_outage_with_a_last_batch_left_ends_failed / test_rate_limit_after_progress_never_fails_the_commute, process-refs exit 0 (2026-10-24)

**Redo 3 (arbiter FIX_NOW, 2026-10-24, test-only)**: cover the control call's 429
branch. Files: `worker/tests/fake_upstream.py`, `worker/tests/test_commute.py`,
`evidence/prefs-filters/step-6.md`; no change to `worker/src/tfl.py`. Done when the new
test passes and fails if the control-call `status == 429` line is removed (recorded in
evidence), both test runs pass, no existing assertion changed.

- [x] Redo 3 implemented — test_rate_limited_control_call_never_fails_the_commute in worker/tests/test_commute.py, START_STATUS in fake_upstream.py; worker/src unchanged (2026-10-24)
- [x] Redo 3 reviewed — evidence: reviewer mutation in throwaway worktree (control-call 429 lines removed) failed the new test at index 2 (failed vs pending); main tree 178 passed exit 0, server-less 99 passed exit 0, check-process-refs exit 0, git diff --stat HEAD -- worker/src empty (2026-10-24)

### Step 7 — TfL 200 with no journeys is transient; README ready sentence (arbiter amendment)

See AMENDMENTS, 2026-10-24, Step 7. Raised by QA-GATE PASS WITH FINDINGS 2026-10-24,
findings 1 and 2. Changing the `classify(200, '{}')` assertion is a ruled spec change,
not a loosening.

**Files in scope**: `worker/src/tfl.py` (`classify` only), `worker/tests/test_tfl_unit.py`,
`worker/tests/fake_upstream.py` (only if needed), `worker/tests/test_commute.py`,
`worker/README.md` (TfL commute times section only).

**Evidence location**: `evidence/prefs-filters/step-7.md`

- [x] Implemented — classify non-list journeys transient, tfl.py:57-59; README sentence only (2026-10-24)
- [x] Tested — server-less 99 passed exit 0; full suite 179 passed exit 0 (:8790); mutation (classify reverted) fails test_classify_answers and test_empty_200_answers_are_not_cached_and_are_asked_again (2026-10-24)
- [x] Best practices met — disambiguation check still follows the type check only for empty lists; 404 and [] unchanged; comment explains retry; check-process-refs exit 0 (2026-10-24)
- [x] Matches locked requirements — Step 7 done-when: exact equalities for {}, journeys null, message x; Step 6 commute-status rule untouched (2026-10-24)
- [x] No scope drift — diff limited to tfl.py classify, test_tfl_unit.py, test_commute.py, README TfL sentence, evidence step-7.md (2026-10-24)

### Step 8 — Commute optional (human amendment, 2026-10-25)

See AMENDMENTS, 2026-10-25.

**Goal**: commute is a stretch goal. `PUT /prefs` accepts a missing or null
`commute_postcode`; then no TfL work runs, `commute_postcode` and `commute_status` are
`null` in the response, and `max_commute_min` with no postcode is 422
`invalid_request`. With a postcode, behaviour is unchanged. Docs say commute is
optional and that the deck never waits for it.

**Files in scope**: `worker/src/entry.py`, `worker/schema.sql`,
`worker/src/prefs.py` (only if validation lives there), `worker/tests/test_prefs.py`,
`worker/tests/test_commute.py` (only if an existing test's premise changes — report
first), `docs/api-contract.md` (Preferences and the Deck errors/commute lines only),
`docs/decisions.md` (Commute line only, rewritten and re-dated), `docs/plan.md` (B3
line wording only), `worker/README.md` (TfL section only), this progress file (B4
HOOKS note only), `evidence/prefs-filters/step-8.md`.

**Done when**: test-mode tests cover PUT without a postcode (200, both fields null, no
TfL call made, GET stays null and makes no TfL call), PUT with `commute_postcode: null`,
`max_commute_min` without a postcode (422 `invalid_request`), and a re-save that adds a
postcode later (status becomes `pending`, then `ready` on the fake); every existing
test passes unchanged; the contract no longer makes the deck refuse on commute
(`commute_pending` / `commute_failed` removed or marked unused, `commute.minutes`
`null` until ready, `commute` `null` or minutes `null` when no postcode — pick one and
state it); decisions.md Commute line says stretch, dated 2026-10-25; B4 HOOKS updated.

**Evidence location**: `evidence/prefs-filters/step-8.md`

- [x] Implemented — entry.py put_prefs optional postcode, schema.sql nullable + CHECK, docs updated (2026-10-25)
- [x] Tested — fresh worktree, fresh seed, server 8790/fake 8801: 183 passed exit 0; server-less 99 passed exit 0; test_no_postcode_is_saved_with_null_commute_and_no_tfl_work, test_resave_adding_a_postcode_starts_commute (2026-10-25)
- [x] Best practices met — SQL bound params, 422 for non-string/malformed postcode and limit without postcode, CHECK pairs postcode/status; only the two ruled 422 cases changed (2026-10-25)
- [x] Matches locked requirements — human amendment 2026-10-25: PUT without postcode 200 nulls, deck 409 commute_* removed, decisions.md Commute dated stretch (2026-10-25)
- [x] No scope drift — diff limited to declared files; contract hunks only in GET/PUT /prefs and Deck; no web/ change; check-process-refs exit 0 (2026-10-25)

**Redo (arbiter FIX_NOW, 2026-10-25)**: re-seed note and re-wrap. Files:
`worker/README.md` (TfL commute times section: one sentence — after pulling this
change each laptop re-runs `worker/scripts/seed.sh` with the dev server stopped, or a
save without a postcode fails on the old NOT NULL columns) and `docs/decisions.md`
(re-wrap the Commute paragraph to the file's ~88-character width, wording and date
unchanged). Done when both are present, check-process-refs exits 0, and the diff
touches only those two hunks.

- [x] Redo implemented — README.md re-seed sentence added; decisions.md Commute re-wrapped, word-for-word identical when whitespace-collapsed; check-process-refs exit 0 (2026-10-25)
- [x] Redo reviewed — evidence: diff limited to worker/README.md and docs/decisions.md hunks, max added line 86 chars, no banned words (2026-10-25)

ESCALATED (arbiter) 2026-10-25: qa-gate finding 2 — `web/` on main still requires a commute postcode (`prefsForm.ts` `canSave`), its mock refuses a missing postcode and returns 409 `commute_pending` / `commute_failed` from `getDeck`, and `deckState.ts` / `DeckScreen.tsx` handle those codes; after this merge the mock contradicts the contract. Any `web/` change escalates, and `web/` is Yewen's. This escalation covers that `web/` follow-up only. It does not block B3: B3 changes nothing under `web/`, the contract change only loosens it (a postcode is still accepted; the removed codes are never sent), and the real backend works with today's frontend. B3 may merge once the Step 8 contract redo (findings 1 and 3) passes review. The human must tell Yewen: postcode optional in the prefs form and mock, drop the commute 409s from the mock and the blocked deck state, cards may have `commute: null`.

**Redo 2 (arbiter FIX_NOW, 2026-10-25)**: contract matches optional commute. Files:
`docs/api-contract.md` (PUT /prefs re-save sentence: fetch a new deck at once, not
"once `commute_status` is `ready`"; Deck commute bullet: with `max_commute_min` set,
listings with no cached time do not pass, so the deck is short while `pending` and
empty with `no_matches` on `failed`; align the GET /prefs "`commute.minutes: null`"
sentence to apply only without a limit), this file (B4 HOOKS bullet replacing the
qa-gate "not yet ruled" note), `evidence/prefs-filters/step-8.md`. No error code or
enum added or removed. Done when no contract sentence makes the deck depend on
`commute_status`, the short/empty deck is stated, and check-process-refs exits 0.

- [x] Redo 2 implemented — docs/api-contract.md three hunks (GET /prefs commute_status bullet, PUT /prefs re-save, Deck commute bullet), B4 HOOKS bullet, evidence/prefs-filters/step-8.md note; check-process-refs exit 0 (2026-10-25)
- [x] Redo 2 reviewed — step-reviewer PASS: `git diff HEAD -- docs/api-contract.md` is exactly three hunks; wording matches `passes` / `matching_listing_ids_for_postcode` in worker/src/filters.py; no enum or error code changed; nothing under web/; check-process-refs exit 0 (2026-10-25)

---

## KICKOFF RULINGS

Q1: Parser model is `gemini-3.8-flash`, thinking set explicitly low, temperature 0, never changed — arbiter 2026-10-24: the only model proven live through Mubit; flash-lite would cost an extra test call for about 30 calls in total; decisions.md fixes no parser model, so no open item is settled by this.
Q2: Parser call failure or unusable output on `PUT /prefs` returns 502 `parse_failed` in the contract error shape, prefs unchanged; add one additive line to the `PUT /prefs` Errors in `docs/api-contract.md` — arbiter 2026-10-24: additive, not breaking; `web/src/api/http.ts` already reads `error.code`/`message` from any non-OK status in the contract shape, so no `web/` change is needed; 500 `internal_error` would be just as undocumented and less honest.
Q3: A NULL listing field is excluded when its matching hard limit is set (property_type, lease) — arbiter 2026-10-24: zero hard-constraint violations is a decided headline claim; the pool cost is small (3 NULL types, 47 NULL leases, only when that limit is set).
Q4: `min_lease_years` excludes any listing whose `lease_years_remaining` is known and below the minimum, whatever the tenure; a NULL lease is excluded only for `leasehold`; freehold and share_of_freehold with NULL pass — arbiter 2026-10-24: changes the planner's "leasehold only": 36 of 60 share_of_freehold rows carry a lease figure, and passing a known 60-year lease under a 90-year limit would read as a violation; about two extra lines.
Q5: Measure the anonymous TfL rate limit in the step 3 pilot; build no app-key support; if the pilot shows a key is needed, ESCALATE (new secret) — arbiter 2026-10-24: missing secret is an escalation trigger; no speculative config before evidence.
Q6: `house` in `property_types` expands in code to house, terraced, semi_detached, end_of_terrace, detached, bungalow — arbiter 2026-10-24: the enum treats `house` as one value among house subtypes (29 rows are plain `house`); without expansion "a house" would exclude 302 houses.
Q7: A well-formed but non-existent postcode is accepted at PUT and ends `failed` after a 3-poll fail streak; if the pilot shows a clear TfL 4xx for it, map that straight to `failed` — arbiter 2026-10-24: no paid or external lookup at PUT; `failed` lets the user re-save, as the contract says.
Q8: `max_commute_min` is an integer 1–180 (JSON bool rejected), else 422 `invalid_request` — arbiter 2026-10-24: contract leaves ranges to the backend; 180 covers any real commute.
Q9: Keep FastAPI's default validation order when the header is bad and the body malformed — arbiter 2026-10-24: contract leaves error precedence to the backend; extra code buys nothing.
Q10: Defer dropping unswiped served cards to B4; implementer logs it as a B3 TRADEOFF in step 1; B4's step scope must include `PUT /prefs` — arbiter 2026-10-24: the decisions table does not exist until B4, so B3 serves no cards and the contract behaviour cannot be violated yet; does not block Sat 13:00 provided B4 carries it.
Q11: Compute commute for every listing passing the other hard filters even when no max is set — arbiter 2026-10-24: decisions.md (Commute, When) says so; the curator weighs it as a factor.
Q12: Poll-driven TfL batching (each `GET /prefs` while pending runs one bounded batch, about 12 pairs, about 5 s, concurrency 6) is approved, not `ctx.waitUntil` — arbiter 2026-10-24: works under `pywrangler dev` without relying on background-task support in the Python Worker ASGI bridge, and the contract already requires polling; about 30 polls for the ~366 London listings is acceptable. Batch size and concurrency are constants, not config, and are revisited only if the pilot shows 429s.
Q13: Optional Worker vars `GEMINI_BASE` / `TFL_BASE` overriding the upstream hosts, defaulting to the real hosts, are approved — arbiter 2026-10-24: not speculative, it is the only way automated tests keep the "never reach Mubit" rule without a new dependency; condition: tests run from a separate gitignored test vars file with a fake `MUBIT_API_KEY`, never `.dev.vars`, so a real key is never sent to the fake.

---

## TRADEOFFS

2026-10-24 | step 1 | Re-saving prefs does not yet drop unswiped served cards | the decisions table does not exist until B4; B4's scope must include `PUT /prefs` | delete the user's unswiped decisions inside `PUT /prefs` once B4 creates the table — accepted by arbiter 2026-10-24: settled by kickoff ruling Q10; B3 serves no cards, so nothing can be violated yet; B4 must carry the delete in `PUT /prefs` and Step 4 writes it into B4 HOOKS

2026-10-24 | step 1 | A soft preference over 120 characters is dropped, not shortened | a cut phrase could change its meaning; the cap is rare | truncate at a word boundary if real outputs hit it — accepted by arbiter 2026-10-24: dropping is the safer failure (a cut phrase can invert meaning), soft prefs only feed the curator, and nothing later in the plan depends on long soft prefs

2026-10-24 | step 1 | Test mode relies on `wrangler dev --var` beating `.dev.vars` (wrangler 4.152.0) | checked by probe; a wrangler upgrade could change it | the suite's final test and the fake's 401 would flag a wrong key; move to a tests-only worker config if it ever breaks — accepted by arbiter 2026-10-24: meets Q13's purpose (a real key never reaches the fake) by a recorded probe plus the fake's 401 and the final key assertion, with no extra file; the deviation from Q13's test-vars-file wording departs from an arbiter ruling, not from decisions.md

2026-10-24 | step 1 redo | The guard covers only modules that use the `fake` fixture | a future API test module that skips it is unguarded | require the fixture in any new API test module — accepted by arbiter 2026-10-24: the only existing modules outside the guard (test_users.py, test_mubit.py) never call PUT /api/prefs, so nothing reaches Mubit today; a session-wide autouse would break the server-less unit tests; Step 3's brief must require test_commute.py to apply `pytestmark = pytest.mark.usefixtures("fake")` (or take `fake` in every test that hits the server) so the probe runs before any PUT /api/prefs, and its reviewer must confirm it

2026-10-24 | step 1 redo | The probe leaves a throwaway `probe_*` user and prefs row in the local D1 | one extra row per session | none needed; seed.sh clears it — accepted by arbiter 2026-10-24: local D1 only, same pattern as the existing t_* test users, cleared by re-seeding; no effect on later steps or the eval

2026-10-24 | step 2 | `matching_listing_ids(db, hard, commutes=None)` takes a listing-id to minutes mapping instead of joining `commute_cache` on the postcode | the table does not exist until Step 3; creating it here would be out of scope | Step 3 adds the join (or a loader returning the mapping) and a postcode-taking wrapper for B4; `passes` is unchanged — accepted by arbiter 2026-10-24: the commute_cache table is Step 3's, and `worker/src/filters.py` is already in Step 3's scope, so nothing later is blocked; Step 3's brief must require (a) a postcode-taking entry point in filters.py that loads the (listing, postcode) minutes from `commute_cache` and calls `matching_listing_ids` with them, so B4 never builds the mapping itself; (b) a listing with no cache row, or a cached null (TfL 404), maps to None and is excluded when `max_commute_min` is set; (c) the TfL batch selects listings with `commutes=None` (commute limit off), as the done-when requires; (d) unit tests for (a) and (b); Step 4 writes the final signature into B4 HOOKS

2026-10-24 | step 2 | The filter loads every listing (635) and applies `passes` in Python, no SQL WHERE | one predicate in one place, so SQL and Python cannot disagree; the table is small | push a pre-filter into SQL only if the listing count grows by orders of magnitude — accepted by arbiter 2026-10-24: 635 rows in a local D1, one query per deck or poll; one predicate keeps the zero-violations claim checkable in one place; the dump is frozen, so the growth case does not arise this weekend

2026-10-24 | step 2 | Unknown tenure with unknown lease is excluded when `min_lease_years` is set | conservative, consistent with Q3 (unknown never passes a set limit); the brief left it open | pass it instead if the pool proves too small (check count of such rows) — accepted by arbiter 2026-10-24: consistent with Q3; the real dump has 0 rows with NULL tenure (339 freehold, 236 leasehold, 60 share_of_freehold), so the pool cost today is nil

2026-10-24 | step 3 | A TfL batch that cached nothing and met a 429 does not add to the fail streak (the brief counted every transient batch) | the pilot showed anonymous TfL answers 429 with `Retry-After: 31` after about 54 calls in 17 s; three rate-limited polls in a row (one poll a second) would end `failed` for a good postcode | none if accepted; a permanent 429 would poll as `pending` for ever, so cap total polls if that is seen — accepted by arbiter 2026-10-24: departs from the wording of kickoff ruling Q7, not from decisions.md; the pilot showed the 429 is a ~30 s throttle that clears, and counting it would end good postcodes `failed`; a non-existent postcode still ends `failed` (HTTP 300 is transient, not 429); a permanent 429 is not observed and re-saving prefs resets it
2026-10-24 | step 3 | Anonymous TfL throughput is roughly 12 calls per 3 to 5 s poll until throttled, then 30 s waits; a 96-listing pool needed 12 polls across a throttle, ~366 London listings will take minutes | Q5 says build no key support unless the pilot shows one is needed; the limit slows the commute step, it does not block it | a TfL app key (new secret) or fewer pairs per poll; ESCALATE decision left to the caller — accepted by arbiter 2026-10-24: the pilot does not show a key is needed (Q5): throughput slows the commute step but every postcode reached `ready`; a new postcode costs minutes, once, and the cache is shared (≤635 listings × ~5 persona destinations, about 15–60 min of polling in total at the measured 45–190 calls/min), which fits Saturday afternoon; Step 4's README must say: (1) a new commute postcode takes minutes to reach `ready` on anonymous TfL; (2) save each persona destination and the demo postcode once and poll to `ready` before the persona batch and before recording (warming is a run-book step, not code in B3); (3) poll `GET /prefs` no faster than every 2–3 s, and a run of quick `pending` polls means the TfL throttle, wait ~30 s; (4) the test-mode command needs `--var TFL_BASE:http://127.0.0.1:8799` as well as `GEMINI_BASE`; revisit (escalate for a key) only if B6's batch stalls on commute
2026-10-24 | step 3 | Date fallback: `london_today` falls back to UTC if `zoneinfo` fails in the runtime; not observed which path ran | UTC is at most an hour off London, which never moves a Tuesday | none — accepted by arbiter 2026-10-24: either path yields a coming Tuesday at 08:30 (a weekday, as decisions.md Commute requires) and a test asserts it; the only edge (London Tuesday 00:00–01:00 BST) picks the following Tuesday, still valid
2026-10-24 | step 3 | A concurrent poll can run a second batch for the same user; the status write is skipped if the prefs row changed, but two simultaneous batches may both count a fail | cache writes are idempotent (INSERT OR REPLACE); a client polls one request at a time | a per-user lock if clients ever poll in parallel — accepted by arbiter 2026-10-24: cache writes are idempotent, the status write is guarded, the frontend and the planned persona swiper poll one request at a time; worst case is an early `failed` the user clears by re-saving
2026-10-24 | step 3 | `test_commute.py` holds two pure unit tests (classify, URL and Tuesday) that need the server because of the module `pytestmark` | the step's file scope has no other test file for tfl.py | move them to a server-less module in a later step — FIX_NOW by arbiter 2026-10-24: cheap (a file move, under 30 lines), and it lets the unit-only run cover tfl.py; see AMENDMENTS (arbiter) Step 5 — resolved by Step 5 2026-10-24
2026-10-24 | step 6 | the new tests prove "cached" and "unknown" from the fake's request log, not a D1 read | the fake runs in the test process and the server's D1 file is not reachable from pytest | a test-only endpoint or opening the .wrangler sqlite by path; one direct D1 read recorded in evidence instead — accepted by arbiter 2026-10-24: the fake's request log shows which listings got an answer, and the evidence records a direct read of the local D1 (95 rows with one failing listing, 83 with 13 failing, 96 for a full postcode) that matches it; a test-only endpoint would be new code with no other use
2026-10-24 | step 6 | with 13 failing head listings the postcode needs ~20+ polls: each progress poll resets the streak and the offset, so a wasted poll on the failing head follows | the rule as ruled | keep the offset while the head is known bad (needs per-postcode state, a schema change) — accepted by arbiter 2026-10-24: at worst it doubles the polls for an affected postcode (one wasted poll per productive one), it never fails the postcode, and the pilot had no failing listings in 96; no checkpoint is blocked, as warming is a manual run-book step done once per destination; fixing it needs per-postcode state, which is not cheap; revisit only if B6's warm-up stalls, and the main agent should add to HANDOVER that listings TfL keeps failing slow warm-up by up to 2x
2026-10-24 | step 6 | no explicit TfL `mode=`: the docs state no default; six observed journeys used only walking, bus and tube legs; four free TfL calls made where one was allowed | small sample, undocumented default | send an explicit mode list if a cycle or taxi leg shows up | resolved by Step 6 redo 2026-10-24
2026-10-24 | step 6 redo 2 | A decision poll can take about 10 s (batch budget plus a 5 s control call) | the control call runs after the batch inside the same request | lower the budgets, or run the control call concurrently with the last batch — accepted by arbiter 2026-10-24: only the one decision poll after three fully failed batches is slow (worst case nearer 15 s, a call started just before the budget ends plus the control call); polls are sequential, web/ has no request timeout and no poll loop yet (F4), and pywrangler dev imposes no wall-clock limit, so a slow poll delays the next one and breaks nothing; the README's 2–3 s is the gap between polls and still holds
2026-10-24 | step 6 redo 2 | Under per-call timeouts a failing batch may try only about 6 of its 12 listings, so "in a failing batch" is not quite "tried" | calls start only while the batch budget lasts, 6 at a time | track tried ids per postcode, which needs a schema change — accepted by arbiter 2026-10-24: bites only when TfL is up (the control call answered), the failures are timeouts rather than fast errors, and 7–36 listings remain (the ready test needs streak*BATCH_SIZE >= len(todo)); then up to about half of them can end unknown untried, and a re-save retries only uncached listings; the pilot had no failing listings in 96; the fix needs per-postcode state, not cheap; the main agent should add it to HANDOVER What is not done
2026-10-24 | step 6 redo 2 | If TfL recovers between the third failing batch and the control call, the poll can end `ready` early with listings never answered | one control call is a sample, not a proof | none cheap; the user can re-save to retry — accepted by arbiter 2026-10-24: a race inside one request (seconds between the last failing batch and the control call), and it can end ready only when at most 36 listings remain uncached; with more left the poll stays pending and the next batch makes progress; a re-save resumes only the uncached listings; the main agent should add it to HANDOVER What is not done

2026-10-24 | step 6 redo 3 | The new control-call test relies on the first 12 pool listings being cached by the first poll and on no uncached listing sharing the control listing's coordinates | it asserts both, so a change to batch order or to the dump fails it loudly rather than passing for the wrong reason | key the test on the cache rows instead of the dump order if the batch order ever changes — accepted by arbiter 2026-10-24: both assumptions are asserted (the first poll's 12 starts match the first 12 pool rows; the control coordinates are not among the uncached rows), so a change to batch order or the dump fails the test loudly and never passes it for the wrong reason; the dump is frozen (635 listings, 626 distinct coordinates); test-only, so no later step or checkpoint depends on it

2026-10-24 | step 3 (qa-gate finding 1) | `tfl.classify` reads any 200 JSON object with no `journeys` and no disambiguation as "no journey" and caches null for good; a degraded TfL answering 200 `{}` gave `ready` with 84 of 96 null on the fake, and a re-save does not retry them | Step 3 design, asserted in test_tfl_unit.py | classify a 200 without a `journeys` key as transient — FIX_NOW by arbiter 2026-10-24: a permanent wrong null drops listings from every deck under a max commute and poisons the shared cache that B6's warm-up and the Sat afternoon checkpoint rely on; TfL documents 404 for no journey, a 200 without `journeys` is not a documented answer, and the pilot did not record the status of its two nulls, so nothing shows the current reading is needed; under 20 lines; see AMENDMENTS (arbiter) Step 7 — resolved by Step 7 2026-10-24

2026-10-24 | step 6 (qa-gate finding 3) | with timeouts, a second user with a different pool caching listings on the same postcode between this user's polls shrinks the uncached list, so the rotation offset can step past a never-asked listing before `ready` | the offset is computed from the current uncached list, with no per-postcode state | track tried ids per postcode (schema change) — accepted by arbiter 2026-10-24: a variant of the accepted step 6 redo 2 timeout tradeoff, needing timeouts, a shared postcode and overlapping polls at once; no deterministic route found; outcome is at most a few unknown listings, same as the accepted case; warm-up is a manual run-book step with one user per destination (HANDOVER item 3 already says so); the fix needs per-postcode state, not cheap

2026-10-25 | step 8 | Existing test cases that expected 422 for a missing or null `commute_postcode` were changed to the new behaviour | human ruling made `commute_postcode` optional; those two cases are now covered as 200 in new tests | none: the parametrised 422 list keeps the non-string postcode and max-commute-without-postcode cases — accepted by arbiter 2026-10-25: a spec change ruled by the human amendment of 2026-10-25 (commute optional), not a loosening; the old shapes are now asserted as exact 200 responses with both fields null and no TfL call, and the replacement 422 cases are still exact

2026-10-25 | step 8 | `schema.sql` changed with no migration | local D1 is rebuilt by `seed.sh`; a stale local D1 with the old NOT NULL columns rejects postcode-less saves until re-seeded | re-run seed.sh on each laptop — FIX_NOW by arbiter 2026-10-25: no migration is right for a local-only D1 that seed.sh rebuilds from scratch, but a stale D1 turns a postcode-less PUT into a 500 on a NOT NULL column, which would hit Yewen's F4 prefs work against the real API with no clue why; the README must say it, the PR body alone is not durable; one sentence in the README TfL section, which is in Step 8's scope, so this is a Step 8 redo; fold in re-wrapping the decisions.md Commute paragraph (also in scope) so no line runs past the file's width — resolved by Step 8 redo 2026-10-25

---

## SPOTTED, NOT FIXED

2026-10-24 | `worker/README.md` | test instructions do not yet describe test mode or the fake upstream | low (Step 4 covers the README) — accepted by arbiter 2026-10-24: in Step 4's scope and done-when; Step 4 must also say test mode is mandatory and that the default BASE_URL (8787) is the normal dev server

2026-10-24 | `worker/tests/test_prefs.py` | no guard if pytest runs against a normal dev server (real key, no GEMINI_BASE): the first PUT would reach the real Mubit; Q13 wanted a separate test vars file | medium (Step 4 README must say test mode is mandatory; consider a guard test that fails fast) — resolved by Step 1 redo 2026-10-24

2026-10-24 | `worker/src/entry.py` GET /prefs | the status-write race guard compares `updated_at`, which has one-second resolution; a re-save in the same second as the previous save could be overwritten by a stale batch, and no test covers the guard | low (a PUT includes an LLM call, so same-second re-saves are not realistic) | step 3 review — accepted by arbiter 2026-10-24: unreachable in practice (each PUT waits on an LLM call); the worst case is a stale status the next poll or re-save corrects; nothing later depends on it
2026-10-24 | `worker/src/tfl.py` run_batch | a permanent TfL 429 leaves a user `pending` for ever (by design, tradeoff logged); the user can still re-save, but the frontend has no timeout | low to medium, B4/F4 may want a poll cap | step 3 review — accepted by arbiter 2026-10-24: not observed (the pilot's 429 cleared in ~30 s); re-saving resets it; no `web/` change is made or needed now; if B4 or F4 wants a poll cap, that work escalates there (any `web/` change does)
2026-10-24 | `.claude/kit-config.md` Test line | the backend test command targets `BASE_URL=http://localhost:8788`, while the qa-gate run used :8790 in a second worktree | low (qa-gate finding) — accepted by arbiter 2026-10-24: 8788 is the test-mode port worker/README.md documents for the normal case; another port only matters when two servers run at once, and BASE_URL (plus FAKE_PORT, which Step 6 documents) already overrides it
2026-10-24 | `worker/README.md` TfL commute times | says the status becomes `ready` "when every listing has a cached time", untrue since Step 6 (an unroutable listing is left unknown) | low (qa-gate finding 2) — FIX_NOW by arbiter 2026-10-24: one sentence, and the README is what the warm-up run-book is read from; folded into AMENDMENTS (arbiter) Step 7 — resolved by Step 7 2026-10-24
2026-10-24 | this file, AMENDMENTS Step 6 | rule (b) was edited in place (dated, attributed) rather than kept with the replacement appended | low (qa-gate note 4) — accepted by arbiter 2026-10-24: the progress file is committed, so the original rule (b) is intact in git history, the in-place note is dated, attributed and points to Step 6 Redo 2, which states the replacement in full; restoring it changes no behaviour. Not a precedent: future amendment changes are appended, never edited in place, and REQUIREMENTS (LOCKED) is untouched
2026-10-25 | `docs/api-contract.md` PUT /prefs re-save paragraph | says the frontend fetches a new deck "once `commute_status` is `ready`"; without a postcode the status is `null` and the Deck section says the deck never waits | low (qa-gate finding 1) — FIX_NOW by arbiter 2026-10-25: one sentence inside Step 8's declared contract scope, and it is the contract Yewen builds F3/F4 against; Step 8 redo — resolved by Step 8 Redo 2 2026-10-25
2026-10-25 | `web/src/prefs/prefsForm.ts`, `web/src/api/mock.ts`, `web/src/deck/deckState.ts`, `web/src/deck/DeckScreen.tsx` (origin/main) | frontend still requires a postcode and the mock still returns 409 `commute_pending` / `commute_failed`; mock contradicts the contract after merge | medium (qa-gate finding 2) — ESCALATED by arbiter 2026-10-25: any `web/` change escalates; follow-up for Yewen; does not block B3's merge (see Step 8)
2026-10-25 | `docs/api-contract.md` Deck commute line; B4 HOOKS | with `max_commute_min` set, listings without a cached time are excluded, so the deck is short while `pending` and empty (`no_matches`) on `failed`; "the deck never waits" reads as if the limit had no effect | low (qa-gate finding 3) — FIX_NOW by arbiter 2026-10-25: state today's behaviour in the contract now (two sentences, in Step 8's Deck commute scope) so neither B4 nor F3 builds on a wrong reading; exclusion stays (zero hard-constraint violations is decided); whether B4 adds a commute-specific `empty_reason` is B4's call, and a new enum value the frontend must handle escalates there; replace the "not yet ruled" B4 HOOKS note; Step 8 redo — resolved by Step 8 Redo 2 2026-10-25

---

## VERIFICATION

- [x] All step checkboxes ticked with evidence — steps 1–8 and the redos of steps 1, 4, 6 (Redo, Redo 2, Redo 3) and 8 (Redo, Redo 2); steps 1–7 dated 2026-10-24, step 8 and its redos 2026-10-25, in order (2026-10-25)
- [x] Every evidence path in this file exists — evidence/prefs-filters/step-1.md to step-8.md (2026-10-25)
- [x] REQUIREMENTS (LOCKED) unchanged — the block hashes the same in all 15 commits of this file since af32e50; the commute-optional change is in AMENDMENTS 2026-10-25 (human) (2026-10-25)
- [x] Test suite run — result: fresh worktree at 4e6b1a3, fresh D1 (`worker/scripts/seed.sh` exit 0), `uv sync --group dev` exit 0; test-mode server :8790 / inspector 9241, fake on 8801: `FAKE_PORT=8801 BASE_URL=http://localhost:8790 uv run --group dev pytest tests -q` 183 passed, exit 0, run twice on one D1, both exit 0; server-less modules (test_filters, test_prefs_unit, test_mubit, test_tfl_unit) 99 passed, exit 0; web on the merge result with origin/main d1dc2c8 (`git merge-tree --write-tree` exit 0, tree e220632): `npm ci` exit 0, `npm test` 178 passed, exit 0 (2026-10-25)
- [x] Lint run — result: not configured in kit-config (2026-10-25)
- [x] Typecheck run — result: web `npm run typecheck` exit 0 on the merge result; no backend typecheck configured (2026-10-25)
- [x] Build run — result: web `npm run build` exit 0 on the merge result (2026-10-25)
- [x] Diff contains no files outside declared scope — every file maps to a step's Files in scope, an Evidence location or this file; `docs/api-contract.md` changes only the parse_failed line and the Step 8 Preferences and Deck hunks (incl. Redo 2's three); `docs/decisions.md` only Commute; `docs/plan.md` only B3; nothing under `web/`; check-process-refs exit 0 (2026-10-25)
- [x] Tradeoff ledger reviewed — signed by arbiter (full automation); every TRADEOFFS and SPOTTED entry carries an arbiter verdict or a resolved marker; one open ESCALATED entry (web/ follow-up for Yewen), which does not block B3 (2026-10-25)
- [ ] Human eye test completed — not human-verified (full automation) — smoke check: 11 of 11 as expected, at 4e6b1a3 against a test-mode server (:8790) with the fake upstream (:8801), cache counts read from the local D1. 401 with no header and with an unknown id; user created; GET all-null; PUT with no postcode → 200, `commute_postcode` and `commute_status` null, three GETs stay null; PUT with `commute_postcode: null` → same; 0 TfL calls for both; `max_commute_min` 45 with no postcode, and with a null postcode → 422 `invalid_request`, no Gemini call, prefs unchanged; same user re-saved with `wc2e9dd` max 45 → 200 `WC2E 9DD` `pending`, `ready` on poll 8, 96 of 96 cached, 0 null; `Liverpool Street` → 422 `invalid_postcode`; one always-failing listing, `NW6 1AB` → `ready` on poll 12, never `failed`, 95 of 96 cached, the failing one not cached; 500 outage after the first poll, `EC1M 4AA` → `pending, pending, pending, failed`, 12 cached, no TfL call on a further GET; re-save → `ready` in 7 polls, 84 new TfL calls, 96 cached; 200 `{}` outage after the first poll, `EC2Y 8DS` → `pending, pending, pending, failed`, 12 rows before and after, 0 null; re-save → `ready` in 7 polls, 84 new TfL calls, 96 cached; 200 `{}` from the start, `EC3A 7BB` → `pending, pending, failed`, nothing cached. Fake saw 9 Gemini calls, fake key only; no live Mubit or TfL call.

QA-GATE: PASS 2026-10-25

Open escalation (does not block B3): `web/` follow-up for Yewen, see Step 8 and SPOTTED, NOT FIXED. Detail in HANDOVER, What is not done.

---

## HANDOVER

### What was built

A user can save their house-hunting wishes in plain English. The backend sends the text
through Mubit to Gemini and stores firm limits (price, bedrooms, type, EPC, tenure,
lease) apart from softer wishes. A filter in code drops any listing that breaks a firm
limit; B4 will use it to build the deck. A commute postcode is optional. With one, the
backend works out public-transport times from every matching listing to it with TfL,
one batch per `GET /api/prefs` poll, cached per (listing, postcode). Without one, no TfL
work runs and nothing waits for it.

### What to check yourself

Full automation was on, so no human has looked at this. The smoke check below ran
instead, against a test-mode server with a fake Mubit and a fake TfL
(`worker/tests/fake_upstream.py`). Nothing reached Mubit or TfL.

1. Fresh worktree at 4e6b1a3, `worker/scripts/seed.sh` (exit 0), then in `worker/`:
   `uvx --from workers-py pywrangler dev --port 8790 --inspector-port 9241 --var MUBIT_API_KEY:test-key-not-a-real-key --var GEMINI_BASE:http://127.0.0.1:8801 --var TFL_BASE:http://127.0.0.1:8801`,
   with the fake running on 8801 inside the smoke script.
2. `GET http://localhost:8790/api/prefs` with no header, and with `X-User-Id: u_nope` →
   401 `unknown_user`. Pass.
3. `POST /api/users` with a new username → 201. `GET /api/prefs` → 200, all five fields
   null. Pass.
4. `PUT /api/prefs` `{"text":"Two bed flat under 550k, near a tube station"}` → 200,
   `commute_postcode` null, `commute_status` null, `parsed.hard.max_commute_min` null.
   Three GETs stay null. Same with `"commute_postcode": null`. The fake saw no TfL call.
   Pass.
5. `PUT /api/prefs` `{"text":"…","max_commute_min":45}`, and with
   `"commute_postcode": null` added → 422 `invalid_request` ("max_commute_min needs a
   commute_postcode."). No Gemini call. Stored prefs unchanged. Pass.
6. Same user re-saved with `"commute_postcode":"wc2e9dd","max_commute_min":45` → 200,
   `WC2E 9DD`, `pending`, `hard.max_commute_min` 45. Polled: `ready` on poll 8, 96 of
   96 pool listings cached, none null. Pass.
7. `"commute_postcode":"Liverpool Street"` → 422 `invalid_postcode`. Pass.
8. One pool listing always failing on the fake, `NW6 1AB` → `ready` on poll 12, never
   `failed`, 95 of 96 cached, the failing one not cached. Pass.
9. `EC1M 4AA`: first poll answered, then every journey answered 500 →
   `pending, pending, pending, failed`, 12 cached. A further GET stayed `failed` with no
   TfL call. Re-saved after clearing → `ready` in 7 polls, 84 new TfL calls, 96 cached.
   Pass.
10. `EC2Y 8DS`: first poll answered, then every journey answered 200 `{}` →
    `pending, pending, pending, failed`. 12 rows before and after, none null. Re-saved
    after clearing → `ready` in 7 polls, 84 new TfL calls, 96 cached. Pass.
11. `EC3A 7BB` answering 200 `{}` from the first call → `pending, pending, failed`,
    nothing cached. Pass.

The branch merges into origin/main (d1dc2c8) with no conflicts. The web tests (178),
typecheck and build pass on the merge result.

If you want to look yourself with real services: re-seed first (`worker/scripts/seed.sh`
with the dev server stopped), then start the normal dev server
(`cd worker && uvx --from workers-py pywrangler dev`). Each `PUT /api/prefs` there is a
paid Gemini call. Save once with no postcode and confirm `commute_status` is `null`. A
save with a postcode makes real TfL traffic; poll `GET /api/prefs` every 3 seconds and
expect a few minutes to `ready`.

### Tools that will help

- curl, for the requests above. Always send `X-User-Id`. With a postcode, watch
  `commute_status` across polls. One poll in a failing run can take 10 to 15 seconds;
  that is the extra check call, not a hang.
- A D1 client (`npx wrangler d1 execute haka --local --command "..."` in `worker/`):
  `SELECT postcode, count(*), sum(minutes IS NULL) FROM commute_cache GROUP BY 1` shows
  how far each postcode has got. Compare the count with the pool size before trusting a
  `ready`. `SELECT user_id, commute_postcode, commute_status, commute_fail_streak FROM prefs`
  shows who has a postcode and why a user is stuck.
- The `pywrangler dev` console: `TfL call failed` warnings, and `Prefs parser` warnings
  when a save returns 502. A 500 on a postcode-less save means the local D1 predates
  Step 8: re-seed.
- The Mubit console: each real save shows one call on `gemini-3.8-flash`. Its `mreq_` id
  is in `prefs.parse_request_id`.

### What is not done

- **Open escalation, for Yewen (`web/`).** The frontend on main still treats commute as
  required and the deck as blocked on it. Nothing breaks against the real backend today
  (the form always sends a postcode; the backend never sends the removed codes), but the
  mock now contradicts the contract. Tell Yewen to change:
  1. `web/src/prefs/prefsForm.ts`: `canSave` must not require a postcode. `toRequest`
     must omit `commute_postcode` (or send `null`) when blank, not send `""`. Block save,
     or show an inline error, when a commute limit is set with no postcode (the backend
     returns 422 `invalid_request`).
  2. `web/src/api/mock.ts`: accept a missing or `null` `commute_postcode` (drop "A
     commute postcode is required."), return `commute_postcode: null` and
     `commute_status: null` then, return 422 `invalid_request` for a limit with no
     postcode, and stop returning 409 `commute_pending` / `commute_failed` from
     `getDeck`.
  3. `web/src/deck/deckState.ts` (`BLOCKED_CODES`) and `web/src/deck/DeckScreen.tsx`:
     drop the `commute_pending` / `commute_failed` blocked states. Keep `prefs_missing`.
  4. `web/src/api/types.ts:162` (`commute: Commute`) and `web/src/deck/format.ts:89`
     (`commuteLine`): a card's `commute` can be `null` (no postcode saved), and
     `commute.minutes` can be `null` until cached. The card must show no commute line,
     not crash.
  5. After a re-save, fetch a new deck at once; do not wait for `commute_status`.
- Re-saving prefs does not yet drop unswiped served cards. B4 must add it to `PUT /prefs`.
- The commute time is not on a card yet, and the curator does not weigh it yet (B4).
- With `max_commute_min` set, listings without a cached time are not served. The deck is
  short while commute is `pending` and empty (`no_matches`) on `failed`. The contract
  says so; B4 decides whether to add a commute-specific `empty_reason`.
- No poll cap. A TfL block that never lifts leaves a user `pending` for ever. The user
  can re-save.
- When TfL times out rather than failing fast, a failing batch may try only about 6 of
  its 12 listings. Once TfL answers the check call, the postcode can end `ready` with up
  to about half of the last 7 to 36 uncached listings never asked. A re-save asks only
  the uncached ones again.
- The same can happen when a second user with a different pool warms the same postcode
  at the same time as TfL times out.
- If TfL recovers in the seconds between the third failing batch and the check call, the
  postcode can end `ready` early, with up to 36 listings never answered. Re-save to retry.
- The poll that decides `failed` or `ready` after three failing batches can take about
  10 seconds, up to about 15.
- The check-call test (Step 6 Redo 3) depends on the frozen dump's id order and
  coordinates. It asserts both, so a change makes it fail loudly.
- Listings TfL keeps failing make warm-up slower, up to about twice the polls.
- `schema.sql` changed with no migration. Every laptop must re-run `worker/scripts/seed.sh`
  (server stopped) after pulling, or a postcode-less save returns 500. The README says so.
- A soft wish over 120 characters is dropped, not shortened.
- Test mode depends on `wrangler dev --var` beating `.dev.vars` (checked on wrangler
  4.152.0). The probe and the fake's 401 would catch a change.
- The test-mode guard covers only `test_prefs.py` and `test_commute.py`. A new API test
  module must use the `fake` fixture.
- The probe leaves a `probe_*` user in the local D1. Re-seed to clear it.
- The filter loads all 635 listings and filters in Python. Fine at this size.
- Unknown tenure with unknown lease is excluded under a lease limit. There are none today.
- Anonymous TfL is slow: about 12 calls per poll, then a 30-second block after about 50
  calls. Any postcode used in the persona batch or the recording must be warmed by hand
  first.
- If two polls for one user run at the same time, both can count a failure.
- If zoneinfo is missing, "today" is taken in UTC. Still a Tuesday at 08:30.
- The status-write guard compares `updated_at` to the second, and no test covers it.
- The Step 6 and 7 tests prove "cached" from the fake's request log, not a D1 read. This
  gate's smoke check read the D1 directly and it matched.
- The kit-config Test line names :8788. Use `BASE_URL` and `FAKE_PORT` when another
  server holds that port.
- AMENDMENTS Step 6 rule (b) was edited in place, not appended. The original is in git
  history.
- The header line `Status` still reads "in progress (reopened 2026-10-25 for Step 8)".
- Leftover `wrangler dev --port 8790` node processes from earlier sessions (process
  groups 1751217 and 2148153) are still running, with no server bound. This gate did not
  start them and did not stop them.
- Every tradeoff above was accepted by the arbiter, not by a person.

### What could bite you

1. **Old local databases.** Step 8 made two `prefs` columns nullable with no migration. A
   laptop that pulls this and does not re-seed returns 500 on any save without a
   postcode. Yewen's laptop is the likely one, as soon as the frontend allows a blank
   postcode.
2. **The frontend and B4 meeting `commute: null`.** `web/src/api/types.ts` types a card's
   `commute` as never null and `commuteLine` reads it directly. Once B4 serves a card for
   a user with no postcode, the card can crash unless Yewen's change lands first, or B4
   keeps sending a `commute` object with `minutes: null` until then.
3. **A commute limit with commute not ready.** A user who sets a limit and opens the deck
   while TfL is still working sees a short deck, and on `failed` an empty one with
   `no_matches`, which reads as "nothing matches your wishes" rather than "commute
   failed".

### B4 HOOKS

All in `worker/src/filters.py`. `hard` is the `hard` dict from
`json.loads(prefs_row["parsed_json"])["hard"]`; keys are `max_price_gbp`, `min_bedrooms`,
`property_types`, `min_epc`, `tenure`, `min_lease_years`, `max_commute_min`, each null
when unset. A null limit is ignored. A listing field that is NULL fails a set limit, with one exception: under `min_lease_years`, a NULL lease passes for `freehold` and `share_of_freehold` (ruling Q4). It is still excluded for `leasehold` or unknown tenure, and a known lease below the minimum fails whatever the tenure.

- `async matching_listing_ids_for_postcode(db, hard, postcode) -> list[str]`: the call B4
  makes. `db` is `env.DB`, `postcode` is the normalised `prefs.commute_postcode`. It loads
  the cached minutes for that postcode and applies every limit including
  `max_commute_min`. A listing with no cache row, or a cached null, is excluded when
  `max_commute_min` is set. Ids come back in `id` order.
- `async matching_listing_ids(db, hard, commutes=None) -> list[str]`: the same without
  the cache lookup. `commutes` maps listing id to minutes. `None` switches the commute
  limit off (the TfL batch uses this). A dict applies it, a missing id counting as unknown.
- `passes(listing, hard, commute_minutes) -> bool`: the pure predicate. `listing` needs
  the filter columns (`FILTER_COLUMNS`); `commute_minutes` is an int or None.

B4 must also:

- Return 409 `prefs_missing` when there is no prefs row. Commute is optional (Step 8): do
  not refuse or wait on `commute_status`, which is `null` without a postcode and
  otherwise may be `pending` or `failed`. With a postcode, call
  `matching_listing_ids_for_postcode`; without one (`commute_postcode` null), call
  `matching_listing_ids(db, hard)` with `commutes=None`. The card `commute` is `null`
  with no postcode; with one, `commute.minutes` is `null` until that listing is cached.
- Commute exclusion stands (arbiter 2026-10-25, zero hard-constraint violations) and the
  contract now states it: with `max_commute_min` set, a listing with no cached time is not
  served, so the deck is short while `pending` and empty (`no_matches`) on `failed`. B4
  decides whether to add a commute-specific `empty_reason`; a new enum value means a
  `web/` change, which escalates.
- Put the delete of the user's unswiped served cards in `PUT /prefs`, in the same handler
  that stores the new prefs, once B4 creates the decisions table (kickoff ruling Q10).
- Poll cap: a permanent TfL 429 leaves a user `pending` for ever (see SPOTTED).
