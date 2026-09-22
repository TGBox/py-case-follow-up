# Support Follow-Up & Ticket-Cockpit (Desktop-App)

Eine moderne Python-Desktop-Applikation (`customtkinter`) zur Erfassung, Nachverfolgung (Follow-up), Priorisierung und standardisierten Übergabe von Support-Fällen und internen Aufgaben an Hotline-, Entwicklungs- und Technikabteilungen.

---

## 🌟 Hauptfunktionen & Features

* **4 Flexible Ansichten (Layout-Modi):**
  * **Cockpit-Ansicht (`Strg+1`)**: Dreigeteiltes Haupt-Layout mit Fallliste, Falldetails/Formular, Notizbereich, Schnellaktionen und BookStack-Wiki. Beinhaltet das dedizierte **Übergabe-Dropdown** direkt in der Aktionsleiste neben dem `✓ Erledigt`-Button.
  * **6-Spalten Kanban-Board (`Strg+2`)**: Vollständige Übersicht nach den 4 Kern-Abteilungsbereichen und 2 Prozessspalten:
    1. 📞 **Hotline** (`hotline`)
    2. 🔧 **Technik** (`tech`)
    3. 💻 **Entwicklung** (`dev`)
    4. 👤 **Kunde** (`customer`)
    5. 🔔 **Wiedervorlage** (`followup`)
    6. ✓ **Erledigt** (`completed`)
    Jede Spalte lässt sich individuell einklappen und zeigt in der Kopfzeile einen Zähler der enthaltenen Fälle.
  * **Tabelle & Details (`Strg+3`)**: Tabellarische Umschalt-Matrix für schnelle Übersicht, Filterung und Sortierung großer Fallmengen.
  * **Auswertungen & Kennzahlen (`Strg+4`)**: Vollständiges Statistik- & KPI-Dashboard.

* **🤝 Gezielte Zuständigkeits-Übergabe & Abwesenheitswarnung:**
  * **Übergabe-Dropdown**: Befindet sich in der unteren Aktionsleiste direkt neben dem `✓ Erledigt`-Button im Cockpit.
  * Auswahl der 4 Zielbereiche: **Hotline**, **Technik**, **Entwicklung** und **Kunde**.
  * Öffnet direkt den Übergabedialog mit vorausgewählter Zielabteilung und springt sofort wieder auf die Beschriftung *"Übergabe"* zurück.
  * **Mitarbeiter-Abwesenheitswarnung**: Warnt visuell sofort, wenn ein zugewiesener Kollege als abwesend (Urlaub/Krankheit) vermerkt ist.

* **🎨 Persönliche Mitarbeiter-Farbmarkierung & Kompaktes Timeline-Design:**
  * **Persönliche Farbmarkierung**: Im Benutzerprofil (`⚙ Profil & Einstellungen` -> Reiter `👤 Benutzerprofil`) kann jeder Mitarbeiter eine persönliche Farbe wählen (Presets oder Farbwähler).
  * **Dezente 10x10 Farbkacheln**: Bei aktivierter Markierung erhalten eigene Fälle und Einträge eine dezente, schwarz umrandete Kachel in der Fallliste, auf Kanban-Karten und in Zeitleisten-Einträgen.
  * **Kompaktes Timeline-Layout**:
    * *Links*: Art der Notiz (z. B. `E-Mail`, `Telefon`, `Interner Vermerk`) und direkt darunter der Notizinhalt ohne Leerzeilen.
    * *Rechts*: Datum (`TT.MM.JJJJ`), Uhrzeit (`HH:MM:SS Uhr`) direkt unter dem Datum und darunter der Name des Bearbeiters mit Farbkachel (ohne Personen-Icon).

* **📤 Konsolidierter Dialog „Export & Übergabe“ (`ExportDialog` / `Strg+E`):**
  * Ersetzt separate Export- und Druckoptionen durch einen gemeinsamen, strukturierten 2-Reiter-Dialog:
    * **Tab 1: Export & Vorlagen (Standard)**: Template-basierter Export (Markdown, HTML, Text, XML) für GitLab, Jira, E-Mail oder Redmine.
    * **Tab 2: Drucken & Akte**: Selektiver Fallakten-Druck mit Checkboxen zum Abwählen einzelner Notizen, HTML-Generierung und Systemdrucker-/PDF-Aufruf.

* **🖨 Komprimierter Fallbericht für PDF-Export & DIN A4-Druck:**
  * Standardfälle passen sauber auf **eine einzige DIN A4-Seite** (`@page { size: A4 portrait; margin: 8mm 10mm; }`).
  * **2-Spalten-Layout (`top-grid`)**: Fall-Metadaten (links) und Kunden-/Praxisdaten (rechts) stehen platzsparend nebeneinander.
  * **2-spaltiges Formular-Grid (`fields-grid`)**: Kurze Formularfelder teilen sich zwei Spalten; längere Antworten spannen automatisch über die volle Breite.
  * **Kompakte Zeitleiste**: Flache Boxen mit minimalem Rand verhindern unnötigen Weißraum.
  * Umbruchschutz (`page-break-inside: avoid;`) auf Tabellen, Kacheln und Bildern.

* **🤖 Hybride KI & Ollama LLM-Integration:**
  * **Lokale LLM-Anbindung:** REST-API Integration mit lokalen Ollama-Modellen (`qwen2.5`, `qwen3.5:9b`, `llama3`, `pvs-support`).
  * **In-App Ollama Server-Steuerung:** Starten (`▶ Ollama Server Starten`) und Beenden (`🛑 Server Beenden`) laufender Ollama-Prozesse direkt aus den Profileinstellungen.
  * **⚡ PVS-Support Modell-Erstellung:** Ein-Klick-Generierung eines spezialisierten `pvs-support` Modells aus dem integrierten `Modelfile`.
  * **🎚 Globaler KI-Schalter & VRAM-Entladung:** Automatisches Entladen des Modells aus dem VRAM beim Ausschalten.
  * **🚦 Präzise Status-Farbcodierung:** Badges (`🔴 Rot` Offline | `⚪ Grau` Inaktiv | `🔵 Blau` Standby | `🟢 Grün` Aktiv im RAM).
  * **⚡ Priorisierte Sonderanweisung & Hierarchische Prompts:** Spontane Direktiven mit höchster Priorität über Basis- und Praxisregeln.
  * **Regelbasierter Zero-Token NLP Fallback:** Robuster Fallback-Modus bei Offline-Ollama.

* **📂 Dynamische Mehrfach-Eingabemasken (Wiederholbare Blöcke / Zuzahlungsnachforderungen):**
  * Wiederholbare Karten-Container in Formularen (z. B. *Zuzahlungsnachforderung & Abrechnungskorrektur*).
  * Beliebig viele Anforderungen per Knopfdruck (`➕ Weitere Datei / Korrektur-Anforderung anfordern`) hinzufügen und verwalten.

* **Auswertungs- & KPI-Dashboard (`Auswertungen & Kennzahlen`):**
  * **6 Top-KPI-Karten**: *Fälle Gesamt, Offene Fälle, Erledigt %, Überfällige Wiedervorlagen, Ø Bearbeitungszeit, VIP-Kundenquote*.
  * **2-Spalten Layout**: Dringlichkeits-Scoring Ampel (`Rot` / `Gelb` / `Grün`), Formular-/Schema-Verteilung, Top 5 Praxen mit VIP-Badge (`★ VIP`), Bearbeiter-Auslastung und Abteilungs-Zuständigkeiten.
  * **📋 Statistik-Bericht kopieren**: Kopiert strukturierte Markdown-Zusammenfassungen in die Zwischenablage.

* **🏢 Interne Vorgänge & Aufgaben (ohne Kunde):** Erfassung rein interner Aufgaben (Systemwartung, Notizen) ohne Kundenelement mit automatischer Schema-Umschaltung und blauem `🏢 INTERN`-Badge.

* **🐍 Cobra CRM Praxen-Import:** Assistent zum Importieren von Kundendatenbanken aus Cobra CRM Exporte im Format CSV, TXT oder JSON mit automatischer Spaltenerkennung.

* **📝 Textbausteine & Snippet-Manager:** Zentrale Verwaltung von Bausteinen mit Kategorien und Tags sowie Schnellauswahl-Dialog (`SnippetPickerDialog`, `Strg+M`) zum direkten Einfügen in Fallnotizen.

* **⌨ Einstellbare Keyboard-Makros & Shortcuts:**
  * Beliebige globale und benutzerdefinierte Tastenkürzel sowie Textbaustein-Makros.
  * Interaktive Tasten-Erfassung und automatische Konfliktprüfung in den Profileinstellungen (`⚙ Profil & Einstellungen` -> Reiter `🧩 Sonstiges`).

* **🔔 Live-Wiedervorlagen & Background Toast-Popups:**
  * Glocken-Badge (`🔔 3`) in der Kopfzeile mit Live-Zähler fälliger Fristen.
  * Periodische Fristenprüfung im Hintergrund mit Toast-Notifications am Bildschirmrand und Wiedervorlagen-Flyout.

* **✉ E-Mail-Entwurf & 📅 Kalender-Export (.ics) & Outlook Transfer:**
  * Support-Mails mit KI-Entwürfen (`EmailDraftDialog`). Direkte Übergabe an Microsoft Outlook oder System-Mailclient.
  * iCalendar (`.ics`) Fristtermine für MS Outlook, Thunderbird & Apple Calendar.

* **⏱ Datumswahl mit Uhrzeit & Stepper-Navigation:**
  * Kalender-Widget mit Datums- und Uhrzeitwahl (HH:MM).
  * Zeit-Stepper (`▲` / `▼`) für 5-Minuten-Intervalle und praxisnahe Kernarbeitszeiten (07:00–20:00 Uhr).

* **🛠 Formular-Baukasten & Schema-Konverter:** In-App Formular-Builder zur Erstellung eigener Erfassungsmasken sowie Schema-Umwandler für bestehende Fälle.

* **📂 Dateianhängs-Vorschau & OS-Integration:**
  * Live-Text- und Bild-Vorschau für Anhänge (PNG, JPG, Logfiles, JSON).
  * Direktes Öffnen von Anhängen im OS-Standardprogramm und Speichern von Screenshots per `Strg+V`.

* **📦 Komplett-ZIP Backup & Import/Export:** Export und Wiederherstellung des gesamten Datenbestands als zeitgestempeltes ZIP-Archiv im Einstellungsdialog (`⚙ Profil & Einstellungen` -> Reiter `📁 Speicherort & Datenexport`).

* **🔌 E-Mail-Import (IMAP) & REST Webhooks:** Automatische Fallentwürfe aus Support-Postfächern sowie Webhooks für GitLab/Jira Issue Tracker.

* **📚 BookStack Wiki Offline-Suche:** SQLite3 FTS5 Volltextsuchindex für Offline-Zugriff auf Wiki-Dokumentationen mit BookStack REST-API Sync (Server-Konfiguration unter `⚙ Profil & Einstellungen` -> Reiter `🧩 Sonstiges`).

* **⚙ Kompakter 4-Reiter Einstellungsdialog (`ProfileSettingsDialog` / `Strg+P`):**
  * **1. 👤 Benutzerprofil**: Kompakte 2-Spalten-Ansicht für persönliche Kontaktdaten (Name, Abteilung, Durchwahl, Mobil), E-Mail-Signatur, P2P-Sync und Farbmarkierung (links) sowie Erscheinungsbild (Theme, Schriftgröße, Spaltenbreiten-Reset rechts).
  * **2. 📁 Speicherort & Datenexport**: 2-Spalten-Layout für Arbeitsverzeichnis, Datei-Pfade und automatische Grandfather-Father-Son Backup-Aufbewahrung (links) sowie Komplett-Datensicherung per ZIP-Export & -Import (rechts).
  * **3. 🤖 KI & NLP**: Ollama Server-Steuerung (Start/Stopp), Modell-Verwaltung, Status-Farbcodes und hierarchische Prompt-Regeln.
  * **4. 🧩 Sonstiges**: 2-Spalten-Layout für BookStack Wiki-Serverkonfiguration & Synchronisation, Prioritäts-Scoring (links) sowie App-Shortcuts und Textbaustein-Makros mit Live-Recorder (rechts).
  * Durch intelligente 2-Spalten-Grids und automatisches Ausblenden der Scrollleisten (`enable_auto_hiding_scrollbar`) sind alle Dialogreiter ohne vertikales Scrollen direkt vollständig sichtbar.

* **🔄 Multi-User P2P-Sync:** Dezentraler Abgleich der `cases.json` von Kollegen über Netzlaufwerke mit interaktivem Diff-Dialog.

* **🌍 Dreisprachigkeit (i18n):** Vollständige Lokalisierung in Deutsch, Englisch und Schwedisch mit 100% Leaf-Key-Parität.

---

## 🚀 Schnellstart & Installation

### Voraussetzungen

* Python 3.14+ (empfohlen via `uv`)
* Windows / Linux / macOS
* *(Optional)* Lokaler [Ollama](https://ollama.com/) Server für KI-Unterstützung

### Installation & Start mit `uv`

```bash
# Virtuelle Umgebung erstellen und Abhängigkeiten synchronisieren
uv sync

# Anwendung starten
uv run main.py
```

### KI-Modell mit Ollama einrichten (Optional)

```bash
# Eigenes PVS-Support Modell aus Modelfile erstellen
ollama create pvs-support -f ollama/Modelfile

# Oder Standard-Modell herunterladen
ollama pull qwen2.5
```

---

## 🔨 PyInstaller Executable (.exe) & Git Hooks

### 1. Eigenständige Windows `.exe` generieren

Die Anwendung kann über PyInstaller und die Konfiguration in `py-case-follow-up.spec` zu einer portablen Windows-Executable gebaut werden:

```bash
uv run pyinstaller py-case-follow-up.spec
```

Das fertige Executable wird im Verzeichnis `dist/py-case-follow-up.exe` erzeugt.

### 2. Automatischer Git Pre-Push Hook

Das Repository enthält einen `pre-push` Hook in `.githooks/pre-push`, der vor jedem `git push`
dieselben Prüfungen fährt wie die GitHub Actions — in der Reihenfolge ihrer Laufzeit, damit ein
Lint-Verstoß in Sekunden auffällt statt erst nach einem kompletten Build:

1. Linting (`uv run ruff check src main.py tests`).
2. Statische Typenprüfung (`uvx pyright src`).
3. Baut eine frische `.exe` anhand des Spec-Files (muss vor den Tests laufen: `dist/` ist
   gitignored, und `test_pyinstaller_bundle.py` überspringt sich ohne gebaute Exe selbst).
4. Die gesamte Testsuite (`uv run pytest --no-cov`).
5. Den Push abbricht, falls einer der vier Schritte fehlschlägt.

Dass Hook und CI nicht auseinanderlaufen, prüft `tests/test_git_hooks.py` gegen
`.github/workflows/tests.yml`.

Um den Hook für Ihr lokales Git-Repository zu aktivieren:

```bash
git config core.hooksPath .githooks
```

---

## 💻 CLI-Befehle

### 1. Test-Daten erzeugen (`--seed`)

Generiert automatisch Praxen, Testfälle, Schemata, Vorlagen und eine SQLite-Wiki-Datenbank:

```bash
uv run main.py --seed
```

### 2. Demo-Modus starten (`--demo`)

Erzeugt die Seed-Datenbank und startet die Anwendung direkt im interaktiven GUI-Demo-Modus:

```bash
uv run main.py --demo
```

### 3. Benutzerdefinierter Arbeitsbereich (`--workspace` / `-w`)

Gibt das Netzlaufwerk- oder Benutzerverzeichnis an:

```bash
uv run main.py --workspace "D:\Support_Workspace"
```

---

## ⌨ Tastatur-Shortcuts

| Tastenkürzel | Funktion |
| :--- | :--- |
| `Strg + N` | Neuen Support-Fall / Vorgang anlegen |
| `Strg + S` | Aktiven Fall speichern |
| `Strg + Umschalt + A` | Fall erledigen / archivieren |
| `Strg + E` | Dialog „Export & Übergabe“ öffnen |
| `Strg + F` | Fallliste- & Kundensuche fokussieren |
| `Strg + M` | Textbaustein-Picker (Snippets) öffnen |
| `Strg + W` | BookStack Offline-Wiki Suche öffnen |
| `Strg + V` | Screenshot aus Zwischenablage im Fall speichern |
| `Strg + 1` | Cockpit-Ansicht (Hauptlayout) |
| `Strg + 2` | 6-Spalten Kanban-Board |
| `Strg + 3` | Tabelle & Details (Sortier-Matrix) |
| `Strg + 4` | Auswertungen & Kennzahlen Dashboard |
| `Strg + P` | Einstellungen öffnen |
| `Strg + T` | Theme umschalten (Hell / Dunkel) |
| `F1` | Handbuch & Hilfe öffnen |

---

## 🧪 Tests ausführen

Das Projekt verfügt über **über 840 automatisierte Tests** in der pytest-Testsuite:

```bash
uv run pytest
```

Abgedeckte Testbereiche:

* `test_git_hooks.py`: Validierung des Git Pre-Push Hooks und der Build-Reihenfolge vor Tests.
* `test_pyinstaller_bundle.py`: Verifikation des PyInstaller Spec-Files und der gebündelten Lokalisierungsdateien in der generierten `.exe`.
* `test_case_print_export_options.py` & `test_case_print_dialog.py`: Komprimierter DIN A4 Fallbericht (`generate_case_report_html`), 2-Spalten Top-Grid, 2-Spalten Formular-Raster und PDF-Druck.
* `test_color_marker_and_timeline_layout.py`: Persönliche Farbmarkierung im Profil, Modellpersistenz, dezente Farbkacheln und Timeline-Kartenlayout.
* `test_translation_parity_and_quality.py` & `test_i18n_translation_parity_and_service.py`: 100% Parität aller Übersetzungsschlüssel über Deutsch, Englisch und Schwedisch hinweg.
* `test_profile_and_ai_management.py`: Ollama Server Process Control (Start/Stop), Modell-Downloads, VRAM-Entladung & asynchroner Status-Scan.
* `test_ai_text_generation_validation.py`: LLM-Generierung, Prompt-Hierarchien, Sonderanweisungen, Fall-ID-Ausschluss und NLP-Fallbacks.
* `test_zuzahlungsnachforderung_multi_requests.py`: Dynamische wiederholbare Karten-Container für Multi-Datei-Anforderungen.
* `test_analytics_metrics.py`: Auswertungs-Dashboard KPIs, Bearbeitungszeiten & Markdown-Berichtsexport.
* `test_keyboard_macros.py`: Keyboard-Makros & Hotkey-Konfliktprüfungen.
* `test_internal_cases.py`: Erfassung & Suche interner Vorgänge ohne Kundenelement.
* `test_cobra_import.py`: Cobra CRM Kunden- & Praxenimport mit Spaltenerkennung.
* `test_snippets.py`: Textbausteine-Verwaltung & Einfüge-Mechanik.
* `test_email_and_calendar_dialog_separation.py`: Eigenständige Dialoge für E-Mail, Outlook-Transfer & .ics Kalenderexport.
* `test_followup_and_relative_dates.py`: Fristen, Relativdaten & Toast-Benachrichtigungen.
* `test_colleague_absence.py`: Abwesenheiten & Vertretungswarnungen.
* `test_storage.py` & `test_storage_robustness_deep.py`: Atomares Schreiben, Backups, Archivierung & Crash-Recovery.
* `test_scoring.py`: Urgency-Score Formel & Ampelschwellen.
* `test_search_parser.py` & `test_quick_filter_search.py`: Token-Parsing & Schnellauswahl.
* `test_export_engine.py`: Jinja2 Rendering, In-Place Validierung & Force-Export.
* `test_p2p_sync.py` & `test_p2p_advanced.py`: Diff-Berechnung & selektiver P2P-Import.
* `test_ui_integration.py` & `test_ui_workflow_chains.py`: E2E-Integrationstests aller GUI-Workflows.
