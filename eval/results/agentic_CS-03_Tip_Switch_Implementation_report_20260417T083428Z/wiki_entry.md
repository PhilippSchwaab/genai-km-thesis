# CS-03 – Tip Switch Implementation (Lines L6, L7, L8)

**Source:** Artifact 1 – CS-03_Tip_Switch_Implementation_report (support_report)
**Producing Organization:** MESHMAKERS.IO
**Project Reference:** Groninger – 1378291_Ompi
**Date:** 2026-03-20 | **Version:** 1.0 | **Author:** [Author 1]

---

## Project Information

| Field            | Value              |
|------------------|--------------------|
| Customer         | Ompi               |
| Ticket Number    | 1378291            |
| Designation      | *(not specified)*  |
| Zenon Version    | 8.0                |
| SCADA            | Yes – SCADAPC13106 |

### Machine Numbers & HMI Client Projects

| Line | Machine Numbers            | HMI Client Projects                                         |
|------|----------------------------|-------------------------------------------------------------|
| L6   | 13101, 13102, 13103, 13104 | 1_HMI_13101, 1_HMI_13102, 1_HMI_13103, 1_HMI_13104         |
| L7   | 13242, 13244, 13245, 13246 | 1_HMI_13242, 1_HMI_13244, 1_HMI_13245, 1_HMI_13246         |
| L8   | 13549, 13550, 13551, 13552 | 1_HMI_13549, 1_HMI_13550, 1_HMI_13551, 1_HMI_13552         |

---

## Overview

The implementation adds tip switch (*Tipptaster*) and machine speed (*Maschinengeschwindigkeit*) support to lines L6, L7, and L8 by introducing two new variables. When the tip switch is active, the machine must not be switched to automatic mode; the corresponding buttons in Zenon are locked. While in tip switch mode, the customer can pre-select a machine speed. The implementation procedure is identical for every project.

---

## Implementation Steps

### 1. Adding Variables

Two new variables are added:

#### Variable 1: `1_S7\db_allgemein.fkt.tipptaster_linie`

| Property           | Value                                                     |
|--------------------|-----------------------------------------------------------|
| Description        | 1 = Tip switch connected to line, automatic mode disabled |
| Network Address    | 1                                                         |
| Data Block         | 1804                                                      |
| Offset             | 2                                                         |
| Bit Number         | 3                                                         |
| Driver             | S7TCP32 – 1_S7 TCP-IP                                     |
| Data Type          | Bool                                                      |
| Driver Object Type | Extended Data Block                                       |

#### Variable 2: `1_S7\db_allgemein.r32._10`

| Property           | Value                                        |
|--------------------|----------------------------------------------|
| Description        | Speed – tip switch connected (*Geschwindigkeit Tipptaster gesteckt*) |
| Unit               | pcs/min                                      |
| Network Address    | 1                                            |
| Data Block         | 1804                                         |
| Offset             | 160                                          |
| Bit Number         | 0                                            |
| Driver             | S7TCP32 – 1_S7 TCP-IP                        |
| Data Type          | REAL                                         |
| Driver Object Type | Extended Data Block                          |
| Setpoint Limits    | Min: 10 / Max: 200                           |

---

### 2. Adding the Interlock

A new interlock named **LockMachineAutoMode** is configured as follows:

| Property  | Value                                                             |
|-----------|-------------------------------------------------------------------|
| Name      | LockMachineAutoMode                                               |
| Variables | `1_S7\db_anl_ges.eing`, `1_S7\db_allgemein.fkt.tipptaster_linie` |
| Logic     | `(X01.Wert = 1) OR (X02.Wert = 1)`                               |

---

### 3. Adding New Language File Entries

New language string IDs are assigned per HMI project:

| HMI Project(s)                                      | `<Maschinengeschwindigkeit>` | `<Verriegelung>` |
|-----------------------------------------------------|------------------------------|------------------|
| 1_HMI_13101                                         | HMI7748                      | HMI7749          |
| 1_HMI_13102, 1_HMI_13103                            | HMI7756                      | HMI7757          |
| 1_HMI_13104                                         | HMI7772                      | HMI7773          |
| 1_HMI_13242, 1_HMI_13244, 1_HMI_13245, 1_HMI_13246 | HMI8517                      | HMI8518          |
| 1_HMI_13549                                         | HMI8651                      | HMI8652          |
| 1_HMI_13550                                         | HMI8695                      | HMI8696          |
| 1_HMI_13551                                         | HMI8936                      | HMI8937          |
| 1_HMI_13552                                         | HMI8514                      | HMI8515          |

#### String Translations

**`<Maschinengeschwindigkeit>`**
| Language | Text |
|----------|------|
| 🇩🇪 DE | *Max. Geschwindigkeit während Tiptaster aktiv* |
| 🇬🇧 EN | *Max. speed while touch switch is active* |
| 🇮🇹 IT | *Velocità massima quando l'interruttore a sfioramento è attivo* |

**`<Verriegelung>`**
| Language | Text |
|----------|------|
| 🇩🇪 DE | *Funktion nicht möglich, solange die Maschine läuft oder Tiptaster an die Line angeschlossen ist!* |
| 🇬🇧 EN | *Function not possible while the machine is running or a Tip switch is connected to the line!* |
| 🇮🇹 IT | *Funzione non disponibile mentre la macchina è in funzione o se un interruttore a sfioramento è collegato alla linea!* |

---

### 4. Adapting the "Start" Screen

Select button `Basic_ButtonToggleFunctionTrigger~~1_S7\db_anl_0.op_auto` and modify the Operation Lock:

| Property  | Value               |
|-----------|---------------------|
| Interlock | LockMachineAutoMode |
| Text      | `@<Verriegelung>`   |

---

### 5. Adapting the "Pop_Favorites" Screen

Select button `Basic_ButtonToggleFunctionTrigger~~1_S7\db_anl_0.op_auto` and modify the Operation Lock:

| Property  | Value               |
|-----------|---------------------|
| Interlock | LockMachineAutoMode |
| Text      | `@<Verriegelung>`   |

---

### 6. Adapting the Machine Speed Screen

Add a new input field for tip speed (*Tippgeschwindigkeit*). The target screen name varies by project:

| HMI Project(s)                                                                  | Screen Name                   |
|---------------------------------------------------------------------------------|-------------------------------|
| 1_HMI_13101, 1_HMI_13103, 1_HMI_13242, 1_HMI_13245, 1_HMI_13549, 1_HMI_13551 | APPL_Machinemaster_Data       |
| 1_HMI_13102, 1_HMI_13244, 1_HMI_13550                                          | APPL_MachinemasterDataGeneral |
| 1_HMI_13104, 1_HMI_13246, 1_HMI_13552                                          | Appl_Machinemaster0           |

**Input field configuration:**

| Property            | Value                           |
|---------------------|---------------------------------|
| Static Text         | `@<Maschinengeschwindigkeit>`   |
| Display Auth. Level | 33                              |
| Variable            | `1_S7\db_allgemein.r32._10`     |
| Setpoint Limits     | Taken from variable             |
| Authorization Level | Machine parametrization         |

---

## Change Log

| Date       | Version | Author     | Reason           |
|------------|---------|------------|------------------|
| 2026-03-20 | 1.0     | [Author 1] | Initial creation |