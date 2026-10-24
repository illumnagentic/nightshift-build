"""Sanitising rules that turn a built listing record into one that fits d1/schema.sql.

Pure functions: nothing here reads files, prints or keeps state. sanitise_record
returns the clean record plus a list of event strings; the caller counts them.

Event strings:
  nulled:<field>:<reason>          value set to NULL
  unknown_enum:<field>:<raw>       value not in the schema's closed set
  dropped_row:<field>              a NOT NULL field was missing or out of range
  station_dropped:no_name          station without a name, left out
  station_unit:<source>:<declared>:<used>   unit used to convert one station distance
"""
import html as htmllib
import math
import re
from datetime import datetime, timezone

# Bounds repeat the CHECKs in d1/schema.sql. Keep the two in step by hand.
RANGES = {
    "price_gbp": (10_000, 50_000_000, True),
    "bedrooms": (0, 10, True),
    "bathrooms": (0, 10, True),
    "lat": (50.5, 52.5, False),
    "lon": (-2.5, 1.5, False),
    "lease_years_remaining": (1, 999, True),
    "service_charge_gbp_pa": (0, 100_000, False),
    "ground_rent_gbp_pa": (0, 100_000, False),
    "distance_km": (0, 100, False),
}

SOURCES = {"rightmove", "rapidapi_uk_real_estate_rightmove"}

# Keys are lower-case raw values. A None value means "known, and NULL by rule".
PROPERTY_TYPE = {
    "flat": "flat", "apartment": "flat", "penthouse": "flat", "ground flat": "flat",
    "maisonette": "maisonette", "duplex": "maisonette",
    "house": "house", "town house": "house",
    "terraced": "terraced", "semi-detached": "semi_detached", "end of terrace": "end_of_terrace",
    "detached": "detached", "link detached house": "detached",
    "bungalow": "bungalow", "detached bungalow": "bungalow",
    "block of apartments": "other",
    "not specified": None,
}
TENURE = {"freehold": "freehold", "leasehold": "leasehold", "share_of_freehold": "share_of_freehold"}
COUNCIL_TAX_BAND = dict({c.lower(): c for c in "ABCDEFGH"}, tbc=None)
EPC_RATING = {c.lower(): c for c in "ABCDEFG"}
PRICE_QUALIFIER = {
    "guide price": "guide_price",
    "offers in excess of": "offers_over", "offers over": "offers_over",
    "offers in region of": "offers_in_region",
    "fixed price": "fixed_price",
}

KM_PER_UNIT = {"miles": 1.609344}
# All distances come from Rightmove, which shows miles. The web pages say so; the
# RapidAPI app API gives no unit, and for the three stations that appear in both feeds
# (Crouch Hill, Finsbury Park, Upper Holloway) its figure matched the position fitted
# to the web pages' mile values within 0.01 miles, against 0.29 to 0.32 as kilometres.
# Decided by the project owner on 2026-10-24: a missing unit means miles.
DEFAULT_UNIT = "miles"

# A 0 in service charge, ground rent or any other number is a real 0 and is kept
# (project owner, 2026-10-24). The one exception is lease_years_remaining: the schema
# allows 1 to 999 and Rightmove fills 0 where no lease applies, so 0 becomes NULL.

COLUMNS = [
    "id", "source", "source_id", "url", "price_gbp", "price_qualifier", "bedrooms", "bathrooms",
    "property_type", "address", "postcode", "lat", "lon", "tenure", "lease_years_remaining",
    "service_charge_gbp_pa", "ground_rent_gbp_pa", "council_tax_band", "epc_current",
    "epc_potential", "floor_level", "key_features", "description", "agent_name", "listed_date",
    "fetched_at", "parsed_fields", "media", "stations",
]


def strip_html(s):
    if not s:
        return ""
    s = re.sub(r"<br\s*/?>|</p>|</li>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = htmllib.unescape(s)
    s = re.sub(r"[ \t\r\f\v]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n\n", s)
    return s.strip()


def clean_text(s):
    """HTML removed, spaces collapsed, paragraph breaks kept. '' becomes None."""
    if not isinstance(s, str):
        return None
    s = strip_html(s)
    s = re.sub(r"[^\S\n]+", " ", s)
    s = re.sub(r" ?\n ?", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip() or None


def clean_line(s, strip_tags=False):
    """One line of text with all whitespace collapsed. '' becomes None."""
    if not isinstance(s, str):
        return None
    if strip_tags:
        s = strip_html(s)
    return " ".join(s.split()) or None


def enum_value(table, raw):
    """(value, known). Blank raw is known and NULL; a raw value not in the table is unknown."""
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None, True
    key = str(raw).strip().lower()
    if key in table:
        return table[key], True
    return None, False


def number(v, field):
    """(value, reason). reason is None when v is a number inside the schema bounds."""
    lo, hi, integer = RANGES[field]
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        return None, "not_a_number"
    if integer:
        if v != int(v):
            return None, "not_an_integer"
        v = int(v)
    if not lo <= v <= hi:
        return None, "out_of_range"
    return v, None


def iso_utc(s):
    """'YYYY-MM-DDTHH:MM:SSZ' in UTC, or None if s is not a date. A time with no
    zone is read as UTC; a bare date becomes midnight UTC."""
    if not isinstance(s, str):
        return None
    try:
        d = datetime.fromisoformat(s.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def distance_km(distance, unit, source):
    """(km, events). The unit comes from the record, else DEFAULT_UNIT."""
    if distance is None:
        return None, []
    used = (unit or DEFAULT_UNIT).lower()
    ev = ["station_unit:%s:%s:%s" % (source, unit or "none", used or "none")]
    if used not in KM_PER_UNIT:
        return None, ev + ["nulled:distance_km:unknown_unit"]
    if isinstance(distance, bool) or not isinstance(distance, (int, float)):
        return None, ev + ["nulled:distance_km:not_a_number"]
    km, why = number(distance * KM_PER_UNIT[used], "distance_km")
    if why:
        return None, ev + ["nulled:distance_km:" + why]
    return round(km, 3), ev


def sanitise_record(r):
    """(clean record, events). The record is None when a NOT NULL field is unusable."""
    ev = []

    def drop(field):
        return None, ev + ["dropped_row:" + field]

    out = {}
    for f in ("id", "source_id", "url"):
        out[f] = clean_line(str(r[f]) if r.get(f) is not None else None)
        if out[f] is None:
            return drop(f)
    if r.get("source") not in SOURCES:
        return drop("source")
    out["source"] = r["source"]
    out["price_gbp"], why = number(r.get("price_gbp"), "price_gbp")
    if why:
        return drop("price_gbp")
    out["fetched_at"] = iso_utc(r.get("fetched_at"))
    if out["fetched_at"] is None:
        return drop("fetched_at")

    def enum(field, table, unmapped=None):
        v, known = enum_value(table, r.get(field))
        if not known:
            ev.append("unknown_enum:%s:%s" % (field, r.get(field)))
            return unmapped
        if v is None and r.get(field) is not None and str(r[field]).strip():
            ev.append("nulled:%s:%s" % (field, str(r[field]).strip().lower()))
        return v

    out["price_qualifier"] = enum("price_qualifier", PRICE_QUALIFIER)
    out["property_type"] = enum("property_type", PROPERTY_TYPE, unmapped="other")
    out["tenure"] = enum("tenure", TENURE)
    out["council_tax_band"] = enum("council_tax_band", COUNCIL_TAX_BAND)
    out["epc_current"] = enum("epc_current", EPC_RATING)
    out["epc_potential"] = enum("epc_potential", EPC_RATING)

    def num(field, null_if=None, why_null=None):
        v = r.get(field)
        if v is None:
            return None
        if null_if is not None and null_if(v):
            ev.append("nulled:%s:%s" % (field, why_null))
            return None
        v, why = number(v, field)
        if why:
            ev.append("nulled:%s:%s" % (field, why))
        return v

    for f in ("bedrooms", "bathrooms", "lat", "lon", "service_charge_gbp_pa", "ground_rent_gbp_pa"):
        out[f] = num(f)
    out["lease_years_remaining"] = num("lease_years_remaining", lambda v: v == 0, "zero_means_none")

    for f in ("address", "postcode", "agent_name"):
        out[f] = clean_line(r.get(f))
    out["floor_level"] = clean_line(r.get("floor_level"))
    if out["floor_level"]:
        out["floor_level"] = out["floor_level"].lower()
    out["description"] = clean_text(r.get("description"))
    out["key_features"] = [k for k in (clean_line(x, strip_tags=True) for x in r.get("key_features") or [])
                           if k]
    out["listed_date"] = iso_utc(r.get("listed_date"))
    if r.get("listed_date") is not None and out["listed_date"] is None:
        ev.append("nulled:listed_date:not_a_date")
    out["parsed_fields"] = [p for p in r.get("parsed_fields") or [] if out.get(p) is not None]

    out["media"] = [
        {"kind": kind, "position": i, "url": u}
        for kind, urls in (("photo", r.get("photo_urls")), ("floorplan", r.get("floorplan_urls")),
                           ("epc", r.get("epc_image_urls")))
        for i, u in enumerate(u for u in urls or [] if isinstance(u, str) and u.strip())
    ]

    out["stations"] = []
    for s in r.get("nearest_stations") or []:
        name = clean_line(s.get("name"))
        if name is None:
            ev.append("station_dropped:no_name")
            continue
        km, sev = distance_km(s.get("distance"), s.get("unit"), out["source"])
        ev += sev
        out["stations"].append({
            "position": len(out["stations"]), "name": name, "distance_km": km,
            "types": [t for t in s.get("types") or [] if isinstance(t, str)],
        })
    return {c: out[c] for c in COLUMNS}, ev
