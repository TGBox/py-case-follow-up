# Support Follow-Up & Ticket-Cockpit (Desktop-App)

Eine moderne Python-Desktop-Applikation (`customtkinter`) zur Erfassung, Nachverfolgung (Follow-up), Priorisierung und standardisierten Übergabe von Support-Fällen und internen Aufgaben an Entwicklungs- und Technikabteilungen.

---

## 🌟 Hauptfunktionen & Features

* **3-Spalten Cockpit, Board & Tabellenmatrix:** Flexible UI-Layouts mit CustomTkinter Flat-Optik, flüssigen Animationen und dynamischem **Dark- & Light-Mode**.
* **🏢 Interne Vorgänge & Aufgaben (ohne Kunde):** Erfassung rein interner Vorgänge (Systemwartung, Notizen, Entwicklungsaufgaben) ohne Kundenelement mit automatischer Umschaltung auf das Schema *"🏢 Interne Aufgabe / Notiz"* und blauem `🏢 INTERN`-Badge.
* **🔔 Live-Wiedervorlagen & Background Toast-Popups:**
  - Glocken-Badge (`🔔 3`) in der Kopfzeile mit Live-Zähler fälliger Fristen.
  - Periodische Fristenprüfung im Hintergrund mit unaufdringlichen Toast-Notifications am Bildschirmrand.
  - **Wiedervorlagen-Flyout** zum schnellen Verfolgen, Erledigen oder Verschieben (`+ 1 Tag`, `+ 1 Woche`).
* **⏱️ Datumswahl mit Uhrzeit & Schnellauswahl:**
  - Kalender-Widget mit Datums- und Uhrzeitwahl (HH:MM).
  - Schnellauswahl-Buttons: *"Morgen 08:00 Uhr"*, *"Heute 11:30 (vor Mittag)"*, *"Heute 13:30 (nach Mittag)"*.
* **📊 Auswertungs- & KPI-Dashboard (`📊 Auswertungen`):**
  - Übersicht über Gesamtfälle, offene/erledigte/archivierte Vorgänge.
  - Dringlichkeits-Scoring Verteilung (`Rot` / `Gelb` / `Grün`).
  - Top 5 Praxen-Ranking nach Fallaufkommen & Abteilungs-Auslastung.
* **🖨️ Fall-Akte PDF/Druck-Export (`CasePrintDialog`):**
  - Druckauswahl-Dialog mit Checkboxen zum gezielten Abwählen einzelner Timeline-Einträge oder Kundendaten.
  - Erzeugt saubere HTML/PDF-Druckberichte und öffnet diese direkt im Browser.
* **📂 Dateianhängs-Vorschau & OS-Integration:**
  - Live-Text- und Bild-Vorschau für Anhänge (PNG, JPG, Logfiles, JSON).
  - Direktes Öffnen von Anhängen im OS-Standardprogramm und Speichern von Screenshots per `Strg+V`.
* **⚠️ Mitarbeiter-Abwesenheiten & Urlaubsnotizen:** Erfassen von Urlaub/Krankheit in der Mitarbeiterverwaltung mit automatischem Warnhinweis im Übergabe-Dialog bei Auswahl abwesender Kollegen.
* **🔍 Erweitertes Suchsystem & Schnellfilter:**
  - Tokens wie `is:internal`, `is:customer`, `vip:true`, `reminder:due`, `actor:dev`, `status:open`, `error:...`.
  - Schnellfilter-Buttons (`[Alle]`, `[🔥 Dringend]`, `[🔔 Wiedervorlagen]`, `[🏢 Intern]`) über der Fallliste.
* **📦 Komplett-ZIP Backup & Import/Export:** Export und Wiederherstellung des gesamten Datenbestands (inkl. aller JSON-Dateien & Anhänge-Ordner) als ZIP-Archiv.
* **🔌 E-Mail-Import & REST Webhooks:** Umwandlung von Support-Mails in Fall-Entwürfe (`ImapImportService`) sowie REST-Webhook Payloads für GitLab/Jira Issue Tracker (`WebhookIntegrationService`).
* **📚 BookStack Wiki Offline-Suche:** SQLite3 FTS5 Volltextsuchindex für Offline-Zugriff auf Wiki-Dokumentationen mit BookStack REST-API Sync.
* **🔄 Multi-User P2P-Sync:** Dezentraler Abgleich der `cases.json` von Kollegen über Netzlaufwerke mit interaktivem Diff-Dialog.

---

## 🚀 Schnellstart & Installation

### Voraussetzungen
* Python 3.14+
* Windows / Linux / macOS

### Installation & Start
```bash
# Virtuelle Umgebung erstellen
python -m venv .venv

# Abhängigkeiten installieren
.\.venv\Scripts\pip install -r requirements.txt

# Anwendung starten
.\.venv\Scripts\python main.py
```

---

## 💻 CLI-Befehle

### 1. Test-Daten erzeugen (`--seed`)
Generiert automatisch 5 Kunden, 12 Test-Fälle (verschiedene Ampelstufen & Vollständigkeitsgrade), 4 Schemata, 4 Templates und eine SQLite-Wiki-Datenbank:
```bash
.\.venv\Scripts\python main.py --seed
```

### 2. Demo-Modus starten (`--demo`)
Erzeugt die Seed-Datenbank und startet die Anwendung direkt im interaktiven GUI-Demo-Modus:
```bash
.\.venv\Scripts\python main.py --demo
```

### 3. Benutzerdefinierter Arbeitsbereich (`--workspace` / `-w`)
Gibt das Netzlaufwerk- oder Benutzerverzeichnis an:
```bash
.\.venv\Scripts\python main.py --workspace "N:\Support_Workspace\users\droesch"
```

---

## ⚙️ Umgebungsvariablen & Konfiguration

BookStack API Tokens können über Umgebungsvariablen bereitgestellt werden:

```env
ENV_BOOKSTACK_TOKEN_ID="your_bookstack_token_id"
ENV_BOOKSTACK_TOKEN_SECRET="your_bookstack_token_secret"
```

---

## ⌨️ Tastatur-Shortcuts

* `Strg+N`: Neuen Support-Fall / Vorgang anlegen
* `Strg+F`: Globale Suche & Praxissuche fokussieren
* `Strg+W`: BookStack Offline-Wiki Suche öffnen
* `Strg+E`: Export-Assistenten öffnen
* `Strg+S`: Aktiven Fall speichern
* `Strg+V`: Screenshot aus Zwischenablage im Fallordner speichern

*(Alle Hotkeys können im Profil-Einstellungen-Dialog benutzerdefiniert angepasst werden inkl. automatischer Konfliktprüfung).*

---

## 🧪 Tests ausführen

Das Projekt verfügt über **85 automatisierte Tests** in der pytest Testsuite:

```bash
.\.venv\Scripts\python -m pytest
```

Abgedeckte Testbereiche:
* `test_internal_cases.py`: Erfassung & Suche interner Vorgänge ohne Kundenelement.
* `test_priority_a.py`: Wiedervorlage-Fristen, Presets, Toast-Notifications & Notiz-Protokollierung.
* `test_priority_b.py`: Abwesenheiten, Quick-Filter Tokens & Hotkey-Konfliktprüfung.
* `test_priority_c.py`: Auswertungs-Dashboard KPIs & Druck-Export Formatierung.
* `test_priority_d.py`: E-Mail-Draft Import & GitLab/Jira Webhook Payloads.
* `test_zip_backup.py`: ZIP-Komplettsicherung & Entpackungs-Workflow.
* `test_storage.py`: Atomares Schreiben, Backups, Archivierung & Crash-Recovery.
* `test_scoring.py`: Urgency-Score Formel & Ampelschwellen.
* `test_search_parser.py`: Token-Parsing (`is:internal`, `vip:true`, `actor:dev`, `status:open`, `error:...`).
* `test_export_engine.py`: Jinja2 Rendering, In-Place Validierung & Force-Export.
* `test_p2p_sync.py`: Diff-Berechnung & selektiver P2P-Import.
* `test_ui_integration.py`: Integrationstest der GUI-Workflowskette.
