"""Line scanner — classifies each line by prefix."""

from __future__ import annotations

import enum
from dataclasses import dataclass

from owf.errors import SourceSpan


class LineType(enum.Enum):
    BLANK = "blank"
    FRONTMATTER_FENCE = "frontmatter_fence"
    HEADING = "heading"
    STEP = "step"
    NOTE = "note"


@dataclass(frozen=True, slots=True)
class LogicalLine:
    """A classified line from the source text."""

    line_type: LineType
    text: str  # Original text (stripped of trailing newline)
    indent: int  # Number of leading spaces
    content: str  # Text after stripping prefix and indent
    span: SourceSpan


def scan(text: str) -> list[LogicalLine]:
    """Scan text into a list of logical lines."""
    lines: list[LogicalLine] = []
    for lineno, raw in enumerate(text.split("\n"), start=1):
        stripped = raw.rstrip()

        if not stripped:
            lines.append(
                LogicalLine(
                    line_type=LineType.BLANK,
                    text=raw,
                    indent=0,
                    content="",
                    span=SourceSpan(line=lineno, col=1),
                )
            )
            continue

        if stripped == "---":
            lines.append(
                LogicalLine(
                    line_type=LineType.FRONTMATTER_FENCE,
                    text=raw,
                    indent=0,
                    content="---",
                    span=SourceSpan(line=lineno, col=1),
                )
            )
            continue

        if stripped.startswith("# "):
            lines.append(
                LogicalLine(
                    line_type=LineType.HEADING,
                    text=raw,
                    indent=0,
                    content=stripped[2:],
                    span=SourceSpan(line=lineno, col=1),
                )
            )
            continue

        if stripped.startswith("> ") or stripped == ">":
            content = stripped[2:] if stripped.startswith("> ") else ""
            lines.append(
                LogicalLine(
                    line_type=LineType.NOTE,
                    text=raw,
                    indent=0,
                    content=content,
                    span=SourceSpan(line=lineno, col=1),
                )
            )
            continue

        # Count leading spaces for indentation
        indent = len(raw) - len(raw.lstrip(" "))
        inner = stripped.lstrip()

        if inner.startswith("- ") or inner == "-":
            content = inner[2:] if inner.startswith("- ") else ""
            lines.append(
                LogicalLine(
                    line_type=LineType.STEP,
                    text=raw,
                    indent=indent,
                    content=content,
                    span=SourceSpan(line=lineno, col=indent + 1),
                )
            )
            continue

        # Treat anything else as a continuation or unknown — skip for now
        # In practice, frontmatter content lines will be handled by the
        # frontmatter parser directly, not through the scanner.
        lines.append(
            LogicalLine(
                line_type=LineType.BLANK,
                text=raw,
                indent=0,
                content=stripped,
                span=SourceSpan(line=lineno, col=1),
            )
        )

    return lines
