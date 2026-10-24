# Backend (worker)

FastAPI on a Cloudflare Python Worker, run locally with `pywrangler dev`, with a local
D1 database. Nothing is deployed.

## Prerequisites

- `uv`
- Node.js with `npx`. `seed.sh` and `pywrangler` both run wrangler through it.
- Network access on the first run: `seed.sh` downloads wrangler, and `pywrangler dev`
  downloads Python packages. The Mubit calls need network every time.

## One-time setup

Create `worker/.dev.vars` with the Mubit key (shared out of band, never commit it):

```
MUBIT_API_KEY=...
```

`.dev.vars` is gitignored.

## Seed the local database

From the repo root:

```
worker/scripts/seed.sh
```

This deletes the local D1 state, then loads the listings schema, the app schema and the
listings data (635 rows in `listings`, none in `users`). It is safe to re-run. Do it
before starting the dev server, and again whenever you want an empty `users` table.
Stop `pywrangler dev` before running it, then start it again. A running server keeps a
stale view of the local D1 and returns 500 until restarted.

## Run

In `worker/`:

```
uvx --from workers-py pywrangler dev
```

The API is at http://localhost:8787/api. The web dev server (`cd web && npm run dev`)
proxies `/api` to it.

## Tests

Order: seed, start the dev server, then run pytest in `worker/`.

```
cd worker && uv run --group dev pytest tests -q
```

- `tests/test_mubit.py` is a unit test of the Mubit client. It needs no server and no
  network.
- `tests/test_users.py` calls the API and needs a seeded, running dev server. It uses
  `http://localhost:8787` unless `BASE_URL` is set. Each run adds users to the local D1;
  re-seed to clear them. Stop `pywrangler dev` before running `worker/scripts/seed.sh`
  and start it again afterwards, or the server returns 500.

## Mubit ping

```
python3 -I worker/scripts/mubit_ping.py
```

Makes one live paid call to `gemini-3.8-flash` through the gateway and prints metadata
only. It reads `MUBIT_API_KEY` from the repo-root `.env`, not `.dev.vars`. Run it only
when checking the gateway.

## Layout

- `src/entry.py`: the FastAPI app and the `/api` routes.
- `src/mubit.py`: the Mubit gateway client.
- `schema.sql`: app tables (`users`).
- `../dataset/d1/`: listings schema and data, loaded by `seed.sh`.
- `scripts/`: `seed.sh` and `mubit_ping.py`.
- `tests/`: unit and API tests.
