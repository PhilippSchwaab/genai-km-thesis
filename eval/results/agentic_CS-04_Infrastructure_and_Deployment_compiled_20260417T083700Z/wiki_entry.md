# Wiki Entry: CS-04 — Infrastructure and Deployment

**Source Artifact:** CS-04_Infrastructure_and_Deployment_compiled (development_activity)
**Project:** [Project Name]
**Work Item:** AB#3151
**Period:** 2026-01-13 to 2026-03-23
**Total Commits:** 23
**Author:** [Developer 1]

---

## 1. Work Item Overview

| Field       | Value                                                             |
|-------------|-------------------------------------------------------------------|
| ID          | AB#3151                                                           |
| Title       | LKV: familiarize yourself with the topic and the current solution |
| Type        | Issue                                                             |
| State       | Active                                                            |
| Assigned To | [Developer 1]                                                     |

**Description:** The goal is to check the current implementation and get familiar with the topic.

### Acceptance Criteria
- Overview of solution produced
- Stability of implementation enhanced
- TODOs fixed
- Classes named e.g. "Sample" renamed appropriately
- Developer documentation exists

---

## 2. Pull Requests

### PR #349 — Add Credential Injection, UnitTests and Misc. Minor Improvements

| Field          | Value      |
|----------------|------------|
| Author         | [Developer 1] |
| Created        | 2026-02-19 |
| Completed      | 2026-03-05 |
| Merge Strategy | Rebase     |

---

### PR #352 — Add Skipping of Feedback Errors and Email Notifications of Errors

| Field          | Value      |
|----------------|------------|
| Author         | [Developer 1] |
| Created        | 2026-03-10 |
| Completed      | 2026-03-10 |
| Merge Strategy | Rebase     |

**Changes introduced:**
- Added an SFTP Server for Integration Testing (Staging)
- Added SMTP for sending error notification emails when configured
- Errors in `CsvAuftragsRueckmeldung.cs` and `CsvBestandsmeldung.cs` no longer cause crashes (graceful skip)

---

### PR #354 — Adapt to new SMTP Staging and Add Integration Tests

| Field          | Value      |
|----------------|------------|
| Author         | [Developer 1] |
| Created        | 2026-03-23 |
| Completed      | 2026-04-07 |
| Merge Strategy | Rebase     |

**Changes introduced:**
- Added 19 integration tests via the `LKVLogistic.Cli.IntegrationTests` project
- Uses Testcontainers (SFTPGo) and Moq

---

## 3. Commit Timeline

| Date       | Hash    | Summary                                                                                                          |
|------------|---------|------------------------------------------------------------------------------------------------------------------|
| 2026-01-13 | af524da | Add unit tests; fix logging issues                                                                               |
| 2026-01-13 | baedcb0 | Add credentials                                                                                                  |
| 2026-01-26 | 1b64323 | Add README.md; add TestConfigCommand.cs; add loading of credentials via Kubernetes secrets in deployment template |
| 2026-01-26 | fb836a7 | Revert overzealous changes                                                                                       |
| 2026-01-26 | af4e2d1 | Restore parity with origin/main                                                                                  |
| 2026-01-26 | 864a968 | Fix warnings/suggestions in unit tests                                                                           |
| 2026-02-09 | 54f0b02 | Rename TestConfigCommand.cs → DisplayConfigCommand.cs; prepare for Kustomize credential management               |
| 2026-02-10 | bd36650 | Update DisplayConfigCommand.cs to use `displayconfig` CLI call; continue Kustomize modifications                 |
| 2026-02-10 | 6db7a94 | Remove deprecated deployment files                                                                               |
| 2026-02-10 | d0401b8 | Update DisplayConfigCommand.cs                                                                                   |
| 2026-02-17 | 428dd75 | Update README.md                                                                                                 |
| 2026-02-19 | 85259a2 | Test build                                                                                                       |
| 2026-02-19 | cf4b66f | Move files from Staging to Production                                                                            |
| 2026-02-19 | 0560803 | Update Staging naming; fix version number bug in azure-pipelines.yml                                             |
| 2026-02-19 | b8bb38a | Move creation of StorageClass to chore task                                                                      |
| 2026-02-19 | ae4873b | Change to use built-in StorageClass                                                                              |
| 2026-02-19 | 83f7507 | Remove ACR secret (now handled by cluster)                                                                       |
| 2026-03-05 | fb7269b | Rename credentials-secret.yaml → credentials-secret.yaml.example; add credentials-secret.yaml to .gitignore     |
| 2026-03-05 | 0eb0805 | Change cronjobs.yaml permissions                                                                                 |
| 2026-03-05 | 70f7117 | Add Staging deployment; change imagePullPolicy to IfNotPresent; make version replacement pipeline-specific       |
| 2026-03-05 | 45507d5 | Map Staging to same available lkv namespace                                                                      |
| 2026-03-05 | 20d9d37 | Add backoffLimit and activeDeadlineSeconds to cronjobs.yaml                                                      |
| 2026-03-23 | 5f6cb6d | Bump Billbee API Client to 2.4.3                                                                                 |

---

## 4. Key Technical Changes

### 4.1 Credential & Secret Management
- Credentials injected via Kubernetes secrets in the deployment template (commit `1b64323`)
- Adopted Kustomize for credential management (commits `54f0b02`, `bd36650`)
- `credentials-secret.yaml` converted to an example file (`credentials-secret.yaml.example`) and excluded from version control via `.gitignore` (commit `fb7269b`)
- ACR secret removed from deployment manifests as it is now handled by the cluster (commit `83f7507`)

### 4.2 Deployment Structure Refactoring
- Deprecated legacy deployment files removed (commit `6db7a94`); specifically removed from `deployment/staging/`: `0_setup.ps1`, `deployment-template-staging.yaml`, `namespace.yaml`, `replace-versioninfo.sh`, `secrets.yaml`, `storage.yaml`
- Deployment reorganized into a Kustomize base/overlay structure: `deployment/base/`, `deployment/overlays/lkv/production/`, `deployment/overlays/lkv/staging/`
- Files moved from Staging overlay to Production overlay (commit `cf4b66f`): `credentials-secret.yaml`, `kustomization.yaml`, `namespace.yaml`, `storage.yaml`
- Staging mapped to the same available `lkv` namespace (commit `45507d5`)
- StorageClass creation moved to a separate admin chore task (`deployment/admin/storageclass.yaml`); subsequently switched to built-in StorageClass (commits `b8bb38a`, `ae4873b`)
- `imagePullPolicy` changed to `IfNotPresent` (commit `70f7117`)
- `backoffLimit` and `activeDeadlineSeconds` added to `cronjobs.yaml` (commit `20d9d37`)
- `cronjobs.yaml` permissions updated (commit `0eb0805`)

### 4.3 CI/CD Pipeline
- Version number bug fixed in `azure-pipelines.yml` (commit `0560803`)
- Automated version number replacement removed from manifests; made pipeline-specific (commit `70f7117`)

### 4.4 Testing
- Unit tests added across multiple new test files (commit `af524da`):
  - `tests/LKVLogistic.Cli.Tests/AutoMapperTests.cs`
  - `tests/LKVLogistic.Cli.Tests/CsvAuftragsImportTests.cs`
  - `tests/LKVLogistic.Cli.Tests/CsvAuftragsRueckmeldungTests.cs`
  - `tests/LKVLogistic.Cli.Tests/CsvBestandsmeldungTests.cs`
  - `tests/LKVLogistic.Cli.Tests/OrderMapperTests.cs`
- Unit test warnings and suggestions resolved (commit `864a968`)
- SFTP Server added for integration testing in Staging (PR #352)
- 19 integration tests added in `LKVLogistic.Cli.IntegrationTests` using Testcontainers (SFTPGo) and Moq (PR #354)

### 4.5 Developer Experience & Documentation
- `README.md` added and iteratively updated (commits `1b64323`, `428dd75`, `b8bb38a`, `83f7507`)
- `TestConfigCommand.cs` added (commit `1b64323`), then renamed to `DisplayConfigCommand.cs` (commit `54f0b02`); CLI call updated to `displayconfig` (commit `bd36650`)
- `SampleOptions.cs` renamed to `GlobalOptions.cs` (commit `af524da`)

### 4.6 Error Handling & Notifications
- SMTP support added for sending error notification emails when configured (PR #352)
- Graceful error skipping implemented in `CsvAuftragsRueckmeldung.cs` and `CsvBestandsmeldung.cs` — errors no longer cause crashes (PR #352)

### 4.7 Dependency Updates
- Billbee API Client bumped to version 2.4.3, affecting `LKVLogistic.Cli.csproj` and `LkvLogistic.csproj` (commit `5f6cb6d`)

---

## 5. Notable Files Changed (Selected)

| Commit  | File(s)                                                        | Nature of Change                                      |
|---------|----------------------------------------------------------------|-------------------------------------------------------|
| af524da | `src/LKVLogistic.Cli/{SampleOptions.cs → GlobalOptions.cs}`   | Rename "Sample" class to production name              |
| af524da | `src/LkvLogistic/CsvAuftragsRueckmeldung.cs`                  | Modified                                              |
| af524da | Multiple command files (`DownloadFilesCommand.cs`, `SyncOrderFeedbackCommand.cs`, `SyncOrdersCommand.cs`, `SyncProductsCommand.cs`, `SyncStocksCommand.cs`, `UploadFilesCommand.cs`) | Modified |
| 1b64323 | `src/LKVLogistic.Cli/Commands/TestConfigCommand.cs`            | Added (89 lines)                                      |
| 54f0b02 | `deployment/base/cronjobs.yaml`                                | Added (154 lines)                                     |
| 54f0b02 | `deployment/base/kustomization.yaml`                           | Added                                                 |
| 54f0b02 | `deployment/base/acr-secret.yaml`                              | Added (later removed in `83f7507`)                    |
| 70f7117 | `deployment/overlays/lkv/staging/credentials-secret.yaml.example` | Added (36 lines)                                  |
| 5f6cb6d | `src/LKVLogistic.Cli/LKVLogistic.Cli.csproj`, `src/LkvLogistic/LkvLogistic.csproj` | Billbee API Client version bump         |

---

## 6. Change Statistics

| Metric        | Value |
|---------------|-------|
| Files changed | 99    |
| Insertions    | 2,729 |
| Deletions     | 643   |