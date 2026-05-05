"""KIP evaluation orchestrator.

Runs the LLM-as-judge KIP scorer over one or more generation-run
directories and writes ``kip_eval.json`` alongside each run's
``metadata.json`` and ``wiki_entry.md``.

The MCDA composite score is a separate concern that aggregates per
architecture rather than per run; it lives in ``eval/run_mcda.py``
and is invoked from the CLI as ``km mcda``.
"""

from __future__ import annotations

import json
from pathlib import Path

from eval.harness.kip_scorer import KIPScoreReport, score_kips


def evaluate_run(
    run_dir: Path,
    *,
    judge_model: str | None = None,
) -> KIPScoreReport:
    """Run KIP evaluation on a single generation run.

    Scores every KIP for the artifact, writes ``kip_eval.json`` into
    ``run_dir``, and returns the report.
    """
    report = score_kips(run_dir, judge_model=judge_model)
    (run_dir / "kip_eval.json").write_text(
        json.dumps(report.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return report


def evaluate_runs(
    *run_dirs: Path,
    judge_model: str | None = None,
) -> list[KIPScoreReport]:
    """Run KIP evaluation on each ``run_dir`` and return all reports."""
    reports: list[KIPScoreReport] = []
    for run_dir in run_dirs:
        cached = run_dir / "kip_eval.json"
        if cached.exists() and judge_model is None:
            reports.append(_report_from_cached(json.loads(cached.read_text()), run_dir))
        else:
            reports.append(evaluate_run(run_dir, judge_model=judge_model))
    return reports


def _report_from_cached(data: dict, run_dir: Path) -> KIPScoreReport:
    """Reconstruct a minimal ``KIPScoreReport`` from cached ``kip_eval.json``."""
    from eval.harness.kip_scorer import KIPJudgment, KIPScoreReport

    report = KIPScoreReport(
        artifact_id=data["artifact_id"],
        run_dir=str(run_dir),
    )
    for j in data["judgments"]:
        report.judgments.append(
            KIPJudgment(
                kip_id=j["kip_id"],
                kip_text=j["kip_text"],
                category=j["category"],
                implicit=j["implicit"],
                judgment=j["judgment"],
                reason=j["reason"],
                score=j["score"],
            )
        )
    return report
