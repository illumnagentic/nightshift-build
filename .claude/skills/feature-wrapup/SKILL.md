---
name: feature-wrapup
description: Final quality and compliance pass on a finished feature, followed by a plain-English handover and a human eye test. Use when all steps of a feature are done, or when the human says a feature is finished, ready, or asks to wrap up.
---

# Feature wrap-up

A feature is not done when the code is written. It is done when it has been checked as
a whole, the human has seen what was traded away, and the human has looked at it with
their own eyes.

## 1. Preconditions

Do not start the wrap-up if any of these is true — fix them first and say which:

- Any step in the progress file has an unticked box.
- Any tick has no evidence against it.
- Any step's tick dates are earlier than an earlier step's (out-of-order completion).
- Any `Evidence location` that is a path does not exist. "The diff" is not a path.
- Any step's review ended in FAIL and was never re-reviewed.

## 2. Run the gate

Invoke `qa-gate` with the progress file path and the branch's BASE_SHA
(`.claude/scripts/kit-context.sh` prints it).

It runs in its own context deliberately: by this point the main conversation is long,
and a fresh reader catches things a tired one waves through. It reads the whole branch
diff, audits the progress file against the locked requirements, runs the repo's test,
lint, typecheck and build commands, checks the tradeoff ledger, and checks no file
outside a declared scope made it into the diff.

Do not run these checks yourself in the main context, and do not pre-judge the result.

## 3. On FAIL

Say so first, plainly, before anything else. Then list what failed, in order of
severity. Do not bury a failing test under a summary of what went well. Do not describe
a failure as "minor" — the human decides what is minor.

Then fix, through the normal route: a scoped `implementer` brief, then `step-reviewer`.
Then run the gate again. Not a shortcut fix in the main context.

## 4. Present the handover

Give the human `qa-gate`'s handover, in plain British English, short sentences:

- **What was built** — what the software does now that it did not before, in terms of
  what someone can actually do.
- **What to check yourself** — numbered, concrete, in order. Real commands, real URLs,
  real values. "Start the app with `npm run dev`, log in as dev@example.com, go to
  Settings, press Save with the name empty — you should see an inline error, not a
  crash." Not "verify the endpoint works".
- **Frontend** — if the repo has one, which screens changed and what should look or
  behave differently. Say where they should click.
- **Tools that will help** — Postman or curl with the exact request for API changes,
  browser devtools network tab for frontend calls, a database client for schema
  changes, the logs for background jobs. Say what to look for, not just the tool name.
- **What is not done** — every tradeoff, every limitation, every spotted-not-fixed
  item. Flatly. This section is the point of the exercise.
- **What could bite you** — the two or three most likely real-world failures. Specific.
  If part of it is fragile, name the part.

Keep it short enough to read in a couple of minutes. If it runs longer than that, the
feature was probably too big to review in one go, and you should say that too.

## 5. Get the two sign-offs

Ask for both explicitly. Neither is optional.

**The tradeoff sign-off.** Walk them through each unsigned entry in the ledger, one
line each: what was traded, why, what fixing it would take. Ask them to accept or
reject each. Mark accepted ones in the file with the date. Rejected ones become new
work, not a footnote.

**The eye test.** Ask them to actually run the checks above and confirm. Not to
approve on the strength of your summary. An agent reporting its own work as correct is
worth very little, and this is the step that catches what every automated check missed.

If the human signs off without running anything, that is their call — but say once,
plainly, that nothing has been verified by a human, and record it in the progress file.

## 6. Close it out

Once both sign-offs are in:

- Set `Status: complete` in the progress file, with the date.
- Offer the `commit-workflow` skill for anything uncommitted, and `pr-description`
  for the PR.
- Ask whether they want a retro. Do not run one uninvited.

Do not congratulate anyone. Say what is done and what is next.
