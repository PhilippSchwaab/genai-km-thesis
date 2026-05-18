"""
Canonical input/output contracts for the wiki-entry generator.

Both architectures (pipeline and agentic) route their core through:

    generate(source: SourceArtifact, ...) -> GenerationResult

Where :class:`SourceArtifact` captures the input (one source, or a
bundle of sources concatenated for a single prompt invocation) and
:class:`GenerationResult` captures the output plus minimal lineage
metadata (prompt ref, model, sampling, tokens, cost, timing, reviewer
state).

The contract is deliberately minimal — thesis-only fields. Production
extensions (multi-source citations, source ACL, tenant_id) are
additive and live in the work-fork CK schemas. See
``docs/production_fork_plan.md``.

Identifier conventions follow OpenLineage's namespace + name scheme,
expressed as a single URI per source (e.g. ``file:///data/anonymized/CS-06.md``).
``run_id`` is a UUIDv7 per RFC 9562 §5.7 — time-sortable, B-tree-friendly.

The legacy ``metadata.json`` shape persisted by each runner is **not**
this contract — it has richer thesis-eval-specific fields. This contract
is what the runner returns in code and what is persisted as ``result.json``
alongside the legacy metadata.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

_SCHEMA_DIR = Path(__file__).resolve().parent / "schemas"
_SOURCE_SCHEMA_PATH = _SCHEMA_DIR / "source_artifact.schema.json"
_RESULT_SCHEMA_PATH = _SCHEMA_DIR / "generation_result.schema.json"


# ── UUIDv7 shim (RFC 9562 §5.7) ──────────────────────────────────────────
# For (python-3.14): delete this shim and replace with
#     from uuid import uuid7
# UUIDv7 landed in the stdlib in Python 3.14. This repo is currently
# pinned to 3.13 because LiteLLM still excludes 3.14 (uvloop
# incompatibility, BerriAI/litellm#26343, May 2026). When the Python
# pin moves to 3.14, drop this function and update the import in
# :func:`new_run_id` to use the stdlib version. No behavioural change —
# the wire format is identical.

def uuid7() -> uuid.UUID:
    """Generate a UUIDv7 per RFC 9562 §5.7.

    128-bit identifier: 48-bit big-endian Unix-time-millisecond timestamp,
    followed by 4 bits version (0b0111) + 12 bits random, 2 bits variant
    (0b10) + 62 bits random. Sortable by creation time, safe for B-tree
    indexes, globally unique without coordination.

    Drop-in replacement target: :func:`uuid.uuid7` in Python ≥ 3.14.
    """
    timestamp_ms = time.time_ns() // 1_000_000
    rand = os.urandom(10)
    b = bytearray(16)
    # 48-bit big-endian Unix-ms timestamp (bytes 0..5)
    b[0] = (timestamp_ms >> 40) & 0xFF
    b[1] = (timestamp_ms >> 32) & 0xFF
    b[2] = (timestamp_ms >> 24) & 0xFF
    b[3] = (timestamp_ms >> 16) & 0xFF
    b[4] = (timestamp_ms >>  8) & 0xFF
    b[5] = timestamp_ms & 0xFF
    # byte 6: version (0x70) | 4 random bits
    b[6] = 0x70 | (rand[0] & 0x0F)
    # byte 7: 8 random bits
    b[7] = rand[1]
    # byte 8: variant (0b10xxxxxx) — top two bits 1,0 then 6 random
    b[8] = 0x80 | (rand[2] & 0x3F)
    # bytes 9..15: 7 fully-random bytes
    b[9:16] = rand[3:10]
    return uuid.UUID(bytes=bytes(b))


def new_run_id() -> str:
    """Return a fresh UUIDv7 as a string (canonical hyphenated form)."""
    return str(uuid7())


# ── Helpers ──────────────────────────────────────────────────────────────

def content_hash(content: str) -> str:
    """sha256 hex digest of the given text, prefixed with ``sha256:``.

    The prefix makes the algorithm self-describing in the on-disk JSON,
    which keeps room to add ``sha512:``-prefixed hashes later without a
    schema migration.
    """
    return "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest()


def utc_now_iso() -> str:
    """Current UTC time in ISO 8601 with seconds precision."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ── Dataclasses ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SourceArtifact:
    """The input to :func:`generate` — a single source identified by URI.

    For thesis runs, the URI is typically
    ``file:///data/anonymized/<filename>`` (single file) or
    ``bundle:///<comma-joined-filenames>`` (multi-file bundles, rare in
    the thesis but supported by the file-based loader). ``content`` is
    the text the LLM actually sees (post-concatenation for bundles).
    """

    source_uri: str
    source_content_hash: str
    content: str
    audience: str

    @classmethod
    def from_text(
        cls,
        content: str,
        *,
        source_uri: str,
        audience: str,
    ) -> "SourceArtifact":
        """Build a SourceArtifact from raw text, computing the hash."""
        return cls(
            source_uri=source_uri,
            source_content_hash=content_hash(content),
            content=content,
            audience=audience,
        )

    def to_dict(self) -> dict:
        """JSON-friendly representation matching the schema."""
        return {
            "source": {
                "uri": self.source_uri,
                "content_hash": self.source_content_hash,
            },
            "content": self.content,
            "audience": self.audience,
        }


@dataclass(frozen=True)
class Generation:
    """Lineage block — what produced the wiki entry and at what cost.

    ``latency_seconds`` is the monotonic wall-clock measurement of the
    generation (via :func:`time.perf_counter`). The ISO ``started_at`` /
    ``ended_at`` timestamps are rounded to the second and intended for
    human-readable lineage; they are not suitable for sub-second latency
    derivation, which is why latency is carried separately.
    """

    architecture: str             # "pipeline" | "agentic"
    prompt_id: str
    prompt_version: int
    model: str
    sampling: dict[str, Any]      # temperature, max_tokens, top_p, top_k
    tokens: dict[str, int]        # input, output, cache_read, cache_creation
    cost_usd: float
    latency_seconds: float
    started_at: str               # ISO 8601 UTC
    ended_at: str                 # ISO 8601 UTC
    reviewer_iterations: int = 0
    reviewer_passed: bool | None = None


@dataclass(frozen=True)
class GenerationResult:
    """Output of :func:`generate` — the wiki entry plus lineage metadata."""

    run_id: str                   # UUIDv7 canonical string
    source_uri: str
    source_content_hash: str
    wiki_entry_markdown: str
    generation: Generation

    def to_dict(self) -> dict:
        """JSON-friendly representation matching the schema."""
        return {
            "run_id": self.run_id,
            "source": {
                "uri": self.source_uri,
                "content_hash": self.source_content_hash,
            },
            "wiki_entry_markdown": self.wiki_entry_markdown,
            "generation": asdict(self.generation),
        }


# ── Validators ───────────────────────────────────────────────────────────
# Eagerly loaded at module import — the schemas are small (<2 KB each)
# and both runners + every test that touches the contract need them, so
# lazy init buys nothing and forces the type system into an Optional
# that's awkward to narrow. Fail-fast at import is also preferable here:
# a missing schema file is a packaging error, not a runtime condition.


def _load_validator(path: Path) -> Draft202012Validator:
    with open(path) as f:
        schema = json.load(f)
    return Draft202012Validator(
        schema, format_checker=Draft202012Validator.FORMAT_CHECKER
    )


_SOURCE_VALIDATOR: Draft202012Validator = _load_validator(_SOURCE_SCHEMA_PATH)
_RESULT_VALIDATOR: Draft202012Validator = _load_validator(_RESULT_SCHEMA_PATH)


def validate_source(payload: dict) -> None:
    """Validate a SourceArtifact dict against the schema; raises on error."""
    _SOURCE_VALIDATOR.validate(payload)


def validate_result(payload: dict) -> None:
    """Validate a GenerationResult dict against the schema; raises on error."""
    _RESULT_VALIDATOR.validate(payload)


# ── URI helpers used by both runners ─────────────────────────────────────

def file_source_uri(filenames: list[str] | tuple[str, ...]) -> str:
    """Build a source URI from one or more anonymized filenames.

    Single file → ``file:///data/anonymized/<filename>``.
    Multi-file → ``bundle:///`` + comma-joined filenames. The
    ``bundle://`` scheme is honest about the source being a concatenation
    of several files; production multi-source generations will use
    ``cited_sources[]`` instead and this fallback won't be needed.
    """
    if len(filenames) == 1:
        return f"file:///data/anonymized/{filenames[0]}"
    return "bundle:///" + ",".join(filenames)
