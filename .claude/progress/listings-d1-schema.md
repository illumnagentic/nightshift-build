# Feature: Listings D1 schema and sanitising

- **Slug**: listings-d1-schema
- **Started**: 2026-10-24
- **Branch**: worktree-agent-a1ac46b9dc8cfd04d
- **BASE_SHA**: 616a69790e141aaa0dbe93f5871d35950597f5d5 (baseline commit of dataset/, raw/ ignored, listings.sqlite left for step 4)
- **Status**: in progress

---

## REQUIREMENTS (LOCKED)

Human, in session, 2026-10-24:

> "It's ok we don't need to re pull the data, but we do need to sanitize the data structure and settle on our own schema. start feature kickoff"

> "we want to have d1 sqlite database out of this dataset, and let's do this progress plan as a feature kickoff"

Answers to kickoff questions (2026-10-24):

- Baseline: "Commit dataset, ignore raw/"
- D1 scope: "D1-ready SQL files only" — `schema.sql` (D1 SQLite dialect, CHECK constraints) and `seed.sql` (INSERTs), plus a local `.sqlite` built from the same files, loaded later with `wrangler d1 execute --file`. No Cloudflare account or wrangler needed now.
- Sanitising in scope: "Enums + units, Null vs empty vs 0, Clean text, Range checks"
- Existing IDs (`rm-<rightmove property id>`) are kept; no re-fetch from RapidAPI.

### Source

This session's conversation, quoted above. Background: `docs/product-idea-high-level.md` ("Data: offline listings dump", "DB: D1").

### Explicitly out of scope

- Re-fetching from RapidAPI or re-scraping Rightmove. No network calls at all.
- Creating or loading a real D1 database; wrangler; Cloudflare account.
- Photo/floorplan vision flags (Gemini), the `photo_flags` table, and every app table (users, sessions, decisions, feedback, favourites).
- TfL commute data.
- Raising EPC rating coverage (EPC register, vision on EPC images).
- Changing listing IDs.
- Worker/API or web code.
- New Python packages (stdlib only, per dataset/requirements.txt).
- Editing the root `.gitignore` or the `nvim.log` files.

---

## AMENDMENTS

- 2026-10-24, human: "use miles for unit that come from rightmove data. if you see 0 it means 0" — station distances from Rightmove data with no unit are miles (converted to km for `distance_km`); a 0 in service charge, ground rent or other money fields is a real zero, not unknown.
- 2026-10-24, human: "I agree with you on the lease one" — `lease_years_remaining` 0 stays NULL (Rightmove placeholder for "no lease given"; schema range 1–999 unchanged).

---

## RULES IN FORCE

| Rule                                                                                                                        | Source                                             | Applies to             |
| --------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- | ---------------------- |
| Commits only via `.claude/scripts/safe-commit.sh`, title only, no signature, human approves                                 | `.claude/CLAUDE.md`                                | commits                |
| Commit title `type(scope): message`; scopes in use: worker, web, db, prep, kit                                              | `.claude/CLAUDE.md`, `.claude/kit-config.md`       | commits                |
| No scope creep: touch only the step's declared files                                                                        | `.claude/CLAUDE.md` #1                             | code, docs             |
| No new dependencies without asking; stdlib only                                                                             | `.claude/CLAUDE.md` #2, `dataset/requirements.txt` | code                   |
| Never weaken a test to pass                                                                                                 | `.claude/CLAUDE.md` #3                             | tests                  |
| No speculative generalisation; walk the ladder (e.g. let SQLite CHECK constraints do validation before writing a validator) | `.claude/CLAUDE.md` #4                             | code                   |
| Tradeoffs logged in TRADEOFFS when made                                                                                     | `.claude/CLAUDE.md` #5                             | progress file          |
| Implementer never ticks its own boxes; only step-reviewer, with evidence and date                                           | `.claude/CLAUDE.md` #6                             | progress file          |
| Out-of-scope problems go in SPOTTED, NOT FIXED                                                                              | `.claude/CLAUDE.md` #7                             | progress file          |
| Plain British English, no banned marketing words                                                                            | `.claude/CLAUDE.md`                                | docs, comments, README |
| Never invent a value: unknown is NULL; parsed values recorded as parsed                                                     | human brief to data agent, 2026-10-23              | generated data         |
| Python reading downloaded files runs with `-I`; scripts never live in `raw/`                                                | session environment rule                           | code, commands         |
| API keys never printed, logged or committed; `.env` stays gitignored                                                        | human, 2026-10-23                                  | code, commits          |

---

## PLAN

All paths relative to the worktree root. Steps 1–5 are independent of the network.

### Step 1 — Define the D1 schema

**Goal**: Write `schema.sql` in D1's SQLite dialect as the single source of truth for the listing data.

**Files in scope**: `dataset/d1/schema.sql` (new)

**Done when**: `schema.sql` creates `listings` (one row per listing, flat scalar columns with CHECK constraints for enums A–G EPC, A–H council tax, tenure, property type, and numeric ranges), `listing_media` (listing_id, position, kind ∈ photo/floorplan/epc, url; PK listing_id+kind+position — this is the `photo_id` later photo flags join on), and `listing_stations` (listing_id, position, name, distance_km, types). Foreign keys to `listings.id`. `key_features` and `parsed_fields` stay JSON text on `listings`. Every column has a comment line stating unit and null meaning. `sqlite3 :memory: < dataset/d1/schema.sql` runs clean.

**Evidence location**: the diff; the sqlite3 command output recorded in the reviewer's tick.

- [x] Implemented — dataset/d1/schema.sql, 3 tables (2026-10-24)
- [x] Tested — `sqlite3 :memory: < dataset/d1/schema.sql` exit 0; CHECKs and FK/cascade bite per earlier review (2026-10-24)
- [x] Best practices met — NOT NULL, CHECKs, FKs with cascade; six TRADEOFFS entries present and match schema.sql (2026-10-24)
- [x] Matches locked requirements — three tables, enums, PK listing_id+kind+position, comment per column (2026-10-24)
- [x] No scope drift — git diff 616a697 shows only .gitignore (human's, pre-existing); dataset/d1/ untracked, only schema.sql (2026-10-24)

### Step 2 — Sanitise rules in normalise

**Goal**: Make `normalise.py` emit records that satisfy the schema: enums and units, one null rule, clean text, range checks.

**Files in scope**: `dataset/scripts/normalise.py`, `dataset/scripts/sanitise.py` (new, pure functions only), `dataset/reports/normalise-report.txt` (new), `dataset/listings.jsonl` and `dataset/listings.csv` (regenerated by running normalise; declared 2026-10-24 before briefing, because "still produces the outputs" regenerates them)

**Done when**: property_type maps to the schema's fixed set; tenure, EPC and council tax are upper/lower-cased to the enum or NULL; station distance is in km; unknown is NULL (no `0` standing in for unknown ground rent/lease/service charge, no empty strings); description and key_features have HTML stripped and whitespace collapsed; out-of-range values are set to NULL and counted per field in the normalise report, never invented. Running `python3 -I dataset/scripts/normalise.py` over the existing `raw/` still produces the outputs.

**Evidence location**: the diff; normalise report output saved to `dataset/reports/normalise-report.txt` (new, committed).

- [x] Implemented — dataset/scripts/sanitise.py new, normalise.py runs it as final pass, report written (2026-10-24)
- [x] Tested — rerun of normalise on a copy: jsonl, csv, report byte-identical (deterministic); throwaway load into schema.sql with FKs on: 398/398 listings, 4577 media, 1194 stations, 0 failures, foreign_key_check empty (2026-10-24)
- [x] Best practices met — RANGES match schema.sql CHECKs exactly; NOT NULL drops counted; tradeoffs logged; process-refs exit 0 (2026-10-24)
- [x] Matches locked requirements — enums, km (78 API rows miles->km), 0 kept for money/bathrooms, lease 0 NULL, no HTML/entities in descriptions, ISO dates, 398 in/398 kept (2026-10-24)
- [x] No scope drift — git diff HEAD touches only declared files plus the human's .gitignore and this progress file; untracked listings.sqlite is rewritten by the old writer as required by 'still produces outputs' (2026-10-24)

### Step 3 — Unit tests for the sanitise rules

**Goal**: Pin the sanitise rules with stdlib `unittest`.

**Files in scope**: `dataset/tests/test_sanitise.py` (new)

**Done when**: each rule from step 2 has at least one passing and one rejecting case (enum mapping, unit conversion, 0→NULL, HTML strip, each range bound). `python3 -I -m unittest discover -s dataset/tests` passes.

**Evidence location**: the test file; test run output recorded in the reviewer's tick.

- [x] Implemented — dataset/tests/test_sanitise.py, 56 unittest cases (2026-10-24)
- [x] Tested — `python3 -I -B -m unittest discover -s dataset/tests` exit 0, Ran 56 OK; 9 mutations of sanitise.py in a temp copy (TBC mapped, lease-0 rule dropped, lon bound, km added, default unit km, 0 nulled, not-specified mapped, unescape removed, rounding) each failed the suite (2026-10-24)
- [x] Best practices met — stdlib only, no raw/ or listings.jsonl read, RANGES and COLUMNS cross-checked against schema.sql, km NULL pin logged in TRADEOFFS; process-refs exit 0 (2026-10-24)
- [x] Matches locked requirements — accept and reject case per rule: enums, miles default, 0 kept vs lease 0 NULL, clean text, dates, range edges, NOT NULL drops, record shape (2026-10-24)
- [x] No scope drift — only dataset/tests/test_sanitise.py new in step; other changes are pre-existing progress file and .gitignore (2026-10-24)

### Step 4 — Build seed.sql and the local sqlite from the schema

**Goal**: Generate `seed.sql` and `listings.sqlite` by loading `schema.sql`, so SQLite's CHECK and foreign-key constraints are the validation.

**Files in scope**: `dataset/scripts/build_d1.py` (new), `dataset/d1/seed.sql` (generated), `dataset/listings.sqlite` (regenerated), `dataset/scripts/normalise.py` (only to remove its old ad-hoc sqlite writer)

**Done when**: `build_d1.py` creates a fresh DB from `schema.sql` with `PRAGMA foreign_keys=ON`, inserts every record from `listings.jsonl`, aborts with the listing id and constraint on the first violation, and writes `seed.sql` as plain INSERTs (no BEGIN/COMMIT, which D1 rejects). All 398 listings (or the post-sanitise count, explained) load. `PRAGMA foreign_key_check` and `PRAGMA integrity_check` are clean. Loading `schema.sql` then `seed.sql` into an empty `sqlite3` gives the same row counts.

**Evidence location**: the diff; row counts and pragma output saved to `dataset/reports/d1-build-report.txt` (new, committed).

- [ ] Implemented
- [ ] Tested — evidence: (date)
- [ ] Best practices met — evidence: (date)
- [ ] Matches locked requirements — evidence: (date)
- [ ] No scope drift — evidence: (date)

### Step 5 — Update the README

**Goal**: Document the schema, the sanitise rules and how to load into D1.

**Files in scope**: `dataset/README.md`

**Done when**: README describes the three tables and the null rule, refreshes the coverage table from the step 4 build, lists the re-run order (normalise → tests → build_d1), and gives the exact `wrangler d1 execute <db> --file dataset/d1/schema.sql` / `--file dataset/d1/seed.sql` commands, marked as not yet run.

**Evidence location**: the diff.

- [ ] Implemented
- [ ] Tested — evidence: (date)
- [ ] Best practices met — evidence: (date)
- [ ] Matches locked requirements — evidence: (date)
- [ ] No scope drift — evidence: (date)

---

## TRADEOFFS

- Step 1: `floor_level` is free TEXT with no CHECK (25 distinct messy values, e.g. '1st', 'raised ground', 'higher than 2nd floor (with lift)'); a fixed set would invent structure. Proper fix: a later decision on a floor enum.
- Step 1: `council_tax_band` and `epc_*` CHECKs reject 'TBC' (52 rows today) and '', so step 2 must map them to NULL.
- 2026-10-24 | step 1 | `price_qualifier` and `source` enums list only the values seen in today's 398 rows (`source` has 2 values); `property_type` is a fixed mapped set, not the raw source values | a CHECK needs a closed list | a new value in any of these is rejected until the schema changes, so extend the CHECK and re-create the table.
- 2026-10-24 | step 1 | `lat` CHECK is 50.5 to 52.5 and `lon` CHECK is -2.5 to 1.5, so any listing outside the South East is rejected | the dataset is South East England only; current data sits at lat 51.23 to 51.77, lon -1.05 to 0.02 | a wider search area needs a schema change to the bounds.
- 2026-10-24 | step 1 | The other numeric bounds are judgement calls, not requirements: `price_gbp` 10,000 to 50,000,000; `bedrooms` and `bathrooms` 0 to 10; `lease_years_remaining` 1 to 999; `service_charge_gbp_pa` and `ground_rent_gbp_pa` 0 to 100,000; `distance_km` 0 to 100 | they catch obvious bad data while leaving wide margins | a value outside any bound aborts the step 4 seed load; either clean or NULL such values in step 2, or widen the bound in the schema.
- 2026-10-24 | step 1 | `NOT NULL` on `source`, `source_id`, `url`, `price_gbp` and `fetched_at` means a row missing any of them fails the load instead of loading with NULL | a listing without these is not usable or traceable | step 2 must drop or report such rows, or the column must become nullable.
- 2026-10-24 | step 1 | `'other'` is in the `property_type` enum for types that cannot be mapped, such as "Block of Apartments" | the enum must be closed but real data has unmappable types | step 2 must map those to `'other'` and "Not Specified" to NULL.
- 2026-10-24 | step 1 | The date GLOB on `listed_date` and `fetched_at` checks only the shape, so '2026-99-99' passes; the JSON CHECKs on `key_features`, `parsed_fields` and `types` confirm only an array type, not that the elements are strings | SQLite has no cheap full date or element-type check | validate real dates and string elements in step 2, or add `date()` and `json_each` checks to the schema.
- 2026-10-24 | step 2 | Station distance unit: a missing unit is read as miles (78 RapidAPI rows). Evidence is thin: only 3 stations (Crouch Hill, Finsbury Park, Upper Holloway) appear in both feeds, and there the RapidAPI figure matched the web pages' mile-fitted position within 0.01 miles, against 0.29 to 0.32 as km. The human then decided missing unit = miles | the API states no unit | a second overlap sample, or the API's documentation.
- 2026-10-24 | step 2 | 0 is kept for service charge, ground rent and bathrooms per the human's amendment ("0 means 0"). Only lease_years_remaining 0 becomes NULL, because the schema range is 1 to 999 and the source fills 0 where no lease applies | schema bound | widen the schema bound if 0 should be storable. Note: 13 freehold rows have a 0 service charge or ground rent that may be filler, and one RapidAPI 4-bed house (rm-94396305) has 0 bathrooms though its description mentions an en suite bathroom; both are kept as 0.
- 2026-10-24 | step 2 | RapidAPI station `type` ("1") is not decoded, so those stations get `types` = '[]', which the schema reads as "none given" rather than "unknown" | the code-to-name mapping is not documented | find the mapping and decode it.
- 2026-10-24 | step 2 | Timestamps with no zone are read as UTC and a bare date becomes midnight UTC. No row does either today (all fetched_at are +00:00, all listed_date end in Z) | a fixed shape is required | store date-only listed dates as dates if that ever matters.
- 2026-10-24 | step 2 | RANGES in sanitise.py repeat the schema.sql CHECK bounds by hand | the schema is SQL, the cleaner is Python | generate one from the other, or test they agree (step 3).
- 2026-10-24 | step 2 | Whitespace collapse changes 19 addresses (embedded newlines become one space) and 295 descriptions (trailing spaces before newlines removed); 92 key_features lose HTML entities such as `&amp;` | required by the clean-text rule | none.
- 2026-10-24 | step 2 | Description is HTML-stripped in build() and again in sanitise, so text that decodes to a tag-like string after the first pass is stripped on the second | build() needs stripped text for its parsers | strip once, at the end only.
- 2026-10-24 | step 3 | test_sanitise.py inserts `dataset/scripts` into `sys.path`; `-t dataset` fails because `dataset/tests` is not a package, and `__init__.py` is outside the step's files | no `__init__.py` allowed | add `dataset/tests/__init__.py` and `dataset/scripts/__init__.py`, then run with `-t dataset`.
- 2026-10-24 | step 3 | sanitise.py has no km unit, so a declared `km` distance is set to NULL (`unknown_unit`) and the test pins that; the RANGES-vs-schema test reads only `BETWEEN` CHECKs by regex | RapidAPI/Rightmove give miles only | add `km` to KM_PER_UNIT if a km source appears.
- Step 1: `postcode` has no format CHECK (UK postcode GLOB is unreliable).

---

## SPOTTED, NOT FIXED

- `.gitignore` (root) | uncommitted `/dataset/.env` line added by the human's editor session; redundant with the existing `.env` rule | low
- main checkout | `.claude/worktrees/` shows as untracked; root `.gitignore` does not ignore it | low
- dataset/listings.jsonl rm-172014869 | tenure 'freehold' with yearsRemainingOnLease 114, but key features say "Share Of Freehold" and the description gives a 125 year lease; schema says lease is NULL when not leasehold. Kept as is. | low

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
