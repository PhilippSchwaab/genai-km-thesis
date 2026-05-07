## Summary
Implementation report for a tip-switch (Tipptaster) feature rolled out across production lines L6, L7, and L8 for customer Ompi (ticket 1378291). When a tip switch is physically connected to a line, the machine must be prevented from entering automatic mode; additionally, the operator can pre-select a machine speed while tip-switch mode is active. The implementation is identical across all affected Zenon client projects. Authored by [Author 1], version 1.0, dated 2026-03-20.

## Decisions
- Add two new Zenon variables per project (`fkt.tipptaster_linie` [Bool] and `r32._10` [REAL]) to represent tip-switch state and tip-switch machine speed respectively.
- Introduce a dedicated interlock (`LockMachineAutoMode`) combining the existing general-plant input variable and the new tip-switch variable via OR logic, rather than modifying existing interlocks directly.
- Machine speed setpoint range fixed at **10–200 pcs/min**, sourced from the variable's own setpoint limits.
- Display authorization level for the new speed input field set to **33** ("Machine parametrization").
- Language strings added in three languages (German, English, Italian) for both the speed label and the interlock message, with per-project HMI string IDs assigned.

## Action items (with owner and due date where stated)
- (none recorded)

## Blockers and open questions
- (none recorded)

## Implementation detail (commits, files, line counts where present)

**Scope**
- Zenon version: 8.0
- SCADA: SCADAPC13106
- Affected lines and machine numbers:
  - L6: 13101, 13102, 13103, 13104
  - L7: 13242, 13244, 13245, 13246
  - L8: 13549, 13550, 13551, 13552
- Affected client projects: 1_HMI_13101–13104, 1_HMI_13242/44/45/46, 1_HMI_13549–13552

**Variables added (per project)**

| Variable | Driver | Data block | Offset | Bit | Data type | Purpose |
|---|---|---|---|---|---|---|
| `1_S7\db_allgemein.fkt.tipptaster_linie` | S7TCP32 – 1_S7 TCP-IP | 1804 | 2 | 3 | Bool | Tip switch active → automatic mode disabled |
| `1_S7\db_allgemein.r32._10` | S7TCP32 – 1_S7 TCP-IP | 1804 | 160 | 0 | REAL | Machine speed setpoint during tip-switch mode (10–200 pcs/min) |

**Interlock added**
- Name: `LockMachineAutoMode`
- Variables: `1_S7\db_anl_ges.eing`, `1_S7\db_allgemein.fkt.tipptaster_linie`
- Logic: `(X01.Wert = 1) OR (X02.Wert = 1)`

**Screens modified**
- `Start` — button `Basic_ButtonToggleFunctionTrigger~~1_S7\db_anl_0.op_auto`: interlock set to `LockMachineAutoMode`, text set to `@<Verriegelung>`.
- `Pop_Favorites` — same button and same changes as `Start`.
- Machine speed screen (project-dependent image name):

| Image name | Projects |
|---|---|
| `APPL_Machinemaster_Data` | 1_HMI_13101, 13103, 13242, 13245, 13549, 13551 |
| `APPL_MachinemasterDataGeneral` | 1_HMI_13102, 13244, 13550 |
| `Appl_Machinemaster0` | 1_HMI_13104, 13246, 13552 |

New input field added: static text `@<Maschinengeschwindigkeit>`, variable `1_S7\db_allgemein.r32._10`, setpoint limits taken from variable, authorization level 33.

**Language file entries (HMI string IDs)**

| Project(s) | `<Maschinengeschwindigkeit>` ID | `<Verriegelung>` ID |
|---|---|---|
| 1_HMI_13101 | HMI7748 | HMI7749 |
| 1_HMI_13102, 13103 | HMI7756 | HMI7757 |
| 1_HMI_13104 | HMI7772 | HMI7773 |
| 1_HMI_13242, 13244, 13245, 13246 | HMI8517 | HMI8518 |
| 1_HMI_13549 | HMI8651 | HMI8652 |
| 1_HMI_13550 | HMI8695 | HMI8696 |
| 1_HMI_13551 | HMI8936 | HMI8937 |
| 1_HMI_13552 | HMI8514 | HMI8515 |

String values:
- `<Maschinengeschwindigkeit>` — DE: *Max. Geschwindigkeit während Tiptaster aktiv* / EN: *Max. speed while touch switch is active* / IT: *Velocità massima quando l'interruttore a sfioramento è attivo*
- `<Verriegelung>` — DE: *Funktion nicht möglich, solange die Maschine läuft oder Tiptaster an die Line angeschlossen ist!* / EN: *Function not possible while the machine is running or a Tip switch is connected to the line!* / IT: *Funzione non disponibile mentre la macchina è in funzione o se un interruttore a sfioramento è collegato alla linea!*

## Sources
- CS-03_Tip_Switch_Implementation_report (support_report), meshmakers.io, [Author 1], 2026-03-20, v1.0. Customer ticket: Ompi 1378291.