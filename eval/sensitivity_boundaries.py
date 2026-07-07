#!/usr/bin/env python3
"""Boundary sensitivity analysis: weight break-even and worst-still-acceptable
aspiration values.

Complements the discrete weight-profile sensitivity (thesis §3.3.2, Table
tab:sensitivity-profiles) with two continuous boundary analyses that answer
the reviewer question "what is the worst configuration under which the
recommendation still holds?":

  1. Weight break-even  - for each criterion, vary its default-profile weight
                          one-at-a-time (redistributing the remaining weight
                          proportionally) and solve for the threshold at which
                          the composite ranking between the two architectures
                          flips. Closed form, since the composite is linear in
                          the varied weight.

  2. Aspiration boundary - for each criterion, vary the aspiration value x*
                          over the plausible range and report (a) the value at
                          which the criterion starts to discriminate between
                          the architectures (relevant for the ceiling criteria
                          Accuracy, Cost, Speed, which are capped at r = 1.0)
                          and (b) the value, if any, at which the overall
                          default-profile ranking flips.

Inputs are the exported MCDA results (``eval/metrics/run{1,2}_mcda.json``)
and ``eval/mcda_config.yaml``. Re-run after data collection updates.

Usage
-----
  python eval/sensitivity_boundaries.py            # both runs
  python eval/sensitivity_boundaries.py --run 2
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
METRICS = HERE / "metrics"
CONFIG = HERE / "mcda_config.yaml"

CRITERIA_ORDER = ["accuracy", "verification_effort", "completeness", "speed", "cost"]
# NOTE: "completeness" is the config-level key; the thesis names this criterion
# "Coverage" (renamed 2026-07; code keys kept stable for cached-result parsing).
THESIS_NAME = {"completeness": "coverage"}


def load_run(run: int) -> dict[str, dict[str, dict]]:
    """arch -> criterion name -> {raw_value, normalized, weight_default}."""
    data = json.loads((METRICS / f"run{run}_mcda.json").read_text(encoding="utf-8"))
    out: dict[str, dict[str, dict]] = {}
    for arch_row in data["by_profile"]["default"]:
        out[arch_row["architecture"]] = {c["name"]: c for c in arch_row["criteria"]}
    return out


def load_config() -> dict[str, dict]:
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    return {name: spec for name, spec in cfg["criteria"].items()}


def normalize(raw: float, direction: str, aspiration: float, anti: float) -> float:
    if direction == "benefit":
        r = (raw - anti) / (aspiration - anti)
    else:
        r = (anti - raw) / (anti - aspiration)
    return min(max(r, 0.0), 1.0)


def composite(weights: dict[str, float], normalized: dict[str, float]) -> float:
    return sum(weights[c] * normalized[c] for c in weights)


# --- 1. weight break-even ------------------------------------------------------
def weight_breakeven(run_data: dict, weights: dict[str, float]) -> None:
    norm = {a: {c: run_data[a][c]["normalized"] for c in weights} for a in run_data}
    archs = sorted(norm)
    a, b = archs[0], archs[1]
    base_delta = composite(weights, norm[b]) - composite(weights, norm[a])
    leader = b if base_delta > 0 else a
    print(f"  default-profile composite delta ({b} - {a}): {base_delta:+.4f} -> leader {leader}")

    for c in CRITERIA_ORDER:
        w0 = weights[c]
        d_c = norm[b][c] - norm[a][c]                       # delta on varied criterion
        rest = sum(weights[k] * (norm[b][k] - norm[a][k]) for k in weights if k != c)
        d_rest = rest / (1.0 - w0) if w0 < 1.0 else 0.0     # per unit of remaining weight
        # delta(t) = t*d_c + (1-t)*d_rest ; flip where delta(t) = 0
        label = THESIS_NAME.get(c, c)
        if abs(d_c - d_rest) < 1e-12:
            print(f"    {label:<20} no flip (delta independent of weight)")
            continue
        t = -d_rest / (d_c - d_rest)
        if 0.0 <= t <= 1.0:
            direction = "below" if (d_c - d_rest) * base_delta > 0 else "above"
            print(
                f"    {label:<20} flips when weight moves {direction} "
                f"{t:.3f} (default {w0:.2f})"
            )
        else:
            print(f"    {label:<20} no flip for any weight in [0, 1] (default {w0:.2f})")


# --- 2. aspiration boundary ----------------------------------------------------
def aspiration_boundary(run_data: dict, weights: dict[str, float], cfg: dict) -> None:
    archs = sorted(run_data)
    a, b = archs[0], archs[1]
    raw = {x: {c: run_data[x][c]["raw_value"] for c in weights} for x in run_data}

    for c in CRITERIA_ORDER:
        spec = cfg[c]
        direction, anti = spec["direction"], float(spec["anti_aspiration"])
        asp0 = float(spec["aspiration"])
        best_raw = (max if direction == "benefit" else min)(raw[a][c], raw[b][c])
        label = THESIS_NAME.get(c, c)

        # scan aspiration over the plausible range (anti -> beyond best raw value)
        if direction == "benefit":
            lo, hi = anti + 1e-9, max(best_raw, asp0) * 1.0000001
            grid = [lo + (hi - lo) * i / 4000 for i in range(4001)]
        else:
            hi = anti - 1e-9
            lo = min(best_raw, asp0) * 0.5
            grid = [lo + (hi - lo) * i / 4000 for i in range(4001)]

        discriminates_at = None
        flip_at = None
        base_sign = None
        for asp in grid:
            if abs(asp - anti) < 1e-9:
                continue
            norm = {
                x: {
                    k: (
                        normalize(raw[x][k], direction, asp, anti)
                        if k == c
                        else run_data[x][k]["normalized"]
                    )
                    for k in weights
                }
                for x in run_data
            }
            r_delta = norm[b][c] - norm[a][c]
            if discriminates_at is None and abs(r_delta) > 1e-9:
                discriminates_at = asp
            delta = composite(weights, norm[b]) - composite(weights, norm[a])
            sign = 1 if delta > 0 else (-1 if delta < 0 else 0)
            if base_sign is None and sign != 0:
                base_sign = sign
            if base_sign is not None and sign != 0 and sign != base_sign and flip_at is None:
                flip_at = asp
        disc = f"{discriminates_at:.4g}" if discriminates_at is not None else "never"
        flip = f"{flip_at:.4g}" if flip_at is not None else "none in range"
        print(
            f"    {label:<20} aspiration {asp0:<8g} discriminates from: {disc:<10} "
            f"ranking flip at: {flip}"
        )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", type=int, choices=(1, 2))
    args = ap.parse_args()
    cfg = load_config()
    weights = {name: float(spec["weight"]) for name, spec in cfg.items()}

    for run in ([args.run] if args.run else [1, 2]):
        print(f"\n=== Run {run} ===")
        data = load_run(run)
        print("\n  [1] Weight break-even (one-at-a-time, proportional redistribution):")
        weight_breakeven(data, weights)
        print("\n  [2] Aspiration boundary (worst still-acceptable calibration):")
        aspiration_boundary(data, weights, cfg)


if __name__ == "__main__":
    main()
