"""Serializer — AST → .owf text (round-trip and canonical modes)."""

from __future__ import annotations

from typing import Any

from owf.ast.base import Document, Program, Week, Workout
from owf.ast.blocks import (
    AMRAP,
    ForTime,
    Interval,
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
    RepeatBlock,
    Step,
)


def dumps(doc: Document | Program) -> str:
    """Serialize a Document or Program AST back to .owf text."""
    if isinstance(doc, Program):
        return _serialize_program(doc)
    return _serialize_document(doc)


def _serialize_document(doc: Document) -> str:
    """Serialize a Document AST back to .owf text."""
    parts: list[str] = []

    # Document-level metadata
    if doc.metadata:
        for key, value in doc.metadata.items():
            parts.append(f"@ {key}: {value}")
        parts.append("")

    # Workouts — each serialized as # heading
    for i, workout in enumerate(doc.workouts):
        if i > 0 or doc.metadata:
            parts.append("")
        parts.append(_serialize_workout(workout))

    result = "\n".join(parts)
    if not result.endswith("\n"):
        result += "\n"
    return result


def _serialize_program(program: Program) -> str:
    """Serialize a Program AST back to .owfp text."""
    parts: list[str] = []

    # Program heading
    heading = f"## {program.name}"
    if program.duration:
        heading += f" ({program.duration})"
    parts.append(heading)

    # Program-level metadata
    if program.metadata:
        for key, value in program.metadata.items():
            parts.append(f"@ {key}: {value}")

    # Cycle
    if program.is_cycle:
        parts.append("@ cycle: true")

    # Progression rules
    for rule in program.progression_rules:
        parts.append(
            f"@ progression: {rule.action} "
            f"{rule.direction}{rule.amount}{rule.unit}/{rule.per}"
        )

    # Deload rule
    if program.deload_rule:
        parts.append(
            f"@ deload: week {program.deload_rule.week} "
            f"x{program.deload_rule.multiplier}"
        )

    # Program-level notes
    for note in program.notes:
        parts.append(f"> {note}")

    # Weeks
    for week in program.weeks:
        parts.append("")
        parts.append(_serialize_week(week))

    result = "\n".join(parts)
    if not result.endswith("\n"):
        result += "\n"
    return result


def _serialize_week(week: Week) -> str:
    """Serialize a Week as --- Name --- separator + workouts."""
    lines: list[str] = []
    lines.append(f"--- {week.name} ---")

    if week.metadata:
        for key, value in week.metadata.items():
            lines.append(f"@ {key}: {value}")

    for note in week.notes:
        lines.append(f"> {note}")

    for workout in week.workouts:
        lines.append("")
        lines.append(_serialize_workout(workout))

    return "\n".join(lines)


def _heading_line(workout: Workout) -> str:
    """Build a heading line like ``# Name [type] (date) @RPE N @RIR N``."""
    parts = [f"# {workout.name}"]
    if workout.sport_type:
        parts.append(f" [{workout.sport_type}]")
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
    """Serialize a top-level workout as a # heading."""
    lines: list[str] = []

    lines.append(_heading_line(workout))
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

    if isinstance(node, Step):
        parts = [node.action]
        if node.sets is not None and node.reps is not None:
            parts.append(f"{node.sets}x{node.reps}rep")
        elif node.reps is not None:
            parts.append(f"{node.reps}rep")
        if node.duration:
            parts.append(str(node.duration))
        if node.distance:
            parts.append(str(node.distance))
        for p in node.params:
            parts.append(_serialize_param(p))
        if node.rest:
            parts.append(f"@rest {node.rest}")
        lines.append(f"{prefix}- {' '.join(parts)}")
        lines.extend(meta)
        for note in node.notes:
            lines.append(f"{child_prefix}> {note}")

    elif isinstance(node, RepeatBlock):
        lines.append(f"{prefix}- {node.count}x:")
        if node.style:
            lines.append(f"{child_prefix}@ style: {node.style}")
        lines.extend(meta)
        for child in node.steps:
            lines.extend(_serialize_node(child, indent + 1))
        for note in node.notes:
            lines.append(f"{child_prefix}> {note}")

    elif isinstance(node, Interval):
        lines.append(f"{prefix}- every {node.interval} for {node.duration}:")
        lines.extend(meta)
        for child in node.steps:
            lines.extend(_serialize_node(child, indent + 1))
        for note in node.notes:
            lines.append(f"{child_prefix}> {note}")

    elif isinstance(node, AMRAP):
        lines.append(f"{prefix}- amrap {node.duration}:")
        lines.extend(meta)
        for child in node.steps:
            lines.extend(_serialize_node(child, indent + 1))
        for note in node.notes:
            lines.append(f"{child_prefix}> {note}")

    elif isinstance(node, ForTime):
        if node.time_cap:
            lines.append(f"{prefix}- for-time {node.time_cap}:")
        else:
            lines.append(f"{prefix}- for-time:")
        lines.extend(meta)
        for child in node.steps:
            lines.extend(_serialize_node(child, indent + 1))
        for note in node.notes:
            lines.append(f"{child_prefix}> {note}")

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
