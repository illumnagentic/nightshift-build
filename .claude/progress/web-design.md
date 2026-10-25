# Feature: Web design (Tailwind restyle)

- **Slug**: web-design
- **Started**: 2026-10-25
- **Branch**: claude/frontend-design-tailwind-91a8a0
- **BASE_SHA**: d080bd1f4683c37c8d9e93f11eb9817048a724ce
- **Status**: in progress

---

## REQUIREMENTS (LOCKED)

> Let's come back to the front-end. I've recorded the demo for submission so now F6 can
> check off. Now let's work on the design. It's quite bare at the moment. For this
> session, we're mainly focusing on the design, don't change any functions and only
> change styling. install tailwind css and the front-end skills, use this image as
> reference for styling

Reference image: four stacked colour swatches over a sunlit balcony photo, each with a
bold expanded uppercase name and a small HEX / RGB / CMYK table with hairline rules:
Darlington `#ACCAB2`, Beeswax `#EBA752`, Grenadine `#D44720`, Cafe Latte.

Answers given in chat, 2026-10-25:

- Fonts: Google Fonts link (Archivo).
- Front-end skills: `frontend-design` already loaded at user level is enough; install
  nothing into the project.
- Design plan "paint chip" approved as shown:
  - Palette: Darlington `#ACCAB2` page, Chalk `#F4EFE4` surfaces, Grenadine `#D44720`
    (darkened `#B93C19` on filled buttons for contrast), Beeswax `#EBA752` with dark
    text only, Cafe Latte `#6E5A4A` muted text, Ink `#33281F` text.
  - Type: Archivo; expanded width bold for wordmark and headings, normal width for body.
  - One bold element: the property card as a paint chip, big Grenadine price, facts and
    details as a small spec grid with hairline Grenadine rules.
  - Buttons: Dislike Latte outline, Love solid Grenadine, Like solid Beeswax. Nav tabs
    as colour chips, active filled Grenadine.
  - Tailwind v4 via `@tailwindcss/vite`, palette as `@theme` tokens. Component CSS files
    rewritten against the tokens. App and UserPicker get utility classes. JSX changes are
    `className` strings only. No logic or copy changes.

### Source

Human instruction in chat, 2026-10-25, plus the approved plan above.

### Explicitly out of scope

- Any change to behaviour, state, API calls, props, handlers, copy text or tests.
- Changing JSX structure (adding, removing or reordering elements). Only `className`
  values may change.
- Motion values in `SwipeableCard.tsx` (drag, rotate, cue opacity).
- Dark mode.
- Installing skills into `.claude/skills`.

---

## AMENDMENTS

### 2026-10-25 — new style reference (human, in chat)

> change style: use this image instead

New reference: two "app cards" on white, large radius (~28px), soft glowing gradients
with a blurred glow, white text, frosted-glass circular icon buttons, clean grotesk
type, a large light-weight number ("$32,023") with a small label under it. Card one
hot magenta/pink fading to orange; card two periwinkle/blue fading to pale sky.

This replaces the paint-chip palette, Archivo and the "paint chip" card in
REQUIREMENTS (LOCKED). Everything else stands: Tailwind v4 tokens, styling only,
className-only JSX, Google Fonts link (font family changes to Inter), no new
dependencies, accessibility rules.

Design "glow cards":
- Page white `#ffffff`, soft surface `#f4f4f8`, ink `#1c1c28`, muted `#6b6b7b`, hairline
  `#e4e4ec`.
- Pulse gradient (pink): `#d6246e` → `#ec4f6a` → `#f2794a`. Income gradient (blue):
  `#4f5fd0` → `#7d8ce8` → `#b9d6fb`. White text only where contrast holds (deep end, or
  large text at 3:1).
- Property card: blue glow card, photo inset with large radius, price large and light
  in white. Love = pink gradient, Like = blue gradient, Dislike = white glass.
- Panels white, radius 24–28px, tinted glow shadows. Glass circular icon buttons.
- Steps 1 and 2 are redone against this. Step 3 follows it.


### 2026-10-25 — card depth (human, in chat)

> for the blue cards, if you look at the reference image, has a faint white inner
> shadow, and a few radial gradient. the pink card also can have a faint inner shadow

Read as: the blue property card gets a faint white inner shadow and several layered
radial gradients, as in the reference's blue card. The pink Love button (the only pink
gradient surface) gets a faint white inner shadow. The blue Like button gets the same
inner shadow to match. Added as Step 4.

### 2026-10-25 — Step 5 (arbiter): durable evidence

- **Goal**: re-run `npm run typecheck`, `npm test` and `npm run build` in `web/` on the
  branch head and record metadata only: command, exit code, test file and test counts,
  CSS and JS bundle sizes, commit SHA, date. No raw logs.
- **Files**: `evidence/web-design/checks.md`, and this progress file's evidence lines.
- **Done when**: `evidence/web-design/checks.md` exists, is committed on this branch,
  and records all three commands with exit 0.
- **Evidence location**: `evidence/web-design/checks.md`

---

## RULES IN FORCE

| Rule                                                                                                  | Source                                   | Applies to       |
| ----------------------------------------------------------------------------------------------------- | ---------------------------------------- | ---------------- |
| Styling only: no function, logic, copy or test changes; JSX edits limited to `className`              | Human, 2026-10-25                        | code             |
| No new dependencies beyond `tailwindcss` and `@tailwindcss/vite` (approved by "install tailwind css") | `.claude/CLAUDE.md` prohibition 2; human | code             |
| Google Fonts `<link>` approved; Inter since amendment (was Archivo)                                                           | Human, 2026-10-25                        | `web/index.html` |
| Touch only the files the step declares                                                                | `.claude/CLAUDE.md` prohibition 1        | code             |
| Never weaken a test                                                                                   | `.claude/CLAUDE.md` prohibition 3        | tests            |
| Accessibility kept: 44px targets, visible focus, reduced motion, WCAG AA text contrast                | `.claude/CLAUDE.md` ladder note          | code             |
| Prettier hook may reformat unrelated lines; check `git diff` after each edit                          | `.claude/kit-config.md`                  | code             |
| Plain British English, no banned words                                                                | `.claude/CLAUDE.md`                      | docs, commits    |
| Commits only via `safe-commit.sh`, title only                                                         | `.claude/CLAUDE.md`                      | commits          |

---

## PLAN

### Step 1 — Tailwind, tokens and app shell

**Goal**: Install Tailwind v4, define the palette and fonts as `@theme` tokens, and
restyle the page, header, nav and user picker.

**Files in scope**: `web/package.json`, `web/package-lock.json`, `web/vite.config.ts`,
`web/index.html`, `web/src/index.css`, `web/src/nav.css`, `web/src/App.tsx`,
`web/src/UserPicker.tsx`

**Done when**: `npm run typecheck`, `npm test` and `npm run build` pass; the user picker
and the signed-in shell (wordmark, signed-in line, Switch user, nav tabs) render in the
new palette and Archivo in mock mode; no non-`className` change in the TSX diff.

**Evidence location**: the diff, plus command output recorded in the review, plus `evidence/web-design/checks.md`.

- [x] Implemented — earlier ticks (paint-chip palette) superseded by 2026-10-25 amendment and unticked; re-ticked: Inter link, glow @theme tokens, white page, segmented-pill nav.css, white glow panel in UserPicker, solid pulse-1 Create user, in diff vs d080bd1 (2026-10-25)
- [x] Tested — evidence: typecheck exit 0, npm test exit 0, build exit 0, run by reviewer (2026-10-25)
- [x] Best practices met — evidence: contrast white/#d6246e 4.84, muted/white 5.23, muted/#f4f4f8 4.77, ink/#f4f4f8 15.36; min-h-11/12 targets, 3px focus-visible outlines, reduced-motion on nav (2026-10-25)
- [x] Matches locked requirements — evidence: amendment tokens exact in index.css @theme; no old-palette grep hits in the 5 files; TSX hunks className-only (2026-10-25)
- [x] No scope drift — evidence: Step 1 files only (index.html, index.css, nav.css, App.tsx, UserPicker.tsx, package.json, lock, vite.config.ts); check-process-refs exit 0 (2026-10-25)

**Redo (2026-10-25, step-reviewer FAIL)**: wordmark Grenadine on Darlington is about
2.5:1 and the latte 14px lines on Darlington about 3.7:1, both below WCAG AA. Fix:
wordmark to grenadine-deep (about 3.1:1, large text), signed-in and loading lines to ink.
Same files as Step 1.

### Step 2 — Deck and feedback

ESCALATED (arbiter) 2026-10-25: qa-gate findings 1-3. The "glow cards" amendment asks for Like = blue gradient, Dislike = white glass, price large and light; deck.css has solid #4f5fd0 Like, solid white Dislike with hairline, and price weight 600. Trigger: any change under web/. The fix is cheap (about 10-15 lines in web/src/deck/deck.css), but only the human can choose between fixing the CSS and rewording the amendment; an orchestrator report that the human saw these and asked only for depth is not consent.

**Human decision 2026-10-25**: "Match the brief". **Redo of Step 2**: Like as a blue gradient, Dislike as translucent white glass with blur, price at a light weight; contrast rechecked. File: web/src/deck/deck.css.

**Goal**: Restyle the property card (paint chip), swipe actions and cues, deck states,
feedback screen and chip dialog against the tokens.

**Files in scope**: `web/src/deck/deck.css`, `web/src/feedback/feedback.css`,
`web/src/deck/DeckScreen.tsx` (className only, for unstyled state paragraphs)

**Done when**: typecheck, tests and build pass; card, actions, feedback (compulsory and
with Skip) and chip dialog render in the new design in mock mode at 375px and desktop.

**Evidence location**: the diff, plus command output recorded in the review, plus `evidence/web-design/checks.md`.

- [x] Implemented — SUPERSEDES earlier Step 2 ticks (pre-redo 2). deck.css: Like blue gradient (radial highlight + linear #5866d6/income-1/#4352c6), Dislike white glass (translucent fill, blur, white rim), price 300 at 2.25rem; git diff HEAD shows only these hunks, Step 4 intact (2026-10-25)
- [x] Tested — supersedes earlier tick: typecheck exit 0, npm test exit 0, build exit 0, check-process-refs exit 0, run by reviewer on uncommitted deck.css vs HEAD 15eb378 (2026-10-25)
- [x] Best practices met — supersedes earlier tick: white on Like gradient incl. radial highlight, computed over label area 4.79-5.08:1 (widths 100-300px; extreme top-right corner 4.06 is outside text); ink on Dislike glass over white 16.85:1; white price 300 weight large text, worst-case 4.27:1 vs 3:1; Retry/Set preferences in .deck-screen__panel, not matched by :first-child (DeckScreen.tsx:157-177) (2026-10-25)
- [x] Matches locked requirements — supersedes earlier tick: amendment lines Like = blue gradient, Dislike = white glass, price large and light, all in deck.css (2026-10-25)
- [x] No scope drift — supersedes earlier tick: only web/src/deck/deck.css changed in web/ (2026-10-25)

**Redo (2026-10-25, step-reviewer FAIL)**: `.deck-card__details` (white .85) and
`.deck-card__assumptions` (white .8) fall to about 4.1–4.4:1 over `#4f5fd0`. Fix: raise
both to white at .92 or more. Also raise the photo nav circles from 40px to 44px.
Same files as Step 2.

### Step 3 — Prefs, favourites and dashboard

ESCALATED (arbiter) 2026-10-25: qa-gate finding 4. The unclassed Retry <button> at web/src/dashboard/DashboardScreen.tsx:74 loses its styling under Tailwind preflight and falls under 44px, breaking the 44px-targets rule in RULES IN FORCE. Trigger: any change under web/. Proposed fix, about 15 lines, CSS only, no TSX change: a `.dashboard > button` rule in web/src/dashboard/dashboard.css with min-height 44px, padding, border and fill from the @theme tokens, and a 3px focus-visible outline matching the other buttons.

**Human decision 2026-10-25**: "Yes, fix it". **Redo of Step 3**: the CSS fix above, in web/src/dashboard/dashboard.css.

**Goal**: Restyle preferences, favourites (with remove dialog) and the results dashboard
against the tokens.

**Files in scope**: `web/src/prefs/prefs.css`, `web/src/favourites/favourites.css`,
`web/src/dashboard/dashboard.css`

**Done when**: typecheck, tests and build pass; the three screens render in the new
design in mock mode, chart error-bar halo matches its surface.

**Evidence location**: the diff, plus command output recorded in the review, plus `evidence/web-design/checks.md`.

- [x] Implemented — prefs.css, favourites.css, dashboard.css glow restyle in diff vs d080bd1; no TSX changed (2026-10-25)
- [x] Redo implemented (supersedes earlier Step 3 ticks) — `.dashboard button:not([class])` rule + hover + focus-visible + reduced-motion entry in dashboard.css only; only unclassed button is Retry (DashboardScreen.tsx:74), `.chart__toggle` is classed (BarChart.tsx:189) so not matched (2026-10-25)
- [x] Redo tested (supersedes earlier) — typecheck exit 0, npm test exit 0, build exit 0, run by reviewer vs HEAD 15eb378 (2026-10-25)
- [x] Redo best practices (supersedes earlier) — min-height 48px, 3px focus-visible outline income-1 on white (~5.4:1), ink/white 16.85, ink/mist hover 15.36; check-process-refs exit 0 (2026-10-25)
- [x] Tested — evidence: typecheck exit 0, npm test exit 0, build exit 0, run by reviewer (2026-10-25)
- [x] Best practices met — evidence: white/#d6246e 4.84, muted/white 5.23, #9d1450/#fdeaf1 6.88, ink/white 16.85; 44px+ targets, 3px focus-visible outlines, reduced-motion blocks kept, .favourites-dialog margin:auto (2026-10-25)
- [x] Matches locked requirements — evidence: all tokens exist in index.css @theme; no --pf-/--fv-/system-ui left; chart halo uses --color-page matching panel; every TSX class has a selector (favourites-screen__address had none before either) (2026-10-25)
- [x] No scope drift — evidence: only the 3 declared CSS files; check-process-refs exit 0 (2026-10-25)

### Step 4 — Card depth

**Goal**: Faint white inner shadow and layered radial gradients on the blue property
card; faint white inner shadow on the pink Love button and the blue Like button.

**Files in scope**: `web/src/deck/deck.css`

**Done when**: typecheck, tests and build pass; card body text keeps WCAG AA (white text
at least 4.5:1 for small text over the deepest-lightened region behind it); the card
and buttons show the inner glow in mock mode.

**Evidence location**: the diff, plus command output recorded in the review, plus `evidence/web-design/checks.md`.

**Redo (2026-10-25, step-reviewer FAIL)**: feature tags (white on white .16 fill, about
3.9–4.3:1) and commute pill (white on white .22 fill, about 3.5–3.9:1) fail AA; these
came from Step 2. The bottom-right sky glow puts the content-box corner at 4.47:1. Fix:
dark glass fill `rgba(28,28,40,.2)` with the white border kept on tags and pill; sky
glow alpha .35 → .25. Same file.

- [x] Implemented — deck.css card: 5 layered radial/linear backgrounds, inset white shadow; Love and Like buttons inset shadow; redo of tags, pill, sky alpha in diff (2026-10-25)
- [x] Tested — evidence: typecheck exit 0, npm test exit 0, build exit 0, run by reviewer (2026-10-25)
- [x] Best practices met — evidence: composited worst case white on tag/pill fill 5.71:1; white .92 small text in content box 4.56:1 (corner 4.73); price large text 4.27:1 vs 3:1 (2026-10-25)
- [x] Matches locked requirements — evidence: amendment "card depth": faint white inner shadow and radial gradients on blue card, inner shadow on Love and Like in deck.css (2026-10-25)
- [x] No scope drift — evidence: only web/src/deck/deck.css changed for Step 4; check-process-refs exit 0 (2026-10-25)

### Step 5 — Durable evidence (arbiter)

**Goal**: Re-run typecheck, test and build in `web/` on the branch head and record
metadata only (command, exit code, test counts, bundle sizes, commit SHA, date).

**Files in scope**: `evidence/web-design/checks.md`, this progress file's evidence lines

**Done when**: `evidence/web-design/checks.md` exists, is committed on this branch, and
records all three commands with exit 0.

**Evidence location**: `evidence/web-design/checks.md`

- [ ] Implemented
- [ ] Tested — evidence: (date)
- [ ] Best practices met — evidence: (date)
- [ ] Matches locked requirements — evidence: (date)
- [ ] No scope drift — evidence: (date)

---

## TRADEOFFS

_None logged._

---

## SPOTTED, NOT FIXED

- (qa-gate 2026-10-25) The Like button's blue styling in web/src/deck/deck.css relies on `:last-child` in the action row; reordering or adding a button would move the styling silently. A Like-specific className would fix it. — accepted by arbiter 2026-10-25: breaks no rule in force or amendment line, buttons are not being reordered in this feature, and the fix would be a further web/ change

---

## VERIFICATION

- [x] All step checkboxes ticked with evidence — all 20 PLAN boxes ticked, dated 2026-10-25, in step order (qa-gate 2026-10-25)
- [x] Every evidence path in this file exists — no evidence paths; every step says "the diff, plus command output recorded in the review", and that output is not stored anywhere durable (qa-gate 2026-10-25)
- [x] Test suite run — result: `cd web && npm test`, 8 files, 186 tests passed, exit 0 (qa-gate 2026-10-25)
- [ ] Lint run — result: not configured in kit-config
- [x] Typecheck run — result: `cd web && npm run typecheck`, exit 0 (qa-gate 2026-10-25)
- [x] Build run — result: `cd web && npm run build`, exit 0, CSS 35.14 kB, JS 439.99 kB (qa-gate 2026-10-25)
- [x] Diff contains no files outside declared scope — all code files declared; `docs/plan.md` (F6 tick) and this progress file are allowed by safe-merge.sh (qa-gate 2026-10-25)
- [ ] Tradeoff ledger reviewed and signed off by human — no entries; nothing to sign
- [ ] Human eye test completed — not human-verified (full automation) — smoke check: Vite dev server in mock mode on :5181 served `/` (200) with the Inter Google Fonts link; `/src/index.css` compiled with `--color-income-1: #4f5fd0`, `.min-h-11` and `.bg-pulse-1`; `/src/deck/deck.css` 200. The orchestrator checked by eye in mock mode: user picker, deck card with Like, Love and Dislike, compulsory feedback and chip dialog, prefs, empty favourites, results. Not seen: favourites remove dialog, dashboard error state, deck blocked and error panels.

QA-GATE: FAIL 2026-10-25 — three lines of the "glow cards" amendment unmet (Like not a blue gradient, Dislike not white glass, price not light weight); dashboard Retry button lost all button styling under Tailwind preflight.

---

## HANDOVER

**What was built**

The web app has a new look. It now uses Tailwind v4 with a white page, the Inter font, and soft pink and blue "glow card" colours. The property card is a blue gradient card with a faint inner glow, the photo inset, and white text. Every screen (user picker, deck, feedback, chip dialog, prefs, favourites, results) uses the same colours. Behaviour, copy and tests are unchanged. `docs/plan.md` also ticks F6 (recording).

**What to check yourself**

1. In `web/`, run `npm ci`, then `VITE_API_MODE=mock npm run dev`. Open http://localhost:5173.
2. User picker: a white rounded panel. "Create user" is solid pink with white text. Create a user and select it.
3. Deck tab: the card is blue with a white inner edge. Look at the three buttons under it. Dislike is plain white. Love is a round pink gradient with a heart. Like is solid blue, not a gradient. Decide if that is what you wanted (see What is not done).
4. Look at the price on the card. It is semibold (600), not light. Decide if that matches your reference.
5. Swipe a card. Check the feedback screen and tap a chip. The dialog should sit centred with a blurred backdrop.
6. Prefs and Results tabs: white panels, pink primary button on prefs, blue bars on the chart.
7. Dashboard error state. Run without mock mode and with the worker stopped (`npm run dev` only), then open Results. The "Retry" button now looks like plain text, with no border or fill. This is a bug.
8. Favourites with at least one saved property (needs the real worker). Press Remove. Check that the dialog is centred and readable. Nobody has looked at it yet.
9. Narrow the window to 375px. Check that the nav pills wrap and the card fits.

**Tools that will help**

- Browser devtools, Elements panel: select the Like button and read its `background`. It is `rgb(79, 95, 208)`, solid.
- Devtools, Rendering panel, "Emulate CSS prefers-reduced-motion": hover transitions should stop.
- Devtools, Network tab with "Offline" ticked: Inter fails to load and text falls back to the system font. Do this before recording.
- Devtools contrast picker on the white text over the card, especially the feature tags and the bottom of the card.

**What is not done**

- Like is solid blue (`#4f5fd0`), not the blue gradient the amendment asks for.
- Dislike is solid white with a grey hairline, not "white glass" (no translucency or blur).
- The card price is weight 600. The reference asks for a large, light number.
- The dashboard "Retry" button (`web/src/dashboard/DashboardScreen.tsx` line 74) has no class. Tailwind's reset strips its border and fill, so it reads as plain text and is under 44px tall.
- The favourites remove dialog, the dashboard error state and the deck blocked and error panels were not checked by eye.
- Step evidence is "command output recorded in the review". That output is not saved anywhere you can look at now.
- The REQUIREMENTS block could not be checked for edits. The progress file first appears in the same commit as the restyle.
- Tradeoff ledger: no entries.

**What could bite you**

- The Like button's blue look comes from `:last-child` in `deck.css`. If anyone reorders or adds a button in the action row, the wrong button turns blue and Like goes white, with no error.
- Inter loads from Google Fonts. Record offline or on a flaky network and the font falls back to the system font, so the recording looks different from what you checked.
- Tailwind's reset (preflight) applies to the whole app. Any future element with no class (a button, list or heading) loses its browser styling. The Retry button is the one case found now. New unstyled markup will look broken in the same way.
