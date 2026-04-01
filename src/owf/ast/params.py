"""Parameter AST nodes — the @-prefixed modifiers on steps."""

from __future__ import annotations

from dataclasses import dataclass, field

from owf.errors import SourceSpan
from owf.units import Pace


@dataclass(frozen=True, slots=True)
class ZoneParam:
    """Heart rate / training zone, e.g. @Z2, @Z4, @Z2:power, @Z3:hr."""

    zone: str  # "Z1", "Z2", etc.
    metric: str | None = None  # "power", "hr", "pace", or None (unqualified)
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class PercentOfParam:
    """Percentage of a named variable, e.g. @80% of FTP, @70% of max HR."""

    percent: float
    variable: str  # "FTP", "LTHR", "max HR", "1RM bench press", etc.
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class PowerParam:
    """Literal power in watts, e.g. @200W."""

    value: int
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class HeartRateParam:
    """Literal heart rate in bpm, e.g. @140bpm."""

    value: int
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class PaceParam:
    """Pace parameter, e.g. @4:30/km."""

    pace: Pace
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class WeightParam:
    """Weight parameter, e.g. @80kg, @175lb."""

    value: float
    unit: str  # "kg", "lb", "lbs"
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class BodyweightPlusParam:
    """Bodyweight plus added weight, e.g. @bodyweight + 20kg."""

    added: float
    unit: str  # "kg", "lb", "lbs"
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class RPEParam:
    """RPE parameter, e.g. @RPE 7."""

    value: int
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class RIRParam:
    """RIR (Reps In Reserve) parameter, e.g. @RIR 2."""

    value: int
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class TypedPercentParam:
    """Typed percentage of a known variable, e.g. @95%FTP, @88%LTHR, @85%1RM.

    Unlike PercentOfParam (which uses generic variable resolution),
    this represents a first-class typed percentage with a known target.
    """

    percent: float
    target: str  # "FTP", "LTHR", "maxHR", "TP", "1RM"
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class TempoParam:
    """Lifting tempo, e.g. @tempo 31X0, @tempo 4-0-1-0."""

    value: str  # "31X0", "4-0-1-0", etc.
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class SetTypeParam:
    """Set type classification, e.g. @warmup, @drop, @failure."""

    set_type: str  # "warmup", "drop", "failure", "cluster", "rest_pause", "myo_rep"
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


# Union type for all parameters
Param = (
    ZoneParam
    | PercentOfParam
    | TypedPercentParam
    | PowerParam
    | HeartRateParam
    | PaceParam
    | WeightParam
    | BodyweightPlusParam
    | RPEParam
    | RIRParam
    | TempoParam
    | SetTypeParam
)
