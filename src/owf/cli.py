"""Command-line interface for parsing and displaying OWF files."""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from typing import Any

from owf.ast.base import Program, Week, Workout
from owf.ast.blocks import (
    AMRAP,
    ForTime,
    Interval,
)
from owf.ast.params import (
    BodyweightPlusParam,
    HeartRateParam,
    PaceParam,
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
from owf.loader import load
from owf.resolver import resolve


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="owf",
        description="Parse and display OpenWorkoutFormat (.owf/.owfp) files.",
    )
    parser.add_argument("files", nargs="+", help="OWF files to parse")
    parser.add_argument(
        "--resolve",
        action="store_true",
        help="Resolve expressions against variables",
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

        if isinstance(doc, Program):
            _print_program(doc)
        else:
            if doc.metadata:
                print("Metadata:")
                for key, value in doc.metadata.items():
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


def _print_program(program: Program) -> None:
    header = f"## {program.name}"
    if program.duration:
        header += f" ({program.duration})"
    print(header)
    print("=" * len(header))

    if program.metadata:
        for key, value in program.metadata.items():
            print(f"  {key}: {value}")

    for rule in program.progression_rules:
        print(f"  progression: {rule.action} {rule.direction}{rule.amount}{rule.unit}/{rule.per}")

    if program.deload_rule:
        print(f"  deload: week {program.deload_rule.week} x{program.deload_rule.multiplier}")

    print()

    for week in program.weeks:
        _print_week(week)


def _print_week(week: Week) -> None:
    print(f"--- {week.name} ---")
    for note in week.notes:
        print(f"  > {note}")
    for workout in week.workouts:
        _print_workout(workout)


def _print_workout(workout: Any) -> None:
    header = workout.name
    if workout.sport_type:
        header += f" [{workout.sport_type}]"
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
            parts.append(_format_param(p))
        if node.rest:
            parts.append(f"rest:{node.rest}")
        print(f"{prefix}{' '.join(parts)}")
        for note in node.notes:
            print(f"{prefix}> {note}")

    elif isinstance(node, Workout):
        _print_workout(node)

    elif isinstance(node, RepeatBlock):
        if node.style:
            print(f"{prefix}{node.style} {node.count}x:")
        else:
            print(f"{prefix}{node.count}x:")
        for child in node.steps:
            _print_node(child, indent + 1)
        for note in node.notes:
            print(f"{prefix}> {note}")

    elif isinstance(node, Interval):
        alt = " (alternating)" if node.is_alternating else ""
        print(f"{prefix}every {node.interval} for {node.duration}{alt}:")
        for child in node.steps:
            _print_node(child, indent + 1)
        for note in node.notes:
            print(f"{prefix}> {note}")

    elif isinstance(node, AMRAP):
        print(f"{prefix}amrap {node.duration}:")
        for child in node.steps:
            _print_node(child, indent + 1)
        for note in node.notes:
            print(f"{prefix}> {note}")

    elif isinstance(node, ForTime):
        cap = f" {node.time_cap}" if node.time_cap else ""
        print(f"{prefix}for-time{cap}:")
        for child in node.steps:
            _print_node(child, indent + 1)
        for note in node.notes:
            print(f"{prefix}> {note}")


def _format_param(param: Any) -> str:
    """Format a parameter for CLI display."""
    if isinstance(param, ZoneParam):
        return f"@{param.zone}"
    if isinstance(param, PercentOfParam):
        p = param.percent
        pct = int(p) if p == int(p) else p
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
        v = int(param.value) if param.value == int(param.value) else param.value
        return f"@RPE {v}"
    if isinstance(param, RIRParam):
        return f"@RIR {param.value}"
    return ""


if __name__ == "__main__":
    main()
