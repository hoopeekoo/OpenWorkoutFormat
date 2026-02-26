"""Tests for the serializer."""

from owf.parser.step_parser import parse_document
from owf.serializer import dumps


def test_serialize_simple_endurance():
    text = "# Easy Run [run]\n\n- warmup 15min @easy\n- run 5km @4:30/km\n- cooldown 10min @easy\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "# Easy Run [run]" in result
    assert "- warmup 15min @easy" in result
    assert "- run 5km @4:30/km" in result


def test_serialize_with_frontmatter():
    text = "---\nFTP: 250W\n---\n\n# Ride [bike]\n\n- bike 30min @200W\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "---" in result
    assert "FTP: 250W" in result
    assert "# Ride [bike]" in result


def test_serialize_repeat_block():
    text = "# Intervals\n\n- 5x:\n  - bike 5min @200W\n  - recover 3min @easy\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "- 5x:" in result
    assert "  - bike 5min @200W" in result
    assert "  - recover 3min @easy" in result


def test_serialize_strength():
    text = "# Strength [strength]\n\n- bench press 3x8rep @80kg rest:90s\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "- bench press 3x8rep @80kg rest:90s" in result


def test_serialize_emom():
    text = "# WoD [wod]\n\n- emom 10min:\n  - power clean 3rep @70kg\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "- emom 10min:" in result
    assert "  - power clean 3rep @70kg" in result


def test_serialize_amrap():
    text = "# Metcon [wod]\n\n- amrap 12min:\n  - pull-up 5rep\n  - push-up 10rep\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "- amrap 12min:" in result


def test_serialize_for_time():
    text = "# Murph [wod]\n\n- for-time:\n  - run 1mile\n  - pull-up 100rep\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "- for-time:" in result
    assert "  - run 1mile" in result


def test_serialize_include():
    text = "# Full\n\n- include: Threshold Ride\n- rest 10min\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "- include: Threshold Ride" in result
    assert "- rest 10min" in result


def test_serialize_rir():
    text = "# Strength [strength]\n\n- bench press 3x8rep @RIR 2 rest:90s\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "@RIR 2" in result


def test_serialize_superset():
    text = "# Strength\n\n- 3x superset:\n  - bench press 3x8rep @80kg rest:90s\n  - bent-over row 3x8rep @60kg rest:90s\n"
    doc = parse_document(text)
    result = dumps(doc)
    assert "- 3x superset:" in result
