"""Tests for the loader (file I/O)."""

from __future__ import annotations

from pathlib import Path

from owf.ast.steps import EnduranceStep
from owf.loader import load


def test_load_simple_file(valid_dir: Path):
    doc = load(valid_dir / "simple_endurance.owf")
    assert len(doc.workouts) == 1
    assert doc.workouts[0].name == "Easy Run"


def test_load_with_frontmatter(valid_dir: Path):
    doc = load(valid_dir / "with_frontmatter.owf")
    assert doc.metadata == {"FTP": "250W"}
    assert len(doc.workouts) == 1


def test_load_includes_source(valid_dir: Path):
    doc = load(valid_dir / "includes_source.owf")
    assert len(doc.workouts) == 2

    w1 = doc.workouts[0]
    assert w1.name == "Warm Up"
    assert len(w1.steps) == 1
    assert isinstance(w1.steps[0], EnduranceStep)

    w2 = doc.workouts[1]
    assert w2.name == "Cool Down"
    assert len(w2.steps) == 1
    assert isinstance(w2.steps[0], EnduranceStep)


def test_load_examples_endurance():
    doc = load(Path("examples/endurance.owf"))
    assert len(doc.workouts) == 1
    assert doc.metadata == {}


def test_load_examples_strength():
    doc = load(Path("examples/strength.owf"))
    assert len(doc.workouts) == 1
    assert doc.workouts[0].name == "Upper Body"


def test_load_examples_crossfit():
    doc = load(Path("examples/crossfit.owf"))
    assert len(doc.workouts) == 5


def test_load_examples_composed():
    doc = load(Path("examples/composed.owf"))
    # composed.owf has # Full Session, # Threshold Ride, # Upper Body
    # Now these are 3 flat workouts
    assert len(doc.workouts) == 3
    assert doc.workouts[0].name == "Full Session"
    assert doc.workouts[1].name == "Threshold Ride"
    assert doc.workouts[2].name == "Upper Body"


def test_load_examples_weekend_session():
    doc = load(Path("examples/weekend_session.owf"))
    # weekend_session.owf has # Run Warmup, # Chipper, # Cooldown
    assert len(doc.workouts) == 3
    assert doc.workouts[0].name == "Run Warmup"
    assert doc.workouts[1].name == "Chipper"
    assert doc.workouts[2].name == "Cooldown"
