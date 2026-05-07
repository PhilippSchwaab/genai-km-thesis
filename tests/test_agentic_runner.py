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
            # CL-05: cache hit/write counters surfaced by Strands' LiteLLMModel.
            "cacheReadInputTokens": 800,
            "cacheWriteInputTokens": 200,
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
    """Mimics a Strands Agent: callable, returns _FakeAgentResult.

    Captures the prompt argument so tests can assert on its shape (CL-05
    forwards a list of content blocks with a cachePoint instead of a
    plain string)."""

    def __init__(self, **kwargs):
        self._kwargs = kwargs
        self.last_prompt = None

    def __call__(self, prompt):
        self.last_prompt = prompt
        return _FakeAgentResult()


# ── Patches ─────────────────────────────────────────────────────────────


@pytest.fixture()
def mock_agent():
    """Patch _create_agent and _make_tools so we don't need strands installed.

    Yields the patched _create_agent mock; the underlying _FakeAgent that
    is returned to the runner can be retrieved via ``mock_create.return_value``
    for tests that need to inspect what the runner sent to it."""
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
    # CL-05: cache token fields persist for §5.3 hit-rate analysis.
    assert meta["cache_read_input_tokens"] == 800
    assert meta["cache_creation_input_tokens"] == 200
    # tool calls (2) + 1 for the initial call
    assert meta["num_calls"] == 3
    assert "timestamp" in meta
    assert "strands_metrics" in meta


def test_writes_messages_json(mock_agent, results_dir):
    run_dir = run_agentic("CS-06_Testing_Strategy_compiled.md")
    messages = json.loads((run_dir / "messages.json").read_text())

    # 1 system + 2*k exemplar (CL-02) + 1 live user.
    assert len(messages) >= 2
    assert messages[0]["role"] == "system"
    assert messages[-1]["role"] == "user"


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


# ── CL-01: audience parameter persisted in metadata ────────────────────


class TestAudiencePersistence:
    """Verify the runner forwards the audience to render() and persists
    it in metadata.json, so every run is replayable from its metadata."""

    def test_default_audience_is_development(self, mock_agent, results_dir):
        run_dir = run_agentic("CS-06_Testing_Strategy_compiled.md")
        meta = json.loads((run_dir / "metadata.json").read_text())
        assert meta["audience"] == "development"

    def test_explicit_audience_recorded(self, mock_agent, results_dir):
        run_dir = run_agentic(
            "CS-06_Testing_Strategy_compiled.md",
            audience="marketing",
        )
        meta = json.loads((run_dir / "metadata.json").read_text())
        assert meta["audience"] == "marketing"

    def test_unknown_audience_raises(self, mock_agent, results_dir):
        with pytest.raises(KeyError):
            run_agentic(
                "CS-06_Testing_Strategy_compiled.md",
                audience="finance",
            )


# ── CL-02: exemplar history routed through Strands' messages= ──────────


class TestExemplarHistoryRouting:
    """Verify the agentic runner splits the rendered messages into
    (system_prompt, history, user_message) and forwards the history
    list to Strands' Agent via the ``messages=`` constructor parameter.
    The live user turn must reach the agent's __call__ method, not the
    initial messages list."""

    def test_split_for_strands_helper_isolates_live_user(self):
        from src.agentic.runner import _split_for_strands

        rendered = [
            {"role": "system", "content": "SYS"},
            {"role": "user", "content": "EX1_USER"},
            {"role": "assistant", "content": "EX1_ASST"},
            {"role": "user", "content": "EX2_USER"},
            {"role": "assistant", "content": "EX2_ASST"},
            {"role": "user", "content": "LIVE_USER"},
        ]
        sys_prompt, history, user_msg = _split_for_strands(rendered)
        assert sys_prompt == "SYS"
        assert user_msg == "LIVE_USER"
        assert [m["role"] for m in history] == ["user", "assistant", "user", "assistant"]
        # Exemplar content wrapped in Strands content-block shape
        # (required by Agent(messages=...); agent(...) auto-wraps).
        assert history[0]["content"] == [{"text": "EX1_USER"}]
        assert history[2]["content"] == [{"text": "EX2_USER"}]

    def test_split_rejects_non_user_terminal(self):
        from src.agentic.runner import _split_for_strands

        rendered = [
            {"role": "system", "content": "SYS"},
            {"role": "user", "content": "U"},
            {"role": "assistant", "content": "A"},  # ends with assistant
        ]
        with pytest.raises(ValueError):
            _split_for_strands(rendered)

    def test_create_agent_receives_history_kwarg(self, mock_agent, results_dir):
        run_agentic(
            "CS-06_Testing_Strategy_compiled.md",
            audience="development",
        )
        mock_agent.assert_called_once()
        call_kwargs = mock_agent.call_args[1]
        history = call_kwargs["history"]
        # Two exemplars per audience -> 4 messages of history.
        assert len(history) == 4
        assert [m["role"] for m in history] == ["user", "assistant", "user", "assistant"]

    def test_split_user_message_inserts_cachepoint_at_marker(self):
        """CL-05: the live user message is split at the source-artifact /
        instruction boundary with a cachePoint between the two text
        blocks."""
        from src.agentic.runner import (
            _USER_INSTRUCTION_MARKER,
            _split_user_message_for_cache,
        )

        msg = (
            "Source artifact (X, type: Y):\n---\nBODY\n---\n\n"
            f"{_USER_INSTRUCTION_MARKER} into a wiki entry.\n\n"
            "## Heading"
        )
        blocks = _split_user_message_for_cache(msg)
        assert len(blocks) == 3
        assert blocks[0]["text"].endswith("---\n\n")
        assert blocks[1] == {"cachePoint": {"type": "default"}}
        assert blocks[2]["text"].startswith(_USER_INSTRUCTION_MARKER)

    def test_split_user_message_no_marker_falls_back_to_single_block(self):
        """Defensive: if the template ever changes such that the marker
        disappears, the runner produces a single text block (no cache
        breakpoint inside the user) rather than crashing."""
        from src.agentic.runner import _split_user_message_for_cache

        blocks = _split_user_message_for_cache("nothing matches here")
        assert blocks == [{"text": "nothing matches here"}]

    def test_runner_forwards_system_prompt_with_cachepoint(
        self, mock_agent, results_dir
    ):
        """CL-05: the system prompt reaching the agent is a content-block
        list ending in a cachePoint."""
        run_agentic("CS-06_Testing_Strategy_compiled.md", audience="development")
        sys_prompt = mock_agent.call_args[1]["system_prompt"]
        assert isinstance(sys_prompt, list)
        assert "text" in sys_prompt[0]
        assert sys_prompt[-1] == {"cachePoint": {"type": "default"}}

    def test_runner_forwards_user_content_with_cachepoint(
        self, mock_agent, results_dir
    ):
        """CL-05: the live user prompt reaching agent(...) is a content-
        block list with a cachePoint between source body and instruction."""
        run_agentic("CS-06_Testing_Strategy_compiled.md", audience="development")
        fake_agent = mock_agent.return_value
        prompt = fake_agent.last_prompt
        assert isinstance(prompt, list)
        # Either a single block (defensive fallback) or 3 blocks (the
        # source / cachePoint / instruction split). Production path is
        # the 3-block form.
        assert len(prompt) == 3
        assert {"cachePoint": {"type": "default"}} in prompt
        # Source artifact body precedes the cachePoint; instruction follows.
        cp_idx = prompt.index({"cachePoint": {"type": "default"}})
        assert "Source artifact" in prompt[cp_idx - 1]["text"]
        from src.agentic.runner import _USER_INSTRUCTION_MARKER
        assert _USER_INSTRUCTION_MARKER in prompt[cp_idx + 1]["text"]

    def test_estimate_cost_passes_cache_token_fields_to_litellm(self):
        """CL-05: _estimate_cost must forward cache token fields to
        ``litellm.cost_per_token`` so cache-read / cache-write rates
        apply correctly."""
        pytest.importorskip("litellm")
        from unittest.mock import patch

        from src.agentic.runner import _estimate_cost

        # Patch the litellm.cost_per_token call at the location the
        # runner imports it (lazy import inside the function).
        with patch("litellm.cost_per_token", return_value=(0.0123, 0.0456)) as cpt:
            cost = _estimate_cost(
                "anthropic/claude-sonnet-4-6",
                prompt_tokens=1000,
                completion_tokens=500,
                cache_read_tokens=800,
                cache_write_tokens=200,
            )
        assert cost == pytest.approx(0.0579)
        cpt.assert_called_once()
        kwargs = cpt.call_args.kwargs
        assert kwargs["cache_creation_input_tokens"] == 200
        assert kwargs["cache_read_input_tokens"] == 800

    def test_estimate_cost_zero_cache_tokens_is_legacy_behaviour(self):
        """When cache fields are zero, _estimate_cost still returns a
        sensible cost (the standard prompt + completion rates)."""
        pytest.importorskip("litellm")
        from unittest.mock import patch

        from src.agentic.runner import _estimate_cost

        with patch("litellm.cost_per_token", return_value=(0.001, 0.002)):
            cost = _estimate_cost(
                "anthropic/claude-sonnet-4-6",
                prompt_tokens=1000,
                completion_tokens=500,
            )
        assert cost == pytest.approx(0.003)

    def test_history_uses_correct_audience_exemplars(self, mock_agent, results_dir):
        """Verify the history reflects the requested audience's exemplars,
        not another audience's. With shared synthetic sources across
        audiences, the audience-specific signal is in the schema headers
        the entry uses (e.g. '## Outcome', '## Stakeholders involved'
        appear only in marketing-rendered entries). History entries are
        wrapped as Strands content blocks ([{"text": ...}])."""
        run_agentic(
            "CS-06_Testing_Strategy_compiled.md",
            audience="marketing",
        )
        call_kwargs = mock_agent.call_args[1]
        history = call_kwargs["history"]
        history_text = " ".join(
            block["text"] for m in history for block in m["content"]
        )
        # Marketing-only schema headers must appear in the assistant
        # turns (the audience-specific entries).
        assert "## Outcome" in history_text
        assert "## Business impact" in history_text
        # Development-only headers must NOT appear in the assistant
        # entries (they should appear only in their own user-wrapper
        # schema reminder, not in marketing rendered entries).
        marketing_assistant_text = " ".join(
            block["text"]
            for m in history if m["role"] == "assistant"
            for block in m["content"]
        )
        assert "## Implementation detail" not in marketing_assistant_text
