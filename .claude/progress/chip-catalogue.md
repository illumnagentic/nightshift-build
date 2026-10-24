# Feature: Chip catalogue and closing the contract's open points

- **Slug**: chip-catalogue
- **Started**: 2026-10-24
- **Branch**: docs/chip-catalogue (worktree `.claude/worktrees/api-contract`)
- **BASE_SHA**: 658c6b502be0ca4152f86040bbeed6bec79b4edd
- **Status**: complete (2026-10-24)

---

## REQUIREMENTS (LOCKED)

Human, in session, 2026-10-24:

> "Should we fix the open questions?"

> "I think flag confidence high medium low is more than enough. so as flag value types.
> ABout chip list, I'd prefer if yewen has the plan ready and she just need to
> implement"

Agreed in session alongside that answer:

1. Open point 2 (flag confidence scale) is settled as `high | medium | low`.
2. Open point 3 (flag value types) is settled as currently written in the contract.
3. Open point 4 (ID formats) is settled as: IDs are opaque strings; the frontend never
   parses them.
4. Open point 1 (chip catalogue) is written out in full in `docs/api-contract.md`, so
   Yewen can build F3 and its mocks without asking anything: every `chip_id`, its
   label, its preset phrases, the taste-profile factor it maps to, and the backend
   filter rule that decides when it is offered.
5. The contract keeps the existing rule that the backend chooses which chips a card
   offers; the frontend renders `chips[]` as sent and never filters.
6. The "Schema baseline" note is brought up to date: `main` is now at `658c6b5`, which
   carries 635 listings and the `listings.split` column.

### Source

This session's conversation, quoted above. Background: `docs/api-contract.md` (Open
points, GET /deck chips, PUT feedback, GET /profile factors), `docs/decisions.md`
(Core interaction: chip examples "lush garden, natural light inside, parking"; chips
filtered per listing from photo flags and listing fields; Learning model),
`dataset/d1/schema.sql` and `dataset/listings.sqlite` on `main` at `658c6b5`.

### Explicitly out of scope

- Any backend or frontend code, mocks, fixtures or generated types.
- UI design of the F3 feedback screen beyond what the contract already states.
- Producing photo flags (B2) or changing the flag schema beyond settling points 2–3.
- Agent-generated chip lists (stretch in `docs/decisions.md`).
- Changing `docs/decisions.md` or `docs/plan.md`.
- Re-running the isolated mock test.

---

## AMENDMENTS

_None._

---

## RULES IN FORCE

| Rule | Source | Applies to |
| ---- | ------ | ---------- |
| Commits only via `.claude/scripts/safe-commit.sh`, title only, no signature, human approves | `.claude/CLAUDE.md` | commits |
| Commit title `type(scope): message`; type `docs`, scope `api` | `.claude/CLAUDE.md`, `.claude/kit-config.md` | commits |
| Plain British English, short sentences, banned marketing words | `.claude/CLAUDE.md` | docs |
| No scope creep: touch only declared files | `.claude/CLAUDE.md` #1 | docs |
| No speculative generalisation: chips only for factors a decision, the data or the contract supports | `.claude/CLAUDE.md` #4 | docs |
| Contract must not contradict `docs/decisions.md`; conflicts are reported | `docs/decisions.md` | docs |
| Chips filtered per listing; a chip is never offered where the feature cannot exist | `docs/decisions.md` (Core interaction) | docs |
| A chip answer is about this property's version of the feature | `docs/decisions.md` (Core interaction) | docs |
| Chip filter rules use only listing fields in `dataset/d1/schema.sql` and photo flag fields in the contract | `dataset/d1/schema.sql`, `docs/api-contract.md` | docs |
| Evidence is metadata only, stored in `evidence/` | `docs/decisions.md` (Evidence) | evidence |

---

## PLAN

### Step 1 — Settle open points 2–4 and update the schema baseline

**Goal**: Close open points 2, 3 and 4 in the contract and bring "Schema baseline" up
to date with `main` at `658c6b5`.

**Files in scope**: `docs/api-contract.md`.

**Done when**:
- Flag confidence (`high | medium | low`) and flag value types are stated as settled,
  not assumed, wherever they were hedged.
- The General section says IDs are opaque strings the frontend never parses.
- Open points 2, 3 and 4 are removed; only the chip catalogue point remains.
- "Schema baseline" says the contract matches `main` at `658c6b5` (635 listings,
  `listings.split` present and never exposed); no text calls `split` uncommitted.
- All JSON blocks parse; no other changes.

**Evidence location**: the diff.

- [x] Implemented — diff: General opaque-ID bullet l.15-17, baseline l.660-665, open points 2-4 removed (2026-10-24)
- [x] Tested — evidence: 20/20 json blocks parse (python3 -I); check-process-refs.sh 658c6b5 exit 0; schema.sql l.32 has split; listings count 635 (2026-10-24)
- [x] Best practices met — evidence: no banned words, no hedging on confidence/value types (grep), no 7597e7f/uncommitted text (2026-10-24)
- [x] Matches locked requirements — evidence: points 2-4 and baseline per reqs 1,2,3,6; only Chip catalogue point remains at l.667-670 (2026-10-24)
- [x] No scope drift — evidence: git diff 658c6b5 --stat shows only docs/api-contract.md (+ untracked progress file) (2026-10-24)

### Step 2 — Write the chip catalogue

**Goal**: Add a "Chip catalogue" section to `docs/api-contract.md` listing every chip
with `chip_id`, label, factor, preset phrases and offered-when rule, and record how
many listings each rule offers the chip on.

**Files in scope**: `docs/api-contract.md`, `evidence/chip-catalogue/coverage.md` (new).

**Done when**:
- Every chip has `chip_id`, label, factor, 3–4 preset phrases about this property's
  version, and an offered-when rule using only schema listing fields, `key_features`
  text or contract photo flag fields.
- The chips include the `docs/decisions.md` examples (garden, natural light, parking).
- No rule can offer a chip where the feature cannot exist (e.g. no garden chip on a
  flat without a garden mention).
- Chips that depend on photo flags say what happens until B2 flags exist.
- The `GET /profile` factor list is defined from the catalogue (plus any non-chip
  factors, each named).
- JSON examples use catalogue `chip_id`s; the chip-catalogue open point is removed (and
  the Open points section with it if empty).
- `evidence/chip-catalogue/coverage.md` gives, per chip, the number of the 635 listings
  on `main` its rule offers it on, the query used, and the date. Metadata only.
- All JSON blocks parse; no contradiction with `docs/decisions.md`.

**Evidence location**: `evidence/chip-catalogue/coverage.md` and the diff.

- [x] Implemented — diff: Chip catalogue section in docs/api-contract.md (20 chips, phrases, factors), evidence/chip-catalogue/coverage.md; open point removed (2026-10-24)
- [x] Tested — evidence: coverage script re-run from coverage.md (python3 -I) matches every count incl. parking 264, top8 558/343/81; 20 table rows; 20/20 json blocks parse; check-process-refs.sh 658c6b5 exit 0 (2026-10-24)
- [x] Best practices met — evidence: parking regex identical in contract l.466 and script; no banned words (grep); deck example's 8 chips follow offered/featured/priority/cap and phrases match catalogue; example assumptions stated in contract (2026-10-24)
- [x] Matches locked requirements — evidence: req 4 and 5: every chip_id, label, phrases, factor, offered rule in contract; frontend renders chips[] as sent; garden, natural_light, parking present (2026-10-24)
- [x] No scope drift — evidence: git status shows only docs/api-contract.md, evidence/chip-catalogue/coverage.md, progress file (2026-10-24)

---

## TRADEOFFS

- 2026-10-24, step 1: the EPC sentence in Schema baseline was lightly reworded (no longer names the commit that dropped epc media) | the baseline is now `658c6b5` | none needed. | **Accepted by human, 2026-10-24** ("accept all").
- 2026-10-24, step 2: at most 8 chips per card, ordered featured first then by priority | the orchestrator's brief suggested 8; evidence shows every card offers 10 to 18 chips, so a cap is needed, and featured chips number 6 at the median | a cap tuned against real swipe data once chips are logged. | **Accepted by human, 2026-10-24** ("Accept all").
- 2026-10-24, step 2: rules search `key_features` only, not `description` | `key_features` is short structured text, `description` is free prose that raises false matches | some flats whose description mentions a garden get no garden chip (flat with garden mention in key_features: 85; in key_features or description across all listings: 456 versus 312). A later pass could add description with tighter patterns. | **Accepted by human, 2026-10-24** ("Accept all").
- 2026-10-24, step 2: regex keyword rules with no sampling of real key_features beyond counts | time | check false matches (for example `original`, `character`, `light`) against a sample of listings before the batch. | **Accepted by human, 2026-10-24** ("Accept all").
- 2026-10-24, step 2: `council_tax` chip dropped | it is never featured and last in priority, so the cap of 8 cuts it from every card (0 of 635) | give it a featured rule, or raise the cap. | **Accepted by human, 2026-10-24** ("Accept all").
- 2026-10-24, step 2: `price_value` and `commute` always featured, priority 5 and 6 | price and commute are universal decision factors in the decisions file | none. | **Accepted by human, 2026-10-24** ("Accept all").
- 2026-10-24, step 2: no non-chip factors, and factor name equals `chip_id` | keeps the profile list fixed and the offered-vs-chosen ratio per factor simple | split a chip across factors only if the learning model needs it. | **Accepted by human, 2026-10-24** ("Accept all").
- 2026-10-24, step 2: `home_office` offered on any listing with 2 or more bedrooms | a spare room can be a desk; 561 listings | none. | **Accepted by human, 2026-10-24** ("Accept all").
- 2026-10-24, step 2: `commute` has no per-listing count in the evidence | depends on user postcode and TfL | count it per user in the persona batch. | **Accepted by human, 2026-10-24** ("accept all").

---

## SPOTTED, NOT FIXED

- docs/api-contract.md ~l.361 (Enums and nullability intro): "Every value is a string" is loose, as flag `value` is a number for `sqm_estimate` (stated at l.389). Enum values are all strings, so not wrong, but worth a tweak later.
- docs/api-contract.md Chip catalogue: a flat's `floor_level` values include odd text ("higher than 2nd floor (with lift)"); the `floor_level` chip does not parse it, it only checks not null | low.
- dataset/listings.sqlite: `key_features` garden mention is in 312 listings, not the 364 the brief quoted; the brief's substring counts differ from `key_features` alone | low.

---

## VERIFICATION

- [x] All step checkboxes ticked with evidence — 10/10, 2026-10-24
- [x] Every evidence path in this file exists — evidence/chip-catalogue/coverage.md, docs/api-contract.md
- [x] Test suite run — result: not configured in kit-config; coverage script re-run, all counts match; 20/20 json blocks parse
- [x] Lint run — result: not configured; check-process-refs.sh 658c6b5 exit 0
- [x] Typecheck run — result: not configured
- [x] Build run — result: not configured
- [x] Diff contains no files outside declared scope — docs/api-contract.md, evidence/chip-catalogue/coverage.md, progress file
- [x] Tradeoff ledger reviewed and signed off by human — all nine entries accepted, 2026-10-24
- [x] Human eye test completed — human read the Chip catalogue section and confirmed "Looks right", 2026-10-24

---

## HANDOVER

**What was built.** The API contract now has no open points. It settles flag confidence (`high | medium | low`), flag value types and opaque IDs. It adds a full chip catalogue: 20 chips, each with label, phrases, factor, offered-when and featured-when rules, and a cap of 8 per card.

**What Yewen checks.**
1. Read `docs/api-contract.md`, section "Chip catalogue", and the deck example near line 195. Build F3 mocks from them.
2. Render `chips[]` exactly as sent: same order, no filtering, no adding. Show `phrases` as suggestions that fill `text` only. Strength (`must_have`, `nice_to_have`, `would_prefer_not`, `deal_breaker`) is a separate choice.
3. Allow up to 8 chips per card. `commute` appears only when `commute.minutes` is not null.
4. Sending a chip not on the card gives 422 `chip_not_offered`.
5. Treat IDs as opaque strings. Do not parse them.

**What is not done.** Photo-flag clauses are written but untestable until B2 produces flags. Rules are regex over `key_features` only, unsampled for false matches. `council_tax` was dropped. The cap of 8 is untuned. `commute` has no per-listing count. Nothing is implemented in code.

**What could bite you.** Regex words such as `light`, `original`, `character` may offer or feature chips wrongly. Chips below the cap are never logged as offered, which skews the offered-versus-chosen weight for low-priority chips such as `home_office` (43 of 635 cards). `floor_level` text can be odd, such as "higher than 2nd floor (with lift)".
