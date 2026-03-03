"""
Validate KIP JSON files against the project schema.

Usage:
    uv run python -m src.common.validate_kips              # validate all files in data/kips/
    uv run python -m src.common.validate_kips path/to.json  # validate a single file
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_SCHEMA_PATH = _PROJECT_ROOT / "data" / "kips" / "kip_schema.json"
_KIPS_DIR = _PROJECT_ROOT / "data" / "kips"


def _load_schema() -> dict:
    with open(_SCHEMA_PATH) as f:
        return json.load(f)


_schema = _load_schema()
_validator = Draft202012Validator(_schema, format_checker=Draft202012Validator.FORMAT_CHECKER)


def validate(data: dict, filepath: str = "<unknown>") -> list[str]:
    """Return a list of human-readable error strings. Empty list == valid."""
    errors: list[str] = []
    for err in sorted(_validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
        path = ".".join(str(p) for p in err.absolute_path) or "(root)"
        errors.append(f"[{filepath}] {path}: {err.message}")

    # Extra: check KIP IDs are sequential (not expressible in JSON Schema)
    kips = data.get("kips", [])
    if isinstance(kips, list) and all(isinstance(k, dict) for k in kips):
        ids = [k.get("id") for k in kips]
        expected = [f"KIP-{n:03d}" for n in range(1, len(kips) + 1)]
        if ids != expected:
            errors.append(f"[{filepath}] KIP IDs must be sequential: expected {expected}, got {ids}")

    return errors


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    targets: list[Path] = []

    if len(sys.argv) > 1:
        targets = [Path(sys.argv[1])]
    else:
        targets = sorted(p for p in _KIPS_DIR.glob("*.json") if p.name != "kip_schema.json")

    if not targets:
        print("No KIP files found in", _KIPS_DIR)
        sys.exit(0)

    total_errors = 0
    for path in targets:
        with open(path) as f:
            data = json.load(f)
        errors = validate(data, filepath=str(path.relative_to(_PROJECT_ROOT)))
        if errors:
            for e in errors:
                print(f"  ERROR: {e}")
            total_errors += len(errors)
        else:
            print(f"  OK: {path.relative_to(_PROJECT_ROOT)}")

    print(f"\n{len(targets)} file(s) checked, {total_errors} error(s).")
    sys.exit(1 if total_errors else 0)


if __name__ == "__main__":
    main()
