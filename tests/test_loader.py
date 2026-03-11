"""Tests for the loader (file I/O)."""

from __future__ import annotations

from pathlib import Path

from owf.ast.steps import Step
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
    assert isinstance(w1.steps[0], Step)

    w2 = doc.workouts[1]
    assert w2.name == "Cool Down"
    assert len(w2.steps) == 1
    assert isinstance(w2.steps[0], Step)


def test_load_examples_easy_run():
    doc = load(Path("examples/easy_run.owf"))
    assert len(doc.workouts) == 1
    assert doc.workouts[0].name == "Easy Run"
    assert doc.workouts[0].sport_type == "Running"


def test_load_examples_strength_upper():
    doc = load(Path("examples/strength_upper.owf"))
    assert len(doc.workouts) == 1
    assert doc.workouts[0].name == "Upper Body"


def test_load_examples_crossfit_benchmarks():
    doc = load(Path("examples/crossfit_benchmarks.owf"))
    assert len(doc.workouts) == 3


def test_load_examples_triathlon_brick():
    doc = load(Path("examples/triathlon_brick.owf"))
    assert len(doc.workouts) == 3
    assert doc.workouts[0].name == "Swim"
    assert doc.workouts[1].name == "Bike"
    assert doc.workouts[2].name == "Brick Run"


def test_load_examples_emom_amrap():
    doc = load(Path("examples/emom_amrap.owf"))
    assert len(doc.workouts) == 4
    assert doc.workouts[0].name == "EMOM Strength"
    assert doc.workouts[2].name == "Cindy"
