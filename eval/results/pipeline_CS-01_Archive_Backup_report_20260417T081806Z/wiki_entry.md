# Wiki Entry: CS-01 — BatchBackup Functionality After Uncontrolled Zenon Runtime Termination

---

**Source Artifact:** CS-01_Archive_Backup_report (support_report)
**Project:** Groninger – Schott Archive Backup
**Organization:** meshmakers.io
**Author:** [Author 1]
**Last Updated:** 2025-07-22

---

## Version History

| Date       | Version | Author     | Change Description                                      |
|------------|---------|------------|---------------------------------------------------------|
| 2025-07-15 | 0.1     | [Author 1] | Initial creation                                        |
| 2025-07-22 | 1.1     | [Author 1] | Added screenshots and manual model import documentation |

---

## 1. Introduction

The **BatchBackup** plant model extends the SCADA system with an automatic backup function that activates in the event of an **uncontrolled Zenon Runtime termination during an active batch production**.

**Key behaviors:**
- The backup procedure is triggered automatically after a crash and subsequent Zenon Runtime restart.
- The user is informed via a popup screen (`Pop_BatchBackup`) when the backup is executing.
- The batch process continues without loss of current batch information.
- During batch production, the current start and end archives are continuously copied to a backup location in the background (every 5 minutes).

---

## 2. System Setup

- **Test and parameterization environment:** Virtual machine `VM 13462_Scada`
- Specifications are to be taken from this virtual environment.

---

## 3. BatchBackup — Functional Description

### 3.1 Control Logic Overview

The backup procedure is initiated on **every Runtime start**. Control logic is governed by the evaluation of the following variables:

| Variable               | Description                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| `B1_Batch.Start`       | Remanent variable; indicates whether a batch was active before shutdown     |
| `nboBatchRuntimeStart` | Set by the `Autostart` script on every Runtime start                        |
| `nboBatchBackupStart`  | Mathematical variable; evaluates the above two and triggers the backup      |

**Trigger condition:**
- If both `nboBatchRuntimeStart` **and** `B1_Batch.Start` are `True` → the Runtime was previously terminated uncontrolled during batch production → backup process starts via script `SE_StartBatchBackup`.
- On a **normal** Runtime start, `B1_Batch.Start` is logically `False` → backup procedure is **not** activated.

**Reset behavior:**
- `nboBatchRuntimeStart` is reset after execution of scripts `SE_StartBatchBackup` and `AUTOSTART_Delay`.

**Continuous archive backup during production:**
- Archives **S1** and **E1** are copied every **5 minutes** to the Runtime folder `ExportArx`.
- Controlled by script `SE_BatchBackupExportArchives` and the time control `BatchBackupExportArchives`.

---

### 3.2 Script: `SE_StartBatchBackup`

Executed hierarchically in the following order upon invocation:

1. Archives **E1** and **S1** are stopped.
2. Popup information screen `Pop_BatchBackup` is displayed to the user.
3. Variable `nboBatchRuntimeStart` is reset.
4. Archives **E1** and **S1** are restarted.
5. *(SCADA project only)* All S1 and E1 start archives from sub-projects are started.

---

### 3.3 Script: `BatchBackupExportArchives`

Executed hierarchically in the following order upon invocation:

1. Files `E1.ARS` and `E1.ARX` are copied from the Runtime data folder to the Runtime export folder `ExportArx`.
2. Files `S1.ARS` and `S1.ARX` are copied from the Runtime data folder to the Runtime export folder `ExportArx`.

---

## 4. Installation & Import

### 4.1 Import via Wizard (Recommended)

- Import the plant model `BatchBackup` using the `ImportModelWizard`.
- All required Zenon components are imported automatically.
- `BatchBackup` is assigned to the `Basic` plant model.

> ⚠️ **Important:** The import must be performed on **all sub-projects first**, and only then on the **SCADA project last**, because the script `SaveRemanentDataAllProject` accesses functions in the sub-projects.

---

### 4.2 Manual Import of the Plant Model

First, store the plant model `BatchBackup` under `Basic`, then add the following components via XML import in the specified order:

| # | Component Type  | Name                                          | Scope              |
|---|-----------------|-----------------------------------------------|--------------------|
| 1 | Template        | `Fra_F_PopupBatchBackup`                      | All projects       |
| 2 | Screen          | `Scr_Pop_BatchBackup`                         | All projects       |
| 3 | Function        | `SS_Pop_BatchBackup`                          | All projects       |
| 4 | Variable        | `nboBatchRuntimeStart`                        | All projects       |
| 5 | Function        | `nboBatchRuntimeStart – 0`                    | All projects       |
| 6 | Function        | `nboBatchRuntimeStart – 1`                    | All projects       |
| 7 | Script          | `StartBatchBackup`                            | All projects       |
| 8 | Function        | `SE_StartBatchBackup`                         | All projects       |
| 9 | Variable        | `nboBatchBackupStart`                         | All projects       |
| 10 | Function       | `Fun_BatchBackup_SaveRemanentData`            | All projects       |
| 11 | Script         | `Sct_SaveRemanentDataAllProjects`             | SCADA project only |
| 12 | Function       | `Fun_SE_SaveRemanentDataAllProjects`          | SCADA project only |
| 13 | Function       | `Fun_BatchBackup_ExportE1Files`               | All projects       |
| 14 | Function       | `Fun_BatchBackup_ExportS1Files`               | All projects       |
| 15 | Script         | `Sct_BatchBackupExportArchives`               | All projects       |
| 16 | Function       | `Fun_SE_BatchBackupExportArchives`            | All projects       |
| 17 | Time Control   | `Tfu_BatchBackupExportArchives`               | All projects       |

---

## 5. Additional Configuration

The following manual adjustments are required after import:

### Variables

| Variable              | Property / Action                                                                                                          |
|-----------------------|----------------------------------------------------------------------------------------------------------------------------|
| `B1_Batch.Active`     | **Limit 1:** Add function `BatchBackup_SaveRemanentData` (`SE_SaveRemanentDataAllProjects` — SCADA project only)          |
| `B1_Batch.Active`     | **Limit 2:** Add function `BatchBackup_SaveRemanentData`                                                                  |
| `B1_Batch.Start`      | Set property **Remanent**                                                                                                  |
| `B1_Batch.Start_Extern` | Set property **Remanent**                                                                                               |

### File System

- Create folder **`ExportArx`** inside the Runtime folder.

### Scripts / Functions

| Component         | Action                                                                                                          |
|-------------------|-----------------------------------------------------------------------------------------------------------------|
| `Autostart` script | Add function `WSV_nboBatchRuntimeStart – 1`                                                                   |
| `Autostart_Delay` | Add function `WSV_nboBatchRuntimeStart – 0`                                                                    |
| `StartBatchBackup` script *(SCADA project only)* | Add function `B1_Start_Archive_S1` from all sub-projects; Add function `B1_Start_Archive_E1` from all sub-projects |

---

## 6. Known Behaviors / Notes

### Batch Name Highlighted in Red After Runtime Restart

- **Observation:** After Runtime restart, the batch name is displayed with a **red background**.
- **Status:** This behavior is **normal and expected**.
- **Explanation:** On Runtime start, the batch name is validated for uniqueness, and the name was already assigned at the start of the batch. No action is required.

---

## 7. Related Artifacts & Components

| Item                        | Reference                          |
|-----------------------------|------------------------------------|
| Test environment            | `VM 13462_Scada`                   |
| Backup export folder        | `ExportArx` (in Runtime directory) |
| Archive files backed up     | `E1.ARS`, `E1.ARX`, `S1.ARS`, `S1.ARX` |
| Backup interval             | Every 5 minutes during batch production |
| Import wizard               | `ImportModelWizard`                |

---

*Entry created from source artifact CS-01_Archive_Backup_report. No information has been added beyond what is contained in the source document.*