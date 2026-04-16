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
        assert prompt.version == 1
        assert isinstance(prompt.model, str)

    def test_load_nonexistent_prompt_raises(self):
        with pytest.raises(FileNotFoundError):
            load_prompt("does_not_exist")

    def test_all_prompts_loadable(self):
        for meta in list_prompts():
            prompt = load_prompt(meta["id"])
            assert prompt.id == meta["id"]


class TestPromptRender:
    def test_render_fills_variables(self):
        prompt = load_prompt("pipeline_generate_wiki")
        messages = prompt.render(
            artifact_type="meeting_transcript",
            artifact_id="test-meeting",
            artifact_text="Some meeting text here.",
        )
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "test-meeting" in messages[1]["content"]
        assert "Some meeting text here." in messages[1]["content"]

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
        # Render with dummy values for all template vars
        kwargs = {var: f"test_{var}" for var in prompt.template_vars}
        messages = prompt.render(**kwargs)
        for msg in messages:
            assert "role" in msg, f"Missing 'role' in {prompt_id}"
            assert "content" in msg, f"Missing 'content' in {prompt_id}"
            assert msg["role"] in ("system", "user", "assistant")


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
