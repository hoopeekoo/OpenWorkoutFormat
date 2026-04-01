"""Step AST nodes — the individual actions in a workout."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from owf.ast.params import Param
from owf.errors import SourceSpan
from owf.units import Distance, Duration


@dataclass(frozen=True, slots=True)
class Step:
    """A unified step: any action with any combination of fields.

    Examples:
        Run 20min @Z2
        Bench Press 3x8rep @80kg @rest 90s
        Rest 5min
        Bike 50min 30km @Z3
        Sled Push 4x50m @100kg
    """

    action: str  # "Run", "Bench Press", "Rest", etc. (Title Case)
    sets: int | None = None
    reps: int | str | None = None  # int or "max"
    duration: Duration | None = None
    distance: Distance | None = None
    rest: Duration | None = None  # inter-set rest
    params: tuple[Param, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class RepeatBlock:
    """A repeat block: Nx: with sub-steps.

    The optional ``style`` field labels the block as a superset or circuit.
    This is set from ``@ style: superset`` or ``@ style: circuit`` metadata.
    It does not change parsing behavior — it's informational for display.
    """

    count: int
    steps: tuple[Any, ...] = ()  # Step | Block
    style: str | None = None  # "superset", "circuit", or None
    metadata: dict[str, str] = field(default_factory=dict)
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


# Partial union — only types from this module. For the full union
# (including Interval, AMRAP, ForTime), use ``owf.ast.StepUnion``.
_StepUnionPartial = Step | RepeatBlock
