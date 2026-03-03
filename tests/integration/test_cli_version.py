"""Integration smoke tests for CLI version option."""

from __future__ import annotations

import subprocess
import sys


def test_pg_version_exits_zero() -> None:
    """`python -m pg.cli --version` should execute successfully."""
    result = subprocess.run(
        [sys.executable, "-m", "pg.cli", "--version"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "pg 0.1.0" in result.stdout.strip()
