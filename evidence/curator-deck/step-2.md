# Curator request and reply

- Date: 2026-10-25
- Source: `dataset/listings.sqlite` (488 train-split listings, photo flags included), read-only.
- Code: `worker/src/curator.py`. Metadata only: no listing rows and no prompt-sized payloads reproduced.

## Frozen task identity

| Part | Value |
| ---- | ----- |
| Model | `gemini-3.8-flash` |
| System prompt SHA-256 | `9b5a064bb97282a54c8a2c85de7aae3d004592ed8c7f1d993536328864c3c777` (2,249 characters, no digits) |
| Generation config SHA-256 (JSON, sorted keys, schema included) | `10a031b51b80ab09b2ae3d2d5bfb3f17645df9d8659d9de0c6e0b7fc9d928248` |
| Thinking | `thinkingConfig: {"thinkingLevel": "low"}`, temperature 0 |
| Response schema | `{"ranking": array of string}`, no enum |

Changing the prompt text, the schema or the config changes these hashes and restarts the
Mubit task count. Unit tests assert that two different buyers get byte-identical
`systemInstruction` and `generationConfig`.

## Request size, 30 candidates

Candidates are a seeded random sample (seed 7, sorted by id) of the train-split pool left
by the hard limits shown. Commute is set to 35 minutes on every candidate, stated prefs
are a short text with two soft wishes, taste profile and recent feedback are empty.
"Total" is system prompt plus user message plus schema. Approximate tokens are
characters divided by four.

| Hard limits | Pool | User message chars | Per candidate min / mean / max | Total chars | Approx tokens |
| ----------- | --: | --: | --: | --: | --: |
| none | 488 | 22,871 | 460 / 757 / 1,119 | 25,238 | 6,309 |
| up to 550000, 2+ bedrooms, flat or maisonette, EPC D or better | 74 | 21,558 | 447 / 713 / 1,121 | 23,925 | 5,981 |
| up to 900000, 3+ bedrooms, house | 104 | 22,377 | 464 / 740 / 994 | 24,744 | 6,186 |
| freehold, 2+ bedrooms, up to 700000 | 103 | 22,866 | 519 / 757 / 1,043 | 25,233 | 6,308 |

About 6,000 input tokens per call. A filled taste profile and recent feedback add to this;
the figures are the floor.

## Tests

`pytest tests/test_curator_unit.py tests/test_chips.py tests/test_filters.py tests/test_prefs_unit.py tests/test_mubit.py tests/test_tfl_unit.py -q`: 163 passed, exit 0.

Full suite in test mode (fake upstream on 8801, server on 8792, fresh seed, throwaway worktree with the same changes): 247 passed, exit 0.
