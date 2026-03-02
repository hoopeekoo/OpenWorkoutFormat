"""Tests for the serializer."""

from owf.parser.step_parser import parse_document
from owf.serializer import dumps


def test_serialize_simple_endurance():
    text = (
        "## Easy Run [endurance]\n\n- warmup 15min @Z1\n"
        "- run 5km @4:30/km\n- cooldown 10min @Z1\n"
    )
    doc = parse_document(text)
    result = dumps(doc)
    assert "## Easy Run [endurance]" in result
    assert "- warmup 15min @Z1" in result
    assert "- run 5km @4:30/km" in result


def test_serialize_with_frontmatter():
    text = "---\nFTP: 250W\n---\n\n## Ride [endurance]\n\n- bike 30min @200W\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "---" in result
    assert "FTP: 250W" in result
    assert "## Ride [endurance]" in result


def test_serialize_repeat_block():
    text = (
        "## Intervals\n\n- 5x:\n"
        "  - bike 5min @200W\n  - recover 3min @Z1\n"
    )
    doc = parse_document(text)
    result = dumps(doc)
    assert "- 5x:" in result
    assert "  - bike 5min @200W" in result
    assert "  - recover 3min @Z1" in result


def test_serialize_strength():
    text = "## Strength [strength]\n\n- bench press 3x8rep @80kg rest:90s\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "- bench press 3x8rep @80kg rest:1min30s" in result


def test_serialize_emom():
    text = "## WoD [mixed]\n\n- emom 10min:\n  - power clean 3rep @70kg\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "- emom 10min:" in result
    assert "  - power clean 3rep @70kg" in result


def test_serialize_amrap():
    text = (
        "## Metcon [mixed]\n\n- amrap 12min:\n"
        "  - pull-up 5rep\n  - push-up 10rep\n"
    )
    doc = parse_document(text)
    result = dumps(doc)
    assert "- amrap 12min:" in result


def test_serialize_for_time():
    text = "## Murph [mixed]\n\n- for-time:\n  - run 1mile\n  - pull-up 100rep\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "- for-time:" in result
    assert "  - run 1mile" in result


def test_serialize_session():
    text = (
        "## Session\n\n- warmup 10min @Z1\n\n"
        "# Ride [endurance]\n\n- bike 30min\n\n"
        "- cooldown 10min @Z1\n"
    )
    doc = parse_document(text)
    result = dumps(doc)
    assert "## Session" in result
    assert "# Ride [endurance]" in result
    assert "- warmup 10min @Z1" in result
    assert "- cooldown 10min @Z1" in result


def test_serialize_rir():
    text = "## Strength [strength]\n\n- bench press 3x8rep @RIR 2 rest:90s\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "@RIR 2" in result


def test_serialize_superset():
    text = (
        "## Strength\n\n- 3x superset:\n"
        "  - bench press 3x8rep @80kg rest:90s\n"
        "  - bent-over row 3x8rep @60kg rest:90s\n"
    )
    doc = parse_document(text)
    result = dumps(doc)
    assert "- 3x superset:" in result


def test_serialize_workout_rpe():
    text = "## Run [endurance] @RPE 7\n\n- run 5km\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "## Run [endurance] @RPE 7" in result
    doc2 = parse_document(result)
    assert doc2.workouts[0].rpe == 7.0


def test_serialize_workout_rir():
    text = "## Strength [strength] @RIR 2\n\n- bench press 3x8rep @80kg\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "## Strength [strength] @RIR 2" in result
    doc2 = parse_document(result)
    assert doc2.workouts[0].rir == 2


def test_serialize_circuit():
    text = (
        "## Strength\n\n- 3x circuit:\n"
        "  - kettlebell swing 10rep @24kg\n"
        "  - push-up 15rep\n"
        "  - air squat 20rep\n"
    )
    doc = parse_document(text)
    result = dumps(doc)
    assert "- 3x circuit:" in result
    assert "  - kettlebell swing 10rep @24kg" in result


def test_serialize_flat_headings_become_sessions():
    """Flat # headings → ## in serialized output."""
    text = "# Run [endurance]\n\n- run 5km\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "##" in result


def test_serialize_percent_of():
    text = "## Ride\n\n- bike 30min @80% of FTP\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "@80% of FTP" in result


def test_serialize_bodyweight_plus():
    text = "## Gym\n\n- dip 3x8rep @bodyweight + 20kg\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "@bodyweight + 20kg" in result


def test_serialize_zone():
    text = "## Run\n\n- run 10min @Z2\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "@Z2" in result


def test_serialize_heart_rate():
    text = "## Run\n\n- run 10min @140bpm\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "@140bpm" in result
