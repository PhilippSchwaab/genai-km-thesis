# MCDA Criteria & Stakeholder Weights

## Source

Weights derived from a Mentimeter ranking session with 6 Meshmakers stakeholders (February 2026). Participants ranked five evaluation criteria for an AI-based documentation system by importance.

## Scope Decision

Stakeholders originally identified five criteria: Accuracy, Verification Effort, Completeness, Speed, and Cost. Of these, three can be fully operationalized with automated, reproducible metrics within the scope of this thesis. Two (Accuracy and Verification Effort) require multiple expert review sessions to measure rigorously — resources not available within the project constraints.

Rather than producing thin measurements for all five, the evaluation focuses on three criteria with robust metrics. Accuracy and Verification Effort are discussed qualitatively in Chapter 5 and identified as evaluation extensions in Section 6.3. The stakeholder weights are redistributed proportionally across the three measured criteria, preserving the original relative ranking.

### Weight Redistribution

Original stakeholder ranking: Accuracy (30%), Verification Effort (25%), Completeness (20%), Speed (15%), Cost (10%).

Redistributed across measured criteria (preserving relative proportions of Completeness, Speed, Cost):

| Original Criterion   | Original Weight | Status                           |
|----------------------|-----------------|----------------------------------|
| Accuracy             | 0.30            | Discussed qualitatively in Ch. 5 |
| Verification Effort  | 0.25            | Discussed qualitatively in Ch. 5 |
| Completeness         | 0.20 → **0.44** | Measured (primary criterion)     |
| Speed                | 0.15 → **0.33** | Measured                         |
| Cost                 | 0.10 → **0.22** | Measured                         |

Redistribution method: `new_weight = original_weight / sum(original_weights_of_measured_criteria)`. Sum of measured = 0.20 + 0.15 + 0.10 = 0.45. Completeness: 0.20/0.45 ≈ 0.44, Speed: 0.15/0.45 ≈ 0.33, Cost: 0.10/0.45 ≈ 0.22.

---

## Measured Criteria

### 1. Completeness (44%)

No important details from the source artifact are missing in the generated entry.

**Operationalized as:**

- **KIP Recall** — percentage of gold-standard Key Information Points captured in the output: `KIPs matched / total KIPs`. Scored via LLM-as-judge (YES/PARTIAL/NO per KIP).

### 2. Speed (33%)

The time from input artifact to finished wiki draft.

**Operationalized as:**

- **End-to-end latency** (seconds) — wall-clock time from API call to final output, including all retries and intermediate steps. Logged automatically by the evaluation harness.

### 3. Cost (22%)

The financial cost of running the system per artifact.

**Operationalized as:**

- **API cost per artifact** (EUR) — computed from LiteLLM's built-in cost tracking (token counts × model pricing).

---

## Qualitative Criteria (Discussed in Ch. 5, Not Scored in MCDA)

### Accuracy

Whether the generated wiki entry is factually correct. Hallucinations and distortions observed during the author's manual review of outputs are reported qualitatively. A rigorous operationalization (e.g., per-statement grounding checks with multiple expert reviewers) exceeds the scope of this thesis.

### Verification Effort

The effort a domain expert needs to review and approve the output. A single expert review session will provide anecdotal observations on relative effort between architectures, reported as a qualitative comparison rather than a scored metric.

---

## MCDA Aggregation Method

Weighted Sum Model (WSM): for each architecture, normalize each metric to a 0–1 scale, then compute the weighted aggregate score.

```
Score(A) = Σ (w_i × normalized_metric_i(A))
```

Normalization: higher-is-better metrics (recall) use `value / max_value`. Lower-is-better metrics (cost, latency) use `1 - (value / max_value)`.

## Sensitivity Analysis

To test robustness of the final ranking, the thesis reports results under alternative weight distributions and notes whether the ranking changes.

| Profile              | Completeness | Speed | Cost |
|----------------------|-------------|-------|------|
| Stakeholder-derived  | 0.44        | 0.33  | 0.22 |
| Equal                | 0.33        | 0.33  | 0.33 |
| Completeness-dominated | 0.70      | 0.15  | 0.15 |
| Cost-dominated       | 0.20        | 0.20  | 0.60 |

## Stakeholder Context

Stakeholders identified **time** as the dominant documentation barrier, followed by complexity, too many systems, and low motivation. Their wish list emphasized automation (no manual uploading), a single access point, and actionable to-dos from meetings. The high weight on Completeness reflects that stakeholders prioritize a system that captures all important information — the core promise of automated knowledge synthesis.

## Relation to KIP Scoring

KIP Recall (the primary metric for Completeness) is scored via LLM-as-judge using the prompt defined in `prompts/eval_kip_scorer.yaml`. Each KIP from the gold-standard registry is checked against the generated output (YES/PARTIAL/NO). Recall is computed as: `(YES_count + 0.5 × PARTIAL_count) / total_KIPs`. Per-KIP judgments are stored for qualitative analysis (e.g., per-category recall breakdown as a secondary lens, not scored in MCDA).
