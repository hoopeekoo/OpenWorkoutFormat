"""Tests for the example files covering all spec features."""

from __future__ import annotations

from pathlib import Path

from owf.ast.blocks import AMRAP, ForTime, Interval
from owf.ast.params import (
    BodyweightPlusParam,
    HeartRateParam,
    PaceParam,
    PercentOfParam,
    PowerParam,
    RIRParam,
    RPEParam,
    WeightParam,
    ZoneParam,
)
from owf.ast.steps import RepeatBlock, Step
from owf.loader import load
from owf.resolver import resolve
from owf.units import Pace

# --- hr_zone_run.owf ---


def test_hr_zone_run():
    doc = load(Path("examples/hr_zone_run.owf"))
    assert doc.metadata == {}
    assert len(doc.workouts) == 1

    w = doc.workouts[0]
    assert w.name == "HR Zone Run"
    assert w.sport_type == "Running"
    assert w.rpe == 6
    assert len(w.steps) == 6

    # @Z1
    s0 = w.steps[0]
    assert s0.action == "Warmup"
    assert isinstance(s0.params[0], ZoneParam)
    assert s0.params[0].zone == "Z1"

    # @140bpm
    s1 = w.steps[1]
    assert s1.action == "Run"
    assert s1.duration.seconds == 600
    assert isinstance(s1.params[0], HeartRateParam)
    assert s1.params[0].value == 140

    # @70% of max HR
    s2 = w.steps[2]
    assert isinstance(s2.params[0], PercentOfParam)
    assert s2.params[0].percent == 70
    assert s2.params[0].variable == "max HR"

    # @Z3
    s3 = w.steps[3]
    assert isinstance(s3.params[0], ZoneParam)
    assert s3.params[0].zone == "Z3"

    # @4:30/km
    s4 = w.steps[4]
    assert s4.distance.value == 5
    assert s4.distance.unit == "km"
    assert isinstance(s4.params[0], PaceParam)
    assert s4.params[0].pace == Pace(minutes=4, seconds=30, unit="km")

    # workout note
    assert any(
        "all targeting methods" in n
        for n in w.notes
    )


def test_hr_zone_run_resolve():
    doc = load(Path("examples/hr_zone_run.owf"))
    resolved = resolve(doc, {"max HR": "190bpm"})
    # 70% of 190bpm = 133bpm
    s2 = resolved.workouts[0].steps[2]
    param = s2.params[0]
    assert isinstance(param, HeartRateParam)
    assert param.value == 133


# --- strength_upper.owf ---


def test_strength_upper():
    doc = load(Path("examples/strength_upper.owf"))
    assert len(doc.workouts) == 1

    w = doc.workouts[0]
    assert w.name == "Upper Body"
    assert w.sport_type == "Strength Training"
    assert w.rir == 2

    # Bench Press 4x8rep @80% of 1RM bench press @rest 2min
    s0 = w.steps[0]
    assert isinstance(s0, Step)
    assert s0.action == "Bench Press"
    assert s0.sets == 4
    assert s0.reps == 8
    assert s0.rest.seconds == 120
    assert isinstance(s0.params[0], PercentOfParam)
    assert s0.params[0].percent == 80
    assert s0.params[0].variable == "1RM bench press"
    assert s0.metadata.get("tempo") == "30X1"

    # RepeatBlock with style=superset: Dumbbell Row + Incline Dumbbell Bench Press
    s1 = w.steps[1]
    assert isinstance(s1, RepeatBlock)
    assert s1.count == 3
    assert s1.style == "superset"
    assert len(s1.steps) == 2

    # Pull-Up 3xmaxrep @bodyweight + 10kg
    s2 = w.steps[2]
    assert s2.action == "Pull-Up"
    assert s2.sets == 3
    assert s2.reps == "max"
    assert isinstance(s2.params[0], BodyweightPlusParam)
    assert s2.params[0].added == 10


def test_strength_upper_resolve():
    doc = load(Path("examples/strength_upper.owf"))
    resolved = resolve(doc, {
        "1RM bench press": "100kg",
        "bodyweight": "80kg",
    })
    # 80% of 100kg = 80kg
    s0 = resolved.workouts[0].steps[0]
    param = s0.params[0]
    assert isinstance(param, WeightParam)
    assert param.value == 80.0

    # bodyweight(80) + 10kg = 90kg
    s2 = resolved.workouts[0].steps[2]
    param2 = s2.params[0]
    assert isinstance(param2, WeightParam)
    assert param2.value == 90.0


# --- triathlon_brick.owf ---


def test_triathlon_brick():
    doc = load(Path("examples/triathlon_brick.owf"))
    assert doc.metadata.get("description") == "Weekend triathlon brick session"
    assert doc.metadata.get("author") == "Coach Rivera"
    assert len(doc.workouts) == 3

    # Swim
    swim = doc.workouts[0]
    assert swim.name == "Swim"
    assert swim.sport_type == "Open Water Swimming"
    assert swim.metadata.get("location") == "Lake Zurich"

    # Bike — @85% of FTP
    bike = doc.workouts[1]
    assert bike.name == "Bike"
    assert bike.sport_type == "Cycling"
    bike_step = bike.steps[1]
    assert isinstance(bike_step.params[0], PercentOfParam)
    assert bike_step.params[0].percent == 85
    assert bike_step.params[0].variable == "FTP"

    # Brick Run — pace
    run_w = doc.workouts[2]
    assert run_w.name == "Brick Run"
    assert run_w.sport_type == "Running"
    run_step = run_w.steps[0]
    assert run_step.distance.value == 3
    assert run_step.distance.unit == "km"
    assert isinstance(run_step.params[0], PaceParam)
    assert run_step.params[0].pace == Pace(minutes=5, seconds=0, unit="km")


def test_triathlon_brick_resolve():
    doc = load(Path("examples/triathlon_brick.owf"))
    resolved = resolve(doc, {"FTP": "230W"})
    # 85% of 230W = 195.5 → 196W
    bike_step = resolved.workouts[1].steps[1]
    param = bike_step.params[0]
    assert isinstance(param, PowerParam)
    assert param.value == 196


# --- pyramid_intervals.owf ---


def test_pyramid_intervals():
    doc = load(Path("examples/pyramid_intervals.owf"))
    assert len(doc.workouts) == 1

    w = doc.workouts[0]
    assert w.name == "Pyramid Intervals"
    assert w.sport_type == "Running"
    assert len(w.steps) == 3
    assert isinstance(w.steps[0], Step)  # Warmup
    assert isinstance(w.steps[2], Step)  # Cooldown

    # outer repeat: 3x
    outer = w.steps[1]
    assert isinstance(outer, RepeatBlock)
    assert outer.count == 3
    assert len(outer.steps) == 4

    # nested repeat: 2x (first)
    inner_first = outer.steps[0]
    assert isinstance(inner_first, RepeatBlock)
    assert inner_first.count == 2
    assert len(inner_first.steps) == 2
    assert inner_first.steps[0].action == "Run"
    assert inner_first.steps[0].duration.seconds == 30
    assert inner_first.steps[1].action == "Recover"
    assert inner_first.steps[1].duration.seconds == 30

    # middle steps: 1min durations
    assert outer.steps[1].action == "Run"
    assert outer.steps[1].duration.seconds == 60
    assert outer.steps[2].action == "Recover"
    assert outer.steps[2].duration.seconds == 60

    # nested repeat: 2x (second)
    inner_last = outer.steps[3]
    assert isinstance(inner_last, RepeatBlock)
    assert inner_last.count == 2


# --- crossfit_benchmarks.owf ---


def test_crossfit_benchmarks():
    doc = load(Path("examples/crossfit_benchmarks.owf"))
    assert len(doc.workouts) == 3
    assert all(w.sport_type == "HIIT" for w in doc.workouts)

    # Fran: for-time with 3x repeat
    fran = doc.workouts[0]
    assert fran.name == "Fran"
    assert len(fran.steps) == 1
    ft = fran.steps[0]
    assert isinstance(ft, ForTime)
    assert ft.time_cap.seconds == 600  # 10min

    # Murph: for-time 60min
    murph = doc.workouts[1]
    assert murph.name == "Murph"
    assert murph.rpe == 10
    assert murph.metadata.get("source") == "CrossFit Hero WOD"
    ft2 = murph.steps[0]
    assert isinstance(ft2, ForTime)
    assert ft2.time_cap.seconds == 3600  # 60min
    assert len(ft2.steps) == 5
    assert ft2.steps[0].action == "Run"
    assert ft2.steps[1].action == "Pull-Up"
    assert ft2.steps[1].reps == 100
    assert ft2.steps[2].action == "Push-Up"
    assert ft2.steps[2].reps == 200
    assert ft2.steps[3].action == "Air Squat"
    assert ft2.steps[3].reps == 300
    assert ft2.steps[4].action == "Run"

    # DT: for-time 20min with 5x repeat
    dt = doc.workouts[2]
    assert dt.name == "DT"
    ft3 = dt.steps[0]
    assert isinstance(ft3, ForTime)
    assert ft3.time_cap.seconds == 1200  # 20min
    repeat = ft3.steps[0]
    assert isinstance(repeat, RepeatBlock)
    assert repeat.count == 5
    assert repeat.steps[0].action == "Deadlift"
    assert repeat.steps[0].reps == 12
    assert repeat.steps[1].action == "Hang Clean"
    assert repeat.steps[2].action == "Push Jerk"


def test_crossfit_benchmarks_notes():
    doc = load(Path("examples/crossfit_benchmarks.owf"))
    murph = doc.workouts[1]
    all_notes = murph.notes
    assert any("Partition" in n for n in all_notes)


# --- emom_amrap.owf ---


def test_emom_amrap():
    doc = load(Path("examples/emom_amrap.owf"))
    assert len(doc.workouts) == 4

    # EMOM Strength: every 1min for 10min
    emom_w = doc.workouts[0]
    assert emom_w.name == "EMOM Strength"
    assert len(emom_w.steps) == 1
    emom = emom_w.steps[0]
    assert isinstance(emom, Interval)
    assert emom.interval.seconds == 60
    assert emom.duration.seconds == 600  # 10min
    assert not emom.is_alternating

    # Alternating EMOM: every 1min for 12min with 3 children
    alt = doc.workouts[1]
    assert alt.name == "Alternating EMOM"
    emom2 = alt.steps[0]
    assert isinstance(emom2, Interval)
    assert emom2.duration.seconds == 720
    assert len(emom2.steps) == 3
    assert emom2.is_alternating

    # Cindy: AMRAP 20min
    cindy = doc.workouts[2]
    assert cindy.name == "Cindy"
    amrap = cindy.steps[0]
    assert isinstance(amrap, AMRAP)
    assert amrap.duration.seconds == 1200  # 20min
    assert len(amrap.steps) == 3

    # Custom Interval: every 2min for 20min
    custom = doc.workouts[3]
    assert custom.name == "Custom Interval"
    interval = custom.steps[0]
    assert isinstance(interval, Interval)
    assert interval.interval.seconds == 120
    assert interval.duration.seconds == 1200


# --- strength_lower.owf ---


def test_strength_lower():
    doc = load(Path("examples/strength_lower.owf"))
    assert len(doc.workouts) == 1

    w = doc.workouts[0]
    assert w.name == "Lower Body"
    assert w.sport_type == "Strength Training"
    assert w.rir == 1

    # Back Squat 5x5rep @85% of 1RM back squat @rest 3min
    s0 = w.steps[0]
    assert s0.action == "Back Squat"
    assert s0.sets == 5
    assert s0.reps == 5
    assert s0.rest.seconds == 180
    assert isinstance(s0.params[0], PercentOfParam)
    assert s0.params[0].percent == 85

    # RPE on calf raise
    s4 = w.steps[4]
    assert s4.action == "Standing Calf Raise"
    rpe_params = [p for p in s4.params if isinstance(p, RPEParam)]
    assert len(rpe_params) == 1
    assert rpe_params[0].value == 8


def test_strength_lower_resolve():
    doc = load(Path("examples/strength_lower.owf"))
    resolved = resolve(doc, {
        "1RM back squat": "140kg",
        "1RM deadlift": "180kg",
    })
    # 85% of 140kg = 119kg
    s0 = resolved.workouts[0].steps[0]
    param = s0.params[0]
    assert isinstance(param, WeightParam)
    assert param.value == 119.0

    # 60% of 180kg = 108kg
    s1 = resolved.workouts[0].steps[1]
    param1 = s1.params[0]
    assert isinstance(param1, WeightParam)
    assert param1.value == 108.0


# --- full_body_circuit.owf ---


def test_full_body_circuit():
    doc = load(Path("examples/full_body_circuit.owf"))
    assert len(doc.workouts) == 1

    w = doc.workouts[0]
    assert w.name == "Full Body Circuit"
    assert w.sport_type == "HIIT"
    assert w.rpe == 8

    # 4x: with style=circuit
    circuit = w.steps[1]  # steps[0] is Warmup
    assert isinstance(circuit, RepeatBlock)
    assert circuit.count == 4
    assert circuit.style == "circuit"
    assert len(circuit.steps) == 5


# --- Program examples ---


def test_strength_program():
    from owf.ast.base import Program

    prog = load(Path("examples/strength_program.owfp"))
    assert isinstance(prog, Program)
    assert prog.name == "Upper Lower Hypertrophy"
    assert prog.duration == "4 weeks"
    assert len(prog.progression_rules) == 3
    assert prog.deload_rule is not None
    assert prog.deload_rule.week == 4
    assert prog.deload_rule.multiplier == 0.8
    assert len(prog.weeks) == 4
    assert prog.weeks[0].is_template is True
    assert len(prog.weeks[0].workouts) == 4
    assert prog.weeks[3].is_deload is True


def test_push_pull_legs_program():
    from owf.ast.base import Program

    prog = load(Path("examples/push_pull_legs.owfp"))
    assert isinstance(prog, Program)
    assert prog.name == "Push Pull Legs"
    assert prog.is_cycle is True
    assert len(prog.weeks) == 1
    assert prog.weeks[0].name == "Cycle"
    assert len(prog.weeks[0].workouts) == 3


def test_endurance_program():
    from owf.ast.base import Program

    prog = load(Path("examples/endurance_program.owfp"))
    assert isinstance(prog, Program)
    assert prog.name == "Marathon Build"
    assert prog.duration == "12 weeks"
    assert len(prog.progression_rules) == 1
    assert prog.progression_rules[0].action == "Run"
    assert prog.progression_rules[0].direction == "-"
    assert prog.progression_rules[0].unit == "s"
    assert len(prog.weeks) == 4
