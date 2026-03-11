"""Expression resolver — evaluates parameters against variable context."""

from __future__ import annotations

import re
from dataclasses import replace
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
    Param,
    PercentOfParam,
    PowerParam,
    WeightParam,
)
from owf.ast.steps import (
    RepeatStep,
    Step,
)
from owf.errors import ResolveError


def resolve(doc: Document, variables: dict[str, str] | None = None) -> Document:
    """Resolve all expressions in a document against caller-supplied variables.

    Training reference variables (FTP, 1RM, bodyweight, max HR) are provided
    by the calling application, not stored in the document.
    """
    ctx = dict(variables) if variables else {}

    resolved_workouts = tuple(
        _resolve_workout(w, ctx) for w in doc.workouts
    )
    return replace(doc, workouts=resolved_workouts)


def _resolve_workout(workout: Workout, variables: dict[str, str]) -> Workout:
    resolved_steps = tuple(_resolve_step(s, variables) for s in workout.steps)
    return replace(workout, steps=resolved_steps)


def _resolve_step(step: Any, variables: dict[str, str]) -> Any:
    if isinstance(step, Step):
        resolved_params = tuple(_resolve_param(p, variables) for p in step.params)
        return replace(step, params=resolved_params)

    if isinstance(step, (RepeatStep, Superset, Circuit)):
        resolved_children = tuple(_resolve_step(s, variables) for s in step.steps)
        return replace(step, steps=resolved_children)

    if isinstance(step, (EMOM, AlternatingEMOM, AMRAP, ForTime, CustomInterval)):
        resolved_children = tuple(_resolve_step(s, variables) for s in step.steps)
        return replace(step, steps=resolved_children)

    return step


def _resolve_param(param: Param, variables: dict[str, str]) -> Param:
    """Resolve a single parameter against variables.

    Only PercentOfParam and BodyweightPlusParam need resolution.
    All other param types are already concrete values.
    """
    if isinstance(param, PercentOfParam):
        var_name = param.variable
        if var_name not in variables:
            raise ResolveError(
                f"Undefined variable: {var_name!r}",
                param.span,
            )
        val = _parse_variable_value(variables[var_name])
        computed = param.percent / 100 * val[0]
        unit = val[1]

        if unit == "W":
            return PowerParam(value=int(round(computed)), span=param.span)
        if unit == "bpm":
            return HeartRateParam(value=int(computed), span=param.span)
        if unit in ("kg", "lb", "lbs"):
            return WeightParam(value=computed, unit=unit, span=param.span)
        # Default: return PowerParam for unitless values
        return PowerParam(value=int(round(computed)), span=param.span)

    if isinstance(param, BodyweightPlusParam):
        if "bodyweight" not in variables:
            raise ResolveError(
                "Undefined variable: 'bodyweight'",
                param.span,
            )
        bw_val = _parse_variable_value(variables["bodyweight"])
        total = bw_val[0] + param.added
        unit = param.unit or bw_val[1] or "kg"
        return WeightParam(value=total, unit=unit, span=param.span)

    return param


def _parse_variable_value(val: str) -> tuple[float, str | None]:
    """Parse a variable value like '250W', '100kg', '185bpm'.

    Returns (numeric_value, unit_or_none).
    """
    m = re.match(r"^(\d+(?:\.\d+)?)\s*(W|kg|lb|lbs|bpm|in|m|km)$", val)
    if m:
        return float(m.group(1)), m.group(2)
    # Try bare number
    try:
        return float(val), None
    except ValueError:
        raise ResolveError(f"Cannot parse variable value: {val!r}")
