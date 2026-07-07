# KIP coverage audit - sampled passages (seed=42)

Target: ~30 independently re-extracted facts. Work through passages in order. For each passage, re-extract every atomic, verifiable, documentation-relevant fact (per docs/kip_extraction_guideline.md). For each fact, check the existing KIP registry for that artifact and mark it covered (Y + matched_kip_id) or missed (N). Stop once you reach the target count.

## [1] CS-01 - p.4

22.07.2025
2 Einführung
Mit Implementierung des Anlagenmodels „BatchBackup“ wird das SCADA System um die Funktionen
einer automatischen Backupfunktion im Falle einer unkontrollierten Zenon Runtime Beendigung
während einer aktiven Chargenproduktion erweitert.
Das Backup Prozedere wird nach Absturz und erneutem Zenon Runtimestart aktiviert, der Benutzer
wird durch ein Popup Bild über das Ausführen des Backups informiert.
Der Chargenprozess wird weiters aufgeführt, ohne dass die aktuellen Chargeninformationen verloren
gehen.
Während der Chargenproduktion werden im Hintergrund die aktuellen Start- und End-Archive
wegkopiert.
3 Systemaufbau
Die Parametrierung und Test wurden auf der „VM 13462_Scada“ durchgeführt.
Die Spezifikationen sind dieser virtuellen Umgebung zu entnehmen.
4 BatchBackup
4.1 Funktionsweise
Die Backupprozedur wird immer bei Runtimestart angestoßen. Die Steuerungslogik erfolgt über die
Auswertung von folgenden Variablen:
 B1_Batch.Start
 nboBatchRuntimeStart
 nboBatchBackupStart
Bei Start wird die Variable „nboBatchRuntimeStart“ über das Skript „Autostart“ gesetzt. Zusätzlich
wird der Status der vorhandenen remanenten Variable „B1_Batch.Start“ ausgelesen. Sind beide
Variablen auf „True“ gesetzt, so wurde zuvor die Runtime unkontrolliert während einer
Chargenproduktion beendet und der Backupprozess startet. Diese Logik ist in der mathematischen
Variable „nboBatchBackupStart“ hinterlegt und startet das Skript „SE_StartBatchBackup“.
Bei einem „normalen“ Runtimestart, ist die Remanentvariable „B1_Batch.Start“ logisch „False“, die
Backupprozedur wird daher nicht aktiviert.
Die Variable „nboBatchRuntimeStart“ wird nach der Ausführung der Skripte „SE_StartBatchBackup“
und „AUTOSTART_Delay“ zurückgesetzt.
Während einer Chargenproduktion werden die beiden Archive S1 und E1 im 5 Minuten Intervall in den
Runtimeordner „ExportArx“ wegkopiert. Somit können die Chargendaten auch bei einer
unkontrollierten Runtime Beendigung gesichert und wiederverwendet werden.
Diese Funktion wird durch das Skript „SE_BatchBackupExportArchives“ und der Zeitsteuerung
„BatchBackupExportArchives“ gesteuert.
MESHMAKERS.IO 3/8

---

## [2] CS-02 - p.4

20.02.2025
2 Projekt Information
Customer: Fresenius
Machine Numbers: 13560
MESHMAKERS.IO 3/4

---

## [3] CS-03 - p.3

20.03.2026
Datum Version Autor Grund der Änderungen
2026-03-20 1.0 [Author 1] Ersterstellung
MESHMAKERS.IO 2/12

---

## [4] CS-04 - Change Summary

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

---

## [5] CS-05 - Files Changed

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

---

## [6] CS-06 - Commit Details

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

---

## [7] CS-01 - p.7

22.07.2025
4.3 Händischer Import des Anlagenmodells
Zuerst das Anlagenmodell „BatchBackup“ unter „Basic“ hinterlegen, danach folgende Komponenten
als XML-Import hinzufügen:
1. Schablone -> „Fra_F_PopupBatchBackup“
2. Bild -> „Scr_Pop_BatchBackup“
3. Funktion -> „SS_Pop_BatchBackup“
4. Variable -> „nboBatchRuntimeStart“
5. Funktion -> „nboBatchRuntimeStart – 0“
6. Funktion -> „nboBatchRuntimeStart – 1“
7. Skript -> „StartBatchBackup“
8. Funktion -> „SE_StartBatchBackup“
9. Variable -> „nboBatchBackupStart“
10. Funktion -> „Fun_BatchBackup_SaveRemanentData“
11. Skript -> „Sct_SaveRemanentDataAllProjects“ (nur im SCADA Projekt)
12. Funkton -> „Fun_SE_SaveRemanentDataAllProjects“ (nur im SCADA Projekt)
13. Funktion -> „Fun_BatchBackup_ExportE1Files“
14. Funktion -> „Fun_BatchBackup_ExportS1Files“
15. Skript -> „Sct_BatchBackupExportArchives“
16. Funktion -> „Fun_SE_BatchBackupExportArchives“
17. Zeitsteuerung -> „Tfu_BatchBackupExportArchives“
4.4 Zusätzliche Anpassungen
 Variable: „B1_Batch.Active“
o Grenzwert_1: Funktion „BatchBackup_SaveRemanentData“ hinzufügen
(SE_SaveRemanentDataAllProjects – nur beim SCADA Projekt)
o Grenzwert_2: Funktion „BatchBackup_SaveRemanentData“ hinzufügen
 Variable: „B1_Batch.Start“
o Eigenschaft: „Remanent“ setzen
 Variable: „B1_Batch.Start_Extern”
o Eigenschaft: “Remanent” setzen
 „ExportArx“ Ordner im Runtimeordner erstellen
 Autostart Skript
o Funktion „WSV_nboBatchRuntimeStart – 1“ hinzufügen
 Autostart_Delay
o Funktion „WSV_nboBatchRuntimeStart – 0“ hinzufügen
 Skrip „StartBatchBackup“ – nur im Scada Projekt!
o Funktion „B1_Start_Archive_S1“ von allen Unterprojekten hinzufügen
o Funktion „B1_Start_Archive_E1“ von allen Unterprojekten hinzufügen
MESHMAKERS.IO 6/8

---

## [8] CS-02 - p.2

20.02.2025
1 Inhalt
2 Project Information ............................................................................................................................ 3
3 Automatischer Bildschirmdruck ......................................................................................................... 4
MESHMAKERS.IO 1/4

---

## [9] CS-03 - p.6

20.03.2026
1.2 Hinzufügen der Verriegelung
 LockMachineAutoMode
Variablen: 1_S7\db_anl_ges.eing, 1_S7\db_allgemein.fkt.tipptaster_linie
Logic: (X01.Wert = 1) OR (X02.Wert = 1)
1.3 Hinzufügen neuer Sprachdatei
<Maschinengeschwindigkeit> <Verriegelung>
1_HMI_13101 HMI7748 HMI7749
1_HMI_13102, 1_HMI_13103 HMI7756 HMI7757
1_HMI_13104 HMI7772 HMI7773
1_HMI_13242, 1_HMI_13244, HMI8517 HMI8518
1_HMI_13245, 1_HMI_13246
1_HMI_13549 HMI8651 HMI8652
1_HMI_13550 HMI8695 HMI8696
1_HMI_13551 HMI8936 HMI8937
1_HMI_13552 HMI8514 HMI8515
<Maschinengeschwindigkeit>
Deutsch: Max. Geschwindigkeit während Tiptaster aktiv
Englisch: Max. speed while touch switch is active
Italienisch: Velocità massima quando l'interruttore a sfioramento è attivo
<Verriegelung>
Deutsch: Funktion nicht möglich, solange die Maschine läuft oder Tiptaster an die Line
angeschlossen ist!
Englisch: Function not possible while the machine is running or a Tip switch is connected to the
line!
Italienisch: Funzione non disponibile mentre la macchina è in funzione o se un interruttore a
sfioramento è collegato alla linea!
MESHMAKERS.IO 5/12

---

## [10] CS-04 - Commit Log (chronological)

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

---

## [11] CS-05 - preamble

# Source Artifact CS-05: Error Handling and Monitoring
# Project: [Project Name]
# Work Items: AB#3603, AB#3626
# Period: 2026-03-06 to 2026-03-11
# Total Commits: 7

---

## [12] CS-06 - Files Changed

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

---

## [13] CS-01 - p.8

22.07.2025
4.5 Screenshots
Vor Runtime Shutdown:
Nach Runtime Shutdown:
MESHMAKERS.IO 7/8

---

## [14] CS-02 - p.3

20.02.2025
Date Version Author Reason for Changes
2025-02-19 1.0 [Author 1] Initial Creation
MESHMAKERS.IO 2/4

---

## [15] CS-03 - p.8

20.03.2026
1.5 Anpassen des Bildes: “Pop_Favorites”
Button „Basic_ButtonToggleFunctionTrigger~~1_S7\db_anl_0.op_auto” auswählen und Operation
Lock ändern:
Verriegelung: “LockMachineAutoMode”
Text: @<Verriegelung>
MESHMAKERS.IO 7/12

---

## [16] CS-04 - Files Changed

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

---

## [17] CS-05 - Commit Log (chronological)

| Date | Hash | Message |
|------|------|---------|
| 2026-03-06 | 87bd6ea | AB#3603: Change SyncOrderFeedback behavior to Log Erros instead of failing |
| 2026-03-09 | 59f5cde | AB#3603: Fix Ignore bad data on fix missing field found |
| 2026-03-09 | 532426c | AB#3603: Fix Ignore ReadingExceptionErrors |
| 2026-03-10 | b3416f6 | AB#3626: Add Email Notification if error is detected |
| 2026-03-10 | 7f2d7e6 | AB#3626: Add Missing Email Notification Files |
| 2026-03-10 | d98d346 | AB#3626: Fix To use STARTTLS |

---

## [18] CS-06 - Work Item Context

### Work Item AB#3651
- **Title:** Integration Testing
- **Type:** Task
- **State:** Active
- **Assigned To:** [Developer 1]

**Description:**
None

---

---

## [19] CS-01 - p.5

22.07.2025
4.1.1 Skript: „SE_StartBatchBackup“
Bei Ausführung werden folgende Funktionen hierarchisch ausgeführt:
 Archive E1 und S1 werden beendet
 Das Popup Informationsbild „Pop_BatchBackup“ wird dem Benutzer angezeigt
 Variable „nboBatchRuntimeStart“ wird zurückgesetzt
 Archive E1 und S1 werden gestartet
 (Im Scada Projekt die Erweiterung, dass alle S1 und E1 Start Archive von Unterprojekten
gestartet werden)
4.1.2 Skript: „BatchBackupExportArchives“
Bei Ausführung werden folgende Funktionen hierarchisch ausgeführt:
 Die Dateien E1.ARS und E1.ARX werden aus dem Runtime-Datenordner in den Runtime-
Exportordner „ExportArx“ kopiert
 Die Dateien S1.ARS und S1.ARX werden aus dem Runtime-Datenordner in den Runtime-
Exportordner „ExportArx“ kopiert
MESHMAKERS.IO 4/8

---

## [20] CS-02 - p.1

MESHMAKERS.IO
Groninger – Fresenius 1381922
Automatischer Bildschirmdruck
19.02.2025
meshmakers.io
[Author 1]

---

## [21] CS-03 - p.9

20.03.2026
1.6 Anpassen des Bildes für Maschinengeschwindigkeit
Projekt Bildname
1_HMI_13101, 1_HMI_13103, 1_HMI_13242, APPL_Machinemaster_Data
1_HMI_13245, 1_HMI_13549, 1_HMI_13551
1_HMI_13102, 1_HMI_13244, 1_HMI_13550 APPL_MachinemasterDataGeneral
1_HMI_13104, 1_HMI_13246, 1_HMI_13552 Appl_Machinemaster0
Static text: @<Maschinengeschwindigkeit>
Display authorization level: 33
Variable: 1_S7\db_allgemein.r32._10
Sollwertgrenzen: von Variable übernehmen
Berechtigungsebene: „Machine parmetrization“
Neues Import Feld für die Tippgeschwindigkeit hinzufügen:
MESHMAKERS.IO 8/12

---

## [22] CS-04 - Work Item Context

### Work Item AB#3151
- **Title:** LKV: familiarize yourself with the topic and the current solution
- **Type:** Issue
- **State:** Active
- **Assigned To:** [Developer 1]

**Description:**
We want to check the current implementation and get familiar with the topic. 
 Acceptance critera: - Overview of solution - Stability of implementation is enhanced - TODO's are fixed. Classes named e.g . "Sample" are fixed - Developer docs are existing

---

---

## [23] CS-05 - Commit Details

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

---

## [24] CS-06 - Pull Requests

No pull requests found matching the specified work items.

---

---

## [25] CS-01 - p.9

22.07.2025
Im Screenshot ist ersichtlich das der Chargenname Rot hinterlegt ist. Dieses Verhalten ist normal und
zulässig, da der Chargenname bei Runtimestart auf seinen eindeutigen Wert überprüft wird und dieser
bereits zu Chargen Start vergeben wurde.
MESHMAKERS.IO 8/8

---

## [26] CS-02 - p.5

20.02.2025
3 Automatischer Bildschirmdruck
 Ein USB-Stick mit dem Laufwerksbuchstaben „G:“ muss am HMI der Maschine angeschlossen
werden
1. Anmelden mit User gronservice2 und Passwort (wird bekannt gegeben).
2. Zum Pfad „Service -> Bedientabeau -> Inbetriebnahme“ navigieren.
3. Button „Fernwartung“ klicken
4. Button „Display access level“ aktivieren
5. Button “Automatischer Bildschirmdruck” aktivieren
In der Statusleiste ist ersichtbar, dass der „Automatische Bildschirmdruck“ aktiv ist:
MESHMAKERS.IO 4/4

---

## [27] CS-03 - p.7

20.03.2026
1.4 Anpassen des Bildes: “Start”
Button “Basic_ButtonToggleFunctionTrigger~~1_S7\db_anl_0.op_auto” auswählen und Operation
Lock ändern:
Verriegelung: “LockMachineAutoMode”
Text: @<Verriegelung>
MESHMAKERS.IO 6/12

---

## [28] CS-04 - preamble

# Source Artifact CS-04: Infrastructure and Deployment
# Project: [Project Name]
# Work Items: AB#3151
# Period: 2026-01-13 to 2026-03-23
# Total Commits: 23

---

## [29] CS-05 - Work Item Context

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

---

## [30] CS-06 - Change Summary

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

---

## [31] CS-01 - p.3

22.07.2025
Datum Version Autor Grund der Änderungen
2025-07-15 0.1 [Author 1] Ersterstellung
2025-07-22 1.1 [Author 1] Ergänzungen Screenshots und
händische Modelimportierung
MESHMAKERS.IO 2/8

---

## [32] CS-03 - p.11

20.03.2026
MESHMAKERS.IO 10/12

---

## [33] CS-04 - Pull Requests

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

---

## [34] CS-05 - Change Summary

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

---

## [35] CS-06 - Commit Log (chronological)

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

---

## [36] CS-01 - p.6

22.07.2025
4.2 Import des Anlagenmodells mit Wizard
Das Anlagenmodel „BatchBackup“ mit dem Wizard „ImportModelWizard“ importieren. Alle Benötigten
Zenon Komponenten werden importiert und „BatckBackup“ wird dem Anlagenmodell Basic
zugeordnet.
Es ist notwendig, den Import zuerst bei allen Unterprojekten durchzuführen und erst zum Schluss im
SCADA Projekt, da das Skript „SaveRemanentDataAllProject“ auf Funktionen im Unterprojekt zugreift.
MESHMAKERS.IO 5/8

---

## [37] CS-03 - p.5

20.03.2026
3. Umsetzung
Für die Umsetzung werden 2 neue Variablen (Tipptaster + Maschinengeschwindigkeit) hinzugefügt.
Wenn der Tipptaster aktiv ist, darf die Maschine nicht in den Automatik Modus geschalten werden.
Dazu müssen die dazugehörigen Buttons in Zenon gesperrt werden.
Wenn die Maschine im Tipptasterbetrieb ist, kann der Kunde eine Maschinengeschwindigkeit
vorauswählen.
Die Umsetzung ist für jedes Projekt identisch.
1.1 Hinzufügen der Variablen
 1_S7\db_allgemein.fkt.tipptaster_linie
 1_S7\db_allgemein.r32._10
1_S7\db_allgemein.fkt.tipptaster_linie
Kennung: 1= Tipptaster an Linie gesteckt Automatik deaktiviert
Netzadresse: 1
Datenbaustein: 1804
Offset: 2
Bitnummer: 3
Treiber: S7TCP32 – 1_S7 TCP-IP
Datentyp: Bool
Treiberobjekttyp: Erweiterter Datenbaustein
1_S7\db_allgemein.r32._10
Kennung: Geschwindigkeit Tipptaster gesteckt
Maßeinheit: pcs/min
Netzadresse: 1
Datenbaustein: 1804
Offset: 160
Bitnummer: 0
Treiber: S7TCP32 – 1_S7 TCP-IP
Datentyp: REAL
Treiberobjekttyp: Erweiterter Datenbaustein
Sollwert setzen: Min: 10; Max: 200
MESHMAKERS.IO 4/12

---

## [38] CS-04 - Commit Details

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

---

## [39] CS-05 - Pull Requests

### PR #353: AB#3626: Add Try Catch Block to catch all errors and send them via SMTP
- **Author:** [Developer 1]
- **Created:** 2026-03-11
- **Completed:** 2026-03-11
- **Merge strategy:** rebase

**Description:**
AB#3626: Add Try Catch Block to catch all errors and send them via SMTP


---

---

## [40] CS-06 - preamble

# Source Artifact CS-06: Testing Strategy
# Project: [Project Name]
# Work Items: AB#3651
# Period: 2026-03-17 to 2026-03-23
# Total Commits: 9

---

## [41] CS-01 - p.1

MESHMAKERS.IO
Groninger – Schott Archive
Backup
Chargen-Backupfunktionalität nach unkontrollierter Zenon
Runtime Beendigung
22.07.2025
meshmakers.io
[Author 1]

---

## [42] CS-03 - p.12

20.03.2026
MESHMAKERS.IO 11/12

---

## [43] CS-01 - p.2

22.07.2025
1 Inhalt
2 Einführung .......................................................................................................................................... 3
3 Systemaufbau ..................................................................................................................................... 3
4 BatchBackup ....................................................................................................................................... 3
4.1 Funktionsweise ......................................................................................................................... 3
4.1.1 Skript: „SE_StartBatchBackup“ ............................................................................................. 4
4.1.2 Skript: „BatchBackupExportArchives“ .................................................................................. 4
4.2 Import des Anlagenmodells mit Wizard ................................................................................... 5
4.3 Händischer Import des Anlagenmodells ................................................................................... 6
4.4 Zusätzliche Anpassungen .......................................................................................................... 6
4.5 Screenshots ............................................................................................................................... 7
MESHMAKERS.IO 1/8

---

## [44] CS-03 - p.10

20.03.2026
MESHMAKERS.IO 9/12

---

## [45] CS-03 - p.4

20.03.2026
2. Projektinformationen
Kunde: Ompi
Kundenvorgangsnr: 1378291
Maschinennummer: L6: 13101, 13102, 13103, 13104
L7: 13242, 13244, 13245, 13246
L 8: 13549, 13550, 13551, 13552
Bezeichnung:
ZenonVersion: 8.0
Client Projekt L6: 1_HMI_13101, 1_HMI_13102,
1_HMI_13103, 1_HMI_13104
L7: 1_HMI_13242, 1_HMI_13244,
1_HMI_13245, 1_HMI_13246
L8: 1_HMI_13549, 1_HMI_13550,
1_HMI_13551, 1_HMI_13552
SCADA Ja - SCADAPC13106
MESHMAKERS.IO 3/12

---

## [46] CS-03 - p.2

20.03.2026
1. Inhalt
1. Inhalt................................................................................................................................................... 1
2. Projektinformationen ......................................................................................................................... 3
3. Umsetzung .......................................................................................................................................... 4
1.1 Hinzufügen der Variablen ......................................................................................................... 4
1.2 Hinzufügen der Verriegelung .................................................................................................... 5
1.3 Hinzufügen neuer Sprachdatei ................................................................................................. 5
1.4 Anpassen des Bildes: “Start” ..................................................................................................... 6
1.5 Anpassen des Bildes: “Pop_Favorites” ..................................................................................... 7
1.6 Anpassen des Bildes für Maschinengeschwindigkeit ................................................................ 8
MESHMAKERS.IO 1/12

---

## [47] CS-03 - p.13

20.03.2026
MESHMAKERS.IO 12/12

---

## [48] CS-03 - p.1

MESHMAKERS.IO
Groninger – 1378291_Ompi
Implementierung eine Tippschalters in Linie V6, L7 und L8
20.03.2026
meshmakers.io
[Author 1]

---

