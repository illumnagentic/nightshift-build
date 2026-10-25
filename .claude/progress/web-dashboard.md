# Feature: F5 Dashboard (frontend)

- **Slug**: web-dashboard
- **Owner**: Yewen
- **Started**: 2026-10-25
- **Branch**: feat/web-dashboard
- **BASE_SHA**: 8d9ed8d3a929dfe540ea221d9e2d8d52247f6e97
- **Status**: in progress

---

## REQUIREMENTS (LOCKED)

Human, in session, 2026-10-25: "merged" (after the formatting PR, in reply to "tell me to go"
for F5).

Binding line from `docs/plan.md` (Frontend — Yewen):

> "**F5 Dashboard** — `feat/web-dashboard` — three-bar chart with error bars,
> false-exclude panel."

Binding lines from `docs/decisions.md` (Headline metric):

> "**Graph:** one chart, three bars — base curator / base + memory / updated + same
> memory. Bar 1 vs 2 shows memory (Layer 1); bar 2 vs 3 shows the adapter (Layer 2)."

> "**Primary number:** hits in the top 5 — of the curator's five highest-ranked
> held-out listings, how many the persona's hidden rules count as good. Averaged
> across held-out personas, with error bars for the spread."

> "**Second panel:** false-exclude rate — rule-good listings ranked below the cut."

> "D. none — graph shows bars 1 and 2; the update is shown with Mubit's version
> history, ..."

Binding lines from `docs/api-contract.md` (Stats):

> "`GET /stats` No header needed. Not per user. Feeds the dashboard graph."

> "`updated_memory` is `null` if no adapter route works (fallback D in decisions.md)."

> "Before any eval has run, all three arms are `null` and the response is still 200 ...
> The dashboard shows an empty state."

Answers to kickoff questions, human, 2026-10-25:

1. Charting: "Inline SVG" — hand-built SVG, no chart library, no new dependency.
2. Placement: "Fourth tab" — a "Results" tab after Deck / Preferences / Favourites, shown
   after sign-in.
3. Delegation: "Yes, delegate" — the orchestrator locks the plan with the advisor and
   approves step commits; the human keeps tradeoff sign-off, the eye test and any push/PR.

### Source

This session's conversation, quoted above. `docs/plan.md`, `docs/decisions.md`,
`docs/api-contract.md` on `main` at `8d9ed8d`. Chart rules from the `dataviz` skill.

### Explicitly out of scope

- Any backend, eval or scoring code; the stats endpoint itself (B7).
- Mubit version history, cost/latency panels, "matched X%" (fallback D extras).
- "Swipes until first great find" (recording illustration only, per decisions).
- Live updating; the tab fetches when opened.
- A chart library or any new dependency.
- Dark mode (the app is light-only by an earlier F2 decision).
- Exploration hit-rate metrics.
- Ticking `docs/plan.md` — done in the merging PR.

---

## AMENDMENTS

- 2026-10-25, orchestrator under the human's F5 delegation, after the Step 2 review
  (FAIL): focusable hit targets inside `<svg role="img">` are an ARIA anti-pattern. Step 2's
  done-when "the SVG has `role="img"` and an `aria-label` summary" is replaced by: the SVG
  has `role="group"` with an `aria-label` summary, and each bar's focusable hit target has
  `role="img"` with its own `aria-label`. Step 3's done-when gains: the rate chart passes a
  percentage `format` (ticks, tooltip and table show e.g. 31%, not 0.31); browser checks of
  keyboard focus on each bar and of the tooltip not hiding value text at about 375px.

---

## RULES IN FORCE

| Rule                                                                                                                                                                                 | Source                                                    | Applies to              |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------- | ----------------------- |
| Commits only via `.claude/scripts/safe-commit.sh`, title only, no signature; step commits approved by the orchestrator under delegation                                              | `.claude/CLAUDE.md`, kickoff answer 3                     | commits                 |
| Commit title `type(scope): message`; scope `web` (progress-only commits `kit`)                                                                                                       | `.claude/CLAUDE.md`, `.claude/kit-config.md`              | commits                 |
| Plain British English, short sentences, banned marketing words                                                                                                                       | `.claude/CLAUDE.md`                                       | docs, comments, UI text |
| No scope creep: touch only the step's declared files                                                                                                                                 | `.claude/CLAUDE.md` #1                                    | code, docs              |
| No new dependencies                                                                                                                                                                  | `.claude/CLAUDE.md` #2, kickoff answer 1                  | code                    |
| Never weaken a test to make it pass                                                                                                                                                  | `.claude/CLAUDE.md` #3                                    | tests                   |
| No speculative generalisation; walk the ladder                                                                                                                                       | `.claude/CLAUDE.md` #4                                    | code                    |
| Every tradeoff inserted as the last entry of TRADEOFFS (above `## SPOTTED, NOT FIXED`) when made, and the report says so                                                             | `.claude/CLAUDE.md` #5, `.claude/agents/implementer.md`   | progress file           |
| Implementer never ticks its own boxes                                                                                                                                                | `.claude/CLAUDE.md` #6                                    | progress file           |
| Evidence has no process wording; the process-wording check runs last and exits 0                                                                                                     | kit check script                                          | evidence                |
| This laptop runs Prettier on every Edit/Write; `web/src` is now Prettier-formatted, but check `git diff` for unrelated hunks                                                         | `.claude/kit-config.md` brief note                        | code                    |
| Use the existing `api` client and types; do not duplicate them                                                                                                                       | ladder rung 2                                             | code                    |
| Arms always in the fixed order base / base + memory / updated + memory, with fixed labels; a `null` arm is shown as missing, never as zero                                           | `docs/decisions.md`, `docs/api-contract.md` (Stats)       | code                    |
| One measure per chart, never two y-axes; hits on a 0–5 scale, false-exclude rate as a percentage on 0–100%                                                                           | `dataviz` non-negotiables                                 | code                    |
| Error bars show ±1 standard deviation, clipped to the axis range; `n_personas` shown                                                                                                 | `docs/decisions.md` (Headline metric)                     | code                    |
| Thin marks, recessive grid and axes, text in text colours not bar colours, a hover tooltip per bar, a table view of the numbers, colours validated with the dataviz validator script | `dataviz` skill                                           | code                    |
| In mock mode only, a visible "Sample numbers from the mock, not real results" banner above the charts; gated on `VITE_API_MODE === "mock"` and absent from other builds              | advisor at kickoff (the dashboard is the project's proof) | code                    |
| Done-when checks restate rules a step depends on; the human eye test is in VERIFICATION                                                                                              | F3 retro                                                  | plan                    |
| `docs/plan.md` changes only to tick F5, in the merging PR                                                                                                                            | `docs/decisions.md` (Overview)                            | docs                    |

---

## PLAN

All paths are relative to the repo root. Each step leaves the app working in mock mode.

### Step 1 — Stats view model

**Goal**: A pure, tested module that turns a `StatsResponse` into what the two charts show.

**Files in scope**: `web/src/dashboard/statsModel.ts`, `web/src/dashboard/statsModel.test.ts`,
`evidence/web-dashboard/step-1.md`.

**Done when**: for each metric (hits in the top 5; false-exclude rate) it returns the
three arms in the fixed order with fixed labels ("Base curator", "Base + memory",
"Updated + memory"), each with mean, standard deviation, its own `n_personas`, the error-bar low
and high clipped to the axis range (0–5 for hits; 0–1 for the rate), and display text
(e.g. "2.2 ± 0.8", "31% ± 9%"); a `null` arm is marked missing, never turned into zero;
`isEmpty` is true when all three arms are `null`; `updatedMissing` is true when only `updated_memory` is `null` (fallback D); a shared `n` is returned when all present arms agree, otherwise `null` (per-arm n still available); tests cover the contract example, all-null,
fallback D, clipping at both ends and the text; typecheck and tests exit 0; the
process-wording check exits 0.

**Evidence location**: `evidence/web-dashboard/step-1.md`.

- [x] Implemented — web/src/dashboard/statsModel.ts buildStatsModel; typecheck/build exit 0 (2026-10-25)
- [x] Tested — evidence: statsModel.test.ts 8 tests; npm test exit 0 (2026-10-25)
- [x] Best practices met — evidence: pure function, reuses api types, null arms never zero; check-process-refs exit 0 (2026-10-25)
- [x] Matches locked requirements — evidence: labels, order, axes 0-5/0-1, clipping, text, per-arm n, shared n null on mismatch, isEmpty/updatedMissing per done-when (2026-10-25)
- [x] No scope drift — evidence: git status shows only dashboard/ (2 files), evidence/web-dashboard/, progress file (2026-10-25)

### Step 2 — Bar chart component

**Goal**: An inline-SVG bar chart with error bars, hover tooltips and a table view, driven
by one metric from the view model.

**Files in scope**: `web/src/dashboard/BarChart.tsx`, `web/src/dashboard/dashboard.css`,
`evidence/web-dashboard/step-2.md`.

**Done when**: it draws one bar per arm in the fixed order on a single y-axis (0–5 or
0–100%), with a baseline, a few recessive gridlines, axis tick labels, the arm label under
each bar and the value text above it (text colours, not the bar colour); each bar has an
error bar (±1 SD, clipped) with caps; a missing arm shows a labelled empty slot ("Not
available"), never a zero bar; bars use one hue from the dataviz reference palette (`references/palette.md` in the skill directory) whose
contrast against the chart surface passes the validator script
(`node /private/tmp/claude-501/bundled-skills/2.1.308/4590c007cd3c4552cbbbdef4319a8183/dataviz/scripts/validate_palette.js`)
— run in light mode against the app's white surface, output recorded in the evidence; marks follow the dataviz mark specs (thin bars, 4px
rounded top, 2px gap); each bar has a hover and keyboard-focus tooltip with arm, mean, SD
and n; the SVG has `role="img"` and an `aria-label` summary, and a "Show table" toggle
reveals an HTML table of the same numbers; styles scoped under a dashboard root class; typecheck, tests and build exit 0;
the process-wording check exits 0. Not wired into the app yet.

**Evidence location**: `evidence/web-dashboard/step-2.md`.

- [x] Implemented — web/src/dashboard/BarChart.tsx; typecheck/build exit 0 after ARIA redo (2026-10-25)
- [x] Tested — evidence: npm test exit 0 (186 tests); no chart test, logged as tradeoff, browser pass in Step 3; validator exit 0 (2026-10-25)
- [x] Best practices met — evidence: svg role=group, per-bar role=img focusable with aria-label, no focusable inside role=img; table view; check-process-refs exit 0 (2026-10-25)
- [x] Matches locked requirements — evidence: done-when as amended 2026-10-25 (AMENDMENTS); order, missing arm, error bars, tooltip hover+focus, table (2026-10-25)
- [x] No scope drift — evidence: git status shows only BarChart.tsx, dashboard.css, evidence/web-dashboard/step-2.md, progress file (2026-10-25)

#### Redo of Step 2 — tooltip never covers the value

**Goal**: A bar's tooltip never covers that bar's value text.

**Files in scope**: `web/src/dashboard/BarChart.tsx`, `evidence/web-dashboard/step-2.md`.

**Done when**: the tooltip is drawn in the top band (as now) unless the active bar's value text falls inside that band, in which case it is drawn in a bottom band above the baseline; the rule is a small pure calculation in the component; nothing else changes; TRADEOFFS entry 2 (tooltip placement) is updated in place to describe what remains, or removed if nothing does; diff contains only intended hunks; typecheck, tests and build exit 0; the process-wording check exits 0.

**Evidence location**: `evidence/web-dashboard/step-2.md`.

- [x] Implemented — BarChart.tsx valueY/tipY; typecheck/build exit 0 (2026-10-25)
- [x] Tested — evidence: npm test exit 0 (186); rule checked by hand for top, missing and short bars; browser pass recorded in Step 3 (2026-10-25)
- [x] Best practices met — evidence: pure calculation, no new state; check-process-refs exit 0 (2026-10-25)
- [x] Matches locked requirements — evidence: top band unless value text overlaps, then bottom band; tradeoff 2 rewritten in place and accurate (2026-10-25)
- [x] No scope drift — evidence: diff touches only placement hunks in BarChart.tsx, step-2.md, progress file (2026-10-25)

### Step 3 — Results tab

**Goal**: A Results tab loads `GET /stats` and shows the two charts, the empty state and
the fallback-D note.

**Files in scope**: `web/src/dashboard/DashboardScreen.tsx`, `web/src/dashboard/dashboard.css`,
`web/src/App.tsx`, `evidence/web-dashboard/step-3.md`.

**Done when**: App gains a fourth tab "Results" after Favourites (same tab pattern,
`aria-current`); DashboardScreen renders only while its tab is open, calls `api.getStats()`
(no user header) each time it opens, shows a loading state, an error with Retry
(`error.message` for an ApiError, otherwise the generic message), the empty state "No
evaluation has run yet." when all arms are `null`, otherwise two titled charts — "Hits in
the top 5" (with a one-line explanation from the decisions text) and "False-exclude rate"
— with "Across N held-out personas" under each when all arms share one n (otherwise per-arm n in the tooltip and table) and the caption "Error bars: ±1 standard deviation across held-out personas." under each; in mock mode only, a banner "Sample numbers from the mock, not real results" above the charts, present in a mock build and absent from plain and http builds (bundle check recorded); when only `updated_memory` is `null` it
shows two bars and the note "The updated curator is not available, so only the base
arms are shown."; restated rules: fixed arm order, a `null` arm never shown as zero, one
measure per chart; switching user still resets to Deck; the rate chart passes a percentage `format` (AMENDMENTS 2026-10-25); orchestrator browser checks recorded in the evidence: the empty state and the fallback-D note shown by overriding `mockClient.getStats` in the page (no code change), and a pass at about 375px wide (no label collisions, tooltips by hover and keyboard, table toggle works, four tabs fit without sideways scrolling); typecheck, tests and build exit
0; the process-wording check exits 0.

**Evidence location**: `evidence/web-dashboard/step-3.md`.

- [x] Implemented — DashboardScreen.tsx, App.tsx Results tab; typecheck/build exit 0, bundle check mock=1 plain=0 http=0 (2026-10-25)
- [x] Tested — evidence: npm test exit 0; no screen test, logged as tradeoff; browser checks in evidence/web-dashboard/step-3.md (2026-10-25)
- [x] Best practices met — evidence: cancelled-fetch guard, error with Retry, role=alert, banner gated on VITE_API_MODE; check-process-refs exit 0 (2026-10-25)
- [x] Matches locked requirements — evidence: done-when as amended; texts exact, percent format passed to rate chart, n shown only when shared (2026-10-25)
- [x] No scope drift — evidence: git status shows only DashboardScreen.tsx, dashboard.css, App.tsx, evidence step-3.md, progress file; RULES table diff is padding only (2026-10-25)

#### Redo of Step 3 — reuse helpers and full browser checks

**Goal**: The Results screen reuses the existing percent formatter and network message, and the amended browser checks are recorded in full.

**Files in scope**: `web/src/dashboard/DashboardScreen.tsx`, `web/src/dashboard/statsModel.ts` (export the existing percent formatter only), `evidence/web-dashboard/step-3.md`.

**Done when**: DashboardScreen passes the percent formatter already in `statsModel.ts` (exported, not rewritten) instead of its own `percent`; its network message reuses `GENERIC_ERROR_MESSAGE` from `web/src/deck/deckState.ts`; no other change; orchestrator browser checks recorded: hover and keyboard focus on each of the six bars, each showing its tooltip without covering that bar's value text; typecheck, tests and build exit 0; the process-wording check exits 0.

**Evidence location**: `evidence/web-dashboard/step-3.md`.

- [x] Implemented — DashboardScreen uses exported pct and GENERIC_ERROR_MESSAGE; typecheck/build exit 0 (2026-10-25)
- [x] Tested — evidence: npm test exit 0 (186 tests); six-bar hover and keyboard checks in evidence/web-dashboard/step-3.md (2026-10-25)
- [x] Best practices met — evidence: duplicates removed, reuse of existing helpers; check-process-refs exit 0 (2026-10-25)
- [x] Matches locked requirements — evidence: done-when for the redo and amended browser checks recorded (2026-10-25)
- [x] No scope drift — evidence: diff touches only DashboardScreen.tsx, statsModel.ts (one-word export), evidence step-3.md (2026-10-25)

---

## TRADEOFFS

- Step 2, `web/src/dashboard/BarChart.tsx` | no automated test for the chart (no test file in scope, no DOM test library installed) | rendering, hover, focus and table toggle are unchecked until the browser pass | add a DOM test environment (new dependency, needs approval) or rely on the browser checks in Step 3
- Step 2, `BarChart.tsx` | when a bar's value text falls in the top band, the tooltip is drawn in a bottom band just above the baseline, where it can cover that bar's body and error bar (never its value text) | fixed two-band placement is the simplest rule that avoids the value text | HTML tooltip positioned from the pointer
- Step 2, `BarChart.tsx` | ticks are 0 to 5 in steps of 1 for hits (six gridlines), 0, 50%, 100% for the rate, keyed on `axisMax` | keeps hit ticks integer | pass ticks as a prop
- Step 3, `web/src/dashboard/DashboardScreen.tsx` | no automated test for the screen (no test file in scope, no DOM test library installed) | loading, error, empty, fallback and banner states are unchecked until the browser pass | add a DOM test environment (new dependency, needs approval)
- Step 3 | Chart text scales with the SVG and renders about 9–10 px tall at 375 px wide | the recording is made on a laptop where text is full size; a fixed font size needs per-width layout | render text outside the scaled SVG or set a minimum size at narrow widths

---

## SPOTTED, NOT FIXED

- `.claude/worktrees/` | untracked and not gitignored | low
- `web/src/deck/useDeck.ts` | `swipeBusy` ref race on a rapid user switch mid-swipe (from F2) | low
- `web/src/feedback/ChipDialog.tsx`, `FeedbackScreen.tsx` | strength labels written out in both files (from F3) | low
- `web/src/deck/deck.css` | orphaned `.deck-feedback` rules (from F3) | low
- `web/src/prefs/PrefsScreen.tsx`, `web/src/favourites/FavouritesScreen.tsx` | generic network message written out instead of reusing `GENERIC_ERROR_MESSAGE` (from F4 gate) | low
- `web/src/nav.css` | at 375 px the "Preferences" tab text (87 px) is wider than its button (85 px); four tabs are tight (from F4, seen in the F5 browser check) | low

---

## VERIFICATION

- [x] All step checkboxes ticked with evidence — 15 of 15 ticked, dated 2026-10-25, in step order (qa-gate 2026-10-25)
- [x] Every evidence path in this file exists — evidence/web-dashboard/step-1.md, step-2.md, step-3.md (qa-gate 2026-10-25)
- [x] Test suite run — result: `npm test` in a clean `git archive HEAD web` copy after `npm ci` (exit 0): 8 files, 186 tests passed, exit 0. Backend tests not run: no `worker/` files in the diff, and they need a seeded, running server (qa-gate 2026-10-25)
- [ ] Lint run — result: not configured (kit-config Lint blank, no `lint` script in web/package.json)
- [x] Typecheck run — result: `npm run typecheck` exit 0 (qa-gate 2026-10-25)
- [x] Build run — result: `npm run build` exit 0. Bundle check: mock build 1 file with the banner text, plain build 0, http build 0 (qa-gate 2026-10-25)
- [x] Diff contains no files outside declared scope — every file is in a step's Files in scope, plus this progress file (qa-gate 2026-10-25)
- [ ] Tradeoff ledger reviewed and signed off by human — 5 entries, all unsigned. Entry 2 describes the wrong cost: see HANDOVER
- [ ] Human eye test completed

QA-GATE: FAIL 2026-10-25 — 5 unsigned tradeoffs; the amended Step 3 browser check (tooltip does not hide value text) is not recorded, and by the chart geometry the tooltip does hide the hovered bar's own value text on two of the three hits bars.

---

## HANDOVER

### What was built

The app has a fourth tab, Results, after Favourites. It loads `GET /stats` each time it opens and shows two bar charts. The first is hits in the top 5 on a 0 to 5 axis, and the second is the false-exclude rate on a 0 to 100% axis. Each chart has three bars in a fixed order (Base curator, Base + memory, Updated + memory) with ±1 SD error bars, a tooltip per bar, and a Show table button. It handles loading, errors with Retry, the empty state ("No evaluation has run yet."), and fallback D, where the updated arm is missing: two bars, a "Not available" slot and a note. In mock builds a banner says the numbers are samples.

### What to check yourself

1. Make sure `web/.env` has `VITE_API_MODE=mock` (copy `web/.env.example` if it does not exist). Run `cd web && npm run dev` and open http://localhost:5173.
2. Pick or create a user, then press Results, the fourth tab. You should see the banner "Sample numbers from the mock, not real results", then "Hits in the top 5" with 2.2 ± 0.8, 3.1 ± 0.7 and 3.8 ± 0.6, then "False-exclude rate" with 31% ± 9%, 22% ± 7% and 15% ± 6%. Under each chart you should see "Across 5 held-out personas" and the error-bar caption.
3. Hover over each bar in turn. Then press Tab to move through the bars. A tooltip should appear each time. Look at Base + memory and Updated + memory on the hits chart. The tooltip sits over the top of the chart and covers that bar's own value text. Decide whether that is acceptable for the recording.
4. Press Show table under each chart. The table should match the bars. The rate table should show percentages, not 0.31.
5. Check the empty state. Open devtools, go to Console, and run:
   `const m = await import('/src/api/mock.ts'); m.mockClient.getStats = async () => ({ arms: { base: null, base_memory: null, updated_memory: null } });`
   Press Deck, then Results. You should see only "No evaluation has run yet."
6. Check fallback D. In the same console, run:
   `const real = (await import('/src/api/mock.ts')).mockClient; const s = { arms: { base: { hits_top5: { mean: 2.2, sd: 0.8, n_personas: 5 }, false_exclude_rate: { mean: 0.31, sd: 0.09, n_personas: 5 } }, base_memory: { hits_top5: { mean: 3.1, sd: 0.7, n_personas: 5 }, false_exclude_rate: { mean: 0.22, sd: 0.07, n_personas: 5 } }, updated_memory: null } }; real.getStats = async () => s;`
   Press Deck, then Results. You should see the note "The updated curator is not available, so only the base arms are shown." Each chart should draw two bars, with "Not available" in the third slot. The decisions text says "graph shows bars 1 and 2". Decide whether the empty third slot is what you want on the recording.
7. Narrow the window to about 375 px (devtools device toolbar). The four tabs should fit without sideways scrolling. Chart text will be small, around 9 to 10 px. That is a logged tradeoff.
8. Press Switch user while on Results. You should land on Deck after picking a user.
9. Read the five TRADEOFFS entries and sign each one, or reject it. Entry 2 says the tooltip can cover the value text of neighbouring bars. It does not. It stays inside its own bar's slot and covers that bar's own value text when the bar is tall.

### Tools that will help

- Browser devtools, Network tab: in http mode, open Results and confirm one `GET /api/stats` per opening, with no `X-User-Id` header. In mock mode there is no network call, because the mock answers in the page.
- Browser devtools, Console: the overrides in steps 5 and 6 are the only way to see the empty and fallback-D states without a backend.
- Devtools Accessibility pane, or VoiceOver (Cmd+F5): each bar should read as, for example, "Base curator: 2.2 ± 0.8, 5 personas". The chart itself is a group with a summary label.
- curl, once B7 lands: `curl -s http://localhost:8787/api/stats` should return the contract shape. Then run the web app with `VITE_API_MODE=http` and compare the numbers.

### What is not done

- Tradeoffs, all unsigned:
  1. No automated test for the chart. Rendering, hover, focus and the table toggle rest on browser checks only.
  2. The tooltip is drawn inside the SVG at a fixed height. As logged, it says it covers neighbouring bars. In fact it covers the hovered bar's own value text on Base + memory and Updated + memory in the hits chart, using the mock numbers.
  3. Ticks are hard-coded from `axisMax`: 0 to 5 in steps of 1, or 0%, 50% and 100%.
  4. No automated test for the screen. Loading, error, empty, fallback and banner states rest on browser checks only.
  5. Chart text scales with the SVG and renders about 9 to 10 px tall at 375 px wide.
- The amendment of 2026-10-25 asked for browser checks of keyboard focus on each bar and of the tooltip not hiding value text at about 375 px. The evidence records focus on the first bar only, records no hover check, and does not record the tooltip check.
- There is no lint command in this repo, so none was run.
- Spotted, not fixed: `.claude/worktrees/` is untracked and not gitignored. There is a `swipeBusy` race in useDeck (F2). Strength labels are written out twice (F3). There are orphaned `.deck-feedback` rules (F3). The generic network message is written out again in Prefs and Favourites (F4), and now in `DashboardScreen.tsx` too as `NETWORK_MESSAGE`, instead of reusing `GENERIC_ERROR_MESSAGE` from `web/src/deck/deckState.ts`. The "Preferences" tab text overflows its button at 375 px.
- The percentage formatter is written twice: `pct` in `statsModel.ts` and `percent` in `DashboardScreen.tsx`.
- Out of scope by design: the stats endpoint itself (B7), Mubit version history and cost panels for fallback D, live updating, and dark mode.

### What could bite you

- The dashboard has never seen a real `/stats` response, because B7 is not built. If the backend sends a shape that differs from the contract (for example, an arm with no `false_exclude_rate`), `buildStatsModel` throws inside the fetch handler. The screen then shows "Could not reach the server. Try again.", which points you at the network when the real fault is the response shape.
- In http mode with no backend running, the Vite proxy returns a 502. The screen will then show "Request failed with status 502.", not "Could not reach the server". That is accurate but looks rough if it shows up in a recording.
- If the real arms report different `n_personas` (for example, one arm evaluated on fewer personas), the "Across N held-out personas" line disappears. The count is then only in the tooltips and tables. Check this before recording.
