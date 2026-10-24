-- Listings schema for Cloudflare D1 (SQLite dialect).
-- Unknown is always NULL, never 0 or ''. Foreign keys are enforced by D1.

CREATE TABLE IF NOT EXISTS listings (
  id TEXT PRIMARY KEY,                       -- 'rm-<Rightmove property id>'; never NULL
  source TEXT NOT NULL CHECK (source IN ('rightmove', 'rapidapi_uk_real_estate_rightmove')), -- where the record came from
  source_id TEXT NOT NULL,                   -- id in the source system; never NULL
  url TEXT NOT NULL,                         -- listing page URL; never NULL
  price_gbp INTEGER NOT NULL CHECK (price_gbp BETWEEN 10000 AND 50000000), -- asking price, whole pounds
  price_qualifier TEXT CHECK (price_qualifier IN ('guide_price', 'offers_over', 'offers_in_region', 'fixed_price')), -- NULL = no qualifier shown
  bedrooms INTEGER CHECK (bedrooms BETWEEN 0 AND 10),   -- count, 0 = studio; NULL = unknown
  bathrooms INTEGER CHECK (bathrooms BETWEEN 0 AND 10), -- count; NULL = unknown
  property_type TEXT CHECK (property_type IN ('flat', 'maisonette', 'house', 'terraced', 'semi_detached', 'end_of_terrace', 'detached', 'bungalow', 'other')), -- NULL = not specified
  address TEXT,                              -- display address; NULL = unknown
  postcode TEXT,                             -- UK postcode as shown; NULL = unknown or only partial
  lat REAL CHECK (lat BETWEEN 50.5 AND 52.5),   -- degrees north, South East England; NULL = unknown
  lon REAL CHECK (lon BETWEEN -2.5 AND 1.5),    -- degrees east, South East England; NULL = unknown
  tenure TEXT CHECK (tenure IN ('freehold', 'leasehold', 'share_of_freehold')), -- NULL = unknown
  lease_years_remaining INTEGER CHECK (lease_years_remaining BETWEEN 1 AND 999), -- years; NULL = unknown or not leasehold
  service_charge_gbp_pa REAL CHECK (service_charge_gbp_pa BETWEEN 0 AND 100000), -- pounds per year; NULL = unknown
  ground_rent_gbp_pa REAL CHECK (ground_rent_gbp_pa BETWEEN 0 AND 100000),       -- pounds per year; NULL = unknown
  council_tax_band TEXT CHECK (council_tax_band IN ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H')), -- NULL = unknown or not yet banded
  epc_current TEXT CHECK (epc_current IN ('A', 'B', 'C', 'D', 'E', 'F', 'G')),     -- current EPC rating; NULL = unknown
  epc_potential TEXT CHECK (epc_potential IN ('A', 'B', 'C', 'D', 'E', 'F', 'G')), -- potential EPC rating; NULL = unknown
  floor_level TEXT,                          -- floor as the agent wrote it, lowercase; NULL = unknown
  key_features TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(key_features) AND json_type(key_features) = 'array'), -- JSON array of strings; '[]' = none listed
  description TEXT,                          -- plain text, no HTML; NULL = none
  agent_name TEXT,                           -- estate agent and branch; NULL = unknown
  listed_date TEXT CHECK (listed_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]*'), -- ISO 8601 UTC; NULL = unknown
  fetched_at TEXT NOT NULL CHECK (fetched_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]*'), -- ISO 8601 UTC, when we pulled the record
  parsed_fields TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(parsed_fields) AND json_type(parsed_fields) = 'array'), -- JSON array of field names parsed from free text; '[]' = none
  split TEXT NOT NULL CHECK (split IN ('train', 'eval')) -- evaluation holdout; listings at the same coordinates share a side
);

CREATE TABLE IF NOT EXISTS listing_media (
  listing_id TEXT NOT NULL,                  -- listings.id; never NULL
  kind TEXT NOT NULL CHECK (kind IN ('photo', 'floorplan', 'epc')), -- what the image shows
  position INTEGER NOT NULL CHECK (position >= 0), -- 0-based order within the listing and kind
  url TEXT NOT NULL,                         -- image URL; never NULL
  PRIMARY KEY (listing_id, kind, position),
  FOREIGN KEY (listing_id) REFERENCES listings(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS listing_stations (
  listing_id TEXT NOT NULL,                  -- listings.id; never NULL
  position INTEGER NOT NULL CHECK (position >= 0), -- 0-based order as listed, nearest first
  name TEXT NOT NULL,                        -- station name; never NULL
  distance_km REAL CHECK (distance_km BETWEEN 0 AND 100), -- kilometres; NULL = unknown
  types TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(types) AND json_type(types) = 'array'), -- JSON array of transport types, e.g. NATIONAL_TRAIN; '[]' = none given
  PRIMARY KEY (listing_id, position),
  FOREIGN KEY (listing_id) REFERENCES listings(id) ON DELETE CASCADE
);
