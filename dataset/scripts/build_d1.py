"""Build listings.sqlite and d1/seed.sql from listings.jsonl and d1/schema.sql.

The schema's CHECK and foreign-key constraints are the validation: the first row
that breaks one aborts the build with the listing id and the SQLite error.
photo_flags.jsonl (written by flag_images.py) supplies the photo_flags table and the
list of photos the model skipped (logos, duplicates), which are dropped from
listing_media. A missing photo_flags.jsonl aborts the build.
Reads only files already on disk. Makes no network requests.

Usage (from the dataset/ directory):
  python3 -I -B scripts/build_d1.py --dataset .
"""
import argparse
import hashlib
import json
import os
import random
import re
import sqlite3
import sys
from collections import Counter

TABLES = ["listings", "listing_media", "listing_stations", "photo_flags"]
LISTING_COLS = [
    "id", "source", "source_id", "url", "price_gbp", "price_qualifier", "bedrooms", "bathrooms",
    "property_type", "address", "postcode", "lat", "lon", "tenure", "lease_years_remaining",
    "service_charge_gbp_pa", "ground_rent_gbp_pa", "council_tax_band", "epc_current",
    "epc_potential", "floor_level", "key_features", "description", "agent_name", "listed_date",
    "fetched_at", "parsed_fields", "split",
]
JSON_COLS = {"key_features", "parsed_fields"}
MEDIA_COLS = ["listing_id", "kind", "position", "url"]
STATION_COLS = ["listing_id", "position", "name", "distance_km", "types"]
FLAG_COLS = ["flag_id", "listing_id", "scope", "field", "value", "observation", "source_photo",
             "confidence", "uncertainty", "room", "corrected_text"]
D1_STATEMENT_LIMIT = 100000  # bytes per statement, about


BANDS = "ABCDEFG"
EPC_SEED = 20261024
SPLIT_SEED = 20261025  # separate from EPC_SEED so the split never moves the EPC draws
EVAL_SHARE = 0.25
# Postcode areas counted as London, as in the README area table. CR and KT are
# included: every CR and KT listing in the data is in Croydon or Kingston, both
# London boroughs (some real CR/KT postcodes, such as Caterham or Esher, are Surrey).
LONDON_AREAS = {"E", "EC", "N", "NW", "SE", "SW", "W", "WC", "BR", "IG", "CR", "KT"}


def demo_epc(r, rng, letters, weights):
    """Return a copy of record r prepared for the demo database.

    Drops every EPC media item (PDFs and charts), since made-up letters would
    contradict them. Keeps a real epc_current, otherwise draws one weighted by the
    real letter counts. epc_potential is always made up: epc_current improved by
    0, 1 or 2 bands (weights 20/50/30), never better than A.
    """
    out = dict(r)
    out["media"] = [m for m in r["media"] if m["kind"] != "epc"]
    if out["epc_current"] is None:
        out["epc_current"] = rng.choices(letters, weights)[0]
    gain = rng.choices([0, 1, 2], [20, 50, 30])[0]
    out["epc_potential"] = BANDS[max(0, BANDS.index(out["epc_current"]) - gain)]
    return out


def area_of(r):
    """Postcode area letters ('SE' for 'SE15 4QA'), or '' when the postcode is unknown."""
    m = re.match(r"[A-Z]+", r["postcode"] or "")
    return m.group() if m else ""


def coord_key(r):
    """Listings at the same coordinates (4 dp) are one group. No coordinates: a group of one."""
    if r["lat"] is None or r["lon"] is None:
        return ("id", r["id"])
    return (round(r["lat"], 4), round(r["lon"], 4))


def assign_split(records):
    """Return {id: 'train' | 'eval'}. Groups of same-coordinate listings stay together.

    Each group's side comes from a hash of SPLIT_SEED and the group key alone, so it
    does not depend on any other listing: adding listings never moves an existing one.
    The eval share is therefore about EVAL_SHARE by chance, not exactly balanced.
    """
    out = {}
    for r in records:
        digest = hashlib.sha256(("%d|%r" % (SPLIT_SEED, coord_key(r))).encode()).digest()
        value = int.from_bytes(digest[:8], "big") / 2 ** 64
        out[r["id"]] = "eval" if value < EVAL_SHARE else "train"
    return out


def check_duplicates(records):
    """Abort the build if two listings are the same home.

    Same id or any shared photo URL always counts. Same coordinates (4 dp) + bedrooms +
    price counts unless the same agent listed both (distinct units in one new-build).
    """
    seen = {}
    for r in records:
        keys = [("id", r["id"])] + [("photo URL", m["url"]) for m in r["media"] if m["kind"] == "photo"]
        if r["lat"] is not None and r["lon"] is not None:
            keys.append(("coordinates + bedrooms + price",
                         (round(r["lat"], 4), round(r["lon"], 4), r["bedrooms"], r["price_gbp"])))
        for k in keys:
            other = seen.setdefault(k, r)
            if other is r:
                continue
            if k[0].startswith("coordinates") and r["agent_name"] and r["agent_name"] == other["agent_name"]:
                continue
            print("build failed: listings %s and %s are duplicates (same %s: %s)"
                  % (other["id"], r["id"], k[0], k[1]), file=sys.stderr)
            sys.exit(1)


def read_flags(path):
    """Return (flag rows as dicts, {listing_id: set of skipped image URLs}) from photo_flags.jsonl.

    Lines with record_type listing_status describe a listing's run; every other line is a flag.
    """
    if not os.path.exists(path):
        print("build failed: %s not found (run scripts/flag_images.py first)" % path, file=sys.stderr)
        sys.exit(1)
    flags, skipped = [], {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("record_type") == "listing_status":
                skipped.setdefault(rec["listing_id"], set()).update(s["url"] for s in rec["skipped"])
            else:
                flags.append(rec)
    return flags, skipped


def drop_skipped(r, urls, flagged):
    """Return a copy of r without media whose URL is in urls, positions renumbered 0-based per kind.

    A listing can list one URL twice. The model then skips the repeat but flags the image once,
    so a skipped URL that has flags keeps its first copy and loses the others.
    """
    out = dict(r)
    kept, next_pos, seen = [], Counter(), set()
    for m in sorted(r["media"], key=lambda m: (m["kind"], m["position"])):
        first = m["url"] not in seen
        seen.add(m["url"])
        if m["url"] in urls and not (first and m["url"] in flagged):
            continue
        kept.append(dict(m, position=next_pos[m["kind"]]))
        next_pos[m["kind"]] += 1
    out["media"] = kept
    return out


def check_flag_sources(flags, records):
    """Abort if a flag's source_photo is not a remaining image of its listing (e.g. a removed one)."""
    urls = {r["id"]: {m["url"] for m in r["media"]} for r in records}
    for fl in flags:
        if fl["source_photo"] not in urls.get(fl["listing_id"], set()):
            print("build failed: flag %s points to %s, which is not an image of listing %s"
                  % (fl["flag_id"], fl["source_photo"], fl["listing_id"]), file=sys.stderr)
            sys.exit(1)


def rows_of(r):
    """Split one record into its listings, listing_media and listing_stations rows."""
    listing = [json.dumps(r[c], ensure_ascii=False) if c in JSON_COLS else r[c] for c in LISTING_COLS]
    media = [[r["id"], m["kind"], m["position"], m["url"]] for m in r["media"]]
    stations = [[r["id"], s["position"], s["name"], s["distance_km"],
                 json.dumps(s["types"], ensure_ascii=False)] for s in r["stations"]]
    return listing, media, stations


def literal(v):
    if v is None:
        return "NULL"
    if isinstance(v, str):
        return "'" + v.replace("'", "''") + "'"
    return repr(v)  # int or float, unquoted


def insert_sql(table, cols, row):
    return "INSERT INTO %s (%s) VALUES (%s);" % (table, ", ".join(cols), ", ".join(literal(v) for v in row))


def counts(con):
    return {t: con.execute("SELECT COUNT(*) FROM " + t).fetchone()[0] for t in TABLES}


def split_lines(rows):
    """Report lines: eval share overall, London versus outside, and per postcode area."""
    def line(label, sides):
        n, e = len(sides), sides.count("eval")
        return "  %s: %d listings, train %d, eval %d (%.1f%% eval)" % (label, n, n - e, e, 100.0 * e / max(n, 1))

    area = {}
    for pc, side in rows:
        area.setdefault(area_of({"postcode": pc}), []).append(side)
    lon = [s for a, v in area.items() if a in LONDON_AREAS for s in v]
    out = [line("all", [s for _, s in rows]), line("London", lon),
           line("outside London", [s for a, v in area.items() if a not in LONDON_AREAS for s in v])]
    return out + [line("area " + (a or "unknown"), area[a]) for a in sorted(area)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True, help="dataset/ directory")
    ds = ap.parse_args().dataset
    schema_path = os.path.join(ds, "d1", "schema.sql")
    seed_path = os.path.join(ds, "d1", "seed.sql")
    db_path = os.path.join(ds, "listings.sqlite")
    with open(schema_path, encoding="utf-8") as f:
        schema = f.read()
    with open(os.path.join(ds, "listings.jsonl"), encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]

    real = Counter(r["epc_current"] for r in records if r["epc_current"] is not None)
    letters = sorted(real)
    weights = [real[x] for x in letters]
    rng = random.Random(EPC_SEED)
    records = [demo_epc(r, rng, letters, weights) for r in sorted(records, key=lambda r: r["id"])]
    check_duplicates(records)
    flags, skipped = read_flags(os.path.join(ds, "photo_flags.jsonl"))
    before = Counter(m["kind"] for r in records for m in r["media"])
    flagged = {(fl["listing_id"], fl["source_photo"]) for fl in flags}
    records = [drop_skipped(r, skipped.get(r["id"], set()), {u for i, u in flagged if i == r["id"]})
               for r in records]
    removed = before - Counter(m["kind"] for r in records for m in r["media"])
    check_flag_sources(flags, records)
    split = assign_split(records)
    for r in records:
        r["split"] = split[r["id"]]

    listings, media, stations = [], [], []
    for r in records:
        a, b, c = rows_of(r)
        listings.append(a)
        media.extend(b)
        stations.extend(c)
    listings.sort(key=lambda x: x[0])
    media.sort(key=lambda x: (x[0], x[1], x[2]))
    stations.sort(key=lambda x: (x[0], x[1]))
    flag_rows = sorted([fl[c] for c in FLAG_COLS] for fl in flags)

    if os.path.exists(db_path):
        os.remove(db_path)
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys=ON")
    con.executescript(schema)
    plan = [("listings", LISTING_COLS, listings), ("listing_media", MEDIA_COLS, media),
            ("listing_stations", STATION_COLS, stations),
            ("photo_flags", FLAG_COLS, flag_rows)]
    statements = []
    for table, cols, rows in plan:
        sql = "INSERT INTO %s (%s) VALUES (%s)" % (table, ", ".join(cols), ", ".join("?" * len(cols)))
        for row in rows:
            try:
                con.execute(sql, row)
            except sqlite3.Error as e:
                print("build failed: %s row for listing %s: %s" % (table, row[0], e), file=sys.stderr)
                con.close()
                sys.exit(1)
            statements.append(insert_sql(table, cols, row))
    con.commit()

    seed = "\n".join(statements) + "\n"
    with open(seed_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(seed)

    db_counts = counts(con)
    epc_cur = dict(con.execute("SELECT epc_current, COUNT(*) FROM listings GROUP BY 1 ORDER BY 1"))
    epc_pot = dict(con.execute("SELECT epc_potential, COUNT(*) FROM listings GROUP BY 1 ORDER BY 1"))
    split_rows = con.execute("SELECT postcode, split FROM listings").fetchall()
    media_kinds = dict(con.execute("SELECT kind, COUNT(*) FROM listing_media GROUP BY 1 ORDER BY 1"))
    flag_fields = dict(con.execute("SELECT scope || '.' || field, COUNT(*) FROM photo_flags GROUP BY 1 ORDER BY 1"))
    fk = con.execute("PRAGMA foreign_key_check").fetchall()
    integrity = con.execute("PRAGMA integrity_check").fetchall()
    con.close()

    check = sqlite3.connect(":memory:")
    check.execute("PRAGMA foreign_keys=ON")
    check.executescript(schema)
    check.executescript(seed)
    seed_counts = counts(check)
    check.close()

    sizes = [len(s.encode("utf-8")) for s in statements]
    ok = seed_counts == db_counts and not fk and integrity == [("ok",)] and max(sizes) < D1_STATEMENT_LIMIT
    lines = ["== row counts (listings.sqlite) =="]
    lines += ["  %s: %d" % (t, db_counts[t]) for t in TABLES]
    lines += ["== pragma results ==",
              "  foreign_key_check: %s" % ("clean" if not fk else "%d violations" % len(fk)),
              "  integrity_check: %s" % integrity[0][0],
              "== photo flags ==",
              "  flags by field: " + ", ".join("%s %d" % kv for kv in flag_fields.items()),
              "  skipped images removed from listing_media: " + ", ".join("%s %d" % kv for kv in sorted(removed.items())),
              "== epc (demo values, see README) ==",
              "  epc_current: " + ", ".join("%s %d" % kv for kv in epc_cur.items()),
              "  epc_potential: " + ", ".join("%s %d" % kv for kv in epc_pot.items()),
              "  media rows by kind: " + ", ".join("%s %d" % kv for kv in media_kinds.items()),
              "== train/eval split (seed %d, groups by coordinates) ==" % SPLIT_SEED]
    lines += split_lines(split_rows)
    lines += ["== seed.sql ==",
              "  statements: %d" % len(statements),
              "  size: %d bytes" % len(seed.encode("utf-8")),
              "  largest statement: %d bytes (D1 limit about %d)" % (max(sizes), D1_STATEMENT_LIMIT),
              "== self-check: schema.sql then seed.sql into empty in-memory db, foreign_keys=ON =="]
    lines += ["  %s: %d (listings.sqlite %d)" % (t, seed_counts[t], db_counts[t]) for t in TABLES]
    lines.append("  result: %s" % ("PASS" if ok else "FAIL"))
    out = "\n".join(lines) + "\n"
    sys.stdout.write(out)
    os.makedirs(os.path.join(ds, "reports"), exist_ok=True)
    with open(os.path.join(ds, "reports", "d1-build-report.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write(out)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
