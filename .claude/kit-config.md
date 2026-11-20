# Kit config

Per-repository settings for the dev kit. Fill this in once when installing the kit.
Agents and skills read this file. Leave a value as `auto` to let the kit work it out.

## Repository

- **Target branch**: auto
  <!-- The branch PRs merge into. `auto` detects it from origin/HEAD, falling back to
       main, then master, then develop. Set explicitly if your repo is unusual. -->

- **Project type**: Cloudflare Python Worker (FastAPI) in /worker, Vite + React in /web, local D1 database.

- **Has a frontend**: yes
  <!-- yes/no. Drives whether qa-gate asks for a browser eye test. -->

## Commands

Leave blank if the repo has none. Never invent one.

- **Install**: `cd web && npm ci`; backend: `cd worker && uv sync --group dev`
- **Test**: `cd web && npm test`; backend: `cd worker && BASE_URL=http://localhost:8788 uv run --group dev pytest tests -q` (needs a seeded dev server in test mode on :8788, see worker/README.md; the run stops if the server is not in test mode)
- **Test (single file)**: `cd web && npx vitest run <path>`; backend: `cd worker && uv run --group dev pytest <path> -q`
- **Lint**: <!-- e.g. npm run lint -->
- **Typecheck**: `cd web && npm run typecheck`
- **Build**: `cd web && npm run build`
- **Run locally**: `cd web && npm run dev` (serves http://localhost:5173, proxies `/api` to :8787); backend: `worker/scripts/seed.sh` once, then `cd worker && uvx --from workers-py pywrangler dev` (serves http://localhost:8787/api)

## Conventions

- **Commit scopes in use**: worker, web, db, prep, kit, api
- **Requirements source**: docs/product-idea-high-level.md
- **Progress files**: committed
  <!-- committed or ignored. `committed` means .claude/progress/*.md are tracked in git
       and go into commits like any other file. -->
- **Test framework**: vitest (web)
- **Where tests live**: alongside source as `*.test.ts` in `web/src/`

- **Real data**: <!-- Where real data lives and the command that runs the current code
  on it, e.g. `data/sample/` and `make run-sample`. Blank means none. Kickoff takes an
  acceptance example from what the code does on it. Figures and outcomes only go in
  the progress file, never raw records. -->

## Brief notes

<!-- Things every step brief in this repo must carry, e.g. files that pin figures and
     must be updated when tests are added. -->

- On Yewen's laptop a PostToolUse hook runs Prettier on every Edit and Write. After
  editing, check `git diff`. If unrelated lines were reformatted, restore the file
  and apply the change with a shell edit.

## Full automation

Read in feature and auto mode (`.claude/scripts/kit-mode.sh status`). Step mode, the
default, ignores this section, except that `kit-escalate-check.sh` uses Escalate paths
and Approved dependencies to flag concerns before a step commit.

### Where the work comes from

- **Plan file**: <!-- e.g. `docs/plan.md`. Required in feature and auto mode. The list
  of features, one per line, as `- [ ] <feature> — feat/<branch>`. `kit-drive.sh --next`
  takes the first unticked line. Close-out ticks it. -->
- **Binding documents**: <!-- e.g. `docs/decisions.md`, `docs/api-contract.md`.
  Already agreed by the human. Kickoff quotes requirements from them, and the arbiter
  escalates anything that contradicts them or needs one of their open items settled. -->

### Escalation

The mechanical triggers are checked by `.claude/scripts/kit-escalate-check.sh`; the
arbiter judges the rest.

- **Approved dependencies**: `fastapi`, `google-genai`, `pytest`
  <!-- May be added without asking. Any other dependency escalates. -->
- **Escalate paths**: <!-- e.g. `web/`, `docs/api-contract.md`, `migrations/*.sql`.
  Any change to these escalates. A trailing / means the whole directory. -->
- **Dependency manifests**: auto
  <!-- `auto` covers package.json, pyproject.toml, requirements*.txt, go.mod,
       Cargo.toml, Gemfile, composer.json. Or list your own in backticks. -->
- **Max review fails**: 3
  <!-- The same step failing review this many times escalates. -->
- **Always escalate**: <!-- Plain-English rules for the arbiter, e.g. spending money
  beyond a single test call; a breaking change to the public API; a missing secret. -->

### Driver

`kit-drive.sh` runs one fresh Claude Code session per phase: kickoff, each step, wrap-up.

- **Driver model**: opus
- **Driver permission mode**: auto
  <!-- auto: the harness approves routine calls and the kit's guard blocks the
       dangerous ones. dontAsk: only calls allowed in settings run; add allow rules
       for your test commands first. bypassPermissions: only in a sandbox. -->
- **Session budget (USD)**: 5
- **Run budget (USD)**: 60
- **Max sessions per phase**: 4
  <!-- A step or wrap-up that needs more sessions than this halts the run. -->
- **Notify command**: <!-- optional, e.g. `notify-send kit-drive`. Called with one
  argument, the message, when a run halts or finishes. -->

## Manual verification hints

Anything the human should know when eyeballing work in this repo. The qa-gate agent
uses this to write better handover notes.

- **API base URL (local)**: <!-- e.g. http://localhost:3000/api -->
- **Auth for local testing**: <!-- e.g. seeded user dev@example.com / password -->
- **Useful tools**: <!-- e.g. Postman collection at docs/postman.json -->
