"""Tests for the block builder."""

from owf.parser.block_builder import build_blocks_for_workout
from owf.parser.scanner import LineType, scan


def _get_workout_lines(text: str) -> list:
    """Get non-heading lines for building blocks."""
    lines = scan(text)
    return [ln for ln in lines if ln.line_type != LineType.HEADING]


def test_flat_steps():
    text = "- warmup 15min\n- run 5km\n- cooldown 10min"
    blocks, notes = build_blocks_for_workout(_get_workout_lines(text))
    assert len(blocks) == 3
    assert notes == []


def test_nested_steps():
    text = "- 5x:\n  - bike 5min\n  - recover 3min"
    blocks, notes = build_blocks_for_workout(_get_workout_lines(text))
    assert len(blocks) == 1
    assert blocks[0].content == "5x:"
    assert len(blocks[0].children) == 2


def test_mixed_flat_and_nested():
    text = "- warmup 15min\n- 5x:\n  - bike 5min\n  - recover 3min\n- cooldown 10min"
    blocks, notes = build_blocks_for_workout(_get_workout_lines(text))
    assert len(blocks) == 3
    assert blocks[0].content == "warmup 15min"
    assert blocks[1].content == "5x:"
    assert len(blocks[1].children) == 2
    assert blocks[2].content == "cooldown 10min"


def test_trailing_notes():
    text = "- run 5km\n\n> Great run!"
    blocks, notes = build_blocks_for_workout(_get_workout_lines(text))
    assert len(blocks) == 1
    # The note after the step gets attached to the block
    assert blocks[0].notes == ["Great run!"]


def test_deeply_nested():
    text = "- 3x:\n  - 2x:\n    - run 1km"
    blocks, notes = build_blocks_for_workout(_get_workout_lines(text))
    assert len(blocks) == 1
    assert len(blocks[0].children) == 1
    assert len(blocks[0].children[0].children) == 1
