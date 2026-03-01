"""Edge case tests for robustness."""

import pytest

from owf.ast.blocks import EMOM, ForTime
from owf.ast.steps import EnduranceStep, StrengthStep
from owf.errors import ParseError
from owf.parser.step_parser import parse_document
from owf.serializer import dumps
from owf.units import Distance, Duration, Pace

# --- Duration edge cases ---


def test_duration_seconds():
    d = Duration.parse("30s")
    assert d.seconds == 30
    assert str(d) == "30s"


def test_duration_seconds_unit_sec():
    d = Duration.parse("90sec")
    assert d.seconds == 90
    assert str(d) == "1min30s"


def test_duration_minutes():
    d = Duration.parse("5min")
    assert d.seconds == 300
    assert str(d) == "5min"


def test_duration_hours():
    d = Duration.parse("2h")
    assert d.seconds == 7200
    assert str(d) == "2h"


def test_duration_mm_ss():
    d = Duration.parse("1:30")
    assert d.seconds == 90
    assert str(d) == "1min30s"


def test_duration_hh_mm_ss():
    d = Duration.parse("1:30:00")
    assert d.seconds == 5400
    assert str(d) == "1h30min"


def test_duration_compound():
    d = Duration.parse("1h28min2s")
    assert d.seconds == 5282
    assert str(d) == "1h28min2s"

    d2 = Duration.parse("1h30min")
    assert d2.seconds == 5400
    assert str(d2) == "1h30min"

    d3 = Duration.parse("5min30s")
    assert d3.seconds == 330
    assert str(d3) == "5min30s"


def test_duration_invalid():
    with pytest.raises(ValueError):
        Duration.parse("abc")


# --- Distance edge cases ---


def test_distance_km():
    d = Distance.parse("10km")
    assert d.value == 10
    assert d.unit == "km"
    assert str(d) == "10km"


def test_distance_miles():
    d = Distance.parse("1mile")
    assert d.value == 1
    assert d.unit == "mile"
    assert str(d) == "1mile"


def test_distance_yards():
    d = Distance.parse("400yd")
    assert d.value == 400
    assert str(d) == "400yd"


def test_distance_invalid():
    with pytest.raises(ValueError):
        Distance.parse("abc")


# --- Pace edge cases ---


def test_pace_km():
    p = Pace.parse("4:30/km")
    assert str(p) == "4:30/km"


def test_pace_mile():
    p = Pace.parse("7:00/mi")
    assert str(p) == "7:00/mi"


def test_pace_invalid():
    with pytest.raises(ValueError):
        Pace.parse("fast")


# --- Parser edge cases ---


def test_only_frontmatter():
    text = "---\nFTP: 250W\n---"
    doc = parse_document(text)
    assert doc.metadata == {"FTP": "250W"}
    assert len(doc.workouts) == 0


def test_only_heading():
    text = "# My Workout"
    doc = parse_document(text)
    assert len(doc.workouts) == 1
    assert doc.workouts[0].name == "My Workout"
    assert len(doc.workouts[0].steps) == 0


def test_heading_without_type():
    text = "# Recovery Day\n\n- rest 30min"
    doc = parse_document(text)
    assert doc.workouts[0].workout_type is None


def test_multiple_notes():
    text = "# Ride [bike]\n\n- bike 30min @easy\n\n> Note 1.\n> Note 2."
    doc = parse_document(text)
    w = doc.workouts[0]
    # Blank line before notes → workout-level, not step-level
    assert w.notes == ("Note 1.", "Note 2.")
    assert w.steps[0].notes == ()


def test_strength_reps_only():
    text = "# WoD\n\n- pull-up 100rep"
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, StrengthStep)
    assert step.reps == 100
    assert step.sets is None


def test_for_time_with_distance():
    text = "# WoD [wod]\n\n- for-time:\n  - run 1mile"
    doc = parse_document(text)
    ft = doc.workouts[0].steps[0]
    assert isinstance(ft, ForTime)
    step = ft.steps[0]
    assert isinstance(step, EnduranceStep)
    assert step.distance is not None
    assert step.distance.unit == "mile"


def test_emom_bare_minutes():
    """EMOM with bare number defaults to minutes."""
    text = "# WoD\n\n- emom 10:\n  - burpee 5rep"
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, EMOM)
    assert step.duration.seconds == 600


def test_whitespace_handling():
    """Extra blank lines should not break parsing."""
    text = "\n\n# Ride [bike]\n\n\n- bike 30min @easy\n\n\n"
    doc = parse_document(text)
    assert len(doc.workouts) == 1


def test_roundtrip_preserves_variables():
    text = (
        "---\nFTP: 250W\nbodyweight: 80kg\n---\n\n"
        "# Ride [bike]\n\n- bike 30min @200W\n"
    )
    doc = parse_document(text)
    result = dumps(doc)
    doc2 = parse_document(result)
    assert doc2.metadata == doc.metadata


def test_unclosed_frontmatter():
    text = "---\nFTP: 250W\n\n# Ride"
    with pytest.raises(ParseError, match="Unclosed frontmatter"):
        parse_document(text)


def test_empty_string():
    doc = parse_document("")
    assert len(doc.workouts) == 0
    assert doc.metadata == {}


def test_blank_lines_only():
    doc = parse_document("\n\n\n")
    assert len(doc.workouts) == 0
