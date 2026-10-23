#!/usr/bin/env bash
#
# pre-commit-guard — git-level backstop, installed as .git/hooks/pre-commit.
#
# The Claude Code hook blocks `git commit` at the tool layer. This catches the routes
# that hook cannot see: a script the agent wrote, a language runtime calling git, a
# subagent. If an agent commits without going through safe-commit.sh, it is rejected.
#
# YOU ARE NOT THE TARGET. By default this only rejects commits made from inside a
# Claude Code session. Your own `git commit`, commitizen (`cz commit`, `git cz`), your
# IDE's commit button, `git rebase`, `git merge` and CI all pass straight through.
#
# Modes — set with:  git config kit.commitguard <mode>
#
#   agent   (default) reject only commits made from inside a Claude Code session
#   strict            reject every commit that did not come through safe-commit.sh,
#                     including your own. Use if you want the format enforced on
#                     humans too. Escape hatch below still works.
#   off               do nothing
#
# Escape hatch in any mode:
#
#   SAFE_COMMIT_OVERRIDE=1 git commit -m "..."
#   git commit --no-verify -m "..."
#
# Any pre-commit hook that existed before the kit was installed is chained below,
# so your linting still runs.

set -uo pipefail

mode="$(git config --get kit.commitguard 2>/dev/null || true)"
[ -n "$mode" ] || mode="agent"

run_chained() {
  chained="$(dirname "$0")/pre-commit.kit-chained"
  [ -x "$chained" ] && { "$chained" "$@" || exit $?; }
  exit 0
}

[ "$mode" = "off" ] && run_chained "$@"

# Sanctioned route, or a human who has explicitly overridden.
[ "${SAFE_COMMIT_TOKEN:-}" = "1" ] && run_chained "$@"
[ "${SAFE_COMMIT_OVERRIDE:-}" = "1" ] && run_chained "$@"

# Is this commit being made from inside an agent session?
agent_session=0
[ -n "${CLAUDECODE:-}" ] && agent_session=1
[ -n "${CLAUDE_CODE_ENTRYPOINT:-}" ] && agent_session=1

if [ "$mode" = "agent" ] && [ "$agent_session" -eq 0 ]; then
  # A human at a terminal, an IDE, CI, or a rebase. Not our business.
  run_chained "$@"
fi

cat >&2 <<'EOF'

  REJECTED: this commit did not come through safe-commit.sh.

  Commits in this repository are created by:

      .claude/scripts/safe-commit.sh "type(scope): message"

  That is what keeps commit messages to a title with no body, and therefore free of
  agent signatures and session links.

  If you are a person reading this in your own terminal, either of these gets you
  through, and neither is cheating:

      SAFE_COMMIT_OVERRIDE=1 git commit -m "..."
      git commit --no-verify -m "..."

  If it is blocking you repeatedly, the guard is in the wrong mode. Check it with:

      git config kit.commitguard

  'agent' (the default) blocks only commits made from inside a Claude Code session.
  'off' disables it entirely.

EOF
exit 1
