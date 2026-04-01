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
    SetTypeParam,
    TempoParam,
    TypedPercentParam,
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
    assert params[0].value == 7


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
    params, rest = parse_params(["@rest", "90s"])
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
    params, rest = parse_params(["@80kg", "@rest", "60s"])
    assert len(params) == 1
    assert isinstance(params[0], WeightParam)
    assert rest is not None
    assert rest.seconds == 60


def test_multiple_step_params():
    params, rest = parse_params(["@15kg", "@RIR", "3", "@rest", "60s"])
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
    """@threshold as standalone is unknown (use @90%TP for threshold pace)."""
    with pytest.raises(ParseError, match="Unknown parameter"):
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
    """Variable name collection stops at @rest token."""
    params, rest = parse_params(["@80%", "of", "1RM", "bench", "press", "@rest", "90s"])
    assert len(params) == 1
    assert isinstance(params[0], PercentOfParam)
    assert params[0].variable == "1RM bench press"
    assert rest is not None
    assert rest.seconds == 90


# ===== Zone metric qualifier =====


def test_zone_with_power_metric():
    params, rest = parse_params(["@Z2:power"])
    assert len(params) == 1
    assert isinstance(params[0], ZoneParam)
    assert params[0].zone == "Z2"
    assert params[0].metric == "power"


def test_zone_with_hr_metric():
    params, rest = parse_params(["@Z3:hr"])
    assert len(params) == 1
    assert isinstance(params[0], ZoneParam)
    assert params[0].zone == "Z3"
    assert params[0].metric == "hr"


def test_zone_with_pace_metric():
    params, rest = parse_params(["@Z4:pace"])
    assert len(params) == 1
    assert isinstance(params[0], ZoneParam)
    assert params[0].zone == "Z4"
    assert params[0].metric == "pace"


def test_zone_unqualified_backward_compat():
    """Bare @Z2 still works with metric=None."""
    params, rest = parse_params(["@Z2"])
    assert len(params) == 1
    assert isinstance(params[0], ZoneParam)
    assert params[0].zone == "Z2"
    assert params[0].metric is None


def test_zone_invalid_metric():
    with pytest.raises(ParseError, match="Unknown zone metric"):
        parse_params(["@Z2:invalid"])


# ===== Typed percentage params =====


def test_typed_percent_ftp():
    params, rest = parse_params(["@95%FTP"])
    assert len(params) == 1
    assert isinstance(params[0], TypedPercentParam)
    assert params[0].percent == 95
    assert params[0].target == "FTP"


def test_typed_percent_lthr():
    params, rest = parse_params(["@88%LTHR"])
    assert len(params) == 1
    assert isinstance(params[0], TypedPercentParam)
    assert params[0].percent == 88
    assert params[0].target == "LTHR"


def test_typed_percent_maxhr():
    params, rest = parse_params(["@92%maxHR"])
    assert len(params) == 1
    assert isinstance(params[0], TypedPercentParam)
    assert params[0].percent == 92
    assert params[0].target == "maxHR"


def test_typed_percent_tp():
    params, rest = parse_params(["@90%TP"])
    assert len(params) == 1
    assert isinstance(params[0], TypedPercentParam)
    assert params[0].percent == 90
    assert params[0].target == "TP"


def test_typed_percent_1rm():
    params, rest = parse_params(["@85%1RM"])
    assert len(params) == 1
    assert isinstance(params[0], TypedPercentParam)
    assert params[0].percent == 85
    assert params[0].target == "1RM"


def test_typed_percent_decimal():
    params, rest = parse_params(["@87.5%FTP"])
    assert len(params) == 1
    assert isinstance(params[0], TypedPercentParam)
    assert params[0].percent == 87.5


def test_typed_percent_coexists_with_generic():
    """@95%FTP (typed) and @80% of FTP (generic) both work."""
    params, rest = parse_params(["@95%FTP", "@80%", "of", "FTP"])
    assert len(params) == 2
    assert isinstance(params[0], TypedPercentParam)
    assert isinstance(params[1], PercentOfParam)


# ===== Tempo param =====


def test_tempo_param():
    params, rest = parse_params(["@tempo", "31X0"])
    assert len(params) == 1
    assert isinstance(params[0], TempoParam)
    assert params[0].value == "31X0"


def test_tempo_with_hyphens():
    params, rest = parse_params(["@tempo", "3-1-X-0"])
    assert len(params) == 1
    assert isinstance(params[0], TempoParam)
    assert params[0].value == "3-1-X-0"


def test_tempo_digits_only():
    params, rest = parse_params(["@tempo", "4010"])
    assert len(params) == 1
    assert isinstance(params[0], TempoParam)
    assert params[0].value == "4010"


def test_tempo_missing_value():
    with pytest.raises(ParseError, match="Expected tempo value"):
        parse_params(["@tempo"])


def test_tempo_with_other_params():
    params, rest = parse_params(["@80kg", "@tempo", "31X0", "@rest", "90s"])
    assert len(params) == 2
    assert isinstance(params[0], WeightParam)
    assert isinstance(params[1], TempoParam)
    assert rest is not None
    assert rest.seconds == 90


# ===== Set type params =====


def test_set_type_warmup():
    params, rest = parse_params(["@warmup"])
    assert len(params) == 1
    assert isinstance(params[0], SetTypeParam)
    assert params[0].set_type == "warmup"


def test_set_type_drop():
    params, rest = parse_params(["@drop"])
    assert len(params) == 1
    assert isinstance(params[0], SetTypeParam)
    assert params[0].set_type == "drop"


def test_set_type_failure():
    params, rest = parse_params(["@failure"])
    assert len(params) == 1
    assert isinstance(params[0], SetTypeParam)
    assert params[0].set_type == "failure"


def test_set_type_cluster():
    params, rest = parse_params(["@cluster"])
    assert len(params) == 1
    assert isinstance(params[0], SetTypeParam)
    assert params[0].set_type == "cluster"


def test_set_type_rest_pause():
    """Hyphenated OWF syntax maps to underscore in AST."""
    params, rest = parse_params(["@rest-pause"])
    assert len(params) == 1
    assert isinstance(params[0], SetTypeParam)
    assert params[0].set_type == "rest_pause"


def test_set_type_myo_rep():
    """Hyphenated OWF syntax maps to underscore in AST."""
    params, rest = parse_params(["@myo-rep"])
    assert len(params) == 1
    assert isinstance(params[0], SetTypeParam)
    assert params[0].set_type == "myo_rep"


def test_set_type_with_other_params():
    params, rest = parse_params(["@60kg", "@warmup", "@rest", "90s"])
    assert len(params) == 2
    assert isinstance(params[0], WeightParam)
    assert isinstance(params[1], SetTypeParam)
    assert params[1].set_type == "warmup"
    assert rest is not None


# ===== Pace units /500m and /100m =====


def test_pace_500m():
    params, rest = parse_params(["@1:45/500m"])
    assert len(params) == 1
    assert isinstance(params[0], PaceParam)
    assert params[0].pace == Pace(minutes=1, seconds=45, unit="500m")


def test_pace_100m():
    params, rest = parse_params(["@1:32/100m"])
    assert len(params) == 1
    assert isinstance(params[0], PaceParam)
    assert params[0].pace == Pace(minutes=1, seconds=32, unit="100m")


# ===== Complex combinations =====


def test_full_strength_step_params():
    """All strength params together: weight, tempo, set type, RIR, rest."""
    params, rest = parse_params(
        ["@80kg", "@tempo", "31X0", "@warmup", "@RIR", "3", "@rest", "2min"]
    )
    assert len(params) == 4
    assert isinstance(params[0], WeightParam)
    assert isinstance(params[1], TempoParam)
    assert isinstance(params[2], SetTypeParam)
    assert isinstance(params[3], RIRParam)
    assert rest is not None
    assert rest.seconds == 120


def test_full_endurance_step_params():
    """All endurance params together: zone metric, typed percent."""
    params, rest = parse_params(["@Z2:power", "@88%LTHR"])
    assert len(params) == 2
    assert isinstance(params[0], ZoneParam)
    assert params[0].metric == "power"
    assert isinstance(params[1], TypedPercentParam)
    assert params[1].target == "LTHR"
