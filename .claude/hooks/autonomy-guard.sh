#!/usr/bin/env bash
#
# autonomy-guard.sh — Claude Code PreToolUse hook for the autonomy switch.
#
# Registered in .claude/settings.json against Bash and Edit|Write. It does four things:
#   1. Refuses any Edit/Write of, or Bash mention of, the switch file .claude/.autonomy,
#      except the exact commands `.claude/scripts/autonomy.sh status|on|off`.
#   2. Refuses `autonomy.sh on` in any form other than the exact one, so the settings
#      `ask` rule for that exact command is the only route to turning autonomy on.
#      The exact `on` also gets an `ask` from here as a second layer.
#   3. Always refuses pushes to main, force-pushes, `gh pr merge` and merge API calls.
#   4. Only while the switch file exists, allows a push of a non-main branch,
#      `gh pr create`, `gh pr view` and safe-merge.sh. Otherwise it makes no decision.
#
# Protocol: tool call as JSON on stdin. Exit 2 with stderr blocks. A JSON decision on
# stdout with exit 0 allows or asks. No output and exit 0 means no decision.

set -uo pipefail

input="$(cat)"
root="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"

block_switch() {
  echo "BLOCKED: the autonomy switch is changed only with .claude/scripts/autonomy.sh. Turning it on needs the human's confirmation in chat first, then run exactly: .claude/scripts/autonomy.sh on" >&2
  exit 2
}

if ! command -v python3 >/dev/null 2>&1; then
  printf '%s' "$input" | grep -q '\.autonomy' && block_switch
  exit 0
fi

printf '%s' "$input" | ROOT="$root" python3 -c '
import json, os, re, shlex, subprocess, sys

raw = sys.stdin.read()
root = os.environ["ROOT"]
switch = os.path.join(root, ".claude", ".autonomy")

def deny(msg):
    sys.stderr.write("BLOCKED: " + msg + "\n")
    sys.exit(2)

def decide(kind, reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
          "permissionDecision": kind, "permissionDecisionReason": reason}}))
    sys.exit(0)

SWITCH_MSG = ("the autonomy switch is changed only with .claude/scripts/autonomy.sh. "
              "Turning it on needs the human confirmation in chat first, then run exactly: "
              ".claude/scripts/autonomy.sh on")

try:
    d = json.loads(raw)
    ti = d.get("tool_input") or {}
    if not isinstance(ti, dict):
        ti = {}
except Exception:
    if ".autonomy" in raw:
        deny(SWITCH_MSG)
    sys.exit(0)

tool = d.get("tool_name", "")
cwd = d.get("cwd") or root

# --- Edit / Write -------------------------------------------------------------
fp = ti.get("file_path") or ti.get("notebook_path")
if fp:
    p = os.path.normpath(os.path.join(cwd, fp))
    if os.path.realpath(p) == os.path.realpath(switch) or p.endswith("/.claude/.autonomy"):
        deny(SWITCH_MSG)

# New file content that names the switch is refused, so a script cannot be written
# and then run to change it. Markdown and the guarded config files are exempt.
if fp:
    texts = [ti.get("content"), ti.get("new_string"), ti.get("new_source")]
    texts += [e.get("new_string") for e in (ti.get("edits") or []) if isinstance(e, dict)]
    rel = os.path.relpath(os.path.normpath(os.path.join(cwd, fp)), root)
    exempt = (p.endswith(".md")
              or rel in (".claude/settings.json", ".claude/settings.local.json",
                         ".claude/scripts/autonomy.sh", ".claude/scripts/safe-merge.sh")
              or rel.startswith(".claude/hooks/"))
    if not exempt and any(isinstance(x, str) and ".autonomy" in x for x in texts):
        deny(SWITCH_MSG)

cmd = ti.get("command") or ""
if not cmd:
    sys.exit(0)

CANON = re.compile(r"\s*\.claude/scripts/autonomy\.sh (status|on|off)\s*")
m = CANON.fullmatch(cmd)
if m:
    if m.group(1) == "on":
        decide("ask", "Second confirmation: switch this laptop to full automation")
    sys.exit(0)

segs = [s for s in re.split(r"&&|\|\||[;|&()`\n]|\$\(", cmd) if s.strip()]

def toks(s):
    try:
        t = shlex.split(s)
    except ValueError:
        t = s.split()
    while t and (re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", t[0]) or t[0] == "sudo"):
        t.pop(0)
    return t

def git_out(directory, *args):
    try:
        return subprocess.run(["git", "-C", directory] + list(args),
                              capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:
        return ""

def branch(directory):
    return git_out(directory, "symbolic-ref", "--short", "-q", "HEAD")

PUSH_ARG_FLAGS = {"-o", "--push-option", "--repo", "--receive-pack", "--exec"}

def check_push(t):
    i, gdir = 1, cwd
    while i < len(t) and t[i].startswith("-"):
        if t[i] == "-C" and i + 1 < len(t):
            gdir = os.path.join(cwd, t[i + 1]); i += 1
        elif t[i] in ("-c", "--git-dir", "--work-tree", "--namespace") and i + 1 < len(t):
            i += 1
        i += 1
    if i >= len(t) or t[i] != "push":
        return
    args, pos, skip = t[i + 1:], [], False
    for a in args:
        if skip:
            skip = False
        elif a in PUSH_ARG_FLAGS:
            skip = True
        elif a.startswith("--"):
            if a in ("--force", "--mirror", "--all") or a.startswith("--force-with-lease"):
                deny("force-pushes, mirror pushes and --all pushes are not permitted: " + a)
        elif a.startswith("-") and len(a) > 1:
            if "f" in a[1:]:
                deny("force-pushes are not permitted: " + a)
        else:
            pos.append(a)
    refspecs = pos[1:]
    if not refspecs:
        cur = branch(gdir)
        if cur == "main":
            deny("pushing main is not permitted; main changes only through a merged PR")
        if not cur and git_out(gdir, "rev-parse", "--abbrev-ref", "HEAD") == "HEAD":
            deny("a bare push from a detached HEAD is not permitted; name the branch")
        up = git_out(gdir, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{push}")
        if up == "main" or up.endswith("/main"):
            deny("this branch pushes to main by default; name the branch explicitly")
        return
    for r in refspecs:
        if r.startswith("+"):
            deny("force-pushes are not permitted: " + r)
        dst = r.split(":")[-1]
        if dst.startswith("refs/heads/"):
            dst = dst[len("refs/heads/"):]
        if dst == "HEAD" and ":" not in r:
            dst = branch(gdir)
        if dst == "main":
            deny("pushing to main is not permitted; main changes only through a merged PR")

for s in segs:
    t = toks(s)
    if ".autonomy" in s:
        deny(SWITCH_MSG)
    if not t:
        continue
    if any(os.path.basename(x) == "autonomy.sh" for x in t) and "on" in t:
        deny(SWITCH_MSG)
    if t[0] == "git":
        check_push(t)
    if t[0] == "gh":
        if "pr" in t and "merge" in t[t.index("pr"):]:
            deny("merging a PR is not permitted from here; use .claude/scripts/safe-merge.sh")
        if "api" in t and any(re.search(r"/merges?($|[?])", x.strip("\"\x27")) for x in t):
            deny("merge API calls are not permitted from here; use .claude/scripts/safe-merge.sh")

# --- Allow list, only while the switch exists ---------------------------------
if not os.path.isfile(switch):
    sys.exit(0)
if "`" in cmd or "$(" in cmd or "\n" in cmd:
    sys.exit(0)
try:
    lex = shlex.shlex(cmd, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    t = list(lex)
except ValueError:
    sys.exit(0)
if not t or any(re.fullmatch(r"[();<>|&]+", x) for x in t):
    sys.exit(0)

ok = False
if t[0] == "git" and len(t) >= 4 and t[1] == "push":
    rest = [x for x in t[2:] if x not in ("-u", "--set-upstream")]
    ok = (len(rest) == 2 and rest[0] == "origin" and not rest[1].startswith(("-", "+"))
          and ":" not in rest[1] and rest[1] not in ("main", "HEAD"))
elif t[0] == "gh" and len(t) >= 3 and t[1] == "pr" and t[2] in ("create", "view"):
    ok = True
elif t[0] == ".claude/scripts/safe-merge.sh" or t[0].endswith("/.claude/scripts/safe-merge.sh"):
    ok = True
if ok:
    decide("allow", "Autonomy is on: routine feature-branch delivery command")
sys.exit(0)
'
