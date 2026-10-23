#!/usr/bin/env bash
#
# check-step-order.sh — Claude Code PreToolUse hook.
#
# Refuses an Agent call whose brief names a step while an earlier step in the
# progress file still has an unticked box. Step order is enforced here, not left to
# the orchestrator's memory.
#
# A brief opts in by starting with a header (within its first few non-empty lines):
#
#     PROGRESS: .claude/progress/<slug>.md      (path relative to the repo root)
#     STEP: <n>                                  or:  REDO OF STEP <n>
#
# No header: the call is allowed. Header present but unusable (missing file, path
# outside the repo, step not found, no repo root): the call is blocked.
# `REDO OF STEP <n>` targets step <n> and so only requires steps below n to be ticked.
#
# Registered in .claude/settings.json against the Agent|Task tool.
#
# Protocol: reads the tool call as JSON on stdin. Exit 0 allows, exit 2 blocks and
# feeds stderr back to the agent as the reason.

set -uo pipefail

input="$(cat)"

block() {
  printf 'BLOCKED: %s\n' "$1" >&2
  exit 2
}

# --- Extract cwd (line 1) and the prompt (rest) -------------------------------
# python3 if available (correct JSON parsing). If python3 is missing, or crashes on
# input it should have handled, fall back to sed on the raw JSON; never allow because
# the extractor failed.
extracted=""
use_fallback=1
if command -v python3 >/dev/null 2>&1; then
  extracted="$(printf '%s' "$input" | python3 -c '
import json,sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
ti = d.get("tool_input") if isinstance(d, dict) else None
if not isinstance(ti, dict):
    sys.exit(0)
p = ti.get("prompt", "")
if not isinstance(p, str):
    sys.exit(0)
c = d.get("cwd", "")
if not isinstance(c, str):
    c = ""
sys.stdout.buffer.write((c + "\n" + p + "\n").encode("utf-8", "replace"))
' 2>/dev/null)" && use_fallback=0
fi
if [ "$use_fallback" = 1 ]; then
  # The prompt is a JSON string: newlines are \n escapes, so awk unescapes them.
  json_field() { sed -nE 's/.*"'"$1"'"[[:space:]]*:[[:space:]]*"(([^"\\]|\\.)*)".*/\1/p' | head -1; }
  cwd_raw="$(printf '%s' "$input" | json_field cwd)"
  prompt_raw="$(printf '%s' "$input" | json_field prompt)"
  if [ -n "$prompt_raw" ]; then
    extracted="$(printf '%s\n%s\n' "$cwd_raw" "$prompt_raw" | awk '
      { gsub(/\\r/, ""); gsub(/\\n/, "\n"); gsub(/\\"/, "\""); gsub(/\\\\/, "\\"); print }')"
  else
    extracted=""
  fi
fi

[ -n "${extracted:-}" ] || exit 0
cwd="$(printf '%s\n' "$extracted" | head -1)"
prompt="$(printf '%s\n' "$extracted" | tail -n +2 | tr -d '\r')"

# --- Find the header in the first five non-empty lines -----------------------
head_lines="$(printf '%s\n' "$prompt" | grep -v '^[[:space:]]*$' | head -5)"
progress_rel="$(printf '%s\n' "$head_lines" | sed -n 's/^[[:space:]]*PROGRESS:[[:space:]]*\(.*[^[:space:]]\)[[:space:]]*$/\1/p' | head -1)"
step_n="$(printf '%s\n' "$head_lines" | sed -n 's/^[[:space:]]*STEP:[[:space:]]*\([0-9][0-9]*\)[[:space:]]*$/\1/p' | head -1)"
redo_n="$(printf '%s\n' "$head_lines" | sed -n 's/^[[:space:]]*REDO OF STEP[[:space:]][[:space:]]*\([0-9][0-9]*\)[[:space:]]*$/\1/p' | head -1)"

[ -n "$progress_rel" ] || [ -n "$step_n" ] || [ -n "$redo_n" ] || exit 0

target="${step_n:-$redo_n}"
if [ -z "$progress_rel" ] || [ -z "$target" ]; then
  block "the brief header is incomplete. It needs a 'PROGRESS: <path>' line and either 'STEP: <n>' or 'REDO OF STEP <n>' (n a positive integer) among its first lines."
fi
[ "${#target}" -le 6 ] || block "step number '$target' in the brief header is too long (6 digits at most)."
target=$((10#$target))

# --- Resolve the repo root and the progress file ------------------------------
root="${CLAUDE_PROJECT_DIR:-}"
if [ -z "$root" ] && [ -n "$cwd" ]; then
  root="$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null)"
fi
[ -n "$root" ] || block "cannot find the repo root to resolve '$progress_rel' (no CLAUDE_PROJECT_DIR, and the working directory is not in a git repository)."
root="${root%/}"

case "$progress_rel" in
  /*)
    case "$progress_rel" in
      "$root"/*) progress_file="$progress_rel" ;;
      *) block "progress path '$progress_rel' is outside the repo. Use a path relative to the repo root." ;;
    esac ;;
  *) progress_file="$root/$progress_rel" ;;
esac
case "/$progress_rel/" in
  */../*) block "progress path '$progress_rel' contains '..'. Use a path inside the repo." ;;
esac

[ -f "$progress_file" ] || block "progress file '$progress_rel' does not exist (looked for $progress_file). Create it with the feature-kickoff skill, or correct the PROGRESS line."

# --- Parse the steps -----------------------------------------------------------
# Prints "FOUND" if the target step exists, then one line per step below the target
# that has at least one unticked box.
result="$(awk -v target="$target" '
  /^###[[:space:]]+Step[[:space:]]+[0-9]+/ {
    s = $0; sub(/^###[[:space:]]+Step[[:space:]]+/, "", s); cur = s + 0
    seen[cur] = 1; next
  }
  /^##[[:space:]]/ { cur = ""; next }
  cur != "" && /^[[:space:]]*- \[ \]/ { open[cur] = 1 }
  END {
    if (target in seen) print "FOUND"
    for (n in open) if (n + 0 < target) print n
  }' "$progress_file" | sort -n)"

printf '%s\n' "$result" | grep -qx 'FOUND' || block "step $target is not in '$progress_rel' (no '### Step $target' heading). Fix the header or the progress file."

unticked="$(printf '%s\n' "$result" | grep -vx 'FOUND' | grep -v '^$' || true)"
[ -n "$unticked" ] || exit 0

list="$(printf '%s\n' "$unticked" | sed 's/^/Step /' | paste -sd, - | sed 's/,/, /g')"
cat >&2 <<EOF
BLOCKED: step order. This brief is for step $target, but $list in $progress_rel still has an unticked box.

Steps run in order. An earlier step is done when a reviewer has ticked every box with evidence.

Do this instead:

  1. Get the earlier step reviewed (step-reviewer subagent) and let it tick the boxes.
  2. Or, if the earlier step needs more work to pass review, brief that work with the header
     'REDO OF STEP <n>' in place of 'STEP: <n>'. Tell the human first.

Do not edit the progress file to tick boxes yourself, and do not reword the header to get
past this check.
EOF
exit 2
