"""Serializer — AST → .owf text (round-trip and canonical modes)."""

from __future__ import annotations

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
from owf.ast.expressions import BinOp, Expression, Literal, Percentage, VarRef
from owf.ast.params import (
    HeartRateParam,
    IntensityParam,
    PaceParam,
    Param,
    PowerParam,
    RIRParam,
    RPEParam,
    WeightParam,
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

    # Frontmatter
    if doc.variables:
        parts.append("---")
        for key, value in doc.variables.items():
            parts.append(f"{key}: {value}")
        parts.append("---")
        parts.append("")

    # Workouts
    for i, workout in enumerate(doc.workouts):
        if i > 0 or doc.variables:
            parts.append("")
        parts.append(_serialize_workout(workout))

    result = "\n".join(parts)
    # Ensure single trailing newline
    if not result.endswith("\n"):
        result += "\n"
    return result


def _serialize_workout(workout: Workout) -> str:
    is_session = any(isinstance(s, Workout) for s in workout.steps)
    prefix = "##" if is_session else "#"
    lines: list[str] = []

    # Heading
    if workout.name:
        if workout.workout_type:
            lines.append(f"{prefix} {workout.name} [{workout.workout_type}]")
        else:
            lines.append(f"{prefix} {workout.name}")
        lines.append("")

    # Steps (child Workouts are serialized inline with # headings)
    for step in workout.steps:
        if isinstance(step, Workout):
            lines.append("")
            lines.append(_serialize_child_workout(step))
        else:
            lines.extend(_serialize_node(step, indent=0))

    # Workout-level notes
    for note in workout.notes:
        lines.append("")
        lines.append(f"> {note}")

    return "\n".join(lines)


def _serialize_child_workout(workout: Workout) -> str:
    """Serialize a child workout (``#`` heading) within a session."""
    lines: list[str] = []

    if workout.name:
        if workout.workout_type:
            lines.append(f"# {workout.name} [{workout.workout_type}]")
        else:
            lines.append(f"# {workout.name}")
        lines.append("")

    for step in workout.steps:
        lines.extend(_serialize_node(step, indent=0))

    for note in workout.notes:
        lines.append("")
        lines.append(f"> {note}")

    return "\n".join(lines)


def _serialize_node(node: Any, indent: int) -> list[str]:
    """Serialize an AST node to lines at the given indentation."""
    prefix = "  " * indent
    lines: list[str] = []

    if isinstance(node, EnduranceStep):
        parts = [node.action]
        if node.duration:
            parts.append(str(node.duration))
        if node.distance:
            parts.append(str(node.distance))
        for p in node.params:
            parts.append(_serialize_param(p))
        lines.append(f"{prefix}- {' '.join(parts)}")
        for note in node.notes:
            lines.append(f"{prefix}> {note}")

    elif isinstance(node, StrengthStep):
        parts = [node.exercise]
        if node.sets is not None and node.reps is not None:
            parts.append(f"{node.sets}x{node.reps}rep")
        elif node.reps is not None:
            parts.append(f"{node.reps}rep")
        if node.duration:
            parts.append(str(node.duration))
        for p in node.params:
            parts.append(_serialize_param(p))
        if node.rest:
            parts.append(f"rest:{node.rest}")
        lines.append(f"{prefix}- {' '.join(parts)}")
        for note in node.notes:
            lines.append(f"{prefix}> {note}")

    elif isinstance(node, RestStep):
        lines.append(f"{prefix}- rest {node.duration}")
        for note in node.notes:
            lines.append(f"{prefix}> {note}")

    elif isinstance(node, RepeatStep):
        lines.append(f"{prefix}- {node.count}x:")
        for child in node.steps:
            lines.extend(_serialize_node(child, indent + 1))
        for note in node.notes:
            lines.append(f"{prefix}> {note}")

    elif isinstance(node, Superset):
        lines.append(f"{prefix}- {node.count}x superset:")
        for child in node.steps:
            lines.extend(_serialize_node(child, indent + 1))
        for note in node.notes:
            lines.append(f"{prefix}> {note}")

    elif isinstance(node, EMOM):
        lines.append(f"{prefix}- emom {node.duration}:")
        for child in node.steps:
            lines.extend(_serialize_node(child, indent + 1))
        for note in node.notes:
            lines.append(f"{prefix}> {note}")

    elif isinstance(node, AlternatingEMOM):
        lines.append(f"{prefix}- emom {node.duration} alternating:")
        for child in node.steps:
            lines.extend(_serialize_node(child, indent + 1))
        for note in node.notes:
            lines.append(f"{prefix}> {note}")

    elif isinstance(node, CustomInterval):
        lines.append(f"{prefix}- every {node.interval} for {node.duration}:")
        for child in node.steps:
            lines.extend(_serialize_node(child, indent + 1))
        for note in node.notes:
            lines.append(f"{prefix}> {note}")

    elif isinstance(node, AMRAP):
        lines.append(f"{prefix}- amrap {node.duration}:")
        for child in node.steps:
            lines.extend(_serialize_node(child, indent + 1))
        for note in node.notes:
            lines.append(f"{prefix}> {note}")

    elif isinstance(node, ForTime):
        if node.time_cap:
            lines.append(f"{prefix}- for-time {node.time_cap}:")
        else:
            lines.append(f"{prefix}- for-time:")
        for child in node.steps:
            lines.extend(_serialize_node(child, indent + 1))
        for note in node.notes:
            lines.append(f"{prefix}> {note}")

    return lines


def _serialize_param(param: Param) -> str:
    """Serialize a parameter to its @-prefixed string."""
    if isinstance(param, PaceParam):
        return f"@{param.pace}"

    if isinstance(param, IntensityParam):
        return f"@{param.name}"

    if isinstance(param, RPEParam):
        v = int(param.value) if param.value == int(param.value) else param.value
        return f"@RPE {v}"

    if isinstance(param, RIRParam):
        return f"@RIR {param.value}"

    if isinstance(param, HeartRateParam):
        if isinstance(param.value, str):
            return f"@{param.value}"
        return f"@{_serialize_expression(param.value)}"

    if isinstance(param, PowerParam):
        return f"@{_serialize_expression(param.value)}"

    if isinstance(param, WeightParam):
        return f"@{_serialize_expression(param.value)}"

    return ""


def _serialize_expression(expr: Expression) -> str:
    """Serialize an expression to string."""
    if isinstance(expr, Literal):
        v = int(expr.value) if expr.value == int(expr.value) else expr.value
        if expr.unit:
            return f"{v}{expr.unit}"
        return str(v)

    if isinstance(expr, VarRef):
        return expr.name

    if isinstance(expr, Percentage):
        pct = int(expr.percent) if expr.percent == int(expr.percent) else expr.percent
        return f"{pct}% of {_serialize_expression(expr.of)}"

    if isinstance(expr, BinOp):
        left = _serialize_expression(expr.left)
        right = _serialize_expression(expr.right)
        return f"{left} {expr.op} {right}"

    return str(expr)
