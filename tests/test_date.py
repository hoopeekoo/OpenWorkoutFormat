"""Tests for date parsing on workout headings."""

from pathlib import Path

from owf.ast.base import WorkoutDate
from owf.parser.step_parser import parse_document
from owf.serializer import dumps


def test_date_on_heading():
    text = "# Morning Run [endurance] (2025-02-27)\n\n- Run 5km"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.name == "Morning Run"
    assert w.sport_type == "endurance"
    assert w.date == WorkoutDate(date="2025-02-27")


def test_date_with_time_range():
    text = "# Morning Run [endurance] (2025-02-27 06:00-07:00)\n\n- Run 5km"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.date == WorkoutDate(
        date="2025-02-27", start_time="06:00", end_time="07:00"
    )


def test_date_with_start_time_only():
    text = "# Morning Run [endurance] (2025-02-27 06:00)\n\n- Run 5km"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.date == WorkoutDate(date="2025-02-27", start_time="06:00")


def test_date_without_type():
    text = "# Morning Run (2025-02-27)\n\n- Run 5km"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.name == "Morning Run"
    assert w.sport_type is None
    assert w.date == WorkoutDate(date="2025-02-27")


def test_no_date_backward_compat():
    text = "# Morning Run [endurance]\n\n- Run 5km"
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


def test_date_on_multiple_workouts():
    """Dates on individual workouts are preserved."""
    text = (
        "# Ride [endurance] (2025-02-27 14:00-15:00)\n\n- Bike 30min\n\n"
        "# Strength [strength] (2025-02-27 15:15-16:00)\n\n"
        "- Bench Press 3x8rep @80kg"
    )
    doc = parse_document(text)
    assert len(doc.workouts) == 2
    assert doc.workouts[0].date == WorkoutDate(
        date="2025-02-27", start_time="14:00", end_time="15:00"
    )
    assert doc.workouts[1].date == WorkoutDate(
        date="2025-02-27", start_time="15:15", end_time="16:00"
    )


def test_serialize_date():
    text = "# Morning Run [endurance] (2025-02-27 06:00-07:00)\n\n- Run 5km\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "# Morning Run [endurance] (2025-02-27 06:00-07:00)" in result


def test_serialize_date_only():
    text = "# Morning Run (2025-02-27)\n\n- Run 5km\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "# Morning Run (2025-02-27)" in result


def test_roundtrip_with_date():
    text = "# Morning Run [endurance] (2025-02-27 06:00-07:00)\n\n- Run 5km"
    doc1 = parse_document(text)
    serialized = dumps(doc1)
    doc2 = parse_document(serialized)

    assert doc1.workouts[0].name == doc2.workouts[0].name
    assert doc1.workouts[0].sport_type == doc2.workouts[0].sport_type
    assert doc1.workouts[0].date == doc2.workouts[0].date


def test_dated_example():
    """triathlon_brick.owf has # workouts with dates."""
    from owf.loader import load

    doc = load(Path("examples/triathlon_brick.owf"))
    assert len(doc.workouts) == 3
    assert doc.workouts[0].name == "Swim"
    assert doc.workouts[0].date == WorkoutDate(
        date="2026-03-15", start_time="07:00", end_time=None,
    )
    assert doc.workouts[1].name == "Bike"
    assert doc.workouts[1].date == WorkoutDate(
        date="2026-03-15", start_time="08:00", end_time="09:00",
    )
    assert doc.workouts[2].name == "Brick Run"
    assert doc.workouts[2].date == WorkoutDate(
        date="2026-03-15", start_time="09:00", end_time=None,
    )
