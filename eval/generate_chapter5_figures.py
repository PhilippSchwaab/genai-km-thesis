"""Generate the Chapter 5 evaluation figures from the per-artifact CSV
and the two ``run{1,2}_mcda.json`` reports.

The figures follow IBCS (International Business Communication Standards)
notation rules so the comparison between runs and architectures reads
unambiguously:

  - Run 1 is rendered as **Previous Year (PY)** — solid medium-gray
    fill (#7F7F7F).
  - Run 2 is rendered as **Actual (AC)** — solid black fill (#000000).
  - Architectures (Pipeline / Agentic) are distinguished by **position
    grouping**, not by color. Where a single panel must show all four
    series, the group order is Pipeline-PY / Pipeline-AC / gap /
    Agentic-PY / Agentic-AC.
  - Y-axes are anchored at zero unless the data is a signed variance
    (where a zero line is shown explicitly).
  - Direct value labels are placed on bars; legends are used only when
    a panel cannot be unambiguously labeled by axis category.
  - Red / green is reserved for variance display (Run 2 − Run 1) where
    sign is meaningful.

Reference: ``https://www.ibcs.com/standards/`` (notation rules for
data scenarios and the SUCCESS principles).

Outputs are written as PDFs to the LaTeX project's ``figures/``
directory so they can be included with ``\\includegraphics``. Filenames
are stable so a re-run silently overwrites stale charts.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # no display
import matplotlib.pyplot as plt
from matplotlib import rcParams
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
METRICS_DIR = PROJECT_ROOT / "eval" / "metrics"


def _figures_dir() -> Path:
    """Resolve the LaTeX project's figures directory.

    Default is the user's local LaTeX repo. ``THESIS_FIGURES_DIR`` env
    var overrides for sandboxed / CI runs.
    """
    env = os.environ.get("THESIS_FIGURES_DIR")
    if env:
        return Path(env).expanduser().resolve()
    return Path(
        "/Users/philipp/Development/misc/Masterarbeit-Latex-v1/figures"
    ).resolve()


FIGURES_DIR = _figures_dir()


# IBCS scenario palette (canonical):
#   Actual (AC):         solid black
#   Previous Year (PY):  solid medium gray (lighter than AC)
#   Plan (PL):           outlined (white fill, gray border)
#   Forecast (FC):       hatched + framed
# Variance accents (used only for signed deltas):
#   Positive (better):   muted green
#   Negative (worse):    muted red
COLOR_PY = "#7F7F7F"            # Run 1 = Previous Year
COLOR_AC = "#000000"            # Run 2 = Actual
COLOR_VARIANCE_POS = "#3F8C3F"  # green, muted, print-safe
COLOR_VARIANCE_NEG = "#B33A3A"  # red, muted, print-safe
COLOR_HIGHLIGHT = "#1F4E9C"     # used sparingly for emphasis only

# IBCS-friendly typographic tone: small-cap-style category labels,
# direct value labels with single-decimal precision where appropriate.
rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": False,
})


def _save(fig: plt.Figure, name: str) -> None:
    out = FIGURES_DIR / f"{name}.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {out.name}")


def _load_per_artifact() -> list[dict]:
    rows: list[dict] = []
    with (METRICS_DIR / "per_artifact.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            for k in ("latency_seconds", "cost_usd", "kip_recall"):
                v = r.get(k)
                r[k] = float(v) if v not in (None, "", "None") else None
            rows.append(r)
    return rows


def _load_mcda(label: str) -> dict:
    return json.loads((METRICS_DIR / f"{label}_mcda.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Helpers

def _direct_label(ax, x, y, text, *, va="bottom", offset_pts=2,
                  fontsize=6.5, rotation=0):
    """Annotate a bar with a direct value label (IBCS principle: prefer
    direct labels over legends/axes ticks when space allows).

    ``rotation=90`` produces a vertical label (reading bottom-up),
    which is the typical fix for dense per-artifact charts where
    horizontal labels would overlap adjacent bars.
    """
    ax.annotate(
        text, xy=(x, y), xytext=(0, offset_pts),
        textcoords="offset points",
        ha="center", va=va, fontsize=fontsize, rotation=rotation,
    )


def _ibcs_style(ax) -> None:
    """Apply IBCS-style axes: minimal spines, faint baseline, no top
    grid, no right axis. Y-axis tick labels are kept (numbers).
    """
    ax.spines["left"].set_color("#666666")
    ax.spines["bottom"].set_color("#666666")
    ax.tick_params(colors="#333333", length=2)
    ax.axhline(0, color="#000000", linewidth=0.6, zorder=0)


def _scenario_handles():
    """Run-scenario legend handles. Color encoding follows IBCS
    PY (medium gray) / AC (black) but the legend uses plain "Run 1"
    / "Run 2" wording so a reader unfamiliar with IBCS notation can
    read the chart without consulting the notation paragraph in
    Section 5.2."""
    from matplotlib.patches import Patch
    return [
        Patch(facecolor=COLOR_PY, edgecolor="none", label="Run 1"),
        Patch(facecolor=COLOR_AC, edgecolor="none", label="Run 2"),
    ]


# ---------------------------------------------------------------------------
# Per-artifact small multiples (cost, latency, KIP)

def per_artifact_small_multiples(
    rows: list[dict], metric: str, ylabel: str, name: str,
    *, fmt: str = "{:.2f}", ylim: tuple[float, float] | None = None,
) -> None:
    """One panel per architecture. Within each panel: per artifact two
    bars side by side (Run 1 / Previous Year and Run 2 / Actual).

    This is the cleanest IBCS-aligned layout for the Run 1 -> Run 2
    comparison since the two scenarios sit immediately adjacent to
    each other on every artifact.
    """
    artifacts = sorted({r["artifact_short"] for r in rows})
    by_key = {(r["run"], r["arch_name"], r["artifact_short"]): r[metric] for r in rows}

    # Per-architecture panels use independent y-axes because the
    # cost / latency ranges differ by up to 5x between architectures
    # in Run 1; a shared scale would clip Agentic bars and mislead
    # the within-architecture Run 1 -> Run 2 comparison that is the
    # main message of these figures. Cross-architecture comparison
    # is supported by the aggregate-means figure (Figure
    # \ref{fig:ch5-aggregate-means}).
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 3.8), sharey=False)
    architectures = [("pipeline", "Pipeline"), ("agentic", "Agentic")]

    for ax, (arch, title) in zip(axes, architectures):
        x = np.arange(len(artifacts))
        bw = 0.32  # narrower bars => wider gap for direct labels
        py_vals = [by_key.get(("Run 1", arch, a)) or 0.0 for a in artifacts]
        ac_vals = [by_key.get(("Run 2", arch, a)) or 0.0 for a in artifacts]

        bars_py = ax.bar(x - bw / 2, py_vals, bw,
                         color=COLOR_PY, edgecolor="none",
                         label="Run 1")
        bars_ac = ax.bar(x + bw / 2, ac_vals, bw,
                         color=COLOR_AC, edgecolor="none",
                         label="Run 2")
        # IBCS-aligned label policy: when Run 1 and Run 2 are
        # numerically equivalent (within ~1 % of axis range) we show
        # a single label centered between the two bars instead of
        # repeating the same number twice. This honours the IBCS
        # rule "things that are the same should look the same":
        # two identical labels add no information and crowd dense
        # panels. When values differ, both labels are shown above
        # their respective bar.
        ymax = max([*py_vals, *ac_vals]) or 1.0
        same_threshold = ymax * 0.012
        for bar_py, bar_ac, v_py, v_ac in zip(
            bars_py, bars_ac, py_vals, ac_vals
        ):
            equal = abs(v_py - v_ac) < same_threshold
            x_center = (bar_py.get_x() + bar_py.get_width() / 2
                        + bar_ac.get_x() + bar_ac.get_width() / 2) / 2
            if equal:
                # One label centered over the (PY, AC) pair.
                _direct_label(ax, x_center, max(v_py, v_ac),
                              fmt.format(v_py))
            else:
                _direct_label(ax, bar_py.get_x() + bar_py.get_width() / 2,
                              v_py, fmt.format(v_py))
                _direct_label(ax, bar_ac.get_x() + bar_ac.get_width() / 2,
                              v_ac, fmt.format(v_ac))
        ax.set_xticks(x)
        ax.set_xticklabels(artifacts)
        ax.set_title(title, loc="left")
        # Headroom so direct labels don't kiss the top of the panel.
        if ylim is not None:
            ax.set_ylim(*ylim)
        else:
            ymax = max([*py_vals, *ac_vals]) or 1.0
            ax.set_ylim(0, ymax * 1.12)
        _ibcs_style(ax)
    axes[0].set_ylabel(ylabel)
    axes[1].set_ylabel(ylabel)  # repeat label since y-axes are independent
    # Single legend below the figure so it never overlaps bars.
    fig.legend(handles=_scenario_handles(), loc="lower center",
               frameon=False, fontsize=7, ncol=2,
               bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    _save(fig, name)


# ---------------------------------------------------------------------------
# Aggregate means: 3 panels (Latency, Cost, KIP) with PY/AC scenario bars.

def aggregate_means(rows: list[dict]) -> None:
    metrics = [
        ("latency_seconds", "Mean latency (s)", "{:.1f}"),
        ("cost_usd",        "Mean cost (USD)", "{:.4f}"),
        ("kip_recall",      "Mean KIP recall", "{:.3f}"),
    ]
    # Stack vertically: each panel takes full text-width when included
    # via \includegraphics[width=\textwidth], so labels stay legible.
    fig, axes = plt.subplots(len(metrics), 1, figsize=(7.0, 7.5))

    for ax, (metric, ylabel, fmt) in zip(axes, metrics):
        groups = ["Pipeline", "Agentic"]
        py_vals: list[float] = []
        ac_vals: list[float] = []
        for arch in ("pipeline", "agentic"):
            for run, store in (("Run 1", py_vals), ("Run 2", ac_vals)):
                vals = [r[metric] for r in rows
                        if r["run"] == run and r["arch_name"] == arch
                        and r[metric] is not None]
                store.append(sum(vals) / len(vals) if vals else 0.0)
        x = np.arange(len(groups))
        bw = 0.34
        bars_py = ax.bar(x - bw / 2, py_vals, bw,
                         color=COLOR_PY, edgecolor="none", label="Run 1")
        bars_ac = ax.bar(x + bw / 2, ac_vals, bw,
                         color=COLOR_AC, edgecolor="none", label="Run 2")
        ymax = max([*py_vals, *ac_vals]) or 1.0
        same_threshold = ymax * 0.012
        for bar_py, bar_ac, v_py, v_ac in zip(
            bars_py, bars_ac, py_vals, ac_vals
        ):
            close = abs(v_py - v_ac) < same_threshold
            _direct_label(ax, bar_py.get_x() + bar_py.get_width() / 2,
                          v_py, fmt.format(v_py), fontsize=8)
            offset = 11 if close else 2
            _direct_label(ax, bar_ac.get_x() + bar_ac.get_width() / 2,
                          v_ac, fmt.format(v_ac), offset_pts=offset,
                          fontsize=8)
        ax.set_xticks(x)
        ax.set_xticklabels(groups, fontsize=9)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.tick_params(labelsize=9)
        ax.set_ylim(bottom=0)
        _ibcs_style(ax)
    fig.legend(handles=_scenario_handles(), loc="lower center",
               frameon=False, fontsize=7, ncol=2,
               bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    _save(fig, "ch5_aggregate_means")


# ---------------------------------------------------------------------------
# MCDA composite scores by profile, both runs

def mcda_profiles(run1: dict, run2: dict) -> None:
    """Four panels (one per sensitivity profile) with PY/AC scenario
    bars per architecture. Y-axis anchored at 0 (IBCS principle).
    """
    profile_pretty = {
        "default": "Default", "equal": "Equal",
        "operational": "Operational", "quality": "Quality",
    }
    profiles = run1["profiles"]

    def get_score(d, profile, arch):
        for ar in d["by_profile"][profile]:
            if ar["architecture"] == arch:
                return ar["composite_score"]
        return None

    fig, axes = plt.subplots(1, len(profiles), figsize=(13.0, 4.0),
                             sharey=True)
    architectures = [("A", "Pipeline"), ("B", "Agentic")]
    for ax, profile in zip(axes, profiles):
        x = np.arange(len(architectures))
        bw = 0.34
        py_vals = [get_score(run1, profile, arch) for arch, _ in architectures]
        ac_vals = [get_score(run2, profile, arch) for arch, _ in architectures]
        bars_py = ax.bar(x - bw / 2, py_vals, bw,
                         color=COLOR_PY, edgecolor="none")
        bars_ac = ax.bar(x + bw / 2, ac_vals, bw,
                         color=COLOR_AC, edgecolor="none")
        same_threshold = 0.012  # ~1.2pp on a 0..1 axis
        for bar_py, bar_ac, v_py, v_ac in zip(
            bars_py, bars_ac, py_vals, ac_vals
        ):
            close = abs(v_py - v_ac) < same_threshold
            _direct_label(ax, bar_py.get_x() + bar_py.get_width() / 2,
                          v_py, f"{v_py:.3f}", fontsize=8)
            offset = 11 if close else 2
            _direct_label(ax, bar_ac.get_x() + bar_ac.get_width() / 2,
                          v_ac, f"{v_ac:.3f}", offset_pts=offset,
                          fontsize=8)
        ax.set_xticks(x)
        ax.set_xticklabels([n for _, n in architectures], fontsize=9)
        ax.set_title(profile_pretty[profile], loc="left", fontsize=11)
        ax.tick_params(labelsize=9)
        ax.set_ylim(0, 1.0)
        _ibcs_style(ax)
    axes[0].set_ylabel("Composite score")
    fig.legend(handles=_scenario_handles(), loc="lower center",
               frameon=False, fontsize=7, ncol=2,
               bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    _save(fig, "ch5_mcda_profiles")


# ---------------------------------------------------------------------------
# Variance: Run 1 -> Run 2 normalized score delta per criterion

def run_delta(run1: dict, run2: dict) -> None:
    """Per criterion, plot the **normalized** score delta (Run 2 -
    Run 1). Higher is always better (normalized values are in [0, 1]
    with 1 = aspiration met).

    IBCS variance notation: positive (better) bars in green, negative
    (worse) in red. Architecture distinction is by position only.
    """
    criteria = ["accuracy", "verification_effort", "completeness", "speed", "cost"]
    arch_label = {"A": "Pipeline", "B": "Agentic"}

    def norm_by_crit(d, arch):
        for ar in d["by_profile"]["default"]:
            if ar["architecture"] == arch:
                return {cr["name"]: cr["normalized"] for cr in ar["criteria"]}
        return {}

    fig, axes = plt.subplots(1, 2, figsize=(10.0, 3.6), sharey=True)
    for ax, arch in zip(axes, ("A", "B")):
        before = norm_by_crit(run1, arch)
        after = norm_by_crit(run2, arch)
        deltas = [after.get(c, 0.0) - before.get(c, 0.0) for c in criteria]
        x = np.arange(len(criteria))
        colors = [COLOR_VARIANCE_POS if d >= 0 else COLOR_VARIANCE_NEG
                  for d in deltas]
        bars = ax.bar(x, deltas, 0.55, color=colors, edgecolor="none")
        for bar, v in zip(bars, deltas):
            offset = (1 if v >= 0 else -1) * 2
            ax.annotate(
                f"{v:+.3f}",
                xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                xytext=(0, offset), textcoords="offset points",
                ha="center", va=("bottom" if v >= 0 else "top"),
                fontsize=7,
            )
        ax.set_xticks(x)
        ax.set_xticklabels(
            [c.replace("_", " ").capitalize() for c in criteria],
            rotation=18, ha="right",
        )
        ax.set_title(arch_label[arch], loc="left")
        _ibcs_style(ax)
    axes[0].set_ylabel(r"Normalized score delta (Run 2 - Run 1)")
    fig.tight_layout()
    _save(fig, "ch5_run1_vs_run2_delta")


# ---------------------------------------------------------------------------
# Run 2 agentic token-tier breakdown (no Run 1 comparison; AC-only).

def token_breakdown(rows: list[dict], all_meta: dict) -> None:
    """Stacked bar of agentic token usage per artifact for Run 2 only.

    Tier ordering bottom-to-top: cache read, cache write, standard
    input, output. Monochrome grayscale gradient (lightest at bottom)
    so the four tiers read as a single quantity sliced by source,
    consistent with IBCS principle of using shape / position rather
    than rainbow color.
    """
    artifacts = sorted({r["artifact_short"] for r in rows
                        if r["run"] == "Run 2" and r["arch_name"] == "agentic"})
    cache_reads, cache_writes, standard_input, output = [], [], [], []
    for art in artifacts:
        m = all_meta[("Run 2", "agentic", art)]
        pt = int(m.get("prompt_tokens", 0))
        cr = int(m.get("cache_read_input_tokens", 0))
        cw = int(m.get("cache_creation_input_tokens", 0))
        si = pt - cr - cw
        cache_reads.append(cr)
        cache_writes.append(cw)
        standard_input.append(si)
        output.append(int(m.get("completion_tokens", 0)))

    fig, ax = plt.subplots(figsize=(8.5, 3.4))
    x = np.arange(len(artifacts))
    bw = 0.55
    layers = [
        ("Cache read input",  cache_reads,    "#D9D9D9"),
        ("Cache write input", cache_writes,   "#A6A6A6"),
        ("Standard input",    standard_input, "#595959"),
        ("Output",            output,         "#000000"),
    ]
    bottom = np.zeros(len(artifacts))
    for label, vals, color in layers:
        ax.bar(x, vals, bw, bottom=bottom,
               label=label, color=color, edgecolor="none")
        bottom = bottom + np.array(vals)
    # Direct totals on top of each stack
    for xi, total in zip(x, bottom):
        _direct_label(ax, xi, total, f"{int(total):,}")
    ax.set_xticks(x)
    ax.set_xticklabels(artifacts)
    ax.set_xlabel("Artifact")
    ax.set_ylabel("Tokens")
    ax.set_ylim(bottom=0)
    _ibcs_style(ax)
    ax.legend(loc="upper right", frameon=False, fontsize=7,
              ncol=2)
    fig.tight_layout()
    _save(fig, "ch5_agentic_token_breakdown")


# ---------------------------------------------------------------------------
# Reviewer iterations (Run 2 agentic only). AC-only, single-bar series.

def reviewer_iterations(rows: list[dict]) -> None:
    items = sorted(
        [r for r in rows if r["run"] == "Run 2" and r["arch_name"] == "agentic"],
        key=lambda r: r["artifact_short"],
    )
    artifacts = [r["artifact_short"] for r in items]
    iterations = [int(r["reviewer_iterations"]) for r in items]

    fig, ax = plt.subplots(figsize=(7.5, 3.0))
    bars = ax.bar(np.arange(len(artifacts)), iterations,
                  width=0.55, color=COLOR_AC, edgecolor="none")
    # Cap line as a horizontal reference, NOT a category bar
    ax.axhline(3, color=COLOR_VARIANCE_NEG, linestyle="--",
               linewidth=0.8)
    ax.text(len(artifacts) - 0.5, 3.05, "max_iterations cap",
            color=COLOR_VARIANCE_NEG, fontsize=7, ha="right", va="bottom")
    for bar, n in zip(bars, iterations):
        _direct_label(ax, bar.get_x() + bar.get_width() / 2,
                      bar.get_height(), str(n))
    ax.set_xticks(np.arange(len(artifacts)))
    ax.set_xticklabels(artifacts)
    ax.set_xlabel("Artifact (Run 2, agentic only)")
    ax.set_ylabel("Reviewer iterations")
    ax.set_yticks(range(0, 4))
    ax.set_ylim(0, 3.5)
    _ibcs_style(ax)
    fig.tight_layout()
    _save(fig, "ch5_reviewer_iterations")


# ---------------------------------------------------------------------------
# Driver

def main() -> int:
    print("Loading data ...")
    rows = _load_per_artifact()
    run1 = _load_mcda("run1")
    run2 = _load_mcda("run2")

    all_meta: dict[tuple, dict] = {}
    for r in rows:
        if r["run"] == "Run 2" and r["arch_name"] == "agentic":
            md = PROJECT_ROOT / "eval" / "results" / r["run_dir"] / "metadata.json"
            if md.exists():
                all_meta[("Run 2", "agentic", r["artifact_short"])] = json.loads(
                    md.read_text(encoding="utf-8"))

    print(f"Writing IBCS-styled figures to {FIGURES_DIR}")
    per_artifact_small_multiples(
        rows, "cost_usd", "Cost per artifact (USD)",
        "ch5_cost_per_artifact", fmt="{:.4f}",
    )
    per_artifact_small_multiples(
        rows, "latency_seconds", "End-to-end latency (s)",
        "ch5_latency_per_artifact", fmt="{:.1f}",
    )
    per_artifact_small_multiples(
        rows, "kip_recall", "KIP recall",
        "ch5_kip_per_artifact", fmt="{:.3f}",
        ylim=(0, 1.05),
    )
    aggregate_means(rows)
    mcda_profiles(run1, run2)
    run_delta(run1, run2)
    token_breakdown(rows, all_meta)
    reviewer_iterations(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
