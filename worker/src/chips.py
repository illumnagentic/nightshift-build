"""Chip catalogue: which feedback chips a card offers, per docs/api-contract.md (Chip catalogue)."""
import re

HOUSE_TYPES = {"house", "terraced", "semi_detached", "end_of_terrace", "detached", "bungalow"}
LEASEHOLD_LIKE = {"leasehold", "share_of_freehold"}
MAX_CHIPS = 8


class _Card:
    """What the rules read: the listing, plus values worked out once from its stations and flags."""

    def __init__(self, listing, flags, commute_minutes):
        self.listing = listing
        self.text = "\n".join(listing["key_features"])
        self.flat_like = listing["property_type"] in (None, "flat", "maisonette", "other")
        distances = [s["distance_km"] for s in listing["stations"] if s["distance_km"] is not None]
        self.nearest = min(distances) if distances else None
        self.commute_minutes = commute_minutes
        self.garden_flag = any(f["room"] == "garden" for f in flags)
        self.light_flag = any(
            f["field"] == "light" and f["value"] in ("bright", "poor") and f["confidence"] in ("high", "medium")
            for f in flags
        )
        self.sqm_flag = any(f["field"] == "sqm_estimate" for f in flags)
        self.defects_flag = any(f["field"] == "defects" for f in flags)

    def mentions(self, pattern):
        return re.search(pattern, self.text, re.IGNORECASE) is not None


_WORK = r"study|office|home working|work(ing)? from home"

# (chip_id, label, phrases, offered, featured). Position is the priority; featured None means
# featured whenever offered. Rules are the contract's, flag clauses included.
CATALOGUE = (
    ("garden", "Garden", ("Lovely garden", "Too small", "Too much upkeep", "Overlooked"),
     lambda c: c.listing["property_type"] in HOUSE_TYPES or c.mentions("garden") or c.garden_flag,
     lambda c: c.mentions("garden") or c.garden_flag),
    ("parking", "Parking", ("Parking is a big plus", "Hard to use", "Not enough space", "Don't need it"),
     lambda c: c.mentions(r"parking|garage|driveway|off[- ]street|car ?port|car ?park"), None),
    ("natural_light", "Natural light inside",
     ("Bright and airy", "A bit dark", "Good light in the main room", "Needs more daylight"),
     lambda c: True,
     lambda c: c.mentions(r"\b(bright|light|sunny|airy|south[- ]facing)\b") or c.light_flag),
    ("balcony_terrace", "Balcony or terrace",
     ("Great outdoor spot", "Too small to use", "Overlooked", "Not needed"),
     lambda c: c.mentions(r"balcon|roof terrace") or (c.mentions(r"\bterrace\b") and c.flat_like), None),
    ("price_value", "Price and value", ("Good value", "Fair for what it is", "Overpriced", "Over my budget"),
     lambda c: True, None),
    ("commute", "Commute",
     ("Easy commute", "Fine a few days a week", "Too long for me", "Too many changes"),
     lambda c: c.commute_minutes is not None, None),
    ("station_access", "Station access",
     ("Close to the station", "Good transport links", "Too far to walk", "Station noise worries me"),
     lambda c: c.nearest is not None,
     lambda c: c.nearest <= 0.8 or c.mentions(r"station|tube|underground|\bdlr\b|overground")),
    ("area_busyness", "Area and street feel",
     ("Quiet, I love it", "Lively, I like that", "Too busy for me", "Too quiet for me"),
     lambda c: True,
     lambda c: c.mentions(r"quiet|peaceful|tranquil|cul[- ]de[- ]sac|vibrant|bustling|lively|high street|village")),
    ("space", "Space and room sizes",
     ("Plenty of room", "Good size for the price", "Rooms feel small", "More than I need"),
     lambda c: True,
     lambda c: c.mentions(r"spacious|generous|large|ample|\bhuge\b|sq\.? ?ft|sq\.? ?m\b|sqm") or c.sqm_flag),
    ("kitchen", "Kitchen", ("Great kitchen", "Fine as it is", "Needs replacing", "Too small to cook in"),
     lambda c: True, lambda c: c.mentions("kitchen")),
    ("layout", "Layout",
     ("Layout works well", "Love the open plan", "Awkward layout", "Want separate rooms"),
     lambda c: True, lambda c: c.mentions(r"open[- ]plan")),
    ("condition", "Condition and decor",
     ("Great condition", "Happy to renovate", "Too dated", "Needs too much work"),
     lambda c: True,
     lambda c: c.mentions(r"refurbish|renovat|modern|newly|new build|immaculate|redecorat|updating|in need of")
     or c.defects_flag),
    ("bathrooms", "Bathrooms",
     ("Good bathroom", "Love the en-suite", "Dated bathroom", "Need more bathrooms"),
     lambda c: True, lambda c: c.mentions(r"en[- ]?suite|bathroom|shower room|wet room")),
    ("floor_level", "Floor level", ("Love being up high", "Good floor for me", "Too low", "Too many stairs"),
     lambda c: c.listing["floor_level"] is not None and c.flat_like, None),
    ("building_amenities", "Building facilities",
     ("Great facilities", "Concierge is a plus", "Would not use them", "Paying for what I don't want"),
     lambda c: c.listing["property_type"] in ("flat", "maisonette")
     and c.mentions(r"concierge|porter|\bgym\b|\blifts?\b|communal|residents|swimming|lounge"), None),
    ("lease", "Lease length",
     ("Long lease, fine", "Lease is too short", "Worried about extending", "Share of freehold helps"),
     lambda c: c.listing["tenure"] in LEASEHOLD_LIKE and c.listing["lease_years_remaining"] is not None, None),
    ("service_charge", "Service charge",
     ("Charge is reasonable", "Too high", "Worried it will rise", "Fine for what's included"),
     lambda c: c.listing["tenure"] in LEASEHOLD_LIKE and c.listing["service_charge_gbp_pa"] is not None, None),
    ("energy_efficiency", "Energy efficiency",
     ("Good energy rating", "Costly to heat", "Happy to improve it", "Rating doesn't matter"),
     lambda c: c.listing["epc_current"] is not None,
     lambda c: c.listing["epc_current"] in ("A", "B", "E", "F", "G")),
    ("home_office", "Space to work from home",
     ("Room to work from home", "Spare room is useful", "No space for a desk", "Don't need an office"),
     lambda c: (c.listing["bedrooms"] or 0) >= 2 or c.mentions(_WORK), lambda c: c.mentions(_WORK)),
    ("building_style", "Period or modern style",
     ("Love the period character", "Prefer a modern build", "Too dated", "Character matters to me"),
     lambda c: c.mentions(
         r"period|victorian|georgian|edwardian|character|original|art deco|new build|purpose[- ]built|contemporary"),
     None),
)

_BY_ID = {row[0]: row for row in CATALOGUE}


def chip_ids_for(listing, flags, commute_minutes):
    """Ordered chip ids for one card: at most 8, featured first, then catalogue priority.

    `listing` needs the listings columns the rules read, `key_features` as a list, and
    `stations` as a list of mappings with `distance_km`. `flags` are photo_flags rows; only
    `field`, `value`, `confidence` and `room` are read, never `corrected_text`.
    """
    card = _Card(listing, flags, commute_minutes)
    offered = []
    for priority, (chip_id, _label, _phrases, is_offered, is_featured) in enumerate(CATALOGUE):
        if is_offered(card):
            offered.append((is_featured is not None and not is_featured(card), priority, chip_id))
    offered.sort()
    return [chip_id for _, _, chip_id in offered[:MAX_CHIPS]]


def chip_objects(chip_ids):
    """Card JSON for chip ids, in the order given."""
    return [{"chip_id": i, "label": _BY_ID[i][1], "phrases": list(_BY_ID[i][2])} for i in chip_ids]
