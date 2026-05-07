"""Tests for the Architecture B agentic runner (no live API calls).

CL-06 (thesis §4.2.3) replaces the Run-1 single-agent + tools design
with a Writer/Reviewer loop. The fixtures below mock both agents so
the runner is exercised end-to-end without strands or litellm being
installed; the loop topology, iteration counting, and metric
accumulation are then asserted on the persisted ``metadata.json``.

The fakes mirror Strands' actual accumulation semantics: each Strands
``Agent`` instance owns one ``EventLoopMetrics`` whose
``accumulated_usage`` grows across **all** invocations of that agent
(verified against ``strands.telemetry.metrics.EventLoopMetrics`` —
``reset_usage_metrics`` only opens a new ``AgentInvocation`` and does
not reset the accumulator). The runner therefore reads each agent's
metrics **once** at end-of-loop; the fakes here add per-call deltas
into a per-agent running total so a final ``get_summary()`` reflects
the same shape as a real Strands run.
"""

import copy
import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from src.agentic.runner import run_agentic

# ── Fake Strands result ─────────────────────────────────────────────────

_FAKE_WIKI = "## Summary\n\nAgent-generated content with self-review."


def _writer_delta(input_tokens=1200, output_tokens=600, cache_read=800, cache_write=200):
    """Per-call delta added to the Writer agent's running totals."""
    return {
        "inputTokens": input_tokens,
        "outputTokens": output_tokens,
        "totalTokens": input_tokens + output_tokens,
        "cacheReadInputTokens": cache_read,
        "cacheWriteInputTokens": cache_write,
    }


def _reviewer_delta(input_tokens=400, output_tokens=80, cache_read=300, cache_write=100):
    """Per-call delta added to the Reviewer agent's running totals."""
    return {
        "inputTokens": input_tokens,
        "outputTokens": output_tokens,
        "totalTokens": input_tokens + output_tokens,
        "cacheReadInputTokens": cache_read,
        "cacheWriteInputTokens": cache_write,
    }


class _FakeAgentResult:
    """Mimics a Strands ``AgentResult`` enough for the runner.

    ``metrics_holder`` is the per-agent live metrics object; calling
    ``self.metrics.get_summary()`` returns the **current** accumulated
    state (mirroring real Strands, where ``result.metrics`` is the
    agent's live ``EventLoopMetrics``)."""

    def __init__(self, text: str, metrics_holder):
        self._text = text
        self.metrics = metrics_holder

    def __str__(self):
        return self._text


class _AccumulatingMetrics:
    """Mimics ``EventLoopMetrics`` accumulating semantics: a single
    instance per agent whose ``accumulated_usage`` grows with every
    call. ``get_summary()`` returns a fresh deep copy so callers that
    capture snapshots at different times see different values, just
    like real Strands."""

    def __init__(self):
        self._usage = {
            "inputTokens": 0,
            "outputTokens": 0,
            "totalTokens": 0,
            "cacheReadInputTokens": 0,
            "cacheWriteInputTokens": 0,
        }

    def add(self, delta: dict) -> None:
        for k, v in delta.items():
            self._usage[k] = self._usage.get(k, 0) + v

    def get_summary(self) -> dict:
        return copy.deepcopy({
            "accumulated_usage": dict(self._usage),
            "tool_usage": {},
        })


class _ScriptedAgent:
    """Mimics a Strands Agent that returns scripted responses.

    Each call pops the next ``(text, delta_metrics)`` tuple from the
    script and adds the delta to the agent's running totals. Captures
    every prompt for later inspection."""

    def __init__(self, script, **kwargs):
        self._script = list(script)
        self._kwargs = kwargs
        self.calls: list = []
        self.metrics_holder = _AccumulatingMetrics()

    def __call__(self, prompt):
        self.calls.append(prompt)
        if not self._script:
            raise RuntimeError(
                "Scripted agent ran out of responses; check max_iterations."
            )
        text, delta = self._script.pop(0)
        self.metrics_holder.add(delta)
        return _FakeAgentResult(text, self.metrics_holder)


# ── Patches ─────────────────────────────────────────────────────────────


@pytest.fixture()
def mock_agents(request):
    """Patch ``_create_agent`` so the runner gets two scripted agents
    in the order Writer-then-Reviewer (which is the order the runner
    constructs them).

    Each test passes its own scripts via parametrize / indirect, OR
    relies on the default "first draft passes" scripts below."""
    writer_script = [
        # First (and only, default) Writer call: produce the draft.
        (_FAKE_WIKI, _writer_delta()),
    ]
    reviewer_script = [
        # First (and only, default) Reviewer call: pass.
        ("NONE", _reviewer_delta()),
    ]
    overrides = getattr(request, "param", None) or {}
    if "writer" in overrides:
        writer_script = overrides["writer"]
    if "reviewer" in overrides:
        reviewer_script = overrides["reviewer"]

    writer = _ScriptedAgent(writer_script)
    reviewer = _ScriptedAgent(reviewer_script)

    # The runner calls _create_agent twice: first for the Writer, then
    # for the Reviewer. side_effect feeds them in that order.
    with patch(
        "src.agentic.runner._create_agent",
        side_effect=[writer, reviewer],
    ) as mock_create:
        yield SimpleNamespace(
            create=mock_create,
            writer=writer,
            reviewer=reviewer,
        )


@pytest.fixture()
def results_dir(tmp_path, monkeypatch):
    """Redirect output to a temp directory."""
    monkeypatch.setattr("src.agentic.runner._RESULTS_DIR", tmp_path)
    return tmp_path


# ── Output structure ────────────────────────────────────────────────────


def test_creates_run_directory(mock_agents, results_dir):
    run_dir = run_agentic("CS-06_Testing_Strategy_compiled.md")
    assert run_dir.exists()
    assert run_dir.is_dir()


def test_writes_wiki_entry(mock_agents, results_dir):
    run_dir = run_agentic("CS-06_Testing_Strategy_compiled.md")
    wiki = (run_dir / "wiki_entry.md").read_text()
    assert "Agent-generated content" in wiki


def test_writes_metadata_json(mock_agents, results_dir):
    run_dir = run_agentic("CS-06_Testing_Strategy_compiled.md")
    meta = json.loads((run_dir / "metadata.json").read_text())

    assert meta["architecture"] == "agentic"
    assert meta["prompt_id"] == "agentic_generate_wiki"
    assert meta["reviewer_prompt_id"] == "agentic_reviewer"
    assert meta["model"] == "anthropic/claude-sonnet-4-6"
    assert "CS-06_Testing_Strategy_compiled" in meta["artifact_id"]
    assert meta["artifact_type"] == "development_activity"
    # First-draft-passes scenario: 1 Writer call + 1 Reviewer call.
    assert meta["num_calls"] == 2
    assert meta["writer_calls"] == 1
    assert meta["reviewer_iterations"] == 1
    assert meta["reviewer_passed"] is True
    # Tokens summed across the two per-agent final summaries.
    assert meta["prompt_tokens"] == 1200 + 400
    assert meta["completion_tokens"] == 600 + 80
    assert meta["total_tokens"] == 1200 + 600 + 400 + 80
    # CL-05: cache token fields persist for §5.3 hit-rate analysis.
    assert meta["cache_read_input_tokens"] == 800 + 300
    assert meta["cache_creation_input_tokens"] == 200 + 100
    assert "timestamp" in meta
    assert "strands_metrics" in meta
    # Per-agent final summaries (one Writer total, one Reviewer total)
    # are persisted for audit. Strands accumulates per agent, so two
    # summaries is the correct shape regardless of how many calls each
    # agent received.
    assert len(meta["strands_metrics"]["per_agent_summaries"]) == 2


def test_writes_messages_json(mock_agents, results_dir):
    run_dir = run_agentic("CS-06_Testing_Strategy_compiled.md")
    messages = json.loads((run_dir / "messages.json").read_text())

    # 1 system + 2*k exemplar (CL-02) + 1 live user.
    assert len(messages) >= 2
    assert messages[0]["role"] == "system"
    assert messages[-1]["role"] == "user"


# ── Directory naming ────────────────────────────────────────────────────


def test_dir_name_contains_architecture_and_artifact(mock_agents, results_dir):
    run_dir = run_agentic("CS-06_Testing_Strategy_compiled.md")
    assert "agentic" in run_dir.name
    assert "CS-06" in run_dir.name


def test_run_tag_appended_to_dir_name(mock_agents, results_dir):
    run_dir = run_agentic("CS-06_Testing_Strategy_compiled.md", run_tag="v1")
    assert run_dir.name.endswith("_v1")


# ── Sampling from YAML defaults ─────────────────────────────────────


def test_sampling_defaults_from_yaml(mock_agents, results_dir):
    """agentic_generate_wiki.yaml has Claude Sonnet sampling params."""
    run_dir = run_agentic("CS-06_Testing_Strategy_compiled.md")
    meta = json.loads((run_dir / "metadata.json").read_text())
    assert meta["temperature"] == 0.3
    assert meta["max_tokens"] == 16384
    assert meta.get("top_p") is None
    assert meta.get("top_k") is None


def test_cli_overrides_yaml_sampling(mock_agents, results_dir):
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


def test_writer_create_agent_receives_yaml_params(mock_agents, results_dir):
    """The Writer (first _create_agent call) is built with the YAML
    sampling defaults."""
    run_agentic("CS-06_Testing_Strategy_compiled.md")
    # First create call is the Writer.
    writer_kwargs = mock_agents.create.call_args_list[0].kwargs
    assert writer_kwargs["model_id"] == "anthropic/claude-sonnet-4-6"
    assert writer_kwargs["temperature"] == 0.3
    assert writer_kwargs["max_tokens"] == 16384


def test_writer_create_agent_receives_overrides(mock_agents, results_dir):
    run_agentic(
        "CS-06_Testing_Strategy_compiled.md",
        temperature=0.5,
        max_tokens=1024,
        top_p=0.8,
        top_k=40,
    )
    writer_kwargs = mock_agents.create.call_args_list[0].kwargs
    assert writer_kwargs["temperature"] == 0.5
    assert writer_kwargs["max_tokens"] == 1024
    assert writer_kwargs["top_p"] == 0.8
    assert writer_kwargs["top_k"] == 40


# ── Support reports ─────────────────────────────────────────────────────


def test_support_report_artifact_type(mock_agents, results_dir):
    run_dir = run_agentic("CS-01_Archive_Backup_report.md")
    meta = json.loads((run_dir / "metadata.json").read_text())
    assert meta["artifact_type"] == "support_report"


# ── CL-04: concision directive on the Reviewer prompt ──────────────────


class TestConcisionDirective:
    """Verify the §4.2.3 CL-04 concision directive lives on the
    Reviewer (intermediate work) and not on the Writer (whose output
    is the final wiki entry, intentionally unconstrained)."""

    def test_reviewer_system_prompt_has_concision_block(self):
        from src.common.prompts import load_prompt

        reviewer = load_prompt("agentic_reviewer")
        sys_text = reviewer._messages[0]["content"].lower()
        assert "bullet" in sys_text, "directive must specify bullet-list format"
        assert "150" in sys_text, "directive must specify the 150-word cap"
        assert "none" in sys_text, "directive must specify the NONE empty marker"

    def test_reviewer_enumerates_three_checks(self):
        """The Reviewer prompt must still cover completeness,
        hallucinations, and attribution."""
        from src.common.prompts import load_prompt

        sys_text = load_prompt("agentic_reviewer")._messages[0]["content"].lower()
        assert "completeness" in sys_text
        assert "hallucination" in sys_text
        assert "attribution" in sys_text

    def test_writer_system_prompt_omits_review_step(self):
        """CL-06: the Writer no longer self-reviews — that's the
        Reviewer's responsibility."""
        from src.common.prompts import load_prompt

        writer_sys = load_prompt("agentic_generate_wiki")._messages[0]["content"].lower()
        # Writer should describe its own role; "reviewer" is mentioned
        # only as a collaborator, not as a self-step.
        assert "writer" in writer_sys
        # The Run-1 four-step "EXTRACT/DRAFT/REVIEW/REVISE" block
        # should be gone — REVIEW belongs to the Reviewer agent.
        assert "self-review" not in writer_sys


# ── CL-01: audience parameter persisted in metadata ────────────────────


class TestAudiencePersistence:
    """Verify the runner forwards the audience to render() and persists
    it in metadata.json, so every run is replayable from its metadata."""

    def test_default_audience_is_development(self, mock_agents, results_dir):
        run_dir = run_agentic("CS-06_Testing_Strategy_compiled.md")
        meta = json.loads((run_dir / "metadata.json").read_text())
        assert meta["audience"] == "development"

    def test_explicit_audience_recorded(self, mock_agents, results_dir):
        run_dir = run_agentic(
            "CS-06_Testing_Strategy_compiled.md",
            audience="marketing",
        )
        meta = json.loads((run_dir / "metadata.json").read_text())
        assert meta["audience"] == "marketing"

    def test_unknown_audience_raises(self, mock_agents, results_dir):
        with pytest.raises(KeyError):
            run_agentic(
                "CS-06_Testing_Strategy_compiled.md",
                audience="finance",
            )


# ── CL-02 / CL-05: input-prep helpers ──────────────────────────────────


class TestInputPrepHelpers:
    """Unit-tests for the (system, history, user) splitter and the
    cache-wrapping helpers."""

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

    def test_split_user_message_for_reviewer_marker(self):
        """CL-06: the Reviewer's user template uses a different marker
        ('Draft to review:') and the cache helper must split there."""
        from src.agentic.runner import (
            _REVIEWER_DRAFT_MARKER,
            _split_user_message_for_cache,
        )

        msg = (
            "Source artifact (X, type: Y):\n---\nBODY\n---\n\n"
            f"{_REVIEWER_DRAFT_MARKER}\n---\nDRAFT\n---\n\n"
            "Review it."
        )
        blocks = _split_user_message_for_cache(msg, marker=_REVIEWER_DRAFT_MARKER)
        assert len(blocks) == 3
        assert blocks[1] == {"cachePoint": {"type": "default"}}
        assert blocks[2]["text"].startswith(_REVIEWER_DRAFT_MARKER)


# ── CL-06: Writer/Reviewer loop topology and counting ──────────────────


class TestWriterReviewerLoop:
    """End-to-end coverage of the CL-06 Writer/Reviewer cycle: number
    of agent calls, iteration counting, and convergence flag."""

    @pytest.mark.parametrize(
        "mock_agents",
        [{
            # Writer: 1 call (initial draft); no revision because the
            # Reviewer passes immediately.
            "writer": [(_FAKE_WIKI, _writer_delta())],
            "reviewer": [("NONE", _reviewer_delta())],
        }],
        indirect=True,
    )
    def test_first_draft_passes(self, mock_agents, results_dir):
        run_dir = run_agentic("CS-06_Testing_Strategy_compiled.md")
        meta = json.loads((run_dir / "metadata.json").read_text())
        assert meta["reviewer_iterations"] == 1
        assert meta["writer_calls"] == 1
        assert meta["reviewer_passed"] is True
        assert meta["num_calls"] == 2  # 1 Writer + 1 Reviewer
        assert len(mock_agents.writer.calls) == 1
        assert len(mock_agents.reviewer.calls) == 1

    @pytest.mark.parametrize(
        "mock_agents",
        [{
            # Writer: initial draft + 1 revision = 2 calls.
            "writer": [
                ("## Summary\n\nDraft v1", _writer_delta()),
                ("## Summary\n\nDraft v2 (revised)", _writer_delta()),
            ],
            # Reviewer: flags an issue, then passes = 2 calls.
            "reviewer": [
                ("- Missing the deadline for #M-12.", _reviewer_delta()),
                ("NONE", _reviewer_delta()),
            ],
        }],
        indirect=True,
    )
    def test_one_revision_then_pass(self, mock_agents, results_dir):
        run_dir = run_agentic("CS-06_Testing_Strategy_compiled.md")
        meta = json.loads((run_dir / "metadata.json").read_text())
        assert meta["reviewer_iterations"] == 2
        assert meta["writer_calls"] == 2
        assert meta["reviewer_passed"] is True
        # 2 Writer + 2 Reviewer = 4 calls total.
        assert meta["num_calls"] == 4
        assert len(mock_agents.writer.calls) == 2
        assert len(mock_agents.reviewer.calls) == 2
        wiki = (run_dir / "wiki_entry.md").read_text()
        # The latest draft (Writer's second response) is what gets persisted.
        assert "Draft v2" in wiki
        # Token totals must reflect Strands' accumulating semantics:
        # 2 Writer calls × default delta + 2 Reviewer calls × default delta.
        # Default deltas: writer 1200 in / 600 out; reviewer 400 in / 80 out.
        assert meta["prompt_tokens"] == 2 * 1200 + 2 * 400
        assert meta["completion_tokens"] == 2 * 600 + 2 * 80

    @pytest.mark.parametrize(
        "mock_agents",
        [{
            # Reviewer never returns NONE; loop hits the cap.
            # With max_iterations=3 and no convergence, the runner
            # invokes Writer 3× (initial + 2 revisions) and Reviewer
            # 3× (one review per iteration). The loop exits without a
            # 3rd revision: there is no 4th Reviewer pass to verify
            # it, so revising once more would be wasteful.
            "writer": [
                ("## Summary\n\nDraft v1", _writer_delta()),
                ("## Summary\n\nDraft v2", _writer_delta()),
                ("## Summary\n\nDraft v3", _writer_delta()),
            ],
            "reviewer": [
                ("- Issue 1", _reviewer_delta()),
                ("- Issue 2", _reviewer_delta()),
                ("- Issue 3", _reviewer_delta()),
            ],
        }],
        indirect=True,
    )
    def test_max_iterations_cap_enforced(self, mock_agents, results_dir):
        run_dir = run_agentic(
            "CS-06_Testing_Strategy_compiled.md",
            max_iterations=3,
        )
        meta = json.loads((run_dir / "metadata.json").read_text())
        assert meta["reviewer_iterations"] == 3
        assert meta["writer_calls"] == 3
        assert meta["reviewer_passed"] is False
        assert meta["max_iterations"] == 3
        # Writer is invoked 3 times (initial + 2 revisions); Reviewer
        # 3 times. The runner skips the would-be 4th revision because
        # the iteration cap has been reached and no Reviewer pass is
        # available to verify it.
        assert len(mock_agents.writer.calls) == 3
        assert len(mock_agents.reviewer.calls) == 3

    def test_reviewer_passes_helper_accepts_decorations(self):
        """The 'NONE' sentinel match should tolerate trailing
        punctuation / markdown emphasis the model sometimes adds."""
        from src.agentic.runner import _reviewer_passes

        assert _reviewer_passes("NONE")
        assert _reviewer_passes("none")
        assert _reviewer_passes("**NONE**")
        assert _reviewer_passes("`NONE.`")
        assert _reviewer_passes("  NONE  ")
        assert not _reviewer_passes("- Issue 1\n- Issue 2")
        assert not _reviewer_passes("None of the issues remain.")


# ── CL-05: cache wrapping reaches the Strands agents ───────────────────


class TestCacheWrapping:
    """Verify both the Writer and Reviewer agents receive system and
    user content that carries cachePoint markers."""

    def test_writer_system_prompt_with_cachepoint(self, mock_agents, results_dir):
        run_agentic("CS-06_Testing_Strategy_compiled.md")
        writer_kwargs = mock_agents.create.call_args_list[0].kwargs
        sys_prompt = writer_kwargs["system_prompt"]
        assert isinstance(sys_prompt, list)
        assert "text" in sys_prompt[0]
        assert sys_prompt[-1] == {"cachePoint": {"type": "default"}}

    def test_reviewer_system_prompt_with_cachepoint(self, mock_agents, results_dir):
        run_agentic("CS-06_Testing_Strategy_compiled.md")
        reviewer_kwargs = mock_agents.create.call_args_list[1].kwargs
        sys_prompt = reviewer_kwargs["system_prompt"]
        assert isinstance(sys_prompt, list)
        assert "text" in sys_prompt[0]
        assert sys_prompt[-1] == {"cachePoint": {"type": "default"}}

    def test_writer_first_user_content_has_cachepoint(self, mock_agents, results_dir):
        run_agentic("CS-06_Testing_Strategy_compiled.md")
        prompt = mock_agents.writer.calls[0]
        assert isinstance(prompt, list)
        assert {"cachePoint": {"type": "default"}} in prompt
        # Source body precedes the cachePoint; instruction follows.
        cp_idx = prompt.index({"cachePoint": {"type": "default"}})
        assert "Source artifact" in prompt[cp_idx - 1]["text"]
        from src.agentic.runner import _USER_INSTRUCTION_MARKER
        assert _USER_INSTRUCTION_MARKER in prompt[cp_idx + 1]["text"]

    @pytest.mark.parametrize(
        "mock_agents",
        [{
            "writer": [(_FAKE_WIKI, _writer_delta())],
            "reviewer": [("NONE", _reviewer_delta())],
        }],
        indirect=True,
    )
    def test_reviewer_first_user_content_has_cachepoint(
        self, mock_agents, results_dir
    ):
        run_agentic("CS-06_Testing_Strategy_compiled.md")
        prompt = mock_agents.reviewer.calls[0]
        assert isinstance(prompt, list)
        assert {"cachePoint": {"type": "default"}} in prompt
        cp_idx = prompt.index({"cachePoint": {"type": "default"}})
        from src.agentic.runner import _REVIEWER_DRAFT_MARKER
        assert "Source artifact" in prompt[cp_idx - 1]["text"]
        assert _REVIEWER_DRAFT_MARKER in prompt[cp_idx + 1]["text"]


# ── CL-05: cache-aware cost estimation ─────────────────────────────────


class TestCachePricing:
    """``_estimate_cost`` must forward cache token fields to
    ``litellm.cost_per_token`` so the cache-read / cache-write rates
    apply correctly."""

    def test_estimate_cost_passes_cache_token_fields_to_litellm(self):
        pytest.importorskip("litellm")
        from src.agentic.runner import _estimate_cost

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
        pytest.importorskip("litellm")
        from src.agentic.runner import _estimate_cost

        with patch("litellm.cost_per_token", return_value=(0.001, 0.002)):
            cost = _estimate_cost(
                "anthropic/claude-sonnet-4-6",
                prompt_tokens=1000,
                completion_tokens=500,
            )
        assert cost == pytest.approx(0.003)


# ── CL-02: history forwarding (Writer only) ────────────────────────────


class TestExemplarHistoryRouting:
    """The Writer agent receives the audience-tailored exemplar
    history; the Reviewer (CL-06 sub-agent) does not."""

    def test_writer_receives_history(self, mock_agents, results_dir):
        run_agentic(
            "CS-06_Testing_Strategy_compiled.md",
            audience="development",
        )
        writer_kwargs = mock_agents.create.call_args_list[0].kwargs
        history = writer_kwargs["history"]
        # Two exemplars per audience -> 4 messages of history.
        assert len(history) == 4
        assert [m["role"] for m in history] == ["user", "assistant", "user", "assistant"]

    def test_reviewer_has_no_history(self, mock_agents, results_dir):
        run_agentic("CS-06_Testing_Strategy_compiled.md")
        reviewer_kwargs = mock_agents.create.call_args_list[1].kwargs
        # _create_agent is invoked with history=None for the Reviewer.
        assert reviewer_kwargs.get("history") is None

    def test_history_uses_correct_audience_exemplars(self, mock_agents, results_dir):
        """Verify the history reflects the requested audience's exemplars,
        not another audience's. Marketing-only schema headers must
        appear in the assistant turns."""
        run_agentic(
            "CS-06_Testing_Strategy_compiled.md",
            audience="marketing",
        )
        writer_kwargs = mock_agents.create.call_args_list[0].kwargs
        history = writer_kwargs["history"]
        history_text = " ".join(
            block["text"] for m in history for block in m["content"]
        )
        assert "## Outcome" in history_text
        assert "## Business impact" in history_text
        marketing_assistant_text = " ".join(
            block["text"]
            for m in history if m["role"] == "assistant"
            for block in m["content"]
        )
        assert "## Implementation detail" not in marketing_assistant_text
