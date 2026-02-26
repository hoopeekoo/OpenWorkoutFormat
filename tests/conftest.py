"""Shared test fixtures for OWF tests."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"
VALID_DIR = FIXTURES_DIR / "valid"
INVALID_DIR = FIXTURES_DIR / "invalid"


@pytest.fixture
def valid_dir() -> Path:
    return VALID_DIR


@pytest.fixture
def invalid_dir() -> Path:
    return INVALID_DIR
