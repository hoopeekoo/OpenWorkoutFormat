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
        "# Strength\n\n- 3x:\n"
        "  @ style: superset\n"
        "  - Bench Press 3x8rep @80kg @rest 90s\n"
        "  - Bent-Over Row 3x8rep @60kg @rest 90s"
    )


def test_roundtrip_circuit_style():
    _roundtrip(
        "# Strength\n\n- 3x:\n"
        "  @ style: circuit\n"
        "  - Kettlebell Swing 10rep @24kg\n"
        "  - Push-Up 15rep\n"
        "  - Air Squat 20rep"
    )


def test_roundtrip_percent_of():
    _roundtrip("# Ride\n\n- Bike 30min @80% of FTP")


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
        "--- Week 1 (template) ---\n\n"
        "# Day 1\n\n- Bench Press 3x8rep @60kg\n\n"
        "--- Week 2 ---\n"
    )
