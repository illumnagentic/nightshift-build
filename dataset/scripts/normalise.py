"""Build listings.jsonl and listings.csv from raw/.

Reads only files already on disk. Makes no network requests.

Usage (from the dataset/ directory):
  python3 -I scripts/normalise.py --dataset .            rebuild from all of raw/
  python3 -I scripts/normalise.py --dataset . --append   add raw/rapidapi records to listings.jsonl

A rebuild refuses to write fewer listings than listings.jsonl already holds.
"""
import argparse
import collections
import contextlib
import csv
import glob
import io
import json
import os
import re
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rm_common as rm  # noqa: E402
from sanitise import COLUMNS, sanitise_record, strip_html  # noqa: E402

FIELDS = [
    "id", "source", "source_id", "url", "price_gbp", "price_qualifier", "bedrooms", "bathrooms",
    "property_type", "address", "postcode", "lat", "lon", "tenure", "lease_years_remaining",
    "service_charge_gbp_pa", "ground_rent_gbp_pa", "council_tax_band", "epc_current",
    "epc_potential", "epc_image_urls", "floor_level", "key_features", "description",
    "photo_urls", "floorplan_urls", "nearest_stations", "agent_name", "listed_date",
    "fetched_at", "parsed_fields",
]
LIST_FIELDS = {"key_features", "parsed_fields", "media", "stations"}
MAX_PHOTOS = 10

TENURE_MAP = {
    "FREEHOLD": "freehold", "LEASEHOLD": "leasehold", "SHARE_OF_FREEHOLD": "share_of_freehold",
    "COMMONHOLD": "commonhold", "FEUDAL": "feudal",
}


# ---- text parsers. Each returns a value or None; callers record provenance. ----

EPC_RE = re.compile(
    r"\b(?:EPC|energy\s+(?:performance\s+)?(?:certificate|rating|efficiency\s+rating))"
    r"(?:\s*(?:rating|band|grade|score))?\s*(?:of|is|are|:|-|–|=)?\s*([A-Ga-g])(?:\d{1,3})?\b(?!\s*\+)",
    re.I,
)
EPC_POT_RE = re.compile(r"\bpotential(?:\s+(?:EPC|rating|band))*\s*(?:of|:|-|–|=)?\s*([A-G])(?:\d{1,3})?\b")


# "energy efficiency rating of 83, classified as Band B"
EPC_SCORE_RE = re.compile(
    r"\benergy\s+efficiency\s+rating\s+of\s+\d{1,3},?\s+(?:classified\s+as\s+|in\s+)?band\s+([A-G])\b", re.I)


def parse_epc(text):
    cur = pot = None
    m = EPC_SCORE_RE.search(text)
    if m and m.group(1).isupper():
        return m.group(1), None
    for m in EPC_RE.finditer(text):
        letter = m.group(1)
        if letter.isupper():  # lower-case single letters are usually words ("a", "e")
            cur = letter
            tail = text[m.end(): m.end() + 40]
            p = EPC_POT_RE.search(tail)
            if p:
                pot = p.group(1)
            break
    return cur, pot


LEASE_RE = re.compile(
    r"(\d{2,3})\s*(?:\+\s*)?(?:years?|yrs?)\s*(?:\(?approx(?:imately)?\.?\)?\s*)?"
    r"(?:remaining|left|unexpired|remain)\b",
    re.I,
)
LEASE_RE2 = re.compile(
    r"(?:remaining|unexpired)\s+(?:lease|term)\s*(?:of|:|-)?\s*(?:approx(?:imately)?\.?\s*)?(\d{2,3})\s*(?:years?|yrs?)",
    re.I,
)


def parse_lease(text):
    for rx in (LEASE_RE, LEASE_RE2):
        m = rx.search(text)
        if m:
            n = int(m.group(1))
            if 1 <= n <= 999:
                return n
    return None


TENURE_TEXT = [
    (re.compile(r"\bshare\s+of\s+(?:the\s+)?freehold\b", re.I), "share_of_freehold"),
    (re.compile(r"\bleasehold\b", re.I), "leasehold"),
    (re.compile(r"\bfreehold\b", re.I), "freehold"),
]


def parse_tenure(text):
    for rx, val in TENURE_TEXT:
        if rx.search(text):
            return val
    return None


CTAX_RE = re.compile(r"\bcouncil\s+tax(?:\s+band)?\s*(?::|-|–|=|is)?\s*(?:band\s*)?([A-H])\b", re.I)


def parse_ctax(text):
    m = CTAX_RE.search(text)
    if m and m.group(1).isupper():
        return m.group(1)
    return None


ANNUAL = r"(?:p\.?\s?a\.?|per\s+annum|per\s+year|a\s+year|annually|/\s?(?:annum|year|yr))"


def money_re(label):
    return re.compile(
        label + r"[^£\n]{0,40}?£\s?([\d,]+(?:\.\d{1,2})?)\s*" + ANNUAL, re.I
    )


SC_RE = money_re(r"\bservice\s+charges?")
GR_RE = money_re(r"\bground\s+rent")


def parse_money(rx, text):
    m = rx.search(text)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:
        return None


ORDINALS = ("lower ground|raised ground|upper ground|ground|first|second|third|fourth|fifth|sixth|"
            "seventh|eighth|ninth|tenth|eleventh|twelfth|top|penthouse|\\d{1,2}(?:st|nd|rd|th)")
FLOOR_RE = re.compile(
    r"\b(" + ORDINALS + r")[\s-]+floor\s+(?:flat|apartment|maisonette|studio|purpose[\s-]built|conversion)",
    re.I,
)
FLOOR_RE2 = re.compile(r"\b(?:on|situated on|located on|positioned on|set on)\s+the\s+(" + ORDINALS + r")[\s-]+floor\b", re.I)


def parse_floor(text):
    for rx in (FLOOR_RE, FLOOR_RE2):
        m = rx.search(text)
        if m:
            return m.group(1).lower()
    return None


def entrance_floor(v):
    """Rightmove's structured entranceFloor, e.g. {'displayText': '1st floor'} -> '1st'."""
    if isinstance(v, dict):
        v = v.get("displayText") or v.get("alias")
    if not v or not isinstance(v, str):
        return None
    return re.sub(r"[\s_-]*floor$", "", v.strip().lower()).replace("_", " ") or None


# ---- building one record ----

def load_cards(raw_dir, stats):
    """All search-result cards, keyed by id (first seen wins)."""
    cards = {}
    for path in sorted(glob.glob(os.path.join(raw_dir, "search", "*.html.gz"))):
        sr = rm.search_json(rm.read_gz(path)) or {}
        for c in sr.get("properties") or []:
            stats["cards_seen"] += 1
            if c["id"] in cards:
                stats["cards_duplicate_across_searches"] += 1
                continue
            cards[c["id"]] = c
            why = rm.card_rejection(c)
            stats["card_drop_" + why if why else "cards_kept"] += 1
    return cards


def load_manifest(raw_dir):
    out = {}
    p = os.path.join(raw_dir, "_manifest.jsonl")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            r = json.loads(line)
            if r.get("status") == 200:
                out[r["path"]] = r["fetched_at"]
    return out


def detail_rejection(pd):
    if (pd.get("transactionType") or "").upper() != "BUY":
        return "not_for_sale"
    st = pd.get("status") or {}
    if st.get("archived") or st.get("published") is False:
        return "archived_or_unpublished"
    so = pd.get("sharedOwnership") or {}
    if so.get("sharedOwnershipFlag"):
        return "shared_ownership"
    tags = " ".join(str(t) for t in (pd.get("tags") or [])).lower()
    if "auction" in tags or "retirement" in tags:
        return "auction_or_retirement"
    return None


def build(pd, card, fetched_at):
    parsed = []
    text_desc = strip_html((pd.get("text") or {}).get("description"))
    kf = [k for k in (pd.get("keyFeatures") or []) if isinstance(k, str)]
    text_all = "\n".join(kf) + "\n" + text_desc

    pid = pd["id"]
    addr = pd.get("address") or {}
    outcode, incode = addr.get("outcode"), addr.get("incode")
    loc = pd.get("location") or {}
    tenure_obj = pd.get("tenure") or {}
    lc = pd.get("livingCosts") or {}

    price = ((card or {}).get("price") or {}).get("amount")
    if price is None:
        digits = re.sub(r"[^\d]", "", (pd.get("prices") or {}).get("primaryPrice") or "")
        price = int(digits) if digits else None

    tenure = TENURE_MAP.get((tenure_obj.get("tenureType") or "").upper())
    if tenure is None:
        tenure = parse_tenure(text_all)
        if tenure:
            parsed.append("tenure")

    lease = tenure_obj.get("yearsRemainingOnLease")
    if lease == 0:  # Rightmove fills 0 when no lease applies (mostly freeholds)
        lease = None
    if lease is None and tenure in ("leasehold", "share_of_freehold"):
        lease = parse_lease(text_all)
        if lease is not None:
            parsed.append("lease_years_remaining")

    sc = lc.get("annualServiceCharge")
    if sc is None:
        sc = parse_money(SC_RE, text_all)
        if sc is not None:
            parsed.append("service_charge_gbp_pa")
    gr = lc.get("annualGroundRent")
    if gr is None:
        gr = parse_money(GR_RE, text_all)
        if gr is not None:
            parsed.append("ground_rent_gbp_pa")

    ctax = lc.get("councilTaxBand")
    if not ctax:
        ctax = parse_ctax(text_all)
        if ctax:
            parsed.append("council_tax_band")

    epc_cur, epc_pot = parse_epc(text_all)
    if epc_cur:
        parsed.append("epc_current")
    if epc_pot:
        parsed.append("epc_potential")

    floor = entrance_floor(pd.get("entranceFloor"))
    if floor is None:
        floor = parse_floor(text_all)
        if floor:
            parsed.append("floor_level")

    photos = [i.get("url") for i in (pd.get("images") or []) if i.get("url")]
    plans = [f.get("url") for f in (pd.get("floorplans") or []) if f.get("url")]
    epcs = [e.get("url") for e in (pd.get("epcGraphs") or []) if e.get("url")]
    stations = [
        {"name": s.get("name"), "distance": round(s["distance"], 2) if s.get("distance") is not None else None,
         "unit": s.get("unit"), "types": s.get("types") or []}
        for s in (pd.get("nearestStations") or [])
    ]
    cust = pd.get("customer") or {}
    listed = (card or {}).get("firstVisibleDate")

    return {
        "id": "rm-%s" % pid,
        "source": "rightmove",
        "source_id": str(pid),
        "url": "%s/properties/%s" % (rm.BASE, pid),
        "price_gbp": price,
        "price_qualifier": (pd.get("prices") or {}).get("displayPriceQualifier") or None,
        "bedrooms": pd.get("bedrooms"),
        "bathrooms": pd.get("bathrooms"),
        "property_type": pd.get("propertySubType") or None,
        "address": addr.get("displayAddress"),
        "postcode": ("%s %s" % (outcode, incode)) if outcode and incode else (outcode or None),
        "lat": loc.get("latitude"),
        "lon": loc.get("longitude"),
        "tenure": tenure,
        "lease_years_remaining": lease,
        "service_charge_gbp_pa": sc,
        "ground_rent_gbp_pa": gr,
        "council_tax_band": ctax,
        "epc_current": epc_cur,
        "epc_potential": epc_pot,
        "epc_image_urls": epcs,
        "floor_level": floor,
        "key_features": kf,
        "description": text_desc or None,
        "photo_urls": photos[:MAX_PHOTOS],
        "floorplan_urls": plans,
        "nearest_stations": stations,
        "agent_name": cust.get("branchDisplayName") or cust.get("companyName"),
        "listed_date": listed,
        "fetched_at": fetched_at,
        "parsed_fields": parsed,
        # internal, removed before output
        "_photo_count": len(photos),
        "_delivery_point": addr.get("deliveryPointId"),
    }


# ---- RapidAPI (uk-real-estate-rightmove, the Rightmove app API) ----

def per_year(s):
    """'£1,500 per year' -> 1500.0. Anything not stated as yearly -> None."""
    if not s or not re.search(r"per\s+(?:year|annum)", s, re.I):
        return None
    m = re.search(r"£\s?([\d,]+(?:\.\d{1,2})?)", s)
    return float(m.group(1).replace(",", "")) if m else None


def rapid_rejection(d):
    if (d.get("transactionType") or "").upper() != "BUY":
        return "not_for_sale"
    if (d.get("status") or {}).get("available") is False:
        return "archived_or_unpublished"
    if (d.get("analyticsInfo") or {}).get("sharedOwnership") == "T" or \
            (d.get("salesInfo") or {}).get("sharedOwnershipPercentage"):
        return "shared_ownership"
    tags = " ".join(str(t) for t in (d.get("tags") or [])).lower()
    if "auction" in tags or "retirement" in tags:
        return "auction_or_retirement"
    return None


def build_rapid(d, card, fetched_at):
    parsed = []
    desc = strip_html(d.get("fullDescription"))
    kf = [k for k in (d.get("keyFeatures") or []) if isinstance(k, str)]
    text_all = "\n".join(kf) + "\n" + desc
    ai = d.get("analyticsInfo") or {}
    si = d.get("salesInfo") or {}
    loc = d.get("location") or {}
    pid = d["identifier"]

    price = ((card or {}).get("price") or {}).get("amount")
    if price is None and ai.get("price", "").isdigit():
        price = int(ai["price"])

    tenure = TENURE_MAP.get((si.get("tenureType") or "").upper())
    if tenure is None:
        tenure = parse_tenure(text_all)
        if tenure:
            parsed.append("tenure")
    lease = None
    m = re.search(r"(\d{1,3})\s+years?\s+left", si.get("lengthOfLease") or "")
    if m:
        lease = int(m.group(1))
    elif tenure in ("leasehold", "share_of_freehold"):
        lease = parse_lease(text_all)
        if lease is not None:
            parsed.append("lease_years_remaining")
    sc = per_year(si.get("annualServiceCharge"))
    if sc is None:
        sc = parse_money(SC_RE, text_all)
        if sc is not None:
            parsed.append("service_charge_gbp_pa")
    gr = per_year(si.get("groundRent"))
    if gr is None:
        gr = parse_money(GR_RE, text_all)
        if gr is not None:
            parsed.append("ground_rent_gbp_pa")
    lpt = d.get("localPropertyTax") or {}
    ctax = lpt.get("value") if lpt.get("type") == "COUNCIL_TAX" and lpt.get("value") else None
    if ctax and not re.fullmatch(r"[A-I]", ctax):
        ctax = None
    if not ctax:
        ctax = parse_ctax(text_all)
        if ctax:
            parsed.append("council_tax_band")
    epc_cur, epc_pot = parse_epc(text_all)
    if epc_cur:
        parsed.append("epc_current")
    if epc_pot:
        parsed.append("epc_potential")
    floor = parse_floor(text_all)
    if floor:
        parsed.append("floor_level")

    photos = [p.get("maxSizeUrl") or p.get("url") for p in (d.get("photos") or [])]
    photos = [p for p in photos if p]
    listed = (card or {}).get("firstVisibleDate")
    if not listed and re.fullmatch(r"\d{8}", ai.get("added") or ""):
        a = ai["added"]
        listed = "%s-%s-%s" % (a[:4], a[4:6], a[6:])

    return {
        "id": "rm-%s" % pid, "source": "rapidapi_uk_real_estate_rightmove", "source_id": str(pid),
        "url": d.get("propertyUrl") or "%s/properties/%s" % (rm.BASE, pid),
        "price_gbp": price, "price_qualifier": (d.get("price") or {}).get("secondary") or None,
        "bedrooms": d.get("bedrooms"), "bathrooms": d.get("bathrooms"),
        "property_type": ai.get("propertySubType") or d.get("propertyDisplayType"),
        "address": d.get("address"), "postcode": d.get("postcode") or ai.get("postcode"),
        "lat": loc.get("latitude"), "lon": loc.get("longitude"),
        "tenure": tenure, "lease_years_remaining": lease,
        "service_charge_gbp_pa": sc, "ground_rent_gbp_pa": gr, "council_tax_band": ctax,
        "epc_current": epc_cur, "epc_potential": epc_pot,
        "epc_image_urls": [e.get("url") for e in (d.get("epcs") or []) if e.get("url")],
        "floor_level": floor, "key_features": kf, "description": desc or None,
        "photo_urls": photos[:MAX_PHOTOS],
        "floorplan_urls": [f.get("url") for f in (d.get("floorplans") or []) if f.get("url")],
        # this API gives no distance unit; sanitise reads a missing unit as miles
        "nearest_stations": [{"name": s.get("station"), "distance": s.get("distance"), "unit": None,
                              "types": []} for s in (d.get("stations") or [])],
        "agent_name": (d.get("branch") or {}).get("displayName"),
        "listed_date": listed, "fetched_at": fetched_at, "parsed_fields": parsed,
        "_photo_count": len(photos), "_delivery_point": None,
    }


def load_rapid(ds, stats):
    raw = os.path.join(ds, "raw", "rapidapi")
    cards, fetched, out = {}, {}, []
    for path in sorted(glob.glob(os.path.join(raw, "search", "*.json"))):
        for c in (json.load(open(path, encoding="utf-8")).get("data") or []):
            stats["rapid_cards_seen"] += 1
            cards.setdefault(c["id"], c)
    log = os.path.join(raw, "_calls.log")
    if os.path.exists(log):
        for line in open(log, encoding="utf-8"):
            r = json.loads(line)
            if r.get("status") == 200 and r.get("path"):
                fetched[r["path"]] = r["ts"]
    for path in sorted(glob.glob(os.path.join(raw, "detail", "*.json"))):
        stats["rapid_detail_files"] += 1
        d = json.load(open(path, encoding="utf-8")).get("data") or {}
        card = cards.get(d.get("identifier"))
        if card is not None and rm.card_rejection(card):
            stats["rapid_dropped_card_rule"] += 1
            continue
        why = rapid_rejection(d)
        if why:
            stats["rapid_dropped_" + why] += 1
            continue
        r = build_rapid(d, card, fetched.get("raw/rapidapi/detail/" + os.path.basename(path)))
        why = thin_reason(r)
        if why:
            stats["rapid_dropped_" + why] += 1
            continue
        out.append(r)
    return out


def richness(r):
    return sum(1 for f in FIELDS if r.get(f) not in (None, [], "")) + min(r["_photo_count"], 20) / 100


def dup_keys(r):
    """The keys under which two records are the same home. Existing records read from
    listings.jsonl carry no delivery point, so that key is simply absent for them."""
    keys = [("id", r["id"]),
            ("geo", round(r["lat"] or 0, 4), round(r["lon"] or 0, 4), r["bedrooms"], r["price_gbp"])]
    if r.get("_delivery_point"):
        keys.append(("dp", r["_delivery_point"]))
    return keys


def dedupe(records, stats):
    """One record per property. Records are linked if they share a Rightmove id,
    a Royal Mail delivery point id, or the same rounded lat/lon + beds + price.
    The richest record in each linked group is kept."""
    parent = list(range(len(records)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    seen = {}
    for i, r in enumerate(records):
        for k in dup_keys(r):
            if k in seen:
                other = records[seen[k]]
                # One agent listing two units in a new-build shares a placeholder
                # delivery point and often the same geo/price; those are distinct homes.
                if k[0] != "id" and r["agent_name"] and r["agent_name"] == other["agent_name"]:
                    continue
                parent[find(i)] = find(seen[k])
            else:
                seen[k] = i
    groups = {}
    for i, r in enumerate(records):
        groups.setdefault(find(i), []).append(r)
    out = []
    for g in groups.values():
        g.sort(key=richness, reverse=True)
        out.append(g[0])
        stats["dropped_duplicate_property"] += len(g) - 1
    return out


def thin_reason(r):
    if r["_photo_count"] < rm.MIN_PHOTOS:
        return "thin_photos"
    if len(r["floorplan_urls"]) < rm.MIN_FLOORPLANS:
        return "thin_no_floorplan"
    if r["tenure"] is None:
        return "thin_no_tenure"
    if r["price_gbp"] is None or not (rm.MIN_PRICE <= r["price_gbp"] <= rm.MAX_PRICE):
        return "price_out_of_range"
    if r["lat"] is None or r["lon"] is None:
        return "no_location"
    return None


def photo_urls_of(r):
    """Photo URLs of a built record, or of a clean one (whose photos sit in media)."""
    if "photo_urls" in r:
        return r["photo_urls"]
    return [m["url"] for m in r["media"] if m["kind"] == "photo"]


def load_existing(ds):
    """Clean records already in listings.jsonl, in file order. Each line must survive a
    parse and dump unchanged, otherwise rewriting the file would alter existing records."""
    out = []
    path = os.path.join(ds, "listings.jsonl")
    if not os.path.exists(path):
        return out
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        r = json.loads(line)
        if json.dumps(r, ensure_ascii=False) + "\n" != line:
            raise SystemExit("listings.jsonl line %d would change on rewrite; refusing" % n)
        r["_photo_count"] = len(photo_urls_of(r))
        out.append(r)
    return out


def check_not_shrinking(ds, n_new):
    """Refuse to replace listings.jsonl with fewer listings than it holds."""
    path = os.path.join(ds, "listings.jsonl")
    if os.path.exists(path):
        n_old = sum(1 for _ in open(path, encoding="utf-8"))
        if n_new < n_old:
            raise SystemExit("refusing to write %d listings over the %d already in listings.jsonl; "
                             "use --append to add to them" % (n_new, n_old))


def drop_clashes(existing, new, stats):
    """The new records that are not a home already seen. Existing records always win;
    among new records the richest is kept. A shared photo URL means the same home. Every
    other rule is waived for two records from the same agent, as in dedupe()."""
    seen = {}

    def keys(r):
        return dup_keys(r) + [("photo", u) for u in photo_urls_of(r)]

    def register(r):
        for k in keys(r):
            seen.setdefault(k, r)

    def clash(r):
        for k in sorted(keys(r), key=lambda k: ["id", "dp", "geo", "photo"].index(k[0])):
            other = seen.get(k)
            if other is None:
                continue
            if k[0] in ("geo", "dp") and r["agent_name"] and r["agent_name"] == other["agent_name"]:
                continue
            return k[0]
        return None

    for r in existing:
        register(r)
    kept = []
    for r in sorted(new, key=lambda r: (-richness(r), r["id"])):
        rule = clash(r)
        if rule:
            stats["append_dropped_duplicate_" + rule] += 1
        else:
            register(r)
            kept.append(r)
    return kept


def write_outputs(ds, records):
    with open(os.path.join(ds, "listings.jsonl"), "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps({k: r[k] for k in COLUMNS}, ensure_ascii=False) + "\n")
    with open(os.path.join(ds, "listings.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLUMNS)
        for r in records:
            w.writerow([json.dumps(r[k], ensure_ascii=False) if k in LIST_FIELDS
                        else ("" if r[k] is None else r[k]) for k in COLUMNS])


def postcode_areas(records):
    return collections.Counter(re.match(r"[A-Z]+", r["postcode"]).group(0) if r["postcode"] else "?"
                               for r in records)


def pct(n, d):
    return "%d (%.0f%%)" % (n, 100.0 * n / d) if d else "0"


def report(records, stats, events, n_in):
    n = len(records)
    print("\n== pipeline counts ==")
    for k in sorted(stats):
        print("  %-40s %d" % (k, stats[k]))
    print("\n== sanitise ==")
    print("  records in: %d  kept: %d  dropped: %d" % (n_in, n, n_in - n))
    for k in sorted(events):
        print("  %-60s %d" % (k, events[k]))
    print("\n== final listings: %d ==" % n)
    print("  by source: " + ", ".join("%s %d" % kv for kv in collections.Counter(r["source"] for r in records).most_common()))
    cov = [
        ("epc_current (any)", lambda r: r["epc_current"]),
        ("epc_potential", lambda r: r["epc_potential"]),
        ("epc image url", lambda r: any(m["kind"] == "epc" for m in r["media"])),
        ("floorplan", lambda r: any(m["kind"] == "floorplan" for m in r["media"])),
        ("tenure", lambda r: r["tenure"]),
        ("tenure from text", lambda r: "tenure" in r["parsed_fields"]),
        ("lease years (of leasehold/SoF)", None),
        ("service charge (of leasehold/SoF)", None),
        ("ground rent (of leasehold/SoF)", None),
        ("council tax band", lambda r: r["council_tax_band"]),
        ("floor level", lambda r: r["floor_level"]),
        (">=6 photos", lambda r: r["_photo_count"] >= 6),
        (">=10 photos", lambda r: r["_photo_count"] >= 10),
        ("lat/lon", lambda r: r["lat"] is not None and r["lon"] is not None),
        ("full postcode", lambda r: r["postcode"] and " " in r["postcode"]),
        ("nearest stations", lambda r: r["stations"]),
        ("listed_date", lambda r: r["listed_date"]),
    ]
    lease_pool = [r for r in records if r["tenure"] in ("leasehold", "share_of_freehold")]
    print("== coverage ==")
    for name, fn in cov:
        if fn is None:
            field = {"lease": "lease_years_remaining", "servi": "service_charge_gbp_pa",
                     "groun": "ground_rent_gbp_pa"}[name[:5]]
            c = sum(1 for r in lease_pool if r[field] is not None)
            cp = sum(1 for r in lease_pool if field in r["parsed_fields"])
            print("  %-36s %s of %d; from text: %d" % (name, pct(c, len(lease_pool)), len(lease_pool), cp))
        else:
            print("  %-36s %s" % (name, pct(sum(1 for r in records if fn(r)), n)))
    epc_text = sum(1 for r in records if "epc_current" in r["parsed_fields"])
    print("  (all epc_current values are text-derived: %d)" % epc_text)
    prices = sorted(r["price_gbp"] for r in records)
    if prices:
        print("\n== price ==\n  min %d  median %d  max %d" % (prices[0], statistics.median(prices), prices[-1]))
        bands = [(250_000, 400_000), (400_000, 550_000), (550_000, 700_000), (700_000, 900_000), (900_000, 1_200_001)]
        for lo, hi in bands:
            print("  £%dk-£%dk: %d" % (lo // 1000, hi // 1000, sum(1 for p in prices if lo <= p < hi)))
    print("== bedrooms ==")
    for k, v in sorted(collections.Counter(r["bedrooms"] for r in records).items(), key=lambda x: (x[0] is None, x[0])):
        print("  %s: %d" % (k, v))
    print("== property type ==")
    for k, v in collections.Counter(r["property_type"] for r in records).most_common():
        print("  %s: %d" % (k, v))
    print("== tenure ==")
    for k, v in collections.Counter(r["tenure"] for r in records).most_common():
        print("  %s: %d" % (k, v))
    print("== postcode area ==")
    print("  " + ", ".join("%s %d" % kv for kv in postcode_areas(records).most_common()))


def build_from_raw(ds, stats):
    """Every record that raw/rightmove and raw/rapidapi give, before dedupe."""
    raw = os.path.join(ds, "raw", "rightmove")
    cards = load_cards(raw, stats)
    fetched = load_manifest(raw)
    records = []
    for path in sorted(glob.glob(os.path.join(raw, "property", "*.html.gz"))):
        stats["detail_pages"] += 1
        pid = int(os.path.basename(path).split(".")[0])
        card = cards.get(pid)
        if card is not None and rm.card_rejection(card):
            stats["detail_skipped_card_rule"] += 1  # fetched under an older rule
            continue
        pd = (rm.page_model(rm.read_gz(path)) or {}).get("propertyData")
        if not pd:
            stats["detail_unparseable"] += 1
            continue
        why = detail_rejection(pd)
        if why:
            stats["dropped_" + why] += 1
            continue
        rel = "raw/rightmove/property/%d.html.gz" % pid
        r = build(pd, card, fetched.get(rel))
        why = thin_reason(r)
        if why:
            stats["dropped_" + why] += 1
            continue
        records.append(r)
    records.extend(load_rapid(ds, stats))
    return records


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True, help="dataset/ directory")
    ap.add_argument("--append", action="store_true",
                    help="keep listings.jsonl as it is and add new records from raw/rapidapi")
    a = ap.parse_args()
    ds = a.dataset
    stats = collections.Counter()
    events = collections.Counter()
    existing = []
    if a.append:
        existing = load_existing(ds)
        built = load_rapid(ds, stats)
        stats["append_new_built"] = len(built)
        records = drop_clashes(existing, built, stats)
    else:
        records = build_from_raw(ds, stats)
        records = dedupe(records, stats)
    records.sort(key=lambda r: r["id"])
    clean = []
    for r in records:
        c, ev = sanitise_record(r)
        events.update(ev)
        if c is not None:
            c["_photo_count"] = r["_photo_count"]
            clean.append(c)
    final = existing + clean
    check_not_shrinking(ds, len(final))
    write_outputs(ds, final)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        if a.append:
            print("== append ==")
            print("  existing listings kept unchanged: %d" % len(existing))
            print("  new records built from raw/rapidapi: %d" % stats["append_new_built"])
            print("  new records dropped before building (rejection and thin rules): %d" % sum(
                v for k, v in stats.items() if k.startswith("rapid_dropped_")))
            for k in ("id", "dp", "geo", "photo"):
                print("  new records dropped, duplicate by %s: %d" % (k, stats["append_dropped_duplicate_" + k]))
            print("  new records dropped by sanitise: %d" % (len(records) - len(clean)))
            print("  new records added: %d" % len(clean))
            print("  new by postcode area: " + ", ".join(
                "%s %d" % kv for kv in postcode_areas(clean).most_common()))
        report(final, stats, events, len(existing) + len(records))
    sys.stdout.write(buf.getvalue())
    os.makedirs(os.path.join(ds, "reports"), exist_ok=True)
    with open(os.path.join(ds, "reports", "normalise-report.txt"), "w", encoding="utf-8") as f:
        f.write(buf.getvalue())


if __name__ == "__main__":
    main()
