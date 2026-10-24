"""Hard filters: a listing either meets every limit the buyer set or it is out. Unknown never passes a set limit."""
from prefs import EPC_RATINGS

HOUSE_TYPES = {"house", "terraced", "semi_detached", "end_of_terrace", "detached", "bungalow"}

FILTER_COLUMNS = "id, price_gbp, bedrooms, property_type, epc_current, tenure, lease_years_remaining"


def _lease_ok(listing, minimum) -> bool:
    lease = listing["lease_years_remaining"]
    if lease is not None:
        return lease >= minimum
    # No lease figure: only a leasehold (or unknown tenure) could still be short.
    return listing["tenure"] in ("freehold", "share_of_freehold")


def passes(listing, hard, commute_minutes) -> bool:
    """True when the listing meets every non-null limit in `hard`."""
    if hard.get("max_price_gbp") is not None and not listing["price_gbp"] <= hard["max_price_gbp"]:
        return False
    if hard.get("min_bedrooms") is not None:
        if listing["bedrooms"] is None or listing["bedrooms"] < hard["min_bedrooms"]:
            return False
    if hard.get("property_types") is not None:
        allowed = set(hard["property_types"])
        if "house" in allowed:
            allowed |= HOUSE_TYPES
        if listing["property_type"] not in allowed:
            return False
    if hard.get("min_epc") is not None:
        epc = listing["epc_current"]
        if epc is None or EPC_RATINGS.index(epc) > EPC_RATINGS.index(hard["min_epc"]):
            return False
    if hard.get("tenure") is not None and listing["tenure"] != hard["tenure"]:
        return False
    if hard.get("min_lease_years") is not None and not _lease_ok(listing, hard["min_lease_years"]):
        return False
    if hard.get("max_commute_min") is not None:
        if commute_minutes is None or commute_minutes > hard["max_commute_min"]:
            return False
    return True


async def matching_listing_ids(db, hard, commutes=None) -> list[str]:
    """Ids of listings that pass `hard`. `commutes` maps listing id to minutes; None skips the commute limit."""
    rows = (await db.prepare(f"SELECT {FILTER_COLUMNS} FROM listings ORDER BY id").all()).results
    if commutes is not None:
        return [r["id"] for r in rows if passes(r, hard, commutes.get(r["id"]))]
    return [r["id"] for r in rows if passes(r, {**hard, "max_commute_min": None}, None)]
