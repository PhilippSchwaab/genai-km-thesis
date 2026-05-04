# Wiki Entry: CS-03 – Tip Switch Implementation (Lines V6, L7, L8)

---

**Source Artifact:** CS-03_Tip_Switch_Implementation_report (support_report)
**Author:** [Author 1]
**Date:** 2026-03-20
**Version:** 1.0
**Organization:** meshmakers.io

---

## Table of Contents

1. [Project Information](#project-information)
2. [Overview](#overview)
3. [Implementation Steps](#implementation-steps)
   - 3.1 [Adding Variables](#31-adding-variables)
   - 3.2 [Adding the Interlock](#32-adding-the-interlock)
   - 3.3 [Adding New Language File Entries](#33-adding-new-language-file-entries)
   - 3.4 [Adapting the "Start" Screen](#34-adapting-the-start-screen)
   - 3.5 [Adapting the "Pop\_Favorites" Screen](#35-adapting-the-pop_favorites-screen)
   - 3.6 [Adapting the Machine Speed Screen](#36-adapting-the-machine-speed-screen)

---

## Project Information

| Field | Value |
|---|---|
| **Customer** | Ompi |
| **Customer Case No.** | 1378291 |
| **Zenon Version** | 8.0 |
| **SCADA** | Yes – SCADAPC13106 |

### Machine Numbers & Client Projects

| Line | Machine Numbers | Client Projects |
|---|---|---|
| **L6** | 13101, 13102, 13103, 13104 | 1_HMI_13101, 1_HMI_13102, 1_HMI_13103, 1_HMI_13104 |
| **L7** | 13242, 13244, 13245, 13246 | 1_HMI_13242, 1_HMI_13244, 1_HMI_13245, 1_HMI_13246 |
| **L8** | 13549, 13550, 13551, 13552 | 1_HMI_13549, 1_HMI_13550, 1_HMI_13551, 1_HMI_13552 |

---

## Overview

The implementation adds tip switch (Tipptaster) functionality to Lines L6, L7, and L8. The key behavioral rules are:

- When the tip switch is **active**, the machine **must not** be switched to automatic mode. The corresponding buttons in Zenon must be locked.
- When the machine is in **tip switch mode**, the customer can **pre-select a machine speed**.
- The implementation is **identical for every project**.

Two new variables are introduced: one for the tip switch state and one for machine speed.

---

## Implementation Steps

### 3.1 Adding Variables

Two new variables must be added to each project.

---

#### Variable 1: `1_S7\db_allgemein.fkt.tipptaster_linie`

| Parameter | Value |
|---|---|
| **Description** | `1` = Tip switch connected to line; automatic mode disabled |
| **Network Address** | 1 |
| **Data Block** | 1804 |
| **Offset** | 2 |
| **Bit Number** | 3 |
| **Driver** | S7TCP32 – 1_S7 TCP-IP |
| **Data Type** | Bool |
| **Driver Object Type** | Extended Data Block |

---

#### Variable 2: `1_S7\db_allgemein.r32._10`

| Parameter | Value |
|---|---|
| **Description** | Speed when tip switch is connected |
| **Unit** | pcs/min |
| **Network Address** | 1 |
| **Data Block** | 1804 |
| **Offset** | 160 |
| **Bit Number** | 0 |
| **Driver** | S7TCP32 – 1_S7 TCP-IP |
| **Data Type** | REAL |
| **Driver Object Type** | Extended Data Block |
| **Setpoint Limits** | Min: 10 / Max: 200 |

---

### 3.2 Adding the Interlock

A new interlock named **`LockMachineAutoMode`** must be created with the following configuration:

| Parameter | Value |
|---|---|
| **Name** | LockMachineAutoMode |
| **Variables** | `1_S7\db_anl_ges.eing`, `1_S7\db_allgemein.fkt.tipptaster_linie` |
| **Logic** | `(X01.Wert = 1) OR (X02.Wert = 1)` |

---

### 3.3 Adding New Language File Entries

Two new language string IDs must be added per project: one for **machine speed** (`<Maschinengeschwindigkeit>`) and one for the **interlock message** (`<Verriegelung>`).

#### String ID Mapping per Project

| Client Project(s) | `<Maschinengeschwindigkeit>` ID | `<Verriegelung>` ID |
|---|---|---|
| 1_HMI_13101 | HMI7748 | HMI7749 |
| 1_HMI_13102, 1_HMI_13103 | HMI7756 | HMI7757 |
| 1_HMI_13104 | HMI7772 | HMI7773 |
| 1_HMI_13242, 1_HMI_13244, 1_HMI_13245, 1_HMI_13246 | HMI8517 | HMI8518 |
| 1_HMI_13549 | HMI8651 | HMI8652 |
| 1_HMI_13550 | HMI8695 | HMI8696 |
| 1_HMI_13551 | HMI8936 | HMI8937 |
| 1_HMI_13552 | HMI8514 | HMI8515 |

#### String Content: `<Maschinengeschwindigkeit>`

| Language | Text |
|---|---|
| German | Max. Geschwindigkeit während Tiptaster aktiv |
| English | Max. speed while touch switch is active |
| Italian | Velocità massima quando l'interruttore a sfioramento è attivo |

#### String Content: `<Verriegelung>`

| Language | Text |
|---|---|
| German | Funktion nicht möglich, solange die Maschine läuft oder Tiptaster an die Line angeschlossen ist! |
| English | Function not possible while the machine is running or a Tip switch is connected to the line! |
| Italian | Funzione non disponibile mentre la macchina è in funzione o se un interruttore a sfioramento è collegato alla linea! |

---

### 3.4 Adapting the "Start" Screen

In the **"Start"** screen, select the following button and update its Operation Lock settings:

| Parameter | Value |
|---|---|
| **Button** | `Basic_ButtonToggleFunctionTrigger~~1_S7\db_anl_0.op_auto` |
| **Interlock (Verriegelung)** | `LockMachineAutoMode` |
| **Text** | `@<Verriegelung>` |

---

### 3.5 Adapting the "Pop_Favorites" Screen

In the **"Pop_Favorites"** screen, select the following button and update its Operation Lock settings:

| Parameter | Value |
|---|---|
| **Button** | `Basic_ButtonToggleFunctionTrigger~~1_S7\db_anl_0.op_auto` |
| **Interlock (Verriegelung)** | `LockMachineAutoMode` |
| **Text** | `@<Verriegelung>` |

---

### 3.6 Adapting the Machine Speed Screen

A new input field for the tip speed must be added to the machine speed screen. The target screen name varies by project:

| Screen Name | Client Projects |
|---|---|
| `APPL_Machinemaster_Data` | 1_HMI_13101, 1_HMI_13103, 1_HMI_13242, 1_HMI_13245, 1_HMI_13549, 1_HMI_13551 |
| `APPL_MachinemasterDataGeneral` | 1_HMI_13102, 1_HMI_13244, 1_HMI_13550 |
| `Appl_Machinemaster0` | 1_HMI_13104, 1_HMI_13246, 1_HMI_13552 |

#### New Input Field Configuration

| Parameter | Value |
|---|---|
| **Static Text** | `@<Maschinengeschwindigkeit>` |
| **Display Authorization Level** | 33 |
| **Variable** | `1_S7\db_allgemein.r32._10` |
| **Setpoint Limits** | Inherited from variable |
| **Authorization Level** | Machine parametrization |

---

## Change History

| Date | Version | Author | Reason |
|---|---|---|---|
| 2026-03-20 | 1.0 | [Author 1] | Initial creation |