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
    """A loaded prompt template with metadata.

    Prompts may declare per-audience scaffolding under ``meta.audiences``.
    Each audience entry is a dict with at least a ``schema`` key whose
    value is the section structure spliced into the rendered user turn.
    Each audience may additionally declare an ``exemplars`` list of
    ``{artifact_id, artifact_type, source, entry}`` items spliced as
    user/assistant turns before the live user request (CL-02, thesis
    §4.2.3). Prompts without an ``audiences`` block render unchanged
    from earlier versions; the audience parameter is opt-in and
    orthogonal to all other rendering inputs.
    """

    id: str
    architecture: str
    version: int
    model: str
    description: str
    sampling: dict[str, float]
    audiences: dict[str, dict]   # name -> {"schema": "...", "exemplars": [...]}
    _messages: list[dict[str, str]]

    def render(
        self,
        *,
        audience: str | None = None,
        **kwargs: str,
    ) -> list[dict[str, str]]:
        """Fill template variables and return litellm-ready messages.

        If ``audience`` is provided, the audience's ``schema`` is
        substituted into the ``{audience_schema}`` placeholder and the
        audience name into the ``{audience}`` placeholder. If the
        audience also declares exemplars, each is spliced as a
        user/assistant pair before the live user turn, with the
        exemplar's user message rendered through the **same** user
        template the live request uses (so the model sees identical
        wrappers across exemplars and the live turn — format-consistent
        few-shot, per Min et al. EMNLP 2022). Raises:

        - ``ValueError`` if the prompt has no ``audiences`` block.
        - ``KeyError`` if the audience name is not declared.
        """
        if audience is not None:
            if not self.audiences:
                raise ValueError(
                    f"Prompt {self.id!r} does not declare audiences; "
                    f"cannot render with audience={audience!r}."
                )
            if audience not in self.audiences:
                raise KeyError(
                    f"Unknown audience {audience!r} for prompt "
                    f"{self.id!r}; declared audiences: "
                    f"{sorted(self.audiences)}."
                )
            kwargs["audience"] = audience
            kwargs["audience_schema"] = self.audiences[audience]["schema"]

        base = [
            {"role": m["role"], "content": m["content"].format(**kwargs)}
            for m in self._messages
        ]

        if audience is None:
            return base
        exemplars = self.audiences[audience].get("exemplars", []) or []
        if not exemplars:
            return base

        # Render each exemplar through the live user template so the
        # model sees the same wrapper for exemplars and the live turn.
        user_template = next(
            m["content"] for m in self._messages if m["role"] == "user"
        )
        schema = self.audiences[audience]["schema"]
        exemplar_messages: list[dict[str, str]] = []
        for ex in exemplars:
            user_content = user_template.format(
                audience=audience,
                audience_schema=schema,
                artifact_id=ex.get("artifact_id", "exemplar"),
                artifact_type=ex.get("artifact_type", "example"),
                artifact_text=ex["source"],
            )
            exemplar_messages.append({"role": "user", "content": user_content})
            exemplar_messages.append({"role": "assistant", "content": ex["entry"]})

        # Splice the exemplar pairs between the system message(s) and
        # the live user turn. The live user turn is the first user
        # message in `base` after the substitution above.
        live_user_idx = next(
            i for i, m in enumerate(base) if m["role"] == "user"
        )
        return base[:live_user_idx] + exemplar_messages + base[live_user_idx:]

    @property
    def template_vars(self) -> set[str]:
        """Return the set of {variable} names used across all messages."""
        vars_found: set[str] = set()
        for m in self._messages:
            vars_found.update(re.findall(r"\{(\w+)}", m["content"]))
        return vars_found

    @property
    def audience_names(self) -> list[str]:
        """Sorted list of declared audience names (empty if none)."""
        return sorted(self.audiences)


def load_prompt(prompt_id: str) -> Prompt:
    """Load a prompt by its id (filename without extension)."""
    path = _PROMPTS_DIR / f"{prompt_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Prompt '{prompt_id}' not found at {path}")

    with open(path) as f:
        data = yaml.safe_load(f)

    meta = data["meta"]
    audiences = meta.get("audiences", {}) or {}
    # Validate each audience entry has the expected shape so misconfigured
    # YAMLs fail at load time rather than at render time.
    for name, body in audiences.items():
        if not isinstance(body, dict) or "schema" not in body:
            raise ValueError(
                f"Prompt {prompt_id!r} audience {name!r} must be a "
                f"mapping with a 'schema' key (got {type(body).__name__})."
            )
        for i, ex in enumerate(body.get("exemplars") or []):
            if not isinstance(ex, dict) or "source" not in ex or "entry" not in ex:
                raise ValueError(
                    f"Prompt {prompt_id!r} audience {name!r} exemplar "
                    f"#{i} must be a mapping with 'source' and 'entry' "
                    f"keys (CL-02 schema)."
                )
    return Prompt(
        id=meta["id"],
        architecture=meta["architecture"],
        version=meta["version"],
        model=meta["model"],
        description=meta["description"],
        sampling=meta.get("sampling", {}),
        audiences=audiences,
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
