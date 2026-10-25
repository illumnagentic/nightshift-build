import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import curator  # noqa: E402
import fake_upstream  # noqa: E402
import prefs  # noqa: E402

LISTING = {"id": "rm-1", "url": "https://x/1", "description": "long text", "address": "1 High St", "split": "train",
           "price_gbp": 500000, "price_qualifier": None, "bedrooms": 2, "bathrooms": None, "property_type": "flat",
           "postcode": "N1 1AA", "tenure": "leasehold", "lease_years_remaining": 90, "service_charge_gbp_pa": None,
           "council_tax_band": "D", "epc_current": "C", "floor_level": "second", "key_features": '["balcony"]'}
STATIONS = [{"name": f"S{i}", "distance_km": None if i == 0 else 0.5 * i} for i in range(5)]
FLAGS = [
    {"field": "light", "value": "bright", "room": "kitchen", "confidence": "high", "observation": "sunny", "corrected_text": "dim after all",
     "source_photo": "https://x/p.jpg", "uncertainty": None},
    {"field": "sqm_estimate", "value": 60, "room": None, "confidence": "low", "observation": "from plan", "corrected_text": None,
     "source_photo": "https://x/f.jpg", "uncertainty": None},
]


def reply(scores):
    return {"candidates": [{"content": {"parts": [{"text": json.dumps({"scores": scores})}]}}]}


def row(lid="a", score=50, reason="ok"):
    return {"listing_id": lid, "score": score, "reason": reason}


def test_system_prompt_is_the_same_for_every_user():
    one = curator.build_score_body({"hard": {}, "soft": ["quiet"]}, {"version": 0, "factors": []}, [])
    two = curator.build_score_body({"hard": {"max_price_gbp": 1}, "soft": ["garden"]}, {"version": 3, "factors": [{"f": "x"}]}, [{"id": "z"}])
    assert one["systemInstruction"] == two["systemInstruction"] == {"parts": [{"text": curator.SYSTEM_PROMPT}]}
    assert "quiet" not in json.dumps(one["systemInstruction"]) and "garden" not in json.dumps(two["systemInstruction"])
    assert one["contents"] != two["contents"]


def test_body_shape():
    body = curator.build_score_body({"hard": {}, "soft": []}, {"version": 0, "factors": []}, [{"id": "a"}])
    assert curator.MODEL == prefs.MODEL == "gemini-3.8-flash"
    assert body["generationConfig"] == {"temperature": 0, "thinkingConfig": {"thinkingLevel": "low"},
                                        "responseMimeType": "application/json", "responseSchema": curator.RESPONSE_SCHEMA}
    assert len(body["contents"]) == 1 and body["contents"][0]["role"] == "user"
    assert json.loads(body["contents"][0]["parts"][0]["text"]) == {
        "stated": {"hard": {}, "soft": []}, "profile": {"version": 0, "factors": []}, "listings": [{"id": "a"}]}


def test_chunk_limit():
    curator.build_score_body({}, {}, [{"id": str(i)} for i in range(curator.CHUNK_SIZE)])
    with pytest.raises(ValueError):
        curator.build_score_body({}, {}, [{"id": str(i)} for i in range(curator.CHUNK_SIZE + 1)])


def test_compact_listing():
    out = curator.compact_listing(LISTING, STATIONS, FLAGS, None)
    assert out["id"] == "rm-1" and out["key_features"] == ["balcony"]
    assert "bathrooms" not in out and "price_qualifier" not in out and "service_charge_gbp_pa" not in out and "commute_minutes" not in out
    assert [s["name"] for s in out["stations"]] == ["S0", "S1", "S2"]
    assert out["stations"][0] == {"name": "S0"}
    assert out["flags"][0] == {"field": "light", "value": "bright", "room": "kitchen", "confidence": "high", "text": "dim after all"}
    assert out["flags"][1] == {"field": "sqm_estimate", "value": 60, "confidence": "low", "text": "from plan"}
    dumped = json.dumps(out)
    for banned in ("split", "description", "http", "address"):
        assert banned not in dumped
    assert curator.compact_listing(LISTING, [], [], 35)["commute_minutes"] == 35


def test_parse_reply_accepts_good():
    got = curator.parse_reply(reply([row("a", 0, "  fine  "), row("b", 100, "")]), ["a", "b"])
    assert got == {"a": (0, "fine"), "b": (100, None)}
    assert curator.parse_reply(reply([row("a", 5, "x" * 500)]), ["a"])["a"][1] == "x" * 200


@pytest.mark.parametrize("scores, ids", [
    ([row("a")], ["a", "b"]),
    ([row("a"), row("b")], ["a"]),
    ([row("a"), row("a")], ["a"]),
    ([row("a", 101)], ["a"]),
    ([row("a", -1)], ["a"]),
    ([row("a", True)], ["a"]),
    ([row("a", 5.5)], ["a"]),
    ([row("a", "5")], ["a"]),
    ([{"listing_id": "a", "score": 5}], ["a"]),
    (["a"], ["a"]),
    ([{"listing_id": ["a"], "score": 5, "reason": "x"}], ["a"]),
])
def test_parse_reply_rejects(scores, ids):
    assert curator.parse_reply(reply(scores), ids) is None


@pytest.mark.parametrize("data", [
    {"candidates": [{"content": {"parts": [{"text": "not json"}]}}]},
    {"candidates": [{"content": {"parts": [{"text": "[1]"}]}}]},
    {"candidates": [{"content": {"parts": [{"text": "{}"}]}}]},
    {"candidates": []},
    {},
])
def test_parse_reply_rejects_unusable(data):
    assert curator.parse_reply(data, ["a"]) is None


def test_fake_upstream_answer_parses():
    ids = ["rm-1", "rm-2", "rm-3"]
    body = curator.build_score_body({"hard": {}, "soft": []}, {"version": 0, "factors": []}, [{"id": i} for i in ids])
    status, text = fake_upstream.curator_answer(body["contents"][0]["parts"][0]["text"])
    assert status == 200
    got = curator.parse_reply(json.loads(text), ids)
    assert got is not None and set(got) == set(ids)
    assert got == curator.parse_reply(json.loads(fake_upstream.curator_answer(body["contents"][0]["parts"][0]["text"])[1]), ids)


def test_fake_upstream_curator_500_marker():
    body = curator.build_score_body({"hard": {}, "soft": ["[[curator_500]]"]}, {}, [{"id": "a"}])
    assert fake_upstream.curator_answer(body["contents"][0]["parts"][0]["text"])[0] == 500
