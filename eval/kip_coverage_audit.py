#!/usr/bin/env python3
"""KIP coverage audit: estimate the false-negative (miss) rate of the manually
extracted KIP gold standard via independent re-extraction on a random sample of
source passages.

Rationale
---------
The KIP registry is a single-extractor instrument with no external gold standard,
so its *coverage* (whether it misses documentation-relevant facts that a second
pass would find) is unverified. This script supports a self-administered coverage
audit:

  1. ``sample``  - segment the anonymized source artifacts into passages, draw a
                   reproducible (seeded), artifact-stratified ordering, and emit a
                   worksheet. The auditor works through the passages in order,
                   re-extracting every documentation-relevant fact per the KIP
                   extraction guideline, until ~N facts have been collected. Each
                   re-extracted fact is marked covered (reflected by an existing
                   KIP) or missed.

  2. ``compute`` - read the filled worksheet (or take counts directly) and report
                   the observed miss rate with a Wilson score 95% CI, plus the
                   Rule-of-Three upper bound when zero misses are observed.

The per-fact outcome is binary (covered / missed), so the estimand is a binomial
proportion. The Wilson score interval is recommended for small n (Brown, Cai &
DasGupta 2001); the Rule of Three (Hanley & Lippman-Hand 1983) gives the 95%
upper bound when the observed count is zero. A t-test/normal interval is NOT
appropriate for a proportion near zero at small n.

Usage
-----
  python eval/kip_coverage_audit.py sample  --target-facts 30 --seed 42
  python eval/kip_coverage_audit.py compute --worksheet eval/coverage_audit/worksheet.csv
  python eval/kip_coverage_audit.py compute --n 30 --misses 0
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
import re
from pathlib import Path

# --- paths -------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
REPO = HERE.parent
KIP_DIR = REPO / "data" / "kips"
SRC_DIR = REPO / "data" / "anonymized"
OUT_DIR = HERE / "coverage_audit"

Z_95 = 1.959963984540054  # standard normal quantile for a two-sided 95% interval


# --- segmentation ------------------------------------------------------------
def _segment_support_report(text: str) -> list[tuple[str, str]]:
    """Split a support/PS report into page units on the ``<!-- Page N -->`` markers."""
    parts = re.split(r"<!--\s*Page\s+(\d+)\s*-->", text)
    units: list[tuple[str, str]] = []
    # re.split with one capture group yields: [pre, n1, body1, n2, body2, ...]
    for i in range(1, len(parts), 2):
        page_no = parts[i].strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        if body:
            units.append((f"p.{page_no}", body))
    return units


def _segment_dev_compilation(text: str) -> list[tuple[str, str]]:
    """Split a dev compilation into ``## `` top-level sections."""
    units: list[tuple[str, str]] = []
    current_label = "preamble"
    buf: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if buf and "".join(buf).strip():
                units.append((current_label, "\n".join(buf).strip()))
            current_label = line[3:].strip()
            buf = []
        else:
            buf.append(line)
    if buf and "".join(buf).strip():
        units.append((current_label, "\n".join(buf).strip()))
    return units


def load_artifacts() -> list[dict]:
    """Load each artifact's source text, type, and existing KIPs."""
    artifacts = []
    for kip_path in sorted(KIP_DIR.glob("cs-0*.json")):
        meta = json.loads(kip_path.read_text(encoding="utf-8"))
        src_path = SRC_DIR / meta["source_file"]
        text = src_path.read_text(encoding="utf-8")
        if meta["artifact_type"] == "support_report":
            units = _segment_support_report(text)
        else:
            units = _segment_dev_compilation(text)
        artifacts.append(
            {
                "artifact_id": meta["artifact_id"].upper(),
                "type": meta["artifact_type"],
                "n_kips": len(meta["kips"]),
                "units": units,
            }
        )
    return artifacts


# --- sampling ----------------------------------------------------------------
def make_worksheet(target_facts: int, seed: int) -> Path:
    artifacts = load_artifacts()
    rng = random.Random(seed)

    # Shuffle each artifact's units independently, then interleave (round-robin)
    # so the early part of the worksheet spans all artifacts (stratification).
    per_artifact = []
    for art in artifacts:
        units = list(art["units"])
        rng.shuffle(units)
        per_artifact.append((art["artifact_id"], units))

    ordered: list[tuple[str, str, str]] = []  # (artifact_id, unit_label, body)
    idx = 0
    while any(idx < len(u) for _, u in per_artifact):
        for art_id, units in per_artifact:
            if idx < len(units):
                label, body = units[idx]
                ordered.append((art_id, label, body))
        idx += 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    worksheet = OUT_DIR / "worksheet.csv"
    with worksheet.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "order", "artifact_id", "unit_label", "fact_id",
                "fact_text", "covered(Y/N)", "matched_kip_id", "notes",
            ]
        )
        for order, (art_id, label, _body) in enumerate(ordered, start=1):
            # One blank fact row per passage as a starting point; the auditor
            # adds more rows (same order/unit_label) for passages with >1 fact,
            # and leaves fact_text blank for passages with no facts.
            w.writerow([order, art_id, label, "", "", "", "", ""])

    # Human-readable companion with the passage texts, in worksheet order.
    passages_md = OUT_DIR / "passages.md"
    with passages_md.open("w", encoding="utf-8") as fh:
        fh.write(f"# KIP coverage audit - sampled passages (seed={seed})\n\n")
        fh.write(
            f"Target: ~{target_facts} independently re-extracted facts. Work through "
            "passages in order. For each passage, re-extract every atomic, verifiable, "
            "documentation-relevant fact (per docs/kip_extraction_guideline.md). For each "
            "fact, check the existing KIP registry for that artifact and mark it covered "
            "(Y + matched_kip_id) or missed (N). Stop once you reach the target count.\n\n"
        )
        for order, (art_id, label, body) in enumerate(ordered, start=1):
            fh.write(f"## [{order}] {art_id} - {label}\n\n")
            fh.write(body + "\n\n---\n\n")

    return worksheet


# --- statistics --------------------------------------------------------------
def wilson_interval(k: int, n: int, z: float = Z_95) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion (k successes in n trials)."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z / denom) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, centre - half), min(1.0, centre + half))


def rule_of_three(n: int) -> tuple[float, float]:
    """95% upper bound on the rate when zero events are observed.
    Returns (exact, approx) where exact = 1 - 0.05**(1/n) and approx = 3/n."""
    if n == 0:
        return (1.0, 1.0)
    return (1 - 0.05 ** (1 / n), 3 / n)


def compute_from_counts(n: int, misses: int) -> None:
    if misses > n:
        raise SystemExit("misses cannot exceed n")
    p = misses / n if n else 0.0
    lo, hi = wilson_interval(misses, n)
    print(f"\nIndependently re-extracted facts (n) : {n}")
    print(f"Facts not covered by any KIP (misses): {misses}")
    print(f"Observed miss rate                   : {p:.4f} ({p*100:.1f}%)")
    print(f"Wilson 95% CI on miss rate           : [{lo*100:.1f}%, {hi*100:.1f}%]")
    if misses == 0:
        exact, approx = rule_of_three(n)
        print(f"Rule of Three 95% upper bound        : {approx*100:.1f}% (3/n); "
              f"exact 1-0.05^(1/n) = {exact*100:.1f}%")
        print(
            "\nLaTeX-ready claim:\n"
            f"  In an independent re-extraction yielding {n} documentation-relevant "
            f"facts, all were reflected in the existing KIP registry. With zero observed "
            f"omissions, the KIP set's miss rate is below {exact*100:.1f}\\,\\% at the "
            f"95\\,\\% level (exact binomial; rule-of-three approximation "
            f"{approx*100:.1f}\\,\\%)."
        )
    else:
        print(
            "\nLaTeX-ready claim:\n"
            f"  In an independent re-extraction yielding {n} documentation-relevant "
            f"facts, {misses} were not reflected in the existing KIP registry "
            f"(miss rate {p*100:.1f}\\,\\%, Wilson 95\\,\\% CI "
            f"[{lo*100:.1f}\\,\\%, {hi*100:.1f}\\,\\%])."
        )


def compute_from_worksheet(path: Path) -> None:
    n = 0
    misses = 0
    unmarked: list[str] = []
    with path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if not (row.get("fact_text") or "").strip():
                continue  # passage row with no fact recorded
            verdict = (row.get("covered(Y/N)") or "").strip().upper()
            if not verdict.startswith(("Y", "N")):
                unmarked.append(row.get("order", "?"))
                continue  # do not count silently; must be resolved
            n += 1
            if verdict.startswith("N"):
                misses += 1
    if unmarked:
        print(
            f"WARNING: {len(unmarked)} fact row(s) without a Y/N verdict "
            f"(order: {', '.join(unmarked)}) — excluded from the counts. "
            "Mark them or clear their fact_text, then re-run."
        )
    compute_from_counts(n, misses)


# --- cli ---------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("sample", help="generate the seeded sampling worksheet")
    s.add_argument("--target-facts", type=int, default=30)
    s.add_argument("--seed", type=int, default=42)

    c = sub.add_parser("compute", help="compute the miss-rate CI")
    c.add_argument("--worksheet", type=Path)
    c.add_argument("--n", type=int)
    c.add_argument("--misses", type=int)

    args = ap.parse_args()
    if args.cmd == "sample":
        ws = make_worksheet(args.target_facts, args.seed)
        print(f"Wrote worksheet : {ws}")
        print(f"Wrote passages  : {ws.parent / 'passages.md'}")
        print(f"(seed={args.seed}, target ~{args.target_facts} facts)")
    elif args.cmd == "compute":
        if args.worksheet:
            compute_from_worksheet(args.worksheet)
        elif args.n is not None and args.misses is not None:
            compute_from_counts(args.n, args.misses)
        else:
            raise SystemExit("provide --worksheet, or both --n and --misses")


if __name__ == "__main__":
    main()
