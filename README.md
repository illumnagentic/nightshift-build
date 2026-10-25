# Property Swipe Agent

A swipe app for buying a home. You describe what you want in plain English, swipe
through real for-sale listings, and say why you liked or disliked each one. The app
learns what you actually want, including what you never said.

Built for the Mubit Night Shift hackathon, London, 23–25 October 2026.
Team: Zsolt (backend + Mubit), Yewen (frontend + demo).

This README is an overview. Where it and [docs/decisions.md](docs/decisions.md)
disagree, decisions.md wins. Status per feature lives in [docs/plan.md](docs/plan.md).

## Intention

House hunting is slow because buyers cannot list everything they care about. They say
"2-bed, Zone 2, under £550k" and leave out that they hate ground floors, need a bright
living room and will not take a short lease. Portals filter on what was typed, so the
buyer wades through listings that match the brief and still miss.

The aim is a deck that gets better with every swipe, for two reasons:

- **This buyer's taste** is learned from their swipes and feedback (memory, Layer 1).
- **The curator itself improves across buyers.** Corrections from many buyers train an
  adapter through Mubit, so a brand-new buyer reaches a good match in fewer swipes
  (model update, Layer 2).

The hackathon brief was to route every LLM call through Mubit and show a correction
turning into a model update for a recurring task. Our recurring task is the
**curator**: the model that decides which listings to show a buyer, and in what order.

## How it works

1. **Pick or create a user.** Username only, no passwords. Accounts exist so each team
   member and persona has their own prefs, swipes, favourites and taste profile.
2. **State preferences** in natural language, optionally with a postcode for commute.
   The backend turns them into hard limits (enforced in code) and soft preferences.
3. **Hard filters** run in code. A listing that breaks a hard limit is never shown.
4. **The curator** (`gemini-3.8-flash` through Mubit) ranks the listings that pass. It
   reads structured listing fields, photo and floorplan flags, the user's stated
   prefs and their learned taste profile.
5. **The deck** mixes ranked cards with **exploration cards**, about 1 in 5, drawn from
   a low percentile band of the filtered pool. Without them, feedback only covers
   cards the curator already chose, so a false exclude is never corrected. Each card
   carries a `source` flag (`ranked` or `exploration`) in the API and logs. It is never
   shown on the card.
6. **Swipe**: left (dislike), right (like), or superlike.
7. **Feedback screen** after each swipe: feature chips filtered to that listing (no
   garden chip on a third-floor flat), a phrase dialog per chip with preset
   suggestions, and a free-text box for the card as a whole. No numeric ratings.
   - Compulsory for roughly the first 15–20 cards, as onboarding, with no skip. This
     gives the agent enough signal from a cold start.
   - After that it is optional with a Skip button. A ranked card gets it on any swipe.
     An exploration card gets none on a left swipe (the curator was right) and gets it
     on a right swipe or superlike (a false exclude).
   - A skip is recorded as `skipped: true` and is left out of the offered counts, so it
     never lowers a factor's weight.
8. **Favourites**: right swipes and superlikes. Removing one asks for a reason, which
   is a delayed correction.
9. **Flag corrections**: a user can correct a photo flag ("not damp"). The correction is
   written onto the cached flag and the curator reads the corrected text.

## Backend

Python, FastAPI on a Cloudflare Python Worker, run locally with `pywrangler dev`
against a local D1 database. Code in [worker/](worker/), data pipeline in
[dataset/](dataset/).

It owns everything that is not drawing the screen:

- **Users**: username-only accounts, identified by the `X-User-Id` header.
- **Preferences** (`worker/src/prefs.py`): one Gemini call through Mubit turns the
  user's text into hard limits and soft preferences, checked before saving.
- **Hard filters** (`worker/src/filters.py`): budget, bedrooms, property type, EPC,
  tenure, lease length and maximum commute, in code, never by the model. Violations are asserted zero.
- **Commute** (`worker/src/tfl.py`): optional TfL lookup, cached per
  (listing, postcode).
- **Mubit client** (`worker/src/mubit.py`): every LLM call goes through it, and it
  records the `mreq_…` request ID.
- **Curator and deck** (B4): ranks the filtered pool, builds the deck with exploration
  cards, stores each decision with its `mreq_` ID and profile version.
- **Feedback and taste profile** (B5): swipes, chip answers, offered-vs-chosen counts,
  the versioned profile, flag corrections, favourites.
- **Personas and eval** (B6, B7): simulated buyers that swipe through the same API,
  and a scoring script that produces the numbers for the graph.

## Frontend

Vite + React + TypeScript in [web/](web/). It calls only our backend, never an LLM,
Mubit or TfL. In development the Vite server proxies `/api` to the backend. A typed
API client has an HTTP version and an in-memory mock built from the contract, so the
screens were built before the backend existed.

Screens:

- **User picker**: pick an existing user or create one; the choice is remembered.
- **Prefs**: free-text preferences plus an optional workplace postcode.
- **Deck**: the property card (photos, price, key facts, EPC), swipe left or
  right, or superlike.
- **Feedback**: filtered chips, the phrase dialog, free text, compulsory onboarding,
  then Skip.
- **Favourites**: saved listings, remove with a reason.
- **Results** (F5, in progress): the three-bar chart with error bars and the
  false-exclude panel.

## How Mubit improves the model

Mubit is a base-URL proxy. Every LLM call goes through it: curator, photo flags,
preference parsing, personas, lesson summariser. Only the **curator** is trained.

**Two layers.**

- **Layer 1, memory, is ours.** The taste profile lives in D1, built from swipes and
  chip feedback, and versioned. We do not use Mubit's memory API.
- **Layer 2, the model update, is Mubit's.** Mubit keeps curator calls as examples.
  Once 25 are kept, it can train an adapter on an open-weight model that learns to
  give the answers the provider model gave, and tests it against them.

**The loop, from one correction to a new model:**

1. A buyer corrects the curator: swipes right on an exploration card, says a chip is a
   deal-breaker, removes a favourite with a reason, or corrects a photo flag.
2. Our taste profile updates and gets a new version number.
3. The next curator call carries that profile in its user message.
4. The provider model (`gemini-3.8-flash`) gives the corrected answer.
5. Mubit keeps that call as a training example.
6. The adapter trains on the kept examples and becomes the updated curator.

Each curator decision stores Mubit's `x-middleware-request-id` (`mreq_…`) and the
profile version, so the recording can show the trail: correction → profile version →
curator call → adapter version.

What the adapter learns is not one buyer's taste (memory already covers that). It
learns, across many buyers, how to rank well given a profile, so a new buyer with an
empty profile gets a better deck sooner.

**Rules that keep the training data usable:**

- **Route**: native Gemini API at `https://api.mubit.ai/gemini`. The app sends only
  the Mubit key. The Gemini key is set in the Mubit console under Provider keys.
- **Fixed task shape**: one fixed system prompt, never templated except with numbers
  or IDs. Everything per user (prefs, profile, lessons, past swipes, the listing) goes
  in the user message. Model ID, the thinking setting (low, set explicitly) and the
  response schema are frozen; changing any of them restarts Mubit's example count.
- **Compact requests**: structured listing fields, not raw API dumps.
- **Volume**: simulated personas generate the examples. Persona batch Saturday
  afternoon, aiming for 100+ kept examples. First training once 25 are kept. The daily
  cap resets at 01:00 London; second training then, with corrected examples.

## Proof: the evaluation

The demo is a **screen recording plus one graph**. Nobody swipes live.

- **Graph**: three bars — base curator / base + memory / updated curator + same memory.
  Bar 1 vs 2 shows memory (Layer 1). Bar 2 vs 3 shows the adapter (Layer 2).
- **Primary number**: hits in the top 5. Of the curator's five highest-ranked held-out
  listings, how many the persona's hidden rules count as good. Averaged over held-out
  personas, with error bars.
- **Second panel**: false-exclude rate, rule-good listings ranked below the cut.
- **Scored by code, not an LLM.** Each persona has a rules block (for example
  `reject: ground_floor AND epc<=D`). A script scores every stored ranking against it.
  Hidden rules go to the persona that swipes, never to the curator.
- **Held out**: about 20 personas, 15 train and 5 held out; about 25% of listings held
  out, duplicates removed across the split. Team-member accounts feed training but
  never the eval.
- **No exploration cards in the eval.** The curator ranks the whole held-out pool.
- **Bar 3 source**, first route that works: (A) the adapter serves our calls through
  the gateway; (B) the adapter can be downloaded and we serve it; (C) a small fixed
  eval set through the console's Try models; (D) none, so the graph shows bars 1 and 2
  and the update is shown through Mubit's version history and match rate.
- "Swipes until first great find" appears only in the Alex → Jordan illustration in
  the recording, labelled as such. It is too noisy to be the proof.

## Data

- **Listings**: a frozen dump of 635 London and commuter-belt homes **for sale**, from
  the unofficial Rightmove API on RapidAPI. Kept only with EPC, floorplan and photos.
  The app never calls the source live. See [dataset/README.md](dataset/README.md).
- **Images**: 6,169 photos and 672 floorplans, downloaded once (gitignored under
  `dataset/photos/`, with a committed manifest).
- **Photo and floorplan flags**: one Gemini call through Mubit per listing, returning a
  flag per image with source image and confidence. 14,684 rows in D1 `photo_flags`.
  Feature chips per listing are generated from these flags and listing fields.
- **Demo EPC values**: 487 listings had no EPC letter in the scraped text, so they carry
  a made-up letter drawn with a fixed seed. Nothing in the database marks them; compare
  with `listings.jsonl`. Every `epc_potential` is made up.
- **Commute (TfL)**: a **stretch goal** since 25 October. No TfL key; keyless access is
  slow. If a user gives a postcode, the backend asks TfL for a weekday 08:30 arrival by
  public transport. Nothing depends on it and the deck never waits for it.

## Stack

| Part     | Choice                                                                           |
| -------- | -------------------------------------------------------------------------------- |
| Backend  | Python, FastAPI on a Cloudflare Python Worker, run locally with `pywrangler dev` |
| Database | D1, local only, filled by a seed script. One per laptop                          |
| Frontend | Vite + React + TypeScript                                                        |
| LLM      | `gemini-3.8-flash` (curator), Gemini Flash-Lite (photo flags), all through Mubit |
| Deploy   | None. Everything runs on one laptop; the recording is made from it               |

## Repository layout

```
docs/       decisions, plan, API contract, product doc, research
worker/     backend: FastAPI app, D1 schema, seed script, tests
web/        frontend: Vite + React app
dataset/    listings dump, D1 schema and seed, fetch/normalise/flag scripts, tests
evidence/   per-step verification records (metadata only)
.claude/    dev-kit rules, agents, skills, hooks, progress files
```

## API

Defined in [docs/api-contract.md](docs/api-contract.md). Base URL
`http://localhost:8787/api`. The user is identified by `X-User-Id` on every endpoint
except `GET /users`, `POST /users` and `GET /stats`.

| Endpoint                                             | Purpose                                                 |
| ---------------------------------------------------- | ------------------------------------------------------- |
| `GET /users`, `POST /users`                          | list, create users                                      |
| `GET /prefs`, `PUT /prefs`                           | read, save natural-language prefs (poll for commute)    |
| `GET /deck?n=10`                                     | next cards, each with a `decision_id` and `source` flag |
| `GET /listings/{id}`                                 | full listing                                            |
| `POST /decisions/{decision_id}/swipe`                | left, right or superlike                                |
| `PUT /decisions/{decision_id}/feedback`              | chip answers, free text, or skip                        |
| `POST /flags/{flag_id}/correction`                   | correct a photo flag                                    |
| `GET /favourites`, `DELETE /favourites/{listing_id}` | favourites, remove with reason                          |
| `GET /profile`                                       | taste profile and what changed it                       |
| `GET /stats`                                         | numbers for the dashboard graph                         |

Simulated personas call this same API. There is no persona, batch or train endpoint;
training happens in the Mubit console.

## Running locally

Prerequisites: `uv`, Node.js 20+ with `npx`, network access. Secrets are shared out of
band and never committed.

```bash
# backend secret
echo 'MUBIT_API_KEY=...' > worker/.dev.vars

# seed the local D1 (with the dev server stopped)
worker/scripts/seed.sh

# backend, http://localhost:8787/api
cd worker && uvx --from workers-py pywrangler dev

# frontend, http://localhost:5173 (proxies /api to :8787)
cd web && npm ci && npm run dev
```

`PUT /api/prefs` makes a paid Gemini call every time on the normal dev server. Re-run
`seed.sh` after pulling schema changes, with the server stopped. Details in
[worker/README.md](worker/README.md).

## Tests

```bash
cd web && npm test && npm run typecheck

# backend unit tests, no server or network
cd worker && uv run --group dev pytest tests/test_filters.py tests/test_prefs_unit.py \
  tests/test_mubit.py tests/test_tfl_unit.py -q
```

The backend API tests need a seeded server in **test mode** on port 8788, pointed at a
fake upstream so nothing reaches Mubit or TfL. Never run them against the normal dev
server. The exact command is in [worker/README.md](worker/README.md). Dataset tests are
described in [dataset/README.md](dataset/README.md).

## Status

From [docs/plan.md](docs/plan.md):

| Feature                                 | Owner | State                               |
| --------------------------------------- | ----- | ----------------------------------- |
| API contract                            | both  | done                                |
| B1 Scaffold                             | Zsolt | done                                |
| B2 Data prep (dump, split, photo flags) | Zsolt | done                                |
| B3 Preferences and filters              | Zsolt | done (commute optional)             |
| B4 Curator and deck                     | Zsolt | open                                |
| B5 Feedback and taste profile           | Zsolt | open                                |
| B6 Personas                             | Zsolt | open                                |
| B7 Eval and stats                       | Zsolt | open                                |
| F1 Shell                                | Yewen | done                                |
| F2 Swipe deck                           | Yewen | done                                |
| F3 Feedback screen                      | Yewen | done                                |
| F4 Prefs and favourites                 | Yewen | done                                |
| F5 Dashboard                            | Yewen | in progress on `feat/web-dashboard` |
| F6 Recording                            | Yewen | open                                |

Checkpoints: Sat 13:00 (create user, swipe a real deck, chip feedback), Sat afternoon
(25+ kept curator examples, persona batch running), Sat evening (first training), Sun
01:00 (second training), Sun 06:00 (freeze, eval, graph final), Sun 10:00 (submission).

## Out of scope

- User-initiated A-vs-B comparison of two properties (post-hackathon idea).
- Numeric ratings, agent-generated chip lists, "did I understand you?" lesson receipts.
- Passwords, a deployed backend, a cloud D1.
- Judges' swipes in training (they watch a recording).
- A trained photo-flag adapter (stretch, only if image tasks turn out to be trainable).

## Open questions

Not blocking the build. Full text in [docs/decisions.md](docs/decisions.md).

- **Exploration metric direction.** With a band recomputed by the curator under test, a
  better curator makes exploration acceptances fall, not rise. The product doc says the
  opposite and needs correcting. Present it as false excludes falling.
- **Exploration seeding**: hold picks fixed per user, or accept random-draw noise.
- **Volume**: 2–4 exploration cards per session is too few for a rate; it must come
  from the persona batch.
- **Weight bias**: an unchosen chip may mean indifference or "fine here".
- **How personas swipe**: calling the API directly is recommended. Playwright would be a
  new dependency and needs a separate yes.
- **Mubit unknowns** for the kickoff walkthrough: whether an adapter serves live calls
  or can be downloaded, how a human verdict reaches training, whether training and its
  limits are relaxed for the event, how long training takes, which base models are used.
- **Known leak**: a sharp user could spot exploration cards because left swipes on them
  never ask for feedback. It shows only after the swipe. Accepted for the recording.
- **Mubit sessions**: Gemini has no session field, so Mubit's own held-back test may be
  split per call rather than per user and flatter its "matched X%". Our eval is
  unaffected.

## How we work

The repo uses a Claude Code dev kit in `.claude/` ([.claude/CLAUDE.md](.claude/CLAUDE.md)).

- One feature branch and one progress file per feature (`.claude/progress/<slug>.md`),
  rebased on `main` often, merged by squash PR.
- Commit and PR titles: `type(scope): message`, title only, no body, no attribution.
  Commits go through `.claude/scripts/safe-commit.sh`; hooks block anything else. After
  cloning, install the git hook as described in [.claude/README.md](.claude/README.md).
- Evidence for each step goes in `evidence/`, metadata only.
- Secrets in `.env` and `.dev.vars`, gitignored.
