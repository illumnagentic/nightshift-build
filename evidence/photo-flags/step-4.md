# Flags in the D1 build

Date: 2026-10-25.

## Build report extract (`dataset/reports/d1-build-report.txt`)

```
  listings: 635
  listing_media: 6715
  listing_stations: 1889
  photo_flags: 14684
  foreign_key_check: clean
  integrity_check: ok
  flags by field: listing.floorplan_notes 1010, listing.sqm_estimate 626, photo.defects 546, photo.light 6045, photo.missing 81, photo.room 6045, photo.size_tricks 331
  skipped images removed from listing_media: floorplan 6, photo 120
  statements: 23923
  size: 10053183 bytes
  largest statement: 13327 bytes (D1 limit about 100000)
  self-check (schema.sql then seed.sql into empty in-memory db, foreign_keys=ON): photo_flags 14684 (listings.sqlite 14684), result: PASS
```

Skipped images: 126 URLs in the status lines; 134 media rows matched them. Eight URLs
are listed twice by their listing and were both skipped and flagged by the model; each
keeps its first copy (8 rows kept), so 126 rows are removed (120 photos, 6 floorplans)
and all 14,684 flag rows load. A flag pointing at an image that is not left aborts the
build; none does.

## Local D1 (`worker/scripts/seed.sh`)

The script ran to the end: schema (4 commands), app schema (3 commands), seed (23,923
commands), no error. Then:

```
select count(*) from photo_flags            -> 14684
select typeof(value), count(*) from photo_flags where field = 'sqm_estimate'
                                            -> integer 76, real 550
```

## Tests

`cd dataset && python3 -I -B -m unittest discover -s tests` -> Ran 158 tests, OK, exit 0.
Seven new tests in `tests/test_build_d1.py` (`FlagTests`): flags load with `typeof`
integer/text after schema then seed, real stays real, CHECK constraints reject six bad
rows, missing flags file aborts, skipped photos removed and renumbered without gaps, a
flag on a removed image aborts, a doubly-listed flagged URL keeps one copy.
