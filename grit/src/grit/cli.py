"""Grit CLI entry point."""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]
    print("grit: not yet implemented")
    raise SystemExit(0)
