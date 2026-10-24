import re
import sys
import unittest
from pathlib import Path

DATASET = Path(__file__).resolve().parent.parent
# tests/ is not a package, so scripts/ is put on the path directly.
sys.path.insert(0, str(DATASET / "scripts"))

import sanitise as s  # noqa: E402

SCHEMA = DATASET / "d1" / "schema.sql"
# Columns the D1 build assigns; they are in the schema but not in the sanitised records.
BUILD_ONLY = {"split"}


def record(**over):
    r = {
        "id": "rm-1", "source": "rightmove", "source_id": "1", "url": "https://example.test/1",
        "price_gbp": 500_000, "fetched_at": "2026-10-01T12:00:00+00:00",
    }
    r.update(over)
    return r


def clean(**over):
    out, ev = s.sanitise_record(record(**over))
    return out, ev


class EnumTests(unittest.TestCase):
    def test_property_type_every_mapping(self):
        for raw, want in s.PROPERTY_TYPE.items():
            if want is None:
                continue
            with self.subTest(raw=raw):
                out, ev = clean(property_type=raw)
                self.assertEqual(out["property_type"], want)
                self.assertEqual(ev, [])

    def test_property_type_expected_values(self):
        expected = {
            "Flat": "flat", "Apartment": "flat", "Penthouse": "flat", "Ground Flat": "flat",
            "Maisonette": "maisonette", "Duplex": "maisonette", "House": "house",
            "Town House": "house", "Terraced": "terraced", "Semi-Detached": "semi_detached",
            "End of Terrace": "end_of_terrace", "Detached": "detached",
            "Link Detached House": "detached", "Bungalow": "bungalow",
            "Detached Bungalow": "bungalow", "Block of Apartments": "other",
        }
        for raw, want in expected.items():
            with self.subTest(raw=raw):
                self.assertEqual(clean(property_type=raw)[0]["property_type"], want)

    def test_property_type_not_specified_is_null(self):
        out, ev = clean(property_type="Not Specified")
        self.assertIsNone(out["property_type"])
        self.assertIn("nulled:property_type:not specified", ev)

    def test_property_type_unmapped_is_other(self):
        out, ev = clean(property_type="Castle")
        self.assertEqual(out["property_type"], "other")
        self.assertIn("unknown_enum:property_type:Castle", ev)

    def test_property_type_case_insensitive(self):
        self.assertEqual(clean(property_type="SEMI-DETACHED")[0]["property_type"], "semi_detached")
        self.assertEqual(clean(property_type="  fLaT ")[0]["property_type"], "flat")

    def test_property_type_missing_is_null(self):
        self.assertIsNone(clean()[0]["property_type"])

    def test_tenure(self):
        for raw, want in (("freehold", "freehold"), ("LEASEHOLD", "leasehold"),
                          ("share_of_freehold", "share_of_freehold")):
            with self.subTest(raw=raw):
                self.assertEqual(clean(tenure=raw)[0]["tenure"], want)

    def test_tenure_unknown_is_null(self):
        out, ev = clean(tenure="commonhold")
        self.assertIsNone(out["tenure"])
        self.assertIn("unknown_enum:tenure:commonhold", ev)

    def test_council_tax_band(self):
        self.assertEqual(clean(council_tax_band="d")[0]["council_tax_band"], "D")
        self.assertEqual(clean(council_tax_band="H")[0]["council_tax_band"], "H")

    def test_council_tax_band_rejected(self):
        out, ev = clean(council_tax_band="TBC")
        self.assertIsNone(out["council_tax_band"])
        self.assertIn("nulled:council_tax_band:tbc", ev)
        out, ev = clean(council_tax_band="I")
        self.assertIsNone(out["council_tax_band"])
        self.assertIn("unknown_enum:council_tax_band:I", ev)

    def test_epc_accepted(self):
        for c in "ABCDEFG":
            with self.subTest(rating=c):
                out, _ = clean(epc_current=c, epc_potential=c.lower())
                self.assertEqual(out["epc_current"], c)
                self.assertEqual(out["epc_potential"], c)

    def test_epc_rejected(self):
        out, ev = clean(epc_current="H", epc_potential="")
        self.assertIsNone(out["epc_current"])
        self.assertIsNone(out["epc_potential"])
        self.assertIn("unknown_enum:epc_current:H", ev)

    def test_price_qualifier_mappings(self):
        expected = {
            "Guide Price": "guide_price", "Offers in Excess of": "offers_over",
            "Offers Over": "offers_over", "Offers in Region of": "offers_in_region",
            "Fixed Price": "fixed_price",
        }
        for raw, want in expected.items():
            with self.subTest(raw=raw):
                self.assertEqual(clean(price_qualifier=raw)[0]["price_qualifier"], want)

    def test_price_qualifier_unknown_is_null(self):
        out, ev = clean(price_qualifier="Auction")
        self.assertIsNone(out["price_qualifier"])
        self.assertIn("unknown_enum:price_qualifier:Auction", ev)


class UnitTests(unittest.TestCase):
    def station(self, **kw):
        out, ev = clean(nearest_stations=[dict({"name": "Alpha", "distance": 1.5}, **kw)])
        return out["stations"][0], ev

    def test_miles_to_km_rounded_to_three_places(self):
        st, _ = self.station(unit="miles")
        self.assertEqual(st["distance_km"], round(1.5 * 1.609344, 3))
        self.assertEqual(st["distance_km"], 2.414)

    def test_missing_unit_is_miles(self):
        st, ev = self.station()
        self.assertEqual(st["distance_km"], 2.414)
        self.assertIn("station_unit:rightmove:none:miles", ev)

    def test_unit_case_insensitive(self):
        self.assertEqual(self.station(unit="MILES")[0]["distance_km"], 2.414)

    def test_unsupported_unit_is_null(self):
        # sanitise.py has no km entry, so a declared "km" is not passed through.
        st, ev = self.station(unit="km")
        self.assertIsNone(st["distance_km"])
        self.assertIn("nulled:distance_km:unknown_unit", ev)

    def test_zero_distance_stays_zero(self):
        st, _ = self.station(distance=0)
        self.assertEqual(st["distance_km"], 0.0)

    def test_missing_distance_is_null(self):
        out, ev = clean(nearest_stations=[{"name": "Alpha"}])
        self.assertIsNone(out["stations"][0]["distance_km"])
        self.assertEqual(ev, [])

    def test_distance_out_of_range_is_null(self):
        st, ev = self.station(distance=100)  # 160 km
        self.assertIsNone(st["distance_km"])
        self.assertIn("nulled:distance_km:out_of_range", ev)

    def test_station_without_name_dropped(self):
        out, ev = clean(nearest_stations=[{"name": "  ", "distance": 1}, {"name": "B", "distance": 1}])
        self.assertEqual([x["name"] for x in out["stations"]], ["B"])
        self.assertEqual(out["stations"][0]["position"], 0)
        self.assertIn("station_dropped:no_name", ev)


class ZeroVersusNullTests(unittest.TestCase):
    def test_zero_kept(self):
        out, ev = clean(service_charge_gbp_pa=0, ground_rent_gbp_pa=0, bathrooms=0)
        self.assertEqual(out["service_charge_gbp_pa"], 0)
        self.assertEqual(out["ground_rent_gbp_pa"], 0)
        self.assertEqual(out["bathrooms"], 0)
        self.assertEqual(ev, [])

    def test_lease_zero_is_null(self):
        out, ev = clean(lease_years_remaining=0)
        self.assertIsNone(out["lease_years_remaining"])
        self.assertIn("nulled:lease_years_remaining:zero_means_none", ev)

    def test_lease_positive_kept(self):
        self.assertEqual(clean(lease_years_remaining=99)[0]["lease_years_remaining"], 99)

    def test_empty_string_is_null(self):
        out, _ = clean(service_charge_gbp_pa="", bathrooms="", lat="", tenure="",
                       address="", postcode="  ", agent_name="", description="", floor_level="")
        for f in ("service_charge_gbp_pa", "bathrooms", "lat", "tenure", "address", "postcode",
                  "agent_name", "description", "floor_level"):
            with self.subTest(field=f):
                self.assertIsNone(out[f])

    def test_missing_is_null(self):
        out, ev = clean()
        for f in s.COLUMNS:
            if f in ("id", "source", "source_id", "url", "price_gbp", "fetched_at",
                     "key_features", "parsed_fields", "media", "stations"):
                continue
            with self.subTest(field=f):
                self.assertIsNone(out[f])
        self.assertEqual(ev, [])

    def test_non_numbers_are_null(self):
        out, ev = clean(bedrooms=True, bathrooms=2.5, lat=float("nan"))
        self.assertIsNone(out["bedrooms"])
        self.assertIsNone(out["bathrooms"])
        self.assertIsNone(out["lat"])
        self.assertIn("nulled:bedrooms:not_a_number", ev)
        self.assertIn("nulled:bathrooms:not_an_integer", ev)
        self.assertIn("nulled:lat:not_a_number", ev)


class CleanTextTests(unittest.TestCase):
    def test_description_html_stripped(self):
        out, _ = clean(description="<p>Light &amp; airy</p><p>Two <b>bedrooms</b><br/>and a garden</p>")
        self.assertNotRegex(out["description"], r"<[^>]+>")
        self.assertNotIn("&amp;", out["description"])
        self.assertIn("Light & airy", out["description"])
        self.assertIn("Two bedrooms", out["description"])

    def test_description_whitespace_collapsed(self):
        out, _ = clean(description="  one   two \t three  \n\n\n\n  four  ")
        self.assertEqual(out["description"], "one two three\n\nfour")

    def test_description_tags_only_is_null(self):
        self.assertIsNone(clean(description="<p> </p>")[0]["description"])

    def test_address_whitespace_collapsed(self):
        out, _ = clean(address="1  High Street,\n  London")
        self.assertEqual(out["address"], "1 High Street, London")

    def test_floor_level_lowercased(self):
        self.assertEqual(clean(floor_level="  Raised  Ground ")[0]["floor_level"], "raised ground")

    def test_key_features_cleaned_and_empties_removed(self):
        out, _ = clean(key_features=["<li>Garden &amp; patio</li>", "", "   ", "<b></b>",
                                     "Two   beds", None, 5])
        self.assertEqual(out["key_features"], ["Garden & patio", "Two beds"])

    def test_key_features_missing_is_empty_list(self):
        self.assertEqual(clean()[0]["key_features"], [])


class DateTests(unittest.TestCase):
    def test_utc_offset_becomes_z(self):
        self.assertEqual(s.iso_utc("2026-10-01T12:00:00+00:00"), "2026-10-01T12:00:00Z")
        self.assertEqual(clean()[0]["fetched_at"], "2026-10-01T12:00:00Z")

    def test_z_kept(self):
        self.assertEqual(s.iso_utc("2026-10-01T12:00:00Z"), "2026-10-01T12:00:00Z")

    def test_bare_date_is_midnight(self):
        self.assertEqual(clean(listed_date="2026-09-30")[0]["listed_date"], "2026-09-30T00:00:00Z")

    def test_other_offset_converted_to_utc(self):
        self.assertEqual(s.iso_utc("2026-07-01T01:30:00+01:00"), "2026-07-01T00:30:00Z")

    def test_invalid_listed_date_is_null(self):
        for bad in ("yesterday", "2026-99-99", "", 20261001):
            with self.subTest(bad=bad):
                out, ev = clean(listed_date=bad)
                self.assertIsNone(out["listed_date"])
                self.assertIn("nulled:listed_date:not_a_date", ev)

    def test_missing_listed_date_is_null_without_event(self):
        out, ev = clean()
        self.assertIsNone(out["listed_date"])
        self.assertEqual(ev, [])


class RangeTests(unittest.TestCase):
    def test_every_bound_at_its_edge(self):
        for field, (lo, hi, integer) in s.RANGES.items():
            step = 1 if integer else 0.001
            with self.subTest(field=field):
                for ok in (lo, hi):
                    self.assertEqual(s.number(ok, field), (ok, None))
                for bad in (lo - step, hi + step):
                    self.assertEqual(s.number(bad, field), (None, "out_of_range"))

    def test_record_fields_in_range_kept_and_outside_nulled(self):
        for field, (lo, hi, integer) in s.RANGES.items():
            if field in ("price_gbp", "distance_km"):
                continue
            step = 1 if integer else 0.001
            with self.subTest(field=field):
                for ok in (lo, hi):
                    if field == "lease_years_remaining" and ok == 0:
                        continue
                    self.assertEqual(clean(**{field: ok})[0][field], ok)
                for bad in (lo - step, hi + step):
                    out, ev = clean(**{field: bad})
                    self.assertIsNone(out[field])
                    self.assertTrue(any(e.startswith("nulled:%s:" % field) for e in ev), ev)

    def test_price_at_edges_and_outside(self):
        lo, hi, _ = s.RANGES["price_gbp"]
        for ok in (lo, hi):
            self.assertEqual(clean(price_gbp=ok)[0]["price_gbp"], ok)
        for bad in (lo - 1, hi + 1):
            out, ev = clean(price_gbp=bad)
            self.assertIsNone(out)
            self.assertEqual(ev, ["dropped_row:price_gbp"])

    def test_distance_at_edges(self):
        lo, hi, _ = s.RANGES["distance_km"]
        km_hi_in_miles = hi / s.KM_PER_UNIT["miles"]
        st = clean(nearest_stations=[{"name": "A", "distance": 0, "unit": "miles"}])[0]["stations"][0]
        self.assertEqual(st["distance_km"], lo)
        st = clean(nearest_stations=[{"name": "A", "distance": km_hi_in_miles, "unit": "miles"}])[0]["stations"][0]
        self.assertEqual(st["distance_km"], hi)
        out, ev = clean(nearest_stations=[{"name": "A", "distance": km_hi_in_miles + 0.01, "unit": "miles"}])
        self.assertIsNone(out["stations"][0]["distance_km"])
        self.assertIn("nulled:distance_km:out_of_range", ev)
        out, ev = clean(nearest_stations=[{"name": "A", "distance": -0.01, "unit": "miles"}])
        self.assertIsNone(out["stations"][0]["distance_km"])
        self.assertIn("nulled:distance_km:out_of_range", ev)

    def test_ranges_match_schema_checks(self):
        text = SCHEMA.read_text()
        found = {m[0]: (float(m[1]), float(m[2]))
                 for m in re.findall(r"\((\w+) BETWEEN (-?[\d.]+) AND (-?[\d.]+)\)", text)}
        want = {f: (float(lo), float(hi)) for f, (lo, hi, _) in s.RANGES.items()}
        self.assertEqual(found, want)


class DroppedRowTests(unittest.TestCase):
    def test_each_not_null_field_missing(self):
        for f in ("id", "source", "source_id", "url", "price_gbp", "fetched_at"):
            with self.subTest(field=f):
                r = record()
                del r[f]
                out, ev = s.sanitise_record(r)
                self.assertIsNone(out)
                self.assertEqual(ev, ["dropped_row:" + f])

    def test_each_not_null_field_blank_or_wrong(self):
        for f, bad in (("id", "  "), ("source_id", ""), ("url", " "), ("price_gbp", "500000"),
                       ("price_gbp", None), ("fetched_at", "not a date"), ("fetched_at", "")):
            with self.subTest(field=f, bad=bad):
                out, ev = clean(**{f: bad})
                self.assertIsNone(out)
                self.assertEqual(ev, ["dropped_row:" + f])

    def test_unknown_source_dropped(self):
        out, ev = clean(source="zoopla")
        self.assertIsNone(out)
        self.assertEqual(ev, ["dropped_row:source"])

    def test_both_known_sources_kept(self):
        for src in sorted(s.SOURCES):
            with self.subTest(source=src):
                self.assertEqual(clean(source=src)[0]["source"], src)

    def test_numeric_source_id_becomes_text(self):
        self.assertEqual(clean(source_id=123)[0]["source_id"], "123")


class RecordShapeTests(unittest.TestCase):
    def test_minimal_record_has_exactly_the_columns(self):
        out, ev = clean()
        self.assertEqual(list(out), s.COLUMNS)
        self.assertEqual(ev, [])
        self.assertEqual(out["media"], [])
        self.assertEqual(out["stations"], [])

    def test_columns_match_schema_and_child_tables(self):
        text = SCHEMA.read_text()
        listings = text.split("CREATE TABLE IF NOT EXISTS listings (")[1].split("\n);")[0]
        cols = re.findall(r"^  (\w+) (?:TEXT|INTEGER|REAL)\b", listings, flags=re.M)
        self.assertEqual(s.COLUMNS[:-2], [c for c in cols if c not in BUILD_ONLY])
        self.assertEqual(s.COLUMNS[-2:], ["media", "stations"])

    def test_media_kinds_and_positions_in_order(self):
        out, _ = clean(photo_urls=["p0", " ", "p1"], floorplan_urls=["f0"],
                       epc_image_urls=["e0", "e1", 7])
        self.assertEqual(out["media"], [
            {"kind": "photo", "position": 0, "url": "p0"},
            {"kind": "photo", "position": 1, "url": "p1"},
            {"kind": "floorplan", "position": 0, "url": "f0"},
            {"kind": "epc", "position": 0, "url": "e0"},
            {"kind": "epc", "position": 1, "url": "e1"},
        ])

    def test_stations_shape_and_order(self):
        out, _ = clean(nearest_stations=[
            {"name": "A", "distance": 1, "unit": "miles", "types": ["NATIONAL_TRAIN", 3]},
            {"name": "B", "distance": 2},
        ])
        self.assertEqual(out["stations"], [
            {"position": 0, "name": "A", "distance_km": 1.609, "types": ["NATIONAL_TRAIN"]},
            {"position": 1, "name": "B", "distance_km": 3.219, "types": []},
        ])

    def test_parsed_fields_keep_only_non_null(self):
        out, _ = clean(tenure="freehold", parsed_fields=["tenure", "epc_current"])
        self.assertEqual(out["parsed_fields"], ["tenure"])


if __name__ == "__main__":
    unittest.main()
