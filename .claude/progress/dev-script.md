# Feature: Root dev script

- **Slug**: dev-script
- **Owner**: Zsolt
- **Started**: 2026-10-25
- **Branch**: feat/dev-script
- **BASE_SHA**: 67a401a8a1f76549ad1c9783dfc239c2bbfeaab4
- **Status**: complete (2026-10-25)
- **Mode**: full automation (on since 2026-10-24)

---

## REQUIREMENTS (LOCKED)

Human, in session, 2026-10-25:

> can you create like a root file or something to make it easy and simple to reseed,
> and to start backend and frontent?

Main agent's proposal, shown to the human in the same session, with no objection:

> ./dev.sh seed     # wipe and reseed the local D1 (stops a running backend first)
> ./dev.sh tables   # add new tables to the existing D1 without wiping users
> ./dev.sh start    # backend on :8787 and frontend on :5173 together; Ctrl+C stops both
>
> `start` will refuse to run if `worker/.dev.vars` is missing, and if port 8787 or 5173
> is already in use. [...] no new dependencies; under the hood it calls the same
> commands the READMEs already give.

### Source

Quoted above.

### Explicitly out of scope

- Any change under `web/` or `worker/src/`, or to `worker/scripts/seed.sh`.
- Running tests, the test-mode server, or the persona batch from the script.
- Installing dependencies automatically (`npm ci`, `uv sync`); the script only says
  what to run when they are missing.
- Windows support beyond WSL; Makefiles; new dependencies.

---

## AMENDMENTS

- 2026-10-25, human instruction in session: `./dev.sh seed` refuses while :8787 is in use (prints that the port is in use and changes nothing) instead of stopping a running backend first. The human chose "Refuse" when asked after the QA gate flagged that the locked proposal said "stops a running backend first". Matches the Step 1 Done-when, the README and the human's manual run. No code change.

---

## RULES IN FORCE

| Rule | Source | Applies to |
| ---- | ------ | ---------- |
| Plain British English, no banned words, no padding | `.claude/CLAUDE.md` Language and tone | script messages, README, evidence, commits |
| Commits via `safe-commit.sh` only, title only, no attribution | `.claude/CLAUDE.md` Committing | commits |
| `type(scope): message`; scopes worker, web, db, prep, kit, api | `.claude/CLAUDE.md`, `kit-config.md` | commits, PR title |
| No scope creep; touch only the step's declared files | `.claude/CLAUDE.md` prohibition 1 | code, docs |
| No new dependencies | `.claude/CLAUDE.md` prohibition 2 | code |
| The ladder: least code, reuse the existing commands | `.claude/CLAUDE.md` The ladder | code |
| Never start a server that uses the real key for tests; the normal dev server is :8787 | `worker/README.md` | script |
| Tradeoffs and spotted items logged in this file | `.claude/CLAUDE.md` prohibitions 5, 7 | this file |
| Only step-reviewer ticks boxes | `.claude/CLAUDE.md` prohibition 6 | this file |

---

## PLAN

### Step 1 — `dev.sh` at the repo root

**Goal**: one executable bash script, `dev.sh`, with the subcommands `seed`, `tables`
and `start`, plus a short section in the root `README.md`.

**Files in scope**: `dev.sh` (new), `README.md`, `evidence/dev-script/step-1.md` (new).

**Done when**:
- `./dev.sh` with no argument or an unknown one prints a usage line and exits non-zero.
- `./dev.sh seed` refuses (non-zero, clear message) while something listens on :8787,
  otherwise runs `worker/scripts/seed.sh` and exits with its status.
- `./dev.sh tables` runs `npx --yes wrangler d1 execute haka --local --file schema.sql`
  from `worker/`, keeps existing users, and refuses while :8787 is in use (a running
  server keeps a stale D1 view).
- `./dev.sh start` refuses with a clear message when `worker/.dev.vars` is missing, when
  `web/node_modules` is missing (says to run `cd web && npm ci`), or when :8787 or
  :5173 is in use; otherwise starts `uvx --from workers-py pywrangler dev` in `worker/`
  and `npm run dev` in `web/`, and Ctrl+C (or either one exiting) stops both, with no
  process left on either port.
- Works from any current directory (resolves paths from the script's own location).
- `bash -n dev.sh` passes; `shellcheck` is run if installed, else that is stated.
- Root `README.md` has a short "Run it locally" section naming the three subcommands.

**Evidence location**: `evidence/dev-script/step-1.md`

**Redo (arbiter) 2026-10-25**: FIX_NOW on the SPOTTED entry (cheap, one line). In
`dev.sh:44` replace `wait -n || true` with `wait -n`, so `start` exits with the status
of the first child to exit (non-zero on a crash; 130 on Ctrl+C), while the EXIT trap
still stops both. Done when: a crashed child gives a non-zero exit, both ports are
free afterwards, `bash -n dev.sh` passes, and step-reviewer re-reviews Step 1.

Redo reviewed 2026-10-25: PASS — dev.sh:44 is `wait -n`; bash -n exit 0; ./dev.sh exit 1 with usage; scratch copy (children `sleep 30` and `sh -c 'sleep 1; exit 3'`, checks stubbed) gave start exit 3 and `pgrep -fx 'sleep 30'` found nothing; check-process-refs.sh exit 0. Scratch copy deleted.

- [x] Implemented — dev.sh (50 lines) with seed/tables/start, README section (2026-10-25)
- [x] Tested — evidence: bash -n exit 0; no/unknown arg exit 1 with usage from any cwd; seed/tables/start each exit 1 with port message against a live :8787 listener, git status unchanged; start run/Ctrl+C and seed/tables success covered by human manual run in evidence/dev-script/step-1.md; shellcheck not installed (2026-10-25)
- [x] Best practices met — evidence: set -euo pipefail, paths from BASH_SOURCE, setsid groups with trap cleanup, errors to stderr; check-process-refs.sh exit 0 (2026-10-25)
- [x] Matches locked requirements — evidence: all Done-when items map to dev.sh lines 18-50 (2026-10-25)
- [x] No scope drift — evidence: diff is dev.sh, README.md, evidence/dev-script/step-1.md only (2026-10-25)

---

## TRADEOFFS

_None logged._

---

## SPOTTED, NOT FIXED

- RESOLVED 2026-10-25 (arbiter FIX_NOW, redo reviewed PASS): dev.sh start exited 0 even if a child died on its own (wait -n || true).

---

## VERIFICATION

- [x] All step checkboxes ticked with evidence (2026-10-25)
- [x] Every evidence path in this file exists — evidence/dev-script/step-1.md (2026-10-25)
- [x] Test suite run — result: `cd web && npm test` 186 passed, exit 0; `cd worker && uv run --group dev pytest tests/test_filters.py tests/test_prefs_unit.py tests/test_mubit.py tests/test_tfl_unit.py tests/test_chips.py tests/test_curator_unit.py tests/test_profile_unit.py -q` 207 passed, exit 0. API suite not run: the diff touches nothing under worker/ or web/, and the suite would need a seeded test-mode server (2026-10-25)
- [x] Lint run — result: no lint command configured in kit-config; `bash -n dev.sh` exit 0; shellcheck not installed (2026-10-25)
- [x] Typecheck run — result: `cd web && npm run typecheck` exit 0 (2026-10-25)
- [x] Build run — result: `cd web && npm run build` exit 0 (2026-10-25)
- [x] Diff contains no files outside declared scope — dev.sh, README.md, evidence/dev-script/step-1.md, plus this file (2026-10-25)
- [x] Tradeoff ledger reviewed — no entries; signed by arbiter (full automation) (2026-10-25)
- [x] Human eye test completed — human-verified: the human ran dev.sh by hand on 2026-10-25 and said "looks good to me" (evidence/dev-script/step-1.md)

QA-GATE: PASS 2026-10-25 — re-run after the 2026-10-25 AMENDMENTS entry (human instruction: seed refuses while :8787 is in use). dev.sh:20 does exactly that. dev.sh, README.md and evidence/dev-script/step-1.md unchanged since the previous gate (mtimes 13:31–13:33, before the amendment). Re-ran: `bash -n dev.sh` exit 0; `check-process-refs.sh 67a401a` exit 0, no hits.

---

## HANDOVER

**What was built.** `./dev.sh` at the repo root wraps the local dev commands. `./dev.sh seed` wipes and reseeds the local D1. `./dev.sh tables` adds new tables and keeps users. `./dev.sh start` runs the backend on :8787 and the frontend on :5173 together, and Ctrl+C stops both. The root README lists the three.

**What to check yourself.** Already done by hand on 2026-10-25. To repeat:
1. Stop your backend. Run `./dev.sh start`. Open http://localhost:5173 and pick a user. Press Ctrl+C. Run `ss -ltn | grep -E ':8787|:5173'`. It should print nothing.
2. With the backend running, run `./dev.sh seed` in another terminal. It should refuse with a port message and exit 1. Nothing is wiped.
3. Stop the backend. Run `./dev.sh tables`. Your users should still be there afterwards.

**Tools that will help.** `ss -ltn` to see what holds :8787 and :5173. `pgrep -fa 'workerd|vite'` to check nothing was left running after Ctrl+C.

**What is not done.**
- `seed` refuses while the backend runs rather than stopping it. The locked proposal said it would stop the backend; you chose refuse on 2026-10-25 (AMENDMENTS). Stop the backend yourself before seeding.
- No tradeoffs logged.
- shellcheck was not run (not installed).
- The API test suite was not run for this change; no application code changed.

**What could bite you.**
- The port checks use `ss`. If `ss` is missing, the check silently reads every port as free, so `seed` would run under a live backend.
- `start` assumes `setsid` and bash 4.3+ (`wait -n`). Fine on WSL and Linux; it will not work on stock macOS bash 3.2.
- If one server dies, `start` stops the other and exits with that server's status. Watch the terminal output; it will not restart anything.
