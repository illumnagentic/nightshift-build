# Feature: Kit fix — safe-merge refuses large progress files

- **Slug**: kit-safe-merge-sigpipe
- **Owner**: Zsolt
- **Started**: 2026-10-25
- **Branch**: fix/safe-merge-sigpipe
- **BASE_SHA**: 278a239144ef0448a6fdccda2bc32e3e3b6f6704
- **Status**: complete (2026-10-25)
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

- 2026-10-25 (arbiter): Step 1 scope covers line 95 of `safe-merge.sh` (the
  `QA-GATE: PASS` check, `grep -qv` → `grep -v … >/dev/null`) as well as lines 76 and 91.
  Same pipe-into-`grep -q` pattern under `pipefail`; logic unchanged (verified by
  qa-gate). Reverting it would leave the same latent failure in the guard. The PLAN
  Done-when already listed it; this records it against the locked "Any other change"
  exclusion. No other change to `safe-merge.sh` is covered.

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

**Redo (arbiter FIX_NOW, 2026-10-25)**: qa-gate finding — the evidence file misreports
the old form. Correct `evidence/kit-safe-merge-sigpipe/step-1.md` only: the old form
(`grep -Fxq`, pipefail, PR #15 progress file at d54ac25) gives 141 under GNU grep
(`/usr/bin/grep`, 3.11); the earlier "141 not reproduced" came from an agent shell
`grep` function wrapping ugrep, which the script itself does not inherit. Record the
real file size (63,223 bytes, not "over 64 KB"; still reproduces). No change to
`safe-merge.sh`. Done when the evidence file shows, from `bash --norc` with
`type grep` giving `/usr/bin/grep`, old form exit codes and new form exit codes over at
least 5 runs each, the byte count, and no "not reproduced" claim.

- [x] Redo implemented — evidence/kit-safe-merge-sigpipe/step-1.md now has 6-run old (141) vs new (0) table, 63,223 bytes, ugrep explanation; reviewer re-ran 5 runs in bash --norc, GNU grep 3.11: old 141, new 0 each (2026-10-25)
- [x] Redo reviewed — git diff HEAD -- .claude/scripts empty; check-process-refs.sh exit 0; numbers reproduced (2026-10-25)

---

## TRADEOFFS

_None logged._

---

## SPOTTED, NOT FIXED

- Portability: the fix relies on grep reading all of stdin when output goes to
  `/dev/null`. GNU grep drains stdin; BSD/macOS grep reads all input unless `-q`/`-m`.
  Agent-shell `grep` functions (ugrep) are not exported, so the script uses the system
  grep. A here-string or variable form would remove the dependency but departs from
  the locked fix. — accepted by arbiter 2026-10-25: no evidence of a platform where it
  fails, and no team laptop OS recorded as macOS; revisit only if safe-merge refuses a
  large progress file again.
- Pre-existing: the `QA-GATE: PASS` check (line 95) passes if any VERIFICATION line
  says `QA-GATE: PASS`, even if another line says `PASS WITH FINDINGS`. — accepted by
  arbiter 2026-10-25: unchanged by this diff, locked out of scope, and qa-gate writes a
  single verdict line, so a stale PASS beside a later finding needs a qa-gate error;
  candidate for a separate kit fix.

---

## VERIFICATION

- [x] All step checkboxes ticked with evidence — Step 1: five ticks plus two redo ticks, all dated 2026-10-25. (qa-gate 2026-10-25, re-run)
- [x] Every evidence path in this file exists — `evidence/kit-safe-merge-sigpipe/step-1.md` present and now correct: old form 141, new form 0 under GNU grep, 63,223 bytes, no "not reproduced" claim. qa-gate re-measured in `bash --norc`, `/usr/bin/grep` 3.11: old form exit 141 x5 (PIPESTATUS `141 0`), new form exit 0 x5, non-matching line exit 1. (qa-gate 2026-10-25, re-run)
- [x] REQUIREMENTS (LOCKED) unchanged — block identical in c99db7d and 4a88ffc. Line 95 covered by AMENDMENT (arbiter) 2026-10-25. (qa-gate 2026-10-25, re-run)
- [x] Test suite run — result: `cd web && npm test` 121 passed, 5 files, exit 0. Backend suite not run: this diff touches no backend code. (qa-gate 2026-10-25, re-run)
- [x] Lint run — result: no lint command configured in kit-config. (qa-gate 2026-10-25)
- [x] Typecheck run — result: `cd web && npm run typecheck` exit 0 (first gate; no web code changed since). (qa-gate 2026-10-25)
- [x] Build run — result: `cd web && npm run build` exit 0 (first gate; no web code changed since). (qa-gate 2026-10-25)
- [x] Script checks — `bash -n .claude/scripts/safe-merge.sh` exit 0; `check-process-refs.sh 278a239` exit 0, no hits. Line 95 by hand: `QA-GATE: PASS` passes; `PASS WITH FINDINGS`, `FAIL` and no line all refuse. (qa-gate 2026-10-25, re-run)
- [x] Diff contains no files outside declared scope — 3 files: safe-merge.sh, step-1.md (Step 1 scope), this progress file. (qa-gate 2026-10-25, re-run)
- [x] Tradeoff ledger reviewed — signed by arbiter (full automation); no tradeoffs logged. SPOTTED items both marked accepted by arbiter. (qa-gate 2026-10-25, re-run)
- [ ] Human eye test completed — not human-verified (full automation) — smoke check: `safe-merge.sh 15 --check-only` exit 0 "ok: all checks passed"; `safe-merge.sh 12 --check-only` exit 2 "PR #12 is MERGED, not OPEN". (qa-gate 2026-10-25, re-run)

QA-GATE: PASS 2026-10-25

---

## HANDOVER

**What was built.** The merge guard (`.claude/scripts/safe-merge.sh`) no longer refuses a PR because its progress file is large. Three checks (lines 76, 91, 95) piped a file into `grep -q`. Under `set -o pipefail`, `grep -q` exits on the first match, the `git show` or `printf` feeding it dies with exit 141, and the guard read that as "not found". Those checks now send grep's output to `/dev/null` instead, so grep reads all the input. PR #15 now passes `--check-only`.

**What to check yourself.**
1. `git diff 278a239...HEAD -- .claude/scripts/safe-merge.sh`. Three lines change: 76, 91, 95. Only `-q` removed and `>/dev/null` added.
2. `.claude/scripts/safe-merge.sh 15 --check-only`. Expect `ok: all checks passed`, exit 0. It merges nothing.
3. `.claude/scripts/safe-merge.sh 12 --check-only`. Expect `safe-merge: PR #12 is MERGED, not OPEN`, exit 2.
4. In `bash --norc` with `set -o pipefail`: `git show d54ac25:.claude/progress/prefs-filters.md | grep -Fxq -- '- **Branch**: feat/prefs-filters'; echo $?` gives 141 (the bug). The same with `grep -Fx … >/dev/null` gives 0.

**Tools that will help.** A plain terminal (`bash --norc`), not an agent shell: agent shells may wrap `grep` in ugrep, which gave misleading results earlier. `echo "${PIPESTATUS[*]}"` after a pipeline shows which stage failed; 141 in the first slot is SIGPIPE.

**What is not done.**
- No tradeoffs logged.
- Accepted by arbiter, not fixed: the fix relies on GNU grep reading all of stdin when output goes to `/dev/null`. BSD/macOS grep is not confirmed to behave the same.
- Accepted by arbiter, not fixed, pre-existing: line 95 passes if any VERIFICATION line says `QA-GATE: PASS`, even if another says `PASS WITH FINDINGS`. Candidate for a separate kit fix.
- The kickoff said PR #15's progress file is "over 64 KB". It is 63,223 bytes. The bug reproduces anyway.
- Not human-verified: full automation, smoke check only.

**What could bite you.**
- Running the merge guard on a Mac or with a non-GNU grep. If it refuses a large progress file again, reading the file into a variable and matching in bash would remove the grep dependency.
- Lines 58 and 64 still use `| grep -q` on purpose (short strings). Anyone piping a file into them later brings the bug back.
- A stale `QA-GATE: PASS` line left beside a newer finding would still let a PR through (line 95, above).
