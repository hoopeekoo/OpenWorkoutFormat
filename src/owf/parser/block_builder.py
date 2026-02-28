"""Block builder — turns flat logical lines into an indentation tree."""

from __future__ import annotations

from dataclasses import dataclass, field

from owf.errors import SourceSpan
from owf.parser.scanner import LineType, LogicalLine


@dataclass(slots=True)
class RawBlock:
    """A step line with its children (determined by indentation)."""

    line: LogicalLine
    children: list[RawBlock] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def content(self) -> str:
        return self.line.content

    @property
    def span(self) -> SourceSpan:
        return self.line.span


def build_blocks(lines: list[LogicalLine]) -> list[RawBlock]:
    """Build a tree of RawBlocks from step lines using indentation.

    Returns top-level blocks (one per workout heading, or step lines at the
    top level). Notes are attached to the preceding block.
    """
    step_lines = [ln for ln in lines if ln.line_type == LineType.STEP]
    if not step_lines:
        return []

    return _build_tree(step_lines, 0, len(step_lines), _min_indent(step_lines))


def build_blocks_for_workout(
    lines: list[LogicalLine],
) -> tuple[list[RawBlock], list[str]]:
    """Build blocks from lines belonging to a single workout section.

    Returns (blocks, trailing_notes).
    """
    step_lines: list[LogicalLine] = []
    trailing_notes: list[str] = []
    note_lines: list[LogicalLine] = []

    for ln in lines:
        if ln.line_type == LineType.NOTE:
            note_lines.append(ln)
        elif ln.line_type == LineType.STEP:
            # Attach any pending notes to... we'll handle after tree build
            step_lines.append(ln)
            note_lines = []
        elif ln.line_type == LineType.BLANK:
            continue

    if not step_lines:
        # Might just have notes
        all_notes = [ln.content for ln in lines if ln.line_type == LineType.NOTE]
        return [], all_notes

    # Find where workout-level (trailing) notes begin.
    # Trailing notes are separated from the last step by at least one blank
    # line.  Notes immediately after the last step (no blank line) are
    # step-level and will be attached by _attach_notes below.
    last_step_idx = max(
        i for i, ln in enumerate(lines) if ln.line_type == LineType.STEP
    )

    saw_blank = False
    attach_boundary = len(lines)
    for i in range(last_step_idx + 1, len(lines)):
        ln = lines[i]
        if ln.line_type == LineType.BLANK:
            saw_blank = True
        elif ln.line_type == LineType.NOTE and saw_blank:
            attach_boundary = i
            break

    for i in range(attach_boundary, len(lines)):
        if lines[i].line_type == LineType.NOTE:
            trailing_notes.append(lines[i].content)

    blocks = _build_tree(step_lines, 0, len(step_lines), _min_indent(step_lines))

    # Attach step-level notes only (up to the trailing boundary)
    _attach_notes(blocks, lines[:attach_boundary])

    return blocks, trailing_notes


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


def _attach_notes(blocks: list[RawBlock], all_lines: list[LogicalLine]) -> None:
    """Attach note lines to the preceding step block."""
    # Build a map from step line number to block
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
        elif ln.line_type == LineType.NOTE and last_block is not None:
            last_block.notes.append(ln.content)
