"""Tests for the expression resolver."""

import pytest

from owf.ast.params import (
    HeartRateParam,
    PowerParam,
    WeightParam,
)
from owf.ast.steps import Step
from owf.errors import ResolveError
from owf.parser.step_parser import parse_document
from owf.resolver import resolve


def test_resolve_percentage_of_ftp():
    text = "# Ride [bike]\n\n- Bike 5min @80% FTP"
    doc = parse_document(text)
    resolved = resolve(doc, {"FTP": "250W"})
    step = resolved.workouts[0].steps[0]
    assert isinstance(step, Step)
    param = step.params[0]
    assert isinstance(param, PowerParam)
    assert param.value == 200.0


def test_resolve_percentage_of_1rm():
    text = "# Strength\n\n- Bench Press 3x8rep @80% 1RM bench press"
    doc = parse_document(text)
    resolved = resolve(doc, {"1RM bench press": "100kg"})
    step = resolved.workouts[0].steps[0]
    assert isinstance(step, Step)
    param = step.params[0]
    assert isinstance(param, WeightParam)
    assert param.value == 80.0
    assert param.unit == "kg"


def test_resolve_percentage_of_max_hr():
    text = "# Run\n\n- Run 10min @70% max HR"
    doc = parse_document(text)
    resolved = resolve(doc, {"max HR": "185bpm"})
    step = resolved.workouts[0].steps[0]
    param = step.params[0]
    assert isinstance(param, HeartRateParam)
    assert param.value == 130  # round(70% * 185) = round(129.5)


def test_resolve_bodyweight_plus():
    text = "# Gym\n\n- Dip 3x8rep @bodyweight + 20kg"
    doc = parse_document(text)
    resolved = resolve(doc, {"bodyweight": "80kg"})
    step = resolved.workouts[0].steps[0]
    param = step.params[0]
    assert isinstance(param, WeightParam)
    assert param.value == 100.0
    assert param.unit == "kg"


def test_resolve_with_different_ftp():
    text = "# Ride [bike]\n\n- Bike 5min @80% FTP"
    doc = parse_document(text)
    resolved = resolve(doc, {"FTP": "300W"})
    step = resolved.workouts[0].steps[0]
    param = step.params[0]
    assert isinstance(param, PowerParam)
    assert param.value == 240.0


def test_resolve_undefined_variable():
    text = "# Ride [bike]\n\n- Bike 5min @80% FTP"
    doc = parse_document(text)
    with pytest.raises(ResolveError, match="Undefined variable"):
        resolve(doc)


def test_resolve_literal_unchanged():
    text = "# Ride [bike]\n\n- Bike 5min @200W"
    doc = parse_document(text)
    resolved = resolve(doc)
    step = resolved.workouts[0].steps[0]
    param = step.params[0]
    assert isinstance(param, PowerParam)
    assert param.value == 200


def test_resolve_zone_unchanged():
    text = "# Run\n\n- Run 10min @Z2"
    doc = parse_document(text)
    resolved = resolve(doc)
    from owf.ast.params import ZoneParam

    step = resolved.workouts[0].steps[0]
    param = step.params[0]
    assert isinstance(param, ZoneParam)
    assert param.zone == "Z2"


# ===== Program path =====


def test_resolve_program_percent_of():
    """resolve() traverses Program → weeks → workouts → steps."""
    from owf.ast.base import Program

    text = (
        "## Block (4 weeks)\n\n"
        "--- Week 1 ---\n\n"
        "# Ride [Cycling]\n\n- Bike 10min @80% FTP\n"
    )
    doc = parse_document(text)
    assert isinstance(doc, Program)
    resolved = resolve(doc, {"FTP": "250W"})
    assert isinstance(resolved, Program)
    step = resolved.weeks[0].workouts[0].steps[0]
    assert isinstance(step, Step)
    param = step.params[0]
    assert isinstance(param, PowerParam)
    assert param.value == 200.0


# ===== Bad variable value =====


def test_resolve_bad_variable_value():
    """Unparseable variable value raises ResolveError."""
    text = "# Ride\n\n- Bike 5min @80% FTP"
    doc = parse_document(text)
    with pytest.raises(ResolveError, match="Cannot parse variable value"):
        resolve(doc, {"FTP": "invalid"})


# ===== BodyweightPlusParam with lb unit =====


def test_resolve_bodyweight_plus_lb():
    """@bodyweight + 45lb resolves with lb unit."""
    text = "# Gym\n\n- Dip 3x8rep @bodyweight + 45lb"
    doc = parse_document(text)
    resolved = resolve(doc, {"bodyweight": "180lb"})
    step = resolved.workouts[0].steps[0]
    param = step.params[0]
    assert isinstance(param, WeightParam)
    assert param.value == 225.0
    assert param.unit == "lb"
