"""Step parser — recursive descent over RawBlocks into typed AST nodes."""

from __future__ import annotations

import re
from typing import Any

from owf.ast.base import Document, Workout, WorkoutDate
from owf.ast.blocks import (
    AMRAP,
    EMOM,
    AlternatingEMOM,
    Circuit,
    CustomInterval,
    ForTime,
    Superset,
)
from owf.ast.steps import (
    RepeatStep,
    Step,
)
from owf.errors import ParseError, SourceSpan
from owf.parser.block_builder import RawBlock, build_blocks_for_workout
from owf.parser.param_parser import parse_params
from owf.parser.scanner import LineType, LogicalLine, scan
from owf.units import Distance, Duration

# Regex for sets x reps: 3x8rep, 3x8, 100rep
SETS_REPS_PATTERN = re.compile(
    r"^(?:(?P<sets>\d+)x)?(?P<reps>\d+|max)(?:rep|reps)?$", re.IGNORECASE
)


def parse_document(text: str) -> Document:
    """Parse a full OWF document from text."""
    lines = scan(text)

    # Extract document-level metadata: @ lines before any heading
    metadata: dict[str, str] = {}
    for ln in lines:
        if ln.line_type == LineType.METADATA and ln.indent == 0:
            key, _, value = ln.content.partition(": ")
            metadata[key] = value
        elif ln.line_type in (
            LineType.HEADING,
            LineType.STEP,
        ):
            break

    # Split lines into workout sections
    workouts = _split_workouts(lines)

    return Document(
        workouts=tuple(workouts),
        metadata=metadata,
        span=SourceSpan(line=1, col=1),
    )


def _split_workouts(lines: list[LogicalLine]) -> list[Workout]:
    """Split scanned lines into top-level workouts (each ``#`` heading)."""
    workouts: list[Workout] = []
    current_heading: LogicalLine | None = None
    current_lines: list[LogicalLine] = []

    for ln in lines:
        if ln.line_type == LineType.HEADING:
            if current_heading is not None or current_lines:
                workouts.append(
                    _build_workout(current_heading, current_lines)
                )
            current_heading = ln
            current_lines = []
        elif ln.line_type == LineType.FRONTMATTER_FENCE:
            continue
        elif ln.line_type == LineType.METADATA and ln.indent == 0:
            current_lines.append(ln)
        else:
            current_lines.append(ln)

    if current_heading is not None or current_lines:
        workouts.append(_build_workout(current_heading, current_lines))

    return [w for w in workouts if w.name or w.steps or w.notes]


def _build_workout(
    heading: LogicalLine | None, lines: list[LogicalLine]
) -> Workout:
    """Build a Workout node from a heading and its body lines."""
    name = ""
    sport_type: str | None = None
    date: WorkoutDate | None = None
    rpe: int | None = None
    rir: int | None = None
    span: SourceSpan | None = None

    if heading is not None:
        name, sport_type, date, rpe, rir = _parse_heading(heading.content)
        span = heading.span

    # Extract workout-level metadata (indent 0 before any steps)
    workout_metadata: dict[str, str] = {}
    remaining_lines: list[LogicalLine] = []
    past_metadata = False
    for ln in lines:
        if (
            not past_metadata
            and ln.line_type == LineType.METADATA
            and ln.indent == 0
        ):
            key, _, value = ln.content.partition(": ")
            workout_metadata[key] = value
        else:
            if ln.line_type in (LineType.STEP, LineType.NOTE):
                past_metadata = True
            remaining_lines.append(ln)

    blocks, trailing_notes = build_blocks_for_workout(remaining_lines)
    steps = tuple(_parse_block(b) for b in blocks)

    return Workout(
        name=name,
        sport_type=sport_type,
        date=date,
        rpe=rpe,
        rir=rir,
        steps=steps,
        metadata=workout_metadata,
        notes=tuple(trailing_notes),
        span=span,
    )


_DATE_RE = re.compile(
    r"\((\d{4}-\d{2}-\d{2})(?:\s+(\d{2}:\d{2})(?:-(\d{2}:\d{2}))?)?\)\s*$"
)

_RPE_TAIL_RE = re.compile(r"\s+@RPE\s+(\d+)\s*$")
_RIR_TAIL_RE = re.compile(r"\s+@RIR\s+(\d+)\s*$")


def _parse_heading(
    content: str,
) -> tuple[str, str | None, WorkoutDate | None, int | None, int | None]:
    """Parse heading content like 'Name [type] (2025-02-27) @RPE 7 @RIR 2'.

    Returns (name, sport_type, date, rpe, rir).

    Any bracket tag sets sport_type (e.g. [Running], [endurance], [Strength Training]).
    """
    text = content

    # Strip trailing @RPE / @RIR (EBNF: heading ends with { SP heading_param })
    rpe: int | None = None
    rir: int | None = None

    for _ in range(2):
        m = _RIR_TAIL_RE.search(text)
        if m:
            rir = int(m.group(1))
            text = text[: m.start()]
            continue
        m = _RPE_TAIL_RE.search(text)
        if m:
            rpe = int(m.group(1))
            text = text[: m.start()]
            continue
        break

    # Extract trailing (date ...) first
    date: WorkoutDate | None = None
    dm = _DATE_RE.search(text)
    if dm:
        date = WorkoutDate(
            date=dm.group(1),
            start_time=dm.group(2),
            end_time=dm.group(3),
        )
        text = text[: dm.start()].rstrip()

    # Extract [tag] — accepts any string inside brackets
    tm = re.match(r"^(.+?)\s*\[([^\]]+)\]\s*$", text)
    if tm:
        name = tm.group(1).strip()
        tag = tm.group(2).strip()
        return name, tag, date, rpe, rir
    return text.strip(), None, date, rpe, rir


def _parse_block(block: RawBlock) -> Any:
    """Parse a single RawBlock into the appropriate AST node."""
    content = block.content
    span = block.span

    # Rest: Rest <duration> (standalone rest step)
    rest_m = re.match(r"^Rest\s+(.+)$", content)
    if rest_m and not block.children:
        try:
            dur = Duration.parse(rest_m.group(1))
            return Step(
                action="Rest",
                duration=dur,
                metadata=block.metadata,
                notes=tuple(block.notes),
                span=span,
            )
        except ValueError:
            pass

    # Repeat: Nx: or Nx superset: or Nx circuit:
    repeat_m = re.match(
        r"^(\d+)x\s*(?:superset|circuit\s*)?:\s*$", content
    )
    if repeat_m:
        count = int(repeat_m.group(1))
        children = tuple(_parse_block(c) for c in block.children)

        if "superset" in content.lower():
            return Superset(
                count=count,
                steps=children,
                metadata=block.metadata,
                notes=tuple(block.notes),
                span=span,
            )

        if "circuit" in content.lower():
            return Circuit(
                count=count,
                steps=children,
                metadata=block.metadata,
                notes=tuple(block.notes),
                span=span,
            )

        return RepeatStep(
            count=count,
            steps=children,
            metadata=block.metadata,
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
                metadata=block.metadata,
                notes=tuple(block.notes),
                span=span,
            )
        return EMOM(
            duration=dur,
            steps=children,
            metadata=block.metadata,
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
            metadata=block.metadata,
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
            metadata=block.metadata,
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
            metadata=block.metadata,
            notes=tuple(block.notes),
            span=span,
        )

    # Parse as unified step (any action, any combination of fields)
    return _parse_step_line(content, block, span)


def _parse_step_line(content: str, block: RawBlock, span: SourceSpan) -> Step:
    """Parse a step line into a unified Step node.

    Tokens are pattern-matched (order-independent after the action):
    - Sets×Reps: 3x10rep, maxrep
    - Duration: 20min, 90s
    - Distance: 5km, 400m
    - Param: @Z2, @80kg, @RPE 7
    - Rest: @rest 90s (inline rest modifier)
    """
    tokens = content.split()
    if not tokens:
        raise ParseError("Empty step", span)

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

        if tok.startswith("@"):
            found_boundary = True
            rest_tokens.append(tok)
            i += 1
            continue

        try:
            Duration.parse(tok)
            found_boundary = True
            rest_tokens.append(tok)
            i += 1
            continue
        except ValueError:
            pass

        try:
            Distance.parse(tok)
            found_boundary = True
            rest_tokens.append(tok)
            i += 1
            continue
        except ValueError:
            pass

        if SETS_REPS_PATTERN.match(tok):
            found_boundary = True
            rest_tokens.append(tok)
            i += 1
            continue

        action_tokens.append(tok)
        i += 1

    action = " ".join(action_tokens)

    # Enforce Title Case: first word must start with an uppercase letter
    first_word = action_tokens[0] if action_tokens else ""
    if first_word and first_word[0].islower():
        raise ParseError(
            f"Action must be Title Case: {first_word!r} "
            f"(did you mean {first_word.capitalize()!r}?)",
            span,
        )

    return _build_step(action, rest_tokens, block, span)


def _build_step(
    action: str,
    metric_tokens: list[str],
    block: RawBlock,
    span: SourceSpan,
) -> Step:
    """Build a unified Step from parsed tokens.

    All tokens populate the single Step node — any combination is valid.
    """
    sets: int | None = None
    reps: int | str | None = None
    duration: Duration | None = None
    distance: Distance | None = None
    param_tokens: list[str] = []

    for tok in metric_tokens:
        if tok.startswith("@"):
            param_tokens.append(tok)
            continue

        # Try as expression continuation (e.g. "of FTP" after "@80%")
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

        # Try distance
        if distance is None:
            try:
                distance = Distance.parse(tok)
                continue
            except ValueError:
                pass

        param_tokens.append(tok)

    params, rest_duration = parse_params(param_tokens, span)

    return Step(
        action=action,
        sets=sets,
        reps=reps,
        duration=duration,
        distance=distance,
        rest=rest_duration,
        params=tuple(params),
        metadata=block.metadata,
        notes=tuple(block.notes),
        span=span,
    )
