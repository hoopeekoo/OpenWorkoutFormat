"""Block builder — turns flat logical lines into an indentation tree."""

from __future__ import annotations

from dataclasses import dataclass, field

from owf.errors import ParseError, SourceSpan
from owf.parser.scanner import LineType, LogicalLine


@dataclass(slots=True)
class RawBlock:
    """A step line with its children (determined by indentation)."""

    line: LogicalLine
    children: list[RawBlock] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def content(self) -> str:
        return self.line.content

    @property
    def span(self) -> SourceSpan:
        return self.line.span


def build_blocks(lines: list[LogicalLine]) -> list[RawBlock]:
    """Build a tree of RawBlocks from step lines using indentation.

    Returns top-level blocks (one per workout heading, or step lines at the
    top level).
    """
    step_lines = [ln for ln in lines if ln.line_type == LineType.STEP]
    if not step_lines:
        return []

    return _build_tree(step_lines, 0, len(step_lines), _min_indent(step_lines))


def build_blocks_for_workout(
    lines: list[LogicalLine],
) -> tuple[list[RawBlock], list[str]]:
    """Build blocks from lines belonging to a single workout section.

    Returns (blocks, description_lines).

    Note lines (> prefix) are only valid at workout level. They are
    collected and returned as description_lines. Step-level notes are
    rejected with a ParseError.
    """
    step_lines: list[LogicalLine] = []
    description_lines: list[str] = []

    for ln in lines:
        if ln.line_type == LineType.STEP:
            step_lines.append(ln)

    if not step_lines:
        # Might just have description lines (notes before any steps)
        all_notes = [ln.content for ln in lines if ln.line_type == LineType.NOTE]
        return [], all_notes

    # Find where the first step is. Notes before any step are description.
    # Notes after any step are errors (step-level notes no longer allowed).
    first_step_idx = min(
        i for i, ln in enumerate(lines) if ln.line_type == LineType.STEP
    )

    # Collect pre-step description lines
    for i in range(first_step_idx):
        if lines[i].line_type == LineType.NOTE:
            description_lines.append(lines[i].content)

    # Check for notes AFTER any step — these are now errors
    last_step_idx = max(
        i for i, ln in enumerate(lines) if ln.line_type == LineType.STEP
    )

    # Notes after the last step (preceded by blank) = trailing description (allowed)
    saw_blank = False
    trailing_start = len(lines)
    for i in range(last_step_idx + 1, len(lines)):
        ln = lines[i]
        if ln.line_type == LineType.BLANK:
            saw_blank = True
        elif ln.line_type == LineType.NOTE:
            if saw_blank:
                trailing_start = i
                break
            # Note immediately after step — error
            raise ParseError(
                "Notes are only allowed at workout level (before steps "
                "or after all steps with a blank line separator). "
                "Step-level notes are no longer supported.",
                ln.span,
            )

    for i in range(trailing_start, len(lines)):
        if lines[i].line_type == LineType.NOTE:
            description_lines.append(lines[i].content)

    # Also check for notes between steps
    in_steps = False
    for i, ln in enumerate(lines):
        if ln.line_type == LineType.STEP:
            in_steps = True
        elif ln.line_type == LineType.NOTE and in_steps and i < last_step_idx:
            raise ParseError(
                "Notes are only allowed at workout level (before steps "
                "or after all steps with a blank line separator). "
                "Step-level notes are no longer supported.",
                ln.span,
            )

    blocks = _build_tree(step_lines, 0, len(step_lines), _min_indent(step_lines))

    # Attach metadata to blocks
    _attach_metadata(blocks, lines[:trailing_start])

    return blocks, description_lines


def _min_indent(lines: list[LogicalLine]) -> int:
    if not lines:
        return 0
    return min(ln.indent for ln in lines)


def _build_tree(
    lines: list[LogicalLine], start: int, end: int, base_indent: int
) -> list[RawBlock]:
    """Recursively build tree from lines[start:end] at base_indent level."""
    blocks: list[RawBlock] = []
    i = start

    while i < end:
        ln = lines[i]
        if ln.indent == base_indent:
            block = RawBlock(line=ln)
            # Find children: subsequent lines with indent > base_indent
            child_start = i + 1
            child_end = child_start
            while child_end < end and lines[child_end].indent > base_indent:
                child_end += 1

            if child_start < child_end:
                child_indent = _min_indent(lines[child_start:child_end])
                block.children = _build_tree(
                    lines, child_start, child_end, child_indent
                )
            blocks.append(block)
            i = child_end
        else:
            # Skip lines with unexpected indentation (shouldn't happen)
            i += 1

    return blocks


def _attach_metadata(
    blocks: list[RawBlock], all_lines: list[LogicalLine]
) -> None:
    """Attach metadata lines to the preceding step block."""
    block_by_line: dict[int, RawBlock] = {}

    def _register(b: RawBlock) -> None:
        block_by_line[b.line.span.line] = b
        for child in b.children:
            _register(child)

    for b in blocks:
        _register(b)

    last_block: RawBlock | None = None
    for ln in all_lines:
        if ln.line_type == LineType.STEP:
            last_block = block_by_line.get(ln.span.line)
        elif ln.line_type == LineType.METADATA and last_block is not None:
            # content is "key: value"
            key, _, value = ln.content.partition(": ")
            last_block.metadata[key] = value
