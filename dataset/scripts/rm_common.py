"""Shared helpers for the Rightmove fetch and normalise scripts.

Stdlib only. Parses pages that were already downloaded; never executes them.
"""
import gzip
import json
import os
import re
import ssl

USER_AGENT = (
    "NightshiftHackathonDataset/0.1 "
    "(one-off student hackathon dataset; about 1 request every 2.5 s; no login)"
)
BASE = "https://www.rightmove.co.uk"

# Listing rules shared by fetch (to avoid wasted requests) and normalise.
MIN_PRICE = 250_000
MAX_PRICE = 1_200_000
MIN_PHOTOS = 6
MIN_FLOORPLANS = 1


def ssl_context():
    """Verified TLS context. python.org builds on macOS ship without a CA
    bundle, so fall back to the system bundle rather than disabling checks."""
    ctx = ssl.create_default_context()
    if not ctx.get_ca_certs() and os.path.exists("/etc/ssl/cert.pem"):
        ctx.load_verify_locations("/etc/ssl/cert.pem")
    return ctx


def read_gz(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return f.read()


def search_json(html):
    """Return searchResults from a search page's __NEXT_DATA__, or None."""
    m = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S
    )
    if not m:
        return None
    return json.loads(m.group(1))["props"]["pageProps"].get("searchResults")


def page_model(html):
    """Decode window.__PAGE_MODEL on a property page into plain Python objects.

    The page stores a flat array where every object/array value is an index
    into that array (negative index = absent). Returns None if not present.
    """
    marker = "window.__PAGE_MODEL = "
    i = html.find(marker)
    if i < 0:
        return None
    outer, _ = json.JSONDecoder().raw_decode(html, i + len(marker))
    data = outer.get("data")
    if not isinstance(data, str):
        return outer  # older plain-JSON form
    arr = json.loads(data)
    cache = {}

    def res(idx):
        if not isinstance(idx, int) or idx < 0:
            return None
        if idx in cache:
            return cache[idx]
        v = arr[idx]
        if isinstance(v, dict):
            out = {}
            cache[idx] = out
            for k, x in v.items():
                out[k] = res(x)
            return out
        if isinstance(v, list):
            out = []
            cache[idx] = out
            out.extend(res(x) for x in v)
            return out
        return v

    return res(0)


def card_rejection(card):
    """Why a search-result card is dropped before its details are fetched.

    Returns None if the card is kept.
    """
    price = (card.get("price") or {}).get("amount")
    if card.get("auction"):
        return "auction"
    if card.get("channel") != "BUY" or card.get("commercial") or not card.get("residential", True):
        return "not_residential_sale"
    if price is None or price < MIN_PRICE or price > MAX_PRICE:
        return "price_out_of_range"
    if (card.get("numberOfImages") or 0) < MIN_PHOTOS:
        return "thin_photos"
    if (card.get("numberOfFloorplans") or 0) < MIN_FLOORPLANS:
        return "thin_no_floorplan"
    return None
