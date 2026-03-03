"""Unit smoke tests for CLI imports."""

import typer
from pg.cli import app


def test_cli_app_importable() -> None:
    """CLI app should import as a Typer app."""
    assert isinstance(app, typer.Typer)
