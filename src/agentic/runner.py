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

# Concision directive appended to every tool response (CL-04, thesis §4.2.3).
# Mirrors the "Intermediate output format" block in the agentic system prompt
# so the cap holds whether the model is responding to a tool result or to its
# own internal REVIEW step. Intermediate-only by design; the final wiki entry
# produced by the REVISE step is unconstrained.
_CONCISION_DIRECTIVE = (
    "Output format: bullet list only, no preamble or restatement of the "
    "source. Hard cap of 150 words. Output exactly `NONE` if no issues are "
    "found."
)


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
            "List every fact in the source that is NOT captured in the draft.\n\n"
            f"{_CONCISION_DIRECTIVE}"
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
            "List every claim in the draft that is NOT supported by the source.\n\n"
            f"{_CONCISION_DIRECTIVE}"
        )

    return [check_completeness, check_hallucinations]


# ── Input helpers ──────────────────────────────────────────────────────
# Build the (system_prompt, history, live_user_content) triplet that
# Strands' Agent expects from the multi-message list produced by
# ``Prompt.render(...)``. CL-05 cache-wrapping helpers are colocated
# here because their output is part of the agent inputs.

# Marker that separates the source-artifact prefix from the task
# instruction in the rendered live user message. Used by CL-05 to
# place a ``cachePoint`` between the (cacheable) source artifact and
# the (varying) instruction. Defensive: if the template changes such
# that this marker disappears, ``_split_user_message_for_cache`` falls
# back to a single text block (no cache breakpoint inside the user).
_USER_INSTRUCTION_MARKER = "Convert the source artifact above"


def _split_for_strands(
    rendered: list[dict[str, str]],
) -> tuple[str, list[dict], str]:
    """Split a rendered message list into (system, history, user_message).

    ``rendered`` follows the LiteLLM convention: a list of
    ``{"role": "...", "content": "..."}`` dicts. The live request is
    always the *last* message in the list (a user turn). Anything
    earlier with role ``user`` or ``assistant`` is exemplar history;
    system messages are concatenated.

    The ``history`` entries returned are wrapped in Strands' content-block
    shape (``[{"text": "..."}]``). Strands auto-wraps the prompt passed
    to ``agent(...)`` but does NOT auto-wrap messages passed through the
    ``Agent(messages=...)`` constructor — passing a plain string there
    causes Strands to iterate the string character-by-character looking
    for content blocks (raising ``TypeError: content_type=<S> | ...``).
    """
    if not rendered or rendered[-1]["role"] != "user":
        raise ValueError(
            "Rendered messages must end with a user turn (the live request)."
        )
    system_parts: list[str] = []
    history: list[dict] = []
    last_idx = len(rendered) - 1
    for i, msg in enumerate(rendered):
        if i == last_idx:
            user_message = msg["content"]
        elif msg["role"] == "system":
            system_parts.append(msg["content"])
        else:
            # Wrap as Strands content-block list; required by the
            # messages= constructor parameter (live user is wrapped by
            # the agent() entry point automatically).
            history.append({
                "role": msg["role"],
                "content": [{"text": msg["content"]}],
            })
    return "".join(system_parts), history, user_message


def _wrap_system_for_cache(system_text: str) -> list[dict]:
    """Wrap a system-prompt string as Strands content blocks with a
    ``cachePoint`` at the end (CL-05).

    Symmetric counterpart to :func:`_split_user_message_for_cache`.
    Strands' ``LiteLLMModel`` translates ``cachePoint`` into Anthropic's
    ``cache_control: ephemeral`` on the preceding text block, so the
    full system prompt becomes the cached prefix shared across all
    agent turns within a run.
    """
    return [
        {"text": system_text},
        {"cachePoint": {"type": "default"}},
    ]


def _split_user_message_for_cache(user_message: str) -> list[dict]:
    """Build a Strands content-block list with a ``cachePoint`` between
    the source-artifact body and the task instruction (CL-05).

    Strands' LiteLLMModel translates ``cachePoint`` into Anthropic's
    ``cache_control: {"type": "ephemeral"}`` on the preceding text
    block, so the source-artifact prefix becomes the cached portion of
    the user message and the (shorter, less stable) instruction trails.
    The agentic loop replays the same prefix on every tool turn, which
    is where the cache savings come from.
    """
    idx = user_message.find(_USER_INSTRUCTION_MARKER)
    if idx == -1:
        return [{"text": user_message}]
    return [
        {"text": user_message[:idx]},
        {"cachePoint": {"type": "default"}},
        {"text": user_message[idx:]},
    ]


# ── Agent factory ──────────────────────────────────────────────────────

def _create_agent(
    model_id: str,
    temperature: float,
    max_tokens: int,
    system_prompt,
    tools: list,
    history: list[dict] | None = None,
    top_p: float | None = None,
    top_k: int | None = None,
) -> Any:
    """Create a Strands Agent. Separated for testability.

    ``system_prompt`` may be a plain string or a list of
    :class:`SystemContentBlock` (the latter is used by CL-05 to carry a
    ``cachePoint`` at the end of the system prompt; Strands translates
    that into Anthropic's ``cache_control: ephemeral`` on the preceding
    text block).

    ``history`` (optional) seeds the agent's conversation with prior
    turns; CL-02 uses this to splice few-shot exemplar (user, assistant)
    pairs in front of the live request. Strands' default
    ``preserve_context=False`` resets to the seeded history before each
    invocation, which is the desired behavior for stable exemplars
    across runs.
    """
    from strands import Agent
    from strands.models.litellm import LiteLLMModel

    params: dict = {
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if top_p is not None:
        params["top_p"] = top_p
    if top_k is not None:
        params["top_k"] = top_k

    llm = LiteLLMModel(
        model_id=model_id,
        params=params,
    )
    agent_kwargs: dict = {
        "model": llm,
        "tools": tools,
        "system_prompt": system_prompt,
    }
    if history:
        agent_kwargs["messages"] = history
    return Agent(**agent_kwargs)


# ── Output helpers ─────────────────────────────────────────────────────
# Process the agent's response and accumulated metrics into the
# fields persisted in metadata.json.

def _extract_wiki_entry(raw_text: str) -> str:
    """Extract the final wiki entry from the agent's full response.

    The agent's output may include reasoning steps (review findings,
    revision notes) before the actual wiki entry.  We look for the last
    top-level heading (``# ...``) that signals the start of the final
    output and return everything from that point onward.
    """
    import re

    # Find all top-level headings (# Title)
    matches = list(re.finditer(r"^# .+", raw_text, re.MULTILINE))
    if matches:
        # Take everything from the last top-level heading
        return raw_text[matches[-1].start():].strip()
    # Fallback: return as-is if no heading found
    return raw_text.strip()


def _estimate_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    *,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
) -> float:
    """Estimate cost in USD using litellm cost tables.

    CL-05 cache awareness: when ``cache_read_tokens`` or
    ``cache_write_tokens`` are set, ``litellm.cost_per_token`` applies
    the per-rate cache-read and cache-write pricing separately from the
    standard input rate (cache reads are ~0.1× input rate, cache writes
    ~1.25× input rate on Anthropic). Passing zero in both keeps the
    legacy behaviour (single standard-input rate) for callers that
    don't track cache usage.
    """
    try:
        import litellm

        prompt_cost, completion_cost = litellm.cost_per_token(
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cache_creation_input_tokens=cache_write_tokens,
            cache_read_input_tokens=cache_read_tokens,
        )
        return prompt_cost + completion_cost
    except (ValueError, KeyError, TypeError, ImportError):
        return 0.0


# ── Runner ──────────────────────────────────────────────────────────────

def run_agentic(
    *artifact_filenames: str,
    prompt_id: str = "agentic_generate_wiki",
    audience: str = "development",
    temperature: float | None = None,
    max_tokens: int | None = None,
    top_p: float | None = None,
    top_k: int | None = None,
    run_tag: str | None = None,
) -> Path:
    """Run Architecture B on one or more artifacts.

    Sampling parameters are read from the prompt YAML by default.
    CLI overrides take precedence when explicitly provided.

    Args:
        artifact_filenames: Filenames in data/anonymized/.
        prompt_id: Prompt template to use.
        audience: Audience name to render the prompt for. Must match one
                  of the audiences declared in the prompt YAML's
                  ``meta.audiences`` block (CL-01, thesis §4.2.3).
                  Defaults to ``development`` (Run-1 schema analog).
        temperature: Override sampling temperature.
        max_tokens: Override max response tokens.
        top_p: Override nucleus sampling threshold.
        top_k: Override top-k sampling.
        run_tag: Optional tag appended to the run directory name.

    Returns:
        Path to the run output directory.
    """
    # ── 1. Load prompt and artifacts ────────────────────────────────
    prompt = load_prompt(prompt_id)
    bundle = load_artifacts(*artifact_filenames)
    model_id = prompt.model

    # Resolve sampling: CLI overrides > prompt YAML > hardcoded defaults
    sampling = prompt.sampling
    eff_temperature = temperature if temperature is not None else sampling.get("temperature", 0.3)
    eff_max_tokens = max_tokens if max_tokens is not None else int(sampling.get("max_tokens", 4096))
    eff_top_p = top_p if top_p is not None else sampling.get("top_p")
    eff_top_k = top_k if top_k is not None else sampling.get("top_k")
    if eff_top_k is not None:
        eff_top_k = int(eff_top_k)

    # Make the source text available to the tools
    global _SOURCE_TEXT
    _SOURCE_TEXT = bundle.artifact_text

    # Audience is forwarded to render() only when the prompt declares
    # an `audiences:` block; mirrors the pipeline runner contract so
    # both architectures resolve audience the same way.
    render_kwargs: dict[str, str] = {
        "artifact_type": bundle.artifact_type,
        "artifact_id": bundle.artifact_id,
        "artifact_text": bundle.artifact_text,
    }
    if prompt.audiences:
        render_kwargs["audience"] = audience  # render() validates membership
    elif audience != "development":
        raise ValueError(
            f"Prompt {prompt_id!r} does not declare audiences; "
            f"cannot run with audience={audience!r}."
        )

    rendered = prompt.render(**render_kwargs)

    # Strands expects (system_prompt, history, live_user_message) split:
    #   - system_prompt: concatenated system messages.
    #   - history: every (user, assistant) turn before the live request
    #              (CL-02 exemplar pairs).
    #   - user_message: the final user turn (the live request).
    system_text, history, user_message = _split_for_strands(rendered)

    # CL-05 cache breakpoints. The system prompt and the source-artifact
    # prefix of the live user are stable across all tool turns within a
    # run; marking them with `cachePoint` lets every subsequent agent
    # cycle hit Anthropic's prompt cache (~10x cheaper for repeated
    # tokens). Strands translates `cachePoint` to `cache_control:
    # ephemeral` on the preceding text block.
    system_prompt = _wrap_system_for_cache(system_text)
    user_content = _split_user_message_for_cache(user_message)

    # ── 2. Configure and run the agent ──────────────────────────────
    tools = _make_tools()
    agent = _create_agent(
        model_id=model_id,
        temperature=eff_temperature,
        max_tokens=eff_max_tokens,
        system_prompt=system_prompt,
        tools=tools,
        history=history,
        top_p=eff_top_p,
        top_k=eff_top_k,
    )

    t0 = time.perf_counter()
    call_ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    result = agent(user_content)
    latency = time.perf_counter() - t0

    # ── 3. Extract metrics ──────────────────────────────────────────
    metrics = result.metrics.get_summary() if hasattr(result, "metrics") else {}
    accumulated = metrics.get("accumulated_usage", {})

    total_tokens = accumulated.get("totalTokens", 0)
    prompt_tokens = accumulated.get("inputTokens", 0)
    completion_tokens = accumulated.get("outputTokens", 0)
    cache_read_tokens = accumulated.get("cacheReadInputTokens", 0)
    cache_write_tokens = accumulated.get("cacheWriteInputTokens", 0)

    # Strands doesn't track cost natively — estimate via litellm. CL-05
    # passes the cache token fields so cost_per_token applies cache-read
    # and cache-write rates separately from the standard input rate.
    cost_usd = _estimate_cost(
        model_id,
        prompt_tokens,
        completion_tokens,
        cache_read_tokens=cache_read_tokens,
        cache_write_tokens=cache_write_tokens,
    )

    # ── 4. Create run output directory ──────────────────────────────
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dir_name = f"agentic_{bundle.artifact_id}_{ts}"
    if run_tag:
        dir_name += f"_{run_tag}"
    run_dir = _RESULTS_DIR / dir_name
    run_dir.mkdir(parents=True, exist_ok=True)

    # ── 5. Write outputs ────────────────────────────────────────────
    wiki_text = _extract_wiki_entry(str(result))

    (run_dir / "wiki_entry.md").write_text(wiki_text, encoding="utf-8")

    metadata = {
        "architecture": "agentic",
        "prompt_id": prompt_id,
        "prompt_version": prompt.version,
        "audience": audience if prompt.audiences else None,
        "model": model_id,
        "artifact_id": bundle.artifact_id,
        "artifact_type": bundle.artifact_type,
        "artifact_files": list(artifact_filenames),
        "temperature": eff_temperature,
        "max_tokens": eff_max_tokens,
        "top_p": eff_top_p,
        "top_k": eff_top_k,
        "timestamp": call_ts,
        "num_calls": metrics.get("tool_usage", {}).get("total_tool_calls", 0) + 1,
        "total_latency_seconds": round(latency, 2),
        "total_cost_usd": round(cost_usd, 6),
        "total_tokens": total_tokens,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cache_read_input_tokens": cache_read_tokens,
        "cache_creation_input_tokens": cache_write_tokens,
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
