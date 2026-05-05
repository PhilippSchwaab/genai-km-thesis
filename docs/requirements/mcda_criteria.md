# MCDA Criteria & Stakeholder Weights

This document narrates the rationale behind the MCDA configuration. The
machine-readable parameters live in [`eval/mcda_config.yaml`](../../eval/mcda_config.yaml);
the math (aspiration-level Simple Additive Weighting with input-reliability gates)
is implemented in [`eval/harness/mcda.py`](../../eval/harness/mcda.py); the
end-to-end orchestrator that produces composite scores is
[`eval/run_mcda.py`](../../eval/run_mcda.py).

## Source of the weights

A Mentimeter ranking session with six Meshmakers stakeholders (February 2026)
ranked five criteria for an AI-assisted knowledge-capture system. The weights
below are the proportional translation of that rank ordering and constitute the
default stakeholder profile used in the MCDA. The full methodology, including
the score-normalization formula and the gate conditions, is committed in
thesis §3.3.2.

## The five criteria

| # | Criterion           | Weight | Direction | Aspiration `x*` | Anti-aspiration `x⁻` |
|---|---------------------|--------|-----------|-----------------|----------------------|
| 1 | Accuracy            | 0.30   | benefit   | 1.0             | 0.5                  |
| 2 | Verification Effort | 0.25   | cost      | 0 sec           | 600 sec              |
| 3 | Completeness        | 0.20   | benefit   | 1.0             | 0.0                  |
| 4 | Speed               | 0.15   | cost      | 5 sec           | 300 sec              |
| 5 | Cost                | 0.10   | cost      | $0.05           | $1.00                |

Aspiration values are stakeholder-meaningful targets: a raw value at or beyond
`x*` is coerced to `r = 1`, a raw value at or beyond `x⁻` is coerced to `r = 0`,
and values in between are interpolated linearly. This preserves the *magnitude*
of differences instead of collapsing to a relative ranking between two
architectures (the failure mode of min-max normalization on n=2).

### 1. Accuracy

**Stakeholder framing:** the content is factually correct.

**Operationalized as:** the proportion of generated claims traceable to the
source artifact, judged by the expert reviewers (`1 - factual_error_rate`).
Block-level `factual_error` flags from the HITL review UI are the operational
unit; one such flag means the block contains at least one untraceable or
contradictory claim. Computed per architecture across all reviewed blocks.

### 2. Verification Effort

**Stakeholder framing:** easy for a human to check and approve.

**Operationalized as:** mean per-session time-on-task from the HITL review UI,
in seconds. The browser-blur-aware timer in the review UI excludes window
switching and interruptions from the time-on-task total.

### 3. Completeness

**Stakeholder framing:** no important details are missing.

**Operationalized as:** KIP recall — the proportion of gold-standard Key
Information Points captured in the generated entry. Each KIP is scored
YES (1.0), PARTIAL (0.5), or NO (0.0) by an LLM-as-judge against the
generated entry; recall is `(YES + 0.5·PARTIAL) / total_KIPs`. Per-architecture
score is the mean across the six Control Set artifacts.

### 4. Speed

**Stakeholder framing:** the draft is available quickly.

**Operationalized as:** end-to-end latency in seconds from input submission to
final wiki entry, captured by the harness. For the agentic architecture this
includes all reasoning steps and tool calls. Per-architecture score is the mean
across the six Control Set artifacts.

### 5. Cost

**Stakeholder framing:** affordable to run per artifact.

**Operationalized as:** total API cost per artifact in USD, summed across all
model calls (extracted from `metadata.json` via LiteLLM's cost tracking). Per
architecture is the mean across the six Control Set artifacts. Aspiration
$0.05 reflects a cost-effective model baseline; $1.00 the SME budget tolerance
for higher-quality outputs.

## Aggregation: aspiration-level SAW

For each architecture, each criterion's raw value is normalized to `[0, 1]`
using thesis equation 3.4 (benefit) or 3.5 (cost):

```
r_benefit = clip( (x - x⁻) / (x* - x⁻), 0, 1 )
r_cost    = clip( (x⁻ - x) / (x⁻ - x*), 0, 1 )
```

The composite score is the weighted sum:

```
U(A_i) = Σ_j  w_j · r_ij        with Σ_j w_j = 1
```

## Input-reliability gates

Two criteria depend on small-sample human-judgment instruments and carry
explicit inclusion gates (thesis §3.3.2 Robustness conditions):

- **Verification Effort** is included only if Cohen's `d ≥ 0.5` between
  architectures' mean per-session time-on-task (between-architecture mean
  difference / within-architecture pooled SD). Failing the gate excludes
  Verification Effort from the aggregate.
- **Accuracy** is included only if at least one review session per architecture
  has been completed. The thesis-mentioned spot-check gate validates an
  *automated* approximation against manual review; with direct human scoring
  as the input there is no automated approximation to validate, so the gate is
  satisfied by construction whenever review data exists.

When a gate fails or its input is not yet available, the criterion is excluded
from the aggregate and the remaining weights are renormalized to sum to 1. The
included-criterion coverage is reported alongside the composite score so a
high score backed by partial coverage is not mistaken for one under full
coverage. Per §3.3.3 the review-derived inputs are reported descriptively in
Chapter 5 rather than as inferential evidence.

## Sensitivity profiles

The architecture ranking is reported under four weight profiles. Stable
ranking across profiles is taken as evidence of robustness to reasonable
variations in stakeholder priorities.

| Profile     | Accuracy | Ver. Effort | Completeness | Speed | Cost |
|-------------|---------:|------------:|-------------:|------:|-----:|
| Default     |   0.30   |    0.25     |    0.20      | 0.15  | 0.10 |
| Equal       |   0.20   |    0.20     |    0.20      | 0.20  | 0.20 |
| Quality     |   0.40   |    0.30     |    0.20      | 0.05  | 0.05 |
| Operational |   0.15   |    0.15     |    0.20      | 0.25  | 0.25 |

## Stakeholder context

Stakeholders identified **time** as the dominant documentation barrier,
followed by complexity, too many systems, and low motivation. Their wish list
emphasized automation, a single access point, and actionable to-dos from
meetings. Together, the high default weights on Accuracy and Verification
Effort (55 % combined) reflect that the system must produce a trustworthy,
easily-verifiable output even at the expense of processing time or
operational cost.

## Outputs

- `eval/metrics/<label>_mcda_summary.md` — canonical human-readable report for
  one run iteration (per-architecture inputs, per-session audit table,
  gate decisions, composite scores per profile, per-criterion contributions).
- `eval/metrics/<label>_mcda.json` — machine-readable form of the same.

Both are produced by `km mcda` (default label `Run 1`); pass `--label "Run 2"`
after Run 2 results land.
