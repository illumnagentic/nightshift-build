# Kit modes: setup and maintenance

For Claude and the human. Read this before turning on feature or auto mode on a
machine, or before changing the mode layer. What each mode does is in
`.claude/CLAUDE.md` under `## Modes`. It is not repeated here.

## A. Turning a mode on

1. Fill in the "Full automation" section of `.claude/kit-config.md`. Both modes need
   **Plan file**. Auto mode also needs **Progress files**: `committed`. Set
   **Escalate paths**, **Approved dependencies** and **Always escalate** for this repo;
   the defaults escalate very little.
2. Have `git`, Python 3 and `gh` on `PATH` (on Windows, Git Bash too: see README,
   "Windows and macOS"), and `gh auth login` with an account that
   can open PRs (and merge them, for auto mode).
3. For auto mode, check the GitHub repo merges the way `safe-merge.sh` expects: squash
   merge allowed, delete branch on merge. `gh api repos/<owner>/<repo>` shows it.
4. The mode is `step` on every machine after a clone. Check with
   `.claude/scripts/kit-mode.sh status`.
5. Turn it on only when the human asks: confirm once in chat, then run exactly
   `.claude/scripts/kit-mode.sh feature` (or `auto`) and let the human approve the
   prompt. Back to the default: one chat confirmation, then
   `.claude/scripts/kit-mode.sh step`.
6. If the hooks or prompts do not fire, restart Claude Code. Hooks and permissions in
   `.claude/settings.json` load at session start.

## B. Running the driver

```
.claude/scripts/kit-drive.sh --dry-run   # what the next session would be
.claude/scripts/kit-drive.sh             # resume the feature on this branch
.claude/scripts/kit-drive.sh --next      # auto: start the next unticked plan line
.claude/scripts/kit-drive.sh --loop      # auto: carry on through the plan
```

Run it from a terminal, not from inside Claude Code. Each phase is a fresh
`claude -p` session with the model, permission mode and budget from kit-config. The run
log is `.claude/.drive/log.jsonl`: one line per session with cost, outcome and the
session's handover summary. `claude --resume <session id>` opens any session from it.

The driver stops, and runs **Notify command** if set, when:

- the feature is ready for the human (feature mode: after qa-gate passes);
- a session writes an `ESCALATED (arbiter)` line, or reports blocked without one;
- a session changes nothing, or changes kit files, the mode or the approvals;
- a session writes a line only the human writes (`**Plan approved**`,
  `RESOLVED (human)`, `HUMAN APPROVAL:`) or removes an `ESCALATED (arbiter)` line;
- a phase needs more than **Max sessions per phase** sessions, or the run passes
  **Run budget (USD)**.

To resume after a halt: fix the cause (for an escalation, decide, and rewrite the line
as `RESOLVED (human) <date>: <decision>`), then run the driver again. If a run was
killed, remove `.claude/.drive/lock`.

**Permission mode.** `auto` lets the harness approve routine calls while the kit's
guard still blocks the dangerous ones. `dontAsk` runs only what settings allow: add
allow rules for the repo's test and build commands first, or every step stalls.
`bypassPermissions` skips Claude Code's checks entirely; the guard hooks still run, but
use it only in a sandbox.

## C. Feature mode, end to end

1. In an interactive session: "start <feature> from the plan". Kickoff asks what it
   must, shows the plan, and writes `Plan approved` once you agree.
2. In a terminal: `.claude/scripts/kit-drive.sh`. It runs each step and the wrap-up in
   its own session, then stops and tells you the feature is ready.
3. Read the HANDOVER in the progress file, do the eye test, and read the provisional
   arbiter rulings (`kit-state.sh summary` counts them).
4. Approve: `.claude/scripts/kit-approve.sh` in a terminal, or
   `! .claude/scripts/kit-approve.sh --yes` in Claude Code (if that is blocked, use a
   terminal). The agent cannot run it.
5. In an interactive session: "deliver". It closes out, pushes and drafts the PR; you
   confirm `gh pr create` at the prompt. Merge it yourself, or ask for `safe-merge.sh`.

Any code change after step 4 voids the approval; run it again after re-checking.

## D. Changing the kit

The mode layer is:

- `.claude/scripts/kit-mode.sh`, `kit-approve.sh`, `kit-drive.sh`, `kit-state.sh`,
  `kit-escalate-check.sh`, `kit-precheck.sh`, `kit-test.sh`, `kit-conf.sh`,
  `safe-merge.sh`;
- `.claude/hooks/kit-guard.sh`;
- `.claude/settings.json` (deny and ask rules, hook registration) and
  `.claude/.gitignore` (the per-laptop state);
- `.claude/agents/arbiter.md`, the mode sections of `qa-gate.md` and `step-reviewer.md`,
  and of the skills `feature-kickoff`, `commit-workflow`, `pr-description`,
  `feature-wrapup`, `continue`;
- the `## Modes` section of `.claude/CLAUDE.md`, and the "Full automation" section of
  `kit-config.md`.

Rules:

1. A kit change is a feature. Run `feature-kickoff` first, like any other change.
2. Change the kit in step mode. In feature and auto mode the guard makes settings,
   hooks and scripts read-only; in step mode editing them raises a permission prompt.
   Never route around either.
3. The guard rejects any non-markdown file that names the mode switch or the approval
   store. Do not write scripts or config that mention them; the kit's own scripts,
   hooks and settings are exempt.
4. The real source of these files is the kit repo. A change made inside a repo's
   `.claude/` is local until copied back; `kit-sync.sh` in the kit shows the drift.

Testing, from the kit repo:

```
tests/run.sh
```

It runs the script tests, the guard tests (every case in step, feature and auto mode,
inside and outside a driver session), the `safe-merge.sh` tests against stub `gh` and
`git`, and the driver tests against a stub `claude`. Extend them when you change the
guard, a script or the driver. Never exercise a real `kit-mode.sh feature|auto` or
`kit-approve.sh` from an agent session to test them; the tests build their own switch
files in scratch repos.
