# Source Artifact CS-06: Testing Strategy
# Project: [Project Name]
# Work Items: AB#3651
# Period: 2026-03-17 to 2026-03-23
# Total Commits: 9

## Work Item Context

### Work Item AB#3651
- **Title:** Integration Testing
- **Type:** Task
- **State:** Active
- **Assigned To:** [Developer 1]

**Description:**
None

---

## Pull Requests

No pull requests found matching the specified work items.

---

## Commit Log (chronological)

| Date | Hash | Message |
|------|------|---------|
| 2026-03-17 | 2e9f1a8 | AB#3651: Semi Auto Integration testing |
| 2026-03-17 | d9f59c2 | AB#3651: Bugfix Integration Testing |
| 2026-03-17 | 3caa466 | AB#3651: Continue Bugfix Integration Testing |
| 2026-03-17 | de655a3 | AB#3651: Bugfix Integration Testing |
| 2026-03-17 | 21350c8 | AB#3651: Update Integration testing logging |
| 2026-03-18 | 27bbf4f | AB#3651: Remove E2E Testing. Update Readme with manual E2E steps. |
| 2026-03-18 | 5088faa | AB#3651: Add Integration Tests |
| 2026-03-23 | ce26c70 | AB#3651: Fix Warnings in Integration tests |


## Commit Details

### 2e9f1a8 — AB#3651: Semi Auto Integration testing
- **Date:** 2026-03-17
- **Author:** [Developer 1]


### d9f59c2 — AB#3651: Bugfix Integration Testing
- **Date:** 2026-03-17
- **Author:** [Developer 1]


### 3caa466 — AB#3651: Continue Bugfix Integration Testing
- **Date:** 2026-03-17
- **Author:** [Developer 1]


### de655a3 — AB#3651: Bugfix Integration Testing
- **Date:** 2026-03-17
- **Author:** [Developer 1]


### 21350c8 — AB#3651: Update Integration testing logging
- **Date:** 2026-03-17
- **Author:** [Developer 1]


### 27bbf4f — AB#3651: Remove E2E Testing. Update Readme with manual E2E steps.
- **Date:** 2026-03-18
- **Author:** [Developer 1]


### 5088faa — AB#3651: Add Integration Tests
- **Date:** 2026-03-18
- **Author:** [Developer 1]


### ce26c70 — AB#3651: Fix Warnings in Integration tests
- **Date:** 2026-03-23
- **Author:** [Developer 1]


### 79a4931 — AB#3651: Further integration test cleanup
- **Date:** 2026-03-23
- **Author:** [Developer 1]


---

## Files Changed

**2e9f1a8 — AB#3651: Semi Auto Integration testing**
 deployment/smoke-test.sh              | 320 ++++++++++++++++++++++++++++++++++
 deployment/test-data/BE_SMOKETEST.txt |   1 +
 2 files changed, 321 insertions(+)

**d9f59c2 — AB#3651: Bugfix Integration Testing**
 deployment/smoke-test.sh | 83 ++++++++++++++++++++++++++----------------------
 1 file changed, 45 insertions(+), 38 deletions(-)

**3caa466 — AB#3651: Continue Bugfix Integration Testing**
 deployment/smoke-test.sh | 14 ++++++++++----
 1 file changed, 10 insertions(+), 4 deletions(-)

**de655a3 — AB#3651: Bugfix Integration Testing**
 deployment/smoke-test.sh | 377 +++++++++++++++--------------------------------
 1 file changed, 120 insertions(+), 257 deletions(-)

**21350c8 — AB#3651: Update Integration testing logging**
 deployment/smoke-test.sh | 4 ++--
 1 file changed, 2 insertions(+), 2 deletions(-)

**27bbf4f — AB#3651: Remove E2E Testing. Update Readme with manual E2E steps.**
 README.md                             |  59 ++++++++--
 deployment/smoke-test.sh              | 196 ----------------------------------
 deployment/test-data/BE_SMOKETEST.txt |   1 -
 3 files changed, 49 insertions(+), 207 deletions(-)

**5088faa — AB#3651: Add Integration Tests**
 LkvLogistik.sln                                    |  15 ++
 README.md                                          |  34 ++-
 .../Fixtures/BillbeeMockFixture.cs                 |  65 ++++++
 .../Fixtures/SftpGoFixture.cs                      | 107 ++++++++++
 .../LKVLogistic.Cli.IntegrationTests.csproj        |  23 +++
 .../SftpClientTests.cs                             | 190 +++++++++++++++++
 .../SyncOrderFeedbackIntegrationTests.cs           | 202 ++++++++++++++++++
 .../SyncOrdersIntegrationTests.cs                  | 227 +++++++++++++++++++++
 .../SyncProductsIntegrationTests.cs                | 170 +++++++++++++++
 .../SyncStocksIntegrationTests.cs                  | 174 ++++++++++++++++
 .../TestData/CsvTestData.cs                        |  41 ++++
 11 files changed, 1239 insertions(+), 9 deletions(-)

**ce26c70 — AB#3651: Fix Warnings in Integration tests**
 .../Fixtures/BillbeeMockFixture.cs                        |  4 ++--
 .../Fixtures/SftpGoFixture.cs                             |  5 ++---
 tests/LKVLogistic.Cli.IntegrationTests/SftpClientTests.cs | 15 ++++++---------
 3 files changed, 10 insertions(+), 14 deletions(-)

**79a4931 — AB#3651: Further integration test cleanup**
 .../SftpClientTests.cs                             | 21 ++++++----------
 .../SyncOrderFeedbackIntegrationTests.cs           | 28 ++++++----------------
 .../SyncOrdersIntegrationTests.cs                  | 25 +++++--------------
 .../SyncStocksIntegrationTests.cs                  | 27 +++++----------------
 4 files changed, 26 insertions(+), 75 deletions(-)


---

## Change Summary

```
 2 files changed, 321 insertions(+)
 1 file changed, 45 insertions(+), 38 deletions(-)
 1 file changed, 10 insertions(+), 4 deletions(-)
 1 file changed, 120 insertions(+), 257 deletions(-)
 1 file changed, 2 insertions(+), 2 deletions(-)
 3 files changed, 49 insertions(+), 207 deletions(-)
 11 files changed, 1239 insertions(+), 9 deletions(-)
 3 files changed, 10 insertions(+), 14 deletions(-)
 4 files changed, 26 insertions(+), 75 deletions(-)

Total:
27 files changed, 1822 insertions(+), 606 deletions(-)
```
