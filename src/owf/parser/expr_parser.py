"""Expression parser — parses computed expressions like '80% of FTP'."""

from __future__ import annotations

import re

from owf.ast.expressions import BinOp, Expression, Literal, Percentage, VarRef


def parse_expression(text: str) -> Expression:
    """Parse an expression string into an Expression AST node.

    Supported forms:
    - "200W" → Literal(200, "W")
    - "80kg" → Literal(80, "kg")
    - "FTP" → VarRef("FTP")
    - "80% of FTP" → Percentage(80, VarRef("FTP"))
    - "70% of 1RM bench press" → Percentage(70, VarRef("1RM bench press"))
    - "bodyweight + 20kg" → BinOp("+", VarRef("bodyweight"), Literal(20, "kg"))
    """
    text = text.strip()
    if not text:
        raise ValueError("Empty expression")

    # Try percentage: N% of <expr>
    pct_m = re.match(r"^(\d+(?:\.\d+)?)%\s+of\s+(.+)$", text)
    if pct_m:
        pct = float(pct_m.group(1))
        of_expr = parse_expression(pct_m.group(2))
        return Percentage(percent=pct, of=of_expr)

    # Try binary operation: <expr> +/- <expr>
    # Find +/- not inside other constructs
    bin_m = re.match(r"^(.+?)\s*([+-])\s*(.+)$", text)
    if bin_m:
        left_str = bin_m.group(1).strip()
        op = bin_m.group(2)
        right_str = bin_m.group(3).strip()
        # Only treat as binop if both sides parse
        try:
            left = parse_expression(left_str)
            right = parse_expression(right_str)
            return BinOp(op=op, left=left, right=right)
        except ValueError:
            pass

    # Try literal with unit: 200W, 80kg, 24in, etc.
    lit_m = re.match(
        r"^(\d+(?:\.\d+)?)\s*(W|kg|lb|lbs|bpm|in|m|km|mi|cal|kcal)$", text
    )
    if lit_m:
        return Literal(value=float(lit_m.group(1)), unit=lit_m.group(2))

    # Try bare number
    if re.match(r"^\d+(?:\.\d+)?$", text):
        return Literal(value=float(text))

    # Try bare percentage (without "of"): 80%
    pct_bare = re.match(r"^(\d+(?:\.\d+)?)%$", text)
    if pct_bare:
        return Literal(value=float(pct_bare.group(1)), unit="%")

    # Variable reference
    return VarRef(name=text)
