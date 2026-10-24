# Scaffold evidence: web/

Date: 2026-10-24. Node v24.4.1, npm 11.4.2. All commands run from `web/`.

Installed (top level): react 19.3.1, react-dom 19.3.1, vite 8.3.5, typescript 7.0.2,
@vitejs/plugin-react 6.1.2, @types/react 19.3.0, @types/react-dom 19.3.0, vitest 5.0.5.

| Command | Exit | Output |
| --- | --- | --- |
| `npm ci` | 0 | found 0 vulnerabilities |
| `npm run typecheck` | 0 | no output from tsc |
| `npm test` | 0 | Test Files 1 passed (1); Tests 1 passed (1) |
| `npm run build` | 0 | 16 modules transformed; built in 171ms |
| `npm run dev` (background), `curl http://localhost:5173/` | n/a | HTTP 200 |
| `curl http://localhost:5173/api/users` (backend not running) | n/a | HTTP 502, confirms the proxy forwards `/api` |

`git status --short -uall` lists no `node_modules/`, `dist/` or `*.tsbuildinfo`.
