---
name: quick-change
description: Run a small, low-risk change in step mode through implementer and step-reviewer with no progress file, at the same correctness bar as a feature. Use when a change is a few files, one sitting, with no new capability, no calculation or data logic and no new dependency, such as a copy, layout or styling fix. Offered by Claude, never chosen silently.
---

# Quick change

A lighter lane for a small change. It drops the paperwork (progress file, requirements
lock, ledger, qa-gate, wrap-up). It keeps every check: the change is written by
`implementer`, checked by `step-reviewer`, and tested at the same bar as a feature.

## 1. Is it eligible

All of these must hold. Decide on size and risk, never on "it is frontend".

- One sitting, a few files, one clear intent.
- No new capability, dependency, or schema or API change.
- No calculation or data logic. A UI change that alters which figures or data are
  shown is not quick.
- Nothing under **Escalate paths** in `.claude/kit-config.md`.

If any fails, use `feature-kickoff`. If `.claude/scripts/kit-mode.sh status` is not
`step`, say the lane is step mode only and use `feature-kickoff`.

## 2. Offer it

One line naming the files, for example: "This looks like a quick change: `a.tsx`,
`a.test.tsx`. Use the quick lane?" Wait for the human's yes. For a UI change, show a
mock-up first and get a yes on it.

Check the branch: on the target branch, create a feature branch first.

## 3. Read what the repo requires

Read once, from `.claude/kit-config.md`: Commands, Brief notes, Run locally. Read a repo
rule file (CONTRIBUTING, coverage thresholds in test config, lint config, a scorecard
file) only for a requirement that kit-config does not already record.

State one line: which checks will run, and which repo requirements the kit cannot run
("not checked by the kit"). Never imply a requirement is checked when it is not.

## 4. Brief the implementer

Send a self-contained brief. The first line is `QUICK CHANGE`. There is no `PROGRESS:`
line, so the step-order hook does not apply. It carries, inline:

- the intent, in the human's words
- the files the implementer may touch, and what is out of scope
- the repo rules from step 3, and the Brief notes

Before sending it, on the branch the change will be committed to, record
`git rev-parse --short HEAD` as BASE.

## 5. Review

Send the reviewer the same header, intent and file list, plus `BASE: <sha>`, the repo
rules from step 3 and the Brief notes. The reviewer checks the change against each rule and says which
it cannot run. The implementer ends with
`kit-test.sh all` on the final tree so the reviewer's run is a cache hit; do not
replace that with a narrower run.

On the first FAIL, redo once through `implementer` with the reviewer's required fixes,
then review again.

## 6. One message to the human

The reviewer's verdict; the implementer's trade-offs and spotted items, one line each;
for UI, a screenshot (start the app with kit-config **Run locally**; do not assume a
tool is installed); any repo requirement not yet in kit-config, with a one-line addition
proposed so the next quick change reads it from there; and "commit as `<title>`?". The human decides trade-offs in that
same reply. Nothing is written to a ledger.

## 7. Commit

After the yes, stage the listed files and run `.claude/scripts/safe-commit.sh "<title>"`.
The commit is the record.

## Escape hatch

Stop and offer `feature-kickoff` if: more files are needed than were named, logic or
data handling turns up, a test fails for a non-obvious reason, or the reviewer fails
it twice.
