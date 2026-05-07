## Summary
Infrastructure and deployment overhaul for the LKVLogistic CLI service under work item AB#3151 ([Developer 1]), covering the period 2026-01-13 to 2026-03-23. Work included: credential injection via Kubernetes secrets and Kustomize overlays, unit and integration test additions, error-handling improvements (skipping feedback errors, SMTP email notifications), SFTP server for integration testing, and general deployment hygiene (renamed placeholder classes, removed deprecated files, updated README and developer docs). Three PRs were raised and merged; the work item remains active.

---

## Decisions
- **Credential management via Kustomize:** Adopt Kustomize overlays for credential management instead of inline secrets in deployment templates. `credentials-secret.yaml` added to `.gitignore`; an `.example` file committed in its place to avoid secret leakage. (Commits `54f0b02`, `fb7269b`)
- **ACR secret removed from manifests:** ACR pull secret is now handled at the cluster level and no longer needs to be declared in deployment manifests. (Commit `83f7507`)
- **Built-in StorageClass used:** Switched from a custom `StorageClass` definition to the cluster's built-in StorageClass; custom `storageclass.yaml` removed. (Commits `b8bb38a`, `ae4873b`)
- **`imagePullPolicy` set to `IfNotPresent`:** Changed from default to `IfNotPresent` in `cronjobs.yaml`. (Commit `70f7117`)
- **Version number replacement made pipeline-specific:** Automated version replacement removed from deployment manifests; responsibility moved to the CI pipeline. (Commit `70f7117`)
- **`TestConfigCommand.cs` renamed to `DisplayConfigCommand.cs`:** Placeholder/sample naming resolved; CLI call updated to `displayconfig`. (Commits `54f0b02`, `bd36650`)
- **Error skipping in feedback processing:** Errors in `CsvAuftragsRueckmeldung.cs` and `CsvBestandsmeldung.cs` no longer crash the process; they are caught and skipped. (PR #352)
- **SMTP email notifications on error:** SMTP support added for error alerting when configured. (PR #352)
- **Integration tests use Testcontainers + SFTPGo:** `LKVLogistic.Cli.IntegrationTests` project introduced using Testcontainers (SFTPGo) and Moq for 19 integration tests. (PR #354)
- **Billbee API Client bumped to 2.4.3.** (Commit `5f6cb6d`)
- **`backoffLimit` and `activeDeadlineSeconds` added to `cronjobs.yaml`:** Improves job failure behaviour and prevents runaway jobs. (Commit `20d9d37`)

---

## Action items (with owner and due date where stated)
- (none recorded)

---

## Blockers and open questions
- Work item AB#3151 remains in **Active** state; full closure (including all acceptance criteria) is not yet confirmed.
- Acceptance criteria still to be verified as complete:
  - Overview of solution documented *(README updated — partially addressed)*
  - Stability of implementation enhanced
  - All TODOs fixed
  - All classes named "Sample" renamed

---

## Implementation detail (commits, files, line counts where present)

**Pull Requests**

| PR | Title | Merged |
|----|-------|--------|
| #349 | Add Credential Injection, UnitTests and Misc. Minor Improvements | 2026-03-05 |
| #352 | Add Skipping of Feedback Errors and Email Notifications of Errors | 2026-03-10 |
| #354 | Adapt to new SMTP Staging and Add Integration Tests (19 tests) | 2026-04-07 |

All PRs authored by [Developer 1]; all merged via rebase strategy.

---

**Commit log**

| Date | Hash | Summary |
|------|------|---------|
| 2026-01-13 | `af524da` | Add unit tests, fix logging issues |
| 2026-01-13 | `baedcb0` | Add credentials |
| 2026-01-26 | `1b64323` | Add README.md, TestConfigCommand.cs, Kubernetes secret loading in deployment template |
| 2026-01-26 | `fb836a7` | Revert overzealous changes |
| 2026-01-26 | `af4e2d1` | Restore parity with origin/main |
| 2026-01-26 | `864a968` | Fix warnings/suggestions in unit tests |
| 2026-02-09 | `54f0b02` | Rename TestConfigCommand → DisplayConfigCommand; prepare Kustomize |
| 2026-02-10 | `bd36650` | Update DisplayConfigCommand to use `displayconfig` CLI call; continue Kustomize migration |
| 2026-02-10 | `6db7a94` | Remove deprecated deployment files |
| 2026-02-10 | `d0401b8` | Update DisplayConfigCommand.cs |
| 2026-02-17 | `428dd75` | Update README.md |
| 2026-02-19 | `85259a2` | Test build |
| 2026-02-19 | `cf4b66f` | Move files from staging to production overlay |
| 2026-02-19 | `0560803` | Update staging naming; fix version number bug in azure-pipelines.yml |
| 2026-02-19 | `b8bb38a` | Move StorageClass creation to chore task |
| 2026-02-19 | `ae4873b` | Switch to built-in StorageClass |
| 2026-02-19 | `83f7507` | Remove ACR secret (now handled by cluster) |
| 2026-03-05 | `fb7269b` | Convert credentials-secret.yaml to .example; add to .gitignore |
| 2026-03-05 | `0eb0805` | Change cronjobs.yaml permissions |
| 2026-03-05 | `70f7117` | Add staging deployment; set imagePullPolicy=IfNotPresent; make version replacement pipeline-specific |
| 2026-03-05 | `45507d5` | Map staging to lkv namespace |
| 2026-03-05 | `20d9d37` | Add backoffLimit and activeDeadlineSeconds to cronjobs.yaml |
| 2026-03-23 | `5f6cb6d` | Bump Billbee API Client to 2.4.3 |

---

**Notable file-level changes**

| File / Area | Notable change |
|---|---|
| `tests/LKVLogistic.Cli.Tests/` | 5 new test files added (`AutoMapperTests.cs`, `CsvAuftragsImportTests.cs`, `CsvAuftragsRueckmeldungTests.cs`, `CsvBestandsmeldungTests.cs`, `OrderMapperTests.cs`) |
| `deployment/base/` | New Kustomize base: `cronjobs.yaml`, `kustomization.yaml`; `acr-secret.yaml` later removed |
| `deployment/overlays/lkv/production/` | Full Kustomize production overlay introduced |
| `deployment/overlays/lkv/staging/` | Full Kustomize staging overlay introduced |
| `deployment/staging/` (old) | All 6 legacy staging deployment files removed (`237 deletions`) |
| `README.md` | Substantially expanded (+453 lines in `1b64323`) |
| `src/LKVLogistic.Cli/Commands/DisplayConfigCommand.cs` | Renamed from `TestConfigCommand.cs` |
| `.gitignore` | `credentials-secret.yaml` added to prevent secret commits |
| `devops-build/azure-pipelines.yml` | Multiple pipeline fixes across the period |

---

**Aggregate change statistics (23 commits)**

| Metric | Value |
|--------|-------|
| Total commits | 23 |
| Files changed | 99 |
| Insertions | 2,729 |
| Deletions | 643 |

---

## Sources
- Development activity report: CS-04_Infrastructure_and_Deployment_compiled, work item AB#3151, period 2026-01-13 to 2026-03-23.