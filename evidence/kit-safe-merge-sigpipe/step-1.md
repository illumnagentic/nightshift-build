# Merge guard: pipe early-exit fix, verification

Change: in the merge guard script, the three checks that pipe a file (or file section) into
`grep -q` now use the same grep with output sent to `/dev/null`, so grep reads all input and
the producer is never killed by SIGPIPE under `pipefail`. Logic of each check is unchanged.

## Commands and exit codes

- `bash -n` on the merge guard script: exit 0.
- Merge guard on PR 15, check-only: output `ok: all checks passed`, exit 0 (previously refused at the branch check).
- Merge guard on PR 12 (already merged), check-only: `PR #12 is MERGED, not OPEN`, exit 2 (still refuses).
- By hand with pipefail, PR 15 head commit d54ac25, its feature tracking file:
  - matching branch line, new form (`grep -Fx … >/dev/null`): exit 0.
  - non-matching branch line (`nope`), new form: exit 1 (still false).
  - matching line, old form (`grep -Fxq`): exit 0 in this run, so the 141 was not reproduced on this
    read; it depends on pipe timing and buffering. The new form does not depend on it.
