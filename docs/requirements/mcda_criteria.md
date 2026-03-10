# MCDA Criteria & Stakeholder Weights

## Source

Weights derived from a Mentimeter ranking session with 6 Meshmakers stakeholders (February 2026). Participants ranked five evaluation criteria for an AI-based documentation system by importance.

## Criteria Definitions

### 1. Accuracy (30%)

The generated wiki entry is factually correct with respect to the source artifact. No information is fabricated or distorted.

**Operationalized as:**

- **KIP Recall** — percentage of gold-standard Key Information Points captured in the output.
- **Hallucination Rate** — percentage of sentences in the output not grounded in the source artifact. Measured via per-sentence grounding check (LLM-as-judge).

### 2. Verification Effort (25%)

The effort a domain expert needs to review, correct, and approve the generated entry. Lower effort means the system is more practically useful.

**Operationalized as:**

- **Human review time** (minutes) — timed session where a domain expert reviews and corrects a generated wiki entry.
- **Edit count** — number of additions, deletions, and modifications the expert makes before approving.

### 3. Completeness (20%)

No important details from the source artifact are missing in the generated entry.

**Operationalized as:**

- **KIP Recall** (shared with Accuracy) — directly measures what fraction of important facts were captured.
- **Per-category recall breakdown** — recall split by KIP category (decision, action_item, deadline, blocker) to identify systematic gaps.

### 4. Speed (15%)

The time from input artifact to finished wiki draft.

**Operationalized as:**

- **End-to-end latency** (seconds) — wall-clock time from API call to final output, including all retries and intermediate steps.
- **Token throughput** — total tokens processed (input + output) per artifact.

### 5. Cost (10%)

The financial cost of running the system per artifact.

**Operationalized as:**

- **API cost per artifact** (EUR) — computed from LiteLLM's built-in cost tracking (token counts × model pricing).
- **Total cost per benchmark run** — sum across all control set artifacts.

## Weight Summary

| Criterion            | Weight | Primary Metric(s)                          |
|----------------------|--------|--------------------------------------------|
| Accuracy             | 0.30   | KIP Recall, Hallucination Rate             |
| Verification Effort  | 0.25   | Review time (min), Edit count              |
| Completeness         | 0.20   | KIP Recall (per-category)                  |
| Speed                | 0.15   | End-to-end latency (s)                     |
| Cost                 | 0.10   | API cost per artifact (EUR)                |

## MCDA Aggregation Method

Weighted Sum Model (WSM): for each architecture, normalize each metric to a 0–1 scale, then compute the weighted aggregate score.

```
Score(A) = Σ (w_i × normalized_metric_i(A))
```

Normalization: higher-is-better metrics (recall) use `value / max_value`. Lower-is-better metrics (hallucination rate, cost, latency, effort) use `1 - (value / max_value)`.

## Sensitivity Analysis

To test robustness of the final ranking, the thesis will report results under alternative weight distributions (e.g., equal weights, accuracy-dominated at 50%, cost-dominated at 40%) and note whether the ranking changes.

## Stakeholder Context

Stakeholders identified **time** as the dominant documentation barrier, followed by complexity, too many systems, and low motivation. Their wish list emphasized automation (no manual uploading), a single access point, and actionable to-dos from meetings. This context justifies the high weight on verification effort — stakeholders want a system that minimizes the time they spend reviewing AI output.
