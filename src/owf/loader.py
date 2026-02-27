"""File I/O — load an OWF file and parse it."""

from __future__ import annotations

from pathlib import Path

from owf.ast.base import Document
from owf.parser.step_parser import parse_document


def load(path: str | Path) -> Document:
    """Load and parse an OWF file."""
    text = Path(path).read_text(encoding="utf-8")
    return parse_document(text)
