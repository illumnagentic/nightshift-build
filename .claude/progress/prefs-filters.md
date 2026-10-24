# Feature: B3 Preferences and filters

- **Slug**: prefs-filters
- **Owner**: Zsolt
- **Started**: 2026-10-24
- **Branch**: feat/prefs-filters
- **BASE_SHA**: 0755bcb39f9d837b2b4285cd495adf7101cea35d
- **Status**: in progress
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
2026-10-24 | step 3 | `test_commute.py` holds two pure unit tests (classify, URL and Tuesday) that need the server because of the module `pytestmark` | the step's file scope has no other test file for tfl.py | move them to a server-less module in a later step — FIX_NOW by arbiter 2026-10-24: cheap (a file move, under 30 lines), and it lets the unit-only run cover tfl.py; see AMENDMENTS (arbiter) Step 5

---

## SPOTTED, NOT FIXED

2026-10-24 | `worker/README.md` | test instructions do not yet describe test mode or the fake upstream | low (Step 4 covers the README) — accepted by arbiter 2026-10-24: in Step 4's scope and done-when; Step 4 must also say test mode is mandatory and that the default BASE_URL (8787) is the normal dev server

2026-10-24 | `worker/tests/test_prefs.py` | no guard if pytest runs against a normal dev server (real key, no GEMINI_BASE): the first PUT would reach the real Mubit; Q13 wanted a separate test vars file | medium (Step 4 README must say test mode is mandatory; consider a guard test that fails fast) — resolved by Step 1 redo 2026-10-24

2026-10-24 | `worker/src/entry.py` GET /prefs | the status-write race guard compares `updated_at`, which has one-second resolution; a re-save in the same second as the previous save could be overwritten by a stale batch, and no test covers the guard | low (a PUT includes an LLM call, so same-second re-saves are not realistic) | step 3 review — accepted by arbiter 2026-10-24: unreachable in practice (each PUT waits on an LLM call); the worst case is a stale status the next poll or re-save corrects; nothing later depends on it
2026-10-24 | `worker/src/tfl.py` run_batch | a permanent TfL 429 leaves a user `pending` for ever (by design, tradeoff logged); the user can still re-save, but the frontend has no timeout | low to medium, B4/F4 may want a poll cap | step 3 review — accepted by arbiter 2026-10-24: not observed (the pilot's 429 cleared in ~30 s); re-saving resets it; no `web/` change is made or needed now; if B4 or F4 wants a poll cap, that work escalates there (any `web/` change does)

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

- Check `prefs.commute_status` before serving a deck: 409 `prefs_missing` (no prefs row),
  `commute_pending`, `commute_failed`, as `docs/api-contract.md` says. The filters do not
  check it; a pending postcode simply has an incomplete cache.
- Put the delete of the user's unswiped served cards in `PUT /prefs`, in the same handler
  that stores the new prefs, once B4 creates the decisions table (kickoff ruling Q10).
- Poll cap: a permanent TfL 429 leaves a user `pending` for ever (see SPOTTED).

