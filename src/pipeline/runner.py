"""
Architecture A — Structured Pipeline runner.

Single-pass generation: load artifact → render prompt → call LLM → save output.
Each run produces a timestamped directory under eval/results/ containing the
wiki entry, raw LLM response, and run metadata (latency, cost, tokens).

Usage:
    from src.pipeline.runner import run_pipeline

    result_dir = run_pipeline("CS-06_Testing_Strategy_compiled.md")
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from src.common.llm_client import CallLog, complete
from src.common.prompts import load_artifacts, load_prompt

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_RESULTS_DIR = _PROJECT_ROOT / "eval" / "results"


def run_pipeline(
    *artifact_filenames: str,
    prompt_id: str = "pipeline_generate_wiki",
    temperature: float = 0.3,
    max_tokens: int = 4096,
    run_tag: str | None = None,
) -> Path:
    """Run Architecture A on one or more artifacts.

    Args:
        artifact_filenames: Filenames in data/anonymized/.
        prompt_id: Prompt template to use.
        temperature: Sampling temperature.
        max_tokens: Max response tokens.
        run_tag: Optional tag appended to the run directory name.

    Returns:
        Path to the run output directory.
    """
    # ── 1. Load prompt and artifacts ─────────────────────────────────
    prompt = load_prompt(prompt_id)
    bundle = load_artifacts(*artifact_filenames)
    model = prompt.model

    messages = prompt.render(
        artifact_type=bundle.artifact_type,
        artifact_id=bundle.artifact_id,
        artifact_text=bundle.artifact_text,
    )

    # ── 2. Call LLM ──────────────────────────────────────────────────
    log = CallLog()
    result = complete(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        call_log=log,
    )

    # ── 3. Create run output directory ───────────────────────────────
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dir_name = f"pipeline_{bundle.artifact_id}_{ts}"
    if run_tag:
        dir_name += f"_{run_tag}"
    run_dir = _RESULTS_DIR / dir_name
    run_dir.mkdir(parents=True, exist_ok=True)

    # ── 4. Write outputs ─────────────────────────────────────────────

    # Wiki entry (the primary output for evaluation)
    (run_dir / "wiki_entry.md").write_text(result.text, encoding="utf-8")

    # Run metadata for MCDA scoring
    metadata = {
        "architecture": "pipeline",
        "prompt_id": prompt_id,
        "prompt_version": prompt.version,
        "model": result.model,
        "artifact_id": bundle.artifact_id,
        "artifact_type": bundle.artifact_type,
        "artifact_files": list(artifact_filenames),
        "temperature": temperature,
        "max_tokens": max_tokens,
        "timestamp": result.timestamp,
        **log.summary(),
    }
    (run_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

    # Raw messages sent to the LLM (for reproducibility / debugging)
    (run_dir / "messages.json").write_text(
        json.dumps(messages, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return run_dir
