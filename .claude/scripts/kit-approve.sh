#!/usr/bin/env bash
#
# kit-approve.sh — the human's approval of a built feature, in feature mode.
#
# The agent cannot run this: the guard hook blocks every form of it except --check and
# --status. Run it yourself, in a terminal or with the `!` prefix in Claude Code.
#
# Usage:
#   kit-approve.sh                 approve the current branch at its HEAD commit
#   kit-approve.sh --yes           the same, without the confirmation question
#   kit-approve.sh --check [<branch> [<sha>]]
#                                  exit 0 if the branch (at <sha>, default its local
#                                  head) has a valid approval
#   kit-approve.sh --status        list approvals on this laptop
#   kit-approve.sh --revoke [<branch>]
#
# An approval is valid while every commit after the approved one touches only the
# feature's progress file and the plan file. Any code change after approval voids it.
#
# Approving needs: a feature branch, a clean working tree, and a progress file whose
# phase is APPROVAL (every box ticked, QA-GATE: PASS recorded, nothing escalated).
# It records the approval in .claude/.approvals/ (gitignored, per laptop) and appends a
# HUMAN APPROVAL line to the progress file's VERIFICATION section.
#
# Exit codes: 0 ok / valid, 1 bad usage, 2 refused / not valid.

set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
die()    { printf 'kit-approve: %s\n' "$1" >&2; exit "${2:-1}"; }
refuse() { die "$1" 2; }

root="$(git rev-parse --show-toplevel 2>/dev/null)" || die "not inside a git repository"
cd "$root"
store="$root/.claude/.approvals"
record() { printf '%s/%s\n' "$store" "$(printf '%s' "$1" | tr '/' '_')"; }

current_branch() { git symbolic-ref --short -q HEAD || true; }

progress_for() {
  local f
  for f in .claude/progress/*.md; do
    [ -f "$f" ] && grep -Fqx -- "- **Branch**: $1" "$f" && { printf '%s\n' "$f"; return 0; }
  done
  return 0
}

plan_file() { "$here/kit-conf.sh" ticks "Plan file" 2>/dev/null | head -n1 || true; }

valid() {   # <branch> [<head sha>]; the head defaults to the local branch
  local branch="$1" rec sha head changed f progress plan
  rec="$(record "$branch")"
  [ -f "$rec" ] || { echo "no approval for $branch"; return 1; }
  read -r sha _ < "$rec"
  head="${2:-$(git rev-parse -q --verify "refs/heads/$branch" || true)}"
  [ -n "$head" ] || { echo "branch $branch not found"; return 1; }
  git merge-base --is-ancestor "$sha" "$head" 2>/dev/null ||
    { echo "approved commit ${sha:0:8} is not in $branch any more"; return 1; }
  progress="$(progress_for "$branch")"; plan="$(plan_file)"
  changed="$(git diff --name-only "$sha" "$head")"
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    [ "$f" = "$progress" ] || [ "$f" = "$plan" ] ||
      { echo "$f changed after approval at ${sha:0:8}"; return 1; }
  done <<< "$changed"
  echo "approved at ${sha:0:8}"
}

case "${1:-}" in
  --check)
    b="${2:-$(current_branch)}"; [ -n "$b" ] || die "no branch"
    valid "$b" ${3:+"$3"} || exit 2 ;;

  --status)
    [ -d "$store" ] || { echo "no approvals"; exit 0; }
    for r in "$store"/*; do [ -f "$r" ] && printf '%s: %s\n' "$(basename "$r" | tr '_' '/')" "$(cat "$r")"; done ;;

  --revoke)
    b="${2:-$(current_branch)}"; [ -n "$b" ] || die "no branch"
    rm -f "$(record "$b")"; echo "revoked: $b" ;;

  ""|--yes)
    b="$(current_branch)"
    [ -n "$b" ] || refuse "not on a branch"
    [ -z "$(git status --porcelain)" ] || refuse "working tree is dirty; approve a committed state"
    mode="$("$here/kit-mode.sh" status | awk '{print $1}')"
    [ "$mode" = feature ] || refuse "kit mode is $mode; approval is a feature-mode step"
    progress="$(progress_for "$b")"
    [ -n "$progress" ] || refuse "no progress file names branch $b"
    phase="$("$here/kit-state.sh" phase "$progress" | sed -n 's/^PHASE=//p')"
    [ "$phase" = APPROVAL ] || refuse "phase is $phase, not APPROVAL; the feature is not ready to approve"
    sha="$(git rev-parse HEAD)"

    "$here/kit-state.sh" summary "$progress"
    printf '\nArbiter rulings you are confirming:\n'
    grep -nE 'by arbiter' "$progress" | cut -c1-160 | sed 's/^/  /' || echo "  none"
    printf '\nApproving %s at %s means: you have read the handover, done the eye test,\n' "$b" "${sha:0:8}"
    printf 'and accept every arbiter ruling above. Push and PR become possible.\n'
    if [ "${1:-}" != --yes ]; then
      [ -t 0 ] || refuse "not a terminal; re-run with --yes"
      read -r -p "Approve? [y/N] " ans
      [ "$ans" = y ] || [ "$ans" = Y ] || refuse "not approved"
    fi

    mkdir -p "$store"
    printf '%s %s\n' "$sha" "$(date +%Y-%m-%d)" > "$(record "$b")"
    line="HUMAN APPROVAL: $(date +%Y-%m-%d) @${sha:0:12} — handover read, eye test done, arbiter rulings confirmed"
    awk -v line="$line" '
      (/^## / || /^---/) && inv && !done { print line; print ""; done = 1 }
      { print }
      /^## VERIFICATION/ { inv = 1 }
      END { if (!done) print line }' "$progress" > "$progress.tmp" && mv "$progress.tmp" "$progress"
    printf '\napproved: %s at %s\nThe progress file has the approval line; the agent commits it with the close-out.\n' "$b" "${sha:0:8}" ;;

  *)
    sed -n '3,24p' "$0" | sed 's/^# \{0,1\}//' >&2
    exit 1 ;;
esac
