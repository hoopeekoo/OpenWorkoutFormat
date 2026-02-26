"""Parameter AST nodes — the @-prefixed modifiers on steps."""

from __future__ import annotations

from dataclasses import dataclass, field

from owf.ast.expressions import Expression
from owf.errors import SourceSpan
from owf.units import Pace


@dataclass(frozen=True, slots=True)
class PaceParam:
    """Pace parameter, e.g. @4:30/km."""

    pace: Pace
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class PowerParam:
    """Power parameter, e.g. @200W or @80% of FTP."""

    value: Expression
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class HeartRateParam:
    """Heart rate parameter, e.g. @Z2, @140bpm, @70% of max HR."""

    value: Expression | str  # str for zone names like "Z2"
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class WeightParam:
    """Weight parameter, e.g. @80kg, @70% of 1RM."""

    value: Expression
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class RPEParam:
    """RPE parameter, e.g. @RPE 7."""

    value: float
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class IntensityParam:
    """Named intensity, e.g. @easy, @moderate, @hard, @max."""

    name: str
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


# Union type for all parameters
Param = (
    PaceParam | PowerParam | HeartRateParam | WeightParam | RPEParam | IntensityParam
)
