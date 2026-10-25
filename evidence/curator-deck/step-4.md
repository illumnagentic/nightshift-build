# Live curator check through the deck endpoint

- Date: 2026-10-25
- Code: `worker/src/deck.py`, `worker/src/curator.py`, `worker/src/entry.py` at the commit before this step's doc edits.
- Run: normal dev server (real Mubit key from `worker/.dev.vars`, no base-URL overrides) in a throwaway worktree with a
  freshly seeded local D1, port 8798. One test user and one prefs row inserted directly into that D1, so no parse call was
  paid. No postcode, so no TfL call. Exactly one `GET /api/deck?n=10`. The test suite was not run against this server.
  Metadata only: no key, no response body, no prompt text stored.

## The call

| Item | Value |
| ---- | ----- |
| HTTP status | 200 |
| Latency | 5.29 s (curl total, one cold request) |
| Cards returned | 10, `empty_reason` null |
| Sources | positions 5 and 10 `exploration`, the other eight `ranked` |
| Exploration ranks | 19 and 20 of 30 (63rd and 67th percentile, inside the 50th to 80th band) |
| Ranked ranks | 1 to 8 |
| `feedback_required` | true on all ten |
| Prefs used | hard: max price 600000, min 2 bedrooms; soft: "bright rooms", "near a station" |

## The `curator_calls` row

| Column | Value |
| ------ | ----- |
| Rows | 1 |
| `status` | `ok` |
| `mreq_id` | `mreq_01a17242996078a2b319edda254622a5` (`mreq_` plus 32 hex characters, 37 in all) |
| `model` | `gemini-3.8-flash` |
| `profile_version` | 0 (empty taste profile) |
| Candidates sent | 30 |
| Ranking length | 30 (full order, no repair) |
| `error` | NULL |
| Prompt tokens | 6,995 |
| Output tokens | 335 |
| Thought tokens | NULL: Mubit's reply carried no thought-token count, so the low thinking setting produced none that were reported |
| `decisions` referencing the call | 10 (all ten served cards) |

The earlier size estimate was about 6,000 prompt tokens at K=30. The real figure is 6,995, about 17% more.
The ranking output is about 11 tokens per id.

Mubit's console was not opened. The `mreq_` id above is the one to look up there.

## Cost per call

Prices for `gemini-3.8-flash` are not confirmed. Two assumptions, with 1 USD = 0.75 GBP:

| Assumption | Input per million tokens | Output per million tokens | Cost per call | 150 calls | 1,000 calls | Share of 16 GBP credit at 1,000 |
| ---------- | ------------------------ | ------------------------- | ------------- | --------- | ----------- | -------------------------------- |
| Flash-class (assumed) | 0.30 USD | 2.50 USD | 0.00294 USD, 0.0022 GBP | 0.33 GBP | 2.20 GBP | 14% |
| Five times that (stress) | 1.50 USD | 12.50 USD | 0.01468 USD, 0.0110 GBP | 1.65 GBP | 11.01 GBP | 69% |

Even at five times the assumed price, 150 persona calls cost under 2 GBP. The credit is also spent on photo flags,
parsing and persona swipes, so the stress figure at 1,000 calls would leave little. The real price should be read from the
provider's bill after the first 50 calls, as decisions.md already requires.

## What this does and does not show

- The endpoint, the Mubit route, the fixed system prompt and schema, the ranking parser, the exploration slots and the
  call and decision records all work against the live model.
- One call is not a sample for ranking quality. Nothing here says whether the order is good.
- Whether Mubit groups the curator calls into one task was not checked (needs the Tasks page, a human step).
