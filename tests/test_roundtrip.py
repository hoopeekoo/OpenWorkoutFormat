"""Round-trip tests: parse → serialize → parse should produce equivalent AST."""

from owf.parser.step_parser import parse_document
from owf.serializer import dumps


def _roundtrip(text: str) -> None:
    """Parse text, serialize, re-parse, and verify equivalence."""
    doc1 = parse_document(text)
    serialized = dumps(doc1)
    doc2 = parse_document(serialized)

    # Compare structurally (ignoring spans)
    assert len(doc1.workouts) == len(doc2.workouts)
    for w1, w2 in zip(doc1.workouts, doc2.workouts):
        assert w1.name == w2.name
        assert w1.workout_type == w2.workout_type
        assert len(w1.steps) == len(w2.steps)


def test_roundtrip_endurance():
    _roundtrip("# Run [run]\n\n- warmup 15min @easy\n- run 5km @4:30/km\n- cooldown 10min @easy")


def test_roundtrip_strength():
    _roundtrip("# Strength [strength]\n\n- bench press 3x8rep @80kg rest:90s\n- bicep curl 3x12rep @15kg rest:60s")


def test_roundtrip_intervals():
    _roundtrip("# Intervals\n\n- 5x:\n  - bike 5min @200W\n  - recover 3min @easy")


def test_roundtrip_emom():
    _roundtrip("# WoD [wod]\n\n- emom 10min:\n  - power clean 3rep @70kg")


def test_roundtrip_amrap():
    _roundtrip("# Metcon [wod]\n\n- amrap 12min:\n  - pull-up 5rep\n  - push-up 10rep\n  - air squat 15rep")


def test_roundtrip_for_time():
    _roundtrip("# Murph [wod]\n\n- for-time:\n  - run 1mile\n  - pull-up 100rep\n  - push-up 200rep")


def test_roundtrip_frontmatter():
    _roundtrip("---\nFTP: 250W\n---\n\n# Ride [bike]\n\n- bike 30min @200W")


def test_roundtrip_session():
    _roundtrip("## Session\n\n- warmup 10min @easy\n\n# Ride [bike]\n\n- bike 30min\n\n- cooldown 10min @easy")


def test_roundtrip_superset():
    _roundtrip("# Strength\n\n- 3x superset:\n  - bench press 3x8rep @80kg rest:90s\n  - bent-over row 3x8rep @60kg rest:90s")
