"""Base AST nodes: Document, Workout."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from owf.errors import SourceSpan

# No base Node dataclass — each AST node is a standalone frozen dataclass
# to avoid inheritance issues with slots=True and default fields.


@dataclass(frozen=True, slots=True)
class Workout:
    """A named workout section (# heading)."""

    name: str
    workout_type: str | None = None
    steps: tuple[Any, ...] = ()  # tuple of Step | Block
    notes: tuple[str, ...] = ()
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class Document:
    """Top-level document: optional frontmatter + workouts."""

    workouts: tuple[Workout, ...] = ()
    variables: dict[str, str] = field(default_factory=dict)
    span: SourceSpan | None = field(default=None, compare=False, repr=False)
