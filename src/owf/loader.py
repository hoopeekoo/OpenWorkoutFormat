"""File I/O and include resolution with cycle detection."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

from owf.ast.base import Document, Workout
from owf.ast.blocks import (
    AMRAP,
    EMOM,
    AlternatingEMOM,
    CustomInterval,
    ForTime,
    Superset,
)
from owf.ast.steps import IncludeStep, RepeatStep
from owf.errors import IncludeError
from owf.parser.step_parser import parse_document


def load(path: str | Path) -> Document:
    """Load and parse an OWF file, resolving includes."""
    return _load_with_visited(Path(path), set())


def _load_with_visited(path: Path, visited: set[str]) -> Document:
    """Internal: load with cycle-detection state."""
    text = path.read_text(encoding="utf-8")
    doc = parse_document(text)
    doc = _resolve_includes(doc, path.parent, visited)
    return doc


def _resolve_includes(
    doc: Document,
    base_dir: Path,
    visited: set[str],
) -> Document:
    """Resolve all include steps, detecting cycles."""
    # Build a map of workout names defined in this document
    workout_map: dict[str, Workout] = {}
    for w in doc.workouts:
        if w.name:
            workout_map[w.name] = w

    resolved_workouts = tuple(
        _resolve_workout_includes(w, workout_map, base_dir, visited)
        for w in doc.workouts
    )
    return replace(doc, workouts=resolved_workouts)


def _resolve_workout_includes(
    workout: Workout,
    workout_map: dict[str, Workout],
    base_dir: Path,
    visited: set[str],
) -> Workout:
    resolved_steps = tuple(
        _resolve_step_includes(s, workout_map, base_dir, visited)
        for s in workout.steps
    )
    return replace(workout, steps=resolved_steps)


def _resolve_step_includes(
    step: Any,
    workout_map: dict[str, Workout],
    base_dir: Path,
    visited: set[str],
) -> Any:
    if isinstance(step, IncludeStep):
        name = step.workout_name

        # Check in same-document workouts first
        if name in workout_map:
            workout = workout_map[name]
            return replace(step, resolved=workout)

        # Try loading from a file
        # Convention: workout name → lowercase, spaces to hyphens + .owf
        filename = name.lower().replace(" ", "-") + ".owf"
        filepath = base_dir / filename

        if not filepath.exists():
            raise IncludeError(
                f"Cannot resolve include: {name!r} "
                f"(not found in document or as {filepath})",
                step.span,
            )

        canonical = str(filepath.resolve())
        if canonical in visited:
            raise IncludeError(
                f"Circular include detected: {name!r}",
                step.span,
            )

        sub_doc = _load_with_visited(filepath, visited | {canonical})
        # Find the matching workout in the loaded document
        for w in sub_doc.workouts:
            if w.name == name:
                return replace(step, resolved=w)

        # If only one workout, use it
        if len(sub_doc.workouts) == 1:
            return replace(step, resolved=sub_doc.workouts[0])

        raise IncludeError(
            f"Cannot find workout {name!r} in {filepath}",
            step.span,
        )

    if isinstance(step, (RepeatStep, Superset)):
        resolved_children = tuple(
            _resolve_step_includes(s, workout_map, base_dir, visited)
            for s in step.steps
        )
        return replace(step, steps=resolved_children)

    if isinstance(step, (EMOM, AlternatingEMOM, AMRAP, ForTime, CustomInterval)):
        resolved_children = tuple(
            _resolve_step_includes(s, workout_map, base_dir, visited)
            for s in step.steps
        )
        return replace(step, steps=resolved_children)

    return step
