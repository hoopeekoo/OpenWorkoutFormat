"""Serializer — AST → .owf text (round-trip and canonical modes)."""

from __future__ import annotations

from typing import Any

from owf.ast.base import Document, Workout
from owf.ast.blocks import (
    AMRAP,
    EMOM,
    AlternatingEMOM,
    Circuit,
    CustomInterval,
    ForTime,
    Superset,
)
from owf.ast.params import (
    BodyweightPlusParam,
    HeartRateParam,
    PaceParam,
    Param,
    PercentOfParam,
    PowerParam,
    RIRParam,
    RPEParam,
    WeightParam,
    ZoneParam,
)
from owf.ast.steps import (
    EnduranceStep,
    RepeatStep,
    RestStep,
    StrengthStep,
)


def dumps(doc: Document) -> str:
    """Serialize a Document AST back to .owf text."""
    parts: list[str] = []

    # Document-level metadata
    if doc.metadata:
        for key, value in doc.metadata.items():
            parts.append(f"@ {key}: {value}")
        parts.append("")

    # Workouts — always serialized as ## sessions
    for i, workout in enumerate(doc.workouts):
        if i > 0 or doc.metadata:
            parts.append("")
        parts.append(_serialize_workout(workout))

    result = "\n".join(parts)
    # Ensure single trailing newline
    if not result.endswith("\n"):
        result += "\n"
    return result


def _normalize_name(name: str) -> str:
    """Title-case a step name, preserving hyphenation."""
    return "-".join(
        " ".join(w.capitalize() for w in part.split())
        for part in name.split("-")
    )


def _heading_line(prefix: str, workout: Workout) -> str:
    """Build a heading line like ``## Name [type] (date) @RPE N @RIR N``."""
    parts = [f"{prefix} {workout.name}"]
    if workout.sport_type:
        parts.append(f" [{workout.sport_type}]")
    elif workout.workout_type and workout.workout_type != "mixed":
        parts.append(f" [{workout.workout_type}]")
    if workout.date:
        parts.append(f" ({workout.date})")
    if workout.rpe is not None:
        parts.append(f" @RPE {workout.rpe}")
    if workout.rir is not None:
        parts.append(f" @RIR {workout.rir}")
    return "".join(parts)


def _metadata_lines(
    metadata: dict[str, str], prefix: str = ""
) -> list[str]:
    """Serialize metadata as ``@ key: value`` lines."""
    return [f"{prefix}@ {k}: {v}" for k, v in metadata.items()]


def _serialize_workout(workout: Workout) -> str:
    """Serialize a top-level workout as a ## session."""
    is_session = any(isinstance(s, Workout) for s in workout.steps)
    lines: list[str] = []

    if is_session:
        # Session with child workouts — always ##
        lines.append(_heading_line("##", workout))
        if workout.metadata:
            lines.extend(_metadata_lines(workout.metadata))
        lines.append("")

        for step in workout.steps:
            if isinstance(step, Workout):
                lines.append("")
                lines.append(_serialize_child_workout(step))
            else:
                lines.extend(_serialize_node(step, indent=0))
    else:
        # No child workouts — wrap as ## session
        lines.append(_heading_line("##", workout))
        if workout.metadata:
            lines.extend(_metadata_lines(workout.metadata))
        lines.append("")

        for step in workout.steps:
            lines.extend(_serialize_node(step, indent=0))

    # Workout-level notes (preceded by blank line)
    if workout.notes:
        lines.append("")
        for note in workout.notes:
            lines.append(f"> {note}")

    return "\n".join(lines)


def _serialize_child_workout(workout: Workout) -> str:
    """Serialize a child workout (``#`` heading) within a session."""
    lines: list[str] = []

    if workout.name:
        # Child workouts never get dates (dates are session-level only)
        child_parts = [f"# {workout.name}"]
        if workout.sport_type:
            child_parts.append(f" [{workout.sport_type}]")
        elif workout.workout_type and workout.workout_type != "mixed":
            child_parts.append(f" [{workout.workout_type}]")
        if workout.rpe is not None:
            child_parts.append(f" @RPE {workout.rpe}")
        if workout.rir is not None:
            child_parts.append(f" @RIR {workout.rir}")
        lines.append("".join(child_parts))
        if workout.metadata:
            lines.extend(_metadata_lines(workout.metadata))
        lines.append("")

    for step in workout.steps:
        lines.extend(_serialize_node(step, indent=0))

    # Workout-level notes (preceded by blank line)
    if workout.notes:
        lines.append("")
        for note in workout.notes:
            lines.append(f"> {note}")

    return "\n".join(lines)


def _serialize_node(node: Any, indent: int) -> list[str]:
    """Serialize an AST node to lines at the given indentation."""
    prefix = "  " * indent
    lines: list[str] = []

    child_prefix = "  " * (indent + 1)
    meta = _metadata_lines(node.metadata, child_prefix) if node.metadata else []

    if isinstance(node, EnduranceStep):
        parts = [node.action]
        if node.duration:
            parts.append(str(node.duration))
        if node.distance:
            parts.append(str(node.distance))
        for p in node.params:
            parts.append(_serialize_param(p))
        lines.append(f"{prefix}- {' '.join(parts)}")
        lines.extend(meta)
        for note in node.notes:
            lines.append(f"{prefix}> {note}")

    elif isinstance(node, StrengthStep):
        parts = [_normalize_name(node.exercise)]
        if node.sets is not None and node.reps is not None:
            parts.append(f"{node.sets}x{node.reps}rep")
        elif node.reps is not None:
            parts.append(f"{node.reps}rep")
        if node.duration:
            parts.append(str(node.duration))
        for p in node.params:
            parts.append(_serialize_param(p))
        if node.rest:
            parts.append(f"@rest {node.rest}")
        lines.append(f"{prefix}- {' '.join(parts)}")
        lines.extend(meta)
        for note in node.notes:
            lines.append(f"{prefix}> {note}")

    elif isinstance(node, RestStep):
        lines.append(f"{prefix}- rest {node.duration}")
        lines.extend(meta)
        for note in node.notes:
            lines.append(f"{prefix}> {note}")

    elif isinstance(node, RepeatStep):
        lines.append(f"{prefix}- {node.count}x:")
        lines.extend(meta)
        for child in node.steps:
            lines.extend(_serialize_node(child, indent + 1))
        for note in node.notes:
            lines.append(f"{prefix}> {note}")

    elif isinstance(node, Superset):
        lines.append(f"{prefix}- {node.count}x superset:")
        lines.extend(meta)
        for child in node.steps:
            lines.extend(_serialize_node(child, indent + 1))
        for note in node.notes:
            lines.append(f"{prefix}> {note}")

    elif isinstance(node, Circuit):
        lines.append(f"{prefix}- {node.count}x circuit:")
        lines.extend(meta)
        for child in node.steps:
            lines.extend(_serialize_node(child, indent + 1))
        for note in node.notes:
            lines.append(f"{prefix}> {note}")

    elif isinstance(node, EMOM):
        lines.append(f"{prefix}- emom {node.duration}:")
        lines.extend(meta)
        for child in node.steps:
            lines.extend(_serialize_node(child, indent + 1))
        for note in node.notes:
            lines.append(f"{prefix}> {note}")

    elif isinstance(node, AlternatingEMOM):
        lines.append(f"{prefix}- emom {node.duration} alternating:")
        lines.extend(meta)
        for child in node.steps:
            lines.extend(_serialize_node(child, indent + 1))
        for note in node.notes:
            lines.append(f"{prefix}> {note}")

    elif isinstance(node, CustomInterval):
        lines.append(f"{prefix}- every {node.interval} for {node.duration}:")
        lines.extend(meta)
        for child in node.steps:
            lines.extend(_serialize_node(child, indent + 1))
        for note in node.notes:
            lines.append(f"{prefix}> {note}")

    elif isinstance(node, AMRAP):
        lines.append(f"{prefix}- amrap {node.duration}:")
        lines.extend(meta)
        for child in node.steps:
            lines.extend(_serialize_node(child, indent + 1))
        for note in node.notes:
            lines.append(f"{prefix}> {note}")

    elif isinstance(node, ForTime):
        if node.time_cap:
            lines.append(f"{prefix}- for-time {node.time_cap}:")
        else:
            lines.append(f"{prefix}- for-time:")
        lines.extend(meta)
        for child in node.steps:
            lines.extend(_serialize_node(child, indent + 1))
        for note in node.notes:
            lines.append(f"{prefix}> {note}")

    return lines


def _serialize_param(param: Param) -> str:
    """Serialize a parameter to its @-prefixed string."""
    if isinstance(param, ZoneParam):
        return f"@{param.zone}"

    if isinstance(param, PercentOfParam):
        pct = (
            int(param.percent)
            if param.percent == int(param.percent)
            else param.percent
        )
        return f"@{pct}% of {param.variable}"

    if isinstance(param, PowerParam):
        return f"@{param.value}W"

    if isinstance(param, HeartRateParam):
        return f"@{param.value}bpm"

    if isinstance(param, PaceParam):
        return f"@{param.pace}"

    if isinstance(param, WeightParam):
        v = int(param.value) if param.value == int(param.value) else param.value
        return f"@{v}{param.unit}"

    if isinstance(param, BodyweightPlusParam):
        v = int(param.added) if param.added == int(param.added) else param.added
        return f"@bodyweight + {v}{param.unit}"

    if isinstance(param, RPEParam):
        return f"@RPE {param.value}"

    if isinstance(param, RIRParam):
        return f"@RIR {param.value}"

    return ""
