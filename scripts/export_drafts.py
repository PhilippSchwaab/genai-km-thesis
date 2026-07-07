"""Export wiki_entry.md files from eval/results as blinded drafts.

Pipeline runs -> draft_<artifact_id>_A.md
Agentic runs  -> draft_<artifact_id>_B.md

Usage:
    python scripts/export_drafts.py <destination>
    python scripts/export_drafts.py <destination> --date 20260417
    python scripts/export_drafts.py <destination> --timestamp-prefix 20260417T08
    python scripts/export_drafts.py <destination> --include-local
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

RESULTS_DIR = Path(__file__).resolve().parent.parent / "eval" / "results"

DIR_PATTERN = re.compile(
    r"^(?P<local>local_)?(?P<variant>agentic|pipeline)_"
    r"(?P<artifact>CS-\d+)_.*_(?P<timestamp>\d{8}T\d{6}Z)$"
)

VARIANT_TO_LABEL = {"pipeline": "A", "agentic": "B"}


@dataclass
class Run:
    path: Path
    variant: str
    artifact: str
    timestamp: str
    is_local: bool


def discover_runs(results_dir: Path) -> list[Run]:
    runs: list[Run] = []
    for entry in results_dir.iterdir():
        if not entry.is_dir():
            continue
        match = DIR_PATTERN.match(entry.name)
        if not match:
            continue
        runs.append(
            Run(
                path=entry,
                variant=match["variant"],
                artifact=match["artifact"],
                timestamp=match["timestamp"],
                is_local=bool(match["local"]),
            )
        )
    return runs


def filter_runs(
    runs: list[Run],
    *,
    include_local: bool,
    timestamp_prefix: str | None,
) -> list[Run]:
    filtered = [r for r in runs if include_local or not r.is_local]
    if timestamp_prefix:
        filtered = [r for r in filtered if r.timestamp.startswith(timestamp_prefix)]
    return filtered


def pick_latest(runs: list[Run]) -> list[Run]:
    latest: dict[tuple[str, str], Run] = {}
    for run in runs:
        key = (run.variant, run.artifact)
        current = latest.get(key)
        if current is None or run.timestamp > current.timestamp:
            latest[key] = run
    return list(latest.values())


def export(runs: list[Run], destination: Path, *, keep_all: bool) -> list[Path]:
    destination.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for run in runs:
        source = run.path / "wiki_entry.md"
        if not source.exists():
            print(f"skip {run.path.name}: no wiki_entry.md", file=sys.stderr)
            continue
        label = VARIANT_TO_LABEL[run.variant]
        suffix = f"_{run.timestamp}" if keep_all else ""
        local_tag = "_local" if run.is_local else ""
        target = destination / f"draft_{run.artifact}_{label}{local_tag}{suffix}.md"
        shutil.copy2(source, target)
        written.append(target)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument(
        "--timestamp-prefix",
        help="Only include runs whose timestamp starts with this prefix "
        "(e.g. 20260417 for a single day, 20260417T08 for an hour).",
    )
    parser.add_argument(
        "--date",
        help="Shortcut for --timestamp-prefix using YYYYMMDD.",
    )
    parser.add_argument(
        "--include-local",
        action="store_true",
        help="Include local_* runs (Ollama). Off by default.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Export every matching run (timestamp suffixed). "
        "Without this, only the latest run per (variant, artifact) is exported.",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=RESULTS_DIR,
        help=f"Override results directory (default: {RESULTS_DIR}).",
    )
    args = parser.parse_args()

    if args.date and args.timestamp_prefix:
        parser.error("--date and --timestamp-prefix are mutually exclusive")
    prefix = args.timestamp_prefix or args.date

    if not args.results_dir.is_dir():
        parser.error(f"results dir not found: {args.results_dir}")

    runs = discover_runs(args.results_dir)
    runs = filter_runs(runs, include_local=args.include_local, timestamp_prefix=prefix)
    if not runs:
        print("no runs matched the given filters", file=sys.stderr)
        return 1

    selected = runs if args.all else pick_latest(runs)
    selected.sort(key=lambda r: (r.artifact, r.variant, r.timestamp))
    written = export(selected, args.destination, keep_all=args.all)

    print(f"exported {len(written)} draft(s) to {args.destination}")
    for path in written:
        print(f"  {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())