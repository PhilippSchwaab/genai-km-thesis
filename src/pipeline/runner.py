"""
Architecture A — Structured Pipeline runner.

Single-pass generation: load artifact → render prompt → call LLM → save output.
Each run produces a timestamped directory under eval/results/ containing the
wiki entry, raw LLM response, run metadata (latency, cost, tokens), and the
canonical :class:`GenerationResult` (``result.json``).

The runner is structured around the canonical contract:

    generate(source: SourceArtifact, ...) -> GenerationResult

:func:`run_pipeline` is the file-based orchestrator that loads anonymized
artifacts from disk, wraps them as a :class:`SourceArtifact`, calls
:func:`generate`, and persists the legacy thesis-eval files plus the new
``result.json``. The legacy ``metadata.json`` shape is preserved key-for-key
so existing eval scripts continue to work unchanged.

Usage:
    from src.pipeline.runner import run_pipeline

    result_dir = run_pipeline("CS-06_Testing_Strategy_compiled.md")
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from src.common.contracts import (
    Generation,
    GenerationResult,
    SourceArtifact,
    file_source_uri,
    new_run_id,
    utc_now_iso,
)
from src.common.llm_client import complete
from src.common.prompts import Prompt, load_artifacts, load_prompt

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_RESULTS_DIR = _PROJECT_ROOT / "eval" / "results"


def generate(
    source: SourceArtifact,
    *,
    prompt: Prompt | None = None,
    prompt_id: str = "pipeline_generate_wiki",
    temperature: float | None = None,
    max_tokens: int | None = None,
    top_p: float | None = None,
    top_k: int | None = None,
    artifact_id: str | None = None,
    artifact_type: str | None = None,
) -> tuple[GenerationResult, list[dict[str, str]]]:
    """Core Architecture A generation — :class:`SourceArtifact` in,
    :class:`GenerationResult` out.

    Returns a tuple of ``(GenerationResult, rendered_messages)``. The
    rendered messages are returned alongside so the orchestrator can
    persist them as ``messages.json`` for reproducibility/debugging —
    they are deliberately *not* part of the canonical contract (full
    LLM traces are sampled-only in production per the volume research
    in ``docs/production_fork_plan.md``).

    Pass a preloaded ``prompt`` to avoid a redundant YAML load when
    the caller already has one; otherwise ``prompt_id`` is loaded here.

    ``artifact_id`` / ``artifact_type`` are optional hints fed into the
    prompt template's ``{artifact_id}`` / ``{artifact_type}`` slots.
    When omitted, the source URI's last path segment is used as a
    reasonable default.
    """
    # ── 1. Load prompt ───────────────────────────────────────────────
    if prompt is None:
        prompt = load_prompt(prompt_id)
    model = prompt.model

    # Resolve sampling: caller overrides > prompt YAML > hardcoded defaults
    sampling = prompt.sampling
    eff_temperature = temperature if temperature is not None else sampling.get("temperature", 0.3)
    eff_max_tokens = max_tokens if max_tokens is not None else int(sampling.get("max_tokens", 4096))
    eff_top_p = top_p if top_p is not None else sampling.get("top_p")
    eff_top_k = top_k if top_k is not None else sampling.get("top_k")
    if eff_top_k is not None:
        eff_top_k = int(eff_top_k)

    # Default artifact_id from the URI's last path segment if not provided
    if artifact_id is None:
        artifact_id = source.source_uri.rstrip("/").rsplit("/", 1)[-1]
    if artifact_type is None:
        artifact_type = "personal_notes"  # safe fallback matching prompts._guess_artifact_type

    # Audience is forwarded to render() only when the prompt declares
    # an `audiences:` block; this keeps backward compatibility with any
    # generation prompt that pre-dates CL-01 while still erroring loudly
    # if a user requests an audience the prompt does not define.
    render_kwargs: dict[str, str] = {
        "artifact_type": artifact_type,
        "artifact_id": artifact_id,
        "artifact_text": source.content,
    }
    if prompt.audiences:
        render_kwargs["audience"] = source.audience  # render() validates membership
    elif source.audience != "development":
        raise ValueError(
            f"Prompt {prompt.id!r} does not declare audiences; "
            f"cannot run with audience={source.audience!r}."
        )

    messages = prompt.render(**render_kwargs)

    # ── 2. Call LLM ──────────────────────────────────────────────────
    # Latency is taken from the LLMResult (measured *inside* complete()
    # via time.perf_counter) rather than re-measured here, so that
    # external orchestration overhead (prompt loading, file IO, etc.)
    # doesn't pollute the lineage metric and so the value matches what
    # log.summary() reported in pre-contract metadata.json.
    print(f"Generating wiki entry for {artifact_id}...", flush=True)
    started_at = utc_now_iso()
    result = complete(
        model=model,
        messages=messages,
        temperature=eff_temperature,
        max_tokens=eff_max_tokens,
        top_p=eff_top_p,
        top_k=eff_top_k,
    )
    ended_at = utc_now_iso()
    latency = result.latency_seconds

    print(f"Done. ({result.latency_seconds}s, {result.total_tokens} tokens)", flush=True)

    # ── 3. Build the canonical GenerationResult ──────────────────────
    generation = Generation(
        architecture="pipeline",
        prompt_id=prompt.id,
        prompt_version=prompt.version,
        model=result.model,
        sampling={
            "temperature": eff_temperature,
            "max_tokens": eff_max_tokens,
            "top_p": eff_top_p,
            "top_k": eff_top_k,
        },
        tokens={
            "input": result.prompt_tokens,
            "output": result.completion_tokens,
            "cache_read": 0,        # pipeline path doesn't use prompt cache
            "cache_creation": 0,
        },
        cost_usd=result.cost_usd,
        latency_seconds=latency,
        started_at=started_at,
        ended_at=ended_at,
        reviewer_iterations=0,
        reviewer_passed=None,
    )
    gen_result = GenerationResult(
        run_id=new_run_id(),
        source_uri=source.source_uri,
        source_content_hash=source.source_content_hash,
        wiki_entry_markdown=result.text,
        generation=generation,
    )
    return gen_result, messages


def run_pipeline(
    *artifact_filenames: str,
    prompt_id: str = "pipeline_generate_wiki",
    audience: str = "development",
    temperature: float | None = None,
    max_tokens: int | None = None,
    top_p: float | None = None,
    top_k: int | None = None,
    run_tag: str | None = None,
) -> Path:
    """File-based orchestrator for Architecture A.

    Loads anonymized artifacts from ``data/anonymized/``, wraps them as
    a :class:`SourceArtifact`, calls :func:`generate`, and writes the
    full per-run output bundle to ``eval/results/<run_dir>/``:

    - ``wiki_entry.md`` — the generated entry (primary evaluation output).
    - ``metadata.json`` — legacy thesis-eval shape, preserved key-for-key
      from earlier versions so existing eval scripts continue to work.
    - ``result.json`` — the canonical :class:`GenerationResult` contract.
    - ``messages.json`` — raw messages sent to the LLM (reproducibility).

    Sampling parameters default to the prompt YAML; CLI overrides take
    precedence when explicitly provided.

    Args:
        artifact_filenames: Filenames in data/anonymized/.
        prompt_id: Prompt template to use.
        audience: Audience name; must match the prompt YAML's ``meta.audiences``
                  (CL-01, thesis §4.2.3).
        temperature: Override sampling temperature.
        max_tokens: Override max response tokens.
        top_p: Override nucleus sampling threshold.
        top_k: Override top-k sampling.
        run_tag: Optional tag appended to the run directory name.

    Returns:
        Path to the run output directory.
    """
    # ── Load prompt + artifacts, wrap as SourceArtifact ──────────────
    prompt = load_prompt(prompt_id)
    bundle = load_artifacts(*artifact_filenames)
    source = SourceArtifact.from_text(
        content=bundle.artifact_text,
        source_uri=file_source_uri(list(artifact_filenames)),
        audience=audience,
    )

    # ── Run the canonical generator ──────────────────────────────────
    gen_result, messages = generate(
        source,
        prompt=prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        top_k=top_k,
        artifact_id=bundle.artifact_id,
        artifact_type=bundle.artifact_type,
    )
    gen = gen_result.generation

    # ── Create run output directory ──────────────────────────────────
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dir_name = f"pipeline_{bundle.artifact_id}_{ts}"
    if run_tag:
        dir_name += f"_{run_tag}"
    run_dir = _RESULTS_DIR / dir_name
    run_dir.mkdir(parents=True, exist_ok=True)

    # ── Write outputs ────────────────────────────────────────────────
    # Wiki entry (the primary output for evaluation)
    (run_dir / "wiki_entry.md").write_text(
        gen_result.wiki_entry_markdown, encoding="utf-8"
    )

    # Canonical contract (new — supplemental to metadata.json)
    (run_dir / "result.json").write_text(
        json.dumps(gen_result.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Legacy thesis-eval metadata shape — kept identical to pre-contract
    # output so MCDA, KIP-scorer, and review_stats keep working without
    # change. Aggregates derived from `gen` so they stay in sync with
    # the contract.
    total_tokens = gen.tokens["input"] + gen.tokens["output"]
    metadata = {
        "architecture": "pipeline",
        "prompt_id": prompt_id,
        "prompt_version": gen.prompt_version,
        "audience": audience if prompt.audiences else None,
        "model": gen.model,
        "artifact_id": bundle.artifact_id,
        "artifact_type": bundle.artifact_type,
        "artifact_files": list(artifact_filenames),
        "temperature": gen.sampling["temperature"],
        "max_tokens": gen.sampling["max_tokens"],
        "top_p": gen.sampling["top_p"],
        "top_k": gen.sampling["top_k"],
        "timestamp": gen.started_at,
        "num_calls": 1,
        "total_latency_seconds": gen.latency_seconds,
        "total_cost_usd": round(gen.cost_usd, 6),
        "total_tokens": total_tokens,
    }
    (run_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

    # Raw messages sent to the LLM (for reproducibility / debugging)
    (run_dir / "messages.json").write_text(
        json.dumps(messages, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return run_dir
