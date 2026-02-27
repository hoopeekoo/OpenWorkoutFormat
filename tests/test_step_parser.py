"""Tests for the step parser and full document parsing."""

from owf.ast.base import Document, Workout
from owf.ast.blocks import (
    AMRAP,
    EMOM,
    AlternatingEMOM,
    Circuit,
    CustomInterval,
    ForTime,
    Superset,
)
from owf.ast.params import PowerParam, RIRParam, WeightParam
from owf.ast.steps import EnduranceStep, RepeatStep, RestStep, StrengthStep
from owf.parser.step_parser import parse_document


def test_empty_document():
    doc = parse_document("")
    assert isinstance(doc, Document)
    assert len(doc.workouts) == 0


def test_simple_endurance():
    text = (
        "# Easy Run [run]\n\n- warmup 15min @easy\n"
        "- run 5km @4:30/km\n- cooldown 10min @easy"
    )
    doc = parse_document(text)
    assert len(doc.workouts) == 1
    w = doc.workouts[0]
    assert w.name == "Easy Run"
    assert w.workout_type == "run"
    assert len(w.steps) == 3
    assert isinstance(w.steps[0], EnduranceStep)
    assert w.steps[0].action == "warmup"
    assert w.steps[0].duration is not None
    assert w.steps[0].duration.seconds == 900


def test_endurance_with_distance():
    text = "# Run\n\n- run 10km @4:30/km"
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, EnduranceStep)
    assert step.distance is not None
    assert step.distance.value == 10
    assert step.distance.unit == "km"


def test_rest_step():
    text = "# Session\n\n- rest 5min"
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, RestStep)
    assert step.duration.seconds == 300


def test_repeat_block():
    text = (
        "# Intervals\n\n- 5x:\n"
        "  - bike 5min @200W\n  - recover 3min @easy"
    )
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, RepeatStep)
    assert step.count == 5
    assert len(step.steps) == 2
    assert isinstance(step.steps[0], EnduranceStep)
    assert isinstance(step.steps[1], EnduranceStep)


def test_strength_step():
    text = (
        "# Strength [strength]\n\n"
        "- bench press 3x8rep @80kg rest:90s"
    )
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, StrengthStep)
    assert step.exercise == "bench press"
    assert step.sets == 3
    assert step.reps == 8
    assert step.rest is not None
    assert step.rest.seconds == 90


def test_superset():
    text = (
        "# Strength\n\n- 3x superset:\n"
        "  - bench press 3x8rep @80kg rest:90s\n"
        "  - bent-over row 3x8rep @60kg rest:90s"
    )
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, Superset)
    assert step.count == 3
    assert len(step.steps) == 2


def test_circuit():
    text = (
        "# Strength\n\n- 3x circuit:\n"
        "  - kettlebell swing 10rep @24kg\n"
        "  - push-up 15rep\n"
        "  - air squat 20rep"
    )
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, Circuit)
    assert step.count == 3
    assert len(step.steps) == 3


def test_emom():
    text = "# WoD [wod]\n\n- emom 10min:\n  - power clean 3rep @70kg"
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, EMOM)
    assert step.duration.seconds == 600
    assert len(step.steps) == 1


def test_emom_alternating():
    text = (
        "# WoD [wod]\n\n- emom 12min alternating:\n"
        "  - deadlift 5rep @100kg\n"
        "  - strict press 7rep @40kg"
    )
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, AlternatingEMOM)
    assert step.duration.seconds == 720
    assert len(step.steps) == 2


def test_custom_interval():
    text = (
        "# WoD [wod]\n\n- every 2min for 20min:\n"
        "  - wall ball 15rep @9kg"
    )
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, CustomInterval)
    assert step.interval.seconds == 120
    assert step.duration.seconds == 1200
    assert len(step.steps) == 1


def test_amrap():
    text = (
        "# Metcon [wod]\n\n- amrap 12min:\n"
        "  - pull-up 5rep\n  - push-up 10rep\n"
        "  - air squat 15rep"
    )
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, AMRAP)
    assert step.duration.seconds == 720
    assert len(step.steps) == 3


def test_for_time():
    text = (
        "# Murph [wod]\n\n- for-time:\n"
        "  - run 1mile\n  - pull-up 100rep\n"
        "  - push-up 200rep"
    )
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, ForTime)
    assert step.time_cap is None
    assert len(step.steps) == 3


def test_for_time_with_cap():
    text = "# WoD [wod]\n\n- for-time 20min:\n  - run 5km"
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, ForTime)
    assert step.time_cap is not None
    assert step.time_cap.seconds == 1200


def test_session_with_child_workouts():
    text = (
        "## Session\n\n- warmup 10min @easy\n\n"
        "# Ride [bike]\n\n- bike 30min\n\n"
        "# Strength [strength]\n\n- bench press 3x8rep @80kg"
    )
    doc = parse_document(text)
    assert len(doc.workouts) == 1
    session = doc.workouts[0]
    assert session.name == "Session"
    # warmup (session-level), child Ride, child Strength
    assert len(session.steps) == 3
    assert isinstance(session.steps[0], EnduranceStep)
    assert isinstance(session.steps[1], Workout)
    assert session.steps[1].name == "Ride"
    assert session.steps[1].workout_type == "bike"
    assert isinstance(session.steps[2], Workout)
    assert session.steps[2].name == "Strength"
    assert session.steps[2].workout_type == "strength"


def test_frontmatter():
    text = (
        "---\nFTP: 250W\n1RM bench press: 100kg\n---\n\n"
        "# Ride [bike]\n\n- bike 30min @80% of FTP"
    )
    doc = parse_document(text)
    assert doc.metadata == {"FTP": "250W", "1RM bench press": "100kg"}
    assert len(doc.workouts) == 1


def test_notes_on_workout():
    text = "# Ride [bike]\n\n- bike 30min @easy\n\n> Great ride today."
    doc = parse_document(text)
    w = doc.workouts[0]
    # The note should be either on the last step or as a workout-level note
    step = w.steps[0]
    assert isinstance(step, EnduranceStep)
    # Note attached to step
    assert "Great ride today." in step.notes or "Great ride today." in w.notes


def test_multiple_workouts():
    text = (
        "# Ride [bike]\n\n- bike 30min\n\n"
        "# Strength [strength]\n\n- bench press 3x8rep @80kg"
    )
    doc = parse_document(text)
    assert len(doc.workouts) == 2
    assert doc.workouts[0].name == "Ride"
    assert doc.workouts[1].name == "Strength"


def test_endurance_with_power_param():
    text = "# Ride [bike]\n\n- bike 5min @200W"
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, EnduranceStep)
    assert len(step.params) == 1
    assert isinstance(step.params[0], PowerParam)


def test_strength_with_rir():
    text = (
        "# Strength [strength]\n\n"
        "- bench press 3x8rep @80kg @RIR 2 rest:90s"
    )
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, StrengthStep)
    rir_params = [p for p in step.params if isinstance(p, RIRParam)]
    assert len(rir_params) == 1
    assert rir_params[0].value == 2


def test_session_combination_inferred():
    """Session with 2+ distinct child workout types → combination."""
    text = (
        "## Training\n\n"
        "# Ride [bike]\n\n- bike 30min\n\n"
        "# Strength [strength]\n\n- bench press 3x8rep @80kg"
    )
    doc = parse_document(text)
    assert doc.workouts[0].workout_type == "combination"


def test_session_single_child_type_no_combination():
    """Session where all children have the same type → None."""
    text = (
        "## Training\n\n"
        "# Ride A [bike]\n\n- bike 30min\n\n"
        "# Ride B [bike]\n\n- bike 20min"
    )
    doc = parse_document(text)
    assert doc.workouts[0].workout_type is None


def test_session_no_child_types_no_combination():
    """Session with children that have no type → None."""
    text = (
        "## Training\n\n"
        "# Part A\n\n- bike 30min\n\n"
        "# Part B\n\n- bench press 3x8rep @80kg"
    )
    doc = parse_document(text)
    assert doc.workouts[0].workout_type is None


def test_session_explicit_type_kept():
    """Session with explicit [type] keeps it, no combination override."""
    text = (
        "## Training [wod]\n\n"
        "# Ride [bike]\n\n- bike 30min\n\n"
        "# Strength [strength]\n\n- bench press 3x8rep @80kg"
    )
    doc = parse_document(text)
    assert doc.workouts[0].workout_type == "wod"


def test_session_combination_roundtrip():
    """Combination is not written to .owf but re-inferred on re-parse."""
    from owf.serializer import dumps

    text = (
        "## Training\n\n"
        "# Ride [bike]\n\n- bike 30min\n\n"
        "# Strength [strength]\n\n- bench press 3x8rep @80kg"
    )
    doc1 = parse_document(text)
    assert doc1.workouts[0].workout_type == "combination"
    serialized = dumps(doc1)
    assert "[combination]" not in serialized
    doc2 = parse_document(serialized)
    assert doc2.workouts[0].workout_type == "combination"


def test_heading_with_rpe():
    text = "# Run [run] @RPE 7\n\n- run 5km\n"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.rpe == 7.0
    assert w.rir is None


def test_heading_with_rir():
    text = "# Strength [strength] @RIR 2\n\n- bench press 3x8rep @80kg\n"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.rir == 2
    assert w.rpe is None


def test_heading_with_both():
    text = "# Gym [strength] @RPE 8 @RIR 2\n\n- bench press 3x8rep @80kg\n"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.rpe == 8.0
    assert w.rir == 2


def test_heading_with_date_and_params():
    text = "# Gym [strength] (2025-02-27) @RIR 2 @RPE 7\n\n- bench press 3x8rep\n"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.date is not None
    assert w.date.date == "2025-02-27"
    assert w.rpe == 7.0
    assert w.rir == 2


def test_heading_params_dont_affect_steps():
    text = "# Gym [strength] @RIR 2\n\n- bench press 3x8rep @80kg rest:90s\n"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.rir == 2
    step = w.steps[0]
    assert isinstance(step, StrengthStep)
    # Step should have only the weight param, no RIR injected
    rir_params = [p for p in step.params if isinstance(p, RIRParam)]
    assert len(rir_params) == 0


def test_strength_with_percentage_weight():
    text = (
        "# Strength\n\n"
        "- bench press 3x8rep @80% of 1RM bench press rest:90s"
    )
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, StrengthStep)
    assert len(step.params) == 1
    assert isinstance(step.params[0], WeightParam)
