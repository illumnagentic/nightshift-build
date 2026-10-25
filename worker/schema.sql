-- App tables for the backend (SQLite dialect, Cloudflare D1).
-- Listing tables live in dataset/d1/schema.sql. Unknown is always NULL.

CREATE TABLE IF NOT EXISTS users (
  user_id TEXT PRIMARY KEY,                  -- opaque random string; never NULL
  username TEXT NOT NULL UNIQUE COLLATE NOCASE, -- unique ignoring case
  created_at TEXT NOT NULL                   -- ISO 8601 UTC
);

CREATE TABLE IF NOT EXISTS prefs (
  user_id TEXT PRIMARY KEY REFERENCES users(user_id), -- one row per user; a save replaces it
  text TEXT NOT NULL,                        -- the user's words, as sent
  commute_postcode TEXT,                     -- normalised: outward, space, inward (EC2N 2DB); NULL = no commute (optional)
  max_commute_min INTEGER CHECK (max_commute_min BETWEEN 1 AND 180), -- NULL = no limit; the request value
  parsed_json TEXT NOT NULL CHECK (json_valid(parsed_json)), -- {hard, soft} after the code's checks
  parse_request_id TEXT,                     -- the parser call's Mubit mreq_ id
  commute_status TEXT CHECK (commute_status IN ('pending', 'ready', 'failed')), -- NULL iff no postcode
  commute_fail_streak INTEGER NOT NULL DEFAULT 0, -- consecutive failed commute polls
  updated_at TEXT NOT NULL,                  -- ISO 8601 UTC
  CHECK ((commute_postcode IS NULL) = (commute_status IS NULL))
);

CREATE TABLE IF NOT EXISTS commute_cache (
  listing_id TEXT NOT NULL REFERENCES listings(id),
  postcode TEXT NOT NULL,                    -- normalised, as in prefs.commute_postcode
  minutes INTEGER,                           -- shortest journey; NULL = TfL found no journey
  fetched_at TEXT NOT NULL,                  -- ISO 8601 UTC
  PRIMARY KEY (listing_id, postcode)         -- shared by every user with that postcode
);

CREATE TABLE IF NOT EXISTS curator_calls (
  call_id TEXT PRIMARY KEY,                  -- 'c_' + hex; one per curator request, failures included
  user_id TEXT NOT NULL REFERENCES users(user_id),
  created_at TEXT NOT NULL,                  -- ISO 8601 UTC
  model TEXT NOT NULL,                       -- the model the request named
  profile_version INTEGER NOT NULL,          -- taste profile version in the request; 0 = empty profile
  prefs_updated_at TEXT NOT NULL,            -- prefs.updated_at the request was built from
  candidate_ids TEXT NOT NULL CHECK (json_valid(candidate_ids) AND json_type(candidate_ids) = 'array'), -- the sampled candidates, as sent
  ranking TEXT CHECK (ranking IS NULL OR (json_valid(ranking) AND json_type(ranking) = 'array')), -- full returned order after repair; NULL = failed
  status TEXT NOT NULL CHECK (status IN ('ok', 'incomplete', 'failed')), -- incomplete = reply repaired
  mreq_id TEXT,                              -- Mubit x-middleware-request-id; NULL = none came back
  error TEXT,                                -- why a failed call failed; NULL otherwise
  prompt_tokens INTEGER,                     -- usageMetadata; NULL = not reported
  output_tokens INTEGER,
  thought_tokens INTEGER
);

CREATE TABLE IF NOT EXISTS decisions (
  decision_id TEXT PRIMARY KEY,              -- 'd_' + hex; one per served card
  user_id TEXT NOT NULL REFERENCES users(user_id),
  listing_id TEXT NOT NULL REFERENCES listings(id),
  source TEXT NOT NULL CHECK (source IN ('ranked', 'exploration')),
  served_at TEXT NOT NULL,                   -- ISO 8601 UTC; shared by every card of one serve
  position INTEGER NOT NULL,                 -- 0-based order within its serve
  rank INTEGER NOT NULL,                     -- 1-based place in the curator call's ranking
  curator_call_id TEXT NOT NULL REFERENCES curator_calls(call_id),
  profile_version INTEGER NOT NULL,          -- taste profile version the curator call used
  offered_chips TEXT NOT NULL CHECK (json_valid(offered_chips) AND json_type(offered_chips) = 'array'), -- chip ids shown, in order
  action TEXT CHECK (action IN ('left', 'right', 'superlike')), -- NULL = not swiped yet
  swiped_at TEXT,                            -- ISO 8601 UTC; NULL = not swiped yet
  UNIQUE (user_id, listing_id)               -- a listing is served to a user once
);

CREATE TABLE IF NOT EXISTS favourites (
  user_id TEXT NOT NULL REFERENCES users(user_id),
  listing_id TEXT NOT NULL REFERENCES listings(id),
  decision_id TEXT NOT NULL,                 -- the superliked decision; no foreign key, a prefs re-save never drops a swiped one
  added_at TEXT NOT NULL,                    -- ISO 8601 UTC
  PRIMARY KEY (user_id, listing_id)
);

CREATE TABLE IF NOT EXISTS profile_versions (
  user_id TEXT NOT NULL REFERENCES users(user_id),
  version INTEGER NOT NULL,                  -- 1, 2, 3 ... per user; no row = version 0
  created_at TEXT NOT NULL,                  -- ISO 8601 UTC
  cause_type TEXT NOT NULL CHECK (cause_type IN ('swipe', 'feedback', 'flag_correction', 'favourite_removed')),
  decision_id TEXT,                          -- set for swipe and feedback
  flag_id TEXT,                              -- set for flag_correction
  listing_id TEXT,                           -- set for favourite_removed
  factors_json TEXT NOT NULL CHECK (json_valid(factors_json) AND json_type(factors_json) = 'array'), -- the profile at this version
  UNIQUE (user_id, version)
);

CREATE TABLE IF NOT EXISTS feedback (
  decision_id TEXT PRIMARY KEY REFERENCES decisions(decision_id), -- one row per swiped decision; a PUT replaces it
  user_id TEXT NOT NULL REFERENCES users(user_id),
  chips_json TEXT NOT NULL CHECK (json_valid(chips_json) AND json_type(chips_json) = 'array'), -- [{chip_id, strength, text}]
  free_text TEXT,                            -- NULL = none; never blank
  skipped INTEGER NOT NULL DEFAULT 0 CHECK (skipped IN (0, 1)), -- 1 only with no chips and no free text
  updated_at TEXT NOT NULL                   -- ISO 8601 UTC of the latest PUT
);

CREATE TABLE IF NOT EXISTS favourite_removals (
  user_id TEXT NOT NULL REFERENCES users(user_id),
  listing_id TEXT NOT NULL REFERENCES listings(id),
  decision_id TEXT NOT NULL,                 -- the superliked decision the favourite came from
  reason TEXT NOT NULL,                      -- the user's words; never blank
  removed_at TEXT NOT NULL,                  -- ISO 8601 UTC
  PRIMARY KEY (user_id, listing_id)
);
