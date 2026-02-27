"""Tests for the loader (file I/O)."""

from __future__ import annotations

from pathlib import Path

from owf.ast.base import Workout
from owf.ast.steps import EnduranceStep
from owf.loader import load


def test_load_simple_file(valid_dir: Path):
    doc = load(valid_dir / "simple_endurance.owf")
    assert len(doc.workouts) == 1
    assert doc.workouts[0].name == "Easy Run"


def test_load_with_frontmatter(valid_dir: Path):
    doc = load(valid_dir / "with_frontmatter.owf")
    assert doc.variables == {"FTP": "250W"}
    assert len(doc.workouts) == 1


def test_load_session_fixture(valid_dir: Path):
    doc = load(valid_dir / "includes_source.owf")
    assert len(doc.workouts) == 1
    session = doc.workouts[0]
    assert session.name == "Session"
    assert len(session.steps) == 2

    child1 = session.steps[0]
    assert isinstance(child1, Workout)
    assert child1.name == "Warm Up"
    assert len(child1.steps) == 1
    assert isinstance(child1.steps[0], EnduranceStep)

    child2 = session.steps[1]
    assert isinstance(child2, Workout)
    assert child2.name == "Cool Down"
    assert len(child2.steps) == 1
    assert isinstance(child2.steps[0], EnduranceStep)


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
    assert len(doc.workouts) == 1
    session = doc.workouts[0]
    assert session.name == "Full Session"

    # Should contain: warmup, Threshold Ride child, Upper Body child
    child_workouts = [s for s in session.steps if isinstance(s, Workout)]
    assert len(child_workouts) == 2
    assert child_workouts[0].name == "Threshold Ride"
    assert child_workouts[1].name == "Upper Body"


def test_load_examples_weekend_session():
    doc = load(Path("examples/weekend_session.owf"))
    assert len(doc.workouts) == 1
    session = doc.workouts[0]
    assert session.name == "Saturday Session"

    child_workouts = [s for s in session.steps if isinstance(s, Workout)]
    assert len(child_workouts) == 3
    assert child_workouts[0].name == "Run Warmup"
    assert child_workouts[1].name == "Chipper"
    assert child_workouts[2].name == "Cooldown"
