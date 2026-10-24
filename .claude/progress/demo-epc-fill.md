# Feature: Demo EPC ratings

- **Slug**: demo-epc-fill
- **Started**: 2026-10-24
- **Branch**: fix/make-dataset-comply
- **BASE_SHA**: 5aa49bf
- **Status**: complete 2026-10-24 (eye test skipped by human)

---

## REQUIREMENTS (LOCKED)

Human, in session, 2026-10-24:

> "Since we need it for a demo, we can make up the EPC ratings for the ones that lack of it. We can get rid of the pdfs."

Answers to kickoff questions (2026-10-24):

- Chart images: "I think the chart shows EPC potential and what it is, so we can drop all charts, make up all, but gotta have both letters each entry"
- Marker for made-up ratings: "No marker"
- How letters are chosen: "Match real spread, seeded (Recommended)" — random but repeatable (fixed seed), weighted to the 93 real ratings.
- epc_potential: "Yes" — invent a potential rating at or above the current one.
- Potential rule: "0-2 bands better (Recommended)" — potential = current improved by 0, 1 or 2 bands (seeded, weights 20/50/30), never better than A.
- Plan, rules in force and out-of-scope list: "Approve (Recommended)".
- Branch: "fix/make-dataset-comply".

Read together, as confirmed by the human at plan approval:

- Every EPC media row (`kind = 'epc'`, PDFs and images alike) is removed.
- The 93 real `epc_current` letters are kept. Every listing with no `epc_current` gets a made-up one.
- Every listing gets an `epc_potential`, made up, never worse than its `epc_current`.
- After the change, all 398 listings have both letters. Nothing in the database marks which are made up.

### Source

This session's conversation, quoted above.

### Explicitly out of scope

- Reading letters from the chart images (OCR, Gemini vision).
- Any marker column or flag for made-up values; schema changes of any kind.
- Changing `listings.jsonl`, `listings.csv`, `normalise.py` or `sanitise.py`. They keep the scraped data as scraped. `raw/` is not on this machine, so `normalise.py` cannot be re-run here anyway.
- Any field other than `epc_current`, `epc_potential` and EPC media rows.
- Editing `docs/decisions.md` (its "keep only listings with EPC" line). Reported, not changed.
- Loading into a real D1 database; wrangler.
- New Python packages (stdlib `random` only).

---

## AMENDMENTS

_None._

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
| Never invent a value: unknown is NULL — **overridden for `epc_current` and `epc_potential` only**, by the human, 2026-10-24. Still in force for every other field | human brief 2026-10-23; override this session | generated data |
| Made-up EPC values are deterministic: same input and seed give byte-identical outputs | human answer "seeded" | code, generated data |
| Docs must not claim EPC letters come from agent text once most are made up | `.claude/CLAUDE.md` ("say what is true") | README |
| Python reading dataset files runs with `-I` | session environment rule | commands |

---

## PLAN

All paths relative to the repository root. The change lives in `build_d1.py`, between reading `listings.jsonl` and inserting rows, so only the D1 outputs carry demo values.

### Step 1 — Demo EPC pass in build_d1

**Goal**: `build_d1.py` drops every EPC media row and fills both EPC letters on every listing before inserting.

**Files in scope**: `dataset/scripts/build_d1.py`, `dataset/d1/seed.sql` (regenerated), `dataset/listings.sqlite` (regenerated), `dataset/reports/d1-build-report.txt` (regenerated)

**Done when**: one pure function applied per record, with a fixed seed: removes media with `kind = 'epc'`; keeps a non-NULL `epc_current`; otherwise draws one with weights equal to the counts of the real letters in the input (today C 43, D 26, B 20, E 3, A 1); sets `epc_potential` to a letter equal to or better than `epc_current`, improved by 0, 1 or 2 bands with weights 20/50/30 and capped at A, stated in a code comment. Running `python3 -I -B scripts/build_d1.py --dataset .` from `dataset/` gives: 398 listings, 0 `epc` media rows, 0 NULL `epc_current`, 0 NULL `epc_potential`, 0 rows where potential is worse than current, the 93 original letters unchanged, `foreign_key_check` and `integrity_check` clean, self-check PASS. A second run is byte-identical. The report adds EPC counts (current and potential by letter, media rows by kind). `listings.jsonl` and `listings.csv` are unchanged.

**Evidence location**: the diff; `dataset/reports/d1-build-report.txt`.

- [x] Implemented — demo_epc in dataset/scripts/build_d1.py; rerun gives 398 listings, self-check PASS (2026-10-24)
- [x] Tested — evidence: rerun checksums unchanged; sqlite3 -I: 0 epc media, 0 NULL letters, 0 potential worse, fk/integrity clean; 56 unittest OK (2026-10-24)
- [x] Best practices met — evidence: stdlib random, fixed seed, byte-identical rerun, three tradeoffs logged (2026-10-24)
- [x] Matches locked requirements — evidence: both letters on all 398, 93 real kept, epc media removed, no marker (2026-10-24)
- [x] No scope drift — evidence: git status shows only the 4 declared files plus progress file; process-refs exit 0 (2026-10-24)

Redo (2026-10-24): review failed on unlogged tradeoffs; logging them, no code change.

### Step 2 — Tests for the demo EPC pass

**Goal**: Pin the step 1 rules with stdlib `unittest`.

**Files in scope**: `dataset/tests/test_build_d1.py` (new)

**Done when**: tests cover: EPC media removed and other media kept with positions unchanged; a real `epc_current` kept; a missing one filled from A–G; potential never worse than current, including current A; same seed gives the same output; weights follow the input's real letters. `python3 -I -B -m unittest discover -s dataset/tests` passes, existing 56 included.

**Evidence location**: the test file; run output in the reviewer's tick.

- [x] Implemented — dataset/tests/test_build_d1.py, 6 build-level tests added in BuildTests (2026-10-24)
- [x] Tested — evidence: unittest discover 75 OK exit 0; mutation weights=1 fails test_seed_pinned_to_epc_seed (2026-10-24)
- [x] Best practices met — evidence: temp dirs, subprocess, dataset sha256 unchanged after run, tradeoff logged (2026-10-24)
- [x] Matches locked requirements — evidence: tests cover media, kept letters, fill, potential, seed, weights (2026-10-24)
- [x] No scope drift — evidence: only test file new; process-refs exit 0 (2026-10-24)

Redo (2026-10-24): review failed, main() weights path untested; adding build-level tests.

### Step 3 — README

**Goal**: The dataset README says what the database now holds.

**Files in scope**: `dataset/README.md`

**Done when**: README states that in `listings.sqlite` and `seed.sql` all EPC chart images are removed and both EPC letters are filled, 93 current letters from agent text and the rest made up for the demo (seeded, weighted to the real spread), while `listings.jsonl` and `listings.csv` keep the scraped values. Coverage table, EPC counts and media row count match the step 1 report. No claim that all EPC letters come from agent text.

**Evidence location**: the diff.

- [x] Implemented — README Demo EPC values section, files list, schema note, coverage table updated (2026-10-24)
- [x] Tested — evidence: every figure matches sqlite3 -I query, d1-build-report.txt and jsonl count (media 4248, 329 rows/313 listings, seed 20261024, 5840 stmts, 2140264 bytes); banned-word grep no hits (2026-10-24)
- [x] Best practices met — evidence: states no marker, jsonl/csv keep scraped values, no remaining claim all DB letters are from agent text (2026-10-24)
- [x] Matches locked requirements — evidence: Done-when items all present in dataset/README.md diff (2026-10-24)
- [x] No scope drift — evidence: git diff 5aa49bf -- dataset/README.md is EPC/media/seed-size text only; process-refs exit 0 (2026-10-24)

---

## TRADEOFFS

- 2026-10-24 | kickoff | 305 current and 398 potential EPC letters are invented, with nothing in the database to tell them apart from the 93 real current letters | human's choice: demo data, no marker | add an `epc_source` column, or compare against `listings.jsonl`, which keeps the originals. — Accepted by human 2026-10-24 ("Accept all").
- 2026-10-24 | kickoff | the real EPC chart images (313 listings) are deleted from the D1 outputs, so a made-up letter can never be checked against a chart | avoids cards whose chart contradicts their letter | the URLs remain in `listings.jsonl`; restore by dropping the pass. — Accepted by human 2026-10-24 ("Accept all").
- 2026-10-24 | step 1 | the report header "== epc (demo values, see README) ==" points at a README that does not say so until step 3 | flags the made-up values where the data has no marker | step 3 updates the README. — Accepted by human 2026-10-24 ("Accept all").
- 2026-10-24 | step 1 | the fixed seed 20261024 plus the sort by id make the made-up letters depend on the exact input set; adding, removing or re-id-ing any listing reshuffles every made-up letter after it | repeatable for a fixed input, which is all the requirement asks | draw per listing from a seed derived from its id, if stability across input changes is ever needed. — Accepted by human 2026-10-24 ("Accept all").
- 2026-10-24 | step 1 | records are now inserted sorted by id, so row order in seed.sql and listings.sqlite changed against the previous build, and the seed.sql diff is larger than the EPC change alone | the seeded draw needs a fixed order | none needed. — Accepted by human 2026-10-24 ("Accept all").
- 2026-10-24 | step 2 | the build-level tests replay the weight computation (Counter of real letters, sorted by id, Random(EPC_SEED)) in the test to pin the exact draws, so a change to the seed or the weights fails them but the expected values are not independent of the method; each build test also runs main() in a subprocess on 40 real records, not the full 398 | an independent oracle for seeded draws does not exist short of freezing expected letters | freeze a golden seed.sql digest for a fixed small input, if a change of method should also fail. — Accepted by human 2026-10-24 ("Accept all").

---

## SPOTTED, NOT FIXED

- `docs/decisions.md` Data › Listings source | says "Keep only listings with EPC, floorplan and photos" and "Target 500+"; the dataset now has made-up EPC and 398 listings | decision text out of date, team to rewrite
- `.claude/progress/listings-d1-schema.md` | VERIFICATION and HANDOVER never filled, though the feature is merged | low

---

## VERIFICATION

- [x] All step checkboxes ticked with evidence (15 of 15, all dated 2026-10-24)
- [x] Every evidence path in this file exists (dataset/reports/d1-build-report.txt, dataset/tests/test_build_d1.py)
- [x] Test suite run — `python3 -I -B -m unittest discover -s dataset/tests`: 75 tests OK, exit 0 (2026-10-24, qa-gate)
- [x] Lint run — none configured in kit-config; none run
- [x] Typecheck run — none configured in kit-config; none run
- [x] Build run — `python3 -I -B scripts/build_d1.py --dataset .` from dataset/: exit 0; listings.sqlite sha256 f0915db0...8e6a and seed.sql sha256 acc88363...8cf2 unchanged after rerun; report byte-identical (2026-10-24, qa-gate). `check-process-refs.sh 5aa49bf`: exit 0, no hits.
- [x] Diff contains no files outside declared scope (the five dataset files, the new test file and this progress file; listings.jsonl and listings.csv untouched)
- [x] Tradeoff ledger reviewed and signed off by human — all six accepted, 2026-10-24 ("Accept all")
- [ ] Human eye test completed — skipped by human 2026-10-24 ("The data set should be improved anyway"). Nothing in this feature has been verified by a human.

---

## HANDOVER

**What was built**

The D1 outputs (`dataset/listings.sqlite` and `dataset/d1/seed.sql`) now give every one of the 398 listings both an EPC current and an EPC potential letter. The 93 real current letters are kept. The other 305 current letters and all 398 potential letters are made up, from a fixed seed, weighted to the real spread. Every EPC chart or PDF row is gone from the media table. Nothing in the database marks which letters are made up. `listings.jsonl` and `listings.csv` are unchanged.

**What to check yourself**

1. From the repo root, run the tests: `python3 -I -B -m unittest discover -s dataset/tests`. Expect "Ran 75 tests" and "OK".
2. Rebuild: `cd dataset && python3 -I -B scripts/build_d1.py --dataset .`. Expect the self-check to say PASS.
3. Run `sha256sum dataset/listings.sqlite dataset/d1/seed.sql`. Expect f0915db046bb88ce707077a34ec10085002c8afd6a914459f9f1958c8bd68e6a and acc8836353915735a09b638e4d74b2c87c0279f7c6138a826881a30bb5ec8cf2. Then `git status`: the report and the database should show no new change from the rebuild.
4. Check the data. Run `python3 -I -c "import sqlite3; c=sqlite3.connect('dataset/listings.sqlite'); print(c.execute(\"select count(*), sum(epc_current is null), sum(epc_potential is null), sum(epc_potential>epc_current) from listings\").fetchall(), c.execute(\"select count(*) from listing_media where kind='epc'\").fetchall())"`. Expect `[(398, 0, 0, 0)] [(0,)]`. (A letter earlier in the alphabet is better, so "potential > current" means worse.)
5. Read the "Demo EPC values" section of `dataset/README.md` and the "epc" block of `dataset/reports/d1-build-report.txt`. Check the figures agree: current A 6, B 83, C 196, D 105, E 8; potential A 135, B 148, C 89, D 23, E 3.
6. Read the five tradeoffs above and decide whether you accept each. Sign them off in this file.

**Tools that will help**

- `git diff 5aa49bf -- dataset/scripts/build_d1.py` is 36 lines and holds the whole logic.
- A database client (or `python3 -I` with sqlite3) to look at a few listings' letters. Compare against `listings.jsonl`: where `epc_current` is null there, the letter is made up.
- `git diff --stat 5aa49bf`: `seed.sql` shows a very large diff. That is expected, see below.

**What is not done**

- Made-up letters are indistinguishable from real ones in the database (tradeoff 1). Only `listings.jsonl` tells them apart.
- The real EPC chart URLs are deleted from the D1 outputs (tradeoff 2). They remain in `listings.jsonl`.
- Made-up letters depend on the exact set of listings. Adding, removing or renaming any listing reshuffles every made-up letter after it (tradeoff 4).
- Rows are now inserted sorted by id, so `seed.sql` and `listings.sqlite` differ from the old build by more than the EPC change (tradeoff 5).
- The tests replay the build's own weighting method to pin the draws, so they are not an independent check (tradeoff 6).
- `docs/decisions.md` still says "Keep only listings with EPC". Not edited, listed in SPOTTED, NOT FIXED.
- `.claude/progress/listings-d1-schema.md` still has empty VERIFICATION and HANDOVER sections.
- No lint, typecheck or CI command exists. No D1 or wrangler import was tried.
- Optional wording note from a reviewer, not applied: `dataset/README.md` line 266 "Ratings come only from agent text" could read "Real ratings come only from agent text". The sentence sits right after a line saying the database holds made-up values, so it is slightly misleading as written.

**What could bite you**

- A made-up rating shown to a user or judge as fact. The database has no marker and the README warning is the only guard. If the recording shows an EPC letter, it may be invented.
- Anyone who re-runs `normalise.py` and then the build, or who adds listings, gets different made-up letters for existing listings without any warning. Letters you have already shown in a recording could change.
- The curator and any eval using EPC will see made-up values as signal. A persona rule such as `epc<=D` is scored against random letters for 77% of listings, so results on EPC-driven rules mean little.
- The `seed.sql` import into real D1 has never been tried (size 2.1 MB, 5,840 statements).
