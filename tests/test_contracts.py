"""Tests for the SourceArtifact / GenerationResult contract module."""

import time
import uuid as _uuid_stdlib

import pytest
from jsonschema import ValidationError

from src.common.contracts import (
    Generation,
    GenerationResult,
    SourceArtifact,
    content_hash,
    file_source_uri,
    new_run_id,
    utc_now_iso,
    uuid7,
    validate_result,
    validate_source,
)


# ── UUIDv7 shim ────────────────────────────────────────────────────────


def test_uuid7_returns_uuid_object():
    assert isinstance(uuid7(), _uuid_stdlib.UUID)


def test_uuid7_version_is_7():
    """RFC 9562 §5.7 mandates version 7 in the high nibble of byte 6."""
    u = uuid7()
    assert u.version == 7
    # Variant is RFC 9562 / 4122 (top two bits of byte 8 are 0b10).
    assert (u.bytes[8] & 0xC0) == 0x80


def test_uuid7_is_time_ordered_within_a_run():
    """Two UUIDv7s generated milliseconds apart sort in creation order."""
    a = uuid7()
    time.sleep(0.005)  # 5 ms guarantees a different timestamp bucket
    b = uuid7()
    assert a.int < b.int


def test_uuid7_timestamp_matches_wall_clock():
    """The 48-bit high prefix encodes Unix-time-ms; verify it's now-ish."""
    before_ms = time.time_ns() // 1_000_000
    u = uuid7()
    after_ms = time.time_ns() // 1_000_000
    extracted = int.from_bytes(u.bytes[:6], "big")
    assert before_ms <= extracted <= after_ms


def test_new_run_id_is_canonical_uuid_string():
    rid = new_run_id()
    # Round-trips through uuid parsing; the parsed uuid is version 7.
    assert _uuid_stdlib.UUID(rid).version == 7
    # Canonical string form (8-4-4-4-12)
    assert len(rid) == 36
    assert rid.count("-") == 4


# ── content_hash ───────────────────────────────────────────────────────


def test_content_hash_is_prefixed_sha256():
    h = content_hash("hello world")
    assert h.startswith("sha256:")
    assert len(h) == len("sha256:") + 64  # 64 hex chars


def test_content_hash_is_deterministic():
    assert content_hash("foo") == content_hash("foo")
    assert content_hash("foo") != content_hash("bar")


def test_content_hash_known_vector():
    # Known sha256 of "hello\n" — sanity check that we're hashing UTF-8 bytes.
    expected = "sha256:5891b5b522d5df086d0ff0b110fbd9d21bb4fc7163af34d08286a2e846f6be03"
    assert content_hash("hello\n") == expected


# ── file_source_uri ────────────────────────────────────────────────────


def test_file_source_uri_single():
    uri = file_source_uri(["CS-06_Testing_Strategy_compiled.md"])
    assert uri == "file:///data/anonymized/CS-06_Testing_Strategy_compiled.md"


def test_file_source_uri_multi_uses_bundle_scheme():
    uri = file_source_uri(["a.md", "b.md"])
    assert uri == "bundle:///a.md,b.md"


# ── SourceArtifact ─────────────────────────────────────────────────────


def test_source_artifact_from_text_computes_hash():
    src = SourceArtifact.from_text(
        "the body",
        source_uri="file:///data/anonymized/x.md",
        audience="development",
    )
    assert src.content == "the body"
    assert src.source_uri == "file:///data/anonymized/x.md"
    assert src.source_content_hash == content_hash("the body")
    assert src.audience == "development"


def test_source_artifact_to_dict_round_trips_and_validates():
    src = SourceArtifact.from_text(
        "body",
        source_uri="file:///data/anonymized/x.md",
        audience="architect",
    )
    payload = src.to_dict()
    # Shape matches the schema's nested `source` object
    assert payload["source"]["uri"] == src.source_uri
    assert payload["source"]["content_hash"] == src.source_content_hash
    assert payload["content"] == "body"
    assert payload["audience"] == "architect"
    validate_source(payload)  # should not raise


def test_source_artifact_schema_rejects_unknown_audience():
    src = SourceArtifact.from_text(
        "body",
        source_uri="file:///x.md",
        audience="board_of_directors",  # not in the enum
    )
    with pytest.raises(ValidationError):
        validate_source(src.to_dict())


def test_source_artifact_schema_rejects_bad_hash_format():
    payload = {
        "source": {"uri": "file:///x.md", "content_hash": "not-a-hash"},
        "content": "body",
        "audience": "development",
    }
    with pytest.raises(ValidationError):
        validate_source(payload)


def test_source_artifact_schema_rejects_extra_fields():
    payload = {
        "source": {"uri": "file:///x.md", "content_hash": content_hash("body")},
        "content": "body",
        "audience": "development",
        "tenant_id": "meshmakers",  # not in v1 — production extension
    }
    with pytest.raises(ValidationError):
        validate_source(payload)


# ── GenerationResult ───────────────────────────────────────────────────


def _example_generation_result() -> GenerationResult:
    src = SourceArtifact.from_text(
        "the artifact body",
        source_uri="file:///data/anonymized/x.md",
        audience="development",
    )
    gen = Generation(
        architecture="pipeline",
        prompt_id="pipeline_generate_wiki",
        prompt_version=2,
        model="ollama_chat/gemma4:26b",
        sampling={"temperature": 0.0, "max_tokens": 4096, "top_p": None, "top_k": None},
        tokens={"input": 1234, "output": 567, "cache_read": 0, "cache_creation": 0},
        cost_usd=0.0012,
        latency_seconds=2.15,
        started_at=utc_now_iso(),
        ended_at=utc_now_iso(),
        reviewer_iterations=0,
        reviewer_passed=None,
    )
    return GenerationResult(
        run_id=new_run_id(),
        source_uri=src.source_uri,
        source_content_hash=src.source_content_hash,
        wiki_entry_markdown="## Heading\n\nbody\n",
        generation=gen,
    )


def test_generation_result_to_dict_validates_pipeline():
    res = _example_generation_result()
    payload = res.to_dict()
    validate_result(payload)
    assert payload["run_id"] == res.run_id
    assert payload["source"]["uri"] == res.source_uri
    assert payload["generation"]["architecture"] == "pipeline"
    assert payload["generation"]["reviewer_iterations"] == 0
    assert payload["generation"]["reviewer_passed"] is None


def test_generation_result_to_dict_validates_agentic():
    base = _example_generation_result()
    agentic_gen = Generation(
        **{**base.generation.__dict__,
           "architecture": "agentic",
           "reviewer_iterations": 2,
           "reviewer_passed": True,
           "tokens": {"input": 5000, "output": 800, "cache_read": 3000, "cache_creation": 1000}},
    )
    result = GenerationResult(
        run_id=base.run_id,
        source_uri=base.source_uri,
        source_content_hash=base.source_content_hash,
        wiki_entry_markdown=base.wiki_entry_markdown,
        generation=agentic_gen,
    )
    validate_result(result.to_dict())


def test_generation_result_schema_rejects_unknown_architecture():
    res = _example_generation_result()
    payload = res.to_dict()
    payload["generation"]["architecture"] = "magic"
    with pytest.raises(ValidationError):
        validate_result(payload)


def test_generation_result_schema_requires_latency():
    res = _example_generation_result()
    payload = res.to_dict()
    del payload["generation"]["latency_seconds"]
    with pytest.raises(ValidationError):
        validate_result(payload)


def test_generation_result_schema_rejects_negative_cost():
    res = _example_generation_result()
    payload = res.to_dict()
    payload["generation"]["cost_usd"] = -0.01
    with pytest.raises(ValidationError):
        validate_result(payload)


def test_generation_result_schema_requires_input_output_tokens():
    res = _example_generation_result()
    payload = res.to_dict()
    del payload["generation"]["tokens"]["output"]
    with pytest.raises(ValidationError):
        validate_result(payload)
