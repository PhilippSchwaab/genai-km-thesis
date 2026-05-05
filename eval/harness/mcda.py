"""MCDA scorer --- aspiration-level Simple Additive Weighting.

Implements the methodology committed in thesis §3.3.2: five
stakeholder-weighted criteria, aspiration-level normalization
(Form 2 of Tzeng & Huang, 2011), and gate-based exclusion of
inputs whose reliability conditions fail.

Public API
----------
    config = load_mcda_config()                       # parses mcda_config.yaml
    result = compute_mcda(arch_metrics, gates, config)

Inputs
------
arch_metrics : dict[str, dict[str, float]]
    Per-architecture metric dictionary. Keys are architecture
    identifiers (e.g. "pipeline", "agentic"). Values map criterion
    name to raw aggregated metric value (e.g. mean across artifacts).
gates : dict[str, dict[str, GateDecision]]
    Per-architecture gate decisions, keyed by criterion. Criteria
    without a gate (Completeness, Speed, Cost) are always included.
    Gated criteria (Accuracy, Verification Effort) must have a
    GateDecision whose `status` is one of {"pass", "fail",
    "not_verified"}; only "pass" leads to inclusion.

Outputs
-------
MCDAResult lists the per-architecture composite score for each
sensitivity profile (default plus the named profiles in the config),
the included-criterion coverage, and the per-criterion contribution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Literal, Mapping

import yaml


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_MCDA_CONFIG = _PROJECT_ROOT / "eval" / "mcda_config.yaml"

GateStatus = Literal["pass", "fail", "not_verified"]


@dataclass(frozen=True)
class CriterionSpec:
    """One row of the MCDA spec (mcda_config.yaml `criteria` section)."""

    name: str
    weight: float                 # default-profile weight
    direction: str                # "benefit" or "cost"
    aspiration: float             # x_star
    anti_aspiration: float        # x_minus
    metric: str                   # name of the input metric this criterion consumes
    has_gate: bool                # True if a gate is configured
    rationale: str = ""


@dataclass(frozen=True)
class MCDAConfig:
    """Parsed MCDA configuration."""

    criteria: dict[str, CriterionSpec]
    sensitivity_profiles: dict[str, dict[str, float]]

    @property
    def default_weights(self) -> dict[str, float]:
        return {name: c.weight for name, c in self.criteria.items()}

    def weights_for_profile(self, profile: str | None) -> dict[str, float]:
        if profile is None or profile == "default":
            return self.default_weights
        if profile not in self.sensitivity_profiles:
            raise KeyError(
                f"Unknown sensitivity profile: {profile!r}. "
                f"Known: {sorted(self.sensitivity_profiles)}"
            )
        return dict(self.sensitivity_profiles[profile])


@dataclass(frozen=True)
class GateDecision:
    """Outcome of a criterion-level reliability gate.

    `status` controls inclusion in the composite score:
      - "pass":          input passes the gate, criterion is included.
      - "fail":          input was evaluated and failed the gate.
      - "not_verified":  the gate input is not (yet) available.

    `detail` is a free-form string describing the underlying number
    (e.g. "Cohen's d = 3.09 (PASS)" or "spot-check not yet completed")
    that is rendered into the audit-trail report.
    """

    status: GateStatus
    detail: str = ""


@dataclass
class CriterionResult:
    """Per-architecture, per-criterion breakdown for one weight profile."""

    name: str
    raw_value: float | None
    normalized: float | None       # None if the criterion was excluded
    weight_default: float          # weight before renormalization (profile)
    weight_renormalized: float     # weight after dropping excluded criteria
    weighted: float | None
    included: bool
    gate_status: GateStatus | None
    gate_detail: str = ""


@dataclass
class ArchitectureResult:
    """One architecture's MCDA result for one weight profile."""

    architecture: str
    profile: str
    composite_score: float
    coverage: list[str]            # included criterion names
    excluded: list[str]            # excluded criterion names
    criterion_results: list[CriterionResult] = field(default_factory=list)


@dataclass
class MCDAResult:
    """All architectures, all weight profiles, plus rankings per profile."""

    profiles: list[str]
    architectures: list[str]
    by_profile: dict[str, list[ArchitectureResult]]   # profile -> sorted by score desc

    def to_dict(self) -> dict:
        return {
            "profiles": list(self.profiles),
            "architectures": list(self.architectures),
            "by_profile": {
                profile: [
                    {
                        "architecture": ar.architecture,
                        "profile": ar.profile,
                        "composite_score": round(ar.composite_score, 4),
                        "coverage": list(ar.coverage),
                        "excluded": list(ar.excluded),
                        "criteria": [
                            {
                                "name": cr.name,
                                "raw_value": cr.raw_value,
                                "normalized": (
                                    None if cr.normalized is None else round(cr.normalized, 4)
                                ),
                                "weight_default": round(cr.weight_default, 4),
                                "weight_renormalized": round(cr.weight_renormalized, 4),
                                "weighted": (
                                    None if cr.weighted is None else round(cr.weighted, 4)
                                ),
                                "included": cr.included,
                                "gate_status": cr.gate_status,
                                "gate_detail": cr.gate_detail,
                            }
                            for cr in ar.criterion_results
                        ],
                    }
                    for ar in self.by_profile[profile]
                ]
                for profile in self.profiles
            },
        }


# ---------------------------------------------------------------------------
# Loading

def load_mcda_config(path: Path | None = None) -> MCDAConfig:
    """Load and validate the MCDA configuration YAML."""
    config_path = path or _MCDA_CONFIG
    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    criteria: dict[str, CriterionSpec] = {}
    for name, c in data["criteria"].items():
        if c["direction"] not in ("benefit", "cost"):
            raise ValueError(
                f"criterion {name!r}: direction must be 'benefit' or 'cost', got {c['direction']!r}"
            )
        criteria[name] = CriterionSpec(
            name=name,
            weight=float(c["weight"]),
            direction=c["direction"],
            aspiration=float(c["aspiration"]),
            anti_aspiration=float(c["anti_aspiration"]),
            metric=c["metric"],
            has_gate="gate" in c,
            rationale=c.get("rationale", ""),
        )

    # Default profile weights must sum to 1 (within tolerance).
    total = sum(c.weight for c in criteria.values())
    if abs(total - 1.0) > 1e-6:
        raise ValueError(
            f"Default-profile weights must sum to 1.0, got {total:.6f}"
        )

    profiles = data.get("sensitivity_profiles", {}) or {}
    for profile_name, weights in profiles.items():
        if set(weights) != set(criteria):
            raise ValueError(
                f"sensitivity profile {profile_name!r} weights must cover exactly "
                f"{sorted(criteria)}, got {sorted(weights)}"
            )
        # Cast each weight to float explicitly so the sum is unambiguously
        # numeric (yaml.safe_load returns Any-typed values; without the
        # cast a strict type checker can infer `s` as int and flag the
        # `1.0` literal below).
        s = sum(float(w) for w in weights.values())
        if abs(s - 1.0) > 1e-6:
            raise ValueError(
                f"sensitivity profile {profile_name!r} weights must sum to 1.0, got {s:.6f}"
            )

    return MCDAConfig(criteria=criteria, sensitivity_profiles=profiles)


# ---------------------------------------------------------------------------
# Normalization

def normalize_aspiration(
    raw: float, *, direction: str, aspiration: float, anti_aspiration: float
) -> float:
    """Aspiration-level normalization to [0, 1] (Tzeng & Huang Form 2).

    For a benefit criterion with aspiration x* and anti-aspiration x-,
    a raw value x normalizes to clip((x - x-)/(x* - x-), 0, 1). For a
    cost criterion the formula is clip((x- - x)/(x- - x*), 0, 1).
    Values better than the aspiration are coerced to 1; values worse
    than the anti-aspiration are coerced to 0.
    """
    if direction == "benefit":
        denom = aspiration - anti_aspiration
        if denom == 0:
            raise ValueError("benefit criterion has aspiration == anti-aspiration")
        r = (raw - anti_aspiration) / denom
    elif direction == "cost":
        denom = anti_aspiration - aspiration
        if denom == 0:
            raise ValueError("cost criterion has aspiration == anti-aspiration")
        r = (anti_aspiration - raw) / denom
    else:
        raise ValueError(f"unknown direction: {direction!r}")
    return max(0.0, min(1.0, r))


# ---------------------------------------------------------------------------
# Gate handling

def _included_for_arch(
    config: MCDAConfig,
    gates: Mapping[str, Mapping[str, GateDecision]],
    arch: str,
) -> dict[str, GateDecision | None]:
    """Resolve gate decisions for one architecture into a per-criterion map.

    Criteria without a configured gate get `None` and are always included.
    Criteria with a gate but no decision in `gates` for this architecture
    raise an error (caller must supply at least a NOT_VERIFIED decision).
    """
    arch_gates = gates.get(arch, {})
    out: dict[str, GateDecision | None] = {}
    for name, spec in config.criteria.items():
        if spec.has_gate:
            decision = arch_gates.get(name)
            if decision is None:
                raise ValueError(
                    f"architecture {arch!r}: criterion {name!r} has a configured "
                    f"gate but no GateDecision was supplied"
                )
            out[name] = decision
        else:
            out[name] = None
    return out


# ---------------------------------------------------------------------------
# Composite-score computation

def compute_mcda(
    arch_metrics: Mapping[str, Mapping[str, float]],
    gates: Mapping[str, Mapping[str, GateDecision]],
    config: MCDAConfig,
    *,
    profiles: Iterable[str] | None = None,
) -> MCDAResult:
    """Compute aspiration-normalized SAW scores per architecture per profile.

    A criterion is included for an architecture iff its gate (if any)
    returns "pass". Excluded criteria's weights are redistributed
    proportionally across the remaining criteria within each profile,
    so all included weights still sum to 1.

    Returns one ArchitectureResult per (architecture, profile), grouped
    by profile and sorted by composite score (descending).
    """
    if not arch_metrics:
        raise ValueError("arch_metrics must contain at least one architecture")

    # Validate that every architecture supplies every metric required.
    required_metrics = {spec.metric for spec in config.criteria.values()}
    for arch, metrics in arch_metrics.items():
        missing = required_metrics - set(metrics)
        if missing:
            raise ValueError(
                f"architecture {arch!r}: missing metrics {sorted(missing)}"
            )

    if profiles is None:
        profiles = ["default", *sorted(config.sensitivity_profiles)]
    profiles = list(profiles)

    by_profile: dict[str, list[ArchitectureResult]] = {}
    for profile in profiles:
        profile_weights = config.weights_for_profile(profile)
        per_arch: list[ArchitectureResult] = []

        for arch, metrics in arch_metrics.items():
            gate_map = _included_for_arch(config, gates, arch)

            # Determine inclusion per criterion.
            included_names: list[str] = []
            for name, spec in config.criteria.items():
                gate = gate_map[name]
                if spec.has_gate:
                    if gate is None:
                        included = False
                    else:
                        included = gate.status == "pass"
                else:
                    included = True
                if included:
                    included_names.append(name)

            # Renormalize weights to sum to 1 across included criteria.
            included_weight_total = sum(profile_weights[n] for n in included_names)
            renormalized: dict[str, float] = {}
            if included_weight_total > 0:
                for name in config.criteria:
                    if name in included_names:
                        renormalized[name] = (
                            profile_weights[name] / included_weight_total
                        )
                    else:
                        renormalized[name] = 0.0
            else:
                # Pathological case: every criterion was excluded.
                renormalized = {name: 0.0 for name in config.criteria}

            criterion_results: list[CriterionResult] = []
            composite = 0.0
            for name, spec in config.criteria.items():
                raw = float(metrics[spec.metric])
                gate = gate_map[name]
                included = name in included_names
                if included:
                    norm = normalize_aspiration(
                        raw,
                        direction=spec.direction,
                        aspiration=spec.aspiration,
                        anti_aspiration=spec.anti_aspiration,
                    )
                    weighted = norm * renormalized[name]
                    composite += weighted
                else:
                    norm = None
                    weighted = None

                criterion_results.append(
                    CriterionResult(
                        name=name,
                        raw_value=raw,
                        normalized=norm,
                        weight_default=profile_weights[name],
                        weight_renormalized=renormalized[name],
                        weighted=weighted,
                        included=included,
                        gate_status=(gate.status if gate is not None else None),
                        gate_detail=(gate.detail if gate is not None else ""),
                    )
                )

            per_arch.append(
                ArchitectureResult(
                    architecture=arch,
                    profile=profile,
                    composite_score=composite,
                    coverage=included_names,
                    excluded=[n for n in config.criteria if n not in included_names],
                    criterion_results=criterion_results,
                )
            )

        per_arch.sort(key=lambda r: r.composite_score, reverse=True)
        by_profile[profile] = per_arch

    return MCDAResult(
        profiles=profiles,
        architectures=list(arch_metrics),
        by_profile=by_profile,
    )
