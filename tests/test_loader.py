"""Tests for the loader (file I/O and include resolution)."""

from __future__ import annotations

from pathlib import Path

import pytest

from owf.ast.steps import IncludeStep, RestStep
from owf.loader import load


def test_load_simple_file(valid_dir: Path):
    doc = load(valid_dir / "simple_endurance.owf")
    assert len(doc.workouts) == 1
    assert doc.workouts[0].name == "Easy Run"


def test_load_with_frontmatter(valid_dir: Path):
    doc = load(valid_dir / "with_frontmatter.owf")
    assert doc.variables == {"FTP": "250W"}
    assert len(doc.workouts) == 1


def test_load_with_same_file_includes(valid_dir: Path):
    doc = load(valid_dir / "includes_source.owf")
    assert len(doc.workouts) == 3
    session = doc.workouts[2]
    assert session.name == "Session"
    assert len(session.steps) == 3

    # Includes should be resolved to Workout objects
    inc1 = session.steps[0]
    assert isinstance(inc1, IncludeStep)
    assert inc1.resolved is not None
    assert inc1.resolved.name == "Warm Up"

    assert isinstance(session.steps[1], RestStep)

    inc2 = session.steps[2]
    assert isinstance(inc2, IncludeStep)
    assert inc2.resolved is not None
    assert inc2.resolved.name == "Cool Down"


def test_load_examples_endurance():
    doc = load(Path("examples/endurance.owf"))
    assert len(doc.workouts) == 1
    assert doc.variables["FTP"] == "250W"


def test_load_examples_strength():
    doc = load(Path("examples/strength.owf"))
    assert len(doc.workouts) == 1
    assert doc.workouts[0].name == "Upper Body"


def test_load_examples_crossfit():
    doc = load(Path("examples/crossfit.owf"))
    assert len(doc.workouts) == 5


def test_load_examples_composed():
    doc = load(Path("examples/composed.owf"))
    assert len(doc.workouts) == 3
    # Full Session should have resolved includes
    full = doc.workouts[2]
    assert full.name == "Full Session"
    inc = full.steps[0]
    assert isinstance(inc, IncludeStep)
    assert inc.resolved is not None
    assert inc.resolved.name == "Threshold Ride"
