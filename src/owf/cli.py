"""Command-line interface for parsing and displaying OWF files."""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from typing import Any

from owf.ast.base import Workout
from owf.ast.blocks import (
    AMRAP,
    EMOM,
    AlternatingEMOM,
    CustomInterval,
    ForTime,
    Superset,
)
from owf.ast.expressions import BinOp, Literal, Percentage, VarRef
from owf.ast.params import (
    HeartRateParam,
    IntensityParam,
    PaceParam,
    PowerParam,
    RPEParam,
    WeightParam,
)
from owf.ast.steps import (
    EnduranceStep,
    RepeatStep,
    RestStep,
    StrengthStep,
)
from owf.loader import load
from owf.resolver import resolve


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="owf",
        description="Parse and display OpenWorkoutFormat (.owf) files.",
    )
    parser.add_argument("files", nargs="+", help="OWF files to parse")
    parser.add_argument(
        "--resolve",
        action="store_true",
        help="Resolve expressions against frontmatter variables",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output the AST as JSON",
    )
    args = parser.parse_args(argv)

    for filepath in args.files:
        try:
            doc = load(filepath)
            if args.resolve:
                doc = resolve(doc)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        if args.json:
            print(json.dumps(_to_dict(doc), indent=2))
            continue

        if doc.variables:
            print("Variables:")
            for key, value in doc.variables.items():
                print(f"  {key}: {value}")
            print()

        for workout in doc.workouts:
            _print_workout(workout)


def _to_dict(obj: Any) -> Any:
    """Recursively convert an AST node to a JSON-serializable dict."""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: _to_dict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_dict(item) for item in obj]
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        result: dict[str, Any] = {"_type": type(obj).__name__}
        for f in dataclasses.fields(obj):
            if f.name == "span":
                continue
            value = getattr(obj, f.name)
            result[f.name] = _to_dict(value)
        return result
    return str(obj)


def _print_workout(workout: Any) -> None:
    header = workout.name
    if workout.workout_type:
        header += f" [{workout.workout_type}]"
    print(header)
    print("-" * len(header))

    for step in workout.steps:
        _print_node(step, indent=1)

    # Print workout-level notes that aren't already on the last step
    last_step_notes = set()
    if workout.steps:
        last_step_notes = set(getattr(workout.steps[-1], "notes", ()))
    for note in workout.notes:
        if note not in last_step_notes:
            print(f'  > {note}')

    print()


def _print_node(node: Any, indent: int) -> None:
    prefix = "  " * indent

    if isinstance(node, EnduranceStep):
        parts = [node.action]
        if node.duration:
            parts.append(str(node.duration))
        if node.distance:
            parts.append(str(node.distance))
        for p in node.params:
            parts.append(_format_param(p))
        print(f"{prefix}{' '.join(parts)}")
        for note in node.notes:
            print(f"{prefix}> {note}")

    elif isinstance(node, StrengthStep):
        parts = [node.exercise]
        if node.sets is not None and node.reps is not None:
            parts.append(f"{node.sets}x{node.reps}rep")
        elif node.reps is not None:
            parts.append(f"{node.reps}rep")
        if node.duration:
            parts.append(str(node.duration))
        for p in node.params:
            parts.append(_format_param(p))
        if node.rest:
            parts.append(f"rest:{node.rest}")
        print(f"{prefix}{' '.join(parts)}")
        for note in node.notes:
            print(f"{prefix}> {note}")

    elif isinstance(node, RestStep):
        print(f"{prefix}rest {node.duration}")
        for note in node.notes:
            print(f"{prefix}> {note}")

    elif isinstance(node, Workout):
        _print_workout(node)

    elif isinstance(node, RepeatStep):
        print(f"{prefix}{node.count}x:")
        for child in node.steps:
            _print_node(child, indent + 1)

    elif isinstance(node, Superset):
        print(f"{prefix}{node.count}x superset:")
        for child in node.steps:
            _print_node(child, indent + 1)

    elif isinstance(node, EMOM):
        print(f"{prefix}emom {node.duration}:")
        for child in node.steps:
            _print_node(child, indent + 1)

    elif isinstance(node, AlternatingEMOM):
        print(f"{prefix}emom {node.duration} alternating:")
        for child in node.steps:
            _print_node(child, indent + 1)

    elif isinstance(node, CustomInterval):
        print(f"{prefix}every {node.interval} for {node.duration}:")
        for child in node.steps:
            _print_node(child, indent + 1)

    elif isinstance(node, AMRAP):
        print(f"{prefix}amrap {node.duration}:")
        for child in node.steps:
            _print_node(child, indent + 1)

    elif isinstance(node, ForTime):
        cap = f" {node.time_cap}" if node.time_cap else ""
        print(f"{prefix}for-time{cap}:")
        for child in node.steps:
            _print_node(child, indent + 1)

    for note in getattr(node, "notes", ()):
        if not isinstance(node, (EnduranceStep, StrengthStep, RestStep)):
            print(f"{prefix}> {note}")


def _format_param(param: Any) -> str:
    if isinstance(param, PaceParam):
        return f"@{param.pace}"
    if isinstance(param, IntensityParam):
        return f"@{param.name}"
    if isinstance(param, RPEParam):
        v = int(param.value) if param.value == int(param.value) else param.value
        return f"@RPE {v}"
    if isinstance(param, (PowerParam, WeightParam, HeartRateParam)):
        if isinstance(param.value, str):
            return f"@{param.value}"
        return f"@{_format_expr(param.value)}"
    return ""


def _format_expr(expr: Any) -> str:
    if isinstance(expr, Literal):
        v = int(expr.value) if expr.value == int(expr.value) else expr.value
        if expr.unit:
            return f"{v}{expr.unit}"
        return str(v)
    if isinstance(expr, VarRef):
        return expr.name
    if isinstance(expr, Percentage):
        pct = int(expr.percent) if expr.percent == int(expr.percent) else expr.percent
        return f"{pct}% of {_format_expr(expr.of)}"
    if isinstance(expr, BinOp):
        return f"{_format_expr(expr.left)} {expr.op} {_format_expr(expr.right)}"
    return str(expr)


if __name__ == "__main__":
    main()
