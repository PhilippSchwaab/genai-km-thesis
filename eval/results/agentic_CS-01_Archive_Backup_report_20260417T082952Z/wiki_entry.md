# CS-01 — BatchBackup: Archive Backup After Uncontrolled Zenon Runtime Termination

**Source Artifact:** CS-01_Archive_Backup_report (support_report)
**Project:** Groninger – Schott Archive Backup
**Date:** 22.07.2025
**Author:** [Author 1]

---

## Version History

| Date       | Version | Author     | Notes                                                        |
|------------|---------|------------|--------------------------------------------------------------|
| 2025-07-15 | 0.1     | [Author 1] | Initial creation                                             |
| 2025-07-22 | 1.1     | [Author 1] | Added screenshots and manual model import                    |

---

## 1. Introduction

The `BatchBackup` plant model extends the SCADA system with an automatic backup function triggered in the event of an uncontrolled Zenon Runtime termination during active batch production.

- The backup procedure is activated after a crash and subsequent Zenon Runtime restart.
- The user is informed via a popup screen about the execution of the backup.
- The batch process continues without loss of current batch information.
- During batch production, the current Start and End archives are continuously copied to a backup location in the background.

---

## 2. System Setup

Parameterization and testing were performed on virtual machine **VM 13462_Scada**. Specifications are to be taken from that virtual environment.

---

## 3. BatchBackup

### 3.1 How It Works

The backup procedure is initiated on every Runtime start. Control logic is based on the evaluation of the following variables:

| Variable               | Role                                                                                          |
|------------------------|-----------------------------------------------------------------------------------------------|
| `B1_Batch.Start`       | Remanent variable; its `True`/`False` state is read at Runtime start                         |
| `nboBatchRuntimeStart` | Set by the `Autostart` script on every Runtime start                                          |
| `nboBatchBackupStart`  | Mathematical variable; contains the trigger logic and starts script `SE_StartBatchBackup`    |

**Trigger condition:** If both `nboBatchRuntimeStart` **and** `B1_Batch.Start` are `True`, the Runtime was previously terminated uncontrollably during batch production, and the backup process starts.

**Normal start:** If `B1_Batch.Start` is logically `False`, the backup procedure is not activated.

**Reset:** `nboBatchRuntimeStart` is reset after execution of scripts `SE_StartBatchBackup` and `AUTOSTART_Delay`.

**Continuous archive copy:** During batch production, archives S1 and E1 are copied every **5 minutes** into the Runtime folder `ExportArx`, so that batch data can be secured and **reused** even after an uncontrolled Runtime termination. This is controlled by script `SE_BatchBackupExportArchives` and the time control `BatchBackupExportArchives`.

---

### 3.2 Script: `SE_StartBatchBackup`

Executed hierarchically in the following order:

1. Archives E1 and S1 are stopped.
2. Popup information screen `Pop_BatchBackup` is displayed to the user.
3. Variable `nboBatchRuntimeStart` is reset.
4. Archives E1 and S1 are restarted.
5. *(SCADA project only)* All S1 and E1 Start Archives from sub-projects are started.

---

### 3.3 Script: `BatchBackupExportArchives`

Executed hierarchically in the following order:

1. Files `E1.ARS` and `E1.ARX` are copied from the Runtime data folder to the Runtime export folder `ExportArx`.
2. Files `S1.ARS` and `S1.ARX` are copied from the Runtime data folder to the Runtime export folder `ExportArx`.

---

### 3.4 Importing the Plant Model — Wizard Method

Import the `BatchBackup` plant model using the `ImportModelWizard`. All required Zenon components are imported and `BatchBackup` is assigned to the `Basic` plant model.

> ⚠️ **Import order:** The import must be performed on all sub-projects first, and only then on the SCADA project last, because the script `SaveRemanentDataAllProject` accesses functions in the sub-projects.

---

### 3.5 Importing the Plant Model — Manual Method

First, store the `BatchBackup` plant model under `Basic`, then add the following components via XML import in order:

| #  | Type         | Name                                         | Scope       |
|----|--------------|----------------------------------------------|-------------|
| 1  | Template     | `Fra_F_PopupBatchBackup`                     | All         |
| 2  | Screen       | `Scr_Pop_BatchBackup`                        | All         |
| 3  | Function     | `SS_Pop_BatchBackup`                         | All         |
| 4  | Variable     | `nboBatchRuntimeStart`                       | All         |
| 5  | Function     | `nboBatchRuntimeStart – 0`                   | All         |
| 6  | Function     | `nboBatchRuntimeStart – 1`                   | All         |
| 7  | Script       | `StartBatchBackup`                           | All         |
| 8  | Function     | `SE_StartBatchBackup`                        | All         |
| 9  | Variable     | `nboBatchBackupStart`                        | All         |
| 10 | Function     | `Fun_BatchBackup_SaveRemanentData`           | All         |
| 11 | Script       | `Sct_SaveRemanentDataAllProjects`            | SCADA only  |
| 12 | Function     | `Fun_SE_SaveRemanentDataAllProjects`         | SCADA only  |
| 13 | Function     | `Fun_BatchBackup_ExportE1Files`              | All         |
| 14 | Function     | `Fun_BatchBackup_ExportS1Files`              | All         |
| 15 | Script       | `Sct_BatchBackupExportArchives`              | All         |
| 16 | Function     | `Fun_SE_BatchBackupExportArchives`           | All         |
| 17 | Time Control | `Tfu_BatchBackupExportArchives`              | All         |

---

### 3.6 Additional Configuration

| Component                       | Action Required                                                                                                   |
|---------------------------------|-------------------------------------------------------------------------------------------------------------------|
| Variable `B1_Batch.Active`      | Limit 1: Add function `BatchBackup_SaveRemanentData` (`SE_SaveRemanentDataAllProjects` — SCADA only)              |
| Variable `B1_Batch.Active`      | Limit 2: Add function `BatchBackup_SaveRemanentData`                                                              |
| Variable `B1_Batch.Start`       | Set property `Remanent`                                                                                           |
| Variable `B1_Batch.Start_Extern`| Set property `Remanent`                                                                                           |
| Folder                          | Create `ExportArx` folder in the Runtime folder                                                                   |
| Autostart script                | Add function `WSV_nboBatchRuntimeStart – 1`                                                                       |
| Autostart_Delay script          | Add function `WSV_nboBatchRuntimeStart – 0`                                                                       |
| Script `StartBatchBackup`       | *(SCADA project only)* Add functions `B1_Start_Archive_S1` and `B1_Start_Archive_E1` from all sub-projects       |

---

### 3.7 Screenshots

The source artifact includes two screenshots in section 4.5:

- **Before Runtime Shutdown** — shows the system state prior to an uncontrolled termination.
- **After Runtime Shutdown** — shows the system state following restart and backup execution.

> **Note on red batch name:** In the post-shutdown screenshot, the batch name is displayed with a red background. This behavior is normal and expected: the batch name is validated for uniqueness on Runtime start, and it was already assigned at the time the batch was originally started.

---