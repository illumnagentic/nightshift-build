# dev.sh

## What was built

`dev.sh` at the repo root, with three subcommands:

- `seed` wipes and reseeds the local D1 (users included) through `worker/scripts/seed.sh`. It refuses while :8787 is in use.
- `tables` applies `worker/schema.sql` to the existing local D1 with `wrangler d1 execute`, adding new tables and keeping users. It refuses while :8787 is in use.
- `start` runs the backend (`pywrangler dev`, :8787) and the frontend (`npm run dev`, :5173) together, each in its own process group. Ctrl+C stops both. It refuses if `worker/.dev.vars` or `web/node_modules` is missing, or if either port is in use.

The root `README.md` "Running locally" section now lists the three subcommands.

## Checks run 2026-10-25

- `bash -n dev.sh`: no output, exit 0.
- `shellcheck dev.sh`: not run, shellcheck is not installed.
- `./dev.sh` with no argument:

```
usage: ./dev.sh seed|tables|start
```

  Exit 1, as intended.

## Human-verified

The human ran `dev.sh` by hand on 2026-10-25 and said "looks good to me". Recorded as human-verified.

## Earlier agent run, throwaway worktree

`seed` ran and completed offline. The `tables` and `start` checks in that run were cut short and were not recorded. They are not claimed here; only the human's manual run above covers them.

`seed`, `tables` and `start` were not run in this checkout, because its D1 belongs to the human.

## Redo

`start` ended with exit 0 whatever happened, because `wait -n || true` swallowed the status. It is now `wait -n`, so with `set -e` the script exits with the status of the first server to stop. The EXIT trap still stops both.

Checks run 2026-10-25, no real server started:

- `bash -n dev.sh`: no output, exit 0.
- `./dev.sh` with no argument: usage line, exit 1.
- Scratch copy of `dev.sh` with the two servers replaced by `sleep 30` and `sh -c 'sleep 1; exit 3'`, and the `.dev.vars`, `node_modules` and port checks stubbed:
  - Short child fails: `start` exited 3. No `sleep 30` process left afterwards.
  - SIGINT while both run: exit 130. No `sleep 30` process left afterwards.
  - Scratch copy deleted.
- Process-reference check script: exit 0, no hits.
