# Bar chart component

Date: 2026-10-25

## What it draws

`web/src/dashboard/BarChart.tsx` renders one `MetricModel` as an inline SVG (viewBox 480 by 270, scales with its container).

- One bar per arm in the model's fixed order, single y-axis. Ticks: 0 to 5 as integers for hits; 0%, 50%, 100% for the rate (the caller passes `format`).
- Baseline in a darker hairline, other gridlines a light grey just off white, solid.
- Bars 24px wide, 4px rounded top, square at the baseline, `#2a78d6`. Slot width is 141px, so the gap between bars is well over 2px.
- Error bar from `low` to `high` with 10px caps, 1.5px, `#52514e`, over a white 4px halo so it reads inside the blue bar.
- Value text (`bar.text`) above the error bar in `#0b0b0b`; arm label under the baseline; tick labels `#52514e`.
- A missing arm shows the label and the text "Not available" at the baseline. No bar is drawn. A present bar with mean 0 also draws no bar path but keeps its text and error bar.
- Each slot has a transparent hit rectangle (slot wide, full plot height, `tabIndex=0`). Hover and keyboard focus show a tooltip: arm, mean, SD, personas. A missing arm shows "Not available".
- The svg has `role="group"` with an `aria-label` summary. Each focusable hit rectangle has `role="img"` and its own `aria-label` (arm, mean ± SD text and persona count, or "Not available"), so no focusable element sits inside a `role="img"`. A "Show table" button toggles an HTML table (caption = title; columns Arm, Mean, Standard deviation, Personas).
- Styles are in `dashboard.css`, every rule under `.dashboard`.

## Palette validator

The dataviz palette validator, run in light mode against the app's white surface:

Command: `validate_palette.js "#2a78d6" --mode light --surface "#ffffff"` (exit 0)

```
Palette (light, surface #ffffff, categorical): 1 slots
  [PASS] Lightness band         all 1 inside L 0.43–0.77
  [PASS] Chroma floor           all 1 >= 0.1
  [PASS] CVD separation         n/a
  [PASS] Normal-vision floor    n/a
  [PASS] Contrast vs surface    all 1 >= 3:1

  → ALL CHECKS PASS
```

The validator covers categorical palettes only. The text colours `#0b0b0b` and `#52514e` are the reference palette's light text values and were not run through it.

## Commands (run from `web/`)

| Command | Exit | Result |
| --- | --- | --- |
| `npm run typecheck` | 0 | no errors |
| `npm test` | 0 | 8 files, 186 tests passed (no new tests; the component has no test file in scope) |
| `npm run build` | 0 | built |

## Not checked

No browser was used. Rendering, hover, focus, the tooltip position and the table toggle have not been seen. The build does not bundle the component yet because nothing imports it; typecheck is the only compile check.
