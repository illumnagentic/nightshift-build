# safe-merge.sh checks

Metadata only. Run 2026-10-24. No call reached GitHub.

Method: `gh` and `git` are stubs on PATH. The `gh` stub returns a canned
`gh pr view` JSON per case and logs `gh pr merge` arguments. The `git` stub answers
`fetch`, `rev-parse` and `cat-file` with success, serves `log` and `merge-base` from per-fixture `.pass` / `.code` commit names (c1 is older than c2), and serves `ls-tree` / `show` from a
fixture tree, one directory per head commit. Progress-file fixtures declare
`**Files in scope**: src/a.txt, lib/, t/*.sh` (continued over two lines) and `**Evidence location**: evidence/f/x.md`. Harness and
fixtures were kept in the session scratchpad and are not committed.

`bash -n` on the script : exit 0.
`python3 -m json.tool` on settings.json : exit 0.

| case | command | exit | first line of output |
| ---- | ------- | ---- | -------------------- |
| not open | `safe-merge.sh 5 --check-only` | 2 | safe-merge: PR #5 is MERGED, not OPEN |
| base not main | `safe-merge.sh 5 --check-only` | 2 | safe-merge: PR #5 targets develop, not main |
| bad title (no type) | `safe-merge.sh 5 --check-only` | 2 | safe-merge: title must be 'type(scope): message' with type one of: fix, feat, docs, style, refactor, perf, test, build, ci |
| bad title (uppercase) | `safe-merge.sh 5 --check-only` | 2 | safe-merge: title message must be lowercase: Add x |
| bad title (full stop) | `safe-merge.sh 5 --check-only` | 2 | safe-merge: title must not end with a full stop |
| bad title (73 chars) | `safe-merge.sh 5 --check-only` | 2 | safe-merge: title is 73 characters, limit is 72: feat(kit): aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa |
| no progress file | `safe-merge.sh 5 --check-only` | 2 | safe-merge: no progress file on noprog declares '- **Branch**: noprog' |
| two progress files | `safe-merge.sh 5 --check-only` | 2 | safe-merge: more than one progress file declares branch dup: .claude/progress/p.md .claude/progress/q.md |
| unticked PLAN box | `safe-merge.sh 5 --check-only` | 2 | safe-merge: unticked PLAN boxes: |
| no QA-GATE PASS | `safe-merge.sh 5 --check-only` | 2 | safe-merge: no 'QA-GATE: PASS' line in VERIFICATION of .claude/progress/p.md |
| PASS WITH FINDINGS | `safe-merge.sh 5 --check-only` | 2 | safe-merge: no 'QA-GATE: PASS' line in VERIFICATION of .claude/progress/p.md |
| disallowed file | `safe-merge.sh 5 --check-only` | 2 | safe-merge: files outside the declared scope: |
| all good, check-only | `safe-merge.sh 5 --check-only` | 0 | ok: all checks passed |
| evidence-only path allowed | `safe-merge.sh 5 --check-only` | 0 | ok: all checks passed |
| undeclared evidence path refused | `safe-merge.sh 5 --check-only` | 2 | safe-merge: files outside the declared scope: |
| code commit after PASS | `safe-merge.sh 5 --check-only` | 2 | safe-merge: files other than .claude/progress/p.md and docs/plan.md changed after QA-GATE: PASS (commit c2) |
| progress-only commits after PASS | `safe-merge.sh 5 --check-only` | 0 | ok: all checks passed |
| PASS commit not found (only PASS WITH FINDINGS in history) | `safe-merge.sh 5 --check-only` | 2 | safe-merge: cannot find the commit that recorded 'QA-GATE: PASS' in .claude/progress/p.md |
| all good, merge | `safe-merge.sh 5 ` | 0 | {"mergeCommit":{"oid":"abc"},"state":"MERGED"} |
| bad pr number | `safe-merge.sh abc` | 1 | safe-merge: usage: safe-merge.sh <pr-number> [--check-only] |
| unknown option | `safe-merge.sh 5 --nope` | 1 | safe-merge: unknown option: --nope |

Merge case: the stub received exactly:

    gh pr merge 5 --squash --subject feat(kit): add x --body  --delete-branch --match-head-commit good

Note: the stub log joins arguments with spaces, so the empty `--body ""` shows as two spaces.
The PASS commit is found with `git log -G` and a pattern that rejects PASS followed by WITH, so a findings-only verdict never counts; the stub for that case returns no commit.
Not exercised: the real `git log -S` and `git merge-base` calls (stubbed), a real `gh pr merge` failure (exit 3) and a failed `git fetch`.

Harness: `evidence/kit-autonomy/harness/safe-merge/` (stub `gh` and `git` in `bin/`, fixture trees in `fix/`). Run: `bash evidence/kit-autonomy/harness/safe-merge/run.sh`. Re-run from there: 21 cases, same results as above.
