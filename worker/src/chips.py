"""Chip selection: which feedback chips a card offers, per the chip catalogue in docs/api-contract.md. Pure, no I/O."""
import json
import re

from filters import HOUSE_TYPES

MAX_CHIPS = 8
FLAT_LIKE = {"flat", "maisonette", "other", None}
LEASEHOLD_LIKE = {"leasehold", "share_of_freehold"}

_HOME_OFFICE = r"study|office|home working|work(ing)? from home"
_BUILDING_STYLE = r"period|victorian|georgian|edwardian|character|original|art deco|new build|purpose[- ]built|contemporary"

# (chip_id, label, phrases, offered, featured), in priority order. Rules take a context `c`;
# `featured` of True means featured whenever offered.
CHIPS = [
    ("garden", "Garden", ["Lovely garden", "Too small", "Too much upkeep", "Overlooked"],
     lambda c: c.type in HOUSE_TYPES or c.has("garden") or c.garden_flag,
     lambda c: c.has("garden") or c.garden_flag),
    ("parking", "Parking", ["Parking is a big plus", "Hard to use", "Not enough space", "Don't need it"],
     lambda c: c.has(r"parking|garage|driveway|off[- ]street|car ?port|car ?park"), True),
    ("natural_light", "Natural light inside",
     ["Bright and airy", "A bit dark", "Good light in the main room", "Needs more daylight"],
     True, lambda c: c.has(r"\b(bright|light|sunny|airy|south[- ]facing)\b") or c.light_flag),
    ("balcony_terrace", "Balcony or terrace",
     ["Great outdoor spot", "Too small to use", "Overlooked", "Not needed"],
     lambda c: c.has(r"balcon|roof terrace") or (c.has(r"\bterrace\b") and c.type in FLAT_LIKE), True),
    ("price_value", "Price and value",
     ["Good value", "Fair for what it is", "Overpriced", "Over my budget"], True, True),
    ("commute", "Commute",
     ["Easy commute", "Fine a few days a week", "Too long for me", "Too many changes"],
     lambda c: c.commute_minutes is not None, True),
    ("station_access", "Station access",
     ["Close to the station", "Good transport links", "Too far to walk", "Station noise worries me"],
     lambda c: c.nearest is not None,
     lambda c: c.nearest <= 0.8 or c.has(r"station|tube|underground|\bdlr\b|overground")),
    ("area_busyness", "Area and street feel",
     ["Quiet, I love it", "Lively, I like that", "Too busy for me", "Too quiet for me"], True,
     lambda c: c.has(r"quiet|peaceful|tranquil|cul[- ]de[- ]sac|vibrant|bustling|lively|high street|village")),
    ("space", "Space and room sizes",
     ["Plenty of room", "Good size for the price", "Rooms feel small", "More than I need"], True,
     lambda c: c.has(r"spacious|generous|large|ample|\bhuge\b|sq\.? ?ft|sq\.? ?m\b|sqm") or c.sqm_flag),
    ("kitchen", "Kitchen", ["Great kitchen", "Fine as it is", "Needs replacing", "Too small to cook in"],
     True, lambda c: c.has("kitchen")),
    ("layout", "Layout", ["Layout works well", "Love the open plan", "Awkward layout", "Want separate rooms"],
     True, lambda c: c.has(r"open[- ]plan")),
    ("condition", "Condition and decor",
     ["Great condition", "Happy to renovate", "Too dated", "Needs too much work"], True,
     lambda c: c.has(r"refurbish|renovat|modern|newly|new build|immaculate|redecorat|updating|in need of")
     or c.defects_flag),
    ("bathrooms", "Bathrooms",
     ["Good bathroom", "Love the en-suite", "Dated bathroom", "Need more bathrooms"], True,
     lambda c: c.has(r"en[- ]?suite|bathroom|shower room|wet room")),
    ("floor_level", "Floor level", ["Love being up high", "Good floor for me", "Too low", "Too many stairs"],
     lambda c: c.listing["floor_level"] is not None and c.type in FLAT_LIKE, True),
    ("building_amenities", "Building facilities",
     ["Great facilities", "Concierge is a plus", "Would not use them", "Paying for what I don't want"],
     lambda c: c.type in ("flat", "maisonette")
     and c.has(r"concierge|porter|\bgym\b|\blifts?\b|communal|residents|swimming|lounge"), True),
    ("lease", "Lease length",
     ["Long lease, fine", "Lease is too short", "Worried about extending", "Share of freehold helps"],
     lambda c: c.listing["tenure"] in LEASEHOLD_LIKE and c.listing["lease_years_remaining"] is not None, True),
    ("service_charge", "Service charge",
     ["Charge is reasonable", "Too high", "Worried it will rise", "Fine for what's included"],
     lambda c: c.listing["tenure"] in LEASEHOLD_LIKE and c.listing["service_charge_gbp_pa"] is not None, True),
    ("energy_efficiency", "Energy efficiency",
     ["Good energy rating", "Costly to heat", "Happy to improve it", "Rating doesn't matter"],
     lambda c: c.listing["epc_current"] is not None, lambda c: c.listing["epc_current"] in "ABEFG"),
    ("home_office", "Space to work from home",
     ["Room to work from home", "Spare room is useful", "No space for a desk", "Don't need an office"],
     lambda c: (c.listing["bedrooms"] or 0) >= 2 or c.has(_HOME_OFFICE), lambda c: c.has(_HOME_OFFICE)),
    ("building_style", "Period or modern style",
     ["Love the period character", "Prefer a modern build", "Too dated", "Character matters to me"],
     lambda c: c.has(_BUILDING_STYLE), True),
]


class _Context:
    def __init__(self, listing, stations, flags, commute_minutes):
        features = listing["key_features"]
        if isinstance(features, str):
            features = json.loads(features)
        self.listing = listing
        self.text = "\n".join(features)
        self.type = listing["property_type"]
        self.commute_minutes = commute_minutes
        distances = [s["distance_km"] for s in stations if s["distance_km"] is not None]
        self.nearest = min(distances) if distances else None
        self.garden_flag = any(f["room"] == "garden" for f in flags)
        self.light_flag = any(f["field"] == "light" and f["value"] in ("bright", "poor")
                              and f["confidence"] in ("high", "medium") for f in flags)
        self.sqm_flag = any(f["field"] == "sqm_estimate" for f in flags)
        self.defects_flag = any(f["field"] == "defects" for f in flags)

    def has(self, pattern) -> bool:
        return re.search(pattern, self.text, re.IGNORECASE) is not None


def _holds(rule, c) -> bool:
    return rule is True or rule(c)


def select(listing, stations, flags, commute_minutes) -> list[dict]:
    """The card's chips: offered ones, featured first then by priority, at most MAX_CHIPS."""
    c = _Context(listing, stations, flags, commute_minutes)
    offered = [(not _holds(featured, c), chip_id, label, phrases)
               for chip_id, label, phrases, offered, featured in CHIPS if _holds(offered, c)]
    offered.sort(key=lambda o: o[0])  # stable: priority order is kept within each group
    return [{"chip_id": i, "label": label, "phrases": phrases} for _, i, label, phrases in offered[:MAX_CHIPS]]
