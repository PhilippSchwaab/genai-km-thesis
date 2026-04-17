"""
Eval Runner — Orchestrates evaluation for one or more run directories.

Runs KIP scoring on each run, writes per-run eval results, and optionally
computes MCDA across all runs.

Usage:
    from eval.harness.run_eval import evaluate_run, evaluate_and_compare

    # Single run
    report = evaluate_run(Path("eval/results/pipeline_CS-06_..."))

    # Compare multiple runs
    comparison = evaluate_and_compare(
        Path("eval/results/pipeline_CS-06_..."),
        Path("eval/results/agentic_CS-06_..."),
    )
"""

from __future__ import annotations

import json
from pathlib import Path

from eval.harness.kip_scorer import KIPScoreReport, score_kips
from eval.harness.mcda import MCDAResult, compute_mcda, load_mcda_config

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_METRICS_DIR = _PROJECT_ROOT / "eval" / "metrics"


def evaluate_run(
    run_dir: Path,
    *,
    judge_model: str | None = None,
) -> KIPScoreReport:
    """Run KIP evaluation on a single generation run.

    Scores all KIPs, writes kip_eval.json into the run directory,
    and returns the report.
    """
    report = score_kips(run_dir, judge_model=judge_model)

    # Write eval results alongside the run outputs
    eval_output = report.to_dict()
    (run_dir / "kip_eval.json").write_text(
        json.dumps(eval_output, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return report


def evaluate_and_compare(
    *run_dirs: Path,
    judge_model: str | None = None,
    weight_profile: str | None = None,
    eur_per_usd: float = 0.92,
) -> dict:
    """Evaluate multiple runs and compute MCDA comparison.

    Args:
        run_dirs: Paths to run directories.
        judge_model: Override the judge model.
        weight_profile: MCDA sensitivity profile name.
        eur_per_usd: Exchange rate for cost conversion.

    Returns:
        Dict with per-run eval reports and MCDA results.
    """
    reports: list[KIPScoreReport] = []
    for run_dir in run_dirs:
        # Check if we already have a cached kip_eval.json
        cached = run_dir / "kip_eval.json"
        if cached.exists() and judge_model is None:
            # Load cached report for MCDA but don't re-run scoring
            cached_data = json.loads(cached.read_text())
            report = _report_from_cached(cached_data, run_dir)
        else:
            report = evaluate_run(run_dir, judge_model=judge_model)
        reports.append(report)

    # Build MCDA input
    mcda_runs = []
    for report in reports:
        metadata = json.loads(
            (Path(report.run_dir) / "metadata.json").read_text()
        )
        mcda_runs.append({
            "run_dir": report.run_dir,
            "architecture": metadata["architecture"],
            "artifact_id": metadata["artifact_id"],
            "kip_recall": report.recall,
            "latency_seconds": metadata["total_latency_seconds"],
            "cost_usd": metadata["total_cost_usd"],
        })

    config = load_mcda_config()
    mcda_results = compute_mcda(
        mcda_runs, config,
        weight_profile=weight_profile,
        eur_per_usd=eur_per_usd,
    )

    # Write comparison to eval/metrics/
    _METRICS_DIR.mkdir(parents=True, exist_ok=True)
    comparison = {
        "weight_profile": weight_profile or "default",
        "eur_per_usd": eur_per_usd,
        "runs": [
            {
                "run_dir": r.run_dir,
                "architecture": r.architecture,
                "artifact_id": r.artifact_id,
                "raw_metrics": r.raw_metrics,
                "normalized": r.normalized,
                "weighted": r.weighted,
                "total_score": r.total_score,
            }
            for r in mcda_results
        ],
    }
    comparison_path = _METRICS_DIR / "comparison.json"
    comparison_path.write_text(
        json.dumps(comparison, indent=2), encoding="utf-8"
    )

    return comparison


def _report_from_cached(data: dict, run_dir: Path) -> KIPScoreReport:
    """Reconstruct a minimal KIPScoreReport from cached kip_eval.json."""
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
