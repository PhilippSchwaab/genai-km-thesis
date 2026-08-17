"""Per-category KIP recall analysis (supervisor feedback session 4).

Computes KIP recall broken down by KIP category (DEC/ACT/TEC/RAT/ISS),
architecture, and run, from the cached LLM-as-judge outputs
(``kip_eval.json``) of the canonical Run-1 and Run-2 evaluation runs.
No new model calls are made; the script only aggregates cached judgments.

Scoring follows the thesis convention: YES = 1.0, PARTIAL = 0.5, NO = 0.0
(Table `tab:kip-scoring`). Category recall = sum(scores) / n_kips within
the category. Also reports the same breakdown by artifact type
(Type 1 = support reports CS-01..03, Type 2 = dev compilations CS-04..06)
to address RQ2 (do some inputs profit from more processing?).

Usage (from repo root):
    python eval/kip_category_analysis.py [--results eval/results] [--out eval/metrics]

Canonical run selection mirrors run_mcda.py: Run 1 dirs are named
``{arch}_{artifact}_{ts}``, Run 2 dirs ``run_2_{arch}_{artifact}_{ts}``;
``local_*``, ``IO_test*``, and ``*_audience_showcase`` dirs are excluded.
"""

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

SCORE = {"YES": 1.0, "PARTIAL": 0.5, "NO": 0.0}
CATEGORIES = ["DEC", "ACT", "TEC", "RAT", "ISS"]
TYPE1 = {"CS-01", "CS-02", "CS-03"}  # support/PS reports
CANONICAL = re.compile(
    r"^(?P<run>run_2_)?(?P<arch>pipeline|agentic)_(?P<artifact>CS-\d{2})_.*Z$"
)


def collect(results_dir: Path):
    rows = []
    for d in sorted(results_dir.iterdir()):
        m = CANONICAL.match(d.name)
        if not m or not (d / "kip_eval.json").exists():
            continue
        run = "Run 2" if m.group("run") else "Run 1"
        arch = m.group("arch")
        artifact = m.group("artifact")
        data = json.loads((d / "kip_eval.json").read_text())
        for j in data["judgments"]:
            rows.append(
                {
                    "run": run,
                    "arch": arch,
                    "artifact": artifact,
                    "type": "Type 1" if artifact in TYPE1 else "Type 2",
                    "kip_id": j["kip_id"],
                    "category": j["category"],
                    "implicit": j.get("implicit", False),
                    "judgment": j["judgment"],
                    "score": SCORE[j["judgment"]],
                }
            )
    return rows


def aggregate(rows, keys):
    agg = defaultdict(lambda: {"n": 0, "sum": 0.0, "no": 0, "partial": 0})
    for r in rows:
        k = tuple(r[k] for k in keys)
        a = agg[k]
        a["n"] += 1
        a["sum"] += r["score"]
        a["no"] += r["judgment"] == "NO"
        a["partial"] += r["judgment"] == "PARTIAL"
    return {k: {**v, "recall": v["sum"] / v["n"]} for k, v in sorted(agg.items())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="eval/results", type=Path)
    ap.add_argument("--out", default="eval/metrics", type=Path)
    args = ap.parse_args()

    rows = collect(args.results)
    n_runs = len({(r["run"], r["arch"], r["artifact"]) for r in rows})
    assert n_runs == 24, f"expected 24 canonical (run, arch, artifact) cells, got {n_runs}"

    args.out.mkdir(parents=True, exist_ok=True)
    with open(args.out / "kip_category_recall.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["run", "arch", "category", "n_kips", "recall", "n_partial", "n_no"])
        for (run, arch, cat), v in aggregate(rows, ["run", "arch", "category"]).items():
            w.writerow([run, arch, cat, v["n"], f"{v['recall']:.3f}", v["partial"], v["no"]])

    # Console report
    def table(title, keys, colw=14):
        print(f"\n== {title} ==")
        agg = aggregate(rows, keys)
        groups = sorted({k[:-1] for k in agg})
        cats = sorted({k[-1] for k in agg})
        header = " " * colw + "".join(f"{c:>16}" for c in cats)
        print(header)
        for g in groups:
            cells = []
            for c in cats:
                v = agg.get(g + (c,))
                cells.append(f"{v['recall']:.3f} (n={v['n']:>2})" if v else "--")
            print(f"{' / '.join(g):<{colw}}" + "".join(f"{s:>16}" for s in cells))

    table("Recall by category (DEC/ACT/TEC/RAT/ISS)", ["run", "arch", "category"], 20)
    table("Recall by artifact type", ["run", "arch", "type"], 20)

    print("\n== Misses (NO) and PARTIALs ==")
    for r in rows:
        if r["judgment"] != "YES":
            print(
                f"{r['run']} {r['arch']:<9} {r['artifact']} {r['kip_id']} "
                f"[{r['category']}]{' (implicit)' if r['implicit'] else ''}: {r['judgment']}"
            )


if __name__ == "__main__":
    main()
