"""Base AST nodes: Document, Workout, WorkoutDate, Program, Week."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from owf.errors import SourceSpan

# No base Node dataclass — each AST node is a standalone frozen dataclass
# to avoid inheritance issues with slots=True and default fields.


@dataclass(frozen=True, slots=True)
class WorkoutDate:
    """Date (and optional time range) on a workout heading."""

    date: str  # "YYYY-MM-DD"
    start_time: str | None = None  # "HH:MM"
    end_time: str | None = None  # "HH:MM"

    def __str__(self) -> str:
        if self.start_time and self.end_time:
            return f"{self.date} {self.start_time}-{self.end_time}"
        if self.start_time:
            return f"{self.date} {self.start_time}"
        return self.date


@dataclass(frozen=True, slots=True)
class Workout:
    """A named workout section (# heading)."""

    name: str
    sport_type: str | None = None
    date: WorkoutDate | None = None
    rpe: int | None = None  # workout-level perceived exertion (1-10)
    rir: int | None = None  # default RIR for strength exercises
    steps: tuple[Any, ...] = ()  # tuple of Step | Block
    metadata: dict[str, str] = field(default_factory=dict)
    description: str | None = None  # workout-level description (from > lines)
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class Document:
    """Top-level workout document: optional metadata + workouts."""

    workouts: tuple[Workout, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class ProgressionRule:
    """A progression rule: @ progression: <action> <rule>.

    Examples:
        @ progression: Bench Press +2.5kg/week
        @ progression: Pull-Up +1rep/week
        @ progression: Bench Press -5s/week
    """

    action: str  # "Bench Press", "Back Squat", etc.
    amount: float  # 2.5, 5, 1, etc.
    unit: str  # "kg", "lb", "%", "rep", "s"
    direction: str  # "+" or "-"
    per: str  # "week" (only supported period for now)
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class DeloadRule:
    """A deload rule: @ deload: week N xM.

    Example: @ deload: week 4 x0.8
    """

    week: int  # which week is the deload
    multiplier: float  # 0.8 = 80% of previous week
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class Week:
    """A week/microcycle within a program (--- Name --- separator)."""

    name: str  # "Week 1 (template)", "Week 4 (Deload)", etc.
    is_template: bool = False
    is_deload: bool = False
    workouts: tuple[Workout, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class Program:
    """Top-level program document (## heading)."""

    name: str
    duration: str | None = None  # "4 weeks", "rotating", etc.
    progression_rules: tuple[ProgressionRule, ...] = ()
    deload_rule: DeloadRule | None = None
    is_cycle: bool = False
    weeks: tuple[Week, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)
    span: SourceSpan | None = field(default=None, compare=False, repr=False)
