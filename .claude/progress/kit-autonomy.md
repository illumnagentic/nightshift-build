# Feature: Kit autonomous mode

- **Slug**: kit-autonomy
- **Owner**: Zsolt
- **Started**: 2026-10-24
- **Branch**: feat/kit-autonomy
- **BASE_SHA**: 628a2c711b4095d4f342a03dfc50b9244e6960ed
- **Status**: in progress

---

## REQUIREMENTS (LOCKED)

Human, in session, 2026-10-24:

> "let's start the backend steps. But first, I want to do a workflow that works without
> human approval. In case there's a trade off and cheap to fix it then rather fix it, or
> if it can become a blocker then obviously better fix it. A smart model should make
> these decisions. How can we set this up leveraging the current governance layer. And
> also it should commit, push, create pr, and merge."

Answers to the proposal, human, 2026-10-24 (each asked as its own yes/no):

1. Arbiter: "Yes" — add the arbiter subagent (Opus) to decide tradeoffs and
   fix-now vs accept vs escalate, replacing the human tradeoff sign-off while autonomy
   is on.
2. Auto-merge: "Yes" — add safe-merge.sh plus permission to push feature branches, open
   PRs and squash-merge them without asking.
3. Repo config: "Yes" — change GitHub repo settings: squash only (no merge commits or
   rebase), PR title as message, empty body, delete branch on merge.
4. Pre-approved backend dependencies: "fastapi, google-genai, pytest". Anything else
   escalates.

Proposal the answers refer to (agreed in the same session):

- An `Autonomy: on` switch in `.claude/kit-config.md`, read by the skills. The
  CLAUDE.md commit-approval exception ("unless they have said otherwise in this
  session") also honours it, so it survives a new session.
- Arbiter verdicts: FIX_NOW (blocks a later step or checkpoint, or cheap: roughly
  30 minutes or 50 lines or less) → redo or arbiter-marked extra step in AMENDMENTS,
  never an edit to the locked block; ACCEPT → logged as `accepted by arbiter <date>:
  <reason>`, distinct from a human sign-off; ESCALATE → halt the feature with a
  summary. Escalation triggers: a dependency not on the approved list; contradicting
  `docs/decisions.md` or needing one of its open items settled; any change under
  `web/` or a breaking change to `docs/api-contract.md`; spending money beyond a test
  call (RapidAPI pulls, persona batch, Mubit training starts); a missing secret; the
  same step failing review 3 times.
- Eye test replaced by a qa-gate smoke check, recorded as "not human-verified".
- qa-gate raised to Opus.
- `safe-merge.sh`: the only route to `main`. Refuses unless every box is ticked, a
  qa-gate PASS is recorded, the PR title is in format, and the diff stays inside the
  owner's paths. Squash-merges with the PR title as message and an empty body, deletes
  the branch. `git push` to `main` and `--force` denied.
- step-reviewer stays the only ticker; step-order hook and both commit guards
  unchanged. PR bodies carry no attribution.

### Source

This session's conversation, quoted above. `.claude/` kit and `docs/decisions.md` on
`main` at `628a2c7`.

### Explicitly out of scope

- Any backend feature work (B1–B7). This feature only changes the kit.
- Changing `block-direct-commit.sh`, `pre-commit-guard.sh`, `check-step-order.sh` or
  `safe-commit.sh`.
- Frontend files, Yewen's progress files, `docs/api-contract.md`.
- CI, branch protection rules, notifications.
- Removing the human-approval path: with `Autonomy: off` (or unset) the kit behaves
  exactly as before.

---

## AMENDMENTS

_None._

---

## RULES IN FORCE

| Rule | Source | Applies to |
| ---- | ------ | ---------- |
| Plain British English, banned words list | `.claude/CLAUDE.md` Language and tone | docs, agent and skill text, commits, PRs |
| Commits only via `safe-commit.sh`, title only, no signature | `.claude/CLAUDE.md` Committing | commits |
| No scope creep, no new dependencies, no speculative generalisation | `.claude/CLAUDE.md` Standing prohibitions 1, 2, 4 | code, kit files |
| Ladder: write as little as possible | `.claude/CLAUDE.md` The ladder | code, kit files |
| `type(scope): message`, scopes from kit-config (`kit`) | `.claude/CLAUDE.md`, `.claude/kit-config.md` | commits, PR titles |
| PR body problem and solution only, no attribution | `.claude/skills/pr-description/SKILL.md` | PRs |
| Human's answers 1–4 above | this session | kit files, repo settings |

---

## PLAN

### Step 1 — Autonomy switch and house rules

**Goal**: Add the `Autonomy` setting and approved-dependency list to kit-config, and
state in CLAUDE.md what autonomous mode changes and what it never changes.

**Files in scope**: `.claude/kit-config.md`, `.claude/CLAUDE.md`

**Done when**: kit-config has `Autonomy: on` and `Approved dependencies: fastapi,
google-genai, pytest`; CLAUDE.md's commit-approval line, prohibition 2 and the
tradeoff/sign-off rules each say how autonomy changes them, and name the arbiter and
its escalation triggers; nothing else in CLAUDE.md changes.

**Evidence location**: the diff

- [x] Implemented — diff of .claude/CLAUDE.md and .claude/kit-config.md vs 628a2c7 (2026-10-24)
- [x] Tested — evidence: cd web && npm test exit 0; check-process-refs.sh exit 0; no code changed (2026-10-24)
- [x] Best practices met — evidence: no banned words; arbiter escalation triggers and unchanged guards stated in CLAUDE.md Autonomous mode (2026-10-24)
- [x] Matches locked requirements — evidence: kit-config Autonomy on + approved deps; CLAUDE.md commit line, prohibition 2, Autonomous mode section with FIX_NOW/ACCEPT/ESCALATE and all 6 triggers (2026-10-24)
- [x] No scope drift — evidence: git diff --stat shows only the two declared files (2026-10-24)

### Step 2 — Arbiter agent and qa-gate on Opus

**Goal**: Add the `arbiter` subagent and raise qa-gate to Opus with an autonomous-mode
smoke check in place of the eye test.

**Files in scope**: `.claude/agents/arbiter.md`, `.claude/agents/qa-gate.md`

**Done when**: `arbiter.md` has frontmatter (`model: opus`, read-only tools), takes a
progress file plus items, returns FIX_NOW / ACCEPT / ESCALATE per item with the
criteria and triggers from the requirements, and writes ACCEPT markers in the stated
form; qa-gate uses `model: opus` and, when autonomy is on, treats arbiter-accepted
tradeoffs as signed and runs a smoke check recorded as not human-verified.

**Evidence location**: the diff

- [ ] Implemented
- [ ] Tested — evidence: (date)
- [ ] Best practices met — evidence: (date)
- [ ] Matches locked requirements — evidence: (date)
- [ ] No scope drift — evidence: (date)

### Step 3 — Skills honour the switch

**Goal**: feature-kickoff, commit-workflow, pr-description and feature-wrapup skip the
human gates when autonomy is on and route decisions to the arbiter instead.

**Files in scope**: `.claude/skills/feature-kickoff/SKILL.md`,
`.claude/skills/commit-workflow/SKILL.md`, `.claude/skills/pr-description/SKILL.md`,
`.claude/skills/feature-wrapup/SKILL.md`

**Done when**: each skill has a short "When autonomy is on" section saying which gate
is replaced and by what; feature-wrapup ends by pushing, opening the PR and calling
`safe-merge.sh`; with autonomy off each skill reads as before.

**Evidence location**: the diff

- [ ] Implemented
- [ ] Tested — evidence: (date)
- [ ] Best practices met — evidence: (date)
- [ ] Matches locked requirements — evidence: (date)
- [ ] No scope drift — evidence: (date)

### Step 4 — safe-merge.sh and permissions

**Goal**: Add the merge script and the push/PR permissions.

**Files in scope**: `.claude/scripts/safe-merge.sh`, `.claude/settings.json`

**Done when**: `safe-merge.sh <pr-number>` refuses (non-zero, reason printed) on: an
unticked box in the branch's progress file, no qa-gate PASS recorded, a bad PR title,
a changed file outside the allowed paths, a PR not targeting `main`; otherwise
squash-merges with the PR title as subject and an empty body and deletes the branch.
`bash -n` passes and each refusal path is exercised. settings.json allows
`git push -u origin <feature branch>`, `gh pr create`, `gh pr view` and the script;
denies push to `main` and force pushes.

**Evidence location**: `evidence/kit-autonomy/safe-merge-checks.md`

- [ ] Implemented
- [ ] Tested — evidence: (date)
- [ ] Best practices met — evidence: (date)
- [ ] Matches locked requirements — evidence: (date)
- [ ] No scope drift — evidence: (date)

### Step 5 — GitHub repo settings

**Goal**: Make the shared repo squash-only with PR title as message, empty body and
branch deletion on merge.

**Files in scope**: `evidence/kit-autonomy/repo-settings.md`

**Done when**: `gh api repos/illumnagentic/nightshift-build` shows
`allow_merge_commit=false`, `allow_rebase_merge=false`, `allow_squash_merge=true`,
`squash_merge_commit_title=PR_TITLE`, `squash_merge_commit_message=BLANK`,
`delete_branch_on_merge=true`; before and after values recorded in the evidence file.

**Evidence location**: `evidence/kit-autonomy/repo-settings.md`

- [ ] Implemented
- [ ] Tested — evidence: (date)
- [ ] Best practices met — evidence: (date)
- [ ] Matches locked requirements — evidence: (date)
- [ ] No scope drift — evidence: (date)

---

## TRADEOFFS

_None logged._

---

## SPOTTED, NOT FIXED

- PR #7 (`feat/web-shell`) merged as a merge commit "Merge pull request #7", against
  the squash decision in `docs/decisions.md`. Already on `main`; not rewritten. Step 5
  stops it recurring. | low

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
