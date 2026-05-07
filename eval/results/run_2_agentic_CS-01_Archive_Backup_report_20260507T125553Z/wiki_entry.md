## Summary
The `BatchBackup` plant model extends the Groninger–Schott Archive SCADA system (Zenon Runtime) with an automatic backup routine that activates whenever the Zenon Runtime terminates uncontrolled during an active batch production run. On the next Runtime start the system detects the crash, stops and restarts archives E1 and S1, notifies the operator via a popup, and resumes the batch process without data loss. During normal batch production, archives S1 and E1 are copied to the `ExportArx` folder every 5 minutes as a rolling safety net. Parametrisation and testing were carried out on virtual machine `VM 13462_Scada`.

## Decisions
- **Backup trigger logic via three variables** (`B1_Batch.Start`, `nboBatchRuntimeStart`, `nboBatchBackupStart`): the backup procedure starts only when both `nboBatchRuntimeStart` (set by the Autostart script) and the remanent variable `B1_Batch.Start` are `True` simultaneously, indicating an uncontrolled shutdown during batch production. On a normal Runtime start `B1_Batch.Start` is `False` and the backup is skipped.
- **Rolling 5-minute archive export** during batch production: archives S1 and E1 (`*.ARS` / `*.ARX`) are copied to the Runtime export folder `ExportArx` on a 5-minute timer (`Tfu_BatchBackupExportArchives`) via script `SE_BatchBackupExportArchives`, ensuring at most 5 minutes of data can be lost.
- **Import order constraint**: the `BatchBackup` plant model must be imported into all sub-projects before the SCADA project, because script `SaveRemanentDataAllProject` calls functions residing in the sub-projects.
- **Red batch-name highlight on restart is expected behaviour**: the batch name is shown with a red background at Runtime start because uniqueness is re-validated against a name already assigned at batch start; this is documented as normal and acceptable.

## Action items (with owner and due date where stated)
- (none recorded)

## Blockers and open questions
- (none recorded)

## Implementation detail (commits, files, line counts where present)
**Key scripts and their execution sequence:**

| Script | Triggered by | Actions (in order) |
|---|---|---|
| `SE_StartBatchBackup` | `nboBatchBackupStart` math variable | 1. Stop archives E1 and S1 · 2. Show popup `Pop_BatchBackup` · 3. Reset `nboBatchRuntimeStart` · 4. Restart archives E1 and S1 · 5. (SCADA project only) Start all S1 and E1 archives from sub-projects |
| `SE_BatchBackupExportArchives` (also referred to as `BatchBackupExportArchives` in section 4.1.2 of the source) | Timer `Tfu_BatchBackupExportArchives` (5 min) | 1. Copy `E1.ARS` + `E1.ARX` from Runtime data folder → `ExportArx` · 2. Copy `S1.ARS` + `S1.ARX` from Runtime data folder → `ExportArx` |

**Manual XML import sequence (17 components, in required order):**
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

**Additional configuration changes required:**
- `B1_Batch.Active`: add limit `Grenzwert_1` → `BatchBackup_SaveRemanentData` (SCADA project: use `SE_SaveRemanentDataAllProjects` instead); add limit `Grenzwert_2` → `BatchBackup_SaveRemanentData` (all projects).
- `B1_Batch.Start`: set property `Remanent`.
- `B1_Batch.Start_Extern`: set property `Remanent`.
- Create folder `ExportArx` inside the Runtime folder.
- Autostart script: add function `WSV_nboBatchRuntimeStart – 1`.
- `Autostart_Delay` script: add function `WSV_nboBatchRuntimeStart – 0`.
- Script `StartBatchBackup` *(SCADA project only)*: add `B1_Start_Archive_S1` and `B1_Start_Archive_E1` functions from all sub-projects.

**Wizard-based import alternative:** use `ImportModelWizard` to import plant model `BatchBackup`; all required Zenon components are imported automatically and `BatchBackup` is assigned to the `Basic` plant model. Sub-projects must still be imported before the SCADA project.

**Document versions:**

| Date | Version | Author | Change |
|---|---|---|---|
| 2025-07-15 | 0.1 | [Author 1] | Initial creation |
| 2025-07-22 | 1.1 | [Author 1] | Added screenshots and manual model import section |

## Sources
- `CS-01_Archive_Backup_report` (support_report), meshmakers.io, [Author 1], 2025-07-22.