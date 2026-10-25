"""The taste profile factors as a pure function. No server needed."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import chips  # noqa: E402
import taste  # noqa: E402

CATALOGUE_IDS = [row[0] for row in chips.CATALOGUE]


def row(offered, answers=(), free_text=None, skipped=False, at=1):
    return {"offered": list(offered), "chips": [{"chip_id": c, "strength": s, "text": t} for c, s, t in answers],
            "free_text": free_text, "skipped": skipped, "updated_at": f"2026-10-25T10:00:{at:02d}Z"}


def by_name(factors):
    return {f["factor"]: f for f in factors}


def test_one_chosen_of_one_offered_is_half():
    (factor,) = taste.compute_factors([row(["garden"], [("garden", "must_have", "Lovely garden")])])
    assert factor == {"factor": "garden", "direction": 'must have "Lovely garden"', "weight": 0.5}


def test_no_rows_and_no_choices_give_no_factors():
    assert taste.compute_factors([]) == []
    assert taste.compute_factors([row(["garden", "parking"])]) == []


def test_a_skip_changes_no_weight():
    answered = row(["garden"], [("garden", "nice_to_have", None)], at=1)
    skip = row(["garden"], skipped=True, at=2)
    assert taste.compute_factors([answered, skip]) == taste.compute_factors([answered])


def test_a_clear_counts_as_offered_with_nothing_chosen():
    answered = row(["garden"], [("garden", "nice_to_have", None)], at=1)
    clear = row(["garden"], at=2)
    assert by_name(taste.compute_factors([answered, clear]))["garden"]["weight"] == round(1 / 3, 2)


def test_rarely_offered_always_chosen_beats_often_offered_rarely_chosen():
    rows = [row(["garden"], [("garden", "must_have", None)], at=1)]
    rows += [row(["parking"], [("parking", "nice_to_have", None)] if i == 0 else [], at=2 + i) for i in range(5)]
    factors = by_name(taste.compute_factors(rows))
    assert factors["garden"]["weight"] == 0.5 and factors["parking"]["weight"] == round(1 / 6, 2)


def test_a_free_text_only_mention_counts_as_mentioned_only_and_chosen():
    (factor,) = taste.compute_factors([row([], free_text="The garden was lovely")])
    assert factor == {"factor": "garden", "direction": "mentioned in comments", "weight": 0.5}
    both = by_name(taste.compute_factors([row([], free_text="Nice garden"), row(["garden"], free_text="no mention")]))
    assert both["garden"]["weight"] == round(1 / 3, 2)


def test_one_decision_counts_once_with_a_chip_and_a_text_match():
    (factor,) = taste.compute_factors([row(["garden"], [("garden", "must_have", "Big")], free_text="garden garden garden")])
    assert factor["weight"] == 0.5


def test_a_term_in_the_text_of_an_offered_chip_is_offered_not_mentioned_only():
    (factor,) = taste.compute_factors([row(["garden"], free_text="the garden")])
    assert factor["weight"] == 0.5


def test_free_text_never_adds_a_factor_outside_the_catalogue():
    factors = taste.compute_factors([row([], free_text="garden parking bright kitchen spaceship dragons")])
    assert {f["factor"] for f in factors} <= set(CATALOGUE_IDS)


def test_direction_newest_first_at_most_three_with_exact_strength_words():
    answers = [("garden", "must_have", "one"), ("garden", "nice_to_have", "two"), ("garden", "would_prefer_not", None),
               ("garden", "deal_breaker", "four")]
    rows = [row(["garden"], [a], at=i + 1) for i, a in enumerate(answers)]
    (factor,) = taste.compute_factors(rows)
    assert factor["direction"] == 'deal-breaker "four"; would prefer not (no comment); nice to have "two"'
    (single,) = taste.compute_factors([row(["garden"], [("garden", "must_have", None)])])
    assert single["direction"] == "must have (no comment)"


def test_rows_with_equal_updated_at_keep_their_input_order_in_the_direction():
    rows = [row(["garden"], [("garden", "must_have", "first")], at=5), row(["garden"], [("garden", "nice_to_have", "second")], at=5)]
    (factor,) = taste.compute_factors(rows)
    assert factor["direction"] == 'must have "first"; nice to have "second"'
    (reversed_factor,) = taste.compute_factors(rows[::-1])
    assert reversed_factor["direction"] == 'nice to have "second"; must have "first"'


def test_direction_with_chip_answers_ignores_free_text_mentions():
    rows = [row(["garden"], [("garden", "must_have", "Big")], at=1), row([], free_text="garden", at=2)]
    (factor,) = taste.compute_factors(rows)
    assert factor["direction"] == 'must have "Big"' and factor["weight"] == round(2 / 3, 2)


def test_order_is_weight_descending_then_chip_id():
    rows = [row(["parking", "garden"], [("parking", "must_have", None), ("garden", "must_have", None)], at=1),
            row(["kitchen"], [("kitchen", "must_have", None)], at=2),
            row(["kitchen"], [("kitchen", "must_have", None)], at=3)]
    assert [(f["factor"], f["weight"]) for f in taste.compute_factors(rows)] == [("kitchen", 0.67), ("garden", 0.5), ("parking", 0.5)]


def test_every_factor_has_a_term_and_names_are_catalogue_ids():
    assert set(taste.TERMS) == set(CATALOGUE_IDS)
    assert set(by_name(taste.compute_factors([row(CATALOGUE_IDS, [(c, "nice_to_have", None) for c in CATALOGUE_IDS])]))) == set(CATALOGUE_IDS)


TERM_SENTENCES = {
    "garden": ("Lovely garden at the back.", "Lovely patio at the back."),
    "parking": ("No parking on the street.", "No room on the street."),
    "natural_light": ("The lounge was dark.", "The lounge was carpeted."),
    "balcony_terrace": ("Nice balcony.", "Nice staircase."),
    "price_value": ("Overpriced for what it is.", "Fine for what it is."),
    "commute": ("The commute would kill me.", "The journey would kill me."),
    "station_access": ("Ten minutes from the tube.", "Ten minutes from the shops."),
    "area_busyness": ("The street felt noisy.", "The street felt long."),
    "space": ("Rooms feel cramped.", "Rooms feel plain."),
    "kitchen": ("Lovely kitchen.", "Lovely hallway."),
    "layout": ("Awkward layout.", "Awkward entrance."),
    "condition": ("Very dated inside.", "Very warm inside."),
    "bathrooms": ("Only one bathroom.", "Only one bedroom."),
    "floor_level": ("Too many stairs.", "Too many flats."),
    "building_amenities": ("A gym would be nice.", "A pool would be nice."),
    "lease": ("The lease is short.", "The agent is short."),
    "service_charge": ("The service charge is huge.", "The council tax is huge."),
    "energy_efficiency": ("The EPC is poor.", "The paint is poor."),
    "home_office": ("No spot for a home office.", "No spot for a sofa."),
    "building_style": ("Love the Victorian features.", "Love the cornicing."),
}


def test_the_sentence_table_covers_every_term():
    assert set(TERM_SENTENCES) == set(taste.TERMS)


@pytest.mark.parametrize("factor", sorted(TERM_SENTENCES))
def test_term_matches_one_sentence_and_not_another(factor):
    match, non_match = TERM_SENTENCES[factor]
    assert taste.TERMS[factor].search(match) and not taste.TERMS[factor].search(non_match)


def test_terms_are_case_insensitive_and_word_bounded():
    assert taste.TERMS["garden"].search("GARDEN") and not taste.TERMS["garden"].search("regardenise")


def test_a_favourite_removal_reason_counts_once_as_offered_or_mentioned_and_once_as_chosen():
    offered_row = taste.removal_row(["garden", "parking"], "No garden, sadly.", "2026-10-25T10:00:09Z")
    assert offered_row["offered"] == ["garden"] and offered_row["chips"] == [] and not offered_row["skipped"]
    assert taste.removal_row(["parking"], "No garden, sadly.", "2026-10-25T10:00:09Z")["offered"] == []
    # Offered and matched: offered 1, chosen 1. Not offered but matched: mentioned_only 1, chosen 1. Same weight either way.
    (offered,) = taste.compute_factors([offered_row])
    (mentioned,) = taste.compute_factors([taste.removal_row(["parking"], "No garden, sadly.", "2026-10-25T10:00:09Z")])
    assert offered == mentioned == {"factor": "garden", "direction": "mentioned in comments", "weight": 0.5}


def test_a_removal_reason_does_not_lower_an_unrelated_offered_chip():
    answered = row(["garden", "parking"], [("parking", "must_have", None)], at=1)
    removal = taste.removal_row(["garden", "parking"], "Garden was too small.", "2026-10-25T10:00:09Z")
    factors = by_name(taste.compute_factors([answered, removal]))
    assert factors["parking"]["weight"] == 0.5
    assert factors["garden"]["weight"] == round(1 / 3, 2)
