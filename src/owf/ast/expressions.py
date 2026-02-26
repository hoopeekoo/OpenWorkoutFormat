"""Expression AST nodes for computed values."""

from __future__ import annotations

from dataclasses import dataclass, field

from owf.errors import SourceSpan


@dataclass(frozen=True, slots=True)
class Literal:
    """A literal numeric value with optional unit, e.g. 200W, 80kg."""

    value: float
    unit: str | None = None
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class VarRef:
    """Reference to a frontmatter variable, e.g. FTP, 1RM bench press."""

    name: str
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class Percentage:
    """Percentage of an expression, e.g. 80% of FTP."""

    percent: float
    of: Literal | VarRef | Percentage | BinOp
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class BinOp:
    """Binary operation, e.g. bodyweight + 20kg."""

    op: str  # '+' or '-'
    left: Literal | VarRef | Percentage | BinOp
    right: Literal | VarRef | Percentage | BinOp
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


# Union type for all expressions
Expression = Literal | VarRef | Percentage | BinOp
