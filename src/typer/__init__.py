"""Minimal local Typer-compatible scaffold used for offline Phase 0 bootstrapping."""

from __future__ import annotations

import inspect
import sys
from dataclasses import dataclass
from typing import Any, Callable


class Exit(Exception):
    """Signal a CLI exit with a specific code."""

    def __init__(self, code: int = 0) -> None:
        self.code = code
        super().__init__(code)


@dataclass
class OptionInfo:
    """Container for option metadata."""

    default: Any
    flags: tuple[str, ...]
    help: str | None = None
    callback: Callable[[Any], None] | None = None


def Option(
    default: Any,
    *flags: str,
    help: str | None = None,
    callback: Callable[[Any], None] | None = None,
) -> OptionInfo:
    """Create option metadata for callback parameters."""
    return OptionInfo(default=default, flags=flags, help=help, callback=callback)


def echo(message: str) -> None:
    """Print a message to stdout."""
    print(message)


class Typer:
    """Tiny Typer-like application for root callback usage."""

    def __init__(self, *, help: str = "") -> None:
        self.help = help
        self._callback: Callable[..., None] | None = None

    def callback(self) -> Callable[[Callable[..., None]], Callable[..., None]]:
        """Register a root callback."""

        def decorator(func: Callable[..., None]) -> Callable[..., None]:
            self._callback = func
            return func

        return decorator

    def _print_help(self) -> None:
        print(f"Usage: pg [OPTIONS]\n\n{self.help}\n")

    def __call__(self) -> None:
        args = sys.argv[1:]
        if "--help" in args or "-h" in args:
            self._print_help()
            raise SystemExit(0)

        if self._callback is None:
            raise SystemExit(0)

        try:
            kwargs: dict[str, Any] = {}
            signature = inspect.signature(self._callback)
            for name, param in signature.parameters.items():
                default = param.default
                if isinstance(default, OptionInfo):
                    value = default.default
                    if any(flag in args for flag in default.flags):
                        value = True
                    kwargs[name] = value
                    if default.callback is not None:
                        default.callback(value)
                else:
                    kwargs[name] = default

            self._callback(**kwargs)
        except Exit as exc:
            raise SystemExit(exc.code) from exc
