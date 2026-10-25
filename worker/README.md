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
listings data (635 rows in `listings`, none in `users`, `prefs` or `commute_cache`). It is safe to re-run. Do it
before starting the dev server, and again whenever you want an empty `users` table.
Stop `pywrangler dev` before running it, then start it again. A running server keeps a
stale view of the local D1 and returns 500 until restarted.

## Run

In `worker/`:

```
uvx --from workers-py pywrangler dev
```

The API is at http://localhost:8787/api. The web dev server (`cd web && npm run dev`)
proxies `/api` to it. This is the normal dev server and it uses the real Mubit key.

`PUT /api/prefs` makes a paid Gemini call through Mubit every time against this server.
Do not run the API tests against it.

### TfL commute times

Commute is optional. Prefs saved without a `commute_postcode` make no TfL calls, and
`commute_status` stays `null`. The warm-up below applies only to users who give a postcode.

After pulling this change, each laptop must re-run `worker/scripts/seed.sh` with the dev server
stopped; otherwise a save without a postcode fails on the old NOT NULL columns.

Saving prefs with a postcode starts the commute lookup for it. Each `GET /api/prefs` while
`commute_status` is `pending` runs one batch of TfL calls; the status becomes `ready`
once every listing has a cached time or TfL was asked and could not route it, so a few
listings can be left unknown. Times are cached per (listing, postcode) in
`commute_cache`, so a second user with the same postcode needs no TfL calls.

- Anonymous TfL is slow. A new postcode takes minutes to reach `ready`. TfL throttles
  after about 50 calls and blocks for about 30 seconds.
- Poll `GET /api/prefs` no faster than every 2 to 3 seconds. A run of fast `pending`
  replies means the throttle: wait about 30 seconds.
- Save each persona destination and the demo postcode once, and poll each to `ready`,
  before the persona batch and before recording.

## Tests

Test mode is mandatory for the API tests. In test mode the dev server gets a fake Mubit
key and sends Gemini and TfL calls to a fake upstream that pytest runs on port 8799, so
nothing reaches Mubit or TfL. Order: seed, start the test-mode server, run pytest.

From the repo root:

```
worker/scripts/seed.sh
```

In `worker/`, start the server in test mode (port 8788, so it does not clash with the
normal dev server on 8787):

```
uvx --from workers-py pywrangler dev --port 8788 --inspector-port 9239 \
  --var MUBIT_API_KEY:test-key-not-a-real-key \
  --var GEMINI_BASE:http://127.0.0.1:8799 \
  --var TFL_BASE:http://127.0.0.1:8799
```

Then, in `worker/`:

```
BASE_URL=http://localhost:8788 uv run --group dev pytest tests -q
```

The fake upstream listens on `FAKE_PORT` (default 8799). It must match the port in
`GEMINI_BASE` and `TFL_BASE`. To use another port, for example when a second server is
running, change all three together:

```
FAKE_PORT=8801 BASE_URL=http://localhost:8790 uv run --group dev pytest tests -q
```

with the server started with `--var GEMINI_BASE:http://127.0.0.1:8801 --var TFL_BASE:http://127.0.0.1:8801`.

`BASE_URL` defaults to http://localhost:8787, the normal dev server. Always set it to the
test-mode server. Before the API tests run, a guard sends one probe save and one probe
poll. If the fake upstream did not receive them with the fake key, or the server is not
running, the run stops with exit code 3 and prints the command above. The guard covers
`test_prefs.py`, `test_commute.py`, `test_deck.py`, `test_swipe.py`, `test_feedback.py`, `test_favourites.py` and `test_flags.py`.

These modules need no server and no network, and run with a plain
`uv run --group dev pytest tests/test_filters.py tests/test_prefs_unit.py tests/test_mubit.py tests/test_tfl_unit.py tests/test_chips.py tests/test_curator_unit.py tests/test_profile_unit.py -q`:

- `tests/test_filters.py`: the hard filters, including a check over the real listings.
- `tests/test_prefs_unit.py`: parsing and checking of the model's reply.
- `tests/test_mubit.py`: the Mubit client.
- `tests/test_tfl_unit.py`: reading TfL answers and building the journey URL.
- `tests/test_chips.py`: the chip catalogue and its filtering by listing.
- `tests/test_curator_unit.py`: the curator request, its reply checking and the fake curator answer.
- `tests/test_profile_unit.py`: the taste profile factors, term matching and removal rows.

`tests/test_users.py`, `tests/test_prefs.py`, `tests/test_commute.py`, `tests/test_deck.py`, `tests/test_swipe.py`,
`tests/test_feedback.py`, `tests/test_favourites.py` and `tests/test_flags.py` call the API and
need the seeded test-mode server. Each run adds users to the local D1. The fake answers
a few postcodes with 500 so the suite can be repeated without re-seeding, but re-seed
to clear the users. `test_deck.py` also reads the local D1 with `npx wrangler d1 execute` from this directory, so the server under test must have been started from this same `worker/` directory. Stop the dev server before running `worker/scripts/seed.sh` and
start it again afterwards, or the server returns 500.

## Adding new tables to an existing local D1

New tables are added to `schema.sql` with `CREATE TABLE IF NOT EXISTS`. To get them onto
a D1 you already have, without losing users, run from `worker/`:

```
npx wrangler d1 execute haka --local --file schema.sql
```

Verified on 2026-10-25 against a seeded D1 holding 143 users: it exits 0 and the users stay.
It cannot add a column to an existing table, so changes to existing tables need a re-seed.
`worker/scripts/seed.sh` also works but wipes users. The swipe and feedback features add `favourites`,
`profile_versions`, `feedback` and `favourite_removals` this way.

## Curator and deck

`GET /api/deck` serves unswiped cards first, then new ones. New cards come from one
curator call: a seeded sample of 30 train-split listings that pass the user's hard
filters is sent to `gemini-3.8-flash` through Mubit, which returns them as an ordered
list of ids. The system prompt, response schema and low thinking setting are fixed;
everything per user goes in the user message. About 1 card in 5 is an `exploration`
card, drawn from the 50th to 80th percentile of that ranking. Every call is stored in
`curator_calls` (candidates, full ranking, status, `mreq_` id, token counts) and each
served card in `decisions`.

Each call also carries the user's taste profile (`taste_profile`, from their latest profile version) and their ten most
recent feedback entries and favourite removals (`recent_feedback`, newest last). The profile version used is stored on
the call and on every card it created. A new user sends `{}`, `[]` and version 0. Flag corrections reach the curator
through the candidate photo digest.

A `GET /api/deck` that needs new cards is a PAID Gemini call through Mubit on the
normal dev server. A request whose unswiped cards already cover `n` makes no call.
Measured on 2026-10-25 (one call, 30 candidates): 6,995 prompt tokens, 335 output
tokens, 5.3 seconds. At an assumed Flash-class price (unconfirmed for
`gemini-3.8-flash`) that is about 0.002 GBP per call, and about 0.011 GBP if the price is
five times higher. See `evidence/curator-deck/step-4.md`.

Under React StrictMode (`web/src/main.tsx`), a dev deck load fires two concurrent
`GET /api/deck` for one user, so it can make two curator calls. No duplicate card is
served, but both calls are paid and both become kept examples. Persona runs must keep
one `GET /api/deck` in flight per persona. Never run the API tests against the normal
dev server.

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
- `src/prefs.py`, `src/tfl.py`, `src/filters.py`: prefs parsing, TfL commute times, hard filters.
- `src/chips.py`, `src/curator.py`, `src/deck.py`: chips per card, the curator request and reply, `GET /api/deck`.
- `src/taste.py`: profile versions, feedback factors, `GET /api/profile`, and the profile and recent feedback the curator reads.
- `schema.sql`: app tables (`users`, `prefs`, `commute_cache`, `curator_calls`, `decisions`, `favourites`, `profile_versions`, `feedback`, `favourite_removals`).
- `../dataset/d1/`: listings schema and data, loaded by `seed.sh`.
- `scripts/`: `seed.sh` and `mubit_ping.py`.
- `tests/`: unit and API tests, and the fake upstream (`fake_upstream.py`).
