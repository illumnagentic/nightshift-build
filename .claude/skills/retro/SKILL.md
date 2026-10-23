---
name: retro
description: Log what went wrong with the kit itself after a feature, and propose concrete improvements to its skills and agents. Use when the human asks for a retro, asks how the process went, or says the workflow is annoying, slow, or getting in the way.
---

# Retro

This is a retro on the kit, not on the code. The question is whether the process helped
or got in the way, and what to change so the next feature goes better.

Run only when asked.

## 1. Gather

Read the feature's progress file: amendments, tradeoffs, spotted-not-fixed, and how
many steps failed review first time.

Then answer honestly, from what actually happened in this session:

- Which skill or agent fired when it should not have, or failed to fire when it should?
- Where did a subagent need more than one attempt, and why? A vague brief, a bad file
  scope, a requirement that was not as locked as it looked?
- Where did the guardrails cost more than they saved? The file-scope trip wire firing
  on a legitimate change, a review round that found nothing, a question that did not
  need asking.
- Where did something slip through that a guardrail should have caught?
- Where did the main context get bloated with work that should have been delegated?
- Did the plan survive contact? If steps were reordered, merged or abandoned, why?

Do not be diplomatic about the kit. It is a tool, it has no feelings, and a retro that
concludes everything went well is a wasted retro. If a rule is not earning its keep,
say so and say why.

## 2. Log it

Append to `.claude/template-feedback.md`:

```
## <date> — <feature slug>

**Repo**: <name> (<project type>)
**Steps**: <n> | **Failed first review**: <n> | **Amendments**: <n>

### Friction
- <what got in the way> | <where: skill/agent name> | <cost: time, tokens, rework>

### Escapes
- <what got through that should not have> | <which guardrail should have caught it>

### Worked well
- <keep this, and why — so it does not get removed in a later tidy-up>

### Proposed changes
- <file in the kit> | <specific change> | <what it would prevent or unblock>
```

Keep entries short and specific. "The reviewer was too strict" is useless. "The reviewer
failed step 3 because the file scope said `src/api/users.ts` but the route registration
lives in `src/api/index.ts`, which was a planning error, not drift" is usable.

## 3. Propose changes

Group what you have logged into concrete edits — which file, which line, what it should
say instead. A proposal that does not name a file is not a proposal.

Judge each against these, and say which you applied:

- **Does it generalise?** A fix for one repo's quirk belongs in that repo's
  `kit-config.md`, not in the shared kit. The kit stays repo-agnostic or it stops
  being reusable.
- **Is the rule earning its keep?** A guardrail that has never caught anything across
  several features is cost without benefit. Propose removing it. Resist the instinct to
  keep adding rules — a kit nobody follows because it is exhausting is worse than a
  smaller one they do.
- **Is it a rule problem or a briefing problem?** Most subagent failures are bad briefs,
  not bad rules. Fix the brief.
- **Would it have prevented a real escape?** Not a hypothetical one.

Show the human the proposals, shortest first, with the cost of each. Let them choose.
Do not apply changes to the kit without agreement.

## 4. Apply

For agreed changes, edit the kit files in `.claude/` directly and note in
`template-feedback.md` which proposals were applied and which were declined, with the
reason. The declined list matters: it stops the same idea being re-proposed every retro.

If the kit lives in a shared location that several repos copy from, say clearly that the
change is local to this repo until it is copied upstream, and which files to copy.

A retro's entry is copied by hand into the kit repo's `feedback/` directory, one file per
retro: `feedback/<date>-<repo>-<feature>.md`. A proposal declined for the kit as a whole
goes in the kit repo's `template-feedback.md` Declined proposals table, the kit-wide list.

## Scaling note

Every few features, read back over `template-feedback.md` as a whole rather than just
appending to it. Patterns only show up across entries: the same skill misfiring in
three repos, the same guardrail always being waived, the same kind of requirement
always needing an amendment. Those patterns are worth more than any single retro, and
they are the thing that tells you whether the kit is getting better or just bigger.
