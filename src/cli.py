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


def _complete_run_dirs(incomplete: str) -> list[str]:
    """Return matching run directory names for shell autocompletion."""
    results_dir = Path(__file__).resolve().parents[1] / "eval" / "results"
    if not results_dir.is_dir():
        return []
    return [
        d.name for d in sorted(results_dir.iterdir())
        if d.is_dir() and d.name.lower().startswith(incomplete.lower())
    ]


@app.command()
def evaluate(
    run_dirs: list[str] = typer.Argument(..., help="Run directory names in eval/results/.", autocompletion=_complete_run_dirs),
    judge_model: Optional[str] = typer.Option(None, help="Override the judge model from the eval prompt."),
):
    """Score generated wiki entries against the KIP ground truth.

    Runs the LLM-as-judge over each provided run directory, writes
    ``kip_eval.json`` alongside the run outputs, and prints the
    per-run KIP-recall summary. Composite-score aggregation across
    runs and architectures is handled separately by ``km mcda``.
    """
    from eval.harness.run_eval import evaluate_run

    results_base = Path(__file__).resolve().parents[1] / "eval" / "results"
    resolved = [results_base / name for name in run_dirs]

    for rd in resolved:
        if not rd.is_dir():
            typer.echo(f"Error: run directory not found: {rd}", err=True)
            raise typer.Exit(code=1)

    for rd in resolved:
        typer.echo(f"Evaluating {rd.name}...")
        report = evaluate_run(rd, judge_model=judge_model)
        counts = report.counts
        typer.echo(
            f"  KIP Recall: {report.recall:.1%} "
            f"({counts['YES']} YES, {counts['PARTIAL']} PARTIAL, {counts['NO']} NO "
            f"out of {report.total_kips} KIPs)"
        )
        typer.echo(f"  Eval cost: ${report.call_log.total_cost_usd:.4f}")
        typer.echo(f"  Results → {rd / 'kip_eval.json'}")


@app.command()
def mcda(
    label: str = typer.Option("Run 1", help="Label used in the report title and output filename stem."),
    frontend: Optional[Path] = typer.Option(None, help="Path to the genai-km-frontend repo (default: ~/PycharmProjects/genai-km-frontend)."),
    config: Optional[Path] = typer.Option(None, help="Override the path to mcda_config.yaml."),
):
    """Compute the aspiration-SAW composite score across architectures.

    Walks ``eval/results/``, joins per-architecture metrics with the
    review-UI aggregates from the frontend, applies the gates from
    thesis §3.3.2, and writes ``eval/<label>_mcda_summary.md`` plus
    ``eval/<label>_mcda.json`` (label normalised to lowercase, no
    spaces). Designed to be re-runnable each time review or generation
    data is updated.
    """
    from eval.run_mcda import main as run_mcda_main

    argv: list[str] = ["--label", label]
    if frontend is not None:
        argv += ["--frontend", str(frontend)]
    if config is not None:
        argv += ["--config", str(config)]
    raise typer.Exit(code=run_mcda_main(argv))


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
