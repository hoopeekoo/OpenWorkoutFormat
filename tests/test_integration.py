"""Integration tests — parse the full example from the spec."""

from owf.ast.blocks import AMRAP, EMOM, AlternatingEMOM, CustomInterval, ForTime, Superset
from owf.ast.steps import EnduranceStep, IncludeStep, RepeatStep, RestStep, StrengthStep
from owf.parser.step_parser import parse_document
from owf.resolver import resolve
from owf.serializer import dumps

FULL_EXAMPLE = """\
---
FTP: 250W
1RM bench press: 100kg
bodyweight: 80kg
max HR: 185bpm
---

# Threshold Ride [bike]

- warmup 15min @60% of FTP
- 5x:
  - bike 5min @95% of FTP
  - recover 3min @50% of FTP
- cooldown 10min @easy

> Felt strong through set 3, faded on 4-5.

# Upper Body [strength]

- 3x superset:
  - bench press 3x8rep @80% of 1RM bench press rest:90s
  - bent-over row 3x8rep @60kg rest:90s
- bicep curl 3x12rep @15kg rest:60s

# Power Clean EMOM [wod]

- emom 10min:
  - power clean 3rep @70kg

# Alternating EMOM [wod]

- emom 12min alternating:
  - deadlift 5rep @100kg
  - strict press 7rep @40kg
  - toes-to-bar 10rep

# Mixed EMOM [wod]

- every 2min for 20min:
  - wall ball 15rep @9kg
  - box jump 10rep @24in

# Murph [wod]

- for-time:
  - run 1mile
  - pull-up 100rep
  - push-up 200rep
  - air squat 300rep
  - run 1mile

# Metcon [wod]

- amrap 12min:
  - pull-up 5rep
  - push-up 10rep
  - air squat 15rep

# Full Session

- include: Threshold Ride
- rest 10min
- include: Upper Body
"""


def test_parse_full_example():
    doc = parse_document(FULL_EXAMPLE)
    assert len(doc.workouts) == 8
    assert doc.variables["FTP"] == "250W"
    assert doc.variables["1RM bench press"] == "100kg"
    assert doc.variables["bodyweight"] == "80kg"
    assert doc.variables["max HR"] == "185bpm"


def test_workout_types():
    doc = parse_document(FULL_EXAMPLE)
    types = [(w.name, w.workout_type) for w in doc.workouts]
    assert ("Threshold Ride", "bike") in types
    assert ("Upper Body", "strength") in types
    assert ("Power Clean EMOM", "wod") in types
    assert ("Full Session", None) in types


def test_threshold_ride_structure():
    doc = parse_document(FULL_EXAMPLE)
    ride = doc.workouts[0]
    assert ride.name == "Threshold Ride"
    assert len(ride.steps) == 3

    warmup = ride.steps[0]
    assert isinstance(warmup, EnduranceStep)
    assert warmup.action == "warmup"
    assert warmup.duration is not None
    assert warmup.duration.seconds == 900

    intervals = ride.steps[1]
    assert isinstance(intervals, RepeatStep)
    assert intervals.count == 5
    assert len(intervals.steps) == 2

    cooldown = ride.steps[2]
    assert isinstance(cooldown, EnduranceStep)
    assert cooldown.action == "cooldown"


def test_upper_body_structure():
    doc = parse_document(FULL_EXAMPLE)
    upper = doc.workouts[1]
    assert upper.name == "Upper Body"
    assert len(upper.steps) == 2

    superset = upper.steps[0]
    assert isinstance(superset, Superset)
    assert superset.count == 3
    assert len(superset.steps) == 2

    curl = upper.steps[1]
    assert isinstance(curl, StrengthStep)
    assert curl.exercise == "bicep curl"
    assert curl.sets == 3
    assert curl.reps == 12


def test_emom_structure():
    doc = parse_document(FULL_EXAMPLE)
    emom = doc.workouts[2]
    assert emom.name == "Power Clean EMOM"
    step = emom.steps[0]
    assert isinstance(step, EMOM)
    assert step.duration.seconds == 600


def test_alternating_emom_structure():
    doc = parse_document(FULL_EXAMPLE)
    alt_emom = doc.workouts[3]
    step = alt_emom.steps[0]
    assert isinstance(step, AlternatingEMOM)
    assert step.duration.seconds == 720
    assert len(step.steps) == 3


def test_custom_interval_structure():
    doc = parse_document(FULL_EXAMPLE)
    mixed = doc.workouts[4]
    step = mixed.steps[0]
    assert isinstance(step, CustomInterval)
    assert step.interval.seconds == 120
    assert step.duration.seconds == 1200
    assert len(step.steps) == 2


def test_for_time_structure():
    doc = parse_document(FULL_EXAMPLE)
    murph = doc.workouts[5]
    step = murph.steps[0]
    assert isinstance(step, ForTime)
    assert step.time_cap is None
    assert len(step.steps) == 5


def test_amrap_structure():
    doc = parse_document(FULL_EXAMPLE)
    metcon = doc.workouts[6]
    step = metcon.steps[0]
    assert isinstance(step, AMRAP)
    assert step.duration.seconds == 720
    assert len(step.steps) == 3


def test_include_structure():
    doc = parse_document(FULL_EXAMPLE)
    full = doc.workouts[7]
    assert full.name == "Full Session"
    assert len(full.steps) == 3
    assert isinstance(full.steps[0], IncludeStep)
    assert full.steps[0].workout_name == "Threshold Ride"
    assert isinstance(full.steps[1], RestStep)
    assert isinstance(full.steps[2], IncludeStep)
    assert full.steps[2].workout_name == "Upper Body"


def test_resolve_full_example():
    doc = parse_document(FULL_EXAMPLE)
    resolved = resolve(doc)

    # Check that FTP-based expressions were resolved
    ride = resolved.workouts[0]
    warmup = ride.steps[0]
    assert isinstance(warmup, EnduranceStep)
    # 60% of 250W = 150W
    from owf.ast.expressions import Literal
    from owf.ast.params import PowerParam

    param = warmup.params[0]
    assert isinstance(param, PowerParam)
    assert isinstance(param.value, Literal)
    assert param.value.value == 150.0
    assert param.value.unit == "W"


def test_serialize_full_example():
    doc = parse_document(FULL_EXAMPLE)
    serialized = dumps(doc)

    # Should contain all workout headings
    assert "# Threshold Ride [bike]" in serialized
    assert "# Upper Body [strength]" in serialized
    assert "# Power Clean EMOM [wod]" in serialized
    assert "# Murph [wod]" in serialized
    assert "# Metcon [wod]" in serialized
    assert "# Full Session" in serialized

    # Should contain key structural elements
    assert "- 5x:" in serialized
    assert "- emom 10min:" in serialized
    assert "- amrap 12min:" in serialized
    assert "- for-time:" in serialized
    assert "- include: Threshold Ride" in serialized


def test_roundtrip_full_example():
    """parse → dumps → parse should be structurally equivalent."""
    doc1 = parse_document(FULL_EXAMPLE)
    serialized = dumps(doc1)
    doc2 = parse_document(serialized)

    assert len(doc1.workouts) == len(doc2.workouts)
    for w1, w2 in zip(doc1.workouts, doc2.workouts):
        assert w1.name == w2.name
        assert w1.workout_type == w2.workout_type
        assert len(w1.steps) == len(w2.steps)


def test_public_api():
    """Test the public API (owf.parse, owf.dumps, owf.resolve)."""
    import owf

    doc = owf.parse(FULL_EXAMPLE)
    assert len(doc.workouts) == 8

    resolved = owf.resolve(doc)
    assert len(resolved.workouts) == 8

    text = owf.dumps(doc)
    assert "# Threshold Ride [bike]" in text
