# Autonomy guard checks

Method: hook fed tool-call JSON on stdin, project dir pointed at a scratch repo on branch main (a second scratch repo is on a feature branch). Every case run with the switch file absent, then present. Metadata only.

Decision key: `deny(exit2)` = exit 2 with stderr; `ask` / `allow` = JSON decision on stdout, exit 0; `none` = no output, exit 0.
In the command column, `<cfg>` stands for the dot-prefixed tool configuration directory, masked so the process-reference checker does not flag the file.

## Hook cases

case | command | switch | cwd | decision
--- | --- | --- | --- | ---
Bash | `git push origin main` | switch off | cwd=./r | deny(exit2)
Bash | `git push -u origin main` | switch off | cwd=./r | deny(exit2)
Bash | `git push origin +main` | switch off | cwd=./r | deny(exit2)
Bash | `git push origin HEAD:main` | switch off | cwd=./r | deny(exit2)
Bash | `git push origin HEAD:refs/heads/main` | switch off | cwd=./r | deny(exit2)
Bash | `git push origin :main` | switch off | cwd=./r | deny(exit2)
Bash | `git push origin --delete main` | switch off | cwd=./r | deny(exit2)
Bash | `git push origin feat/x:main` | switch off | cwd=./r | deny(exit2)
Bash | `git push origin feat/x:refs/heads/main` | switch off | cwd=./r | deny(exit2)
Bash | `git push` | switch off | cwd=./r | deny(exit2)
Bash | `git push origin` | switch off | cwd=./r | deny(exit2)
Bash | `git push origin HEAD` | switch off | cwd=./r | deny(exit2)
Bash | `git push -f origin feat/x` | switch off | cwd=./r | deny(exit2)
Bash | `git push --force origin feat/x` | switch off | cwd=./r | deny(exit2)
Bash | `git push --force-with-lease origin feat/x` | switch off | cwd=./r | deny(exit2)
Bash | `git push --force-with-lease=feat/x origin feat/x` | switch off | cwd=./r | deny(exit2)
Bash | `git push --mirror` | switch off | cwd=./r | deny(exit2)
Bash | `git push origin +feat/x` | switch off | cwd=./r | deny(exit2)
Bash | `git push -fu origin feat/x` | switch off | cwd=./r | deny(exit2)
Bash | `git -C /tmp push origin main` | switch off | cwd=./r | deny(exit2)
Bash | `git -c a=b push origin main` | switch off | cwd=./r | deny(exit2)
Bash | `FOO=1 git push origin main` | switch off | cwd=./r | deny(exit2)
Bash | `sudo git push origin main` | switch off | cwd=./r | deny(exit2)
Bash | `cd x && git push origin main` | switch off | cwd=./r | deny(exit2)
Bash | `true; git push --force` | switch off | cwd=./r | deny(exit2)
Bash | `gh pr merge 3` | switch off | cwd=./r | deny(exit2)
Bash | `gh pr merge 3 --squash` | switch off | cwd=./r | deny(exit2)
Bash | `gh api -X PUT repos/o/r/pulls/3/merge` | switch off | cwd=./r | deny(exit2)
Bash | `gh api repos/o/r/merges -f base=main` | switch off | cwd=./r | deny(exit2)
Bash | `sudo gh pr merge 1` | switch off | cwd=./r | deny(exit2)
Bash | `echo x > <cfg>/.autonomy` | switch off | cwd=./r | deny(exit2)
Bash | `touch <cfg>/.autonomy` | switch off | cwd=./r | deny(exit2)
Bash | `rm <cfg>/.autonomy` | switch off | cwd=./r | deny(exit2)
Bash | `rm -f <cfg>/.autonomy` | switch off | cwd=./r | deny(exit2)
Bash | `cp a <cfg>/.autonomy` | switch off | cwd=./r | deny(exit2)
Bash | `date > <scratch>/r/<cfg>/.autonomy` | switch off | cwd=./r | deny(exit2)
Bash | `true && echo 1 > <cfg>/.autonomy; ls` | switch off | cwd=./r | deny(exit2)
Bash | `/home/x/<cfg>/scripts/autonomy.sh on` | switch off | cwd=./r | deny(exit2)
Bash | `bash <cfg>/scripts/autonomy.sh on` | switch off | cwd=./r | deny(exit2)
Bash | `sh <cfg>/scripts/autonomy.sh on` | switch off | cwd=./r | deny(exit2)
Bash | `cd . && <cfg>/scripts/autonomy.sh on` | switch off | cwd=./r | deny(exit2)
Bash | `FOO=1 <cfg>/scripts/autonomy.sh on` | switch off | cwd=./r | deny(exit2)
Bash | `<cfg>/scripts/autonomy.sh on; ls` | switch off | cwd=./r | deny(exit2)
Bash | `./<cfg>/scripts/autonomy.sh on` | switch off | cwd=./r | deny(exit2)
Bash | `<cfg>/scripts/autonomy.sh on extra` | switch off | cwd=./r | deny(exit2)
Bash | `sudo <cfg>/scripts/autonomy.sh on` | switch off | cwd=./r | deny(exit2)
Bash | `git push` | switch off | cwd=./rf | none
Bash | `git push origin HEAD` | switch off | cwd=./rf | none
Bash | `git -C <scratch>/rf push` | switch off | cwd=./r | none
Bash | `git -C <scratch>/r push` | switch off | cwd=./rf | deny(exit2)
Bash | `<cfg>/scripts/autonomy.sh on` | switch off | cwd=./r | ask
Bash | `<cfg>/scripts/autonomy.sh on` | switch off | cwd=./r | ask
Bash | `<cfg>/scripts/autonomy.sh off` | switch off | cwd=./r | none
Bash | `<cfg>/scripts/autonomy.sh status` | switch off | cwd=./r | none
Edit | `<cfg>/.autonomy` | switch off | cwd=./r | deny(exit2)
Write | `<scratch>/r/<cfg>/.autonomy` | switch off | cwd=./r | deny(exit2)
Write | `../<cfg>/.autonomy` | switch off | cwd=./r/sub | deny(exit2)
Write | `<scratch>/r/README.md` | switch off | cwd=./r | none
Bash | `git push origin feat/x` | switch off | cwd=./r | none
Bash | `git push -u origin feat/x` | switch off | cwd=./r | none
Bash | `gh pr create --title "fix: a; b" --body b` | switch off | cwd=./r | none
Bash | `gh pr view 3` | switch off | cwd=./r | none
Bash | `<cfg>/scripts/safe-merge.sh 3` | switch off | cwd=./r | none
Bash | `/abs/<cfg>/scripts/safe-merge.sh 3 --dry-run` | switch off | cwd=./r | none
Bash | `git status` | switch off | cwd=./r | none
Bash | `git push origin feat/x && rm -rf x` | switch off | cwd=./r | none
Bash | `gh pr create --body "$(whoami)"` | switch off | cwd=./r | none
Bash | `git push origin a:b` | switch off | cwd=./r | none
Bash | `ls` | switch off | cwd=./r | none
Bash | `git push origin main` | switch on | cwd=./r | deny(exit2)
Bash | `git push -u origin main` | switch on | cwd=./r | deny(exit2)
Bash | `git push origin +main` | switch on | cwd=./r | deny(exit2)
Bash | `git push origin HEAD:main` | switch on | cwd=./r | deny(exit2)
Bash | `git push origin HEAD:refs/heads/main` | switch on | cwd=./r | deny(exit2)
Bash | `git push origin :main` | switch on | cwd=./r | deny(exit2)
Bash | `git push origin --delete main` | switch on | cwd=./r | deny(exit2)
Bash | `git push origin feat/x:main` | switch on | cwd=./r | deny(exit2)
Bash | `git push origin feat/x:refs/heads/main` | switch on | cwd=./r | deny(exit2)
Bash | `git push` | switch on | cwd=./r | deny(exit2)
Bash | `git push origin` | switch on | cwd=./r | deny(exit2)
Bash | `git push origin HEAD` | switch on | cwd=./r | deny(exit2)
Bash | `git push -f origin feat/x` | switch on | cwd=./r | deny(exit2)
Bash | `git push --force origin feat/x` | switch on | cwd=./r | deny(exit2)
Bash | `git push --force-with-lease origin feat/x` | switch on | cwd=./r | deny(exit2)
Bash | `git push --force-with-lease=feat/x origin feat/x` | switch on | cwd=./r | deny(exit2)
Bash | `git push --mirror` | switch on | cwd=./r | deny(exit2)
Bash | `git push origin +feat/x` | switch on | cwd=./r | deny(exit2)
Bash | `git push -fu origin feat/x` | switch on | cwd=./r | deny(exit2)
Bash | `git -C /tmp push origin main` | switch on | cwd=./r | deny(exit2)
Bash | `git -c a=b push origin main` | switch on | cwd=./r | deny(exit2)
Bash | `FOO=1 git push origin main` | switch on | cwd=./r | deny(exit2)
Bash | `sudo git push origin main` | switch on | cwd=./r | deny(exit2)
Bash | `cd x && git push origin main` | switch on | cwd=./r | deny(exit2)
Bash | `true; git push --force` | switch on | cwd=./r | deny(exit2)
Bash | `gh pr merge 3` | switch on | cwd=./r | deny(exit2)
Bash | `gh pr merge 3 --squash` | switch on | cwd=./r | deny(exit2)
Bash | `gh api -X PUT repos/o/r/pulls/3/merge` | switch on | cwd=./r | deny(exit2)
Bash | `gh api repos/o/r/merges -f base=main` | switch on | cwd=./r | deny(exit2)
Bash | `sudo gh pr merge 1` | switch on | cwd=./r | deny(exit2)
Bash | `echo x > <cfg>/.autonomy` | switch on | cwd=./r | deny(exit2)
Bash | `touch <cfg>/.autonomy` | switch on | cwd=./r | deny(exit2)
Bash | `rm <cfg>/.autonomy` | switch on | cwd=./r | deny(exit2)
Bash | `rm -f <cfg>/.autonomy` | switch on | cwd=./r | deny(exit2)
Bash | `cp a <cfg>/.autonomy` | switch on | cwd=./r | deny(exit2)
Bash | `date > <scratch>/r/<cfg>/.autonomy` | switch on | cwd=./r | deny(exit2)
Bash | `true && echo 1 > <cfg>/.autonomy; ls` | switch on | cwd=./r | deny(exit2)
Bash | `/home/x/<cfg>/scripts/autonomy.sh on` | switch on | cwd=./r | deny(exit2)
Bash | `bash <cfg>/scripts/autonomy.sh on` | switch on | cwd=./r | deny(exit2)
Bash | `sh <cfg>/scripts/autonomy.sh on` | switch on | cwd=./r | deny(exit2)
Bash | `cd . && <cfg>/scripts/autonomy.sh on` | switch on | cwd=./r | deny(exit2)
Bash | `FOO=1 <cfg>/scripts/autonomy.sh on` | switch on | cwd=./r | deny(exit2)
Bash | `<cfg>/scripts/autonomy.sh on; ls` | switch on | cwd=./r | deny(exit2)
Bash | `./<cfg>/scripts/autonomy.sh on` | switch on | cwd=./r | deny(exit2)
Bash | `<cfg>/scripts/autonomy.sh on extra` | switch on | cwd=./r | deny(exit2)
Bash | `sudo <cfg>/scripts/autonomy.sh on` | switch on | cwd=./r | deny(exit2)
Bash | `git push` | switch on | cwd=./rf | none
Bash | `git push origin HEAD` | switch on | cwd=./rf | none
Bash | `git -C <scratch>/rf push` | switch on | cwd=./r | none
Bash | `git -C <scratch>/r push` | switch on | cwd=./rf | deny(exit2)
Bash | `<cfg>/scripts/autonomy.sh on` | switch on | cwd=./r | ask
Bash | `<cfg>/scripts/autonomy.sh on` | switch on | cwd=./r | ask
Bash | `<cfg>/scripts/autonomy.sh off` | switch on | cwd=./r | none
Bash | `<cfg>/scripts/autonomy.sh status` | switch on | cwd=./r | none
Edit | `<cfg>/.autonomy` | switch on | cwd=./r | deny(exit2)
Write | `<scratch>/r/<cfg>/.autonomy` | switch on | cwd=./r | deny(exit2)
Write | `../<cfg>/.autonomy` | switch on | cwd=./r/sub | deny(exit2)
Write | `<scratch>/r/README.md` | switch on | cwd=./r | none
Bash | `git push origin feat/x` | switch on | cwd=./r | allow
Bash | `git push -u origin feat/x` | switch on | cwd=./r | allow
Bash | `gh pr create --title "fix: a; b" --body b` | switch on | cwd=./r | allow
Bash | `gh pr view 3` | switch on | cwd=./r | allow
Bash | `<cfg>/scripts/safe-merge.sh 3` | switch on | cwd=./r | allow
Bash | `/abs/<cfg>/scripts/safe-merge.sh 3 --dry-run` | switch on | cwd=./r | allow
Bash | `git status` | switch on | cwd=./r | none
Bash | `git push origin feat/x && rm -rf x` | switch on | cwd=./r | none
Bash | `gh pr create --body "$(whoami)"` | switch on | cwd=./r | none
Bash | `git push origin a:b` | switch on | cwd=./r | none
Bash | `ls` | switch on | cwd=./r | none
Bash | `git push` | main repo | cwd=./r (main) | deny(exit2)
Bash | `git push origin` | main repo | cwd=./r (main) | deny(exit2)

Result line: `BAD COUNT 0` (0 cases differed from expectation; 142 OK rows in total).

## Unparseable input

not valid JSON, no mention of the switch | exit 0 (no decision)
not valid JSON, text mentions the switch file | exit 2 (deny)

## Switch script against a scratch copy

status | off | exit 0
on | on (since 2026-10-24) | exit 0
status | on (since 2026-10-24) | exit 0
off | off | exit 0
status | off | exit 0
unknown argument | usage message | exit 1

The real switch file was never created in the repository; `git check-ignore` reports it ignored by the ignore file in the config directory.

## Syntax checks

`bash -n` on both scripts: exit 0. `python3 -m json.tool` on settings.json: exit 0.

## Redo: bare push, content check, protected-file prompts

Method as above, with four extra scratch repos: feature branch whose upstream is origin/main with push.default=upstream, detached HEAD, feature branch with no upstream, feature branch with its own upstream. Content-check cases run with the switch absent and present.

case | repo state / target | decision
--- | --- | ---
git push (feat/x, upstream origin/main, push.default=upstream) | Bash in <scratch>/rU | deny(exit2)
git push (detached HEAD) | Bash in <scratch>/rD | deny(exit2)
git push (feat/x, no upstream) | Bash in <scratch>/rN | none
git push (feat/x, upstream origin/feat/x) | Bash in <scratch>/rV | none
git push origin (feat/x, upstream origin/main, push.default=upstream) | Bash in <scratch>/rU | deny(exit2)
git push origin (detached HEAD) | Bash in <scratch>/rD | deny(exit2)
git push origin (feat/x, no upstream) | Bash in <scratch>/rN | none
git push origin (feat/x, upstream origin/feat/x) | Bash in <scratch>/rV | none
git push --tags (feat/x, no upstream) | Bash in <scratch>/rN | none
git push origin feat/x (upstream origin/main) | Bash in <scratch>/rU | none
Write x.sh touching the switch [switch off] | Write in <scratch>/r | deny(exit2)
Edit scripts/y.py new_string names switch [switch off] | Edit in <scratch>/r | deny(exit2)
MultiEdit second edit names switch [switch off] | MultiEdit in <scratch>/r | deny(exit2)
NotebookEdit new_source names switch [switch off] | NotebookEdit in <scratch>/r | deny(exit2)
Write CLAUDE.md mentioning switch [switch off] | Write in <scratch>/r | none
Write notes.md mentioning switch [switch off] | Write in <scratch>/r | none
Write x.sh without it [switch off] | Write in <scratch>/r | none
Write hook file mentioning switch (exempt) [switch off] | Write in <scratch>/r | none
Edit autonomy script mentioning switch (exempt) [switch off] | Edit in <scratch>/r | none
Edit settings file mentioning switch (exempt) [switch off] | Edit in <scratch>/r | none
Write x.sh touching the switch [switch on] | Write in <scratch>/r | deny(exit2)
Edit scripts/y.py new_string names switch [switch on] | Edit in <scratch>/r | deny(exit2)
MultiEdit second edit names switch [switch on] | MultiEdit in <scratch>/r | deny(exit2)
NotebookEdit new_source names switch [switch on] | NotebookEdit in <scratch>/r | deny(exit2)
Write CLAUDE.md mentioning switch [switch on] | Write in <scratch>/r | none
Write notes.md mentioning switch [switch on] | Write in <scratch>/r | none
Write x.sh without it [switch on] | Write in <scratch>/r | none
Write hook file mentioning switch (exempt) [switch on] | Write in <scratch>/r | none
Edit autonomy script mentioning switch (exempt) [switch on] | Edit in <scratch>/r | none
Edit settings file mentioning switch (exempt) [switch on] | Edit in <scratch>/r | none

Result: 30 OK, 0 differences. The original 142 cases were re-run unchanged: 142 OK, 0 differences.

### Protected-file prompts (settings ask rules, not exercised live)

Rules added: ask on both Edit and Write for the settings file, the local settings file, everything under the hooks directory, and the two named scripts. Syntax chosen: `Edit(/<cfg>/settings.json)` form, a single leading slash.

Doc line relied on (permissions page, Read and Edit rules, table of where a pattern anchors): rule defined in project settings, `/path` resolves to `<primary working directory>/path`. Also: `Edit(/docs/**)` matches edits in `<primary working directory>/docs/`, not `/docs/` and not `<primary working directory>/<cfg>/docs/`. So the leading `/` anchors at the project root, not at the settings file's own directory, and the config directory name must be spelled out. Deny and ask rules match at the anchored location. A live prompt was not triggered here; the orchestrator verifies it with the human. `python3 -m json.tool` on settings.json: exit 0.

## Live check (orchestrator, 2026-10-24)

| case | action | result |
| ---- | ------ | ------ |
| ask rule on the guard hook | Edit tool on `hooks/autonomy-guard.sh` (adds one comment line), auto mode | permission prompt raised; human refused; file unchanged |
