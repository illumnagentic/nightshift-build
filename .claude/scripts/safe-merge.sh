#!/usr/bin/env bash
#
# safe-merge.sh — the only permitted way for the agent to merge a pull request.
#
# Refuses unless: the PR is open and targets the target branch (kit-config, else
# origin/HEAD, else main); the title is in commit format; the progress file on the PR
# branch has every PLAN box ticked and a recorded "QA-GATE: PASS"; nothing but the
# progress file and the plan file changed after that PASS; every changed file is inside
# the paths the progress file declares; and, in feature mode, the human has approved
# the PR's head commit (kit-approve.sh). Then squash-merges with the PR title as
# subject, an empty body, and deletes the branch.
#
# Usage:
#   safe-merge.sh 12
#   safe-merge.sh 12 --check-only      # run the checks, do not merge
#
# Exit codes: 0 ok, 1 bad usage, 2 a check refused, 3 merge failed.

set -euo pipefail

VALID_TYPES="fix|feat|docs|style|refactor|perf|test|build|ci"
MAX_LEN=72

die() { printf 'safe-merge: %s\n' "$1" >&2; exit "${2:-1}"; }
refuse() { die "$1" 2; }

pr=""
check_only=0
while [ $# -gt 0 ]; do
  case "$1" in
    --check-only) check_only=1; shift ;;
    -h|--help)
      sed -n '3,17p' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    -*) die "unknown option: $1" ;;
    *)  [ -n "$pr" ] && die "unexpected extra argument: $1"
        pr="$1"; shift ;;
  esac
done

[[ "$pr" =~ ^[0-9]+$ ]] || die "usage: safe-merge.sh <pr-number> [--check-only]"
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "not inside a git repository"

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$here/kit-py.sh"
[ "${#KIT_PY[@]}" -gt 0 ] || die "Python 3 is needed (tried python3, python, py -3)"
target="$("$here/kit-conf.sh" get "Target branch" 2>/dev/null | tr -d '`' || true)"
if [ -z "$target" ] || [ "$target" = auto ]; then
  target="$(git symbolic-ref -q refs/remotes/origin/HEAD 2>/dev/null || true)"
  target="${target##*/}"
fi
target="${target:-main}"
msg="$("$here/kit-conf.sh" check "Plan file" 2>/dev/null || true)"
[ -z "$msg" ] || refuse "$msg"
plan="$("$here/kit-conf.sh" ticks "Plan file" 2>/dev/null | head -n1 || true)"
plan="${plan:-docs/plan.md}"
mode="$("$here/kit-mode.sh" status 2>/dev/null | awk '{print $1}' || true)"

# --- PR state ----------------------------------------------------------------
json="$(gh pr view "$pr" --json state,baseRefName,headRefName,headRefOid,title,files)" \
  || die "could not read PR #${pr}"
field() { printf '%s' "$json" | kit_py -I -c 'import json,sys; print(json.load(sys.stdin)[sys.argv[1]])' "$1"; }

state="$(field state)"
base="$(field baseRefName)"
head="$(field headRefName)"
oid="$(field headRefOid)"
title="$(field title)"
changed="$(printf '%s' "$json" | kit_py -I -c 'import json,sys; print("\n".join(f["path"] for f in json.load(sys.stdin)["files"]))')"

[ "$state" = "OPEN" ] || refuse "PR #${pr} is ${state}, not OPEN"
[ "$base" = "$target" ] || refuse "PR #${pr} targets ${base}, not ${target}"

# --- Title: same rules as safe-commit.sh --------------------------------------
printf '%s' "$title" | grep -Eq "^(${VALID_TYPES})(\([a-z0-9._/-]+\))?!?: .+$" \
  || refuse "title must be 'type(scope): message' with type one of: ${VALID_TYPES//|/, }
  got: ${title}"
[ "${#title}" -le "$MAX_LEN" ] || refuse "title is ${#title} characters, limit is ${MAX_LEN}: ${title}"
subject_msg="${title#*: }"
case "$subject_msg" in *.) refuse "title must not end with a full stop" ;; esac
if printf '%s' "$subject_msg" | LC_ALL=C grep -q '^[A-Z]'; then
  refuse "title message must be lowercase: ${subject_msg}"
fi

# --- Progress file on the PR head ----------------------------------------------
git fetch --quiet origin "+refs/heads/${head}:refs/remotes/origin/${head}" \
  || die "could not fetch ${head} from origin" 3
git cat-file -e "${oid}^{commit}" 2>/dev/null || refuse "head commit ${oid} not found after fetch"

matches=()
while IFS= read -r p; do
  [ -n "$p" ] || continue
  if git show "${oid}:${p}" | grep -Fx -- "- **Branch**: ${head}" >/dev/null; then matches+=("$p"); fi
done < <(git ls-tree -r --name-only "$oid" -- .claude/progress/ | grep '\.md$' || true)

[ "${#matches[@]}" -ge 1 ] || refuse "no progress file on ${head} declares '- **Branch**: ${head}'"
[ "${#matches[@]}" -le 1 ] || refuse "more than one progress file declares branch ${head}: ${matches[*]}"
progress="${matches[0]}"
content="$(git show "${oid}:${progress}")"

# --- Every PLAN box ticked -----------------------------------------------------
open_boxes="$(printf '%s\n' "$content" | awk '
  /^## /        { inplan = ($0 ~ /^## PLAN/); next }
  inplan && /^### / { step = $0 }
  inplan && /^- \[ \]/ { print step " :: " $0 }')"
[ -z "$open_boxes" ] || refuse "unticked PLAN boxes:
${open_boxes}"
printf '%s\n' "$content" | grep '^- \[x\]' >/dev/null || refuse "no ticked boxes found in ${progress}"

# --- QA-GATE: PASS in VERIFICATION ----------------------------------------------
verification="$(printf '%s\n' "$content" | awk '/^## /{v = ($0 ~ /^## VERIFICATION/); next} v')"
printf '%s\n' "$verification" | grep -E '^(\*\*)?QA-GATE: PASS' | grep -v 'PASS WITH FINDINGS' >/dev/null \
  || refuse "no 'QA-GATE: PASS' line in VERIFICATION of ${progress}"

# --- No code change after the QA-GATE PASS --------------------------------------
# Only the progress file and the plan file may change after the commit that recorded PASS.
pass_commit="$(git log -1 --format=%H -G'^(\*\*)?QA-GATE: PASS( [^W]|$)' "$oid" -- "$progress")"
[ -n "$pass_commit" ] || refuse "cannot find the commit that recorded 'QA-GATE: PASS' in ${progress}"
code_commit="$(git log -1 --format=%H "$oid" -- . ":(exclude)${progress}" ":(exclude)${plan}")"
if [ -n "$code_commit" ] && ! git merge-base --is-ancestor "$code_commit" "$pass_commit"; then
  refuse "files other than ${progress} and ${plan} changed after QA-GATE: PASS (commit ${code_commit})"
fi

# --- Changed files inside declared scope ---------------------------------------
# Entries: backticked paths on "**Files in scope**:", "**Files**:" and "**Evidence location**:" lines and the
# lines that continue them (up to a blank line or the next bold/heading line).
entries="$(printf '%s\n' "$content" | awk '
  /^(- )?\*\*(Files( in scope)?|Evidence location)\*\*:/ { on = 1; print; next }
  /^[[:space:]]*$|^\*\*|^#|^- \*\*/  { on = 0 }
  on' | grep -o '`[^`]*`' | tr -d '`' || true)"

allowed() {
  local f="$1" e
  [ "$f" = "$progress" ] || [ "$f" = "$plan" ] && return 0
  while IFS= read -r e; do
    [ -n "$e" ] || continue
    # A bare suffix such as `.uid` ("`main.gd` and its `.uid`") extends every other
    # entry: it allows <entry><suffix>, as well as a file named exactly the suffix.
    case "$e" in */*) ;; .?*)
      [[ "$f" == ?*"$e" ]] && grep -Fqx -- "${f%"$e"}" <<< "$entries" && return 0 ;;
    esac
    case "$e" in
      */) [[ "$f" == "$e"* ]] && return 0 ;;
      *\**) [[ "$f" == $e ]] && return 0 ;;
      *)  [ "$f" = "$e" ] && return 0 ;;
    esac
  done <<< "$entries"
  return 1
}

bad=""
while IFS= read -r f; do
  [ -n "$f" ] || continue
  allowed "$f" || bad+="  ${f}"$'\n'
done <<< "$changed"
[ -z "$bad" ] || refuse "files outside the declared scope:
${bad%$'\n'}"

# --- Feature mode: the human approved this head --------------------------------------
if [ "$mode" = feature ]; then
  "$here/kit-approve.sh" --check "$head" "$oid" >/dev/null 2>&1 \
    || refuse "feature mode: ${head} has no valid human approval (kit-approve.sh) for its current head"
fi

if [ "$check_only" -eq 1 ]; then
  echo "ok: all checks passed"
  exit 0
fi

# --- Merge ---------------------------------------------------------------------
gh pr merge "$pr" --squash --subject "$title" --body "" --delete-branch --match-head-commit "$oid" \
  || die "merge of PR #${pr} failed" 3
gh pr view "$pr" --json mergeCommit,state
