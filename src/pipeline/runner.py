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
    temperature: float | None = None,
    max_tokens: int | None = None,
    top_p: float | None = None,
    top_k: int | None = None,
    run_tag: str | None = None,
) -> Path:
    """Run Architecture A on one or more artifacts.

    Sampling parameters are read from the prompt YAML by default.
    CLI overrides (temperature, max_tokens, top_p, top_k) take precedence
    when explicitly provided.

    Args:
        artifact_filenames: Filenames in data/anonymized/.
        prompt_id: Prompt template to use.
        temperature: Override sampling temperature.
        max_tokens: Override max response tokens.
        top_p: Override nucleus sampling threshold.
        top_k: Override top-k sampling.
        run_tag: Optional tag appended to the run directory name.

    Returns:
        Path to the run output directory.
    """
    # ── 1. Load prompt and artifacts ─────────────────────────────────
    prompt = load_prompt(prompt_id)
    bundle = load_artifacts(*artifact_filenames)
    model = prompt.model

    # Resolve sampling: CLI overrides > prompt YAML > hardcoded defaults
    sampling = prompt.sampling
    eff_temperature = temperature if temperature is not None else sampling.get("temperature", 0.3)
    eff_max_tokens = max_tokens if max_tokens is not None else int(sampling.get("max_tokens", 4096))
    eff_top_p = top_p if top_p is not None else sampling.get("top_p")
    eff_top_k = top_k if top_k is not None else sampling.get("top_k")
    if eff_top_k is not None:
        eff_top_k = int(eff_top_k)

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
        temperature=eff_temperature,
        max_tokens=eff_max_tokens,
        top_p=eff_top_p,
        top_k=eff_top_k,
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
        "temperature": eff_temperature,
        "max_tokens": eff_max_tokens,
        "top_p": eff_top_p,
        "top_k": eff_top_k,
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
