# prompt_generator

Phase 0 bootstrap scaffold for the Prompt Generator (PG) CLI.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pg --help
pg --version
```

## Baseline checks

```bash
ruff check .
pytest
python -m build
```

## Scope

This repository currently contains only Phase 0 scaffolding:
- package/layout wiring
- minimal Typer CLI skeleton
- deterministic smoke tests
- lint/test/build tooling baseline

No Phase 1+ business logic is implemented yet.
