<!-- Page 1 -->
MESHMAKERS.IO
Groninger – Schott Archive
Backup
Chargen-Backupfunktionalität nach unkontrollierter Zenon
Runtime Beendigung
22.07.2025
meshmakers.io
[Author 1]

<!-- Page 2 -->
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

<!-- Page 3 -->
22.07.2025
Datum Version Autor Grund der Änderungen
2025-07-15 0.1 [Author 1] Ersterstellung
2025-07-22 1.1 [Author 1] Ergänzungen Screenshots und
händische Modelimportierung
MESHMAKERS.IO 2/8

<!-- Page 4 -->
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

<!-- Page 5 -->
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

<!-- Page 6 -->
22.07.2025
4.2 Import des Anlagenmodells mit Wizard
Das Anlagenmodel „BatchBackup“ mit dem Wizard „ImportModelWizard“ importieren. Alle Benötigten
Zenon Komponenten werden importiert und „BatckBackup“ wird dem Anlagenmodell Basic
zugeordnet.
Es ist notwendig, den Import zuerst bei allen Unterprojekten durchzuführen und erst zum Schluss im
SCADA Projekt, da das Skript „SaveRemanentDataAllProject“ auf Funktionen im Unterprojekt zugreift.
MESHMAKERS.IO 5/8

<!-- Page 7 -->
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

<!-- Page 8 -->
22.07.2025
4.5 Screenshots
Vor Runtime Shutdown:
Nach Runtime Shutdown:
MESHMAKERS.IO 7/8

<!-- Page 9 -->
22.07.2025
Im Screenshot ist ersichtlich das der Chargenname Rot hinterlegt ist. Dieses Verhalten ist normal und
zulässig, da der Chargenname bei Runtimestart auf seinen eindeutigen Wert überprüft wird und dieser
bereits zu Chargen Start vergeben wurde.
MESHMAKERS.IO 8/8