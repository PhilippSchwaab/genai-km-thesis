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
    prompt: Optional[str] = typer.Option(None, help="Prompt template id (overrides default for the architecture)."),
    temperature: Optional[float] = typer.Option(None, help="Override sampling temperature."),
    max_tokens: Optional[int] = typer.Option(None, help="Override max response tokens."),
    top_p: Optional[float] = typer.Option(None, help="Override nucleus sampling (top_p)."),
    top_k: Optional[int] = typer.Option(None, help="Override top-k sampling."),
    tag: str = typer.Option("", help="Optional tag for the run directory."),
):
    """Generate wiki entries from anonymized artifacts.

    Sampling parameters (temperature, max_tokens, top_p, top_k) default to
    the values in the prompt YAML. CLI flags override them when provided.
    """
    # Build kwargs — only include sampling overrides that were explicitly set
    sampling_overrides: dict = {}
    if temperature is not None:
        sampling_overrides["temperature"] = temperature
    if max_tokens is not None:
        sampling_overrides["max_tokens"] = max_tokens
    if top_p is not None:
        sampling_overrides["top_p"] = top_p
    if top_k is not None:
        sampling_overrides["top_k"] = top_k

    if arch == Architecture.pipeline:
        from src.pipeline.runner import run_pipeline

        run_dir = run_pipeline(
            *artifacts,
            prompt_id=prompt or "pipeline_generate_wiki",
            run_tag=tag or None,
            **sampling_overrides,
        )
        typer.echo(f"Pipeline complete → {run_dir}")
    elif arch == Architecture.agentic:
        from src.agentic.runner import run_agentic

        run_dir = run_agentic(
            *artifacts,
            prompt_id=prompt or "agentic_generate_wiki",
            run_tag=tag or None,
            **sampling_overrides,
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
