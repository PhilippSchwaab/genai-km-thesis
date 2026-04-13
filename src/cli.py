"""Unified CLI for the GenAI KM thesis project."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(name="km", help="GenAI Knowledge Management — Thesis CLI")


@app.command()
def anonymize():
    """Redact PII from data/raw/ → data/anonymized/."""
    from src.common.anonymize_files import anonymize_all

    anonymize_all()


class Architecture(str, Enum):
    pipeline = "pipeline"
    agentic = "agentic"


@app.command()
def generate(
    arch: Architecture = typer.Option(..., help="Architecture to use."),
    artifacts: list[str] = typer.Argument(..., help="Filenames in data/anonymized/."),
):
    """Generate wiki entries from anonymized artifacts."""
    typer.echo(f"generate: arch={arch.value}, artifacts={artifacts}")
    typer.echo("Not yet implemented.")
    raise typer.Exit(code=1)


@app.command()
def evaluate(
    run_dir: Path = typer.Option(..., help="Directory with generation outputs."),
):
    """Run the evaluation suite on generated outputs."""
    typer.echo(f"evaluate: run_dir={run_dir}")
    typer.echo("Not yet implemented.")
    raise typer.Exit(code=1)


@app.command()
def validate(
    files: Optional[list[str]] = typer.Argument(None, help="KIP JSON files to validate (default: all)."),
):
    """Validate KIP JSON files against the schema."""
    import sys

    from src.common.validate_kips import main as val_main

    # Forward file arguments to the existing CLI
    if files:
        sys.argv = ["validate"] + files
    else:
        sys.argv = ["validate"]
    val_main()


@app.command()
def prompts():
    """List available prompt templates."""
    from src.common.prompts import list_prompts

    for p in list_prompts():
        typer.echo(f"  {p['id']}  v{p['version']}  ({p['architecture']}, {p['model']})")


if __name__ == "__main__":
    app()
