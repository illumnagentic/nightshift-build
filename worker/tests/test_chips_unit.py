import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import chips  # noqa: E402


def listing(*features, **over):
    base = {
        "property_type": "flat", "bedrooms": 1, "epc_current": None, "tenure": "freehold",
        "lease_years_remaining": None, "service_charge_gbp_pa": None, "floor_level": None,
        "key_features": json.dumps(list(features)),
    }
    return {**base, **over}


def flag(field, value="x", confidence="high", room=None):
    return {"field": field, "value": value, "confidence": confidence, "room": room}


def ids(l, commute=None, stations=(), flags=()):
    return [c["chip_id"] for c in chips.select(l, list(stations), list(flags), commute)]


def offered(l, chip_id, **kw):
    # Compare against the full uncapped rule set by checking the chip table directly.
    c = chips._Context(l, kw.get("stations", []), kw.get("flags", []), kw.get("commute"))
    rule = next(r[3] for r in chips.CHIPS if r[0] == chip_id)
    return chips._holds(rule, c)


def featured(l, chip_id, **kw):
    c = chips._Context(l, kw.get("stations", []), kw.get("flags", []), kw.get("commute"))
    rule = next(r[4] for r in chips.CHIPS if r[0] == chip_id)
    return chips._holds(rule, c)


def test_catalogue_has_twenty_chips_in_priority_order():
    assert [r[0] for r in chips.CHIPS] == [
        "garden", "parking", "natural_light", "balcony_terrace", "price_value", "commute",
        "station_access", "area_busyness", "space", "kitchen", "layout", "condition", "bathrooms",
        "floor_level", "building_amenities", "lease", "service_charge", "energy_efficiency",
        "home_office", "building_style"]
    assert all(len(r[2]) == 4 for r in chips.CHIPS)


def test_output_shape_label_and_phrases():
    out = chips.select(listing(), [], [], None)
    price = next(c for c in out if c["chip_id"] == "price_value")
    assert price == {"chip_id": "price_value", "label": "Price and value",
                     "phrases": ["Good value", "Fair for what it is", "Overpriced", "Over my budget"]}


def test_key_features_accepts_list():
    assert "parking" in ids(listing(key_features=["Allocated parking"]))


@pytest.mark.parametrize("ptype", sorted(chips.HOUSE_TYPES))
def test_garden_offered_on_house_types_not_featured(ptype):
    l = listing(property_type=ptype)
    assert offered(l, "garden") and not featured(l, "garden")


def test_garden_on_flat_needs_mention_or_flag():
    assert not offered(listing(), "garden")
    assert offered(listing("Communal GARDEN"), "garden")
    assert featured(listing("Communal garden"), "garden")
    f = [flag("room", "garden", room="garden")]
    assert offered(listing(), "garden", flags=f) and featured(listing(), "garden", flags=f)


def test_parking():
    for text in ["Off-street parking", "Garage", "driveway", "off street", "Carport", "car park"]:
        assert offered(listing(text), "parking"), text
    assert not offered(listing("Quiet road"), "parking")


def test_natural_light_always_offered_featured_on_text_or_flag():
    assert offered(listing(), "natural_light") and not featured(listing(), "natural_light")
    assert featured(listing("Bright rooms"), "natural_light")
    assert featured(listing("South-facing"), "natural_light")
    assert not featured(listing("Lightweight"), "natural_light")  # word boundary


@pytest.mark.parametrize("value,conf,expected", [
    ("bright", "high", True), ("poor", "medium", True), ("bright", "low", False), ("ok", "high", False)])
def test_light_flag_clause(value, conf, expected):
    f = [flag("light", value, conf)]
    assert featured(listing(), "natural_light", flags=f) is expected


def test_balcony_terrace_rule():
    assert offered(listing("Private balcony"), "balcony_terrace")
    assert offered(listing("Roof terrace"), "balcony_terrace")
    assert offered(listing("Terrace"), "balcony_terrace")  # flat
    assert offered(listing("Terrace", property_type=None), "balcony_terrace")
    assert offered(listing("Terrace", property_type="maisonette"), "balcony_terrace")
    assert not offered(listing("Terrace", property_type="terraced"), "balcony_terrace")
    assert offered(listing("Roof terrace", property_type="terraced"), "balcony_terrace")


def test_price_value_always_offered_and_featured():
    assert offered(listing(), "price_value") and featured(listing(), "price_value")


def test_commute_offered_only_with_minutes():
    assert "commute" not in ids(listing())
    assert "commute" in ids(listing(), commute=0)
    assert "commute" in ids(listing(), commute=35)


def test_station_access():
    near = [{"distance_km": 0.5}]
    far = [{"distance_km": 1.5}, {"distance_km": None}]
    assert not offered(listing(), "station_access", stations=[])
    assert not offered(listing(), "station_access", stations=[{"distance_km": None}])
    assert offered(listing(), "station_access", stations=far)
    assert not featured(listing(), "station_access", stations=far)
    assert featured(listing(), "station_access", stations=near)
    assert featured(listing(), "station_access", stations=[{"distance_km": 0.8}])
    assert featured(listing("Near the Tube"), "station_access", stations=far)


@pytest.mark.parametrize("chip_id,text", [
    ("area_busyness", "Cul-de-sac"), ("area_busyness", "village feel"),
    ("space", "Spacious"), ("space", "850 sq ft"), ("space", "60 sqm"),
    ("kitchen", "Fitted kitchen"), ("layout", "Open plan living"),
    ("condition", "Newly refurbished"), ("condition", "In need of updating"),
    ("bathrooms", "En suite"), ("bathrooms", "Wet room"),
    ("home_office", "Study"), ("home_office", "Work from home"),
])
def test_text_featured_rules(chip_id, text):
    assert offered(listing(), chip_id) is (chip_id != "home_office")
    assert featured(listing(text), chip_id)
    assert not featured(listing("Nothing relevant"), chip_id)


def test_sqm_and_defects_flags_feature_space_and_condition():
    assert featured(listing(), "space", flags=[flag("sqm_estimate", 55, "low")])
    assert not featured(listing(), "space", flags=[flag("light")])
    assert featured(listing(), "condition", flags=[flag("defects", "damp")])
    assert not featured(listing(), "condition", flags=[flag("light")])


def test_floor_level_needs_value_and_flat_like():
    assert offered(listing(floor_level="third"), "floor_level")
    assert not offered(listing(), "floor_level")
    assert not offered(listing(floor_level="ground", property_type="detached"), "floor_level")
    assert offered(listing(floor_level="ground", property_type=None), "floor_level")


def test_building_amenities_flat_or_maisonette_only():
    assert offered(listing("Concierge"), "building_amenities")
    assert offered(listing("Passenger lift", property_type="maisonette"), "building_amenities")
    assert not offered(listing("Concierge", property_type="other"), "building_amenities")
    assert not offered(listing("Concierge", property_type="terraced"), "building_amenities")
    assert not offered(listing("Nothing"), "building_amenities")


def test_lease_and_service_charge():
    for tenure in ("leasehold", "share_of_freehold"):
        l = listing(tenure=tenure, lease_years_remaining=99, service_charge_gbp_pa=1200)
        assert offered(l, "lease") and offered(l, "service_charge")
    l = listing(tenure="leasehold")
    assert not offered(l, "lease") and not offered(l, "service_charge")
    l = listing(tenure="freehold", lease_years_remaining=99, service_charge_gbp_pa=1200)
    assert not offered(l, "lease") and not offered(l, "service_charge")


@pytest.mark.parametrize("epc,expected", [("A", True), ("B", True), ("C", False), ("D", False),
                                          ("E", True), ("F", True), ("G", True)])
def test_energy_efficiency(epc, expected):
    l = listing(epc_current=epc)
    assert offered(l, "energy_efficiency") and featured(l, "energy_efficiency") is expected
    assert not offered(listing(), "energy_efficiency")


def test_home_office():
    assert offered(listing(bedrooms=2), "home_office") and not featured(listing(bedrooms=2), "home_office")
    assert not offered(listing(bedrooms=1), "home_office")
    assert not offered(listing(bedrooms=None), "home_office")
    assert offered(listing("Home office", bedrooms=None), "home_office")


def test_building_style():
    assert offered(listing("Victorian conversion"), "building_style")
    assert offered(listing("Purpose built block"), "building_style")
    assert not offered(listing("Nothing"), "building_style")


def test_mentions_searches_key_features_only():
    l = listing(key_features=json.dumps(["Two bedrooms"]), description="Lovely garden and parking")
    assert not offered(l, "parking") and not offered(l, "garden")


def test_plain_flat_gets_always_chips_featured_first():
    assert ids(listing()) == ["price_value", "natural_light", "area_busyness", "space", "kitchen",
                              "layout", "condition", "bathrooms"]


def test_cap_of_eight_and_featured_first():
    l = listing("Garden", "Parking", "Bright", "Balcony", "Quiet street", "Spacious", "Kitchen",
                "Open plan", "Newly refurbished", "En suite", "Victorian", "Concierge",
                floor_level="third", tenure="leasehold", lease_years_remaining=90,
                service_charge_gbp_pa=900, epc_current="B", bedrooms=3)
    out = ids(l, commute=20, stations=[{"distance_km": 0.3}])
    assert len(out) == 8
    # Everything offered here is featured except home_office, so it is cut first;
    # the featured ones follow priority order.
    assert out == ["garden", "parking", "natural_light", "balcony_terrace", "price_value",
                   "commute", "station_access", "area_busyness"]


def test_featured_chips_outrank_earlier_unfeatured_ones():
    # garden (priority 1) offered on a house but not featured, so it sorts behind featured chips.
    l = listing("Kitchen", property_type="house")
    out = ids(l)
    assert out.index("garden") > out.index("kitchen")
    assert out.index("garden") > out.index("price_value")


def test_chip_cut_by_limit_when_unfeatured():
    # Unfeatured bottom-priority chips fall off the end.
    l = listing(property_type="house", bedrooms=2)
    out = ids(l)
    assert len(out) == 8
    assert "home_office" not in out
