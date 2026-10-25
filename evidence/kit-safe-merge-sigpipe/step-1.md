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

## Old form versus new form, measured

Shell: `bash --norc`, `type grep` gives `grep is /usr/bin/grep`, `grep --version` first line
`grep (GNU grep) 3.11`. Option `pipefail` set. Input: the feature tracking file of PR 15 at head
commit d54ac2566915bfeb835434b27458045f2fe48181, read with `git show`, 63,223 bytes (measured with
`wc -c`). Line searched: `- **Branch**: feat/prefs-filters` (present in the file).

- Old form (`git show ... | grep -Fxq -- "<line>"`), 6 runs: exit 141 every time. PIPESTATUS
  `141 0` every time: `git show` is killed by SIGPIPE because `-q` makes grep exit on the first match
  while the producer is still writing.
- New form (`git show ... | grep -Fx -- "<line>" >/dev/null`), 6 runs: exit 0 every time. PIPESTATUS
  `0 0` every time.

The failure still reproduces at 63,223 bytes. The new form works because GNU grep reads stdin to
the end when its output goes to `/dev/null`, so the producer is never writing into a closed pipe.

## Why an earlier run showed exit 0 for the old form

That run was made from an agent shell where `grep` is a shell function wrapping ugrep. The function
is not exported, so the merge guard script runs the system GNU grep instead, and there the old form
fails as above. The earlier "not reproduced" result came from the wrapper, not from the script's
behaviour, and is withdrawn.
