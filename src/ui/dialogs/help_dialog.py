import customtkinter as ctk
from constants import DIALOG_DIMENSIONS, DIALOG_TITLES


HELP_ARTICLES = [
    {
        "id": "basics",
        "title": "🚀 Grundlagen & Layouts",
        "category": "Grundlagen",
        "content": """
### 🚀 Grundlagen der Benutzeroberfläche

Das **Support-Cockpit** unterstützt Sie bei der effizienten Nachverfolgung, Kategorisierung und Priorisierung von Support-Fällen und Praxisanfragen.

#### Die 3 Ansichten (Layout-Modi)
In der oberen Menüleiste können Sie jederzeit zwischen 3 Ansichten umschalten:

1. **Cockpit-Ansicht (Standard)**: 
   - Dreigeteilte Ansicht für maximale Übersicht.
   - **Links**: Filterbare Fall-Liste sortiert nach Dringlichkeit (Score).
   - **Mitte**: Hauptdaten des aktiven Falls (Kunde, Status, Dringlichkeit, dynamische Formularfelder, Zeitleiste & Anhänge).
   - **Rechts**: Integriertes BookStack Wiki zur schnellen Lösungssuche.

2. **Tab-Ansicht (Reiter-Modus)**:
   - Übersichtliche Reiter-Navigation für kompakte Bildschirme.
   - Schnelles Umschalten zwischen Fallübersicht, Falldetails und Historie.

3. **Split-Ansicht (2-Spalten-Modus)**:
   - Links Fall-Liste, rechts Falldetailansicht für fokussiertes Arbeiten ohne Wiki-Seitenleiste.

---

#### 🔍 Such- & Filterfunktion
- Nutzen Sie das Suchfeld oben in der Fallliste, um Fälle nach **Fall-ID**, **Praxisname**, **Betreff** oder **Tags** zu filtern.
- Tastenkürzel zum Fokussieren der Suche: `Strg+F`
"""
    },
    {
        "id": "ui_customization",
        "title": "📅 Datumsformate, Kalender & Spaltenbreiten",
        "category": "Benutzeroberfläche",
        "content": """
### 📅 Datumsformatierung, Kalender-Picker & Spaltenbreiten

#### 1. 📅 Deutsche Datumsformatierung
- Alle Datumsangaben im Support-Cockpit (Fristen, Rückrufe, Wiedervorlagen, Zeitleiste) werden einheitlich im deutschen Format (`DD.MM.YYYY` bzw. `DD.MM.YYYY HH:MM`) dargestellt.

#### 2. 🗓 Interaktiver Kalender-Picker
- Bei allen Datumseingaben (z. B. Wiedervorlage einplanen, Rückruf-Deadline festlegen) steht ein interaktiver Kalender-Dialog zur Verfügung.
- Klicken Sie neben dem Eingabefeld auf **📅 Kalender**, um den Monatskalender zu öffnen und das gewünschte Datum bequem per Klick auszuwählen.
- Schnellauswahl-Tasten für *Heute*, *+ 1 Tag* und *+ 1 Woche* beschleunigen die Eingabe.

#### 3. 📐 Individuelle & dauerhafte Spaltenbreiten
- Über den Button **📐 Spalten** in der oberen Menüleiste können Sie die Breiten der einzelnen Spalten im Cockpit (Fallliste, Details/Formular, Zeitleiste) sowie im Kanban-Board frei anpassen.
- Ihre gewählten Breiten werden automatisch in der Benutzerkonfiguration (`user_config.json`) gespeichert und bleiben beim Neustart der Anwendung erhalten.
"""
    },
    {
        "id": "praxis",
        "title": "🏥 Praxis- & Kundenverwaltung",
        "category": "Kunden",
        "content": """
### 🏥 Praxis- & Kundenverwaltung

Jeder Support-Fall ist einer bestimmten Praxis (Kunde) zugeordnet.

#### 1. Praxis-Verwaltung öffnen
- Klicken Sie in der oberen Menüleiste auf **🏥 Praxen**.
- Hier sehen Sie eine vollständige Liste aller registrierten Praxen mit Kundennummer, Praxisname, Hauptansprechpartner, E-Mail und Telefon.

#### 2. Neue Praxis anlegen
- Öffnen Sie **🏥 Praxen** -> **+ Neue Praxis anlegen**.
- Oder direkt beim Erstellen eines neuen Falls im Dialog **+ Neuer Fall**: Klicken Sie auf den Button **+ Neue Praxis** neben der Praxisauswahl. Die neue Praxis steht sofort zur Auswahl bereit!

#### 3. Ansprechpartner (Kontakte) verwalten
- In den Praxis-Details können Sie mehrere Ansprechpartner (z.B. Praxisinhaber, IT-Beauftragter, MFAs) hinterlegen.
"""
    },
    {
        "id": "scoring",
        "title": "📊 Fall-Scoring & Priorisierung",
        "category": "Workflow",
        "content": """
### 📊 Automatisches Dringlichkeits-Scoring

Das Support-Cockpit berechnet für jeden offenen Fall automatisch einen **Dringlichkeits-Score** (Punkte), damit Sie dringende Fälle sofort erkennen.

#### Wie setzt sich der Score zusammen?
- **Priorität**: Critical (60 Pkt), High (40 Pkt), Medium (20 Pkt), Low (10 Pkt).
- **VIP-Status**: VIP-Praxen erhalten einen Bonus von +30 Punkten.
- **Wartezeit (Liegezeit)**: Je länger ein Fall offen ist, desto höher steigt der Score (+2 Pkt / Tag).
- **Inaktivität**: Fälle ohne Update in den letzten 48 Stunden erhalten zusätzliche Punkte.
- **Workflow-Status**: In Bearbeitung (+10 Pkt), Warten auf Kunden (+0 Pkt), Vorort-Termin nötig (+20 Pkt).

#### Automatische Stundenneuberechnung
Ein Hintergrund-Timer aktualisiert die Scores aller offenen Fälle stündlich.
"""
    },
    {
        "id": "schemas",
        "title": "📄 Formular-Baukasten (Schemas)",
        "category": "Formulare",
        "content": """
### 📄 Dynamische Formular-Baukästen

Unterschiedliche Support-Typen (z.B. Hardware-Tausch, Abrechnungsfrage, Schnittstellen-Problem) erfordern unterschiedliche Informationen.

#### Eigene Formulare erstellen & anpassen
1. Klicken Sie in der Menüleiste auf **🛠 Formular-Baukasten**.
2. Erstellen Sie ein neues Schema (z.B. *"PVS-Schnittstelle"*) oder bearbeiten Sie ein bestehendes.
3. Fügen Sie eigene Felder hinzu:
   - **Text-Felder** (z.B. Fehlermeldung)
   - **Zahlen-Felder** (z.B. Port-Nummer)
   - **Ja/Nein Kontrollkästchen** (z.B. Dienst neu gestartet)
   - **Drop-Down Auswahlfelder** (z.B. PVS-Hersteller)
4. Legen Sie Pflichtfelder fest (*).

Beim Ausfüllen eines Falls im Cockpit passt sich das Formular automatisch an das gewählte Schema an!
"""
    },
    {
        "id": "export",
        "title": "📤 Export-Engine & Vorlagen",
        "category": "Export",
        "content": """
### 📤 Übergabe- & Export-Engine

Generieren Sie mit einem Klick fertige Übergabeprotokolle, E-Mails oder Dokumentationen für Kollegen oder Ticketsysteme.

#### Fall exportieren
1. Wählen Sie den gewünschten Fall aus und klicken Sie auf **📤 Export (Strg+E)**.
2. Wählen Sie eine Vorlage (z.B. *"Standard Übergabe"*, *"Kunden-Zusammenfassung"*, *"Entwickler-Bugreport"*).
3. Wählen Sie das Ausgabeformat:
   - **Markdown** (ideal für Wikis / Jira / GitHub)
   - **HTML / Text** (ideal für E-Mails)
   - **PDF** (für Ausdruck / Archivierung)
4. Nutzen Sie den Button **📋 In Zwischenablage kopieren** oder **💾 Als Datei speichern**.
"""
    },
    {
        "id": "wiki",
        "title": "📚 BookStack Wiki Integration",
        "category": "Wiki",
        "content": """
### 📚 BookStack Wiki Integration

Das Support-Cockpit ist direkt mit Ihrem BookStack Wiki verbunden, um Lösungsartikel sofort griffbereit zu haben.

#### Funktionen
- **Automatische Suche**: Tippen Sie Suchbegriffe in die Wiki-Suchleiste ein, um passende Artikel zu finden.
- **Artikel-Vorschau**: Artikel-Inhalte werden direkt im rechten Cockpit-Panel gerendert.
- **In BookStack öffnen**: Öffnen Sie Artikel mit einem Klick in Ihrem Standard-Browser.
- **Fall-Verknüpfung**: Verknüpfen Sie gelöste Fälle mit dem entsprechenden Wiki-Artikel.
- **Konfiguration**: Tragen Sie Ihre BookStack URL und API-Tokens in **Profil & Einstellungen** (`👤`) ein.
"""
    },
    {
        "id": "p2p",
        "title": "🔄 Peer-to-Peer Sync (Kollegen)",
        "category": "Sync",
        "content": """
### 🔄 Peer-to-Peer (P2P) Synchronisation

Arbeiten Sie mit Kollegen ohne zentralen Server zusammen! Die P2P-Sync ermöglicht das Abgleichen von Fällen direkt zwischen lokalen Arbeitsplätzen.

#### Ablauf
1. Klicken Sie auf **🔄 P2P-Sync**.
2. Wählen Sie den Kollegen aus, mit dem Sie synchronisieren möchten.
3. Das System vergleicht den Versionsstand der Fälle.
4. Im **Diff-Dialog** sehen Sie Konflikte oder neu hinzugefügte Fälle und können Änderungen sicher zusammenführen.
"""
    },
    {
        "id": "shortcuts",
        "title": "⌨ Tastenkürzel & Hotkeys",
        "category": "Tastenkürzel",
        "content": """
### ⌨ Tastenkürzel (Shortcuts)

Arbeiten Sie noch schneller mit folgenden Hotkeys:

| Aktion | Standard-Hotkey |
| :--- | :--- |
| **Neuer Fall** | `Strg + N` |
| **Fall speichern** | `Strg + S` |
| **Fall archivieren** | `Strg + Umschalt + A` |
| **Fall exportieren** | `Strg + E` |
| **Einstellungen öffnen** | `Strg + P` |
| **Snippet-Picker öffnen** | `Strg + M` |
| **Wiki-Suche fokussieren** | `Strg + W` |
| **Kundensuche fokussieren** | `Strg + F` |
| **Cockpit-Ansicht** | `Strg + 1` |
| **Kanban-Board-Ansicht** | `Strg + 2` |
| **Tabellen-Ansicht** | `Strg + 3` |
| **Theme umschalten** | `Strg + T` |
| **Hilfe-Dialog** | `F1` |
| **Textbaustein-Makros** | e.g. `Strg + Alt + 1` |

*Hinweis: Alle Tastenkürzel und Textbaustein-Makros können in den Einstellungen (`⚙ Profil & Einstellungen` -> `⌨ Tastenkürzel & Scoring`) frei angepasst und per Taste erfasst werden.*
"""
    },
    {
        "id": "storage_paths",
        "title": "📁 Speicherorte, Datenordner & Exe-Betrieb",
        "category": "Konfiguration",
        "content": """
### 📁 Speicherorte, Datenstruktur & Exe-Betrieb

Das **Support-Cockpit** speichert Arbeitsdaten getrennt von Programmdateien. Dies ermöglicht die sichere Ausführung aus einer geschützten Einzel-Datei (PyInstaller `.exe`) und verhindert das Versionieren echter Kundendaten in Git-Repositories.

#### 1. Datenordner & Pfade anpassen
- Öffnen Sie **Profil & Einstellungen** (`👤 [Ihr Name]`) -> Reiter **📁 Speicherort & Pfade**.
- **Haupt-Datenordner**: Klicken Sie auf **📁 Ordner wählen**, um Ihren Arbeitsbereich (z. B. auf `D:\\SupportDaten` oder ein Netzwerklaufwerk) frei festzulegen.
- **Einzelne Dateipfade**: Sie können bei Bedarf einzelne Dateien (`cases.json`, `customers.json`, `wiki_index.sqlite`) an abweichende Orte koppeln oder über **🔄 Einzelpfade auf Standard zurücksetzen** zum Standard zurückkehren.

#### 2. Verhalten beim Ausführen als Einzeldatei (Exe)
- Wenn die Anwendung als kompilierte `.exe` ausgeführt wird, werden keine Ordner am Ausführungsort (z. B. `C:\\Program Files\\`) erstellt.
- Stattdessen wird die zentrale Benutzerkonfiguration in Ihrem Benutzerprofil gespeichert:
  - Windows: `%APPDATA%\\SupportCockpit\\user_config.json`
  - Linux/Mac: `~/.config/SupportCockpit/user_config.json`
- Fehlt die Konfiguration, wird als Standard-Datenordner automatisch `Dokumente\\SupportCockpitData` verwendet.

#### 3. Beispieldateien & Automatische Initialisierung
- **Vorlagen im Repository (`data_examples/`)**: Werden beim ersten Start Vorlagendateien aus `data_examples/` in Ihren gewählten Datenordner kopiert.
- **Leere Dateien**: Sollten weder Daten noch Vorlagen existieren, erzeugt die Anwendung automatisch neue, leere Datendateien, damit der Betrieb reibungslos startet.
"""
    },
    {
        "id": "template_editor",
        "title": "📄 Export-Vorlagen-Editor",
        "category": "Export",
        "content": """
### 📄 Eigene Export-Vorlagen erstellen & anpassen

Im **Export-Vorlagen-Editor** können Sie bestehende Übergabevorlagen anpassen oder völlig neue Exportformate definieren.

#### Vorlagen-Manager öffnen
- Klicken Sie in der oberen Menüleiste auf **📄 Vorlagen** oder im Export-Dialog (`Strg+E`) auf **🛠 Vorlagen verwalten**.

#### Vorlage konfigurieren
1. **Name & ID**: Vergeben Sie eine eindeutige ID und einen lesbaren Anzeigenamen.
2. **Ziel-Aktion**: Wählen Sie zwischen Zwischenablage-Text und Datei-Export.
3. **Zugeordnete Formulare**: Aktivieren Sie die Häkchen bei den Formular-Schemas, für die die Vorlage angeboten werden soll.
4. **Erforderliche Pflichtfelder**: Legen Sie fest, welche Felder im Fall ausgefüllt sein müssen, bevor exportiert werden darf.
5. **Jinja2-Template**: Schreiben Sie den Vorlagentext in Markdown/HTML. Nutzen Sie den Button **👁 Live-Vorschau rendern**, um das Ergebnis sofort zu prüfen!
"""
    },
    {
        "id": "handover_followup",
        "title": "🔔 Zuständigkeitswechsel & Wiedervorlage",
        "category": "Workflow",
        "content": """
### 🔔 Zuständigkeitswechsel & Wiedervorlage

Behalten Sie stets den Überblick darüber, wann ein Fall an wen übergeben wurde und wann Sie beim Kollegen nachfragen müssen.

#### 1. Automatische Übergabe-Protokollierung
- Sobald Sie den **Zuständig (Akteur)** eines Falls ändern (z. B. von *Support* auf *Entwicklung*), erstellt das System automatisch einen präzisen Eintrag in der **Zeitleiste**:
  - *Zeitstempel & Urheber*
  - *Statusänderung: ZUSTÄNDIGKEIT: Support -> Entwicklung*
  - *Hinweis: Zuständigkeit übergeben an: Entwicklung (vorher: Support)*

#### 2. Wiedervorlage & Nachfrage-Erinnerung einplanen
- Beim Wechsel der Zuständigkeit öffnet sich automatisch der Dialog **🔔 Wiedervorlage einplanen**.
- Oder klicken Sie in den Falldetails jederzeit auf den Button **🔔 Wiedervorlage**.
- Wählen Sie ein Schnell-Preset (`+ 1 Tag`, `+ 2 Tage`, `+ 1 Woche`) oder ein freies Datum mit Notiz.
- Fälle mit aktiver Wiedervorlage werden in der Fallliste 3-zeilig hervorgehoben (Nachfragen am, Datum mit Relativangabe `(morgen)` / `(heute)` / `(in X Tagen)`, Uhrzeit).
"""
    },
    {
        "id": "email_calendar_outlook",
        "title": "✉ E-Mail, Kalender (.ics) & Outlook",
        "category": "Kommunikation",
        "content": """
### ✉ E-Mail-Verfassen, Kalender-Export & Microsoft Outlook Integration

Im Cockpit stehen Ihnen zwei getrennte Funktionen zur Verfügung:

#### 1. ✉ E-Mail verfassen
- Klicken Sie auf **✉ E-Mail**, um den E-Mail-Entwurf für den aktuellen Fall zu öffnen.
- Empfänger und Betreff sind anhand der Praxisdaten und des Themas vorausgefüllt.
- Über **🧩 Textbaustein** können Sie vorgefertigte Support-Vorlagen (z. B. TI-Entstörung, Abrechnungskorrektur) per Klick einfügen.
- **In Outlook übertragen**: Öffnet die E-Mail direkt in Microsoft Outlook mit allen Feldern.
- **In Standard-Mail-App öffnen**: Startet Ihren Standard-Mail-Client über das `mailto:`-Protokoll.

#### 2. 📅 Kalendereintrag erstellen (.ics)
- Klicken Sie auf **📅 Kalender**, um einen Kalendertermin für Wiedervorlagen oder Rückruf-Deadlines zu erzeugen.
- **Direkt im Kalender öffnen**: Erzeugt eine temporäre `.ics`-Datei und öffnet Ihren Kalender (Outlook / Thunderbird).
- **Als .ics Datei speichern...**: Speichert die Termindatei an einem beliebigen Ort.

#### 3. 📬 Outlook Add-in / Makro (E-Mails in Support-Cockpit übertragen)
- Mit dem integrierten Outlook-Makro können Sie empfangene Kundenmails direkt aus Outlook an das Support-Cockpit übergeben, um automatisch einen neuen Fall anzulegen oder eine Notiz zur Zeitleiste hinzuzufügen.
"""
    },
    {
        "id": "case_print_reporting",
        "title": "🖨 Fall-Druckansicht, PDF & Bilder",
        "category": "Export",
        "content": """
### 🖨 Fall-Druckansicht, PDF-Export & Bildanhänge

Erstellen Sie vollständige Aktenübersichten für die Archivierung oder Besprechungen.

#### 1. Druckdialog öffnen
- Klicken Sie im Cockpit auf **🖨 Drucken**.
- Wählen Sie aus, welche Bereiche enthalten sein sollen (Kundendaten, Formularfelder, Zeitleisteneinträge, Bilder).

#### 2. Bilder & Screenshots am Dokumentende
- Alle Bilddateien (`.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`) aus dem Fallordner werden automatisch am Ende der Seite eingebettet.
- Sie können die Screenshots durch einfaches Scrollen im Bericht sofort betrachten und mit ausdrucken.

#### 3. Export-Möglichkeiten
- **🖨 Im Browser öffnen & Drucken**: Öffnet die Seite im Standardbrowser und startet automatisch den Druck- bzw. PDF-Exportdialog.
- **💾 Als HTML/PDF-Bericht speichern...**: Speichert die vollständige, eigenständige HTML-Akte auf Ihrer Festplatte.
"""
    },
    {
        "id": "ai_ollama_management",
        "title": "🤖 KI-Assistent, Ollama Server & Modell-Verwaltung",
        "category": "KI & Ollama",
        "content": """
### 🤖 Lokaler KI-Assistent & Ollama Server-Steuerung

Das Support-Cockpit bietet eine vollständige, datenschutzkonforme KI-Unterstützung auf Basis lokaler Open-Source Sprachmodelle (z. B. Ollama mit Qwen2.5 / Llama3). Sämtliche Anfragen bleiben 100% auf Ihrem PC!

#### 1. ⚙ Ollama Server-Steuerung (Start & Beenden aus der App)
Unter **Profil & Einstellungen** (`👤`) -> Reiter **🤖 KI & NLP** können Sie den Ollama-Server direkt aus der Anwendung bedienen:
- **`▶ Ollama Server Starten`**: Startet den Ollama-Hintergrundprozess (`ollama serve`), ohne dass Sie ein Terminal öffnen müssen.
- **`🛑 Server Beenden`**: Beendet den Ollama-Serverprozess sauber und gibt belegten Speicherplatz sofort frei.
- **`🌐 Download-Links`**: Sollte Ollama noch nicht installiert sein oder fehlen lokale Modelle, bietet die App direkte Download-Links zu `ollama.com`, `qwen2.5` und `llama3`.

#### 2. ⚡ PVS-Support Modell per Klick erstellen
- Über den Button **`⚡ PVS-Support Modell aus Modelfile erstellen`** wird automatisch ein spezialisiertes KI-Modell (`pvs-support`) aus dem hinterlegten `Modelfile` generiert.
- Dieses Modell ist speziell auf deutschen IT-Support im Gesundheitswesen (PVS, TI-Konnektoren, GKV-Abrechnung, KV-SafeNet) vorbereitet.

#### 3. 🎚 Globaler KI-Schalter & Automatisches Entladen
- Über den Schalter **`🤖 KI Global Aktiv`** (oben rechts in KI-Dialogen und Profil) können Sie die KI jederzeit global deaktivieren.
- Beim Deaktivieren wird das aktuell geladene KI-Modell automatisch aus dem RAM/VRAM entladen.
- Alle KI-Generierungs-Buttons werden bei inaktivem Schalter geschützt deaktiviert.

#### 4. 🚦 Präzise Status-Farbcodierung
Der KI-Status wird durch eindeutige Farbcodes angezeigt:
- **`🔴 Rot`**: Ollama Offline oder Server nicht erreichbar.
- **`⚪ Grau`**: Ollama Online, aber KI ist global ausgeschaltet (Schalter OFF).
- **`🔵 Blau`**: Ollama Online & KI Aktiv, aber Standby (kein Modell im RAM).
- **`🟢 Grün`**: Ollama Online & KI Aktiv und Modell einsatzbereit im RAM geladen.

#### 5. 🎯 Hierarchische Prompt-Regeln & Sonderanweisungen
Bei jeder KI-Generierung gilt eine strikte Prioritäten-Hierarchie:
1. **Globale Basis-Regeln** (Grundregeln im Benutzerprofil).
2. **Praxis-Spezifische Vorrang-Regeln** (In den Praxisdetails hinterlegt, übersteuern Basis-Regeln).
3. **⚡ Priorisierte Sonderanweisung** (Im Dialog eingegebene Einzeldirektive, hat **allerhöchste Priorität**).
"""
    },
    {
        "id": "stepper_time_picker",
        "title": "⏱ Zeitauswahl (07:00-20:00) & Stepper",
        "category": "Benutzeroberfläche",
        "content": """
### ⏱ Zeitauswahl & Stepper-Pfeile

Die Zeitauswahl in Kalender- und Wiedervorlage-Dialogen ist speziell auf Praxis-Arbeitszeiten optimiert:

- **Praxisnaher Zeitbereich**: Stunden sind auf die Kernarbeitszeit von **07:00 Uhr bis 20:00 Uhr** fokussiert.
- **Schnelle Stepper-Buttons**: Neben den Dropdown-Menüs stehen Pfeiltasten (`▲` / `▼`) zur Verfügung:
  - Stunden: Schrittweise um `+/- 1 Stunde` anpassen.
  - Minuten: Schrittweise im 5-Minuten-Takt (`+/- 5 Min.`) anpassen.
"""
    },
    {
        "id": "internal_cases",
        "title": "🏢 Interne Vorgänge & Aufgaben (ohne Kunde)",
        "category": "Workflow",
        "content": """
### 🏢 Interne Vorgänge & Aufgaben

Neben kundenbezogenen Support-Fällen können Sie im Cockpit auch **rein interne Vorgänge** (z. B. Server-Wartung, System-Updates, Notizen oder Entwicklungsaufgaben) verwalten.

#### Funktionen:
- **Kein Kunde erforderlich**: Beim Erstellen eines neuen Falls (`+ Neuer Fall` / `Strg+N`) kann das Feld Praxis/Kunde leer gelassen oder auf *"🏢 Interner Vorgang / Keine Praxis"* gesetzt werden.
- **Automatische Schema-Anpassung**: Das Formular schaltet automatisch auf das Schema *"🏢 Interne Aufgabe / Notiz"* um.
- **Optische Hervorhebung**: Interne Fälle erhalten in der Fallliste ein prägnantes blaues **`🏢 INTERN`**-Badge.
- **Suchfilter**: Mit dem Schnellfilter **`[🏢 Intern]`** oder dem Suchtoken `is:internal` filtern Sie auf einen Klick alle internen Vorgänge heraus.
"""
    },
    {
        "id": "cobra_crm_import",
        "title": "🐍 Cobra CRM Praxen- & Kundenimport",
        "category": "Kunden",
        "content": """
### 🐍 Cobra CRM Praxen- & Kundenimport

Importieren Sie Ihre bestehende Praxendatenbank direkt aus Cobra CRM in das Support-Cockpit.

#### Ablauf:
1. Öffnen Sie die Praxenverwaltung (**🏥 Praxen**).
2. Klicken Sie auf **🐍 Cobra CRM Import...**.
3. Wählen Sie Ihre Export-Datei aus (unterstützt `.csv`, `.txt`, `.json`).
4. **Automatische Spaltenerkennung**: Das System erkennt Cobra-Felder (wie Kundennummer, Praxisname, Ansprechpartner, E-Mail, Telefon, VIP-Kennzeichnung) automatisch per Aliasing.
5. Nach Bestätigung stehen alle Praxen sofort zur Fall-Zuordnung bereit.
"""
    },
    {
        "id": "snippets_manager",
        "title": "📝 Textbausteine & Snippet-Manager",
        "category": "Kommunikation",
        "content": """
### 📝 Textbausteine (Snippets) verwalten & einfügen

Sparen Sie Zeit bei wiederkehrenden Antworten und Standardnotizen durch den integrierten Textbaustein-Manager.

#### 1. Textbausteine verwalten
- Klicken Sie im Hauptmenü auf **📝 Textbausteine**.
- Erstellen Sie neue Bausteine mit Titel, Kategorie (z.B. *Abrechnung*, *Hardware*, *TI-Entstörung*), Tags und Vorlagentext.

#### 2. Bausteine in Notizen oder E-Mails einfügen
- Im Notizfeld oder im E-Mail-Dialog (`✉ E-Mail`): Klicken Sie auf **🧩 Textbaustein**.
- Es öffnet sich der `SnippetPickerDialog` mit Suchfeld und Kategoriefilter.
- Wählen Sie den gewünschten Baustein aus - der Text wird an der aktuellen Cursor-Position eingefügt!
"""
    },
    {
        "id": "analytics_kpi_dashboard",
        "title": "📊 Auswertungs- & KPI-Dashboard",
        "category": "Auswertungen",
        "content": """
### 📊 Auswertungs- & KPI-Dashboard

Erhalten Sie einen schnellen Überblick über Ihre Support-Kennzahlen und Auslastungen.

#### Dashboard öffnen:
- Klicken Sie in der Menüleiste auf **📊 Auswertungen**.

#### Enthaltene Metriken & Visualisierungen:
- **Gesamt-Kennzahlen**: Offene Fälle, Erledigte Fälle, Archivierte Fälle, Durchschnittliche Bearbeitungszeit.
- **Dringlichkeits-Verteilung**: Ampelanzeige für `🔴 Kritisch`, `🟡 Hoch`, `🟢 Normal`.
- **Top 5 Praxen-Ranking**: Praxen mit dem höchsten Fallaufkommen zur frühzeitigen Problemidentifikation.
- **Abteilungs-Auslastung**: Verteilung der Fälle auf Support, Technik, Entwicklung und Buchhaltung.
"""
    },
    {
        "id": "advanced_search_filters",
        "title": "🔍 Erweitertes Suchsystem & Such-Tokens",
        "category": "Grundlagen",
        "content": """
### 🔍 Erweitertes Suchsystem & Such-Tokens

Die Suchleiste im Cockpit unterstützt neben Freitextsuche auch leistungsfähige Filter-Tokens.

#### 1. Schnellfilter-Buttons
Über der Fallliste finden Sie praktische Schnellfilter:
- **`[Alle]`**: Alle Fälle anzeigen.
- **`[🔥 Dringend]`**: Zeigt nur Fälle mit hohem Urgency-Score.
- **`[🔔 Wiedervorlagen]`**: Zeigt fällige Wiedervorlagen.
- **`[🏢 Intern]`**: Zeigt rein interne Vorgänge.

#### 2. Such-Tokens für die Suchleiste (`Strg+F`):
Kombinierbare Tokens zur präzisen Eingrenzung:
- `is:internal` / `is:customer`: Nur interne oder kundenbezogene Fälle.
- `vip:true`: Nur VIP-Praxen.
- `reminder:due`: Nur fällige Wiedervorlagen.
- `actor:dev` / `actor:support` / `actor:tech`: Nach Zuständigkeit filtern.
- `status:open` / `status:closed`: Nach Status filtern.
- `error:XYZ`: Nach Fehlercodes oder Freitext in Notizen suchen.
"""
    },
    {
        "id": "attachments_and_screenshots",
        "title": "📂 Dateianhänge & Screenshots (Strg+V)",
        "category": "Dokumente",
        "content": """
### 📂 Dateianhänge, Screenshots & Vorschau

Verwalten Sie Logfiles, Screenshots und Dokumente direkt im Fall.

#### 1. Screenshots direkt per `Strg+V` einfügen
- Erstellen Sie einen Screenshot (z. B. mit `Win+Shift+S`).
- Drücken Sie im Cockpit einfach **`Strg + V`**: Das Bild wird automatisch im Fallordner gespeichert und in die Zeitleiste eingebunden!

#### 2. Live-Vorschau & OS-Öffnung
- Bilddateien (`.png`, `.jpg`, `.webp`) und Text-Anhangsdateien (`.log`, `.json`, `.txt`) können in der Anhänge-Leiste direkt per Vorschau betrachtet werden.
- Ein Doppelklick öffnet die Datei im Standardprogramm Ihres Betriebssystems.
"""
    },
    {
        "id": "zip_backup_restore",
        "title": "📦 Komplett-ZIP Backup & Import/Export",
        "category": "Konfiguration",
        "content": """
### 📦 Komplett-ZIP Backup & Import/Export

Sichern Sie Ihren gesamten Datenbestand inkl. aller Fälle, Kundendaten, Formulare und Dateianhänge in einer einzigen ZIP-Datei.

#### Ablauf:
1. Öffnen Sie **Profil & Einstellungen** (`👤`) -> **📦 Sicherung & Wiederherstellung**.
2. **`💾 Komplett-Backup erstellen...`**: Speichert alle JSON-Dateien und den Anhänge-Ordner als ZIP-Archiv.
3. **`📥 Backup wiederherstellen...`**: Entpackt und stellt einen früheren Datenstand wieder her (inkl. Sicherheits-Sicherung des aktuellen Stands).
"""
    },
    {
        "id": "email_webhook_integration",
        "title": "🔌 E-Mail-Import & REST Webhooks (Jira/GitLab)",
        "category": "Integrationen",
        "content": """
### 🔌 E-Mail-Import & REST Webhooks

Binden Sie das Support-Cockpit an externe Systeme an.

#### 1. 📬 Automatische E-Mail-Import (IMAP)
- Das System kann ein Support-Postfach per IMAP abfragen und neue E-Mails automatisch als Fall-Entwürfe im Cockpit anlegen.

#### 2. 🔗 REST Webhook Integration (GitLab / Jira)
- Konfigurieren Sie Webhook-URLs unter Einstellungen, um bei Erstellung oder Übergabe eines Falls automatisch Issue-Payloads an GitLab, Jira oder eigene APIs zu senden.
"""
    }
]


class HelpDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        w, h = DIALOG_DIMENSIONS["help"]
        self.title(DIALOG_TITLES["help"])
        self.geometry(f"{w}x{h}")
        self.minsize(960, 600)
        from utils.ui_utils import center_window
        center_window(self, w, h)

        # Make modal window
        self.transient(parent)
        self.grab_set()

        self.filtered_articles = list(HELP_ARTICLES)
        self.active_article = HELP_ARTICLES[0]

        self.create_widgets()
        self.select_article(self.active_article["id"])

    def create_widgets(self):
        # Main Layout: Top search bar, Left navigation list, Right detail view
        top_bar = ctk.CTkFrame(self, height=50, corner_radius=0)
        top_bar.pack(fill="x", side="top", padx=10, pady=(10, 5))

        ctk.CTkLabel(top_bar, text="📖 Handbuch & Hilfe", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10)

        self.search_entry = ctk.CTkEntry(top_bar, placeholder_text="🔍 Themen & Stichworte suchen...", width=320)
        self.search_entry.pack(side="right", padx=10)
        self.search_entry.bind("<KeyRelease>", self.on_search_changed)

        body_frame = ctk.CTkFrame(self, fg_color="transparent")
        body_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        # Left Sidebar (Article list)
        left_frame = ctk.CTkFrame(body_frame, width=280)
        left_frame.pack(side="left", fill="y", padx=(0, 5), pady=0)
        left_frame.pack_propagate(False)

        ctk.CTkLabel(left_frame, text="Themenübersicht", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))

        self.nav_scroll = ctk.CTkScrollableFrame(left_frame, fg_color="transparent")
        self.nav_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        # Right Detail View (Article Content)
        right_frame = ctk.CTkFrame(body_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0), pady=0)

        self.article_title_lbl = ctk.CTkLabel(right_frame, text="", font=ctk.CTkFont(size=18, weight="bold"), anchor="w")
        self.article_title_lbl.pack(fill="x", padx=15, pady=(15, 5))

        self.content_scroll = ctk.CTkScrollableFrame(right_frame, fg_color="transparent")
        self.content_scroll.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        self.render_nav_list()

    def render_nav_list(self):
        for w in self.nav_scroll.winfo_children():
            w.destroy()

        if not self.filtered_articles:
            ctk.CTkLabel(self.nav_scroll, text="Keine Themen gefunden.", text_color="gray").pack(pady=20)
            return

        for art in self.filtered_articles:
            is_active = art["id"] == self.active_article["id"]
            fg_color = ("gray75", "gray30") if is_active else ("gray85", "gray20")
            btn = ctk.CTkButton(
                self.nav_scroll,
                text=art["title"],
                anchor="w",
                fg_color=fg_color,
                hover_color=("gray70", "gray35"),
                text_color=("black", "white") if is_active else ("gray10", "gray90"),
                command=lambda a_id=art["id"]: self.select_article(a_id)
            )
            btn.pack(fill="x", pady=3, padx=2)

    def select_article(self, article_id: str):
        article = next((a for a in HELP_ARTICLES if a["id"] == article_id), None)
        if not article:
            return

        self.active_article = article
        self.article_title_lbl.configure(text=article["title"])

        self.render_markdown(article["content"])
        self.render_nav_list()

    def render_markdown(self, markdown_text: str):
        import re

        for w in self.content_scroll.winfo_children():
            w.destroy()

        lines = markdown_text.strip().split("\n")
        in_table = False
        table_rows = []

        def clean_inline(text: str) -> str:
            cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
            cleaned = re.sub(r'\*(.*?)\*', r'\1', cleaned)
            cleaned = re.sub(r'`(.*?)`', r'\1', cleaned)
            return cleaned.strip()

        def flush_table():
            nonlocal in_table, table_rows
            if not table_rows:
                return

            table_frame = ctk.CTkFrame(self.content_scroll, fg_color=("gray85", "gray20"), corner_radius=6)
            table_frame.pack(fill="x", padx=10, pady=8)

            header_cols = [clean_inline(c) for c in table_rows[0].strip("|").split("|")]
            data_rows = table_rows[2:] if len(table_rows) > 2 and "---" in table_rows[1] else table_rows[1:]

            # Header Frame
            hdr_frame = ctk.CTkFrame(table_frame, fg_color=("gray70", "gray30"), corner_radius=4)
            hdr_frame.pack(fill="x", padx=4, pady=(4, 2))
            for col_txt in header_cols:
                ctk.CTkLabel(hdr_frame, text=col_txt.strip(), font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(side="left", fill="x", expand=True, padx=8, pady=4)

            # Data Rows
            for r_idx, r_line in enumerate(data_rows):
                r_cols = [clean_inline(c) for c in r_line.strip("|").split("|")]
                r_bg = ("gray90", "gray22") if r_idx % 2 == 0 else ("gray85", "gray25")
                row_frame = ctk.CTkFrame(table_frame, fg_color=r_bg, corner_radius=2)
                row_frame.pack(fill="x", padx=4, pady=1)

                for col_txt in r_cols:
                    ctk.CTkLabel(row_frame, text=col_txt.strip(), font=ctk.CTkFont(size=11), anchor="w").pack(side="left", fill="x", expand=True, padx=8, pady=4)

            table_rows = []
            in_table = False

        for line in lines:
            stripped = line.strip()

            # Check Table line
            if stripped.startswith("|") and stripped.endswith("|"):
                in_table = True
                table_rows.append(stripped)
                continue
            elif in_table:
                flush_table()

            if not stripped:
                continue

            # Horizontal rule
            if stripped in ("---", "***", "___"):
                sep = ctk.CTkFrame(self.content_scroll, height=2, fg_color=("gray75", "gray35"))
                sep.pack(fill="x", padx=10, pady=10)
                continue

            # Headings
            if stripped.startswith("### "):
                txt = clean_inline(stripped[4:])
                lbl = ctk.CTkLabel(self.content_scroll, text=txt, font=ctk.CTkFont(size=15, weight="bold"), text_color=("dodgerblue", "#4dabf7"), anchor="w")
                lbl.pack(fill="x", padx=10, pady=(12, 4))
                continue

            if stripped.startswith("#### "):
                txt = clean_inline(stripped[5:])
                lbl = ctk.CTkLabel(self.content_scroll, text=txt, font=ctk.CTkFont(size=13, weight="bold"), text_color=("gray10", "gray90"), anchor="w")
                lbl.pack(fill="x", padx=10, pady=(8, 2))
                continue

            # Lists (unordered or ordered)
            is_bullet = stripped.startswith("- ") or stripped.startswith("* ")
            is_num = bool(re.match(r'^\d+\.\s', stripped))

            if is_bullet or is_num:
                prefix = "• " if is_bullet else stripped.split()[0] + " "
                raw_body = stripped.split(" ", 1)[1] if " " in stripped else stripped
                clean_body = clean_inline(raw_body)

                row = ctk.CTkFrame(self.content_scroll, fg_color="transparent")
                row.pack(fill="x", padx=15, pady=2)

                bullet_lbl = ctk.CTkLabel(row, text=prefix, font=ctk.CTkFont(size=12, weight="bold"), text_color=("dodgerblue", "cyan"), anchor="nw", width=20)
                bullet_lbl.pack(side="left", anchor="nw")

                txt_lbl = ctk.CTkLabel(row, text=clean_body, font=ctk.CTkFont(size=12), anchor="w", justify="left", wraplength=560)
                txt_lbl.pack(side="left", fill="x", expand=True)
                continue

            # Standard Paragraph
            clean_para = clean_inline(stripped)
            para_lbl = ctk.CTkLabel(self.content_scroll, text=clean_para, font=ctk.CTkFont(size=12), anchor="w", justify="left", wraplength=580)
            para_lbl.pack(fill="x", padx=10, pady=3)

        if in_table:
            flush_table()

    def on_search_changed(self, event=None):
        query = self.search_entry.get().strip().lower()
        if not query:
            self.filtered_articles = list(HELP_ARTICLES)
        else:
            self.filtered_articles = [
                a for a in HELP_ARTICLES
                if query in a["title"].lower() or query in a["content"].lower() or query in a["category"].lower()
            ]

        if self.filtered_articles and self.active_article not in self.filtered_articles:
            self.active_article = self.filtered_articles[0]
            self.select_article(self.active_article["id"])

        self.render_nav_list()
