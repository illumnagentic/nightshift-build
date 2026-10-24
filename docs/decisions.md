# Decisions

Settled choices for the Property Swipe Agent build. Short and current: if a decision
changes, rewrite its line and re-date it. Do not stack corrections.

A box is ticked only once the team has agreed it. `Doc proposes` is what the research
docs suggest, not a decision.

## Product

- [x] **Market.** Sale or rent?
  Doc proposes: sale (EPC, tenure, floorplans give more signals).
  Decided: 2026-10-23 — sale.

- [x] **Core interaction.** Which feedback mechanisms are in the cut?
  Options: (a) swipe + checkbox survey on left swipe; (b) per-feature feedback on a
  photo or bullet ("love / live with / deal-breaker"); (c) "did I understand you?"
  lesson receipt with confirm / edit; (d) A-vs-B compromise comparison.
  Doc proposes: product doc (a); research doc (b) + (c) first, (d) later.
  Decided: 2026-10-23 — a blend of (a) and (b), as one flow per card:
  1. Property card with three actions: swipe left (dislike), swipe right (like),
     superlike button.
  2. Feedback screen after the decision. A preset list of feature chips (e.g. lush
     garden, natural light inside, parking), plus a free-text box for the card as a
     whole.
  3. Tapping a chip opens a dialog: free text only, with preset suggested phrases.
     No numeric rating. Chips are optional, any number of them, and an existing
     answer can be edited.
  4. Done closes the screen and the next card appears.
  The feedback screen is compulsory for roughly the first 15–20 cards, as onboarding
  (the Spotify genre-picker pattern), then optional on right swipes. It is what gives
  the agent enough signal to learn preferences from a cold start.
  Chip lists are **filtered per listing** from the photo flags and listing fields. A
  garden chip is not shown on a third-floor flat with no garden.
  A chip answer is about **this property's** version of that feature, phrased as how
  much the user likes or dislikes it. The general preference is derived from these
  answers across cards — see Learning model below.
  Not in the cut: numeric ratings; agent-generated chip lists (stretch — preset list
  for the demo); (c) lesson receipts; (d) A-vs-B comparison.

- [x] **User-initiated comparison.** User picks any two properties, compares photos,
  details and features side by side, and ranks them. Possibly also a learning signal.
  Related to option (d) above, but user-driven rather than system-offered.
  Open: in the cut or stretch? Does a ranking feed learning, and if so, is a "why"
  follow-up required (two properties differ in many features, so the choice alone
  does not say which one mattered)?
  Decided: 2026-10-23 — out of scope for this hackathon. Post-hackathon idea only.

- [x] **Exploration cards.** About 1 in 5 cards from a lower-ranked band?
  Doc proposes: in the cut.
  Decided: 2026-10-23 — in the cut. Without it, feedback only ever covers cards the
  curator already chose to show, so a false exclude is never corrected.
  With the chip feedback screen, a right swipe on an exploration card now carries a
  reason as well as the correction, which the original swipe-only plan did not.
  **Band:** a percentile band of the pool that passes the hard filters, never fixed
  ranks. If filters cut 300 listings to 30, "ranks 20–40" is the bottom of the barrel,
  exploration cards are obviously bad and teach nothing. Check real pool sizes during
  data prep. Decided: 2026-10-23.
  **Flag:** each card carries a source flag, `ranked` or `exploration`, in the API
  payload and the logs. Never shown on the card face — a user who can see a card is
  exploratory swipes differently. Decided: 2026-10-23.
  **Scoring (inverse):** an exploration card is expected to be rejected, so a rejection
  counts as the curator being right and an acceptance as a false exclude. Exploration
  cards are therefore measured on their own metric, not mixed into the headline count.
  Decided: 2026-10-23.
  Open: inverse scoring only reads as improvement if the band is recomputed by the
  curator under test. A better curator promotes the good ones out of its own low band,
  so the band gets purer rubbish and acceptances fall. If the band is instead fixed
  from a baseline ranking, the measure is "does the updated curator now rank these
  higher", which is a different calculation. Only affects the live exploration metric —
  the headline eval uses no exploration cards.
  Open: this contradicts the product doc, which claims a *rising* exploration hit rate
  proves improvement. With a recomputed band the rate should fall. The doc needs
  correcting or the direction needs restating.
  Open: present it as false excludes falling, not rejections rising. "Our model
  improved, users now reject more cards" lands badly with a judge.
  Open: still the seeding question — exploration picks held fixed per user, or base and
  updated decks differ by random draw as well as by curator, and the graph is noisy.
  Open: one card in five over a 10–20 card session is only 2–4 exploration cards.
  Far too few to quote a rate from. Volume has to come from the persona batch.

- [x] **Commute (TfL).** In the cut or stretch?
  Doc proposes: stretch.
  Decided: 2026-10-23 — in the cut. The user enters one location (workplace or
  anywhere else). The TfL Journey Planner API returns the commute time between that
  location and each property. A calculated fact, not an LLM guess.
  - **Input:** postcode. Free-text place names make TfL return candidate matches
    instead of a journey.
  - **Assumptions:** weekday, arrive 08:30, public transport. Shown next to the time
    on the card.
  - **When:** once when the location is saved, for every listing that passes the other
    hard filters, cached in D1 per (listing, location) pair. Never during a swipe.
  - **Max commute:** if the user states a limit, it is a hard filter enforced in code.
    Otherwise commute is a factor the curator weighs.
  - **Volume:** personas share about 5 destinations so the cache does most of the work.

- [x] **Accounts.** Username + hashed password in the cut?
  Doc proposes: yes, needed to demo a new user live.
  Decided: 2026-10-23 — as simple as possible. Accounts exist only so multiple users
  (team members, personas) each get their own prefs, swipes, favourites and Mubit
  user_id. Judges watch a recording, so no polish.
  **Username only, no passwords.** Pick or create a user; the API takes the user_id.
  Known cost: on a public deploy anyone with the URL can act as any user. Acceptable
  with fake data. Whether to add one shared access key is settled with Deploy below.

## Learning model

- [x] **Two metrics per factor.** Every factor (distance to a station, garden size,
  how busy the area is, parking) carries two separate things:
  1. **Direction** — where on that factor the user sits. Not like or dislike: some
     people want a quieter area, others want a busier district. Both are valid
     positions on the same factor.
  2. **Weight** — how much that factor matters to this person at all. Location may
     decide everything for one buyer and be an afterthought for another.
  Both are learned, and both feed the curator. A factor with a strong direction and a
  low weight should not drive a decision.
  Decided: 2026-10-23.

- [x] **How the two are inferred.** No numeric input from the user. Instead:
  - **Weight** from how often a factor comes up. A chip chosen repeatedly, or a term
    recurring in the free-text box, means the factor matters. Chips that are available
    but consistently left alone suggest it matters less.
  - **Direction** from reading what was written. For or against, and how strongly, is
    in the user's words, not in a counter.
  Preset chips exist to seed the popular factors so there is something to count early.
  Decided: 2026-10-23.
  Open: filtering chips per listing biases the weight count. Someone who cares deeply
  about parking sees the parking chip only on properties that have parking, so it is
  mentioned rarely and reads as low weight. Proposed fix: log how often each chip was
  *offered* as well as chosen, and weight on the ratio, not the raw count. Build this
  in from the start — retrofitting it makes the early swipe data unusable.
  Open: an unchosen chip is ambiguous — indifference, or the feature was simply fine
  here. Absence of comment is not absence of care.
  Open: strength of feeling now rests entirely on wording, so "would rather not" and
  "absolutely not" are hard to tell apart. Proposed fix: the preset phrases carry the
  strength, e.g. must-have / nice to have / would prefer not / deal-breaker. One tap
  then gives direction and force together, with free text still available.

## Proof and evaluation

- [x] **Demo format.** Live swiping by judges, or a recording?
  Decided: 2026-10-23 — a screen recording, plus a graph showing the improvement.
  No judge swipes live, so the length of compulsory onboarding does not eat the slot.
  Knock-on: the product doc scores the demo 5/5 on "judges swipe live". That claim no
  longer holds, so the pitch needs a different strength — likely that the recording
  shows one complete, genuine loop with correction provenance, not a staged moment.

- [x] **Headline metric.** What does the dashboard prove?
  Decided: 2026-10-23.
  - **Graph:** one chart, three bars — base curator / base + memory / updated + same
    memory. Bar 1 vs 2 shows memory (Layer 1); bar 2 vs 3 shows the adapter (Layer 2).
  - **Primary number:** hits in the top 5 — of the curator's five highest-ranked
    held-out listings, how many the persona's hidden rules count as good. Averaged
    across held-out personas, with error bars for the spread.
  - **Second panel:** false-exclude rate — rule-good listings ranked below the cut.
  - **Scoring by code, not an LLM.** Each persona brief carries a rules block (e.g.
    `reject: ground_floor AND epc<=D`, `prefers: light=bright`); a script scores every
    ranking against it. Persona LLMs still swipe and write feedback for training data.
  - **No exploration cards in the eval.** The curator ranks the whole held-out pool, so
    the exploration band question does not touch the proof.
  - **Hard-constraint violations:** enforced in code, asserted zero, one line in the
    pitch, not charted.
  - **Recording:** "swipes until first great find" appears only as the Alex → Jordan
    illustration, labelled as such. Too noisy to be the proof.
  - **Bar 3 source.** The scoring script scores stored decisions, whichever model made
    them. Decisions for bar 3 come from the first route that works:
    A. the adapter serves our calls through the gateway — persona eval as normal;
    B. the adapter can be downloaded — we serve it and run the same eval;
    C. console only — a small fixed eval set through Try models, answers stored in the
       decisions table (capped, so small, but genuine);
    D. none — graph shows bars 1 and 2; the update is shown with Mubit's version
       history, "matched X% of provider answers", and cost/latency vs the provider.
  - **Stretch:** rejection-reason accuracy; soft preferences wrongly promoted to hard.
  - **Prep impact:** persona briefs need the rules block; scoring script to write.

- [x] **Training vs evaluation split.** Hold out a set of listings that are never used
  for training?
  Decided: 2026-10-23 — hold out both personas and listings. About 20 personas: 15
  train, 5 held out. About 25% of listings held out, duplicates removed across the
  split. The adapter trains across users, so evaluating on a training persona cannot
  tell "better at anyone's hidden taste" from "memorised that persona".

- [x] **Real-user feedback in shared training.** Do judges' and our own swipes feed the
  shared adapter, or only simulated personas?
  Decided: 2026-10-23 — team members and simulated personas only. Judges watch a
  recording, so they give no feedback. Team-member accounts have no rules block, so
  they feed training but never the evaluation.
  Persona preferences live in a CSV sheet. Proposed shape, one row per persona per
  factor: `persona_id, split (train|eval), factor, direction, weight, dealbreaker
  (yes|no)`, plus the stated brief text per persona. This maps directly onto the
  direction + weight model and is the rules block the eval scorer reads. Hidden rules
  go to the persona that swipes, never to the curator.
  Open: how personas swipe. Recommended: call the backend API directly — fast, no
  browser, and it uses the API contract that has to exist anyway. Playwright drives
  the real UI but is slow, brittle for hundreds of swipes, and is a new dependency, so
  it needs a separate yes from both of you.

## Mubit

Source: public Mubit docs and the `mubit-task-design` skill, read 23 Oct 2026. Mubit
is a base-URL proxy. An adapter trains after 25 kept examples and is tested against the
provider model's answers. No documented API for corrections, no documented way to call
an adapter from the app, no live memory API. The design below works whichever way the
unknowns fall.

- [x] **Which calls go through Mubit.** Every LLM call: curator, photo flags,
  preference parsing, personas, lesson summariser. Only the **curator** is trained.
  Decided: 2026-10-23.

- [x] **Curator task shape.** The system prompt is one fixed string, never templated
  with anything but numbers or IDs. Everything per user — stated prefs, taste profile,
  lessons, past swipes, the listing — goes in the user message. Model ID and output
  schema are fixed before the first persona run; changing either restarts the count.
  Requests kept compact: structured listing fields, not raw API dumps.
  Decided: 2026-10-23.

- [x] **Memory is ours.** The taste profile (factor, direction, weight) lives in D1,
  built from swipes and chip feedback. This is Layer 1. Not Mubit's memory API.
  Decided: 2026-10-23.

- [x] **Correction → model update path.** Correction → our profile updates (versioned)
  → next curator call carries that profile in its user message → provider gives the
  corrected answer → Mubit keeps the call as an example → the adapter trains on it.
  Every curator decision stores Mubit's `x-middleware-request-id` (`mreq_…`) and the
  profile version in D1, so the recording can show the trail: correction → profile
  version → curator call → adapter version.
  Decided: 2026-10-23.

- [x] **Training timeline.** Persona batch Saturday afternoon, not overnight, aiming
  for 100+ varied kept examples. First training as soon as 25 are kept. The daily
  training cap resets at 01:00 London on both Sat and Sun; second training then, with
  corrected examples. Real results recorded Sunday morning before the 10:00 deadline.
  No training time is documented — assume hours, not "about 2 minutes".
  Decided: 2026-10-23.

- [x] **Curator model.** Which provider and model the adapter learns to copy.
  Decided: 2026-10-24 — **`gemini-3.8-flash`, frozen.** Flash rather than Flash-Lite:
  the adapter copies the curator, so curator quality caps adapter quality. Pro-class
  models would likely exhaust the £16 before the eval. No `-latest` aliases (Google can
  repoint them mid-weekend) and no `-preview` models.
  Fixed with the model: a low thinking setting, never changed, and one response schema.
  Test call through Mubit, 2026-10-24: 200, reply "OK", `modelVersion`
  gemini-3.8-flash, request ID `mreq_01a16b49bb7479d1aa83b7df659a7740`. Thinking is on
  by default: 79 thought tokens for a one-word reply, so the setting must be explicit.
  Check real cost after the first 50 curator calls, before the persona batch.
  Decided: 2026-10-24 — Gemini, native Gemini API through Mubit
  (`https://api.mubit.ai/gemini`). We have a Gemini key with £16 credit. The Gemini key
  goes into the Mubit console under Provider keys; the app only ever sends the Mubit
  key. Replaces the earlier OpenAI-format choice.
  Known cost: Gemini has no session field, so Mubit derives sessions from the
  instructions plus the first user message. Each single-turn curator call is then
  likely its own session (inference), so Mubit's held-back test cases are split per
  call, not per user. Calls from one persona can land on both sides of Mubit's own
  test, which may flatter its "matched X%" figure. Our own eval is unaffected: it uses
  held-out personas and listings.

- [x] **Photo flags.** Gemini vision call through the gateway, not trained. A user's
  correction to a flag ("not damp") is written onto the cached flag record, and the
  curator reads the corrected text. Photo-flag adapter is stretch, only if image tasks
  turn out to be trainable.
  Decided: 2026-10-23.

**Questions for the kickoff walkthrough.** None block the build; the answers pick which
fallback (A–D under Headline metric) applies.
1. Does a passing adapter serve our live calls, or only Try models? Can it be
   downloaded, in what format?
2. How does a human verdict reach training? Is Good/Bad rating available as an API?
3. Is the memory / lessons API live for the event, at what endpoint?
4. Is training switched on for hackathon workspaces? Are the daily limit, pause,
   3 starts/day and Try models cap relaxed?
5. How long does training take at 25 examples?
6. Which base models do adapters use, and do any take images?

## Stack

- [x] **Languages.** Python backend, TypeScript frontend.
  Decided: 2026-10-23.

- [x] **Backend host.** Cloudflare Python Worker (FastAPI) or plain FastAPI host?
  Decided: 2026-10-24 — Python Worker with FastAPI, run locally with `pywrangler dev`.
  The local spike passed (below), and nothing is deployed, so the deployed half and
  the bundle-size question no longer apply.
  Mubit needs no SDK, only a base URL, so the old SDK question is gone. Remaining
  spike, 30 minutes at most: one call to the Mubit gateway from a Python Worker with
  the client we plan to use, plus one D1 query. If either fights the runtime, plain
  FastAPI host.
  **Spike result, local (`pywrangler dev`), 2026-10-24 — pass.** Throwaway Worker,
  FastAPI via `asgi.entrypoint(app)`, Python 3.13, workers-py 1.17.9, wrangler 4.152.
  - Plain runtime `fetch` → Mubit OpenAI route, starter model `gpt-4o-mini`: 200,
    request ID read (`mreq_01a16b436d0573218ee217e44471a0f6`).
  - `openai` SDK (`AsyncOpenAI`, `with_raw_response`) → same: 200, request ID read
    (`mreq_01a16b4374e47502b826da8b82243e4e`). The SDK runs on Pyodide.
  - D1 local binding: create table, insert, select all work. `.all().results` is
    already a Python list, no `.to_py()` needed.
  - Starter credit OpenAI models (from Mubit's 400): gpt-6-sol, gpt-6.1-sol,
    gpt-6-luna, gpt-6-astra, gpt-5.5, gpt-4o-mini, gpt-4.1-mini (+ dated variants).
  - Bundle: 18.9 MB of vendored modules uncompressed with `fastapi` + `openai`. Worker
    size limits apply to the compressed bundle; deploy will show whether it fits.
  Not tested: `google-genai`; the `openai` SDK working suggests it likely will.

- [x] **Password hashing.** bcrypt / argon2 may not be available in the Python Workers
  runtime; stdlib `hashlib.pbkdf2_hmac` is the fallback. Check during the spike.
  Decided: 2026-10-23 — not needed. Accounts are username only.

- [x] **Frontend.** Vite + React?
  Doc proposes: yes, no Next.js.
  Decided: 2026-10-23 — Vite + React, TypeScript.

- [x] **Database.** D1 (local + one shared cloud instance)?
  Decided: 2026-10-24 — D1, local only (the copy `pywrangler dev` keeps on disk). One
  per laptop, filled by a seed script in the repo. No cloud instance.

- [x] **Deploy.** Deploy to Cloudflare for the demo, or run from one laptop?
  Decided: 2026-10-24 — not deployed. Everything runs locally (`pywrangler dev` + Vite
  dev server); the recording is made from one laptop. Replaces the earlier
  deploy-to-Cloudflare choice. No shared access key needed: the API is not public.
  Knock-ons: the persona batch and the recording run on Zsolt's laptop, which has to
  stay awake for the batch. Yewen runs the backend locally too, against a local D1
  filled by the same seed script, so both laptops see the same data.

## Data

- [x] **Listings source.** RapidAPI unofficial Rightmove, frozen dump of 200–400
  for-sale listings with EPC + floorplan + photos?
  Decided: 2026-10-24 — RapidAPI unofficial Rightmove, Pro plan, for-sale only, frozen
  dump. Keep only listings with EPC, floorplan and photos. Target **500+**, not
  200–400: hard filters, onboarding and the held-out set all eat into the pool. Check
  the pool size per persona after filters before the batch runs.

- [x] **Photo model.** Gemini 3.5 Flash-Lite, JSON flags, cached per photo?
  Decided: 2026-10-24 — yes, called through Mubit. Send one test call first: Mubit's
  starter credit serves a fixed model list and refuses others.

- [x] **Photo flag schema.** Fields per photo and per listing.
  Doc proposes: schema in product doc section 7.
  Decided: 2026-10-24 — the section 7 schema, plus a source photo and a confidence for
  every flag. Observation, source photo and uncertainty kept as separate fields. The
  per-listing feature chips are generated from these flags.

## Team workflow

- [x] **Ownership.** A: backend + Mubit. B: frontend + demo. Who is A, who is B?
  Decided: 2026-10-24 — Zsolt: backend + Mubit. Yewen: frontend + demo.

- [x] **Git.** Trunk on `main` with small pushes and `pull --rebase`, or short branches?
  Decided: 2026-10-24 — feature branches, one per feature (matching its progress file).
  Kept short-lived and rebased on `main` often, so the two halves never drift far.
  Merged by PR, titles in the kit's `type(scope): message` format.
  Squash merge, with GitHub set to use the PR title as the commit message and an empty
  body (Settings → General → Pull Requests). GitHub's default merge message ("Merge
  pull request #…") breaks the commit format, and merges on GitHub do not pass through
  `safe-commit.sh`.

- [x] **Progress files.** One per person, named by owner (e.g. `backend-auth.md`)?
  Decided: 2026-10-24 — one per feature, owner in the name. No main progress file: it
  would lock the whole build's requirements up front, block one person's steps on the
  other's, and conflict across branches.

- [x] **Overview.** `docs/plan.md`: one line per feature (name, owner, branch, status)
  and the checkpoints (Sat 13:00, Sat evening, Sun 06:00 freeze) with what must work by
  each. Status lines only, never a copy of progress-file detail. Updated in the PR that
  merges a feature, so it only changes on `main`. Written after feature-kickoff.
  Decided: 2026-10-24.

- [x] **Step size.** Coarse vertical slices, 3–5 steps per feature?
  Decided: 2026-10-24 — yes.

- [x] **Evidence.** Mubit run IDs, adapter versions and metric outputs stored in
  `evidence/` in the repo?
  Decided: 2026-10-24 — yes. Metadata only, not raw response bodies.

- [x] **Secrets.** `.env` and `.dev.vars` gitignored, keys shared out of band?
  Decided: 2026-10-24 — yes.
