"""Tests for the parameter parser."""

from owf.ast.expressions import Literal, Percentage, VarRef
from owf.ast.params import (
    HeartRateParam,
    IntensityParam,
    PaceParam,
    PowerParam,
    RIRParam,
    RPEParam,
    WeightParam,
)
from owf.parser.param_parser import parse_params
from owf.units import Pace


def test_pace_param():
    params, rest = parse_params(["@4:30/km"])
    assert len(params) == 1
    assert isinstance(params[0], PaceParam)
    assert params[0].pace == Pace(minutes=4, seconds=30, unit="km")


def test_pace_with_prefix():
    params, rest = parse_params(["@pace:4:30/km"])
    assert len(params) == 1
    assert isinstance(params[0], PaceParam)


def test_intensity_param():
    params, rest = parse_params(["@easy"])
    assert len(params) == 1
    assert isinstance(params[0], IntensityParam)
    assert params[0].name == "easy"


def test_hr_zone():
    params, rest = parse_params(["@Z2"])
    assert len(params) == 1
    assert isinstance(params[0], HeartRateParam)
    assert params[0].value == "Z2"


def test_hr_bpm():
    params, rest = parse_params(["@140bpm"])
    assert len(params) == 1
    assert isinstance(params[0], HeartRateParam)
    assert isinstance(params[0].value, Literal)
    assert params[0].value.value == 140
    assert params[0].value.unit == "bpm"


def test_rpe():
    params, rest = parse_params(["@RPE", "7"])
    assert len(params) == 1
    assert isinstance(params[0], RPEParam)
    assert params[0].value == 7.0


def test_power_watts():
    params, rest = parse_params(["@200W"])
    assert len(params) == 1
    assert isinstance(params[0], PowerParam)
    assert isinstance(params[0].value, Literal)
    assert params[0].value.value == 200
    assert params[0].value.unit == "W"


def test_weight_kg():
    params, rest = parse_params(["@80kg"])
    assert len(params) == 1
    assert isinstance(params[0], WeightParam)
    assert isinstance(params[0].value, Literal)
    assert params[0].value.value == 80


def test_percentage_of_variable():
    params, rest = parse_params(["@80%", "of", "FTP"])
    assert len(params) == 1
    assert isinstance(params[0], PowerParam)
    assert isinstance(params[0].value, Percentage)
    assert params[0].value.percent == 80
    assert isinstance(params[0].value.of, VarRef)
    assert params[0].value.of.name == "FTP"


def test_percentage_of_1rm():
    params, rest = parse_params(["@70%", "of", "1RM", "bench", "press"])
    assert len(params) == 1
    assert isinstance(params[0], WeightParam)
    assert isinstance(params[0].value, Percentage)
    assert params[0].value.percent == 70
    assert isinstance(params[0].value.of, VarRef)
    assert params[0].value.of.name == "1RM bench press"


def test_rest_duration():
    params, rest = parse_params(["rest:90s"])
    assert len(params) == 0
    assert rest is not None
    assert rest.seconds == 90


def test_rir_separate_tokens():
    params, rest = parse_params(["@RIR", "2"])
    assert len(params) == 1
    assert isinstance(params[0], RIRParam)
    assert params[0].value == 2


def test_rir_attached():
    params, rest = parse_params(["@RIR2"])
    assert len(params) == 1
    assert isinstance(params[0], RIRParam)
    assert params[0].value == 2


def test_rir_case_insensitive():
    params, rest = parse_params(["@rir", "3"])
    assert len(params) == 1
    assert isinstance(params[0], RIRParam)
    assert params[0].value == 3


def test_rir_zero():
    params, rest = parse_params(["@RIR", "0"])
    assert len(params) == 1
    assert isinstance(params[0], RIRParam)
    assert params[0].value == 0


def test_multiple_params():
    params, rest = parse_params(["@80kg", "rest:60s"])
    assert len(params) == 1
    assert isinstance(params[0], WeightParam)
    assert rest is not None
    assert rest.seconds == 60
