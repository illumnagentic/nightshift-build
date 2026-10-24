# Prefs screen: onSaved callback

Date: 2026-10-25

Change: `PrefsScreen` takes a required `onSaved: () => void` prop. It is called once per
successful save, after the stale-response check passes and before the commute status is
applied. Polling, the leave-screen guard and messages are unchanged. `App.tsx` passes a
no-op `onSaved={() => {}}` for now, only so the app type-checks.

## Commands (from `web/`)

- `npm run typecheck` exit 0
- `npm test` exit 0, 7 files, 178 tests passed
- `npm run build` exit 0
