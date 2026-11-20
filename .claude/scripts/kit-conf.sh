#!/usr/bin/env bash
#
# kit-conf.sh — read a value from .claude/kit-config.md.
#
# Usage:
#   kit-conf.sh get <Key>       the text after "- **<Key>**:", HTML comments removed
#   kit-conf.sh ticks <Key>     each `backticked` part of that value, one per line
#
# Only the key's own line is read. A missing key, or one holding only a comment,
# prints nothing and exits 0. KIT_CONFIG overrides the file path (used by tests).
#
# Exit codes: 0 ok, 1 bad usage or no config file.

set -euo pipefail

usage() { printf 'usage: kit-conf.sh get|ticks <Key>\n' >&2; exit 1; }
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
  *)     usage ;;
esac
