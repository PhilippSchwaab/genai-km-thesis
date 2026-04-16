"""
Architecture B — Agentic Workflow runner (Strands Agents SDK).

Multistep generation with self-review: the agent extracts facts, drafts a
wiki entry, checks for completeness / hallucinations against the source, and
revises autonomously.  Each run produces a timestamped directory under
eval/results/ with the same structure as Architecture A for fair comparison.

Usage:
    from src.agentic.runner import run_agentic

    result_dir = run_agentic("CS-06_Testing_Strategy_compiled.md")
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from src.common.prompts import load_artifacts, load_prompt

load_dotenv()

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_RESULTS_DIR = _PROJECT_ROOT / "eval" / "results"

# ── Strands tool definitions ────────────────────────────────────────────
# These are lightweight Python functions the agent can call during its
# reasoning loop.  They receive and return plain strings so the agent
# can inspect intermediate artifacts.

_SOURCE_TEXT: str = ""  # set per-run so tools can access the source


def _make_tools() -> list:
    """Build the Strands @tool functions.

    We import inside the function so the module can be imported even when
    strands is not installed (e.g. during pipeline-only usage).
    """
    from strands import tool

    @tool
    def check_completeness(draft: str) -> str:
        """Compare the draft wiki entry against the original source artifact.

        Return a list of facts from the source that are missing in the draft.
        """
        return (
            "SOURCE ARTIFACT (for comparison):\n"
            "---\n"
            f"{_SOURCE_TEXT}\n"
            "---\n\n"
            "DRAFT TO CHECK:\n"
            "---\n"
            f"{draft}\n"
            "---\n\n"
            "List every fact in the source that is NOT captured in the draft."
        )

    @tool
    def check_hallucinations(draft: str) -> str:
        """Check the draft for claims that are not grounded in the source.

        Return a list of unsupported statements.
        """
        return (
            "SOURCE ARTIFACT (ground truth):\n"
            "---\n"
            f"{_SOURCE_TEXT}\n"
            "---\n\n"
            "DRAFT TO CHECK:\n"
            "---\n"
            f"{draft}\n"
            "---\n\n"
            "List every claim in the draft that is NOT supported by the source."
        )

    return [check_completeness, check_hallucinations]


def _create_agent(
    model_id: str,
    temperature: float,
    max_tokens: int,
    system_prompt: str,
    tools: list,
) -> Any:
    """Create a Strands Agent. Separated for testability."""
    from strands import Agent
    from strands.models.litellm import LiteLLMModel

    llm = LiteLLMModel(
        model_id=model_id,
        params={
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
    )
    return Agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
    )


# ── Runner ──────────────────────────────────────────────────────────────

def run_agentic(
    *artifact_filenames: str,
    prompt_id: str = "agentic_generate_wiki",
    temperature: float = 0.3,
    max_tokens: int = 4096,
    run_tag: str | None = None,
) -> Path:
    """Run Architecture B on one or more artifacts.

    Args:
        artifact_filenames: Filenames in data/anonymized/.
        prompt_id: Prompt template to use.
        temperature: Sampling temperature.
        max_tokens: Max response tokens.
        run_tag: Optional tag appended to the run directory name.

    Returns:
        Path to the run output directory.
    """
    # ── 1. Load prompt and artifacts ────────────────────────────────
    prompt = load_prompt(prompt_id)
    bundle = load_artifacts(*artifact_filenames)
    model_id = prompt.model

    # Make the source text available to the tools
    global _SOURCE_TEXT
    _SOURCE_TEXT = bundle.artifact_text

    # Build the user message from the prompt template
    rendered = prompt.render(
        artifact_type=bundle.artifact_type,
        artifact_id=bundle.artifact_id,
        artifact_text=bundle.artifact_text,
    )

    # Extract system prompt and user message from the rendered messages
    system_prompt = ""
    user_message = ""
    for msg in rendered:
        if msg["role"] == "system":
            system_prompt += msg["content"]
        elif msg["role"] == "user":
            user_message += msg["content"]

    # ── 2. Configure and run the agent ──────────────────────────────
    tools = _make_tools()
    agent = _create_agent(
        model_id=model_id,
        temperature=temperature,
        max_tokens=max_tokens,
        system_prompt=system_prompt,
        tools=tools,
    )

    t0 = time.perf_counter()
    call_ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    result = agent(user_message)
    latency = time.perf_counter() - t0

    # ── 3. Extract metrics ──────────────────────────────────────────
    metrics = result.metrics.get_summary() if hasattr(result, "metrics") else {}
    accumulated = metrics.get("accumulated_usage", {})

    total_tokens = accumulated.get("totalTokens", 0)
    prompt_tokens = accumulated.get("inputTokens", 0)
    completion_tokens = accumulated.get("outputTokens", 0)

    # Strands doesn't track cost natively — estimate via litellm
    cost_usd = _estimate_cost(model_id, prompt_tokens, completion_tokens)

    # ── 4. Create run output directory ──────────────────────────────
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dir_name = f"agentic_{bundle.artifact_id}_{ts}"
    if run_tag:
        dir_name += f"_{run_tag}"
    run_dir = _RESULTS_DIR / dir_name
    run_dir.mkdir(parents=True, exist_ok=True)

    # ── 5. Write outputs ────────────────────────────────────────────
    wiki_text = str(result)

    (run_dir / "wiki_entry.md").write_text(wiki_text, encoding="utf-8")

    metadata = {
        "architecture": "agentic",
        "prompt_id": prompt_id,
        "prompt_version": prompt.version,
        "model": model_id,
        "artifact_id": bundle.artifact_id,
        "artifact_type": bundle.artifact_type,
        "artifact_files": list(artifact_filenames),
        "temperature": temperature,
        "max_tokens": max_tokens,
        "timestamp": call_ts,
        "num_calls": metrics.get("tool_usage", {}).get("total_tool_calls", 0) + 1,
        "total_latency_seconds": round(latency, 2),
        "total_cost_usd": round(cost_usd, 6),
        "total_tokens": total_tokens,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "strands_metrics": metrics,
    }
    (run_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

    # Raw messages for reproducibility
    (run_dir / "messages.json").write_text(
        json.dumps(rendered, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return run_dir


def _estimate_cost(
    model: str, prompt_tokens: int, completion_tokens: int
) -> float:
    """Estimate cost in USD using litellm cost tables."""
    try:
        import litellm

        return litellm.completion_cost(
            model=model,
            prompt=str(prompt_tokens),
            completion=str(completion_tokens),
        )
    except (ValueError, KeyError, TypeError, ImportError):
        return 0.0
