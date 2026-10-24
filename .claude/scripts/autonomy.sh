#!/usr/bin/env bash
#
# autonomy.sh — read or change this laptop's autonomy switch.
#
# Usage:
#   autonomy.sh status    prints "on (since <date>)" or "off"
#   autonomy.sh on        creates the switch file, holding today's date
#   autonomy.sh off       removes the switch file
#
# Turning it on needs two human confirmations: a chat confirmation first, then the
# harness permission prompt that a settings rule raises for the exact command
# `.claude/scripts/autonomy.sh on`. Turning it off needs one.
#
# The switch is a gitignored file, so it is per laptop and off by default. The guard
# hook refuses every other way of writing or deleting it.
#
# Exit codes: 0 ok, 1 bad usage.

set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
switch="$root/.claude/.autonomy"

case "${1:-}" in
  status)
    if [ -f "$switch" ]; then
      printf 'on (since %s)\n' "$(cat "$switch")"
    else
      printf 'off\n'
    fi ;;
  on)
    date +%Y-%m-%d > "$switch"
    printf 'on (since %s)\n' "$(cat "$switch")" ;;
  off)
    rm -f "$switch"
    printf 'off\n' ;;
  *)
    printf 'usage: autonomy.sh status|on|off\n' >&2
    exit 1 ;;
esac
