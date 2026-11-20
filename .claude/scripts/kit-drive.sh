#!/usr/bin/env bash
#
# kit-drive.sh — run a feature as a chain of fresh Claude Code sessions, one per phase:
# kickoff, each step, wrap-up, delivery. Feature and auto mode only.
#
# Usage:
#   kit-drive.sh                    resume the feature on this branch, or the one in flight
#   kit-drive.sh --next             start the first unticked feature in the plan file
#   kit-drive.sh "<feature>"        start this feature (auto mode)
#   kit-drive.sh --loop             auto mode: after a merge, carry on with --next
#   kit-drive.sh --once             run one session, then stop
#   kit-drive.sh --dry-run          print what the next session would be, run nothing
#
# The progress file is the state. Before each session the driver asks kit-state.sh for
# the phase; it never takes a session's word for what happened. After each session it
# stops the run when:
#   - the session changed nothing (HEAD, working tree and progress file all the same);
#   - kit files, the mode switch or the approvals changed;
#   - a progress file gained a line only the human writes (**Plan approved**,
#     RESOLVED (human), HUMAN APPROVAL:) or lost an ESCALATED (arbiter) line;
#   - a phase has taken more than **Max sessions per phase** sessions;
#   - the run has spent more than **Run budget (USD)**;
#   - kit-state.sh reports HALT (an ESCALATED line) or the mode is no longer feature/auto.
#
# Feature mode: kickoff and plan approval happen with the human in an interactive
# session first. The driver runs the steps and the wrap-up, then stops at APPROVAL and
# notifies. Pushing, the PR and merging happen with the human after kit-approve.sh.
#
# Auto mode: the driver also runs kickoff and delivery (push, PR, safe-merge.sh).
#
# Settings come from the "Full automation" section of .claude/kit-config.md.
# Run log: .claude/.drive/log.jsonl. KIT_CLAUDE_BIN overrides the claude binary (tests).
#
# Exit codes: 0 finished or waiting for the human, 1 bad usage or setup, 3 halted.

set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "kit-drive: not inside a git repository" >&2; exit 1; }
cd "$root" || exit 1

die() { printf 'kit-drive: %s\n' "$1" >&2; exit 1; }
conf() { "$here/kit-conf.sh" "$@" 2>/dev/null || true; }
num() { local v; v="$(conf get "$1" | grep -oE '^[0-9]+(\.[0-9]+)?' || true)"; printf '%s' "${v:-$2}"; }

[ "${KIT_DRIVER:-}" != 1 ] || die "already inside a driver session"

feature=""; next=0; loop=0; once=0; dry=0
for a in "$@"; do
  case "$a" in
    --next) next=1 ;;
    --loop) loop=1; next=1 ;;
    --once) once=1 ;;
    --dry-run) dry=1 ;;
    -h|--help) sed -n '3,33p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*) die "unknown option: $a" ;;
    *) [ -z "$feature" ] || die "one feature at a time"; feature="$a" ;;
  esac
done

mode="$("$here/kit-mode.sh" status | awk '{print $1}')"
case "$mode" in feature|auto) ;; *) die "kit mode is '$mode'. The driver runs in feature or auto mode only" ;; esac
[ "$mode" = auto ] || [ "$loop" -eq 0 ] || die "--loop is auto mode only; each feature-mode plan needs the human's approval"
. "$here/kit-py.sh"
[ "${#KIT_PY[@]}" -gt 0 ] || die "Python 3 is needed (tried python3, python, py -3)"
claude_bin="${KIT_CLAUDE_BIN:-claude}"
command -v "$claude_bin" >/dev/null 2>&1 || die "cannot find $claude_bin"

plan="$(conf ticks "Plan file" | head -n1)"
[ -n "$plan" ] && [ -f "$plan" ] || die "set **Plan file** in .claude/kit-config.md to an existing file; $mode mode works from a plan"
if [ "$mode" = auto ] && [ "$(conf get "Progress files")" != committed ]; then
  die "auto mode needs **Progress files**: committed in kit-config (safe-merge.sh reads the progress file from the PR branch)"
fi

model="$(conf get "Driver model")"; model="${model:-opus}"
perm="$(conf get "Driver permission mode")"; perm="${perm:-auto}"
session_budget="$(num "Session budget (USD)" 5)"
run_budget="$(num "Run budget (USD)" 60)"
max_sessions="$(num "Max sessions per phase" 4)"
notify_cmd="$(conf ticks "Notify command" | head -n1)"
target="$(conf get "Target branch" | tr -d '`')"
if [ -z "$target" ] || [ "$target" = auto ]; then
  target="$(git symbolic-ref -q refs/remotes/origin/HEAD 2>/dev/null || true)"; target="${target##*/}"
fi
target="${target:-main}"

state_dir="$root/.claude/.drive"
mkdir -p "$state_dir"
if [ "$dry" -eq 0 ]; then
  mkdir "$state_dir/lock" 2>/dev/null || die "another kit-drive.sh holds $state_dir/lock (remove it if that run is dead)"
  trap 'rmdir "$state_dir/lock" 2>/dev/null' EXIT
fi
log="$state_dir/log.jsonl"
current="$state_dir/current"

notify() {
  printf '\n== %s\n' "$1"
  [ -z "$notify_cmd" ] || bash -c "$notify_cmd \"\$1\"" _ "$1" >/dev/null 2>&1 || true
}
halt() { notify "kit-drive halted: $1"; exit 3; }
finish() { notify "kit-drive: $1"; exit 0; }

digest() { git hash-object --stdin | cut -c1-16; }
guarded_hash() {
  find .claude/settings.json .claude/settings.local.json .claude/hooks .claude/scripts \
       .claude/.kit-mode .claude/.approvals "$(git rev-parse --git-path hooks)" \
       -type f 2>/dev/null | LC_ALL=C sort | while IFS= read -r f; do
    printf '%s %s\n' "$(git hash-object "$f")" "$f"
  done | digest
}
work_hash() {   # HEAD, the whole working tree (via a throwaway index) and progress files
  local idx tree
  idx="$(mktemp)"; cp "$(git rev-parse --git-path index)" "$idx" 2>/dev/null || true
  tree="$(GIT_INDEX_FILE="$idx" git add -A . >/dev/null 2>&1; GIT_INDEX_FILE="$idx" git write-tree 2>/dev/null)"
  rm -f "$idx"
  { git rev-parse HEAD 2>/dev/null; printf '%s\n' "$tree"; cat .claude/progress/*.md 2>/dev/null; } | digest
}

human_marks() {   # lines only the human writes, and open escalations, in every progress file
  cat .claude/progress/*.md 2>/dev/null |
    grep -E '^(\*\*)?(ESCALATED \(arbiter\)|RESOLVED \(human\)|HUMAN APPROVAL:)|^- \*\*Plan approved\*\*:' |
    LC_ALL=C sort || true
}

next_plan_item() {
  grep -m1 -E '^[[:space:]]*- \[ \] ' "$plan" | sed -E 's/^[[:space:]]*- \[ \] //' || true
}

schema='{"type":"object","properties":{"outcome":{"type":"string","enum":["done","partial","blocked","escalated"]},"summary":{"type":"string"},"next":{"type":"string"}},"required":["outcome","summary"]}'

system_note="You are one session of kit-drive.sh, in ${mode} mode (.claude/CLAUDE.md, ## Modes). There is no conversation history: the progress file is the state, and the next session sees only the progress file and your handover. Do only the phase you are given, then stop. Run subagents in the foreground. Before stopping, write into the progress file anything the next session needs: arbiter rulings, redo notes, REVIEW FAIL lines, ESCALATED lines. Never change the kit mode, kit files, settings, hooks or approvals. When an escalation trigger fires, write the ESCALATED (arbiter) line and stop. End with the structured handover: outcome, a summary of what changed, and what the next session should know."

prompt_for() {   # phase step fails progress
  case "$1" in
    KICKOFF) printf 'Phase: KICKOFF.\nFeature: %s\n\nRun the feature-kickoff skill, full automation section. Quote the requirements from the plan file `%s` and the binding documents. Create the branch, the progress file and the plan, commit the progress file through safe-commit.sh, then stop. Do not start step 1.' "$feature" "$plan" ;;
    STEP) printf 'Phase: STEP %s of `%s`. Review FAILs on this step so far: %s.\n\nRun `.claude/scripts/kit-state.sh brief %s` for the brief (add --redo if the step has a REVIEW FAIL or an arbiter redo note), then follow "One step" in .claude/CLAUDE.md ## Modes for %s mode: implementer, step-reviewer, kit-escalate-check.sh, one batched arbiter call if anything needs a ruling, redo within this session if the arbiter says FIX_NOW, then commit with the reviewer COMMIT TITLE through safe-commit.sh. Stop when step %s is committed, or escalated. Do not brief step %s.' "$2" "$4" "$3" "$2" "$mode" "$2" "$(( $2 + 1 ))" ;;
    WRAPUP) printf 'Phase: WRAPUP of `%s`. QA-GATE FAILs so far: %s.\n\nRun the feature-wrapup skill for %s mode. kit-precheck.sh first; qa-gate only once it passes. Fixes go through implementer and step-reviewer as usual. Commit what you change through safe-commit.sh. %s' "$4" "$3" "$mode" \
              "$([ "$mode" = feature ] && echo 'Stop once QA-GATE: PASS is recorded and committed. Do not push, open a PR or set Status: complete: the human approves first.' || echo 'Stop once QA-GATE: PASS is recorded and committed.')" ;;
    DELIVER) printf 'Phase: DELIVER of `%s`.\n\nRun the close-out in the feature-wrapup skill, auto mode: Status complete, tick the feature in `%s`, commit, push, open the PR through pr-description, run safe-merge.sh, then switch to %s and pull. Stop after the merge.' "$4" "$plan" "$target" ;;
  esac
}

spent=0
counts=""   # "<key> <n>" lines; bash 3 has no associative arrays
handover=""

while true; do
  m="$("$here/kit-mode.sh" status | awk '{print $1}')"
  [ "$m" = "$mode" ] || halt "kit mode changed to '$m' during the run"

  st="$("$here/kit-state.sh" phase)"
  get() { printf '%s\n' "$st" | sed -n "s/^$1=//p" | head -n1; }
  phase="$(get PHASE)"; step="$(get STEP)"; progress="$(get PROGRESS)"; branch="$(get BRANCH)"
  fails="$(get FAILS)"; [ "$phase" = WRAPUP ] && fails="$(get QA_FAILS)"

  case "$phase" in
    KICKOFF)
      if [ -f "$current" ] && [ -z "$feature" ]; then
        read -r cur_branch < "$current"
        if [ "$branch" != "$cur_branch" ]; then
          [ -z "$(git status --porcelain)" ] || halt "working tree dirty; cannot switch to $cur_branch, the feature in flight"
          git switch -q "$cur_branch" || halt "cannot switch to $cur_branch, the feature in flight"
          continue
        fi
      fi
      [ "$mode" = auto ] || finish "feature mode: run feature-kickoff in an interactive session and approve the plan there, then run kit-drive.sh on the feature branch"
      [ "$branch" = "$target" ] || halt "on $branch with no progress file; start from $target"
      if [ -z "$feature" ] && [ "$next" -eq 1 ]; then feature="$(next_plan_item)"; fi
      [ -n "$feature" ] || finish "nothing to do: no feature given and no unticked line in $plan"
      [ -z "$(git status --porcelain)" ] || halt "working tree dirty on $target; commit or clean it first" ;;
    PLAN_APPROVAL) halt "the plan in $progress has no **Plan approved** line. Review it with the agent in an interactive session" ;;
    HALT) halt "$(get REASON | cut -c1-300)" ;;
    APPROVAL) finish "$branch is built and passed qa-gate. Read the HANDOVER in $progress, do the eye test, then run .claude/scripts/kit-approve.sh" ;;
    DELIVER) [ "$mode" = auto ] || finish "$branch is approved. Open Claude Code and ask it to deliver: it drafts the PR for you to confirm" ;;
    DONE)
      rm -f "$current"
      notify "merged: $branch"
      [ "$loop" -eq 1 ] || exit 0
      git switch -q "$target" || halt "cannot switch to $target after the merge"
      if git rev-parse -q --verify '@{u}' >/dev/null 2>&1; then
        git pull -q --ff-only || halt "cannot update $target after the merge"
      fi
      feature=""; handover=""; continue ;;
    STEP|WRAPUP) ;;
    *) halt "unknown phase '$phase' from kit-state.sh" ;;
  esac

  key="$phase${step:+-$step}"
  n="$(printf '%s\n' "$counts" | awk -v k="$key" '$1 == k { print $2 }')"; n=$(( ${n:-0} + 1 ))
  counts="$(printf '%s\n' "$counts" | awk -v k="$key" '$1 != k && NF')"$'\n'"$key $n"
  [ "$n" -le "$max_sessions" ] || halt "$key needed more than $max_sessions sessions"
  awk -v s="$spent" -v b="$run_budget" 'BEGIN { exit !(s + 0 >= b + 0) }' && halt "run budget of \$$run_budget spent (\$$spent)"

  prompt="$(prompt_for "$phase" "${step:-0}" "${fails:-0}" "$progress")"
  [ -z "$handover" ] || prompt="$prompt"$'\n\nHandover from the previous session:\n'"$handover"

  if [ "$dry" -eq 1 ]; then
    printf 'Next session: %s (%s mode, model %s, permission mode %s, budget $%s)\n\n%s\n' \
      "$key" "$mode" "$model" "$perm" "$session_budget" "$prompt"
    exit 0
  fi

  printf '\n-- session %s (%s) ...\n' "$key" "$(date +%H:%M)"
  before_work="$(work_hash)"; before_guard="$(guarded_hash)"; before_marks="$(human_marks)"; started="$(date +%s)"
  out_file="$state_dir/last-session.json"
  KIT_DRIVER=1 "$claude_bin" -p "$prompt" \
    --output-format json --json-schema "$schema" \
    --model "$model" --permission-mode "$perm" --permission-prompts none \
    --max-budget-usd "$session_budget" \
    --append-system-prompt "$system_note" \
    --name "kit-drive $key" > "$out_file" 2> "$state_dir/last-session.err"
  ec=$?

  parsed="$(kit_py -I - "$out_file" <<'PY'
import json, sys
try:
    d = json.load(open(sys.argv[1]))
except Exception:
    d = {}
s = d.get("structured_output")
if not isinstance(s, dict):
    try:
        s = json.loads(d.get("result") or "")
    except Exception:
        s = {"outcome": "partial", "summary": (d.get("result") or "no output")[:2000]}
if not isinstance(s, dict):
    s = {"outcome": "partial", "summary": str(s)[:2000]}
print(d.get("total_cost_usd") or 0)
print(d.get("session_id") or "")
print(s.get("outcome") or "partial")
print(" ".join(str(s.get("summary") or "").split())[:1500])
print(" ".join(str(s.get("next") or "").split())[:800])
PY
)"
  cost="$(sed -n 1p <<< "$parsed")"; sid="$(sed -n 2p <<< "$parsed")"; outcome="$(sed -n 3p <<< "$parsed")"
  summary="$(sed -n 4p <<< "$parsed")"; nxt="$(sed -n 5p <<< "$parsed")"
  spent="$(awk -v a="$spent" -v b="$cost" 'BEGIN { printf "%.2f", a + b }')"
  after_work="$(work_hash)"; after_guard="$(guarded_hash)"
  now_branch="$(git symbolic-ref --short -q HEAD || echo DETACHED)"

  kit_py -I -c 'import json,sys; print(json.dumps(dict(zip(sys.argv[1::2], sys.argv[2::2]))))' \
    time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" phase "$key" branch "$now_branch" exit "$ec" cost "$cost" spent "$spent" \
    seconds "$(( $(date +%s) - started ))" session "$sid" outcome "$outcome" summary "$summary" next "$nxt" >> "$log"
  printf '   %s, $%s (run $%s): %s\n' "$outcome" "$cost" "$spent" "$(cut -c1-200 <<< "$summary")"

  [ "$before_guard" = "$after_guard" ] || halt "kit files, the mode switch or the approvals changed during session $key ($sid). Check them before resuming"
  # The guard refuses these markers in Edit and Write; this also catches sed, python and the rest.
  after_marks="$(human_marks)"
  added="$(LC_ALL=C comm -13 <(printf '%s\n' "$before_marks") <(printf '%s\n' "$after_marks") | grep -vE '^(\*\*)?ESCALATED|^$' || true)"
  cleared="$(LC_ALL=C comm -23 <(printf '%s\n' "$before_marks") <(printf '%s\n' "$after_marks") | grep -E '^(\*\*)?ESCALATED' || true)"
  [ -z "$added" ] || halt "session $key ($sid) wrote a line only the human writes: $(head -n1 <<< "$added" | cut -c1-200). Check the progress file before resuming"
  [ -z "$cleared" ] || halt "session $key ($sid) removed an escalation: $(head -n1 <<< "$cleared" | cut -c1-200). Check the progress file before resuming"
  [ "$ec" -eq 0 ] || [ "$before_work" != "$after_work" ] || halt "session $key failed (exit $ec, see $state_dir/last-session.err) and changed nothing"
  [ "$before_work" != "$after_work" ] || halt "session $key changed nothing: $summary"

  if [ "$phase" = KICKOFF ]; then
    p="$("$here/kit-state.sh" find)"
    [ -n "$p" ] && [ "$now_branch" != "$target" ] || halt "kickoff ended without a feature branch and a progress file naming it"
    printf '%s\n' "$now_branch" > "$current"
    feature=""
  fi
  case "$outcome" in blocked|escalated)
    "$here/kit-state.sh" phase | grep -q '^PHASE=HALT' || halt "session $key reported $outcome without an ESCALATED line: $summary" ;;
  esac

  handover="$summary${nxt:+ Next: $nxt}"
  [ "$once" -eq 0 ] || finish "one session run; next phase: $("$here/kit-state.sh" phase | sed -n 's/^PHASE=//p')"
done
