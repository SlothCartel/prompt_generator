"""Integration smoke tests for CLI execution."""

from __future__ import annotations

import subprocess
import sys


def test_pg_help_exits_zero() -> None:
    """`python -m pg.cli --help` should execute successfully."""
    result = subprocess.run(
        [sys.executable, "-m", "pg.cli", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Prompt Generator (PG) CLI scaffold." in result.stdout
