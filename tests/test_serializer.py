"""Tests for the serializer."""

from owf.parser.step_parser import parse_document
from owf.serializer import dumps


def test_serialize_simple_endurance():
    text = (
        "# Easy Run [endurance]\n\n- Warmup 15min @Z1\n"
        "- Run 5km @4:30/km\n- Cooldown 10min @Z1\n"
    )
    doc = parse_document(text)
    result = dumps(doc)
    assert "# Easy Run [endurance]" in result
    assert "- Warmup 15min @Z1" in result
    assert "- Run 5km @4:30/km" in result


def test_serialize_with_metadata():
    text = "@ FTP: 250W\n\n# Ride [endurance]\n\n- Bike 30min @200W\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "@ FTP: 250W" in result
    assert "# Ride [endurance]" in result


def test_serialize_repeat_block():
    text = (
        "# Intervals\n\n- 5x:\n"
        "  - Bike 5min @200W\n  - Recover 3min @Z1\n"
    )
    doc = parse_document(text)
    result = dumps(doc)
    assert "- 5x:" in result
    assert "  - Bike 5min @200W" in result
    assert "  - Recover 3min @Z1" in result


def test_serialize_strength():
    text = "# Strength [strength]\n\n- Bench Press 3x8rep @80kg @rest 90s\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "- Bench Press 3x8rep @80kg @rest 1min30s" in result


def test_serialize_emom():
    text = "# WoD [mixed]\n\n- emom 10min:\n  - Power Clean 3rep @70kg\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "- emom 10min:" in result
    assert "  - Power Clean 3rep @70kg" in result


def test_serialize_amrap():
    text = (
        "# Metcon [mixed]\n\n- amrap 12min:\n"
        "  - Pull-Up 5rep\n  - Push-Up 10rep\n"
    )
    doc = parse_document(text)
    result = dumps(doc)
    assert "- amrap 12min:" in result


def test_serialize_for_time():
    text = "# Murph [mixed]\n\n- for-time:\n  - Run 1mile\n  - Pull-Up 100rep\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "- for-time:" in result
    assert "  - Run 1mile" in result


def test_serialize_rir():
    text = "# Strength [strength]\n\n- Bench Press 3x8rep @RIR 2 @rest 90s\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "@RIR 2" in result


def test_serialize_superset():
    text = (
        "# Strength\n\n- 3x superset:\n"
        "  - Bench Press 3x8rep @80kg @rest 90s\n"
        "  - Bent-Over Row 3x8rep @60kg @rest 90s\n"
    )
    doc = parse_document(text)
    result = dumps(doc)
    assert "- 3x superset:" in result


def test_serialize_workout_rpe():
    text = "# Run [endurance] @RPE 7\n\n- Run 5km\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "# Run [endurance] @RPE 7" in result
    doc2 = parse_document(result)
    assert doc2.workouts[0].rpe == 7


def test_serialize_workout_rir():
    text = "# Strength [strength] @RIR 2\n\n- Bench Press 3x8rep @80kg\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "# Strength [strength] @RIR 2" in result
    doc2 = parse_document(result)
    assert doc2.workouts[0].rir == 2


def test_serialize_circuit():
    text = (
        "# Strength\n\n- 3x circuit:\n"
        "  - Kettlebell Swing 10rep @24kg\n"
        "  - Push-Up 15rep\n"
        "  - Air Squat 20rep\n"
    )
    doc = parse_document(text)
    result = dumps(doc)
    assert "- 3x circuit:" in result
    assert "  - Kettlebell Swing 10rep @24kg" in result


def test_serialize_percent_of():
    text = "# Ride\n\n- Bike 30min @80% of FTP\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "@80% of FTP" in result


def test_serialize_bodyweight_plus():
    text = "# Gym\n\n- Dip 3x8rep @bodyweight + 20kg\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "@bodyweight + 20kg" in result


def test_serialize_zone():
    text = "# Run\n\n- Run 10min @Z2\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "@Z2" in result


def test_serialize_heart_rate():
    text = "# Run\n\n- Run 10min @140bpm\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "@140bpm" in result
