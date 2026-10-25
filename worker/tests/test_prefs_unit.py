import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import prefs  # noqa: E402


@pytest.mark.parametrize("raw, expected", [
    ("EC2N 2DB", "EC2N 2DB"),
    ("ec2n2db", "EC2N 2DB"),
    ("  ec2n   2db ", "EC2N 2DB"),
    ("SW1A 1AA", "SW1A 1AA"),
    ("M1 1AE", "M1 1AE"),
    ("B33 8TH", "B33 8TH"),
    ("W1A0AX", "W1A 0AX"),
    ("Liverpool Street", None),
    ("EC2N", None),
    ("EC2N 2D", None),
    ("EC2N 2DBX", None),
    ("1234 5AB", None),
    ("", None),
    ("   ", None),
])
def test_normalise_postcode(raw, expected):
    assert prefs.normalise_postcode(raw) == expected


def test_request_body_shape():
    body = prefs.build_parse_body("Two bed flat under 550k")
    assert body["systemInstruction"] == {"parts": [{"text": prefs.SYSTEM_PROMPT}]}
    assert body["contents"] == [{"role": "user", "parts": [{"text": "Two bed flat under 550k"}]}]
    config = body["generationConfig"]
    assert config["temperature"] == 0
    assert config["thinkingConfig"] == {"thinkingLevel": "low"}
    assert config["responseMimeType"] == "application/json"
    assert config["responseSchema"] == prefs.RESPONSE_SCHEMA
    assert prefs.MODEL == "gemini-3.8-flash"


def test_system_prompt_is_fixed_and_holds_no_user_text():
    first = prefs.build_parse_body("alpha unique words")["systemInstruction"]
    second = prefs.build_parse_body("beta other words")["systemInstruction"]
    assert first == second
    assert "alpha unique words" not in json.dumps(first)


def test_schema_has_no_commute_field():
    assert "max_commute_min" not in json.dumps(prefs.RESPONSE_SCHEMA)


def reply(obj) -> dict:
    return {"candidates": [{"content": {"parts": [{"text": obj if isinstance(obj, str) else json.dumps(obj)}]}}]}


def test_good_reply_passes_through_with_request_commute():
    raw = {"hard": {"max_price_gbp": 550000, "min_bedrooms": 2, "property_types": ["flat", "house"],
                    "min_epc": "D", "tenure": "freehold", "min_lease_years": 90}, "soft": ["bright rooms"]}
    parsed = prefs.parse_reply(reply(raw), 45)
    assert parsed == {"hard": {**raw["hard"], "max_commute_min": 45}, "soft": ["bright rooms"]}


def test_bad_values_become_null():
    raw = {"hard": {"max_price_gbp": 5, "min_bedrooms": True, "property_types": ["castle"],
                    "min_epc": "H", "tenure": "commonhold", "min_lease_years": "99"}, "soft": "not a list"}
    assert prefs.parse_reply(reply(raw), None) == {
        "hard": {"max_price_gbp": None, "min_bedrooms": None, "property_types": None, "min_epc": None,
                 "tenure": None, "min_lease_years": None, "max_commute_min": None},
        "soft": [],
    }


@pytest.mark.parametrize("field, value, expected", [
    ("max_price_gbp", 10_000, 10_000), ("max_price_gbp", 9_999, None), ("max_price_gbp", 50_000_000, 50_000_000),
    ("max_price_gbp", 50_000_001, None), ("max_price_gbp", 550000.5, None), ("max_price_gbp", "550000", None),
    ("min_bedrooms", 0, 0), ("min_bedrooms", 10, 10), ("min_bedrooms", 11, None), ("min_bedrooms", -1, None),
    ("min_bedrooms", False, None),
    ("min_lease_years", 1, 1), ("min_lease_years", 999, 999), ("min_lease_years", 0, None), ("min_lease_years", 1000, None),
    ("min_epc", "A", "A"), ("min_epc", "G", "G"), ("min_epc", "a", None), ("min_epc", 3, None),
    ("tenure", "share_of_freehold", "share_of_freehold"), ("tenure", "Freehold", None), ("tenure", ["freehold"], None),
])
def test_scalar_ranges(field, value, expected):
    parsed = prefs.parse_reply(reply({"hard": {field: value}, "soft": []}), None)
    assert parsed["hard"][field] == expected


def test_property_types_filtered_and_deduplicated():
    parsed = prefs.parse_reply(reply({"hard": {"property_types": ["flat", "castle", "flat", 3, "house"]}, "soft": []}), None)
    assert parsed["hard"]["property_types"] == ["flat", "house"]
    assert prefs.parse_reply(reply({"hard": {"property_types": []}, "soft": []}), None)["hard"]["property_types"] is None
    assert prefs.parse_reply(reply({"hard": {"property_types": "flat"}, "soft": []}), None)["hard"]["property_types"] is None


def test_soft_trimmed_cleaned_and_capped():
    soft = ["  quiet  ", "", "   ", 7, None, "y" * 121, "y" * 120] + [f"item {i}" for i in range(20)]
    result = prefs.parse_reply(reply({"hard": {}, "soft": soft}), None)["soft"]
    assert result[:2] == ["quiet", "y" * 120]
    assert len(result) == 10


@pytest.mark.parametrize("data", [
    {}, {"candidates": []}, {"candidates": [{}]}, {"candidates": [{"content": {"parts": []}}]},
    {"candidates": [{"content": {"parts": [{"text": 5}]}}]}, {"candidates": "x"},
    reply("not json"), reply("[1, 2]"), reply("null"),
])
def test_unusable_reply_is_none(data):
    assert prefs.parse_reply(data, None) is None


def test_object_without_hard_gives_all_null():
    parsed = prefs.parse_reply(reply({}), 30)
    assert parsed["soft"] == []
    assert parsed["hard"]["max_commute_min"] == 30
    assert all(v is None for k, v in parsed["hard"].items() if k != "max_commute_min")
