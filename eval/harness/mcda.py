"""
MCDA Scorer — Multi-Criteria Decision Analysis.

Computes the weighted MCDA score from the three measured criteria:
  - Completeness (KIP Recall, weight 0.44, higher is better)
  - Speed (latency_seconds, weight 0.33, lower is better)
  - Cost (cost_per_artifact_eur, weight 0.22, lower is better)

Supports alternate weight profiles for sensitivity analysis.

Usage:
    from eval.harness.mcda import compute_mcda, load_mcda_config

    config = load_mcda_config()
    scores = compute_mcda(runs, config)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_MCDA_CONFIG = _PROJECT_ROOT / "eval" / "mcda_config.yaml"


@dataclass(frozen=True)
class MCDAConfig:
    """Parsed MCDA configuration."""

    weights: dict[str, float]  # criterion → weight
    directions: dict[str, str]  # criterion → higher_is_better | lower_is_better
    sensitivity_profiles: dict[str, dict[str, float]]


@dataclass(frozen=True)
class MCDAResult:
    """MCDA score for a single run."""

    run_dir: str
    architecture: str
    artifact_id: str
    raw_metrics: dict[str, float]
    normalized: dict[str, float]
    weighted: dict[str, float]
    total_score: float


def load_mcda_config(path: Path | None = None) -> MCDAConfig:
    """Load the MCDA configuration YAML."""
    config_path = path or _MCDA_CONFIG
    with open(config_path) as f:
        data = yaml.safe_load(f)

    weights = {}
    directions = {}
    for name, crit in data["criteria"].items():
        weights[name] = crit["weight"]
        directions[name] = crit["direction"]

    return MCDAConfig(
        weights=weights,
        directions=directions,
        sensitivity_profiles=data.get("sensitivity_profiles", {}),
    )


def compute_mcda(
    runs: list[dict],
    config: MCDAConfig,
    *,
    weight_profile: str | None = None,
    eur_per_usd: float = 0.92,
) -> list[MCDAResult]:
    """Compute MCDA scores for a set of runs.

    Each run dict must contain:
      - run_dir: str
      - architecture: str
      - artifact_id: str
      - kip_recall: float (0.0–1.0)
      - latency_seconds: float
      - cost_usd: float

    Args:
        runs: List of run metric dicts.
        config: MCDA configuration.
        weight_profile: Name of an alternate weight profile from
                        sensitivity_profiles, or None for default.
        eur_per_usd: EUR/USD exchange rate for cost conversion.

    Returns:
        List of MCDAResult, one per run, sorted by total_score descending.
    """
    if not runs:
        return []

    # Select weights
    if weight_profile and weight_profile in config.sensitivity_profiles:
        weights = config.sensitivity_profiles[weight_profile]
    else:
        weights = config.weights

    # Extract raw metrics for each run
    raw_data = []
    for run in runs:
        cost_eur = run["cost_usd"] * eur_per_usd
        raw_data.append({
            "run": run,
            "completeness": run["kip_recall"],
            "speed": run["latency_seconds"],
            "cost": cost_eur,
        })

    # Normalize each criterion to 0–1 range using min-max
    results = []
    for criterion in ["completeness", "speed", "cost"]:
        values = [d[criterion] for d in raw_data]
        min_val = min(values)
        max_val = max(values)
        spread = max_val - min_val

        for d in raw_data:
            if spread == 0:
                # All runs have the same value — give everyone 1.0
                d[f"norm_{criterion}"] = 1.0
            elif config.directions[criterion] == "higher_is_better":
                d[f"norm_{criterion}"] = (d[criterion] - min_val) / spread
            else:  # lower_is_better
                d[f"norm_{criterion}"] = (max_val - d[criterion]) / spread

    # Compute weighted scores
    for d in raw_data:
        normalized = {}
        weighted = {}
        for criterion in ["completeness", "speed", "cost"]:
            norm = d[f"norm_{criterion}"]
            normalized[criterion] = round(norm, 4)
            weighted[criterion] = round(norm * weights[criterion], 4)

        total = sum(weighted.values())

        results.append(MCDAResult(
            run_dir=d["run"]["run_dir"],
            architecture=d["run"]["architecture"],
            artifact_id=d["run"]["artifact_id"],
            raw_metrics={
                "kip_recall": d["completeness"],
                "latency_seconds": d["speed"],
                "cost_eur": d["cost"],
            },
            normalized=normalized,
            weighted=weighted,
            total_score=round(total, 4),
        ))

    return sorted(results, key=lambda r: r.total_score, reverse=True)
