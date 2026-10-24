# Dev kit setup after cloning

The Claude Code rules and hooks in this folder come with the clone. The git-level
commit guard does not, because git never copies hooks into a clone. Install it once, from the repo root:

```bash
# If you already have a pre-commit hook, keep it: the guard runs it after its own check.
[ -e .git/hooks/pre-commit ] && mv .git/hooks/pre-commit .git/hooks/pre-commit.kit-chained
cp .claude/hooks/pre-commit-guard.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

By default it only blocks commits made from inside a Claude Code session that bypass
`.claude/scripts/safe-commit.sh`. Your own commits pass through. See the header of
`.claude/hooks/pre-commit-guard.sh` for modes and overrides.

For full automation, see `.claude/AUTO_SETUP.md`. It covers setting it up on another
machine and updating the kit. The mode is off by default on every machine.
