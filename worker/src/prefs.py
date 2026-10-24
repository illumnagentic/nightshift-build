"""Preference parsing: postcode normaliser, the parser request, and checks on what the model returns."""
import json
import re

MODEL = "gemini-3.8-flash"

POSTCODE_RE = re.compile(r"([A-Z]{1,2}[0-9][A-Z0-9]?)([0-9][A-Z]{2})")
PROPERTY_TYPES = ["flat", "maisonette", "house", "terraced", "semi_detached", "end_of_terrace", "detached", "bungalow", "other"]
EPC_RATINGS = ["A", "B", "C", "D", "E", "F", "G"]
TENURES = ["freehold", "leasehold", "share_of_freehold"]
MAX_SOFT_ITEMS, MAX_SOFT_CHARS = 10, 120

# One fixed string. The buyer's text goes only in the user message.
SYSTEM_PROMPT = """You turn a home buyer's free-text wishes into structured search limits for a UK for-sale property search.

Return JSON with two keys, "hard" and "soft".

"hard" holds limits the buyer states firmly. Words such as "must", "no", "under", "at least", "max" or "minimum" mark a firm limit. Every field is null when the buyer does not state it. Never guess.
- max_price_gbp: whole pounds, an integer. "550k" is 550000, "1.2m" is 1200000.
- min_bedrooms: whole number of bedrooms, 0 for a studio.
- property_types: list of the allowed types, from: flat, maisonette, house, terraced, semi_detached, end_of_terrace, detached, bungalow, other. Use "house" when the buyer says house without a more specific kind. null when no type is stated.
- min_epc: the worst acceptable energy rating, one of A, B, C, D, E, F, G. "EPC C or better" is "C".
- tenure: one of freehold, leasehold, share_of_freehold, or null.
- min_lease_years: minimum years left on the lease, an integer, or null.

"soft" is a list of the buyer's other wishes, each a short phrase of a few words, such as "near a tube station" or "bright rooms". A wish stated as a preference rather than a firm limit goes here. Do not repeat anything already in "hard". Use an empty list when there are none.

The buyer's commute is handled elsewhere. Ignore it."""

_NULLABLE_INT = {"type": "INTEGER", "nullable": True}
RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "hard": {
            "type": "OBJECT",
            "properties": {
                "max_price_gbp": _NULLABLE_INT,
                "min_bedrooms": _NULLABLE_INT,
                "property_types": {"type": "ARRAY", "nullable": True, "items": {"type": "STRING", "enum": PROPERTY_TYPES}},
                "min_epc": {"type": "STRING", "nullable": True, "enum": EPC_RATINGS},
                "tenure": {"type": "STRING", "nullable": True, "enum": TENURES},
                "min_lease_years": _NULLABLE_INT,
            },
            "required": ["max_price_gbp", "min_bedrooms", "property_types", "min_epc", "tenure", "min_lease_years"],
        },
        "soft": {"type": "ARRAY", "items": {"type": "STRING"}},
    },
    "required": ["hard", "soft"],
}


def normalise_postcode(raw: str) -> str | None:
    """'ec2n2db' -> 'EC2N 2DB'. None when it is not a full UK postcode."""
    match = POSTCODE_RE.fullmatch("".join(raw.split()).upper())
    return f"{match.group(1)} {match.group(2)}" if match else None


def build_parse_body(text: str) -> dict:
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


def _int_in(value, low: int, high: int) -> int | None:
    # bool is an int in Python; a JSON true is not a price.
    if isinstance(value, int) and not isinstance(value, bool) and low <= value <= high:
        return value
    return None


def _choice(value, allowed: list[str]) -> str | None:
    return value if isinstance(value, str) and value in allowed else None


def check_parsed(raw, max_commute_min: int | None) -> dict:
    """Keep only values that are valid; anything else becomes null. Never raises."""
    hard_in = raw.get("hard") if isinstance(raw, dict) else None
    hard_in = hard_in if isinstance(hard_in, dict) else {}
    types = hard_in.get("property_types")
    types = list(dict.fromkeys(t for t in types if isinstance(t, str) and t in PROPERTY_TYPES)) if isinstance(types, list) else []
    soft_in = raw.get("soft") if isinstance(raw, dict) else None
    soft = []
    if isinstance(soft_in, list):
        soft = [s.strip() for s in soft_in if isinstance(s, str) and s.strip()]
        soft = [s for s in soft if len(s) <= MAX_SOFT_CHARS][:MAX_SOFT_ITEMS]
    return {
        "hard": {
            "max_price_gbp": _int_in(hard_in.get("max_price_gbp"), 10_000, 50_000_000),
            "min_bedrooms": _int_in(hard_in.get("min_bedrooms"), 0, 10),
            "property_types": types or None,
            "min_epc": _choice(hard_in.get("min_epc"), EPC_RATINGS),
            "tenure": _choice(hard_in.get("tenure"), TENURES),
            "min_lease_years": _int_in(hard_in.get("min_lease_years"), 1, 999),
            "max_commute_min": max_commute_min,
        },
        "soft": soft,
    }


def reply_text(data: dict) -> str | None:
    """The model's JSON text from a generateContent answer, or None when it is missing."""
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        return None
    return text if isinstance(text, str) else None


def parse_reply(data: dict, max_commute_min: int | None) -> dict | None:
    """Checked parsed prefs from a generateContent answer; None when the reply is unusable."""
    text = reply_text(data)
    if text is None:
        return None
    try:
        raw = json.loads(text)
    except ValueError:
        return None
    return check_parsed(raw, max_commute_min) if isinstance(raw, dict) else None
