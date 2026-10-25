# Feature: Kit fix — safe-merge refuses large progress files

- **Slug**: kit-safe-merge-sigpipe
- **Owner**: Zsolt
- **Started**: 2026-10-25
- **Branch**: fix/safe-merge-sigpipe
- **BASE_SHA**: 278a239144ef0448a6fdccda2bc32e3e3b6f6704
- **Status**: in progress
- **Mode**: full automation (on since 2026-10-24)

---

## REQUIREMENTS (LOCKED)

Main agent to the human, 2026-10-24, after `safe-merge.sh 15` refused PR #15:

> "Bug in the merge guard: safe-merge.sh runs `set -o pipefail` and checks files with
> `… | grep -q`. `grep -q` stops reading at the first match, so the command feeding it
> is killed (exit 141), and `pipefail` turns that into a failed check. Fix: in the
> checks that pipe a whole file into `grep -q` (lines 76 and 91), swap `-q` for
> `>/dev/null`. Should I fix the merge script on a small `fix(kit)` branch (you approve
> the edit), merge that, then merge #15?"

Human, 2026-10-25: "carry on".

### Source

Quoted above.

### Explicitly out of scope

- Any other change to `safe-merge.sh` or any other kit script, hook or setting.
- The short title checks on lines 58 and 64 (they pipe a single short string).
- Merging PR #15 (that is B3's own close-out).

---

## AMENDMENTS

_None._

---

## RULES IN FORCE

| Rule | Source | Applies to |
| ---- | ------ | ---------- |
| Commits only via `.claude/scripts/safe-commit.sh`, title only, no signature | `.claude/CLAUDE.md` | commits |
| Edits to `safe-merge.sh` always prompt the human | `.claude/CLAUDE.md` Modes | the edit |
| No scope creep; never weaken a check | `.claude/CLAUDE.md` #1, #3 | code |
| Only step-reviewer ticks, with evidence and date | `.claude/CLAUDE.md` #6 | progress file |
| Evidence is metadata only, under `evidence/kit-safe-merge-sigpipe/` | `.claude/CLAUDE.md` | evidence |

---

## PLAN

### Step 1 — Stop pipe-early-exit from failing safe-merge checks

**Goal**: the checks in `safe-merge.sh` that pipe a file or file section into
`grep -q` (lines 76, 91, 95) give the same verdict whatever the input size.

**Files in scope**: `.claude/scripts/safe-merge.sh`,
`evidence/kit-safe-merge-sigpipe/step-1.md`.

**Done when**: each of those three checks uses `grep … >/dev/null` (or reads into a
variable) instead of `grep -q` on the pipe, with no other change to its logic;
`safe-merge.sh 15 --check-only` passes the branch check that failed before (PR #15's
progress file is over 64 KB); a check that should refuse still refuses (e.g.
`--check-only` on a PR with no matching progress file, or a dry test with a pattern
that does not match); `bash -n` passes.

**Evidence location**: `evidence/kit-safe-merge-sigpipe/step-1.md`

- [x] Implemented — 3 lines changed in safe-merge.sh (76, 91, 95), git diff 278a239 (2026-10-25)
- [x] Tested — evidence: bash -n 0; `safe-merge.sh 15 --check-only` 0; `12 --check-only` 2 refuse; GNU grep under pipefail old form 141 x8, new form 0 x8; PASS WITH FINDINGS only refused (2026-10-25)
- [x] Best practices met — evidence: no check weakened, pattern/flags identical bar -q, check-process-refs.sh exit 0 (2026-10-25)
- [x] Matches locked requirements — evidence: lines 76, 91 swapped -q for >/dev/null as quoted, plus line 95 per Done-when (2026-10-25)
- [x] No scope drift — evidence: diff touches only .claude/scripts/safe-merge.sh plus step-1.md (2026-10-25)

---

## TRADEOFFS

_None logged._

---

## SPOTTED, NOT FIXED

_None._

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
