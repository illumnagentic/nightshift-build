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


def build(records, tmp):
    """Run the real build script on records in a temporary dataset dir; return it as a Path."""
    ds = Path(tmp)
    (ds / "d1").mkdir(parents=True, exist_ok=True)
    (ds / "d1" / "schema.sql").write_text((DATASET / "d1" / "schema.sql").read_text(encoding="utf-8"), encoding="utf-8")
    with open(ds / "listings.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    subprocess.run([sys.executable, "-I", "-B", str(DATASET / "scripts" / "build_d1.py"), "--dataset", str(ds)],
                   check=True, capture_output=True)
    return ds


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


if __name__ == "__main__":
    unittest.main()
