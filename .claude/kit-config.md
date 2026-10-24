# Kit config

Per-repository settings for the dev kit. Fill this in once when installing the kit.
Agents and skills read this file. Leave a value as `auto` to let the kit work it out.

## Repository

- **Target branch**: auto
  <!-- The branch PRs merge into. `auto` detects it from origin/HEAD, falling back to
       main, then master, then develop. Set explicitly if your repo is unusual. -->

- **Project type**: Planned: Cloudflare Python Worker (FastAPI) in /worker, Vite + React in /web, D1 database. No code yet.

- **Has a frontend**: yes
  <!-- yes/no. Drives whether qa-gate asks for a browser eye test. -->

## Commands

Leave blank if the repo has none. Never invent one.

- **Install**: `cd web && npm ci`
- **Test**: `cd web && npm test`
- **Test (single file)**: `cd web && npx vitest run <path>`
- **Lint**: <!-- e.g. npm run lint -->
- **Typecheck**: `cd web && npm run typecheck`
- **Build**: `cd web && npm run build`
- **Run locally**: `cd web && npm run dev` (serves http://localhost:5173, proxies `/api` to :8787)

## Conventions

- **Commit scopes in use**: worker, web, db, prep, kit, api
- **Requirements source**: docs/product-idea-high-level.md
- **Progress files**: committed
  <!-- committed or ignored. `committed` means .claude/progress/*.md are tracked in git
       and go into commits like any other file. -->
- **Test framework**: vitest (web)
- **Where tests live**: alongside source as `*.test.ts` in `web/src/`

## Dependencies

- **Approved dependencies**: fastapi, google-genai, pytest
  <!-- Applies only in full automation. These may be added without asking. Any other
       dependency escalates. In default mode every new dependency is a question for
       the human. -->


## Brief notes

<!-- Things every step brief in this repo must carry, e.g. files that pin figures and
     must be updated when tests are added. -->

## Manual verification hints

Anything the human should know when eyeballing work in this repo. The qa-gate agent
uses this to write better handover notes.

- **API base URL (local)**: <!-- e.g. http://localhost:3000/api -->
- **Auth for local testing**: <!-- e.g. seeded user dev@example.com / password -->
- **Useful tools**: <!-- e.g. Postman collection at docs/postman.json -->
