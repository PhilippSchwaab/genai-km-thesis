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
    assert meta["model"] == "anthropic/claude-sonnet-4-6"
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


# ── Sampling from YAML defaults ─────────────────────────────────────


def test_sampling_defaults_from_yaml(mock_agent, results_dir):
    """agentic_generate_wiki.yaml has Claude Sonnet sampling params."""
    run_dir = run_agentic("CS-06_Testing_Strategy_compiled.md")
    meta = json.loads((run_dir / "metadata.json").read_text())
    assert meta["temperature"] == 0.3
    assert meta["max_tokens"] == 16384
    assert meta.get("top_p") is None
    assert meta.get("top_k") is None


def test_cli_overrides_yaml_sampling(mock_agent, results_dir):
    run_dir = run_agentic(
        "CS-06_Testing_Strategy_compiled.md",
        temperature=0.7,
        max_tokens=2048,
        top_p=0.9,
        top_k=50,
    )
    meta = json.loads((run_dir / "metadata.json").read_text())
    assert meta["temperature"] == 0.7
    assert meta["max_tokens"] == 2048
    assert meta["top_p"] == 0.9
    assert meta["top_k"] == 50


def test_create_agent_receives_yaml_params(mock_agent, results_dir):
    run_agentic("CS-06_Testing_Strategy_compiled.md")
    mock_agent.assert_called_once()
    call_kwargs = mock_agent.call_args[1]
    assert call_kwargs["model_id"] == "anthropic/claude-sonnet-4-6"
    assert call_kwargs["temperature"] == 0.3
    assert call_kwargs["max_tokens"] == 16384


def test_create_agent_receives_overrides(mock_agent, results_dir):
    run_agentic(
        "CS-06_Testing_Strategy_compiled.md",
        temperature=0.5,
        max_tokens=1024,
        top_p=0.8,
        top_k=40,
    )
    mock_agent.assert_called_once()
    call_kwargs = mock_agent.call_args[1]
    assert call_kwargs["temperature"] == 0.5
    assert call_kwargs["max_tokens"] == 1024
    assert call_kwargs["top_p"] == 0.8
    assert call_kwargs["top_k"] == 40


# ── Support reports ─────────────────────────────────────────────────────


def test_support_report_artifact_type(mock_agent, results_dir):
    run_dir = run_agentic("CS-01_Archive_Backup_report.md")
    meta = json.loads((run_dir / "metadata.json").read_text())
    assert meta["artifact_type"] == "support_report"


# ── CL-04: concision directives on intermediate calls ──────────────────


class TestConcisionDirective:
    """Verify the §4.2.3 CL-04 concision directive is consistently applied
    to intermediate work (REVIEW step + tool responses) but not to the
    final wiki entry. Intermediate-only by design; the rendered system
    prompt explicitly limits the directive's scope."""

    def test_directive_constant_carries_required_elements(self):
        from src.agentic.runner import _CONCISION_DIRECTIVE

        text = _CONCISION_DIRECTIVE.lower()
        assert "bullet" in text, "directive must specify bullet-list format"
        assert "150" in text, "directive must specify the 150-word cap"
        assert "none" in text, "directive must specify the NONE empty marker"
        assert "preamble" in text or "restatement" in text, (
            "directive must forbid preamble / source restatement"
        )

    def test_system_prompt_includes_intermediate_format_block(self):
        from src.common.prompts import load_prompt

        prompt = load_prompt("agentic_generate_wiki")
        sys_text = prompt._messages[0]["content"]
        sys_lower = sys_text.lower()
        # Same four elements as the runner constant.
        assert "bullet" in sys_lower
        assert "150" in sys_lower
        assert "none" in sys_lower
        # Scope must be explicit: intermediate only, final unconstrained.
        assert "intermediate" in sys_lower, (
            "system prompt must mark the directive as intermediate-only"
        )
        assert "final" in sys_lower and "unconstrained" in sys_lower, (
            "system prompt must explicitly exempt the final wiki entry"
        )

    def test_review_step_still_enumerates_three_checks(self):
        """Adding the format block must not erase the REVIEW substance."""
        from src.common.prompts import load_prompt

        prompt = load_prompt("agentic_generate_wiki")
        sys_text = prompt._messages[0]["content"].lower()
        assert "completeness" in sys_text
        assert "hallucination" in sys_text
        assert "attribution" in sys_text
