---
name: feature-kickoff
description: Plan a feature and create its locked progress file before any code is written. Use whenever starting work on a feature, a bug fix of any size, or any change that will take more than one step. Triggers on "let's build", "implement", "add support for", "start working on", "new feature".
---

# Feature kickoff

No code is written before this runs. Not a line, not a scaffold, not a "quick start".

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
- **Done when** — an observable condition, not "implemented correctly".
- **Evidence location** — where evidence for this step lives. Durable: in the repo, or
  a location the human names. Never only a session scratch area. "The diff" is fine
  where the diff is the evidence.
- The five checkboxes, all unticked.

Order steps so each leaves the repo in a working state. If that is impossible, say so
explicitly rather than pretending otherwise.

Use the `Plan` agent for the decomposition if the feature is large — it keeps the
architectural thinking out of the main context.

## 5. Gitignore

Ensure `.claude/.gitignore` exists and contains `progress/`. The progress file is a
working document, not a deliverable.

If the human explicitly says this feature's progress file should be committed, add an
exception for that one file — `!progress/<slug>.md` — and nothing else.

## 6. Show it and get agreement

Show the human the plan: steps, file scopes, RULES IN FORCE, and what you have ruled
out of scope. The human confirms RULES IN FORCE before the plan is locked. Ask them to
confirm the plan before implementation starts. Never fold a new capability into a table
or list the human approves as a whole. Each new capability is asked as its own question
with a yes/no. This is the last cheap moment to correct a misunderstanding.

Once they confirm, the requirements block is locked. From this point it changes only
by explicit instruction, appended to AMENDMENTS with the date and never by rewriting
the original.

## Then

Hand each step to the `implementer` subagent one at a time, and each finished step to
`step-reviewer`, including steps with no diff. Never run the next step before the
current one passes review. Never implement in the main context yourself.

Every brief starts with the header: `PROGRESS: .claude/progress/<slug>.md`, then
`STEP: <n>` or `REDO OF STEP <n>`. Briefs cite rules from RULES IN FORCE. The redo rule
is in `.claude/CLAUDE.md`, and `.claude/hooks/check-step-order.sh` enforces the order.
