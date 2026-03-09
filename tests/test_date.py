"""Tests for date parsing on workout headings."""

from pathlib import Path

import pytest

from owf.ast.base import Workout, WorkoutDate
from owf.errors import ParseError
from owf.loader import load
from owf.parser.step_parser import parse_document
from owf.serializer import dumps


def test_date_on_session():
    text = "## Morning Run [endurance] (2025-02-27)\n\n- run 5km"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.name == "Morning Run"
    assert w.sport_type == "endurance"
    assert w.date == WorkoutDate(date="2025-02-27")


def test_date_with_time_range():
    text = "## Morning Run [endurance] (2025-02-27 06:00-07:00)\n\n- run 5km"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.date == WorkoutDate(
        date="2025-02-27", start_time="06:00", end_time="07:00"
    )


def test_date_with_start_time_only():
    text = "## Morning Run [endurance] (2025-02-27 06:00)\n\n- run 5km"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.date == WorkoutDate(date="2025-02-27", start_time="06:00")


def test_date_without_type():
    text = "## Morning Run (2025-02-27)\n\n- run 5km"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.name == "Morning Run"
    assert w.sport_type is None
    assert w.date == WorkoutDate(date="2025-02-27")


def test_no_date_backward_compat():
    text = "## Morning Run [endurance]\n\n- run 5km"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.date is None


def test_workout_date_str_date_only():
    d = WorkoutDate(date="2025-02-27")
    assert str(d) == "2025-02-27"


def test_workout_date_str_with_time_range():
    d = WorkoutDate(date="2025-02-27", start_time="06:00", end_time="07:00")
    assert str(d) == "2025-02-27 06:00-07:00"


def test_workout_date_str_with_start_only():
    d = WorkoutDate(date="2025-02-27", start_time="06:00")
    assert str(d) == "2025-02-27 06:00"


def test_session_date_preserved():
    text = (
        "## Session (2025-02-27 14:00-16:00)\n\n"
        "# Ride [endurance]\n\n- bike 30min\n\n"
        "# Strength [strength]\n\n- Bench Press 3x8rep @80kg"
    )
    doc = parse_document(text)
    assert len(doc.workouts) == 1
    session = doc.workouts[0]
    assert session.date == WorkoutDate(
        date="2025-02-27", start_time="14:00", end_time="16:00"
    )


def test_dates_on_child_headings_rejected():
    """Dates on # child headings inside sessions raise ParseError."""
    text = (
        "## Session (2025-02-27 14:00-16:00)\n\n"
        "# Ride [endurance] (2025-02-27 14:00-15:00)\n\n"
        "- bike 30min\n\n"
        "# Strength [strength] (2025-02-27 15:15-16:00)\n\n"
        "- Bench Press 3x8rep @80kg"
    )
    with pytest.raises(ParseError, match="Dates are only allowed on session"):
        parse_document(text)


def test_serialize_session_date():
    text = "## Morning Run [endurance] (2025-02-27 06:00-07:00)\n\n- run 5km\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "## Morning Run [endurance] (2025-02-27 06:00-07:00)" in result


def test_serialize_date_only():
    text = "## Morning Run (2025-02-27)\n\n- run 5km\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "## Morning Run (2025-02-27)" in result


def test_roundtrip_with_date():
    text = "## Morning Run [endurance] (2025-02-27 06:00-07:00)\n\n- run 5km"
    doc1 = parse_document(text)
    serialized = dumps(doc1)
    doc2 = parse_document(serialized)

    assert doc1.workouts[0].name == doc2.workouts[0].name
    assert doc1.workouts[0].sport_type == doc2.workouts[0].sport_type
    assert doc1.workouts[0].date == doc2.workouts[0].date


def test_roundtrip_session_with_date():
    text = (
        "## Session (2025-02-27 14:00-16:00)\n\n"
        "# Ride [endurance]\n\n- bike 30min\n\n"
        "# Strength [strength]\n\n- Bench Press 3x8rep @80kg"
    )
    doc1 = parse_document(text)
    serialized = dumps(doc1)
    doc2 = parse_document(serialized)

    session1 = doc1.workouts[0]
    session2 = doc2.workouts[0]
    assert session1.date == session2.date


def test_dated_session_example():
    doc = load(Path("examples/dated_session.owf"))
    assert len(doc.workouts) == 1
    session = doc.workouts[0]
    assert session.name == "Saturday Training"
    assert session.date == WorkoutDate(
        date="2025-02-27", start_time="14:00", end_time="16:00"
    )

    child_workouts = [s for s in session.steps if isinstance(s, Workout)]
    assert len(child_workouts) == 2
    assert child_workouts[0].name == "Threshold Ride"
    assert child_workouts[0].date is None  # no dates on child workouts
    assert child_workouts[1].name == "Upper Body"
    assert child_workouts[1].date is None  # no dates on child workouts


def test_flat_date_lifted_to_session():
    """Single flat # workout with date: date is lifted to implicit session."""
    text = "# Morning Run [endurance] (2025-02-27 06:00)\n\n- run 5km"
    doc = parse_document(text)
    session = doc.workouts[0]
    assert session.date == WorkoutDate(date="2025-02-27", start_time="06:00")
    child = session.steps[0]
    assert isinstance(child, Workout)
    assert child.date is None
