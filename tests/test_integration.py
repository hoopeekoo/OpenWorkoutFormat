"""Integration tests -- parse full examples with all container types."""

from owf.ast.base import Program
from owf.ast.blocks import (
    AMRAP,
    ForTime,
    Interval,
)
from owf.ast.params import PowerParam
from owf.ast.steps import RepeatBlock, Step
from owf.parser.step_parser import parse_document
from owf.resolver import resolve
from owf.serializer import dumps

FULL_EXAMPLE = """\
# Threshold Ride [endurance]

- Warmup 15min @60% FTP
- 5x:
  - Bike 5min @95% FTP
  - Recover 3min @50% FTP
- Cooldown 10min @Z1

> Felt strong through set 3, faded on 4-5.

# Upper Body [strength]

- superset 3x:
  - Bench Press 3x8rep @80% 1RM bench press @rest 90s
  - Bent-Over Row 3x8rep @60kg @rest 90s
- Bicep Curl 3x12rep @15kg @rest 60s

# Power Clean EMOM [mixed]

- every 1min for 10min:
  - Power Clean 3rep @70kg

# Alternating EMOM [mixed]

- every 1min for 12min:
  - Deadlift 5rep @100kg
  - Strict Press 7rep @40kg
  - Toes-To-Bar 10rep

# Mixed Interval [mixed]

- every 2min for 20min:
  - Wall Ball 15rep @9kg
  - Box Jump 10rep

# Murph [mixed]

- for-time:
  - Run 1mile
  - Pull-Up 100rep
  - Push-Up 200rep
  - Air Squat 300rep
  - Run 1mile

# Metcon [mixed]

- amrap 12min:
  - Pull-Up 5rep
  - Push-Up 10rep
  - Air Squat 15rep
"""

MULTI_WORKOUT_EXAMPLE = """\
# Saturday Warmup [endurance]

- Warmup 10min @Z1

# Threshold Ride [endurance]

- 5x:
  - Bike 5min @95% FTP
  - Recover 3min @50% FTP

# Upper Body [strength]

- Bench Press 3x8rep @80kg @rest 90s

> Great session overall.
"""

PROGRAM_EXAMPLE = """\
## Strength Block (4 weeks)
@ author: Coach Smith
@ progression: Bench Press +2.5kg/week
@ deload: week 4 x0.8

--- Week 1 ---
@ template: true

# Day 1 [Strength Training]

- Bench Press 3x8rep @60kg @rest 90s
- Pull-Up 3x8rep @rest 90s

# Day 2 [Strength Training]

- Back Squat 3x5rep @100kg @rest 2min

--- Week 2 ---
> Derived from template + progression.

--- Week 4 ---
@ deload: true
"""


def test_parse_full_example():
    doc = parse_document(FULL_EXAMPLE)
    assert len(doc.workouts) == 7
    assert doc.metadata == {}


def test_workout_types():
    doc = parse_document(FULL_EXAMPLE)
    types = [(w.name, w.sport_type) for w in doc.workouts]
    assert ("Threshold Ride", "endurance") in types
    assert ("Upper Body", "strength") in types
    assert ("Power Clean EMOM", "mixed") in types


def test_threshold_ride_structure():
    doc = parse_document(FULL_EXAMPLE)
    ride = doc.workouts[0]
    assert ride.name == "Threshold Ride"
    assert len(ride.steps) == 3

    warmup = ride.steps[0]
    assert isinstance(warmup, Step)
    assert warmup.action == "Warmup"
    assert warmup.duration is not None
    assert warmup.duration.seconds == 900

    intervals = ride.steps[1]
    assert isinstance(intervals, RepeatBlock)
    assert intervals.count == 5
    assert len(intervals.steps) == 2

    cooldown = ride.steps[2]
    assert isinstance(cooldown, Step)
    assert cooldown.action == "Cooldown"


def test_upper_body_structure():
    doc = parse_document(FULL_EXAMPLE)
    upper = doc.workouts[1]
    assert upper.name == "Upper Body"
    assert len(upper.steps) == 2

    superset = upper.steps[0]
    assert isinstance(superset, RepeatBlock)
    assert superset.count == 3
    assert superset.style == "superset"
    assert len(superset.steps) == 2

    curl = upper.steps[1]
    assert isinstance(curl, Step)
    assert curl.action == "Bicep Curl"
    assert curl.sets == 3
    assert curl.reps == 12


def test_emom_structure():
    doc = parse_document(FULL_EXAMPLE)
    emom = doc.workouts[2]
    assert emom.name == "Power Clean EMOM"
    step = emom.steps[0]
    assert isinstance(step, Interval)
    assert step.interval.seconds == 60
    assert step.duration.seconds == 600


def test_alternating_emom_structure():
    doc = parse_document(FULL_EXAMPLE)
    alt_emom = doc.workouts[3]
    step = alt_emom.steps[0]
    assert isinstance(step, Interval)
    assert step.duration.seconds == 720
    assert len(step.steps) == 3
    assert step.is_alternating


def test_custom_interval_structure():
    doc = parse_document(FULL_EXAMPLE)
    mixed = doc.workouts[4]
    step = mixed.steps[0]
    assert isinstance(step, Interval)
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


def test_multi_workout_structure():
    """Multiple # headings produce flat workouts."""
    doc = parse_document(MULTI_WORKOUT_EXAMPLE)
    assert len(doc.workouts) == 3

    warmup_w = doc.workouts[0]
    assert warmup_w.name == "Saturday Warmup"
    assert warmup_w.sport_type == "endurance"
    assert len(warmup_w.steps) == 1
    assert isinstance(warmup_w.steps[0], Step)
    assert warmup_w.steps[0].action == "Warmup"

    ride = doc.workouts[1]
    assert ride.name == "Threshold Ride"
    assert ride.sport_type == "endurance"
    assert len(ride.steps) == 1
    assert isinstance(ride.steps[0], RepeatBlock)

    upper = doc.workouts[2]
    assert upper.name == "Upper Body"
    assert upper.sport_type == "strength"
    assert len(upper.steps) == 1  # bench press


def test_program_structure():
    """Program with ## heading, weeks, progression, deload."""
    prog = parse_document(PROGRAM_EXAMPLE)
    assert isinstance(prog, Program)
    assert prog.name == "Strength Block"
    assert prog.duration == "4 weeks"
    assert prog.metadata.get("author") == "Coach Smith"
    assert len(prog.progression_rules) == 1
    assert prog.progression_rules[0].action == "Bench Press"
    assert prog.progression_rules[0].amount == 2.5
    assert prog.deload_rule is not None
    assert prog.deload_rule.week == 4
    assert prog.deload_rule.multiplier == 0.8
    assert len(prog.weeks) == 3
    assert prog.weeks[0].is_template is True
    assert prog.weeks[0].name == "Week 1"
    assert len(prog.weeks[0].workouts) == 2
    assert prog.weeks[2].is_deload is True
    assert prog.weeks[2].name == "Week 4"


def test_resolve_full_example():
    doc = parse_document(FULL_EXAMPLE)
    resolved = resolve(doc, {
        "FTP": "250W",
        "1RM bench press": "100kg",
        "bodyweight": "80kg",
        "max HR": "185bpm",
    })

    # Check that FTP-based expressions were resolved
    ride = resolved.workouts[0]
    warmup = ride.steps[0]
    assert isinstance(warmup, Step)
    # 60% of 250W = 150W
    param = warmup.params[0]
    assert isinstance(param, PowerParam)
    assert param.value == 150.0


def test_resolve_multi_workout_example():
    """Resolver should resolve across all workouts."""
    doc = parse_document(MULTI_WORKOUT_EXAMPLE)
    resolved = resolve(doc, {"FTP": "250W"})

    # The Threshold Ride workout should have resolved FTP expressions
    ride = resolved.workouts[1]
    repeat = ride.steps[0]
    assert isinstance(repeat, RepeatBlock)
    bike = repeat.steps[0]
    assert isinstance(bike, Step)
    param = bike.params[0]
    assert isinstance(param, PowerParam)
    # 95% of 250W = 237.5W -> rounds to 238
    assert param.value == 238


def test_serialize_full_example():
    doc = parse_document(FULL_EXAMPLE)
    serialized = dumps(doc)

    # Should contain all workout headings with their sport_type tags
    assert "# Threshold Ride [endurance]" in serialized
    assert "# Upper Body [strength]" in serialized
    assert "# Power Clean EMOM [mixed]" in serialized
    assert "# Murph [mixed]" in serialized
    assert "# Metcon [mixed]" in serialized

    # Should contain key structural elements
    assert "- 5x:" in serialized
    assert "- every 1min for 10min:" in serialized
    assert "- amrap 12min:" in serialized
    assert "- for-time:" in serialized


def test_serialize_multi_workout_example():
    doc = parse_document(MULTI_WORKOUT_EXAMPLE)
    serialized = dumps(doc)

    assert "# Saturday Warmup [endurance]" in serialized
    assert "# Threshold Ride [endurance]" in serialized
    assert "# Upper Body [strength]" in serialized
    assert "- Warmup 10min @Z1" in serialized
    assert "> Great session overall." in serialized


def test_serialize_program():
    prog = parse_document(PROGRAM_EXAMPLE)
    serialized = dumps(prog)

    assert "## Strength Block (4 weeks)" in serialized
    assert "@ author: Coach Smith" in serialized
    assert "@ progression: Bench Press +2.5kg/week" in serialized
    assert "@ deload: week 4 x0.8" in serialized
    assert "--- Week 1 ---" in serialized
    assert "@ template: true" in serialized


def test_roundtrip_full_example():
    """parse -> dumps -> parse should be structurally equivalent."""
    doc1 = parse_document(FULL_EXAMPLE)
    serialized = dumps(doc1)
    doc2 = parse_document(serialized)

    assert len(doc1.workouts) == len(doc2.workouts)
    for w1, w2 in zip(doc1.workouts, doc2.workouts):
        assert w1.name == w2.name
        assert w1.sport_type == w2.sport_type
        assert len(w1.steps) == len(w2.steps)


def test_roundtrip_multi_workout_example():
    """parse -> dumps -> parse for multi-workout documents."""
    doc1 = parse_document(MULTI_WORKOUT_EXAMPLE)
    serialized = dumps(doc1)
    doc2 = parse_document(serialized)

    assert len(doc1.workouts) == len(doc2.workouts)
    for w1, w2 in zip(doc1.workouts, doc2.workouts):
        assert w1.name == w2.name
        assert w1.sport_type == w2.sport_type
        assert len(w1.steps) == len(w2.steps)


def test_roundtrip_program():
    """parse -> dumps -> parse for program documents."""
    prog1 = parse_document(PROGRAM_EXAMPLE)
    serialized = dumps(prog1)
    prog2 = parse_document(serialized)

    assert isinstance(prog2, Program)
    assert prog1.name == prog2.name
    assert len(prog1.weeks) == len(prog2.weeks)


def test_public_api():
    """Test the public API (owf.parse, owf.dumps, owf.resolve)."""
    import owf

    doc = owf.parse(FULL_EXAMPLE)
    assert len(doc.workouts) == 7

    resolved = owf.resolve(doc, {
        "FTP": "250W",
        "1RM bench press": "100kg",
        "bodyweight": "80kg",
        "max HR": "185bpm",
    })
    assert len(resolved.workouts) == 7

    text = owf.dumps(doc)
    assert "# Threshold Ride [endurance]" in text
