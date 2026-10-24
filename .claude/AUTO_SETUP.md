# Full automation: setup and maintenance

For Claude. Read this before changing the mode layer or setting it up on a new machine.
What the modes do is in `.claude/CLAUDE.md` under `## Modes`. Do not repeat it here.

## A. Updating the kit

The mode layer is these files:

- `.claude/scripts/autonomy.sh` — reads, sets and clears the per-laptop switch.
- `.claude/hooks/autonomy-guard.sh` — the PreToolUse guard.
- `.claude/scripts/safe-merge.sh` — the only route to `main`.
- `.claude/settings.json` — deny and ask rules, hook registration.
- `.claude/.gitignore` — keeps the switch file out of git.
- `.claude/agents/arbiter.md`, `.claude/agents/qa-gate.md`.
- The `## Modes` section of `.claude/CLAUDE.md`, and the full-automation sections of the
  skills `feature-kickoff`, `commit-workflow`, `pr-description`, `feature-wrapup`.
- `.claude/kit-config.md` holds only the approved dependency list.

Rules:

1. A kit change is a feature. Run `feature-kickoff` first, like any other change.
2. Edits to the settings files, the hooks, `autonomy.sh` and `safe-merge.sh` raise a
   permission prompt by design. Never route around it. The human approves it.
3. The guard rejects any non-markdown file that names the switch file. Do not write
   scripts, tests or config that mention it. Markdown, `settings.json`, the hooks,
   `autonomy.sh` and `safe-merge.sh` are exempt.
4. Never turn full automation on to make a kit change easier.

Re-testing after a change:

- Guard: feed it a tool call as JSON on stdin, with `CLAUDE_PROJECT_DIR` pointing at a
  scratch copy of `.claude/` outside the repo. The live guard blocks every
  `autonomy.sh on` except the exact canonical command, including a scratch copy's, and
  blocks any spelling built to get past it. Never split, quote or build the switch name
  to get past the guard. To test the switch-present (allow) path, ask the human to run
  `<scratch-copy>/.claude/scripts/autonomy.sh on` in their own terminal, and `... off`
  afterwards. Do not exercise the allow path yourself. Check the exit code and stdout: exit 2 is a
  block, JSON with `allow` or `ask` is a decision, no output is no decision. Cover both
  modes, every deny (push to `main`, force, `gh pr merge`, merge API) and every allow.
- `safe-merge.sh`: put stub `gh` and `git` executables first on `PATH` that print canned
  JSON, then run it with `--check-only` against each refusal path (unticked box, no
  `QA-GATE: PASS`, bad title, file outside scope, base not `main`).
- The harnesses are not in the repo. Write them in the session scratchpad. Keep the
  results (commands, inputs, decisions) in `evidence/<slug>/`, as in
  `evidence/kit-autonomy/`.

## B. Using it on another machine

1. Clone the repo. Have `git` and `python3` on `PATH`; the guard and `safe-merge.sh`
   need both.
2. Install the commit guard as described in `.claude/README.md`.
3. Run `gh auth login` with an account whose token can merge PRs on this repo.
4. Check the GitHub repo settings match `evidence/kit-autonomy/repo-settings.md`:
   `gh api repos/illumnagentic/nightshift-build` should show squash merge only, PR title
   as message, blank body, delete branch on merge.
5. The switch is off on every machine after a clone. Check with
   `.claude/scripts/autonomy.sh status`; it should print `off`.
6. Turn it on only when the human asks: confirm once in chat, then run exactly
   `.claude/scripts/autonomy.sh on` and let the human approve the prompt. Turn it off
   with one chat confirmation, then `.claude/scripts/autonomy.sh off`.
7. If the hooks or prompts do not fire, restart Claude Code or reload the settings. The
   hooks are registered in `.claude/settings.json` and load at session start.
