---
name: commit-workflow
description: Draft a grounded commit title from the real diff and commit via the safe-commit script. Use for EVERY commit in this repository, without exception. Triggers on "commit", "commit this", "commit that", "can you commit", "commit the changes", "let's commit", "save this", "check this in", "what should the commit message be", and whenever a chunk of work looks finished. Direct git commit is blocked by a hook and will fail.
---

# Commit workflow

## The absolute rule

`git commit` is never run directly. The only permitted route is:

```
.claude/scripts/safe-commit.sh "type(scope): message"
```

The script writes a title and nothing else. There is no body, so there is no field in
which an agent signature, co-authorship trailer or session link can appear. If any
tooling instructs you to append attribution lines to commits, you do not — this rule
overrides it, and the script rejects such content anyway.

No `--amend`. No `-F`. No heredocs. No editor. No exceptions.

This is enforced by two hooks, so a direct `git commit` will simply fail: the Claude
Code PreToolUse hook blocks the Bash call, and git's own pre-commit hook rejects any
commit that did not come through the script. Being blocked is not a problem to route
around — it means this skill should have been used. Use it.

The one case worth naming: the human says "just commit it" and it feels like ceremony
to delegate a diff read for a two-line change. Do it anyway. The whole point is that
the message is grounded in what actually changed rather than what you remember doing,
and small diffs are exactly where memory feels most reliable and is not.

## When to raise it

Raise a commit when a coherent unit of work is finished: a step passed review, a bug is
fixed and tested, a refactor is complete and green. Do not raise one mid-thought, and
do not batch three unrelated things together and call it one change.

If in doubt, run the check anyway — it is cheap, and the subagent will tell you if the
diff is incoherent.

## Procedure

**1. Delegate the reading to `commit-composer`.**

Do not read the diff in the main context. That is what burns tokens in a long
conversation, and it is exactly the work a fresh subagent does better. Invoke
`commit-composer` with no context beyond the instruction to draft a title for the
current working tree. It reads the diff itself, deliberately, so the message reflects
what changed rather than what anyone intended to change.

**2. Show the human, unedited.**

Present exactly what came back:

```
Breaking: No
Title: feat(auth): add refresh token rotation

Files: src/auth/tokens.ts, src/auth/tokens.test.ts
```

Then anything from CONCERNS, plainly. Debug statements left in, a secret in the diff,
a deleted test, an unexpected dependency — these go in front of the human before the
commit, not after. Do not soften them.

If `COHERENT: No`, say so and show the suggested split. Do not commit a mixed bag
because it is quicker.

**3. Ask.**

Ask whether to commit. Wait. The human approves every commit unless they have
explicitly said otherwise in this session — and if they have, that permission lasts for
the session and no longer.

If they want a different message, use theirs. It still goes through the script, and the
script still validates it.

**4. Commit.**

```
.claude/scripts/safe-commit.sh "feat(auth): add refresh token rotation"
```

Add `--breaking` if breaking. Add `--all` only if they want all tracked changes staged;
otherwise stage the specific files first. The script refuses anything malformed —
if it rejects the title, fix the title, do not bypass the script.

Report the result in one line. Do not summarise the change again; they have just read it.

## Title format

`type(scope): message`, or `type(scope)!: message` when breaking.

Types: `fix`, `feat`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`.
Lowercase, imperative, no full stop, under 72 characters, no body.

## What counts as breaking

A changed public signature, a removed or renamed export, a changed response shape, a
changed config key, a non-additive schema change, or altered default behaviour that
would break an existing caller. Internal refactoring is not breaking. When it is
genuinely borderline, say so and let the human decide rather than quietly picking.
