#!/usr/bin/env bash
#
# kit-conf.sh — read a value from .claude/kit-config.md.
#
# Usage:
#   kit-conf.sh get <Key>       the text after "- **<Key>**:", HTML comments removed
#   kit-conf.sh ticks <Key>     each `backticked` part of that value, one per line
#   kit-conf.sh check <Key>     for keys whose entries must be backticked: exit 2, with
#                               a message on stdout, when the value has text but no
#                               backticked part (and is not "auto")
#
# Only the key's own line is read. A missing key, or one holding only a comment,
# prints nothing and exits 0. KIT_CONFIG overrides the file path (used by tests).
#
# `ticks` on a value with no backticks prints nothing, the same as an empty value. A
# caller that would treat that as "nothing configured" runs `check` first, so a
# forgotten pair of backticks fails instead of silently turning the setting off.
#
# Exit codes: 0 ok, 1 bad usage or no config file, 2 `check` found an unticked value.

set -euo pipefail

usage() { printf 'usage: kit-conf.sh get|ticks|check <Key>\n' >&2; exit 1; }
[ $# -eq 2 ] || usage

if [ -n "${KIT_CONFIG:-}" ]; then
  cfg="$KIT_CONFIG"
else
  root="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "kit-conf: not in a git repository" >&2; exit 1; }
  cfg="$root/.claude/kit-config.md"
fi
[ -r "$cfg" ] || { echo "kit-conf: no config at $cfg" >&2; exit 1; }

value="$(awk -v key="- **$2**:" '
  index($0, key) == 1 {
    v = substr($0, length(key) + 1)
    while (match(v, /<!--.*-->/)) v = substr(v, 1, RSTART - 1) substr(v, RSTART + RLENGTH)
    sub(/<!--.*/, "", v)
    gsub(/^[ \t]+|[ \t]+$/, "", v)
    print v
    exit
  }' "$cfg")"

case "$1" in
  get)   [ -z "$value" ] || printf '%s\n' "$value" ;;
  ticks) printf '%s' "$value" | grep -o '`[^`]*`' | tr -d '`' || true ;;
  check)
    case "$value" in ''|auto|*'`'*'`'*) ;; *)
      printf '**%s** in .claude/kit-config.md has text but nothing in backticks: put each entry in backticks\n' "$2"
      exit 2 ;;
    esac ;;
  *)     usage ;;
esac
