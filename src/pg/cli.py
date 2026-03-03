"""Minimal Typer CLI scaffold for PG Phase 0."""

from __future__ import annotations

import typer
from pg import __version__
from pg.constants import APP_NAME

app = typer.Typer(help="Prompt Generator (PG) CLI scaffold.")


def version_callback(value: bool) -> None:
    """Print version and exit when --version is provided."""
    if value:
        typer.echo(f"{APP_NAME} {__version__}")
        raise typer.Exit(code=0)


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        help="Show PG version and exit.",
        callback=version_callback,
    ),
) -> None:
    """Root command callback for the PG CLI scaffold."""
    _ = version


if __name__ == "__main__":
    app()
