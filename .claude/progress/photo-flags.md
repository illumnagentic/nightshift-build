# Feature: Photo and floorplan textualisation

- **Slug**: photo-flags
- **Started**: 2026-10-25
- **Branch**: feat/photo-flags
- **BASE_SHA**: 8d9ed8d3a929dfe540ea221d9e2d8d52247f6e97
- **Status**: complete (2026-10-25)

---

## REQUIREMENTS (LOCKED)

Human instruction, 2026-10-25:

> get the textualisation done on worktree while backend is being built in other session

`docs/plan.md`, B2 line:

> **B2 Data prep** — `feat/data-prep` — RapidAPI dump (500+ rich for-sale
> listings), photo flags via Gemini Flash-Lite through Mubit, listing train/eval split.
> Listing dump (635) and train/eval split merged (PRs #1, #2, #5). Still open: photo
> and floorplan textualisation, own branch `feat/photo-flags` (needs its own kickoff);
> workflow in decisions.md under Image textualisation workflow.

`docs/decisions.md`, Image textualisation workflow (binding lines):

> - **Scope:** photos and floorplans both. Floorplans give room count and layout
>   for the curator. Current dump: 635 listings, 6,169 photos, 672 floorplans.
> - **Download first.** Images fetched once from the Rightmove CDN with stdlib
>   `urllib`, a small thread pool, skip-if-exists so it can resume. Stored gitignored
>   under `dataset/photos/`; a committed manifest records path, URL, sha256, bytes.
>   Freezes the dump and makes re-runs cost only Gemini, not Rightmove.
> - **Route:** plain HTTP to `https://api.mubit.ai/gemini` with `MUBIT_API_KEY`. No
>   `google-genai`. The Gemini key stays in the Mubit console. Not trained.
> - **Call shape:** one request per listing, all its images with index numbers,
>   returning one JSON entry per image. Results still stored per image, with source
>   image and confidence. About 635 calls instead of about 6,800.
> - **Cost:** Gemini media-resolution option set low or medium, not local resizing
>   (that would need Pillow). Exact per-image cost measured in the pilot.
> - **Order:** one test call, then a pilot on about 10 listings read by eye with cost
>   checked, then the full run in the background.
> - **Output:** its own file (e.g. `dataset/photo_flags.jsonl`), read by
>   `build_d1.py` into a flags table in `seed.sql`. Never written straight into
>   `listings.sqlite`: it is binary and cannot be merged across branches.

`docs/decisions.md`, Photo model:

> Decided: 2026-10-24 — yes, called through Mubit. Send one test call first: Mubit's
> starter credit serves a fixed model list and refuses others.
> (Question line: Gemini 3.5 Flash-Lite, JSON flags, cached per photo?)

`docs/decisions.md`, Photo flag schema:

> Decided: 2026-10-24 — the section 7 schema, plus a source photo and a confidence for
> every flag. Observation, source photo and uncertainty kept as separate fields. The
> per-listing feature chips are generated from these flags.

`docs/decisions.md`, Photo flags (Mubit section):

> Gemini vision call through the gateway, not trained. A user's
> correction to a flag ("not damp") is written onto the cached flag record, and the
> curator reads the corrected text.

`docs/api-contract.md`, photo flag fields (binding shape for the stored rows):

> - `field` for `photo` scope: `room`, `light`, `size_tricks`, `defects`, `missing`.
>   `light` values: `none`, `poor`, `ok`, `bright`. The other values are short text.
> - `field` for `listing` scope: `floorplan_notes`, `sqm_estimate`.
> - `value` is the flag itself. `observation` is what the model saw. `source_photo` is
>   the URL of the photo or floorplan it came from. `confidence` is `high`, `medium` or
>   `low`. `uncertainty` is free text or `null`. These are separate fields.
> - `room` is always set (never `null`) on photo-scope flags and is `null` on
>   listing-scope flags. [...] one of `living_room`, `kitchen`, `bedroom`, `bathroom`,
>   `hallway`, `garden`, `exterior`, `other`
> - `corrected_text` is `null` unless the user corrected the flag.
> - Photos the pipeline marked `skip` (agent logos, duplicates) do not appear in `photos`
>   or `photo_flags`.

### Source

Human instruction in chat (2026-10-25); `docs/plan.md` B2; `docs/decisions.md` (Image
textualisation workflow, Photo model, Photo flag schema, Photo flags);
`docs/api-contract.md` (listing detail field notes, Enums and nullability);
`docs/product-idea-high-level.md` section 7 (Photo pipeline).

Spend: the full run (step 3) spends Gemini credit beyond a single test call. It is
authorised by the human instruction above. If the pilot's cost extrapolated to all
listings exceeds £5, stop and escalate before the full run.

### Explicitly out of scope

- Chip logic that uses flags ("once flags exist" clauses) — that is worker work in B4/B5.
- Any change under `worker/` or `web/`.
- Flag correction endpoint and `corrected_text` writes (B5).
- Training a photo-flag adapter (stretch, per decisions).
- Local image resizing or any new dependency (Pillow, `google-genai`).
- Re-fetching listings from RapidAPI or changing listing fields.
- Per-listing fields from section 7 that come from listing JSON (EPC, tenure, council
  tax): already in `listings`, not from vision.

---

## AMENDMENTS

<!-- Append only. Each entry: date, what changed, who asked. Empty is normal. -->

_None._

---

## RULES IN FORCE

| Rule | Source | Applies to |
| ---- | ------ | ---------- |
| Commits only via `safe-commit.sh`, title only, no attribution | `.claude/CLAUDE.md` | commits |
| No scope creep: touch only declared files | `.claude/CLAUDE.md` prohibition 1 | code, docs |
| No new dependencies; dataset scripts are stdlib only | `.claude/CLAUDE.md` prohibition 2; `dataset/requirements.txt` | code |
| Never weaken a test | `.claude/CLAUDE.md` prohibition 3 | tests |
| The ladder: reuse before writing (e.g. `worker/src/mubit.py` request/response helpers) | `.claude/CLAUDE.md` | code |
| Tradeoffs and spotted problems logged in this file | `.claude/CLAUDE.md` prohibitions 5, 7 | progress file |
| Only step-reviewer ticks boxes | `.claude/CLAUDE.md` prohibition 6 | progress file |
| Evidence durable in `evidence/photo-flags/`, metadata only, no raw response bodies | `.claude/CLAUDE.md`; `docs/decisions.md` Evidence | evidence |
| All LLM calls through Mubit, only the Mubit key sent, record `x-middleware-request-id` | `docs/decisions.md` Mubit; `mubit-gateway` skill | code |
| Secrets never committed (`.env` gitignored) | `docs/decisions.md` Secrets | code, commits |
| Flag rows match the contract's fields and enums | `docs/api-contract.md` | generated data, schema |
| Run Python that reads downloaded files with `python3 -I` | session environment rule | commands |
| Plain British English, banned word list | `.claude/CLAUDE.md` | docs, comments |

---

## PLAN

### Step 1 — Download images and manifest

**Goal**: Download every photo and floorplan in the dataset once, resumable, with a
committed manifest.

**Files in scope**: `dataset/scripts/fetch_images.py` (new),
`dataset/tests/test_fetch_images.py` (new), `dataset/.gitignore` (add `photos/`),
`dataset/images-manifest.csv` (new, generated), `dataset/README.md` (one short usage
section), `evidence/photo-flags/step-1.md` (new).

**Done when**:
- The script reads image URLs (kinds `photo` and `floorplan`) from
  `dataset/listings.sqlite`, downloads with stdlib `urllib` and a thread pool of about
  8, writes to `dataset/photos/<listing_id>/<kind>-<position>.<ext>`, skips files that
  already exist, and never writes outside `dataset/photos/`.
- Failures (HTTP error, timeout, non-image content type) are listed, not fatal.
- The manifest has one row per image: listing_id, kind, position, url, path, sha256,
  bytes, status.
- A real run over all listings has finished; a second run downloads nothing new.
- Unit tests cover skip-if-exists and failure handling without network.
- `dataset/photos/` is gitignored and no image is staged.

**Evidence location**: `evidence/photo-flags/step-1.md` (run counts, failures, total
bytes, second-run result, test output).

- [x] Implemented — dataset/scripts/fetch_images.py; reviewer re-run: 6841 skipped, 0 downloaded, manifest byte-identical (2026-10-25)
- [x] Tested — evidence: unittest discover in dataset/, 129 tests OK, exit 0; 6 new in test_fetch_images.py (2026-10-25)
- [x] Best practices met — evidence: id/path validation, atomic .part rename, size cap, per-image failures non-fatal, stdlib only (2026-10-25)
- [x] Matches locked requirements — evidence: manifest 6841 rows all ok (6169 photo, 672 floorplan), all files exist; photos/ gitignored, no tracked images; retries accepted as second run downloads nothing (2026-10-25)
- [x] No scope drift — evidence: diff limited to declared step-1 files (2026-10-25)

### Step 2 — Flag script, test call and pilot

**Goal**: A script that sends one listing's images to Gemini Flash-Lite through Mubit
and writes contract-shaped flag rows, proven by one test call and a 10-listing pilot.

**Files in scope**: `dataset/scripts/flag_images.py` (new),
`dataset/tests/test_flag_images.py` (new), `dataset/photo_flags.jsonl` (new, generated),
`dataset/README.md` (usage section), `evidence/photo-flags/step-2.md` (new).

**Done when**:
- Request building and response parsing reuse `build_request` / `parse_response` from
  `worker/src/mubit.py` (imported, not copied) and send only `MUBIT_API_KEY`, read from
  the environment or `.env`.
- One request per listing: all its downloaded photos and floorplans, each labelled with
  its index; media resolution set low or medium; a JSON response schema; thinking set
  explicitly where the model supports it.
- Output rows match `docs/api-contract.md` exactly: `flag_id`, `listing_id`, `scope`,
  `field`, `value`, `observation`, `source_photo` (the image URL), `confidence`,
  `uncertainty`, `room`, `corrected_text` (null). Photo scope fields `room`, `light`,
  `size_tricks`, `defects`, `missing`; listing scope `floorplan_notes`, `sqm_estimate`
  from floorplans. Enums validated; a row that breaks one is rejected and logged.
- Photos the model marks `skip` (agent logos, duplicates) produce no flags and are
  recorded as skipped in the output, so the build can drop them.
- Each listing's result records the `x-middleware-request-id` and token usage.
- Resumable: listings already in the output are skipped. Failed listings are retried on
  the next run, not written as empty.
- Unit tests cover response parsing, enum rejection, skip handling and resume, with no
  network.
- One test call succeeded (model ID confirmed served), then a pilot of 10 listings ran;
  their flags were read by eye and judged plausible in the evidence; cost per listing
  measured and extrapolated to 635 listings.

**Evidence location**: `evidence/photo-flags/step-2.md` (test call request ID and model
version, pilot request IDs, token counts, cost extrapolation, a short sample of flags
with what the photo shows, test output).

- [x] Implemented — dataset/scripts/flag_images.py; 400-with-GIF resend, uncertainty required, prompt asks for minor defects; photo_flags.jsonl 30 listing_status lines match evidence token total 187,613 (2026-10-25)
- [x] Tested — evidence: unittest discover in dataset/, 151 tests OK, exit 0; 22 in test_flag_images.py incl. GIF mimeType, 400->200, 400 no GIF, 400 twice, uncertainty required (2026-10-25)
- [x] Best practices met — evidence: stdlib only, key via env/.env (ignored), enum validation, failed listings write nothing, process-refs check exit 0 (2026-10-25)
- [x] Matches locked requirements — evidence: build_request/parse_response imported from worker/src/mubit.py; per-listing request, schema, thinking minimal, medium resolution; pilot of 10 with request IDs, cost extrapolation and eye checks in evidence/photo-flags/step-2.md (2026-10-25)
- [x] No scope drift — evidence: diff limited to step 2 files plus progress file (2026-10-25)

**Redo 1 (2026-10-25, arbiter FIX_NOW after review FAIL 1 of 3)**: (A) evidence
passes the process-reference check, plus a GIF mimeType test; (B1) a 400 with a GIF in
the request resends once without the GIFs, recording them as `rejected_by_model`;
live run of the 20 GIF listings; (B3) `uncertainty` required in the schema and the
system instruction asks for minor defects, real uncertainty and low confidence when
ambiguous; pilot re-run. Files: Step 2's files in scope.

### Step 3 — Full run

**Goal**: Flag every listing.

**Files in scope**: `dataset/photo_flags.jsonl` (generated),
`evidence/photo-flags/step-3.md` (new). No code changes; if the script needs a fix,
that is a redo of step 2.

**Done when**:
- Step 2's extrapolated cost was £5 or less (otherwise escalated, not run).
- The script ran over all listings in the background; a rerun of failures leaves at
  most 2% of listings without flags, each listed with its error.
- Counts recorded: listings flagged, photos flagged, photos skipped, floorplans read,
  flags by field, request ID range, total tokens, measured cost.

**Evidence location**: `evidence/photo-flags/step-3.md`.

- [x] Implemented — 635/635 listings have one listing_status line (ids equal listings.id in listings.sqlite), 0 without flags, 14,684 flag rows, 635 distinct request IDs (2026-10-25)
- [x] Tested — evidence: reviewer script over photo_flags.jsonl: exact 11 keys, enums, room set/null, sqm numeric, flag_id unique, 0 violations; token totals 3,970,404/1,378,774 and counts match step-3.md (2026-10-25)
- [x] Best practices met — evidence: no code changed, no response bodies or key in evidence, process-refs check exit 0, cost est USD 0.95-4.64 (GBP 0.73-3.57) under GBP 5 cap (2026-10-25)
- [x] Matches locked requirements — evidence: all counts in evidence/photo-flags/step-3.md reproduced from the file; 0 failed listings (limit 2%); cost under cap on stated assumptions (2026-10-25)
- [x] No scope drift — evidence: diff vs HEAD touches only progress file and dataset/photo_flags.jsonl, plus untracked evidence/photo-flags/step-3.md (2026-10-25)

### Step 4 — Flags into D1 build

**Goal**: `build_d1.py` loads `photo_flags.jsonl` into a `photo_flags` table in
`listings.sqlite` and `seed.sql`, and drops skipped photos from `listing_media`.

**Files in scope**: `dataset/d1/schema.sql`, `dataset/scripts/build_d1.py`,
`dataset/tests/test_build_d1.py`, `dataset/d1/seed.sql` (generated),
`dataset/listings.sqlite` (generated), `dataset/reports/d1-build-report.txt`
(generated), `dataset/README.md` (schema notes), `docs/api-contract.md` (only the
sentence saying no flag table exists yet), `evidence/photo-flags/step-4.md` (new).

**Done when**:
- `schema.sql` adds `photo_flags` with the contract's columns, CHECK constraints for
  every enum (`scope`, `field` per scope, `light` value, `confidence`, `room` set on
  photo scope and null on listing scope) and a foreign key to `listings`. Additive only:
  no existing table or column changes.
- Skipped photos are removed from `listing_media`, and the remaining photo positions are
  renumbered 0-based without gaps.
- The build passes its self-check (schema then seed into an empty database) and the
  report shows flag counts.
- `worker/scripts/seed.sh` loads the new seed into local D1 without error.
- Existing build tests still pass; new tests cover the flags table and skip handling.

**Evidence location**: `evidence/photo-flags/step-4.md` (build report extract, seed.sh
output, test output).

- [x] Implemented — schema.sql photo_flags additive, build_d1.py read_flags/drop_skipped; listings.sqlite 14,684 flags, media 6,715, positions gapless, seed.sh exit 0 and local D1 count 14684 (2026-10-25)
- [x] Tested — evidence: unittest discover in dataset/, 158 tests OK, exit 0; 7 new FlagTests, no existing test altered (2026-10-25)
- [x] Best practices met — evidence: CHECKs enforce enums, FK, build aborts on missing file or orphan flag, sqm typeof integer 76/real 550, others text, process-refs exit 0 (2026-10-25)
- [x] Matches locked requirements — evidence: contract columns/enums/room nullability match schema; seed self-check PASS; arbiter sqm_estimate FIX_NOW met (typeof test) (2026-10-25)
- [x] No scope drift — evidence: diff limited to declared step-4 files; api-contract.md changes one sentence only (2026-10-25)

---

## TRADEOFFS

<!-- Format: date | step | what was traded away | why | what it would take to fix. -->

- 2026-10-25 | all | Downloaded images live only in this worktree's gitignored
  `dataset/photos/`, not shared with the main checkout. | The images are only needed
  for the flag run; after it, flags carry the source URL. | Copy or symlink the folder
  if a later re-run happens from another checkout. — accepted by arbiter 2026-10-25: steps 2 and 3 run in this worktree, and the manifest (URL, sha256) lets any other checkout re-fetch or verify a copy.

- 2026-10-25 | 1 | The downloader checks the content type starts with `image/` but
  does not check magic bytes, and a failed image is only retried by re-running the
  script. | The CDN returned real images throughout; magic bytes were checked once over
  the whole set. | Sniff magic bytes in the script and retry with backoff per image. — accepted by arbiter 2026-10-25: the dump is frozen, all 6,841 rows are `ok` and were sniffed once, and a re-run is the retry; adding it now changes no output and blocks nothing.

- 2026-10-25 | 2 | GIF floorplans (20) are sent as `image/gif` although Google's
  documented types exclude GIF. | One live GIF call returned 200 and read the plan (area
  right, one bedroom-count error), and leaving GIFs out would drop those listings' floorplan
  flags. | Convert the 20 GIFs to PNG (needs Pillow or similar, out of scope) or check all 20
  outputs by eye after the full run. — accepted by arbiter 2026-10-25: Redo 1 added a resend-without-GIF fallback on HTTP 400 (tested with a fake sender); all 20 GIF listings returned 200 live and their floorplan outputs were checked by eye, so no listing loses flags either way.

- 2026-10-25 | 2 | Cost is extrapolated from assumed prices, not the model's published
  price. | The model is newer than the implementer's knowledge and no price page was read.
  Estimate GBP 0.7 to 3.3 for 635 listings, under the GBP 5 limit on both bases. | Read the
  Mubit console cost page before and after the full run. — accepted by arbiter 2026-10-25: tokens are measured (about 3.8 M in, 1.3 M out for 635 listings); the GBP 5 cap holds up to about 2 to 3 times Gemini 2.5 Flash rates, well above any Flash-Lite-class price, and step 3 records actual tokens and console cost.

- 2026-10-25 | 2 | Pilot flags look optimistic: after the prompt change, the 10 pilot listings
  still have no `defects` rows, light `poor` once and never `none`, `uncertainty` set on 12 of
  223 rows, confidence never low (10 listings, 93 photos). The 20 GIF listings gave 16 defect
  rows, 1 low-confidence row and 38 of 463 rows with uncertainty. | The
  prompt and schema were kept as asked; tuning them was not part of the step and the sample is
  small. | Re-prompt for defects and uncertainty, or accept that a missing defect flag means
  none seen, before the full run. — accepted by arbiter 2026-10-25: the redo's prompt change was made and the model does report defects when they exist (16 rows on the GIF set, eye-checked correct, one with overstated confidence); the pilot 10 may simply be clean. Flags are soft curator input, a missing defect flag reads as "none seen", and users can correct flags (B5). A second prompt redo would re-spend on the pilot with no evidence it would help.

- 2026-10-25 | 2 | A request has a 300 s timeout and no retry inside a run. One pilot
  listing hung once and succeeded on the next run in 10 s. | Failed listings are retried by
  re-running, as the step specifies. | Add a shorter timeout with one automatic retry. — accepted by arbiter 2026-10-25: step 3's done-when allows a rerun of failures, which is the retry; one hang in 10 listings costs minutes, not flags.

- 2026-10-25 | 3 | Two images in rm-90723729 (one photo, one floorplan) came back
  unanswered by the model and have no flags; the listing itself has flags. Cost is an estimate
  (assumed prices on measured tokens), the Mubit console cost was not read. | Re-running would
  not resume the listing (it has a status line), and the loss is two images of 6,841. No console
  access from this session. | Delete that listing's lines from the output and rerun; read the
  console cost page. — accepted by arbiter 2026-10-25: 2 of 6,841 images (one listing's floorplan and one photo) is a 0.03% gap; that listing keeps 17 photo flags and simply lacks `sqm_estimate`/`floorplan_notes`, as 8 other listings already do, and flags are soft curator input. A rerun means hand-editing the output and a fresh Step 3 review for one listing. Cost: tokens are measured (3.97 M in, 1.38 M out), the estimate sits under the GBP 5 cap on stated assumptions, and console access is not available here; the human can read the console page when back, and decisions.md already requires a real cost check before the persona batch.

- 2026-10-25 | 4 | In 8 listings the model both skipped and flagged the same URL, which the
  listing lists twice. The build keeps the first copy of such a URL and drops the repeat, instead
  of dropping the image and its flags. | The contract says skipped images have no flags, but
  dropping would lose 19 flags for images that are real; the skip was about the repeat. The flag
  file is not editable in this step. | Re-run those 8 listings, or have the flag script not
  list a flagged URL as skipped. — accepted by arbiter 2026-10-25: the result matches the contract's intent: the duplicate is gone from `listing_media` and the real image appears once with its flags, so no skipped image carries flags. Dropping it would lose 19 good flags, and re-running 8 listings would cost money and a Step 3 re-review for no gain. Covered by a build test.

---

## SPOTTED, NOT FIXED

- `dataset/photo_flags.jsonl` | 8 listings repeat a URL; the model skipped one copy and flagged the other (see Step 4 tradeoff). | low — accepted by arbiter 2026-10-25: same as the Step 4 tradeoff; the build keeps one copy with its flags, tested.

- `dataset/photos/*/floorplan-0.gif` (20 files) | Floorplans are GIF; Gemini's
  documented image types are PNG, JPEG, WebP, HEIC, HEIF. Step 2 must skip or handle
  them (no Pillow) | medium — accepted by arbiter 2026-10-25: handled in Step 2 Redo 1 (sent as image/gif, resend without GIFs on 400); 20/20 accepted live.

- `dataset/photo_flags.jsonl` | `sqm_estimate` values are numbers (626 rows); every other `value` is text. The contract already allows this ("a string, or a number for `sqm_estimate`"). Step 4's schema must keep the type: a `value TEXT` column would coerce 58 to '58', and `NUMERIC` would turn numeric-looking text into numbers. | low — arbiter 2026-10-25: FIX_NOW inside Step 4 (in its files, no amendment): declare `value` with no type affinity (or keep numbers in a typed way the contract allows), emit `sqm_estimate` unquoted in `seed.sql`, and test that it round-trips as a number while text values stay text. — resolved, confirmed by arbiter 2026-10-25: Step 4 passed review with sqm_estimate stored as typeof integer (76) / real (550) and other values as text, covered by a typeof test.

---

## VERIFICATION

- [x] All step checkboxes ticked with evidence — 20/20 PLAN boxes ticked, each dated 2026-10-25 with evidence; order holds (all same day) (2026-10-25)
- [x] Every evidence path in this file exists — evidence/photo-flags/step-1.md to step-4.md all present (2026-10-25)
- [x] Test suite run — result: dataset `python3 -I -B -m unittest discover -s tests` 158 OK, exit 0; worker pytest against seeded test-mode server (port 8790, fake upstream 8801) 183 passed, exit 0; web `npm test` 178 passed, exit 0 (2026-10-25)
- [ ] Lint run — n/a: no lint command configured in .claude/kit-config.md
- [x] Typecheck run — result: web `npm run typecheck` exit 0 (web untouched by this branch) (2026-10-25)
- [x] Build run — result: web `npm run build` exit 0; `worker/scripts/seed.sh` exit 0; d1-build-report self-check PASS (2026-10-25)
- [x] Diff contains no files outside declared scope — 20 files from merge base 99c1e4d, all in a step's Files in scope or Evidence location, plus this progress file; no tracked file under dataset/photos/; no secrets (only a fake `mbt_abc` in a test) (2026-10-25)
- [x] Tradeoff ledger reviewed — signed by arbiter (full automation): all 8 TRADEOFFS and 3 SPOTTED entries carry an arbiter verdict dated 2026-10-25 (2026-10-25)
- [ ] Human eye test completed — not human-verified (full automation) — smoke check: pass. Local D1 after seed.sh: photo_flags 14,684 rows over 635 listings, listing_media 6,715, sqm_estimate stored as real; sample rows for rm-137220284 read correctly (floorplan 69.6 sqm "stated explicitly on the floor plan", kitchen/living room/bedroom photos with room and light set)
- QA-GATE: PASS 2026-10-25

---

## HANDOVER

**What was built**

Every photo and floorplan for the 635 listings has been downloaded once and described by
Gemini 3.5 Flash-Lite through Mubit. The descriptions are stored as 14,684 flags: for
each photo the room, how much light, things that make it look bigger or smaller, visible
defects and what is missing; for each floorplan layout notes and floor area in square
metres. They are loaded into a new `photo_flags` table in the local D1, ready for the
curator and the chips. Agent logos and duplicate photos were dropped from the listing's
photo list. Nothing in the API serves the flags yet; that is B4/B5.

**What to check yourself**

1. From the repo root run `worker/scripts/seed.sh`. It should finish without an error.
2. In `worker/`, run
   `npx wrangler d1 execute haka --local --command "SELECT COUNT(*) FROM photo_flags"`.
   You should see 14684.
3. Pick a listing and read its flags:
   `npx wrangler d1 execute haka --local --command "SELECT field, room, value, confidence, observation FROM photo_flags WHERE listing_id='rm-137220284'"`.
   Open the same listing's photos (URLs in `source_photo`) in a browser and judge whether
   the room, light and defects match what you see. Do this for two or three listings,
   including one older or tired-looking house.
4. Read `dataset/reports/d1-build-report.txt`. The self-check line at the bottom should say
   PASS, and "skipped images removed" should be photo 120, floorplan 6.
5. From `dataset/`, run `python3 -I -B -m unittest discover -s tests`. Expect 158 tests OK.
6. Open the Mubit console and read the actual spend for 635 calls on
   `gemini-3.5-flash-lite`. The progress file only has an estimate (GBP 0.73 to 3.57).

**Tools that will help**

- The wrangler D1 command above, or any SQLite client on `dataset/listings.sqlite`
  (same data). Look at `photo_flags` grouped by `field` and `confidence`.
- A browser, to open `source_photo` URLs next to their flags.
- The Mubit console: request IDs are in `dataset/photo_flags.jsonl` status lines
  (`"record_type": "listing_status"`), one `mreq_…` per listing. Use them to find calls
  and check cost.

**What is not done**

- The API does not return flags yet. The listing detail and card endpoints (B4/B5) must
  read `photo_flags`. Chip filtering from flags is not built.
- Flag corrections (`corrected_text`) have a column but no endpoint (B5).
- Cost is an estimate on measured tokens and assumed prices. The console was not read.
- Two images in rm-90723729 (one photo, one floorplan) were not answered and have no
  flags. 3 listings have no floorplan flags at all; some lack `sqm_estimate`.
- In 8 listings a URL appears twice; the build keeps the first copy with its flags.
- 20 floorplans are GIFs, which Google does not document as supported. All 20 were
  accepted live; if the model starts refusing GIFs, the script resends without them.
- Images live only in this worktree's gitignored `dataset/photos/`. The manifest lets
  any checkout re-fetch them.
- The downloader does not check magic bytes or retry within a run.
- Lint is not configured for this repo.

**What could bite you**

1. The flags are optimistic. Light is "bright" on 4,254 of 6,045 photos, "ok" on 1,763,
   "poor" on 28 and never "none". 476 of 635 listings have no defect flag. 13,056 of
   14,684 flags are high confidence. Estate-agent photos are staged, so some of this is
   real, but light barely tells listings apart. A persona rule such as
   `prefers: light=bright` will score almost every listing as good and teach the curator
   little. Check this before writing the persona rules block in B6.
2. Photo positions in `listing_media` were renumbered after removing skipped images.
   `flag_id` and the files in `dataset/photos/` still use the old positions. Join flags
   to photos by URL (`source_photo` = `listing_media.url`), never by position.
3. `seed.sql` is now 10 MB in 23,923 statements. It loads locally, but `seed.sh` deletes
   the local D1 state first, so re-seeding wipes all users, swipes and prefs.
