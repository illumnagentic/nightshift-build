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

- **Install**: <!-- e.g. npm ci -->
- **Test**: <!-- The exact command CI runs, including any extras or flags CI uses.
  e.g. npm test -->
- **Test (single file)**: <!-- e.g. npx vitest run <path> -->
- **Lint**: <!-- e.g. npm run lint -->
- **Typecheck**: <!-- e.g. npm run typecheck -->
- **Build**: <!-- e.g. npm run build -->
- **Run locally**: <!-- e.g. npm run dev -->

## Conventions

- **Commit scopes in use**: worker, web, db, prep, kit
- **Requirements source**: docs/product-idea-high-level.md
- **Progress files**: committed
  <!-- committed or ignored. `committed` means .claude/progress/*.md are tracked in git
       and go into commits like any other file. -->
- **Test framework**: <!-- e.g. vitest, pytest, go test -->
- **Where tests live**: <!-- e.g. alongside source as *.test.ts -->

## Brief notes

<!-- Things every step brief in this repo must carry, e.g. files that pin figures and
     must be updated when tests are added. -->

## Manual verification hints

Anything the human should know when eyeballing work in this repo. The qa-gate agent
uses this to write better handover notes.

- **API base URL (local)**: <!-- e.g. http://localhost:3000/api -->
- **Auth for local testing**: <!-- e.g. seeded user dev@example.com / password -->
- **Useful tools**: <!-- e.g. Postman collection at docs/postman.json -->
