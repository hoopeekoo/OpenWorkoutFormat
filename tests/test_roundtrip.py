"""Round-trip tests: parse -> serialize -> parse should produce equivalent AST."""

from owf.ast.base import Program
from owf.parser.step_parser import parse_document
from owf.serializer import dumps


def _roundtrip(text: str) -> None:
    """Parse text, serialize, re-parse, and verify equivalence."""
    doc1 = parse_document(text)
    serialized = dumps(doc1)
    doc2 = parse_document(serialized)

    if isinstance(doc1, Program):
        assert isinstance(doc2, Program)
        assert doc1.name == doc2.name
        assert len(doc1.weeks) == len(doc2.weeks)
        return

    # Compare structurally (ignoring spans)
    assert len(doc1.workouts) == len(doc2.workouts)
    for w1, w2 in zip(doc1.workouts, doc2.workouts):
        assert w1.name == w2.name
        assert w1.sport_type == w2.sport_type
        assert w1.description == w2.description
        assert len(w1.steps) == len(w2.steps)


def test_roundtrip_endurance():
    _roundtrip(
        "# Run [run]\n\n- Warmup 15min @Z1\n"
        "- Run 5km @4:30/km\n- Cooldown 10min @Z1"
    )


def test_roundtrip_strength():
    _roundtrip(
        "# Strength [strength]\n\n"
        "- Bench Press 3x8rep @80kg @rest 90s\n"
        "- Bicep Curl 3x12rep @15kg @rest 60s"
    )


def test_roundtrip_intervals():
    _roundtrip(
        "# Intervals\n\n- 5x:\n"
        "  - Bike 5min @200W\n  - Recover 3min @Z1"
    )


def test_roundtrip_interval():
    _roundtrip(
        "# WoD [wod]\n\n- every 1min for 10min:\n"
        "  - Power Clean 3rep @70kg"
    )


def test_roundtrip_amrap():
    _roundtrip(
        "# Metcon [wod]\n\n- amrap 12min:\n"
        "  - Pull-Up 5rep\n  - Push-Up 10rep\n"
        "  - Air Squat 15rep"
    )


def test_roundtrip_for_time():
    _roundtrip(
        "# Murph [wod]\n\n- for-time:\n"
        "  - Run 1mile\n  - Pull-Up 100rep\n"
        "  - Push-Up 200rep"
    )


def test_roundtrip_metadata():
    _roundtrip(
        "@ FTP: 250W\n\n"
        "# Ride [bike]\n\n- Bike 30min @200W"
    )


def test_roundtrip_multiple_workouts():
    _roundtrip(
        "# Ride [bike]\n\n- Bike 30min\n\n"
        "# Strength [strength]\n\n- Bench Press 3x8rep @80kg"
    )


def test_roundtrip_superset_style():
    _roundtrip(
        "# Strength\n\n- superset 3x:\n"
        "  - Bench Press 3x8rep @80kg @rest 90s\n"
        "  - Bent-Over Row 3x8rep @60kg @rest 90s"
    )


def test_roundtrip_circuit_style():
    _roundtrip(
        "# Strength\n\n- circuit 3x:\n"
        "  - Kettlebell Swing 10rep @24kg\n"
        "  - Push-Up 15rep\n"
        "  - Air Squat 20rep"
    )


def test_roundtrip_percent_of():
    _roundtrip("# Ride\n\n- Bike 30min @80% FTP")


def test_roundtrip_bodyweight_plus():
    _roundtrip("# Gym\n\n- Dip 3x8rep @bodyweight + 20kg @rest 90s")


def test_roundtrip_zone():
    _roundtrip("# Run\n\n- Run 10min @Z2\n- Recover 5min @Z1")


def test_roundtrip_heart_rate():
    _roundtrip("# Run\n\n- Run 10min @140bpm")


def test_roundtrip_program():
    _roundtrip(
        "## My Program (4 weeks)\n"
        "@ author: Coach\n\n"
        "--- Week 1 ---\n"
        "@ template: true\n\n"
        "# Day 1\n\n- Bench Press 3x8rep @60kg\n\n"
        "--- Week 2 ---\n"
    )


# ===== New feature round-trip tests =====


def test_roundtrip_zone_metric():
    _roundtrip("# Ride\n\n- Bike 20min @Z2:power\n- Run 10min @Z3:hr")


def test_roundtrip_typed_percent_ftp():
    _roundtrip("# Ride\n\n- Bike 10min @95%FTP")


def test_roundtrip_typed_percent_lthr():
    _roundtrip("# Run\n\n- Run 30min @88%LTHR")


def test_roundtrip_typed_percent_maxhr():
    _roundtrip("# Run\n\n- Run 20min @92%maxHR")


def test_roundtrip_typed_percent_tp():
    _roundtrip("# Swim\n\n- Swim 8x100m @90%TP")


def test_roundtrip_typed_percent_1rm():
    _roundtrip("# Gym\n\n- Bench Press 3x5rep @85%1RM")


def test_roundtrip_tempo():
    _roundtrip("# Gym\n\n- Back Squat 4x6rep @120kg @tempo 31X0 @rest 2min")


def test_roundtrip_set_type_warmup():
    _roundtrip("# Gym\n\n- Bench Press 3x8rep @60kg @warmup @rest 90s")


def test_roundtrip_set_type_drop():
    _roundtrip("# Gym\n\n- Bench Press 1x8rep @70kg @drop @rest 30s")


def test_roundtrip_set_type_rest_pause():
    _roundtrip("# Gym\n\n- Bench Press 1x12rep @60kg @rest-pause")


def test_roundtrip_set_type_myo_rep():
    _roundtrip("# Gym\n\n- Leg Press 1x20rep @myo-rep")


def test_roundtrip_pace_500m():
    _roundtrip("# Row\n\n- Row 4x500m @1:45/500m @rest 90s")


def test_roundtrip_pace_100m():
    _roundtrip("# Swim\n\n- Swim 8x100m @1:32/100m @rest 20s")


def test_roundtrip_complex_strength():
    """Full strength step with all new features."""
    _roundtrip(
        "# Gym\n\n"
        "- Bench Press 3x8rep @80kg @tempo 31X0 @warmup @RIR 3 @rest 2min"
    )


def test_roundtrip_description():
    """Workout description survives a round-trip."""
    text = "# Run [Running]\n\n> Great workout today.\n> Felt strong.\n\n- Run 5km\n"
    doc1 = parse_document(text)
    assert doc1.workouts[0].description == "Great workout today.\nFelt strong."
    serialized = dumps(doc1)
    doc2 = parse_document(serialized)
    assert doc2.workouts[0].description == doc1.workouts[0].description


# ===== Container metadata round-trip =====


def test_roundtrip_container_metadata():
    """@ rest_between_rounds on a RepeatBlock survives round-trip."""
    from owf.ast.steps import RepeatBlock

    text = (
        "# Strength\n\n- circuit 4x:\n"
        "  @ rest_between_rounds: 90s\n"
        "  - Kettlebell Swing 15rep @24kg\n"
        "  - Push-Up 15rep\n"
    )
    doc1 = parse_document(text)
    block1 = doc1.workouts[0].steps[0]
    assert isinstance(block1, RepeatBlock)
    assert block1.metadata["rest_between_rounds"] == "90s"

    serialized = dumps(doc1)
    doc2 = parse_document(serialized)
    block2 = doc2.workouts[0].steps[0]
    assert isinstance(block2, RepeatBlock)
    assert block2.metadata["rest_between_rounds"] == "90s"


# ===== Step-level metadata round-trip =====


def test_roundtrip_step_metadata():
    """@ unilateral: true on a Step survives round-trip."""
    from owf.ast.steps import Step

    text = (
        "# Strength\n\n"
        "- Dumbbell Row 3x8rep @24kg @rest 90s\n"
        "  @ unilateral: true\n"
    )
    doc1 = parse_document(text)
    step1 = doc1.workouts[0].steps[0]
    assert isinstance(step1, Step)
    assert step1.metadata["unilateral"] == "true"

    serialized = dumps(doc1)
    doc2 = parse_document(serialized)
    step2 = doc2.workouts[0].steps[0]
    assert isinstance(step2, Step)
    assert step2.metadata["unilateral"] == "true"


# ===== Deep program round-trip =====


def test_roundtrip_program_deep():
    """Program round-trip preserves week contents, progression, and deload."""
    from owf.ast.steps import Step

    text = (
        "## Strength Block (4 weeks)\n"
        "@ author: Coach\n"
        "@ progression: Bench Press +2.5kg/week\n"
        "@ deload: week 4 x0.8\n\n"
        "--- Week 1 ---\n"
        "@ template: true\n\n"
        "# Day 1 [Strength Training]\n\n"
        "- Bench Press 3x8rep @60kg @rest 90s\n"
        "- Pull-Up 3x8rep\n\n"
        "--- Week 2 ---\n"
    )
    doc1 = parse_document(text)
    assert isinstance(doc1, Program)
    serialized = dumps(doc1)
    doc2 = parse_document(serialized)
    assert isinstance(doc2, Program)

    # Name and duration
    assert doc2.name == doc1.name
    assert doc2.duration == doc1.duration

    # Week count and names
    assert len(doc2.weeks) == len(doc1.weeks)
    assert doc2.weeks[0].name == "Week 1"
    assert doc2.weeks[0].is_template is True
    assert doc2.weeks[1].name == "Week 2"

    # Workout content in week 1
    assert len(doc2.weeks[0].workouts) == 1
    w = doc2.weeks[0].workouts[0]
    assert w.name == "Day 1"
    assert w.sport_type == "Strength Training"
    assert len(w.steps) == 2
    step = w.steps[0]
    assert isinstance(step, Step)
    assert step.action == "Bench Press"
    assert step.sets == 3
    assert step.reps == 8

    # Progression rules
    assert len(doc2.progression_rules) == 1
    assert doc2.progression_rules[0].action == "Bench Press"
    assert doc2.progression_rules[0].amount == 2.5
    assert doc2.progression_rules[0].unit == "kg"

    # Deload rule
    assert doc2.deload_rule is not None
    assert doc2.deload_rule.week == 4
    assert doc2.deload_rule.multiplier == 0.8
