"""Tests for the five new example files covering all spec features."""

from __future__ import annotations

from pathlib import Path

from owf.ast.blocks import EMOM, ForTime
from owf.ast.expressions import BinOp, Literal, Percentage, VarRef
from owf.ast.params import (
    HeartRateParam,
    IntensityParam,
    PaceParam,
    PowerParam,
    RIRParam,
    WeightParam,
)
from owf.ast.steps import EnduranceStep, RepeatStep, StrengthStep
from owf.loader import load
from owf.resolver import resolve
from owf.units import Pace

# --- heart_rate_run.owf ---


def test_heart_rate_run():
    doc = load(Path("examples/heart_rate_run.owf"))
    assert doc.metadata == {}
    assert len(doc.workouts) == 1

    w = doc.workouts[0]
    assert w.name == "HR Zone Run"
    assert w.workout_type == "run"
    assert len(w.steps) == 8
    assert all(isinstance(s, EnduranceStep) for s in w.steps)

    # @140bpm
    s1 = w.steps[1]
    assert s1.action == "run"
    assert s1.duration.seconds == 600
    assert isinstance(s1.params[0], HeartRateParam)
    assert isinstance(s1.params[0].value, Literal)
    assert s1.params[0].value.value == 140
    assert s1.params[0].value.unit == "bpm"

    # @70% of max HR
    s2 = w.steps[2]
    assert isinstance(s2.params[0], HeartRateParam)
    assert isinstance(s2.params[0].value, Percentage)
    assert s2.params[0].value.percent == 70
    assert isinstance(s2.params[0].value.of, VarRef)
    assert s2.params[0].value.of.name == "max HR"

    # @Z3
    s3 = w.steps[3]
    assert isinstance(s3.params[0], HeartRateParam)
    assert s3.params[0].value == "Z3"

    # @threshold
    s4 = w.steps[4]
    assert isinstance(s4.params[0], IntensityParam)
    assert s4.params[0].name == "threshold"

    # @tempo
    s5 = w.steps[5]
    assert isinstance(s5.params[0], IntensityParam)
    assert s5.params[0].name == "tempo"

    # @pace:5:00/km
    s6 = w.steps[6]
    assert s6.distance.value == 5
    assert s6.distance.unit == "km"
    assert isinstance(s6.params[0], PaceParam)
    assert s6.params[0].pace == Pace(minutes=5, seconds=0, unit="km")

    # workout note
    note = "Great session for building aerobic base and pace awareness."
    assert note in w.notes or note in w.steps[-1].notes


def test_heart_rate_run_resolve():
    doc = load(Path("examples/heart_rate_run.owf"))
    resolved = resolve(doc, {"max HR": "190bpm"})
    # 70% of 190bpm = 133bpm
    s2 = resolved.workouts[0].steps[2]
    param = s2.params[0]
    assert isinstance(param, HeartRateParam)
    assert isinstance(param.value, Literal)
    assert param.value.value == 133.0
    assert param.value.unit == "bpm"


# --- gym_session.owf ---


def test_gym_session():
    doc = load(Path("examples/gym_session.owf"))
    assert doc.metadata == {}
    assert len(doc.workouts) == 1

    w = doc.workouts[0]
    assert w.name == "Full Gym Session"
    assert w.workout_type == "strength"
    assert len(w.steps) == 6
    assert all(isinstance(s, StrengthStep) for s in w.steps)

    # reps-only: pull-up 100rep
    s0 = w.steps[0]
    assert s0.exercise == "pull-up"
    assert s0.reps == 100
    assert s0.sets is None

    # BinOp: dip 3x8rep @bodyweight + 20kg rest:90s
    s1 = w.steps[1]
    assert s1.exercise == "dip"
    assert s1.sets == 3
    assert s1.reps == 8
    assert s1.rest.seconds == 90
    assert isinstance(s1.params[0], PowerParam)
    assert isinstance(s1.params[0].value, BinOp)
    assert s1.params[0].value.op == "+"
    assert isinstance(s1.params[0].value.left, VarRef)
    assert s1.params[0].value.left.name == "bodyweight"
    assert isinstance(s1.params[0].value.right, Literal)
    assert s1.params[0].value.right.value == 20
    assert s1.params[0].value.right.unit == "kg"

    # timed set: plank 60s
    s2 = w.steps[2]
    assert s2.exercise == "plank"
    assert s2.duration.seconds == 60
    assert s2.reps is None
    assert s2.sets is None

    # RIR: back squat 5x5rep @RIR 3 rest:120s
    s3 = w.steps[3]
    assert s3.exercise == "back squat"
    assert s3.sets == 5
    assert s3.reps == 5
    assert s3.rest.seconds == 120
    assert isinstance(s3.params[0], RIRParam)
    assert s3.params[0].value == 3

    # RIR: romanian deadlift 3x10rep @60kg @RIR 2 rest:90s
    s4 = w.steps[4]
    assert s4.exercise == "romanian deadlift"
    rir_params = [p for p in s4.params if isinstance(p, RIRParam)]
    assert len(rir_params) == 1
    assert rir_params[0].value == 2

    # maxrep: face pull 3xmaxrep @15kg rest:60s
    s5 = w.steps[5]
    assert s5.exercise == "face pull"
    assert s5.sets == 3
    assert s5.reps == "max"
    assert s5.rest.seconds == 60
    assert isinstance(s5.params[0], WeightParam)
    assert s5.params[0].value == Literal(value=15, unit="kg")


def test_gym_session_resolve():
    doc = load(Path("examples/gym_session.owf"))
    resolved = resolve(doc, {"bodyweight": "80kg"})
    # bodyweight(80kg) + 20kg = 100kg
    s1 = resolved.workouts[0].steps[1]
    param = s1.params[0]
    assert isinstance(param, PowerParam)
    assert isinstance(param.value, Literal)
    assert param.value.value == 100.0
    assert param.value.unit == "kg"


# --- triathlon.owf ---


def test_triathlon():
    doc = load(Path("examples/triathlon.owf"))
    assert doc.metadata == {}
    assert len(doc.workouts) == 4

    # Swim Intervals
    swim = doc.workouts[0]
    assert swim.name == "Swim Intervals"
    assert swim.workout_type == "swim"
    assert len(swim.steps) == 3
    assert isinstance(swim.steps[0], EnduranceStep)
    assert swim.steps[0].distance.value == 200
    assert swim.steps[0].distance.unit == "m"
    assert isinstance(swim.steps[1], RepeatStep)
    assert swim.steps[1].count == 4
    assert len(swim.steps[1].steps) == 2
    assert swim.steps[1].steps[0].action == "swim"

    # Rowing Warmup
    row_w = doc.workouts[1]
    assert row_w.name == "Rowing Warmup"
    assert row_w.workout_type == "row"
    row_last = row_w.steps[2]
    assert isinstance(row_last, EnduranceStep)
    assert row_last.action == "row"
    assert row_last.distance.value == 100
    assert row_last.distance.unit == "yd"

    # Bike Tempo — @85% of FTP
    bike = doc.workouts[2]
    assert bike.name == "Bike Tempo"
    assert bike.workout_type == "bike"
    bike_step = bike.steps[1]
    assert isinstance(bike_step.params[0], PowerParam)
    assert isinstance(bike_step.params[0].value, Percentage)
    assert bike_step.params[0].value.percent == 85
    assert bike_step.params[0].value.of == VarRef(name="FTP")

    # Brick Run — 3mi @7:00/mi
    run_w = doc.workouts[3]
    assert run_w.name == "Brick Run"
    assert run_w.workout_type == "run"
    run_step = run_w.steps[0]
    assert run_step.distance.value == 3
    assert run_step.distance.unit == "mi"
    assert isinstance(run_step.params[0], PaceParam)
    assert run_step.params[0].pace == Pace(minutes=7, seconds=0, unit="mi")


def test_triathlon_resolve():
    doc = load(Path("examples/triathlon.owf"))
    resolved = resolve(doc, {"FTP": "230W"})
    # 85% of 230W = 195.5W
    bike_step = resolved.workouts[2].steps[1]
    param = bike_step.params[0]
    assert isinstance(param, PowerParam)
    assert isinstance(param.value, Literal)
    assert param.value.value == 195.5
    assert param.value.unit == "W"


# --- pyramid.owf ---


def test_pyramid():
    doc = load(Path("examples/pyramid.owf"))
    assert doc.metadata == {}
    assert len(doc.workouts) == 1

    w = doc.workouts[0]
    assert w.name == "Pyramid Intervals"
    assert w.workout_type is None  # heading without type bracket

    assert len(w.steps) == 3
    assert isinstance(w.steps[0], EnduranceStep)  # warmup
    assert isinstance(w.steps[2], EnduranceStep)  # cooldown

    # outer repeat: 3x
    outer = w.steps[1]
    assert isinstance(outer, RepeatStep)
    assert outer.count == 3
    assert len(outer.steps) == 4

    # nested repeat: 2x (first)
    inner_first = outer.steps[0]
    assert isinstance(inner_first, RepeatStep)
    assert inner_first.count == 2
    assert len(inner_first.steps) == 2
    assert inner_first.steps[0].action == "run"
    assert inner_first.steps[0].duration.seconds == 30
    assert inner_first.steps[1].action == "recover"
    assert inner_first.steps[1].duration.seconds == 30

    # middle steps: 1:00 durations (mm:ss = 60 seconds)
    assert outer.steps[1].action == "run"
    assert outer.steps[1].duration.seconds == 60
    assert outer.steps[2].action == "recover"
    assert outer.steps[2].duration.seconds == 60

    # nested repeat: 2x (second)
    inner_last = outer.steps[3]
    assert isinstance(inner_last, RepeatStep)
    assert inner_last.count == 2


# --- hero_wod.owf ---


def test_hero_wod():
    doc = load(Path("examples/hero_wod.owf"))
    assert len(doc.workouts) == 3
    assert all(w.workout_type == "wod" for w in doc.workouts)

    # DT: for-time 20min containing 5x repeat
    dt = doc.workouts[0]
    assert dt.name == "DT"
    assert len(dt.steps) == 1
    ft = dt.steps[0]
    assert isinstance(ft, ForTime)
    assert ft.time_cap.seconds == 1200  # 20min
    assert len(ft.steps) == 1
    repeat = ft.steps[0]
    assert isinstance(repeat, RepeatStep)
    assert repeat.count == 5
    assert len(repeat.steps) == 3
    assert all(isinstance(s, StrengthStep) for s in repeat.steps)
    assert repeat.steps[0].exercise == "deadlift"
    assert repeat.steps[0].reps == 12
    assert repeat.steps[1].exercise == "hang clean"
    assert repeat.steps[1].reps == 9
    assert repeat.steps[2].exercise == "push jerk"
    assert repeat.steps[2].reps == 6

    # Kalsu: emom 30min + burpee 100rep
    kalsu = doc.workouts[1]
    assert kalsu.name == "Kalsu"
    assert len(kalsu.steps) == 2
    emom = kalsu.steps[0]
    assert isinstance(emom, EMOM)
    assert emom.duration.seconds == 1800  # 30min
    assert len(emom.steps) == 1
    assert emom.steps[0].exercise == "thruster"
    burpee = kalsu.steps[1]
    assert isinstance(burpee, StrengthStep)
    assert burpee.exercise == "burpee"
    assert burpee.reps == 100

    # Filthy Fifty: for-time 35min with 10 movements
    fifty = doc.workouts[2]
    assert fifty.name == "Filthy Fifty"
    assert len(fifty.steps) == 1
    ft2 = fifty.steps[0]
    assert isinstance(ft2, ForTime)
    assert ft2.time_cap.seconds == 2100  # 35min
    assert len(ft2.steps) == 10
    assert all(isinstance(s, StrengthStep) for s in ft2.steps)
    assert ft2.steps[0].exercise == "box jump"
    assert ft2.steps[-1].exercise == "double under"


def test_hero_wod_notes():
    doc = load(Path("examples/hero_wod.owf"))
    kalsu = doc.workouts[1]
    # Multiple notes on the Kalsu workout
    all_notes = kalsu.notes + kalsu.steps[-1].notes
    note1 = "Every minute starts with 5 thrusters; fill remaining time with burpees."
    assert note1 in all_notes
    note2 = "Time cap is 30 minutes \u2014 aim to finish 100 thrusters total."
    assert note2 in all_notes
    assert len([n for n in all_notes if n]) >= 2
