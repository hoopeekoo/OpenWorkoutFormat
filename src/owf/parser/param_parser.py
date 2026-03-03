"""Parameter parser — handles @-prefixed parameters and rest:duration."""

from __future__ import annotations

import re

from owf.ast.params import (
    BodyweightPlusParam,
    HeartRateParam,
    PaceParam,
    Param,
    PercentOfParam,
    PowerParam,
    RIRParam,
    RPEParam,
    WeightParam,
    ZoneParam,
)
from owf.errors import ParseError, SourceSpan
from owf.units import Duration, Pace

# Old intensity names that are no longer valid
_REMOVED_INTENSITIES = frozenset(
    {"easy", "moderate", "hard", "max", "threshold", "tempo"}
)

# Regex for rest:duration (captures everything after "rest:")
REST_PATTERN = re.compile(r"rest:(.+)")

# Regex for bodyweight + Nkg/Nlb
_BW_PLUS_RE = re.compile(
    r"^bodyweight\s*\+\s*(\d+(?:\.\d+)?)\s*(kg|lb|lbs)$"
)


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

        # 1. Zone: @Z1, @Z2, etc.
        if re.match(r"^Z\d$", value):
            params.append(ZoneParam(zone=value, span=span))
            i += 1
            continue

        # 2. RPE: @RPE or @RPE7 — next token might be the number
        if value.upper().startswith("RPE"):
            rpe_val = value[3:].strip()
            if rpe_val:
                params.append(RPEParam(value=int(rpe_val), span=span))
                i += 1
                continue
            if i + 1 < len(tokens) and _is_number(tokens[i + 1]):
                params.append(RPEParam(value=int(tokens[i + 1]), span=span))
                i += 2
                continue
            i += 1
            continue

        # 3. RIR: @RIR or @RIR2 — next token might be the number
        if value.upper().startswith("RIR"):
            rir_val = value[3:].strip()
            if rir_val:
                params.append(RIRParam(value=int(rir_val), span=span))
                i += 1
                continue
            if i + 1 < len(tokens) and _is_number(tokens[i + 1]):
                params.append(
                    RIRParam(value=int(float(tokens[i + 1])), span=span)
                )
                i += 2
                continue
            i += 1
            continue

        # 4. Pace: @4:30/km or @pace:4:30/km
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

        # 5. Percent of variable: @N% — collect "of VAR" from following tokens
        pct_m = re.match(r"^(\d+(?:\.\d+)?)%$", value)
        if pct_m:
            pct = float(pct_m.group(1))
            # Expect "of" then variable name tokens
            if i + 1 < len(tokens) and tokens[i + 1].lower() == "of":
                var_tokens: list[str] = []
                j = i + 2
                while j < len(tokens):
                    next_tok = tokens[j]
                    if next_tok.startswith("@") or REST_PATTERN.match(next_tok):
                        break
                    var_tokens.append(next_tok)
                    j += 1
                if var_tokens:
                    variable = " ".join(var_tokens)
                    params.append(
                        PercentOfParam(
                            percent=pct, variable=variable, span=span
                        )
                    )
                    i = j
                    continue
            raise ParseError(
                f"Expected 'of VARIABLE' after '{pct}%'", span
            )

        # 6. Bodyweight plus: @bodyweight — collect "+ Nkg" from following tokens
        if value.lower() == "bodyweight":
            # Collect remaining expression tokens
            bw_tokens = [value]
            j = i + 1
            while j < len(tokens):
                next_tok = tokens[j]
                if next_tok.startswith("@") or REST_PATTERN.match(next_tok):
                    break
                bw_tokens.append(next_tok)
                j += 1
            bw_str = " ".join(bw_tokens)
            bw_m = _BW_PLUS_RE.match(bw_str)
            if bw_m:
                params.append(
                    BodyweightPlusParam(
                        added=float(bw_m.group(1)),
                        unit=bw_m.group(2),
                        span=span,
                    )
                )
                i = j
                continue
            raise ParseError(
                "Expected '@bodyweight + N<kg|lb>' format", span
            )

        # 7. Power: @NW (literal watts)
        power_m = re.match(r"^(\d+(?:\.\d+)?)W$", value)
        if power_m:
            params.append(
                PowerParam(value=float(power_m.group(1)), span=span)
            )
            i += 1
            continue

        # 8. Heart rate: @Nbpm (literal bpm)
        bpm_m = re.match(r"^(\d+)bpm$", value)
        if bpm_m:
            params.append(
                HeartRateParam(value=int(bpm_m.group(1)), span=span)
            )
            i += 1
            continue

        # 9. Weight: @Nkg, @Nlb, @Nlbs
        weight_m = re.match(r"^(\d+(?:\.\d+)?)(kg|lb|lbs)$", value)
        if weight_m:
            params.append(
                WeightParam(
                    value=float(weight_m.group(1)),
                    unit=weight_m.group(2),
                    span=span,
                )
            )
            i += 1
            continue

        # Reject removed syntax with clear error
        if value.lower() in _REMOVED_INTENSITIES:
            raise ParseError(
                f"Named intensity '@{value}' is no longer supported. "
                f"Use a zone (@Z2), literal (@140bpm, @200W), or "
                f"percentage (@80% of FTP) instead.",
                span,
            )

        raise ParseError(
            f"Unknown parameter '@{value}'. Valid forms: "
            "@Z2, @N% of VAR, @NW, @Nbpm, @MM:SS/km, "
            "@Nkg, @bodyweight + Nkg, @RPE N, @RIR N",
            span,
        )

    return params, rest_duration


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
    raw_tokens = tail.split()
    return raw_tokens
