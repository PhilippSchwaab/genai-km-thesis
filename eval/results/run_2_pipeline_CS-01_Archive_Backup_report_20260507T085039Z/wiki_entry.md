## Summary
The `BatchBackup` plant model extends the Zenon-based SCADA system (Groninger – Schott Archive) with an automatic backup routine that activates when the Zenon Runtime terminates uncontrolled during an active batch production run. On the next Runtime start, the system detects the uncontrolled shutdown, triggers a backup procedure, notifies the operator via popup, and resumes the batch process without data loss. During active batch production, archives S1 and E1 are copied to the `ExportArx` folder every 5 minutes as a rolling safeguard. Parametrisation and testing were performed on virtual machine `VM 13462_Scada`. Document authored by [Author 1]; version 1.1 as of 2025-07-22.

---

## Decisions
- **Backup trigger logic via three control variables** (`B1_Batch.Start`, `nboBatchRuntimeStart`, `nboBatchBackupStart`): backup starts only when both `nboBatchRuntimeStart` (set by Autostart script) and the remanent variable `B1_Batch.Start` are `True` simultaneously, indicating an uncontrolled shutdown during batch production. A normal Runtime start leaves `B1_Batch.Start` as `False`, so the backup procedure is not activated.
- **Rolling archive copy every 5 minutes** during batch production: files `E1.ARS`, `E1.ARX`, `S1.ARS`, and `S1.ARX` are copied from the Runtime data folder to the Runtime export folder `ExportArx` to ensure recoverability at all times.
- **Import order for sub-projects**: the `BatchBackup` plant model must be imported into all sub-projects first, and into the SCADA project last, because script `SaveRemanentDataAllProject` depends on functions residing in sub-projects.
- **Red batch name highlight on restart is expected behaviour**: the batch name is flagged red at Runtime start because its uniqueness is re-validated against an already-assigned value; this is documented as normal and acceptable.

---

## Action items (with owner and due date where stated)
- (none recorded)

---

## Blockers and open questions
- (none recorded)

---

## Implementation detail (commits, files, line counts where present)

**Scripts**

| Script | Responsibility |
|---|---|
| `SE_StartBatchBackup` | Stops archives E1 & S1, shows popup `Pop_BatchBackup`, resets `nboBatchRuntimeStart`, restarts E1 & S1 (including all sub-project S1/E1 start archives in the SCADA project) |
| `BatchBackupExportArchives` (a.k.a. `Sct_BatchBackupExportArchives`) | Copies `E1.ARS`, `E1.ARX`, `S1.ARS`, `S1.ARX` from Runtime data folder to `ExportArx` |
| `Sct_SaveRemanentDataAllProjects` | SCADA project only; saves remanent data across all sub-projects |

**Manual XML import sequence (17 components, in order)**

1. Template → `Fra_F_PopupBatchBackup`
2. Screen → `Scr_Pop_BatchBackup`
3. Function → `SS_Pop_BatchBackup`
4. Variable → `nboBatchRuntimeStart`
5. Function → `nboBatchRuntimeStart – 0`
6. Function → `nboBatchRuntimeStart – 1`
7. Script → `StartBatchBackup`
8. Function → `SE_StartBatchBackup`
9. Variable → `nboBatchBackupStart`
10. Function → `Fun_BatchBackup_SaveRemanentData`
11. Script → `Sct_SaveRemanentDataAllProjects` *(SCADA project only)*
12. Function → `Fun_SE_SaveRemanentDataAllProjects` *(SCADA project only)*
13. Function → `Fun_BatchBackup_ExportE1Files`
14. Function → `Fun_BatchBackup_ExportS1Files`
15. Script → `Sct_BatchBackupExportArchives`
16. Function → `Fun_SE_BatchBackupExportArchives`
17. Timer → `Tfu_BatchBackupExportArchives`

**Additional configuration changes required**

| Object | Change |
|---|---|
| Variable `B1_Batch.Active` | Add limit value 1 & 2: function `BatchBackup_SaveRemanentData` (SCADA project: `SE_SaveRemanentDataAllProjects`) |
| Variable `B1_Batch.Start` | Set property `Remanent` |
| Variable `B1_Batch.Start_Extern` | Set property `Remanent` |
| Filesystem | Create folder `ExportArx` inside the Runtime folder |
| Autostart script | Add function `WSV_nboBatchRuntimeStart – 1` |
| `Autostart_Delay` script | Add function `WSV_nboBatchRuntimeStart – 0` |
| Script `StartBatchBackup` *(SCADA project only)* | Add `B1_Start_Archive_S1` and `B1_Start_Archive_E1` functions from all sub-projects |

No commit hashes, file paths, or line counts are present in the source artifact.

---

## Sources
- `CS-01_Archive_Backup_report` (support_report) — meshmakers.io, [Author 1], v1.1, 2025-07-22.