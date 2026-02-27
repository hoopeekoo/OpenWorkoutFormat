"""Step AST nodes — the individual actions in a workout."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from owf.ast.params import Param
from owf.errors import SourceSpan
from owf.units import Distance, Duration


@dataclass(frozen=True, slots=True)
class EnduranceStep:
    """An endurance step: action + duration/distance + params.

    Examples: bike 5min @200W, run 10km @4:30/km, warmup 15min @easy
    """

    action: str  # run, bike, swim, warmup, cooldown, recover, etc.
    duration: Duration | None = None
    distance: Distance | None = None
    params: tuple[Param, ...] = ()
    notes: tuple[str, ...] = ()
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class StrengthStep:
    """A strength step: exercise + sets x reps + params.

    Examples: bench press 3x8rep @80kg rest:90s
    """

    exercise: str
    sets: int | None = None
    reps: int | str | None = None  # int or "max"
    duration: Duration | None = None  # for timed sets
    params: tuple[Param, ...] = ()
    rest: Duration | None = None
    notes: tuple[str, ...] = ()
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class RestStep:
    """A rest step: rest 5min."""

    duration: Duration
    notes: tuple[str, ...] = ()
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class RepeatStep:
    """A repeat block: Nx: with sub-steps."""

    count: int
    steps: tuple[Any, ...] = ()  # Step | Block
    notes: tuple[str, ...] = ()
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


# Union type for all steps
Step = EnduranceStep | StrengthStep | RestStep | RepeatStep
