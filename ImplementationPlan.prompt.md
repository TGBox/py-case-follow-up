## Plan: Support-Cockpit Implementierung

Ziel ist eine schrittweise implementierbare Desktop-App gemaess `agent-todo.md`. Die Reihenfolge folgt der Abhaengigkeitskette: Projektbasis und Datenvertraege, Storage, deterministische Fachservices, Seed und Tests, UI, danach Wiki und P2P-Integration. Jedes Todo ist klein genug fuer einen eigenen Commit oder eine eigene Validierung.

**Schritte**

##### Phase 1: Projektbasis und verbindliche Regeln
1. [x] Projektstruktur `main.py`, `src/models/`, `src/services/`, `src/ui/`, `tests/` und Paketinitialisierer anlegen. Abhaengigkeit: keine.
2. [x] Abhaengigkeiten und minimale Entwicklungsumgebung fuer Python 3.14+, `customtkinter`, `jinja2` und `pytest` festlegen. Abhaengig von 1.
3. [x] Zentrale Enums/Konstanten fuer Ampel, Status, Actor, Feldtypen, Sync-Modi und Exportziele definieren. Abhaengig von 1.
4. [x] Eine Zeitzonenregel fuer alle ISO-Zeitstempel festlegen und zentrale Parser/Formatter dafuer definieren. Abhaengig von 1.
5. [x] Konfigurationsmodell fuer Benutzer-Arbeitsbereich, Dateipfade und optionale Netzlaufwerkspfade definieren. Abhaengig von 3 und 4.
6. [x] Sicherheitsregeln fuer Profil-/Tokenwerte festlegen: URL normalisieren, Secrets nur aus Umgebungsvariablen lesen und niemals loggen. Abhaengig von 5.
7. [x] Entscheiden und dokumentieren, ob Datamodelle mit `dataclasses` plus eigener Validierung oder Pydantic umgesetzt werden; fuer diese Planung: schlanke `dataclasses` plus explizite Validatoren. Abhaengig von 2.

### Phase 2: Datenmodelle und Storage
8. [x] Modelle fuer Kontakt und Kunde mit 1:n-Kontakten implementieren. Abhaengig von 3 und 7.
9. [x] Modelle fuer Timeline-Eintrag, Fall-Kunde, Klassifikation und Workflow-Status implementieren. Abhaengig von 3, 4 und 7.
10. [x] Modelle fuer Fall, Schema/Feld, Export-Template, Profil und Kollege implementieren. Abhaengig von 8 und 9.
11. [x] Modellvalidatoren fuer Pflichtfelder, Datentypen, IDs, Zeitstempel, Enumwerte und Statuskonsistenz implementieren. Abhaengig von 8 bis 10.
12. [x] JSON-Roundtrip fuer alle Modelle inklusive der im SRS gezeigten Strukturen implementieren und testen. Abhaengig von 11.
13. [x] `StorageService` fuer JSON-Lesen mit fehlender-/beschaedigter-Datei-Behandlung implementieren. Abhaengig von 5, 10 und 11.
14. [x] Atomare JSON-Speicherung ueber temporaere Datei und `Path.replace()` implementieren. Abhaengig von 13.
15. [x] Rotierendes Logging in `app.log` sowie sichere Fehlerprotokollierung ohne Secrets integrieren. Abhaengig von 6 und 13.
16. [x] Taegliches Backup von `cases.json` in `backups/cases_YYYY-MM-DD.json` implementieren. Abhaengig von 14.
17. [x] Sicheres Verschieben eines Falls von `cases.json` nach `archive.json` implementieren, einschliesslich Duplikat- und Absturzstrategie. Abhaengig von 14.
18. [x] Leere Standarddateien und Default-Konfigurationen fuer alle JSON-Arbeitsdaten definieren. Abhaengig von 10 und 13.
19. [x] Storage-Tests fuer Roundtrip, atomare Ersetzung, fehlende/beschaedigte Dateien, Schreibfehler und Daily-Backup schreiben. Abhaengig von 12 bis 18.

### Phase 3: Fachservices ohne UI
20. [x] `ScoringService` mit injizierbarer Uhr und Scoring-Matrix implementieren. Abhaengig von 4, 9 und 10.
21. [x] VIP-, Idle-Day- und Deadline-Beitraege exakt nach der SRS-Formel berechnen. Abhaengig von 20.
22. [x] Ampelzuweisung inklusive exakter Gelb-/Rot-Grenzwerte implementieren. Abhaengig von 21.
23. [x] Scoring-Tests fuer VIP, Idle-Zeit, Deadline-Naehe, Ueberfaelligkeit und Grenzwerte schreiben. Abhaengig von 22.
24. [x] Suchquery-Modell und Parser fuer Tokens plus verbleibenden Freitext implementieren. Abhaengig von 3 und 10.
25. [x] Token-Mapping fuer `vip`, `actor`, `status`, `error` und `deadline` implementieren; unbekannte/ungueltige Tokens definiert behandeln. Abhaengig von 24.
26. [x] Freitextsuche ueber Praxisname, Kundennummer, Kontakte und Timeline-Notizen implementieren. Abhaengig von 25.
27. [x] Parser-/Filtertests fuer Einzel- und Kombinationsabfragen, Gross-/Kleinschreibung und Deadline-Faelle schreiben. Abhaengig von 26.
28. [x] Schema- und Formular-Service fuer Text, Dropdown, Zahl und Boolean implementieren. Abhaengig von 10 und 11.
29. [x] Pflichtfeldvalidierung mit korrekter Behandlung leerer Werte und Boolean-`False` implementieren. Abhaengig von 28.
30. [x] Vorab-Speichern unvollstaendiger Faelle inklusive `is_data_complete` und `missing_required_fields` implementieren. Abhaengig von 29 und 14.
31. [x] Fallanlage mit ID-Generator, Zeitstempeln, initialem Timeline-Eintrag und Score-Berechnung implementieren. Abhaengig von 18, 20 und 30.
32. [x] Attachment-Pfade aus Fall-ID und Windows-sicher bereinigtem Praxisnamen erzeugen; reservierte Namen und Kollisionen behandeln. Abhaengig von 5 und 31.
33. [x] Datei-Anhaengen per Kopie, Fallordner-Oeffnen und PNG-Speicherung aus der Windows-Zwischenablage kapseln. Abhaengig von 32.
34. [x] Kundenverwaltung fuer Lesen, Anlegen, Bearbeiten und Kontaktliste implementieren. Abhaengig von 8, 13 und 14.
35. [x] Schema-Baukastenlogik fuer Hinzufuegen, Entfernen, Up/Down und Pflichtfeldumschaltung implementieren. Abhaengig von 28.
36. [x] Persistierung der Baukasten-Aenderungen ueber `StorageService` implementieren. Abhaengig von 35 und 14.

### Phase 4: Export, Lebenszyklus und Seed
37. [x] `ExportService` mit Jinja2-Umgebung und Template-Laden implementieren. Abhaengig von 10, 13 und 18.
38. [x] Template-Auswahl nach `schema_id` sowie vorgeschlagene Templates aus dem Schema implementieren. Abhaengig von 37.
39. [x] Export-Pflichtfeldpruefung und In-Place-Ergaenzung fehlender Fallwerte implementieren. Abhaengig von 29, 30 und 38.
40. [x] Force-Export mit lesbaren `[FEHLT: ...]`-Platzhaltern implementieren. Abhaengig von 39.
41. [x] Clipboard- und Datei-Export sowie Template-Neuanlage/-Speicherung implementieren. Abhaengig von 37 und 40.
42. [x] Exporttests fuer Rendering, Sonderzeichen, Pflichtfelder, In-Place-Ergaenzung und Force-Export schreiben. Abhaengig von 41.
43. [x] Fall-Erledigung und manuelle Archivierung implementieren. Abhaengig von 17, 30 und 31.
44. [x] Auto-Archivierung beim Start fuer erledigte Faelle ab 30 Tagen implementieren. Abhaengig von 16, 17 und 43.
45. [x] Regressionstests fuer Statuswechsel, Archivierung, Duplikatfreiheit und Restart-Verhalten schreiben. Abhaengig von 44.
46. [x] Seed-Datensatz mit fuenf Kunden, acht Faellen, drei Schemas und zwei Templates ueber die echten Modelle erzeugen. Abhaengig von 18, 20, 30, 34 und 41.
47. [x] Mock-Wiki-SQLite-Datenbank im Seed mit realistischen Metadaten und FTS5-Inhalten erzeugen. Abhaengig von 46 und 51.
48. [x] Seed-Verhalten bei vorhandenen Daten festlegen und idempotent bzw. explizit nicht-ueberschreibend implementieren. Abhaengig von 46.
49. [x] `main.py` mit `--seed` und `--demo`, Arbeitsbereichsoption und sauberem Exit-Code implementieren. Abhaengig von 5, 46 und 48.
50. [x] Seed-Integrationstest mit temporaerem Arbeitsbereich und exakten Mengen-/Beziehungspruefungen schreiben. Abhaengig von 49.

### Phase 5: GUI-Grundgeruest und Kernworkflow
51. [x] `customtkinter`-App mit Logging, Profil-Laden, Theme-/Systemfarberkennung und sauberem Shutdown initialisieren. Abhaengig von 15, 18 und 49.
52. [x] Profil- und Kollegenkonfiguration laden, validieren und mit Defaults zusammenfuehren. Abhaengig von 11, 13 und 51.
53. [x] Cockpit-Grundlayout mit drei stabilen Spalten und Fallauswahl implementieren. Abhaengig von 51 und 52.
54. [x] Fallliste mit Sortierung nach Score, Ampelanzeige, Status und Such-/Filteranbindung implementieren. Abhaengig von 22, 26 und 53.
55. [x] Dynamisches Fallformular aus dem ausgewaehlten Schema rendern. Abhaengig von 28, 29 und 53.
56. [x] Formularvalidierung visuell darstellen und unvollstaendiges Speichern ermoeglichen. Abhaengig von 30 und 55.
57. [x] Kunden-/Kontaktwahl und neue Fallanlage in den Workflow integrieren. Abhaengig von 31, 34 und 56.
58. [x] Timeline, Fallstatus, Erledigen und Archivieren im Detailbereich anbinden. Abhaengig von 43 bis 45 und 57.
59. [x] Attachment-Bereich mit Dateiaktionen, Explorer und Clipboard-Paste anbinden. Abhaengig von 33 und 57.
60. [x] Exportdialog mit Template-Auswahl, fehlenden Feldern, Force-Export und Zielaktionen anbinden. Abhaengig von 38 bis 41 und 57.
61. [x] Suchleiste und Kunden-/Fallfilter im Cockpit vollstaendig verdrahten. Abhaengig von 24 bis 27 und 54.
62. [x] Tab-View und Split-View als alternative Layout-Modi implementieren. Abhaengig von 53 bis 61.
63. [x] Fensterposition, Spaltenbreiten, Splitter und aktives Layout in `app_profile.json` speichern/wiederherstellen. Abhaengig von 52 und 62.
64. [x] Konfigurierbare `bind_all`-Shortcuts mit Standardbelegung und Konfliktbehandlung implementieren. Abhaengig von 52 und 63.
65. [x] Score-Timer, Backup, Auto-Archivierung, Shutdown-Cleanup und optionalen Startup-Ablauf in den App-Lifecycle integrieren. Abhaengig von 20, 16, 44, 51 und 64.
66. [x] Headless-nahe UI-/Service-Integrationstests fuer Start, Auswahl, Bearbeiten, unvollstaendiges Speichern, Export und Archivierung schreiben. Abhaengig von 57 bis 65.

### Phase 6: Wiki-Offline-Index und UI
67. [x] SQLite-Schema fuer Shelves, Books, Pages, Tags, URLs und Inhalte definieren. Abhaengig von 3 und 5.
68. [x] FTS5-Verfuegbarkeit beim Start pruefen und einen klaren Offline-/Fehlerpfad definieren. Abhaengig von 67.
69. [x] `WikiSyncService` mit BookStack-Authentifizierung, Timeouts, API-Fehlerbehandlung und Secret-Schutz implementieren. Abhaengig von 6 und 67.
70. [x] `METADATA_ONLY`-Sync fuer `/api/shelves`, `/api/books` und `/api/pages` implementieren. Abhaengig von 69.
71. [x] `FULL_OFFLINE`-Sync inklusive Markdown-/HTML-Inhalt und FTS5-Indexierung implementieren. Abhaengig von 70.
72. [x] Lokale Wiki-Suche und Ergebnisnormalisierung implementieren. Abhaengig von 71.
73. [x] Wiki-Tests mit Mock-API, Timeout, Auth-Fehler, ungueltiger Antwort, beiden Sync-Modi und FTS-Suche schreiben. Abhaengig von 72.
74. [x] Wiki-Suche in die rechte Cockpit-Arbeitsflaeche integrieren. Abhaengig von 72 und 61.
75. [x] Manuellen Wiki-Sync-Button und optionalen Startup-Sync aus den Profileinstellungen anbinden. Abhaengig von 52, 65 und 74.

### Phase 7: P2P-Sync und Abschluss
76. [x] Kollegenpfade aus `colleagues.json` validieren und lesbare Zugriffsfehler liefern. Abhaengig von 5, 13 und 52.
77. [x] `SyncService` zum Laden fremder `cases.json` mit Modellvalidierung implementieren. Abhaengig von 11, 13 und 76.
78. [x] Diff-Logik nach `case_id` und `updated_at` fuer neuere, aeltere, gleiche und neue Faelle implementieren. Abhaengig von 77 und 4.
79. [x] Selektive Uebernahme einzelner Faelle mit erneuter Validierung und atomarem Speichern implementieren. Abhaengig von 14, 17 und 78.
80. [x] Interaktiven Diff-Dialog mit Auswahl, Vorschau und Konfliktinformationen implementieren. Abhaengig von 79 und 62.
81. [x] P2P-Tests fuer neue Faelle, beide Aktualitaetsrichtungen, gleiche Zeitstempel und selektive Uebernahme schreiben. Abhaengig von 80.
82. [x] P2P-Sync in Navigation/Workflow integrieren, ohne automatische Zwangsueberschreibung. Abhaengig von 80 und 81.
83. [x] Vollstaendigen `pytest`-Lauf, Seed-Lauf im temporaerem Workspace und manuellen `--demo`-Start durchfuehren. Abhaengig von 19, 23, 27, 42, 45, 50, 66, 73 und 81.
84. [x] Dokumentation fuer Installation, Arbeitsbereichspfad, Umgebungsvariablen, Seed-/Demo-Modus, Backup, Wiki-Sync und bekannte Netzlaufwerk-Limits ergaenzen. Abhaengig von 83.

**Relevante Dateien**
- `agent-todo.md` - verbindliche SRS und Akzeptanzkriterien.
- `main.py` - CLI-Einstieg, Seed/Demo und App-Lifecycle.
- `src/models/` - Datenvertraege und Validatoren.
- `src/services/` - Storage, Scoring, Suche, Export, Wiki und P2P-Sync.
- `src/ui/` - Cockpit, Layouts, Formulare, Dialoge, Shortcuts und Attachments.
- `tests/` - Unit-, Integrations- und GUI-nahe Tests gemaess SRS.

**Verifikation**
1. Nach jeder Phase den jeweils angegebenen fokussierten Test bzw. einen deterministischen Smoke-Test ausfuehren.
2. Vor der GUI-Integration `pytest` fuer Storage, Scoring, Suche, Export, Lebenszyklus und Seed erfolgreich ausfuehren.
3. Wiki-Sync nur gegen Mock-API testen; echte Tokens und Produktionsnetzpfade nicht in Tests verwenden.
4. P2P mit temporaeren lokalen Dateien simulieren und sicherstellen, dass kein automatisches Ueberschreiben ohne Auswahl erfolgt.
5. Abschluss: `pytest`, isolierter `python main.py --seed`-Lauf, anschliessend `python main.py --demo` sowie manueller Workflow fuer Fallanlage, unvollstaendiges Speichern, Export, Attachment, Erledigung, Archivierung und Suche.

**Entscheidungen**
- Planung umfasst die gesamte SRS inklusive UI, Seed, Wiki und P2P; keine Funktion wird als spaetere optionale Erweiterung ausgelassen.
- Zeitstempel werden intern timezone-aware behandelt und an einer Stelle formatiert; bestehende naive Beispieldaten muessen beim Einlesen normalisiert werden.
- `dataclasses` plus explizite Validierung werden als leichtgewichtige Standardloesung vorgesehen.
- `--seed` arbeitet standardmaessig in einem explizit konfigurierten Arbeitsbereich und darf produktive Daten nicht stillschweigend ueberschreiben.
- Atomare Writes verhindern Teilwrites, loesen aber keine konkurrierenden Lost Updates; diese Grenze wird dokumentiert und bei P2P durch erneutes Einlesen vor Uebernahme minimiert.
- Clipboard, Explorer, `customtkinter` und echte Netzlaufwerke werden service-seitig gekapselt und in automatisierten Tests gemockt.
- Der in der SRS enthaltene Markdown-Link im `api_url`-Beispiel wird als reine URL normalisiert.

**Bewusste Scope-Grenzen**
- Keine proprietaere Verschluesselung; Zugriffsschutz bleibt bei Windows-/Netzlaufwerk-Berechtigungen.
- Kein automatisches Konflikt-Merging und keine stille Zwangsueberschreibung im P2P-Sync.
- Keine echte BookStack- oder Produktions-Cobra-Integration in Tests; Export erfolgt als Clipboard-/Dateitext.
