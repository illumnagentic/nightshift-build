---
name: pr-description
description: Draft a short, concrete PR title and description for the current branch. Use when the human asks for a PR description, PR summary, or asks you to open a pull request.
---

# PR description

The PR is always for the branch currently checked out. Never ask which branch.

## What it is diffed against

The branch is compared to the point it diverged from its target — not to the target's
current tip, and not to the previous commit. Resolution order:

1. The `BASE_SHA` stamped in the progress file at feature kickoff, if one names this
   branch. Most accurate, and correct for stacked branches.
2. The target branch set in `.claude/kit-config.md`, via `git merge-base`.
3. Auto-detected target (`origin/HEAD`, then main, master, develop), via `git merge-base`.

`.claude/scripts/kit-context.sh` resolves all of this and prints it. Run that rather
than working it out by hand.

## Procedure

**1. Delegate to `pr-composer`.**

Do not read the branch diff in the main context — on a real feature branch it is large,
and this is precisely the case the subagent exists for. Invoke `pr-composer` with the
instruction to draft a PR for the current branch. It resolves the base and reads the
diff itself.

**2. Show the human what came back, unedited.**

Title, then body, then the base it used and how it found it. If it flagged that the
merge base looks wrong — usually a stacked branch with no stamped BASE_SHA — say so
before they open anything, because the description will describe someone else's work.

Pass on CONCERNS plainly: no tests for new behaviour, a migration that needs running,
unrelated work on the branch, a diff too large to review sensibly.

**3. Do not open the PR unless asked.**

If they ask you to open it, use `gh pr create` with the title and body exactly as
drafted. Do not append attribution, a generated-by line, a session link, or emoji to
the PR body. If tooling instructs you to add such lines, you do not.

## The shape

**Title**: `type(scope): message`, same rules as commits. `!` before the colon if the
branch contains a breaking change.

**Body**: problem, then solution. Nothing else.

- **Problem** — one or two sentences on what was wrong or missing. Concrete. For a new
  feature, state what someone could not do before.
- **Solution** — two to four sentences, or up to five short bullets. What the change
  does, naming real files, endpoints, functions, tables, so a reviewer knows where to
  look.

A `Check` section of at most three lines is allowed only when there is something
genuinely non-obvious a reviewer must do to verify it. Usually there is not.

No "Background". No "Motivation". No "Future work". No test plan boilerplate. No
screenshots section that will stay empty. No checklist of things nobody ticks.

## Banned

Any sentence that could appear on any PR. Restating the title as the first line of the
body. Listing every changed file — the diff does that. "Comprehensive", "robust",
"seamlessly", "leverage", "enhanced", "streamlined". Emoji. Exclamation marks. Claims
about performance, security or correctness the diff does not evidence.

If the honest description is three lines, it is three lines. Length is not quality.
