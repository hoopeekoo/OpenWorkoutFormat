"""Duration and distance parsing and representation."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Duration:
    """A time duration stored as total seconds."""

    seconds: float

    _PATTERN = re.compile(
        r"^(?:"
        r"(?P<hms>(?P<h>\d+):(?P<m>\d{1,2}):(?P<s>\d{1,2}))"
        r"|(?P<ms>(?P<min>\d+):(?P<sec>\d{2}))"
        r"|(?P<num>\d+(?:\.\d+)?)\s*(?P<unit>s|sec|min|h|hr|hour)"
        r")$"
    )

    @classmethod
    def parse(cls, text: str) -> Duration:
        text = text.strip()
        m = cls._PATTERN.match(text)
        if m is None:
            raise ValueError(f"Cannot parse duration: {text!r}")
        if m.group("hms"):
            h = int(m.group("h"))
            mi = int(m.group("m"))
            s = int(m.group("s"))
            return cls(seconds=h * 3600 + mi * 60 + s)
        if m.group("ms"):
            mi = int(m.group("min"))
            s = int(m.group("sec"))
            return cls(seconds=mi * 60 + s)
        num = float(m.group("num"))
        unit = m.group("unit")
        if unit in ("s", "sec"):
            return cls(seconds=num)
        if unit == "min":
            return cls(seconds=num * 60)
        if unit in ("h", "hr", "hour"):
            return cls(seconds=num * 3600)
        raise ValueError(f"Unknown duration unit: {unit!r}")

    def __str__(self) -> str:
        s = self.seconds
        if s < 60:
            v = int(s) if s == int(s) else s
            return f"{v}s"
        if s < 3600:
            mins = s / 60
            if mins == int(mins):
                return f"{int(mins)}min"
            # Not a clean minute — use seconds
            v = int(s) if s == int(s) else s
            return f"{v}s"
        hours = s / 3600
        if hours == int(hours):
            return f"{int(hours)}h"
        # Not a clean hour — use minutes if clean, else seconds
        mins = s / 60
        if mins == int(mins):
            return f"{int(mins)}min"
        v = int(s) if s == int(s) else s
        return f"{v}s"


@dataclass(frozen=True, slots=True)
class Distance:
    """A distance with value and unit."""

    value: float
    unit: str  # m, km, mi, mile, yd, ft

    _PATTERN = re.compile(
        r"^(?P<num>\d+(?:\.\d+)?)\s*(?P<unit>m|km|mi|mile|miles|yd|ft|in)$"
    )

    @classmethod
    def parse(cls, text: str) -> Distance:
        text = text.strip()
        m = cls._PATTERN.match(text)
        if m is None:
            raise ValueError(f"Cannot parse distance: {text!r}")
        num = float(m.group("num"))
        unit = m.group("unit")
        # Normalize miles
        if unit == "miles":
            unit = "mile"
        return cls(value=num, unit=unit)

    def __str__(self) -> str:
        v = int(self.value) if self.value == int(self.value) else self.value
        return f"{v}{self.unit}"


@dataclass(frozen=True, slots=True)
class Pace:
    """A pace like 4:30/km."""

    minutes: int
    seconds: int
    unit: str  # km, mi, mile

    _PATTERN = re.compile(r"^(?P<min>\d+):(?P<sec>\d{2})/(?P<unit>km|mi|mile)$")

    @classmethod
    def parse(cls, text: str) -> Pace:
        text = text.strip()
        m = cls._PATTERN.match(text)
        if m is None:
            raise ValueError(f"Cannot parse pace: {text!r}")
        return cls(
            minutes=int(m.group("min")),
            seconds=int(m.group("sec")),
            unit=m.group("unit"),
        )

    def __str__(self) -> str:
        return f"{self.minutes}:{self.seconds:02d}/{self.unit}"
