# Source Artifact CS-05: Error Handling and Monitoring
# Project: [Project Name]
# Work Items: AB#3603, AB#3626
# Period: 2026-03-06 to 2026-03-11
# Total Commits: 7

## Work Item Context

### Work Item AB#3603
- **Title:** Fix SyncOrderFeedback
- **Type:** Task
- **State:** Active
- **Assigned To:** [Developer 1]

**Description:**
None

### Work Item AB#3626
- **Title:** Add Email Feedback
- **Type:** Task
- **State:** Active
- **Assigned To:** [Developer 1]

**Description:**
None

---

## Pull Requests

### PR #353: AB#3626: Add Try Catch Block to catch all errors and send them via SMTP
- **Author:** [Developer 1]
- **Created:** 2026-03-11
- **Completed:** 2026-03-11
- **Merge strategy:** rebase

**Description:**
AB#3626: Add Try Catch Block to catch all errors and send them via SMTP


---

## Commit Log (chronological)

| Date | Hash | Message |
|------|------|---------|
| 2026-03-06 | 87bd6ea | AB#3603: Change SyncOrderFeedback behavior to Log Erros instead of failing |
| 2026-03-09 | 59f5cde | AB#3603: Fix Ignore bad data on fix missing field found |
| 2026-03-09 | 532426c | AB#3603: Fix Ignore ReadingExceptionErrors |
| 2026-03-10 | b3416f6 | AB#3626: Add Email Notification if error is detected |
| 2026-03-10 | 7f2d7e6 | AB#3626: Add Missing Email Notification Files |
| 2026-03-10 | d98d346 | AB#3626: Fix To use STARTTLS |


## Commit Details

### 87bd6ea — AB#3603: Change SyncOrderFeedback behavior to Log Erros instead of failing
- **Date:** 2026-03-06
- **Author:** [Developer 1]


### 59f5cde — AB#3603: Fix Ignore bad data on fix missing field found
- **Date:** 2026-03-09
- **Author:** [Developer 1]


### 532426c — AB#3603: Fix Ignore ReadingExceptionErrors
- **Date:** 2026-03-09
- **Author:** [Developer 1]


### b3416f6 — AB#3626: Add Email Notification if error is detected
- **Date:** 2026-03-10
- **Author:** [Developer 1]


### 7f2d7e6 — AB#3626: Add Missing Email Notification Files
- **Date:** 2026-03-10
- **Author:** [Developer 1]


### d98d346 — AB#3626: Fix To use STARTTLS
- **Date:** 2026-03-10
- **Author:** [Developer 1]


### e8bc570 — AB#3626: Add Try Catch Block to catch all errors and send them via SMTP
- **Date:** 2026-03-11
- **Author:** [Developer 1]


---

## Files Changed

**87bd6ea — AB#3603: Change SyncOrderFeedback behavior to Log Erros instead of failing**
 .../Commands/SyncOrderFeedbackCommand.cs           | 63 ++++++++++++----------
 src/LKVLogistic.Cli/Commands/SyncStocksCommand.cs  | 28 ++++++----
 src/LkvLogistic/CSVBestandsmeldung.cs              |  8 ++-
 src/LkvLogistic/CsvAuftragsRueckmeldung.cs         |  8 ++-
 4 files changed, 68 insertions(+), 39 deletions(-)

**59f5cde — AB#3603: Fix Ignore bad data on fix missing field found**
 src/LkvLogistic/CSVBestandsmeldung.cs      | 4 ++++
 src/LkvLogistic/CsvAuftragsRueckmeldung.cs | 4 ++++
 2 files changed, 8 insertions(+)

**532426c — AB#3603: Fix Ignore ReadingExceptionErrors**
 src/LkvLogistic/CSVBestandsmeldung.cs      | 5 +++++
 src/LkvLogistic/CsvAuftragsRueckmeldung.cs | 5 +++++
 2 files changed, 10 insertions(+)

**b3416f6 — AB#3626: Add Email Notification if error is detected**
 .../lkv/production/credentials-secret.yaml.example         | 11 +++++++++++
 .../overlays/lkv/staging/credentials-secret.yaml.example   | 11 +++++++++++
 src/LKVLogistic.Cli/Commands/SyncOrderFeedbackCommand.cs   | 14 +++++++++++++-
 src/LKVLogistic.Cli/Commands/SyncOrdersCommand.cs          | 10 +++++++++-
 src/LKVLogistic.Cli/Commands/SyncProductsCommand.cs        | 10 +++++++++-
 src/LKVLogistic.Cli/Commands/SyncStocksCommand.cs          | 12 +++++++++++-
 src/LKVLogistic.Cli/LKVLogistic.Cli.csproj                 |  1 +
 src/LKVLogistic.Cli/Program.cs                             |  5 +++++
 src/LKVLogistic.Cli/appsettings.json                       | 11 +++++++++++
 9 files changed, 81 insertions(+), 4 deletions(-)

**7f2d7e6 — AB#3626: Add Missing Email Notification Files**
 .../Configurations/SmtpConfiguration.cs            |  14 +++
 .../EmailNotificationService.cs                    | 112 +++++++++++++++++++++
 .../IEmailNotificationService.cs                   |   6 ++
 3 files changed, 132 insertions(+)

**d98d346 — AB#3626: Fix To use STARTTLS**
 .../EmailNotificationService/EmailNotificationService.cs            | 6 +++++-
 1 file changed, 5 insertions(+), 1 deletion(-)

**e8bc570 — AB#3626: Add Try Catch Block to catch all errors and send them via SMTP**
 .../Commands/SyncOrderFeedbackCommand.cs           | 116 +++++++++++----------
 src/LKVLogistic.Cli/Commands/SyncOrdersCommand.cs  |   5 +
 .../Commands/SyncProductsCommand.cs                |   5 +
 src/LKVLogistic.Cli/Commands/SyncStocksCommand.cs  |  76 ++++++++------
 4 files changed, 116 insertions(+), 86 deletions(-)


---

## Change Summary

```
 4 files changed, 68 insertions(+), 39 deletions(-)
 2 files changed, 8 insertions(+)
 2 files changed, 10 insertions(+)
 9 files changed, 81 insertions(+), 4 deletions(-)
 3 files changed, 132 insertions(+)
 1 file changed, 5 insertions(+), 1 deletion(-)
 4 files changed, 116 insertions(+), 86 deletions(-)

Total:
25 files changed, 420 insertions(+), 130 deletions(-)
```
