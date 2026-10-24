# Feature: B1 Backend scaffold

- **Slug**: backend-scaffold
- **Owner**: Zsolt
- **Started**: 2026-10-24
- **Branch**: feat/backend-scaffold
- **BASE_SHA**: cb7cd3b010a8a492b741039a02e5a9d725d260dd
- **Status**: in progress
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

- [ ] Implemented
- [ ] Tested — evidence: (date)
- [ ] Best practices met — evidence: (date)
- [ ] Matches locked requirements — evidence: (date)
- [ ] No scope drift — evidence: (date)

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

- [ ] Implemented
- [ ] Tested — evidence: (date)
- [ ] Best practices met — evidence: (date)
- [ ] Matches locked requirements — evidence: (date)
- [ ] No scope drift — evidence: (date)

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

- [ ] Implemented
- [ ] Tested — evidence: (date)
- [ ] Best practices met — evidence: (date)
- [ ] Matches locked requirements — evidence: (date)
- [ ] No scope drift — evidence: (date)

---

## TRADEOFFS

| Date | Step | What | Why | Fix cost |
| ---- | ---- | ---- | --- | -------- |
| 2026-10-24 | 1 | `seed.sh` runs wrangler through `npx --yes wrangler`, so the first run downloads wrangler (about 20 s) and needs network | `wrangler` on PATH is a Windows pnpm shim in WSL; wrangler is not a project dependency | Small: pin wrangler in a `package.json`, or document a global install — accepted by arbiter 2026-10-24: no project dependency added and pywrangler already needs wrangler via Node; pinning it in a `package.json` would be an unapproved dependency. Step 4 README must state Node/npx is required and the first seed run needs network |
| 2026-10-24 | 1 | `app = FastAPI()` has no `/api` prefix yet; routes will use `APIRouter(prefix="/api")` | `FastAPI(root_path=...)` is deprecated and printed an error in the dev log | None: step 2 adds the router — accepted by arbiter 2026-10-24: step 2 done-when already requires `/api/users`, so the reviewer checks the prefix there |

---

## SPOTTED, NOT FIXED

- `worker/pylock.toml` is generated by `pywrangler dev` and is not in the declared file scope (the scope names `uv.lock`). Left untracked in the working tree; decide whether to commit it or gitignore it. Low. resolved by Step 1 redo 2026-10-24

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
