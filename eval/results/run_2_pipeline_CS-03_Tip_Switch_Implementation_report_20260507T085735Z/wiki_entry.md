## Summary
Implementation report for a tip-switch (Tipptaster) feature rolled out across Zenon HMI projects on production lines L6, L7, and L8 for customer Ompi (ticket 1378291). When a tip switch is physically connected to a line, the machine is prevented from switching into automatic mode. In tip-switch mode the operator can pre-select a machine speed. The implementation is identical across all affected projects. Authored by [Author 1], version 1.0, dated 2026-03-20.

**Affected machines**

| Line | Machine numbers |
|------|----------------|
| L6 | 13101, 13102, 13103, 13104 |
| L7 | 13242, 13244, 13245, 13246 |
| L8 | 13549, 13550, 13551, 13552 |

**Zenon version:** 8.0 · **SCADA:** SCADAPC13106

---

## Decisions
- **Interlock logic via Zenon lock function** (`LockMachineAutoMode`): automatic mode buttons are locked whenever the tip switch is active (`X01.Wert = 1`) OR the machine is already running (`X02.Wert = 1`). No alternative approach recorded.
- **Machine speed setpoint sourced from a new REAL variable** (`1_S7\db_allgemein.r32._10`) with hard limits of 10–200 pcs/min.
- **Uniform implementation across all projects**: the same variable definitions, lock configuration, and screen changes are applied identically to every HMI project on L6, L7, and L8.

---

## Action items (with owner and due date where stated)
- (none recorded)

---

## Blockers and open questions
- (none recorded)

---

## Implementation detail (commits, files, line counts where present)

### 1. New variables added (per project)

| Variable | Data block | Offset | Bit | Data type | Driver | Notes |
|---|---|---|---|---|---|---|
| `1_S7\db_allgemein.fkt.tipptaster_linie` | DB 1804 | 2 | 3 | Bool | S7TCP32 – 1_S7 TCP-IP | 1 = tip switch connected, auto mode disabled |
| `1_S7\db_allgemein.r32._10` | DB 1804 | 160 | 0 | REAL | S7TCP32 – 1_S7 TCP-IP | Machine speed in pcs/min; setpoint min 10, max 200 |

Both variables use network address 1, driver object type: *Erweiterter Datenbaustein*.

### 2. Interlock added

- **Lock name:** `LockMachineAutoMode`
- **Variables:** `1_S7\db_anl_ges.eing`, `1_S7\db_allgemein.fkt.tipptaster_linie`
- **Logic:** `(X01.Wert = 1) OR (X02.Wert = 1)`

### 3. Language file entries added

Two new string IDs per HMI project (Maschinengeschwindigkeit + Verriegelung), in German, English, and Italian:

| Project(s) | `<Maschinengeschwindigkeit>` ID | `<Verriegelung>` ID |
|---|---|---|
| 1_HMI_13101 | HMI7748 | HMI7749 |
| 1_HMI_13102, 1_HMI_13103 | HMI7756 | HMI7757 |
| 1_HMI_13104 | HMI7772 | HMI7773 |
| 1_HMI_13242, 1_HMI_13244, 1_HMI_13245, 1_HMI_13246 | HMI8517 | HMI8518 |
| 1_HMI_13549 | HMI8651 | HMI8652 |
| 1_HMI_13550 | HMI8695 | HMI8696 |
| 1_HMI_13551 | HMI8936 | HMI8937 |
| 1_HMI_13552 | HMI8514 | HMI8515 |

**String content:**

- `<Maschinengeschwindigkeit>` — DE: *Max. Geschwindigkeit während Tiptaster aktiv* / EN: *Max. speed while touch switch is active* / IT: *Velocità massima quando l'interruttore a sfioramento è attivo*
- `<Verriegelung>` — DE: *Funktion nicht möglich, solange die Maschine läuft oder Tiptaster an die Line angeschlossen ist!* / EN: *Function not possible while the machine is running or a Tip switch is connected to the line!* / IT: *Funzione non disponibile mentre la macchina è in funzione o se un interruttore a sfioramento è collegato alla linea!*

### 4. Screen changes

**Screen "Start" and screen "Pop_Favorites" (all projects)**
- Select button `Basic_ButtonToggleFunctionTrigger~~1_S7\db_anl_0.op_auto`
- Set Operation Lock → `LockMachineAutoMode`
- Set lock text → `@<Verriegelung>`

**Machine speed screen (project-dependent screen name)**

| Project(s) | Screen name |
|---|---|
| 1_HMI_13101, 1_HMI_13103, 1_HMI_13242, 1_HMI_13245, 1_HMI_13549, 1_HMI_13551 | `APPL_Machinemaster_Data` |
| 1_HMI_13102, 1_HMI_13244, 1_HMI_13550 | `APPL_MachinemasterDataGeneral` |
| 1_HMI_13104, 1_HMI_13246, 1_HMI_13552 | `Appl_Machinemaster0` |

Add new input field with:
- Static text: `@<Maschinengeschwindigkeit>`
- Display authorization level: 33
- Variable: `1_S7\db_allgemein.r32._10`
- Setpoint limits: inherit from variable
- Authorization level: *Machine parametrization*

No commit hashes, file paths, or line counts were recorded in the source artifact.

---

## Sources
- CS-03_Tip_Switch_Implementation_report (support_report), meshmakers.io, [Author 1], 2026-03-20, v1.0. Customer: Ompi, ticket 1378291.