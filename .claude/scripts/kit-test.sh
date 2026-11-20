#!/usr/bin/env bash
#
# kit-test.sh — run the repo's configured checks, and reuse a result when nothing has
# changed since it was produced.
#
# Usage:
#   kit-test.sh [test|lint|typecheck|build|all] [--fresh]     default: test
#
# Commands come from the Test, Lint, Typecheck and Build lines of
# .claude/kit-config.md (every backticked part, run in order from the repo root).
#
# A result is keyed by the working tree's content (tracked and untracked files that git
# does not ignore) plus the command. If a run with the same key exists, its exit code
# and log are reported without running again. --fresh always runs. Ignored files such
# as .env or a local database are not in the key: use --fresh when the result depends
# on them.
#
# Cache: <git dir>/kit-test-cache/ — inside .git, so it is never committed and does not
# change the tree it describes.
#
# Prints one line per check:
#   CHECK: <kind> exit=<n> cached=<yes|no> tree=<short> log=<path>
# and the last 40 lines of the log for a failure.
#
# A line with text but no backticked command (e.g. `- **Lint**: npm run lint`) is
# reported as a failure, never as "not configured".
#
# Exit codes: 0 every configured check passed (or none configured), 1 bad usage,
# 2 a command line has text but no backticked command, otherwise the first failing
# check's exit code.

set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "kit-test: not inside a git repository" >&2; exit 1; }
cd "$root" || exit 1

what="test"; fresh=0
for a in "$@"; do
  case "$a" in
    --fresh) fresh=1 ;;
    test|lint|typecheck|build|all) what="$a" ;;
    *) echo "usage: kit-test.sh [test|lint|typecheck|build|all] [--fresh]" >&2; exit 1 ;;
  esac
done

cache="$(git rev-parse --absolute-git-dir)/kit-test-cache"
mkdir -p "$cache"

# Tree of the working copy, through a throwaway index so the real one is untouched.
tmp_index="$(mktemp)"
trap 'rm -f "$tmp_index"' EXIT
# No index yet (a repo with no commits): remove the empty temp file so git starts a new
# index there. git rejects an empty file as a corrupt index.
cp "$(git rev-parse --git-path index)" "$tmp_index" 2>/dev/null || rm -f "$tmp_index"
tree="$(GIT_INDEX_FILE="$tmp_index" git add -A . >/dev/null 2>&1 && GIT_INDEX_FILE="$tmp_index" git write-tree)" ||
  { echo "kit-test: could not compute the working tree" >&2; exit 1; }

run_kind() {
  local kind="$1" label cmds key log ec cached
  case "$kind" in test) label=Test ;; lint) label=Lint ;; typecheck) label=Typecheck ;; build) label=Build ;; esac
  cmds="$("$here/kit-conf.sh" ticks "$label" 2>/dev/null || true)"
  if [ -z "$cmds" ]; then
    # Text with no backticked command is a broken config. Reporting it as "not
    # configured" would let a skipped check pass as green.
    if [ -n "$("$here/kit-conf.sh" get "$label" 2>/dev/null || true)" ]; then
      printf 'CHECK: %s has no backticked command in .claude/kit-config.md (%s): put the command in backticks\n' "$kind" "$label"
      return 2
    fi
    printf 'CHECK: %s not configured in .claude/kit-config.md\n' "$kind"
    return 0
  fi
  key="$(printf '%s\n%s\n%s\n' "$tree" "$kind" "$cmds" | git hash-object --stdin)"
  log="$cache/$key.log"
  if [ "$fresh" -eq 0 ] && [ -f "$cache/$key.exit" ]; then
    ec="$(cat "$cache/$key.exit")"; cached=yes
  else
    cached=no; ec=0
    : > "$log"
    while IFS= read -r c; do
      [ -n "$c" ] || continue
      printf '$ %s\n' "$c" >> "$log"
      (cd "$root" && bash -c "$c") >> "$log" 2>&1
      ec=$?
      printf '[exit %s]\n' "$ec" >> "$log"
      [ "$ec" -eq 0 ] || break
    done <<< "$cmds"
    printf '%s\n' "$ec" > "$cache/$key.exit"
  fi
  printf 'CHECK: %s exit=%s cached=%s tree=%s log=%s\n' "$kind" "$ec" "$cached" "${tree:0:12}" "$log"
  if [ "$ec" -ne 0 ]; then
    tail -n 40 "$log" | sed 's/^/  | /'
  fi
  return "$ec"
}

status=0
if [ "$what" = all ]; then kinds="test lint typecheck build"; else kinds="$what"; fi
for k in $kinds; do
  run_kind "$k"; ec=$?
  [ "$status" -ne 0 ] || status=$ec
done
exit "$status"
