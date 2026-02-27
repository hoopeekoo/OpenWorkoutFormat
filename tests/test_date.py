"""Tests for date parsing on workout headings."""

from pathlib import Path

from owf.ast.base import Workout, WorkoutDate
from owf.loader import load
from owf.parser.step_parser import parse_document
from owf.serializer import dumps


def test_date_only():
    text = "# Morning Run [run] (2025-02-27)\n\n- run 5km"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.name == "Morning Run"
    assert w.workout_type == "run"
    assert w.date == WorkoutDate(date="2025-02-27")


def test_date_with_time_range():
    text = "# Morning Run [run] (2025-02-27 06:00-07:00)\n\n- run 5km"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.date == WorkoutDate(
        date="2025-02-27", start_time="06:00", end_time="07:00"
    )


def test_date_with_start_time_only():
    text = "# Morning Run [run] (2025-02-27 06:00)\n\n- run 5km"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.date == WorkoutDate(date="2025-02-27", start_time="06:00")


def test_date_without_type():
    text = "# Morning Run (2025-02-27)\n\n- run 5km"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.name == "Morning Run"
    assert w.workout_type is None
    assert w.date == WorkoutDate(date="2025-02-27")


def test_no_date_backward_compat():
    text = "# Morning Run [run]\n\n- run 5km"
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


def test_session_with_dates():
    text = (
        "## Session (2025-02-27 14:00-16:00)\n\n"
        "# Ride [bike] (2025-02-27 14:00-15:00)\n\n"
        "- bike 30min\n\n"
        "# Strength [strength] (2025-02-27 15:15-16:00)\n\n"
        "- bench press 3x8rep @80kg"
    )
    doc = parse_document(text)
    assert len(doc.workouts) == 1
    session = doc.workouts[0]
    assert session.date == WorkoutDate(
        date="2025-02-27", start_time="14:00", end_time="16:00"
    )

    child1 = session.steps[0]
    assert isinstance(child1, Workout)
    assert child1.date == WorkoutDate(
        date="2025-02-27", start_time="14:00", end_time="15:00"
    )

    child2 = session.steps[1]
    assert isinstance(child2, Workout)
    assert child2.date == WorkoutDate(
        date="2025-02-27", start_time="15:15", end_time="16:00"
    )


def test_serialize_date():
    text = "# Morning Run [run] (2025-02-27 06:00-07:00)\n\n- run 5km\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "# Morning Run [run] (2025-02-27 06:00-07:00)" in result


def test_serialize_date_only():
    text = "# Morning Run (2025-02-27)\n\n- run 5km\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "# Morning Run (2025-02-27)" in result


def test_roundtrip_with_date():
    text = "# Morning Run [run] (2025-02-27 06:00-07:00)\n\n- run 5km"
    doc1 = parse_document(text)
    serialized = dumps(doc1)
    doc2 = parse_document(serialized)

    assert doc1.workouts[0].name == doc2.workouts[0].name
    assert doc1.workouts[0].workout_type == doc2.workouts[0].workout_type
    assert doc1.workouts[0].date == doc2.workouts[0].date


def test_roundtrip_session_with_dates():
    text = (
        "## Session (2025-02-27 14:00-16:00)\n\n"
        "# Ride [bike] (2025-02-27 14:00-15:00)\n\n"
        "- bike 30min\n\n"
        "# Strength [strength] (2025-02-27 15:15-16:00)\n\n"
        "- bench press 3x8rep @80kg"
    )
    doc1 = parse_document(text)
    serialized = dumps(doc1)
    doc2 = parse_document(serialized)

    session1 = doc1.workouts[0]
    session2 = doc2.workouts[0]
    assert session1.date == session2.date
    for s1, s2 in zip(session1.steps, session2.steps):
        if isinstance(s1, Workout):
            assert isinstance(s2, Workout)
            assert s1.date == s2.date


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
    assert child_workouts[0].date == WorkoutDate(
        date="2025-02-27", start_time="14:00", end_time="15:00"
    )
    assert child_workouts[1].name == "Upper Body"
    assert child_workouts[1].date == WorkoutDate(
        date="2025-02-27", start_time="15:15", end_time="16:00"
    )
