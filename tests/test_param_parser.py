"""Tests for the parameter parser."""

import pytest

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
from owf.errors import ParseError
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


def test_zone_param():
    params, rest = parse_params(["@Z2"])
    assert len(params) == 1
    assert isinstance(params[0], ZoneParam)
    assert params[0].zone == "Z2"


def test_hr_bpm():
    params, rest = parse_params(["@140bpm"])
    assert len(params) == 1
    assert isinstance(params[0], HeartRateParam)
    assert params[0].value == 140


def test_rpe():
    params, rest = parse_params(["@RPE", "7"])
    assert len(params) == 1
    assert isinstance(params[0], RPEParam)
    assert params[0].value == 7.0


def test_power_watts():
    params, rest = parse_params(["@200W"])
    assert len(params) == 1
    assert isinstance(params[0], PowerParam)
    assert params[0].value == 200


def test_weight_kg():
    params, rest = parse_params(["@80kg"])
    assert len(params) == 1
    assert isinstance(params[0], WeightParam)
    assert params[0].value == 80
    assert params[0].unit == "kg"


def test_weight_lb():
    params, rest = parse_params(["@175lb"])
    assert len(params) == 1
    assert isinstance(params[0], WeightParam)
    assert params[0].value == 175
    assert params[0].unit == "lb"


def test_percentage_of_ftp():
    params, rest = parse_params(["@80%", "of", "FTP"])
    assert len(params) == 1
    assert isinstance(params[0], PercentOfParam)
    assert params[0].percent == 80
    assert params[0].variable == "FTP"


def test_percentage_of_1rm():
    params, rest = parse_params(["@70%", "of", "1RM", "bench", "press"])
    assert len(params) == 1
    assert isinstance(params[0], PercentOfParam)
    assert params[0].percent == 70
    assert params[0].variable == "1RM bench press"


def test_percentage_of_max_hr():
    params, rest = parse_params(["@70%", "of", "max", "HR"])
    assert len(params) == 1
    assert isinstance(params[0], PercentOfParam)
    assert params[0].percent == 70
    assert params[0].variable == "max HR"


def test_bodyweight_plus():
    params, rest = parse_params(["@bodyweight", "+", "20kg"])
    assert len(params) == 1
    assert isinstance(params[0], BodyweightPlusParam)
    assert params[0].added == 20
    assert params[0].unit == "kg"


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


def test_multiple_step_params():
    params, rest = parse_params(["@15kg", "@RIR", "3", "rest:60s"])
    assert len(params) == 2
    assert isinstance(params[0], WeightParam)
    assert isinstance(params[1], RIRParam)
    assert rest is not None


def test_rejected_intensity_easy():
    with pytest.raises(ParseError, match="no longer supported"):
        parse_params(["@easy"])


def test_rejected_intensity_hard():
    with pytest.raises(ParseError, match="no longer supported"):
        parse_params(["@hard"])


def test_rejected_intensity_threshold():
    with pytest.raises(ParseError, match="no longer supported"):
        parse_params(["@threshold"])


def test_rejected_unknown_param():
    with pytest.raises(ParseError, match="Unknown parameter"):
        parse_params(["@FTP"])


def test_percent_of_stops_at_next_param():
    """Variable name collection stops at the next @ token."""
    params, rest = parse_params(["@80%", "of", "FTP", "@Z2"])
    assert len(params) == 2
    assert isinstance(params[0], PercentOfParam)
    assert params[0].variable == "FTP"
    assert isinstance(params[1], ZoneParam)


def test_percent_of_stops_at_rest():
    """Variable name collection stops at rest: token."""
    params, rest = parse_params(["@80%", "of", "1RM", "bench", "press", "rest:90s"])
    assert len(params) == 1
    assert isinstance(params[0], PercentOfParam)
    assert params[0].variable == "1RM bench press"
    assert rest is not None
    assert rest.seconds == 90
