"""The taste profile: one stored snapshot per version, so a version number always maps to what it held."""
import json
import re

from chips import CATALOGUE
from deck import _all, _now

STRENGTH_WORDS = {"must_have": "must have", "nice_to_have": "nice to have", "would_prefer_not": "would prefer not",
                  "deal_breaker": "deal-breaker"}
MAX_DIRECTION_ANSWERS = 3
FREE_TEXT_DIRECTION = "mentioned in comments"

# Buyer words that show a factor in free text (or a favourite-removal reason). One regex per catalogue factor.
# A match moves a weight only; it never adds a factor.
TERMS = {factor: re.compile(pattern, re.IGNORECASE) for factor, pattern in {
    "garden": r"\bgardens?\b",
    "parking": r"\b(parking|garage|driveway|car ?port|car ?park)\b",
    "natural_light": r"\b(natural light|daylight|sunlight|sunny|bright|dark|gloomy)\b",
    "balcony_terrace": r"\b(balcon(y|ies)|terrace)\b",
    "price_value": r"\b(price[sd]?|overpriced|value|budget|expensive|cheap|afford\w*)\b",
    "commute": r"\b(commute|commuting)\b",
    "station_access": r"\b(station|tube|underground|dlr|overground)\b",
    "area_busyness": r"\b(quiet|noisy|noise|busy|lively|peaceful|traffic)\b",
    "space": r"\b(spacious|cramped|roomy|tiny|room sizes?|plenty of room|enough space)\b",
    "kitchen": r"\bkitchens?\b",
    "layout": r"\b(layout|open[- ]plan)\b",
    "condition": r"\b(condition|dated|renovat\w*|refurb\w*|decor|modernis\w*)\b",
    "bathrooms": r"\b(bathrooms?|en[- ]?suite|shower room|wet room)\b",
    "floor_level": r"\b(ground floor|top floor|upper floor|stairs|floor level)\b",
    "building_amenities": r"\b(concierge|porter|gym|communal|lifts?)\b",
    "lease": r"\b(lease|leasehold|freehold)\b",
    "service_charge": r"\b(service charges?|ground rent)\b",
    "energy_efficiency": r"\b(epc|energy rating|energy efficien\w*|insulation|heating bills?)\b",
    "home_office": r"\b(home office|study|work(ing)? from home|wfh)\b",
    "building_style": r"\b(period|victorian|georgian|edwardian|character|new[- ]build)\b",
}.items()}


def compute_factors(rows) -> list:
    """The profile factors from feedback, as a pure function. Each row is one swiped decision's feedback:
    {offered: chip ids, chips: answers, free_text, skipped, updated_at}. A favourite-removal reason is a row with
    its reason as free_text and no chips. Skipped rows count nowhere, so a skip never lowers a weight.

    weight = chosen / (offered + mentioned_only + 1): offered is the chip being on the card, mentioned_only is a term
    match in the text without the chip, chosen is the chip answered or a term match. Factors with no choice are left out."""
    rows = sorted((r for r in rows if not r["skipped"]), key=lambda r: r["updated_at"], reverse=True)
    factors = []
    for factor, *_ in CATALOGUE:
        offered = mentioned_only = chosen = 0
        answers = []
        for row in rows:
            matched = bool(row["free_text"]) and TERMS[factor].search(row["free_text"]) is not None
            answer = next((c for c in row["chips"] if c["chip_id"] == factor), None)
            if factor in row["offered"]:
                offered += 1
            elif matched:
                mentioned_only += 1
            chosen += answer is not None or matched
            if answer is not None:
                answers.append(answer)
        if chosen:
            direction = "; ".join(
                f'{STRENGTH_WORDS[a["strength"]]} "{a["text"]}"' if a["text"] else f'{STRENGTH_WORDS[a["strength"]]} (no comment)'
                for a in answers[:MAX_DIRECTION_ANSWERS]) or FREE_TEXT_DIRECTION
            factors.append({"factor": factor, "direction": direction, "weight": round(chosen / (offered + mentioned_only + 1), 2)})
    return sorted(factors, key=lambda f: (-f["weight"], f["factor"]))


def removal_row(offered, reason, removed_at) -> dict:
    """A favourite-removal reason as a feedback row: free text only. Only the chips whose terms the reason matches count
    as offered, so an unrelated chip on that card is not lowered by it."""
    return {"offered": [f for f in offered if TERMS[f].search(reason)], "chips": [], "free_text": reason,
            "skipped": False, "updated_at": removed_at}


async def current_factors(db, user_id) -> list:
    """compute_factors over the user's feedback on swiped decisions and their favourite-removal reasons."""
    rows = await _all(
        db,
        "SELECT f.chips_json, f.free_text, f.skipped, f.updated_at, d.offered_chips FROM feedback f"
        " JOIN decisions d ON d.decision_id = f.decision_id WHERE f.user_id = ? AND d.swiped_at IS NOT NULL"
        " ORDER BY f.updated_at DESC, f.decision_id", user_id)
    removals = await _all(
        db,
        "SELECT r.reason, r.removed_at, d.offered_chips FROM favourite_removals r"
        " JOIN decisions d ON d.decision_id = r.decision_id WHERE r.user_id = ? ORDER BY r.removed_at DESC, r.listing_id", user_id)
    return compute_factors([{"offered": json.loads(r["offered_chips"]), "chips": json.loads(r["chips_json"]),
                             "free_text": r["free_text"], "skipped": bool(r["skipped"]), "updated_at": r["updated_at"]}
                            for r in rows]
                           + [removal_row(json.loads(r["offered_chips"]), r["reason"], r["removed_at"]) for r in removals])


async def bump(db, user_id, cause_type, decision_id=None, flag_id=None, listing_id=None) -> int:
    """Add the next version for the user, storing the freshly computed factors, and return it. One statement, so the
    number is taken from the stored maximum with no read-then-write window."""
    factors = json.dumps(await current_factors(db, user_id))
    rows = await _all(
        db,
        "INSERT INTO profile_versions (user_id, version, created_at, cause_type, decision_id, flag_id, listing_id, factors_json)"
        " SELECT ?, COALESCE(MAX(version), 0) + 1, ?, ?, ?, ?, ?, ? FROM profile_versions WHERE user_id = ? RETURNING version",
        user_id, _now(), cause_type, decision_id, flag_id, listing_id, factors, user_id)
    return rows[0]["version"]


async def read(db, user_id) -> dict:
    """The GET /profile body: the latest snapshot and the ten most recent versions."""
    rows = await _all(db, "SELECT * FROM profile_versions WHERE user_id = ? ORDER BY version DESC LIMIT 10", user_id)
    return {
        "version": rows[0]["version"] if rows else 0,
        "factors": json.loads(rows[0]["factors_json"]) if rows else [],
        "history": [{
            "version": r["version"], "created_at": r["created_at"],
            "cause": {"type": r["cause_type"], "decision_id": r["decision_id"], "flag_id": r["flag_id"], "listing_id": r["listing_id"]},
        } for r in rows],
    }
