# Run 2 MCDA Summary

Composite score per architecture is computed by aspiration-level Simple Additive Weighting per thesis §3.3.2 (5 criteria, default weights Accuracy 0.30 / Verification Effort 0.25 / Completeness 0.20 / Speed 0.15 / Cost 0.10). Verification Effort is gated by Cohen's d >= 0.5 on per-session time-on-task. Accuracy is sourced from the review-UI factual-error flag rate (direct human scoring per §3.3.3); the §3.3.2 spot-check gate validates an automated approximation against manual review and is satisfied by construction whenever review data exists. Failed or not-yet-verified criteria are excluded and the remaining weights are renormalized to sum to 1; the included-criterion coverage is reported alongside the score.

**Review-UI status:** 20 of 20 review sessions submitted.

## Architecture-aggregated inputs

| Architecture | Artifacts | KIP recall (n) | Mean latency (s) | Mean cost ($) | Mean time-on-task (s) | Claim support (factual / blocks) |
| --- | --- | --- | --- | --- | --- | --- |
| Pipeline (A) | 6 | 0.929 (n=6) | 19.80 | 0.0300 | 158.60 | 1.000 (0 / 140) |
| Agentic (B) | 6 | 0.946 (n=6) | 28.73 | 0.0620 | 68.30 | 1.000 (0 / 111) |

## Per-session review record (architecture-resolved)

Architecture is resolved from `session_config.json`'s `architecture_internal` field (the canonical mapping); `system_label` is shown for traceability. Per-reviewer label overrides in `study_design.json` mean the blinded labels do not consistently identify architectures across reviewers.

| session_id | reviewer_id | architecture | artifact_id | system_label | total_time_s | approved | edited | flagged | removed | edit_distance | likert_conf | likert_eff |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| s001 | R1 | A | CS-01 | System 2 | 220 | 11 | 0 | 0 | 1 | 82 | 6 | 3 |
| s002 | R1 | B | CS-04 | System 1 | 152 | 13 | 0 | 0 | 0 | 0 | 6 | 3 |
| s003 | R2 | A | CS-04 | System 1 | 230 | 14 | 0 | 0 | 0 | 0 | 5 | 4 |
| s004 | R2 | B | CS-01 | System 2 | 108 | 10 | 0 | 0 | 0 | 0 | 6 | 4 |
| s009 | R1 | A | CS-02 | System 2 | 55 | 13 | 0 | 0 | 0 | 0 | 7 | 2 |
| s010 | R1 | B | CS-03 | System 1 | 90 | 18 | 0 | 0 | 0 | 0 | 5 | 3 |
| s011 | R1 | A | CS-05 | System 2 | 88 | 13 | 0 | 0 | 0 | 0 | 5 | 2 |
| s012 | R1 | B | CS-06 | System 1 | 55 | 9 | 0 | 0 | 0 | 0 | 4 | 2 |
| s013 | R1 | B | CS-02 | System 1 | 34 | 7 | 0 | 0 | 0 | 0 | 6 | 1 |
| s014 | R1 | A | CS-03 | System 2 | 193 | 19 | 0 | 0 | 0 | 0 | 4 | 5 |
| s015 | R1 | B | CS-05 | System 1 | 48 | 10 | 0 | 0 | 0 | 0 | 6 | 2 |
| s016 | R1 | A | CS-06 | System 2 | 191 | 11 | 0 | 1 | 0 | 0 | 3 | 5 |
| s017 | R2 | B | CS-02 | System 2 | 25 | 7 | 0 | 0 | 0 | 0 | 7 | 1 |
| s018 | R2 | A | CS-03 | System 1 | 189 | 18 | 0 | 1 | 0 | 0 | 4 | 7 |
| s019 | R2 | B | CS-05 | System 2 | 37 | 10 | 0 | 0 | 0 | 0 | 6 | 3 |
| s020 | R2 | A | CS-06 | System 1 | 112 | 12 | 0 | 0 | 0 | 0 | 4 | 5 |
| s021 | R2 | A | CS-02 | System 1 | 87 | 12 | 0 | 1 | 0 | 0 | 5 | 4 |
| s022 | R2 | B | CS-03 | System 2 | 87 | 18 | 0 | 0 | 0 | 0 | 6 | 2 |
| s023 | R2 | A | CS-05 | System 1 | 221 | 13 | 0 | 0 | 0 | 0 | 4 | 6 |
| s024 | R2 | B | CS-06 | System 2 | 47 | 9 | 0 | 0 | 0 | 0 | 6 | 1 |

## Verification Effort gate

Cohen's d = **1.66** (n_A=10, n_B=10, pooled SD = 54.47). Threshold |d| >= 0.5: **PASS**.

## Composite score --- Default weight profile

| Architecture | Composite | Coverage | Excluded |
| --- | --- | --- | --- |
| Agentic (B) | 0.9474 | accuracy, verification_effort, completeness, speed, cost | (none) |
| Pipeline (A) | 0.9122 | accuracy, verification_effort, completeness, speed, cost | (none) |

### Agentic (B) --- per-criterion contribution (Default)

| Criterion | Raw | Normalized | Default weight | Renormalized weight | Weighted | Included | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| accuracy | 1.0000 | 1.0000 | 0.30 | 0.3000 | 0.3000 | yes | pass |
| verification_effort | 68.3000 | 0.8862 | 0.25 | 0.2500 | 0.2215 | yes | pass |
| completeness | 0.9460 | 0.9460 | 0.20 | 0.2000 | 0.1892 | yes | n/a |
| speed | 28.7267 | 0.9196 | 0.15 | 0.1500 | 0.1379 | yes | n/a |
| cost | 0.0620 | 0.9874 | 0.10 | 0.1000 | 0.0987 | yes | n/a |

### Pipeline (A) --- per-criterion contribution (Default)

| Criterion | Raw | Normalized | Default weight | Renormalized weight | Weighted | Included | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| accuracy | 1.0000 | 1.0000 | 0.30 | 0.3000 | 0.3000 | yes | pass |
| verification_effort | 158.6000 | 0.7357 | 0.25 | 0.2500 | 0.1839 | yes | pass |
| completeness | 0.9291 | 0.9291 | 0.20 | 0.2000 | 0.1858 | yes | n/a |
| speed | 19.7983 | 0.9498 | 0.15 | 0.1500 | 0.1425 | yes | n/a |
| cost | 0.0300 | 1.0000 | 0.10 | 0.1000 | 0.1000 | yes | n/a |

## Composite score --- Equal weight profile

| Architecture | Composite | Coverage | Excluded |
| --- | --- | --- | --- |
| Agentic (B) | 0.9478 | accuracy, verification_effort, completeness, speed, cost | (none) |
| Pipeline (A) | 0.9229 | accuracy, verification_effort, completeness, speed, cost | (none) |

### Agentic (B) --- per-criterion contribution (Equal)

| Criterion | Raw | Normalized | Default weight | Renormalized weight | Weighted | Included | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| accuracy | 1.0000 | 1.0000 | 0.20 | 0.2000 | 0.2000 | yes | pass |
| verification_effort | 68.3000 | 0.8862 | 0.20 | 0.2000 | 0.1772 | yes | pass |
| completeness | 0.9460 | 0.9460 | 0.20 | 0.2000 | 0.1892 | yes | n/a |
| speed | 28.7267 | 0.9196 | 0.20 | 0.2000 | 0.1839 | yes | n/a |
| cost | 0.0620 | 0.9874 | 0.20 | 0.2000 | 0.1975 | yes | n/a |

### Pipeline (A) --- per-criterion contribution (Equal)

| Criterion | Raw | Normalized | Default weight | Renormalized weight | Weighted | Included | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| accuracy | 1.0000 | 1.0000 | 0.20 | 0.2000 | 0.2000 | yes | pass |
| verification_effort | 158.6000 | 0.7357 | 0.20 | 0.2000 | 0.1471 | yes | pass |
| completeness | 0.9291 | 0.9291 | 0.20 | 0.2000 | 0.1858 | yes | n/a |
| speed | 19.7983 | 0.9498 | 0.20 | 0.2000 | 0.1900 | yes | n/a |
| cost | 0.0300 | 1.0000 | 0.20 | 0.2000 | 0.2000 | yes | n/a |

## Composite score --- Operational weight profile

| Architecture | Composite | Coverage | Excluded |
| --- | --- | --- | --- |
| Agentic (B) | 0.9489 | accuracy, verification_effort, completeness, speed, cost | (none) |
| Pipeline (A) | 0.9336 | accuracy, verification_effort, completeness, speed, cost | (none) |

### Agentic (B) --- per-criterion contribution (Operational)

| Criterion | Raw | Normalized | Default weight | Renormalized weight | Weighted | Included | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| accuracy | 1.0000 | 1.0000 | 0.15 | 0.1500 | 0.1500 | yes | pass |
| verification_effort | 68.3000 | 0.8862 | 0.15 | 0.1500 | 0.1329 | yes | pass |
| completeness | 0.9460 | 0.9460 | 0.20 | 0.2000 | 0.1892 | yes | n/a |
| speed | 28.7267 | 0.9196 | 0.25 | 0.2500 | 0.2299 | yes | n/a |
| cost | 0.0620 | 0.9874 | 0.25 | 0.2500 | 0.2469 | yes | n/a |

### Pipeline (A) --- per-criterion contribution (Operational)

| Criterion | Raw | Normalized | Default weight | Renormalized weight | Weighted | Included | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| accuracy | 1.0000 | 1.0000 | 0.15 | 0.1500 | 0.1500 | yes | pass |
| verification_effort | 158.6000 | 0.7357 | 0.15 | 0.1500 | 0.1103 | yes | pass |
| completeness | 0.9291 | 0.9291 | 0.20 | 0.2000 | 0.1858 | yes | n/a |
| speed | 19.7983 | 0.9498 | 0.25 | 0.2500 | 0.2375 | yes | n/a |
| cost | 0.0300 | 1.0000 | 0.25 | 0.2500 | 0.2500 | yes | n/a |

## Composite score --- Quality weight profile

| Architecture | Composite | Coverage | Excluded |
| --- | --- | --- | --- |
| Agentic (B) | 0.9504 | accuracy, verification_effort, completeness, speed, cost | (none) |
| Pipeline (A) | 0.9040 | accuracy, verification_effort, completeness, speed, cost | (none) |

### Agentic (B) --- per-criterion contribution (Quality)

| Criterion | Raw | Normalized | Default weight | Renormalized weight | Weighted | Included | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| accuracy | 1.0000 | 1.0000 | 0.40 | 0.4000 | 0.4000 | yes | pass |
| verification_effort | 68.3000 | 0.8862 | 0.30 | 0.3000 | 0.2659 | yes | pass |
| completeness | 0.9460 | 0.9460 | 0.20 | 0.2000 | 0.1892 | yes | n/a |
| speed | 28.7267 | 0.9196 | 0.05 | 0.0500 | 0.0460 | yes | n/a |
| cost | 0.0620 | 0.9874 | 0.05 | 0.0500 | 0.0494 | yes | n/a |

### Pipeline (A) --- per-criterion contribution (Quality)

| Criterion | Raw | Normalized | Default weight | Renormalized weight | Weighted | Included | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| accuracy | 1.0000 | 1.0000 | 0.40 | 0.4000 | 0.4000 | yes | pass |
| verification_effort | 158.6000 | 0.7357 | 0.30 | 0.3000 | 0.2207 | yes | pass |
| completeness | 0.9291 | 0.9291 | 0.20 | 0.2000 | 0.1858 | yes | n/a |
| speed | 19.7983 | 0.9498 | 0.05 | 0.0500 | 0.0475 | yes | n/a |
| cost | 0.0300 | 1.0000 | 0.05 | 0.0500 | 0.0500 | yes | n/a |

## Composite score --- Survey_derived weight profile

| Architecture | Composite | Coverage | Excluded |
| --- | --- | --- | --- |
| Agentic (B) | 0.9432 | accuracy, verification_effort, completeness, speed, cost | (none) |
| Pipeline (A) | 0.9004 | accuracy, verification_effort, completeness, speed, cost | (none) |

### Agentic (B) --- per-criterion contribution (Survey_derived)

| Criterion | Raw | Normalized | Default weight | Renormalized weight | Weighted | Included | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| accuracy | 1.0000 | 1.0000 | 0.30 | 0.3000 | 0.3000 | yes | pass |
| verification_effort | 68.3000 | 0.8862 | 0.30 | 0.3000 | 0.2659 | yes | pass |
| completeness | 0.9460 | 0.9460 | 0.18 | 0.1800 | 0.1703 | yes | n/a |
| speed | 28.7267 | 0.9196 | 0.15 | 0.1500 | 0.1379 | yes | n/a |
| cost | 0.0620 | 0.9874 | 0.07 | 0.0700 | 0.0691 | yes | n/a |

### Pipeline (A) --- per-criterion contribution (Survey_derived)

| Criterion | Raw | Normalized | Default weight | Renormalized weight | Weighted | Included | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| accuracy | 1.0000 | 1.0000 | 0.30 | 0.3000 | 0.3000 | yes | pass |
| verification_effort | 158.6000 | 0.7357 | 0.30 | 0.3000 | 0.2207 | yes | pass |
| completeness | 0.9291 | 0.9291 | 0.18 | 0.1800 | 0.1672 | yes | n/a |
| speed | 19.7983 | 0.9498 | 0.15 | 0.1500 | 0.1425 | yes | n/a |
| cost | 0.0300 | 1.0000 | 0.07 | 0.0700 | 0.0700 | yes | n/a |
