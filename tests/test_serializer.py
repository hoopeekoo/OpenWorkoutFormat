"""Tests for the serializer."""

from owf.ast.base import Program
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


def test_serialize_interval():
    text = "# WoD [mixed]\n\n- every 1min for 10min:\n  - Power Clean 3rep @70kg\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "- every 1min for 10min:" in result
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


def test_serialize_superset_style():
    text = (
        "# Strength\n\n- superset 3x:\n"
        "  - Bench Press 3x8rep @80kg @rest 90s\n"
        "  - Bent-Over Row 3x8rep @60kg @rest 90s\n"
    )
    doc = parse_document(text)
    result = dumps(doc)
    assert "- superset 3x:" in result


def test_serialize_circuit_style():
    text = (
        "# Strength\n\n- circuit 3x:\n"
        "  - Kettlebell Swing 10rep @24kg\n"
        "  - Push-Up 15rep\n"
        "  - Air Squat 20rep\n"
    )
    doc = parse_document(text)
    result = dumps(doc)
    assert "- circuit 3x:" in result
    assert "  - Kettlebell Swing 10rep @24kg" in result


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


def test_serialize_percent_of():
    text = "# Ride\n\n- Bike 30min @80% of FTP\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "@80% FTP" in result


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


def test_serialize_program():
    text = (
        "## My Program (4 weeks)\n"
        "@ author: Coach\n"
        "@ progression: Bench Press +2.5kg/week\n"
        "@ deload: week 4 x0.8\n\n"
        "--- Week 1 ---\n"
        "@ template: true\n\n"
        "# Day 1\n\n- Bench Press 3x8rep @60kg\n\n"
        "--- Week 2 ---\n"
    )
    prog = parse_document(text)
    assert isinstance(prog, Program)
    result = dumps(prog)
    assert "## My Program (4 weeks)" in result
    assert "@ author: Coach" in result
    assert "@ progression: Bench Press +2.5kg/week" in result
    assert "@ deload: week 4 x0.8" in result
    assert "--- Week 1 ---" in result
    assert "@ template: true" in result
    assert "--- Week 2 ---" in result


# ===== New feature serialization tests =====


def test_serialize_zone_with_metric():
    text = "# Ride\n\n- Bike 20min @Z2:power\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "@Z2:power" in result


def test_serialize_zone_unqualified():
    text = "# Run\n\n- Run 10min @Z2\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "@Z2" in result
    assert "@Z2:" not in result  # no trailing colon


def test_serialize_typed_percent_ftp():
    text = "# Ride\n\n- Bike 10min @95%FTP\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "@95%FTP" in result


def test_serialize_typed_percent_lthr():
    text = "# Run\n\n- Run 30min @88%LTHR\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "@88%LTHR" in result


def test_serialize_typed_percent_1rm():
    text = "# Gym\n\n- Bench Press 3x5rep @85%1RM\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "@85%1RM" in result


def test_serialize_tempo():
    text = "# Gym\n\n- Back Squat 4x6rep @120kg @tempo 31X0 @rest 2min\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "@tempo 31X0" in result


def test_serialize_set_type_warmup():
    text = "# Gym\n\n- Bench Press 3x8rep @60kg @warmup @rest 90s\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "@warmup" in result


def test_serialize_set_type_rest_pause():
    text = "# Gym\n\n- Bench Press 1x12rep @60kg @rest-pause\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "@rest-pause" in result


def test_serialize_set_type_myo_rep():
    text = "# Gym\n\n- Leg Press 1x20rep @myo-rep\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "@myo-rep" in result


def test_serialize_pace_500m():
    text = "# Row\n\n- Row 4x500m @1:45/500m @rest 90s\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "@1:45/500m" in result


def test_serialize_pace_100m():
    text = "# Swim\n\n- Swim 8x100m @1:32/100m @rest 20s\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "@1:32/100m" in result
