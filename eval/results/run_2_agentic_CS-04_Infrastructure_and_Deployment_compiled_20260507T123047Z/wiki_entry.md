## Summary
Work item AB#3151 ("LKV: familiarize yourself with the topic and the current solution") covers infrastructure stabilisation, deployment restructuring, credential management hardening, and test coverage expansion for the LKVLogistic CLI. All work was authored by [Developer 1] across 23 commits and 3 pull requests between 2026-01-13 and 2026-03-23. The work item remains in **Active** state. Total churn across the period: 99 files changed, 2 729 insertions, 643 deletions.

## Decisions
- **Adopt Kustomize for credential and deployment management.** `TestConfigCommand.cs` renamed to `DisplayConfigCommand.cs`; deployment overlays restructured under `deployment/overlays/lkv/{production,staging}/` with Kustomize `kustomization.yaml` files. Deprecated flat deployment templates removed (commit `6db7a94`, 2026-02-10).
- **Credentials file excluded from version control.** `credentials-secret.yaml` converted to `credentials-secret.yaml.example` and added to `.gitignore` to prevent secret leakage (commit `fb7269b`, 2026-03-05).
- **ACR pull secret removed from manifests; handled by cluster.** `acr-secret.yaml` deleted from `deployment/base/`; `cronjobs.yaml` references removed (commit `83f7507`, 2026-02-19).
- **Switch to built-in StorageClass.** Custom `storageclass.yaml` removed; `storage.yaml` updated to reference the cluster's built-in StorageClass (commit `ae4873b`, 2026-02-19).
- **StorageClass creation moved to a separate chore task** rather than being part of the main deployment manifest (commit `b8bb38a`, 2026-02-19).
- **`imagePullPolicy` changed to `IfNotPresent`** in `cronjobs.yaml` (commit `70f7117`, 2026-03-05).
- **Automated version-number replacement removed from manifests; made pipeline-specific** (commit `70f7117`, 2026-03-05).
- **Error handling: skip (do not crash) on errors in `CsvAuftragsRueckmeldung.cs` and `CsvBestandsmeldung.cs`** (PR #352 description, 2026-03-10).
- **Add SFTP server (SFTPGo via Testcontainers) for integration testing in staging** (PR #352 / PR #354).
- **Add SMTP-based error notification when configured** (PR #352, 2026-03-10).
- **Bump Billbee API Client dependency to 2.4.3** (commit `5f6cb6d`, 2026-03-23).
- **`backoffLimit` and `activeDeadlineSeconds` added to `cronjobs.yaml`** to bound retry and runtime behaviour (commit `20d9d37`, 2026-03-05).
- **Staging environment mapped to the existing `lkv` namespace** rather than a separate namespace (commit `45507d5`, 2026-03-05).
- **Credentials loaded via Kubernetes Secrets** in the deployment template (commit `1b64323`, 2026-01-26).

## Action items (with owner and due date where stated)
- (none explicitly recorded in the source artifact)

## Blockers and open questions
- Work item AB#3151 remains in **Active** state; acceptance criteria (overview of solution, stability enhancements, TODO fixes, removal of "Sample"-named classes, developer docs) are not confirmed as fully met in the source artifact.

## Implementation detail (commits, files, line counts where present)

**Pull Requests**
| PR | Title | Merged |
|----|-------|--------|
| #349 | Add Credential Injection, Unit Tests and Misc. Minor Improvements | 2026-03-05 |
| #352 | Add Skipping of Feedback Errors and Email Notifications of Errors | 2026-03-10 |
| #354 | Adapt to new SMTP Staging and Add Integration Tests | 2026-04-07 |

All PRs merged via rebase strategy by [Developer 1].

**Commit log**
| Date | Hash | Summary |
|------|------|---------|
| 2026-01-13 | `af524da` | Add unit tests, fix logging issues — 21 files, +1 271 / −72 |
| 2026-01-13 | `baedcb0` | Add credentials — 1 file, +1 / −2 |
| 2026-01-26 | `1b64323` | Add README.md, `TestConfigCommand.cs`, Kubernetes secret credential loading — 7 files, +562 / −33 |
| 2026-01-26 | `fb836a7` | Revert overzealous changes — 11 files, +52 / −293 |
| 2026-01-26 | `af4e2d1` | Restore parity with origin/main — 1 file, +2 / −2 |
| 2026-01-26 | `864a968` | Fix warnings/suggestions in unit tests — 3 files, +12 / −9 |
| 2026-02-09 | `54f0b02` | Rename `TestConfigCommand.cs` → `DisplayConfigCommand.cs`; prepare Kustomize — 9 files, +253 / −6 |
| 2026-02-10 | `bd36650` | Update `DisplayConfigCommand.cs`; continue Kustomize migration — 6 files, +86 / −68 |
| 2026-02-10 | `6db7a94` | Remove deprecated deployment files — 6 files, −237 |
| 2026-02-10 | `d0401b8` | Update `DisplayConfigCommand.cs` — 1 file, +2 / −6 |
| 2026-02-17 | `428dd75` | Update README.md — 1 file, +1 / −11 |
| 2026-02-19 | `85259a2` | Test build — 1 file, +1 |
| 2026-02-19 | `cf4b66f` | Move files from staging to production overlay — 4 files, 0 net |
| 2026-02-19 | `0560803` | Update staging naming; fix version number bug in `azure-pipelines.yml` — 3 files, +5 / −5 |
| 2026-02-19 | `b8bb38a` | Move StorageClass creation to chore task — 3 files, +61 / −30 |
| 2026-02-19 | `ae4873b` | Switch to built-in StorageClass — 2 files, +1 / −31 |
| 2026-02-19 | `83f7507` | Remove ACR secret (now cluster-managed) — 4 files, +42 / −45 |
| 2026-03-05 | `fb7269b` | Convert credentials file to `.example`; add to `.gitignore` — 2 files, +16 / −5 |
| 2026-03-05 | `0eb0805` | Change `cronjobs.yaml` permissions — 1 file, +8 / −4 |
| 2026-03-05 | `70f7117` | Add staging deployment; `imagePullPolicy` → `IfNotPresent`; version replacement made pipeline-specific — 7 files, +99 / −12 |
| 2026-03-05 | `45507d5` | Map staging to `lkv` namespace — 2 files, +7 / −7 |
| 2026-03-05 | `20d9d37` | Add `backoffLimit` and `activeDeadlineSeconds` to `cronjobs.yaml` — 1 file, +8 |
| 2026-03-23 | `5f6cb6d` | Bump Billbee API Client to 2.4.3 — 2 files, +2 / −2 |

**Notable file-level changes**
- `tests/LKVLogistic.Cli.Tests/` — five new test files added (`AutoMapperTests.cs`, `CsvAuftragsImportTests.cs`, `CsvAuftragsRueckmeldungTests.cs`, `CsvBestandsmeldungTests.cs`, `OrderMapperTests.cs`), totalling hundreds of lines of unit-test coverage.
- `LKVLogistic.Cli.IntegrationTests` project added (PR #354) with 19 integration tests using Testcontainers (SFTPGo) and Moq.
- `deployment/base/cronjobs.yaml` — new base manifest introduced (commit `54f0b02`) and iteratively refined across multiple commits.
- `README.md` — substantially expanded (commit `1b64323`, +453 lines) and subsequently refined.
- `src/LKVLogistic.Cli/Commands/` — `SampleOptions.cs` renamed to `GlobalOptions.cs`; multiple command classes updated for credential injection and logging fixes.

**Totals:** 99 files changed, 2 729 insertions(+), 643 deletions(−)

## Sources
- Development activity report CS-04_Infrastructure_and_Deployment_compiled, work item AB#3151, period 2026-01-13 to 2026-03-23.