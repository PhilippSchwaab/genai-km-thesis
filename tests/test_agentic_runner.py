"""Tests for the Architecture B agentic runner (no live API calls)."""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.agentic.runner import run_agentic

# ── Fake Strands result ─────────────────────────────────────────────────

_FAKE_WIKI = "# Wiki Entry\n\nAgent-generated content with self-review."


def _fake_metrics_summary():
    return {
        "accumulated_usage": {
            "inputTokens": 1200,
            "outputTokens": 600,
            "totalTokens": 1800,
        },
        "tool_usage": {
            "total_tool_calls": 2,
        },
        "total_duration": 5.0,
        "latencyMs": 4800,
    }


class _FakeAgentResult:
    """Mimics the strands AgentResult enough for the runner."""

    def __init__(self):
        self.metrics = SimpleNamespace(get_summary=_fake_metrics_summary)

    def __str__(self):
        return _FAKE_WIKI


class _FakeAgent:
    """Mimics a Strands Agent: callable, returns _FakeAgentResult."""

    def __init__(self, **kwargs):
        self._kwargs = kwargs

    def __call__(self, user_message: str):
        return _FakeAgentResult()


# ── Patches ─────────────────────────────────────────────────────────────


@pytest.fixture()
def mock_agent():
    """Patch _create_agent and _make_tools so we don't need strands installed."""
    fake = _FakeAgent()
    with (
        patch("src.agentic.runner._create_agent", return_value=fake) as mock_create,
        patch("src.agentic.runner._make_tools", return_value=[]),
    ):
        yield mock_create


@pytest.fixture()
def results_dir(tmp_path, monkeypatch):
    """Redirect output to a temp directory."""
    monkeypatch.setattr("src.agentic.runner._RESULTS_DIR", tmp_path)
    return tmp_path


# ── Output structure ────────────────────────────────────────────────────


def test_creates_run_directory(mock_agent, results_dir):
    run_dir = run_agentic("CS-06_Testing_Strategy_compiled.md")
    assert run_dir.exists()
    assert run_dir.is_dir()


def test_writes_wiki_entry(mock_agent, results_dir):
    run_dir = run_agentic("CS-06_Testing_Strategy_compiled.md")
    wiki = (run_dir / "wiki_entry.md").read_text()
    assert "Agent-generated content" in wiki


def test_writes_metadata_json(mock_agent, results_dir):
    run_dir = run_agentic("CS-06_Testing_Strategy_compiled.md")
    meta = json.loads((run_dir / "metadata.json").read_text())

    assert meta["architecture"] == "agentic"
    assert meta["prompt_id"] == "agentic_generate_wiki"
    assert meta["model"] == "mistral/mistral-large-latest"
    assert "CS-06_Testing_Strategy_compiled" in meta["artifact_id"]
    assert meta["artifact_type"] == "development_activity"
    assert meta["total_tokens"] == 1800
    assert meta["prompt_tokens"] == 1200
    assert meta["completion_tokens"] == 600
    # tool calls (2) + 1 for the initial call
    assert meta["num_calls"] == 3
    assert "timestamp" in meta
    assert "strands_metrics" in meta


def test_writes_messages_json(mock_agent, results_dir):
    run_dir = run_agentic("CS-06_Testing_Strategy_compiled.md")
    messages = json.loads((run_dir / "messages.json").read_text())

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"


# ── Directory naming ────────────────────────────────────────────────────


def test_dir_name_contains_architecture_and_artifact(mock_agent, results_dir):
    run_dir = run_agentic("CS-06_Testing_Strategy_compiled.md")
    assert "agentic" in run_dir.name
    assert "CS-06" in run_dir.name


def test_run_tag_appended_to_dir_name(mock_agent, results_dir):
    run_dir = run_agentic("CS-06_Testing_Strategy_compiled.md", run_tag="v1")
    assert run_dir.name.endswith("_v1")


# ── Parameters ──────────────────────────────────────────────────────────


def test_temperature_and_max_tokens_in_metadata(mock_agent, results_dir):
    run_dir = run_agentic(
        "CS-06_Testing_Strategy_compiled.md",
        temperature=0.7,
        max_tokens=2048,
    )
    meta = json.loads((run_dir / "metadata.json").read_text())
    assert meta["temperature"] == 0.7
    assert meta["max_tokens"] == 2048


def test_create_agent_receives_params(mock_agent, results_dir):
    run_agentic(
        "CS-06_Testing_Strategy_compiled.md",
        temperature=0.5,
        max_tokens=1024,
    )
    mock_agent.assert_called_once()
    call_kwargs = mock_agent.call_args[1]
    assert call_kwargs["model_id"] == "mistral/mistral-large-latest"
    assert call_kwargs["temperature"] == 0.5
    assert call_kwargs["max_tokens"] == 1024


# ── Support reports ─────────────────────────────────────────────────────


def test_support_report_artifact_type(mock_agent, results_dir):
    run_dir = run_agentic("CS-01_Archive_Backup_report.md")
    meta = json.loads((run_dir / "metadata.json").read_text())
    assert meta["artifact_type"] == "support_report"
