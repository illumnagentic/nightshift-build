#!/usr/bin/env bash
#
# kit-escalate-check.sh — the escalation triggers a script can check, so the arbiter
# only gets the ones that need judgement.
#
# Usage:
#   kit-escalate-check.sh [<progress>]
#
# Compares the working tree (committed, staged, unstaged and untracked) with the
# progress file's BASE_SHA, and reports:
#   - a changed file under an **Escalate paths** entry in kit-config;
#   - an added dependency line in a manifest that names nothing on the
#     **Approved dependencies** list;
#   - something that looks like a secret in an added line;
#   - a test skipped in an added line, or a test file deleted;
#   - a step with **Max review fails** (default 3) or more REVIEW FAIL lines;
#   - an Escalate paths, Approved dependencies or Dependency manifests line with text
#     but nothing in backticks, which would otherwise read as empty and turn the
#     check off.
#
# Output: one "ESCALATE: <reason>" line per finding, then "ESCALATE-CHECK: clear" or
# "ESCALATE-CHECK: <n> finding(s)".
#
# In step mode the same findings are concerns to show the human before a commit.
#
# Exit codes: 0 clear, 1 bad usage, 3 findings.

set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "kit-escalate-check: not inside a git repository" >&2; exit 1; }
cd "$root" || exit 1
conf() { "$here/kit-conf.sh" "$@" 2>/dev/null || true; }

progress="${1:-$("$here/kit-state.sh" find)}"
[ -n "$progress" ] && [ -r "$progress" ] || { echo "kit-escalate-check: no progress file" >&2; exit 1; }
base="$(grep -m1 -oE '\*\*BASE_SHA\*\*:[[:space:]]*[0-9a-f]{7,40}' "$progress" | grep -oE '[0-9a-f]{7,40}$' || true)"
git cat-file -e "${base}^{commit}" 2>/dev/null || { echo "kit-escalate-check: BASE_SHA '$base' is not a commit" >&2; exit 1; }

findings=0
flag() { printf 'ESCALATE: %s\n' "$1"; findings=$((findings + 1)); }

changed="$( { git diff --name-only "$base"; git ls-files --others --exclude-standard; } | sort -u)"
untracked="$(git ls-files --others --exclude-standard)"

# Added lines per file, as "<path>\t<line>". Untracked files count as wholly added.
added() {
  git diff -U0 "$base" -- "$@" | awk '
    /^\+\+\+ b\// { f = substr($0, 7); next }
    /^\+\+\+/     { f = ""; next }
    /^\+/ && f != "" { print f "\t" substr($0, 2) }'
  local u
  while IFS= read -r u; do
    [ -n "$u" ] || continue
    if [ $# -eq 0 ] || printf '%s\n' "$@" | grep -Fqx -- "$u"; then
      [ -f "$u" ] && grep -Iv '^$' "$u" 2>/dev/null | sed "s|^|$u\t|"
    fi
  done <<< "$untracked"
}

matches() {   # <file> <pattern>: dir/ prefix, glob, or exact path
  case "$2" in
    */) [[ "$1" == "$2"* ]] ;;
    *[\*\?]*) [[ "$1" == $2 ]] ;;
    *) [ "$1" = "$2" ] ;;
  esac
}

# --- Config lines the checks below depend on --------------------------------------
for key in "Escalate paths" "Approved dependencies" "Dependency manifests"; do
  msg="$(conf check "$key")"
  [ -z "$msg" ] || flag "$msg"
done

# --- Escalate paths --------------------------------------------------------------
while IFS= read -r pat; do
  [ -n "$pat" ] || continue
  while IFS= read -r f; do
    [ -n "$f" ] && matches "$f" "$pat" && flag "$f changed; it is under the escalate path \`$pat\`"
  done <<< "$changed"
done < <(conf ticks "Escalate paths")

# --- Dependencies ------------------------------------------------------------------
manifests="$(conf ticks "Dependency manifests")"
if [ -z "$manifests" ] || [ "$(conf get "Dependency manifests")" = auto ]; then
  manifests=$'package.json\npyproject.toml\nrequirements*.txt\ngo.mod\nCargo.toml\nGemfile\ncomposer.json'
fi
approved="$(conf ticks "Approved dependencies")"
manifest_files=()
while IFS= read -r f; do
  [ -n "$f" ] || continue
  while IFS= read -r m; do
    [ -n "$m" ] && [[ "$(basename "$f")" == $m || "$f" == $m ]] && { manifest_files+=("$f"); break; }
  done <<< "$manifests"
done <<< "$changed"
if [ "${#manifest_files[@]}" -gt 0 ]; then
  while IFS=$'\t' read -r f line; do
    [ -n "$line" ] || continue
    # A dependency line carries a version: 1.2, ^1, ~1, >=1, ==1, workspace:, a git URL,
    # or a go.mod "path vX".
    printf '%s' "$line" | grep -Eq '[0-9]+\.[0-9]+|["'\'' ][~^]|[<>=~!]=|workspace:|git\+|github:|[[:space:]]v[0-9]' || continue
    ok=0
    while IFS= read -r d; do
      [ -n "$d" ] && printf '%s' "$line" | grep -Fqi -- "$d" && { ok=1; break; }
    done <<< "$approved"
    [ "$ok" -eq 1 ] || flag "dependency line in $f is not on the approved list: $(printf '%s' "$line" | sed 's/^[[:space:]]*//' | cut -c1-120)"
  done < <(added "${manifest_files[@]}")
fi

# --- Secrets, skipped and deleted tests ----------------------------------------------
secret_re='-----BEGIN [A-Z ]*PRIVATE KEY-----|AKIA[0-9A-Z]{16}|\bsk-[A-Za-z0-9_-]{20,}|\bgh[pousr]_[A-Za-z0-9]{30,}|xox[baprs]-[A-Za-z0-9-]{10,}|AIza[0-9A-Za-z_-]{35}'
skip_re='\b(it|test|describe)\.skip\(|\bx(it|describe|test)\(|@pytest\.mark\.skip|@unittest\.skip|\bt\.Skip\(|#\[ignore\]|\.todo\('
while IFS=$'\t' read -r f line; do
  [ -n "$f" ] || continue
  case "$f" in .claude/*) continue ;; esac   # the kit's own docs name these patterns
  printf '%s' "$line" | grep -Eq -- "$secret_re" && flag "possible secret added in $f"
  printf '%s' "$line" | grep -Eq -- "$skip_re" && flag "test skipped in $f: $(printf '%s' "$line" | sed 's/^[[:space:]]*//' | cut -c1-100)"
done < <(added)
while IFS= read -r f; do
  [ -n "$f" ] || continue
  printf '%s' "$f" | grep -Eqi '(^|/)(tests?|spec|__tests__)/|[._-](test|spec)\.|(^|/)test_' && flag "test file deleted: $f"
done < <(git diff --name-only --diff-filter=D "$base")

# --- Repeated review failures --------------------------------------------------------
max="$(conf get "Max review fails" | grep -oE '^[0-9]+' || true)"; max="${max:-3}"
while IFS=$'\t' read -r n open done fails title; do
  [ "${fails:-0}" -ge "$max" ] && flag "step $n has failed review $fails times (limit $max)"
done < <("$here/kit-state.sh" steps "$progress" 2>/dev/null)

if [ "$findings" -eq 0 ]; then echo "ESCALATE-CHECK: clear"; exit 0; fi
echo "ESCALATE-CHECK: $findings finding(s)"
exit 3
