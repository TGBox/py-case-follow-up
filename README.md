# Support Follow-Up & Ticket-Cockpit (Desktop-App)

Eine leichtgewichtige Python-Desktop-Applikation (`customtkinter`) zur Erfassung, Nachverfolgung (Follow-up), Priorisierung und standardisierten Übergabe von Support-Fällen und Tickets an die Entwicklungs- und Technikabteilungen.

---

## 🌟 Features

* **3-Spalten Cockpit, Tab-View & Split-View:** Flexible UI-Layouts mit flüssiger CustomTkinter Flat-Optik und nativem Dark/Light Theme Support.
* **Dringlichkeits-Scoring & Ampelstufen:** Automatische Berechnung des Dringlichkeits-Scores (VIP-Status, Liegezeit-Staffelung, Rückruf-Deadlines) und Zuordnung zu `GRÜN`, `GELB` oder `ROT`.
* **Dynamische Formulare & In-App Baukasten:** Schemabasierte Erfassung von Fallparametern mit visueller Pflichtfeld-Hervorhebung und integriertem Baukasten-Editor.
* **Übergabe- & Export-Assistent:** Jinja2-basierter Export (z. B. GitLab Dev-Tickets, Cobra CRM Notizen) mit In-Place Pflichtfeld-Ergänzung und Force-Export-Option.
* **BookStack Wiki Offline-Suche:** SQLite3 FTS5 Volltextsuchindex für Offline-Zugriff auf Wiki-Dokumentationen mit BookStack REST-API Sync.
* **Multi-User P2P-Sync:** Dezentraler Abgleich der `cases.json` von Kollegen über Netzlaufwerke mit interaktivem Diff-Dialog (ohne automatische Zwangsüberschreibung).
* **Anhänge & Clipboard-Integration:** Automatische Fallordner-Erstellung und direktes Speichern von Screenshots per `Strg+V`.
* **Crash-Recovery & Datensicherheit:** Atomares Schreiben via `.tmp.json`, automatische tägliche Sicherungen (`backups/cases_YYYY-MM-DD.json`) und 30-Tage Auto-Archivierung.

---

## 🚀 Schnellstart & Installation

### Voraussetzungen
* Python 3.14+
* Windows / Linux / macOS

### Installation
```bash
# Virtuelle Umgebung erstellen
python -m venv .venv

# Abhängigkeiten installieren
.venv\Scripts\pip install -r requirements.txt
```

---

## 💻 CLI-Befehle

### 1. Test-Daten erzeugen (`--seed`)
Generiert automatisch 5 Kunden, 8 Test-Fälle (verschiedene Ampelstufen & Vollständigkeitsgrade), 3 Schemata, 2 Templates und eine SQLite-Wiki-Datenbank:
```bash
.venv\Scripts\python main.py --seed
```

### 2. Demo-Modus starten (`--demo`)
Erzeugt die Seed-Datenbank und startet die Anwendung direkt im interaktiven GUI-Demo-Modus:
```bash
.venv\Scripts\python main.py --demo
```

### 3. Benutzerdefinierter Arbeitsbereich (`--workspace` / `-w`)
Gibt das Netzlaufwerk- oder Benutzerverzeichnis an:
```bash
.venv\Scripts\python main.py --workspace "N:\Support_Workspace\users\droesch"
```

---

## ⚙️ Umgebungsvariablen & Konfiguration

BookStack API Tokens können über Umgebungsvariablen sicher bereitgestellt werden (keine Passwörter/Tokens im Quellcode):

```env
ENV_BOOKSTACK_TOKEN_ID="your_bookstack_token_id"
ENV_BOOKSTACK_TOKEN_SECRET="your_bookstack_token_secret"
```

---

## ⌨️ Tastatur-Shortcuts

* `Strg+N`: Neuen Support-Fall anlegen
* `Strg+F`: globale Suche & Praxissuche fokussieren
* `Strg+W`: BookStack Offline-Wiki Suche öffnen
* `Strg+E`: Export-Assistenten öffnen
* `Strg+S`: Aktiven Fall speichern
* `Strg+V`: Screenshot aus Zwischenablage im Fallordner speichern

---

## 🧪 Tests ausführen

Das Projekt verfügt über eine vollständige automatisierte Testsuite:

```bash
.venv\Scripts\pytest -v
```

Erreichte Testabdeckung:
* `test_storage.py`: Atomares Schreiben, Backups, Archivierung & Crash-Recovery.
* `test_scoring.py`: Urgency-Score Formel & Ampelschwellen.
* `test_search_parser.py`: Token-Parsing (`vip:true`, `actor:dev`, `status:open`, `error:...`) und Freitextsuche.
* `test_export_engine.py`: Jinja2 Rendering, In-Place Validierung & Force-Export.
* `test_seed.py`: Idempotentes Seeding und SQLite FTS5 Suche.
* `test_p2p_sync.py`: Diff-Berechnung & selektiver P2P-Import.
* `test_ui_integration.py`: Integrationstest der GUI-Service-Workflowskette.
