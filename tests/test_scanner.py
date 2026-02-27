"""Tests for the line scanner."""

from owf.parser.scanner import LineType, scan


def test_blank_lines():
    lines = scan("\n\n")
    assert all(ln.line_type == LineType.BLANK for ln in lines)


def test_frontmatter_fences():
    lines = scan("---\nFTP: 250W\n---")
    fences = [ln for ln in lines if ln.line_type == LineType.FRONTMATTER_FENCE]
    assert len(fences) == 2


def test_heading():
    lines = scan("# Threshold Ride [bike]")
    assert lines[0].line_type == LineType.HEADING
    assert lines[0].content == "Threshold Ride [bike]"


def test_session_heading():
    lines = scan("## Saturday Training")
    assert lines[0].line_type == LineType.SESSION_HEADING
    assert lines[0].content == "Saturday Training"


def test_step_line():
    lines = scan("- warmup 15min @easy")
    assert lines[0].line_type == LineType.STEP
    assert lines[0].content == "warmup 15min @easy"
    assert lines[0].indent == 0


def test_indented_step():
    lines = scan("  - bike 5min @200W")
    assert lines[0].line_type == LineType.STEP
    assert lines[0].indent == 2
    assert lines[0].content == "bike 5min @200W"


def test_nested_steps():
    text = "- 5x:\n  - bike 5min @200W\n  - recover 3min @easy"
    lines = scan(text)
    steps = [ln for ln in lines if ln.line_type == LineType.STEP]
    assert len(steps) == 3
    assert steps[0].indent == 0
    assert steps[1].indent == 2
    assert steps[2].indent == 2


def test_note():
    lines = scan("> Felt strong today")
    assert lines[0].line_type == LineType.NOTE
    assert lines[0].content == "Felt strong today"


def test_empty_note():
    lines = scan(">")
    assert lines[0].line_type == LineType.NOTE
    assert lines[0].content == ""


def test_line_numbers():
    text = "# Title\n\n- step 1\n- step 2"
    lines = scan(text)
    assert lines[0].span.line == 1
    assert lines[1].span.line == 2
    assert lines[2].span.line == 3
    assert lines[3].span.line == 4


def test_full_document_scan():
    text = """---
FTP: 250W
---

# Ride [bike]

- warmup 15min @easy
- 5x:
  - bike 5min @200W
  - recover 3min @easy
- cooldown 10min @easy

> Nice ride."""
    lines = scan(text)
    types = [ln.line_type for ln in lines]
    assert types.count(LineType.FRONTMATTER_FENCE) == 2
    assert types.count(LineType.HEADING) == 1
    assert types.count(LineType.NOTE) == 1
    steps = [ln for ln in lines if ln.line_type == LineType.STEP]
    assert len(steps) == 5
