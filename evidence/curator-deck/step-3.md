# Deck endpoint and prefs re-save drop

- Date: 2026-10-25
- Code: `worker/src/deck.py`, `worker/src/entry.py`, `worker/schema.sql`; tests in `worker/tests/test_deck.py`.
- Run: test-mode dev server on a freshly seeded local D1 in a throwaway worktree, fake upstream on port 8801. No Mubit or TfL call was made. Metadata only.

## Results

| Run | Command | Result | Exit |
| --- | ------- | ------ | ---- |
| Deck tests alone | `pytest tests/test_deck.py -q` | 25 passed | 0 |
| Full suite, first run | `pytest tests -q` | 275 passed | 0 |
| Full suite, second run, same D1 | `pytest tests -q` | 275 passed | 0 |

## Tables

- `curator_calls`: one row per curator request, failures included: user, time, model, profile version, the prefs version it
  was built from, the sampled candidate ids, the full returned order (NULL on failure), status `ok` / `incomplete` / `failed`,
  the Mubit `mreq_` id when one came back, the error text, and the three token counts when reported.
- `decisions`: one row per served card: source, serve time, position in the serve, rank in the call's ranking, the call it
  came from, the profile version, the offered chip ids, and `action` / `swiped_at` left NULL for the swipe step. Unique per
  (user, listing).

## Empty profile

Until a taste profile exists, the request carries `taste_profile: {}` and `recent_feedback: []`, and both the call row and
each decision row store profile version `0`.

## Rows seen after the full suite (counts only)

- Calls: 30 `ok` (all with an `mreq_` id), 5 `failed` (all with an `mreq_` id, error text set, ranking NULL; the three
  failure kinds in the tests are an upstream 500, a reply that is not JSON, and a reply with 1 of 30 valid ids).
- Decisions: 250, of which 49 `exploration` and 201 `ranked`; every one joins to a call row; profile version 0 throughout.
- Token columns carry the fake's figures on `ok` rows and NULL on failures.

## What the tests cover

409 `prefs_missing`; 422 for `n` of 0, 11, -1, `abc`, empty and 2.5; default `n` of 10; ten cards with `exploration` at
positions 5 and 10, each at 50-80% of the fake's returned ranking; card and listing key sets; chips 1-8 with no commute chip
when minutes are unknown; `feedback_required` true throughout a first page; commute `null` without a postcode and
`{minutes: null, postcode, assumptions}` with one; a commute limit with nothing cached gives an empty `no_matches` deck and no
curator call; a refetch returns the same decisions with no new curator call; a 4-card first page then a 10-card page keeps
the first four and puts exploration at positions 5 and 10; a re-save leaves no old `decision_id`; six users' decks are
subsets of the train pool, with no repeat and none from the eval split (pool counts from `dataset/listings.sqlite`, read-only);
a 7-listing pool gives 7 cards with exploration at position 5; each of three failure markers gives 502 `curator_failed`
and a curator call; a failing curator with 3 outstanding cards gives 200 with only those 3; a failed call leaves no
decisions behind; the placement function falls back to a ranked card when the band is empty.

## Not covered by a test

- `exhausted`: a user cannot reach it before swipes exist, because unswiped cards are re-served and a page holds at most
  10 cards, so no API-level path empties the pool. The reason is `exhausted` when the filtered train pool is non-empty and
  every listing already has a decision.
- `feedback_required` false after 15 swipes, for the same reason.
