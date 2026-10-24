import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import tfl  # noqa: E402


def test_classify_answers():
    assert tfl.classify(200, '{"journeys": [{"duration": 41}, {"duration": 33}, {"duration": 50}]}') == ("ok", 33)
    assert tfl.classify(404, "{}") == ("no_journey", None)
    assert tfl.classify(200, '{"journeys": []}') == ("no_journey", None)
    assert tfl.classify(200, '{}') == ("no_journey", None)
    for status in (400, 429, 500, 503, 300):
        assert tfl.classify(status, "{}") == ("transient", None)
    assert tfl.classify(200, "<html>") == ("transient", None)
    assert tfl.classify(200, "[1]") == ("transient", None)
    assert tfl.classify(200, '{"journeys": [{"duration": "x"}]}') == ("transient", None)
    assert tfl.classify(200, '{"toLocationDisambiguation": {"matchStatus": "list"}}') == ("transient", None)


def test_url_and_next_tuesday():
    from datetime import date
    assert tfl.next_tuesday(date(2026, 10, 24)) == date(2026, 10, 27)  # Saturday
    assert tfl.next_tuesday(date(2026, 10, 27)) == date(2026, 11, 3)  # a Tuesday gives the following one
    assert tfl.next_tuesday(date(2026, 10, 26)) == date(2026, 10, 27)
    assert tfl.build_url("http://x", 51.5, -0.1, "EC2N 2DB", date(2026, 10, 27)) == (
        "http://x/Journey/JourneyResults/51.5,-0.1/to/EC2N2DB?date=20261027&time=0830&timeIs=Arriving"
        "&mode=bus,cable-car,dlr,elizabeth-line,national-rail,overground,replacement-bus,river-bus,tram,tube,walking")
