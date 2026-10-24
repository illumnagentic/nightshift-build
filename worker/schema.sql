-- App tables for the backend (SQLite dialect, Cloudflare D1).
-- Listing tables live in dataset/d1/schema.sql. Unknown is always NULL.

CREATE TABLE IF NOT EXISTS users (
  user_id TEXT PRIMARY KEY,                  -- opaque random string; never NULL
  username TEXT NOT NULL UNIQUE COLLATE NOCASE, -- unique ignoring case
  created_at TEXT NOT NULL                   -- ISO 8601 UTC
);
