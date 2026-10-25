"""The curator call: ranks a set of candidate listings for one buyer. Pure: builds the request and checks the reply."""
import json

from prefs import reply_text

MODEL = "gemini-3.8-flash"
FLOORPLAN_NOTES_CHARS = 160

# One fixed string. Everything about the buyer and the listings goes in the user message.
SYSTEM_PROMPT = """You rank UK for-sale properties for one home buyer, best match first.

The user message is compact JSON with these keys.
- stated_prefs: what the buyer wrote. "text" is their own words. "soft" is the list of wishes taken from it that are not firm limits. Firm limits are already applied, so every candidate meets them.
- taste_profile: what has been learned about the buyer from their reactions to earlier properties. It maps a factor to a direction (what the buyer leans towards on that factor) and a weight (how much that factor matters to them). A strong direction on a factor with a low weight should not decide a ranking. It is empty when nothing has been learned yet.
- recent_feedback: the buyer's latest comments on properties they have seen, newest last. Each entry names the property and says what they liked or disliked about it. It is empty when there is none yet.
- candidates: the properties to rank. Each has an "id" and structured facts: price_gbp, price_qualifier, bedrooms, bathrooms, property_type, tenure, lease_years_remaining, service_charge_gbp_pa, epc_current, floor_level, key_features, station (nearest station name and distance_km), commute_min (minutes door to door to the buyer's chosen destination, when known). A missing key means the fact is unknown, not zero.
  "photos" is a digest of what a vision model saw. "light" gives the light seen in each room (none, poor, ok or bright). "defects" lists faults seen, "size_tricks" lists things that make rooms look bigger than they are, and "missing" lists things expected in a room but not seen, each as "room: item". "sqm_estimate" is the floor area in square metres and "floorplan_notes" summarises the floor plan. The digest may be incomplete and the vision model can be wrong.

Rank by how well each candidate fits the buyer's stated_prefs, taste_profile and recent_feedback. When these say little, judge by what a typical buyer would want: value for the price, good light, no obvious defects, useful space and layout, a sensible commute and access to a station. Do not invent facts that are not in the candidate.

Return JSON with one key, "ranking": a list holding the "id" of every candidate exactly once, best first. Use the ids exactly as given. Add nothing else."""

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {"ranking": {"type": "ARRAY", "items": {"type": "STRING"}}},
    "required": ["ranking"],
}

GENERATION_CONFIG = {
    "temperature": 0,
    "thinkingConfig": {"thinkingLevel": "low"},
    "responseMimeType": "application/json",
    "responseSchema": RESPONSE_SCHEMA,
}

_LIGHT_ORDER = ["none", "poor", "ok", "bright"]


class CuratorError(Exception):
    """The reply cannot be used as a ranking."""


def _flag_value(flag):
    return flag["corrected_text"] if flag["corrected_text"] is not None else flag["value"]


def _flag_digest(flags) -> dict:
    light, corrected_light, lists, digest = {}, {}, {"defects": set(), "size_tricks": set(), "missing": set()}, {}
    sqm, notes = None, None
    for f in flags:
        field, value = f["field"], _flag_value(f)
        if field == "light":
            light.setdefault(f["room"], []).append(str(value))
            if f["corrected_text"] is not None:
                corrected_light.setdefault(f["room"], []).append(str(value))
        elif field in lists:
            lists[field].add(f"{f['room']}: {value}")
        elif field == "sqm_estimate":
            sqm = value
        elif field == "floorplan_notes":
            notes = str(value)[:FLOORPLAN_NOTES_CHARS]
    if light:
        # A user's correction wins its room, whatever the counts: the most frequent corrected value, then the
        # first in flag order. Without one, the most frequent reading; a tie goes to the worse reading.
        def pick(room, values):
            if room in corrected_light:
                fixed = corrected_light[room]
                return max(dict.fromkeys(fixed), key=fixed.count)
            return max(set(values), key=lambda v: (values.count(v), -(_LIGHT_ORDER.index(v) if v in _LIGHT_ORDER else -1), v))
        digest["light"] = {room: pick(room, values) for room, values in sorted(light.items())}
    for field, items in lists.items():
        if items:
            digest[field] = sorted(items)
    if sqm is not None:
        digest["sqm_estimate"] = sqm
    if notes is not None:
        digest["floorplan_notes"] = notes
    return digest


def candidate_summary(listing, flags, commute_minutes) -> dict:
    """The compact, ordered facts the curator sees for one listing. Absent facts are left out."""
    out = {"id": listing["id"]}
    for key in ("price_gbp", "price_qualifier", "bedrooms", "bathrooms", "property_type", "tenure",
                "lease_years_remaining", "service_charge_gbp_pa", "epc_current", "floor_level"):
        if listing[key] is not None:
            out[key] = listing[key]
    if listing["key_features"]:
        out["key_features"] = listing["key_features"]
    stations = [s for s in listing["stations"] if s["distance_km"] is not None]
    if stations:
        nearest = min(stations, key=lambda s: s["distance_km"])
        out["station"] = {"name": nearest["name"], "distance_km": nearest["distance_km"]}
    if commute_minutes is not None:
        out["commute_min"] = commute_minutes
    photos = _flag_digest(flags)
    if photos:
        out["photos"] = photos
    return out


def build_body(stated_prefs, profile, recent_feedback, candidates) -> dict:
    """The generateContent body. Only the user message differs between buyers."""
    message = {
        "stated_prefs": {"text": stated_prefs["text"], "soft": stated_prefs["soft"]},
        "taste_profile": profile,
        "recent_feedback": recent_feedback,
        "candidates": candidates,
    }
    return {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": json.dumps(message, separators=(",", ":"), ensure_ascii=False)}]}],
        "generationConfig": GENERATION_CONFIG,
    }


def _usage(data) -> dict | None:
    meta = data.get("usageMetadata") if isinstance(data, dict) else None
    if not isinstance(meta, dict):
        return None
    return {"prompt": meta.get("promptTokenCount"), "candidates": meta.get("candidatesTokenCount"),
            "thoughts": meta.get("thoughtsTokenCount")}


def parse_ranking(data, candidate_ids) -> tuple[list[str], str, dict | None]:
    """(ranking, status, usage). Unknown and repeated ids are dropped and missing candidates go last, status
    "incomplete". Raises CuratorError when the reply is unusable or fewer than half the candidates came back."""
    text = reply_text(data) if isinstance(data, dict) else None
    if text is None:
        raise CuratorError("no reply text")
    try:
        raw = json.loads(text)
    except ValueError:
        raise CuratorError("reply is not JSON") from None
    items = raw.get("ranking") if isinstance(raw, dict) else None
    if not isinstance(items, list):
        raise CuratorError("reply has no ranking list")
    known = set(candidate_ids)
    valid = [i for i in dict.fromkeys(i for i in items if isinstance(i, str)) if i in known]
    if len(valid) * 2 < len(candidate_ids):
        raise CuratorError(f"only {len(valid)} of {len(candidate_ids)} candidates came back")
    missing = [i for i in candidate_ids if i not in set(valid)]
    repaired = bool(missing) or len(items) != len(valid)
    return valid + missing, "incomplete" if repaired else "ok", _usage(data)
