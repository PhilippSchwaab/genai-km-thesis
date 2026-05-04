# Wiki Entry: CS-04 — Infrastructure and Deployment

---

## Metadata

| Field | Value |
|---|---|
| **Source Artifact** | CS-04_Infrastructure_and_Deployment_compiled (development_activity) |
| **Work Item** | AB#3151 |
| **Project** | [Project Name] |
| **Period** | 2026-01-13 to 2026-03-23 |
| **Total Commits** | 23 |
| **Total File Changes** | 99 files changed, 2,729 insertions(+), 643 deletions(−) |
| **Primary Contributor** | [Developer 1] |

---

## Work Item Summary

### AB#3151 — LKV: Familiarize Yourself with the Topic and the Current Solution

- **Type:** Issue
- **State:** Active
- **Assigned To:** [Developer 1]

**Goal:** Review the existing implementation, improve stability, resolve outstanding TODOs, rename placeholder classes (e.g. classes named "Sample"), and produce developer documentation.

**Acceptance Criteria (as stated in work item):**
1. Overview of solution produced.
2. Stability of implementation enhanced.
3. TODOs resolved; placeholder-named classes (e.g. "Sample") renamed.
4. Developer documentation exists.

---

## Pull Requests

### PR #349 — Add Credential Injection, Unit Tests and Misc. Minor Improvements

| Field | Value |
|---|---|
| **Author** | [Developer 1] |
| **Created** | 2026-02-19 |
| **Completed** | 2026-03-05 |
| **Merge Strategy** | Rebase |

**Scope:** Credential injection, unit test additions, and miscellaneous minor improvements.

---

### PR #352 — Add Skipping of Feedback Errors and Email Notifications of Errors

| Field | Value |
|---|---|
| **Author** | [Developer 1] |
| **Created** | 2026-03-10 |
| **Completed** | 2026-03-10 |
| **Merge Strategy** | Rebase |

**Scope:**
- Added an SFTP server for integration testing (staging environment).
- Added SMTP support for sending error notification emails when configured.
- Errors in `CsvAuftragsRueckmeldung.cs` and `CsvBestandsmeldung.cs` are now handled gracefully (no crash on error).

---

### PR #354 — Adapt to New SMTP Staging and Add Integration Tests

| Field | Value |
|---|---|
| **Author** | [Developer 1] |
| **Created** | 2026-03-23 |
| **Completed** | 2026-04-07 |
| **Merge Strategy** | Rebase |

**Scope:**
- Added 19 integration tests in the new `LKVLogistic.Cli.IntegrationTests` project.
- Integration tests use Testcontainers (SFTPGo) and Moq.
- Adapted to new SMTP staging configuration.

---

## Decisions

| # | Decision | Evidence (Commit) | Attributed To |
|---|---|---|---|
| 1 | Adopt Kustomize for credential and deployment management, replacing legacy deployment template files. | `54f0b02`, `bd36650` | [Developer 1] |
| 2 | Remove ACR (Azure Container Registry) secret from deployment manifests; ACR authentication is now handled at the cluster level. | `83f7507` | [Developer 1] |
| 3 | Switch to the built-in Kubernetes storage class instead of a custom `StorageClass` resource. | `ae4873b` | [Developer 1] |
| 4 | Move `StorageClass` creation to a separate chore/admin task rather than including it in the standard deployment. | `b8bb38a` | [Developer 1] |
| 5 | Change `imagePullPolicy` to `IfNotPresent` in cronjob manifests. | `70f7117` | [Developer 1] |
| 6 | Remove automated version number replacement from deployment manifests; version replacement is now pipeline-specific. | `70f7117` | [Developer 1] |
| 7 | Rename `TestConfigCommand.cs` to `DisplayConfigCommand.cs` and expose it via the `displayconfig` CLI call. | `54f0b02`, `bd36650` | [Developer 1] |
| 8 | Exclude `credentials-secret.yaml` from version control (added to `.gitignore`); provide `credentials-secret.yaml.example` as a template instead. | `fb7269b` | [Developer 1] |
| 9 | Map the staging overlay to the same available `lkv` namespace (rather than a separate staging namespace). | `45507d5` | [Developer 1] |
| 10 | Add `backoffLimit` and `activeDeadlineSeconds` to `cronjobs.yaml` for improved job reliability. | `20d9d37` | [Developer 1] |
| 11 | Use Testcontainers (SFTPGo) and Moq as the integration testing stack. | PR #354 description | [Developer 1] |

---

## Key Changes by Theme

### Testing
- Added comprehensive unit test suite (`AutoMapperTests`, `CsvAuftragsImportTests`, `CsvAuftragsRueckmeldungTests`, `CsvBestandsmeldungTests`, `OrderMapperTests`) — commit `af524da`.
- Fixed unit test warnings and suggestions — commit `864a968`.
- Added `LKVLogistic.Cli.IntegrationTests` project with 19 integration tests using Testcontainers (SFTPGo) and Moq — PR #354.

### Credential & Secret Management
- Added credential loading via Kubernetes secrets in the deployment template — commit `1b64323`.
- Prepared and implemented Kustomize-based credential management — commits `54f0b02`, `bd36650`.
- Converted `credentials-secret.yaml` to an example file and gitignored the real secret — commit `fb7269b`.

### Deployment Structure (Kustomize Migration)
- Created `deployment/base/` with `cronjobs.yaml`, `kustomization.yaml` — commit `54f0b02`.
- Created `deployment/overlays/lkv/staging/` and `deployment/overlays/lkv/production/` overlay directories — commits `54f0b02`, `cf4b66f`, `70f7117`.
- Removed deprecated legacy staging and production deployment template files — commits `fb836a7`, `6db7a94`.

### CI/CD Pipeline (`azure-pipelines.yml`)
- Fixed version number bug in pipeline — commit `0560803`.
- Updated staging naming conventions — commit `0560803`.
- Removed automated version replacement from pipeline (made pipeline-specific) — commit `70f7117`.

### Error Handling
- Errors in `CsvAuftragsRueckmeldung.cs` and `CsvBestandsmeldung.cs` no longer cause a crash; errors are skipped gracefully — PR #352.
- Added SMTP-based error email notifications (when configured) — PR #352.

### Documentation
- Added `README.md` with extensive documentation (453+ lines) — commit `1b64323`.
- Updated `README.md` iteratively — commits `428dd75`, `b8bb38a`, `83f7507`.

### Dependency Updates
- Bumped Billbee API Client to version 2.4.3 — commit `5f6cb6d`.

---

## Commit Log Summary

| Date | Hash | Summary |
|---|---|---|
| 2026-01-13 | `af524da` | Add unit tests; fix logging issues |
| 2026-01-13 | `baedcb0` | Add credentials |
| 2026-01-26 | `1b64323` | Add README.md; add `TestConfigCommand.cs`; add Kubernetes secret credential loading |
| 2026-01-26 | `fb836a7` | Revert overzealous changes |
| 2026-01-26 | `af4e2d1` | Restore parity with `origin/main` |
| 2026-01-26 | `864a968` | Fix warnings/suggestions in unit tests |
| 2026-02-09 | `54f0b02` | Rename `TestConfigCommand.cs` → `DisplayConfigCommand.cs`; prepare Kustomize structure |
| 2026-02-10 | `bd36650` | Update `DisplayConfigCommand.cs` for `displayconfig` CLI call; continue Kustomize migration |
| 2026-02-10 | `6db7a94` | Remove deprecated deployment files |
| 2026-02-10 | `d0401b8` | Update `DisplayConfigCommand.cs` |
| 2026-02-17 | `428dd75` | Update README.md |
| 2026-02-19 | `85259a2` | Test build |
| 2026-02-19 | `cf4b66f` | Move overlay files from staging to production directory |
| 2026-02-19 | `0560803` | Update staging naming; fix version number bug in `azure-pipelines.yml` |
| 2026-02-19 | `b8bb38a` | Move `StorageClass` creation to admin/chore task |
| 2026-02-19 | `ae4873b` | Switch to built-in storage class |
| 2026-02-19 | `83f7507` | Remove ACR secret (now handled by cluster) |
| 2026-03-05 | `fb7269b` | Convert `credentials-secret.yaml` to `.example`; add to `.gitignore` |
| 2026-03-05 | `0eb0805` | Update `cronjobs.yaml` permissions |
| 2026-03-05 | `70f7117` | Add staging deployment; set `imagePullPolicy: IfNotPresent`; remove automated version replacement |
| 2026-03-05 | `45507d5` | Map staging to `lkv` namespace |
| 2026-03-05 | `20d9d37` | Add `backoffLimit` and `activeDeadlineSeconds` to `cronjobs.yaml` |
| 2026-03-23 | `5f6cb6d` | Bump Billbee API Client to 2.4.3 |

---

## Action Items & Outstanding Work

> *Note: The work item AB#3151 remains in **Active** state as of the period end (2026-03-23). PR #354 was still open (completed 2026-04-07, outside the artifact period).*

| # | Action Item | Status | Assigned To |
|---|---|---|---|
| 1 | Complete and merge PR #354 (integration tests + SMTP staging adaptation) | In Progress (created 2026-03-23, merged 2026-04-07) | [Developer 1] |
| 2 | Resolve remaining acceptance criteria for AB#3151 (solution overview, stability, TODOs, docs) | Active | [Developer 1] |

---

## Blockers

*No explicit blockers were recorded in the source artifact.*

---

## Related Artifacts

| Reference | Description |
|---|---|
| AB#3151 | Parent work item: LKV familiarization and solution improvement |
| PR #349 | Credential injection, unit tests, minor improvements |
| PR #352 | SFTP staging server, SMTP error notifications, graceful error handling |
| PR #354 | Integration tests (19 tests), SMTP staging adaptation |