---
name: continue
description: Resume a feature from its progress file in a fresh context, after /clear or in a new session. Use when the human says "continue", "carry on", "next step", "resume", "where were we", or starts a session on a feature branch with work in progress.
---

# Continue

The progress file is the state. A fresh context needs nothing else, so do not ask the
human to recap.

## 1. Find where things stand

```
.claude/scripts/kit-state.sh phase
.claude/scripts/kit-state.sh summary
```

Do not read the whole progress file. `summary` gives the steps, the ledger counts,
escalations, follow-ups and QA runs. Read a section only when a decision needs it.

Tell the human in two or three lines: the feature, the mode, what is done, and what
comes next.

## 2. Act on the phase

- **KICKOFF**: no progress file names this branch. Ask what to build, then run
  `feature-kickoff`. On the target branch with a feature in flight elsewhere, say so.
- **PLAN_APPROVAL** (feature mode): show the plan and ask for approval, as in
  `feature-kickoff` section 6.
- **STEP**: run "One step" from `## Modes` in `.claude/CLAUDE.md` for step `STEP`.
  `FAILS` above 0, or a redo note under the step, means a redo: use
  `kit-state.sh brief <n> --redo`.
- **WRAPUP**: run `feature-wrapup`.
- **APPROVAL** (feature mode): the feature is built and passed qa-gate. Point the human
  at the HANDOVER and `.claude/scripts/kit-approve.sh`. Do nothing else until they have
  approved.
- **DELIVER**: step mode, the human decides about the PR; feature mode, the close-out
  in `feature-wrapup`; auto mode, let `kit-drive.sh` deliver or follow the same
  close-out.
- **HALT**: quote the `ESCALATED` line and ask the human to decide. Once they have,
  rewrite it as `RESOLVED (human) <date>: <their decision>` and carry on.
- **DONE**: say so.

## 3. After the step

When the step is committed, stop and tell the human they can `/clear` and say
"continue" for the next one. One step per context keeps every step's context small.
