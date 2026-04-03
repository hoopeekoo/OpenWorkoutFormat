"""Tests for the step parser and full document parsing."""

import pytest

from owf.ast.base import Document, Program
from owf.ast.blocks import (
    AMRAP,
    ForTime,
    Interval,
)
from owf.ast.params import PercentOfParam, PowerParam, RIRParam
from owf.ast.steps import RepeatBlock, Step
from owf.errors import ParseError
from owf.parser.step_parser import parse_document


def test_empty_document():
    doc = parse_document("")
    assert isinstance(doc, Document)
    assert len(doc.workouts) == 0


def test_simple_endurance():
    """Single # heading produces a single workout."""
    text = (
        "# Easy Run [endurance]\n\n- Warmup 15min @Z1\n"
        "- Run 5km @4:30/km\n- Cooldown 10min @Z1"
    )
    doc = parse_document(text)
    assert len(doc.workouts) == 1
    w = doc.workouts[0]
    assert w.name == "Easy Run"
    assert w.sport_type == "endurance"
    assert len(w.steps) == 3
    assert isinstance(w.steps[0], Step)
    assert w.steps[0].action == "Warmup"
    assert w.steps[0].duration is not None
    assert w.steps[0].duration.seconds == 900


def test_endurance_with_distance():
    text = "# Run\n\n- Run 10km @4:30/km"
    doc = parse_document(text)
    w = doc.workouts[0]
    step = w.steps[0]
    assert isinstance(step, Step)
    assert step.distance is not None
    assert step.distance.value == 10
    assert step.distance.unit == "km"


def test_rest_step():
    text = "# Session\n\n- Rest 5min"
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, Step)
    assert step.action == "Rest"
    assert step.duration.seconds == 300


def test_repeat_block():
    text = (
        "# Intervals\n\n- 5x:\n"
        "  - Bike 5min @200W\n  - Recover 3min @Z1"
    )
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, RepeatBlock)
    assert step.count == 5
    assert len(step.steps) == 2
    assert isinstance(step.steps[0], Step)
    assert isinstance(step.steps[1], Step)


def test_strength_step():
    text = (
        "# Strength [strength]\n\n"
        "- Bench Press 3x8rep @80kg @rest 90s"
    )
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, Step)
    assert step.action == "Bench Press"
    assert step.sets == 3
    assert step.reps == 8
    assert step.rest is not None
    assert step.rest.seconds == 90


def test_repeat_with_superset_style():
    """superset 3x: parses as RepeatBlock with style."""
    text = (
        "# Strength\n\n- superset 3x:\n"
        "  - Bench Press 3x8rep @80kg @rest 90s\n"
        "  - Bent-Over Row 3x8rep @60kg @rest 90s"
    )
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, RepeatBlock)
    assert step.count == 3
    assert step.style == "superset"
    assert len(step.steps) == 2


def test_repeat_with_circuit_style():
    """circuit 3x: parses as RepeatBlock with style."""
    text = (
        "# Strength\n\n- circuit 3x:\n"
        "  - Kettlebell Swing 10rep @24kg\n"
        "  - Push-Up 15rep\n"
        "  - Air Squat 20rep"
    )
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, RepeatBlock)
    assert step.count == 3
    assert step.style == "circuit"
    assert len(step.steps) == 3


def test_repeat_with_style_metadata_fallback():
    """@ style: superset metadata still works as fallback."""
    text = (
        "# Strength\n\n- 3x:\n"
        "  @ style: superset\n"
        "  - Bench Press 3x8rep @80kg @rest 90s\n"
        "  - Bent-Over Row 3x8rep @60kg @rest 90s"
    )
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, RepeatBlock)
    assert step.count == 3
    assert step.style == "superset"
    assert len(step.steps) == 2


def test_interval_emom():
    """every 1min for 10min: parses as Interval."""
    text = "# WoD [mixed]\n\n- every 1min for 10min:\n  - Power Clean 3rep @70kg"
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, Interval)
    assert step.interval.seconds == 60
    assert step.duration.seconds == 600
    assert len(step.steps) == 1
    assert not step.is_alternating


def test_interval_alternating():
    """Interval with multiple children is alternating."""
    text = (
        "# WoD [mixed]\n\n- every 1min for 12min:\n"
        "  - Deadlift 5rep @100kg\n"
        "  - Strict Press 7rep @40kg"
    )
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, Interval)
    assert step.interval.seconds == 60
    assert step.duration.seconds == 720
    assert len(step.steps) == 2
    assert step.is_alternating


def test_custom_interval():
    text = (
        "# WoD [mixed]\n\n- every 2min for 20min:\n"
        "  - Wall Ball 15rep @9kg"
    )
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, Interval)
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
    step = doc.workouts[0].steps[0]
    assert isinstance(step, AMRAP)
    assert step.duration.seconds == 720
    assert len(step.steps) == 3


def test_for_time():
    text = (
        "# Murph [mixed]\n\n- for-time:\n"
        "  - Run 1mile\n  - Pull-Up 100rep\n"
        "  - Push-Up 200rep"
    )
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, ForTime)
    assert step.time_cap is None
    assert len(step.steps) == 3


def test_for_time_with_cap():
    text = "# WoD [mixed]\n\n- for-time 20min:\n  - Run 5km"
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, ForTime)
    assert step.time_cap is not None
    assert step.time_cap.seconds == 1200


def test_multiple_workouts():
    """Multiple # headings produce flat workouts in doc.workouts."""
    text = (
        "# Ride [endurance]\n\n- Bike 30min\n\n"
        "# Strength [strength]\n\n- Bench Press 3x8rep @80kg"
    )
    doc = parse_document(text)
    assert len(doc.workouts) == 2
    assert doc.workouts[0].name == "Ride"
    assert doc.workouts[0].sport_type == "endurance"
    assert doc.workouts[1].name == "Strength"
    assert doc.workouts[1].sport_type == "strength"


def test_metadata():
    text = (
        "@ FTP: 250W\n@ 1RM bench press: 100kg\n\n"
        "# Ride [endurance]\n\n- Bike 30min @80% FTP"
    )
    doc = parse_document(text)
    assert doc.metadata == {"FTP": "250W", "1RM bench press": "100kg"}
    assert len(doc.workouts) == 1


def test_description_on_workout():
    text = "# Ride [endurance]\n\n- Bike 30min @Z1\n\n> Great ride today."
    doc = parse_document(text)
    w = doc.workouts[0]
    step = w.steps[0]
    assert isinstance(step, Step)
    assert w.description is not None
    assert "Great ride today." in w.description


def test_endurance_with_power_param():
    text = "# Ride [endurance]\n\n- Bike 5min @200W"
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, Step)
    assert len(step.params) == 1
    assert isinstance(step.params[0], PowerParam)
    assert step.params[0].value == 200


def test_strength_with_rir():
    text = (
        "# Strength [strength]\n\n"
        "- Bench Press 3x8rep @80kg @RIR 2 @rest 90s"
    )
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, Step)
    rir_params = [p for p in step.params if isinstance(p, RIRParam)]
    assert len(rir_params) == 1
    assert rir_params[0].value == 2


def test_program_heading():
    """## headings produce a Program node."""
    text = "## My Program (4 weeks)\n\n--- Week 1 ---\n\n# Day 1\n\n- Run 5km"
    result = parse_document(text)
    assert isinstance(result, Program)
    assert result.name == "My Program"
    assert result.duration == "4 weeks"
    assert len(result.weeks) == 1
    assert result.weeks[0].name == "Week 1"
    assert len(result.weeks[0].workouts) == 1


def test_program_with_progression():
    """Program parses progression rules."""
    text = (
        "## Strength Block (4 weeks)\n"
        "@ progression: Bench Press +2.5kg/week\n"
        "@ progression: Back Squat +2.5kg/week\n\n"
        "--- Week 1 ---\n\n# Day 1\n\n- Bench Press 3x8rep @60kg"
    )
    result = parse_document(text)
    assert isinstance(result, Program)
    assert len(result.progression_rules) == 2
    assert result.progression_rules[0].action == "Bench Press"
    assert result.progression_rules[0].amount == 2.5
    assert result.progression_rules[0].unit == "kg"
    assert result.progression_rules[0].direction == "+"
    assert result.progression_rules[1].action == "Back Squat"


def test_program_with_deload():
    """Program parses deload rules."""
    text = (
        "## Block (4 weeks)\n"
        "@ deload: week 4 x0.8\n\n"
        "--- Week 1 ---\n\n# Day 1\n\n- Squat 3x5rep @100kg"
    )
    result = parse_document(text)
    assert isinstance(result, Program)
    assert result.deload_rule is not None
    assert result.deload_rule.week == 4
    assert result.deload_rule.multiplier == 0.8


def test_program_with_cycle():
    """Program parses cycle flag."""
    text = (
        "## PPL (rotating)\n"
        "@ cycle: true\n\n"
        "--- Cycle ---\n\n# Push\n\n- Bench Press 3x8rep @80kg"
    )
    result = parse_document(text)
    assert isinstance(result, Program)
    assert result.is_cycle is True


def test_program_multiple_weeks():
    """Program with multiple weeks."""
    text = (
        "## Block (3 weeks)\n\n"
        "--- Week 1 ---\n@ template: true\n\n# Day 1\n\n- Squat 3x5rep @100kg\n\n"
        "--- Week 2 ---\n\n"
        "--- Week 3 ---\n@ deload: true\n"
    )
    result = parse_document(text)
    assert isinstance(result, Program)
    assert len(result.weeks) == 3
    assert result.weeks[0].name == "Week 1"
    assert result.weeks[0].is_template is True
    assert result.weeks[1].name == "Week 2"
    assert result.weeks[2].name == "Week 3"
    assert result.weeks[2].is_deload is True


def test_sport_type_parsed():
    """Bracket tags set sport_type."""
    text = "# Morning Run [Trail Running]\n\n- Run 5km\n"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.sport_type == "Trail Running"


def test_sport_type_on_workouts():
    """Multiple workouts can each have sport_type."""
    text = (
        "# Ride [Gravel Cycling]\n\n- Bike 30min\n\n"
        "# Gym [Strength Training]\n\n- Deadlift 3x5rep @100kg"
    )
    doc = parse_document(text)
    assert doc.workouts[0].sport_type == "Gravel Cycling"
    assert doc.workouts[1].sport_type == "Strength Training"


def test_legacy_tags_become_sport_type():
    """Legacy tags [endurance] etc. now set sport_type like any other tag."""
    text = "# Run [endurance]\n\n- Run 5km\n"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.sport_type == "endurance"


def test_sport_type_roundtrip():
    """Sport type round-trips through serialize -> parse."""
    from owf.serializer import dumps

    text = "# Morning Run [Trail Running]\n\n- Run 5km\n"
    doc1 = parse_document(text)
    serialized = dumps(doc1)
    assert "[Trail Running]" in serialized
    doc2 = parse_document(serialized)
    assert doc2.workouts[0].sport_type == "Trail Running"


def test_sport_type_with_date():
    """Sport type and date can coexist on a heading."""
    text = "# Run [Trail Running] (2025-02-27)\n\n- Run 5km\n"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.sport_type == "Trail Running"
    assert w.date is not None
    assert w.date.date == "2025-02-27"


def test_sport_type_with_params():
    """Sport type, date, RPE, and RIR all coexist."""
    text = "# Gym [Strength Training] (2025-02-27) @RPE 8 @RIR 2\n\n- Squat 3x5rep\n"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.sport_type == "Strength Training"
    assert w.date.date == "2025-02-27"
    assert w.rpe == 8
    assert w.rir == 2


def test_sport_type_unknown_accepted():
    """Parser accepts any string in brackets, even unknown ones."""
    text = "# Fun [Underwater Basket Weaving]\n\n- Swim 30min\n"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.sport_type == "Underwater Basket Weaving"


def test_unified_step_serialization():
    """Serializer handles unified Step for both endurance and strength actions."""
    from owf.serializer import dumps

    text = "# Workout\n\n- Run 5km\n- Bench Press 3x8rep @80kg\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "- Run 5km" in result
    assert "- Bench Press 3x8rep @80kg" in result


def test_unified_step_roundtrip():
    """Unified Step output re-parses correctly."""
    from owf.serializer import dumps

    text = "# Workout\n\n- Run 5km\n- Bench Press 3x8rep @80kg\n"
    doc1 = parse_document(text)
    serialized = dumps(doc1)
    doc2 = parse_document(serialized)
    assert doc2.workouts[0].steps[0].action == "Run"
    assert doc2.workouts[0].steps[1].action == "Bench Press"


def test_heading_with_rpe():
    text = "# Run [endurance] @RPE 7\n\n- Run 5km\n"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.rpe == 7
    assert w.rir is None


def test_heading_with_rir():
    text = "# Strength [strength] @RIR 2\n\n- Bench Press 3x8rep @80kg\n"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.rir == 2
    assert w.rpe is None


def test_heading_with_both():
    text = "# Gym [strength] @RPE 8 @RIR 2\n\n- Bench Press 3x8rep @80kg\n"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.rpe == 8
    assert w.rir == 2


def test_heading_with_date_and_params():
    text = "# Gym [strength] (2025-02-27) @RIR 2 @RPE 7\n\n- Bench Press 3x8rep\n"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.date is not None
    assert w.date.date == "2025-02-27"
    assert w.rpe == 7
    assert w.rir == 2


def test_heading_params_dont_affect_steps():
    text = "# Gym [strength] @RIR 2\n\n- Bench Press 3x8rep @80kg @rest 90s\n"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.rir == 2
    step = w.steps[0]
    assert isinstance(step, Step)
    rir_params = [p for p in step.params if isinstance(p, RIRParam)]
    assert len(rir_params) == 0


def test_strength_with_percentage_weight():
    text = (
        "# Strength\n\n"
        "- Bench Press 3x8rep @80% 1RM bench press @rest 90s"
    )
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, Step)
    assert len(step.params) == 1
    assert isinstance(step.params[0], PercentOfParam)
    assert step.params[0].percent == 80
    assert step.params[0].variable == "1RM bench press"


# -- Parametrized test for endurance actions (parse + round-trip) --

_ACTIONS = [
    "Skate-Ski",
    "Classic-Ski",
    "Alpine-Ski",
    "Snowboard",
    "Snowshoe",
    "Skate",
    "Paddle",
    "Kayak",
    "Surf",
    "Climb",
    "Elliptical",
    "Stairs",
    "Jumprope",
    "Ebike",
    "Other",
]


@pytest.mark.parametrize("action", _ACTIONS)
def test_action_parse(action: str) -> None:
    text = f"# Workout\n\n- {action} 30min @Z2"
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, Step)
    assert step.action == action
    assert step.duration is not None
    assert step.duration.seconds == 1800


@pytest.mark.parametrize("action", _ACTIONS)
def test_action_roundtrip(action: str) -> None:
    from owf.serializer import dumps

    text = f"# Workout\n\n- {action} 30min @Z2"
    doc1 = parse_document(text)
    serialized = dumps(doc1)
    doc2 = parse_document(serialized)
    step1 = doc1.workouts[0].steps[0]
    step2 = doc2.workouts[0].steps[0]
    assert isinstance(step1, Step)
    assert isinstance(step2, Step)
    assert step1.action == step2.action
    assert step1.duration == step2.duration


def test_date_on_heading():
    """Dates are allowed directly on # headings."""
    text = "# Morning Run [endurance] (2025-02-27)\n\n- Run 5km"
    doc = parse_document(text)
    w = doc.workouts[0]
    assert w.date is not None
    assert w.date.date == "2025-02-27"


def test_mixed_field_step():
    """A step can have any combination of fields."""
    text = "# Workout\n\n- Sled Push 4rep 50m @100kg"
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, Step)
    assert step.action == "Sled Push"
    assert step.reps == 4
    assert step.distance is not None
    assert step.distance.value == 50
    assert step.distance.unit == "m"


def test_step_with_duration_and_rest():
    """Unified step with duration and rest."""
    text = "# Workout\n\n- Plank 60s @rest 30s"
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, Step)
    assert step.action == "Plank"
    assert step.duration is not None
    assert step.duration.seconds == 60
    assert step.rest is not None
    assert step.rest.seconds == 30


def test_step_with_sets_reps_and_distance():
    """Unified step with sets x reps and distance."""
    text = "# Workout\n\n- Sled Push 4x1rep 50m @100kg"
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, Step)
    assert step.action == "Sled Push"
    assert step.sets == 4
    assert step.reps == 1
    assert step.distance is not None
    assert step.distance.value == 50


def test_lowercase_action_rejected():
    """Lowercase actions raise ParseError — Title Case required."""
    with pytest.raises(ParseError, match="Title Case"):
        parse_document("# Test\n\n- run 5km")


# ===== Compound durations in containers =====


def test_amrap_compound_duration():
    """amrap 1h30min: parses with compound duration."""
    text = "# WoD\n\n- amrap 1h30min:\n  - Burpee 10rep\n  - Pull-Up 5rep"
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, AMRAP)
    assert step.duration.seconds == 5400


def test_interval_compound_duration():
    """every 2min for 1h30min: parses as Interval with compound duration."""
    text = "# WoD\n\n- every 2min for 1h30min:\n  - Burpee 10rep"
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, Interval)
    assert step.interval.seconds == 120
    assert step.duration.seconds == 5400


def test_for_time_compound_duration():
    """for-time 1h30min: parses as ForTime with compound time cap."""
    text = "# WoD\n\n- for-time 1h30min:\n  - Run 10km"
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, ForTime)
    assert step.time_cap is not None
    assert step.time_cap.seconds == 5400


# ===== NxDuration and NxDistance parsing =====


def test_nx_duration_plank():
    """- Plank 3x60s parses as sets=3, duration=60s."""
    text = "# Gym\n\n- Plank 3x60s @rest 30s"
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, Step)
    assert step.action == "Plank"
    assert step.sets == 3
    assert step.duration is not None
    assert step.duration.seconds == 60
    assert step.reps is None
    assert step.rest is not None
    assert step.rest.seconds == 30


def test_nx_duration_run():
    """- Run 3x10min parses as sets=3, duration=600s."""
    text = "# Run\n\n- Run 3x10min @Z3"
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, Step)
    assert step.action == "Run"
    assert step.sets == 3
    assert step.duration is not None
    assert step.duration.seconds == 600
    assert step.reps is None


def test_nx_distance_sled():
    """- Sled Push 4x50m parses as sets=4, distance=50m."""
    text = "# Gym\n\n- Sled Push 4x50m @100kg"
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, Step)
    assert step.action == "Sled Push"
    assert step.sets == 4
    assert step.distance is not None
    assert step.distance.value == 50
    assert step.distance.unit == "m"
    assert step.reps is None


def test_nx_distance_row():
    """- Row 4x500m parses as sets=4, distance=500m."""
    text = "# Row\n\n- Row 4x500m @1:45/500m @rest 90s"
    doc = parse_document(text)
    step = doc.workouts[0].steps[0]
    assert isinstance(step, Step)
    assert step.action == "Row"
    assert step.sets == 4
    assert step.distance is not None
    assert step.distance.value == 500
    assert step.distance.unit == "m"
    assert step.rest is not None
    assert step.rest.seconds == 90
