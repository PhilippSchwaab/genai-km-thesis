"""
KIP Scorer — LLM-as-Judge for KIP Recall.

Loads the KIP registry for an artifact, reads a generated wiki entry,
and asks the judge LLM whether each KIP is present.

Returns per-KIP judgments and an aggregate recall score.

Usage:
    from eval.harness.kip_scorer import score_kips

    report = score_kips(run_dir=Path("eval/results/pipeline_CS-06_..."))
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from src.common.llm_client import CallLog, complete
from src.common.prompts import load_prompt

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_KIPS_DIR = _PROJECT_ROOT / "data" / "kips"

# Score mapping
_SCORE_MAP = {"YES": 1.0, "PARTIAL": 0.5, "NO": 0.0}


@dataclass(frozen=True)
class KIPJudgment:
    """Result of judging a single KIP against a wiki entry."""

    kip_id: str
    kip_text: str
    category: str
    implicit: bool
    judgment: str  # YES | PARTIAL | NO
    reason: str
    score: float  # 1.0 | 0.5 | 0.0


@dataclass
class KIPScoreReport:
    """Aggregate results from scoring all KIPs for one run."""

    artifact_id: str
    run_dir: str
    judgments: list[KIPJudgment] = field(default_factory=list)
    call_log: CallLog = field(default_factory=CallLog)

    @property
    def total_kips(self) -> int:
        return len(self.judgments)

    @property
    def recall(self) -> float:
        if not self.judgments:
            return 0.0
        return sum(j.score for j in self.judgments) / len(self.judgments)

    @property
    def counts(self) -> dict[str, int]:
        counts = {"YES": 0, "PARTIAL": 0, "NO": 0}
        for j in self.judgments:
            counts[j.judgment] = counts.get(j.judgment, 0) + 1
        return counts

    def to_dict(self) -> dict:
        return {
            "artifact_id": self.artifact_id,
            "run_dir": self.run_dir,
            "total_kips": self.total_kips,
            "recall": round(self.recall, 4),
            "counts": self.counts,
            "eval_cost_usd": round(self.call_log.total_cost_usd, 6),
            "eval_latency_seconds": round(self.call_log.total_latency, 2),
            "eval_tokens": self.call_log.total_tokens,
            "judgments": [
                {
                    "kip_id": j.kip_id,
                    "kip_text": j.kip_text,
                    "category": j.category,
                    "implicit": j.implicit,
                    "judgment": j.judgment,
                    "reason": j.reason,
                    "score": j.score,
                }
                for j in self.judgments
            ],
        }


def _parse_judgment(text: str) -> tuple[str, str]:
    """Extract JUDGMENT and REASON from the LLM response.

    Expected format:
        JUDGMENT: YES
        REASON: The wiki entry clearly states...
    """
    judgment = "NO"
    reason = ""

    # Match JUDGMENT line
    jm = re.search(r"JUDGMENT:\s*(YES|PARTIAL|NO)", text, re.IGNORECASE)
    if jm:
        judgment = jm.group(1).upper()

    # Match REASON line
    rm = re.search(r"REASON:\s*(.+)", text, re.IGNORECASE)
    if rm:
        reason = rm.group(1).strip()

    return judgment, reason


def _load_kips(artifact_id: str) -> list[dict]:
    """Load KIPs for an artifact from data/kips/.

    The artifact_id from metadata (e.g. "CS-06_Testing_Strategy_compiled")
    is mapped to the KIP file (e.g. "cs-06.json") by extracting the CS-XX
    prefix.
    """
    # Extract "cs-06" from "CS-06_Testing_Strategy_compiled"
    match = re.match(r"(CS-\d+)", artifact_id, re.IGNORECASE)
    if not match:
        raise FileNotFoundError(
            f"Cannot extract CS-XX from artifact_id '{artifact_id}'"
        )
    kip_file = _KIPS_DIR / f"{match.group(1).lower()}.json"
    if not kip_file.exists():
        raise FileNotFoundError(f"KIP file not found: {kip_file}")

    with open(kip_file) as f:
        data = json.load(f)
    return data["kips"]


def score_kips(
    run_dir: Path,
    *,
    prompt_id: str = "eval_kip_scorer",
    judge_model: str | None = None,
) -> KIPScoreReport:
    """Score all KIPs for a generation run.

    Args:
        run_dir: Path to the run directory (must contain metadata.json
                 and wiki_entry.md).
        prompt_id: Eval prompt to use.
        judge_model: Override the judge model from the prompt YAML.

    Returns:
        KIPScoreReport with per-KIP judgments and aggregate recall.
    """
    # Load run outputs
    metadata = json.loads((run_dir / "metadata.json").read_text())
    wiki_entry = (run_dir / "wiki_entry.md").read_text()
    artifact_id = metadata["artifact_id"]

    # Load KIPs and prompt
    kips = _load_kips(artifact_id)
    prompt = load_prompt(prompt_id)
    model = judge_model or prompt.model

    # Resolve sampling from prompt YAML
    sampling = prompt.sampling
    temperature = sampling.get("temperature", 0.0)
    max_tokens = int(sampling.get("max_tokens", 256))
    top_p = sampling.get("top_p")
    top_k = sampling.get("top_k")
    if top_k is not None:
        top_k = int(top_k)

    # Score each KIP
    report = KIPScoreReport(
        artifact_id=artifact_id,
        run_dir=str(run_dir),
    )

    for kip in kips:
        messages = prompt.render(
            kip_text=kip["text"],
            wiki_entry=wiki_entry,
        )

        result = complete(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            top_k=top_k,
            call_log=report.call_log,
        )

        judgment, reason = _parse_judgment(result.text)

        report.judgments.append(
            KIPJudgment(
                kip_id=kip["id"],
                kip_text=kip["text"],
                category=kip["category"],
                implicit=kip.get("implicit", False),
                judgment=judgment,
                reason=reason,
                score=_SCORE_MAP.get(judgment, 0.0),
            )
        )

    return report
