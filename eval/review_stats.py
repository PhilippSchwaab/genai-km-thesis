"""Review-UI loaders and review-side aggregations.

Loads the frontend's ``sessions_summary.csv`` and joins it via
``session_id`` to ``session_config.json``, resolving the blinded
``system_label`` column into the canonical ``architecture_internal``
(A or B). This is essential: the same blinded label refers to
different architectures across reviewers (``study_design.json``
defines per-reviewer label overrides), so any per-architecture
aggregate computed from ``system_label`` alone would mix architectures.

The Cohen's d on per-session time-on-task implements the inclusion
gate from thesis §3.3.2; per §3.3.3 the data is used descriptively
in Chapter 5.

This module is library-only; the orchestrator at ``eval/run_mcda.py``
consumes :class:`ReviewData` and :class:`CohensD` and renders the
canonical Run-1 Markdown.
"""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path


# CSV columns from the frontend's `sessions_summary.csv`.
FLAG_COLS = (
    "n_flagged_factual",
    "n_flagged_missing",
    "n_flagged_attribution",
    "n_flagged_style",
    "n_flagged_other",
)
DISPOSITION_INT_COLS = ("n_approved", "n_edited", "n_removed")
INT_COLS: tuple[str, ...] = (
    "total_time_s",
    *DISPOSITION_INT_COLS,
    *FLAG_COLS,
    "final_edit_distance",
    "likert_confidence",
    "likert_effort",
)


# ---------------------------------------------------------------------------
# Value types

@dataclass(frozen=True)
class ReviewSession:
    """One submitted review session, joined with its config row."""

    session_id: str
    reviewer_id: str
    artifact_id: str
    system_label: str            # blinded label as the reviewer saw it
    architecture: str            # canonical "A" or "B" from session_config.json
    total_time_s: int
    n_approved: int
    n_edited: int
    n_flagged_factual: int
    n_flagged_missing: int
    n_flagged_attribution: int
    n_flagged_style: int
    n_flagged_other: int
    n_removed: int
    final_edit_distance: int
    likert_confidence: int
    likert_effort: int

    @property
    def n_flagged(self) -> int:
        return (
            self.n_flagged_factual
            + self.n_flagged_missing
            + self.n_flagged_attribution
            + self.n_flagged_style
            + self.n_flagged_other
        )

    @property
    def n_blocks(self) -> int:
        return self.n_approved + self.n_edited + self.n_flagged + self.n_removed


@dataclass(frozen=True)
class ReviewData:
    """All loaded review data: submitted sessions plus the planned set."""

    sessions: list[ReviewSession]
    planned_session_ids: list[str]
    planned_reviewer_ids: list[str]

    @property
    def n_submitted(self) -> int:
        return len(self.sessions)

    @property
    def n_planned(self) -> int:
        return len(self.planned_session_ids)

    @property
    def submitted_reviewers(self) -> list[str]:
        return sorted({s.reviewer_id for s in self.sessions})

    @property
    def pending_reviewers(self) -> list[str]:
        submitted = {s.session_id for s in self.sessions}
        return sorted({
            rid for sid, rid in zip(self.planned_session_ids, self.planned_reviewer_ids)
            if sid not in submitted
        })

    def by_architecture(self) -> dict[str, list[ReviewSession]]:
        out: dict[str, list[ReviewSession]] = {}
        for s in self.sessions:
            out.setdefault(s.architecture, []).append(s)
        return out


@dataclass(frozen=True)
class CohensD:
    """Cohen's d for two independent samples with pooled SD.

    Implements the §3.3.2 inclusion gate on Verification Effort:
    ``|d| >= 0.5`` between architectures' mean per-session
    time-on-task, divided by the within-architecture pooled SD.
    """

    mean_a: float
    mean_b: float
    sd_a: float
    sd_b: float
    n_a: int
    n_b: int
    pooled_sd: float
    d: float
    gate_passed: bool

    @classmethod
    def from_groups(cls, a: list[float], b: list[float]) -> "CohensD":
        n_a, n_b = len(a), len(b)
        mean_a = sum(a) / n_a if n_a > 0 else float("nan")
        mean_b = sum(b) / n_b if n_b > 0 else float("nan")
        sd_a = _sample_sd(a) if n_a > 1 else 0.0
        sd_b = _sample_sd(b) if n_b > 1 else 0.0
        denom = n_a + n_b - 2
        if denom <= 0:
            pooled = float("nan")
        else:
            pooled = math.sqrt(
                ((n_a - 1) * sd_a**2 + (n_b - 1) * sd_b**2) / denom
            )
        if math.isnan(pooled) or pooled <= 0:
            d = float("nan")
        else:
            d = (mean_a - mean_b) / pooled
        return cls(
            mean_a=mean_a,
            mean_b=mean_b,
            sd_a=sd_a,
            sd_b=sd_b,
            n_a=n_a,
            n_b=n_b,
            pooled_sd=pooled,
            d=d,
            gate_passed=(not math.isnan(d)) and abs(d) >= 0.5,
        )


def _sample_sd(values: list[float]) -> float:
    """Sample standard deviation (Bessel-corrected, ddof=1)."""
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    var = sum((x - mean) ** 2 for x in values) / (n - 1)
    return math.sqrt(var)


# ---------------------------------------------------------------------------
# Loaders

def load_review_data(frontend: Path) -> ReviewData:
    """Load and enrich the frontend's review outputs.

    Reads ``logs/sessions_summary.csv`` and ``data/session_config.json``
    and joins each summary row to its config row by ``session_id``,
    resolving the blinded ``system_label`` into ``architecture_internal``.

    Raises ``FileNotFoundError`` if ``session_config.json`` is missing
    (it defines the planned set even when no sessions have been
    submitted yet). A missing ``sessions_summary.csv`` is treated as
    "no sessions submitted".
    """
    config_path = frontend / "data" / "session_config.json"
    if not config_path.exists():
        raise FileNotFoundError(
            f"session_config.json not found at {config_path}"
        )
    with config_path.open(encoding="utf-8") as f:
        cfg_rows = json.load(f)
    arch_by_session: dict[str, str] = {
        row["session_id"]: row["architecture_internal"] for row in cfg_rows
    }
    planned_session_ids = [row["session_id"] for row in cfg_rows]
    planned_reviewer_ids = [row["reviewer_id"] for row in cfg_rows]

    sessions: list[ReviewSession] = []
    summary_path = frontend / "logs" / "sessions_summary.csv"
    if summary_path.exists():
        with summary_path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                sid = r["session_id"]
                if sid not in arch_by_session:
                    raise ValueError(
                        f"Session {sid!r} in summary CSV not found in "
                        "session_config.json"
                    )
                int_fields = {col: int(r[col]) for col in INT_COLS}
                sessions.append(
                    ReviewSession(
                        session_id=sid,
                        reviewer_id=r["reviewer_id"],
                        artifact_id=r["artifact_id"],
                        system_label=r["system_label"],
                        architecture=arch_by_session[sid],
                        **int_fields,
                    )
                )
    return ReviewData(
        sessions=sessions,
        planned_session_ids=planned_session_ids,
        planned_reviewer_ids=planned_reviewer_ids,
    )


# ---------------------------------------------------------------------------
# Per-architecture aggregates

@dataclass(frozen=True)
class ArchitectureReview:
    """Per-architecture aggregates over the submitted review sessions."""

    architecture: str
    n_sessions: int
    time_s_mean: float
    time_s_sd: float
    time_s_median: float
    edit_distance_mean: float
    likert_confidence_mean: float
    likert_effort_mean: float
    # Disposition tallies (sums across sessions).
    n_approved_total: int
    n_edited_total: int
    n_flagged_total: int
    n_removed_total: int
    # Flag-reason tallies.
    flag_totals: dict[str, int]
    # Direct-human Accuracy input: 1 - (factual flags / reviewed blocks).
    n_flagged_factual_total: int
    n_blocks_total: int
    claim_support_rate: float | None


def aggregate_by_architecture(data: ReviewData) -> dict[str, ArchitectureReview]:
    """Aggregate :class:`ReviewSession` rows per architecture (A/B)."""
    out: dict[str, ArchitectureReview] = {}
    for arch, items in data.by_architecture().items():
        n = len(items)
        times = [float(s.total_time_s) for s in items]
        time_mean = sum(times) / n
        time_sd = _sample_sd(times) if n > 1 else 0.0
        sorted_times = sorted(times)
        if n % 2:
            median = sorted_times[n // 2]
        else:
            median = 0.5 * (sorted_times[n // 2 - 1] + sorted_times[n // 2])

        edit_distance_mean = sum(s.final_edit_distance for s in items) / n
        likert_conf_mean = sum(s.likert_confidence for s in items) / n
        likert_eff_mean = sum(s.likert_effort for s in items) / n

        flag_totals = {col: sum(getattr(s, col) for s in items) for col in FLAG_COLS}
        n_factual = flag_totals["n_flagged_factual"]
        n_blocks = sum(s.n_blocks for s in items)
        claim_support = (1.0 - n_factual / n_blocks) if n_blocks else None

        out[arch] = ArchitectureReview(
            architecture=arch,
            n_sessions=n,
            time_s_mean=time_mean,
            time_s_sd=time_sd,
            time_s_median=median,
            edit_distance_mean=edit_distance_mean,
            likert_confidence_mean=likert_conf_mean,
            likert_effort_mean=likert_eff_mean,
            n_approved_total=sum(s.n_approved for s in items),
            n_edited_total=sum(s.n_edited for s in items),
            n_flagged_total=sum(s.n_flagged for s in items),
            n_removed_total=sum(s.n_removed for s in items),
            flag_totals=flag_totals,
            n_flagged_factual_total=n_factual,
            n_blocks_total=n_blocks,
            claim_support_rate=claim_support,
        )
    return out


def cohens_d_on_time_on_task(data: ReviewData) -> CohensD | None:
    """Compute Cohen's d on per-session time-on-task between A and B.

    Returns ``None`` if either group is empty (e.g. before any
    sessions for one architecture have been submitted).
    """
    by_arch = data.by_architecture()
    a = [float(s.total_time_s) for s in by_arch.get("A", [])]
    b = [float(s.total_time_s) for s in by_arch.get("B", [])]
    if not a or not b:
        return None
    return CohensD.from_groups(a, b)
