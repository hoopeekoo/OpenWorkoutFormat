"""Frontmatter parser — extracts YAML-like key-value pairs from --- fences."""

from __future__ import annotations

import re

from owf.errors import ParseError, SourceSpan


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Extract frontmatter variables and return remaining text.

    Returns (variables_dict, remaining_text).
    """
    lines = text.split("\n")

    # Find opening ---
    start = -1
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "---":
            start = i
            break
        if stripped:
            # Non-blank, non-fence line before frontmatter → no frontmatter
            return {}, text

    if start == -1:
        return {}, text

    # Find closing ---
    end = -1
    for i in range(start + 1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break

    if end == -1:
        raise ParseError(
            "Unclosed frontmatter: missing closing '---'",
            SourceSpan(line=start + 1, col=1),
        )

    # Parse key-value pairs
    variables: dict[str, str] = {}
    for i in range(start + 1, end):
        line = lines[i].strip()
        if not line:
            continue

        # key: value
        m = re.match(r"^(.+?):\s*(.+)$", line)
        if m:
            key = m.group(1).strip()
            value = m.group(2).strip()
            variables[key] = value
        else:
            raise ParseError(
                f"Invalid frontmatter line: {line!r}",
                SourceSpan(line=i + 1, col=1),
            )

    # Remaining text is everything after closing fence
    remaining = "\n".join(lines[end + 1 :])
    return variables, remaining
