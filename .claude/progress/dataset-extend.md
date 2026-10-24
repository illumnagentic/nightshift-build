# Feature: Extend the dataset to 500+ and split train/eval

- **Slug**: dataset-extend
- **Started**: 2026-10-24
- **Branch**: feat/dataset-extend
- **BASE_SHA**: 7597e7f
- **Status**: complete 2026-10-24 (eye test not done by human)

---

## REQUIREMENTS (LOCKED)

Human, in session, 2026-10-24:

> "let's extend the dataset so we have the required numbers. There's a RAPID_API_KEY in the .env for rapidapi's api. gateway is rapidapi.com, header: uk-real-estate-rightmove.p.rapidapi.com, and it needs an identifier which is String. - identifier get from auto-complete endpoint, data[index]->locationIdentifier"

> "I have a limit of 600 requests"

> "also need to make sure there are no duplicates"

Answers to kickoff questions (2026-10-24):

- Existing listings: "Keep, append new (Recommended)" — keep all 398, add about 150 new RapidAPI listings to reach 500+ with margin.
- Areas: "Mixed, favour commuter belt (Recommended)" — a few London boroughs not yet covered plus more commuter towns, so non-London personas get a real deck.
- Train/eval split: "Yes (Recommended)" — a split column on listings, about 25% held out, seeded, assigned once all listings are in.
- MCP: "No, use the script (Recommended)" — fetch with `dataset/scripts/fetch_rapidapi.py`, which logs and caps calls.
- Plan, rules in force and out-of-scope list: "Approve (Recommended)".
- Live API calls: "Yes, cap 300 (Recommended)".
- Branch: "feat/dataset-extend (Recommended)".

The required numbers, from `docs/decisions.md` (Data, Training vs evaluation split):

> "Target **500+**, not 200–400: hard filters, onboarding and the held-out set all eat into the pool."

> "About 25% of listings held out, duplicates removed across the split."

### Source

This session's conversation, quoted above; `docs/decisions.md`.

### Explicitly out of scope

- The RapidAPI MCP server (`npx mcp-remote`). Human said no.
- Re-fetching or replacing the existing 398 listings. Scraping rightmove.co.uk directly.
- Rebuilding from `raw/rightmove` (not on this machine).
- Persona train/eval split (B6). Photo flags (B2, later). TfL commute.
- Changing the demo EPC pass, other than re-running it over the larger set.
- Loading into a real D1 database; wrangler.
- New Python packages (stdlib only).
- Editing `docs/decisions.md` or `docs/plan.md`.
- Committing any API key, or any raw response body. `raw/` stays gitignored.

---

## AMENDMENTS

- 2026-10-24, human: "Same-agent waiver (Recommended)" — in step 4, the duplicate guard's coordinates + bedrooms + price check skips pairs listed by the same agent (matching the normalise dedupe rule), because two Taylor Wimpey new-build pairs in the existing 398 are distinct units. A shared id or a shared photo URL still aborts the build.
- 2026-10-24, human: "Named build-only columns (Recommended)" — `dataset/tests/test_sanitise.py` is added to step 4's files in scope. Its schema-columns test keeps an exact match, against the schema's columns minus an explicit `BUILD_ONLY = {'split'}`, and a new assertion checks that build_d1 writes every BUILD_ONLY column.
- 2026-10-24, human: "Top up cheaper listings (Recommended)" — the 24 Oct RapidAPI page-1 searches came back highest price first, so the 161 new listings are each area's top-priced slice (52 at exactly £1.2m). Top up with the remaining calls: about one search per area for cheaper or newest listings (target band £250k–£700k), about 80 detail calls, total calls in this feature still at most 300 and within the provider's remaining count. Steps 1 (search options), 2 (top-up fetch), 3 (append re-run), 4 (rebuild) are redone and step 5 is fixed, reviewed in order.
- 2026-10-24, human: "Yes, in this feature (Recommended)" — make the train/eval split stable: each coordinate group's side is decided from a hash of the split seed and the group's coordinates, so adding listings never moves an existing listing. The share bounds in step 4 stay (25% ± 2 overall, ± 5 London and outside); if the fixed seed misses them, stop and report rather than search for a seed. Step 4 is redone (redo 2) and reviewed before step 5.
- 2026-10-24, human: "accept all, make sure what could bite is noted, do commit pr and merge" — step 5 adds a "What could bite" section to `dataset/README.md` listing the four handover risks (unbalanced hash split near its bound; thin budget decks below £450k, check pool sizes per persona; `--append` overwrites the normalise report; photo URLs repeated within single listings).

---

## RULES IN FORCE

| Rule | Source | Applies to |
| ---- | ------ | ---------- |
| Commits only via `.claude/scripts/safe-commit.sh`, title only, no signature, human approves | `.claude/CLAUDE.md` | commits |
| Commit title `type(scope): message`; scopes in use: worker, web, db, prep, kit | `.claude/CLAUDE.md`, `.claude/kit-config.md` | commits |
| No scope creep: touch only the step's declared files | `.claude/CLAUDE.md` #1 | code, docs |
| No new dependencies; stdlib only | `.claude/CLAUDE.md` #2, `dataset/requirements.txt` | code |
| Never weaken a test to pass | `.claude/CLAUDE.md` #3 | tests |
| No speculative generalisation; walk the ladder | `.claude/CLAUDE.md` #4 | code |
| Tradeoffs logged in TRADEOFFS when made | `.claude/CLAUDE.md` #5 | progress file |
| Implementer never ticks its own boxes; only step-reviewer, with evidence and date | `.claude/CLAUDE.md` #6 | progress file |
| Out-of-scope problems go in SPOTTED, NOT FIXED | `.claude/CLAUDE.md` #7 | progress file |
| Plain British English, no banned marketing words | `.claude/CLAUDE.md` | docs, comments, README |
| Evidence stored durably in `evidence/`, metadata only, never raw response bodies | `.claude/CLAUDE.md`, `docs/decisions.md` (Evidence) | evidence |
| API keys never printed, logged or committed; `.env` stays gitignored | human, 2026-10-23 | code, commands, commits |
| Total RapidAPI calls in this feature at most 300 (half of the human's 600), counted from the call log and cross-checked against the provider's remaining header | human: "I have a limit of 600 requests" | fetch runs |
| Never invent a value: unknown is NULL — except `epc_current` / `epc_potential` in the D1 build (demo EPC pass) | human brief 2026-10-23; override 2026-10-24 | generated data |
| Selection rules unchanged: for sale only, no auctions, shared ownership or retirement; £250k–£1.2m; at least 6 photos and 1 floorplan; tenure known; lat/lon present | `dataset/README.md`, `rm_common.py` | generated data |
| No duplicate homes, within the new data, against the existing 398, or across the train/eval split | human, 2026-10-24; `docs/decisions.md` | generated data |
| Python reading downloaded files runs with `-I`; scripts never live in `raw/` | session environment rule | code, commands |

---

## PLAN

All paths relative to the repository root.

### Step 1 — Fetch script: auto-complete, key name, skip known ids

**Goal**: `fetch_rapidapi.py` can resolve a place name to a `locationIdentifier`, reads the human's key, and never spends a detail call on a listing already in `listings.jsonl`.

**Files in scope**: `dataset/scripts/fetch_rapidapi.py`, `dataset/.env.example`, `evidence/dataset-extend/probe.md` (new), `dataset/tests/test_fetch_rapidapi.py` (added in redo 2)

**Done when**: a new `autocomplete --query <place>` subcommand calls the auto-complete endpoint, saves the response under `raw/rapidapi/autocomplete/`, and prints each `data[i].locationIdentifier` with its display name. The key is read from `RAPID_API_KEY` (environment, `dataset/.env`, or the repository-root `.env`) as well as the existing names, and its value is never printed. `details` skips any id already present in `dataset/listings.jsonl`. The endpoint path and response shape are confirmed with at most 2 live calls, and the call metadata (endpoint, status, provider's remaining count, no body, no key) is written to `evidence/dataset-extend/probe.md`. Existing tests pass.

**Evidence location**: the diff; `evidence/dataset-extend/probe.md`.

- [x] Implemented — evidence: autocomplete subcommand, RAPID_API_KEY lookup, known_ids skip in dataset/scripts/fetch_rapidapi.py; diff vs 7597e7f = fetch_rapidapi.py + .env.example only (2026-10-24)
- [x] Tested — evidence: 75 existing tests OK; 1 live call 200, 297 remaining, evidence/dataset-extend/probe.md; missing unit test logged in TRADEOFFS (2026-10-24)
- [x] Best practices met — evidence: key never printed, env/.env reads only, tradeoffs logged in TRADEOFFS (2026-10-24)
- [x] Matches locked requirements — evidence: autocomplete via /auto-complete?location=, locationIdentifier printed, raw saved under raw/rapidapi/autocomplete/, <=2 live calls (2026-10-24)
- [x] No scope drift — evidence: git diff 7597e7f --stat shows only declared files; evidence/ new; raw/ untracked (2026-10-24)
- Redo 2 re-reviewed 2026-10-24 (all five boxes): price_band rejects outside rm.MIN_PRICE..MAX_PRICE or inverted (test_out_of_range_rejected, test_bad_band_rejected); default search file names identical old vs new for all 10 cached searches (verified against 7597e7f) and pinned by test_search_path_unchanged_for_defaults; details band filter runs inside search_ids before any detail call (test_max_price_skips_dearer_cards, test_min_price_skips_cheaper_cards, test_band_edges_inclusive); 121 tests OK exit 0; _calls.log still 190 lines; check-process-refs exit 0; no key printed (2026-10-24)

Redo (2026-10-24): review failed on unlogged tradeoffs; logging them, no code change.
Redo 2 (2026-10-24): amendment "Top up cheaper listings"; `search` gains options to set sort order and/or a price ceiling.

### Step 2 — Fetch the new listings

**Goal**: Download enough new for-sale listings, commuter belt favoured, to reach 500+ after filters and dedupe.

**Files in scope**: `evidence/dataset-extend/fetch.md` (new). Files written under `dataset/raw/rapidapi/` (gitignored, not committed).

**Done when**: areas used: commuter towns Brighton, Cambridge, Croydon, Kingston upon Thames, Oxford, Chelmsford, Sevenoaks, and London boroughs Greenwich, Haringey, Hammersmith and Fulham (an area can be swapped for a nearby one if auto-complete finds no match; any swap is recorded). Searches use the existing price and type filters. Detail calls stop once about 170 new candidates have passed the card rules. Total calls in steps 1 and 2 together are at most 300. `evidence/dataset-extend/fetch.md` lists, per area: identifier, search calls, detail calls, candidates; plus the total calls and the provider's last remaining count. No response bodies and no key in the evidence.

**Evidence location**: `evidence/dataset-extend/fetch.md`.

- [x] Implemented — evidence: _calls.log 190 calls (10 autocomplete, 10 search, 170 detail), 169 distinct detail files, per-area split 20x7 + 10x3, evidence/dataset-extend/fetch.md (2026-10-24)
- [x] Tested — evidence: log re-counted: 190 <= 300, provider remaining 108; 0 of 169 detail ids in listings.jsonl source_ids; search params price 250000-1200000 plus retirement/schemes exclusions (2026-10-24)
- [x] Best practices met — evidence: key value absent from log, fetch.md, probe.md, progress file (grep count 0); fetch.md metadata only; tradeoffs written (2026-10-24)
- [x] Matches locked requirements — evidence: areas match Step 2 list, no swaps, commuter belt 140 vs boroughs 30 details; ~170 candidates met by 169 saved; no duplicate spend (2026-10-24)
- [x] No scope drift — evidence: git status: only evidence/ new; raw/ ignored; diff vs 7597e7f unchanged (2 files, +35/-11) (2026-10-24)

- Redo 2 re-reviewed 2026-10-24 (all five boxes): _calls.log 292 lines (top-up lines 191-292: 22 search + 80 detail, all 200), last remaining 6; 80 distinct detail ids, 0 in listings.jsonl source_ids, 0 repeats of earlier fetches; every id's card price in search files lies 265000-700000 (median 450000, 40 at 450000, 23 at 700000), none outside band; 63 commuter-belt vs 17 borough details; search params 10x250-450k, 10x450-700k, 2 sort probes; fetch.md matches log, key value absent from evidence, progress file and log (grep 0 files); fetch_rapidapi.py unchanged this redo; check-process-refs exit 0; bunching and 22-search deviation logged in TRADEOFFS (2026-10-24)

Redo 2 (2026-10-24): amendment "Top up cheaper listings"; extra searches and details for the £250k–£700k band.

### Step 3 — Append new listings to listings.jsonl, with dedupe

**Goal**: `normalise.py` adds the new RapidAPI records to the existing 398 without needing `raw/rightmove`, with no duplicates.

**Files in scope**: `dataset/scripts/normalise.py`, `dataset/listings.jsonl`, `dataset/listings.csv`, `dataset/reports/normalise-report.txt`, `dataset/tests/test_normalise_append.py` (new)

**Done when**: when `raw/rightmove` is absent, `normalise.py` refuses to overwrite `listings.jsonl` with fewer listings unless run in an explicit append mode. Append mode loads the existing `listings.jsonl`, builds the new records from `raw/rapidapi`, and dedupes new against existing and new against new with the existing rules (Rightmove id, delivery point id where present, same coordinates to 4 dp plus bedrooms plus price). It also treats two listings sharing any photo URL as one home. On a clash the existing record is kept. Sanitise runs on the new records. The 398 existing records are byte-identical in the output. The output has 500 or more listings, with the count per area and the duplicates dropped, by rule, in the report. Tests cover: existing records kept unchanged, each dedupe rule, and refusing to shrink.

**Evidence location**: the diff; `dataset/reports/normalise-report.txt`; `evidence/dataset-extend/append-runs.md` (added in redo 1).

- [x] Implemented — evidence: --append, check_not_shrinking, load_existing, drop_clashes in dataset/scripts/normalise.py; listings.jsonl 559 lines, first 398 byte-identical to 7597e7f (cmp), csv 559 rows (2026-10-24)
- [x] Tested — evidence: unittest discover 91 tests OK exit 0; test_normalise_append.py covers each dedupe rule, shrink refusal, unchanged existing; copy run without --append exits 1 and leaves file intact; --append rerun on copy is cmp-identical (2026-10-24)
- [x] Best practices met — evidence: load_existing round-trip check, shrink guard exit 1, stdlib only, report tradeoff logged in TRADEOFFS; check-process-refs exit 0 (2026-10-24)
- [x] Matches locked requirements — evidence: 559>=500, 0 shared photo URLs, 559 unique ids, only 2 geo+beds+price pairs (same agent Taylor Wimpey, both in original 398), new 161 all meet price/6 photos/floorplan/tenure/lat-lon rules (2026-10-24)
- [x] No scope drift — evidence: git diff 7597e7f --stat lists only declared step 3 files plus step 1 fetch_rapidapi.py/.env.example; sqlite and seed.sql unchanged (2026-10-24)

Redo 1 (2026-10-24): re-run `--append` over the top-up; no code change expected.

Redo 1 re-reviewed 2026-10-24 (all five boxes): listings.jsonl 635 lines, first 559 cmp-identical to saved copy and first 398 to 7597e7f; 635 unique ids; all 635 insert into in-memory sqlite from d1/schema.sql with no CHECK violation (price_qualifier 'From' nulled by sanitise, studio rm-94490961 bedrooms 0 allowed); csv 635 rows; append-runs.md counts match old and current reports; unittest 121 OK exit 0; check-process-refs exit 0; sqlite/seed.sql mtimes predate the run (2026-10-24)

### Step 4 — Train/eval split and duplicate guard in the D1 build

**Goal**: Every listing in the D1 build carries `split` ('train' or 'eval'), about 25% eval, seeded, and the build fails on any duplicate.

**Files in scope**: `dataset/d1/schema.sql`, `dataset/scripts/build_d1.py`, `dataset/tests/test_build_d1.py`, `dataset/tests/test_sanitise.py` (added by amendment 2026-10-24), `dataset/d1/seed.sql`, `dataset/listings.sqlite`, `dataset/reports/d1-build-report.txt` (all regenerated)

**Done when**: `listings.split` is `TEXT NOT NULL CHECK (split IN ('train','eval'))`. The split is drawn with a fixed seed. Listings at the same coordinates (4 dp) land on the same side, so near-identical new-build units never straddle it. The eval share is 25% ± 2 points overall and within ± 5 points in London versus outside London. The build aborts if two listings share an id, a photo URL, or coordinates plus bedrooms plus price. The report shows split counts overall and per area. The build is byte-identical on a rerun. The existing tests pass, and new tests cover the split share, grouping by coordinates, determinism and the duplicate abort.

**Evidence location**: the diff; `dataset/reports/d1-build-report.txt`.

- [x] Implemented — evidence: split column + CHECK in schema.sql; SPLIT_SEED, assign_split, check_duplicates, split_lines in build_d1.py; report has split per area (2026-10-24)
- [x] Tested — evidence: unittest discover 105 OK exit 0; rebuild checksums match (sqlite 692ab236..., seed 789cc29c...); SplitTests, DuplicateGuardTests, BuildOnlyColumnTests (2026-10-24)
- [x] Best practices met — evidence: guard aborts exit 1 with ids; stdlib only; own RNG so EPC draws unaffected; tradeoffs logged; check-process-refs exit 0 (2026-10-24)
- [x] Matches locked requirements — evidence: sqlite: 559 rows, 0 NULL split, eval 24.9% all / 24.9% London / 24.7% outside, 0 coordinate groups straddling, 0 NULL EPC (2026-10-24)
- [x] No scope drift — evidence: step 4 hunks only in schema.sql, build_d1.py, test_build_d1.py, test_sanitise.py (amended) and regenerated seed/sqlite/report; original exact-match schema test kept with BUILD_ONLY subtraction (2026-10-24)

- Redo 1 re-reviewed 2026-10-24 (all five boxes): scratch rebuild from listings.jsonl reproduces sqlite 4b0c94cc..., seed.sql fa09179c..., report 49e71f25... (exit 0, matches files in repo); sqlite: 635 listings, 6841 media, 1889 stations, 0 NULL split/epc, 0 epc media, 0 potential worse than current, 0 coordinate groups straddling, fk/integrity clean; split 477/158 (24.9%), London 301/100, outside 176/58; build_d1.py, schema.sql, tests mtimes predate the rebuild; 188 of 559 changed side reproduced by building first 559 lines in scratch (139 eval); 121 tests OK exit 0; check-process-refs exit 0 (2026-10-24)

- Redo 2 re-reviewed 2026-10-24 (all five boxes): scratch rebuild exit 0 reproduces sqlite a1701826..., seed.sql 32d8020b..., report byte-identical (cmp 0); hash is hashlib.sha256 of "%d|%r" (SPLIT_SEED 20261025, as logged in the step 4 tradeoff; EVAL_SHARE 0.25), not hash(); split 488/147, 23.15% overall, London 100/401 24.94%, outside 47/234 20.09% (bounds met, margin 0.09); 0 straddling coordinate groups; 0 of 559 change side building first 559 lines; EPC letters identical to epc_before.txt (635 match); no-coordinate listings keyed by id (code only, no direct test); share bounds in SplitTests unchanged; 123 tests OK; check-process-refs exit 0 (2026-10-24)

Redo 1 (2026-10-24): rebuild over the larger set; no code change expected.
Redo 2 (2026-10-24): amendment "stable split"; per-group hash replaces the shuffled fill in build_d1.py.

### Step 5 — README

**Goal**: The dataset README describes the larger set, the append mode, the split and the duplicate guard.

**Files in scope**: `dataset/README.md`

**Done when**: sources, call counts (from `evidence/dataset-extend/fetch.md`), selection, dedupe, coverage, distributions and area tables match the step 3 and step 4 reports. The re-run order includes append mode. A "Train/eval split" section states the seed, grouping rule and counts. No figure is left over from the 398-listing set.

**Evidence location**: the diff.

- [x] Implemented — dataset/README.md rewritten for 635 set, append mode, split (2026-10-24)
- [x] Tested — evidence: unittest discover 123 tests OK exit 0; README counts re-derived from listings.jsonl/sqlite (other 5, NULL 3, 401 London, 234 other, 438/197, 210/193/17, 148 EPC, 1889 stations) (2026-10-24)
- [x] Best practices met — evidence: banned-word grep clean; process-refs exit 0; stated limits flagged in TRADEOFFS (2026-10-24)
- [x] Matches locked requirements — evidence: no 398-set figures left; sections match step 3/4 reports (2026-10-24)
- [x] No scope drift — evidence: only dataset/README.md changed for this step (2026-10-24)
- Amendment re-reviewed 2026-10-24 (all five boxes): "What could bite" section in dataset/README.md checked with python3 -I against listings.jsonl/sqlite and reports: outside London 234, 37 under 450k outside, 114 overall, eval share 47/234 = 20.1%, 8 repeated photo URLs in 7 listings (listing_media, kind photo), 0 across listings; four points match handover; cross-references (Train/eval split, Search order and price skew, Re-running) exist; banned words absent (2026-10-24)

---

## TRADEOFFS

- 2026-10-24 | kickoff | the script's monthly call counter reads `raw/rapidapi/_calls.log`, which is not on this machine, so it cannot see the 28 earlier calls; the cap is enforced from a fresh log plus the provider's remaining header | `raw/` was lost | none; the provider header is the real count. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | kickoff | adding listings re-runs the demo EPC pass, so many existing made-up EPC letters change (known from demo-epc-fill) | accepted by the human there | none. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 1 | no unit test for `autocomplete`, `known_ids` or the known-id skip in `search_ids`; the skip was checked only ad hoc by the reviewer | the script has no test file and step 1 declared none | add `dataset/tests/test_fetch_rapidapi.py` with a mocked Client. Redo 2: `dataset/tests/test_fetch_rapidapi.py` now covers `known_ids` and the known-id skip in `search_ids`; `autocomplete` and `Client.call` are still untested (no mocked Client). — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 1 | `probe` still makes one detail call for the first search id without the known-id or card-rule filter | existing behaviour, `probe` is not used in this feature | apply the same filter in `probe`. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 1 | the key can come from three places (environment, `dataset/.env`, repository-root `.env`), environment first | the human keeps the key in the root `.env`; the old location still works | drop the extra locations if that causes confusion. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 1 | `.env.example` lists three key names (`RAPID_API_KEY`, `RAPIDAPI_KEY`, `RAPIDAPI_KEY_2`) | the old names are still read | remove the old names once unused. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 1 | the provider reported 297 calls remaining after the probe, not ~599; the real monthly quota on this key looks like 300, so the 300 cap in RULES IN FORCE is effectively the whole quota | the human's "600" may cover a second key or another plan; unconfirmed | confirm with the human; step 2 treats the provider's remaining count as the ceiling. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 1 redo 2 | `--sort` is passed to the API as `sort_by` unchecked, and which value gives cheapest-first or newest-first is not known; the first live use has to find it | the accepted values are not documented | confirm one value with a single search call in the redo of step 2 and record it in fetch.md. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 1 redo 2 | a non-default band or sort changes the search params hash, so those searches get new cache files; default searches keep their file names (pinned by a test on `REGION_93965_p1_b8e6e53209.json`) | needed so cached 24 Oct searches are still found | none. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 1 redo 2 | `details --min-price/--max-price` filters on the card price in every saved search file for the identifier, so the old expensive cards are skipped only because of the band, not because they are tagged as old; a top-up without `--max-price` would again pick them | keeps the command simple, no search-file selection option added | pass `--max-price 700000` on every top-up details run. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 1 redo 2 | the band is checked to lie within rm.MIN_PRICE..rm.MAX_PRICE and min <= max, so a band can never widen the selection rules; a single-value override (only `--max-price`) keeps the other limit at the rule's value | human instruction: do not loosen the selection rules | none. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 2 | one search page (25 cards) per area, 20 detail calls per commuter town and 10 per London borough, so 169 details saved; the card rules only check the search card, so photo, floorplan and tenure rules apply later and some of the 169 may drop, leaving fewer than 500 after step 3 | keeps the run at 190 of 300 calls | 108 calls remain; fetch more detail pages or extra search pages if step 3 ends under 500. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 2 | Sevenoaks had one detail call return HTTP 400 (id 94155597) and one Cambridge run died on a connection error; neither listing was retried | a retry would cost a call and the 400 is a permanent answer | retry the id once if the pool is short. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 2 | Croydon, Kingston, Greenwich, Haringey and Hammersmith and Fulham use the London Borough identifier, not the town entry (Kingston also has `REGION^746`, Croydon `REGION^391`) | the borough covers the whole area the persona sees | none. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 3 | final count is 559 (398 existing + 161 new); of 169 detail files, 6 failed the thin rules (no tenure) and 2 were dropped as coordinates + bedrooms + price duplicates (existing or new, not split out) | step 2 fetched what the plan asked for | none; 59 above the 500 target. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 3 | the shared-photo rule has no same-agent exception, so two distinct new-build units from one agent that reuse marketing photos would be merged; it dropped 0 records on this data | the human said any shared photo URL means the same home | add an agent exception if a later dataset shows distinct units dropped. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 3 | the photo rule compares URLs exactly; the same image served at another size or path would not match | Rightmove photo URLs in both sources have the same form (checked on one record each), but not checked across all | normalise the URL to its hash file name before comparing. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 3 | append dedupe is a greedy pass (existing records first, then new by richness), not the union-find `dedupe()` used by a full rebuild, so a chain of links through a dropped record is not followed | simpler and gives the same answer on pairs; the two paths are separate code on purpose, as a full rebuild cannot run here | share one implementation if a full rebuild ever returns. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 3 | existing records have no delivery point id, so the delivery point rule only applies new-vs-new, and RapidAPI records never carry one; it dropped 0 | the sanitised jsonl does not keep that field and the RapidAPI feed does not provide it | none without re-fetching. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 3 | for existing records `_photo_count` is the number of photo media rows (capped at 10), so the report's ">=6" and ">=10" coverage lines are right but the count behind them is not the original total | the original count is not stored | none. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 3 | each --append run overwrites `normalise-report.txt`, so the report on disk describes only the latest run (run 2: 559 existing, 76 added, 635 final). Run 1's per-rule counts (398 existing, 161 added) are kept in `evidence/dataset-extend/append-runs.md`; the idempotence check was run on a copy so the committed report stays the real run's | the per-rule counts of each real append would otherwise be lost | write the report only when something is added, or keep one report per run. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 3 | the full-rebuild path (no `--append`) is unchanged apart from the shrink guard and a move of its body into `build_from_raw`; it cannot be run here and its dedupe still has no photo rule | raw/rightmove is gone and the human ruled a rebuild out of scope | add the photo rule to `dedupe()` if a rebuild is ever needed. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 4 | the split is stratified only by London versus outside London, not by price, bedrooms or property type, so eval can differ from train on those (per postcode area the share ranges from 0% in WC to 50% in BR and IG, areas of 2-3 listings) | the requirement asks for 25% overall and within 5 points in London and outside; small areas cannot be balanced one by one | stratify further if an eval comparison shows a skew. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 4 | London is decided by postcode area (E, EC, N, NW, SE, SW, W, WC, BR, IG, CR, KT); a CR or KT postcode outside Croydon or Kingston (for example Caterham, Esher) would count as London, and a listing with no postcode counts as outside London | every CR and KT listing in the data is in Croydon or Kingston; the data has no listing without a postcode | use the borough or a postcode lookup if the data changes. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 4 | (superseded by redo 2) the split was a greedy fill per stratum on a shuffled group order, so the share depended on group sizes and on the other listings | replaced in step 4 redo 2 by a per-group hash; see the redo 2 lines below — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 4 | the split uses its own seed (SPLIT_SEED 20261025) so it adds no change to the EPC draws; the EPC letters still change against the 398-listing build because the input set grew | accepted at kickoff | none. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 4 | the duplicate guard compares photo URLs of kind photo only (not floorplans) and exact URL strings; the same-agent waiver applies to coordinates + bedrooms + price only | matches the normalise rule and the amendment | normalise URLs to the file hash if the same image appears at different paths. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 4 | adding `split` to schema.sql broke `test_sanitise.RecordShapeTests.test_columns_match_schema_and_child_tables` (`split` is assigned by the D1 build, not stored in listings.jsonl); resolved by the human's amendment "Named build-only columns": the test now compares sanitise COLUMNS with the schema columns minus `BUILD_ONLY = {"split"}`, still an exact match, and a new test in test_build_d1.py checks every BUILD_ONLY column is in `build_d1.LISTING_COLS` and in the schema | test_sanitise.py was added to step 4 scope by amendment | none; a new build-only column must be added to BUILD_ONLY by hand. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 4 | the duplicate guard tests work around the SPOTTED `demo_epc` IndexError by setting one sample record's `epc_current` to "C" in `DuplicateGuardTests.pair`, so the EPC pass has a real letter; no test covers the empty-letter case | the crash is a separate bug, out of scope | fix `demo_epc` for an input with no real letters, then drop the workaround. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 5 | whether the 24 Oct key (`RAPID_API_KEY`) is the same account as `RAPIDAPI_KEY` is not recorded, so the README reports the header readings (272 after 23 Oct; 297, 108 and 6 on 24 Oct) without drawing a conclusion | the evidence does not say | confirm with the human. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 5 | the dropped table for the append run gives "74 passing cards not fetched in detail" as 244 distinct passing minus 170 detail calls; the fetch evidence does not say how many of those were skipped because the id was already in listings.jsonl | not recorded | derive from raw/rapidapi search files if needed. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 5 | the README's split and area figures (London share, per-area spread, flats over 800k, 4+ bed share, bathrooms 0) were counted ad hoc with python3 -I from listings.jsonl and listings.sqlite and are not covered by a test or script | no figure-check tooling in scope | add a script that prints these from the database. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 2 | the first 24 Oct fetch took page 1 of each area's search, and every RapidAPI page comes back highest price first (card 2 to 25 in falling order in all 32 saved search files, card 1 a cheaper featured card), so the 161 homes it added are each area's top-priced slice under 1.2m (52 at exactly 1.2m, 33 at 1.15m, 19 at 1.1m; median 1.15m). This was not recorded as a tradeoff when step 2 ran | the sort order was not known until the results were read, and the sort_by values 1 and 2 did nothing | deeper pages or a working sort value; the quota is 6 calls from exhausted. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 5 | the README states the price skew as fact: 161 first-pull homes top-priced, 76 top-up homes bunched (37 at 450,000, 22 at 700,000 of the appended records; 40 and 23 of the 80 fetched cards), medians 1.15m and 450,000, original 398 median 600,000, whole set 700,000 | the figures come from listings.jsonl and the search files, counted with python3 -I, and are not covered by a test | none beyond a figure-check script. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 5 | the README says prices are real asking prices because card price equals detail-page price for 237 of 237 records added on 24 Oct (checked ad hoc against `raw/rapidapi/detail`); the 23 Oct RapidAPI and Rightmove-direct prices were not re-checked (raw files gone) | raw/rightmove is not on this machine | none. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 5 | "the 2 coordinate duplicates in append run 2 are the same two as run 1, and the top-up lost 4 files to the tenure rule and none to dedupe" is derived by arithmetic (239 = 161 + 2 + 76; 80 = 76 + 4), not stated in the report; the README says so | the report gives totals per run only | have the append report list dropped ids. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 5 | the README names the three NULL property types as Not Specified, Cottage and Barn Conversion; the first two come from the sanitise report, Barn Conversion from the earlier README, since the 398 raw files are gone | not re-checkable here | none. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 2 redo 2 | no `sort_by` value worked: `1` and `2` both returned the same highest-first order (Brighton, band 250k-700k, 24 of 25 cards at exactly 700000); no further value was tried | a third probe would have left fewer than 5 provider calls spare | find the accepted values (provider docs or playground) and re-run with `--sort`; calls remain only 6. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 2 redo 2 | fell back to two bands per area (250k-450k, 450k-700k), default sort, page 1 only, so each band is highest-first and the 80 new candidates bunch at the band limits: 40 at exactly 450,000 and 23 at exactly 700,000, only 17 elsewhere (min 265,000) | a deeper page or a working sort was unaffordable | needs more calls (page 2+ per band) or a working sort value; the quota is 6 calls from exhausted. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 2 redo 2 | the price spread asked for (across the band, not bunched) was not achieved; prices at exactly 450,000 and 700,000 may be asking-price round numbers or an artefact of how the provider orders the band, not recorded which | cannot be told from card metadata | inspect a second page or a sorted list. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 2 redo 2 | two sort probe searches (Brighton) were spent and their cards are in the pool for the upper-band details run; the 80 detail calls were split 5/4 per commuter town, 3/3 per borough (Hammersmith and Fulham 3/2, to stay at 80), not weighted by pool size | to hit about 80 with 6 calls spare | none. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 2 redo 2 | the upper-band details run accepts cards at exactly 450000 (edge inclusive), so some "upper band" details are the same 450,000 cards the lower band offers; Cambridge's 9 are all 350,000-450,000 and Hammersmith and Fulham's 5 are 375,000-450,000, none above 450,000 | the band filter is inclusive and the search files hold few cards above 450,000 for those areas before the 450,000 ones | exclude the shared edge or pick by price rank; not a code change in this redo. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 2 redo 2 | the feature is at 292 of 300 calls and the provider reports 6 remaining, so no retry or extra page is possible this month | 5 calls must stay spare | wait for the quota to reset or use the human's second key if one exists. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 4 redo 1 | 188 of the 559 listings in the previous build changed train/eval side when the input grew to 635 (old build: 139 eval; the 76 new listings: 19 eval; now 158 eval, 24.9%); the split shuffles whole coordinate groups with one seeded RNG, so any added group reshuffles the order and moves many existing listings. The EPC draws share this dependence on the exact input set | the split is only fixed once all listings are in, as agreed; the previous 559 split was reconstructed by running the current build_d1.py on the first 559 lines of listings.jsonl in a scratch copy | seed the draw per coordinate group (e.g. hash of seed plus group key, or per listing id) so adding listings never moves existing ones; any later append should do that before the split is relied on (training sets, evidence). | redo 2 (2026-10-24): fixed for the split, which is now a per-group hash and moves no existing listing (0 of 559 differ between the 559-line and 635-line builds). Still true for the EPC draws: they use one seeded RNG over the sorted input, so adding listings still reshuffles made-up EPC letters. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 4 redo 2 | the eval share is no longer balanced by construction: each coordinate group is put in eval if sha256(seed, group key) maps below 0.25, so the share is only about 25% by chance. On the 635 listings: 147 eval, 23.1% overall (bound 25 +/- 2), London 100 of 401, 24.9%, outside London 47 of 234, 20.1% (bound 25 +/- 5, margin 0.1 point). Per postcode area it ranges from 0% (BR, IG) to 66.7% (WC) and 34.8% (SE, 92 listings) | the amendment asked for a stable split; stability needs a decision that ignores other listings, which rules out exact balancing. The seed and threshold were not changed | any later append can push outside London below 20% and fail the bound; the share test would then fail and the human decides (a different seed, a wider bound, or accept); more listings narrow the spread. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 4 redo 2 | the old test of exact balancing no longer exists by design: the share test (`test_eval_share_overall_and_by_london`) keeps its bounds unchanged (25 +/- 2 overall, +/- 5 London and outside) and now checks the hash result; nothing was loosened. `test_grouping_keeps_big_groups_together` is unchanged and still passes | change of requirement by the human's amendment | none. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 4 redo 2 | the group key is the rounded (lat, lon) tuple's repr, or ("id", id) with no coordinates, hashed as "SPLIT_SEED|repr" with sha256; the float repr of a 4 dp rounded value is stable across Python 3 builds but would change if the key format changed, which would reassign the whole split | simplest stable form with the stdlib | store the split as a column in listings.jsonl if it must survive a key-format change. — Accepted by human 2026-10-24 ("accept all").
- 2026-10-24 | step 5 | the README names the source type of only one of the five `other` listings ("Block of Apartments"); `listings.jsonl` keeps no raw type field, and the NULL names (Not Specified, Cottage, Barn Conversion) were taken from the README's Coverage table, not re-checked against raw files | the raw type is dropped by sanitise | read the source type from `dataset/raw/rapidapi/detail/` for the RapidAPI ones (the 23 Oct raw files are gone), or keep the raw type in normalise output. — Accepted by human 2026-10-24 ("accept all").

---

## SPOTTED, NOT FIXED

- `dataset/scripts/fetch_rapidapi.py` docstring says "free tier only"; the human now has a 600-request limit | low, step 1 may correct the docstring as part of its change — resolved in step 1
- `dataset/scripts/fetch_rapidapi.py` `--cap` help text still says "free tier ~300" | low
- `dataset/scripts/fetch_rapidapi.py` `Client.call` does not catch `http.client.RemoteDisconnected`, so a dropped connection kills the whole run with a traceback (hit once in step 2) | low
- `dataset/scripts/build_d1.py` `demo_epc` crashes with IndexError (empty letter list) when no listing in the input has a real EPC letter | low, unreachable with real data
- `dataset/scripts/fetch_rapidapi.py` `details --max N` counts only new calls, so a rerun after a crash fetches N more unless --max is reduced by hand | low
- `dataset/scripts/normalise.py` lines ~543 and ~556 use `open()` without closing, causing ResourceWarnings in the test run (step 3 code) | low

---

## VERIFICATION

- [x] All step checkboxes ticked with evidence (25 of 25, 2026-10-24, qa-gate)
- [x] Every evidence path in this file exists (evidence/dataset-extend/probe.md, fetch.md, append-runs.md; dataset/reports/*.txt)
- [x] Test suite run — result: `python3 -I -B -m unittest discover -s dataset/tests`, 123 tests OK, exit 0
- [x] Lint run — result: none configured in kit-config; not run
- [x] Typecheck run — result: none configured in kit-config; not run
- [x] Build run — result: `python3 -I -B scripts/build_d1.py --dataset .` from dataset/, exit 0; listings.sqlite a1701826..., seed.sql 32d8020b..., d1-build-report.txt byte-identical to before
- [x] Diff contains no files outside declared scope (14 modified + 2 new tests + evidence/ + this file, all declared or amended)
- [x] Tradeoff ledger reviewed and signed off by human — all 48 entries accepted, 2026-10-24 ("accept all")
- [ ] Human eye test completed — not done: the human signed off ("accept all ... do commit pr and merge") without running the checks, 2026-10-24. Nothing in this feature has been verified by a human.

---

## HANDOVER

**What was built.** The listings set grew from 398 to 635 for-sale homes. 237 came from RapidAPI on 24 Oct, using 292 calls. Each listing now has a `train` or `eval` label (488 train, 147 eval). The D1 build refuses to run if two listings share an id, a photo URL, or the same coordinates, bedrooms and price from different agents. `normalise.py --append` adds new records without needing the lost raw files. The README describes all of it.

**What to check yourself.**
1. From the repo root run `python3 -I -B -m unittest discover -s dataset/tests`. Expect `Ran 123 tests` and `OK`.
2. `cd dataset && python3 -I -B scripts/build_d1.py --dataset . && sha256sum listings.sqlite d1/seed.sql`. Expect a1701826b78ff5720df067ad8cd7de31fa20c7a2ac730615fe9fe439474b4a04 and 32d8020b49ec2ce4231e531ec54217c8acb120439379bd3b64341f72244f6cb1. Then `git status --short .` should show no change beyond what was already modified.
3. `wc -l dataset/listings.jsonl` should say 635. `git show 7597e7f:dataset/listings.jsonl | head -398 | cmp - <(head -398 dataset/listings.jsonl)` should print nothing.
4. `sqlite3 dataset/listings.sqlite "select split, count(*) from listings group by 1"` should give eval 147, train 488.
5. Open the price spread: `sqlite3 dataset/listings.sqlite "select min(price_gbp), max(price_gbp) from listings"`. Look at the price skew section of `dataset/README.md` and decide if it is acceptable.
6. Read `dataset/README.md` top to bottom. Check the call counts against `evidence/dataset-extend/fetch.md`.
7. Run `git status --short dataset/raw` and `git check-ignore dataset/raw`. Raw files must stay ignored.

**Tools that will help.** A SQLite client (DB Browser or `sqlite3`) on `dataset/listings.sqlite` for the split and price checks. `git diff 7597e7f --stat` for scope. The RapidAPI dashboard to confirm the real remaining quota (we read 6).

**What is not done.**
- The ledger is unsigned: all entries under TRADEOFFS need your sign-off.
- Prices skew. The 161 first-pull homes are each area's top slice under 1.2m (52 at exactly 1.2m). The 76 top-up homes bunch at 450,000 (37) and 700,000 (22). No working `sort_by` value was found.
- Outside London the eval share is 20.1%, only 0.09 points inside the bound. Overall is 23.1%. Any later append may fail the share test.
- Per postcode area the split is uneven (0% to 66.7%).
- The quota is 6 calls from exhausted. No retries or extra pages possible this month.
- Made-up EPC letters still reshuffle whenever the input grows.
- Gaps in tests: `autocomplete` and `Client.call`, `probe` unfiltered, no-coordinate split key, README figures counted by hand.
- SPOTTED, NOT FIXED: stale `--cap` help text; `Client.call` does not catch RemoteDisconnected; `demo_epc` IndexError on input with no EPC letters; `details --max` counts only new calls; two unclosed `open()` calls in normalise.py.
- Photo-URL dedupe is exact-string only, and has no same-agent exception.
- Delivery-point rule never fires on the existing 398.
- Whether the 24 Oct key is the same account as the old key is unrecorded.

**What could bite you.**
1. The split is a hash, so it is stable but not balanced. Adding listings can push outside-London below the bound and fail the share test. The decision is then yours (new seed, wider bound, accept).
2. The price skew means a deck for a budget persona may be thin below 450k and rich at the band edges. Check pool sizes per persona before the batch.
3. Anyone re-running `normalise.py` without `--append` on this machine is refused (by design). With `--append` on the real data it is a no-op that overwrites the normalise report.
4. Eight photo URLs repeat within single listings (not across listings). Harmless to the guard, but a count of "photos" can include repeats.
