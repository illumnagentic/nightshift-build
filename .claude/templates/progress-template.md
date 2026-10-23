# Feature: {{FEATURE_NAME}}

- **Slug**: {{SLUG}}
- **Started**: {{DATE}}
- **Branch**: {{BRANCH}}
- **BASE_SHA**: {{BASE_SHA}}
- **Status**: in progress

---

## REQUIREMENTS (LOCKED)

<!-- Written once at kickoff, verbatim from the human. Never edited, never reworded,
     never tidied up. If it needs to change, it changes in AMENDMENTS below. -->

{{REQUIREMENTS}}

### Source

{{REQUIREMENTS_SOURCE}}

### Explicitly out of scope

{{OUT_OF_SCOPE}}

---

## AMENDMENTS

<!-- Append only. Each entry: date, what changed, who asked. Empty is normal. -->

_None._

---

## RULES IN FORCE

<!-- Filled at kickoff and confirmed by the human. One row per rule that governs this
     work: the rule, the file or tool that carries it, and what it applies to (code,
     comments, docs, commits, generated product output). Briefs cite rules from here.
     A rule not listed here is not enforced. A rule the human adds later goes here as
     a new row, with the date. -->

| Rule | Source | Applies to |
| ---- | ------ | ---------- |

---

## PLAN

<!-- Each step declares the files it may touch. A diff touching anything else fails
     review unless the extra file was declared here first, with a reason. -->

### Step 1 — {{STEP_TITLE}}

**Goal**: {{STEP_GOAL}}

**Files in scope**: {{STEP_FILES}}

**Done when**: {{STEP_DONE_WHEN}}

**Evidence location**: {{STEP_EVIDENCE}}

- [ ] Implemented
- [ ] Tested — evidence: (date)
- [ ] Best practices met — evidence: (date)
- [ ] Matches locked requirements — evidence: (date)
- [ ] No scope drift — evidence: (date)

<!-- Repeat the block above for each step. -->

---

## TRADEOFFS

<!-- Every shortcut, known limitation or deferred fix, logged the moment it is made.
     Format: date | step | what was traded away | why | what it would take to fix.
     A step cannot be marked done while it has an unlogged tradeoff.
     qa-gate fails the feature if anything here is unsigned by the human. -->

_None logged._

---

## SPOTTED, NOT FIXED

<!-- Problems noticed in passing that were deliberately left alone.
     Format: file:line | what is wrong | severity guess. -->

_None._

---

## VERIFICATION

<!-- Filled in by qa-gate at wrap-up. Not by the implementer. -->

- [ ] All step checkboxes ticked with evidence
- [ ] Every evidence path in this file exists
- [ ] Test suite run — result:
- [ ] Lint run — result:
- [ ] Typecheck run — result:
- [ ] Build run — result:
- [ ] Diff contains no files outside declared scope
- [ ] Tradeoff ledger reviewed and signed off by human
- [ ] Human eye test completed

---

## HANDOVER

<!-- qa-gate writes the plain-English summary for the human here at wrap-up. -->
