"""Tests for the MCDA scorer (pure math, no API calls)."""

import pytest

from eval.harness.mcda import MCDAConfig, compute_mcda, load_mcda_config


# ── Config loading ──────────────────────────────────────────────────────


class TestLoadConfig:
    def test_loads_default_weights(self):
        config = load_mcda_config()
        assert config.weights["completeness"] == pytest.approx(0.44)
        assert config.weights["speed"] == pytest.approx(0.33)
        assert config.weights["cost"] == pytest.approx(0.22)

    def test_directions(self):
        config = load_mcda_config()
        assert config.directions["completeness"] == "higher_is_better"
        assert config.directions["speed"] == "lower_is_better"
        assert config.directions["cost"] == "lower_is_better"

    def test_sensitivity_profiles_present(self):
        config = load_mcda_config()
        assert "equal" in config.sensitivity_profiles
        assert "completeness_dominated" in config.sensitivity_profiles
        assert "cost_dominated" in config.sensitivity_profiles

    def test_weights_sum_to_one(self):
        config = load_mcda_config()
        assert sum(config.weights.values()) == pytest.approx(1.0, abs=0.02)


# ── MCDA computation ───────────────────────────────────────────────────


@pytest.fixture()
def config():
    return load_mcda_config()


def _make_run(arch: str, recall: float, latency: float, cost: float) -> dict:
    return {
        "run_dir": f"eval/results/{arch}_test",
        "architecture": arch,
        "artifact_id": "CS-06_test",
        "kip_recall": recall,
        "latency_seconds": latency,
        "cost_usd": cost,
    }


class TestComputeMCDA:
    def test_empty_input(self, config):
        assert compute_mcda([], config) == []

    def test_single_run_gets_perfect_score(self, config):
        """With only one run, all normalized values are 1.0."""
        runs = [_make_run("pipeline", 0.85, 50.0, 0.01)]
        results = compute_mcda(runs, config)
        assert len(results) == 1
        assert results[0].total_score == pytest.approx(1.0, abs=0.02)

    def test_better_run_scores_higher(self, config):
        """A run with better recall, lower latency, and lower cost should win."""
        runs = [
            _make_run("pipeline", 0.90, 40.0, 0.005),  # better on all axes
            _make_run("agentic", 0.80, 60.0, 0.010),   # worse on all axes
        ]
        results = compute_mcda(runs, config)
        # Results sorted descending by score
        assert results[0].architecture == "pipeline"
        assert results[0].total_score > results[1].total_score

    def test_tradeoff_scenario(self, config):
        """Agentic has better recall but worse speed and cost."""
        runs = [
            _make_run("pipeline", 0.80, 30.0, 0.003),
            _make_run("agentic", 0.95, 70.0, 0.015),
        ]
        results = compute_mcda(runs, config)
        # Both should have valid scores between 0 and 1
        for r in results:
            assert 0.0 <= r.total_score <= 1.0
        # The winner depends on weights — with completeness at 0.44,
        # the agentic's 15% recall advantage may or may not overcome
        # its speed/cost penalty
        assert results[0].total_score > results[1].total_score

    def test_sensitivity_profile(self, config):
        """Completeness-dominated weights should favor higher recall."""
        runs = [
            _make_run("pipeline", 0.70, 30.0, 0.003),
            _make_run("agentic", 0.95, 70.0, 0.015),
        ]
        results = compute_mcda(runs, config, weight_profile="completeness_dominated")
        assert results[0].architecture == "agentic"

    def test_cost_dominated_profile(self, config):
        """Cost-dominated weights should favor cheaper runs."""
        runs = [
            _make_run("pipeline", 0.70, 30.0, 0.003),
            _make_run("agentic", 0.95, 70.0, 0.015),
        ]
        results = compute_mcda(runs, config, weight_profile="cost_dominated")
        assert results[0].architecture == "pipeline"

    def test_eur_conversion(self, config):
        """Cost should be converted to EUR in raw_metrics."""
        runs = [_make_run("pipeline", 0.85, 50.0, 0.01)]
        results = compute_mcda(runs, config, eur_per_usd=0.90)
        assert results[0].raw_metrics["cost_eur"] == pytest.approx(0.009)

    def test_identical_runs_get_equal_scores(self, config):
        """Two identical runs should get the same MCDA score."""
        runs = [
            _make_run("pipeline", 0.85, 50.0, 0.01),
            _make_run("agentic", 0.85, 50.0, 0.01),
        ]
        results = compute_mcda(runs, config)
        assert results[0].total_score == pytest.approx(results[1].total_score)
