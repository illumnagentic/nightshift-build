#!/usr/bin/env bash
#
# kit-state.sh — read a feature's state from its progress file, so nobody has to read
# the whole file to know where things stand.
#
# Usage:
#   kit-state.sh find                 path of the progress file naming the current branch
#   kit-state.sh phase   [<progress>] machine-readable phase, as KEY=value lines
#   kit-state.sh summary [<progress>] one screen: steps, ledger, escalations, QA runs
#   kit-state.sh brief <n> [--redo] [<progress>]
#                                     the start of a step brief: header, the step block,
#                                     out of scope, and where the rules are
#   kit-state.sh scope   [<progress>] every declared path, one per line
#   kit-state.sh unsigned [<progress>] TRADEOFFS and SPOTTED entries with no verdict
#   kit-state.sh steps   [<progress>] "<n>\t<open>\t<ticked>\t<review fails>\t<title>" per step
#
# <progress> defaults to the file `find` prints. Paths are relative to the repo root.
#
# Markers this script reads (written by the agents, see .claude/CLAUDE.md):
#   - [ ] / - [x]                   step boxes under "### Step <n>" in ## PLAN
#   REVIEW FAIL <date>: ...         a failed step review, under the step (any case)
#   ESCALATED (arbiter) <date>: ... at the start of a line: the feature is halted.
#                                   The human resolves it by rewriting the line as
#                                   RESOLVED (human) <date>: <decision>
#   FOLLOW-UP (arbiter) <date>: ... something for a human that does not halt
#   QA-GATE: PASS <date> / QA-GATE: FAIL <date> @<sha>   in ## VERIFICATION
#   - **Plan approved**: <date>      header line; feature mode needs it before steps
#
# phase prints PHASE as one of:
#   KICKOFF        no progress file for this branch
#   HALT           an ESCALATED (arbiter) line is open (REASON=<the line>)
#   PLAN_APPROVAL  feature mode, and the plan has no "Plan approved" line yet
#   STEP           the first step with an unticked box (STEP=<n> FAILS=<review fails>)
#   WRAPUP         every box ticked, no QA-GATE: PASS yet (QA_FAILS=<n> QA_LAST_SHA=<sha>)
#   APPROVAL       feature mode, QA-GATE: PASS, no valid human approval (kit-approve.sh)
#   DELIVER        ready to push, open the PR and (auto mode) merge
#   DONE           the branch's PR is merged (checked with gh, if present)
# MODE=<step|feature|auto> is printed too.
#
# Exit codes: 0 ok, 1 bad usage or unreadable file.

set -euo pipefail

die() { printf 'kit-state: %s\n' "$1" >&2; exit 1; }

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(git rev-parse --show-toplevel 2>/dev/null)" || die "not inside a git repository"
cd "$root"
mode="$("$here/kit-mode.sh" status 2>/dev/null | awk '{print $1}')"
mode="${mode:-step}"

find_progress() {
  local branch f
  branch="$(git symbolic-ref --short -q HEAD || true)"
  [ -n "$branch" ] || return 0
  [ -d .claude/progress ] || return 0
  for f in .claude/progress/*.md; do
    [ -f "$f" ] || continue
    if grep -Fqx -- "- **Branch**: ${branch}" "$f"; then printf '%s\n' "$f"; return 0; fi
  done
}

progress_arg() {
  local p="${1:-}"
  [ -n "$p" ] || p="$(find_progress)"
  [ -n "$p" ] || return 0
  [ -r "$p" ] || die "cannot read progress file: $p"
  printf '%s\n' "$p"
}

field() { grep -m1 -E "^- \*\*$1\*\*:" "$2" | sed -E "s/^- \*\*$1\*\*:[[:space:]]*//" || true; }

# One line per step: "<n>\t<open boxes>\t<ticked boxes>\t<review fails>\t<title>"
steps() {
  awk '
    function flush() { if (n != "") printf "%s\t%d\t%d\t%d\t%s\n", n, open, done, fails, title }
    /^## /  { flush(); n = ""; inplan = ($0 ~ /^## PLAN/); next }
    inplan && /^###[[:space:]]+Step[[:space:]]+[0-9]+/ {
      flush()
      s = $0; sub(/^###[[:space:]]+Step[[:space:]]+/, "", s)
      n = s + 0; title = s; sub(/^[0-9]+[[:space:]]*(—|-|:)?[[:space:]]*/, "", title)
      open = 0; done = 0; fails = 0; next
    }
    n != "" && /^[[:space:]]*- \[ \]/ { open++ }
    n != "" && /^[[:space:]]*- \[[xX]\]/ { done++ }
    n != "" && tolower($0) ~ /^(\*\*)?review fail/ { fails++ }
    END { flush() }' "$1"
}

section() { awk -v h="$2" '/^## /{on = (index($0, "## " h) == 1); next} on' "$1"; }

escalations() { grep -E '^(\*\*)?ESCALATED \(arbiter\)' "$1" || true; }

# Entries in a ledger section with no verdict marker. An entry is a non-blank line that
# is not a comment or a placeholder.
unsigned_in() {
  section "$1" "$2" | awk '
    /^<!--/ { c = 1 } c { if ($0 ~ /-->/) c = 0; next }
    /^[[:space:]]*$/ || /^_None/ || /^---/ { next }
    tolower($0) ~ /accepted by|rejected by|signed by|fix_now by|escalated/ { next }
    { print }'
}

merged() {
  local branch="$1"
  command -v gh >/dev/null 2>&1 || return 1
  [ "$(gh pr list --head "$branch" --state merged --json number --jq length 2>/dev/null || echo 0)" -gt 0 ]
}

cmd="${1:-}"; shift || true
case "$cmd" in
  find)
    find_progress ;;

  phase)
    p="$(progress_arg "${1:-}")"
    branch="$(git symbolic-ref --short -q HEAD || echo DETACHED)"
    printf 'BRANCH=%s\nMODE=%s\n' "$branch" "$mode"
    if [ -z "$p" ]; then printf 'PHASE=KICKOFF\n'; exit 0; fi
    printf 'PROGRESS=%s\n' "$p"
    esc="$(escalations "$p" | head -n1)"
    if [ -n "$esc" ]; then
      printf 'PHASE=HALT\nREASON=%s\n' "$esc"; exit 0
    fi
    if [ "$mode" = feature ] && [ -z "$(field 'Plan approved' "$p")" ]; then
      printf 'PHASE=PLAN_APPROVAL\n'; exit 0
    fi
    first_open="$(steps "$p" | awk -F'\t' '$2 > 0 { print $1 "\t" $4; exit }')"
    if [ -n "$first_open" ]; then
      printf 'PHASE=STEP\nSTEP=%s\nFAILS=%s\n' "${first_open%%$'\t'*}" "${first_open##*$'\t'}"
      exit 0
    fi
    [ -n "$(steps "$p")" ] || { printf 'PHASE=HALT\nREASON=no steps under ## PLAN in %s\n' "$p"; exit 0; }
    verification="$(section "$p" VERIFICATION)"
    qa_fails="$(printf '%s\n' "$verification" | grep -cE '^(\*\*)?QA-GATE: FAIL' || true)"
    last_sha="$(printf '%s\n' "$verification" | grep -E '^(\*\*)?QA-GATE: FAIL' | tail -n1 | grep -oE '@[0-9a-f]{7,40}' | tr -d @ || true)"
    if printf '%s\n' "$verification" | grep -E '^(\*\*)?QA-GATE: PASS' | grep -qv 'PASS WITH FINDINGS'; then
      if merged "$branch"; then printf 'PHASE=DONE\n'
      elif [ "$mode" = feature ] && ! "$here/kit-approve.sh" --check "$branch" >/dev/null 2>&1; then
        printf 'PHASE=APPROVAL\n'
      else printf 'PHASE=DELIVER\n'; fi
    else
      printf 'PHASE=WRAPUP\nQA_FAILS=%s\nQA_LAST_SHA=%s\n' "$qa_fails" "$last_sha"
    fi ;;

  summary)
    p="$(progress_arg "${1:-}")"
    [ -n "$p" ] || { echo "no progress file names the current branch"; exit 0; }
    printf 'PROGRESS: %s\n' "$p"
    printf 'Kit mode: %s\n' "$mode"
    for k in Branch BASE_SHA Status Mode 'Plan approved'; do printf '%s: %s\n' "$k" "$(field "$k" "$p")"; done
    printf '\nSTEPS:\n'
    steps "$p" | awk -F'\t' '{
      state = ($2 == 0) ? "done" : (($3 == 0) ? "not started" : "open")
      printf "  %s. %s — %s (%d/%d)%s\n", $1, $5, state, $3, $2 + $3, ($4 > 0 ? ", review fails: " $4 : "") }'
    amend="$(section "$p" AMENDMENTS | grep -cE '^- ' || true)"
    printf '\nAMENDMENTS: %s\n' "$amend"
    printf 'UNSIGNED TRADEOFFS: %s\n' "$(unsigned_in "$p" TRADEOFFS | grep -c . || true)"
    printf 'UNSIGNED SPOTTED: %s\n' "$(unsigned_in "$p" "SPOTTED, NOT FIXED" | grep -c . || true)"
    printf 'ESCALATIONS:\n'; escalations "$p" | sed 's/^/  /'
    printf 'FOLLOW-UPS:\n'; grep -E '^(\*\*)?FOLLOW-UP \(arbiter\)' "$p" | sed 's/^/  /' || true
    printf 'QA RUNS:\n'; section "$p" VERIFICATION | grep -E '^(\*\*)?QA-GATE:' | sed 's/^/  /' || true ;;

  brief)
    n="${1:-}"; shift || true
    [[ "$n" =~ ^[0-9]+$ ]] || die "usage: kit-state.sh brief <n> [--redo] [<progress>]"
    redo=0
    if [ "${1:-}" = "--redo" ]; then redo=1; shift; fi
    p="$(progress_arg "${1:-}")"
    [ -n "$p" ] || die "no progress file names the current branch"
    block="$(awk -v n="$n" '
      /^## / { on = 0 }
      /^###[[:space:]]+Step[[:space:]]+[0-9]+/ { s = $0; sub(/^###[[:space:]]+Step[[:space:]]+/, "", s); on = (s + 0 == n) }
      on && !/^[[:space:]]*- \[[ xX]\]/' "$p")"
    [ -n "$block" ] || die "no '### Step $n' in $p"
    printf 'PROGRESS: %s\n' "$p"
    if [ "$redo" -eq 1 ]; then printf 'REDO OF STEP %s\n' "$n"; else printf 'STEP: %s\n' "$n"; fi
    printf '\nThe step, quoted from the progress file:\n\n%s\n' "$block"
    printf '\nExplicitly out of scope, quoted:\n\n%s\n' \
      "$(awk '/^### Explicitly out of scope/{on=1; next} /^#/{on=0} on' "$p" | sed '/^[[:space:]]*$/d')"
    printf '\nRead REQUIREMENTS (LOCKED) and RULES IN FORCE in %s before starting.\n' "$p"
    printf 'Branch base: %s\n' "$(field BASE_SHA "$p")" ;;

  scope)
    p="$(progress_arg "${1:-}")"
    [ -n "$p" ] || exit 0
    # Same rule as safe-merge.sh: backticked paths on Files / Files in scope /
    # Evidence location lines and the lines that continue them.
    awk '
      /^(- )?\*\*(Files( in scope)?|Evidence location)\*\*:/ { on = 1; print; next }
      /^[[:space:]]*$|^\*\*|^#|^- \*\*/ { on = 0 }
      on' "$p" | grep -o '`[^`]*`' | tr -d '`' | LC_ALL=C sort -u || true ;;

  steps)
    p="$(progress_arg "${1:-}")"
    [ -n "$p" ] || exit 0
    steps "$p" ;;

  unsigned)
    p="$(progress_arg "${1:-}")"
    [ -n "$p" ] || exit 0
    unsigned_in "$p" TRADEOFFS | sed 's/^/TRADEOFFS: /'
    unsigned_in "$p" "SPOTTED, NOT FIXED" | sed 's/^/SPOTTED: /' ;;

  *)
    sed -n '3,42p' "$0" | sed 's/^# \{0,1\}//' >&2
    exit 1 ;;
esac
