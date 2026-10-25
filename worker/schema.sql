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

CREATE TABLE IF NOT EXISTS decisions (
  decision_id TEXT PRIMARY KEY,              -- opaque random string; one per card served
  user_id TEXT NOT NULL REFERENCES users(user_id),
  listing_id TEXT NOT NULL REFERENCES listings(id),
  source TEXT NOT NULL CHECK (source IN ('ranked', 'exploration')), -- never shown on the card face
  score INTEGER,                             -- the curator score at serve time
  curator_request_id TEXT,                   -- mreq_ id of the call that scored it; NULL = none
  profile_version INTEGER NOT NULL,          -- taste profile version the score was made under
  served_at TEXT NOT NULL,                   -- ISO 8601 UTC
  swiped_at TEXT                             -- ISO 8601 UTC; NULL = not swiped
);

CREATE INDEX IF NOT EXISTS decisions_user ON decisions (user_id);

CREATE TABLE IF NOT EXISTS offered_chips (
  decision_id TEXT NOT NULL REFERENCES decisions(decision_id) ON DELETE CASCADE,
  chip_id TEXT NOT NULL,                     -- a chip sent on the card; chips cut by the limit are not logged
  position INTEGER NOT NULL,                 -- 0-based place in the card's chips[]
  PRIMARY KEY (decision_id, chip_id)
);

CREATE TABLE IF NOT EXISTS curator_scores (
  user_id TEXT NOT NULL REFERENCES users(user_id),
  listing_id TEXT NOT NULL REFERENCES listings(id),
  profile_version INTEGER NOT NULL,          -- scored under this taste profile version
  score INTEGER NOT NULL CHECK (score BETWEEN 0 AND 100),
  reason TEXT,                               -- the curator's short reason; NULL = none given
  request_id TEXT,                           -- mreq_ id of the scoring call; NULL = none
  scored_at TEXT NOT NULL,                   -- ISO 8601 UTC
  PRIMARY KEY (user_id, listing_id, profile_version)
);
