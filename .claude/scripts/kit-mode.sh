#!/usr/bin/env bash
#
# kit-mode.sh — read or change this laptop's kit mode.
#
# Usage:
#   kit-mode.sh status     prints "step", "feature (since <date>)" or "auto (since <date>)"
#   kit-mode.sh step       back to the default: the human approves every step
#   kit-mode.sh feature    the agent builds a whole feature; the human approves it
#                          before anything is pushed
#   kit-mode.sh auto       full automation, merges included
#
# The mode lives in .claude/.kit-mode, a gitignored file, so it is per laptop and
# `step` by default. The guard hook refuses every other way of writing or deleting it.
#
# Moving to `feature` or `auto` needs two human confirmations: one in chat, then the
# permission prompt that a settings rule and the guard raise for the exact commands
# `.claude/scripts/kit-mode.sh feature` and `.claude/scripts/kit-mode.sh auto`.
# Moving back to `step` needs one.
#
# Exit codes: 0 ok, 1 bad usage.

set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
switch="$root/.claude/.kit-mode"

show() {
  if [ -f "$switch" ]; then
    read -r mode since < "$switch" || true
    case "$mode" in
      feature|auto) printf '%s (since %s)\n' "$mode" "${since:-unknown}" ;;
      *) printf 'step\n' ;;   # an unreadable switch is the safe mode
    esac
  else
    printf 'step\n'
  fi
}

case "${1:-}" in
  status) show ;;
  step)   rm -f "$switch"; show ;;
  feature|auto)
    printf '%s %s\n' "$1" "$(date +%Y-%m-%d)" > "$switch"
    show ;;
  *)
    printf 'usage: kit-mode.sh status|step|feature|auto\n' >&2
    exit 1 ;;
esac
