"""Tests for the expression resolver."""

import pytest

from owf.ast.expressions import Literal
from owf.ast.params import PowerParam, WeightParam
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
    assert isinstance(param.value, Literal)
    assert param.value.value == 200.0
    assert param.value.unit == "W"


def test_resolve_percentage_of_1rm():
    text = "# Strength\n\n- bench press 3x8rep @80% of 1RM bench press"
    doc = parse_document(text)
    resolved = resolve(doc, {"1RM bench press": "100kg"})
    step = resolved.workouts[0].steps[0]
    assert isinstance(step, StrengthStep)
    param = step.params[0]
    assert isinstance(param, WeightParam)
    assert isinstance(param.value, Literal)
    assert param.value.value == 80.0
    assert param.value.unit == "kg"


def test_resolve_with_variables():
    text = "# Ride [bike]\n\n- bike 5min @80% of FTP"
    doc = parse_document(text)
    resolved = resolve(doc, {"FTP": "300W"})
    step = resolved.workouts[0].steps[0]
    param = step.params[0]
    assert isinstance(param, PowerParam)
    assert isinstance(param.value, Literal)
    assert param.value.value == 240.0


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
    assert isinstance(param.value, Literal)
    assert param.value.value == 200
