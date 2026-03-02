"""Batch-anonymize raw business artifacts.

Reads every file in data/raw/, redacts PII, and writes the result
to data/anonymized/ with the same filename. Files that already exist
in data/anonymized/ are skipped.
"""

from pathlib import Path

from src.common.pii import redact

_ROOT = Path(__file__).resolve().parents[2]
_RAW_DIR = _ROOT / "data" / "raw"
_ANON_DIR = _ROOT / "data" / "anonymized"


def anonymize_all() -> None:
    _ANON_DIR.mkdir(parents=True, exist_ok=True)

    for source in sorted(_RAW_DIR.iterdir()):
        if not source.is_file():
            continue

        target = _ANON_DIR / source.name
        if target.exists():
            print(f"SKIP  {source.name} (already anonymized)")
            continue

        text = source.read_text(encoding="utf-8")
        anon, _ = redact(text)
        target.write_text(anon, encoding="utf-8")
        print(f"OK    {source.name}")


if __name__ == "__main__":
    anonymize_all()
