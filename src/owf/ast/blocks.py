"""Block AST nodes — structured workout blocks (superset, circuit, WoD types)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from owf.errors import SourceSpan
from owf.units import Duration


@dataclass(frozen=True, slots=True)
class Superset:
    """A superset block: Nx superset: with sub-steps."""

    count: int
    steps: tuple[Any, ...] = ()
    notes: tuple[str, ...] = ()
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class Circuit:
    """A circuit block: Nx circuit: with sub-steps."""

    count: int
    steps: tuple[Any, ...] = ()
    notes: tuple[str, ...] = ()
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class EMOM:
    """EMOM block: emom duration: with sub-steps."""

    duration: Duration
    steps: tuple[Any, ...] = ()
    notes: tuple[str, ...] = ()
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class AlternatingEMOM:
    """Alternating EMOM: emom duration alternating: with sub-steps."""

    duration: Duration
    steps: tuple[Any, ...] = ()
    notes: tuple[str, ...] = ()
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class CustomInterval:
    """Custom interval: every interval for duration: with sub-steps."""

    interval: Duration
    duration: Duration
    steps: tuple[Any, ...] = ()
    notes: tuple[str, ...] = ()
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class AMRAP:
    """AMRAP block: amrap duration: with sub-steps."""

    duration: Duration
    steps: tuple[Any, ...] = ()
    notes: tuple[str, ...] = ()
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class ForTime:
    """For-time block: for-time [time_cap]: with sub-steps."""

    time_cap: Duration | None = None
    steps: tuple[Any, ...] = ()
    notes: tuple[str, ...] = ()
    span: SourceSpan | None = field(default=None, compare=False, repr=False)
