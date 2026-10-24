"""Build listings.sqlite and d1/seed.sql from listings.jsonl and d1/schema.sql.

The schema's CHECK and foreign-key constraints are the validation: the first row
that breaks one aborts the build with the listing id and the SQLite error.
Reads only files already on disk. Makes no network requests.

Usage (from the dataset/ directory):
  python3 -I -B scripts/build_d1.py --dataset .
"""
import argparse
import json
import os
import sqlite3
import sys

TABLES = ["listings", "listing_media", "listing_stations"]
LISTING_COLS = [
    "id", "source", "source_id", "url", "price_gbp", "price_qualifier", "bedrooms", "bathrooms",
    "property_type", "address", "postcode", "lat", "lon", "tenure", "lease_years_remaining",
    "service_charge_gbp_pa", "ground_rent_gbp_pa", "council_tax_band", "epc_current",
    "epc_potential", "floor_level", "key_features", "description", "agent_name", "listed_date",
    "fetched_at", "parsed_fields",
]
JSON_COLS = {"key_features", "parsed_fields"}
MEDIA_COLS = ["listing_id", "kind", "position", "url"]
STATION_COLS = ["listing_id", "position", "name", "distance_km", "types"]


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

    listings, media, stations = [], [], []
    for r in records:
        a, b, c = rows_of(r)
        listings.append(a)
        media.extend(b)
        stations.extend(c)
    listings.sort(key=lambda x: x[0])
    media.sort(key=lambda x: (x[0], x[1], x[2]))
    stations.sort(key=lambda x: (x[0], x[1]))

    if os.path.exists(db_path):
        os.remove(db_path)
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys=ON")
    con.executescript(schema)
    plan = [("listings", LISTING_COLS, listings), ("listing_media", MEDIA_COLS, media),
            ("listing_stations", STATION_COLS, stations)]
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
    ok = seed_counts == db_counts and not fk and integrity == [("ok",)]
    lines = ["== row counts (listings.sqlite) =="]
    lines += ["  %s: %d" % (t, db_counts[t]) for t in TABLES]
    lines += ["== pragma results ==",
              "  foreign_key_check: %s" % ("clean" if not fk else "%d violations" % len(fk)),
              "  integrity_check: %s" % integrity[0][0],
              "== seed.sql ==",
              "  statements: %d" % len(statements),
              "  size: %d bytes" % len(seed.encode("utf-8")),
              "  largest statement: %d bytes (D1 limit about 100000)" % max(sizes),
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
