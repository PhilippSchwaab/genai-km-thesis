# Run 1 MCDA Summary

Composite score per architecture is computed by aspiration-level Simple Additive Weighting per thesis §3.3.2 (5 criteria, default weights Accuracy 0.30 / Verification Effort 0.25 / Completeness 0.20 / Speed 0.15 / Cost 0.10). Verification Effort is gated by Cohen's d >= 0.5 on per-session time-on-task. Accuracy is sourced from the review-UI factual-error flag rate (direct human scoring per §3.3.3); the §3.3.2 spot-check gate validates an automated approximation against manual review and is satisfied by construction whenever review data exists. Failed or not-yet-verified criteria are excluded and the remaining weights are renormalized to sum to 1; the included-criterion coverage is reported alongside the score.

**Review-UI status:** 4 of 8 review sessions submitted.

## Architecture-aggregated inputs

| Architecture | Artifacts | KIP recall (n) | Mean latency (s) | Mean cost ($) | Mean time-on-task (s) | Claim support (factual / blocks) |
| --- | --- | --- | --- | --- | --- | --- |
| Pipeline (A) | 6 | 0.967 (n=6) | 28.93 | 0.0396 | 308.00 | 1.000 (0 / 44) |
| Agentic (B) | 6 | 0.965 (n=6) | 87.77 | 0.2109 | 123.00 | 1.000 (0 / 37) |

## Per-session review record (architecture-resolved)

Architecture is resolved from `session_config.json`'s `architecture_internal` field (the canonical mapping); `system_label` is shown for traceability. Per-reviewer label overrides in `study_design.json` mean the blinded labels do not consistently identify architectures across reviewers.

| session_id | reviewer_id | architecture | artifact_id | system_label | total_time_s | approved | edited | flagged | removed | edit_distance | likert_conf | likert_eff |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| s001 | R1 | A | CS-01 | System 1 | 362 | 17 | 1 | 3 | 0 | 11 | 5 | 6 |
| s002 | R1 | B | CS-04 | System 2 | 97 | 19 | 0 | 0 | 0 | 0 | 6 | 3 |
| s003 | R2 | A | CS-04 | System 2 | 254 | 18 | 0 | 3 | 2 | 283 | 4 | 5 |
| s004 | R2 | B | CS-01 | System 1 | 149 | 17 | 0 | 1 | 0 | 0 | 5 | 4 |

## Verification Effort gate

Cohen's d = **3.09** (n_A=2, n_B=2, pooled SD = 59.93). Threshold |d| >= 0.5: **PASS**.

*Caveat:* the within-group SD is unstable at this sample size; Verification Effort is reported descriptively per §3.3.3.

## Composite score --- Default weight profile

| Architecture | Composite | Coverage | Excluded |
| --- | --- | --- | --- |
| Agentic (B) | 0.8827 | accuracy, verification_effort, completeness, speed, cost | (none) |
| Pipeline (A) | 0.8528 | accuracy, verification_effort, completeness, speed, cost | (none) |

### Agentic (B) --- per-criterion contribution (Default)

| Criterion | Raw | Normalized | Default weight | Renormalized weight | Weighted | Included | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| accuracy | 1.0000 | 1.0000 | 0.30 | 0.3000 | 0.3000 | yes | pass |
| verification_effort | 123.0000 | 0.7950 | 0.25 | 0.2500 | 0.1988 | yes | pass |
| completeness | 0.9650 | 0.9650 | 0.20 | 0.2000 | 0.1930 | yes | n/a |
| speed | 87.7650 | 0.7194 | 0.15 | 0.1500 | 0.1079 | yes | n/a |
| cost | 0.2109 | 0.8306 | 0.10 | 0.1000 | 0.0831 | yes | n/a |

### Pipeline (A) --- per-criterion contribution (Default)

| Criterion | Raw | Normalized | Default weight | Renormalized weight | Weighted | Included | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| accuracy | 1.0000 | 1.0000 | 0.30 | 0.3000 | 0.3000 | yes | pass |
| verification_effort | 308.0000 | 0.4867 | 0.25 | 0.2500 | 0.1217 | yes | pass |
| completeness | 0.9667 | 0.9667 | 0.20 | 0.2000 | 0.1933 | yes | n/a |
| speed | 28.9333 | 0.9189 | 0.15 | 0.1500 | 0.1378 | yes | n/a |
| cost | 0.0396 | 1.0000 | 0.10 | 0.1000 | 0.1000 | yes | n/a |

## Composite score --- Equal weight profile

| Architecture | Composite | Coverage | Excluded |
| --- | --- | --- | --- |
| Pipeline (A) | 0.8745 | accuracy, verification_effort, completeness, speed, cost | (none) |
| Agentic (B) | 0.8620 | accuracy, verification_effort, completeness, speed, cost | (none) |

### Pipeline (A) --- per-criterion contribution (Equal)

| Criterion | Raw | Normalized | Default weight | Renormalized weight | Weighted | Included | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| accuracy | 1.0000 | 1.0000 | 0.20 | 0.2000 | 0.2000 | yes | pass |
| verification_effort | 308.0000 | 0.4867 | 0.20 | 0.2000 | 0.0973 | yes | pass |
| completeness | 0.9667 | 0.9667 | 0.20 | 0.2000 | 0.1933 | yes | n/a |
| speed | 28.9333 | 0.9189 | 0.20 | 0.2000 | 0.1838 | yes | n/a |
| cost | 0.0396 | 1.0000 | 0.20 | 0.2000 | 0.2000 | yes | n/a |

### Agentic (B) --- per-criterion contribution (Equal)

| Criterion | Raw | Normalized | Default weight | Renormalized weight | Weighted | Included | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| accuracy | 1.0000 | 1.0000 | 0.20 | 0.2000 | 0.2000 | yes | pass |
| verification_effort | 123.0000 | 0.7950 | 0.20 | 0.2000 | 0.1590 | yes | pass |
| completeness | 0.9650 | 0.9650 | 0.20 | 0.2000 | 0.1930 | yes | n/a |
| speed | 87.7650 | 0.7194 | 0.20 | 0.2000 | 0.1439 | yes | n/a |
| cost | 0.2109 | 0.8306 | 0.20 | 0.2000 | 0.1661 | yes | n/a |

## Composite score --- Operational weight profile

| Architecture | Composite | Coverage | Excluded |
| --- | --- | --- | --- |
| Pipeline (A) | 0.8961 | accuracy, verification_effort, completeness, speed, cost | (none) |
| Agentic (B) | 0.8498 | accuracy, verification_effort, completeness, speed, cost | (none) |

### Pipeline (A) --- per-criterion contribution (Operational)

| Criterion | Raw | Normalized | Default weight | Renormalized weight | Weighted | Included | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| accuracy | 1.0000 | 1.0000 | 0.15 | 0.1500 | 0.1500 | yes | pass |
| verification_effort | 308.0000 | 0.4867 | 0.15 | 0.1500 | 0.0730 | yes | pass |
| completeness | 0.9667 | 0.9667 | 0.20 | 0.2000 | 0.1933 | yes | n/a |
| speed | 28.9333 | 0.9189 | 0.25 | 0.2500 | 0.2297 | yes | n/a |
| cost | 0.0396 | 1.0000 | 0.25 | 0.2500 | 0.2500 | yes | n/a |

### Agentic (B) --- per-criterion contribution (Operational)

| Criterion | Raw | Normalized | Default weight | Renormalized weight | Weighted | Included | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| accuracy | 1.0000 | 1.0000 | 0.15 | 0.1500 | 0.1500 | yes | pass |
| verification_effort | 123.0000 | 0.7950 | 0.15 | 0.1500 | 0.1192 | yes | pass |
| completeness | 0.9650 | 0.9650 | 0.20 | 0.2000 | 0.1930 | yes | n/a |
| speed | 87.7650 | 0.7194 | 0.25 | 0.2500 | 0.1799 | yes | n/a |
| cost | 0.2109 | 0.8306 | 0.25 | 0.2500 | 0.2077 | yes | n/a |

## Composite score --- Quality weight profile

| Architecture | Composite | Coverage | Excluded |
| --- | --- | --- | --- |
| Agentic (B) | 0.9090 | accuracy, verification_effort, completeness, speed, cost | (none) |
| Pipeline (A) | 0.8353 | accuracy, verification_effort, completeness, speed, cost | (none) |

### Agentic (B) --- per-criterion contribution (Quality)

| Criterion | Raw | Normalized | Default weight | Renormalized weight | Weighted | Included | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| accuracy | 1.0000 | 1.0000 | 0.40 | 0.4000 | 0.4000 | yes | pass |
| verification_effort | 123.0000 | 0.7950 | 0.30 | 0.3000 | 0.2385 | yes | pass |
| completeness | 0.9650 | 0.9650 | 0.20 | 0.2000 | 0.1930 | yes | n/a |
| speed | 87.7650 | 0.7194 | 0.05 | 0.0500 | 0.0360 | yes | n/a |
| cost | 0.2109 | 0.8306 | 0.05 | 0.0500 | 0.0415 | yes | n/a |

### Pipeline (A) --- per-criterion contribution (Quality)

| Criterion | Raw | Normalized | Default weight | Renormalized weight | Weighted | Included | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| accuracy | 1.0000 | 1.0000 | 0.40 | 0.4000 | 0.4000 | yes | pass |
| verification_effort | 308.0000 | 0.4867 | 0.30 | 0.3000 | 0.1460 | yes | pass |
| completeness | 0.9667 | 0.9667 | 0.20 | 0.2000 | 0.1933 | yes | n/a |
| speed | 28.9333 | 0.9189 | 0.05 | 0.0500 | 0.0459 | yes | n/a |
| cost | 0.0396 | 1.0000 | 0.05 | 0.0500 | 0.0500 | yes | n/a |
