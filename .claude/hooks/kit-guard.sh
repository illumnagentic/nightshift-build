#!/usr/bin/env bash
#
# kit-guard.sh — Claude Code PreToolUse hook for the kit modes.
#
# Registered in .claude/settings.json against Bash and Edit|Write|MultiEdit|NotebookEdit.
#
# In every mode it:
#   1. refuses any write to, or Bash mention of, the mode switch .claude/.kit-mode and
#      the approval store .claude/.approvals, except the exact commands
#      `.claude/scripts/kit-mode.sh status|step|feature|auto` and
#      `.claude/scripts/kit-approve.sh --check [<branch>]|--status`;
#   2. refuses `kit-mode.sh feature|auto` in any other form, and answers the exact form
#      with `ask`, so the human approves it. A driver session may only read the mode;
#   3. refuses any other run of kit-approve.sh: approving is the human's, in a terminal;
#   4. refuses writing a "HUMAN APPROVAL:" line into any file;
#   5. refuses pushes to the target branch, force, mirror and --all pushes,
#      `gh pr merge` and merge API calls.
#
# In feature and auto mode it also:
#   6. refuses edits to .claude/settings*.json, .claude/hooks/, .claude/scripts/ and
#      .git/hooks/, and Bash that writes to them (reading and running kit scripts is
#      fine);
#   7. auto-allows the kit's own scripts (kit-state, kit-test, kit-precheck,
#      kit-escalate-check, kit-context, check-process-refs, safe-commit, kit-mode status).
#
# In feature mode only:
#   8. a push, or `gh pr create`, needs a valid human approval of that branch
#      (kit-approve.sh --check). `gh pr create` then asks, so the human confirms the PR.
#      `safe-merge.sh` asks. Inside a driver session all three are refused.
#   9. writing "**Status**: complete" into a progress file needs a valid approval.
#  Inside a driver session, in any mode, writing "**Plan approved**" or
#  "RESOLVED (human)" into a progress file is refused: those are the human's.
#
# In auto mode only:
#  10. auto-allows a feature-branch push, `gh pr create`, `gh pr view` and safe-merge.sh.
#
# A driver session is one kit-drive.sh started: it sets KIT_DRIVER=1.
#
# Protocol: tool call as JSON on stdin. Exit 2 with stderr blocks. A JSON decision on
# stdout with exit 0 allows or asks. No output and exit 0 means no decision.
#
# Fails closed: if the Python check itself crashes, the call is blocked. Claude Code
# treats any exit other than 2 as "allow", so a crash must not leave the guard off.
#
# Windows: runs under Git Bash. Paths may arrive as C:\x, C:/x or /c/x; they are
# compared in one form, case-insensitively.

set -uo pipefail

input="$(cat)"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="${CLAUDE_PROJECT_DIR:-$(cd "$here/../.." && pwd)}"

# shellcheck source=../scripts/kit-py.sh
. "$here/../scripts/kit-py.sh" 2>/dev/null || KIT_PY=()
if [ "${#KIT_PY[@]}" -eq 0 ]; then
  if printf '%s' "$input" | grep -Eq '\.kit-mode|\.approvals|kit-approve\.sh'; then
    echo "BLOCKED: the kit mode and approvals change only through their scripts, and Python 3 is needed to check this call" >&2
    exit 2
  fi
  exit 0
fi
# The bash running this hook, in a form Python can start (Git Bash: C:\...\bash.exe).
kit_bash="$(cygpath -w "$BASH" 2>/dev/null || printf '%s' "$BASH")"

printf '%s' "$input" | ROOT="$root" KIT_BASH="$kit_bash" "${KIT_PY[@]}" -I -c '
import json, os, posixpath, re, shlex, subprocess, sys

raw = sys.stdin.read()
root_raw = os.environ["ROOT"]
driver = os.environ.get("KIT_DRIVER") == "1"
BASH = os.environ.get("KIT_BASH") or "bash"
WIN = (os.name == "nt" or sys.platform.startswith(("msys", "cygwin"))
       or re.match(r"[A-Za-z]:", root_raw) is not None or "\\" in root_raw)

def canon(p):
    # One form for comparing: forward slashes, drive as /c/..., lower case on Windows.
    p = (p or "").replace("\\", "/")
    m = re.match(r"([A-Za-z]):(/|$)", p) or (re.match(r"/([A-Za-z])(/|$)", p) if WIN else None)
    if m:
        p = "/" + m.group(1) + p[2:]
    p = posixpath.normpath(p) if p else p
    return p.lower() if WIN else p

def native(p):
    # A path this Python can open: /c/x becomes C:/x under native Windows Python.
    if os.name == "nt":
        m = re.match(r"/([A-Za-z])(/|$)", (p or "").replace("\\", "/"))
        if m:
            return m.group(1).upper() + ":" + p[2:]
    return p

root = native(root_raw)
ROOT = canon(root_raw)
switch = os.path.join(root, ".claude", ".kit-mode")
approvals = os.path.join(root, ".claude", ".approvals")

def deny(msg):
    sys.stderr.write("BLOCKED: " + msg + "\n")
    sys.exit(2)

def decide(kind, reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
          "permissionDecision": kind, "permissionDecisionReason": reason}}))
    sys.exit(0)

SWITCH_MSG = ("the kit mode is changed only with .claude/scripts/kit-mode.sh. Moving to feature "
              "or auto needs the human confirmation in chat first, then run exactly: "
              ".claude/scripts/kit-mode.sh feature (or auto)")
APPROVE_MSG = ("approving a feature is the human job. Ask them to review it and run "
               ".claude/scripts/kit-approve.sh themselves (with ! in Claude Code, or in a terminal)")

try:
    d = json.loads(raw)
    ti = d.get("tool_input") or {}
    if not isinstance(ti, dict):
        ti = {}
except Exception:
    if ".kit-mode" in raw or ".approvals" in raw or "kit-approve" in raw:
        deny(SWITCH_MSG)
    sys.exit(0)

mode = "step"
try:
    w = open(switch).read().split()
    if w and w[0] in ("feature", "auto"):
        mode = w[0]
except OSError:
    pass
locked = mode in ("feature", "auto")
cwd = native(d.get("cwd") or root)
CWD = canon(cwd)

def git_out(directory, *args):
    try:
        return subprocess.run(["git", "-C", directory] + list(args),
                              capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:
        return ""

def branch(directory):
    return git_out(directory, "symbolic-ref", "--short", "-q", "HEAD")

def target_branch():
    t = ""
    try:
        for line in open(os.path.join(root, ".claude", "kit-config.md")):
            if line.startswith("- **Target branch**:"):
                t = re.sub(r"<!--.*", "", line.split(":", 1)[1]).strip().strip("`")
                break
    except OSError:
        pass
    if t and t != "auto":
        return t
    ref = git_out(root, "symbolic-ref", "-q", "refs/remotes/origin/HEAD")
    return ref.rsplit("/", 1)[-1] if ref else "main"

TARGET = target_branch()

def approved(b):
    script = os.path.join(root, ".claude", "scripts", "kit-approve.sh")
    try:
        return subprocess.run([BASH, script, "--check", b], cwd=root, capture_output=True,
                              timeout=10).returncode == 0
    except Exception:
        return False

PROTECTED = (".claude/settings.json", ".claude/settings.local.json", ".claude/hooks/",
             ".claude/scripts/", ".git/hooks/")
SENSITIVE = (".kit-mode", ".approvals")

def rel(path):
    p = canon(path)
    if not p.startswith("/"):
        p = posixpath.join(CWD, p)
    return posixpath.relpath(posixpath.normpath(p), ROOT)

def is_protected(r):
    r = r + "/" if os.path.isdir(os.path.join(root, r)) else r
    return any(r == p or r.startswith(p) for p in PROTECTED)

# --- Edit / Write -------------------------------------------------------------
fp = ti.get("file_path") or ti.get("notebook_path")
if fp:
    r = rel(fp)
    if any(r == ".claude/" + s or r.startswith(".claude/" + s + "/") for s in SENSITIVE):
        deny(SWITCH_MSG)
    texts = [ti.get("content"), ti.get("new_string"), ti.get("new_source")]
    texts += [e.get("new_string") for e in (ti.get("edits") or []) if isinstance(e, dict)]
    texts = [x for x in texts if isinstance(x, str)]
    if any("HUMAN APPROVAL:" in x for x in texts):
        deny(APPROVE_MSG)
    if locked and is_protected(r):
        deny("kit files (settings, hooks, scripts, git hooks) are read-only while " + mode +
             " mode is on. Turn it off with .claude/scripts/kit-mode.sh step first; the human approves kit changes")
    exempt = (r.endswith(".md") or is_protected(r))
    if not exempt and any(s in x for x in texts for s in SENSITIVE + ("kit-approve",)):
        deny(SWITCH_MSG)
    if r.startswith(".claude/progress/") and r.endswith(".md"):
        if mode == "feature" and any(re.search(r"\*\*Status\*\*:\s*complete", x) for x in texts):
            if not approved(branch(cwd)):
                deny("feature mode: the feature is complete only after the human approves it "
                     "(.claude/scripts/kit-approve.sh). Stop and tell them it is ready for review")
        if driver and any("**Plan approved**" in x for x in texts):
            deny("only the human approves a plan, in an interactive session")
        if driver and any("RESOLVED (human)" in x for x in texts):
            deny("only the human resolves an escalation, in an interactive session")
    sys.exit(0)

cmd = ti.get("command") or ""
if not cmd:
    sys.exit(0)

# --- Exact forms of the mode and approval scripts --------------------------------------
m = re.fullmatch(r"\s*\.claude/scripts/kit-mode\.sh (status|step|feature|auto)\s*", cmd)
if m:
    if driver and m.group(1) != "status":
        deny("a driver session cannot change the kit mode")
    if m.group(1) in ("feature", "auto"):
        decide("ask", "Second confirmation: switch this laptop to " + m.group(1) + " mode")
    if m.group(1) == "status" and locked:
        decide("allow", "kit mode status")
    sys.exit(0)
if re.fullmatch(r"\s*\.claude/scripts/kit-approve\.sh (--status|--check( [A-Za-z0-9._/-]+( [0-9a-f]{7,40})?)?)\s*", cmd):
    sys.exit(0)

segs = [s for s in re.split(r"&&|\|\||[;|&()`\n]|\$\(", cmd) if s.strip()]

def toks(s):
    try:
        t = shlex.split(s)
    except ValueError:
        t = s.split()
    while t and (re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", t[0]) or t[0] in ("sudo", "env", "command", "exec")):
        t.pop(0)
    return t

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
        return None
    args, pos, skip = t[i + 1:], [], False
    for a in args:
        if skip:
            skip = False
        elif a in PUSH_ARG_FLAGS:
            skip = True
        elif a.startswith("--"):
            if a in ("--force", "--mirror", "--all", "--delete") or a.startswith("--force-with-lease"):
                deny("force, mirror, --all and --delete pushes are not permitted: " + a)
        elif a.startswith("-") and len(a) > 1:
            if "f" in a[1:] or "d" in a[1:]:
                deny("force and delete pushes are not permitted: " + a)
        else:
            pos.append(a)
    refspecs = pos[1:]
    pushed = []
    if not refspecs:
        cur = branch(gdir)
        if cur == TARGET:
            deny("pushing " + TARGET + " is not permitted; it changes only through a merged PR")
        if not cur:
            # Detached HEAD, or a -C path the guard cannot read (on Windows, bash drops
            # the backslashes in C:\x): either way it cannot tell what this pushes.
            deny("a bare push is not permitted when the guard cannot tell which branch it pushes "
                 "(detached HEAD or unreadable -C path); name the branch")
        up = git_out(gdir, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{push}")
        if up == TARGET or up.endswith("/" + TARGET):
            deny("this branch pushes to " + TARGET + " by default; name the branch explicitly")
        return [cur]
    for r in refspecs:
        if r.startswith("+"):
            deny("force-pushes are not permitted: " + r)
        src, _, dst = r.partition(":")
        dst = dst or src
        if dst.startswith("refs/heads/"):
            dst = dst[len("refs/heads/"):]
        if dst == "HEAD":
            dst = branch(gdir)
        if dst == TARGET or (r.startswith(":")):
            deny("pushing to or deleting " + (dst or TARGET) + " is not permitted; it changes only through a merged PR")
        s = branch(gdir) if src in ("HEAD", "") else src.replace("refs/heads/", "")
        pushed.append(s)
    return pushed

READONLY = {"cat", "head", "tail", "less", "more", "grep", "egrep", "fgrep", "rg", "wc", "ls",
            "stat", "file", "diff", "cmp", "sha256sum", "sha1sum", "md5sum", "shasum", "bat",
            "test", "[", "echo", "printf", "true"}
GIT_READONLY = {"show", "diff", "log", "status", "blame", "ls-files", "cat-file", "rev-parse"}

def kit_script(x):
    return re.search(r"(^|/)\.claude/scripts/[A-Za-z0-9._-]+\.sh$", x) is not None

def check_protected(s, t):
    if not locked or not t:
        return
    # Also look with backslashes as separators: shlex drops them from C:\x\.claude\scripts.
    s_fwd = s.replace("\\", "/")
    t_fwd = toks(s_fwd)
    is_hit = lambda x: any(p in (x.lower() if WIN else x) or x.rstrip("/") == p.rstrip("/") for p in PROTECTED)
    hits = [x for x in t if is_hit(x)]
    if not hits and any(is_hit(x) for x in t_fwd):
        t, hits = t_fwd, [x for x in t_fwd if is_hit(x)]
    if not hits:
        return
    if re.search(r">\s*\S*(" + "|".join(re.escape(p) for p in PROTECTED) + ")", s_fwd.lower() if WIN else s_fwd):
        deny("kit files are read-only while " + mode + " mode is on: no redirection into them")
    head = t[0]
    if kit_script(head.replace("\\", "/")) and hits == [head]:
        return
    if head in ("bash", "sh") and len(t) > 1 and kit_script(t[1]) and hits == [t[1]]:
        return
    if head in READONLY:
        return
    if head == "sed" and "-n" in t and not any(x.startswith("-i") or x.startswith("--in-place") for x in t):
        return
    if head == "git" and len(t) > 1 and t[1] in GIT_READONLY:
        return
    if head == "find" and not any(x in ("-delete", "-exec", "-execdir", "-ok", "-okdir") for x in t):
        return
    deny("kit files (settings, hooks, scripts, git hooks) are read-only while " + mode +
         " mode is on; only reading or running them is allowed: " + s.strip()[:80])

for s in segs:
    t = toks(s)
    if any(x in s for x in SENSITIVE):
        deny(SWITCH_MSG)
    if not t:
        continue
    names = [os.path.basename(x) for x in t]
    if "kit-mode.sh" in names and any(x in t for x in ("feature", "auto")):
        deny(SWITCH_MSG)
    if "kit-approve.sh" in names:
        rest = t[names.index("kit-approve.sh") + 1:]
        if not rest or rest[0] not in ("--check", "--status"):
            deny(APPROVE_MSG)
    check_protected(s, t)
    if t[0] == "git":
        pushed = check_push(t)
        if pushed is not None and mode == "feature":
            if driver:
                deny("feature mode: a driver session never pushes; delivery happens with the human")
            for b in pushed:
                if not b or not approved(b):
                    deny("feature mode: pushing " + (b or "this branch") + " needs the human approval of the built "
                         "feature. Stop and tell them it is ready for review; they run .claude/scripts/kit-approve.sh")
    if t[0] == "gh":
        if "pr" in t and "merge" in t[t.index("pr"):]:
            deny("merging a PR is not permitted from here; use .claude/scripts/safe-merge.sh")
        if "api" in t and any(re.search(r"/merges?($|[?])", x.strip("\"\x27")) for x in t):
            deny("merge API calls are not permitted from here; use .claude/scripts/safe-merge.sh")
        if mode == "feature" and len(t) >= 3 and t[1] == "pr" and t[2] == "create":
            if driver:
                deny("feature mode: a driver session never opens a PR; delivery happens with the human")
            if not approved(branch(cwd)):
                deny("feature mode: a PR needs the human approval of the built feature first "
                     "(.claude/scripts/kit-approve.sh, run by the human)")
            decide("ask", "Feature mode: confirm this PR title and body before it opens")
    if os.path.basename(t[0]) == "safe-merge.sh" and mode == "feature":
        if driver:
            deny("feature mode: the human merges, or asks for safe-merge.sh in an interactive session")
        decide("ask", "Feature mode: merge only because the human asked for it")

# --- Allow list -----------------------------------------------------------------------
if not locked:
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

KIT_OK = {"kit-state.sh", "kit-test.sh", "kit-precheck.sh", "kit-escalate-check.sh",
          "kit-context.sh", "check-process-refs.sh", "safe-commit.sh", "kit-conf.sh"}
if kit_script(t[0]) and os.path.basename(t[0]) in KIT_OK:
    decide("allow", mode + " mode: kit script")
if t[0] == "gh" and len(t) >= 3 and t[1] == "pr" and t[2] == "view":
    decide("allow", mode + " mode: read-only PR query")

if mode != "auto":
    sys.exit(0)
ok = False
if t[0] == "git" and len(t) >= 4 and t[1] == "push":
    rest = [x for x in t[2:] if x not in ("-u", "--set-upstream")]
    ok = (len(rest) == 2 and rest[0] == "origin" and not rest[1].startswith(("-", "+"))
          and ":" not in rest[1] and rest[1] not in (TARGET, "HEAD"))
elif t[0] == "gh" and len(t) >= 3 and t[1] == "pr" and t[2] == "create":
    ok = True
elif os.path.basename(t[0]) == "safe-merge.sh" and kit_script(t[0]):
    ok = True
if ok:
    decide("allow", "auto mode: routine feature-branch delivery command")
sys.exit(0)
'
ec=$?
case "$ec" in 0|2) exit "$ec" ;; esac
echo "BLOCKED: kit-guard.sh failed (exit $ec), so this call cannot be checked. Check that Python 3 runs here, and report it to the human" >&2
exit 2
