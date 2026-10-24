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
  commute_postcode TEXT NOT NULL,            -- normalised: outward, space, inward (EC2N 2DB)
  max_commute_min INTEGER CHECK (max_commute_min BETWEEN 1 AND 180), -- NULL = no limit; the request value
  parsed_json TEXT NOT NULL CHECK (json_valid(parsed_json)), -- {hard, soft} after the code's checks
  parse_request_id TEXT,                     -- the parser call's Mubit mreq_ id
  commute_status TEXT NOT NULL CHECK (commute_status IN ('pending', 'ready', 'failed')),
  commute_fail_streak INTEGER NOT NULL DEFAULT 0, -- consecutive failed commute polls
  updated_at TEXT NOT NULL                   -- ISO 8601 UTC
);

CREATE TABLE IF NOT EXISTS commute_cache (
  listing_id TEXT NOT NULL REFERENCES listings(id),
  postcode TEXT NOT NULL,                    -- normalised, as in prefs.commute_postcode
  minutes INTEGER,                           -- shortest journey; NULL = TfL found no journey
  fetched_at TEXT NOT NULL,                  -- ISO 8601 UTC
  PRIMARY KEY (listing_id, postcode)         -- shared by every user with that postcode
);
