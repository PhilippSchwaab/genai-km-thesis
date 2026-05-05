"""Run-level MCDA orchestrator.

Aggregates per-architecture metrics for one run iteration and writes a
markdown summary plus a machine-readable JSON ranking. Inputs:

  - eval/results/<arch>_<artifact>_<timestamp>/metadata.json + kip_eval.json
    (one such directory per (architecture, artifact) pair). Local trial
    directories whose name begins with "local_" are excluded.
  - The frontend's sessions_summary.csv joined to session_config.json
    (read by eval.review_stats). Verification Effort, the Cohen's d
    gate decision, and the human-scored Accuracy input (factual-error
    flag rate) are derived from there.
  - eval/mcda_config.yaml. Aspirations, weights, sensitivity profiles,
    and gate definitions.

CLI:
    python eval/run_mcda.py
    python eval/run_mcda.py --label "Run 2"
    python eval/run_mcda.py --frontend /path/to/genai-km-frontend
"""

from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from eval.harness.mcda import (
    ArchitectureResult,
    GateDecision,
    MCDAResult,
    compute_mcda,
    load_mcda_config,
)
from eval.review_stats import (
    ArchitectureReview,
    CohensD,
    ReviewData,
    aggregate_by_architecture,
    cohens_d_on_time_on_task,
    load_review_data,
)


_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_RESULTS_DIR = _PROJECT_ROOT / "eval" / "results"


def _default_frontend() -> Path:
    """Resolve the frontend repo path: env var, then sibling default."""
    env = os.environ.get("KM_FRONTEND_PATH")
    if env:
        return Path(env).expanduser()
    return Path("~/PycharmProjects/genai-km-frontend").expanduser()


# metadata.json's `architecture` field uses the descriptive names; the
# review-UI side uses "A"/"B". Normalize both into the canonical short
# label used throughout the MCDA report.
_ARCH_NORMALIZE = {
    "pipeline": "A",
    "agentic": "B",
    "A": "A",
    "B": "B",
}
_ARCH_DISPLAY = {"A": "Pipeline (A)", "B": "Agentic (B)"}


@dataclass(frozen=True)
class ArtifactRunMetrics:
    """One (architecture, artifact) pair's automated metrics."""

    architecture: str           # "A" or "B"
    artifact_id: str            # e.g. "CS-06_Testing_Strategy_compiled"
    artifact_short: str         # e.g. "CS-06"
    run_dir: Path
    kip_recall: float | None    # None if kip_eval.json is missing
    latency_seconds: float
    cost_usd: float


@dataclass(frozen=True)
class ArchitectureRuns:
    """Per-architecture run-side aggregates (mean across artifacts)."""

    architecture: str
    n_artifacts: int
    artifact_short_ids: list[str]
    kip_recall: float | None
    kip_recall_n: int
    latency_seconds: float
    cost_usd_per_artifact: float


# ---------------------------------------------------------------------------
# Discover and load Run-1 results

def _short_artifact_id(full_id: str) -> str:
    """Extract the CS-XX prefix from a metadata artifact_id."""
    return full_id.split("_", 1)[0].upper()


def discover_runs(results_dir: Path) -> list[ArtifactRunMetrics]:
    """Walk eval/results/ and return one ArtifactRunMetrics per Run-1 dir.

    Directories whose name begins with "local_" are excluded (these are
    pre-Run-1 local trials, not part of the evaluation set). If multiple
    runs exist for the same (architecture, artifact_short) pair, the
    most recent (by directory name, which embeds an ISO-8601 compact
    timestamp) is kept and the older ones are silently dropped.
    """
    if not results_dir.exists():
        raise FileNotFoundError(f"Results directory not found: {results_dir}")

    candidates: dict[tuple[str, str], ArtifactRunMetrics] = {}
    for run_dir in sorted(results_dir.iterdir()):
        if not run_dir.is_dir() or run_dir.name.startswith("local_"):
            continue
        metadata_path = run_dir / "metadata.json"
        if not metadata_path.exists():
            continue
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        raw_arch = metadata["architecture"]
        if raw_arch not in _ARCH_NORMALIZE:
            raise ValueError(
                f"{run_dir}: unknown architecture {raw_arch!r} "
                f"(expected one of {sorted(_ARCH_NORMALIZE)})"
            )
        arch = _ARCH_NORMALIZE[raw_arch]
        artifact_full = metadata["artifact_id"]

        kip_path = run_dir / "kip_eval.json"
        if kip_path.exists():
            kip_recall = float(json.loads(kip_path.read_text(encoding="utf-8"))["recall"])
        else:
            kip_recall = None

        rec = ArtifactRunMetrics(
            architecture=arch,
            artifact_id=artifact_full,
            artifact_short=_short_artifact_id(artifact_full),
            run_dir=run_dir,
            kip_recall=kip_recall,
            latency_seconds=float(metadata["total_latency_seconds"]),
            cost_usd=float(metadata["total_cost_usd"]),
        )
        # If multiple matches, keep the lexicographically later run_dir
        # (timestamp embedded in the name).
        key = (arch, rec.artifact_short)
        prior = candidates.get(key)
        if prior is None or run_dir.name > prior.run_dir.name:
            candidates[key] = rec
    return sorted(candidates.values(), key=lambda r: (r.architecture, r.artifact_short))


def aggregate_runs_by_architecture(
    runs: Iterable[ArtifactRunMetrics],
) -> dict[str, ArchitectureRuns]:
    """Mean across artifacts per architecture, matching thesis §3.3.2."""
    grouped: dict[str, list[ArtifactRunMetrics]] = defaultdict(list)
    for r in runs:
        grouped[r.architecture].append(r)

    out: dict[str, ArchitectureRuns] = {}
    for arch, items in grouped.items():
        n = len(items)
        kip_values = [r.kip_recall for r in items if r.kip_recall is not None]
        out[arch] = ArchitectureRuns(
            architecture=arch,
            n_artifacts=n,
            artifact_short_ids=sorted({r.artifact_short for r in items}),
            kip_recall=(sum(kip_values) / len(kip_values)) if kip_values else None,
            kip_recall_n=len(kip_values),
            latency_seconds=sum(r.latency_seconds for r in items) / n,
            cost_usd_per_artifact=sum(r.cost_usd for r in items) / n,
        )
    return out


# ---------------------------------------------------------------------------
# Build the MCDA inputs

def build_mcda_inputs(
    arch_runs: dict[str, ArchitectureRuns],
    arch_reviews: dict[str, ArchitectureReview],
    cohens: CohensD | None,
) -> tuple[dict[str, dict[str, float]], dict[str, dict[str, GateDecision]]]:
    """Construct (arch_metrics, gates) dicts for compute_mcda."""
    arch_metrics: dict[str, dict[str, float]] = {}
    gates: dict[str, dict[str, GateDecision]] = {}

    for arch, run_agg in arch_runs.items():
        review = arch_reviews.get(arch)
        time_on_task = review.time_s_mean if review is not None else None
        claim_support = review.claim_support_rate if review is not None else None

        kip = run_agg.kip_recall
        arch_metrics[arch] = {
            "claim_support_rate": float(claim_support) if claim_support is not None else 0.0,
            "kip_recall": float(kip) if kip is not None else 0.0,
            "latency_seconds": run_agg.latency_seconds,
            "cost_usd_per_artifact": run_agg.cost_usd_per_artifact,
            "mean_time_on_task_seconds": float(time_on_task) if time_on_task is not None else 0.0,
        }

        # Verification Effort gate: Cohen's d >= 0.5.
        if cohens is None:
            ve_decision = GateDecision(
                status="not_verified",
                detail="No review-UI data available.",
            )
        elif time_on_task is None:
            ve_decision = GateDecision(
                status="not_verified",
                detail=(
                    f"Cohen's d = {cohens.d:.2f} from review data, "
                    f"but no per-architecture time-on-task observed for {arch}."
                ),
            )
        else:
            ve_decision = GateDecision(
                status="pass" if cohens.gate_passed else "fail",
                detail=(
                    f"Cohen's d = {cohens.d:.2f} on n_A={cohens.n_a}, n_B={cohens.n_b}; "
                    f"|d| {'>=' if cohens.gate_passed else '<'} 0.5."
                ),
            )

        # Accuracy gate: direct human scoring from review-UI factual-error
        # flag rate. The §3.3.2 spot-check gate validates an automated
        # approximation against manual review; with direct human scoring
        # as the input there is no automated approximation to validate,
        # so the gate is satisfied by construction whenever review data
        # exists.
        if review is None or claim_support is None:
            accuracy_decision = GateDecision(
                status="not_verified",
                detail=(
                    f"No review-UI data for {arch}; factual-error rate "
                    "cannot be computed."
                ),
            )
        else:
            accuracy_decision = GateDecision(
                status="pass",
                detail=(
                    f"Direct human scoring: {review.n_flagged_factual_total} "
                    f"factual-error flags across {review.n_blocks_total} "
                    f"reviewed blocks ({claim_support:.3f} support rate). "
                    "Automated cross-check gate not applicable to direct "
                    "human input."
                ),
            )

        gates[arch] = {
            "verification_effort": ve_decision,
            "accuracy": accuracy_decision,
        }

    return arch_metrics, gates


# ---------------------------------------------------------------------------
# Markdown rendering

def _fmt(v: float | None, *, decimals: int = 3) -> str:
    if v is None:
        return "---"
    return f"{v:.{decimals}f}"


def _render_md_table(headers: list[str], rows: list[list[str]]) -> str:
    sep = ["---"] * len(headers)
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(sep) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def render_arch_table(result: ArchitectureResult) -> str:
    """One row per criterion for one (architecture, profile) pair."""
    headers = [
        "Criterion", "Raw", "Normalized", "Default weight",
        "Renormalized weight", "Weighted", "Included", "Gate",
    ]
    rows: list[list[str]] = []
    for cr in result.criterion_results:
        rows.append([
            cr.name,
            _fmt(cr.raw_value, decimals=4),
            _fmt(cr.normalized, decimals=4),
            _fmt(cr.weight_default, decimals=2),
            _fmt(cr.weight_renormalized, decimals=4),
            _fmt(cr.weighted, decimals=4),
            "yes" if cr.included else "no",
            cr.gate_status if cr.gate_status is not None else "n/a",
        ])
    return _render_md_table(headers, rows)


def render_profile_summary(result: MCDAResult, profile: str) -> str:
    headers = ["Architecture", "Composite", "Coverage", "Excluded"]
    rows: list[list[str]] = []
    for ar in result.by_profile[profile]:
        rows.append([
            _ARCH_DISPLAY.get(ar.architecture, ar.architecture),
            f"{ar.composite_score:.4f}",
            ", ".join(ar.coverage) if ar.coverage else "(none)",
            ", ".join(ar.excluded) if ar.excluded else "(none)",
        ])
    return _render_md_table(headers, rows)


def render_session_audit_table(review: ReviewData) -> str:
    """Per-session audit trail: which reviewer saw which artifact."""
    headers = [
        "session_id", "reviewer_id", "architecture", "artifact_id",
        "system_label", "total_time_s", "approved", "edited",
        "flagged", "removed", "edit_distance", "likert_conf", "likert_eff",
    ]
    rows: list[list[str]] = []
    for s in sorted(review.sessions, key=lambda r: r.session_id):
        rows.append([
            s.session_id,
            s.reviewer_id,
            s.architecture,
            s.artifact_id,
            s.system_label,
            str(s.total_time_s),
            str(s.n_approved),
            str(s.n_edited),
            str(s.n_flagged),
            str(s.n_removed),
            str(s.final_edit_distance),
            str(s.likert_confidence),
            str(s.likert_effort),
        ])
    return _render_md_table(headers, rows)


def render_report(
    label: str,
    result: MCDAResult,
    arch_runs: dict[str, ArchitectureRuns],
    arch_reviews: dict[str, ArchitectureReview],
    review: ReviewData,
    cohens: CohensD | None,
) -> str:
    lines: list[str] = []
    lines.append(f"# {label} MCDA Summary")
    lines.append("")
    lines.append(
        "Composite score per architecture is computed by aspiration-level "
        "Simple Additive Weighting per thesis §3.3.2 (5 criteria, "
        "default weights Accuracy 0.30 / Verification Effort 0.25 / "
        "Completeness 0.20 / Speed 0.15 / Cost 0.10). Verification Effort "
        "is gated by Cohen's d >= 0.5 on per-session time-on-task. "
        "Accuracy is sourced from the review-UI factual-error flag rate "
        "(direct human scoring per §3.3.3); the §3.3.2 spot-check gate "
        "validates an automated approximation against manual review and "
        "is satisfied by construction whenever review data exists. "
        "Failed or not-yet-verified criteria are excluded and the "
        "remaining weights are renormalized to sum to 1; the included-"
        "criterion coverage is reported alongside the score."
    )
    lines.append("")
    lines.append(
        f"**Review-UI status:** {review.n_submitted} of {review.n_planned} "
        "review sessions submitted."
    )
    lines.append("")

    # Per-architecture aggregate inputs (audit trail).
    lines.append("## Architecture-aggregated inputs")
    lines.append("")
    lines.append(_render_md_table(
        [
            "Architecture", "Artifacts", "KIP recall (n)", "Mean latency (s)",
            "Mean cost ($)", "Mean time-on-task (s)",
            "Claim support (factual / blocks)",
        ],
        [
            [
                _ARCH_DISPLAY.get(arch, arch),
                str(run_agg.n_artifacts),
                (
                    f"{run_agg.kip_recall:.3f} (n={run_agg.kip_recall_n})"
                    if run_agg.kip_recall is not None
                    else f"--- (n={run_agg.kip_recall_n})"
                ),
                f"{run_agg.latency_seconds:.2f}",
                f"{run_agg.cost_usd_per_artifact:.4f}",
                _fmt(arch_reviews[arch].time_s_mean, decimals=2)
                if arch in arch_reviews else "---",
                (
                    f"{arch_reviews[arch].claim_support_rate:.3f} ("
                    f"{arch_reviews[arch].n_flagged_factual_total} / "
                    f"{arch_reviews[arch].n_blocks_total})"
                    if arch in arch_reviews
                    and arch_reviews[arch].claim_support_rate is not None
                    else "--- (no review data)"
                ),
            ]
            for arch, run_agg in sorted(arch_runs.items())
        ],
    ))
    lines.append("")

    # Per-session audit trail (review-UI side).
    if review.sessions:
        lines.append("## Per-session review record (architecture-resolved)")
        lines.append("")
        lines.append(
            "Architecture is resolved from `session_config.json`'s "
            "`architecture_internal` field (the canonical mapping); "
            "`system_label` is shown for traceability. Per-reviewer label "
            "overrides in `study_design.json` mean the blinded labels do "
            "not consistently identify architectures across reviewers."
        )
        lines.append("")
        lines.append(render_session_audit_table(review))
        lines.append("")

    if cohens is not None:
        lines.append("## Verification Effort gate")
        lines.append("")
        gate_pass = "PASS" if cohens.gate_passed else "FAIL"
        lines.append(
            f"Cohen's d = **{cohens.d:.2f}** "
            f"(n_A={cohens.n_a}, n_B={cohens.n_b}, "
            f"pooled SD = {cohens.pooled_sd:.2f}). "
            f"Threshold |d| >= 0.5: **{gate_pass}**."
        )
        if cohens.n_a < 5 or cohens.n_b < 5:
            lines.append("")
            lines.append(
                "*Caveat:* the within-group SD is unstable at this sample "
                "size; Verification Effort is reported descriptively per §3.3.3."
            )
        lines.append("")

    # Composite scores per profile.
    for profile in result.profiles:
        title = profile.capitalize() if profile != "default" else "Default"
        lines.append(f"## Composite score --- {title} weight profile")
        lines.append("")
        lines.append(render_profile_summary(result, profile))
        lines.append("")
        for ar in result.by_profile[profile]:
            lines.append(
                f"### {_ARCH_DISPLAY.get(ar.architecture, ar.architecture)} "
                f"--- per-criterion contribution ({title})"
            )
            lines.append("")
            lines.append(render_arch_table(ar))
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


# ---------------------------------------------------------------------------
# CLI

def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--label",
        default="Run 1",
        help="Label used in the report title and filename stem "
             "(default: 'Run 1', producing 'run1_mcda_summary.md').",
    )
    parser.add_argument(
        "--frontend",
        type=Path,
        default=None,
        help="Path to genai-km-frontend repo. Defaults to "
             "$KM_FRONTEND_PATH or ~/PycharmProjects/genai-km-frontend.",
    )
    parser.add_argument(
        "--results",
        type=Path,
        default=_RESULTS_DIR,
        help=f"Path to eval/results directory (default: {_RESULTS_DIR})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_PROJECT_ROOT / "eval" / "metrics",
        help="Directory where the markdown and JSON outputs are written "
             "(default: eval/metrics/, the canonical location for derived "
             "cross-run aggregates).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to mcda_config.yaml (defaults to eval/mcda_config.yaml).",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    config = load_mcda_config(args.config)
    frontend = args.frontend or _default_frontend()

    # Discover and aggregate run-side metrics.
    runs = discover_runs(args.results)
    arch_runs = aggregate_runs_by_architecture(runs)
    if not arch_runs:
        raise SystemExit(
            f"No Run-1 result directories found under {args.results}."
        )

    # Load and aggregate review-side metrics.
    review = load_review_data(frontend)
    arch_reviews = aggregate_by_architecture(review)
    cohens = cohens_d_on_time_on_task(review)

    # Compose MCDA inputs and compute.
    arch_metrics, gates = build_mcda_inputs(arch_runs, arch_reviews, cohens)
    result = compute_mcda(arch_metrics, gates, config)

    # Write outputs.
    stem = args.label.lower().replace(" ", "")
    md_path = args.output_dir / f"{stem}_mcda_summary.md"
    json_path = args.output_dir / f"{stem}_mcda.json"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(
        render_report(
            label=args.label,
            result=result,
            arch_runs=arch_runs,
            arch_reviews=arch_reviews,
            review=review,
            cohens=cohens,
        ),
        encoding="utf-8",
    )
    json_path.write_text(
        json.dumps(result.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Concise stdout summary.
    print(f"Architectures: {', '.join(sorted(arch_runs))}")
    print(
        "Run dirs evaluated: "
        f"{sum(a.n_artifacts for a in arch_runs.values())}"
    )
    if cohens is not None:
        gate_pass = "PASS" if cohens.gate_passed else "FAIL"
        print(
            f"Cohen's d = {cohens.d:.2f} "
            f"(n_A={cohens.n_a}, n_B={cohens.n_b}) -> VE gate {gate_pass}"
        )
    for profile in result.profiles:
        ranked = result.by_profile[profile]
        ordering = " > ".join(
            f"{_ARCH_DISPLAY.get(r.architecture, r.architecture)} "
            f"({r.composite_score:.3f})"
            for r in ranked
        )
        cov = ", ".join(ranked[0].coverage) if ranked else "(none)"
        print(f"  {profile:<11} -> {ordering}; coverage = {cov}")
    print(f"Report  : {md_path}")
    print(f"JSON    : {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
