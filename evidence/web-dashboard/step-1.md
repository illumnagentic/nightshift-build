# Stats view model

Date: 2026-10-25

## Module

`web/src/dashboard/statsModel.ts` exports `buildStatsModel(stats)`. It returns:

- `hits` and `rate`: one model per metric (axis 0 to 5 and 0 to 1). Each holds the three
  bars in the fixed order, and `n`, the shared number of personas or `null`.
- A present bar carries mean, sd, its own n, error-bar low and high clipped to the axis,
  and display text. A `null` arm becomes `{ missing: true }` with its label and no numbers.
- `isEmpty`: all three arms are `null`.
- `updatedMissing`: only `updated_memory` is `null`.

## Tests (`web/src/dashboard/statsModel.test.ts`, 8 tests)

- Contract example: order, labels, mean, sd, n, text, axes, flags.
- Rate text as whole percentages.
- All arms `null`: empty, every bar missing, no numbers.
- Updated arm `null` with both base arms present: `updatedMissing`, bar missing not zero.
- `updatedMissing` stays false when a base arm is also missing.
- Clipping: hits low at 0, hits high at 5, rate high at 1, rate low at 0.
- Unclipped bar equals mean plus or minus sd.
- Differing n: shared n is `null`, per-arm n kept.

## Commands (run from `web/`)

| Command | Exit | Result |
| --- | --- | --- |
| `npm run typecheck` | 0 | no errors |
| `npm test` | 0 | 8 files, 186 tests passed |
| `npm run build` | 0 | built |
