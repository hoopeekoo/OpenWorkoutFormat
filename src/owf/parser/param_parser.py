"""Parameter parser — handles @-prefixed parameters."""

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
    SetTypeParam,
    TempoParam,
    TypedPercentParam,
    WeightParam,
    ZoneParam,
)
from owf.errors import ParseError, SourceSpan
from owf.units import Duration, Pace

# Old intensity names that are no longer valid
_REMOVED_INTENSITIES = frozenset(
    {"easy", "moderate", "hard", "max"}
)

# Valid set type tokens (OWF syntax uses hyphens; AST stores underscores)
_SET_TYPE_TOKENS: dict[str, str] = {
    "warmup": "warmup",
    "drop": "drop",
    "failure": "failure",
    "cluster": "cluster",
    "rest-pause": "rest_pause",
    "myo-rep": "myo_rep",
}

# Known typed percentage targets (no-space compact form)
_TYPED_PERCENT_TARGETS = frozenset({"FTP", "LTHR", "maxHR", "TP", "1RM"})

# Pre-compiled regex for typed percent params
_TYPED_PCT_RE = re.compile(
    r"^(\d+(?:\.\d+)?)%("
    + "|".join(sorted(_TYPED_PERCENT_TARGETS, key=len, reverse=True))
    + r")$"
)

# Zone metric qualifiers
_ZONE_METRICS = frozenset({"power", "hr", "pace"})

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

        if not token.startswith("@"):
            i += 1
            continue

        value = token[1:]  # strip @

        # 1. Rest: @rest or @rest90s — next token is duration
        # BUT NOT @rest-pause (set type) — check set types first
        if value.lower().startswith("rest") and value.lower() not in _SET_TYPE_TOKENS:
            rest_val = value[4:].strip()
            if rest_val:
                rest_duration = Duration.parse(rest_val)
                i += 1
                continue
            if i + 1 < len(tokens) and not tokens[i + 1].startswith("@"):
                rest_duration = Duration.parse(tokens[i + 1])
                i += 2
                continue
            i += 1
            continue

        # 2. Zone: @Z1, @Z2, @Z2:power, @Z3:hr, @Z4:pace
        zone_m = re.match(r"^(Z\d)(?::(\w+))?$", value)
        if zone_m:
            zone_str = zone_m.group(1)
            metric = zone_m.group(2)
            if metric and metric not in _ZONE_METRICS:
                raise ParseError(
                    f"Unknown zone metric '{metric}'. "
                    f"Valid metrics: power, hr, pace",
                    span,
                )
            params.append(ZoneParam(zone=zone_str, metric=metric, span=span))
            i += 1
            continue

        # 2b. Set type: @warmup, @drop, @failure, @cluster, @rest-pause, @myo-rep
        if value.lower() in _SET_TYPE_TOKENS:
            canonical = _SET_TYPE_TOKENS[value.lower()]
            params.append(SetTypeParam(set_type=canonical, span=span))
            i += 1
            continue

        # 2c. Tempo: @tempo 31X0 — next token is the tempo value
        if value.lower() == "tempo":
            if i + 1 < len(tokens) and not tokens[i + 1].startswith("@"):
                params.append(
                    TempoParam(value=tokens[i + 1], span=span)
                )
                i += 2
                continue
            raise ParseError("Expected tempo value after '@tempo'", span)

        # 3. RPE: @RPE or @RPE7 — next token might be the number
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

        # 5a. Typed percent: @95%FTP, @88%LTHR, @92%maxHR, @90%TP, @85%1RM
        typed_pct_m = _TYPED_PCT_RE.match(value)
        if typed_pct_m:
            params.append(
                TypedPercentParam(
                    percent=float(typed_pct_m.group(1)),
                    target=typed_pct_m.group(2),
                    span=span,
                )
            )
            i += 1
            continue

        # 5b. Percent of variable: @N% [of] VAR — "of" is optional
        pct_m = re.match(r"^(\d+(?:\.\d+)?)%$", value)
        if pct_m:
            pct = float(pct_m.group(1))
            # Skip optional "of" keyword, then collect variable name tokens
            j = i + 1
            if j < len(tokens) and tokens[j].lower() == "of":
                j += 1
            var_tokens: list[str] = []
            while j < len(tokens):
                next_tok = tokens[j]
                if next_tok.startswith("@"):
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
                f"Expected variable name after '{pct}%'", span
            )

        # 6. Bodyweight plus: @bodyweight — collect "+ Nkg" from following tokens
        if value.lower() == "bodyweight":
            # Collect remaining expression tokens
            bw_tokens = [value]
            j = i + 1
            while j < len(tokens):
                next_tok = tokens[j]
                if next_tok.startswith("@"):
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
                PowerParam(value=int(round(float(power_m.group(1)))), span=span)
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
            "@Z2, @Z2:power, @N%FTP, @N% of VAR, @NW, @Nbpm, @MM:SS/km, "
            "@Nkg, @bodyweight + Nkg, @RPE N, @RIR N, @tempo VALUE, "
            "@warmup, @drop, @failure, @cluster, @rest-pause, @myo-rep",
            span,
        )

    return params, rest_duration


def _is_number(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


