"""Tests for the LLM client wrapper (no live API calls)."""

from unittest.mock import MagicMock, patch

import pytest

from src.common.llm_client import CallLog, LLMResult, complete


# ── LLMResult dataclass ──────────────────────────────────────────────


def _make_result(**overrides) -> LLMResult:
    defaults = dict(
        text="Hello world",
        model="mistral/mistral-large-latest",
        timestamp="2026-04-16T14:30:00+00:00",
        latency_seconds=1.23,
        prompt_tokens=50,
        completion_tokens=30,
        total_tokens=80,
        cost_usd=0.001,
    )
    defaults.update(overrides)
    return LLMResult(**defaults)


def test_result_is_frozen():
    r = _make_result()
    with pytest.raises(AttributeError):
        r.text = "changed"


def test_cost_stored_as_usd():
    r = _make_result(cost_usd=0.005)
    assert r.cost_usd == 0.005


# ── CallLog accumulator ─────────────────────────────────────────────


def test_call_log_empty():
    log = CallLog()
    assert log.total_latency == 0.0
    assert log.total_cost_usd == 0.0
    assert log.total_tokens == 0
    assert log.summary()["num_calls"] == 0


def test_call_log_accumulates():
    log = CallLog()
    log.record(_make_result(latency_seconds=1.0, cost_usd=0.01, total_tokens=100))
    log.record(_make_result(latency_seconds=2.5, cost_usd=0.02, total_tokens=200))

    assert log.total_latency == pytest.approx(3.5)
    assert log.total_cost_usd == pytest.approx(0.03)
    assert log.total_tokens == 300
    assert len(log.calls) == 2


def test_call_log_summary_keys():
    log = CallLog()
    log.record(_make_result())
    s = log.summary()
    assert set(s.keys()) == {
        "num_calls",
        "total_latency_seconds",
        "total_cost_usd",
        "total_tokens",
    }


# ── complete() with mocked litellm ──────────────────────────────────


def _mock_response(text="Generated wiki", prompt_tok=100, comp_tok=200):
    """Build a fake litellm response object."""
    resp = MagicMock()
    resp.choices = [MagicMock()]
    resp.choices[0].message.content = text
    resp.model = "mistral/mistral-large-latest"
    resp.usage = MagicMock()
    resp.usage.prompt_tokens = prompt_tok
    resp.usage.completion_tokens = comp_tok
    resp.usage.total_tokens = prompt_tok + comp_tok
    return resp


@patch("src.common.llm_client.litellm")
def test_complete_returns_result(mock_litellm):
    mock_litellm.completion.return_value = _mock_response("test output")
    mock_litellm.completion_cost.return_value = 0.005

    result = complete(
        model="mistral/mistral-large-latest",
        messages=[{"role": "user", "content": "hello"}],
    )

    assert isinstance(result, LLMResult)
    assert result.text == "test output"
    assert result.prompt_tokens == 100
    assert result.completion_tokens == 200
    assert result.cost_usd == 0.005
    assert result.latency_seconds >= 0  # mocked call is near-instant
    # Timestamp should be a valid ISO 8601 UTC string
    from datetime import datetime, timezone
    ts = datetime.fromisoformat(result.timestamp)
    assert ts.tzinfo is not None  # timezone-aware


@patch("src.common.llm_client.litellm")
def test_complete_records_to_call_log(mock_litellm):
    mock_litellm.completion.return_value = _mock_response()
    mock_litellm.completion_cost.return_value = 0.003

    log = CallLog()
    complete(
        model="mistral/mistral-large-latest",
        messages=[{"role": "user", "content": "hi"}],
        call_log=log,
    )

    assert len(log.calls) == 1
    assert log.total_cost_usd == pytest.approx(0.003)


@patch("src.common.llm_client.litellm")
def test_complete_passes_params(mock_litellm):
    mock_litellm.completion.return_value = _mock_response()
    mock_litellm.completion_cost.return_value = 0.0

    complete(
        model="mistral/mistral-large-latest",
        messages=[{"role": "user", "content": "test"}],
        temperature=0.7,
        max_tokens=2048,
    )

    mock_litellm.completion.assert_called_once_with(
        model="mistral/mistral-large-latest",
        messages=[{"role": "user", "content": "test"}],
        temperature=0.7,
        max_tokens=2048,
        stream=False,
    )


@patch("src.common.llm_client.litellm")
def test_complete_passes_top_p_and_top_k(mock_litellm):
    mock_litellm.completion.return_value = _mock_response()
    mock_litellm.completion_cost.return_value = 0.0

    complete(
        model="ollama_chat/gemma4:26b",
        messages=[{"role": "user", "content": "test"}],
        temperature=1.0,
        max_tokens=4096,
        top_p=0.95,
        top_k=64,
    )

    mock_litellm.completion.assert_called_once_with(
        model="ollama_chat/gemma4:26b",
        messages=[{"role": "user", "content": "test"}],
        temperature=1.0,
        max_tokens=4096,
        stream=False,
        top_p=0.95,
        top_k=64,
    )


@patch("src.common.llm_client.litellm")
def test_complete_omits_top_p_top_k_when_none(mock_litellm):
    """When top_p/top_k are None, they should not be passed to litellm."""
    mock_litellm.completion.return_value = _mock_response()
    mock_litellm.completion_cost.return_value = 0.0

    complete(
        model="mistral/mistral-large-latest",
        messages=[{"role": "user", "content": "test"}],
    )

    mock_litellm.completion.assert_called_once_with(
        model="mistral/mistral-large-latest",
        messages=[{"role": "user", "content": "test"}],
        temperature=0.3,
        max_tokens=4096,
        stream=False,
    )


@patch("src.common.llm_client.litellm")
def test_complete_handles_empty_content(mock_litellm):
    resp = _mock_response()
    resp.choices[0].message.content = None
    mock_litellm.completion.return_value = resp
    mock_litellm.completion_cost.return_value = 0.0

    result = complete(
        model="mistral/mistral-large-latest",
        messages=[{"role": "user", "content": "hi"}],
    )
    assert result.text == ""
