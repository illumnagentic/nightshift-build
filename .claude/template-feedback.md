# Kit feedback log

Appended to by the `retro` skill. Read the whole thing every few features — the
patterns across entries matter more than any single retro.

Entries are about the kit, not about the code.

---

## Declined proposals

Changes that were considered and rejected, so they do not get re-proposed every retro.

| Date | Proposal | Why declined |
|------|----------|--------------|
| 2026-10-24 | qa-gate `READY FOR SIGN-OFF` verdict | `safe-merge.sh` matches the literal `QA-GATE: PASS`, so new verdict words risk breaking the automation path. Asking the gate in the brief to say plainly when only sign-offs remain worked in F3. |
| 2026-10-24 | Step-order hook accepts `GATE: feature` for qa-gate | Loosening an enforcement hook for a one-line workaround (a `STEP:` header with a note) is not worth it. |
| 2026-10-24 | commit-composer must read every staged file in full | No recurrence in F2 or F3 after F1. |
| 2026-10-24 | pr-description reminds the human of the merge rule | Superseded: the GitHub repo is now squash-only with the PR title as message. |
| 2026-10-24 | CLAUDE.md: commit a passed step before briefing the next | Followed in practice since F2 with no recurrence; not worth a rule. |

---

<!-- Retro entries go below, newest last. Format:

## YYYY-MM-DD — feature-slug

**Repo**: name (project type)
**Steps**: n | **Failed first review**: n | **Amendments**: n

### Friction
- what got in the way | where | cost

### Escapes
- what got through | which guardrail should have caught it

### Worked well
- keep this, and why

### Proposed changes
- kit file | specific change | what it prevents

-->

## 2026-10-24 — web-shell

**Repo**: nightshift-build (Vite + React frontend in `web/`; Python Worker backend planned)
**Steps**: 4 | **Failed first review**: 1 (step 3) | **Amendments**: 1

### Friction
- Step-order hook blocked the qa-gate brief because it had no `STEP:` line; it was re-sent as `STEP: 4` with a note | `.claude/hooks/check-step-order.sh` | one blocked call; the header now claims a step review that it is not
- Per-step commits were decided after step 3 had been briefed. Step 3's implementer appended to the progress file between the orchestrator's check and `git add`, so step 2's commit had to leave the progress file out | orchestrator, `commit-workflow` | one extra round trip with the human; step 2's ticks landed one commit late
- commit-composer twice drafted a title without reading the whole staged diff (step 2: progress file and evidence skipped; step 3: 1,363-line fixtures file skimmed) | `.claude/agents/commit-composer.md` | one resend; one human decision on a partial read
- Step 4's done-when included "the human has eyeballed it", so the step reviewer could not tick "Matches locked requirements" and had to be resumed after the eye test | `feature-kickoff` (plan wording) | one extra reviewer round
- Evidence files tripped the process-reference check in steps 1, 2 and 3. The implementer fixed 1 and 2 itself; step 3 failed review partly on it and recorded the script's exit as 0 when it was 1 | `.claude/agents/implementer.md` | part of one failed review
- Step 1's implementer reported a tradeoff but did not write it to TRADEOFFS; the reviewer logged it | `.claude/agents/implementer.md` | minor
- qa-gate returned FAIL when the only open items were the two human sign-offs, which are expected to be open at that point | `.claude/agents/qa-gate.md` | noise; a FAIL that needed explaining
- The eye test had to be repeated three times (implementer could not click, human ran it, orchestrator re-ran in the built-in browser, then four extra rows were filled in) | `feature-kickoff` checklist + the implementer padding the check list with 8 rows when the done-when named 5 | several turns

### Escapes
- PR #7 was merged on GitHub as a merge commit ("Merge pull request #7 …"), not a squash with the PR title, against `docs/decisions.md` (Git) | nothing in the kit covers the GitHub merge; `pr-description` mentions only opening | one non-conforming commit on `main`
- The step 3 brief told the implementer it could compute chips "with a small local helper in fixtures.ts", which contradicted the locked out-of-scope line ("hand-picked chips"). The step reviewer caught it, but the contradiction came from the orchestrator | orchestrator brief vs RULES/out-of-scope; no check compares brief to lock | one failed review and an amendment
- Two tradeoff entries were worded wrongly and reached human sign-off: #11 says commute minutes hash on postcode (they hash on listing id only); #17 says the username is refreshed on restore (state only, not storage) | step-reviewer accepted ledger wording without checking it against the code | human signed slightly inaccurate entries
- qa-gate counted 20 tradeoffs when there were 21, and recorded typecheck/build exits it did not capture directly | `.claude/agents/qa-gate.md` | minor

### Worked well
- step-reviewer hand-derived chip lists from the contract instead of trusting the implementer's test, and failed step 3 on an unlogged deviation from the lock. That is the review doing its job; keep the "verify, don't trust the report" wording.
- commit-composer caught real problems: the progress file holding step 3 content inside step 2's commit, and a self-contradicting line in step 4's evidence.
- Kickoff asked four questions in one round, each with a recommendation; two of them were dependency approvals. The human answered in one go and nothing had to be re-asked.
- `safe-commit.sh` and the hooks never got in the way of a legitimate commit.
- The built-in browser let the orchestrator run the eye test and quote `localStorage` values as evidence.

### Proposed changes
- `.claude/hooks/check-step-order.sh` | accept a `GATE: feature` header (or skip when the target agent is `qa-gate`) instead of requiring `STEP:` | stops briefs claiming a step they are not
- `.claude/agents/qa-gate.md` | when everything passes except the human sign-off boxes, verdict `READY FOR SIGN-OFF`, not FAIL | removes a false alarm at every wrap-up
- `.claude/agents/implementer.md` | before reporting: run `.claude/scripts/check-process-refs.sh` and write every tradeoff into TRADEOFFS (not only the report) | removes the most common review failure seen here
- `.claude/agents/commit-composer.md` | read every staged file in full; a file it only skimmed must be named in CONCERNS as "not fully read" | stops titles drafted from part of a diff
- `.claude/skills/feature-kickoff/SKILL.md` | (a) keep the human eye test in VERIFICATION, not in a step's done-when; (b) out-of-scope lists outcomes, not implementation methods | avoids the step 4 reviewer round and the step 3 lock breach
- `.claude/CLAUDE.md` (Delegation policy, Step order) | when per-step commits are in force, commit a passed step before briefing the next one, and before each brief re-read the step's out-of-scope lines | prevents the progress-file race and the brief-contradicts-lock escape
- `.claude/skills/pr-description/SKILL.md` | after opening a PR, remind the human of the repo's merge rule (squash, PR title as message) | would have prevented the merge-commit escape; the repo setting (squash only) is the stronger fix and is the human's

**Outcome (2026-10-24)**: human said "document these but leave it". All proposals above are deferred, neither applied nor declined. Revisit at the next retro. Proposal 1 in session (GitHub repo set to squash merge only) is a repo setting for the human, not a kit change.

## 2026-10-24 — web-feedback

**Repo**: nightshift-build (Vite + React frontend in `web/`; Python Worker backend in `worker/`)
**Steps**: 7 (5 planned, 2 added by amendment) + 2 redos | **Failed first review**: 2 (Redo of Step 5, Step 7) | **Amendments**: 3 | **QA gate runs**: 3

(F2 `web-deck` had no retro; its one escape is recorded here because it surfaced in F3.)

### Friction
- Implementers again reported tradeoffs without writing them to TRADEOFFS (Step 6), and one brief's "shell append" put a tradeoff after HANDOVER (Step 7 failed review for it). Third feature in a row; F1 proposal still deferred | `.claude/agents/implementer.md`, orchestrator briefs | 1 failed review, 3 reviewer patch-ups
- This laptop runs Prettier in a PostToolUse hook on every Edit/Write. The first Redo of Step 5 picked up four unrelated reformat hunks and failed review on scope; the fix was a shell edit. The hook is machine config, not in the repo | machine setup; no kit-config brief note warned about it | 1 failed review, 1 extra redo
- qa-gate returned FAIL three times, twice when only the human sign-offs and an external contract change were open. Each time the orchestrator had to explain it was not a defect. Same as F1's deferred proposal | `.claude/agents/qa-gate.md` | noise on every wrap-up
- The step-order hook still forces `STEP: <n>` onto qa-gate briefs. Same as F1's deferred proposal | `.claude/hooks/check-step-order.sh` | small, recurring
- Every commit needed a separate human approval (about 16 in F3), each after a commit-composer round | `.claude/CLAUDE.md` commit rule | a lot of human attention for routine step commits
- Long browser automation scripts hit the 45-second tool limit; results had to be logged to `window` and polled | orchestrator, built-in browser | a few extra turns

### Escapes
- F2's deck ended after 10 cards in development. React StrictMode runs effects twice; a discarded first fetch still applied after reset and `fetchOk` set `exhausted` with cards queued. Passed F2's step review, F2's qa-gate and F2's eye test, because no one swiped past the first batch of 10 and the hook had no test | F2 eye-test list (no "go past the first batch" check); no hook test environment | found by the human in F3's eye test; fixed as F3 Step 6
- Done on an empty optional feedback screen sent empty feedback instead of a skip, breaking a rule in RULES IN FORCE. Steps 3 and 5 each passed review on their own; the gap was between them | step-reviewer reviews one step at a time; the orchestrator's briefs did not restate the skip rule in the step that consumed it | caught by qa-gate run 1
- "Added to favourites" carried over to the next card once every Love opened feedback (a Step 2 rule change with a side effect on F2 behaviour) | no reviewer looked at F2 behaviour affected by the new rule | caught by qa-gate run 1
- F3 was built against a `skipped` field and a feedback rule that the shared contract does not yet contain. Recorded at kickoff as an assumption; the PR is a draft until the backend side lands it | kickoff allows building ahead of the contract | not an escape yet, a merge blocker

### Worked well
- qa-gate run 1 caught two real cross-step defects that five step reviews missed. Keep the whole-branch read and the rule-against-code coverage table.
- Diagnosis by importing the mock module in the page (`await import('/src/api/mock.ts')`) separated a mock fault from a deck fault in one call.
- Recording a contract dependency at kickoff, then opening the PR as a draft, kept the frontend moving without merging ahead of the agreed contract.
- The human asked for an exploration marker against a decisions rule; asking once and gating it to mock mode (tree-shaken out of other builds, checked by grepping the bundle) kept the rule intact.
- Asking decisions through AskUserQuestion with a recommendation got single-turn answers every time.

### Proposed changes
- `.claude/agents/implementer.md` | before reporting: insert every tradeoff as the last entry of the TRADEOFFS section (before `## SPOTTED, NOT FIXED`), never append to the end of the file, and say in the report that it is done | the repeated omission and the misplaced line (3 features)
- `.claude/kit-config.md` (Brief notes) | "On Yewen's laptop a PostToolUse hook runs Prettier on every Edit/Write. After editing, check `git diff`; if unrelated lines were reformatted, restore the file and apply the change with a shell edit." | the Step 5 scope failure
- `.claude/agents/qa-gate.md` | add a verdict `READY FOR SIGN-OFF` for "all checks pass; only human sign-offs or named external dependencies remain" | three misleading FAILs in F3, one in F1 and F2
- `.claude/skills/feature-kickoff/SKILL.md` | (a) any list, deck or paged view gets an eye-test or done-when check that goes past the first batch; (b) a rule in RULES IN FORCE that a later step depends on is restated in that later step's done-when | the 10-card escape and the empty-Done gap
- `.claude/hooks/check-step-order.sh` | accept `GATE: feature` for qa-gate briefs | carried from F1
- Human, not kit: grant commit approval per feature ("approve step commits for this feature") under the existing CLAUDE.md exception, or keep per-commit approval | the 16 approvals
- Human, not kit: one formatting-only commit of `web/src` (Prettier, no logic) so the hook stops producing churn | removes the root cause of the scope failure; needs its own small change and a yes

**Outcome (2026-10-24)**: the human asked the orchestrator to decide ("use an advisor or your own judgement"). Applied: Prettier brief note in `.claude/kit-config.md`; tradeoff insertion rule in `.claude/agents/implementer.md`; past-the-first-batch, restate-dependent-rules and eye-test-in-VERIFICATION lines in `.claude/skills/feature-kickoff/SKILL.md` (the last one closes F1's deferred proposal 6a). Declined, with reasons in the Declined table: the qa-gate verdict, the step-order hook change, and F1's deferred commit-composer, pr-description and CLAUDE.md proposals. Human items: per-feature commit approval not granted (left to the human); the `web/src` Prettier formatting commit agreed ("Use b") and queued until F3 (PR #13) merges, to avoid conflicts. These changes are local to this repo until copied to the shared kit.
