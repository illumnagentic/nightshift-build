#!/usr/bin/env bash
#
# block-direct-commit.sh — Claude Code PreToolUse hook.
#
# Refuses any Bash tool call that runs `git commit` directly, and tells the agent
# what to do instead. This is the enforcement layer: CLAUDE.md and the skill are
# advice the model can talk itself out of, a blocked tool call is not.
#
# Registered in .claude/settings.json against the Bash tool.
#
# Protocol: reads the tool call as JSON on stdin. Exit 0 allows, exit 2 blocks and
# feeds stderr back to the agent as the reason.

set -uo pipefail

input="$(cat)"

# --- Extract the command field ----------------------------------------------
# python3 if available (correct JSON parsing), otherwise a good-enough fallback.
if command -v python3 >/dev/null 2>&1; then
  command_text="$(printf '%s' "$input" | python3 -c '
import json,sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
ti = d.get("tool_input") or {}
print(ti.get("command","") if isinstance(ti, dict) else "")
' 2>/dev/null)"
else
  command_text="$(printf '%s' "$input" | tr ',' '\n' | sed -n 's/.*"command"[[:space:]]*:[[:space:]]*"\(.*\)".*/\1/p' | head -1)"
fi

[ -n "${command_text:-}" ] || exit 0

# --- Normalise: split compound commands onto their own lines -----------------
# Catches `cd foo && git commit`, `x; git commit`, `(git commit)`, pipelines.
normalised="$(printf '%s' "$command_text" | sed -e 's/&&/\n/g' -e 's/||/\n/g' -e 's/;/\n/g' -e 's/|/\n/g' -e 's/(/\n/g' -e 's/`/\n/g' -e 's/\$(/\n/g')"

# --- Does any segment invoke `git commit`? -----------------------------------
# Allows for: sudo, leading env assignments, and git's own flags before the
# subcommand (git -C path commit, git --no-pager commit, ...).
# The flag group allows a flag optionally followed by its argument, so `git -C path
# commit` and `git -c user.name=x commit` are caught as well as the plain form.
# `git commit-graph write` is not a commit and is not matched.
pattern='^[[:space:]]*(sudo[[:space:]]+)?([A-Za-z_][A-Za-z0-9_]*=[^[:space:]]*[[:space:]]+)*git([[:space:]]+-{1,2}[^[:space:]]+([[:space:]]+[^-][^[:space:]]*)?)*[[:space:]]+commit([[:space:]]|$)'

if printf '%s\n' "$normalised" | grep -Eq "$pattern"; then
  cat >&2 <<'EOF'
BLOCKED: direct `git commit` is not permitted in this repository.

Commits here have a title and nothing else — no body, so no field in which an agent
signature, co-authorship trailer or session link can appear. That is enforced, not
requested.

Do this instead:

  1. Use the commit-workflow skill. It delegates the diff read to the commit-composer
     subagent, shows the human the drafted title and any concerns, and waits for
     approval.
  2. Then commit with the script:

       .claude/scripts/safe-commit.sh "type(scope): message"
       .claude/scripts/safe-commit.sh --breaking "type(scope): message"

Types: fix, feat, docs, style, refactor, perf, test, build, ci.

Do not attempt to work around this block — not with a wrapper script, not with a
language runtime calling git, not by setting SAFE_COMMIT_TOKEN yourself. A second
guard runs inside git and will reject those too. If the script refuses your title,
the title is wrong; fix it.
EOF
  exit 2
fi

exit 0
