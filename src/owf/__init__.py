"""OpenWorkoutFormat — a human-readable workout description language.

Public API:
    parse(text)             — parse OWF text into a Document AST
    load(path)              — parse an OWF file
    dumps(doc)              — serialize a Document AST back to OWF text
    resolve(doc, variables) — evaluate expressions against caller-supplied variables
"""

from __future__ import annotations

from owf.ast.base import Document
from owf.loader import load
from owf.parser.step_parser import parse_document
from owf.resolver import resolve
from owf.serializer import dumps


def parse(text: str) -> Document:
    """Parse OWF text into a Document AST."""
    return parse_document(text)


__all__ = ["Document", "dumps", "load", "parse", "resolve"]
