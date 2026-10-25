import re
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import chips  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
LISTINGS_DB = ROOT / "dataset" / "listings.sqlite"
CONTRACT = ROOT / "docs" / "api-contract.md"


def listing(features=(), stations=(), **over):
    base = {
        "property_type": "flat", "floor_level": None, "tenure": None, "lease_years_remaining": None,
        "service_charge_gbp_pa": None, "epc_current": None, "bedrooms": 1,
        "key_features": list(features), "stations": [{"distance_km": d} for d in stations],
    }
    return {**base, **over}


def flag(field, value="x", confidence="high", room="other", corrected_text=None):
    return {"field": field, "value": value, "confidence": confidence, "room": room, "corrected_text": corrected_text}


def ids(lst, flags=(), minutes=None):
    return chips.chip_ids_for(lst, list(flags), minutes)


def offered(chip_id, lst, flags=(), minutes=None):
    """Offered ignoring the cap: reads the rule directly."""
    row = next(r for r in chips.CATALOGUE if r[0] == chip_id)
    return row[3](chips._Card(lst, list(flags), minutes))


def featured(chip_id, lst, flags=(), minutes=None):
    row = next(r for r in chips.CATALOGUE if r[0] == chip_id)
    return row[4] is None or row[4](chips._Card(lst, list(flags), minutes))


# ---- the constant matches the contract ----

def _contract_section(title):
    text = CONTRACT.read_text()
    start = text.index(f"### {title}")
    end = text.index("\n#", start + 4)
    return text[start:end]


def test_catalogue_matches_contract_chip_table():
    rows = re.findall(r"^\| (\d+) \| `(\w+)` \| ([^|]+) \|", _contract_section("Chips"), re.M)
    assert [(int(n), c, label.strip()) for n, c, label in rows] == [
        (i + 1, r[0], r[1]) for i, r in enumerate(chips.CATALOGUE)
    ]


def test_catalogue_matches_contract_phrases():
    rows = re.findall(r"^\| `(\w+)` \| (\".*\") \|$", _contract_section("Preset phrases"), re.M)
    assert {c: tuple(re.findall(r'"([^"]*)"', p)) for c, p in rows} == {r[0]: r[2] for r in chips.CATALOGUE}


def test_chip_objects():
    assert chips.chip_objects(["parking", "garden"]) == [
        {"chip_id": "parking", "label": "Parking",
         "phrases": ["Parking is a big plus", "Hard to use", "Not enough space", "Don't need it"]},
        {"chip_id": "garden", "label": "Garden", "phrases": ["Lovely garden", "Too small", "Too much upkeep", "Overlooked"]},
    ]


# ---- offered and featured rules ----

@pytest.mark.parametrize("kind", ["house", "terraced", "semi_detached", "end_of_terrace", "detached", "bungalow"])
def test_garden_offered_on_house_types_but_not_featured(kind):
    lst = listing(property_type=kind)
    assert offered("garden", lst) and not featured("garden", lst)


def test_garden_rules():
    assert not offered("garden", listing())
    assert offered("garden", listing(["Communal Garden"])) and featured("garden", listing(["Communal Garden"]))
    flagged = [flag("light", room="garden")]
    assert offered("garden", listing(), flagged) and featured("garden", listing(), flagged)
    assert not offered("garden", listing(), [flag("light", room="kitchen")])


def test_parking():
    for text in ["Off-street parking", "Garage", "Driveway", "off street", "Carport", "car park"]:
        assert offered("parking", listing([text])), text
    assert not offered("parking", listing(["Bright flat"]))


def test_natural_light_text_and_flag():
    assert offered("natural_light", listing())
    assert not featured("natural_light", listing())
    assert featured("natural_light", listing(["South-facing"]))
    assert not featured("natural_light", listing(["Highlights"]))  # whole word only
    for conf in ("high", "medium"):
        assert featured("natural_light", listing(), [flag("light", "poor", conf)])
        assert not featured("natural_light", listing(), [flag("light", "bright", conf)])
    assert not featured("natural_light", listing(), [flag("light", "poor", "low")])
    assert not featured("natural_light", listing(), [flag("light", "bright", "low")])
    assert not featured("natural_light", listing(), [flag("light", "ok", "high")])
    assert not featured("natural_light", listing(), [flag("light", "none", "high")])


def test_balcony_terrace_and_bare_terrace_rule():
    assert offered("balcony_terrace", listing(["Private balcony"], property_type="detached"))
    assert offered("balcony_terrace", listing(["Roof terrace"], property_type="detached"))
    assert offered("balcony_terrace", listing(["Terrace"], property_type="flat"))
    assert offered("balcony_terrace", listing(["Terrace"], property_type="maisonette"))
    assert offered("balcony_terrace", listing(["Terrace"], property_type="other"))
    assert offered("balcony_terrace", listing(["Terrace"], property_type=None))
    for kind in ("house", "terraced", "semi_detached", "end_of_terrace", "detached", "bungalow"):
        assert not offered("balcony_terrace", listing(["Terrace"], property_type=kind)), kind
    assert not offered("balcony_terrace", listing(["Terraced house"], property_type="flat"))


def test_price_value_always():
    assert offered("price_value", listing())


def test_commute_only_with_minutes():
    assert "commute" not in ids(listing())
    assert "commute" in ids(listing(), minutes=35)
    assert "commute" in ids(listing(), minutes=0)


def test_station_access():
    assert not offered("station_access", listing())
    assert not offered("station_access", listing(stations=[None]))
    near = listing(stations=[None, 0.8])
    assert offered("station_access", near) and featured("station_access", near)
    far = listing(stations=[1.5, 0.9])
    assert offered("station_access", far) and not featured("station_access", far)
    assert featured("station_access", listing(["Close to tube"], stations=[2.0]))
    assert featured("station_access", listing(["Overground nearby"], stations=[2.0]))


def test_area_busyness():
    assert offered("area_busyness", listing())
    assert not featured("area_busyness", listing())
    assert featured("area_busyness", listing(["Quiet cul-de-sac"]))


def test_space_text_and_flag():
    assert offered("space", listing()) and not featured("space", listing())
    assert featured("space", listing(["Spacious"]))
    assert featured("space", listing(["650 sq ft"]))
    assert not featured("space", listing(), [flag("sqm_estimate", 55.0, "high")])
    assert not featured("space", listing(), [flag("sqm_estimate", 55.0, "low")])
    assert not featured("space", listing(), [flag("floorplan_notes")])


def test_kitchen_layout_bathrooms():
    assert offered("kitchen", listing()) and not featured("kitchen", listing())
    assert featured("kitchen", listing(["Fitted kitchen"]))
    assert not featured("layout", listing()) and featured("layout", listing(["Open plan living"]))
    assert not featured("bathrooms", listing()) and featured("bathrooms", listing(["Two bathrooms"]))
    assert featured("bathrooms", listing(["En-suite"]))


def test_condition_text_and_flag():
    assert offered("condition", listing()) and not featured("condition", listing())
    assert featured("condition", listing(["Newly refurbished"]))
    assert featured("condition", listing(), [flag("defects", "worn carpet", "low")])
    assert not featured("condition", listing(), [flag("size_tricks")])


def test_floor_level():
    assert offered("floor_level", listing(floor_level="ground floor"))
    assert offered("floor_level", listing(floor_level="2", property_type=None))
    assert not offered("floor_level", listing())
    assert not offered("floor_level", listing(floor_level="ground", property_type="detached"))


def test_building_amenities():
    assert offered("building_amenities", listing(["Lift"], property_type="flat"))
    assert offered("building_amenities", listing(["Concierge"], property_type="maisonette"))
    assert not offered("building_amenities", listing(["Concierge"], property_type="other"))
    assert not offered("building_amenities", listing(["Gym"], property_type=None))
    assert not offered("building_amenities", listing(["Nothing"], property_type="flat"))
    assert not offered("building_amenities", listing(["Shifts"], property_type="flat"))  # \blifts?\b


@pytest.mark.parametrize("tenure,expected", [("leasehold", True), ("share_of_freehold", True), ("freehold", False), (None, False)])
def test_lease_and_service_charge(tenure, expected):
    lst = listing(tenure=tenure, lease_years_remaining=90, service_charge_gbp_pa=1200.0)
    assert offered("lease", lst) is expected
    assert offered("service_charge", lst) is expected


def test_lease_and_service_charge_need_figure():
    assert not offered("lease", listing(tenure="leasehold", service_charge_gbp_pa=1.0))
    assert not offered("service_charge", listing(tenure="leasehold", lease_years_remaining=90))


def test_energy_efficiency():
    assert not offered("energy_efficiency", listing())
    for rating in "ABEFG":
        assert featured("energy_efficiency", listing(epc_current=rating)), rating
    for rating in "CD":
        lst = listing(epc_current=rating)
        assert offered("energy_efficiency", lst) and not featured("energy_efficiency", lst)


def test_home_office():
    assert offered("home_office", listing(bedrooms=2)) and not featured("home_office", listing(bedrooms=2))
    assert not offered("home_office", listing(bedrooms=1))
    assert not offered("home_office", listing(bedrooms=None))
    assert offered("home_office", listing(["Study"], bedrooms=0)) and featured("home_office", listing(["Study"], bedrooms=0))
    assert offered("home_office", listing(["Ideal for working from home"], bedrooms=None))


def test_building_style():
    assert not offered("building_style", listing())
    for text in ("Victorian", "Period features", "Art Deco", "Purpose-built block", "Contemporary finish"):
        assert offered("building_style", listing([text])), text


def test_only_key_features_are_searched():
    lst = listing(description="garden parking kitchen")
    assert not offered("parking", lst) and not featured("kitchen", lst)


# ---- per-card order and cap ----

def test_plain_card_order():
    # price_value is featured whenever offered; the rest are unfeatured and follow in priority order.
    assert ids(listing()) == ["price_value", "natural_light", "area_busyness", "space", "kitchen", "layout", "condition", "bathrooms"]


def test_featured_first_then_priority_and_cap_cuts_lowest():
    lst = listing(
        ["Garden", "Parking", "Bright", "Balcony", "Near station", "Quiet", "Spacious", "Fitted kitchen",
         "Open plan", "Refurbished", "En-suite", "Study", "Victorian"],
        stations=[0.3], epc_current="F", bedrooms=3,
    )
    got = ids(lst, minutes=20)
    assert len(got) == 8
    # Featured: garden, parking, natural_light, balcony_terrace, price_value, commute, station_access, area_busyness, ...
    assert got == ["garden", "parking", "natural_light", "balcony_terrace", "price_value", "commute", "station_access", "area_busyness"]


def test_featured_chip_beats_lower_number_unfeatured_chip():
    # natural_light (3) and area_busyness (8) are offered everywhere; only area_busyness is featured.
    got = ids(listing(["Quiet"]))
    assert got.index("area_busyness") < got.index("natural_light")


def test_commute_chip_takes_its_place_by_priority():
    got = ids(listing(), minutes=40)
    assert got[:3] == ["price_value", "commute", "natural_light"]  # featured first: price_value, commute


def test_corrected_text_never_changes_chips():
    base = [flag("light", "bright", "high", "living_room"), flag("defects", "damp", "low", "bedroom"),
            flag("sqm_estimate", 50.0, "high", None), flag("light", "ok", "high", "garden")]
    corrected = [{**f, "corrected_text": "not damp, actually fine"} for f in base]
    lst = listing(["Garden"])
    assert ids(lst, base) == ids(lst, corrected)
    assert ids(lst, [flag("defects", "x")]) == ids(lst, [flag("defects", "x", corrected_text="corrected")])


# ---- recount over the committed dataset ----

def _load():
    db = sqlite3.connect(f"file:{LISTINGS_DB}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    try:
        import json
        stations, flags = {}, {}
        for r in db.execute("select listing_id, distance_km from listing_stations"):
            stations.setdefault(r["listing_id"], []).append({"distance_km": r["distance_km"]})
        for r in db.execute("select listing_id, field, value, confidence, room, corrected_text from photo_flags"):
            flags.setdefault(r["listing_id"], []).append(dict(r))
        out = []
        for r in db.execute("select * from listings order by id"):
            lst = {**dict(r), "key_features": json.loads(r["key_features"]), "stations": stations.get(r["id"], [])}
            out.append((lst, flags.get(r["id"], [])))
        return out
    finally:
        db.close()


def _counts(rows, with_flags):
    result = {r[0]: [0, 0, 0] for r in chips.CATALOGUE}
    for lst, fl in rows:
        card = chips._Card(lst, fl if with_flags else [], None)
        sent = set(chips.chip_ids_for(lst, fl if with_flags else [], None))
        for chip_id, _l, _p, is_offered, is_featured in chips.CATALOGUE:
            if is_offered(card):
                result[chip_id][0] += 1
                result[chip_id][1] += is_featured is None or bool(is_featured(card))
            result[chip_id][2] += chip_id in sent
    return result


def test_recount_without_flags_matches_earlier_coverage():
    got = _counts(_load(), with_flags=False)
    expected = {
        "garden": (418, 312, 412), "parking": (264, 264, 264), "natural_light": (635, 108, 515),
        "balcony_terrace": (124, 124, 124), "station_access": (635, 383, 558), "area_busyness": (635, 68, 343),
        "space": (635, 283, 438), "kitchen": (635, 257, 381), "layout": (635, 123, 172),
        "condition": (635, 147, 148), "price_value": (635, 635, 635), "bathrooms": (635, 310, 296),
        "floor_level": (135, 135, 123), "building_amenities": (99, 99, 81), "lease": (225, 225, 183),
        "service_charge": (207, 207, 143), "energy_efficiency": (635, 170, 128), "home_office": (561, 57, 43),
        "building_style": (140, 140, 93), "commute": (0, 0, 0),
    }
    assert {k: tuple(v) for k, v in got.items()} == expected


def test_recount_with_flags():
    rows = _load()
    assert len(rows) == 635
    got = _counts(rows, with_flags=True)
    expected = {
        "garden": (496, 448, 493), "parking": (264, 264, 264), "natural_light": (635, 128, 503),
        "balcony_terrace": (124, 124, 124), "station_access": (635, 383, 547), "area_busyness": (635, 68, 309),
        "space": (635, 283, 415), "kitchen": (635, 257, 350), "layout": (635, 123, 152),
        "condition": (635, 267, 261), "price_value": (635, 635, 635), "bathrooms": (635, 310, 290),
        "floor_level": (135, 135, 116), "building_amenities": (99, 99, 76), "lease": (225, 225, 171),
        "service_charge": (207, 207, 130), "energy_efficiency": (635, 170, 118), "home_office": (561, 57, 42),
        "building_style": (140, 140, 84), "commute": (0, 0, 0),
    }
    assert {k: tuple(v) for k, v in got.items()} == expected
    for lst, fl in rows:
        got_ids = chips.chip_ids_for(lst, fl, None)
        assert len(got_ids) == 8 and len(set(got_ids)) == 8


@pytest.mark.parametrize("minutes, expected", [(None, (1, 7, 14, 142)), (20, (2, 8, 15, 212))])
def test_featured_chips_per_card_with_flags(minutes, expected):
    counts = []
    for lst, fl in _load():
        card = chips._Card(lst, fl, minutes)
        counts.append(sum(1 for r in chips.CATALOGUE if r[3](card) and (r[4] is None or r[4](card))))
    counts.sort()
    assert (counts[0], counts[len(counts) // 2], counts[-1], sum(n > 8 for n in counts)) == expected
