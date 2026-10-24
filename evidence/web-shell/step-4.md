# Web shell: pick or create user

Date: 2026-10-24

## Commands (run from `web/`, exit codes captured directly)

| Command | Exit |
| --- | --- |
| `npm run typecheck` | 0 |
| `npm test` (3 files, 50 tests passed) | 0 |
| `npm run build` | 0 |
| `VITE_API_MODE=mock npm run dev`, then `curl http://localhost:5173/` | 200 (curl exit 0); server killed afterwards |
| process-reference check script | 0 |

## Behaviour notes

- Session is stored in `localStorage` under `session.user` as `{user_id, username}`.
- On load, a stored user is checked against `listUsers()` by `user_id`. If absent, the session is cleared and the picker shows. If the backend is unreachable, the picker shows and reports its own error.
- Mock mode: seeded users `u_01` (alex) and `u_02` (jordan) keep their ids across reloads, so they restore. A user created in the mock (`u_03` onwards) is lost on reload because mock state is in memory, so reload returns to the picker.

## Manual check list (mock mode: `VITE_API_MODE=mock npm run dev`)

Eye test, 2026-10-24. The human ran the five core checks in the browser and reported "it's fine". At the human's request the checks were then re-run in the desktop app's built-in browser against http://localhost:5173 after clearing `localStorage`; results below. No console errors. No screenshot kept.

| Check | Result |
| --- | --- |
| Picker lists alex and jordan | pass |
| Create a new user (for example "sam"): signed in as sam | pass |
| Create "alex" again: server message for `username_taken` shows, button re-enables | pass: "That username is taken." shown; re-enable not checked |
| Empty or spaces-only username: nothing is submitted | pass (checked by the human, 2026-10-24) |
| Pick alex, reload: still signed in as alex | pass (`session.user` = u_01 after reload) |
| Create "sam", reload: back at picker (mock state resets; expected in mock mode only) | pass as expected: created user disappears on reload, alex and jordan stay signed in (checked by the human, 2026-10-24) |
| "Switch user" returns to the picker; reload stays on the picker | pass: returns to picker, `session.user` cleared; reload not checked |
| Keyboard: Tab reaches list buttons, input and Create; Enter submits the form | pass (Tab order checked by the human, 2026-10-24; Enter checked in the built-in browser) |
| No mock, no backend (`npm run dev -- --port 5174`): picker shows an error, no crash | pass: "Request failed with status 502." shown; `GET /api/users` returned 502 from the dev proxy (2026-10-24, built-in browser) |
