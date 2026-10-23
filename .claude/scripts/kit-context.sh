#!/usr/bin/env bash
#
# kit-context.sh — prints the git facts the kit's agents need, in one call.
#
# Usage:
#   kit-context.sh            # branch, target, base sha, diff stats
#   kit-context.sh --base     # print just the base sha and exit
#
# Base resolution order:
#   1. BASE_SHA recorded in a .claude/progress/*.md file naming the current branch
#   2. Target branch set in .claude/kit-config.md
#   3. origin/HEAD, then main, then master, then develop
# Then: merge-base of that target and HEAD.

set -euo pipefail

base_only=0
[ "${1:-}" = "--base" ] && base_only=1

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
  echo "kit-context: not inside a git repository" >&2; exit 1; }

repo_root="$(git rev-parse --show-toplevel)"
branch="$(git rev-parse --abbrev-ref HEAD)"

# --- 1. stamped BASE_SHA from the progress file ------------------------------
base=""
base_source=""
progress_file=""
progress_dir="${repo_root}/.claude/progress"

if [ -d "$progress_dir" ]; then
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    if grep -Eq "^[-*[:space:]]*\*\*Branch\*\*:[[:space:]]*${branch}$" "$f" 2>/dev/null; then
      candidate="$(grep -Eo '\*\*BASE_SHA\*\*:[[:space:]]*[0-9a-f]{7,40}' "$f" | head -n1 | grep -Eo '[0-9a-f]{7,40}' || true)"
      if [ -n "$candidate" ] && git cat-file -e "${candidate}^{commit}" 2>/dev/null; then
        base="$candidate"
        base_source="stamped at kickoff in $(basename "$f")"
        progress_file="$f"
        break
      fi
    fi
  done < <(find "$progress_dir" -maxdepth 1 -name '*.md' -type f 2>/dev/null | sort)
fi

# --- 2 & 3. target branch, then merge-base -----------------------------------
target=""
if [ -z "$base" ]; then
  config="${repo_root}/.claude/kit-config.md"
  if [ -f "$config" ]; then
    configured="$(grep -Eo '^\*\*Target branch\*\*:[[:space:]]*\S+' "$config" 2>/dev/null | awk '{print $NF}' || true)"
    [ "$configured" = "auto" ] && configured=""
    target="$configured"
  fi

  if [ -z "$target" ]; then
    if head_ref="$(git symbolic-ref --quiet refs/remotes/origin/HEAD 2>/dev/null)"; then
      target="${head_ref#refs/remotes/origin/}"
    fi
  fi

  if [ -z "$target" ]; then
    for candidate in main master develop; do
      if git rev-parse --verify --quiet "$candidate" >/dev/null 2>&1 ||
         git rev-parse --verify --quiet "origin/${candidate}" >/dev/null 2>&1; then
        target="$candidate"; break
      fi
    done
  fi

  [ -n "$target" ] || { echo "kit-context: could not determine a target branch. Set it in .claude/kit-config.md" >&2; exit 1; }

  target_ref="$target"
  git rev-parse --verify --quiet "$target_ref" >/dev/null 2>&1 || target_ref="origin/${target}"

  base="$(git merge-base "$target_ref" HEAD 2>/dev/null || true)"
  [ -n "$base" ] || { echo "kit-context: no merge base between ${target_ref} and HEAD" >&2; exit 1; }
  base_source="merge-base with ${target_ref}"
fi

if [ "$base_only" -eq 1 ]; then
  printf '%s\n' "$base"
  exit 0
fi

# --- Report ------------------------------------------------------------------
printf 'BRANCH: %s\n' "$branch"
printf 'TARGET: %s\n' "${target:-n/a (stamped base)}"
printf 'BASE: %s\n' "$base"
printf 'BASE_SOURCE: %s\n' "$base_source"
printf 'PROGRESS_FILE: %s\n' "${progress_file:-none}"
printf 'WORKING_TREE: %s\n' "$([ -n "$(git status --porcelain)" ] && echo dirty || echo clean)"
printf '\nCOMMITS ON BRANCH:\n'
git log "${base}..HEAD" --oneline || true
printf '\nDIFF STAT (%s...HEAD):\n' "${base:0:8}"
git diff "${base}...HEAD" --stat || true
printf '\nUNCOMMITTED:\n'
git status --porcelain || true
