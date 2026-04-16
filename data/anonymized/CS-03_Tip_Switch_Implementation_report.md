<!-- Page 1 -->
MESHMAKERS.IO
Groninger – 1378291_Ompi
Implementierung eine Tippschalters in Linie V6, L7 und L8
20.03.2026
meshmakers.io
[Author 1]

<!-- Page 2 -->
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

<!-- Page 3 -->
20.03.2026
Datum Version Autor Grund der Änderungen
2026-03-20 1.0 [Author 1] Ersterstellung
MESHMAKERS.IO 2/12

<!-- Page 4 -->
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

<!-- Page 5 -->
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

<!-- Page 6 -->
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

<!-- Page 7 -->
20.03.2026
1.4 Anpassen des Bildes: “Start”
Button “Basic_ButtonToggleFunctionTrigger~~1_S7\db_anl_0.op_auto” auswählen und Operation
Lock ändern:
Verriegelung: “LockMachineAutoMode”
Text: @<Verriegelung>
MESHMAKERS.IO 6/12

<!-- Page 8 -->
20.03.2026
1.5 Anpassen des Bildes: “Pop_Favorites”
Button „Basic_ButtonToggleFunctionTrigger~~1_S7\db_anl_0.op_auto” auswählen und Operation
Lock ändern:
Verriegelung: “LockMachineAutoMode”
Text: @<Verriegelung>
MESHMAKERS.IO 7/12

<!-- Page 9 -->
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

<!-- Page 10 -->
20.03.2026
MESHMAKERS.IO 9/12

<!-- Page 11 -->
20.03.2026
MESHMAKERS.IO 10/12

<!-- Page 12 -->
20.03.2026
MESHMAKERS.IO 11/12

<!-- Page 13 -->
20.03.2026
MESHMAKERS.IO 12/12