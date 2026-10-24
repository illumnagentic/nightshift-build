import json, subprocess, sys, os
S = sys.argv[1]
H = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../.claude/hooks/autonomy-guard.sh"))
R = S + "/r"
RF = S + "/rf"
SWF = R + "/.claude/.autonomy"
D = "deny(exit2)"


def run(tool, ti, cwd):
    p = subprocess.run([H], input=json.dumps({"tool_name": tool, "tool_input": ti, "cwd": cwd}),
                       capture_output=True, text=True, env={**os.environ, "CLAUDE_PROJECT_DIR": R})
    if p.returncode == 2:
        return D
    if p.stdout.strip():
        return json.loads(p.stdout)["hookSpecificOutput"]["permissionDecision"]
    return "none"


def sw(on):
    if on:
        open(SWF, "w").write("2026-10-24\n")
    elif os.path.exists(SWF):
        os.remove(SWF)


cases = []


def B(c, exp, cwd=R):
    cases.append(("Bash", {"command": c}, exp, cwd))


for c in ["git push origin main", "git push -u origin main", "git push origin +main", "git push origin HEAD:main",
          "git push origin HEAD:refs/heads/main", "git push origin :main", "git push origin --delete main",
          "git push origin feat/x:main", "git push origin feat/x:refs/heads/main", "git push", "git push origin",
          "git push origin HEAD", "git push -f origin feat/x", "git push --force origin feat/x",
          "git push --force-with-lease origin feat/x", "git push --force-with-lease=feat/x origin feat/x",
          "git push --mirror", "git push origin +feat/x", "git push -fu origin feat/x",
          "git -C /tmp push origin main", "git -c a=b push origin main", "FOO=1 git push origin main",
          "sudo git push origin main", "cd x && git push origin main", "true; git push --force",
          "gh pr merge 3", "gh pr merge 3 --squash", "gh api -X PUT repos/o/r/pulls/3/merge",
          "gh api repos/o/r/merges -f base=main", "sudo gh pr merge 1",
          "echo x > .claude/.autonomy", "touch .claude/.autonomy", "rm .claude/.autonomy",
          "rm -f .claude/.autonomy", "cp a .claude/.autonomy", "cat x | tee .claude/.autonomy",
          "date > " + SWF, "true && echo 1 > .claude/.autonomy; ls",
          "/home/x/.claude/scripts/autonomy.sh on", "bash .claude/scripts/autonomy.sh on",
          "sh .claude/scripts/autonomy.sh on", "cd . && .claude/scripts/autonomy.sh on",
          "FOO=1 .claude/scripts/autonomy.sh on", ".claude/scripts/autonomy.sh on; ls",
          "./.claude/scripts/autonomy.sh on", ".claude/scripts/autonomy.sh on extra",
          "sudo .claude/scripts/autonomy.sh on"]:
    B(c, D)
# bare push: main denies, feature branch does not
cases.append(("Bash", {"command": "git push"}, "none", RF))
cases.append(("Bash", {"command": "git push origin HEAD"}, "none", RF))
cases.append(("Bash", {"command": "git -C %s push" % RF}, "none", R))
cases.append(("Bash", {"command": "git -C %s push" % R}, D, RF))
B(".claude/scripts/autonomy.sh on", "ask")
B("  .claude/scripts/autonomy.sh on  ", "ask")
B(".claude/scripts/autonomy.sh off", "none")
B(".claude/scripts/autonomy.sh status", "none")
cases.append(("Edit", {"file_path": ".claude/.autonomy"}, D, R))
cases.append(("Write", {"file_path": SWF, "content": "x"}, D, R))
cases.append(("Write", {"file_path": "../.claude/.autonomy"}, D, R + "/sub"))
cases.append(("Write", {"file_path": R + "/README.md", "content": "x"}, "none", R))

allow = ["git push origin feat/x", "git push -u origin feat/x", 'gh pr create --title "fix: a; b" --body b',
         "gh pr view 3", ".claude/scripts/safe-merge.sh 3", "/abs/.claude/scripts/safe-merge.sh 3 --dry-run"]
notallow = ["git status", "git push origin feat/x && rm -rf x", 'gh pr create --body "$(whoami)"',
            "git push origin a:b", "ls"]

bad = 0
for state in (False, True):
    sw(state)
    label = "switch " + ("on" if state else "off")
    rows = []
    for tool, ti, exp, cwd in cases:
        rows.append((tool, ti.get("command", ti.get("file_path")), exp, cwd))
    for c in allow:
        rows.append(("Bash", c, "allow" if state else "none", R))
    for c in notallow:
        rows.append(("Bash", c, "none", R))
    for tool, c, exp, cwd in rows:
        # bare pushes on the main-branch repo: R is on main
        ti = {"command": c} if tool == "Bash" else {"file_path": c}
        got = run(tool, ti, cwd)
        ok = got == exp
        bad += not ok
        print(("OK  " if ok else "BAD ") + " | ".join([tool, c, label, "cwd=" + cwd.replace(S, "."), got]))
sw(False)
for raw in ("not json", "garbage .claude/.autonomy"):
    p = subprocess.run([H], input=raw, capture_output=True, text=True)
    print("raw", repr(raw), "exit", p.returncode)
# bare push on main repo
for c in ("git push", "git push origin"):
    got = run("Bash", {"command": c}, R)
    print(("OK  " if got == D else "BAD ") + "Bash | %s | cwd=./r (main) | %s" % (c, got))
print("BAD COUNT", bad)
