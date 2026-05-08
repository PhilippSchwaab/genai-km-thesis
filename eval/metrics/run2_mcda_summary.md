# Run 2 MCDA Summary

Composite score per architecture is computed by aspiration-level Simple Additive Weighting per thesis §3.3.2 (5 criteria, default weights Accuracy 0.30 / Verification Effort 0.25 / Completeness 0.20 / Speed 0.15 / Cost 0.10). Verification Effort is gated by Cohen's d >= 0.5 on per-session time-on-task. Accuracy is sourced from the review-UI factual-error flag rate (direct human scoring per §3.3.3); the §3.3.2 spot-check gate validates an automated approximation against manual review and is satisfied by construction whenever review data exists. Failed or not-yet-verified criteria are excluded and the remaining weights are renormalized to sum to 1; the included-criterion coverage is reported alongside the score.

**Review-UI status:** 4 of 8 review sessions submitted.

## Architecture-aggregated inputs

| Architecture | Artifacts | KIP recall (n) | Mean latency (s) | Mean cost ($) | Mean time-on-task (s) | Claim support (factual / blocks) |
| --- | --- | --- | --- | --- | --- | --- |
| Pipeline (A) | 6 | 0.929 (n=6) | 19.80 | 0.0300 | 225.00 | 1.000 (0 / 26) |
| Agentic (B) | 6 | 0.946 (n=6) | 28.73 | 0.0620 | 130.00 | 1.000 (0 / 23) |

## Per-session review record (architecture-resolved)

Architecture is resolved from `session_config.json`'s `architecture_internal` field (the canonical mapping); `system_label` is shown for traceability. Per-reviewer label overrides in `study_design.json` mean the blinded labels do not consistently identify architectures across reviewers.

| session_id | reviewer_id | architecture | artifact_id | system_label | total_time_s | approved | edited | flagged | removed | edit_distance | likert_conf | likert_eff |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| s001 | R1 | A | CS-01 | System 2 | 220 | 11 | 0 | 0 | 1 | 82 | 6 | 3 |
| s002 | R1 | B | CS-04 | System 1 | 152 | 13 | 0 | 0 | 0 | 0 | 6 | 3 |
| s003 | R2 | A | CS-04 | System 1 | 230 | 14 | 0 | 0 | 0 | 0 | 5 | 4 |
| s004 | R2 | B | CS-01 | System 2 | 108 | 10 | 0 | 0 | 0 | 0 | 6 | 4 |

## Verification Effort gate

Cohen's d = **4.21** (n_A=2, n_B=2, pooled SD = 22.56). Threshold |d| >= 0.5: **PASS**.

*Caveat:* the within-group SD is unstable at this sample size; Verification Effort is reported descriptively per §3.3.3.

## Composite score --- Default weight profile

| Architecture | Composite | Coverage | Excluded |
| --- | --- | --- | --- |
| Agentic (B) | 0.9217 | accuracy, verification_effort, completeness, speed, cost | (none) |
| Pipeline (A) | 0.8846 | accuracy, verification_effort, completeness, speed, cost | (none) |

### Agentic (B) --- per-criterion contribution (Default)

| Criterion | Raw | Normalized | Default weight | Renormalized weight | Weighted | Included | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| accuracy | 1.0000 | 1.0000 | 0.30 | 0.3000 | 0.3000 | yes | pass |
| verification_effort | 130.0000 | 0.7833 | 0.25 | 0.2500 | 0.1958 | yes | pass |
| completeness | 0.9460 | 0.9460 | 0.20 | 0.2000 | 0.1892 | yes | n/a |
| speed | 28.7267 | 0.9196 | 0.15 | 0.1500 | 0.1379 | yes | n/a |
| cost | 0.0620 | 0.9874 | 0.10 | 0.1000 | 0.0987 | yes | n/a |

### Pipeline (A) --- per-criterion contribution (Default)

| Criterion | Raw | Normalized | Default weight | Renormalized weight | Weighted | Included | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| accuracy | 1.0000 | 1.0000 | 0.30 | 0.3000 | 0.3000 | yes | pass |
| verification_effort | 225.0000 | 0.6250 | 0.25 | 0.2500 | 0.1562 | yes | pass |
| completeness | 0.9291 | 0.9291 | 0.20 | 0.2000 | 0.1858 | yes | n/a |
| speed | 19.7983 | 0.9498 | 0.15 | 0.1500 | 0.1425 | yes | n/a |
| cost | 0.0300 | 1.0000 | 0.10 | 0.1000 | 0.1000 | yes | n/a |

## Composite score --- Equal weight profile

| Architecture | Composite | Coverage | Excluded |
| --- | --- | --- | --- |
| Agentic (B) | 0.9273 | accuracy, verification_effort, completeness, speed, cost | (none) |
| Pipeline (A) | 0.9008 | accuracy, verification_effort, completeness, speed, cost | (none) |

### Agentic (B) --- per-criterion contribution (Equal)

| Criterion | Raw | Normalized | Default weight | Renormalized weight | Weighted | Included | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| accuracy | 1.0000 | 1.0000 | 0.20 | 0.2000 | 0.2000 | yes | pass |
| verification_effort | 130.0000 | 0.7833 | 0.20 | 0.2000 | 0.1567 | yes | pass |
| completeness | 0.9460 | 0.9460 | 0.20 | 0.2000 | 0.1892 | yes | n/a |
| speed | 28.7267 | 0.9196 | 0.20 | 0.2000 | 0.1839 | yes | n/a |
| cost | 0.0620 | 0.9874 | 0.20 | 0.2000 | 0.1975 | yes | n/a |

### Pipeline (A) --- per-criterion contribution (Equal)

| Criterion | Raw | Normalized | Default weight | Renormalized weight | Weighted | Included | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| accuracy | 1.0000 | 1.0000 | 0.20 | 0.2000 | 0.2000 | yes | pass |
| verification_effort | 225.0000 | 0.6250 | 0.20 | 0.2000 | 0.1250 | yes | pass |
| completeness | 0.9291 | 0.9291 | 0.20 | 0.2000 | 0.1858 | yes | n/a |
| speed | 19.7983 | 0.9498 | 0.20 | 0.2000 | 0.1900 | yes | n/a |
| cost | 0.0300 | 1.0000 | 0.20 | 0.2000 | 0.2000 | yes | n/a |

## Composite score --- Operational weight profile

| Architecture | Composite | Coverage | Excluded |
| --- | --- | --- | --- |
| Agentic (B) | 0.9334 | accuracy, verification_effort, completeness, speed, cost | (none) |
| Pipeline (A) | 0.9170 | accuracy, verification_effort, completeness, speed, cost | (none) |

### Agentic (B) --- per-criterion contribution (Operational)

| Criterion | Raw | Normalized | Default weight | Renormalized weight | Weighted | Included | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| accuracy | 1.0000 | 1.0000 | 0.15 | 0.1500 | 0.1500 | yes | pass |
| verification_effort | 130.0000 | 0.7833 | 0.15 | 0.1500 | 0.1175 | yes | pass |
| completeness | 0.9460 | 0.9460 | 0.20 | 0.2000 | 0.1892 | yes | n/a |
| speed | 28.7267 | 0.9196 | 0.25 | 0.2500 | 0.2299 | yes | n/a |
| cost | 0.0620 | 0.9874 | 0.25 | 0.2500 | 0.2469 | yes | n/a |

### Pipeline (A) --- per-criterion contribution (Operational)

| Criterion | Raw | Normalized | Default weight | Renormalized weight | Weighted | Included | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| accuracy | 1.0000 | 1.0000 | 0.15 | 0.1500 | 0.1500 | yes | pass |
| verification_effort | 225.0000 | 0.6250 | 0.15 | 0.1500 | 0.0938 | yes | pass |
| completeness | 0.9291 | 0.9291 | 0.20 | 0.2000 | 0.1858 | yes | n/a |
| speed | 19.7983 | 0.9498 | 0.25 | 0.2500 | 0.2375 | yes | n/a |
| cost | 0.0300 | 1.0000 | 0.25 | 0.2500 | 0.2500 | yes | n/a |

## Composite score --- Quality weight profile

| Architecture | Composite | Coverage | Excluded |
| --- | --- | --- | --- |
| Agentic (B) | 0.9195 | accuracy, verification_effort, completeness, speed, cost | (none) |
| Pipeline (A) | 0.8708 | accuracy, verification_effort, completeness, speed, cost | (none) |

### Agentic (B) --- per-criterion contribution (Quality)

| Criterion | Raw | Normalized | Default weight | Renormalized weight | Weighted | Included | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| accuracy | 1.0000 | 1.0000 | 0.40 | 0.4000 | 0.4000 | yes | pass |
| verification_effort | 130.0000 | 0.7833 | 0.30 | 0.3000 | 0.2350 | yes | pass |
| completeness | 0.9460 | 0.9460 | 0.20 | 0.2000 | 0.1892 | yes | n/a |
| speed | 28.7267 | 0.9196 | 0.05 | 0.0500 | 0.0460 | yes | n/a |
| cost | 0.0620 | 0.9874 | 0.05 | 0.0500 | 0.0494 | yes | n/a |

### Pipeline (A) --- per-criterion contribution (Quality)

| Criterion | Raw | Normalized | Default weight | Renormalized weight | Weighted | Included | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| accuracy | 1.0000 | 1.0000 | 0.40 | 0.4000 | 0.4000 | yes | pass |
| verification_effort | 225.0000 | 0.6250 | 0.30 | 0.3000 | 0.1875 | yes | pass |
| completeness | 0.9291 | 0.9291 | 0.20 | 0.2000 | 0.1858 | yes | n/a |
| speed | 19.7983 | 0.9498 | 0.05 | 0.0500 | 0.0475 | yes | n/a |
| cost | 0.0300 | 1.0000 | 0.05 | 0.0500 | 0.0500 | yes | n/a |
