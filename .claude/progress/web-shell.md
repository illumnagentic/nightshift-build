# Feature: F1 Shell (frontend)

- **Slug**: web-shell
- **Owner**: Yewen
- **Started**: 2026-10-24
- **Branch**: feat/web-shell
- **BASE_SHA**: 9365776810c0de2f6dead51f86af9b708be7ed04
- **Status**: complete (2026-10-24)

---

## REQUIREMENTS (LOCKED)

Human, in session, 2026-10-24:

> "the contract has been made. We're working on the frontend on this. go through the
> plan, the decisions, and the api-contract, and kick off the frontend build. make sure
> to use the governance layer"

Binding line from `docs/plan.md` (Frontend — Yewen):

> "**F1 Shell** — `feat/web-shell` — Vite + React + TS, pick or create user, API
> client against mocks from the contract."

Binding lines from `docs/decisions.md`:

> "**Frontend.** ... Decided: 2026-10-23 — Vite + React, TypeScript."

> "**Username only, no passwords.** Pick or create a user; the API takes the user_id."

Binding lines from `docs/api-contract.md` (General):

> "Base URL: `http://localhost:8787/api`."

> "In development the Vite dev server proxies `/api` to `:8787`, so the browser only
> calls its own origin. There is no CORS setup and no preflight to handle."

> "The user is identified by the header `X-User-Id: <user_id>` on every endpoint except
> `GET /users`, `POST /users` and `GET /stats`."

> "The frontend shows `error.message` for any 4xx and does not replicate these checks."

> "The frontend never calls an LLM, Mubit or TfL."

Answers to kickoff questions, human, 2026-10-24:

1. Client scope: "Every endpoint" — typed client and in-memory mocks for every endpoint
   in the contract, so F2–F5 build against mocks without reopening F1.
2. Mocks: "In-process module" — a mock implementation of the same client interface,
   chosen by a `VITE_` env var. No new dependency for mocking.
3. Tests: "Yes, Vitest" — new dev dependency, approved.
4. Routing: "No router yet" — one screen in F1.

### Source

This session's conversation, quoted above. `docs/plan.md`, `docs/decisions.md`,
`docs/api-contract.md` on `main` at `9365776`.

### Explicitly out of scope

- Swipe deck, card UI, gestures (F2).
- Feedback screen, chip dialog, onboarding enforcement in the UI (F3).
- Prefs form, commute polling UI, favourites UI (F4).
- Dashboard and chart (F5). No chart library.
- Any backend, Worker, D1 or seed-script code. Nothing under `worker/` or `dataset/`.
- Changes to `docs/api-contract.md` or `docs/decisions.md`. A contract gap found while
  building is reported, not edited.
- A router, state library, UI kit, CSS framework, MSW, Testing Library or jsdom.
- Component tests. UI is checked by eye in the browser.
- Mock fidelity beyond the contract: the mock does not run the chip catalogue rules or
  any ranking. Fixture cards carry hand-picked chips that obey the catalogue.
- Visual design beyond plain, readable styling.
- Deployment, Cloudflare Pages, production builds served anywhere.
- Ticking `docs/plan.md` — done in the merging PR.

---

## AMENDMENTS

- 2026-10-24, human: "b" — after the Step 3 review failed on the locked out-of-scope line
  "the mock does not run the chip catalogue rules or any ranking. Fixture cards carry
  hand-picked chips that obey the catalogue". The human authorises keeping the chip
  catalogue function in `web/src/api/fixtures.ts` (`buildChips`) that computes fixture
  chips at load. Conditions: it is logged under TRADEOFFS as a deviation, and
  `mock.test.ts` gains independent hand-written expected chip lists for at least two more
  fixtures, so the function is not only checked against itself. Ranking stays out of
  scope.

---

## RULES IN FORCE

| Rule                                                                                                                                                                                           | Source                                             | Applies to              |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- | ----------------------- |
| Commits only via `.claude/scripts/safe-commit.sh`, title only, no signature, human approves                                                                                                    | `.claude/CLAUDE.md`                                | commits                 |
| Commit title `type(scope): message`; scope `web`                                                                                                                                               | `.claude/CLAUDE.md`, `.claude/kit-config.md`       | commits                 |
| Plain British English, short sentences, banned marketing words                                                                                                                                 | `.claude/CLAUDE.md`                                | docs, comments, UI text |
| No scope creep: touch only the step's declared files                                                                                                                                           | `.claude/CLAUDE.md` #1                             | code, docs              |
| No new dependencies beyond those approved here: `vite`, `react`, `react-dom`, `typescript`, `@vitejs/plugin-react`, `@types/react`, `@types/react-dom`, `vitest`. Anything else is asked first | `.claude/CLAUDE.md` #2, kickoff answers            | code                    |
| Never weaken a test to make it pass                                                                                                                                                            | `.claude/CLAUDE.md` #3                             | tests                   |
| No speculative generalisation; walk the ladder                                                                                                                                                 | `.claude/CLAUDE.md` #4                             | code                    |
| Tradeoffs logged in TRADEOFFS when made; out-of-scope problems in SPOTTED                                                                                                                      | `.claude/CLAUDE.md` #5, #7                         | progress file           |
| Implementer never ticks its own boxes                                                                                                                                                          | `.claude/CLAUDE.md` #6                             | progress file           |
| Types, field names, enums, nullability and error codes exactly as `docs/api-contract.md`                                                                                                       | `docs/api-contract.md`                             | code                    |
| IDs are opaque strings: stored and sent back unchanged, never parsed                                                                                                                           | `docs/api-contract.md` (General)                   | code                    |
| `X-User-Id` on every call except `GET /users`, `POST /users`, `GET /stats`                                                                                                                     | `docs/api-contract.md` (General)                   | code                    |
| Show `error.message` for any 4xx; no client-side copy of backend validation                                                                                                                    | `docs/api-contract.md` (General)                   | code                    |
| All calls go to same-origin `/api`; Vite proxies to `:8787`; no CORS code                                                                                                                      | `docs/api-contract.md` (General)                   | code                    |
| Card `source` is in the payload but never shown on the card face                                                                                                                               | `docs/decisions.md`, `docs/api-contract.md` (Deck) | code                    |
| Frontend never calls an LLM, Mubit or TfL                                                                                                                                                      | `docs/api-contract.md`, `docs/decisions.md`        | code                    |
| Chips rendered as sent, in order sent, never filtered, added or reordered                                                                                                                      | `docs/api-contract.md` (Chip catalogue)            | code                    |
| TypeScript, Vite + React                                                                                                                                                                       | `docs/decisions.md` (Frontend)                     | code                    |
| `docs/plan.md` changes only to tick F1, in the merging PR                                                                                                                                      | `docs/decisions.md` (Overview)                     | docs                    |

---

## PLAN

All paths are relative to the repo root. Frontend lives in `web/`.

### Step 1 — Scaffold `web/`

**Goal**: A Vite + React + TypeScript app in `web/` with Vitest, a `/api` → `:8787`
dev proxy, and one passing smoke test.

**Files in scope**: `web/package.json`, `web/package-lock.json`, `web/.gitignore`,
`web/index.html`, `web/tsconfig.json`, `web/tsconfig.app.json`, `web/tsconfig.node.json`,
`web/vite.config.ts`, `web/src/main.tsx`, `web/src/App.tsx`, `web/src/index.css`,
`web/src/vite-env.d.ts`, `web/src/smoke.test.ts`, `evidence/web-shell/step-1.md`, `.claude/kit-config.md` (Commands,
Test framework and Where tests live only).

**Done when**: from `web/`, `npm ci`, `npm run typecheck`, `npm test` and
`npm run build` all exit 0; `npm run dev` serves a page; `vite.config.ts` proxies `/api`
to `http://localhost:8787`; `node_modules/` and `dist/` are gitignored; only the
approved dependencies are in `package.json`; kit-config Commands are filled with the
exact commands.

**Evidence location**: the diff, plus command output recorded in
`evidence/web-shell/step-1.md`.

- [x] Implemented — web/ scaffold present, 8 approved deps only in web/package.json (2026-10-24)
- [x] Tested — npm ci, typecheck, test, build all exit 0 on reviewer re-run; dev server 200 on /, 502 on /api/users with no backend (2026-10-24)
- [x] Best practices met — strict TS, no node_modules/dist/tsbuildinfo in git status -uall, check-process-refs.sh exit 0 (2026-10-24)
- [x] Matches locked requirements — web/vite.config.ts proxies "/api" to http://localhost:8787; Vite + React + TS; Vitest (2026-10-24)
- [x] No scope drift — all files within declared scope; kit-config diff limited to Commands, Test framework, Where tests live; *.tsbuildinfo ignore line is in-scope web/.gitignore (2026-10-24)

### Step 2 — Contract types and HTTP client

**Goal**: TypeScript types for every request and response in the contract, a client
interface with one method per endpoint, and its real `fetch` implementation.

**Files in scope**: `web/src/api/types.ts`, `web/src/api/client.ts`,
`web/src/api/http.ts`, `web/src/api/http.test.ts`, `evidence/web-shell/step-2.md`.

**Done when**: every endpoint in `docs/api-contract.md` has a client method with typed
request and response; enums are string-literal unions and nullable fields are
`| null` exactly as the contract's Enums and nullability section; the HTTP client calls
same-origin `/api/...`, sends `X-User-Id` on every call except `GET /users`,
`POST /users`, `GET /stats`, sends JSON bodies (including the `DELETE /favourites`
body), and turns a non-2xx `{"error": {...}}` into a thrown error carrying `status`,
`code` and `message`; tests with a stubbed `fetch` cover the header rule, the error
shape and one body-carrying `DELETE`; typecheck and tests pass.

**Evidence location**: the diff, plus test output in `evidence/web-shell/step-2.md`.

- [x] Implemented — 13 ApiClient methods in web/src/api/client.ts, fetch impl in http.ts, contract types in types.ts (2026-10-24)
- [x] Tested — typecheck exit 0, npm test exit 0, 11 passed (10 in http.test.ts) on reviewer re-run (2026-10-24)
- [x] Best practices met — non-2xx to ApiError with fallback, ids URL-encoded, check-process-refs.sh exit 0 (2026-10-24)
- [x] Matches locked requirements — enums, nullability, 20 chip_ids, header rule, DELETE body checked field by field against docs/api-contract.md (2026-10-24)
- [x] No scope drift — only the 5 declared step-2 files plus progress file appended (2026-10-24)

### Step 3 — In-memory mock client

**Goal**: A mock implementation of the same client interface that follows the
contract's behaviour, selected by `VITE_API_MODE=mock`.

**Files in scope**: `web/src/api/mock.ts`, `web/src/api/fixtures.ts`,
`web/src/api/index.ts`, `web/src/api/mock.test.ts`, `web/.env.example`, `evidence/web-shell/step-3.md`.

**Done when**: the mock implements every client method; it throws the same error type
as the HTTP client with the contract's codes (at least `unknown_user`,
`username_taken`, `prefs_missing`, `commute_pending`, `decision_not_found`, `already_swiped`, `not_swiped`,
`chip_not_offered`, `reason_required`, `not_favourited`, `listing_not_found`); it
models: `commute_status` going `pending` → `ready`, deck re-serving unswiped cards
first with the same `decision_id`, about 1 in 5 cards `exploration`,
`feedback_required` true for the first 15 swipes, superlike adding a favourite,
profile `version` bumping on swipe, feedback PUT, favourite removal and flag
correction, empty deck with `empty_reason`, and `GET /stats` returning sample arms;
fixtures are a small set (at least 12) of listings shaped exactly as the contract, with
chips that obey the catalogue; `index.ts` exports the mock when
`VITE_API_MODE=mock` and the HTTP client otherwise; tests cover onboarding count,
re-serve, version bumps and the error codes; typecheck and tests pass.

**Evidence location**: the diff, plus test output in `evidence/web-shell/step-3.md`.

- [x] Implemented — mock.ts, fixtures.ts (20 listings), index.ts, .env.example present; all contract methods and error codes covered (2026-10-24)
- [x] Tested — typecheck, npm test (50 passed), build, check-process-refs all exit 0 on reviewer re-run; chip lists for rm-170906828, rm-171802127, rm-91380246 hand-derived by reviewer and match test (2026-10-24)
- [x] Best practices met — no-op catch removed, already_swiped asserted via expectError (mock.test.ts:483-491), no new deps, process refs exit 0 (2026-10-24)
- [x] Matches locked requirements — buildChips deviation covered by AMENDMENTS 2026-10-24 and TRADEOFFS entry; behaviours and codes unchanged (2026-10-24)
- [x] No scope drift — only the 6 declared step-3 files untracked; dataset/, docs/, package.json untouched (2026-10-24)

### Step 4 — Pick or create user

**Goal**: The one F1 screen: list users, pick one, or create one by username; the
chosen user persists across reloads and can be switched.

**Files in scope**: `web/src/App.tsx`, `web/src/UserPicker.tsx`,
`web/src/session.ts`, `web/src/index.css`, `evidence/web-shell/step-4.md`.

**Done when**: in mock mode the screen lists users from `GET /users`; creating a user
calls `POST /users` and selects it; a 409 `username_taken` shows the server's
`error.message`; the chosen `user_id` is kept in `localStorage` (wrapped in try/catch)
and restored on reload; a signed-in placeholder shows the username and a "Switch user"
control; typecheck, tests and build pass; the human has eyeballed it in the browser.

**Evidence location**: the diff, plus a short note and screenshot path in
`evidence/web-shell/step-4.md`.

- [x] Implemented — App.tsx, UserPicker.tsx, session.ts: list, create, restore, switch; localStorage in try/catch (2026-10-24)
- [x] Tested — typecheck, npm test (50 passed), build, check-process-refs all exit 0 on reviewer re-run; smoke.test.ts unchanged; UI has no component tests by locked scope (2026-10-24)
- [x] Best practices met — ApiError.message shown, fallback for non-ApiError, labelled input, role=alert, no router/deps, no mock checks copied, source never shown (2026-10-24)
- [x] Matches locked requirements — done-when holds; human eye test recorded in evidence/web-shell/step-4.md (human: "it's fine"; orchestrator re-run: list, create, username_taken message, reload restore, switch all pass; no screenshot kept, done-when does not require one) (2026-10-24)
- [x] No scope drift — only 5 declared files plus progress-file TRADEOFFS appends; smoke.test.ts and package.json untouched (2026-10-24)

---

## TRADEOFFS

- Step 1 | Smoke test only checks App renders its heading (renderToString); it does not cover the proxy or the build. Proxy evidenced by a manual 502 curl with no backend. Component tests are out of scope per requirements. | reported by implementer, logged by reviewer 2026-10-24 | accepted by human 2026-10-24
- Step 2 | A non-2xx response whose body is not `{"error": {code, message}}` (proxy 502, non-JSON) throws `ApiError` with the real status, code `http_error` and message "Request failed with status N." The contract defines no code for this; `http_error` is a client-side invention. | reported by implementer | accepted by human 2026-10-24
- Step 2 | A network failure (fetch rejects, e.g. backend down with no proxy answer) propagates as the native `TypeError`, not `ApiError`. The contract says nothing on it and the brief asked for no extra handling. Callers must not assume every failure is `ApiError`. | reported by implementer | accepted by human 2026-10-24
- Step 2 | `PhotoFlag.value` is `string | number` and `field`/`scope` are independent unions, so scope/field mismatches and the `light` value set are not expressed in the type. A discriminated union would be stricter but is more code than the contract's loose wording needs. | reported by implementer | accepted by human 2026-10-24
- Step 2 | The HTTP client has no timeout or abort handling and no response validation (backend owns validation, per brief). | reported by implementer | accepted by human 2026-10-24
- Step 3 | Mock `soft` prefs are the text split on commas and full stops; `hard` is all null except `max_commute_min`. No parsing. | reported by implementer | accepted by human 2026-10-24
- Step 3 | Mock `commute_status` is `pending` in the PUT response and `ready` on the first GET after it. A pending status therefore never lasts more than one poll. The reserved postcode `FAIL 1AA` (case-insensitive) makes that first GET return `failed`, so the failed state can be shown; this magic value exists only in the mock. | reported by implementer | accepted by human 2026-10-24
- Step 3 | No hard filtering, so `no_matches` is never returned. Exploration is every fifth new card per user, drawn from the same fixture order as ranked cards, not from a band. Fixture order is the "ranking". | reported by implementer | accepted by human 2026-10-24
- Step 3 | `feedback_required` on deck cards is recomputed on every response (swipes so far plus position under 15), including re-served cards. | reported by implementer | accepted by human 2026-10-24
- Step 3 | Mock profile `factors` is one entry per chip the user has answered: direction is the latest answer's text or its strength, weight is answers over times offered, capped at 1. Not the learning model. | reported by implementer | accepted by human 2026-10-24
- Step 3 | Mock commute minutes are a deterministic hash of listing id and postcode (about 1 in 4 `null`), not real journey times. | reported by implementer | accepted by human 2026-10-24
- Step 3 | Mock `POST /users` compares usernames case-insensitively after trimming, and rejects an empty username with 422 `invalid_request`. The contract leaves username rules to the backend. | reported by implementer | accepted by human 2026-10-24
- Step 3 | Mock does light shape validation beyond the brief where the contract states the shape (swipe `action`, chip `strength`, text types), returning 422 `invalid_request`. It does not check formats. | reported by implementer | accepted by human 2026-10-24
- Step 3 | `index.ts` imports the mock unconditionally, so fixtures are in the production bundle even in HTTP mode. | reported by implementer | accepted by human 2026-10-24
- Step 3 | Chip catalogue clauses for photo flags are applied to the three fixtures that carry flags. The contract says flags do not exist yet and to skip those clauses, so these fixtures would differ from the real backend today. | reported by implementer | accepted by human 2026-10-24
- Step 3 | Fixture chips are computed at load by `buildChips` in `fixtures.ts`, a local implementation of the contract's chip catalogue rules. This departs from the locked out-of-scope line about hand-picked chips; authorised by the human in AMENDMENTS 2026-10-24. Risk: it can drift from the backend's implementation. Fix: replace with the real backend once B4 lands. Mitigation: `mock.test.ts` checks hand-derived chip lists for five fixtures. | reported by implementer | accepted by human 2026-10-24
- Step 4 | Session stores `{user_id, username}` in `localStorage`, not only the id. The username is refreshed from `listUsers()` on restore. | reported by implementer | accepted by human 2026-10-24
- Step 4 | A network failure (native error) shows a fixed message, "Could not reach the server. Try again."; no retry. On restore, a failed `listUsers()` falls back to the picker rather than trusting the stored user. | reported by implementer | accepted by human 2026-10-24
- Step 4 | On load with a stored user, `listUsers()` is called by App and again by the picker if the check fails or the user is gone. One extra call, no caching. | reported by implementer | accepted by human 2026-10-24
- Step 4 | In mock mode a created user (`u_03`+) does not survive reload, because mock state is in memory. Seeded alex and jordan do. | reported by implementer | accepted by human 2026-10-24
- Step 4 | Create form blocks only empty or whitespace-only input; the raw (untrimmed) text is sent, the backend decides. | reported by implementer | accepted by human 2026-10-24

---

## SPOTTED, NOT FIXED

- `.claude/worktrees/` | untracked and not gitignored on `main` | low
- `.claude/kit-config.md` Project type | still says "No code yet"; `web/` now exists. Outside every F1 step's scope | low
- `docs/api-contract.md` Flag corrections | `POST /flags/{id}/correction` response is "the same shape as one entry of `photo_flags`, plus `profile_version`", so it is typed as `PhotoFlag & {profile_version}`. Fine, but the contract lists no 404-vs-400 behaviour for a flag on a listing the user has not seen. | low
- `docs/api-contract.md` Prefs | `PUT /prefs` response is "same shape as `GET /prefs`" but with `commute_status: "pending"`; typed as `PrefsResponse` (nullable status) so the type does not enforce `pending`. `max_commute_min` request field is optional but the contract does not say whether `null` is accepted, so it is typed `?: number` only. | low
- `docs/api-contract.md` Deck | `n` range 1-10 and integer is backend-validated; client passes any number through. Contract is consistent with this. | none
- `docs/api-contract.md` Chip catalogue | "Until flags exist every rule is evaluated as if the flags were absent" is stated globally, but `GET /listings/{id}` returns `photo_flags`. Unclear whether the flag clauses apply per listing or only once the pipeline has run. The mock applies them per listing. | low
- `docs/api-contract.md` Favourites | `GET /favourites` order is not stated. The mock returns insertion order. | low
- `docs/api-contract.md` Deck | Whether `feedback_required` on a re-served card is the original hint or recomputed is not stated. The mock recomputes. | low

---

## VERIFICATION

QA gate, 2026-10-24, base 9365776.

- [x] All step checkboxes ticked with evidence — 20 of 20 ticked, each with text (2026-10-24)
- [x] Every evidence path in this file exists — evidence/web-shell/step-1.md to step-4.md present (2026-10-24)
- [x] Test suite run — `cd web && npm test`: 3 files, 50 passed, exit 0
- [ ] Lint run — not configured (Lint is blank in kit-config by choice); not run
- [x] Typecheck run — `cd web && npm run typecheck`: exit 0
- [x] Build run — `cd web && npm run build`: exit 0 (23 modules, JS 270.43 kB)
- [x] Diff contains no files outside declared scope — 30 files, all in a step's scope or the progress file
- [x] Tradeoff ledger reviewed and signed off by human — all 21 entries accepted by the human, "accept all" (2026-10-24)
- [x] Human eye test completed — core checks passed (human and built-in browser); follow-up checks for empty input, Tab order, no-backend error and created-user reload done by the human or in the built-in browser and recorded in evidence/web-shell/step-4.md. Button re-enable after `username_taken` and reload after Switch user not separately checked; no screenshot kept (2026-10-24)

Also: `npm ci` exit 0; `.claude/scripts/check-process-refs.sh 9365776` exit 0, no hits.

---

## HANDOVER

**What was built.** A Vite, React and TypeScript app in `web/`. It has a typed client for every endpoint in the API contract, a real fetch version and an in-memory mock with 20 fixture listings. One screen works: you list users, pick one or create one by username, and the choice survives a reload. Nothing else is in the UI yet. No deck, feedback, prefs or dashboard.

**What to check yourself.**
1. `cd web && npm ci && VITE_API_MODE=mock npm run dev`. Open http://localhost:5173. (Without the variable the app calls the real API, which is not running.)
2. Clear `localStorage` for the site. You should see "Choose a user" with alex and jordan.
3. Type "sam" and press Create user. You should see "Signed in as sam" and a Switch user button.
4. Press Switch user. Create "alex". You should see "That username is taken." and the button usable again.
5. Not yet run by anyone: submit an empty box, and a box of spaces. Nothing should be sent and nothing should change.
6. Pick alex, reload. You should still be signed in as alex.
7. Pick sam (create again after a reload), reload. You should land on the picker. This is expected in mock mode only.
8. Press Switch user, then reload. You should stay on the picker.
9. Tab through the picker. Order should be user buttons, the input, Create user.
10. Without the mock variable, run `npm run dev` with no backend. The picker should show "Request failed with status 502." or the fixed unreachable message.

**Tools that will help.** Browser devtools, Application tab: check `localStorage` key `session.user` holds `{user_id, username}` after sign-in and is gone after Switch user. Network tab in real mode: `GET /api/users` should carry no `X-User-Id`. Console: should be empty. `cd web && npm test` for the 50 tests.

**What is not done.** Everything in TRADEOFFS above stands. Plainly:
- No lint. No linter is approved.
- No component tests. UI is checked by eye only.
- `buildChips` in `fixtures.ts` re-implements the chip catalogue. It was authorised by amendment but can drift from the backend.
- The mock is not the backend: no filtering, no ranking, no `no_matches`, commute is a hash, `FAIL 1AA` is a mock-only magic postcode.
- Fixtures ship in the production bundle.
- Network failures from the HTTP client are a native `TypeError`, not `ApiError`. The picker handles both. Later screens must too.
- The HTTP client has no timeout and no response validation.
- Step 4 evidence has no screenshot. The plan mentioned a screenshot path.
- `.claude/kit-config.md` Project type still says "No code yet". Not fixed (outside scope). `.claude/worktrees/` is untracked.
- Contract gaps in SPOTTED, NOT FIXED, none fixed or edited.
- `docs/plan.md` is not ticked; that belongs in the merging PR.
- The REQUIREMENTS block could only be compared from the commit where the progress file first appeared (4b3ca20). It is unchanged since then.

**What could bite you.**
1. Real backend mismatch. The client has only been run against a mock and stubbed fetch. The first run against the real Worker may expose shape or error-code differences. Check `GET /api/users` and `POST /api/users` first.
2. Mock drift. F2 and F3 will build on mock chips and deck behaviour that come from the implementer's reading of the contract, including `feedback_required` recomputing on re-served cards, which the contract does not state.
3. Forgetting the mock variable. `.env.example` sets it but nobody copies it automatically. Without it the app talks to a dead `:8787` and shows an error.

Feature is not complete until the human has done the eye test and signed the tradeoff ledger.
