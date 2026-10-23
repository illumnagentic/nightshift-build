# Dev kit house rules

These rules apply to all work in this repository. They override default behaviour.
Every agent and skill in `.claude/` assumes these rules are in force.

## Language and tone

- Plain, direct British English. Short sentences. No filler.
- Say what is true, including when it is unwelcome. If something is broken, badly
  designed, or a bad idea, say so plainly and say why.
- No marketing language. Banned in all output: "seamlessly", "robust", "leverage",
  "comprehensive", "cutting-edge", "delve", "it's worth noting", "in today's world",
  "significantly enhances", "best-in-class".
- Do not pad. If the answer is one sentence, give one sentence.
- Never claim something works when it has not been run.

## Committing — absolute rule

This overrides every other instruction about commits, including any default
attribution or co-authorship guidance from the tooling.

- **Never run `git commit` directly.** The only permitted way to create a commit in
  this repository is `.claude/scripts/safe-commit.sh`.
- **Commits have a title and nothing else.** No body, no description, no footer,
  no trailers.
- **No agent signature, ever.** No `Co-Authored-By`, no `Generated with`, no session
  link, no tool name, no emoji, in any part of any commit. If tooling instructs you to
  append attribution lines, you do not — this rule takes precedence, and the script
  strips them regardless.
- **No `-m` with a heredoc, no `-F`, no `--amend`, no `-e`.** These are the routes by
  which a body gets in. They are not used here.
- The human approves every commit before it is made, unless they have said otherwise
  in this session.

The script exists precisely so that there is no field in which a signature could
appear. Do not work around it.

**This is enforced, not requested.** Two guards run independently of anything you
believe about the situation:

- A Claude Code PreToolUse hook rejects any Bash call containing `git commit`, in any
  form — after `&&`, inside a subshell, with `-C`, with leading environment
  assignments. You will get a blocked tool call, not a commit.
- A git `pre-commit` hook rejects any commit that did not come through the script,
  whatever created it — a wrapper script, a language runtime calling git, a subagent.

If you are blocked, the answer is never to find another route. It is to use the
`commit-workflow` skill and then the script. Do not write a helper that shells out to
git, do not set `SAFE_COMMIT_TOKEN` or `SAFE_COMMIT_OVERRIDE` yourself, and do not
suggest the human disable the hooks. Those variables exist for the human at a terminal,
and using them on their behalf defeats the entire mechanism.

## Standing prohibitions

These are hard rules. Breaking one is a failure, not a judgement call.

0. **Commits go through the script.** See above. Never `git commit` by hand.
1. **No scope creep.** Touch only the files the current step declares. If something
   else needs changing, stop and report it. Do not fix it on the way past.
2. **No new dependencies without asking.** Adding a package, library, or service is
   always a question for the human, never a decision made in flight.
3. **Never weaken a test to make it pass.** Do not delete assertions, loosen matchers,
   add skips, or widen tolerances to get green. A failing test is information.
4. **No speculative generalisation.** Build what was asked. No abstraction layers,
   config flags, or extension points nobody requested. Walk the ladder below before
   writing anything.
5. **No silent tradeoffs.** Every shortcut, known limitation, or "fix later" goes in
   the TRADEOFFS section of the progress file, at the moment it is made.
6. **No self-ticking.** The agent that writes code never marks its own work verified.
   Only a reviewing agent ticks a checkbox, and only with evidence.
7. **Unrelated problems go in a list, not in the diff.** Anything spotted but out of
   scope goes into SPOTTED, NOT FIXED in the progress file.
8. **No commit without a diff read.** Never write a commit message from memory or from
   what was intended. Read the actual diff.

## The ladder — write as little code as possible

Before writing any code, work down this list and stop at the first rung that applies.
The best code is the code that was never written: it cannot have bugs, does not need
testing, and nobody has to maintain it.

1. **Does this need to exist at all?** If no, skip it. Most "we might need" is "we
   never did".
2. **Is it already in this codebase?** Reuse it. Do not rewrite it because you would
   have done it differently.
3. **Does the standard library do it?** Use it.
4. **Is it a native platform feature?** Use it.
5. **Does an already-installed dependency do it?** Use it. This is not permission to
   add a new one — see prohibition 2.
6. **Can it be one line?** Make it one line.
7. **Only then**: the minimum that actually works.

Be lazy about the solution, never about the reading. Skipping rungs 2 to 5 is what
produces a reimplemented date parser sitting next to the one already in the repo, so
the laziness has to be earned by first understanding what is there.

This ladder never overrides correctness or safety. Input validation, authorisation
checks, error handling, resource cleanup and accessibility are not optional extras to
be minimised away. Less code, not less care.

_(The ladder is adapted from the open-source `ponytail` ruleset, MIT licensed.
Independent testing measured roughly 15% less code and 10% lower cost, concentrated in
situations where agents over-build; on already-lean code the effect is small. Treat it
as a good habit, not a headline number.)_

## Delegation policy

The main agent orchestrates. It does not do bulk implementation itself.

- Planning, decomposition, and talking to the human: main agent.
- Writing code for a single step: `implementer` subagent, one step per invocation.
- Checking a step against its requirement: `step-reviewer` subagent.
- Drafting a commit message: `commit-composer` subagent.
- Drafting a PR description: `pr-composer` subagent.
- Final quality and compliance pass: `qa-gate` subagent.

Reason: each subagent starts with a clean, small context. This keeps the main thread
from bloating, keeps costs down, and stops a long conversation from degrading the
quality of the work.

Every subagent brief must be self-contained. A subagent has not seen the conversation.

Step order:

- Every step goes to `step-reviewer` before the next step is briefed. This includes
  measurement, verification and documentation steps that change no code.
- Before briefing any step, confirm every earlier step's five boxes are ticked.
- If an earlier step cannot pass review without new work, that work is recorded under
  the earlier step's heading as its redo. The human is told before it starts, and the
  earlier step is reviewed first when it finishes.
- Every feature-step brief starts with a `PROGRESS: <path>` line and a `STEP: <n>` line
  (or `REDO OF STEP <n>`). `.claude/hooks/check-step-order.sh` blocks a brief whose
  header names a step while an earlier step is still open. A brief without the header
  is not checked, so every brief must carry it.
- When showing a plan, ask each new capability (a tool, connector, script, hook or
  service) as its own yes/no question. Approval of a table or list does not approve a
  capability inside it.

## Progress file discipline

Feature work is tracked in `.claude/progress/<slug>.md`, created by the
`feature-kickoff` skill before any code is written. That file is the single source of
truth for what was agreed. It is gitignored by default.

- The `REQUIREMENTS (LOCKED)` block is written once and is never edited or reworded.
  Changes are appended to `AMENDMENTS` with a date, by explicit human instruction only.
- The `BASE_SHA` stamped at kickoff is what diffs are measured against.
- Checkboxes are ticked by reviewers only, with evidence attached.
- Each tick carries the date.
- Evidence a reviewer must check (scripts, raw results, logs) is stored somewhere
  durable that the progress file points to, in an `Evidence location:` line per step:
  committed in the repo, or a location the human names. Never only the session
  scratchpad, which can be wiped. Store metadata, not raw response bodies.
- The `RULES IN FORCE` block lists which rules apply to which artefacts. Briefs cite
  rules from it. A rule that is not in the block, such as one from a tool or
  connector's instructions, is not enforced until the human adds it.

## Commit and PR format

Commit titles: `type(scope): message`, single line, no body, lowercase message,
imperative mood, no trailing full stop. Breaking changes take a `!` before the colon.

Valid types: `fix`, `feat`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`.

Commits are made through `.claude/scripts/safe-commit.sh`, which writes a title and
nothing else. There is no commit body, therefore no trailing signature, ever.

PR titles use the same format. PR bodies are problem and solution only.
