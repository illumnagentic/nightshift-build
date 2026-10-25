import asyncio
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import filters  # noqa: E402

LISTINGS_DB = Path(__file__).resolve().parents[2] / "dataset" / "listings.sqlite"

NO_LIMITS = {
    "max_price_gbp": None, "min_bedrooms": None, "property_types": None,
    "min_epc": None, "tenure": None, "min_lease_years": None, "max_commute_min": None,
}


def listing(**over):
    base = {
        "id": "rm-1", "price_gbp": 500_000, "bedrooms": 2, "property_type": "flat",
        "epc_current": "C", "tenure": "leasehold", "lease_years_remaining": 120,
    }
    return {**base, **over}


def hard(**over):
    return {**NO_LIMITS, **over}


def ok(lst, limits, commute=None):
    return filters.passes(lst, hard(**limits), commute)


def test_no_limits_passes_even_with_nulls():
    nulls = listing(bedrooms=None, property_type=None, epc_current=None, tenure=None, lease_years_remaining=None)
    assert ok(nulls, {})


def test_price_boundary():
    assert ok(listing(price_gbp=500_000), {"max_price_gbp": 500_000})
    assert not ok(listing(price_gbp=500_001), {"max_price_gbp": 500_000})


def test_bedrooms_boundary_and_null():
    assert ok(listing(bedrooms=2), {"min_bedrooms": 2})
    assert not ok(listing(bedrooms=1), {"min_bedrooms": 2})
    assert not ok(listing(bedrooms=None), {"min_bedrooms": 2})
    assert ok(listing(bedrooms=0), {"min_bedrooms": 0})
    assert not ok(listing(bedrooms=None), {"min_bedrooms": 0})


def test_property_type_exact_and_null():
    assert ok(listing(property_type="flat"), {"property_types": ["flat", "maisonette"]})
    assert not ok(listing(property_type="detached"), {"property_types": ["flat", "maisonette"]})
    assert not ok(listing(property_type=None), {"property_types": ["flat"]})


@pytest.mark.parametrize("kind", ["house", "terraced", "semi_detached", "end_of_terrace", "detached", "bungalow"])
def test_house_expands(kind):
    assert ok(listing(property_type=kind), {"property_types": ["house"]})


def test_house_does_not_admit_flats_and_specific_type_stays_narrow():
    assert not ok(listing(property_type="flat"), {"property_types": ["house"]})
    assert not ok(listing(property_type="other"), {"property_types": ["house"]})
    assert not ok(listing(property_type="detached"), {"property_types": ["terraced"]})


def test_epc_ordering():
    assert ok(listing(epc_current="A"), {"min_epc": "C"})
    assert ok(listing(epc_current="C"), {"min_epc": "C"})
    assert not ok(listing(epc_current="D"), {"min_epc": "C"})
    assert not ok(listing(epc_current="G"), {"min_epc": "F"})
    assert ok(listing(epc_current="G"), {"min_epc": "G"})
    assert not ok(listing(epc_current=None), {"min_epc": "G"})


def test_tenure():
    assert ok(listing(tenure="freehold"), {"tenure": "freehold"})
    assert not ok(listing(tenure="leasehold"), {"tenure": "freehold"})
    assert not ok(listing(tenure="share_of_freehold"), {"tenure": "freehold"})
    assert not ok(listing(tenure=None), {"tenure": "freehold"})


def test_lease_boundary_and_known_short_lease():
    assert ok(listing(lease_years_remaining=90), {"min_lease_years": 90})
    assert not ok(listing(lease_years_remaining=89), {"min_lease_years": 90})


def test_lease_known_short_excluded_whatever_the_tenure():
    for tenure in ("leasehold", "share_of_freehold", "freehold", None):
        assert not ok(listing(tenure=tenure, lease_years_remaining=60), {"min_lease_years": 90})


def test_lease_known_long_passes_whatever_the_tenure():
    for tenure in ("leasehold", "share_of_freehold", "freehold", None):
        assert ok(listing(tenure=tenure, lease_years_remaining=150), {"min_lease_years": 90})


def test_lease_null_depends_on_tenure():
    limits = {"min_lease_years": 90}
    assert not ok(listing(tenure="leasehold", lease_years_remaining=None), limits)
    assert ok(listing(tenure="freehold", lease_years_remaining=None), limits)
    assert ok(listing(tenure="share_of_freehold", lease_years_remaining=None), limits)
    assert not ok(listing(tenure=None, lease_years_remaining=None), limits)


def test_commute():
    limits = {"max_commute_min": 45}
    assert ok(listing(), limits, 45)
    assert not ok(listing(), limits, 46)
    assert not ok(listing(), limits, None)
    assert ok(listing(), {}, None)
    assert ok(listing(), {}, 999)


def test_every_limit_must_hold():
    limits = {"max_price_gbp": 600_000, "min_bedrooms": 2, "min_epc": "C"}
    assert ok(listing(), limits)
    assert not ok(listing(price_gbp=700_000), limits)
    assert not ok(listing(bedrooms=1), limits)
    assert not ok(listing(epc_current="E"), limits)


class FakeDb:
    def __init__(self, rows):
        self.rows, self.sql = rows, []

    def prepare(self, sql):
        self.sql.append(sql)
        return self

    async def all(self):
        return type("Result", (), {"results": self.rows})()


ROWS = [
    listing(id="a", price_gbp=400_000),
    listing(id="b", price_gbp=600_000),
    listing(id="c", price_gbp=400_000, bedrooms=None),
]


def test_matching_ids_without_commutes_ignores_commute_limit():
    db = FakeDb(ROWS)
    ids = asyncio.run(filters.matching_listing_ids(db, hard(max_price_gbp=500_000, max_commute_min=30)))
    assert ids == ["a", "c"]
    assert len(db.sql) == 1 and "?" not in db.sql[0]


def test_matching_ids_with_commutes_applies_commute_limit():
    commutes = {"a": 20, "b": 10, "c": None}
    ids = asyncio.run(filters.matching_listing_ids(FakeDb(ROWS), hard(max_commute_min=30), commutes))
    assert ids == ["a", "b"]


# Real listings, read-only. The independent check below is written out plainly and does not call passes().
PREF_SETS = {
    "price only": {"max_price_gbp": 500_000},
    "family house": {"max_price_gbp": 900_000, "min_bedrooms": 3, "property_types": ["house"]},
    "flat good epc": {"property_types": ["flat", "maisonette"], "min_epc": "C", "max_price_gbp": 600_000},
    "freehold detached": {"tenure": "freehold", "property_types": ["detached", "bungalow"]},
    "long lease flat": {"property_types": ["flat"], "min_lease_years": 100, "min_bedrooms": 1},
    "everything": {"max_price_gbp": 750_000, "min_bedrooms": 2, "property_types": ["terraced", "semi_detached"],
                   "min_epc": "D", "tenure": "freehold", "min_lease_years": 50},
    "leasehold 90": {"tenure": "leasehold", "min_lease_years": 90},
    "share of freehold lease": {"tenure": "share_of_freehold", "min_lease_years": 80},
}


def meets_every_limit(r, lim):
    """True when the row meets every set limit. None means a field is unknown, which fails a set limit."""
    if lim.get("max_price_gbp") is not None and r["price_gbp"] > lim["max_price_gbp"]:
        return False
    if lim.get("min_bedrooms") is not None and (r["bedrooms"] is None or r["bedrooms"] < lim["min_bedrooms"]):
        return False
    if lim.get("property_types") is not None:
        wanted = list(lim["property_types"])
        if "house" in wanted:
            wanted += ["terraced", "semi_detached", "end_of_terrace", "detached", "bungalow"]
        if r["property_type"] is None or r["property_type"] not in wanted:
            return False
    if lim.get("min_epc") is not None and (r["epc_current"] is None or "ABCDEFG".index(r["epc_current"]) > "ABCDEFG".index(lim["min_epc"])):
        return False
    if lim.get("tenure") is not None and r["tenure"] != lim["tenure"]:
        return False
    if lim.get("min_lease_years") is not None:
        if r["lease_years_remaining"] is not None:
            if r["lease_years_remaining"] < lim["min_lease_years"]:
                return False
        elif r["tenure"] not in ("freehold", "share_of_freehold"):
            return False
    return True


@pytest.fixture(scope="module")
def real_rows():
    if not LISTINGS_DB.exists():
        pytest.skip("dataset/listings.sqlite not present")
    con = sqlite3.connect(f"file:{LISTINGS_DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute(f"SELECT {filters.FILTER_COLUMNS} FROM listings")]
    con.close()
    return rows


@pytest.mark.parametrize("name", list(PREF_SETS))
def test_real_listings_zero_violations(real_rows, name):
    lim = PREF_SETS[name]
    returned = set(asyncio.run(filters.matching_listing_ids(FakeDb(real_rows), hard(**lim))))
    for r in real_rows:
        assert (r["id"] in returned) == meets_every_limit(r, lim), (name, r)


def test_real_pool_sizes_are_not_degenerate(real_rows):
    sizes = {n: sum(meets_every_limit(r, lim) for r in real_rows) for n, lim in PREF_SETS.items()}
    assert sizes["price only"] > 0 and sizes["family house"] > 0
    assert any(s < len(real_rows) for s in sizes.values())


class CacheDb:
    """Answers the listings query and the commute_cache query, as D1 would."""

    def __init__(self, rows, cache):
        self.rows, self.cache, self.bound = rows, cache, []
        self._sql = ""

    def prepare(self, sql):
        self._sql = sql
        return self

    def bind(self, *args):
        self.bound.append(args)
        return self

    async def all(self):
        if "commute_cache" in self._sql:
            results = [{"listing_id": k, "minutes": v} for k, v in self.cache.items()]
        else:
            results = self.rows
        return type("Result", (), {"results": results})()


def test_postcode_entry_point_uses_cached_minutes():
    db = CacheDb(ROWS, {"a": 20, "b": 50, "c": 25})
    ids = asyncio.run(filters.matching_listing_ids_for_postcode(db, hard(max_commute_min=30), "EC2N 2DB"))
    assert ids == ["a", "c"]
    assert db.bound == [("EC2N 2DB",)]


def test_postcode_entry_point_excludes_uncached_and_no_journey_when_limit_set():
    db = CacheDb(ROWS, {"a": 20, "b": None})  # b: TfL found no journey; c: never fetched
    ids = asyncio.run(filters.matching_listing_ids_for_postcode(db, hard(max_commute_min=30), "EC2N 2DB"))
    assert ids == ["a"]


def test_postcode_entry_point_ignores_cache_when_no_limit_set():
    db = CacheDb(ROWS, {})
    ids = asyncio.run(filters.matching_listing_ids_for_postcode(db, hard(max_price_gbp=500_000), "EC2N 2DB"))
    assert ids == ["a", "c"]
