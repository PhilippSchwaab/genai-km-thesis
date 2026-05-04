"""Tests for the Architecture A pipeline runner (no live API calls)."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.common.llm_client import LLMResult
from src.pipeline.runner import run_pipeline


def _fake_result(text: str = "# Wiki Entry\n\nGenerated content.") -> LLMResult:
    return LLMResult(
        text=text,
        model="mistral/mistral-large-latest",
        timestamp="2026-04-16T14:30:00+00:00",
        latency_seconds=2.15,
        prompt_tokens=500,
        completion_tokens=300,
        total_tokens=800,
        cost_usd=0.004,
    )


def _fake_complete(model, messages, *, temperature=0.3, max_tokens=4096,
                   top_p=None, top_k=None, call_log=None):
    """Stand-in for complete() that records to the call_log like the real one."""
    result = _fake_result()
    if call_log is not None:
        call_log.record(result)
    return result


@pytest.fixture()
def mock_complete():
    """Patch complete() to return a fake result without hitting the API."""
    with patch("src.pipeline.runner.complete", side_effect=_fake_complete) as m:
        yield m


@pytest.fixture()
def results_dir(tmp_path, monkeypatch):
    """Redirect output to a temp directory."""
    monkeypatch.setattr("src.pipeline.runner._RESULTS_DIR", tmp_path)
    return tmp_path


# ── Output structure ─────────────────────────────────────────────────


def test_creates_run_directory(mock_complete, results_dir):
    run_dir = run_pipeline("CS-06_Testing_Strategy_compiled.md")
    assert run_dir.exists()
    assert run_dir.is_dir()


def test_writes_wiki_entry(mock_complete, results_dir):
    run_dir = run_pipeline("CS-06_Testing_Strategy_compiled.md")
    wiki = (run_dir / "wiki_entry.md").read_text()
    assert "Generated content" in wiki


def test_writes_metadata_json(mock_complete, results_dir):
    run_dir = run_pipeline("CS-06_Testing_Strategy_compiled.md")
    meta = json.loads((run_dir / "metadata.json").read_text())

    assert meta["architecture"] == "pipeline"
    assert meta["prompt_id"] == "pipeline_generate_wiki"
    assert "CS-06_Testing_Strategy_compiled" in meta["artifact_id"]
    assert meta["artifact_type"] == "development_activity"
    assert meta["total_latency_seconds"] == 2.15
    assert meta["total_cost_usd"] == 0.004
    assert meta["total_tokens"] == 800
    assert meta["num_calls"] == 1
    assert "timestamp" in meta


def test_writes_messages_json(mock_complete, results_dir):
    run_dir = run_pipeline("CS-06_Testing_Strategy_compiled.md")
    messages = json.loads((run_dir / "messages.json").read_text())

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"


# ── Directory naming ─────────────────────────────────────────────────


def test_dir_name_contains_architecture_and_artifact(mock_complete, results_dir):
    run_dir = run_pipeline("CS-06_Testing_Strategy_compiled.md")
    assert "pipeline" in run_dir.name
    assert "CS-06" in run_dir.name


def test_run_tag_appended_to_dir_name(mock_complete, results_dir):
    run_dir = run_pipeline("CS-06_Testing_Strategy_compiled.md", run_tag="v2test")
    assert run_dir.name.endswith("_v2test")


# ── Sampling from YAML defaults ─────────────────────────────────────


def test_sampling_defaults_from_yaml(mock_complete, results_dir):
    """When no overrides are given, sampling comes from the prompt YAML."""
    run_dir = run_pipeline("CS-06_Testing_Strategy_compiled.md")
    meta = json.loads((run_dir / "metadata.json").read_text())
    # pipeline_generate_wiki.yaml has: temperature=0.3, max_tokens=4096
    assert meta["temperature"] == 0.3
    assert meta.get("top_p") is None
    assert meta.get("top_k") is None
    assert meta["max_tokens"] == 4096


def test_cli_overrides_yaml_sampling(mock_complete, results_dir):
    """CLI overrides take precedence over YAML defaults."""
    run_dir = run_pipeline(
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


def test_complete_called_with_correct_model(mock_complete, results_dir):
    run_pipeline("CS-06_Testing_Strategy_compiled.md")
    call_kwargs = mock_complete.call_args
    assert call_kwargs.kwargs.get("model") or call_kwargs.args[0] == "ollama_chat/gemma4:26b"


# ── Support reports work too ─────────────────────────────────────────


def test_support_report_artifact_type(mock_complete, results_dir):
    run_dir = run_pipeline("CS-01_Archive_Backup_report.md")
    meta = json.loads((run_dir / "metadata.json").read_text())
    assert meta["artifact_type"] == "support_report"
