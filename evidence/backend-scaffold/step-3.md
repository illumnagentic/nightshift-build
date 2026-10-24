# Mubit gateway client evidence

Date: 2026-10-24

## Unit tests

`cd worker && uv run --group dev pytest tests/test_mubit.py -q` -> `10 passed in 0.02s`, exit 0.

## Live call (one, via `python3 -I worker/scripts/mubit_ping.py`)

Model `gemini-3.8-flash`, prompt "Reply with the single word OK.", `generationConfig.thinkingConfig.thinkingLevel = "low"`. The API accepted the setting; no retry was needed.

| Field | Value |
| ----- | ----- |
| HTTP status | 200 |
| modelVersion | gemini-3.8-flash |
| promptTokenCount | 8 |
| candidatesTokenCount | 1 |
| thoughtsTokenCount | absent from usageMetadata (no thought tokens reported; the earlier default-thinking call reported 79) |
| x-middleware-request-id | mreq_01a16ea1592f7052b9714df8ae035fb2 |

The call used urllib. The Workers `fetch` path in `generate_content` was not exercised.
