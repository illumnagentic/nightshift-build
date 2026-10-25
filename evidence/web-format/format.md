# Web source formatting

Date: 2026-10-25

One-off Prettier pass over `web/src` (`.ts`, `.tsx`, `.css`), agreed by the human after the
web-feedback retro ("Use b") and run once the feedback and prefs work had merged. Purpose: this
laptop's editor hook runs `npx prettier --write` on every edited file; formatting everything
once makes later diffs contain only real changes.

- Tool: `npx prettier` 3.9.10, default settings (no Prettier config in the repo), the same
  command the editor hook runs. Nothing added to `package.json`.
- Files changed: 26, all under `web/src`. `fixtures.ts` needed a second pass to settle; further
  passes change nothing. `npx prettier --check "web/src/**/*.{ts,tsx,css}"` exit 0.
- Behaviour unchanged, checked by minifying every file before and after with the installed
  rolldown/oxc minifier (layout ignored) and lightningcss for CSS: 24 of 26 identical; the
  other two differ only in key quoting (`"id":` → `id:` in `fixtures.ts`) and a JSX text split
  (`": "` → `":"` + `{" "}` in `FeedbackScreen.tsx`); both identical after normalising those.

| Command (from `web/`) | Exit |
| --- | --- |
| `npm run typecheck` | 0 |
| `npm test` (7 files, 178 tests passed) | 0 |
| `npm run build` | 0 |
