## Summary
[Developer 1] stabilised and hardened the LKVLogistic CLI infrastructure and deployment pipeline under work item AB#3151 over a ten-week period (2026-01-13 to 2026-03-23). The work encompassed four main themes: (1) replacing placeholder/sample class names and files with production-quality equivalents; (2) migrating credential and deployment management to Kustomize overlays for both staging and production environments on Kubernetes; (3) adding unit and integration test coverage; and (4) improving operational robustness through error-skipping, email error notifications, and cronjob hardening. Three PRs were merged (#349, #352, #354).

## Decisions (each paired with its driver and at least one alternative considered)
- **Adopt Kustomize for credential and deployment management.** Driver: need for a structured, overlay-based approach to manage staging vs. production configuration differences on Kubernetes. Alternative considered: the previous flat deployment-template YAML files (deprecated and removed in commit `6db7a94`); rejected because they did not cleanly separate environment-specific configuration.
- **Load credentials via Kubernetes Secrets (not embedded in deployment manifests).** Driver: security — credentials must not be stored in version-controlled deployment files. Alternative considered: inline credentials in deployment YAML (present in early commits); superseded by the Kubernetes Secrets approach introduced in commit `1b64323` and hardened in `fb7269b` (credentials-secret.yaml moved to `.gitignore`, replaced by a `.example` template).
- **Remove the ACR pull secret from manifests; delegate to the cluster.** Driver: simplification — the cluster already handles ACR authentication, making a per-manifest `acr-secret.yaml` redundant. Alternative considered: retaining `acr-secret.yaml` in the Kustomize base (present until commit `83f7507`); removed because it added unnecessary operational surface.
- **Switch `imagePullPolicy` to `IfNotPresent`.** Driver: avoid unnecessary image pulls in environments where the correct image is already present, reducing startup latency and registry load. Alternative considered: `Always` (prior default); replaced in commit `70f7117`.
- **Make version-number replacement pipeline-specific rather than automated in manifests.** Driver: the automated replacement introduced a version-number bug in `azure-pipelines.yml` (fixed in `0560803`); moving ownership to the pipeline makes the behaviour explicit and environment-controlled. Alternative considered: automated in-manifest replacement; removed in commit `70f7117`.
- **Add `backoffLimit` and `activeDeadlineSeconds` to cronjobs.** Driver: prevent runaway or indefinitely retrying cronjob pods from consuming cluster resources. Alternative considered: no retry/deadline limits (prior state); replaced in commit `20d9d37`.
- **Skip (do not crash on) errors in `CsvAuftragsRueckmeldung.cs` and `CsvBestandsmeldung.cs`; send email notifications instead.** Driver: improve operational resilience — a single malformed record should not abort the entire job. Alternative considered: fail-fast on any error (prior behaviour); replaced in PR #352.
- **Use Testcontainers (SFTPGo) and Moq for integration testing.** Driver: enable realistic SFTP integration tests in CI without a persistent external SFTP dependency. Alternative considered: no integration tests / manual testing only (prior state); replaced in PR #354 with 19 automated integration tests.
- **Use the cluster's built-in StorageClass rather than a custom one.** Driver: reduce operational overhead of managing a custom StorageClass. Alternative considered: custom `storageclass.yaml` (introduced in `b8bb38a`, immediately removed in `ae4873b`); rejected because the built-in class was sufficient.

## Consequences
- Kustomize overlay structure (`deployment/base/`, `deployment/overlays/lkv/staging/`, `deployment/overlays/lkv/production/`) is now the authoritative deployment model; all legacy flat deployment-template files have been deleted.
- Credentials are never committed to the repository; operators must supply `credentials-secret.yaml` from the `.example` template before deploying.
- Staging and production environments share the same `lkv` namespace on the cluster, mapped via the staging Kustomize overlay.
- Cronjobs now have bounded retry behaviour (`backoffLimit`, `activeDeadlineSeconds`), reducing the risk of resource exhaustion from failed jobs.
- Error-skipping in feedback/stock CSV processing means partial failures are now silent at the job level unless email notification is configured; operators must ensure SMTP is configured to receive alerts.
- The integration test suite (19 tests, `LKVLogistic.Cli.IntegrationTests`) requires Docker to be available in the CI environment for Testcontainers to spin up SFTPGo.
- Billbee API Client was bumped to 2.4.3 (commit `5f6cb6d`); downstream compatibility with this version should be verified.

## Open questions and risks
- SMTP email notification for errors is conditional on configuration being present; it is not recorded whether a monitoring fallback exists if SMTP is not configured in a given environment.
- The staging and production environments share the `lkv` namespace; namespace isolation between environments is not enforced at the cluster level, which may present a risk if resource names collide.
- No alternative reviewer is attributed in the PR records; all three PRs were authored and apparently self-merged by [Developer 1]. It is not recorded whether a second reviewer approved the changes.
- Work item AB#3151 remains in **Active** state as of the artifact date; it is not confirmed that all acceptance criteria (overview, stability, TODO fixes, developer docs) have been signed off.

## Sources
- Development activity artifact: CS-04_Infrastructure_and_Deployment_compiled, work item AB#3151, 2026-01-13 to 2026-03-23 (23 commits, PRs #349, #352, #354).