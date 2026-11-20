---
name: feature-kickoff
description: Plan a feature and create its locked progress file before any code is written. Use whenever starting work on a feature, or any change that will take more than one step. Triggers on "let's build", "implement", "add support for", "start working on", "new feature".
---

# Feature kickoff

No code is written before this runs. Not a line, not a scaffold, not a "quick start".

A change that meets the `quick-change` eligibility is offered that lane first, in step
mode. Anything else comes here.

## 1. Understand before planning

Read `.claude/CLAUDE.md` and `.claude/kit-config.md` first.

Then explore the codebase enough to plan honestly — where this change lands, what it
touches, what already exists that does something similar. Delegate broad searching to
the `Explore` agent rather than doing it in the main context.

List the rules that apply to this feature and where each comes from: the dev kit
(`.claude/CLAUDE.md`), repo conventions (CONTRIBUTING.md, linters, tests that enforce
style), client or product rules (e.g. house style enforced in code, tool or connector
instructions), and the human's own instructions. For each, record which artefacts it
governs (generated product output, code, comments, docs, commits).

If the repo names a requirements source in kit-config (a PRD directory, ticket system),
read the relevant document now.

## 2. Ask, do not assume

If any of these is unclear, ask the human before planning. One round of questions, all
of them together.

- What is the actual outcome wanted, in terms of what someone can do afterwards?
- What is explicitly out of scope?
- Are there constraints not stated — compatibility, performance, deadline, a shape the
  solution has to fit?
- What does "done" mean to you?

If the human's request is already precise, do not manufacture questions.

## 3. Create the progress file

Slug the feature name: lowercase, hyphens. Create `.claude/progress/<slug>.md` from
`.claude/templates/progress-template.md`.

Fill in:

- `BRANCH` — `git rev-parse --abbrev-ref HEAD`.
- `BASE_SHA` — `git rev-parse HEAD`. This is the pointer everything is diffed against
  later. Stamp it before any code exists, or it is worthless.
- `REQUIREMENTS (LOCKED)` — the human's requirements, in their words. Quote them.
  Do not tidy, do not improve the wording, do not merge in your own assumptions. If
  you are summarising a longer document, quote the binding lines verbatim and cite it.
- `Explicitly out of scope` — what was ruled out. Be generous here; it is cheap now
  and expensive later.
- `RULES IN FORCE` — the listing from section 1, one row per rule: the rule, its
  source, what it applies to.

If the working tree is dirty, say so and ask whether to commit or stash first. A dirty
tree makes BASE_SHA meaningless.

## 4. Plan the steps

Break the work into steps that are each independently reviewable. A step is too big if
its diff would take more than a few minutes to read. Too small if it cannot be
reviewed against a requirement on its own.

For each step, write into the file:

- **Goal** — one sentence.
- **Files in scope** — the specific paths it may touch. Be precise. This list is the
  trip wire that catches sprawl later, so a lazy `src/**` defeats the purpose. If you
  genuinely cannot predict a path, say so in the step rather than widening the glob.
  Put each path in backticks. A bare suffix extends the other paths on the list:
  "`player.gd` and its `.uid`" allows `player.gd` and `player.gd.uid`.
- **Done when** — an observable condition, not "implemented correctly". If the step
  shows a list, deck or paged view, the condition goes past the first batch. If the
  step relies on a rule another step introduced, restate that rule here.
- **Acceptance examples** - for a step that changes behaviour, 2 to 4 named cases:
  a concrete input, the expected result, and the path it runs on (real data, demo
  backend, fake). Write them after drafting the steps. A step with nothing to assert
  (a measurement, docs) has none: leave the field out.
- **Evidence location** — where evidence for this step lives. Durable: in the repo, or
  a location the human names. Never only a session scratch area. "The diff" is fine
  where the diff is the evidence.
- The five checkboxes, all unticked.

**Real data.** Where **Real data** in kit-config is set and a step changes behaviour on
that data, run the current code on it once now, before the plan is shown. Take at least
one example from what it actually did. Record figures and outcomes in the progress file,
never raw records. Where **Real data** is blank or absent, say so in one line and skip
this.

The human eye test belongs in VERIFICATION at wrap-up, not in a step's done-when. A
reviewer cannot tick a box that waits on the human.

Order steps so each leaves the repo in a working state. If that is impossible, say so
explicitly rather than pretending otherwise.

Use the `Plan` agent for the decomposition if the feature is large — it keeps the
architectural thinking out of the main context.

**Plan review.** In every mode, before the plan is shown to the human (in auto mode,
before it is locked), send the `plan-reviewer` subagent the progress file path
(`Progress file: .claude/progress/<slug>.md`) and nothing else. Fix the plan from its
findings. Then write one line under `## PLAN`, so the record outlives the session:
`**Plan review**: <n> findings; fixed: <which, how>; left: <which, why>` (or
`**Plan review**: no findings`). In auto mode a finding left unfixed is not yours to
waive: it goes to the `arbiter` (see By mode).

## 5. Gitignore

Check **Progress files** in `.claude/kit-config.md`.

- `committed`: leave `.claude/.gitignore` as it is. It un-ignores `progress/`, and the
  progress file is committed with the work it tracks.
- `ignored` or unset: ensure `.claude/.gitignore` exists and contains `progress/`. The
  progress file is a working document, not a deliverable. If the human explicitly says
  this feature's progress file should be committed, add an exception for that one
  file — `!progress/<slug>.md` — and nothing else.

## 6. Show it and get agreement

Show the human the plan: steps, file scopes, acceptance examples, RULES IN FORCE, and
what you have ruled out of scope. Also show what the plan reviewer raised, what changed,
and any finding you left alone and why. The human confirms RULES IN FORCE before the
plan is locked. Ask them to confirm the plan before implementation starts. Never fold
a new capability into a table or list the human approves as a whole. Each new
capability is asked as its own question with a yes/no. This is the last cheap moment
to correct a misunderstanding.

Once they confirm, the requirements block is locked. From this point it changes only
by explicit instruction, appended to AMENDMENTS with the date and never by rewriting
the original.

## Then

Hand each step to the `implementer` subagent one at a time, and each finished step to
`step-reviewer`, including steps with no diff. Never run the next step before the
current one passes review. Never implement in the main context yourself. The loop is
"One step" in `## Modes` of `.claude/CLAUDE.md`; `.claude/scripts/kit-state.sh brief
<n>` gives the start of each brief.

After each step is committed, tell the human they can `/clear` and say "continue" to
start the next step with a fresh context.

Every step brief starts with the header: `PROGRESS: .claude/progress/<slug>.md`, then
`STEP: <n>` or `REDO OF STEP <n>`. Briefs cite rules from RULES IN FORCE. The redo rule
is in `.claude/CLAUDE.md`, and `.claude/hooks/check-step-order.sh` enforces the order.

## By mode

Run `.claude/scripts/kit-mode.sh status`. Step mode is everything above. Otherwise see
`## Modes` in `.claude/CLAUDE.md`, and:

**Both feature and auto mode**

- **Requirements (sections 2 and 3).** Quote `REQUIREMENTS (LOCKED)` from the feature's
  line in the **Plan file** and the binding lines of the **Binding documents** named in
  kit-config, plus any human instruction. No plan file configured: say so and stop.
- **Branch.** Create the branch the plan line names (else `feat/<slug>`) from an
  up-to-date target branch (`git switch <target> && git pull --ff-only && git switch -c
  <branch>`) before stamping `BASE_SHA`.
- Write `- **Mode**: <mode> (<date>)` in the header.
- **Dirty working tree.** Stop. Do not commit or stash someone else's changes.
- Commit the progress file through `safe-commit.sh` as `docs(kit): record <slug> plan`
  when **Progress files** is `committed`.

**Feature mode** (interactive, with the human)

- Section 2 questions are asked as usual, but only where the plan line and binding
  documents leave a real gap.
- Section 6 runs as usual: the human approves the plan, RULES IN FORCE and each new
  capability. Then write `- **Plan approved**: <date> (human, in chat)` in the header.
  Never write that line without the human's yes in this conversation.
- Then tell them the plan is locked and they can run `.claude/scripts/kit-drive.sh` to
  build it, one fresh session per step, or carry on here.

**Auto mode** (run by `kit-drive.sh`)

- Do not ask the section 2 questions. Anything ambiguous goes to the `arbiter`. On
  ESCALATE, write the `ESCALATED (arbiter)` line and stop.
- Section 6 approval is skipped. Instead, check yourself that every locked requirement
  is served by a step (the plan reviewer does not check this), and run the plan review
  in section 4. Fix what you can; every finding you leave unfixed goes to the `arbiter`
  in one call, as items for `kickoff`, and its rulings stand. A new capability, or a
  dependency not on the approved list, is an ESCALATE.
- Stop after the progress file is committed. The driver starts step 1 in a fresh
  session.
