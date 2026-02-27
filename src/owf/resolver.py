"""Expression resolver — evaluates expressions against variable context."""

from __future__ import annotations

import re
from dataclasses import replace
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
    Param,
    PowerParam,
    WeightParam,
)
from owf.ast.steps import (
    EnduranceStep,
    RepeatStep,
    StrengthStep,
)
from owf.errors import ResolveError


def resolve(doc: Document, extra_variables: dict[str, str] | None = None) -> Document:
    """Resolve all expressions in a document against its variables.

    Merges extra_variables on top of the document's own frontmatter.
    """
    variables = dict(doc.variables)
    if extra_variables:
        variables.update(extra_variables)

    resolved_workouts = tuple(
        _resolve_workout(w, variables) for w in doc.workouts
    )
    return replace(doc, workouts=resolved_workouts)


def _resolve_workout(workout: Workout, variables: dict[str, str]) -> Workout:
    resolved_steps = tuple(_resolve_step(s, variables) for s in workout.steps)
    return replace(workout, steps=resolved_steps)


def _resolve_step(step: Any, variables: dict[str, str]) -> Any:
    if isinstance(step, Workout):
        return _resolve_workout(step, variables)

    if isinstance(step, EnduranceStep):
        resolved_params = tuple(_resolve_param(p, variables) for p in step.params)
        return replace(step, params=resolved_params)

    if isinstance(step, StrengthStep):
        resolved_params = tuple(_resolve_param(p, variables) for p in step.params)
        return replace(step, params=resolved_params)

    if isinstance(step, (RepeatStep, Superset)):
        resolved_children = tuple(_resolve_step(s, variables) for s in step.steps)
        return replace(step, steps=resolved_children)

    if isinstance(step, (EMOM, AlternatingEMOM, AMRAP, ForTime, CustomInterval)):
        resolved_children = tuple(_resolve_step(s, variables) for s in step.steps)
        return replace(step, steps=resolved_children)

    return step


def _resolve_param(param: Param, variables: dict[str, str]) -> Param:
    if isinstance(param, (PowerParam, WeightParam, HeartRateParam)):
        if isinstance(param.value, Expression):
            resolved = _resolve_expression(param.value, variables)
            return replace(param, value=resolved)
    return param


def _resolve_expression(expr: Expression, variables: dict[str, str]) -> Expression:
    if isinstance(expr, Literal):
        return expr

    if isinstance(expr, VarRef):
        if expr.name not in variables:
            raise ResolveError(
                f"Undefined variable: {expr.name!r}",
                expr.span,
            )
        val_str = variables[expr.name]
        return _parse_variable_value(val_str)

    if isinstance(expr, Percentage):
        resolved_of = _resolve_expression(expr.of, variables)
        if isinstance(resolved_of, Literal) and resolved_of.value is not None:
            computed = expr.percent / 100 * resolved_of.value
            return Literal(value=computed, unit=resolved_of.unit)
        return replace(expr, of=resolved_of)

    if isinstance(expr, BinOp):
        left = _resolve_expression(expr.left, variables)
        right = _resolve_expression(expr.right, variables)
        if isinstance(left, Literal) and isinstance(right, Literal):
            if expr.op == "+":
                result = left.value + right.value
            elif expr.op == "-":
                result = left.value - right.value
            else:
                raise ResolveError(f"Unknown operator: {expr.op!r}")
            unit = left.unit or right.unit
            return Literal(value=result, unit=unit)
        return replace(expr, left=left, right=right)

    return expr


def _parse_variable_value(val: str) -> Literal:
    """Parse a variable value like '250W', '100kg', '185bpm'."""
    m = re.match(r"^(\d+(?:\.\d+)?)\s*(W|kg|lb|lbs|bpm|in|m|km)$", val)
    if m:
        return Literal(value=float(m.group(1)), unit=m.group(2))
    # Try bare number
    try:
        return Literal(value=float(val))
    except ValueError:
        raise ResolveError(f"Cannot parse variable value: {val!r}")
