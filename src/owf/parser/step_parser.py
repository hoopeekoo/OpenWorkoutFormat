"""Step parser — recursive descent over RawBlocks into typed AST nodes."""

from __future__ import annotations

import re
from typing import Any

from owf.ast.base import (
    DeloadRule,
    Document,
    Program,
    ProgressionRule,
    Week,
    Workout,
    WorkoutDate,
)
from owf.ast.blocks import (
    AMRAP,
    ForTime,
    Interval,
)
from owf.ast.steps import (
    RepeatBlock,
    Step,
)
from owf.errors import ParseError, SourceSpan
from owf.parser.block_builder import RawBlock, build_blocks_for_workout
from owf.parser.param_parser import parse_params
from owf.parser.scanner import LineType, LogicalLine, scan
from owf.units import Distance, Duration

# Regex for sets x reps: 3x8rep, 3x8, 100rep, 3xmax, 3xmaxrep
SETS_REPS_PATTERN = re.compile(
    r"^(?:(?P<sets>\d+)x)?(?P<reps>\d+|max)(?:rep|reps)?$", re.IGNORECASE
)

# Progression rule: +2.5kg/week, +5%/week, +1rep/week, -5s/week
_PROGRESSION_RE = re.compile(
    r"^(.+?)\s+([+-])(\d+(?:\.\d+)?)(kg|lb|lbs|%|rep|reps|s|sec|min)/(\w+)$"
)

# Deload rule: week 4 x0.8
_DELOAD_RE = re.compile(r"^week\s+(\d+)\s+x(\d+(?:\.\d+)?)$")


def parse_document(text: str) -> Document | Program:
    """Parse a full OWF document from text.

    Returns a Document for workout files (.owf) or a Program for
    program files (.owfp).
    """
    lines = scan(text)

    # Check if this is a program document (has ## heading)
    has_program = any(ln.line_type == LineType.PROGRAM_HEADING for ln in lines)

    if has_program:
        return _parse_program(lines)
    return _parse_workout_document(lines)


def _parse_workout_document(lines: list[LogicalLine]) -> Document:
    """Parse a workout document (no ## heading)."""
    # Extract document-level metadata: @ lines before any heading
    metadata: dict[str, str] = {}
    for ln in lines:
        if ln.line_type == LineType.METADATA and ln.indent == 0:
            key, _, value = ln.content.partition(": ")
            metadata[key] = value
        elif ln.line_type in (LineType.HEADING, LineType.STEP):
            break

    workouts = _split_workouts(lines)

    return Document(
        workouts=tuple(workouts),
        metadata=metadata,
        span=SourceSpan(line=1, col=1),
    )


def _parse_program(lines: list[LogicalLine]) -> Program:
    """Parse a program document (has ## heading)."""
    # Find the program heading
    program_heading: LogicalLine | None = None
    heading_idx = 0
    for i, ln in enumerate(lines):
        if ln.line_type == LineType.PROGRAM_HEADING:
            program_heading = ln
            heading_idx = i
            break

    if program_heading is None:
        raise ParseError("No program heading (##) found", SourceSpan(line=1, col=1))

    name, duration = _parse_program_heading(program_heading.content)

    # Extract program-level metadata (between ## heading and first --- or #)
    metadata: dict[str, str] = {}
    progression_rules: list[ProgressionRule] = []
    deload_rule: DeloadRule | None = None
    is_cycle = False

    for ln in lines[heading_idx + 1 :]:
        if ln.line_type == LineType.METADATA and ln.indent == 0:
            key, _, value = ln.content.partition(": ")
            if key == "progression":
                rule = _parse_progression_rule(value, ln.span)
                if rule:
                    progression_rules.append(rule)
            elif key == "deload":
                deload_rule = _parse_deload_rule(value, ln.span)
            elif key == "cycle" and value.strip().lower() == "true":
                is_cycle = True
            else:
                metadata[key] = value
        elif ln.line_type in (
            LineType.HEADING,
            LineType.WEEK_SEPARATOR,
            LineType.STEP,
        ):
            break

    # Split into weeks
    weeks = _split_weeks(lines)

    return Program(
        name=name,
        duration=duration,
        progression_rules=tuple(progression_rules),
        deload_rule=deload_rule,
        is_cycle=is_cycle,
        weeks=tuple(weeks),
        metadata=metadata,
        span=program_heading.span,
    )


def _parse_program_heading(content: str) -> tuple[str, str | None]:
    """Parse program heading: 'Name (duration)' → (name, duration)."""
    m = re.match(r"^(.+?)\s*\(([^)]+)\)\s*$", content)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return content.strip(), None


def _parse_progression_rule(
    value: str, span: SourceSpan
) -> ProgressionRule | None:
    """Parse a progression rule value like 'Bench Press +2.5kg/week'."""
    m = _PROGRESSION_RE.match(value.strip())
    if not m:
        return None

    action = m.group(1).strip()
    direction = m.group(2)
    amount = float(m.group(3))
    unit = m.group(4)
    per = m.group(5)

    # Normalize unit
    if unit in ("reps",):
        unit = "rep"
    if unit in ("sec",):
        unit = "s"

    return ProgressionRule(
        action=action,
        amount=amount,
        unit=unit,
        direction=direction,
        per=per,
        span=span,
    )


def _parse_deload_rule(
    value: str, span: SourceSpan
) -> DeloadRule | None:
    """Parse a deload rule value like 'week 4 x0.8'."""
    m = _DELOAD_RE.match(value.strip())
    if not m:
        return None
    return DeloadRule(
        week=int(m.group(1)),
        multiplier=float(m.group(2)),
        span=span,
    )


def _split_weeks(lines: list[LogicalLine]) -> list[Week]:
    """Split program lines into weeks."""
    weeks: list[Week] = []
    current_sep: LogicalLine | None = None
    current_lines: list[LogicalLine] = []

    # Skip lines before the first week separator
    started = False
    for ln in lines:
        if ln.line_type == LineType.WEEK_SEPARATOR:
            if started and (current_sep is not None or current_lines):
                weeks.append(_build_week(current_sep, current_lines))
            current_sep = ln
            current_lines = []
            started = True
        elif started:
            current_lines.append(ln)

    if started and (current_sep is not None or current_lines):
        weeks.append(_build_week(current_sep, current_lines))

    return weeks


def _build_week(
    separator: LogicalLine | None, lines: list[LogicalLine]
) -> Week:
    """Build a Week node from a separator and its body lines."""
    name = separator.content if separator else ""
    span = separator.span if separator else None

    is_template = "(template)" in name.lower() if name else False
    is_deload = False

    # Extract week-level metadata and notes
    metadata: dict[str, str] = {}
    workout_lines: list[LogicalLine] = []
    notes: list[str] = []
    past_metadata = False

    for ln in lines:
        if (
            not past_metadata
            and ln.line_type == LineType.METADATA
            and ln.indent == 0
        ):
            key, _, value = ln.content.partition(": ")
            if key == "deload" and value.strip().lower() == "true":
                is_deload = True
            else:
                metadata[key] = value
        elif ln.line_type == LineType.NOTE and not past_metadata:
            notes.append(ln.content)
        elif ln.line_type in (LineType.HEADING, LineType.STEP):
            past_metadata = True
            workout_lines.append(ln)
        else:
            if past_metadata:
                workout_lines.append(ln)

    # If "(Deload)" in name, also mark as deload
    if name and "(deload)" in name.lower():
        is_deload = True

    workouts = _split_workouts(workout_lines)

    return Week(
        name=name,
        is_template=is_template,
        is_deload=is_deload,
        workouts=tuple(workouts),
        metadata=metadata,
        notes=tuple(notes),
        span=span,
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
    """
    text = content

    # Strip trailing @RPE / @RIR
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

    # Extract [tag]
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

    # Repeat: Nx:
    repeat_m = re.match(r"^(\d+)x\s*:\s*$", content)
    if repeat_m:
        count = int(repeat_m.group(1))
        children = tuple(_parse_block(c) for c in block.children)

        # Check for @ style metadata (superset, circuit)
        style = block.metadata.pop("style", None)

        return RepeatBlock(
            count=count,
            steps=children,
            style=style,
            metadata=block.metadata,
            notes=tuple(block.notes),
            span=span,
        )

    # Interval: every <interval> for <duration>:
    interval_m = re.match(
        r"^every\s+(\d+(?:\.\d+)?(?:s|sec|min|h|hr|hour)?)\s+for\s+(\d+(?:\.\d+)?(?:s|sec|min|h|hr|hour)?)\s*:\s*$",
        content,
    )
    if interval_m:
        interval_str = interval_m.group(1)
        dur_str = interval_m.group(2)
        if not re.search(r"[a-zA-Z]", interval_str):
            interval_str += "min"
        if not re.search(r"[a-zA-Z]", dur_str):
            dur_str += "min"
        interval = Duration.parse(interval_str)
        dur = Duration.parse(dur_str)
        children = tuple(_parse_block(c) for c in block.children)
        return Interval(
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

    # Parse as unified step
    return _parse_step_line(content, block, span)


def _parse_step_line(content: str, block: RawBlock, span: SourceSpan) -> Step:
    """Parse a step line into a unified Step node."""
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
    """Build a unified Step from parsed tokens."""
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
