"""Tests for the expression resolver."""

import pytest

from owf.ast.params import (
    HeartRateParam,
    PowerParam,
    WeightParam,
)
from owf.ast.steps import EnduranceStep, StrengthStep
from owf.errors import ResolveError
from owf.parser.step_parser import parse_document
from owf.resolver import resolve


def test_resolve_percentage_of_ftp():
    text = "# Ride [bike]\n\n- bike 5min @80% of FTP"
    doc = parse_document(text)
    resolved = resolve(doc, {"FTP": "250W"})
    step = resolved.workouts[0].steps[0]
    assert isinstance(step, EnduranceStep)
    param = step.params[0]
    assert isinstance(param, PowerParam)
    assert param.value == 200.0


def test_resolve_percentage_of_1rm():
    text = "# Strength\n\n- Bench Press 3x8rep @80% of 1RM bench press"
    doc = parse_document(text)
    resolved = resolve(doc, {"1RM bench press": "100kg"})
    step = resolved.workouts[0].steps[0]
    assert isinstance(step, StrengthStep)
    param = step.params[0]
    assert isinstance(param, WeightParam)
    assert param.value == 80.0
    assert param.unit == "kg"


def test_resolve_percentage_of_max_hr():
    text = "# Run\n\n- run 10min @70% of max HR"
    doc = parse_document(text)
    resolved = resolve(doc, {"max HR": "185bpm"})
    step = resolved.workouts[0].steps[0]
    param = step.params[0]
    assert isinstance(param, HeartRateParam)
    assert param.value == 129  # int(70% of 185)


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
    text = "# Ride [bike]\n\n- bike 5min @80% of FTP"
    doc = parse_document(text)
    resolved = resolve(doc, {"FTP": "300W"})
    step = resolved.workouts[0].steps[0]
    param = step.params[0]
    assert isinstance(param, PowerParam)
    assert param.value == 240.0


def test_resolve_undefined_variable():
    text = "# Ride [bike]\n\n- bike 5min @80% of FTP"
    doc = parse_document(text)
    with pytest.raises(ResolveError, match="Undefined variable"):
        resolve(doc)


def test_resolve_literal_unchanged():
    text = "# Ride [bike]\n\n- bike 5min @200W"
    doc = parse_document(text)
    resolved = resolve(doc)
    step = resolved.workouts[0].steps[0]
    param = step.params[0]
    assert isinstance(param, PowerParam)
    assert param.value == 200


def test_resolve_zone_unchanged():
    text = "# Run\n\n- run 10min @Z2"
    doc = parse_document(text)
    resolved = resolve(doc)
    from owf.ast.params import ZoneParam

    step = resolved.workouts[0].steps[0]
    param = step.params[0]
    assert isinstance(param, ZoneParam)
    assert param.zone == "Z2"
