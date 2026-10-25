"""The curator: scores a chunk of listings for one buyer. Request body, compact listings, and checks on the reply."""
import json

import prefs

CHUNK_SIZE = 20
MODEL = prefs.MODEL
MAX_REASON_CHARS = 200
MAX_STATIONS = 3

# One fixed string. Everything about the buyer and the listings goes in the user message.
SYSTEM_PROMPT = """You score UK for-sale listings for one home buyer.

The user message is JSON with three keys.
- "stated": the buyer's own preferences. "hard" limits are already enforced in code, so every listing you see passes them. "soft" is a list of wishes.
- "profile": what we have learned about the buyer's taste, as factors with a direction and a weight. It may be empty.
- "listings": the listings to score. Photo flags describe what the photos show.

Score every listing from 0 to 100 for how well it suits this buyer. Weight each factor by its profile weight: a heavy factor decides the score, a light one barely moves it. Give each listing a short reason, one sentence, naming the deciding factors.

Never skip a listing. Return exactly one score for each listing id."""

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "scores": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "listing_id": {"type": "STRING"},
                    "score": {"type": "INTEGER"},
                    "reason": {"type": "STRING"},
                },
                "required": ["listing_id", "score", "reason"],
            },
        },
    },
    "required": ["scores"],
}

_LISTING_FIELDS = ["price_gbp", "price_qualifier", "bedrooms", "bathrooms", "property_type", "postcode", "tenure",
                   "lease_years_remaining", "service_charge_gbp_pa", "council_tax_band", "epc_current", "floor_level"]


def compact_listing(listing: dict, stations: list[dict], flags: list[dict], commute_minutes: int | None) -> dict:
    """Structured fields only, nulls dropped. No description, URLs, split or address."""
    features = listing.get("key_features")
    out = {"id": listing["id"], **{k: listing.get(k) for k in _LISTING_FIELDS},
           "key_features": json.loads(features) if isinstance(features, str) else features,
           "stations": [{"name": s["name"], "distance_km": s.get("distance_km")} for s in stations[:MAX_STATIONS]],
           "commute_minutes": commute_minutes,
           "flags": [{"field": f["field"], "value": f["value"], "room": f.get("room"), "confidence": f["confidence"],
                      "text": f["corrected_text"] if f.get("corrected_text") is not None else f["observation"]}
                     for f in flags]}
    out["flags"] = [{k: v for k, v in f.items() if v is not None} for f in out["flags"]]
    out["stations"] = [{k: v for k, v in s.items() if v is not None} for s in out["stations"]]
    return {k: v for k, v in out.items() if v is not None and v != [] or k == "id"}


def build_score_body(stated: dict, profile: dict, listings: list[dict]) -> dict:
    if len(listings) > CHUNK_SIZE:
        raise ValueError(f"at most {CHUNK_SIZE} listings per curator call, got {len(listings)}")
    text = json.dumps({"stated": stated, "profile": profile, "listings": listings}, separators=(",", ":"))
    return {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": text}]}],
        "generationConfig": {
            "temperature": 0,
            "thinkingConfig": {"thinkingLevel": "low"},
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA,
        },
    }


def parse_reply(data: dict, listing_ids: list[str]) -> dict[str, tuple[int, str | None]] | None:
    """{listing_id: (score, reason)} when every listing is scored exactly once; None when the reply is unusable."""
    text = prefs.reply_text(data)
    if text is None:
        return None
    try:
        raw = json.loads(text)
    except ValueError:
        return None
    items = raw.get("scores") if isinstance(raw, dict) else None
    if not isinstance(items, list):
        return None
    scores = {}
    for item in items:
        if not isinstance(item, dict):
            return None
        lid, score, reason = item.get("listing_id"), item.get("score"), item.get("reason")
        if not isinstance(lid, str) or lid in scores or prefs._int_in(score, 0, 100) is None or not isinstance(reason, str):
            return None
        scores[lid] = (score, reason.strip()[:MAX_REASON_CHARS].strip() or None)
    return scores if set(scores) == set(listing_ids) and len(listing_ids) == len(set(listing_ids)) else None
