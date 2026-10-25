"""The taste profile: one stored snapshot per version, so a version number always maps to what it held."""
import json

from deck import _all, _now


async def bump(db, user_id, cause_type, decision_id=None, flag_id=None, listing_id=None) -> int:
    """Add the next version for the user, copying the previous factors forward, and return it. One statement, so the
    number is taken from the stored maximum with no read-then-write window."""
    rows = await _all(
        db,
        "INSERT INTO profile_versions (user_id, version, created_at, cause_type, decision_id, flag_id, listing_id, factors_json)"
        " SELECT ?, COALESCE(MAX(version), 0) + 1, ?, ?, ?, ?, ?,"
        " COALESCE((SELECT factors_json FROM profile_versions WHERE user_id = ? ORDER BY version DESC LIMIT 1), '[]')"
        " FROM profile_versions WHERE user_id = ? RETURNING version",
        user_id, _now(), cause_type, decision_id, flag_id, listing_id, user_id, user_id)
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
