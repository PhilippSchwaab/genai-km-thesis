"""
Prompt loader for the versioned prompt library.

Loads YAML prompt files from prompts/ and returns messages formatted
for litellm.completion().

Usage:
    from src.common.prompts import load_prompt, load_artifacts

    # Load artifacts by filename (resolved from data/anonymized/)
    bundle = load_artifacts("sample_meeting.txt")

    # Or multiple files at once
    bundle = load_artifacts("sample_meeting.txt", "chat_sprint42.txt")

    # Load prompt and render with the bundle
    prompt = load_prompt("pipeline_generate_wiki")
    messages = prompt.render(
        artifact_type=bundle.artifact_type,
        artifact_id=bundle.artifact_id,
        artifact_text=bundle.artifact_text,
    )

    response = litellm.completion(model=prompt.model, messages=messages)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_PROMPTS_DIR = _PROJECT_ROOT / "prompts"
_ANONYMIZED_DIR = _PROJECT_ROOT / "data" / "anonymized"

# Map file-stem conventions to artifact types.
# Extend this as new source types are added to data/anonymized/.
_TYPE_HINTS: dict[str, str] = {
    "meeting": "meeting_transcript",
    "chat": "chat_log",
    "commit": "commit_history",
    "commits": "commit_history",
    "compiled": "development_activity",
    "report": "support_report",
    "wiki": "wiki_page",
    "workitem": "work_item",
    "notes": "personal_notes",
}


@dataclass(frozen=True)
class Prompt:
    """A loaded prompt template with metadata."""

    id: str
    architecture: str
    version: int
    model: str
    description: str
    _messages: list[dict[str, str]]

    def render(self, **kwargs: str) -> list[dict[str, str]]:
        """Fill template variables and return litellm-ready messages."""
        return [
            {"role": m["role"], "content": m["content"].format(**kwargs)}
            for m in self._messages
        ]

    @property
    def template_vars(self) -> set[str]:
        """Return the set of {variable} names used across all messages."""
        vars_found: set[str] = set()
        for m in self._messages:
            vars_found.update(re.findall(r"\{(\w+)}", m["content"]))
        return vars_found


def load_prompt(prompt_id: str) -> Prompt:
    """Load a prompt by its id (filename without extension)."""
    path = _PROMPTS_DIR / f"{prompt_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Prompt '{prompt_id}' not found at {path}")

    with open(path) as f:
        data = yaml.safe_load(f)

    meta = data["meta"]
    return Prompt(
        id=meta["id"],
        architecture=meta["architecture"],
        version=meta["version"],
        model=meta["model"],
        description=meta["description"],
        _messages=data["messages"],
    )


def _guess_artifact_type(filename: str) -> str:
    """Infer artifact_type from filename prefix (e.g. 'sample_meeting' → 'meeting_transcript')."""
    name = filename.lower()
    for hint, atype in _TYPE_HINTS.items():
        if hint in name:
            return atype
    return "personal_notes"  # safe fallback


@dataclass(frozen=True)
class ArtifactBundle:
    """The result of loading one or more artifact files."""

    artifacts: list[dict[str, str]]  # each has artifact_id, artifact_type, text

    @property
    def artifact_text(self) -> str:
        """Formatted text block for prompt injection."""
        sections = []
        for i, a in enumerate(self.artifacts, 1):
            sections.append(
                f"[Artifact {i}: {a['artifact_id']} ({a['artifact_type']})]\n"
                f"{a['text']}"
            )
        return "\n\n---\n\n".join(sections)

    @property
    def artifact_id(self) -> str:
        return ", ".join(a["artifact_id"] for a in self.artifacts)

    @property
    def artifact_type(self) -> str:
        types = {a["artifact_type"] for a in self.artifacts}
        return types.pop() if len(types) == 1 else "multiple"


def load_artifacts(*paths: str | Path) -> ArtifactBundle:
    """Load artifact files from data/anonymized/ (or absolute paths).

    Accepts filenames (looked up in data/anonymized/), relative paths,
    or absolute paths. Artifact type is inferred from the filename.

    Usage:
        # Just pass filenames — they're resolved from data/anonymized/
        bundle = load_artifacts("sample_meeting.txt", "chat_sprint42.txt")

        prompt = load_prompt("pipeline_generate_wiki")
        messages = prompt.render(
            artifact_type=bundle.artifact_type,
            artifact_id=bundle.artifact_id,
            artifact_text=bundle.artifact_text,
        )
    """
    artifacts = []
    for p in paths:
        path = Path(p)
        # If just a filename, resolve from data/anonymized/
        if not path.is_absolute() and not path.exists():
            path = _ANONYMIZED_DIR / path
        text = path.read_text(encoding="utf-8")
        artifact_id = path.stem
        artifact_type = _guess_artifact_type(path.stem)
        artifacts.append({
            "artifact_id": artifact_id,
            "artifact_type": artifact_type,
            "text": text,
        })
    return ArtifactBundle(artifacts=artifacts)


def list_prompts() -> list[dict[str, str | int]]:
    """Return metadata for all prompts in the library."""
    prompts = []
    for path in sorted(_PROMPTS_DIR.glob("*.yaml")):
        with open(path) as f:
            data = yaml.safe_load(f)
        meta = data["meta"]
        prompts.append({
            "id": meta["id"],
            "architecture": meta["architecture"],
            "version": meta["version"],
            "model": meta["model"],
        })
    return prompts
