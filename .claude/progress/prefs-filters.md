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

_None._

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

- [ ] Implemented
- [ ] Tested — evidence: (date)
- [ ] Best practices met — evidence: (date)
- [ ] Matches locked requirements — evidence: (date)
- [ ] No scope drift — evidence: (date)

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

- [ ] Implemented
- [ ] Tested — evidence: (date)
- [ ] Best practices met — evidence: (date)
- [ ] Matches locked requirements — evidence: (date)
- [ ] No scope drift — evidence: (date)

### Step 4 — README and B4 handover

**Goal**: anyone can run the backend and its tests in test mode; B4 knows the hooks.

**Files in scope**: `worker/README.md`, `.claude/kit-config.md` (Commands lines only,
if the test command changes), this progress file (a `B4 HOOKS` note under HANDOVER).

**Done when**: the README sequence (seed → dev server in test mode → pytest) is run
from a clean state and passes; the B4 hooks are written down: the
`matching_listing_ids` signature, and that the drop-unswiped-cards delete belongs in
`PUT /prefs` once B4 creates the decisions table.

**Evidence location**: `evidence/prefs-filters/step-4.md`

- [ ] Implemented
- [ ] Tested — evidence: (date)
- [ ] Best practices met — evidence: (date)
- [ ] Matches locked requirements — evidence: (date)
- [ ] No scope drift — evidence: (date)

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

---

## SPOTTED, NOT FIXED

2026-10-24 | `worker/README.md` | test instructions do not yet describe test mode or the fake upstream | low (Step 4 covers the README) — accepted by arbiter 2026-10-24: in Step 4's scope and done-when; Step 4 must also say test mode is mandatory and that the default BASE_URL (8787) is the normal dev server

2026-10-24 | `worker/tests/test_prefs.py` | no guard if pytest runs against a normal dev server (real key, no GEMINI_BASE): the first PUT would reach the real Mubit; Q13 wanted a separate test vars file | medium (Step 4 README must say test mode is mandatory; consider a guard test that fails fast)

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
