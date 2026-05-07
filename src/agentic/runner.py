"""
Architecture B — Agentic Workflow runner (Strands Agents SDK).

CL-06 (thesis §4.2.3) restructures the Run-1 single-agent + self-tools
design into a Writer/Reviewer loop. The Writer drafts the wiki entry;
the Reviewer re-reads the source against the draft and returns either
the literal sentinel ``NONE`` (the entry is acceptable) or a bullet
list of issues to fix. The runner cycles Writer → Reviewer → Writer
until the Reviewer passes the draft or the max-iteration cap is hit.

Each run produces a timestamped directory under ``eval/results/`` with
the same shape as Architecture A so downstream evaluation can consume
both architectures identically.

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

# CL-06: cap the Writer/Reviewer cycle so a stubborn Reviewer (or a
# Writer that fails to converge on the Reviewer's feedback) cannot run
# unbounded. Three iterations keeps cost and latency bounded while
# leaving enough headroom for the typical case to converge in 1–2
# cycles.
_MAX_REVIEWER_ITERATIONS = 3

# Reviewer's "no issues" sentinel. Matched case-insensitively after
# stripping markdown / whitespace so a model that emits "**NONE**" or
# "NONE." still terminates the loop. The format is reinforced by the
# Reviewer system prompt (CL-04 concision directive) and tested in
# tests/test_agentic_runner.py.
_REVIEWER_PASS_SENTINEL = "NONE"


def _safe_invoke_agent(agent: Any, prompt: Any) -> tuple[Any, str | None]:
    """Invoke a Strands agent and tolerate ``MaxTokensReachedException``.

    Some models (notably reasoning-trace models like Gemma on Ollama)
    can consume the entire ``max_tokens`` budget in their internal
    chain-of-thought before emitting any user-visible text, in which
    case Strands raises ``MaxTokensReachedException`` rather than
    returning the partial result. The runner treats this as a
    non-fatal "agent ran out of room": returns ``(None, error_msg)``
    so the Writer/Reviewer loop can record the failure and continue
    (the Reviewer's missed turn becomes a synthetic non-pass; the
    Writer's missed revision aborts the loop with the latest verified
    draft as the output).

    This is the only Strands exception we catch — anything else is a
    real error that should propagate.
    """
    try:
        from strands.types.exceptions import MaxTokensReachedException
    except ImportError:  # older / vendored Strands; fall back to broad except
        MaxTokensReachedException = Exception  # type: ignore[assignment]
    try:
        return agent(prompt), None
    except MaxTokensReachedException as e:
        return None, str(e)


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

# Reviewer counterpart to ``_USER_INSTRUCTION_MARKER``: the Reviewer's
# user template ends "Draft to review:\n---\n{draft}\n---\n\nReview
# the draft against the source." Cache breakpoint sits between the
# source artifact and the draft block (everything before the draft is
# stable across cycles).
_REVIEWER_DRAFT_MARKER = "Draft to review:"


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


def _split_user_message_for_cache(
    user_message: str,
    *,
    marker: str = _USER_INSTRUCTION_MARKER,
) -> list[dict]:
    """Build a Strands content-block list with a ``cachePoint`` between
    the source-artifact prefix and the variable instruction / draft
    suffix (CL-05).

    Strands' LiteLLMModel translates ``cachePoint`` into Anthropic's
    ``cache_control: {"type": "ephemeral"}`` on the preceding text
    block, so the source-artifact prefix becomes the cached portion of
    the user message and the (shorter, less stable) instruction trails.

    The Writer replays the same prefix on every revision turn; the
    Reviewer replays the same prefix on every review turn. Both share
    the same source artifact, so both benefit from a cache breakpoint
    placed at the same boundary (CL-06 extension of CL-05). The
    ``marker`` parameter selects which suffix marker to split on:

    - ``_USER_INSTRUCTION_MARKER`` — Writer's user template (default).
    - ``_REVIEWER_DRAFT_MARKER`` — Reviewer's user template.
    """
    idx = user_message.find(marker)
    if idx == -1:
        return [{"text": user_message}]
    return [
        {"text": user_message[:idx]},
        {"cachePoint": {"type": "default"}},
        {"text": user_message[idx:]},
    ]


# ── Agent factory ──────────────────────────────────────────────────────

def _make_cache_aware_litellm_model_class():
    """Build a :class:`LiteLLMModel` subclass that preserves
    ``cachePoint`` semantics on regular (user/assistant) messages.

    Strands' upstream :class:`LiteLLMModel` translates ``cachePoint``
    to ``cache_control: ephemeral`` for **system** prompts (in
    ``_format_system_messages``) but not for regular messages — its
    inherited ``_format_regular_messages`` calls
    ``format_request_message_content`` on each content block, which
    raises ``TypeError: content_type=<cachePoint> | unsupported type``
    on the first cachePoint marker.

    This subclass strips ``cachePoint`` blocks before delegating to the
    parent and re-applies ``cache_control: ephemeral`` to the
    immediately-preceding text block of each formatted message,
    mirroring the upstream system-prompt behaviour. Constructed lazily
    so importing this module without ``strands`` installed still works.
    """
    from strands.models.litellm import LiteLLMModel

    class _CacheAwareLiteLLMModel(LiteLLMModel):
        @classmethod
        def _format_regular_messages(cls, messages):
            # Pre-pass: strip cachePoint blocks; remember (out_msg_idx,
            # content_idx) tuples where cache_control should land in
            # the formatted output.
            cleaned: list[dict] = []
            cache_apply: list[tuple[int, int]] = []
            out_idx = 0
            for msg in messages:
                blocks = list(msg.get("content", []))
                kept: list = []
                for block in blocks:
                    if isinstance(block, dict) and "cachePoint" in block:
                        # Apply cache_control to the most recent kept
                        # block in the same message; defensive if
                        # cachePoint is the first block (skip).
                        if kept:
                            cache_apply.append((out_idx, len(kept) - 1))
                    else:
                        kept.append(block)
                if kept:
                    cleaned.append({**msg, "content": kept})
                    out_idx += 1

            formatted = super()._format_regular_messages(cleaned)

            # Post-pass: stamp cache_control on the formatted blocks.
            for msg_idx, content_idx in cache_apply:
                if not (0 <= msg_idx < len(formatted)):
                    continue
                content = formatted[msg_idx].get("content")
                if not isinstance(content, list):
                    continue
                if not (0 <= content_idx < len(content)):
                    continue
                content[content_idx]["cache_control"] = {"type": "ephemeral"}

            return formatted

    return _CacheAwareLiteLLMModel


def _create_agent(
    model_id: str,
    temperature: float,
    max_tokens: int,
    system_prompt,
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
    ``SlidingWindowConversationManager`` preserves conversation across
    successive invocations of the same agent (until the window fills),
    which is what CL-06 relies on: the Writer's later revisions and the
    Reviewer's later reviews see the prior turns of the same agent
    without the runner having to replay them.

    The agent has no tools; CL-06 replaced the Run-1 self-referential
    tools with a separate Reviewer agent (see :func:`_run_writer_reviewer_loop`).

    Uses :func:`_make_cache_aware_litellm_model_class` so ``cachePoint``
    markers in the live user content are also translated to
    ``cache_control`` (Strands' upstream only translates them for
    system prompts).
    """
    from strands import Agent

    params: dict = {
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if top_p is not None:
        params["top_p"] = top_p
    if top_k is not None:
        params["top_k"] = top_k

    model_cls = _make_cache_aware_litellm_model_class()
    llm = model_cls(
        model_id=model_id,
        params=params,
    )
    agent_kwargs: dict = {
        "model": llm,
        "system_prompt": system_prompt,
    }
    if history:
        agent_kwargs["messages"] = history
    return Agent(**agent_kwargs)


# ── Writer / Reviewer loop ─────────────────────────────────────────────

def _reviewer_passes(reviewer_response: str) -> bool:
    """Return True when the Reviewer signals the draft is acceptable.

    The Reviewer system prompt instructs the model to return the
    literal sentinel ``NONE`` (CL-06 / CL-04). This helper strips
    common markdown and whitespace so spelling-equivalent responses
    (``"NONE."``, ``"**NONE**"``, ``" none "``) also terminate the
    loop. Matching is case-insensitive.
    """
    cleaned = reviewer_response.strip().strip("*_`. ").strip()
    return cleaned.casefold() == _REVIEWER_PASS_SENTINEL.casefold()


def _accumulate_metrics(
    per_agent_summaries: list[dict],
) -> tuple[dict, int, int, int, int]:
    """Combine the per-agent final metrics summaries into one view.

    Each entry in ``per_agent_summaries`` is the **final** summary of
    one Strands agent (one for the Writer, one for the Reviewer). The
    function returns the merged ``strands_metrics`` payload and the
    four token totals the runner persists in ``metadata.json``:
    prompt, completion, cache-read, cache-write.

    Strands' ``Agent.event_loop_metrics.accumulated_usage`` accumulates
    across **all** invocations of that agent (verified against
    ``strands.telemetry.metrics.EventLoopMetrics`` — ``accumulated_usage``
    docstring: "across all model invocations (across all requests)";
    ``reset_usage_metrics`` only opens a new ``AgentInvocation`` and
    does **not** reset ``accumulated_usage``). The runner therefore
    queries each agent's metrics **once** at end-of-loop and passes
    the two per-agent totals here; summing per-call snapshots would
    double-count tokens because each snapshot already contains the
    cumulative state up to that point.
    """
    prompt_tokens = 0
    completion_tokens = 0
    cache_read_tokens = 0
    cache_write_tokens = 0
    for summary in per_agent_summaries:
        usage = summary.get("accumulated_usage", {})
        prompt_tokens += usage.get("inputTokens", 0)
        completion_tokens += usage.get("outputTokens", 0)
        cache_read_tokens += usage.get("cacheReadInputTokens", 0)
        cache_write_tokens += usage.get("cacheWriteInputTokens", 0)

    combined = {
        "accumulated_usage": {
            "inputTokens": prompt_tokens,
            "outputTokens": completion_tokens,
            "totalTokens": prompt_tokens + completion_tokens,
            "cacheReadInputTokens": cache_read_tokens,
            "cacheWriteInputTokens": cache_write_tokens,
        },
        "per_agent_summaries": per_agent_summaries,
    }
    return (
        combined,
        prompt_tokens,
        completion_tokens,
        cache_read_tokens,
        cache_write_tokens,
    )


def _run_writer_reviewer_loop(
    writer_agent: Any,
    reviewer_agent: Any,
    writer_user_content: list[dict],
    reviewer_first_user_content_factory,
    *,
    max_iterations: int = _MAX_REVIEWER_ITERATIONS,
) -> tuple[str, list[dict], int, int, bool]:
    """Run the Writer/Reviewer cycle until the Reviewer passes the
    draft (returns ``NONE``) or the iteration cap is reached.

    The ``reviewer_first_user_content_factory`` is a callable that
    takes the current draft and returns the Reviewer's first-turn
    user content (a list of Strands content blocks, with a cachePoint
    between source and draft). It is invoked once on the Reviewer's
    first turn — subsequent turns send only the updated draft because
    the Reviewer's conversation history already contains the source.

    Returns ``(final_draft, per_agent_summaries, writer_calls,
    reviewer_iterations, converged)``. ``per_agent_summaries`` is a
    list of two ``EventLoopMetrics.get_summary()`` dicts (Writer's
    final, then Reviewer's final). Strands' ``accumulated_usage``
    accumulates across **all** calls of an agent, so the **final**
    summary on each agent is its full lifetime total — summing
    snapshots from every individual call would double-count.
    ``writer_calls`` is the number of times the Writer was invoked
    (1 = initial draft; >1 = initial + N revisions). ``reviewer_iterations``
    is the number of Reviewer invocations (1 = first draft passed).
    ``converged`` is True iff the Reviewer returned ``NONE`` before
    the cap.
    """
    # 1) Writer: produce the initial draft.
    writer_result, writer_err = _safe_invoke_agent(writer_agent, writer_user_content)
    writer_calls = 1
    if writer_result is None:
        # The Writer's first call exhausted its max_tokens budget
        # before emitting any text. We have no draft to feed the
        # Reviewer, so abort the loop and surface the error message
        # as the "draft" for downstream visibility.
        return (
            f"[ERROR] Writer hit max_tokens on its initial draft: {writer_err}",
            [],
            writer_calls,
            0,
            False,
        )
    draft = str(writer_result).strip()

    reviewer_iterations = 0
    converged = False
    reviewer_result = None
    for i in range(max_iterations):
        # 2) Reviewer: review the current draft. The first turn sends
        # the full source-+-draft user message (with a cachePoint);
        # subsequent turns send only the updated draft, and the
        # Reviewer agent's conversation history carries the source.
        if i == 0:
            reviewer_input = reviewer_first_user_content_factory(draft)
        else:
            reviewer_input = (
                "Updated draft after Writer revision:\n---\n"
                f"{draft}\n---\n\n"
                "Re-review against the source. List remaining issues "
                "or output `NONE`."
            )
        new_reviewer_result, reviewer_err = _safe_invoke_agent(
            reviewer_agent, reviewer_input
        )
        reviewer_iterations += 1
        if new_reviewer_result is None:
            # Reviewer ran out of room (typically a reasoning-heavy
            # model whose chain-of-thought consumed the budget).
            # Treat as a non-pass: we couldn't verify the draft, so
            # we don't claim convergence. Stop the loop — another
            # cycle would just hit the same limit.
            feedback = (
                f"[Reviewer max_tokens reached, no review emitted: {reviewer_err}]"
            )
            break
        reviewer_result = new_reviewer_result
        feedback = str(reviewer_result).strip()

        if _reviewer_passes(feedback):
            converged = True
            break

        # If this was the last allowed iteration and the Reviewer still
        # flagged issues, stop here. Revising once more would be
        # wasteful (we have no remaining iteration to verify the
        # revision) and the Reviewer's last feedback is preserved in
        # the per-call metrics for the §5.3 audit trail.
        if i == max_iterations - 1:
            break

        # 3) Writer: revise the entry to address the Reviewer's
        # feedback. The Writer agent's conversation history carries
        # the prior draft and the source, so we send only the feedback
        # and the revise instruction.
        revise_input = (
            "Reviewer feedback on the previous draft:\n---\n"
            f"{feedback}\n---\n\n"
            "Address every item above and re-emit the complete revised "
            "wiki entry. Output the entry only — no commentary."
        )
        new_writer_result, writer_err = _safe_invoke_agent(writer_agent, revise_input)
        writer_calls += 1
        if new_writer_result is None:
            # Writer's revision blew the budget. Keep the prior
            # (verified) draft; that is at least one the Reviewer has
            # seen. Stop the loop because another revision would hit
            # the same limit.
            break
        writer_result = new_writer_result
        draft = str(writer_result).strip()

    # Take ONE final summary per agent. Strands' EventLoopMetrics
    # accumulates ``accumulated_usage`` across all invocations of the
    # same agent, so the final result.metrics already contains the
    # full lifetime totals; do not sum per-call snapshots.
    per_agent_summaries: list[dict] = []
    if hasattr(writer_result, "metrics"):
        per_agent_summaries.append(writer_result.metrics.get_summary())
    if reviewer_result is not None and hasattr(reviewer_result, "metrics"):
        per_agent_summaries.append(reviewer_result.metrics.get_summary())

    return (
        draft,
        per_agent_summaries,
        writer_calls,
        reviewer_iterations,
        converged,
    )


# ── Output helpers ─────────────────────────────────────────────────────
# Process the agent's response and accumulated metrics into the
# fields persisted in metadata.json.

def _extract_wiki_entry(raw_text: str) -> str:
    """Extract the final wiki entry from the Writer's last response.

    After CL-06 the Writer is instructed to emit *only* the wiki entry
    (no preamble, no review notes), so this is mostly a defensive
    cleanup. The audience schemas use ``## `` (h2) section headings;
    we look for the first such heading and return everything from
    there onward, falling back to the legacy ``# `` (h1) form for
    backward compatibility with earlier prompt versions, and finally
    to the raw text trimmed.
    """
    import re

    # Prefer the first h2 (current audience-schema convention).
    h2_match = re.search(r"^## .+", raw_text, re.MULTILINE)
    if h2_match:
        return raw_text[h2_match.start():].strip()
    # Fall back to h1 for older prompt versions.
    h1_matches = list(re.finditer(r"^# .+", raw_text, re.MULTILINE))
    if h1_matches:
        return raw_text[h1_matches[-1].start():].strip()
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
    reviewer_prompt_id: str = "agentic_reviewer",
    audience: str = "development",
    temperature: float | None = None,
    max_tokens: int | None = None,
    top_p: float | None = None,
    top_k: int | None = None,
    max_iterations: int = _MAX_REVIEWER_ITERATIONS,
    run_tag: str | None = None,
) -> Path:
    """Run Architecture B on one or more artifacts.

    Sampling parameters are read from the prompt YAML by default.
    CLI overrides take precedence when explicitly provided.

    Args:
        artifact_filenames: Filenames in data/anonymized/.
        prompt_id: Writer prompt template to use.
        reviewer_prompt_id: Reviewer prompt template to use (CL-06).
        audience: Audience name to render the prompt for. Must match one
                  of the audiences declared in the prompt YAML's
                  ``meta.audiences`` block (CL-01, thesis §4.2.3).
                  Defaults to ``development`` (Run-1 schema analog).
        temperature: Override sampling temperature.
        max_tokens: Override max response tokens.
        top_p: Override nucleus sampling threshold.
        top_k: Override top-k sampling.
        max_iterations: Cap on Writer/Reviewer cycles (CL-06 safeguard).
        run_tag: Optional tag appended to the run directory name.

    Returns:
        Path to the run output directory.
    """
    # ── 1. Load prompts and artifacts ───────────────────────────────
    writer_prompt = load_prompt(prompt_id)
    reviewer_prompt = load_prompt(reviewer_prompt_id)
    bundle = load_artifacts(*artifact_filenames)
    model_id = writer_prompt.model

    # Resolve sampling: CLI overrides > prompt YAML > hardcoded defaults
    sampling = writer_prompt.sampling
    eff_temperature = temperature if temperature is not None else sampling.get("temperature", 0.3)
    eff_max_tokens = max_tokens if max_tokens is not None else int(sampling.get("max_tokens", 4096))
    eff_top_p = top_p if top_p is not None else sampling.get("top_p")
    eff_top_k = top_k if top_k is not None else sampling.get("top_k")
    if eff_top_k is not None:
        eff_top_k = int(eff_top_k)

    # Audience is forwarded to render() only when the prompt declares
    # an `audiences:` block; mirrors the pipeline runner contract so
    # both architectures resolve audience the same way.
    render_kwargs: dict[str, str] = {
        "artifact_type": bundle.artifact_type,
        "artifact_id": bundle.artifact_id,
        "artifact_text": bundle.artifact_text,
    }
    if writer_prompt.audiences:
        render_kwargs["audience"] = audience  # render() validates membership
    elif audience != "development":
        raise ValueError(
            f"Prompt {prompt_id!r} does not declare audiences; "
            f"cannot run with audience={audience!r}."
        )

    rendered = writer_prompt.render(**render_kwargs)

    # Strands expects (system_prompt, history, live_user_message) split:
    #   - system_prompt: concatenated system messages.
    #   - history: every (user, assistant) turn before the live request
    #              (CL-02 exemplar pairs).
    #   - user_message: the final user turn (the live request).
    writer_system_text, writer_history, writer_user_message = _split_for_strands(rendered)

    # CL-05 cache breakpoints. The system prompt and the source-artifact
    # prefix of the live user are stable across all Writer revision
    # turns; marking them with ``cachePoint`` lets every subsequent
    # cycle hit Anthropic's prompt cache (~10x cheaper for repeated
    # tokens). Strands translates ``cachePoint`` to ``cache_control:
    # ephemeral`` on the preceding text block.
    writer_system_prompt = _wrap_system_for_cache(writer_system_text)
    writer_user_content = _split_user_message_for_cache(writer_user_message)

    # ── 2. Build the Writer and Reviewer agents ─────────────────────
    writer_agent = _create_agent(
        model_id=model_id,
        temperature=eff_temperature,
        max_tokens=eff_max_tokens,
        system_prompt=writer_system_prompt,
        history=writer_history,
        top_p=eff_top_p,
        top_k=eff_top_k,
    )

    # Reviewer uses its own YAML so the prompt is reviewable / testable
    # independently of the Writer. Sampling resolution mirrors the Writer
    # (CLI override → YAML default), with one deliberate exception:
    # ``max_tokens`` is taken from the Reviewer YAML and is not
    # CLI-overridable — the Reviewer is intermediate work capped at 150
    # words, not user-facing output, so a CLI ``--max-tokens`` aimed at
    # the Writer should not also bloat the Reviewer's budget.
    reviewer_sampling = reviewer_prompt.sampling
    reviewer_temperature = (
        temperature
        if temperature is not None
        else reviewer_sampling.get("temperature", 0.3)
    )
    reviewer_max_tokens = int(reviewer_sampling.get("max_tokens", 1024))
    reviewer_top_p = top_p if top_p is not None else reviewer_sampling.get("top_p")
    reviewer_top_k = top_k if top_k is not None else reviewer_sampling.get("top_k")
    if reviewer_top_k is not None:
        reviewer_top_k = int(reviewer_top_k)

    reviewer_system_text = next(
        m["content"] for m in reviewer_prompt._messages if m["role"] == "system"
    )
    reviewer_user_template = next(
        m["content"] for m in reviewer_prompt._messages if m["role"] == "user"
    )

    reviewer_agent = _create_agent(
        model_id=reviewer_prompt.model,
        temperature=reviewer_temperature,
        max_tokens=reviewer_max_tokens,
        system_prompt=_wrap_system_for_cache(reviewer_system_text),
        history=None,  # Reviewer does not use exemplars; CL-02 is Writer-only.
        top_p=reviewer_top_p,
        top_k=reviewer_top_k,
    )

    def _reviewer_first_user_content(current_draft: str) -> list[dict]:
        """Render the Reviewer's first-turn user message and split it
        for caching at the source/draft boundary."""
        rendered_user = reviewer_user_template.format(
            artifact_id=bundle.artifact_id,
            artifact_type=bundle.artifact_type,
            artifact_text=bundle.artifact_text,
            draft=current_draft,
        )
        return _split_user_message_for_cache(
            rendered_user, marker=_REVIEWER_DRAFT_MARKER
        )

    # ── 3. Run the Writer/Reviewer loop ─────────────────────────────
    t0 = time.perf_counter()
    call_ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (
        final_draft,
        per_agent_summaries,
        writer_calls,
        reviewer_iterations,
        reviewer_passed,
    ) = _run_writer_reviewer_loop(
        writer_agent,
        reviewer_agent,
        writer_user_content,
        _reviewer_first_user_content,
        max_iterations=max_iterations,
    )
    latency = time.perf_counter() - t0

    # ── 4. Aggregate metrics ────────────────────────────────────────
    (
        combined_metrics,
        prompt_tokens,
        completion_tokens,
        cache_read_tokens,
        cache_write_tokens,
    ) = _accumulate_metrics(per_agent_summaries)
    total_tokens = prompt_tokens + completion_tokens

    # Strands doesn't track cost natively — estimate via litellm. CL-05
    # passes the cache token fields so cost_per_token applies cache-read
    # and cache-write rates separately from the standard input rate.
    # Cost is computed per-agent (Writer at its model, Reviewer at its
    # model) and summed, so a future refinement that makes the Reviewer
    # a cheaper model is priced correctly without further changes.
    agent_models = [model_id, reviewer_prompt.model]
    cost_usd = 0.0
    for summary, agent_model in zip(per_agent_summaries, agent_models):
        usage = summary.get("accumulated_usage", {})
        cost_usd += _estimate_cost(
            agent_model,
            usage.get("inputTokens", 0),
            usage.get("outputTokens", 0),
            cache_read_tokens=usage.get("cacheReadInputTokens", 0),
            cache_write_tokens=usage.get("cacheWriteInputTokens", 0),
        )

    # ── 5. Create run output directory ──────────────────────────────
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dir_name = f"agentic_{bundle.artifact_id}_{ts}"
    if run_tag:
        dir_name += f"_{run_tag}"
    run_dir = _RESULTS_DIR / dir_name
    run_dir.mkdir(parents=True, exist_ok=True)

    # ── 6. Write outputs ────────────────────────────────────────────
    wiki_text = _extract_wiki_entry(final_draft)

    (run_dir / "wiki_entry.md").write_text(wiki_text, encoding="utf-8")

    metadata = {
        "architecture": "agentic",
        "prompt_id": prompt_id,
        "prompt_version": writer_prompt.version,
        "reviewer_prompt_id": reviewer_prompt_id,
        "reviewer_prompt_version": reviewer_prompt.version,
        "audience": audience if writer_prompt.audiences else None,
        "model": model_id,
        "artifact_id": bundle.artifact_id,
        "artifact_type": bundle.artifact_type,
        "artifact_files": list(artifact_filenames),
        "temperature": eff_temperature,
        "max_tokens": eff_max_tokens,
        "top_p": eff_top_p,
        "top_k": eff_top_k,
        "timestamp": call_ts,
        # CL-06: total LLM invocations across both agents. Writer is
        # invoked once for the initial draft plus once per revision;
        # Reviewer once per iteration of the loop.
        "num_calls": writer_calls + reviewer_iterations,
        "writer_calls": writer_calls,
        "reviewer_iterations": reviewer_iterations,
        "reviewer_passed": reviewer_passed,
        "max_iterations": max_iterations,
        "total_latency_seconds": round(latency, 2),
        "total_cost_usd": round(cost_usd, 6),
        "total_tokens": total_tokens,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cache_read_input_tokens": cache_read_tokens,
        "cache_creation_input_tokens": cache_write_tokens,
        "strands_metrics": combined_metrics,
    }
    (run_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

    # Raw messages for reproducibility
    (run_dir / "messages.json").write_text(
        json.dumps(rendered, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return run_dir
