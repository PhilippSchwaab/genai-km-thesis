"""
Thin wrapper around litellm.completion() that tracks latency and cost.

Every call returns an LLMResult with the response text plus the metrics
needed for the Speed and Cost MCDA criteria.  Cost is logged in USD
(litellm's native currency).

Usage:
    from src.common.llm_client import complete

    result = complete(
        model="mistral/mistral-large-latest",
        messages=[{"role": "user", "content": "Hello"}],
    )
    print(result.text)
    print(f"{result.latency_seconds:.1f}s, ${result.cost_usd:.4f}")
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

import litellm
from dotenv import load_dotenv

load_dotenv()

# LiteLLM needs the key in the environment; ensure it's set.
_MISTRAL_KEY = os.getenv("MISTRAL_API_KEY", "")
if _MISTRAL_KEY:
    os.environ["MISTRAL_API_KEY"] = _MISTRAL_KEY

# Suppress litellm's noisy logging by default.
litellm.suppress_debug_info = True


@dataclass(frozen=True)
class LLMResult:
    """The response from a single LLM call with attached metrics."""

    text: str
    model: str
    timestamp: str  # ISO 8601 UTC, e.g. "2026-04-16T14:30:00Z"
    latency_seconds: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float


@dataclass
class CallLog:
    """Accumulates metrics across multiple LLM calls for one run."""

    calls: list[LLMResult] = field(default_factory=list)

    def record(self, result: LLMResult) -> None:
        self.calls.append(result)

    @property
    def total_latency(self) -> float:
        return sum(c.latency_seconds for c in self.calls)

    @property
    def total_cost_usd(self) -> float:
        return sum(c.cost_usd for c in self.calls)

    @property
    def total_tokens(self) -> int:
        return sum(c.total_tokens for c in self.calls)

    def summary(self) -> dict:
        """Return a dict suitable for writing to a run metadata file."""
        return {
            "num_calls": len(self.calls),
            "total_latency_seconds": round(self.total_latency, 2),
            "total_cost_usd": round(self.total_cost_usd, 6),
            "total_tokens": self.total_tokens,
        }


def complete(
    model: str,
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.3,
    max_tokens: int = 4096,
    top_p: float | None = None,
    top_k: int | None = None,
    call_log: CallLog | None = None,
) -> LLMResult:
    """Call an LLM via litellm and return text + metrics.

    Args:
        model: LiteLLM model string (e.g. "mistral/mistral-large-latest").
        messages: Chat messages in OpenAI format.
        temperature: Sampling temperature.
        max_tokens: Max tokens in the response.
        top_p: Nucleus sampling threshold (omit to use provider default).
        top_k: Top-k sampling (omit to use provider default).
        call_log: Optional CallLog to accumulate metrics across calls.

    Returns:
        LLMResult with the response text, timing, and cost.
    """
    call_ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    t0 = time.perf_counter()

    # Build optional kwargs — only pass if explicitly set so providers
    # that don't support them don't receive unexpected params.
    optional: dict = {}
    if top_p is not None:
        optional["top_p"] = top_p
    if top_k is not None:
        optional["top_k"] = top_k

    response = litellm.completion(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=False,
        **optional,
    )
    latency = time.perf_counter() - t0

    # litellm.completion() with stream=False returns ModelResponse.
    # We access attributes directly; the stream=False flag guarantees
    # we get a ModelResponse, not a CustomStreamWrapper.
    text: str = response.choices[0].message.content or ""  # type: ignore[union-attr]
    usage = response.usage  # type: ignore[union-attr]
    resolved_model: str = response.model or model  # type: ignore[union-attr]
    cost = litellm.completion_cost(completion_response=response)

    result = LLMResult(
        text=text,
        model=resolved_model,
        timestamp=call_ts,
        latency_seconds=round(latency, 2),
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        total_tokens=usage.total_tokens,
        cost_usd=round(cost, 6),
    )

    if call_log is not None:
        call_log.record(result)

    return result
