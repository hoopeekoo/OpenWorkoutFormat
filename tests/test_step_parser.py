"""Tests for the step parser and full document parsing."""

import pytest

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
from owf.ast.params import PercentOfParam, PowerParam, RIRParam
from owf.ast.steps import EnduranceStep, RepeatStep, RestStep, StrengthStep
from owf.errors import ParseError
from owf.parser.step_parser import parse_document


def test_empty_document():
    doc = parse_document("")
    assert isinstance(doc, Document)
    assert len(doc.workouts) == 0


def test_simple_endurance():
    """Flat # headings auto-wrapped in session."""
    text = (
        "# Easy Run [endurance]\n\n- warmup 15min @Z1\n"
        "- run 5km @4:30/km\n- cooldown 10min @Z1"
    )
    doc = parse_document(text)
    # Auto-wrapped in implicit session
    assert len(doc.workouts) == 1
    session = doc.workouts[0]
    assert session.name == ""  # implicit session
    # Single child workout
    assert len(session.steps) == 1
    w = session.steps[0]
    assert isinstance(w, Workout)
    assert w.name == "Easy Run"
    assert w.sport_type == "endurance"
    assert len(w.steps) == 3
    assert isinstance(w.steps[0], EnduranceStep)
    assert w.steps[0].action == "warmup"
    assert w.steps[0].duration is not None
    assert w.steps[0].duration.seconds == 900


def test_endurance_with_distance():
    text = "# Run\n\n- run 10km @4:30/km"
    doc = parse_document(text)
    w = doc.workouts[0].steps[0]
    assert isinstance(w, Workout)
    step = w.steps[0]
    assert isinstance(step, EnduranceStep)
    assert step.distance is not None
    assert step.distance.value == 10
    assert step.distance.unit == "km"


def test_rest_step():
    text = "# Session\n\n- rest 5min"
    doc = parse_document(text)
    step = doc.workouts[0].steps[0].steps[0]
    assert isinstance(step, RestStep)
    assert step.duration.seconds == 300


def test_repeat_block():
    text = (
        "# Intervals\n\n- 5x:\n"
        "  - bike 5min @200W\n  - recover 3min @Z1"
    )
    doc = parse_document(text)
    step = doc.workouts[0].steps[0].steps[0]
    assert isinstance(step, RepeatStep)
    assert step.count == 5
    assert len(step.steps) == 2
    assert isinstance(step.steps[0], EnduranceStep)
    assert isinstance(step.steps[1], EnduranceStep)


def test_strength_step():
    text = (
        "# Strength [strength]\n\n"
        "- Bench Press 3x8rep @80kg @rest 90s"
    )
    doc = parse_document(text)
    step = doc.workouts[0].steps[0].steps[0]
    assert isinstance(step, StrengthStep)
    assert step.exercise == "Bench Press"
    assert step.sets == 3
    assert step.reps == 8
    assert step.rest is not None
    assert step.rest.seconds == 90


def test_superset():
    text = (
        "# Strength\n\n- 3x superset:\n"
        "  - Bench Press 3x8rep @80kg @rest 90s\n"
        "  - Bent-Over Row 3x8rep @60kg @rest 90s"
    )
    doc = parse_document(text)
    step = doc.workouts[0].steps[0].steps[0]
    assert isinstance(step, Superset)
    assert step.count == 3
    assert len(step.steps) == 2


def test_circuit():
    text = (
        "# Strength\n\n- 3x circuit:\n"
        "  - Kettlebell Swing 10rep @24kg\n"
        "  - Push-Up 15rep\n"
        "  - Air Squat 20rep"
    )
    doc = parse_document(text)
    step = doc.workouts[0].steps[0].steps[0]
    assert isinstance(step, Circuit)
    assert step.count == 3
    assert len(step.steps) == 3


def test_emom():
    text = "# WoD [mixed]\n\n- emom 10min:\n  - Power Clean 3rep @70kg"
    doc = parse_document(text)
    step = doc.workouts[0].steps[0].steps[0]
    assert isinstance(step, EMOM)
    assert step.duration.seconds == 600
    assert len(step.steps) == 1


def test_emom_alternating():
    text = (
        "# WoD [mixed]\n\n- emom 12min alternating:\n"
        "  - Deadlift 5rep @100kg\n"
        "  - Strict Press 7rep @40kg"
    )
    doc = parse_document(text)
    step = doc.workouts[0].steps[0].steps[0]
    assert isinstance(step, AlternatingEMOM)
    assert step.duration.seconds == 720
    assert len(step.steps) == 2


def test_custom_interval():
    text = (
        "# WoD [mixed]\n\n- every 2min for 20min:\n"
        "  - Wall Ball 15rep @9kg"
    )
    doc = parse_document(text)
    step = doc.workouts[0].steps[0].steps[0]
    assert isinstance(step, CustomInterval)
    assert step.interval.seconds == 120
    assert step.duration.seconds == 1200
    assert len(step.steps) == 1


def test_amrap():
    text = (
        "# Metcon [mixed]\n\n- amrap 12min:\n"
        "  - Pull-Up 5rep\n  - Push-Up 10rep\n"
        "  - Air Squat 15rep"
    )
    doc = parse_document(text)
    step = doc.workouts[0].steps[0].steps[0]
    assert isinstance(step, AMRAP)
    assert step.duration.seconds == 720
    assert len(step.steps) == 3


def test_for_time():
    text = (
        "# Murph [mixed]\n\n- for-time:\n"
        "  - run 1mile\n  - Pull-Up 100rep\n"
        "  - Push-Up 200rep"
    )
    doc = parse_document(text)
    step = doc.workouts[0].steps[0].steps[0]
    assert isinstance(step, ForTime)
    assert step.time_cap is None
    assert len(step.steps) == 3


def test_for_time_with_cap():
    text = "# WoD [mixed]\n\n- for-time 20min:\n  - run 5km"
    doc = parse_document(text)
    step = doc.workouts[0].steps[0].steps[0]
    assert isinstance(step, ForTime)
    assert step.time_cap is not None
    assert step.time_cap.seconds == 1200


def test_session_with_child_workouts():
    text = (
        "## Session\n\n- warmup 10min @Z1\n\n"
        "# Ride [endurance]\n\n- bike 30min\n\n"
        "# Strength [strength]\n\n- Bench Press 3x8rep @80kg"
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
    assert session.steps[1].sport_type == "endurance"
    assert isinstance(session.steps[2], Workout)
    assert session.steps[2].name == "Strength"
    assert session.steps[2].sport_type == "strength"


def test_metadata():
    text = (
        "@ FTP: 250W\n@ 1RM bench press: 100kg\n\n"
        "## Ride [endurance]\n\n- bike 30min @80% of FTP"
    )
    doc = parse_document(text)
    assert doc.metadata == {"FTP": "250W", "1RM bench press": "100kg"}
    assert len(doc.workouts) == 1


def test_notes_on_workout():
    text = "## Ride [endurance]\n\n- bike 30min @Z1\n\n> Great ride today."
    doc = parse_document(text)
    w = doc.workouts[0]
    step = w.steps[0]
    assert isinstance(step, EnduranceStep)
    assert "Great ride today." in step.notes or "Great ride today." in w.notes


def test_multiple_workouts_auto_wrapped():
    """Multiple flat # workouts are auto-wrapped in a single session."""
    text = (
        "# Ride [endurance]\n\n- bike 30min\n\n"
        "# Strength [strength]\n\n- Bench Press 3x8rep @80kg"
    )
    doc = parse_document(text)
    # Auto-wrapped in one implicit session
    assert len(doc.workouts) == 1
    session = doc.workouts[0]
    assert session.name == ""
    assert session.sport_type is None  # no mixed inference in parser
    children = [s for s in session.steps if isinstance(s, Workout)]
    assert len(children) == 2
    assert children[0].name == "Ride"
    assert children[1].name == "Strength"


def test_endurance_with_power_param():
    text = "## Ride [endurance]\n\n- bike 5min @200W"
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, EnduranceStep)
    assert len(step.params) == 1
    assert isinstance(step.params[0], PowerParam)
    assert step.params[0].value == 200


def test_strength_with_rir():
    text = (
        "## Strength [strength]\n\n"
        "- Bench Press 3x8rep @80kg @RIR 2 @rest 90s"
    )
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, StrengthStep)
    rir_params = [p for p in step.params if isinstance(p, RIRParam)]
    assert len(rir_params) == 1
    assert rir_params[0].value == 2


def test_session_no_mixed_inference():
    """Parser does not infer mixed — that's app-side logic."""
    text = (
        "## Training\n\n"
        "# Ride [endurance]\n\n- bike 30min\n\n"
        "# Strength [strength]\n\n- Bench Press 3x8rep @80kg"
    )
    doc = parse_document(text)
    assert doc.workouts[0].sport_type is None  # no inference


def test_session_single_child_type():
    """Session where all children have the same type."""
    text = (
        "## Training\n\n"
        "# Ride A [endurance]\n\n- bike 30min\n\n"
        "# Ride B [endurance]\n\n- bike 20min"
    )
    doc = parse_document(text)
    assert doc.workouts[0].sport_type is None


def test_session_no_child_types():
    """Session with children that have no type."""
    text = (
        "## Training\n\n"
        "# Part A\n\n- bike 30min\n\n"
        "# Part B\n\n- Bench Press 3x8rep @80kg"
    )
    doc = parse_document(text)
    assert doc.workouts[0].sport_type is None


def test_session_explicit_type_kept():
    """Session with explicit [type] keeps it as sport_type."""
    text = (
        "## Training [mixed]\n\n"
        "# Ride [endurance]\n\n- bike 30min\n\n"
        "# Strength [strength]\n\n- Bench Press 3x8rep @80kg"
    )
    doc = parse_document(text)
    assert doc.workouts[0].sport_type == "mixed"


def test_sport_type_parsed():
    """Bracket tags set sport_type."""
    text = "## Morning Run [Trail Running]\n\n- run 5km\n"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.sport_type == "Trail Running"


def test_sport_type_on_child():
    """Child workouts can also have sport_type."""
    text = (
        "## Session\n\n"
        "# Ride [Gravel Cycling]\n\n- bike 30min\n\n"
        "# Gym [Strength Training]\n\n- Deadlift 3x5rep @100kg"
    )
    doc = parse_document(text)
    ride = doc.workouts[0].steps[0]
    gym = doc.workouts[0].steps[1]
    assert ride.sport_type == "Gravel Cycling"
    assert gym.sport_type == "Strength Training"


def test_legacy_tags_become_sport_type():
    """Legacy tags [endurance] etc. now set sport_type like any other tag."""
    text = "## Run [endurance]\n\n- run 5km\n"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.sport_type == "endurance"


def test_sport_type_roundtrip():
    """Sport type round-trips through serialize → parse."""
    from owf.serializer import dumps

    text = "## Morning Run [Trail Running]\n\n- run 5km\n"
    doc1 = parse_document(text)
    serialized = dumps(doc1)
    assert "[Trail Running]" in serialized
    doc2 = parse_document(serialized)
    assert doc2.workouts[0].sport_type == "Trail Running"


def test_sport_type_with_date():
    """Sport type and date can coexist on a heading."""
    text = "## Run [Trail Running] (2025-02-27)\n\n- run 5km\n"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.sport_type == "Trail Running"
    assert w.date is not None
    assert w.date.date == "2025-02-27"


def test_sport_type_with_params():
    """Sport type, date, RPE, and RIR all coexist."""
    text = "## Gym [Strength Training] (2025-02-27) @RPE 8 @RIR 2\n\n- Squat 3x5rep\n"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.sport_type == "Strength Training"
    assert w.date.date == "2025-02-27"
    assert w.rpe == 8
    assert w.rir == 2


def test_sport_type_unknown_accepted():
    """Parser accepts any string in brackets, even unknown ones."""
    text = "## Fun [Underwater Basket Weaving]\n\n- swim 30min\n"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.sport_type == "Underwater Basket Weaving"


def test_casing_serialization():
    """Serializer preserves lowercase endurance actions and Title Case exercises."""
    from owf.serializer import dumps

    text = "## Workout\n\n- run 5km\n- Bench Press 3x8rep @80kg\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "- run 5km" in result
    assert "- Bench Press 3x8rep @80kg" in result


def test_casing_roundtrip():
    """Casing-based output re-parses correctly."""
    from owf.serializer import dumps

    text = "## Workout\n\n- run 5km\n- Bench Press 3x8rep @80kg\n"
    doc1 = parse_document(text)
    serialized = dumps(doc1)
    doc2 = parse_document(serialized)
    # Endurance action stays lowercase
    assert doc2.workouts[0].steps[0].action == "run"
    # Strength exercise stays Title Case
    assert doc2.workouts[0].steps[1].exercise == "Bench Press"


def test_heading_with_rpe():
    text = "## Run [endurance] @RPE 7\n\n- run 5km\n"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.rpe == 7
    assert w.rir is None


def test_heading_with_rir():
    text = "## Strength [strength] @RIR 2\n\n- Bench Press 3x8rep @80kg\n"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.rir == 2
    assert w.rpe is None


def test_heading_with_both():
    text = "## Gym [strength] @RPE 8 @RIR 2\n\n- Bench Press 3x8rep @80kg\n"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.rpe == 8
    assert w.rir == 2


def test_heading_with_date_and_params():
    text = "## Gym [strength] (2025-02-27) @RIR 2 @RPE 7\n\n- Bench Press 3x8rep\n"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.date is not None
    assert w.date.date == "2025-02-27"
    assert w.rpe == 7
    assert w.rir == 2


def test_heading_params_dont_affect_steps():
    text = "## Gym [strength] @RIR 2\n\n- Bench Press 3x8rep @80kg @rest 90s\n"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.rir == 2
    step = w.steps[0]
    assert isinstance(step, StrengthStep)
    rir_params = [p for p in step.params if isinstance(p, RIRParam)]
    assert len(rir_params) == 0


def test_strength_with_percentage_weight():
    text = (
        "## Strength\n\n"
        "- Bench Press 3x8rep @80% of 1RM bench press @rest 90s"
    )
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, StrengthStep)
    assert len(step.params) == 1
    assert isinstance(step.params[0], PercentOfParam)
    assert step.params[0].percent == 80
    assert step.params[0].variable == "1RM bench press"


# -- Parametrized test for all new endurance actions (parse + round-trip) --

_NEW_ACTIONS = [
    "skate-ski",
    "classic-ski",
    "alpine-ski",
    "snowboard",
    "snowshoe",
    "skate",
    "paddle",
    "kayak",
    "surf",
    "climb",
    "elliptical",
    "stairs",
    "jumprope",
    "ebike",
    "other",
]


@pytest.mark.parametrize("action", _NEW_ACTIONS)
def test_new_endurance_action_parse(action: str) -> None:
    text = f"## Workout\n\n- {action} 30min @Z2"
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, EnduranceStep)
    assert step.action == action
    assert step.duration is not None
    assert step.duration.seconds == 1800


@pytest.mark.parametrize("action", _NEW_ACTIONS)
def test_new_endurance_action_roundtrip(action: str) -> None:
    from owf.serializer import dumps

    text = f"## Workout\n\n- {action} 30min @Z2"
    doc1 = parse_document(text)
    serialized = dumps(doc1)
    doc2 = parse_document(serialized)
    step1 = doc1.workouts[0].steps[0]
    step2 = doc2.workouts[0].steps[0]
    assert isinstance(step1, EnduranceStep)
    assert isinstance(step2, EnduranceStep)
    assert step1.action == step2.action
    assert step1.duration == step2.duration


def test_flat_headings_auto_wrapped_in_session():
    """Flat # headings are wrapped in an implicit unnamed session."""
    text = "# Run [endurance]\n\n- run 5km"
    doc = parse_document(text)
    assert len(doc.workouts) == 1
    session = doc.workouts[0]
    assert session.name == ""
    assert len(session.steps) == 1
    child = session.steps[0]
    assert isinstance(child, Workout)
    assert child.name == "Run"


def test_dates_rejected_on_child_headings():
    """Dates on # child headings inside ## sessions raise ParseError."""
    text = (
        "## Session\n\n"
        "# Ride [endurance] (2025-02-27)\n\n- bike 30min"
    )
    with pytest.raises(ParseError, match="Dates are only allowed on session"):
        parse_document(text)


def test_single_flat_date_lifted_to_session():
    """Single # workout with date: date is lifted to the implicit session."""
    text = "# Morning Run [endurance] (2025-02-27)\n\n- run 5km"
    doc = parse_document(text)
    session = doc.workouts[0]
    assert session.date is not None
    assert session.date.date == "2025-02-27"
    child = session.steps[0]
    assert isinstance(child, Workout)
    assert child.date is None  # lifted to session
