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

**Evidence location**: the diff, plus command output recorded in the review.

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

**Goal**: Restyle the property card (paint chip), swipe actions and cues, deck states,
feedback screen and chip dialog against the tokens.

**Files in scope**: `web/src/deck/deck.css`, `web/src/feedback/feedback.css`,
`web/src/deck/DeckScreen.tsx` (className only, for unstyled state paragraphs)

**Done when**: typecheck, tests and build pass; card, actions, feedback (compulsory and
with Skip) and chip dialog render in the new design in mock mode at 375px and desktop.

**Evidence location**: the diff, plus command output recorded in the review.

- [x] Implemented — deck.css, feedback.css, DeckScreen.tsx glow-card restyle in diff vs d080bd1 (2026-10-25)
- [x] Tested — evidence: typecheck exit 0, npm test exit 0, build exit 0, run by reviewer (2026-10-25)
- [x] Best practices met — evidence: white .92 over #4f5fd0 = 4.85:1, over #4352c6 = 5.72:1; nav 44px; 3px focus outlines; reduced motion kept (2026-10-25)
- [x] Matches locked requirements — evidence: amendment glow-card tokens used; DeckScreen.tsx hunks className-only (2026-10-25)
- [x] No scope drift — evidence: Step 2 files only; check-process-refs exit 0 (2026-10-25)

**Redo (2026-10-25, step-reviewer FAIL)**: `.deck-card__details` (white .85) and
`.deck-card__assumptions` (white .8) fall to about 4.1–4.4:1 over `#4f5fd0`. Fix: raise
both to white at .92 or more. Also raise the photo nav circles from 40px to 44px.
Same files as Step 2.

### Step 3 — Prefs, favourites and dashboard

**Goal**: Restyle preferences, favourites (with remove dialog) and the results dashboard
against the tokens.

**Files in scope**: `web/src/prefs/prefs.css`, `web/src/favourites/favourites.css`,
`web/src/dashboard/dashboard.css`

**Done when**: typecheck, tests and build pass; the three screens render in the new
design in mock mode, chart error-bar halo matches its surface.

**Evidence location**: the diff, plus command output recorded in the review.

- [x] Implemented — prefs.css, favourites.css, dashboard.css glow restyle in diff vs d080bd1; no TSX changed (2026-10-25)
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

**Evidence location**: the diff, plus command output recorded in the review.

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

---

## TRADEOFFS

_None logged._

---

## SPOTTED, NOT FIXED

_None._

---

## VERIFICATION

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
