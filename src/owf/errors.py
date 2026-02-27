"""Error types for OWF parsing and resolution."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceSpan:
    """Location in source text for error reporting."""

    line: int  # 1-based
    col: int  # 1-based
    end_line: int | None = None
    end_col: int | None = None

    def __str__(self) -> str:
        s = f"line {self.line}, col {self.col}"
        if self.end_line is not None and self.end_line != self.line:
            s += f" to line {self.end_line}, col {self.end_col}"
        return s


class OWFError(Exception):
    """Base exception for all OWF errors."""

    def __init__(self, message: str, span: SourceSpan | None = None) -> None:
        self.span = span
        if span is not None:
            message = f"{span}: {message}"
        super().__init__(message)


class ParseError(OWFError):
    """Raised when the parser encounters invalid syntax."""


class ResolveError(OWFError):
    """Raised when expression resolution fails."""
