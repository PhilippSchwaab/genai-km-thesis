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


def _complete_artifacts(incomplete: str) -> list[str]:
    """Return matching filenames from data/anonymized/ for shell autocompletion."""
    anon_dir = Path(__file__).resolve().parents[1] / "data" / "anonymized"
    if not anon_dir.is_dir():
        return []
    return [
        f.name for f in sorted(anon_dir.iterdir())
        if f.is_file() and f.name.lower().startswith(incomplete.lower())
    ]


@app.command()
def generate(
    arch: Architecture = typer.Option(..., help="Architecture to use."),
    artifacts: list[str] = typer.Argument(..., help="Filenames in data/anonymized/.", autocompletion=_complete_artifacts),
    temperature: float = typer.Option(0.3, help="Sampling temperature."),
    max_tokens: int = typer.Option(4096, help="Max response tokens."),
    tag: str = typer.Option("", help="Optional tag for the run directory."),
):
    """Generate wiki entries from anonymized artifacts."""
    if arch == Architecture.pipeline:
        from src.pipeline.runner import run_pipeline

        run_dir = run_pipeline(
            *artifacts,
            temperature=temperature,
            max_tokens=max_tokens,
            run_tag=tag or None,
        )
        typer.echo(f"Pipeline complete → {run_dir}")
    elif arch == Architecture.agentic:
        from src.agentic.runner import run_agentic

        run_dir = run_agentic(
            *artifacts,
            temperature=temperature,
            max_tokens=max_tokens,
            run_tag=tag or None,
        )
        typer.echo(f"Agentic complete → {run_dir}")


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
