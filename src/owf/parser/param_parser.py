"""Parameter parser — handles @-prefixed parameters and rest:duration."""

from __future__ import annotations

import re

from owf.ast.expressions import Expression, Literal, Percentage, VarRef
from owf.ast.params import (
    HeartRateParam,
    IntensityParam,
    PaceParam,
    Param,
    PowerParam,
    RPEParam,
    WeightParam,
)
from owf.errors import SourceSpan
from owf.parser.expr_parser import parse_expression
from owf.units import Duration, Pace

INTENSITY_NAMES = frozenset({"easy", "moderate", "hard", "max", "threshold", "tempo"})

# Regex for rest:duration
REST_PATTERN = re.compile(r"rest:(\d+(?:\.\d+)?(?:s|sec|min|h|hr|hour))")


def parse_params(
    tokens: list[str], span: SourceSpan | None = None
) -> tuple[list[Param], Duration | None]:
    """Parse a list of @-tokens into Param objects.

    Returns (params, rest_duration).
    """
    params: list[Param] = []
    rest_duration: Duration | None = None

    i = 0
    while i < len(tokens):
        token = tokens[i]

        # rest:duration
        rest_m = REST_PATTERN.match(token)
        if rest_m:
            rest_duration = Duration.parse(rest_m.group(1))
            i += 1
            continue

        if not token.startswith("@"):
            i += 1
            continue

        value = token[1:]  # strip @

        # Try pace: @4:30/km or @pace:4:30/km
        if value.startswith("pace:"):
            pace_str = value[5:]
            try:
                pace = Pace.parse(pace_str)
                params.append(PaceParam(pace=pace, span=span))
                i += 1
                continue
            except ValueError:
                pass

        try:
            pace = Pace.parse(value)
            params.append(PaceParam(pace=pace, span=span))
            i += 1
            continue
        except ValueError:
            pass

        # RPE: @RPE or @RPE7 — next token might be the number
        if value.upper().startswith("RPE"):
            rpe_val = value[3:].strip()
            if rpe_val:
                params.append(RPEParam(value=float(rpe_val), span=span))
                i += 1
                continue
            # Check next token for the number
            if i + 1 < len(tokens) and _is_number(tokens[i + 1]):
                params.append(RPEParam(value=float(tokens[i + 1]), span=span))
                i += 2
                continue
            i += 1
            continue

        # Heart rate zone: @Z1, @Z2, etc.
        if re.match(r"^Z\d$", value):
            params.append(HeartRateParam(value=value, span=span))
            i += 1
            continue

        # Heart rate bpm: @140bpm
        bpm_m = re.match(r"^(\d+)bpm$", value)
        if bpm_m:
            params.append(
                HeartRateParam(
                    value=Literal(value=float(bpm_m.group(1)), unit="bpm"),
                    span=span,
                )
            )
            i += 1
            continue

        # Named intensity: @easy, @moderate, etc.
        if value.lower() in INTENSITY_NAMES:
            params.append(IntensityParam(name=value.lower(), span=span))
            i += 1
            continue

        # Expression: could be "80%" with "of" "FTP" following, or "200W", "80kg"
        # Collect tokens that form an expression
        expr_tokens = [value]
        j = i + 1
        while j < len(tokens):
            next_tok = tokens[j]
            if next_tok.startswith("@") or REST_PATTERN.match(next_tok):
                break
            expr_tokens.append(next_tok)
            j += 1

        expr_str = " ".join(expr_tokens)
        expr, param = _classify_expression(expr_str, span)
        if param is not None:
            params.append(param)
        i = j

    return params, rest_duration


def _classify_expression(
    text: str, span: SourceSpan | None
) -> tuple[Expression | None, Param | None]:
    """Classify an expression string into the appropriate Param type."""
    expr = parse_expression(text)

    # Determine param type from the expression's unit or structure
    if isinstance(expr, Literal):
        if expr.unit == "W":
            return expr, PowerParam(value=expr, span=span)
        if expr.unit in ("kg", "lb", "lbs"):
            return expr, WeightParam(value=expr, span=span)
        if expr.unit == "bpm":
            return expr, HeartRateParam(value=expr, span=span)
        if expr.unit in ("in",):
            return expr, WeightParam(value=expr, span=span)
        return expr, PowerParam(value=expr, span=span)

    if isinstance(expr, Percentage):
        # Look at what it's a percentage of
        inner = expr.of
        if isinstance(inner, VarRef):
            name_lower = inner.name.lower()
            if "hr" in name_lower or "heart" in name_lower:
                return expr, HeartRateParam(value=expr, span=span)
            if "rm" in name_lower or "1rm" in name_lower.replace(" ", ""):
                return expr, WeightParam(value=expr, span=span)
            # Default: power (FTP etc.)
            return expr, PowerParam(value=expr, span=span)
        return expr, PowerParam(value=expr, span=span)

    if isinstance(expr, VarRef):
        return expr, PowerParam(value=expr, span=span)

    return expr, PowerParam(value=expr, span=span)


def _is_number(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


def tokenize_step_tail(tail: str) -> list[str]:
    """Split the tail portion of a step line into tokens.

    Respects @-prefixed params, rest:duration, and groups
    'X% of VarName' expressions together.
    """
    # Split on whitespace but keep @-prefixed groups together
    raw_tokens = tail.split()
    return raw_tokens
