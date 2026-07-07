## Summary
Over a ten-week period (2026-01-13 to 2026-03-23), [Developer 1] stabilised and productionised the LKVLogistic CLI deployment under work item AB#3151. The work encompassed: replacing placeholder/sample class names, introducing Kubernetes-native credential injection via Kustomize overlays, adding a unit- and integration-test suite, hardening cronjob configuration, adding SFTP- and SMTP-based error-notification infrastructure, and producing developer documentation. Three PRs were opened across the period; PR #349 and PR #352 completed within the period (2026-03-05 and 2026-03-10 respectively), while PR #354 was created on 2026-03-23 but completed on 2026-04-07, outside the stated period. The commit log table lists 22 commits; one additional commit (`5f6cb6d`, Billbee API Client bump, 2026-03-23) appears only in the Commit Details section, bringing the source-stated total to 23.

## Decisions (each paired with its driver and at least one alternative considered)
- **Adopt Kustomize overlays for credential and environment management.** Driver: need to manage credentials and environment differences across staging and production. Alternative considered: the earlier flat deployment-template YAML files, which were deprecated and removed (commit `6db7a94`; Kustomize structure introduced in `54f0b02`).
- **Load credentials via Kubernetes Secrets and exclude the credentials file from version control.** Driver: credentials must not be stored in the repository. Alternative considered: the prior `secrets.yaml` / `credentials-secret.yaml` committed directly to the repository; superseded by moving the file to `.gitignore` and providing a `.example` template (commit `fb7269b`).
- **Remove the ACR pull secret from manifests and rely on cluster-level ACR handling.** Driver: the cluster already handles registry authentication. Alternative considered: maintaining an explicit `acr-secret.yaml` referenced in `kustomization.yaml` (removed in commit `83f7507`).
- **Switch `imagePullPolicy` to `IfNotPresent`.** Driver: not stated explicitly in the source. Alternative considered: the prior setting (changed in commit `70f7117`).
- **Make version-number replacement pipeline-specific rather than automated in manifests.** Driver: a version number bug existed in `azure-pipelines.yml` (fixed in commit `0560803`). Alternative considered: automated in-manifest version substitution (removed in commit `70f7117`).
- **Add `backoffLimit` and `activeDeadlineSeconds` to cronjobs.** Driver: not stated explicitly in the source. Alternative considered: the prior state with no explicit limits (changed in commit `20d9d37`).
- **Use Testcontainers (SFTPGo) and Moq for integration tests.** Driver: integration tests require an SFTP server; Testcontainers provides an ephemeral instance. Alternative considered: not recorded in the source; the prior state had no integration tests (PR #354).
- **Add SMTP error-notification support (opt-in via configuration) and suppress rather than crash on feedback errors.** Driver: `CsvAuftragsRueckmeldung.cs` and `CsvBestandsmeldung.cs` previously crashed on errors. Alternative considered: crashing on errors (prior behaviour, explicitly changed in PR #352).
- **Bump Billbee API Client to 2.4.3.** Driver: not stated explicitly in the source. Alternative considered: not recorded in the source (commit `5f6cb6d`, 2026-03-23).

## Consequences
- Credentials are no longer committed to the repository; operators must provision `credentials-secret.yaml` from the `.example` template before deploying.
- Kustomize overlays for both staging and production are now the canonical deployment path; the legacy flat deployment-template YAML files have been deleted.
- The cluster must have ACR integration configured at the cluster level; the manifest no longer carries a fallback pull secret.
- Cronjobs now carry explicit `backoffLimit` and `activeDeadlineSeconds` values.
- 19 integration tests (PR #354) and a unit-test suite now cover core CSV processing and mapping logic.
- SMTP error notification is optional; deployments without SMTP configuration will suppress (not crash on) feedback errors.
- The Billbee API Client was bumped to 2.4.3 (commit `5f6cb6d`).

## Open questions and risks
- AB#3151 remains in **Active** state; it is not recorded as closed in the source.
- PR #354 completed on 2026-04-07, outside the stated artifact period; its integration-test changes are not fully reflected in the period's commit log.
- The commit log table lists 22 commits against a source-stated total of 23; the discrepancy is not explained in the source.
- SMTP error notification is opt-in; there is no recorded mechanism to alert operators that SMTP is unconfigured, meaning error suppression could go unnoticed.
- The staging environment maps to the same `lkv` namespace as production (commit `45507d5`); potential namespace collision between staging and production workloads is not addressed in the source.
- No rollback procedure for the Kustomize-based deployment is documented in the source.

## Sources
- Development activity report: CS-04_Infrastructure_and_Deployment_compiled, work item AB#3151, 2026-01-13 to 2026-03-23 (source-stated 23 commits, PRs #349, #352, #354).