# Kit feedback log

Appended to by the `retro` skill. Read the whole thing every few features — the
patterns across entries matter more than any single retro.

Entries are about the kit, not about the code.

---

## Declined proposals

Changes that were considered and rejected, so they do not get re-proposed every retro.

| Date | Proposal | Why declined |
|------|----------|--------------|
|      |          |              |

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
