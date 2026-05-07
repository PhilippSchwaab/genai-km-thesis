"""Tests for the prompt loader and artifact bundler."""

import pytest

from src.common.prompts import (
    ArtifactBundle,
    Prompt,
    load_artifacts,
    load_prompt,
    list_prompts,
    _guess_artifact_type,
)


class TestLoadPrompt:
    def test_load_existing_prompt(self):
        prompt = load_prompt("pipeline_generate_wiki")
        assert prompt.id == "pipeline_generate_wiki"
        assert prompt.architecture == "pipeline"
        assert prompt.version == 2
        assert isinstance(prompt.model, str)

    def test_load_nonexistent_prompt_raises(self):
        with pytest.raises(FileNotFoundError):
            load_prompt("does_not_exist")

    def test_all_prompts_loadable(self):
        for meta in list_prompts():
            prompt = load_prompt(meta["id"])
            assert prompt.id == meta["id"]

    def test_sampling_loaded_from_yaml(self):
        prompt = load_prompt("pipeline_generate_wiki")
        assert isinstance(prompt.sampling, dict)
        assert prompt.sampling["temperature"] == 0.3
        assert "top_p" not in prompt.sampling
        assert "top_k" not in prompt.sampling

    def test_sampling_empty_when_missing(self):
        """Prompts without a sampling block get an empty dict."""
        # All our prompts now have sampling, but the code handles missing gracefully.
        prompt = load_prompt("pipeline_generate_wiki")
        assert isinstance(prompt.sampling, dict)


class TestPromptRender:
    def test_render_fills_variables(self):
        prompt = load_prompt("pipeline_generate_wiki")
        messages = prompt.render(
            audience="development",
            artifact_type="meeting_transcript",
            artifact_id="test-meeting",
            artifact_text="Some meeting text here.",
        )
        # 1 system + 2*k exemplar + 1 live user (k=2 → 6 total).
        assert len(messages) >= 2
        assert messages[0]["role"] == "system"
        assert messages[-1]["role"] == "user"
        # Live values appear only in the final user turn.
        assert "test-meeting" in messages[-1]["content"]
        assert "Some meeting text here." in messages[-1]["content"]

    def test_render_missing_variable_raises(self):
        prompt = load_prompt("pipeline_generate_wiki")
        with pytest.raises(KeyError):
            prompt.render(artifact_type="meeting_transcript")

    def test_template_vars_detected(self):
        prompt = load_prompt("pipeline_generate_wiki")
        assert "artifact_text" in prompt.template_vars
        assert "artifact_id" in prompt.template_vars
        assert "artifact_type" in prompt.template_vars


class TestPromptMessagesFormat:
    """Verify prompts produce messages compatible with litellm.completion()."""

    @pytest.mark.parametrize("prompt_id", [p["id"] for p in list_prompts()])
    def test_messages_have_role_and_content(self, prompt_id):
        prompt = load_prompt(prompt_id)
        # Render with dummy values for all template vars; audience-aware
        # prompts need the audience kwarg as well, since the {audience}
        # and {audience_schema} placeholders are filled by render() not
        # by the **kwargs path.
        kwargs = {var: f"test_{var}" for var in prompt.template_vars}
        kwargs.pop("audience", None)
        kwargs.pop("audience_schema", None)
        if prompt.audiences:
            messages = prompt.render(audience=prompt.audience_names[0], **kwargs)
        else:
            messages = prompt.render(**kwargs)
        for msg in messages:
            assert "role" in msg, f"Missing 'role' in {prompt_id}"
            assert "content" in msg, f"Missing 'content' in {prompt_id}"
            assert msg["role"] in ("system", "user", "assistant")


# ── CL-01: audience parameter ───────────────────────────────────────────


class TestAudiences:
    """The CL-01 audience parameter: a configurable section schema
    selected per render() call, declared declaratively in the prompt
    YAML's `meta.audiences` block. Tests cover the loader contract,
    the render() routing, and backward compatibility for prompts that
    do not declare an `audiences` block."""

    def test_generation_prompts_declare_three_audiences(self):
        for prompt_id in ("pipeline_generate_wiki", "agentic_generate_wiki"):
            prompt = load_prompt(prompt_id)
            assert set(prompt.audiences) == {
                "marketing", "development", "architect"
            }, f"{prompt_id} audience set mismatch"

    def test_each_audience_has_schema(self):
        prompt = load_prompt("pipeline_generate_wiki")
        for name, body in prompt.audiences.items():
            assert "schema" in body, f"{name} missing schema"
            assert body["schema"].strip(), f"{name} schema is empty"

    def test_audience_names_property_sorted(self):
        prompt = load_prompt("pipeline_generate_wiki")
        assert prompt.audience_names == sorted(prompt.audiences)

    def test_render_substitutes_selected_schema(self):
        prompt = load_prompt("pipeline_generate_wiki")
        marketing = prompt.render(
            audience="marketing",
            artifact_type="meeting_transcript",
            artifact_id="x",
            artifact_text="…",
        )
        development = prompt.render(
            audience="development",
            artifact_type="meeting_transcript",
            artifact_id="x",
            artifact_text="…",
        )
        marketing_user = marketing[-1]["content"]
        development_user = development[-1]["content"]
        # Audience name appears in the rendered user turn.
        assert "marketing" in marketing_user
        assert "development" in development_user
        # Schemas differ between audiences.
        assert marketing_user != development_user
        # Marketing schema-specific markers come through; development ones don't.
        assert "Outcome" in marketing_user
        assert "Outcome" not in development_user

    def test_render_unknown_audience_raises(self):
        prompt = load_prompt("pipeline_generate_wiki")
        with pytest.raises(KeyError):
            prompt.render(
                audience="finance",
                artifact_type="meeting_transcript",
                artifact_id="x",
                artifact_text="…",
            )

    def test_render_audience_against_prompt_without_audiences_raises(self):
        # Eval prompts intentionally do not declare audiences; passing one
        # to render() must error rather than silently substituting nothing.
        prompt = load_prompt("eval_kip_scorer")
        assert prompt.audiences == {}
        with pytest.raises(ValueError):
            prompt.render(audience="marketing", kip_text="…", wiki_entry="…")

    def test_render_without_audience_works_for_audience_less_prompt(self):
        prompt = load_prompt("eval_kip_scorer")
        kwargs = {var: f"test_{var}" for var in prompt.template_vars}
        messages = prompt.render(**kwargs)
        assert len(messages) >= 1


# ── CL-02: few-shot exemplars per audience ──────────────────────────────


class TestExemplars:
    """The CL-02 few-shot exemplars: synthetic (source, entry) pairs
    declared per audience under `meta.audiences.<name>.exemplars`,
    spliced as user/assistant turns before the live user request. The
    exemplar user message uses the **same** user-template wrapper as
    the live request so the model sees a format-consistent few-shot
    history (Min et al. EMNLP 2022 demonstrate that format consistency
    is one of the load-bearing properties of few-shot prompting)."""

    def test_each_audience_declares_two_exemplars(self):
        for prompt_id in ("pipeline_generate_wiki", "agentic_generate_wiki"):
            prompt = load_prompt(prompt_id)
            for audience, body in prompt.audiences.items():
                exemplars = body.get("exemplars") or []
                assert len(exemplars) == 2, (
                    f"{prompt_id}/{audience} must declare exactly 2 "
                    f"exemplars, got {len(exemplars)}"
                )

    def test_exemplar_source_and_entry_present(self):
        prompt = load_prompt("pipeline_generate_wiki")
        for audience, body in prompt.audiences.items():
            for i, ex in enumerate(body["exemplars"]):
                assert ex["source"].strip(), f"{audience}#{i} empty source"
                assert ex["entry"].strip(), f"{audience}#{i} empty entry"
                assert "artifact_id" in ex, f"{audience}#{i} missing artifact_id"
                assert "artifact_type" in ex, f"{audience}#{i} missing artifact_type"

    def test_render_splices_exemplar_pairs(self):
        """With k=2 exemplars, render output is 1 system + 2*k user/asst
        + 1 live user = 6 messages, in that order."""
        prompt = load_prompt("pipeline_generate_wiki")
        messages = prompt.render(
            audience="development",
            artifact_type="support_report",
            artifact_id="LIVE",
            artifact_text="LIVE BODY",
        )
        assert len(messages) == 6
        roles = [m["role"] for m in messages]
        assert roles == ["system", "user", "assistant", "user", "assistant", "user"]

    def test_exemplar_user_uses_same_wrapper_as_live_user(self):
        """Format-consistency check: the exemplar user message contains
        the same fixed wrapper substrings as the live user message.
        Markers chosen to be unbroken across YAML literal-block lines."""
        prompt = load_prompt("pipeline_generate_wiki")
        messages = prompt.render(
            audience="development",
            artifact_type="support_report",
            artifact_id="LIVE",
            artifact_text="LIVE BODY",
        )
        live_user = messages[-1]["content"]
        first_exemplar_user = messages[1]["content"]
        for marker in (
            "Source artifact (",
            "Convert the source artifact above",
            "tailored for the development audience",
            "## Summary",
        ):
            assert marker in live_user, f"missing in live: {marker!r}"
            assert marker in first_exemplar_user, f"missing in exemplar: {marker!r}"

    def test_live_user_appears_last(self):
        prompt = load_prompt("pipeline_generate_wiki")
        messages = prompt.render(
            audience="development",
            artifact_type="support_report",
            artifact_id="LIVE_ARTIFACT_ID",
            artifact_text="LIVE_BODY_MARKER",
        )
        # Only the LAST user turn carries the live artifact body.
        assert "LIVE_BODY_MARKER" in messages[-1]["content"]
        for m in messages[:-1]:
            assert "LIVE_BODY_MARKER" not in m["content"]

    def test_exemplar_count_matches_audience(self):
        """Different audiences route to their own exemplar sets, not
        a shared/cached list."""
        prompt = load_prompt("pipeline_generate_wiki")
        marketing_msgs = prompt.render(
            audience="marketing",
            artifact_type="support_report",
            artifact_id="L",
            artifact_text="b",
        )
        architect_msgs = prompt.render(
            audience="architect",
            artifact_type="support_report",
            artifact_id="L",
            artifact_text="b",
        )
        # Both have 2 exemplars but different content.
        assert marketing_msgs[2]["content"] != architect_msgs[2]["content"]

    def test_load_prompt_rejects_malformed_exemplar(self, tmp_path, monkeypatch):
        """Loader-time validation: a missing 'source' or 'entry' key
        must fail at load_prompt(), not silently at render time."""
        bad = tmp_path / "bad_prompt.yaml"
        bad.write_text(
            "meta:\n"
            "  id: bad_prompt\n"
            "  architecture: pipeline\n"
            "  version: 1\n"
            "  model: anthropic/claude-sonnet-4-6\n"
            "  description: malformed exemplar test\n"
            "  audiences:\n"
            "    development:\n"
            "      schema: '## H'\n"
            "      exemplars:\n"
            "        - artifact_id: x\n"
            "          source: 's'\n"  # missing 'entry'
            "messages:\n"
            "  - role: user\n"
            "    content: '{audience} {audience_schema} {artifact_text}'\n",
            encoding="utf-8",
        )
        monkeypatch.setattr("src.common.prompts._PROMPTS_DIR", tmp_path)
        with pytest.raises(ValueError):
            load_prompt("bad_prompt")


class TestGuessArtifactType:
    def test_meeting(self):
        assert _guess_artifact_type("sample_meeting") == "meeting_transcript"

    def test_chat(self):
        assert _guess_artifact_type("chat_sprint42") == "chat_log"

    def test_commits(self):
        assert _guess_artifact_type("commits_q1") == "commit_history"

    def test_unknown_falls_back(self):
        assert _guess_artifact_type("random_file") == "personal_notes"


class TestLoadArtifacts:
    def test_load_single_file(self):
        bundle = load_artifacts("CS-06_Testing_Strategy_compiled.md")
        assert len(bundle.artifacts) == 1
        assert "CS-06" in bundle.artifact_id
        assert bundle.artifact_type == "development_activity"
        assert len(bundle.artifact_text) > 0

    def test_load_nonexistent_raises(self):
        with pytest.raises(FileNotFoundError):
            load_artifacts("does_not_exist.txt")


class TestArtifactBundle:
    def test_single_type(self):
        bundle = ArtifactBundle(artifacts=[
            {"artifact_id": "a", "artifact_type": "chat_log", "text": "hello"},
        ])
        assert bundle.artifact_type == "chat_log"

    def test_mixed_types(self):
        bundle = ArtifactBundle(artifacts=[
            {"artifact_id": "a", "artifact_type": "chat_log", "text": "hello"},
            {"artifact_id": "b", "artifact_type": "meeting_transcript", "text": "world"},
        ])
        assert bundle.artifact_type == "multiple"

    def test_combined_ids(self):
        bundle = ArtifactBundle(artifacts=[
            {"artifact_id": "a", "artifact_type": "chat_log", "text": "hello"},
            {"artifact_id": "b", "artifact_type": "chat_log", "text": "world"},
        ])
        assert bundle.artifact_id == "a, b"

    def test_artifact_text_formatting(self):
        bundle = ArtifactBundle(artifacts=[
            {"artifact_id": "a", "artifact_type": "chat_log", "text": "hello"},
            {"artifact_id": "b", "artifact_type": "chat_log", "text": "world"},
        ])
        text = bundle.artifact_text
        assert "[Artifact 1: a (chat_log)]" in text
        assert "[Artifact 2: b (chat_log)]" in text
        assert "---" in text
