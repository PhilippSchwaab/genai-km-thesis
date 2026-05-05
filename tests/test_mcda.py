"""Tests for the aspiration-SAW MCDA scorer (pure math, no API calls).

Covers:
  - mcda_config.yaml parses cleanly under the thesis §3.3.2 spec
  - aspiration-level normalization formulas (Tzeng & Huang Form 2,
    eq. 3.4 and eq. 3.5) at the boundary, midpoint, and clipping cases
  - Simple Additive Weighting end-to-end with all gates passing
  - gate-driven exclusion + weight renormalization
  - sensitivity profile behavior
"""

import pytest

from eval.harness.mcda import (
    GateDecision,
    MCDAConfig,
    compute_mcda,
    load_mcda_config,
    normalize_aspiration,
)


# ── Config loading ──────────────────────────────────────────────────────


class TestLoadConfig:
    def test_loads_default_weights(self):
        config = load_mcda_config()
        assert config.criteria["accuracy"].weight == pytest.approx(0.30)
        assert config.criteria["verification_effort"].weight == pytest.approx(0.25)
        assert config.criteria["completeness"].weight == pytest.approx(0.20)
        assert config.criteria["speed"].weight == pytest.approx(0.15)
        assert config.criteria["cost"].weight == pytest.approx(0.10)

    def test_directions(self):
        config = load_mcda_config()
        assert config.criteria["accuracy"].direction == "benefit"
        assert config.criteria["completeness"].direction == "benefit"
        assert config.criteria["verification_effort"].direction == "cost"
        assert config.criteria["speed"].direction == "cost"
        assert config.criteria["cost"].direction == "cost"

    def test_aspiration_values_match_thesis_table(self):
        """Aspiration ranges match thesis §3.3.2 Table tab:aspirations."""
        config = load_mcda_config()
        assert config.criteria["accuracy"].aspiration == 1.0
        assert config.criteria["accuracy"].anti_aspiration == 0.5
        assert config.criteria["verification_effort"].aspiration == 0.0
        assert config.criteria["verification_effort"].anti_aspiration == 600.0
        assert config.criteria["completeness"].aspiration == 1.0
        assert config.criteria["completeness"].anti_aspiration == 0.0
        assert config.criteria["speed"].aspiration == 5.0
        assert config.criteria["speed"].anti_aspiration == 300.0
        assert config.criteria["cost"].aspiration == 0.05
        assert config.criteria["cost"].anti_aspiration == 1.00

    def test_default_weights_sum_to_one(self):
        config = load_mcda_config()
        assert sum(config.default_weights.values()) == pytest.approx(1.0)

    def test_sensitivity_profiles_present(self):
        config = load_mcda_config()
        assert "equal" in config.sensitivity_profiles
        assert "quality" in config.sensitivity_profiles
        assert "operational" in config.sensitivity_profiles

    def test_sensitivity_profiles_sum_to_one(self):
        config = load_mcda_config()
        for name, weights in config.sensitivity_profiles.items():
            assert sum(weights.values()) == pytest.approx(1.0), name

    def test_gates_configured_on_accuracy_and_verification_effort(self):
        config = load_mcda_config()
        assert config.criteria["accuracy"].has_gate is True
        assert config.criteria["verification_effort"].has_gate is True
        assert config.criteria["completeness"].has_gate is False
        assert config.criteria["speed"].has_gate is False
        assert config.criteria["cost"].has_gate is False


# ── Normalization formulas ─────────────────────────────────────────────


class TestNormalize:
    """Tzeng & Huang Form 2 normalization (thesis eq. 3.4 / 3.5)."""

    def test_benefit_at_aspiration_returns_1(self):
        # raw == aspiration -> r = 1
        assert normalize_aspiration(
            1.0, direction="benefit", aspiration=1.0, anti_aspiration=0.5
        ) == pytest.approx(1.0)

    def test_benefit_at_anti_aspiration_returns_0(self):
        assert normalize_aspiration(
            0.5, direction="benefit", aspiration=1.0, anti_aspiration=0.5
        ) == pytest.approx(0.0)

    def test_benefit_above_aspiration_clips_to_1(self):
        assert normalize_aspiration(
            1.5, direction="benefit", aspiration=1.0, anti_aspiration=0.5
        ) == pytest.approx(1.0)

    def test_benefit_below_anti_aspiration_clips_to_0(self):
        assert normalize_aspiration(
            0.0, direction="benefit", aspiration=1.0, anti_aspiration=0.5
        ) == pytest.approx(0.0)

    def test_benefit_midpoint(self):
        # raw = 0.75, aspiration 1.0, anti 0.5 -> r = (0.75 - 0.5) / 0.5 = 0.5
        assert normalize_aspiration(
            0.75, direction="benefit", aspiration=1.0, anti_aspiration=0.5
        ) == pytest.approx(0.5)

    def test_cost_at_aspiration_returns_1(self):
        # raw == aspiration -> r = 1 even for cost criteria
        assert normalize_aspiration(
            0.0, direction="cost", aspiration=0.0, anti_aspiration=600.0
        ) == pytest.approx(1.0)

    def test_cost_at_anti_aspiration_returns_0(self):
        assert normalize_aspiration(
            600.0, direction="cost", aspiration=0.0, anti_aspiration=600.0
        ) == pytest.approx(0.0)

    def test_cost_below_aspiration_clips_to_1(self):
        assert normalize_aspiration(
            -50.0, direction="cost", aspiration=0.0, anti_aspiration=600.0
        ) == pytest.approx(1.0)

    def test_cost_above_anti_aspiration_clips_to_0(self):
        assert normalize_aspiration(
            900.0, direction="cost", aspiration=0.0, anti_aspiration=600.0
        ) == pytest.approx(0.0)

    def test_cost_verification_effort_observed_run1_values(self):
        """Spot-check the Run 1 review-stats numbers against the formula."""
        # Architecture A: 308 s -> (600 - 308) / (600 - 0) = 0.4867
        assert normalize_aspiration(
            308.0, direction="cost", aspiration=0.0, anti_aspiration=600.0
        ) == pytest.approx(0.4867, abs=1e-4)
        # Architecture B: 123 s -> (600 - 123) / (600 - 0) = 0.7950
        assert normalize_aspiration(
            123.0, direction="cost", aspiration=0.0, anti_aspiration=600.0
        ) == pytest.approx(0.7950, abs=1e-4)

    def test_unknown_direction_raises(self):
        with pytest.raises(ValueError):
            normalize_aspiration(
                0.5, direction="weird", aspiration=1.0, anti_aspiration=0.0
            )


# ── End-to-end SAW with gates ──────────────────────────────────────────


def _all_pass(arches: list[str]) -> dict[str, dict[str, GateDecision]]:
    """Build a gates dict where every gated criterion passes for every arch."""
    return {
        a: {
            "accuracy": GateDecision(status="pass", detail="test"),
            "verification_effort": GateDecision(status="pass", detail="test"),
        }
        for a in arches
    }


def _accuracy_excluded(arches: list[str]) -> dict[str, dict[str, GateDecision]]:
    return {
        a: {
            "accuracy": GateDecision(status="not_verified", detail="test"),
            "verification_effort": GateDecision(status="pass", detail="test"),
        }
        for a in arches
    }


def _all_excluded(arches: list[str]) -> dict[str, dict[str, GateDecision]]:
    return {
        a: {
            "accuracy": GateDecision(status="fail", detail="test"),
            "verification_effort": GateDecision(status="fail", detail="test"),
        }
        for a in arches
    }


def _at_aspiration_metrics() -> dict[str, float]:
    """Raw values at the aspiration on every criterion -> all r=1."""
    return {
        "claim_support_rate": 1.0,
        "kip_recall": 1.0,
        "mean_time_on_task_seconds": 0.0,
        "latency_seconds": 5.0,
        "cost_usd_per_artifact": 0.05,
    }


def _at_anti_aspiration_metrics() -> dict[str, float]:
    return {
        "claim_support_rate": 0.5,
        "kip_recall": 0.0,
        "mean_time_on_task_seconds": 600.0,
        "latency_seconds": 300.0,
        "cost_usd_per_artifact": 1.00,
    }


@pytest.fixture()
def config():
    return load_mcda_config()


class TestComputeMCDA:
    def test_perfect_metrics_with_all_gates_passing_score_1(self, config):
        result = compute_mcda(
            arch_metrics={"A": _at_aspiration_metrics()},
            gates=_all_pass(["A"]),
            config=config,
            profiles=["default"],
        )
        ar = result.by_profile["default"][0]
        assert ar.composite_score == pytest.approx(1.0)
        assert ar.coverage == ["accuracy", "verification_effort", "completeness", "speed", "cost"]
        assert ar.excluded == []

    def test_anti_aspiration_metrics_score_0(self, config):
        result = compute_mcda(
            arch_metrics={"A": _at_anti_aspiration_metrics()},
            gates=_all_pass(["A"]),
            config=config,
            profiles=["default"],
        )
        ar = result.by_profile["default"][0]
        assert ar.composite_score == pytest.approx(0.0)

    def test_excluded_criterion_renormalizes_remaining_weights(self, config):
        """When Accuracy is excluded, remaining default weights should sum to 1
        and an architecture at aspiration on the remaining criteria should
        still score 1.0."""
        metrics = _at_aspiration_metrics()
        result = compute_mcda(
            arch_metrics={"A": metrics},
            gates=_accuracy_excluded(["A"]),
            config=config,
            profiles=["default"],
        )
        ar = result.by_profile["default"][0]
        assert "accuracy" in ar.excluded
        assert ar.composite_score == pytest.approx(1.0)
        # Renormalized weights: original 0.25/0.20/0.15/0.10 -> divide by 0.70
        renorm = {cr.name: cr.weight_renormalized for cr in ar.criterion_results}
        assert renorm["accuracy"] == pytest.approx(0.0)
        assert renorm["verification_effort"] == pytest.approx(0.25 / 0.70, abs=1e-4)
        assert renorm["completeness"] == pytest.approx(0.20 / 0.70, abs=1e-4)
        assert renorm["speed"] == pytest.approx(0.15 / 0.70, abs=1e-4)
        assert renorm["cost"] == pytest.approx(0.10 / 0.70, abs=1e-4)
        assert sum(renorm.values()) == pytest.approx(1.0)

    def test_all_gated_criteria_excluded_renormalizes_to_remaining_three(self, config):
        metrics = _at_aspiration_metrics()
        result = compute_mcda(
            arch_metrics={"A": metrics},
            gates=_all_excluded(["A"]),
            config=config,
            profiles=["default"],
        )
        ar = result.by_profile["default"][0]
        assert set(ar.excluded) == {"accuracy", "verification_effort"}
        assert ar.composite_score == pytest.approx(1.0)
        # Remaining weights 0.20/0.15/0.10 -> sum 0.45, renormalized 0.444/0.333/0.222
        renorm = {cr.name: cr.weight_renormalized for cr in ar.criterion_results}
        assert renorm["completeness"] == pytest.approx(0.20 / 0.45, abs=1e-4)
        assert renorm["speed"] == pytest.approx(0.15 / 0.45, abs=1e-4)
        assert renorm["cost"] == pytest.approx(0.10 / 0.45, abs=1e-4)

    def test_missing_gate_decision_raises(self, config):
        with pytest.raises(ValueError):
            compute_mcda(
                arch_metrics={"A": _at_aspiration_metrics()},
                gates={"A": {}},  # neither accuracy nor verification_effort supplied
                config=config,
                profiles=["default"],
            )

    def test_better_arch_outscores_worse_arch_default(self, config):
        better = {
            "claim_support_rate": 0.95,
            "kip_recall": 0.95,
            "mean_time_on_task_seconds": 100.0,   # faster to verify
            "latency_seconds": 30.0,              # faster end-to-end
            "cost_usd_per_artifact": 0.05,        # cheap
        }
        worse = {
            "claim_support_rate": 0.85,
            "kip_recall": 0.85,
            "mean_time_on_task_seconds": 400.0,
            "latency_seconds": 100.0,
            "cost_usd_per_artifact": 0.50,
        }
        result = compute_mcda(
            arch_metrics={"good": better, "bad": worse},
            gates=_all_pass(["good", "bad"]),
            config=config,
            profiles=["default"],
        )
        ranking = [ar.architecture for ar in result.by_profile["default"]]
        assert ranking == ["good", "bad"]

    def test_quality_profile_favors_completeness_and_accuracy(self, config):
        """Architecture B has higher Accuracy/Completeness but worse Speed/Cost.
        Under the Quality profile (Acc 0.40, VE 0.30, Compl 0.20, Speed 0.05,
        Cost 0.05) B should win."""
        a = {
            "claim_support_rate": 0.80,
            "kip_recall": 0.80,
            "mean_time_on_task_seconds": 200.0,
            "latency_seconds": 30.0,
            "cost_usd_per_artifact": 0.05,
        }
        b = {
            "claim_support_rate": 0.95,
            "kip_recall": 0.95,
            "mean_time_on_task_seconds": 100.0,
            "latency_seconds": 100.0,
            "cost_usd_per_artifact": 0.50,
        }
        result = compute_mcda(
            arch_metrics={"A": a, "B": b},
            gates=_all_pass(["A", "B"]),
            config=config,
            profiles=["quality"],
        )
        winner = result.by_profile["quality"][0].architecture
        assert winner == "B"

    def test_operational_profile_favors_speed_and_cost(self, config):
        a = {
            "claim_support_rate": 0.80,
            "kip_recall": 0.80,
            "mean_time_on_task_seconds": 200.0,
            "latency_seconds": 30.0,
            "cost_usd_per_artifact": 0.05,
        }
        b = {
            "claim_support_rate": 0.95,
            "kip_recall": 0.95,
            "mean_time_on_task_seconds": 100.0,
            "latency_seconds": 100.0,
            "cost_usd_per_artifact": 0.50,
        }
        result = compute_mcda(
            arch_metrics={"A": a, "B": b},
            gates=_all_pass(["A", "B"]),
            config=config,
            profiles=["operational"],
        )
        winner = result.by_profile["operational"][0].architecture
        assert winner == "A"
