# Source Artifact CS-04: Infrastructure and Deployment
# Project: [Project Name]
# Work Items: AB#3151
# Period: 2026-01-13 to 2026-03-23
# Total Commits: 23

## Work Item Context

### Work Item AB#3151
- **Title:** LKV: familiarize yourself with the topic and the current solution
- **Type:** Issue
- **State:** Active
- **Assigned To:** [Developer 1]

**Description:**
We want to check the current implementation and get familiar with the topic. 
 Acceptance critera: - Overview of solution - Stability of implementation is enhanced - TODO's are fixed. Classes named e.g . "Sample" are fixed - Developer docs are existing

---

## Pull Requests

### PR #349: AB#3151: Add Credential Injection, UnitTests and Misc. Minor Improvements
- **Author:** [Developer 1]
- **Created:** 2026-02-19
- **Completed:** 2026-03-05
- **Merge strategy:** rebase

### PR #352: AB#3151: Add Skipping of Feedback Errors and Email Notifications of Errors
- **Author:** [Developer 1]
- **Created:** 2026-03-10
- **Completed:** 2026-03-10
- **Merge strategy:** rebase

**Description:**
Add an SFTP Server For Integration Testing (Staging)
Add SMTP for Sending Emails of Errors if Configured
Ignore (Don't) Crash on Errors in CsvAuftragsRueckmeldung.cs and CsvBestandsmeldung.cs

### PR #354: Ab#3151: Adapt to new SMTP Staging and Add Integration tests
- **Author:** [Developer 1]
- **Created:** 2026-03-23
- **Completed:** 2026-04-07
- **Merge strategy:** rebase

**Description:**
New: Integration Tests (19 tests)                                                                                                          
  - LKVLogistic.Cli.IntegrationTests project with Testcontainers (SFTPGo) + Moq


---

## Commit Log (chronological)

| Date | Hash | Message |
|------|------|---------|
| 2026-01-13 | af524da | AB#3151: Add Unit tests, fix logging issues |
| 2026-01-13 | baedcb0 | AB#3151: Add credentials |
| 2026-01-26 | 1b64323 | AB#3151: Add README.md, Add TestConfigCommand.cs, Add loading of credentials via kubernetes secrets in deployment template |
| 2026-01-26 | fb836a7 | AB#3151: Revert overzealous changes |
| 2026-01-26 | af4e2d1 | AB#3151: Restore parity with origin/main |
| 2026-01-26 | 864a968 | AB#3151: Fix Warnings/Suggestions in Unit tests |
| 2026-02-09 | 54f0b02 | AB#3151: Rename TestConfigCommand.cs to DisplayConfigCommand.cs. Prepare for Kustomize implementation for credential management. |
| 2026-02-10 | bd36650 | AB#3151: Update DisplayConfigCommand.cs to use displayconfig as cli call. Continue modification to use kustomize. |
| 2026-02-10 | 6db7a94 | AB#3151: Remove depreciated deployment files |
| 2026-02-10 | d0401b8 | AB#3151: Updated DisplayConfigCommand.cs |
| 2026-02-17 | 428dd75 | AB#3151: Update README.md |
| 2026-02-19 | 85259a2 | AB#3151: Test Build |
| 2026-02-19 | cf4b66f | AB#3151: Move Files from Staging to Production |
| 2026-02-19 | 0560803 | AB#3151: Update Staging naming and fix version number bug in azure-pipelines.yml |
| 2026-02-19 | b8bb38a | AB#3151: Move Creation of StorageClass to chore task |
| 2026-02-19 | ae4873b | AB#3151: Change to use built in storageclass |
| 2026-02-19 | 83f7507 | AB#3151: Remove acr secret now handled by cluster |
| 2026-03-05 | fb7269b | AB#3151: Change credentials-secret.yaml to credentials-secret.yaml.example and add credentials-secret.yaml to .gitignore |
| 2026-03-05 | 0eb0805 | AB#3151: Change cronjobs.yaml Permissions |
| 2026-03-05 | 70f7117 | AB#3151: Add Staging deployment. Change imagePullPolicy to IfNotPresent. Remove Automated Replacement of Version number make it pipeline specific. |
| 2026-03-05 | 45507d5 | AB#3151: Map Staging to same available lkv namespace |
| 2026-03-05 | 20d9d37 | AB#3151: Add backoffLimit and activeDeadlineSeconds to cronjobs.yaml |


## Commit Details

### af524da — AB#3151: Add Unit tests, fix logging issues
- **Date:** 2026-01-13
- **Author:** [Developer 1]


### baedcb0 — AB#3151: Add credentials
- **Date:** 2026-01-13
- **Author:** [Developer 1]


### 1b64323 — AB#3151: Add README.md, Add TestConfigCommand.cs, Add loading of credentials via kubernetes secrets in deployment template
- **Date:** 2026-01-26
- **Author:** [Developer 1]


### fb836a7 — AB#3151: Revert overzealous changes
- **Date:** 2026-01-26
- **Author:** [Developer 1]


### af4e2d1 — AB#3151: Restore parity with origin/main
- **Date:** 2026-01-26
- **Author:** [Developer 1]


### 864a968 — AB#3151: Fix Warnings/Suggestions in Unit tests
- **Date:** 2026-01-26
- **Author:** [Developer 1]


### 54f0b02 — AB#3151: Rename TestConfigCommand.cs to DisplayConfigCommand.cs. Prepare for Kustomize implementation for credential management.
- **Date:** 2026-02-09
- **Author:** [Developer 1]


### bd36650 — AB#3151: Update DisplayConfigCommand.cs to use displayconfig as cli call. Continue modification to use kustomize.
- **Date:** 2026-02-10
- **Author:** [Developer 1]


### 6db7a94 — AB#3151: Remove depreciated deployment files
- **Date:** 2026-02-10
- **Author:** [Developer 1]


### d0401b8 — AB#3151: Updated DisplayConfigCommand.cs
- **Date:** 2026-02-10
- **Author:** [Developer 1]


### 428dd75 — AB#3151: Update README.md
- **Date:** 2026-02-17
- **Author:** [Developer 1]


### 85259a2 — AB#3151: Test Build
- **Date:** 2026-02-19
- **Author:** [Developer 1]


### cf4b66f — AB#3151: Move Files from Staging to Production
- **Date:** 2026-02-19
- **Author:** [Developer 1]


### 0560803 — AB#3151: Update Staging naming and fix version number bug in azure-pipelines.yml
- **Date:** 2026-02-19
- **Author:** [Developer 1]


### b8bb38a — AB#3151: Move Creation of StorageClass to chore task
- **Date:** 2026-02-19
- **Author:** [Developer 1]


### ae4873b — AB#3151: Change to use built in storageclass
- **Date:** 2026-02-19
- **Author:** [Developer 1]


### 83f7507 — AB#3151: Remove acr secret now handled by cluster
- **Date:** 2026-02-19
- **Author:** [Developer 1]


### fb7269b — AB#3151: Change credentials-secret.yaml to credentials-secret.yaml.example and add credentials-secret.yaml to .gitignore
- **Date:** 2026-03-05
- **Author:** [Developer 1]


### 0eb0805 — AB#3151: Change cronjobs.yaml Permissions
- **Date:** 2026-03-05
- **Author:** [Developer 1]


### 70f7117 — AB#3151: Add Staging deployment. Change imagePullPolicy to IfNotPresent. Remove Automated Replacement of Version number make it pipeline specific.
- **Date:** 2026-03-05
- **Author:** [Developer 1]


### 45507d5 — AB#3151: Map Staging to same available lkv namespace
- **Date:** 2026-03-05
- **Author:** [Developer 1]


### 20d9d37 — AB#3151: Add backoffLimit and activeDeadlineSeconds to cronjobs.yaml
- **Date:** 2026-03-05
- **Author:** [Developer 1]


### 5f6cb6d — AB#3151: Bump Billbee API Client to 2.4.3
- **Date:** 2026-03-23
- **Author:** [Developer 1]


---

## Files Changed

**af524da — AB#3151: Add Unit tests, fix logging issues**
 deployment/production/0_setup.ps1                  |   9 +
 .../production/deployment-template-production.yaml | 144 +++++++++++++
 deployment/production/namespace.yaml               |   5 +
 deployment/production/replace-versioninfo.sh       |  25 +++
 deployment/production/secrets.yaml                 |  11 +
 deployment/production/storage.yaml                 |  32 +++
 devops-build/azure-pipelines.yml                   |  14 +-
 .../Commands/DownloadFilesCommand.cs               |   4 +-
 .../Commands/SyncOrderFeedbackCommand.cs           |  40 ++--
 src/LKVLogistic.Cli/Commands/SyncOrdersCommand.cs  |  24 +--
 .../Commands/SyncProductsCommand.cs                |  30 ++-
 src/LKVLogistic.Cli/Commands/SyncStocksCommand.cs  |  22 +-
 src/LKVLogistic.Cli/Commands/UploadFilesCommand.cs |   4 +-
 .../{SampleOptions.cs => GlobalOptions.cs}         |   2 +-
 src/LKVLogistic.Cli/appsettings.json               |   3 +-
 src/LkvLogistic/CsvAuftragsRueckmeldung.cs         |   9 +-
 tests/LKVLogistic.Cli.Tests/AutoMapperTests.cs     | 156 ++++++++++++++
 .../CsvAuftragsImportTests.cs                      | 222 +++++++++++++++++++
 .../CsvAuftragsRueckmeldungTests.cs                | 184 ++++++++++++++++
 .../CsvBestandsmeldungTests.cs                     | 164 ++++++++++++++
 tests/LKVLogistic.Cli.Tests/OrderMapperTests.cs    | 239 +++++++++++++++++++++
 21 files changed, 1271 insertions(+), 72 deletions(-)

**baedcb0 — AB#3151: Add credentials**
 deployment/production/secrets.yaml | 3 +--
 1 file changed, 1 insertion(+), 2 deletions(-)

**1b64323 — AB#3151: Add README.md, Add TestConfigCommand.cs, Add loading of credentials via kubernetes secrets in deployment template**
 .gitignore                                         |   3 +
 README.md                                          | 453 ++++++++++++++++++++-
 .../production/deployment-template-production.yaml |  12 +
 .../staging/deployment-template-staging.yaml       |  20 +-
 src/LKVLogistic.Cli/Commands/TestConfigCommand.cs  |  89 ++++
 src/LKVLogistic.Cli/Program.cs                     |   1 +
 src/LKVLogistic.Cli/appsettings.json               |  17 +-
 7 files changed, 562 insertions(+), 33 deletions(-)

**fb836a7 — AB#3151: Revert overzealous changes**
 deployment/production/0_setup.ps1                  |   9 --
 .../production/deployment-template-production.yaml | 156 ---------------------
 deployment/production/namespace.yaml               |   5 -
 deployment/production/replace-versioninfo.sh       |  25 ----
 deployment/production/secrets.yaml                 |  10 --
 deployment/production/storage.yaml                 |  32 -----
 devops-build/azure-pipelines.yml                   |  10 +-
 .../Commands/SyncOrderFeedbackCommand.cs           |  36 +++--
 src/LKVLogistic.Cli/Commands/SyncOrdersCommand.cs  |  20 ++-
 .../Commands/SyncProductsCommand.cs                |  26 ++--
 src/LKVLogistic.Cli/Commands/SyncStocksCommand.cs  |  16 +--
 11 files changed, 52 insertions(+), 293 deletions(-)

**af4e2d1 — AB#3151: Restore parity with origin/main**
 devops-build/azure-pipelines.yml | 4 ++--
 1 file changed, 2 insertions(+), 2 deletions(-)

**864a968 — AB#3151: Fix Warnings/Suggestions in Unit tests**
 tests/LKVLogistic.Cli.Tests/CsvAuftragsImportTests.cs       | 7 ++++---
 tests/LKVLogistic.Cli.Tests/CsvAuftragsRueckmeldungTests.cs | 9 +++++----
 tests/LKVLogistic.Cli.Tests/CsvBestandsmeldungTests.cs      | 5 +++--
 3 files changed, 12 insertions(+), 9 deletions(-)

**54f0b02 — AB#3151: Rename TestConfigCommand.cs to DisplayConfigCommand.cs. Prepare for Kustomize implementation for credential management.**
 deployment/base/acr-secret.yaml                    |  13 ++
 deployment/base/cronjobs.yaml                      | 154 +++++++++++++++++++++
 deployment/base/kustomization.yaml                 |   9 ++
 deployment/overlays/lkv/staging/kustomization.yaml |  30 ++++
 deployment/overlays/lkv/staging/namespace.yaml     |   4 +
 deployment/overlays/lkv/staging/storage.yaml       |  36 +++++
 devops-build/azure-pipelines.yml                   |   9 +-
 ...estConfigCommand.cs => DisplayConfigCommand.cs} |   2 +-
 src/LKVLogistic.Cli/Program.cs                     |   2 +-
 9 files changed, 253 insertions(+), 6 deletions(-)

**bd36650 — AB#3151: Update DisplayConfigCommand.cs to use displayconfig as cli call. Continue modification to use kustomize.**
 .gitignore                                         |   3 -
 README.md                                          | 109 ++++++++++-----------
 deployment/base/cronjobs.yaml                      |   2 +-
 .../overlays/lkv/staging/credentials-secret.yaml   |  28 ++++++
 devops-build/azure-pipelines.yml                   |  10 +-
 .../Commands/DisplayConfigCommand.cs               |   2 +-
 6 files changed, 86 insertions(+), 68 deletions(-)

**6db7a94 — AB#3151: Remove depreciated deployment files**
 deployment/staging/0_setup.ps1                     |   9 --
 .../staging/deployment-template-staging.yaml       | 156 ---------------------
 deployment/staging/namespace.yaml                  |   5 -
 deployment/staging/replace-versioninfo.sh          |  25 ----
 deployment/staging/secrets.yaml                    |  10 --
 deployment/staging/storage.yaml                    |  32 -----
 6 files changed, 237 deletions(-)

**d0401b8 — AB#3151: Updated DisplayConfigCommand.cs**
 src/LKVLogistic.Cli/Commands/DisplayConfigCommand.cs | 8 ++------
 1 file changed, 2 insertions(+), 6 deletions(-)

**428dd75 — AB#3151: Update README.md**
 README.md | 12 +-----------
 1 file changed, 1 insertion(+), 11 deletions(-)

**85259a2 — AB#3151: Test Build**
 devops-build/azure-pipelines.yml | 1 +
 1 file changed, 1 insertion(+)

**cf4b66f — AB#3151: Move Files from Staging to Production**
 deployment/overlays/lkv/{staging => production}/credentials-secret.yaml | 0
 deployment/overlays/lkv/{staging => production}/kustomization.yaml      | 0
 deployment/overlays/lkv/{staging => production}/namespace.yaml          | 0
 deployment/overlays/lkv/{staging => production}/storage.yaml            | 0
 4 files changed, 0 insertions(+), 0 deletions(-)

**0560803 — AB#3151: Update Staging naming and fix version number bug in azure-pipelines.yml**
 deployment/overlays/lkv/production/credentials-secret.yaml | 2 +-
 deployment/overlays/lkv/production/kustomization.yaml      | 6 +++---
 devops-build/azure-pipelines.yml                           | 2 +-
 3 files changed, 5 insertions(+), 5 deletions(-)

**b8bb38a — AB#3151: Move Creation of StorageClass to chore task**
 README.md                                       | 31 +++++++++++++++++++------
 deployment/admin/storageclass.yaml              | 30 ++++++++++++++++++++++++
 deployment/overlays/lkv/production/storage.yaml | 30 ++++++------------------
 3 files changed, 61 insertions(+), 30 deletions(-)

**ae4873b — AB#3151: Change to use built in storageclass**
 deployment/admin/storageclass.yaml              | 30 -------------------------
 deployment/overlays/lkv/production/storage.yaml |  2 +-
 2 files changed, 1 insertion(+), 31 deletions(-)

**83f7507 — AB#3151: Remove acr secret now handled by cluster**
 README.md                          | 65 ++++++++++++++++++++++++--------------
 deployment/base/acr-secret.yaml    | 13 --------
 deployment/base/cronjobs.yaml      |  8 -----
 deployment/base/kustomization.yaml |  1 -
 4 files changed, 42 insertions(+), 45 deletions(-)

**fb7269b — AB#3151: Change credentials-secret.yaml to credentials-secret.yaml.example and add credentials-secret.yaml to .gitignore**
 .gitignore                                             |  3 +++
 ...als-secret.yaml => credentials-secret.yaml.example} | 18 +++++++++++++-----
 2 files changed, 16 insertions(+), 5 deletions(-)

**0eb0805 — AB#3151: Change cronjobs.yaml Permissions**
 deployment/base/cronjobs.yaml | 12 ++++++++----
 1 file changed, 8 insertions(+), 4 deletions(-)

**70f7117 — AB#3151: Add Staging deployment. Change imagePullPolicy to IfNotPresent. Remove Automated Replacement of Version number make it pipeline specific.**
 deployment/base/cronjobs.yaml                      |  8 ++---
 .../overlays/lkv/production/kustomization.yaml     |  7 +++--
 .../lkv/staging/credentials-secret.yaml.example    | 36 ++++++++++++++++++++++
 deployment/overlays/lkv/staging/kustomization.yaml | 31 +++++++++++++++++++
 deployment/overlays/lkv/staging/namespace.yaml     |  4 +++
 deployment/overlays/lkv/staging/storage.yaml       | 20 ++++++++++++
 devops-build/azure-pipelines.yml                   |  5 ---
 7 files changed, 99 insertions(+), 12 deletions(-)

**45507d5 — AB#3151: Map Staging to same available lkv namespace**
 deployment/overlays/lkv/staging/kustomization.yaml | 12 ++++++------
 deployment/overlays/lkv/staging/namespace.yaml     |  2 +-
 2 files changed, 7 insertions(+), 7 deletions(-)

**20d9d37 — AB#3151: Add backoffLimit and activeDeadlineSeconds to cronjobs.yaml**
 deployment/base/cronjobs.yaml | 8 ++++++++
 1 file changed, 8 insertions(+)

**5f6cb6d — AB#3151: Bump Billbee API Client to 2.4.3**
 src/LKVLogistic.Cli/LKVLogistic.Cli.csproj | 2 +-
 src/LkvLogistic/LkvLogistic.csproj         | 2 +-
 2 files changed, 2 insertions(+), 2 deletions(-)


---

## Change Summary

```
 21 files changed, 1271 insertions(+), 72 deletions(-)
 1 file changed, 1 insertion(+), 2 deletions(-)
 7 files changed, 562 insertions(+), 33 deletions(-)
 11 files changed, 52 insertions(+), 293 deletions(-)
 1 file changed, 2 insertions(+), 2 deletions(-)
 3 files changed, 12 insertions(+), 9 deletions(-)
 9 files changed, 253 insertions(+), 6 deletions(-)
 6 files changed, 86 insertions(+), 68 deletions(-)
 6 files changed, 237 deletions(-)
 1 file changed, 2 insertions(+), 6 deletions(-)
 1 file changed, 1 insertion(+), 11 deletions(-)
 1 file changed, 1 insertion(+)
 4 files changed, 0 insertions(+), 0 deletions(-)
 3 files changed, 5 insertions(+), 5 deletions(-)
 3 files changed, 61 insertions(+), 30 deletions(-)
 2 files changed, 1 insertion(+), 31 deletions(-)
 4 files changed, 42 insertions(+), 45 deletions(-)
 2 files changed, 16 insertions(+), 5 deletions(-)
 1 file changed, 8 insertions(+), 4 deletions(-)
 7 files changed, 99 insertions(+), 12 deletions(-)
 2 files changed, 7 insertions(+), 7 deletions(-)
 1 file changed, 8 insertions(+)
 2 files changed, 2 insertions(+), 2 deletions(-)

Total:
99 files changed, 2729 insertions(+), 643 deletions(-)
```
