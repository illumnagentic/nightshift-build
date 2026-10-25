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

- [x] All step checkboxes ticked with evidence — Step 1: five ticks, all dated 2026-10-25 (qa-gate 2026-10-25)
- [x] Every evidence path in this file exists — `evidence/kit-safe-merge-sigpipe/step-1.md` present. Its "old form exit 0, 141 not reproduced" line is wrong: that run used a shell `grep` wrapper (ugrep), not GNU grep. Under GNU grep 3.11 qa-gate got old form 141 x8, new form 0 x8. File not corrected (qa-gate does not edit evidence). (qa-gate 2026-10-25)
- [x] Test suite run — result: `cd web && npm test` 121 passed, 5 files, exit 0. Backend suite not run: needs a seeded test-mode server and this diff touches no backend code. (qa-gate 2026-10-25)
- [x] Lint run — result: no lint command configured in kit-config. (qa-gate 2026-10-25)
- [x] Typecheck run — result: `cd web && npm run typecheck` exit 0. (qa-gate 2026-10-25)
- [x] Build run — result: `cd web && npm run build` exit 0. (qa-gate 2026-10-25)
- [x] Diff contains no files outside declared scope — 3 files: safe-merge.sh, step-1.md (Step 1 scope), this progress file. (qa-gate 2026-10-25)
- [x] Tradeoff ledger reviewed — signed by arbiter (full automation); no tradeoffs logged. (qa-gate 2026-10-25)
- [ ] Human eye test completed — not human-verified (full automation) — smoke check: `safe-merge.sh 15 --check-only` exit 0 "ok: all checks passed" (old script on the same PR: exit 2, branch check refused, 3 of 3 runs); `safe-merge.sh 12 --check-only` exit 2 "PR #12 is MERGED, not OPEN".

Finding (blocks PASS): the line 95 change is not covered by REQUIREMENTS (LOCKED). The quoted fix names lines 76 and 91 only, and "Explicitly out of scope" says "Any other change to `safe-merge.sh`". The PLAN Done-when adds line 95, but no AMENDMENT records it. The change is harmless (same logic, verified by hand) but the locked block and the diff disagree. Needs an AMENDMENT (arbiter or human) covering line 95, then a re-gate.

QA-GATE: PASS WITH FINDINGS 2026-10-25

---

## HANDOVER

**What was built.** The merge guard (`.claude/scripts/safe-merge.sh`) no longer refuses a PR just because its progress file is large. Three checks piped a file into `grep -q`; under `set -o pipefail` the early exit of `grep -q` killed the `git show`/`printf` feeding it (exit 141), and the guard read that as "not found". Those three now use `grep … >/dev/null`, which reads all input. PR #15 now passes `--check-only`; with the old script it was refused at the branch check.

**What to check yourself.**
1. `git diff 278a239...HEAD -- .claude/scripts/safe-merge.sh`. You should see three lines: 76, 91, 95. Only `-q` removed and `>/dev/null` added.
2. Run `.claude/scripts/safe-merge.sh 15 --check-only`. Expect `ok: all checks passed`, exit 0. It does not merge.
3. Run `git show 278a239:.claude/scripts/safe-merge.sh > /tmp/old.sh && bash /tmp/old.sh 15 --check-only`. Expect `no progress file on feat/prefs-filters declares ...`, exit 2. That is the bug.
4. Run `.claude/scripts/safe-merge.sh 12 --check-only`. Expect `PR #12 is MERGED, not OPEN`, exit 2.
5. Decide whether line 95 may stay. The locked requirements name only lines 76 and 91. If yes, add an AMENDMENT saying so and re-run qa-gate.

**Tools that will help.** A plain terminal (`bash --norc`), not an agent shell: agent shells may wrap `grep` in ugrep, which behaves differently and gave misleading results during this work. `echo "${PIPESTATUS[*]}"` after a pipeline shows which stage failed; 141 in the first slot is the SIGPIPE.

**What is not done.**
- Line 95 change has no amendment behind it (see VERIFICATION finding).
- `evidence/kit-safe-merge-sigpipe/step-1.md` says the old form was not reproduced. That is wrong under GNU grep; it was measured with a ugrep wrapper.
- The kickoff said PR #15's progress file is "over 64 KB". It is 63,223 bytes. The bug reproduces anyway, so the claim does not matter, but it is inaccurate.
- Pre-existing, unchanged by this diff: line 95 accepts VERIFICATION if any line says `QA-GATE: PASS`, even when a later line says `PASS WITH FINDINGS`. Not fixed here; out of scope.
- No tradeoffs logged.

**What could bite you.**
- The fix relies on GNU grep draining stdin when its output goes to `/dev/null`. GNU grep 3.11 does. BSD grep (macOS) or a ugrep alias may not. If Yewen runs the merge guard on a Mac, the same refusal could come back. Reading into a variable first (`c="$(git show …)"; [[ $c == *…* ]]`) would not depend on grep at all.
- The other `| grep -q` uses on lines 58 and 64 were left alone on purpose (short single strings). If someone later pipes a file into them, the same bug returns.
