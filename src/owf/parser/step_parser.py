"""Step parser — recursive descent over RawBlocks into typed AST nodes."""

from __future__ import annotations

import re
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
from owf.ast.steps import (
    EnduranceStep,
    IncludeStep,
    RepeatStep,
    RestStep,
    StrengthStep,
)
from owf.errors import ParseError, SourceSpan
from owf.parser.block_builder import RawBlock, build_blocks_for_workout
from owf.parser.frontmatter import parse_frontmatter
from owf.parser.param_parser import parse_params
from owf.parser.scanner import LineType, LogicalLine, scan
from owf.units import Distance, Duration

# Known endurance actions
ENDURANCE_ACTIONS = frozenset(
    {
        "run",
        "bike",
        "swim",
        "row",
        "ski",
        "walk",
        "hike",
        "warmup",
        "cooldown",
        "recover",
    }
)

# Regex for sets x reps: 3x8rep, 3x8, 100rep
SETS_REPS_PATTERN = re.compile(
    r"^(?:(?P<sets>\d+)x)?(?P<reps>\d+|max)(?:rep|reps)?$", re.IGNORECASE
)


def parse_document(text: str) -> Document:
    """Parse a full OWF document from text."""
    # Extract frontmatter
    variables, remaining = parse_frontmatter(text)

    # Scan remaining text
    lines = scan(remaining)

    # Split lines into workout sections
    workouts = _split_into_workouts(lines)

    return Document(
        workouts=tuple(workouts),
        variables=variables,
        span=SourceSpan(line=1, col=1),
    )


def _split_into_workouts(lines: list[LogicalLine]) -> list[Workout]:
    """Split scanned lines into Workout sections by heading."""
    workouts: list[Workout] = []
    current_heading: LogicalLine | None = None
    current_lines: list[LogicalLine] = []

    for ln in lines:
        if ln.line_type == LineType.HEADING:
            if current_heading is not None or current_lines:
                # Emit previous workout
                workouts.append(
                    _build_workout(current_heading, current_lines)
                )
            current_heading = ln
            current_lines = []
        elif ln.line_type == LineType.FRONTMATTER_FENCE:
            continue  # Skip any stray fences
        else:
            current_lines.append(ln)

    # Emit last workout
    if current_heading is not None or current_lines:
        workouts.append(_build_workout(current_heading, current_lines))

    # Filter out empty workouts (no heading, no steps, no notes)
    return [w for w in workouts if w.name or w.steps or w.notes]


def _build_workout(
    heading: LogicalLine | None, lines: list[LogicalLine]
) -> Workout:
    """Build a Workout node from a heading and its body lines."""
    name = ""
    workout_type: str | None = None
    span: SourceSpan | None = None

    if heading is not None:
        name, workout_type = _parse_heading(heading.content)
        span = heading.span

    blocks, trailing_notes = build_blocks_for_workout(lines)
    steps = tuple(_parse_block(b) for b in blocks)

    return Workout(
        name=name,
        workout_type=workout_type,
        steps=steps,
        notes=tuple(trailing_notes),
        span=span,
    )


def _parse_heading(content: str) -> tuple[str, str | None]:
    """Parse heading content like 'Name [type]' into (name, type)."""
    m = re.match(r"^(.+?)\s*\[(\w+)\]\s*$", content)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return content.strip(), None


def _parse_block(block: RawBlock) -> Any:
    """Parse a single RawBlock into the appropriate AST node."""
    content = block.content
    span = block.span

    # Include: include: Name
    if content.startswith("include:"):
        workout_name = content[8:].strip()
        return IncludeStep(workout_name=workout_name, span=span)

    # Rest: rest <duration>
    rest_m = re.match(r"^rest\s+(.+)$", content)
    if rest_m and not block.children:
        try:
            dur = Duration.parse(rest_m.group(1))
            return RestStep(
                duration=dur, notes=tuple(block.notes), span=span
            )
        except ValueError:
            pass

    # Repeat: Nx: or Nx superset:
    repeat_m = re.match(r"^(\d+)x\s*(?:superset\s*)?:\s*$", content)
    if repeat_m:
        count = int(repeat_m.group(1))
        children = tuple(_parse_block(c) for c in block.children)

        if "superset" in content.lower():
            return Superset(
                count=count,
                steps=children,
                notes=tuple(block.notes),
                span=span,
            )

        return RepeatStep(
            count=count,
            steps=children,
            notes=tuple(block.notes),
            span=span,
        )

    # EMOM: emom <dur>: or emom <dur> alternating:
    emom_m = re.match(
        r"^emom\s+(\d+(?:\.\d+)?(?:s|sec|min|h|hr|hour)?)\s*(alternating\s*)?:\s*$",
        content,
    )
    if emom_m:
        dur_str = emom_m.group(1)
        if not re.search(r"[a-zA-Z]", dur_str):
            dur_str += "min"
        dur = Duration.parse(dur_str)
        children = tuple(_parse_block(c) for c in block.children)
        alternating = emom_m.group(2) is not None

        if alternating:
            return AlternatingEMOM(
                duration=dur,
                steps=children,
                notes=tuple(block.notes),
                span=span,
            )
        return EMOM(
            duration=dur,
            steps=children,
            notes=tuple(block.notes),
            span=span,
        )

    # Custom interval: every <interval> for <duration>:
    custom_m = re.match(
        r"^every\s+(\d+(?:\.\d+)?(?:s|sec|min|h|hr|hour)?)\s+for\s+(\d+(?:\.\d+)?(?:s|sec|min|h|hr|hour)?)\s*:\s*$",
        content,
    )
    if custom_m:
        interval_str = custom_m.group(1)
        dur_str = custom_m.group(2)
        if not re.search(r"[a-zA-Z]", interval_str):
            interval_str += "min"
        if not re.search(r"[a-zA-Z]", dur_str):
            dur_str += "min"
        interval = Duration.parse(interval_str)
        dur = Duration.parse(dur_str)
        children = tuple(_parse_block(c) for c in block.children)
        return CustomInterval(
            interval=interval,
            duration=dur,
            steps=children,
            notes=tuple(block.notes),
            span=span,
        )

    # AMRAP: amrap <dur>:
    amrap_m = re.match(
        r"^amrap\s+(\d+(?:\.\d+)?(?:s|sec|min|h|hr|hour)?)\s*:\s*$",
        content,
    )
    if amrap_m:
        dur_str = amrap_m.group(1)
        if not re.search(r"[a-zA-Z]", dur_str):
            dur_str += "min"
        dur = Duration.parse(dur_str)
        children = tuple(_parse_block(c) for c in block.children)
        return AMRAP(
            duration=dur,
            steps=children,
            notes=tuple(block.notes),
            span=span,
        )

    # For-time: for-time: or for-time <dur>:
    ft_m = re.match(
        r"^for-time\s*(?:(\d+(?:\.\d+)?(?:s|sec|min|h|hr|hour)?)\s*)?:\s*$",
        content,
    )
    if ft_m:
        time_cap = None
        if ft_m.group(1):
            cap_str = ft_m.group(1)
            if not re.search(r"[a-zA-Z]", cap_str):
                cap_str += "min"
            time_cap = Duration.parse(cap_str)
        children = tuple(_parse_block(c) for c in block.children)
        return ForTime(
            time_cap=time_cap,
            steps=children,
            notes=tuple(block.notes),
            span=span,
        )

    # Parse as endurance or strength step
    return _parse_step_line(content, block, span)


def _parse_step_line(content: str, block: RawBlock, span: SourceSpan) -> Any:
    """Parse a step line into EnduranceStep or StrengthStep."""
    tokens = content.split()
    if not tokens:
        raise ParseError("Empty step", span)

    # Find the action/exercise and classify
    # Strategy: scan for duration/distance/sets-reps/params to find boundary
    action_tokens: list[str] = []
    rest_tokens: list[str] = []
    found_boundary = False
    i = 0

    while i < len(tokens):
        tok = tokens[i]

        if found_boundary:
            rest_tokens.append(tok)
            i += 1
            continue

        # Check if this token starts the parameter/metric section
        if tok.startswith("@"):
            found_boundary = True
            rest_tokens.append(tok)
            i += 1
            continue

        if tok.startswith("rest:"):
            found_boundary = True
            rest_tokens.append(tok)
            i += 1
            continue

        # Check if it's a duration
        try:
            Duration.parse(tok)
            found_boundary = True
            rest_tokens.append(tok)
            i += 1
            continue
        except ValueError:
            pass

        # Check if it's a distance
        try:
            Distance.parse(tok)
            found_boundary = True
            rest_tokens.append(tok)
            i += 1
            continue
        except ValueError:
            pass

        # Check if it's sets x reps
        if SETS_REPS_PATTERN.match(tok):
            found_boundary = True
            rest_tokens.append(tok)
            i += 1
            continue

        action_tokens.append(tok)
        i += 1

    action = " ".join(action_tokens)

    # Determine if this is an endurance or strength step
    # Split into first word for action classification
    first_word = action_tokens[0].lower() if action_tokens else ""

    if first_word in ENDURANCE_ACTIONS:
        return _build_endurance_step(action, rest_tokens, block, span)
    else:
        return _build_strength_step(action, rest_tokens, block, span)


def _build_endurance_step(
    action: str,
    metric_tokens: list[str],
    block: RawBlock,
    span: SourceSpan,
) -> EnduranceStep:
    """Build an EnduranceStep from parsed tokens."""
    duration: Duration | None = None
    distance: Distance | None = None
    param_tokens: list[str] = []

    for tok in metric_tokens:
        if tok.startswith("@") or tok.startswith("rest:"):
            param_tokens.append(tok)
            continue

        # Try as "of" or other expression continuations
        if param_tokens and not tok.startswith("@"):
            param_tokens.append(tok)
            continue

        if duration is None:
            try:
                duration = Duration.parse(tok)
                continue
            except ValueError:
                pass

        if distance is None:
            try:
                distance = Distance.parse(tok)
                continue
            except ValueError:
                pass

        param_tokens.append(tok)

    params, _rest = parse_params(param_tokens, span)

    return EnduranceStep(
        action=action,
        duration=duration,
        distance=distance,
        params=tuple(params),
        notes=tuple(block.notes),
        span=span,
    )


def _build_strength_step(
    exercise: str,
    metric_tokens: list[str],
    block: RawBlock,
    span: SourceSpan,
) -> StrengthStep:
    """Build a StrengthStep from parsed tokens."""
    sets: int | None = None
    reps: int | str | None = None
    duration: Duration | None = None
    param_tokens: list[str] = []

    for tok in metric_tokens:
        if tok.startswith("@") or tok.startswith("rest:"):
            param_tokens.append(tok)
            continue

        # Try as expression continuation
        if param_tokens and not tok.startswith("@"):
            param_tokens.append(tok)
            continue

        # Try sets x reps
        sr_m = SETS_REPS_PATTERN.match(tok)
        if sr_m and sets is None:
            if sr_m.group("sets"):
                sets = int(sr_m.group("sets"))
            reps_str = sr_m.group("reps")
            reps = reps_str if reps_str == "max" else int(reps_str)
            continue

        # Try duration
        if duration is None:
            try:
                duration = Duration.parse(tok)
                continue
            except ValueError:
                pass

        param_tokens.append(tok)

    params, rest_duration = parse_params(param_tokens, span)

    return StrengthStep(
        exercise=exercise,
        sets=sets,
        reps=reps,
        duration=duration,
        params=tuple(params),
        rest=rest_duration,
        notes=tuple(block.notes),
        span=span,
    )
