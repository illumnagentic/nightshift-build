import json, subprocess, sys, os, shutil
S = sys.argv[1]
H = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../.claude/hooks/autonomy-guard.sh"))
R = S + "/r"
D = "deny(exit2)"
A = "." + "autonomy"


def g(d, *a):
    return subprocess.run(["git", "-C", d] + list(a), capture_output=True, text=True, check=True).stdout.strip()


def mk(name, branch):
    d = S + "/" + name
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    g(d, "init", "-q", "-b", branch)
    tree = g(d, "write-tree")
    c = g(d, "-c", "user.email=a@b", "-c", "user.name=n", "commit-tree", tree, "-m", "x")
    g(d, "update-ref", "refs/heads/" + branch, c)
    return d, c


def run(tool, ti, cwd):
    p = subprocess.run([H], input=json.dumps({"tool_name": tool, "tool_input": ti, "cwd": cwd}),
                       capture_output=True, text=True, env={**os.environ, "CLAUDE_PROJECT_DIR": R})
    if p.returncode == 2:
        return D
    if p.stdout.strip():
        return json.loads(p.stdout)["hookSpecificOutput"]["permissionDecision"]
    return "none"


bad = 0


def chk(label, tool, ti, cwd, exp):
    global bad
    got = run(tool, ti, cwd)
    ok = got == exp
    bad += not ok
    print(("OK  " if ok else "BAD ") + " | ".join([tool, label, cwd.replace(S, "<scratch>"), got]))


def setup_up(d, c, merge):
    g(d, "update-ref", "refs/remotes/origin/" + merge, c)
    g(d, "config", "remote.origin.url", "/nonexistent")
    g(d, "config", "remote.origin.fetch", "+refs/heads/*:refs/remotes/origin/*")
    g(d, "config", "branch.feat/x.remote", "origin")
    g(d, "config", "branch.feat/x.merge", "refs/heads/" + merge)
    g(d, "config", "push.default", "upstream")


u, c = mk("rU", "feat/x")
setup_up(u, c, "main")
v, c = mk("rV", "feat/x")
setup_up(v, c, "feat/x")
dd, c = mk("rD", "feat/x")
g(dd, "checkout", "-q", "--detach", c)
n, c = mk("rN", "feat/x")

for cmd in ("git push", "git push origin"):
    chk(cmd + " (feat/x, upstream origin/main, push.default=upstream)", "Bash", {"command": cmd}, u, D)
    chk(cmd + " (detached HEAD)", "Bash", {"command": cmd}, dd, D)
    chk(cmd + " (feat/x, no upstream)", "Bash", {"command": cmd}, n, "none")
    chk(cmd + " (feat/x, upstream origin/feat/x)", "Bash", {"command": cmd}, v, "none")
chk("git push --tags (feat/x, no upstream)", "Bash", {"command": "git push --tags"}, n, "none")
chk("git push origin feat/x (upstream origin/main)", "Bash", {"command": "git push origin feat/x"}, u, "none")

sw = R + "/.claude/" + A
for state in (False, True):
    if state:
        open(sw, "w").write("2026-10-24\n")
    elif os.path.exists(sw):
        os.remove(sw)
    m = "switch " + ("on" if state else "off")
    chk("Write x.sh touching the switch [%s]" % m, "Write", {"file_path": "x.sh", "content": "touch .claude/" + A + "\n"}, R, D)
    chk("Edit scripts/y.py new_string names switch [%s]" % m, "Edit", {"file_path": "scripts/y.py", "old_string": "a", "new_string": "p='" + A + "'"}, R, D)
    chk("MultiEdit second edit names switch [%s]" % m, "MultiEdit", {"file_path": "z.py", "edits": [{"old_string": "a", "new_string": "b"}, {"old_string": "c", "new_string": "x" + A}]}, R, D)
    chk("NotebookEdit new_source names switch [%s]" % m, "NotebookEdit", {"notebook_path": "n.ipynb", "new_source": "open('" + A + "')"}, R, D)
    chk("Write CLAUDE.md mentioning switch [%s]" % m, "Write", {"file_path": ".claude/CLAUDE.md", "content": "see .claude/" + A + "\n"}, R, "none")
    chk("Write notes.md mentioning switch [%s]" % m, "Write", {"file_path": "notes.md", "content": A}, R, "none")
    chk("Write x.sh without it [%s]" % m, "Write", {"file_path": "x.sh", "content": "echo hi\n"}, R, "none")
    chk("Write hook file mentioning switch (exempt) [%s]" % m, "Write", {"file_path": ".claude/hooks/h.sh", "content": A}, R, "none")
    chk("Edit autonomy script mentioning switch (exempt) [%s]" % m, "Edit", {"file_path": ".claude/scripts/autonomy.sh", "new_string": A}, R, "none")
    chk("Edit settings file mentioning switch (exempt) [%s]" % m, "Edit", {"file_path": ".claude/settings.json", "new_string": A}, R, "none")
if os.path.exists(sw):
    os.remove(sw)
print("BAD COUNT", bad)
