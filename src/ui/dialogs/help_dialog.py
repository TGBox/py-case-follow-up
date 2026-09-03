import customtkinter as ctk
from constants import DIALOG_DIMENSIONS, DIALOG_TITLES


HELP_ARTICLES = [
    {
        "id": "first_steps",
        "title": "🐣 Erste Schritte & Schnellstart-Guide",
        "category": "Grundlagen",
        "content": r"""
### 🐣 Schnellstart-Guide für neue Anwender

Willkommen beim **Support-Cockpit**! Dieser Leitfaden führt Sie Schritt für Schritt durch Ihre ersten Aktionen im System.

#### Schritt 1: Praxis / Kunde auswählen oder neu anlegen
- Öffnen Sie den Bereich **🏥 Praxen** in der oberen Menüleiste.
- Prüfen Sie, ob die betroffene Praxis bereits in der Liste steht.
- Falls nicht, klicken Sie auf **+ Neue Praxis anlegen** und tragen Sie Kundennummer, Praxisname, Haupt-Ansprechpartner und E-Mail-Adresse ein.

#### Schritt 2: Ihren ersten Support-Fall anlegen (`Strg + N`)
1. Drücken Sie **`Strg + N`** oder klicken Sie oben links auf **+ Neuer Fall**.
2. Wählen Sie im Dialog die Praxis aus (z. B. *Gemeinschaftspraxis Dr. Muster*).
3. Wählen Sie das passende **Formular-Schema** aus (z. B. *Schnellerfassung*, *Hardware-Tausch*, *Abrechnung*).
4. Tragen Sie einen prägnanten **Betreff** und eine Beschreibung des Problems ein.
5. Klicken Sie auf **💾 Fall erstellen**.

#### Schritt 3: Falldetails dokumentieren & Screenshots einfügen
- Öffnen Sie den Fall in der Cockpit-Ansicht.
- **Screenshots einfügen**: Erstellen Sie einen Screenshot (z. B. mit `Win + Shift + S`) und drücken Sie direkt im Cockpit **`Strg + V`**. Das Bild wird sofort im Fall gespeichert und in der Zeitleiste abgelegt.
- **Textbausteine nutzen**: Klicken Sie im Notizbereich auf **🧩 Textbaustein** (oder `Strg + M`), um häufig benötigte Antworttexte (z. B. TI-Fehlersuche, Abrechnungstipps) per Klick einzufügen.

#### Schritt 4: Wiedervorlage planen oder Bearbeiter zuweisen
- Wenn der Fall nicht sofort gelöst werden kann:
  - Klicken Sie auf **🔔 Wiedervorlage**, um ein Nachfragedatum mit Erinnerungsnotiz festzulegen.
  - Oder ändern Sie im Cockpit das Feld **Zuständig (Akteur)** (z. B. auf *Entwicklung* oder *Technik*), um die Aufgabe zu übergeben.

#### Schritt 5: Fall erfolgreich abschließen (`Strg + Shift + A`)
- Ist das Problem gelöst, klicken Sie oben rechts auf **✓ Erledigt** (oder drücken `Strg + Shift + A`).
- Der Fall wird als erledigt markiert und in der Chronologie sauber archiviert.
"""
    },
    {
        "id": "basics",
        "title": "🚀 Grundlagen & 4 Ansichten",
        "category": "Grundlagen",
        "content": r"""
### 🚀 Grundlagen der Benutzeroberfläche & Layouts

Das Support-Cockpit bietet 4 spezialisierte Arbeitsansichten, zwischen denen Sie jederzeit über das Dropdown **Layout** in der Menüleiste oder per Hotkey umschalten können:

#### 1. 🎛 Cockpit-Ansicht (Standard, `Strg + 1`)
- **Dreigeteiltes Haupt-Layout**:
  - **Links**: Fallliste mit Suchleiste, Schnellfiltern (`[🔥 Dringend]`, `[🔔 Wiedervorlagen]`, `[🏢 Intern]`) und Dringlichkeits-Badges.
  - **Mitte**: Falldetails, dynamische Formularfelder, Schnellaktionen (E-Mail, Kalender, Wiedervorlage, Notiz) und Zeitleisteneinträge.
  - **Rechts**: Wechselbarer Tab-Container mit *Zeitleiste*, *Dateianhängen & Screenshots* sowie dem *BookStack Offline-Wiki*.

#### 2. 📋 Kanban-Board (`Strg + 2`)
- Übersicht aller Fälle nach Zuständigkeits- und Bearbeitungsstatus:
  - *Neu*, *Aktion erforderlich*, *Warten*, *In Bearbeitung*, *Erledigt*.
- Ideal für Team-Overviews und tägliche Standup-Meetings.

#### 3. 📊 Tabellarische Matrix (`Strg + 3`)
- Übersichtliche Tabellenansicht aller Fälle für schnelles Durchsuchen, Vergleichen und Verwalten großer Fallmengen.

#### 4. 📈 Auswertungen & Kennzahlen (`Strg + 4`)
- Statistisches Dashboard mit Kennzahlen zu offenen Fällen, Überfälligkeiten, durchschnittlicher Bearbeitungsdauer, VIP-Quoten und Auslastung.
"""
    },
    {
        "id": "case_lifecycle",
        "title": "🔄 Der komplette Lebenszyklus eines Support-Falls",
        "category": "Workflow",
        "content": r"""
### 🔄 Lebenszyklus eines Support-Falls

Jeder Vorgang im Support-Cockpit durchläuft eine klar strukturierte Phasenabfolge:

#### 1. Erfassung & Initialisierung
- **Erstellung**: Manuell über `+ Neuer Fall` (`Strg+N`), durch E-Mail-Import (IMAP) oder per Outlook-Add-in Makro.
- **Klassifizierung**: Automatische Ermittlung der Erst-Priorität und Errechnen des **Dringlichkeits-Scores**.

#### 2. Bearbeitung & Dokumentation
- **Akteur-Zuweisung**: Festlegen der aktuellen Zuständigkeit (*Support*, *Entwicklung*, *Technik*, *Kunde/Praxis*).
- **Zeitleiste**: Jeder Schritt, Notizen, Anrufe und Screenshots (`Strg+V`) werden unveränderlich in der Chronologie protokolliert.
- **Formularausfüllung**: Eingabe spezifischer Daten im aktiven Formular-Schema (z. B. PVS-Version, Modul, Fehlermeldung).

#### 3. Fristüberwachung & Wiedervorlage
- **Nachfragen einplanen**: Bei Warten auf Rückmeldung oder Bearbeitung durch Dritte wird eine Wiedervorlage hinterlegt.
- **Optische Hervorhebung**: Das Cockpit warnt bei fälligen oder überfälligen Fristen durch farbige Relativangaben (`(heute fällig)`, `(seit X Tagen überfällig)`).

#### 4. Abschluss, Archivierung & Wiedereröffnung
- **Abschluss**: Klick auf **✓ Erledigt** setzt den Status um, entfernt aktive Wiedervorlagen und aktualisiert den Gesamtstatus.
- **Wiedereröffnung**: Sollte sich der Kunde erneut zum selben Problem melden, klicken Sie im geschlossenen Fall einfach auf **✓ Wieder öffnen**.
"""
    },
    {
        "id": "praxis",
        "title": "🏥 Praxis- & Kundenverwaltung",
        "category": "Kunden",
        "content": r"""
### 🏥 Praxis- & Kundenverwaltung

Die Praxis- und Kundenverwaltung speichert Stammdaten aller betreuten Praxen und Kunden.

#### 1. Übersicht & Suche (`🏥 Praxen`)
- Öffnen Sie **🏥 Praxen** in der Menüleiste.
- Suchen Sie nach Praxisname, Kundennummer, Ansprechpartner oder Ort.

#### 2. Praxis-Details & VIP-Status
- **Kundennummer & Name**: Eindeutige ID und offizieller Praxisname.
- **Ansprechpartner**: Hauptansprechpartner für E-Mails und telefonische Rückfragen.
- **★ VIP-Kennzeichnung**: Aktivieren Sie das Häkchen **VIP-Kunde**, um Fälle dieser Praxis in allen Ansichten mit einem Stern-Badge zu kennzeichnen und einen **+30 Punkte Bonus** beim Dringlichkeits-Scoring zu vergeben.
- **KI-Sonderregeln**: Hinterlegen Sie praxisspezifische Anweisungen für den KI-Assistenten (z. B. *"Praxis wünscht Rückmeldung stets telefonisch vor 12 Uhr"*).

#### 3. Schnellanlage aus dem Falldialog
- Beim Erstellen eines neuen Falls können Sie über den Button **+ Neue Praxis** direkt aus dem Erfassungs-Dialog heraus eine neue Praxis anlegen, ohne das Formular abzubrechen.
"""
    },
    {
        "id": "cobra_crm_import",
        "title": "🐍 Cobra CRM Praxen- & Kundenimport",
        "category": "Kunden",
        "content": r"""
### 🐍 Cobra CRM Praxen- & Kundenimport

Importieren Sie Ihre bestehenden Kundendaten direkt aus Cobra CRM oder anderen CRM-Systemen.

#### Schritt-für-Schritt Anleitung:
1. Öffnen Sie die Praxenverwaltung (**🏥 Praxen**).
2. Klicken Sie oben rechts auf **🐍 Cobra CRM Import...**.
3. **Datei auswählen**: Wählen Sie Ihre aus Cobra CRM exportierte Datei (`.csv`, `.txt` oder `.json`).
4. **Spalten-Mapping prüfen**: Das System erkennt Standardspalten (Kundennummer, Praxisname, Ansprechpartner, E-Mail, Telefon, VIP-Status) automatisch. Bei abweichenden Spaltenüberschriften können Sie diese im Zuordnungs-Dropdown manuell verknüpfen.
5. **Importmodus wählen**:
   - *Nur neue Praxen hinzufügen* (Schützt bestehende Daten).
   - *Bestehende Praxen aktualisieren* (Überschreibt Kontaktdaten mit neuesten Werten).
6. Klicken Sie auf **🚀 Import starten**. Alle importierten Praxen stehen sofort zur Fallzuordnung bereit.
"""
    },
    {
        "id": "schemas",
        "title": "📄 Formular-Baukasten (Schemas) verwalten",
        "category": "Formulare",
        "content": r"""
### 📄 Formular-Baukasten (Schemas)

Mit dem Formular-Baukasten passen Sie die Erfassungsfelder im Cockpit exakt an Ihre Support-Prozesse an.

#### 1. Formular-Baukasten öffnen
- Klicken Sie in der oberen Menüleiste auf **📄 Vorlagen & Formulare** -> **🛠 Formular-Baukasten**.

#### 2. Neues Formular-Schema erstellen
1. Klicken Sie auf **+ Neues Formular**.
2. Vergeben Sie einen Namen (z. B. *"Hardware-Tausch"*) und eine optionale Beschreibung.
3. Wählen Sie das Formular aus der Dropdown-Liste aus.

#### 3. Felder hinzufügen & konfigurieren
- Fügen Sie neue Felder hinzu:
  - **Text-Feld** (z. B. Seriennummer, Treiberversion)
  - **Zahlen-Feld** (z. B. Anzahl Geräte)
  - **Ja/Nein Kontrollkästchen** (z. B. Garantie vorhanden)
  - **Drop-Down Auswahlfeld** (z. B. Betriebssystem: Windows 10, Windows 11, Server 2022)
- **Pflichtfelder (*)**: Aktivieren Sie den Schalter *Obligatorisch*, um sicherzustellen, dass ein Fall erst abgeschlossen werden kann, wenn dieses Feld ausgefüllt ist.

#### 4. Nutzung im Cockpit
- Sobald Sie im Cockpit das Formular-Schema eines Falls umstellen, werden die Eingabefelder im mittleren Panel dynamisch neu aufgebaut.
"""
    },
    {
        "id": "repeatable_sub_forms",
        "title": "📂 Dynamische Mehrfach-Eingabemasken (z. B. Zuzahlungsnachforderung)",
        "category": "Formulare",
        "content": r"""
### 📂 Dynamische Mehrfach-Eingabemasken

Bestimmte Support-Formulare (wie *"Zuzahlungsnachforderung & Abrechnungskorrektur"*) erfordern die Erfassung mehrerer gleichartiger Positionen (z. B. mehrere ESOL-Dateien oder Korrektur-Rechnungen) innerhalb desselben Falls.

#### Schritt-für-Schritt Anleitung:
1. Wählen Sie im Fall das Schema **"Zuzahlungsnachforderung & Abrechnungskorrektur"**.
2. Das Formular stellt eigenständige Karteikarten-Container bereit (z. B. für *ESOL-Dateiname*, *Rechnungs-Nr.*, *Verordnungs-Nr.*, *Patientenname(n)*, *Begründung*).
3. **Mehrere Einträge hinzufügen**: Klicken Sie unten auf **➕ Weitere Datei / Korrektur-Anforderung hinzufügen**. Es wird sofort eine neue, nummerierte Karteikarte angefügt.
4. **Positionen löschen**: Über den roten Button **🗑 Anforderung #N entfernen** können Sie einzelne Einträge wieder entfernen.
5. **Automatische Formatierung**: Beim E-Mail-Versand oder Vorlagen-Export werden alle erfassten Positionen automatisch als sauber gegliederte Abschnitte formatiert.
"""
    },
    {
        "id": "convert_schema",
        "title": "🔄 Formular umwandeln (Schema-Konvertierung)",
        "category": "Formulare",
        "content": r"""
### 🔄 Formular umwandeln (Schema-Konvertierung)

Sollte ein Fall versehentlich unter einem falschen Formular-Schema angelegt worden sein (z. B. als *Schnellerfassung* statt *PVS-Schnittstelle*), können Sie das Schema jederzeit konvertieren.

#### Anleitung:
1. Öffnen Sie den betreffenden Fall im Cockpit.
2. Klicken Sie im Rechten Aktionsbereich auf **⚙ Weitere Aktionen...** -> **🔄 Formular umwandeln**.
3. Wählen Sie im Dialog das Ziel-Schema aus.
4. **Datensicherung**: Alle bisher eingegebenen Feldwerte werden automatisch gesichert und als formatierte Zusammenfassung in der Zeitleiste protokolliert (`ℹ Datensicherung: ...`), sodass keine Informationen verloren gehen!
5. Bestätigen Sie mit **🔄 Schema umwandeln**.
"""
    },
    {
        "id": "email_calendar_outlook",
        "title": "✉ E-Mail, Kalender (.ics) & Outlook Integration",
        "category": "Kommunikation",
        "content": r"""
### ✉ E-Mail, Kalender-Export (.ics) & Outlook Integration

Das Support-Cockpit vereinfacht die externe Kommunikation mit Kunden und Kollegen.

#### 1. ✉ E-Mail-Entwurf erstellen & senden
1. Klicken Sie im Cockpit auf **✉ E-Mail**.
2. Empfängeradresse und Betreff werden automatisch aus den Praxisdaten und der Fall-ID generiert.
3. Klicken Sie auf **🧩 Textbaustein**, um vorgefertigte Textblöcke einzufügen.
4. **In Outlook übergeben**: Klicken Sie auf **✉ In Outlook öffnen**, um die E-Mail direkt als fertigen Entwurf in Microsoft Outlook anzuzeigen.
5. **Standard-Mail-Client**: Klicken Sie auf **📧 In Mail-App öffnen**, um die E-Mail über das System-`mailto:`-Protokoll zu öffnen.

#### 2. 📅 Kalender-Termine (.ics) erstellen
1. Klicken Sie im Cockpit auf **📅 Kalender**.
2. Datum und Uhrzeit der Wiedervorlage oder des Rückrufs werden übernommen.
3. Klicken Sie auf **📅 Direkt im Kalender öffnen**, um den Termin in Outlook / Thunderbird zu öffnen, oder auf **💾 Als .ics speichern**, um die Datei abzulegen.

#### 3. 📬 E-Mails aus Outlook ins Cockpit übertragen (Add-in / Makro)
- Unter **⚙ Weitere Aktionen...** -> **📧 Outlook-Makro anzeigen** finden Sie ein vorgefertigtes VBA-Skript für Outlook.
- Damit können Sie empfangene Kunden-E-Mails direkt per Klick in Outlook als neuen Fall im Support-Cockpit anlegen!
"""
    },
    {
        "id": "snippets_manager",
        "title": "📝 Textbausteine & Snippet-Manager",
        "category": "Kommunikation",
        "content": r"""
### 📝 Textbausteine (Snippets) verwalten & einfügen

Vermeiden Sie tippintensive Wiederholungen durch zentral verwaltete Textbausteine.

#### 1. Textbausteine verwalten (`📝 Textbausteine`)
- Öffnen Sie im Hauptmenü **📄 Vorlagen & Formulare** -> **📝 Textbausteine verwalten**.
- Erstellen Sie neue Bausteine mit Titel, Kategorie (z. B. *TI-Entstörung*, *Hardware*, *Abrechnung*), Schlagworten und Vorlagentext.
- **Tastenkürzel zuweisen**: Weisen Sie beliebigen Bausteinen eigene Schnell-Hotkeys zu (z. B. `Strg + Alt + 1`).

#### 2. Bausteine im Cockpit oder E-Mail-Dialog einfügen (`Strg + M`)
- Drücken Sie im Notizfeld oder im E-Mail-Dialog **`Strg + M`** (oder Klick auf **🧩 Textbaustein**).
- Der Snippet-Picker öffnet sich mit Live-Suche und Kategoriefilter.
- Wählen Sie den gewünschten Baustein per Pfeiltasten oder Doppelklick aus: Der Text wird sofort an der aktuellen Cursorposition eingefügt!
"""
    },
    {
        "id": "attachments_and_screenshots",
        "title": "📂 Dateianhänge & Screenshots (Strg+V)",
        "category": "Dokumente",
        "content": r"""
### 📂 Dateianhänge & Screenshots (`Strg + V`)

Dokumentieren Sie Fehlermeldungen und Screenshots direkt im Fall.

#### 1. Screenshots per `Strg + V` einfügen
1. Erstellen Sie einen beliebigen Screenshot (z. B. mit `Win + Shift + S` oder `Druck`).
2. Klicken Sie ins Support-Cockpit und drücken Sie **`Strg + V`**.
3. Das Bild wird automatisch im Anhänge-Ordner des Falls als PNG gespeichert und in der Zeitleiste protokolliert.

#### 2. Anhänge verwalten & Vorschau
- Im rechten Cockpit-Panel unter dem Reiter **Anhänge** werden alle Dateien des Falls gelistet.
- **Vorschau**: Bilddateien (`.png`, `.jpg`, `.webp`) und Text/Logdateien (`.log`, `.txt`, `.json`) werden direkt in einer integrierten Vorschau angezeigt.
- **Öffnen**: Ein Klick auf den Dateinamen öffnet die Datei im Standardprogramm Ihres Betriebssystems.
"""
    },
    {
        "id": "handover_followup",
        "title": "🔔 Zuständigkeitswechsel & Wiedervorlagen",
        "category": "Workflow",
        "content": r"""
### 🔔 Zuständigkeitswechsel & Wiedervorlagen

Sorgen Sie dafür, dass kein Fall in Vergessenheit gerät und Übergaben lückenlos nachvollziehbar bleiben.

#### 1. Zuständigkeit (Akteur) wechseln
- Ändern Sie im Cockpit das Dropdown **Zuständig (Akteur)** (z. B. von *Support* auf *Entwicklung*).
- Das System protokolliert den Wechsel automatisch mit Zeitstempel und Urheber in der Zeitleiste (*ZUSTÄNDIGKEIT: Support -> Entwicklung*).

#### 2. Wiedervorlage & Erinnerung festlegen
1. Klicken Sie im Cockpit auf **🔔 Wiedervorlage** (oder nach einem Akteurwechsel im automatischen Pop-up).
2. Wählen Sie das Gewünschte Datum per Kalender-Picker oder nutzen Sie Schnelltasten (`+ 1 Tag`, `+ 2 Tage`, `+ 1 Woche`).
3. Tragen Sie eine kurze Erinnerungs-Notiz ein (z. B. *"Beim Entwickler bezüglich Ticket #402 nachfragen"*).
4. **Anzeige in der Fallliste**: Fällige Wiedervorlagen werden 3-zeilig hervorgehoben und zeigen den relativen Status (`(heute fällig)`, `(morgen)` oder `(seit X Tagen überfällig)`).
"""
    },
    {
        "id": "stepper_time_picker",
        "title": "⏱ Zeitauswahl (07:00-20:00) & Stepper-Bedienung",
        "category": "Benutzeroberfläche",
        "content": r"""
### ⏱ Zeitauswahl & Stepper-Bedienung

Die Uhrzeitauswahl in Kalender- und Wiedervorlagedialogen ist speziell für den Praxiseinsatz optimiert.

#### Merkmale & Bedienung:
- **Praxisnahe Kernarbeitszeit**: Die Stundenauswahl konzentriert sich auf **07:00 Uhr bis 20:00 Uhr**, um Fehleingaben außerhalb der Arbeitszeiten zu vermeiden.
- **Stepper-Buttons (`▲` / `▼`)**:
  - Klicken Sie auf die Pfeile neben den Stunden- und Minuten-Dropdowns, um Zeiten in exakten Schritten anzupassen (`+/- 1 Std.` bzw. `+/- 5 Min.`).
- **Tastatur- & Mausrad-Unterstützung**: Sie können Uhrzeiten auch direkt per Tastatur eintippen oder mit dem Mausrad über dem Feld scrollen.
"""
    },
    {
        "id": "scoring",
        "title": "📊 Fall-Scoring & Dringlichkeits-Priorisierung",
        "category": "Workflow",
        "content": r"""
### 📊 Automatisches Dringlichkeits-Scoring

Das Support-Cockpit berechnet für jeden offenen Fall automatisch einen **Dringlichkeits-Score** (Punkte), damit Sie kritische Fälle sofort oben in Ihrer Liste sehen.

#### Berechnungsfaktoren:
- **Priorität**: Critical (60 Pkt), High (40 Pkt), Medium (20 Pkt), Low (10 Pkt).
- **★ VIP-Praxis**: Praxen mit VIP-Status erhalten einen pauschalen Bonus von **+30 Punkten**.
- **Wartezeit (Liegezeit)**: Je länger ein Fall ungelöst ist, desto höher steigt der Score (automatisch **+2 Punkte pro Tag**).
- **Inaktivität**: Fälle ohne Notiz/Update in den letzten 48 Stunden erhalten Zusatzpunkte.
- **Workflow-Status**: In Bearbeitung (+10 Pkt), Warten auf Kunde (+0 Pkt), Vorort-Termin nötig (+20 Pkt).

#### Automatische Hintergrund-Aktualisierung:
Ein Hintergrund-Timer aktualisiert die Scores aller offenen Fälle stündlich. Sie können die Punkte-Matrix in den Einstellungen (`⚙ Profil & Einstellungen` -> `⌨ Tastenkürzel & Scoring`) individuell anpassen.
"""
    },
    {
        "id": "internal_cases",
        "title": "🏢 Interne Vorgänge & Aufgaben (ohne Kunde)",
        "category": "Workflow",
        "content": r"""
### 🏢 Interne Vorgänge & Notizen (ohne Kunde)

Sie können das Support-Cockpit auch für interne Aufgaben, Wartungsarbeiten oder Notizen nutzen, die keiner spezifischen Praxis zugeordnet sind.

#### Anleitung:
1. Erstellen Sie einen neuen Fall (`Strg + N`).
2. Lassen Sie das Feld **Praxis / Kunde** leer oder wählen Sie *"🏢 Interner Vorgang / Keine Praxis"*.
3. Das Formular schaltet automatisch auf das Schema *"🏢 Interne Aufgabe / Notiz"* um.
4. **Hervorhebung**: Interne Fälle erhalten in der Fallliste ein blaues **`🏢 INTERN`**-Badge.
5. **Filter**: Klicken Sie über der Fallliste auf den Schnellfilter **`[🏢 Intern]`** oder geben Sie `is:internal` in die Suchleiste ein, um alle internen Aufgaben auf einen Klick anzuzeigen.
"""
    },
    {
        "id": "export",
        "title": "📤 Export-Engine & Ticket-Protokolle",
        "category": "Export",
        "content": r"""
### 📤 Export-Engine & Ticket-Protokolle

Generieren Sie mit einem Klick saubere Übergabeprotokolle, E-Mails oder Dokumentationen.

#### Schritt-für-Schritt Anleitung:
1. Wählen Sie den gewünschten Fall im Cockpit aus.
2. Klicken Sie auf **📤 Export** (oder drücken Sie `Strg + E`).
3. **Vorlage wählen**: Wählen Sie eine passende Vorlage (z. B. *Standard Übergabe*, *Kunden-Zusammenfassung*, *Entwickler-Bugreport*).
4. **Ausgabeformat wählen**:
   - **Markdown**: Perfekt geeignet für Jira, GitHub, Redmine oder BookStack.
   - **HTML / Text**: Ideal für E-Mail-Entwürfe und Dokumente.
   - **PDF**: Zur Archivierung oder zum Ausdrucken.
5. Klicken Sie auf **📋 In Zwischenablage kopieren** oder **💾 Als Datei speichern**.
"""
    },
    {
        "id": "template_editor",
        "title": "📄 Export-Vorlagen-Editor (Jinja2)",
        "category": "Export",
        "content": r"""
### 📄 Export-Vorlagen-Editor (Jinja2)

Im Vorlagen-Editor können Sie eigene Platzhalter-Vorlagen für Exporte und Berichte erstellen.

#### Vorlagen-Manager öffnen:
- Klicken Sie in der Menüleiste auf **📄 Vorlagen & Formulare** -> **📄 Export-Vorlagen verwalten** (oder im Export-Dialog auf `🛠 Vorlagen verwalten`).

#### Vorlage anpassen:
1. Wählen Sie eine bestehende Vorlage aus oder klicken Sie auf **+ Neue Vorlage**.
2. **Jinja2-Template**: Verwenden Sie Variablen wie `{{ case.case_id }}`, `{{ case.customer.practice_name }}`, `{{ case.classification.title }}` oder Schleifen über Zeitleisteneinträge (`{% for entry in case.timeline %}`).
3. **Live-Vorschau**: Klicken Sie auf **👁 Live-Vorschau rendern**, um das Ergebnis mit echten Spieldaten sofort im rechten Panel zu überprüfen!
"""
    },
    {
        "id": "case_print_reporting",
        "title": "🖨 Fall-Druckansicht, PDF & Bilder",
        "category": "Export",
        "content": r"""
### 🖨 Fall-Druckansicht, PDF & Bildberichte

Erstellen Sie druckfähige Gesamtberichte inklusive aller Screenshots und Zeitleisteneinträge.

#### Schritt-für-Schritt Anleitung:
1. Klicken Sie im Cockpit auf **🖨 Drucken** (unter `⚙ Weitere Aktionen...`).
2. **Optionen festlegen**: Wählen Sie aus, welche Abschnitte im Bericht enthalten sein sollen (Kundendaten, Formularfelder, Zeitleiste, Bildanhänge).
3. **Bilder am Berichtsende**: Alle im Fall gespeicherten Screenshots (`.png`, `.jpg`) werden automatisch am Ende der Druckseite eingebettet.
4. **Drucken oder als PDF speichern**:
   - Klicken Sie auf **🖨 Im Browser öffnen & Drucken**, um das Dokument im Browser anzuzeigen und den System-Druckdialog aufzurufen.
   - Oder nutzen Sie **💾 Als HTML/PDF speichern**, um die Datei lokal abzulegen.
"""
    },
    {
        "id": "wiki",
        "title": "📚 BookStack Wiki Integration",
        "category": "Wiki",
        "content": r"""
### 📚 BookStack Offline-Wiki Integration

Das Support-Cockpit verfügt über eine direkte Anbindung an Ihr BookStack-Wiki, damit Sie Lösungsanleitungen ohne Fensterwechsel direkt im Cockpit nachschlagen können.

#### Funktionen & Bedienung:
1. **Wiki-Tab öffnen**: Klicken Sie im rechten Cockpit-Panel auf den Reiter **Wiki / Wissensdatenbank**.
2. **Suche (`Strg + W`)**: Tippen Sie Suchbegriffe oder Fehlercodes (z. B. `ERR_DB_902`, `TI-Konnektor`) in die Suchleiste ein.
3. **Artikel lesen**: Klicken Sie auf ein Suchergebnis – der Inhalt wird sofort sauber formatiert im Cockpit gerendert.
4. **Im Browser öffnen**: Ein Klick auf das Globus-Icon öffnet die Original-Seite direkt in Ihrem Webbrowser.
5. **Offline-Cache & Sync**: Über **🔄 Wiki Sync** können Sie den lokalen Offline-Index mit Ihrem BookStack-Server abgleichen. Die Zugangsdaten (URL, API-Tokens) hinterlegen Sie unter `⚙ Profil & Einstellungen` -> `📚 BookStack Wiki`.
"""
    },
    {
        "id": "ai_ollama_management",
        "title": "🤖 KI-Assistent & Ollama Server-Steuerung",
        "category": "KI & Ollama",
        "content": r"""
### 🤖 Lokaler KI-Assistent & Ollama Server-Steuerung

Das Support-Cockpit enthält einen integrierten, datenschutzkonformen KI-Assistenten auf Basis lokaler Open-Source Sprachmodelle (Ollama mit Qwen2.5 / Llama3). Sämtliche Anfragen bleiben zu 100% lokal auf Ihrem Rechner!

#### 1. Ollama Server-Steuerung (Start & Beenden aus der App)
Unter **⚙ Profil & Einstellungen** (`👤`) -> Reiter **🤖 KI & NLP** steuern Sie den KI-Server:
- **`▶ Ollama Server Starten`**: Startet den Ollama-Hintergrundprozess (`ollama serve`), ohne dass ein Terminal geöffnet werden muss.
- **`🛑 Server Beenden`**: Beendet den Serverprozess sauber und gibt belegten Arbeitsspeicher (VRAM) frei.
- **`⚡ PVS-Support Modell erstellen`**: Generiert automatisch ein auf deutschen IT-Support im Gesundheitswesen spezialisiertes KI-Modell (`pvs-support`).

#### 2. Status-Farbcodes der KI:
- **`🔴 Rot`**: Server Offline oder nicht erreichbar.
- **`⚪ Grau`**: Server Online, aber KI ist global ausgeschaltet (Schalter OFF).
- **`🔵 Blau`**: Server Online & KI Aktiv, aber Standby (kein Modell im RAM).
- **`🟢 Grün`**: Server Online, KI Aktiv & Modell einsatzbereit im RAM geladen.

#### 3. Hierarchische Prompt-Regeln:
Bei jeder KI-Generierung berücksichtigt die KI automatisch folgende Prioritäten:
1. **Globale Basis-Regeln** (Grundkonfiguration).
2. **Praxis-Spezifische Vorrang-Regeln** (Aus den Praxisdetails).
3. **⚡ Priorisierte Sonderanweisung** (Direkteingabe im Dialog hat **allerhöchste Priorität**).
"""
    },
    {
        "id": "email_webhook_integration",
        "title": "🔌 E-Mail-Import (IMAP) & REST Webhooks",
        "category": "Integrationen",
        "content": r"""
### 🔌 E-Mail-Import (IMAP) & REST Webhooks (Jira/GitLab)

Verknüpfen Sie das Support-Cockpit mit Ihren bestehenden Postfächern und Ticket-Systemen.

#### 1. 📬 Automatische E-Mail-Import (IMAP)
- **Funktionsweise**: Das Support-Cockpit fragt in konfigurierbaren Intervallen Ihr Support-Postfach per IMAP ab.
- **Automatische Fallentwürfe**: Neue E-Mails werden automatisch als unbestätigte Fall-Entwürfe im Cockpit gelistet. Sie können den Entwurf mit einem Klick prüfen, einer Praxis zuordnen und übernehmen.

#### 2. 🔗 REST Webhooks (GitLab, Jira, Custom APIs)
- **Outbound-Webhooks**: Konfigurieren Sie unter `⚙ Profil & Einstellungen` -> `🔌 Webhooks` Ihre Ziel-URLs.
- **Automatische Payloads**: Bei Erstellung, Bearbeitung oder Abschluss eines Falls sendet das System strukturierte JSON-Payloads an Ihr präferiertes Ticketsystem (Jira / GitLab / In-House REST API).
"""
    },
    {
        "id": "p2p",
        "title": "🔄 Peer-to-Peer Sync (Dezentraler Kollegen-Abgleich)",
        "category": "Sync",
        "content": r"""
### 🔄 Peer-to-Peer Sync (Dezentraler Kollegen-Abgleich)

Arbeiten Sie auch ohne zentralen Datenbank-Server nahtlos mit Kollegen zusammen.

#### Schritt-für-Schritt Anleitung:
1. Klicken Sie in der Menüleiste auf **🔄 Datenaustausch** -> **🔄 P2P-Sync**.
2. **Kollegen auswählen**: Wählen Sie den Arbeitsplatz des Kollegen aus (z. B. über ein gemeinsames Netzlaufwerk oder einen Synchronisations-Ordner).
3. **Versionsvergleich**: Das System vergleicht die Zeitstempel aller Fälle und Kundenstämme.
4. **Diff-Dialog**: Im Konflikt-Dialog sehen Sie auf einen Blick:
   - *Neu hinzugekommene Fälle des Kollegen*
   - *Aktualisierte Notizen / Zeitleisteneinträge*
   - *Konflikte bei zeitgleichen Änderungen*
5. Klicken Sie auf **🚀 Synchronisation durchführen**, um die Stände sicher zusammenzuführen.
"""
    },
    {
        "id": "analytics_kpi_dashboard",
        "title": "📊 Auswertungs- & KPI-Dashboard",
        "category": "Auswertungen",
        "content": r"""
### 📊 Auswertungs- & KPI-Dashboard

Analysieren Sie Support-Aufkommen, Bearbeitungszeiten und Engpässe in Echtzeit.

#### Dashboard öffnen (`Strg + 4`):
- Klicken Sie auf **Auswertungen & Kennzahlen** in der Menüleiste oder drücken Sie `Strg + 4`.

#### Kennzahlen im Überblick:
- **📋 Fälle Gesamt**: Gesamtzahl aller erfassten Vorgänge.
- **⏳ Offene Fälle**: Aktuell zu bearbeitende Vorgänge.
- **✓ Erledigt (%)**: Erfolgsquote und Anzahl gelöster Fälle.
- **⚠ Überfällig**: Offene Fälle mit abgelaufener Wiedervorlage / Frist.
- **⏱ Ø Bearbeitung**: Durchschnittliche Durchlaufzeit von Fallerstellung bis Abschluss.
- **⭐ VIP-Quote**: Anteil der Fälle von VIP-Praxen.

#### Berichte kopieren:
- Nutzen Sie den Button **📋 Statistik-Bericht kopieren**, um eine vollständige Markdown-Zusammenfassung aller Zahlen für Ihre Teambesprechung in die Zwischenablage zu kopieren.
"""
    },
    {
        "id": "advanced_search_filters",
        "title": "🔍 Erweitertes Suchsystem & Such-Tokens",
        "category": "Grundlagen",
        "content": r"""
### 🔍 Erweitertes Suchsystem & Such-Tokens

Finden Sie jeden Fall in Sekundenschnelle über intelligente Suchfilter.

#### 1. Schnellfilter-Buttons
Über der Fallliste finden Sie direkte Filter-Buttons:
- **`[Alle]`**: Alle Fälle anzeigen.
- **`[🔥 Dringend]`**: Filtert auf Fälle mit hohem Dringlichkeits-Score (> 50 Pkt.).
- **`[🔔 Wiedervorlagen]`**: Zeigt alle heute oder früher fälligen Wiedervorlagen.
- **`[🏢 Intern]`**: Zeigt nur rein interne Aufgaben.

#### 2. Such-Tokens in der Suchleiste (`Strg + F`):
Sie können in der Suchleiste Freitext mit Präfix-Tokens kombinieren:
- `is:internal` / `is:customer`: Nach Fallart filtern.
- `vip:true`: Nur Fälle von VIP-Praxen anzeigen.
- `reminder:due`: Nur fällige Wiedervorlagen anzeigen.
- `actor:support` / `actor:dev` / `actor:tech`: Nach aktueller Zuständigkeit filtern.
- `status:open` / `status:closed`: Nach Fallstatus filtern.
"""
    },
    {
        "id": "zip_backup_restore",
        "title": "📦 Komplett-ZIP Backup & Wiederherstellung",
        "category": "Konfiguration",
        "content": r"""
### 📦 Komplett-ZIP Backup & Wiederherstellung

Sichern Sie Ihren gesamten Datenbestand inkl. aller Fälle, Kundendaten, Formulare und Dateianhänge in einem ZIP-Archiv.

#### 1. Backup erstellen
1. Öffnen Sie **⚙ Profil & Einstellungen** (`👤`) -> Reiter **📦 Sicherung & Wiederherstellung**.
2. Klicken Sie auf **💾 Komplett-Backup erstellen...**.
3. Wählen Sie den Zielordner – das System erstellt ein zeitstempeltes Archiv (z. B. `SupportCockpit_Backup_2026-09-03.zip`).

#### 2. Backup wiederherstellen
1. Klicken Sie auf **📥 Backup wiederherstellen...**.
2. Wählen Sie das gewünschte ZIP-Archiv aus.
3. **Automatische Sicherheitssicherung**: Vor dem Überschreiben erstellt das System automatisch ein Sicherheits-Backup des aktuellen Datenstands, sodass Sie jederzeit zurückrollen können.
"""
    },
    {
        "id": "storage_paths",
        "title": "📁 Speicherorte, Datenstruktur & Exe-Betrieb",
        "category": "Konfiguration",
        "content": r"""
### 📁 Speicherorte, Datenstruktur & Portable Exe-Betrieb

Das Support-Cockpit ist vollkommen mobil und speichert Arbeitsdaten getrennt von den Programmdateien.

#### 1. Datenordner frei festlegen
- Öffnen Sie **⚙ Profil & Einstellungen** (`👤`) -> Reiter **📁 Speicherort & Pfade**.
- Wählen Sie über **📁 Ordner wählen** Ihren gewünschten Speicherort (z. B. lokales Laufwerk `D:\SupportDaten` oder einen Netzwert-Ordner).

#### 2. Verhalten beim Betrieb als Einzeldatei (`.exe`)
- Wird die Anwendung als portable `.exe` gestartet, werden keine Dateien im Ausführungsverzeichnis (z. B. `Program Files`) geschrieben.
- Die Benutzerkonfiguration wird sicher in Ihrem Benutzerprofil abgelegt:
  - Windows: `%APPDATA%\SupportCockpit\user_config.json`
- Fehlt die Konfiguration, wird automatisch der Ordner `Dokumente\SupportCockpitData` verwendet.
"""
    },
    {
        "id": "shortcuts",
        "title": "⌨ Tastenkürzel (Hotkeys) Übersicht",
        "category": "Tastenkürzel",
        "content": r"""
### ⌨ Tastenkürzel (Shortcuts) Übersicht

Arbeiten Sie noch schneller mit Tastenkürzeln:

| Funktion | Tastenkürzel |
| :--- | :--- |
| **Neuer Fall** | `Strg + N` |
| **Fall speichern** | `Strg + S` |
| **Fall erledigen / archivieren** | `Strg + Umschalt + A` |
| **Fall exportieren** | `Strg + E` |
| **Einstellungen öffnen** | `Strg + P` |
| **Snippet-Picker (Textbausteine)** | `Strg + M` |
| **Wiki-Suche fokussieren** | `Strg + W` |
| **Kundensuche / Fallsuche** | `Strg + F` |
| **Screenshot einfügen** | `Strg + V` |
| **Cockpit-Ansicht** | `Strg + 1` |
| **Kanban-Board** | `Strg + 2` |
| **Tabellen-Ansicht** | `Strg + 3` |
| **Auswertungen & Kennzahlen** | `Strg + 4` |
| **Theme umschalten** | `Strg + T` |
| **Handbuch & Hilfe** | `F1` |

*Tipp: Alle Hotkeys können in den Einstellungen (`⚙ Profil & Einstellungen` -> `⌨ Tastenkürzel & Scoring`) individuell angepasst und erfasst werden.*
"""
    },
    {
        "id": "faq_troubleshooting",
        "title": "❓ Häufige Fragen & Fehlerbehebung (FAQ)",
        "category": "Tastenkürzel",
        "content": r"""
### ❓ Häufige Fragen & Fehlerbehebung (FAQ)

#### Q: Die KI zeigt einen roten Status (Offline) an. Was tun?
- **A**: Öffnen Sie `⚙ Profil & Einstellungen` -> `🤖 KI & NLP` und klicken Sie auf **`▶ Ollama Server Starten`**. Stellen Sie sicher, dass Ollama auf Ihrem PC installiert ist (`ollama.com`).

#### Q: Wie übertrage ich meine Daten auf einen neuen PC?
- **A**: Erstellen Sie unter `⚙ Profil & Einstellungen` -> `📦 Sicherung & Wiederherstellung` ein **Komplett-Backup (ZIP)**. Spielen Sie diese ZIP-Datei auf dem neuen PC über **Backup wiederherstellen** ein.

#### Q: Wie setze ich die Spaltenbreiten im Cockpit zurück?
- **A**: Öffnen Sie `⚙ Profil & Einstellungen` -> `🎨 Erscheinungsbild` und klicken Sie unter *Gespeicherte Spaltenbreiten* auf **↻ Alle Spaltenbreiten auf Standard zurücksetzen**.

#### Q: Kann ich eigene Tastenkürzel definieren?
- **A**: Ja! Unter `⚙ Profil & Einstellungen` -> `⌨ Tastenkürzel & Scoring` können Sie für jede Aktion und für Ihre Textbausteine eigene Hotkeys per Tastendruck erfassen.
"""
    }
]


class HelpDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        from services.i18n_service import tr

        w, h = DIALOG_DIMENSIONS["help"]
        self.title(tr("dialog_titles.help", "📖 Handbuch & Anwendungsdokumentation"))
        self.geometry(f"{w}x{h}")
        self.minsize(960, 600)
        from utils.ui_utils import center_window
        center_window(self, w, h)

        # Make modal window
        self.transient(parent)
        self.grab_set()

        self.articles = self.get_localized_articles()
        self.filtered_articles = list(self.articles)
        self.active_article = self.articles[0]

        self.create_widgets()
        self.select_article(self.active_article["id"])

    def get_localized_articles(self) -> list[dict]:
        from services.i18n_service import tr
        result = []
        for art in HELP_ARTICLES:
            art_id = art["id"]
            result.append({
                "id": art_id,
                "title": tr(f"help_content.{art_id}.title", art["title"]),
                "category": tr(f"help_content.{art_id}.category", art["category"]),
                "content": tr(f"help_content.{art_id}.content", art["content"]),
            })
        return result

    def create_widgets(self):
        from services.i18n_service import tr

        # Main Layout: Top search bar, Left navigation list, Right detail view
        top_bar = ctk.CTkFrame(self, height=50, corner_radius=0)
        top_bar.pack(fill="x", side="top", padx=10, pady=(10, 5))

        ctk.CTkLabel(top_bar, text=tr("help_dialog.header", "📖 Handbuch & Hilfe"), font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10)

        self.search_entry = ctk.CTkEntry(top_bar, placeholder_text=tr("help_dialog.search_placeholder", "🔍 Themen & Stichworte suchen..."), width=320)
        self.search_entry.pack(side="right", padx=10)
        self.search_entry.bind("<KeyRelease>", self.on_search_changed)

        body_frame = ctk.CTkFrame(self, fg_color="transparent")
        body_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        # Left Sidebar (Article list)
        left_frame = ctk.CTkFrame(body_frame, width=280)
        left_frame.pack(side="left", fill="y", padx=(0, 5), pady=0)
        left_frame.pack_propagate(False)

        ctk.CTkLabel(left_frame, text=tr("help_dialog.nav_title", "Themenübersicht"), font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))

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
        from services.i18n_service import tr

        for w in self.nav_scroll.winfo_children():
            w.destroy()

        if not self.filtered_articles:
            ctk.CTkLabel(self.nav_scroll, text=tr("help_dialog.no_topics", "Keine Themen gefunden."), text_color="gray").pack(pady=20)
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
        article = next((a for a in self.articles if a["id"] == article_id), None)
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
            self.filtered_articles = list(self.articles)
        else:
            self.filtered_articles = [
                a for a in self.articles
                if query in a["title"].lower() or query in a["content"].lower() or query in a["category"].lower()
            ]

        if self.filtered_articles and self.active_article not in self.filtered_articles:
            self.active_article = self.filtered_articles[0]
            self.select_article(self.active_article["id"])

        self.render_nav_list()
