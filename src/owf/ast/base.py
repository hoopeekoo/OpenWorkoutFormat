"""Base AST nodes: Document, Workout, WorkoutDate."""

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
    workout_type: str | None = None
    date: WorkoutDate | None = None
    steps: tuple[Any, ...] = ()  # tuple of Step | Block
    notes: tuple[str, ...] = ()
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class Document:
    """Top-level document: optional frontmatter + workouts."""

    workouts: tuple[Workout, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)
    span: SourceSpan | None = field(default=None, compare=False, repr=False)
