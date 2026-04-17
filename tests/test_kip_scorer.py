"""Tests for the KIP scorer (no live API calls)."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from eval.harness.kip_scorer import (
    KIPScoreReport,
    _load_kips,
    _parse_judgment,
    score_kips,
)
from src.common.llm_client import LLMResult


# ── Judgment parsing ────────────────────────────────────────────────────


class TestParseJudgment:
    def test_parse_yes(self):
        j, r = _parse_judgment("JUDGMENT: YES\nREASON: The fact is clearly present.")
        assert j == "YES"
        assert "clearly present" in r

    def test_parse_partial(self):
        j, r = _parse_judgment("JUDGMENT: PARTIAL\nREASON: Partially mentioned.")
        assert j == "PARTIAL"

    def test_parse_no(self):
        j, r = _parse_judgment("JUDGMENT: NO\nREASON: Not found in the entry.")
        assert j == "NO"

    def test_parse_case_insensitive(self):
        j, _ = _parse_judgment("judgment: yes\nreason: found it.")
        assert j == "YES"

    def test_parse_garbage_defaults_to_no(self):
        j, r = _parse_judgment("I think this is good.")
        assert j == "NO"
        assert r == ""

    def test_parse_with_extra_whitespace(self):
        j, r = _parse_judgment("  JUDGMENT:  PARTIAL  \n  REASON:  Some reason  ")
        assert j == "PARTIAL"
        assert r == "Some reason"


# ── KIP loading ─────────────────────────────────────────────────────────


class TestLoadKips:
    def test_load_cs06(self):
        kips = _load_kips("CS-06_Testing_Strategy_compiled")
        assert len(kips) == 11
        assert kips[0]["id"] == "KIP-001"

    def test_load_cs01(self):
        kips = _load_kips("CS-01_Archive_Backup_report")
        assert len(kips) == 10

    def test_bad_artifact_id_raises(self):
        with pytest.raises(FileNotFoundError):
            _load_kips("no_cs_prefix_here")


# ── score_kips with mocked LLM ─────────────────────────────────────────


def _fake_judge_result(judgment: str = "YES") -> LLMResult:
    return LLMResult(
        text=f"JUDGMENT: {judgment}\nREASON: Test reason.",
        model="test-judge",
        timestamp="2026-04-17T12:00:00+00:00",
        latency_seconds=0.5,
        prompt_tokens=100,
        completion_tokens=20,
        total_tokens=120,
        cost_usd=0.001,
    )


_call_count = 0


def _fake_complete_alternating(model, messages, *, temperature=0.0,
                                max_tokens=256, top_p=None, top_k=None,
                                call_log=None):
    """Return YES for most KIPs, PARTIAL for implicit ones."""
    global _call_count
    _call_count += 1
    # Every 3rd call returns PARTIAL (simulate implicit KIP misses)
    judgment = "PARTIAL" if _call_count % 3 == 0 else "YES"
    result = _fake_judge_result(judgment)
    if call_log is not None:
        call_log.record(result)
    return result


@pytest.fixture()
def fake_run_dir(tmp_path):
    """Create a minimal run directory with metadata and wiki entry."""
    run_dir = tmp_path / "pipeline_CS-06_test"
    run_dir.mkdir()
    (run_dir / "metadata.json").write_text(json.dumps({
        "architecture": "pipeline",
        "artifact_id": "CS-06_Testing_Strategy_compiled",
        "artifact_type": "development_activity",
        "total_latency_seconds": 50.0,
        "total_cost_usd": 0.0,
    }))
    (run_dir / "wiki_entry.md").write_text("# Test Wiki\n\nSome generated content.")
    return run_dir


@patch("eval.harness.kip_scorer.complete", side_effect=_fake_complete_alternating)
def test_score_kips_returns_report(mock_complete, fake_run_dir):
    global _call_count
    _call_count = 0

    report = score_kips(fake_run_dir)

    assert isinstance(report, KIPScoreReport)
    assert report.artifact_id == "CS-06_Testing_Strategy_compiled"
    assert report.total_kips == 11
    assert 0.0 <= report.recall <= 1.0
    assert report.counts["YES"] + report.counts["PARTIAL"] + report.counts["NO"] == 11


@patch("eval.harness.kip_scorer.complete", side_effect=_fake_complete_alternating)
def test_score_kips_tracks_eval_cost(mock_complete, fake_run_dir):
    global _call_count
    _call_count = 0

    report = score_kips(fake_run_dir)

    # 11 KIPs × $0.001 each
    assert report.call_log.total_cost_usd == pytest.approx(0.011)
    assert report.call_log.total_tokens == 11 * 120


@patch("eval.harness.kip_scorer.complete", side_effect=_fake_complete_alternating)
def test_to_dict_structure(mock_complete, fake_run_dir):
    global _call_count
    _call_count = 0

    report = score_kips(fake_run_dir)
    d = report.to_dict()

    assert "recall" in d
    assert "counts" in d
    assert "judgments" in d
    assert len(d["judgments"]) == 11
    assert all(
        {"kip_id", "kip_text", "category", "implicit", "judgment", "reason", "score"}
        <= set(j.keys())
        for j in d["judgments"]
    )
