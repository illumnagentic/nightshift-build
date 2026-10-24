# Feature: B1 Backend scaffold

- **Slug**: backend-scaffold
- **Owner**: Zsolt
- **Started**: 2026-10-24
- **Branch**: feat/backend-scaffold
- **BASE_SHA**: cb7cd3b010a8a492b741039a02e5a9d725d260dd
- **Status**: complete (2026-10-24)
- **Mode**: full automation (on since 2026-10-24)

---

## REQUIREMENTS (LOCKED)

Human, in session, 2026-10-24:

> "start backend build, with full auto mode"

`docs/plan.md`, Backend — Zsolt:

> **B1 Scaffold** — `feat/backend-scaffold` — Python Worker + FastAPI, local D1
> schema, seed script, username-only accounts, Mubit gateway client.

`docs/decisions.md`, binding lines:

> **Backend host.** Decided: 2026-10-24 — Python Worker with FastAPI, run locally with
> `pywrangler dev`.

> **Database.** Decided: 2026-10-24 — D1, local only (the copy `pywrangler dev` keeps on
> disk). One per laptop, filled by a seed script in the repo. No cloud instance.

> **Deploy.** Decided: 2026-10-24 — not deployed. Everything runs locally (`pywrangler
> dev` + Vite dev server) [...] Yewen runs the backend locally too, against a local D1
> filled by the same seed script, so both laptops see the same data.

> **Accounts.** [...] **Username only, no passwords.** Pick or create a user; the API
> takes the user_id.

> **Curator model.** [...] Gemini, native Gemini API through Mubit
> (`https://api.mubit.ai/gemini`). [...] The Gemini key goes into the Mubit console
> under Provider keys; the app only ever sends the Mubit key.

> **Correction → model update path.** [...] Every curator decision stores Mubit's
> `x-middleware-request-id` (`mreq_…`) [...]

> **Secrets.** `.env` and `.dev.vars` gitignored, keys shared out of band.

`docs/api-contract.md`, binding sections: General (base URL
`http://localhost:8787/api`, error shape, 422 `invalid_request`, unknown is `null`),
Users (`GET /users`, `POST /users`, 409 `username_taken`).

### Source

Quoted above. Contract: `docs/api-contract.md` on `main` at `cb7cd3b`.

### Explicitly out of scope

- Every endpoint other than `GET /users` and `POST /users`. That includes the
  `X-User-Id` header check and 401 `unknown_user`: its first consumer is B3
  (`/prefs`), so it is built there.
- App tables other than `users` (prefs, decisions, feedback, favourites, profile,
  flags, commute cache). Each belongs to the feature that first writes it.
- Curator prompt, response schema, thinking setting for production calls (B4).
- Photo flags (`feat/photo-flags`), TfL, personas, eval.
- Deploying to Cloudflare, a cloud D1, any Worker secret beyond local `.dev.vars`.
- Changing `dataset/d1/schema.sql`, `dataset/d1/seed.sql` or any `dataset/` script.
- Anything under `web/`, and any change to `docs/api-contract.md`.
- `google-genai` or `openai` SDKs: the gateway client is a plain HTTPS POST with the
  runtime `fetch` (decisions: Image textualisation workflow, "No `google-genai`";
  spike: plain runtime `fetch` passed).
- `httpx` (FastAPI's `TestClient` needs it; not approved). Tests use stdlib `urllib`
  against a running `pywrangler dev`.

---

## AMENDMENTS

_None._

---

## RULES IN FORCE

| Rule | Source | Applies to |
| ---- | ------ | ---------- |
| Commits only via `.claude/scripts/safe-commit.sh`, title only, no signature | `.claude/CLAUDE.md` | commits |
| Commit/PR title `type(scope): message`; scopes: worker, web, db, prep, kit, api | `.claude/CLAUDE.md`, `.claude/kit-config.md` | commits, PR |
| No scope creep: touch only the step's declared files | `.claude/CLAUDE.md` #1 | code, docs |
| Dependencies: only `fastapi`, `google-genai`, `pytest` may be added; anything else escalates. `pywrangler` is run with `uvx --from workers-py`, not added to the project | `.claude/CLAUDE.md` #2, kit-config, decisions (Backend host) | code, pyproject |
| Never weaken a test to pass | `.claude/CLAUDE.md` #3 | tests |
| Walk the ladder; no speculative generalisation | `.claude/CLAUDE.md` #4 | code |
| Tradeoffs logged when made; arbiter rules on them | `.claude/CLAUDE.md` #5, Modes | progress file |
| Only step-reviewer ticks, with evidence and date | `.claude/CLAUDE.md` #6 | progress file |
| Out-of-scope problems go in SPOTTED, NOT FIXED | `.claude/CLAUDE.md` #7 | progress file |
| Plain British English, no banned marketing words | `.claude/CLAUDE.md` | docs, comments |
| Error body `{"error": {"code", "message"}}`, status matches code; unknown is `null` | `docs/api-contract.md` General | code |
| App sends only the Mubit key (`x-goog-api-key` for Gemini, never `?key=`); keys never printed, logged or committed; `.dev.vars` gitignored | mubit-gateway skill, decisions (Secrets) | code, evidence, commits |
| Store `x-middleware-request-id` from every Mubit call | decisions (Correction path), mubit-gateway skill | code |
| No Mubit call beyond a single test call (money) | `.claude/CLAUDE.md` Modes | commands |
| Evidence is metadata only, under `evidence/backend-scaffold/` | `.claude/CLAUDE.md`, decisions (Evidence) | evidence |
| Python reading downloaded files runs with `-I` | session environment rule | commands |

---

## PLAN

All paths relative to the repo root. New backend lives in `worker/`.

### Step 1 — Worker skeleton, local D1 and seed script

**Goal**: A Python Worker running FastAPI under `pywrangler dev`, bound to a local D1
that a seed script fills with the listings data and an empty `users` table.

**Files in scope**: `worker/pyproject.toml`, `worker/wrangler.jsonc`,
`worker/src/entry.py`, `worker/schema.sql` (app tables: `users` only),
`worker/scripts/seed.sh`, `worker/.gitignore`, `worker/uv.lock` (if generated).
`worker/.dev.vars` is created locally from `.env` and never committed.

**Done when**: `worker/scripts/seed.sh` exits 0 on a fresh and on an already-seeded
local D1 (it resets local state, then applies `dataset/d1/schema.sql`,
`worker/schema.sql`, `dataset/d1/seed.sql`); afterwards `SELECT count(*) FROM listings`
is 635 and `SELECT count(*) FROM users` is 0. `pywrangler dev` starts on :8787 and
`GET /docs` returns 200.

**Evidence location**: `evidence/backend-scaffold/step-1.md` (commands run and their
output counts).

- [x] Implemented — evidence: worker/ files present, seed.sh and entry.py read (2026-10-24)
- [x] Tested — evidence: reviewer re-run: seed.sh exit 0 twice, listings=635, users=0, pywrangler dev GET /docs 200, /openapi.json 200, server stopped by PID (2026-10-24)
- [x] Best practices met — evidence: set -euo pipefail, cwd-independent paths, .dev.vars gitignored (git check-ignore), no .env value found in worker/, evidence/ or progress file (2026-10-24)
- [x] Matches locked requirements — evidence: FastAPI Python Worker, D1 binding, seed order schema/worker schema/seed.sql, users table only, local only (2026-10-24)
- [x] No scope drift — evidence: only worker/ declared files plus generated worker/pylock.toml (declared in SPOTTED); dataset/, web/, docs/ untouched (2026-10-24)

**Redo (arbiter FIX_NOW, 2026-10-24)**: gitignore the generated `worker/pylock.toml`.
Files: `worker/.gitignore` only. Done when `git check-ignore worker/pylock.toml` exits 0
and `git status --porcelain worker/` no longer lists it.

- [x] Redo implemented — evidence: worker/.gitignore line 7 `pylock.toml`; `git check-ignore worker/pylock.toml` exit 0 (2026-10-24)
- [x] Redo reviewed — evidence: check-ignore exit 0, `git status --porcelain -uall worker/` lists no pylock.toml, check-process-refs.sh exit 0 (2026-10-24)

### Step 2 — Username-only accounts

**Goal**: `GET /api/users` and `POST /api/users` per the contract, with the contract's
error shape for 409 `username_taken` and 422 `invalid_request`.

**Files in scope**: `worker/src/entry.py`, `worker/src/*.py` (new modules only if
`entry.py` passes ~150 lines; name them in the step report), `worker/tests/test_users.py`,
`worker/pyproject.toml` (pytest in a dev group only).

**Done when**: against a freshly seeded `pywrangler dev`, `worker/tests/test_users.py`
passes and covers: create returns 201 `{user_id, username}`; list includes it; same
username again (any case) is 409 `username_taken`; missing, empty, whitespace,
over-long or non-`[A-Za-z0-9_-]` username is 422 `invalid_request`; a malformed JSON
body is 422 `invalid_request`; every error body matches the contract shape. Username
rules: trimmed, 1–32 chars, `[A-Za-z0-9_-]`, unique ignoring case. `user_id` is an
opaque random string.

**Evidence location**: `evidence/backend-scaffold/step-2.md` (pytest output summary).

- [x] Implemented — evidence: worker/src/entry.py /api router, GET/POST /users, contract error handlers (2026-10-24)
- [x] Tested — evidence: reviewer re-run: seed.sh exit 0, pywrangler dev, pytest tests -q 24 passed exit 0; curl malformed JSON gives 422 invalid_request; GET /api/users gives {"users":[]} (2026-10-24)
- [x] Best practices met — evidence: parameterised SQL (bind), UNIQUE COLLATE NOCASE decides duplicates, token_hex ids, no secrets, uv.lock only fastapi/pytest and transitive deps (2026-10-24)
- [x] Matches locked requirements — evidence: contract 201/409/422 shapes, username rules, opaque u_ ids, username-only, check-process-refs.sh exit 0 (2026-10-24)
- [x] No scope drift — evidence: diff touches only entry.py, tests/test_users.py, pyproject.toml, uv.lock (Step 1 scope), evidence/step-2.md, progress file (2026-10-24)

**Redo (arbiter FIX_NOW, 2026-10-24)**: qa-gate finding — 404, 405 and unhandled 500
responses do not use the contract error shape (contract General: "Errors always have
this shape"). Files: `worker/src/entry.py`, `worker/tests/test_users.py`,
`evidence/backend-scaffold/step-2.md`. Add a handler for Starlette's `HTTPException`
mapping 404 to `not_found`, 405 to `method_not_allowed`, any other status to
`http_error`, keeping the status and any `Allow` header; and an unhandled-exception
path returning 500 `internal_error` with a fixed message (no exception text, no
traceback in the body; log it). If Starlette's `Exception` handler re-raises and the
body is lost under the Workers ASGI adapter, use an `@app.middleware("http")`
try/except instead. Do not edit `docs/api-contract.md`: the new codes give undefined
errors the contract's shape, which is not a breaking change. Done when: test_users.py
covers GET `/api/nope` 404 `not_found` and DELETE `/api/users` 405
`method_not_allowed`, both in contract shape; full suite passes against a freshly
seeded `pywrangler dev`; a manual 500 check (drop `users` in local D1, GET
`/api/users`, expect 500 `{"error":{"code":"internal_error",...}}`, then re-seed) is
recorded in `evidence/backend-scaffold/step-2.md`.

- [x] Redo implemented — evidence: entry.py http_error_handler + internal_error_guard middleware; test_unknown_path_is_404_contract_shape, test_wrong_method_is_405_contract_shape (2026-10-24)
- [x] Redo reviewed — evidence: reviewer re-run seed exit 0, pytest 36 passed exit 0, DELETE /api/users 405 method_not_allowed with Allow header, DROP TABLE users gives 500 internal_error with fixed message, re-seeded (users=0), check-process-refs exit 0 (2026-10-24)

### Step 3 — Mubit gateway client

**Goal**: A small module that sends a native Gemini `generateContent` request through
`https://api.mubit.ai/gemini` with the Mubit key and returns the parsed JSON and the
`x-middleware-request-id`, raising a clear error (status, Mubit `code` if any, request
ID) on non-2xx.

**Files in scope**: `worker/src/mubit.py`, `worker/tests/test_mubit.py`,
`worker/scripts/mubit_ping.py`.

**Done when**: request building and response parsing are pure functions, unit-tested
without network (URL, `x-goog-api-key` header, no `?key=`, request ID extracted,
`middleware_gateway_error` vs provider error told apart). The async call uses the
Workers runtime `fetch`, imported inside the function so tests run outside the runtime.
`worker/scripts/mubit_ping.py` (stdlib `urllib`, key read from `.env`, never printed)
makes exactly one live call to `gemini-3.8-flash` with an explicit low thinking setting
using the same build/parse functions, and writes status, model version, token counts
and the `mreq_` ID to evidence.

**Evidence location**: `evidence/backend-scaffold/step-3.md` (unit test summary, the
one live call's metadata).

- [x] Implemented — worker/src/mubit.py, worker/tests/test_mubit.py, worker/scripts/mubit_ping.py; diff within declared scope (2026-10-24)
- [x] Tested — evidence: `uv run --group dev pytest tests/test_mubit.py -q` 10 passed exit 0; test_users.py still collects (34); one live call in evidence/backend-scaffold/step-3.md, 200, mreq_01a16ea1592f7052b9714df8ae035fb2 (2026-10-24)
- [x] Best practices met — evidence: key only in x-goog-api-key, no ?key= (test_build_request_url_headers_body), never in error text (test_key_never_in_error), ping prints metadata only; fetch(url, method=, headers=, body=) and response.status/.headers.get/.text() checked against python_modules/workers/fetch.py and response.py (2026-10-24)
- [x] Matches locked requirements — evidence: request ID returned and MubitError carries status/code/request_id; gateway vs provider told apart in tests; fixed gemini-3.8-flash with explicit thinkingLevel low (2026-10-24)
- [x] No scope drift — evidence: git status shows only the 3 declared files, the evidence file and the progress file changed; no hunk outside Step 3 (2026-10-24)

### Step 4 — Run instructions

**Goal**: Anyone (Yewen's laptop included) can set up, seed, run and test the backend
from written steps, and the kit knows the backend commands.

**Files in scope**: `worker/README.md`, `.claude/kit-config.md` (Commands and Project
type lines only).

**Done when**: following `worker/README.md` from a clean clone (`.dev.vars`, seed, dev
server, tests) works when run by the reviewer; kit-config Test / Run locally lines
name the backend commands alongside the web ones.

**Evidence location**: `evidence/backend-scaffold/step-4.md` (reviewer's run of the
README steps).

- [x] Implemented — worker/README.md, kit-config Commands lines, evidence/backend-scaffold/step-4.md present (2026-10-24)
- [x] Tested — evidence: clean-clone README run: seed exit 0, 34 passed, server stopped; evidence/backend-scaffold/step-4.md (2026-10-24)
- [x] Best practices met — evidence: README states Node/npx and network; no banned words in README, kit-config, evidence; check-process-refs.sh exit 0 (2026-10-24)
- [x] Matches locked requirements — evidence: kit-config Test, Test (single file), Run locally name backend commands beside web ones; README run from clean clone (2026-10-24)
- [x] No scope drift — evidence: only worker/README.md and kit-config Commands+Project type lines changed; redo touched evidence file only (2026-10-24)

**Redo (arbiter FIX_NOW, 2026-10-24)**: step-reviewer FAIL — process-reference hit in
the evidence heading. File: `evidence/backend-scaffold/step-4.md` only. Rename the
heading to subject language and rewrite the closing note to describe the clean-clone
run (seed exit 0, 34 passed; only cold-cache downloads unobserved). Done when
`.claude/scripts/check-process-refs.sh` exits 0.

- [x] Redo implemented — heading now subject language, closing note describes clean-clone run (2026-10-24)
- [x] Redo reviewed — evidence: check-process-refs.sh exit 0, banned-word grep clean (2026-10-24)

**Redo (arbiter FIX_NOW, 2026-10-24)**: qa-gate finding — kit-config backend "Test
(single file)" names `tests/test_mubit.py` where the web entry uses a `<path>`
placeholder. File: `.claude/kit-config.md` (that line only). Done when the backend
part reads `cd worker && uv run --group dev pytest <path> -q` and no other line in
kit-config changed.

- [x] Redo implemented — evidence: kit-config.md line 23 backend part now `pytest <path> -q`, diff is that single line (2026-10-24)
- [x] Redo reviewed — evidence: git diff HEAD single-line, web part unchanged; pytest tests/test_mubit.py 10 passed exit 0; check-process-refs exit 0 (2026-10-24)

**Redo (arbiter FIX_NOW, 2026-10-24)**: README re-seed note. File: `worker/README.md`
only. The seed section and the re-seed note for test users both say to stop
`pywrangler dev` before running `worker/scripts/seed.sh` and restart it afterwards,
because a running server keeps a stale view of the D1 and returns 500. Done when no
other file changes, `.claude/scripts/check-process-refs.sh` exits 0, no banned words.

- [x] Redo implemented — evidence: worker/README.md two additions (seed section, test re-seed note); git diff HEAD -- worker/README.md is only those (2026-10-24)
- [x] Redo reviewed — evidence: diff limited to two README additions, accurate, no banned words; check-process-refs.sh exit 0 (2026-10-24)

---

## TRADEOFFS

| Date | Step | What | Why | Fix cost |
| ---- | ---- | ---- | --- | -------- |
| 2026-10-24 | 1 | `seed.sh` runs wrangler through `npx --yes wrangler`, so the first run downloads wrangler (about 20 s) and needs network | `wrangler` on PATH is a Windows pnpm shim in WSL; wrangler is not a project dependency | Small: pin wrangler in a `package.json`, or document a global install — accepted by arbiter 2026-10-24: no project dependency added and pywrangler already needs wrangler via Node; pinning it in a `package.json` would be an unapproved dependency. Step 4 README must state Node/npx is required and the first seed run needs network |
| 2026-10-24 | 1 | `app = FastAPI()` has no `/api` prefix yet; routes will use `APIRouter(prefix="/api")` | `FastAPI(root_path=...)` is deprecated and printed an error in the dev log | None: step 2 adds the router — accepted by arbiter 2026-10-24: step 2 done-when already requires `/api/users`, so the reviewer checks the prefix there |
| 2026-10-24 | 2 | Duplicate detection maps any exception whose text contains `UNIQUE constraint failed` to 409; D1 gives no error code to match on | Only string matching works through the Pyodide JS exception; a pre-check alone would race | Small: match on a structured D1 error code if the runtime ever exposes one — accepted by arbiter 2026-10-24: no error code is exposed through Pyodide, the UNIQUE constraint still decides the race, and any other error is re-raised, so a mismatch fails loudly as 500 rather than a false 409 |
| 2026-10-24 | 2 | Tests need a running `pywrangler dev` and a seeded DB; no in-process test | `TestClient` needs `httpx`, not approved; D1 only exists in the Worker runtime | Large: add `httpx` and a fake D1, which would not test the real binding — accepted by arbiter 2026-10-24: already the locked approach (httpx out of scope, stdlib urllib against `pywrangler dev`); testing the real D1 binding is the better test. Step 4 README must give the seed, dev-server and pytest sequence |
| 2026-10-24 | 2 | All 422 bodies for malformed or mistyped JSON share one generic message | The contract says the frontend shows `error.message` and replicates no checks; per-field messages were not asked for | Small: map pydantic error types to messages — accepted by arbiter 2026-10-24: contract wants code `invalid_request` and a displayable message, not per-field messages; the generic message names the expected body shape, and the frontend sends that shape anyway |
| 2026-10-24 | 3 | `generate_content` (Workers `fetch` transport) is not exercised live or in a test; the ping uses urllib. The runtime `fetch` call and `response.headers.get(...)` follow the workers-py API from memory and the 24 Oct spike | The workers module exists only inside the runtime, and an extra endpoint to hit it was out of scope | Small: B4's first curator call through `pywrangler dev` exercises it; fix there if the response API differs — accepted by arbiter 2026-10-24: step-reviewer checked the fetch call and Response API against the vendored workers SDK, and a live runtime test now would need another paid Mubit call, which this feature may not make. B4's first curator call under `pywrangler dev` exercises it |
| 2026-10-24 | 3 | Only `x-middleware-request-id` is copied out of the runtime's response headers, so `retry-after` and `x-should-retry` are not available to callers | Nobody consumes them yet; the runtime Headers object has no confirmed iteration API | Small: copy more headers once a caller retries — accepted by arbiter 2026-10-24: no caller retries, so copying more headers now would be speculative (ladder rung 1); MubitError already carries status and request ID, enough to decide on a retry later |
| 2026-10-24 | 3 | The Gemini-format gateway error type is read from `error.type` or ErrorInfo `metadata.type`, a guess; the skill only says the code is the ErrorInfo `reason` | No real gateway refusal body was seen (spend limited to one call) | Small: confirm on the first real refusal and adjust `parse_response` — accepted by arbiter 2026-10-24: confirming needs a real refusal body, which needs more paid calls; a wrong guess only mislabels gateway vs provider in the error, and status, code and request ID are still raised |
| 2026-10-24 | 4 | README steps were run on the existing working tree, not a clean clone; kit-config's backend Lint, Typecheck and Build lines are left blank (no such commands exist) | A clean clone would redownload wrangler and Python packages; inventing commands is barred | Small: reviewer repeats from a fresh clone — accepted by arbiter 2026-10-24: the reviewer has since run the README from a clean clone (seed exit 0, 34 tests passed); only the first-run download with cold npx/uv caches is unobserved, and the README already states Node/npx and network on first run. Blank Lint/Typecheck/Build lines are correct, as no such backend commands exist |
| 2026-10-24 | 2 redo | 500 guard is an `@app.middleware("http")` try/except, chosen without trying the `Exception` handler route | The handler route re-raises after responding and the Workers ASGI adapter may drop the body; middleware is the redo's stated fallback | Small: try the `Exception` handler if the middleware causes trouble (reviewer observed 500 `internal_error` body works) — accepted by arbiter 2026-10-24: the middleware route is the redo's stated fallback and the reviewer saw it return the contract 500 body under `pywrangler dev`; trying the other route now buys nothing |
| 2026-10-24 | 2 redo | Statuses other than 404/405 reaching the HTTPException handler get the message "Request not allowed.", which can be inaccurate | No other HTTPException status is raised today; a per-status message table would be speculative | Small: add messages when a route raises another status — accepted by arbiter 2026-10-24: no route raises HTTPException; app errors go through `ApiError` with contract codes and messages, and B3's 401 `unknown_user` will too. The path is unreachable today, so a message table would be speculative |

---

## SPOTTED, NOT FIXED

- `worker/pylock.toml` is generated by `pywrangler dev` and is not in the declared file scope (the scope names `uv.lock`). Left untracked in the working tree; decide whether to commit it or gitignore it. Low. resolved by Step 1 redo 2026-10-24
- `worker/README.md` ping section: the ping reads repo-root `.env` while the dev server reads `worker/.dev.vars`, so the key lives in two files. Low. — accepted by arbiter 2026-10-24: by design, Step 1 creates `.dev.vars` from `.env` and Step 3's reviewed done-when has the ping read `.env`; both files are gitignored and the README states which file each reads
- `worker/uv.lock` is generated by `uv run --group dev` and is untracked. Step 1 scope names it "if generated"; commit it with step 2. Low. — accepted by arbiter 2026-10-24: commit it with the step 2 commit. Two laptops run the backend, and a lockfile keeps fastapi/pytest versions identical on both; it is declared in Step 1 scope, not gitignored, and holds only fastapi, pytest and their transitive deps
- `worker/scripts/mubit_ping.py` parses `.env` with a plain `KEY=value` split, so an `export KEY=...` line is not read (qa-gate). Low. — accepted by arbiter 2026-10-24: the repo `.env` has no `export` lines, the ping has already made its one call and must not be re-run casually, and a missed key fails loudly with a KeyError before any request is sent
- Re-seeding the local D1 while `pywrangler dev` runs leaves the server returning 500 until it is restarted (step 2 redo). Low. — resolved by Step 4 redo 2026-10-24 (README re-seed note)
- The 405 `Allow` header for `DELETE /api/users` lists only `GET`, though POST is also allowed (GET and POST are separate routes on one path; Starlette reports the first). Low. — accepted by arbiter 2026-10-24: the web client never sends a wrong method and nothing reads `Allow`; correcting it means re-matching routes in the handler, Starlette's job, for no consumer

---

## VERIFICATION

- [x] All step checkboxes ticked with evidence — qa-gate: 4 steps x 5 boxes, plus 5 redos x 2 boxes (Step 1 once, Step 2 once, Step 4 three times), all dated 2026-10-24; REQUIREMENTS (LOCKED) block byte-identical in every commit since bcc34d6 (2026-10-24)
- [x] Every evidence path in this file exists — qa-gate: evidence/backend-scaffold/step-1.md to step-4.md present (2026-10-24)
- [x] Test suite run — result: backend `uv sync --group dev` exit 0; `worker/scripts/seed.sh` exit 0 (listings 635, users 0); `uv run --group dev pytest tests -q` 36 passed, exit 0, against a fresh `pywrangler dev`; web `npm ci` exit 0, `npm test` 121 passed (5 files), exit 0 (2026-10-24)
- [ ] Lint run — result: not configured in kit-config (no lint command for web or backend); not run
- [x] Typecheck run — result: web `npm run typecheck` exit 0; no backend typecheck configured (2026-10-24)
- [x] Build run — result: web `npm run build` exit 0; no backend build configured (2026-10-24)
- [x] Diff contains no files outside declared scope — qa-gate: all 18 files map to a step's Files in scope, an Evidence location or this file (2026-10-24)
- [x] Tradeoff ledger reviewed — signed by arbiter (full automation): all 11 TRADEOFFS entries carry `accepted by arbiter`; all 6 SPOTTED, NOT FIXED entries carry an arbiter verdict or a resolved marker (2026-10-24)
- [ ] Human eye test completed — not human-verified (full automation) — smoke check: seed.sh exit 0, `pywrangler dev` on :8787. curl: GET /api/users 200; GET /docs 200; POST new user 201 `{user_id: "u_…", username}`; same name upper-cased 409 `username_taken`; `"al ex"` 422 `invalid_request`; malformed JSON 422 `invalid_request`; GET /api/nope 404 `{"error":{"code":"not_found","message":"No such endpoint."}}`; DELETE /api/users 405 `{"error":{"code":"method_not_allowed","message":"Request not allowed."}}` with `Allow: GET`. Vite dev server on :5173: GET /api/users through the proxy 200 with the new user, GET /api/nope 404 in contract shape. Both servers stopped by process group; local D1 re-seeded afterwards (users empty). Mubit not called.

QA-GATE: PASS 2026-10-24

---

## HANDOVER

**What was built**

There is now a backend in `worker/`. It runs on your laptop as a Cloudflare Python
Worker with FastAPI, against a local D1 database. A seed script fills that database
with the 635 listings and an empty users table. You can list users and create a user
by username alone, and every error, including unknown paths and wrong methods, comes
back in the contract's `{"error": {"code", "message"}}` shape. There is also a small
client for calling Gemini through Mubit, which the curator and photo flags will use.
Nothing in the running app calls it yet.

**What to check yourself**

1. Make sure no `pywrangler dev` or `wrangler dev` is running: `ss -ltn | grep 8787`
   should print nothing. Stop any you find first.
2. From the repo root, run `worker/scripts/seed.sh`. It should end with exit 0. The
   first run downloads wrangler, so it needs network.
3. Check the counts: `cd worker && npx wrangler d1 execute haka --local --command "SELECT (SELECT count(*) FROM listings), (SELECT count(*) FROM users)"`.
   You should see 635 and 0.
4. Create `worker/.dev.vars` with `MUBIT_API_KEY=...` if it is not there. It is
   gitignored.
5. In `worker/`, run `uvx --from workers-py pywrangler dev`. Wait for "Ready on
   http://localhost:8787".
6. `curl -s http://localhost:8787/api/users` should return `{"users":[]}`.
7. `curl -si -X POST -H 'Content-Type: application/json' -d '{"username":"alex"}' http://localhost:8787/api/users`
   should return 201 and `{"user_id":"u_…","username":"alex"}`.
8. Send the same request with `"ALEX"`. You should get 409 and
   `{"error":{"code":"username_taken",…}}`.
9. Send `{"username":"al ex"}`. You should get 422 and `invalid_request`.
10. `curl -si http://localhost:8787/api/nope` should give 404 and
    `{"error":{"code":"not_found","message":"No such endpoint."}}`.
    `curl -si -X DELETE http://localhost:8787/api/users` should give 405 and
    `{"error":{"code":"method_not_allowed",…}}`.
11. In a second terminal, `cd worker && uv run --group dev pytest tests -q`. Expect 36
    passed. This adds test users (`t_…`) to the local D1. To clear them, stop the dev
    server, re-seed, then start it again.
12. Start the web app with `cd web && npm run dev` (leave `VITE_API_MODE` unset or not
    `mock`). Open http://localhost:5173. The user picker should list `alex`, and
    creating a user there should work. The deck screen will fail after that, because
    `/prefs` and `/deck` do not exist yet.
13. Do not run `worker/scripts/mubit_ping.py` unless you mean to: it makes a paid call.

**Tools that will help**

- curl or Postman for the endpoints. Look at the status code as well as the body; every
  non-2xx body should have exactly `error.code` and `error.message`.
- Browser devtools, Network tab, on http://localhost:5173: requests to `/api/users`
  should go to the same origin and come back 200 or 201, with no CORS errors.
- `npx wrangler d1 execute haka --local --command "SELECT * FROM users"` in `worker/`
  to see what is stored.
- The `pywrangler dev` terminal: Python tracebacks from the Worker appear there. A 500
  body says only "Something went wrong on the server."; the cause is in this log.

**What is not done**

- The Mubit client's real call path (`generate_content`, using the Workers `fetch`) has
  never run. Only request building and response parsing are tested, and the one live
  call used Python's `urllib`. B4's first curator call is its first real test.
- How the client tells a Mubit gateway refusal from a Gemini error is a guess. No real
  refusal body has been seen.
- Only `x-middleware-request-id` is read from Mubit responses; retry headers are not.
- A duplicate username is detected by matching the text "UNIQUE constraint failed" in
  the D1 error. If D1 words it differently, a duplicate becomes a 500, not a 409.
- All bad-body 422s share one generic message, not one per field.
- The 405 `Allow` header for `/api/users` says `GET` only, though POST is allowed too.
- Any HTTP error other than 404 or 405 from routing gets code `http_error` and the
  message "Request not allowed.", which may be wrong. No route raises one today.
- The 500 guard is middleware; the alternative exception-handler route was not tried.
- The API tests need a seeded, running dev server. There is no in-process test.
- `seed.sh` needs Node and `npx`, and network on first run, to fetch wrangler.
- The README was run from a clean clone, but with warm caches. A truly cold first run
  is unobserved.
- `mubit_ping.py` does not read `export KEY=...` lines in `.env`. It reads repo-root
  `.env`; the dev server reads `worker/.dev.vars`. The key lives in both.
- No lint, backend typecheck or backend build commands exist.
- The `X-User-Id` check and 401 `unknown_user` are not built; B3 builds them.
- No human has looked at this. The checks above were run by the QA agent in full
  automation.

**What could bite you**

- The Mubit client in the Worker. It is written against the Workers `fetch` API from
  the SDK source, not from a run. If the response object differs, B4's first curator
  call fails, and that is on the critical path to Sat 13:00. Test it early in B4.
- Stray dev servers. A `wrangler dev` tree started at 16:52 in `worker/` is still
  running (not on :8787 at the time of this check). A second server, or one left
  running across a re-seed, serves a stale D1 and returns 500. Check with
  `ss -ltn | grep 8787` before testing.
- `seed.sh` deletes all local D1 state, including users, every time. Once B3 to B5
  write prefs, swipes and feedback, re-seeding wipes them too. Do not re-seed during
  the persona batch.
