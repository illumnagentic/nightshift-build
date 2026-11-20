#!/usr/bin/env bash
#
# kit-precheck.sh — the mechanical part of the feature gate. Run it before briefing
# qa-gate: if it fails, qa-gate would fail too, and costs far more to find out.
#
# Usage:
#   kit-precheck.sh [<progress>] [--no-tests]
#
# Checks, against the progress file and the working tree:
#   1. every PLAN box is ticked, and every tick carries a (YYYY-MM-DD) date;
#   2. step order: no step's earliest tick is before an earlier step's latest tick;
#   3. every Evidence location that is a path exists;
#   4. every changed file since BASE_SHA is inside a declared scope (Files in scope,
#      Files and Evidence location lines), the progress file or the plan file;
#   5. TRADEOFFS and SPOTTED entries all carry a verdict (in step mode this is a NOTE:
#      the human signs at wrap-up, after qa-gate);
#   6. check-process-refs.sh exits 0;
#   7. kit-escalate-check.sh is clear;
#   8. kit-test.sh all passes (cached when the tree is unchanged). --no-tests skips it.
#
# Output: "FAIL: ..." and "NOTE: ..." lines, then "PRECHECK: PASS" or
# "PRECHECK: FAIL (<n>)".
#
# Exit codes: 0 pass, 1 bad usage, 2 a check failed, 3 an escalation trigger fired.

set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "kit-precheck: not inside a git repository" >&2; exit 1; }
cd "$root" || exit 1

progress=""; tests=1
for a in "$@"; do
  case "$a" in
    --no-tests) tests=0 ;;
    -*) echo "usage: kit-precheck.sh [<progress>] [--no-tests]" >&2; exit 1 ;;
    *) progress="$a" ;;
  esac
done
[ -n "$progress" ] || progress="$("$here/kit-state.sh" find)"
[ -n "$progress" ] && [ -r "$progress" ] || { echo "kit-precheck: no progress file" >&2; exit 1; }

mode="$("$here/kit-mode.sh" status | awk '{print $1}')"
base="$(grep -m1 -oE '\*\*BASE_SHA\*\*:[[:space:]]*[0-9a-f]{7,40}' "$progress" | grep -oE '[0-9a-f]{7,40}$' || true)"
git cat-file -e "${base}^{commit}" 2>/dev/null || { echo "kit-precheck: BASE_SHA '$base' is not a commit" >&2; exit 1; }
plan="$("$here/kit-conf.sh" ticks "Plan file" 2>/dev/null | head -n1 || true)"

fails=0
fail() { printf 'FAIL: %s\n' "$1"; fails=$((fails + 1)); }
note() { printf 'NOTE: %s\n' "$1"; }

# --- 1 and 2: boxes, dates, order ------------------------------------------------------
while IFS= read -r line; do fail "$line"; done < <(awk '
  /^## / { inplan = ($0 ~ /^## PLAN/); next }
  inplan && /^###[[:space:]]+Step[[:space:]]+[0-9]+/ { s = $0; sub(/^###[[:space:]]+Step[[:space:]]+/, "", s); n = s + 0; next }
  inplan && n != "" && /^[[:space:]]*- \[ \]/ { print "step " n " has an unticked box: " $0 }
  inplan && n != "" && /^[[:space:]]*- \[[xX]\]/ {
    if (match($0, /[0-9]{4}-[0-9]{2}-[0-9]{2}/)) {
      d = substr($0, RSTART, RLENGTH)
      if (!(n in lo) || d < lo[n]) lo[n] = d
      if (!(n in hi) || d > hi[n]) hi[n] = d
      order[n] = 1
    } else print "step " n " has a tick with no date: " $0
  }
  END {
    m = 0; for (k in order) keys[++m] = k + 0
    for (i = 1; i <= m; i++) for (j = i + 1; j <= m; j++) if (keys[j] < keys[i]) { t = keys[i]; keys[i] = keys[j]; keys[j] = t }
    for (i = 2; i <= m; i++) if (lo[keys[i]] < hi[keys[i-1]])
      print "step " keys[i] " was ticked (" lo[keys[i]] ") before step " keys[i-1] " finished (" hi[keys[i-1]] ")"
  }' "$progress")

# --- 3: evidence paths ------------------------------------------------------------------
while IFS= read -r e; do
  [ -n "$e" ] || continue
  case "$e" in *" "*|"the diff") continue ;; esac
  [ -e "$e" ] || fail "evidence path does not exist: $e"
done < <(awk '/^\*\*Evidence location\*\*:/' "$progress" | grep -o '`[^`]*`' | tr -d '`')

# --- 4: scope ---------------------------------------------------------------------------
scope="$("$here/kit-state.sh" scope "$progress")"
in_scope() {
  local f="$1" e
  [ "$f" = "$progress" ] || { [ -n "$plan" ] && [ "$f" = "$plan" ]; } && return 0
  while IFS= read -r e; do
    [ -n "$e" ] || continue
    case "$e" in
      */) [[ "$f" == "$e"* ]] && return 0 ;;
      *\**) [[ "$f" == $e ]] && return 0 ;;
      *) [ "$f" = "$e" ] && return 0 ;;
    esac
  done <<< "$scope"
  return 1
}
while IFS= read -r f; do
  [ -n "$f" ] || continue
  in_scope "$f" || fail "changed file outside every declared scope: $f"
done < <( { git diff --name-only "$base"; git ls-files --others --exclude-standard; } | sort -u)

# --- 5: ledger --------------------------------------------------------------------------
unsigned="$("$here/kit-state.sh" unsigned "$progress")"
if [ -n "$unsigned" ]; then
  n="$(printf '%s\n' "$unsigned" | grep -c .)"
  if [ "$mode" = step ]; then
    note "$n ledger entr$( [ "$n" -eq 1 ] && echo y || echo ies) wait for the human sign-off at wrap-up"
  else
    fail "$n ledger entr$( [ "$n" -eq 1 ] && echo y || echo ies) have no arbiter verdict:"
    printf '%s\n' "$unsigned" | cut -c1-140 | sed 's/^/  /'
  fi
fi

# --- 6: process references ----------------------------------------------------------------
if [ -x "$here/check-process-refs.sh" ]; then
  out="$("$here/check-process-refs.sh" "$base" 2>&1)"; ec=$?
  [ "$ec" -eq 0 ] || { fail "check-process-refs.sh exit $ec"; printf '%s\n' "$out" | head -n 20 | sed 's/^/  /'; }
fi

# --- 7: escalation triggers ---------------------------------------------------------------
esc="$("$here/kit-escalate-check.sh" "$progress" 2>&1)"; esc_ec=$?
[ "$esc_ec" -eq 0 ] || printf '%s\n' "$esc"

# --- 8: tests ----------------------------------------------------------------------------
if [ "$tests" -eq 1 ]; then
  out="$("$here/kit-test.sh" all 2>&1)"; ec=$?
  printf '%s\n' "$out" | grep '^CHECK:' || true
  [ "$ec" -eq 0 ] || { fail "kit-test.sh all exit $ec"; printf '%s\n' "$out" | grep -v '^CHECK:' | tail -n 20; }
fi

if [ "$esc_ec" -eq 3 ]; then echo "PRECHECK: ESCALATE"; exit 3; fi
if [ "$fails" -gt 0 ]; then echo "PRECHECK: FAIL ($fails)"; exit 2; fi
echo "PRECHECK: PASS"
