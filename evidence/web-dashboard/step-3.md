# Results tab

Date: 2026-10-25

## What the tab shows

A fourth tab, "Results", after Favourites. It fetches `GET /stats` each time it opens.

- Loading: "Loading…".
- Error: the API error message, or "Could not reach the server. Try again.", with a Retry button.
- Empty (all three arms null): "No evaluation has run yet." and nothing else.
- Mock mode only: a banner first, "Sample numbers from the mock, not real results".
- Fallback D (updated arm null): the note "The updated curator is not available, so only the base arms are shown."
- Chart 1, "Hits in the top 5", with a one-line definition, then the bar chart.
- Chart 2, "False-exclude rate", with a one-line definition, then the bar chart with percentage ticks, tooltip and table.
- Under each chart: "Across N held-out personas" when all present arms share one n (omitted otherwise), and "Error bars: ±1 standard deviation across held-out personas."
- Responses that arrive after the tab closes are ignored.

## Bundle check

The banner text must be in the mock build only. Count of files in `dist/assets/*.js` containing "Sample numbers from the mock":

| Build command | Build exit | Files containing the text |
| --- | --- | --- |
| `VITE_API_MODE=mock npm run build` | 0 | 1 |
| `npm run build` | 0 | 0 |
| `VITE_API_MODE=http npm run build` | 0 | 0 |

`dist` was left holding the plain build (a final `npm run build`, exit 0, 0 files containing the text).

## Commands (from `web/`)

- `npm run typecheck`: exit 0
- `npm test`: exit 0, 8 files, 186 tests passed
- `npm run build`: exit 0

## Browser checks

Built-in browser, mock dev server on port 5183, user alex, 2026-10-25.

- Results tab is the fourth tab. Shows the mock banner, "Hits in the top 5" (2.2 ± 0.8, 3.1 ± 0.7, 3.8 ± 0.6 in the fixed order, 0–5 axis) and "False-exclude rate" (31% ± 9%, 22% ± 7%, 15% ± 6%, 0–100% axis), each with its one-line explanation, "Across 5 held-out personas" and the error-bar caption.
- Keyboard: focusing the first bar announces "Base curator: 2.2 ± 0.8, 5 personas"; the chart element has role group.
- Show table: reveals Arm / Mean / Standard deviation / Personas for the three arms; the button changes to "Hide table" with aria-expanded true.
- Empty state (stats client overridden in the page to return three null arms): only "No evaluation has run yet." is shown.
- Fallback D (overridden to null the updated arm): the note "The updated curator is not available, so only the base arms are shown." appears and the missing bars read "Not available", not zero.
- 375 px wide: no sideways scrolling (page width 375), the four tabs fit (right edge 343 px, gaps 8 px), no overlapping chart text. Chart text renders about 9–10 px tall at this width, and the "Preferences" tab text (87 px) is slightly wider than its button (85 px).


### Each bar, after the tooltip placement change (2026-10-25)

Built-in browser, mock dev server on port 5183.

- Hover on all six bars (three hits, three rate): each shows its tooltip; no tooltip rectangle intersects that bar's value text.
- Keyboard (real Tab key presses from each chart heading): each of the six bars receives focus, announces e.g. "Base curator: 2.2 ± 0.8, 5 personas", and shows its tooltip (e.g. "Base curator · Mean 2.2 · SD 0.8 · Personas 5"); no tooltip covers that bar's value text.
- The two tall hits bars (Base + memory, Updated + memory) draw their tooltip in the bottom band above the baseline; the others use the top band.

## Code

The dashboard screen reuses the existing percent formatter exported from the stats model and the existing network error message from the deck state, instead of local copies.
