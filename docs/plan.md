# Plan

High-level roadmap. One line per feature, ticked in the PR that merges it, so this
file only changes on `main`. Detail lives in each feature's progress file, not here.
Decisions behind every line: [decisions.md](decisions.md).

Branch names are proposals; set them at feature-kickoff.

## Checkpoints

- [ ] **Sat 13:00** — a user can be created, swipe a real deck (with at least one
  exploration card) and give chip feedback. Curator calls show in Mubit under one task.
- [ ] **Sat afternoon** — curator task has 25+ kept examples. Persona batch running.
- [ ] **Sat evening** — first adapter training done (or waiting on the daily cap).
  Full loop works end to end on one laptop.
- [ ] **Sun 01:00** — daily training cap resets. Second training with corrected examples.
- [ ] **Sun 06:00** — feature freeze. Eval run, graph final.
- [ ] **Sun 10:00** — recording and submission in.

## Shared, before either side builds

- [x] **API contract** — Zsolt + Yewen — `docs/api-contract.md`: endpoints, request and
  response shapes, `decision_id`, card `source` flag. Frontend mocks come from it.

## Backend — Zsolt

- [x] **B1 Scaffold** — `feat/backend-scaffold` — Python Worker + FastAPI, local D1
  schema, seed script, username-only accounts, Mubit gateway client.
- [ ] **B2 Data prep** — `feat/data-prep` — RapidAPI dump (500+ rich for-sale
  listings), photo flags via Gemini Flash-Lite through Mubit, listing train/eval split.
  Listing dump (635) and train/eval split merged (PRs #1, #2, #5). Still open: photo
  and floorplan textualisation, own branch `feat/photo-flags` (needs its own kickoff);
  workflow in decisions.md under Image textualisation workflow.
- [x] **B3 Preferences and filters** — `feat/prefs-filters` — natural-language prefs
  to hard limits + soft prefs, hard filters in code, TfL commute cached per
  (listing, postcode).
- [ ] **B4 Curator and deck** — `feat/curator-deck` — fixed-prompt curator on
  `gemini-3.8-flash`, deck with percentile-band exploration (seeded per user), decision
  IDs and `mreq_` IDs stored.
- [ ] **B5 Feedback and taste profile** — `feat/feedback-profile` — swipe / superlike /
  chip feedback endpoints, offered-vs-chosen logging, versioned profile (direction +
  weight), flag corrections, favourites.
- [ ] **B6 Personas** — `feat/personas` — persona CSV with rules block, 15/5 split,
  persona swiper calling the API, batch runner.
- [ ] **B7 Eval and stats** — `feat/eval-stats` — scoring script against persona rules,
  three-arm run, stats endpoint for the graph, results in `evidence/`.

## Frontend — Yewen

- [x] **F1 Shell** — `feat/web-shell` — Vite + React + TS, pick or create user, API
  client against mocks from the contract.
- [x] **F2 Swipe deck** — `feat/web-deck` — property card, swipe left / right,
  superlike.
- [ ] **F3 Feedback screen** — `feat/web-feedback` — filtered chips, phrase dialog with
  preset suggestions, free-text box, compulsory for the first 15–20 cards.
- [ ] **F4 Prefs and favourites** — `feat/web-prefs-favourites` — prefs input with
  workplace postcode, favourites with remove-with-reason.
- [ ] **F5 Dashboard** — `feat/web-dashboard` — three-bar chart with error bars,
  false-exclude panel.
- [ ] **F6 Recording** — `feat/demo-recording` — demo script, Alex → Jordan run,
  correction trail, final recording.

## Order

API contract first. Then B1 and F1 in parallel. B2 → B3 → B4 is the critical path to
Sat 13:00; F2 and F3 build against mocks meanwhile and switch to the real API as B4
and B5 land. B6 must start by Sat afternoon to hit the training timeline. B7 and F5
meet at the stats endpoint. F6 last.
