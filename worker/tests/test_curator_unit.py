import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import curator  # noqa: E402
from fake_upstream import curator_answer  # noqa: E402


def listing(lid="rm-1", **over):
    base = {
        "id": lid, "price_gbp": 500_000, "price_qualifier": None, "bedrooms": 2, "bathrooms": 1, "property_type": "flat",
        "tenure": "leasehold", "lease_years_remaining": 120, "service_charge_gbp_pa": 1800.0, "epc_current": "C",
        "floor_level": "second", "key_features": ["Balcony", "Chain free"], "description": "SECRET DESCRIPTION",
        "lat": 51.5, "lon": -0.1,
        "stations": [{"name": "Far", "distance_km": 1.4}, {"name": "Near", "distance_km": 0.3}, {"name": "Unknown", "distance_km": None}],
    }
    return {**base, **over}


def flag(field, value, room="kitchen", corrected_text=None, confidence="high"):
    return {"field": field, "value": value, "room": room, "confidence": confidence, "corrected_text": corrected_text}


def body_for(text, ids=("rm-1", "rm-2"), profile=None, feedback=None):
    cands = [curator.candidate_summary(listing(i), [], None) for i in ids]
    return curator.build_body({"text": text, "soft": ["bright rooms"]}, profile or {}, feedback or [], cands)


def reply(ranking, usage=None):
    data = {"candidates": [{"content": {"parts": [{"text": json.dumps({"ranking": ranking})}]}}]}
    if usage:
        data["usageMetadata"] = usage
    return data


def test_two_users_share_system_instruction_and_generation_config_byte_for_byte():
    a = body_for("two beds under 500k, quiet", profile={"light": {"direction": "bright", "weight": 0.9}})
    b = body_for("studio near a tube station", ids=("rm-7", "rm-8", "rm-9"), feedback=[{"id": "rm-3", "note": "too dark"}])
    for key in ("systemInstruction", "generationConfig"):
        assert json.dumps(a[key], sort_keys=True) == json.dumps(b[key], sort_keys=True)
    assert a["contents"] != b["contents"]


def test_user_text_is_only_in_the_user_message():
    body = body_for("UNIQUE-BUYER-WORDS", profile={"x": "UNIQUE-PROFILE"}, feedback=["UNIQUE-FEEDBACK"])
    fixed = json.dumps([body["systemInstruction"], body["generationConfig"]])
    for word in ("UNIQUE-BUYER-WORDS", "UNIQUE-PROFILE", "UNIQUE-FEEDBACK", "rm-1"):
        assert word not in fixed
        assert word in body["contents"][0]["parts"][0]["text"]


def test_system_prompt_has_no_digits_and_names_every_user_message_field():
    assert not re.search(r"\d", curator.SYSTEM_PROMPT)
    message = json.loads(body_for("x")["contents"][0]["parts"][0]["text"])
    for key in message:
        assert key in curator.SYSTEM_PROMPT
    for key in curator.candidate_summary(listing(), [flag("light", "ok")], 30):
        assert key in curator.SYSTEM_PROMPT
    for key in ("light", "defects", "size_tricks", "missing", "sqm_estimate", "floorplan_notes"):
        assert key in curator.SYSTEM_PROMPT


def test_thinking_is_explicit_low_and_temperature_zero():
    config = body_for("x")["generationConfig"]
    assert config["thinkingConfig"] == {"thinkingLevel": "low"}
    assert config["temperature"] == 0
    assert config["responseMimeType"] == "application/json"
    assert curator.MODEL == "gemini-3.8-flash"


def test_schema_is_a_plain_string_array_with_no_enum():
    schema = curator.RESPONSE_SCHEMA
    assert schema["properties"] == {"ranking": {"type": "ARRAY", "items": {"type": "STRING"}}}
    assert "enum" not in json.dumps(schema)
    assert body_for("x")["generationConfig"]["responseSchema"] is schema


def test_user_message_key_order_is_fixed_and_compact():
    text = body_for("x")["contents"][0]["parts"][0]["text"]
    assert list(json.loads(text)) == ["stated_prefs", "taste_profile", "recent_feedback", "candidates"]
    assert ": " not in text.split('"candidates"')[0] and ", " not in text.split('"candidates"')[0]


def test_summary_is_compact_and_ordered():
    s = curator.candidate_summary(listing(), [], 42)
    assert list(s) == ["id", "price_gbp", "bedrooms", "bathrooms", "property_type", "tenure", "lease_years_remaining",
                       "service_charge_gbp_pa", "epc_current", "floor_level", "key_features", "station", "commute_min"]
    assert s["station"] == {"name": "Near", "distance_km": 0.3}
    assert s["commute_min"] == 42
    assert "description" not in s and "lat" not in s


def test_summary_leaves_out_unknowns():
    s = curator.candidate_summary(listing(bedrooms=None, tenure=None, key_features=[], stations=[]), [], None)
    assert not {"bedrooms", "tenure", "key_features", "station", "commute_min", "photos"} & set(s)


def test_flag_digest():
    flags = [
        flag("light", "bright", "kitchen"), flag("light", "bright", "kitchen"), flag("light", "poor", "kitchen"),
        flag("light", "poor", "bedroom"), flag("light", "bright", "bedroom"),
        flag("defects", "damp patch", "bathroom"), flag("defects", "damp patch", "bathroom"),
        flag("size_tricks", "wide-angle lens", "living_room"), flag("missing", "window", "bathroom"),
        flag("sqm_estimate", 69.6, None), flag("floorplan_notes", "x" * 500, None), flag("room", "kitchen"),
    ]
    photos = curator.candidate_summary(listing(), flags, None)["photos"]
    assert photos["light"] == {"bedroom": "poor", "kitchen": "bright"}  # most frequent; a tie goes to the worse reading
    assert photos["defects"] == ["bathroom: damp patch"]
    assert photos["size_tricks"] == ["living_room: wide-angle lens"]
    assert photos["missing"] == ["bathroom: window"]
    assert photos["sqm_estimate"] == 69.6
    assert photos["floorplan_notes"] == "x" * curator.FLOORPLAN_NOTES_CHARS
    assert "room" not in photos


def test_corrected_text_replaces_the_value():
    flags = [flag("defects", "damp patch", "bathroom", corrected_text="not damp, just a shadow"),
             flag("light", "poor", "kitchen", corrected_text="bright")]
    photos = curator.candidate_summary(listing(), flags, None)["photos"]
    assert photos["defects"] == ["bathroom: not damp, just a shadow"]
    assert photos["light"] == {"kitchen": "bright"}
    assert "damp patch" not in json.dumps(photos)


def light_for(flags):
    return curator.candidate_summary(listing(), flags, None)["photos"]["light"]


def test_correction_wins_its_room_over_more_numerous_readings():
    flags = [flag("light", "bright"), flag("light", "bright"), flag("light", "bright"),
             flag("light", "ok", corrected_text="not bright at all")]
    assert light_for(flags) == {"kitchen": "not bright at all"}


def test_uncorrected_tie_goes_to_the_worse_reading():
    assert light_for([flag("light", "bright"), flag("light", "poor")]) == {"kitchen": "poor"}


def test_several_corrections_take_the_most_frequent_then_the_first():
    flags = [flag("light", "ok", corrected_text="gloomy"), flag("light", "ok", corrected_text="sunny"),
             flag("light", "ok", corrected_text="sunny"), flag("light", "bright")]
    assert light_for(flags) == {"kitchen": "sunny"}
    flags = [flag("light", "ok", corrected_text="gloomy"), flag("light", "ok", corrected_text="sunny")]
    assert light_for(flags) == {"kitchen": "gloomy"}


def test_same_input_gives_identical_bytes():
    flags = [flag("defects", "b"), flag("defects", "a"), flag("light", "ok")]
    one = json.dumps(body_for("x"), sort_keys=False)
    assert one == json.dumps(body_for("x"), sort_keys=False)
    assert curator.candidate_summary(listing(), flags, 1) == curator.candidate_summary(listing(), list(reversed(flags)), 1)


IDS = ["a", "b", "c", "d"]


def test_complete_reply_is_ok_and_carries_usage():
    usage = {"promptTokenCount": 900, "candidatesTokenCount": 30, "thoughtsTokenCount": 12}
    assert curator.parse_ranking(reply(["c", "a", "d", "b"], usage), IDS) == (
        ["c", "a", "d", "b"], "ok", {"prompt": 900, "candidates": 30, "thoughts": 12})


def test_usage_is_none_when_absent():
    assert curator.parse_ranking(reply(IDS), IDS)[2] is None


def test_unknown_and_duplicate_ids_are_dropped_and_missing_appended_in_candidate_order():
    ranking, status, _ = curator.parse_ranking(reply(["c", "zzz", "c", "a", 5, None, ["a"]]), IDS)
    assert ranking == ["c", "a", "b", "d"]
    assert status == "incomplete"


def test_unknown_id_alone_marks_incomplete():
    assert curator.parse_ranking(reply(["a", "x", "b", "c", "d"]), IDS)[1:2] == ("incomplete",)


def test_exactly_half_is_repaired():
    ranking, status, _ = curator.parse_ranking(reply(["d", "c"]), IDS)
    assert (ranking, status) == (["d", "c", "a", "b"], "incomplete")


def test_below_half_is_a_failure():
    with pytest.raises(curator.CuratorError):
        curator.parse_ranking(reply(["d", "x", "y", "z"]), IDS)


@pytest.mark.parametrize("data", [
    {"candidates": []},
    {},
    None,
    {"candidates": [{"content": {"parts": [{"text": "not json"}]}}]},
    {"candidates": [{"content": {"parts": [{"text": "[1, 2]"}]}}]},
    {"candidates": [{"content": {"parts": [{"text": '{"ranking": "a,b"}'}]}}]},
    {"candidates": [{"content": {"parts": [{"text": '{"other": []}'}]}}]},
    {"candidates": [{"content": {"parts": [{"text": 5}]}}]},
])
def test_unusable_replies_fail(data):
    with pytest.raises(curator.CuratorError):
        curator.parse_ranking(data, IDS)


def test_fake_curator_answer_sorts_ids_and_honours_markers():
    msg = {"stated_prefs": {"text": "x"}, "candidates": [{"id": "rm-3"}, {"id": "rm-1"}, {"id": "rm-2"}]}
    status, text, returned = curator_answer(msg)
    assert (status, returned) == (200, ["rm-1", "rm-2", "rm-3"])
    assert curator.parse_ranking(json.loads(text), ["rm-3", "rm-1", "rm-2"])[1] == "ok"
    assert curator_answer({**msg, "stated_prefs": {"text": "[[curator_http_500]]"}})[0] == 500
    status, text, _ = curator_answer({**msg, "stated_prefs": {"text": "[[curator_not_json]]"}})
    with pytest.raises(curator.CuratorError):
        curator.parse_ranking(json.loads(text), ["rm-1", "rm-2", "rm-3"])
    status, text, _ = curator_answer({**msg, "stated_prefs": {"text": "[[curator_bad_ids]]"}})
    with pytest.raises(curator.CuratorError):
        curator.parse_ranking(json.loads(text), ["rm-1", "rm-2", "rm-3"])
