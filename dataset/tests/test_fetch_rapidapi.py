"""Tests for the RapidAPI fetch script's search params, price band and detail
candidate selection. No network."""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import fetch_rapidapi as fr  # noqa: E402
import rm_common as rm  # noqa: E402

ID = "REGION^93965"


def card(pid, price, **kw):
    c = {"id": pid, "channel": "BUY", "price": {"amount": price},
         "numberOfImages": 8, "numberOfFloorplans": 1}
    c.update(kw)
    return c


class SearchParamsTests(unittest.TestCase):
    def test_defaults_unchanged(self):
        self.assertEqual(fr.search_params(ID, 1, False), {
            "identifier": ID, "page": "1", "min_price": "250000", "max_price": "1200000",
            "do_not_show_retirement_home": "true", "do_not_show_buying_schemes": "true"})

    def test_flats_unchanged(self):
        p = fr.search_params(ID, 2, True)
        self.assertEqual(p["property_type"], "Flat")
        self.assertEqual((p["min_bedroom"], p["max_bedroom"]), ("1", "3"))
        self.assertNotIn("sort_by", p)

    def test_band_and_sort_added(self):
        p = fr.search_params(ID, 1, False, 300000, 700000, "6")
        self.assertEqual((p["min_price"], p["max_price"], p["sort_by"]), ("300000", "700000", "6"))

    def test_max_only_keeps_default_min(self):
        p = fr.search_params(ID, 1, False, max_price=700000)
        self.assertEqual((p["min_price"], p["max_price"]), ("250000", "700000"))

    def test_out_of_range_rejected(self):
        for lo, hi in [(100000, None), (None, 2000000), (800000, 700000), (1300000, None)]:
            with self.assertRaises(ValueError):
                fr.search_params(ID, 1, False, lo, hi)

    def test_search_path_unchanged_for_defaults(self):
        # cache file name of the default params as saved before the band and sort options
        self.assertEqual(fr.search_path(fr.search_params(ID, 1, False)),
                         "search/REGION_93965_p1_b8e6e53209.json")

    def test_search_path_differs_with_band_or_sort(self):
        base = fr.search_path(fr.search_params(ID, 1, False))
        self.assertNotEqual(base, fr.search_path(fr.search_params(ID, 1, False, max_price=700000)))
        self.assertNotEqual(base, fr.search_path(fr.search_params(ID, 1, False, sort="6")))


class SearchIdsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.raw = os.path.join(self.tmp.name, "rapidapi")
        os.makedirs(os.path.join(self.raw, "search"))
        cards = [card(1, 300000), card(2, 600000), card(3, 900000), card(4, 400000),
                 card(5, 500000, numberOfImages=2), card(6, 450000, auction=True)]
        with open(os.path.join(self.raw, "search", "REGION_93965_p1_x.json"), "w") as f:
            json.dump({"data": cards}, f)

    def ids(self, known=(), **kw):
        return fr.search_ids(self.raw, set(known), ID, **kw)

    def test_no_band_keeps_all_rule_passing_cards(self):
        self.assertEqual(self.ids(), ["1", "2", "3", "4"])

    def test_max_price_skips_dearer_cards(self):
        self.assertEqual(self.ids(max_price=700000), ["1", "2", "4"])

    def test_min_price_skips_cheaper_cards(self):
        self.assertEqual(self.ids(min_price=500000), ["2", "3"])

    def test_band_edges_inclusive(self):
        self.assertEqual(self.ids(min_price=300000, max_price=600000), ["1", "2", "4"])

    def test_known_id_skipped(self):
        self.assertEqual(self.ids(known={"2"}, max_price=700000), ["1", "4"])

    def test_card_rule_skips_kept(self):
        self.assertNotIn("5", self.ids())
        self.assertNotIn("6", self.ids())

    def test_bad_band_rejected(self):
        with self.assertRaises(ValueError):
            self.ids(max_price=rm.MAX_PRICE + 1)


class KnownIdsTests(unittest.TestCase):
    def test_reads_ids_without_prefix(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "listings.jsonl"), "w") as f:
                f.write(json.dumps({"id": "rm-11"}) + "\n\n" + json.dumps({"id": "rm-22"}) + "\n")
            self.assertEqual(fr.known_ids(d), {"11", "22"})

    def test_missing_file_is_empty(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(fr.known_ids(d), set())


if __name__ == "__main__":
    unittest.main()
