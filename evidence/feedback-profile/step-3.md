# Favourites, flag corrections and listing detail: evidence

Metadata only.

## Built

- `GET /api/favourites`, `DELETE /api/favourites/{listing_id}`, `POST /api/flags/{flag_id}/correction`,
  `GET /api/listings/{id}` in `worker/src/entry.py`.
- New table `favourite_removals` in `worker/schema.sql` (new table only; apply to an existing D1 with the
  `wrangler d1 execute --local --file schema.sql` command).
- `taste.removal_row` and `taste.current_factors`: a removal reason is a free-text-only feedback row. Only chips
  whose terms the reason matches are listed as offered, so an unrelated chip on that card is not lowered.
- Swipe route: a zero-change update re-reads the decision; a missing row is 404 `decision_not_found`, a present
  swiped row stays 409 `already_swiped`.
- Flag correction is one `UPDATE ... RETURNING` restricted to train-split listings. An eval-split or unknown id
  matches no row and gives 404 `flag_not_found`.
- The schema has no photo `skip` marker (`listing_media` has none, the deck does not filter), so nothing is filtered.

## Runs

Throwaway git worktree, `worker/scripts/seed.sh`, server on port 8840 (inspector 9270, fake upstream 8841):

    uvx --from workers-py pywrangler dev --port 8840 --inspector-port 9270 --var MUBIT_API_KEY:test-key-not-a-real-key --var GEMINI_BASE:http://127.0.0.1:8841 --var TFL_BASE:http://127.0.0.1:8841
    FAKE_PORT=8841 BASE_URL=http://localhost:8840 uv run --group dev pytest tests -q

- Full suite, first run on the seeded D1: 412 passed, exit 0.
- Full suite, second run on the same D1 (corrections persisted): 412 passed, exit 0.
- Server-less modules (chips, curator_unit, filters, mubit, prefs_unit, profile_unit, tfl_unit): 206 passed, exit 0.
- No paid calls; port 8787 not used.
