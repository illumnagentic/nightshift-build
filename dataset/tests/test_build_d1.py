import copy
import json
import random
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

DATASET = Path(__file__).resolve().parent.parent
# tests/ is not a package, so scripts/ is put on the path directly.
sys.path.insert(0, str(DATASET / "scripts"))

import build_d1 as b  # noqa: E402
from test_sanitise import BUILD_ONLY  # noqa: E402

LETTERS = list("ABCDE")
WEIGHTS = [1, 20, 40, 25, 3]


def record(**over):
    r = {
        "id": "rm-1",
        "epc_current": None,
        "epc_potential": None,
        "media": [
            {"kind": "photo", "position": 0, "url": "https://example.test/p0.jpg"},
            {"kind": "epc", "position": 0, "url": "https://example.test/epc0.png"},
            {"kind": "floorplan", "position": 0, "url": "https://example.test/fp0.png"},
            {"kind": "photo", "position": 1, "url": "https://example.test/p1.jpg"},
            {"kind": "epc", "position": 1, "url": "https://example.test/epc1.pdf"},
        ],
    }
    r.update(over)
    return r


def run(r, seed=1, letters=LETTERS, weights=WEIGHTS):
    return b.demo_epc(r, random.Random(seed), letters, weights)


class MediaTests(unittest.TestCase):
    def test_epc_media_removed(self):
        out = run(record())
        self.assertEqual([m for m in out["media"] if m["kind"] == "epc"], [])

    def test_other_media_kept_with_positions(self):
        r = record()
        expected = [m for m in r["media"] if m["kind"] != "epc"]
        self.assertEqual(run(r)["media"], expected)


class InputTests(unittest.TestCase):
    def test_input_not_mutated(self):
        r = record()
        before = copy.deepcopy(r)
        out = run(r)
        self.assertEqual(r, before)
        self.assertIsNot(out, r)


class CurrentTests(unittest.TestCase):
    def test_real_current_kept(self):
        for seed in range(50):
            self.assertEqual(run(record(epc_current="E"), seed)["epc_current"], "E")

    def test_missing_current_filled_from_letters(self):
        seen = set()
        for seed in range(300):
            cur = run(record(), seed, letters=["B", "D", "F"], weights=[1, 1, 1])["epc_current"]
            self.assertIn(cur, ["B", "D", "F"])
            seen.add(cur)
        self.assertEqual(seen, {"B", "D", "F"})

    def test_weights_steer_the_draw(self):
        for seed in range(100):
            out = run(record(), seed, letters=["B", "D"], weights=[1, 0])
            self.assertEqual(out["epc_current"], "B")
        for seed in range(100):
            out = run(record(), seed, letters=["B", "D"], weights=[0, 1])
            self.assertEqual(out["epc_current"], "D")

    def test_heavier_weight_drawn_more_often(self):
        rng = random.Random(7)
        picks = [b.demo_epc(record(), rng, ["B", "D"], [9, 1])["epc_current"] for _ in range(2000)]
        self.assertGreater(picks.count("B"), picks.count("D") * 4)


class PotentialTests(unittest.TestCase):
    def test_potential_between_current_and_two_bands_better(self):
        rng = random.Random(3)
        for cur in b.BANDS:
            gains = set()
            for _ in range(500):
                out = b.demo_epc(record(epc_current=cur), rng, LETTERS, WEIGHTS)
                gain = b.BANDS.index(cur) - b.BANDS.index(out["epc_potential"])
                self.assertGreaterEqual(gain, 0, cur)
                self.assertLessEqual(gain, 2, cur)
                gains.add(gain)
            if cur not in "AB":
                self.assertEqual(gains, {0, 1, 2}, cur)

    def test_current_a_always_gives_a(self):
        rng = random.Random(4)
        for _ in range(500):
            out = b.demo_epc(record(epc_current="A"), rng, LETTERS, WEIGHTS)
            self.assertEqual(out["epc_potential"], "A")

    def test_potential_made_up_even_when_input_has_one(self):
        out = run(record(epc_current="D", epc_potential="A"), seed=5)
        self.assertIn(out["epc_potential"], "BCD")

    def test_both_letters_always_set(self):
        for seed in range(100):
            out = run(record(), seed)
            self.assertIn(out["epc_current"], b.BANDS)
            self.assertIn(out["epc_potential"], b.BANDS)


class DeterminismTests(unittest.TestCase):
    def test_same_seed_same_output(self):
        recs = [record(id="rm-%d" % i) for i in range(50)]

        def batch():
            rng = random.Random(b.EPC_SEED)
            return [b.demo_epc(r, rng, LETTERS, WEIGHTS) for r in recs]

        self.assertEqual(batch(), batch())

    def test_different_seed_can_differ(self):
        outs = {(o["epc_current"], o["epc_potential"]) for o in (run(record(), s) for s in range(50))}
        self.assertGreater(len(outs), 1)


def sample_records(n=40):
    """The first n real records, so every build test runs on valid data."""
    with open(DATASET / "listings.jsonl", encoding="utf-8") as f:
        return [json.loads(line) for _, line in zip(range(n), f)]


def build(records, tmp, flag_lines=()):
    """Run the real build script on records in a temporary dataset dir; return it as a Path."""
    ds = Path(tmp)
    (ds / "d1").mkdir(parents=True, exist_ok=True)
    (ds / "d1" / "schema.sql").write_text((DATASET / "d1" / "schema.sql").read_text(encoding="utf-8"), encoding="utf-8")
    with open(ds / "listings.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    if flag_lines is not None:
        (ds / "photo_flags.jsonl").write_text("".join(json.dumps(x) + "\n" for x in flag_lines), encoding="utf-8")
    subprocess.run([sys.executable, "-I", "-B", str(DATASET / "scripts" / "build_d1.py"), "--dataset", str(ds)],
                   check=True, capture_output=True)
    return ds


def build_raw(records, tmp, flag_lines=()):
    """Like build, but return the finished process instead of raising when the build fails."""
    ds = Path(tmp)
    (ds / "d1").mkdir(parents=True, exist_ok=True)
    (ds / "d1" / "schema.sql").write_text((DATASET / "d1" / "schema.sql").read_text(encoding="utf-8"), encoding="utf-8")
    with open(ds / "listings.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    if flag_lines is not None:
        (ds / "photo_flags.jsonl").write_text("".join(json.dumps(x) + "\n" for x in flag_lines), encoding="utf-8")
    return subprocess.run([sys.executable, "-I", "-B", str(DATASET / "scripts" / "build_d1.py"), "--dataset", str(ds)],
                          capture_output=True, text=True)


def split_by_id(ds):
    con = sqlite3.connect(str(ds / "listings.sqlite"))
    try:
        return dict(con.execute("SELECT id, split FROM listings"))
    finally:
        con.close()


def all_records():
    with open(DATASET / "listings.jsonl", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def geo(i, lat, lon, postcode="SE1 1AA"):
    return {"id": "rm-%d" % i, "lat": lat, "lon": lon, "postcode": postcode}


def epc_by_id(ds):
    con = sqlite3.connect(str(ds / "listings.sqlite"))
    try:
        return {i: (c, p) for i, c, p in con.execute("SELECT id, epc_current, epc_potential FROM listings")}
    finally:
        con.close()


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.recs = sample_records()

    def with_letters(self, letters):
        out = copy.deepcopy(self.recs)
        for r, x in zip(out, letters):
            r["epc_current"] = x
        return out

    def test_filled_letters_come_only_from_real_letters(self):
        # Real letters B and D only; the rest missing.
        letters = ["B", "D"] * 5 + [None] * (len(self.recs) - 10)
        recs = self.with_letters(letters)
        with tempfile.TemporaryDirectory() as tmp:
            got = epc_by_id(build(recs, tmp))
        for r in recs:
            self.assertIn(got[r["id"]][0], "BD")
        self.assertEqual({c for c, _ in got.values()}, {"B", "D"})

    def test_single_real_letter_fills_every_gap(self):
        recs = self.with_letters(["D"] + [None] * (len(self.recs) - 1))
        with tempfile.TemporaryDirectory() as tmp:
            got = epc_by_id(build(recs, tmp))
        self.assertEqual({c for c, _ in got.values()}, {"D"})
        for c, p in got.values():
            self.assertIn(p, "BCD")

    def test_real_letters_unchanged(self):
        letters = list("ABCDE") * 4 + [None] * (len(self.recs) - 20)
        recs = self.with_letters(letters)
        with tempfile.TemporaryDirectory() as tmp:
            got = epc_by_id(build(recs, tmp))
        for r in recs:
            if r["epc_current"] is not None:
                self.assertEqual(got[r["id"]][0], r["epc_current"])
        for c, p in got.values():
            self.assertLessEqual(b.BANDS.index(p), b.BANDS.index(c))

    def test_build_is_byte_identical_across_runs(self):
        recs = self.with_letters(list("BCD") * 3 + [None] * (len(self.recs) - 9))
        with tempfile.TemporaryDirectory() as t1, tempfile.TemporaryDirectory() as t2:
            a = (build(recs, t1) / "d1" / "seed.sql").read_bytes()
            c = (build(recs, t2) / "d1" / "seed.sql").read_bytes()
        self.assertEqual(a, c)

    def test_input_line_order_does_not_change_output(self):
        recs = self.with_letters(list("BCD") * 3 + [None] * (len(self.recs) - 9))
        shuffled = recs[:]
        random.Random(11).shuffle(shuffled)
        self.assertNotEqual([r["id"] for r in recs], [r["id"] for r in shuffled])
        with tempfile.TemporaryDirectory() as t1, tempfile.TemporaryDirectory() as t2:
            a = (build(recs, t1) / "d1" / "seed.sql").read_bytes()
            c = (build(shuffled, t2) / "d1" / "seed.sql").read_bytes()
        self.assertEqual(a, c)

    def test_seed_pinned_to_epc_seed(self):
        # Replays the draws main() makes: sorted by id, Random(EPC_SEED), weights B 1, C 6, D 2.
        recs = self.with_letters(list("BCCCCCCDD") + [None] * (len(self.recs) - 9))
        real = [r["epc_current"] for r in recs if r["epc_current"]]
        letters = sorted(set(real))
        weights = [real.count(x) for x in letters]
        rng = random.Random(b.EPC_SEED)
        want = {}
        for r in sorted(recs, key=lambda r: r["id"]):
            o = b.demo_epc(r, rng, letters, weights)
            want[o["id"]] = (o["epc_current"], o["epc_potential"])
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(epc_by_id(build(recs, tmp)), want)


class SplitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recs = all_records()
        cls.tmp = tempfile.TemporaryDirectory()
        cls.split = split_by_id(build(cls.recs, cls.tmp.name))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def share(self, ids):
        return 100.0 * sum(self.split[i] == "eval" for i in ids) / len(ids)

    def test_every_listing_has_a_side(self):
        self.assertEqual(set(self.split), {r["id"] for r in self.recs})
        self.assertEqual(set(self.split.values()), {"train", "eval"})

    def test_eval_share_overall_and_by_london(self):
        self.assertAlmostEqual(self.share(list(self.split)), 25, delta=2)
        london = [r["id"] for r in self.recs if b.area_of(r) in b.LONDON_AREAS]
        outside = [r["id"] for r in self.recs if b.area_of(r) not in b.LONDON_AREAS]
        self.assertAlmostEqual(self.share(london), 25, delta=5)
        self.assertAlmostEqual(self.share(outside), 25, delta=5)

    def test_same_coordinates_share_a_side(self):
        sides = {}
        for r in self.recs:
            sides.setdefault((round(r["lat"], 4), round(r["lon"], 4)), set()).add(self.split[r["id"]])
        self.assertTrue(all(len(v) == 1 for v in sides.values()))

    def test_split_ignores_input_order(self):
        shuffled = self.recs[:]
        random.Random(5).shuffle(shuffled)
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(split_by_id(build(shuffled, tmp)), self.split)

    def test_split_is_repeatable(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(split_by_id(build(self.recs, tmp)), self.split)

    def test_grouping_keeps_big_groups_together(self):
        recs = [geo(i, 51.5, -0.1) for i in range(30)] + [geo(100 + i, 51.5 + i / 100.0, -0.1) for i in range(1, 71)]
        out = b.assign_split(recs)
        self.assertEqual(len({out["rm-%d" % i] for i in range(30)}), 1)
        # coordinates equal to 4 dp are one group
        out = b.assign_split([geo(1, 51.50001, -0.1), geo(2, 51.50002, -0.1)] + [geo(10 + i, 51.6 + i / 100.0, -0.2) for i in range(40)])
        self.assertEqual(out["rm-1"], out["rm-2"])

    def test_adding_listings_never_moves_existing_ones(self):
        base = self.recs[:559]
        rest = self.recs[559:]
        before = b.assign_split(base)
        # new coordinate groups arrive in two different amounts and orders
        for extra in (rest, rest[::-1][:30]):
            after = b.assign_split(base + extra)
            self.assertEqual({i: after[i] for i in before}, before)
        # and the full build agrees with the direct call
        self.assertEqual({i: self.split[i] for i in before}, before)

    def test_group_side_ignores_other_listings(self):
        r = self.recs[0]
        alone = b.assign_split([r])[r["id"]]
        self.assertEqual(self.split[r["id"]], alone)

    def test_split_seed_does_not_touch_epc_seed(self):
        self.assertNotEqual(b.SPLIT_SEED, b.EPC_SEED)


class DuplicateGuardTests(unittest.TestCase):
    def pair(self, **second):
        recs = sample_records(3)
        recs[2]["epc_current"] = "C"  # the EPC pass needs at least one real letter
        a, c = recs[0], copy.deepcopy(recs[1])
        c.update(second)
        return [a, c] + recs[2:], a, c

    def abort(self, recs):
        with tempfile.TemporaryDirectory() as tmp:
            res = build_raw(recs, tmp)
        self.assertEqual(res.returncode, 1)
        return res.stderr

    def test_shared_photo_url_aborts(self):
        recs, a, c = self.pair()
        photo = next(m for m in a["media"] if m["kind"] == "photo")
        next(m for m in c["media"] if m["kind"] == "photo")["url"] = photo["url"]
        err = self.abort(recs)
        self.assertIn(a["id"], err)
        self.assertIn(c["id"], err)
        self.assertIn("photo URL", err)

    def test_same_coordinates_beds_price_different_agents_aborts(self):
        recs, a, c = self.pair()
        for k in ("lat", "lon", "bedrooms", "price_gbp"):
            c[k] = a[k]
        a["agent_name"], c["agent_name"] = "Agent One", "Agent Two"
        err = self.abort(recs)
        self.assertIn(a["id"], err)
        self.assertIn(c["id"], err)
        self.assertIn("coordinates + bedrooms + price", err)

    def test_same_coordinates_beds_price_no_agent_aborts(self):
        recs, a, c = self.pair()
        for k in ("lat", "lon", "bedrooms", "price_gbp"):
            c[k] = a[k]
        a["agent_name"] = c["agent_name"] = None
        self.abort(recs)

    def test_same_coordinates_beds_price_same_agent_builds(self):
        recs, a, c = self.pair()
        for k in ("lat", "lon", "bedrooms", "price_gbp"):
            c[k] = a[k]
        a["agent_name"] = c["agent_name"] = "Agent One"
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(build_raw(recs, tmp).returncode, 0)

    def test_same_agent_does_not_excuse_shared_photo(self):
        recs, a, c = self.pair()
        a["agent_name"] = c["agent_name"] = "Agent One"
        photo = next(m for m in a["media"] if m["kind"] == "photo")
        next(m for m in c["media"] if m["kind"] == "photo")["url"] = photo["url"]
        self.abort(recs)

    def test_shared_id_aborts(self):
        recs, a, c = self.pair(id="x")
        c["id"] = a["id"]
        err = self.abort(recs)
        self.assertIn(a["id"], err)
        self.assertIn("id", err)


class BuildOnlyColumnTests(unittest.TestCase):
    def test_build_only_columns_are_in_schema_and_written(self):
        schema = (Path(__file__).resolve().parent.parent / "d1" / "schema.sql").read_text()
        listings = schema.split("CREATE TABLE IF NOT EXISTS listings (")[1].split("\n);")[0]
        for col in BUILD_ONLY:
            with self.subTest(col=col):
                self.assertIn(col, b.LISTING_COLS)
                self.assertRegex(listings, r"(?m)^  %s " % col)


def flag(listing, image, field, value, scope="photo", room="kitchen", n=0, **over):
    row = {"flag_id": "%s:%s:%s:%d" % (listing, image, field, n), "listing_id": listing, "scope": scope,
           "field": field, "value": value, "observation": "seen", "source_photo": image,
           "confidence": "high", "uncertainty": None, "room": room if scope == "photo" else None,
           "corrected_text": None}
    row.update(over)
    return row


def status(listing, *skipped_urls):
    return {"record_type": "listing_status", "listing_id": listing, "request_id": "mreq_x",
            "skipped": [{"url": u, "reason": "duplicate"} for u in skipped_urls]}


def sql_rows(ds, query, args=()):
    con = sqlite3.connect(str(ds / "listings.sqlite"))
    try:
        return con.execute(query, args).fetchall()
    finally:
        con.close()


class FlagTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_flags_load_and_values_keep_their_type(self):
        recs = sample_records()
        r = recs[0]
        url = next(m["url"] for m in r["media"] if m["kind"] == "photo")
        lines = [flag(r["id"], url, "room", "kitchen"), flag(r["id"], url, "light", "bright"),
                 flag(r["id"], url, "defects", "58", n=0),
                 flag(r["id"], url, "sqm_estimate", 58, scope="listing"),
                 flag(r["id"], url, "floorplan_notes", "two beds", scope="listing"),
                 status(r["id"])]
        ds = build(recs, self.tmp.name, lines)
        self.assertEqual(sql_rows(ds, "SELECT COUNT(*) FROM photo_flags"), [(5,)])
        types = dict(sql_rows(ds, "SELECT field, typeof(value) FROM photo_flags"))
        self.assertEqual(types["sqm_estimate"], "integer")
        self.assertEqual(types["defects"], "text")  # numeric-looking text stays text
        self.assertEqual(types["room"], "text")
        # same holds after schema then seed into an empty database
        con = sqlite3.connect(":memory:")
        con.executescript((ds / "d1" / "schema.sql").read_text(encoding="utf-8"))
        con.executescript((ds / "d1" / "seed.sql").read_text(encoding="utf-8"))
        self.assertEqual(dict(con.execute("SELECT field, typeof(value) FROM photo_flags")), types)
        con.close()

    def test_real_sqm_stays_real(self):
        recs = sample_records()
        r = recs[0]
        url = r["media"][0]["url"]
        ds = build(recs, self.tmp.name, [flag(r["id"], url, "sqm_estimate", 61.5, scope="listing")])
        self.assertEqual(sql_rows(ds, "SELECT typeof(value), value FROM photo_flags"), [("real", 61.5)])

    def test_check_constraints_reject_bad_rows(self):
        recs = sample_records()
        r = recs[0]
        url = next(m["url"] for m in r["media"] if m["kind"] == "photo")
        bad = {
            "light value": flag(r["id"], url, "light", "dim"),
            "photo scope without room": dict(flag(r["id"], url, "room", "kitchen"), room=None),
            "room on listing scope": dict(flag(r["id"], url, "sqm_estimate", 50, scope="listing"), room="kitchen"),
            "field from the other scope": flag(r["id"], url, "sqm_estimate", 50),
            "bad confidence": flag(r["id"], url, "room", "kitchen", confidence="certain"),
            "null value": flag(r["id"], url, "defects", None),
        }
        for label, row in bad.items():
            with self.subTest(label):
                p = build_raw(recs, self.tmp.name, [row])
                self.assertNotEqual(p.returncode, 0)
                self.assertIn("photo_flags", p.stderr)

    def test_missing_flags_file_aborts(self):
        p = build_raw(sample_records(), self.tmp.name, None)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("photo_flags.jsonl", p.stderr)

    def test_skipped_photos_removed_and_positions_renumbered(self):
        recs = sample_records()
        r = recs[0]
        photos = [m["url"] for m in sorted(r["media"], key=lambda m: m["position"]) if m["kind"] == "photo"]
        self.assertGreaterEqual(len(photos), 4)
        gone = [photos[0], photos[2]]
        ds = build(recs, self.tmp.name, [status(r["id"], *gone)])
        got = sql_rows(ds, "SELECT position, url FROM listing_media WHERE kind = 'photo' AND listing_id = ? ORDER BY position", (r["id"],))
        self.assertEqual(got, list(enumerate([u for u in photos if u not in gone])))
        floor = sql_rows(ds, "SELECT COUNT(*) FROM listing_media WHERE kind = 'floorplan' AND listing_id = ?", (r["id"],))
        self.assertEqual(floor[0][0], len([m for m in r["media"] if m["kind"] == "floorplan"]))

    def test_flag_on_removed_photo_aborts(self):
        recs = sample_records()
        r = recs[0]
        url = next(m["url"] for m in r["media"] if m["kind"] == "photo")
        other = flag(r["id"], "https://example.test/not-an-image.jpg", "room", "kitchen")
        p = build_raw(recs, self.tmp.name, [other, status(r["id"], url)])
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("not an image", p.stderr)

    def test_url_listed_twice_keeps_one_copy_when_flagged(self):
        recs = sample_records()
        r = recs[0]
        photo = next(m for m in r["media"] if m["kind"] == "photo")
        r["media"] = r["media"] + [{"kind": "photo", "position": 99, "url": photo["url"]}]
        ds = build(recs, self.tmp.name, [flag(r["id"], photo["url"], "room", "kitchen"), status(r["id"], photo["url"])])
        self.assertEqual(sql_rows(ds, "SELECT COUNT(*) FROM listing_media WHERE url = ?", (photo["url"],)), [(1,)])


if __name__ == "__main__":
    unittest.main()
