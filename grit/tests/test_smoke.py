"""Smoke test: Grit can import OWF."""

from __future__ import annotations


def test_grit_imports_owf() -> None:
    import owf

    assert hasattr(owf, "parse")
    assert hasattr(owf, "load")


def test_grit_version() -> None:
    import grit

    assert grit.__version__ == "0.1.0"
