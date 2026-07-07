#!/usr/bin/env python3
"""KIP agreement audit: validate the existing KIP baseline and the LLM judge
on a random sample of KIPs.

Rationale
---------
Complementary to ``kip_coverage_audit.py`` (which estimates what the manually
extracted KIP baseline *misses* via re-extraction), this audit validates what
the baseline *contains* and how the LLM-as-judge scores it. It supports the
cross-validation recommended in thesis §5.5 ("KIP set and LLM-as-judge
cross-validation") with two estimands, both binomial proportions:

  1. KIP correctness  - for each sampled KIP, the auditor re-reads the source
                        passage (``source_ref``) and marks whether the KIP
                        accurately reflects the source (per sampled KIP).
  2. Judge agreement  - for each sampled KIP, the auditor reads the Run-2
                        generated wiki entries of BOTH architectures and marks
                        whether they agree with the LLM judge's YES/PARTIAL/NO
                        judgment (per sampled KIP x architecture, i.e. two
                        checks per KIP).

Like the coverage audit, results are reported with a Wilson score 95% CI
(Brown, Cai & DasGupta 2001) and the Rule-of-Three 95% upper bound when zero
errors are observed (Hanley & Lippman-Hand 1983). A t-based interval is NOT
appropriate for a proportion near zero at small n.

The sample is seeded and stratified proportionally by artifact so that all six
Control Set artifacts contribute.

Usage
-----
  python eval/kip_agreement_audit.py sample  --target-kips 30 --seed 42
  python eval/kip_agreement_audit.py compute --worksheet eval/agreement_audit/worksheet.csv
  python eval/kip_agreement_audit.py compute --n 60 --errors 0
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
from pathlib import Path

# --- paths -------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
REPO = HERE.parent
KIP_DIR = REPO / "data" / "kips"
RESULTS_DIR = HERE / "results"
OUT_DIR = HERE / "agreement_audit"

Z_95 = 1.959963984540054  # standard normal quantile for a two-sided 95% interval

ARCHITECTURES = {"pipeline": "A", "agentic": "B"}


# --- loading -----------------------------------------------------------------
def load_kips() -> list[dict]:
    """All KIPs across artifacts, with normalized upper-case artifact IDs."""
    kips: list[dict] = []
    for path in sorted(KIP_DIR.glob("cs-*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        artifact_id = str(doc["artifact_id"]).upper()
        for k in doc["kips"]:
            kips.append({"artifact_id": artifact_id, **k})
    return kips


def latest_run2_judgments(artifact_id: str, arch: str) -> dict[str, dict]:
    """kip_id -> judgment row from the newest run_2_<arch>_<artifact>_* result."""
    pattern = f"run_2_{arch}_{artifact_id}_*"
    matches = sorted(RESULTS_DIR.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"no Run-2 results match {pattern}")
    kip_eval = json.loads((matches[-1] / "kip_eval.json").read_text(encoding="utf-8"))
    return {j["kip_id"]: j for j in kip_eval["judgments"]}


# --- statistics (identical basis to kip_coverage_audit) -----------------------
def wilson_interval(errors: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = errors / n
    z2 = Z_95 * Z_95
    denom = 1 + z2 / n
    center = (p + z2 / (2 * n)) / denom
    half = (Z_95 / denom) * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n))
    return (max(0.0, center - half), min(1.0, center + half))


def rule_of_three(n: int) -> float:
    return 3.0 / n if n else 1.0


def report(label: str, errors: int, n: int) -> None:
    lo, hi = wilson_interval(errors, n)
    print(f"\n{label}: {errors}/{n} ({errors / n:.1%})" if n else f"\n{label}: no data")
    print(f"  Wilson 95% CI: [{lo:.1%}, {hi:.1%}]")
    if errors == 0 and n:
        exact = 1.0 - 0.05 ** (1.0 / n)
        print(
            f"  95% upper bound: {exact:.1%} (exact binomial); "
            f"Rule-of-Three approximation: {rule_of_three(n):.1%}"
        )


# --- sample ------------------------------------------------------------------
def cmd_sample(target: int, seed: int) -> None:
    kips = load_kips()
    rng = random.Random(seed)

    # Proportional stratification by artifact (largest-remainder rounding).
    by_artifact: dict[str, list[dict]] = {}
    for k in kips:
        by_artifact.setdefault(k["artifact_id"], []).append(k)
    total = len(kips)
    quotas: dict[str, float] = {a: target * len(v) / total for a, v in by_artifact.items()}
    alloc = {a: int(q) for a, q in quotas.items()}
    for a in sorted(quotas, key=lambda a: quotas[a] - alloc[a], reverse=True):
        if sum(alloc.values()) >= target:
            break
        alloc[a] += 1

    sampled: list[dict] = []
    for artifact in sorted(by_artifact):
        pool = sorted(by_artifact[artifact], key=lambda k: k["id"])
        sampled.extend(rng.sample(pool, min(alloc[artifact], len(pool))))
    rng.shuffle(sampled)

    # Join Run-2 judgments for both architectures.
    # Artifact prefix in results dirs includes the descriptive suffix; glob by CS-ID.
    judgments: dict[tuple[str, str], dict[str, dict]] = {}
    for artifact in by_artifact:
        for arch in ARCHITECTURES:
            judgments[(artifact, arch)] = latest_run2_judgments(artifact, arch)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "worksheet.csv"
    cols = [
        "order", "artifact_id", "kip_id", "category", "implicit", "kip_text",
        "source_ref", "kip_correct(Y/N)",
        "pipeline_judgment", "pipeline_reason", "pipeline_agree(Y/N)",
        "agentic_judgment", "agentic_reason", "agentic_agree(Y/N)",
        "notes",
    ]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for i, k in enumerate(sampled, 1):
            row_j = {
                arch: judgments[(k["artifact_id"], arch)].get(k["id"], {})
                for arch in ARCHITECTURES
            }
            w.writerow([
                i, k["artifact_id"], k["id"], k["category"], k["implicit"],
                k["text"], k.get("source_ref", ""), "",
                row_j["pipeline"].get("judgment", "MISSING"),
                row_j["pipeline"].get("reason", ""), "",
                row_j["agentic"].get("judgment", "MISSING"),
                row_j["agentic"].get("reason", ""), "",
                "",
            ])

    print(f"Sampled {len(sampled)} of {total} KIPs (seed={seed}), stratified by artifact:")
    for a in sorted(alloc):
        print(f"  {a}: {alloc[a]} of {len(by_artifact[a])}")
    print(f"\nWorksheet: {out.relative_to(REPO)}")
    print(
        "\nAuditor instructions:\n"
        "  1. kip_correct(Y/N): re-read the source passage (source_ref) and mark\n"
        "     whether the KIP text accurately reflects it.\n"
        "  2. *_agree(Y/N): open the Run-2 wiki entry of the architecture and mark\n"
        "     whether you agree with the judge's YES/PARTIAL/NO judgment.\n"
        "  Work top to bottom; use notes for anything ambiguous."
    )


# --- compute -----------------------------------------------------------------
def cmd_compute(worksheet: Path | None, n: int | None, errors: int | None) -> None:
    if worksheet is not None:
        rows = list(csv.DictReader(worksheet.open(encoding="utf-8")))
        filled = [r for r in rows if r["kip_correct(Y/N)"].strip()]
        if not filled:
            print("Worksheet has no filled rows yet.")
            return
        kip_n = len(filled)
        kip_err = sum(1 for r in filled if r["kip_correct(Y/N)"].strip().upper() == "N")
        agree_n = agree_err = 0
        for r in filled:
            for col in ("pipeline_agree(Y/N)", "agentic_agree(Y/N)"):
                v = r[col].strip().upper()
                if v:
                    agree_n += 1
                    agree_err += v == "N"
        report("KIP correctness errors", kip_err, kip_n)
        report("Judge disagreements", agree_err, agree_n)
    elif n is not None and errors is not None:
        report("Errors", errors, n)
    else:
        raise SystemExit("compute needs --worksheet or both --n and --errors")


# --- cli ---------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sample")
    s.add_argument("--target-kips", type=int, default=30)
    s.add_argument("--seed", type=int, default=42)
    c = sub.add_parser("compute")
    c.add_argument("--worksheet", type=Path)
    c.add_argument("--n", type=int)
    c.add_argument("--errors", type=int)
    args = ap.parse_args()
    if args.cmd == "sample":
        cmd_sample(args.target_kips, args.seed)
    else:
        cmd_compute(args.worksheet, args.n, args.errors)


if __name__ == "__main__":
    main()
