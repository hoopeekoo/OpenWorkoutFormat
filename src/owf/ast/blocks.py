"""Block AST nodes — structured workout containers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from owf.errors import SourceSpan
from owf.units import Duration


@dataclass(frozen=True, slots=True)
class Interval:
    """Interval block: every <interval> for <duration>: with sub-steps.

    Subsumes EMOM (interval=1min), alternating EMOM (inferred from
    multiple children), and custom intervals.

    Alternation rule: 1 child = repeat each interval.
    Multiple children = rotate through them.
    """

    interval: Duration
    duration: Duration
    steps: tuple[Any, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)
    span: SourceSpan | None = field(default=None, compare=False, repr=False)

    @property
    def is_alternating(self) -> bool:
        """Whether this interval alternates between children."""
        return len(self.steps) > 1


@dataclass(frozen=True, slots=True)
class AMRAP:
    """AMRAP block: amrap duration: with sub-steps."""

    duration: Duration
    steps: tuple[Any, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)
    span: SourceSpan | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class ForTime:
    """For-time block: for-time [time_cap]: with sub-steps."""

    time_cap: Duration | None = None
    steps: tuple[Any, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)
    span: SourceSpan | None = field(default=None, compare=False, repr=False)
