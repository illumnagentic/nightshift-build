# The curator reads the profile: evidence

Metadata only.

## Built

- `taste.latest(db, user_id)`: `(version, {factor: {direction, weight}})` from the user's latest `profile_versions`
  row, read as one row so the factors and the version cannot disagree. `(0, {})` when there is no row.
- `taste.recent_feedback(db, user_id)`: the last 10 feedback entries (not skipped, at least one chip or a non-null
  free text, on a swiped decision) and favourite removals, ordered by when each was last written, ties broken by
  decision id, returned newest last. Shapes: `{"listing_id", "action", "chips", "free_text"}` and
  `{"listing_id", "favourite_removed"}`.
- `deck._serve_new` reads both once, sends them in the user message, and stores the version on the
  `curator_calls` row and on every `decisions` row the call creates. `curator.py` is unchanged.
- Flag corrections needed no code: `curator._flag_digest` already prefers `corrected_text`. A test proves it.

## Frozen request parts

Recomputed on this tree with `python3 -I`, same method as the curator evidence (system prompt encoded as UTF-8;
generation config as `json.dumps(..., sort_keys=True)`):

- `SYSTEM_PROMPT` SHA-256 `9b5a064bb97282a54c8a2c85de7aae3d004592ed8c7f1d993536328864c3c777`: matches.
- `GENERATION_CONFIG` SHA-256 `10a031b51b80ab09b2ae3d2d5bfb3f17645df9d8659d9de0c6e0b7fc9d928248`: matches.
- The new tests hash the `systemInstruction` and `generationConfig` of the request body the fake recorded, with the
  same two constants.

## Trail query

For one user, profile version, its cause, the curator call that used that version, and that call's `mreq_` id
(replace `<user_id>`):

    SELECT v.version, v.cause_type, v.decision_id, v.flag_id, v.listing_id,
           c.call_id, c.created_at AS call_at, c.mreq_id
    FROM profile_versions v
    LEFT JOIN curator_calls c ON c.user_id = v.user_id AND c.profile_version = v.version
    WHERE v.user_id = '<user_id>'
    ORDER BY v.version, c.created_at;

Run with `npx wrangler d1 execute haka --local --command` against the test D1 after the suite. Output for one test
user (ids shortened; one row per version and call):

| version | cause_type | decision_id | flag_id | listing_id | call_id | call_at | mreq_id |
| ------- | ---------- | ----------- | ------- | ---------- | ------- | ------- | ------- |
| 1 | swipe | d_584e... | null | null | null | null | null |
| 2 | flag_correction | null | rm-172... | null | c_8edd... | 2026-1... | mreq_0... |

A version no call used has null call columns. A version used by several calls gives several rows.

## Runs

Throwaway git worktree, `worker/scripts/seed.sh`, server on port 8840 (inspector 9270, fake upstream 8841):

    uvx --from workers-py pywrangler dev --port 8840 --inspector-port 9270 --var MUBIT_API_KEY:test-key-not-a-real-key --var GEMINI_BASE:http://127.0.0.1:8841 --var TFL_BASE:http://127.0.0.1:8841
    FAKE_PORT=8841 BASE_URL=http://localhost:8840 uv run --group dev pytest tests -q

- Full suite, first run on the seeded D1: 416 passed, exit 0.
- Full suite, second run on the same D1: 416 passed, exit 0.
- Server-less modules (chips, curator_unit, filters, mubit, prefs_unit, profile_unit, tfl_unit): 206 passed, exit 0.
- No paid calls; port 8787 not used.
