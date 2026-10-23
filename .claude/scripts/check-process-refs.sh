#!/usr/bin/env bash
#
# check-process-refs.sh — flags references to the development process in added code.
#
# Usage:
#   check-process-refs.sh [BASE]
#
# BASE defaults to the output of kit-context.sh --base. It must be a commit.
#
# Scans lines added relative to BASE in the working tree (staged or not), plus every
# line of untracked, non-ignored files. Binary files and paths under .claude/ are skipped.
# Matches are case-insensitive, except AMENDMENTS, which is all caps:
#   Step <n>, AMENDMENTS, progress file, requirements document, per the brief,
#   implementer, step-reviewer, qa-gate, .claude/, dev kit
#
# Output: one "path:line: text" per hit, then "PROCESS REFS: <n> found" or "PROCESS REFS: none".
# Exit: 0 none found, 1 hits found, 2 usage or git error.

set -euo pipefail

[ "$#" -le 1 ] || { echo "usage: check-process-refs.sh [BASE]" >&2; exit 2; }

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
  echo "check-process-refs: not inside a git repository" >&2; exit 2; }
cd "$(git rev-parse --show-toplevel)"

if [ "$#" -eq 1 ]; then
  base="$1"
else
  base="$("$(dirname "$0")/kit-context.sh" --base)" || {
    echo "check-process-refs: could not determine BASE" >&2; exit 2; }
fi
git rev-parse --verify --quiet "${base}^{commit}" >/dev/null 2>&1 || {
  echo "check-process-refs: not a valid commit: ${base}" >&2; exit 2; }

# Emit added lines as: path <TAB> line <TAB> text
added_lines() {
  git -c core.quotepath=off diff -U0 --no-color --no-ext-diff --no-renames "$base" \
      -- . ':(exclude).claude' |
    awk '
      /^diff --git / { inhdr = 1; file = ""; next }
      inhdr && /^\+\+\+ / {
        file = substr($0, 5); sub(/\t.*$/, "", file)
        if (file == "/dev/null") file = ""; else sub(/^b\//, "", file)
        next
      }
      /^@@ / {
        inhdr = 0
        if (match($0, /\+[0-9]+/)) ln = substr($0, RSTART + 1, RLENGTH - 1) + 0
        next
      }
      !inhdr && file != "" && /^\+/ { printf "%s\t%d\t%s\n", file, ln, substr($0, 2); ln++ }
    '
  git -c core.quotepath=off ls-files --others --exclude-standard | while IFS= read -r f; do
    case "$f" in .claude/*) continue ;; esac
    [ -f "$f" ] || continue
    grep -Iq . "$f" 2>/dev/null || continue
    F="$f" awk '{ printf "%s\t%d\t%s\n", ENVIRON["F"], FNR, $0 }' "$f"
  done
}

hits="$(added_lines | awk '
  {
    i = index($0, "\t"); path = substr($0, 1, i - 1); rest = substr($0, i + 1)
    j = index(rest, "\t"); ln = substr(rest, 1, j - 1); text = substr(rest, j + 1)
    low = tolower(text)
    w = "(^|[^a-z0-9_])"; e = "([^a-z0-9_]|$)"
    if (low ~ (w "step [0-9]+") || text ~ /AMENDMENTS/ ||
        low ~ /progress file/ || low ~ /requirements doc(ument)?/ || low ~ /per the brief/ ||
        low ~ (w "implementer" e) || low ~ /step-reviewer/ || low ~ /qa-gate/ ||
        low ~ /\.claude\// || low ~ /dev kit/)
      printf "%s:%s: %s\n", path, ln, text
  }
')"

if [ -z "$hits" ]; then
  echo "PROCESS REFS: none"
  exit 0
fi
printf '%s\n' "$hits"
echo "PROCESS REFS: $(printf '%s\n' "$hits" | wc -l | tr -d ' ') found"
exit 1
