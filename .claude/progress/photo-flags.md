# Feature: Photo and floorplan textualisation

- **Slug**: photo-flags
- **Started**: 2026-10-25
- **Branch**: feat/photo-flags
- **BASE_SHA**: 8d9ed8d3a929dfe540ea221d9e2d8d52247f6e97
- **Status**: in progress

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

- [ ] Implemented
- [ ] Tested — evidence: (date)
- [ ] Best practices met — evidence: (date)
- [ ] Matches locked requirements — evidence: (date)
- [ ] No scope drift — evidence: (date)

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

- [ ] Implemented
- [ ] Tested — evidence: (date)
- [ ] Best practices met — evidence: (date)
- [ ] Matches locked requirements — evidence: (date)
- [ ] No scope drift — evidence: (date)

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

- [ ] Implemented
- [ ] Tested — evidence: (date)
- [ ] Best practices met — evidence: (date)
- [ ] Matches locked requirements — evidence: (date)
- [ ] No scope drift — evidence: (date)

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

---

## SPOTTED, NOT FIXED

- `dataset/photos/*/floorplan-0.gif` (20 files) | Floorplans are GIF; Gemini's
  documented image types are PNG, JPEG, WebP, HEIC, HEIF. Step 2 must skip or handle
  them (no Pillow) | medium

---

## VERIFICATION

- [ ] All step checkboxes ticked with evidence
- [ ] Every evidence path in this file exists
- [ ] Test suite run — result:
- [ ] Lint run — result:
- [ ] Typecheck run — result:
- [ ] Build run — result:
- [ ] Diff contains no files outside declared scope
- [ ] Tradeoff ledger reviewed and signed off by human
- [ ] Human eye test completed

---

## HANDOVER

