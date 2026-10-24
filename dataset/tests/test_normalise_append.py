import collections
import json
import sys
import tempfile
import unittest
from pathlib import Path

DATASET = Path(__file__).resolve().parent.parent
# tests/ is not a package, so scripts/ is put on the path directly.
sys.path.insert(0, str(DATASET / "scripts"))

import normalise as n  # noqa: E402


def existing(**over):
    """A record as it sits in listings.jsonl: sanitised, photos in media."""
    r = {"id": "rm-1", "price_gbp": 500_000, "bedrooms": 2, "lat": 51.5, "lon": -0.1,
         "agent_name": "Agent A", "postcode": "N1 1AA",
         "media": [{"kind": "photo", "position": 0, "url": "https://img.test/own-1.jpg"}]}
    r.update(over)
    return r


def new(**over):
    """A record as the builders return it, before sanitise."""
    r = {"id": "rm-2", "price_gbp": 600_000, "bedrooms": 3, "lat": 52.0, "lon": 0.2,
         "agent_name": "Agent B", "postcode": "CB1 1AA", "_delivery_point": None,
         "photo_urls": ["https://img.test/own-2.jpg"], "_photo_count": 1}
    r.update(over)
    return r


def run(old, add):
    stats = collections.Counter()
    return n.drop_clashes(old, add, stats), stats


class DropClashTests(unittest.TestCase):
    def test_unrelated_new_record_is_kept(self):
        kept, stats = run([existing()], [new()])
        self.assertEqual([r["id"] for r in kept], ["rm-2"])
        self.assertEqual(sum(stats.values()), 0)

    def test_same_rightmove_id_is_dropped(self):
        kept, stats = run([existing()], [new(id="rm-1")])
        self.assertEqual(kept, [])
        self.assertEqual(stats["append_dropped_duplicate_id"], 1)

    def test_same_delivery_point_is_dropped(self):
        old = existing()
        old["_delivery_point"] = 777
        kept, stats = run([old], [new(_delivery_point=777)])
        self.assertEqual(kept, [])
        self.assertEqual(stats["append_dropped_duplicate_dp"], 1)

    def test_same_coordinates_bedrooms_price_is_dropped(self):
        kept, stats = run([existing()], [new(lat=51.50004, lon=-0.10004, bedrooms=2, price_gbp=500_000)])
        self.assertEqual(kept, [])
        self.assertEqual(stats["append_dropped_duplicate_geo"], 1)

    def test_same_place_with_other_price_is_kept(self):
        kept, _ = run([existing()], [new(lat=51.5, lon=-0.1, bedrooms=2, price_gbp=510_000)])
        self.assertEqual(len(kept), 1)

    def test_same_agent_waives_geo_clash(self):
        kept, _ = run([existing()], [new(lat=51.5, lon=-0.1, bedrooms=2, price_gbp=500_000,
                                         agent_name="Agent A")])
        self.assertEqual(len(kept), 1)

    def test_shared_photo_url_is_dropped_even_for_the_same_agent(self):
        kept, stats = run([existing()], [new(agent_name="Agent A",
                                             photo_urls=["https://img.test/x.jpg", "https://img.test/own-1.jpg"])])
        self.assertEqual(kept, [])
        self.assertEqual(stats["append_dropped_duplicate_photo"], 1)

    def test_floorplan_url_in_common_is_not_a_clash(self):
        old = existing()
        old["media"].append({"kind": "floorplan", "position": 0, "url": "https://img.test/plan.jpg"})
        kept, _ = run([old], [new(floorplan_urls=["https://img.test/plan.jpg"])])
        self.assertEqual(len(kept), 1)

    def test_new_against_new_keeps_the_richer_one(self):
        poor = new(id="rm-3", photo_urls=["https://img.test/shared.jpg"], _photo_count=1)
        rich = new(id="rm-4", photo_urls=["https://img.test/shared.jpg"], _photo_count=9,
                   description="text", tenure="freehold")
        kept, stats = run([], [poor, rich])
        self.assertEqual([r["id"] for r in kept], ["rm-4"])
        self.assertEqual(stats["append_dropped_duplicate_photo"], 1)

    def test_new_against_new_same_id(self):
        kept, stats = run([], [new(id="rm-5"), new(id="rm-5", photo_urls=["https://img.test/other.jpg"])])
        self.assertEqual(len(kept), 1)
        self.assertEqual(stats["append_dropped_duplicate_id"], 1)

    def test_existing_record_is_never_changed(self):
        old = existing()
        before = json.dumps(old, sort_keys=True)
        run([old], [new(id="rm-1")])
        self.assertEqual(json.dumps(old, sort_keys=True), before)


class FileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ds = self.tmp.name
        self.addCleanup(self.tmp.cleanup)

    def write(self, lines):
        (Path(self.ds) / "listings.jsonl").write_text("".join(lines), encoding="utf-8")

    def test_load_existing_returns_records_in_file_order(self):
        a, b = existing(id="rm-9"), existing(id="rm-3")
        self.write([json.dumps(a, ensure_ascii=False) + "\n", json.dumps(b, ensure_ascii=False) + "\n"])
        got = n.load_existing(self.ds)
        self.assertEqual([r["id"] for r in got], ["rm-9", "rm-3"])
        self.assertEqual(got[0]["_photo_count"], 1)

    def test_load_existing_refuses_a_line_that_would_change(self):
        self.write([json.dumps(existing(), separators=(",", ":")) + "\n"])
        with self.assertRaises(SystemExit):
            n.load_existing(self.ds)

    def test_refuses_to_shrink(self):
        self.write([json.dumps(existing(id="rm-%d" % i)) + "\n" for i in range(3)])
        with self.assertRaises(SystemExit) as cm:
            n.check_not_shrinking(self.ds, 2)
        self.assertIn("--append", str(cm.exception))

    def test_same_or_larger_count_is_allowed(self):
        self.write([json.dumps(existing(id="rm-%d" % i)) + "\n" for i in range(3)])
        n.check_not_shrinking(self.ds, 3)
        n.check_not_shrinking(self.ds, 4)

    def test_no_existing_file_is_allowed(self):
        n.check_not_shrinking(self.ds, 0)


if __name__ == "__main__":
    unittest.main()
