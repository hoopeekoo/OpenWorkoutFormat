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
    EnduranceStep,
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
    metadata, remaining = parse_frontmatter(text)

    # Scan remaining text
    lines = scan(remaining)

    # Split lines into workout sections
    workouts = _split_into_workouts(lines)

    return Document(
        workouts=tuple(workouts),
        metadata=metadata,
        span=SourceSpan(line=1, col=1),
    )


def _split_into_workouts(lines: list[LogicalLine]) -> list[Workout]:
    """Split scanned lines into Workout sections by heading.

    If any ``SESSION_HEADING`` (``##``) lines are present, the document uses
    two-level nesting: ``##`` defines session workouts whose ``steps`` may
    contain child ``Workout`` nodes (from ``#`` headings) alongside regular
    steps.  ``#`` headings that appear before the first ``##`` become
    top-level workouts (backward compat).

    If no ``SESSION_HEADING`` lines exist the original flat behaviour is
    used — each ``#`` heading becomes a top-level workout.
    """
    has_sessions = any(
        ln.line_type == LineType.SESSION_HEADING for ln in lines
    )

    if not has_sessions:
        return _split_flat(lines)

    return _split_two_level(lines)


def _split_flat(lines: list[LogicalLine]) -> list[Workout]:
    """Original flat splitting: each ``#`` heading → top-level workout."""
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
        else:
            current_lines.append(ln)

    if current_heading is not None or current_lines:
        workouts.append(_build_workout(current_heading, current_lines))

    return [w for w in workouts if w.name or w.steps or w.notes]


def _split_two_level(lines: list[LogicalLine]) -> list[Workout]:
    """Two-level splitting: ``##`` sessions contain ``#`` child workouts."""
    workouts: list[Workout] = []

    # Accumulate sections: each section is (heading_line_or_None, body_lines)
    # A SESSION_HEADING starts a new session section.
    # A HEADING before the first SESSION_HEADING becomes a standalone workout.
    # A HEADING inside a session section becomes a child workout.

    # First, split into top-level chunks separated by SESSION_HEADING.
    # The chunk before the first SESSION_HEADING is the "orphan" chunk.
    chunks: list[tuple[LogicalLine | None, list[LogicalLine]]] = []
    current_session: LogicalLine | None = None
    current_lines: list[LogicalLine] = []
    seen_session = False

    for ln in lines:
        if ln.line_type == LineType.SESSION_HEADING:
            if seen_session or current_lines:
                chunks.append((current_session, current_lines))
            current_session = ln
            current_lines = []
            seen_session = True
        elif ln.line_type == LineType.FRONTMATTER_FENCE:
            continue
        else:
            current_lines.append(ln)

    if current_session is not None or current_lines:
        chunks.append((current_session, current_lines))

    for session_heading, body_lines in chunks:
        if session_heading is None:
            # Orphan lines before first ##: split by # as flat workouts
            workouts.extend(_split_flat(body_lines))
        else:
            workouts.append(_build_session_workout(session_heading, body_lines))

    return [w for w in workouts if w.name or w.steps or w.notes]


def _build_session_workout(
    session_heading: LogicalLine, body_lines: list[LogicalLine]
) -> Workout:
    """Build a session-level workout from a ``##`` heading and its body.

    The body may contain interleaved steps/notes and ``#`` child workout
    sections.  Each ``#`` section becomes a child ``Workout`` placed inline
    in the session's ``steps`` tuple.
    """
    name, workout_type, date, rpe, rir = _parse_heading(
        session_heading.content,
    )

    # Split body into segments: each segment is either a group of
    # non-heading lines (steps/notes/blanks) or a # heading section.
    segments: list[tuple[LogicalLine | None, list[LogicalLine]]] = []
    current_child_heading: LogicalLine | None = None
    current_child_lines: list[LogicalLine] = []
    in_child = False

    for ln in body_lines:
        if ln.line_type == LineType.HEADING:
            # Flush previous segment
            if in_child:
                segments.append((current_child_heading, current_child_lines))
            elif current_child_lines:
                segments.append((None, current_child_lines))
            current_child_heading = ln
            current_child_lines = []
            in_child = True
        else:
            current_child_lines.append(ln)

    # Flush final segment
    if in_child:
        segments.append((current_child_heading, current_child_lines))
    elif current_child_lines:
        segments.append((None, current_child_lines))

    # Build steps list: non-heading segments become parsed steps,
    # heading segments become child Workout nodes.
    all_steps: list[Any] = []
    trailing_notes: list[str] = []

    for child_heading, child_lines in segments:
        if child_heading is not None:
            child_workout = _build_workout(child_heading, child_lines)
            all_steps.append(child_workout)
        else:
            blocks, notes = build_blocks_for_workout(child_lines)
            all_steps.extend(_parse_block(b) for b in blocks)
            trailing_notes.extend(notes)

    if workout_type is None:
        child_types = {
            s.workout_type
            for s in all_steps
            if isinstance(s, Workout) and s.workout_type is not None
        }
        if len(child_types) >= 2:
            workout_type = "combination"

    return Workout(
        name=name,
        workout_type=workout_type,
        date=date,
        rpe=rpe,
        rir=rir,
        steps=tuple(all_steps),
        notes=tuple(trailing_notes),
        span=session_heading.span,
    )


def _build_workout(
    heading: LogicalLine | None, lines: list[LogicalLine]
) -> Workout:
    """Build a Workout node from a heading and its body lines."""
    name = ""
    workout_type: str | None = None
    date: WorkoutDate | None = None
    rpe: float | None = None
    rir: int | None = None
    span: SourceSpan | None = None

    if heading is not None:
        name, workout_type, date, rpe, rir = _parse_heading(heading.content)
        span = heading.span

    blocks, trailing_notes = build_blocks_for_workout(lines)
    steps = tuple(_parse_block(b) for b in blocks)

    return Workout(
        name=name,
        workout_type=workout_type,
        date=date,
        rpe=rpe,
        rir=rir,
        steps=steps,
        notes=tuple(trailing_notes),
        span=span,
    )


_DATE_RE = re.compile(
    r"\((\d{4}-\d{2}-\d{2})(?:\s+(\d{2}:\d{2})(?:-(\d{2}:\d{2}))?)?\)\s*$"
)

_RPE_RE = re.compile(r"@RPE\s+(\d+(?:\.\d+)?)")
_RIR_RE = re.compile(r"@RIR\s+(\d+)")


def _parse_heading(
    content: str,
) -> tuple[str, str | None, WorkoutDate | None, float | None, int | None]:
    """Parse heading content like 'Name [type] (2025-02-27) @RPE 7 @RIR 2'.

    Returns (name, workout_type, date, rpe, rir).
    """
    text = content

    # Extract @RPE and @RIR first (they may appear after date or type)
    rpe: float | None = None
    rir: int | None = None

    rpe_m = _RPE_RE.search(text)
    if rpe_m:
        rpe = float(rpe_m.group(1))
        text = text[: rpe_m.start()] + text[rpe_m.end() :]

    rir_m = _RIR_RE.search(text)
    if rir_m:
        rir = int(rir_m.group(1))
        text = text[: rir_m.start()] + text[rir_m.end() :]

    text = text.rstrip()

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

    # Extract [type]
    tm = re.match(r"^(.+?)\s*\[(\w+)\]\s*$", text)
    if tm:
        return tm.group(1).strip(), tm.group(2).strip(), date, rpe, rir
    return text.strip(), None, date, rpe, rir


def _parse_block(block: RawBlock) -> Any:
    """Parse a single RawBlock into the appropriate AST node."""
    content = block.content
    span = block.span

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
                notes=tuple(block.notes),
                span=span,
            )

        if "circuit" in content.lower():
            return Circuit(
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
