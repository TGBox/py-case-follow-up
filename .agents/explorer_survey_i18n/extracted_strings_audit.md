# Detailed Audit of Extracted Hardcoded UI Strings in `src/`

**Total Files with Unlocalized String Literals:** 29

**Total Hardcoded String Occurrences Found:** 238

## Summary Table by File

| File Path | Hardcoded Occurrences | Key Categories |
| :--- | :---: | :--- |
| `src/ui/dialogs/customer_form_builders.py` | 57 | placeholder_text, text, values_item |
| `src/ui/dialogs/schema_builder_dialog.py` | 20 | placeholder_text, text, title |
| `src/ui/dialogs/profile_settings_dialog.py` | 19 | placeholder_text, text, title |
| `src/ui/dialogs/ai_assistant_dialog.py` | 14 | text |
| `src/ui/dialogs/cobra_import_dialog.py` | 13 | placeholder_text, text, title, values_item |
| `src/ui/dialogs/customer_management_dialog.py` | 13 | placeholder_text, text |
| `src/ui/dialogs/template_manager_dialog.py` | 13 | placeholder_text, text, title |
| `src/ui/dialogs/colleague_management_dialog.py` | 10 | placeholder_text, text |
| `src/ui/dialogs/case_print_dialog.py` | 9 | text, title |
| `src/services/snippet_service.py` | 8 | title |
| `src/services/seed_case_data.py` | 7 | title |
| `src/ui/dialogs/email_calendar_dialog.py` | 7 | placeholder_text, text, title |
| `src/ui/dialogs/email_draft_dialog.py` | 7 | placeholder_text, text |
| `src/ui/dialogs/followup_flyout_dialog.py` | 6 | text |
| `src/ui/dialogs/new_case_dialog.py` | 6 | placeholder_text |
| `src/ui/dialogs/profile_settings_ai_tab.py` | 4 | placeholder_text, text |
| `src/ui/dialogs/snippet_management_dialog.py` | 4 | placeholder_text |
| `src/ui/app.py` | 3 | text, title |
| `src/ui/dialogs/followup_dialog.py` | 3 | placeholder_text, title |
| `src/ui/dialogs/zip_import_dialog.py` | 3 | title |
| `src/ui/dialogs/calendar_export_dialog.py` | 2 | text, title |
| `src/ui/dialogs/email_import_dialog.py` | 2 | text |
| `src/ui/widgets/dynamic_form_widget.py` | 2 | title |
| `src/ui/dialogs/snippet_picker_dialog.py` | 1 | title |
| `src/ui/views/analytics_view.py` | 1 | message |
| `src/ui/views/cockpit_layout_builders.py` | 1 | text |
| `src/ui/views/cockpit_view.py` | 1 | message |
| `src/ui/widgets/case_list_widget.py` | 1 | text |
| `src/ui/widgets/date_picker.py` | 1 | title |

---

## Detailed File-by-File Breakdown

### `src/ui/dialogs/customer_form_builders.py` (57 occurrences)

| Line | Type | Function / Widget | String Literal |
| :---: | :--- | :--- | :--- |
| 70 | `values_item` | `CTkOptionMenu` | "Name (A-Z)" |
| 70 | `values_item` | `CTkOptionMenu` | "Praxisnummer / ID" |
| 70 | `values_item` | `CTkOptionMenu` | "Zeit seit letztem Kontakt" |
| 80 | `text` | `CTkButton` | "↑ Aufst." |
| 128 | `placeholder_text` | `CTkEntry` | "CUST-..." |
| 138 | `placeholder_text` | `CTkEntry` | "z.B. Hausarztpraxis Dr. Med. Weber" |
| 144 | `placeholder_text` | `CTkEntry` | "z.B. Ehem. Praxis Dr. Alt" |
| 154 | `placeholder_text` | `CTkEntry` | "Frau / Herr / Dr." |
| 160 | `placeholder_text` | `CTkEntry` | "Vorname..." |
| 166 | `placeholder_text` | `CTkEntry` | "Nachname..." |
| 176 | `placeholder_text` | `CTkEntry` | "z.B. Hauptstr. 10" |
| 182 | `placeholder_text` | `CTkEntry` | "12345" |
| 188 | `placeholder_text` | `CTkEntry` | "Ort..." |
| 203 | `placeholder_text` | `CTkEntry` | "0711-..." |
| 209 | `placeholder_text` | `CTkEntry` | "Durchwahl..." |
| 215 | `placeholder_text` | `CTkEntry` | "Privat..." |
| 224 | `placeholder_text` | `CTkEntry` | "Zweitnr...." |
| 230 | `placeholder_text` | `CTkEntry` | "Drittnr...." |
| 236 | `placeholder_text` | `CTkEntry` | "0171-..." |
| 242 | `placeholder_text` | `CTkEntry` | "Mobil privat..." |
| 252 | `placeholder_text` | `CTkEntry` | "zweit-email@praxis.de" |
| 258 | `placeholder_text` | `CTkEntry` | "dritt-email@praxis.de" |
| 274 | `placeholder_text` | `CTkEntry` | "https://praxis-beispiel.de" |
| 277 | `text` | `CTkButton` | "🔗 Öffnen" |
| 291 | `placeholder_text` | `CTkEntry` | "104" |
| 305 | `placeholder_text` | `CTkEntry` | "DSC..." |
| 311 | `placeholder_text` | `CTkEntry` | "DSCNEU..." |
| 326 | `placeholder_text` | `CTkEntry` | "z.B. Erreichbarkeit, Wünsche..." |
| 331 | `text` | `CTkCheckBox` | "⭐ VIP-Kunde (erhöht den Dringlichkeits-Score um +30)" |
| 357 | `text` | `CTkButton` | "+ Kontakt hinzufügen" |
| 143 | `text` | `CTkLabel` | "Praxisname (Alt):" |
| 153 | `text` | `CTkLabel` | "Anrede:" |
| 159 | `text` | `CTkLabel` | "Vorname:" |
| 165 | `text` | `CTkLabel` | "Nachname:" |
| 175 | `text` | `CTkLabel` | "🏠 Straße & Hausnr.:" |
| 181 | `text` | `CTkLabel` | "PLZ:" |
| 187 | `text` | `CTkLabel` | "Ort:" |
| 195 | `text` | `CTkLabel` | "📞 Telefonnummern (Cobra Export)" |
| 202 | `text` | `CTkLabel` | "Telefon Hauptnr.:" |
| 208 | `text` | `CTkLabel` | "Telefon direkt:" |
| 214 | `text` | `CTkLabel` | "Telefon privat:" |
| 223 | `text` | `CTkLabel` | "Telefon 2:" |
| 229 | `text` | `CTkLabel` | "Telefon 3:" |
| 235 | `text` | `CTkLabel` | "Mobil:" |
| 241 | `text` | `CTkLabel` | "Mobil privat:" |
| 251 | `text` | `CTkLabel` | "✉ E-Mail 2:" |
| 257 | `text` | `CTkLabel` | "✉ E-Mail 3:" |
| 269 | `text` | `CTkLabel` | "🌐 Webseite:" |
| 290 | `text` | `CTkLabel` | "🖥 VM-Nr.:" |
| 297 | `text` | `CTkLabel` | "🔢 Instanz-Nr.:" |
| 304 | `text` | `CTkLabel` | "🏷 DSC:" |
| 310 | `text` | `CTkLabel` | "🏷 DSCNEU:" |
| 318 | `text` | `CTkLabel` | "👥 Weitere Ansprechpartner (1 Name pro Zeile):" |
| 325 | `text` | `CTkLabel` | "📝 Allgemeine Notizen:" |
| 337 | `text` | `CTkLabel` | "⚡ Praxisspezifische KI-Regeln (haben VORRANG vor Basis-Regeln):" |
| 342 | `text` | `CTkLabel` | "1 Regel pro Zeile (z. B. 'Duzen erwünscht (Herr Schmidt)', 'Betreff mit [SCHMIDT] beginnen')" |
| 356 | `text` | `CTkLabel` | "👥 Ansprechpartner & Kontakte" |

### `src/ui/dialogs/schema_builder_dialog.py` (20 occurrences)

| Line | Type | Function / Widget | String Literal |
| :---: | :--- | :--- | :--- |
| 13 | `title` | `title` | "🆕 Neues Formular (Schema) erstellen" |
| 27 | `placeholder_text` | `CTkEntry` | "z. B. Abrechnung & Tarife" |
| 31 | `placeholder_text` | `CTkEntry` | "z. B. schema_abrechnung" |
| 35 | `placeholder_text` | `CTkEntry` | "Optionale Beschreibung des Formulars" |
| 82 | `title` | `title` | "In-App Formular-Baukasten (Schemata verwalten)" |
| 177 | `placeholder_text` | `CTkEntry` | "Abhängig von Feld-ID" |
| 180 | `placeholder_text` | `CTkEntry` | "Bei Wert (z. B. Sonstiges)" |
| 184 | `placeholder_text` | `CTkEntry` | ".pdf, .log, .png" |
| 52 | `text` | `configure` | "Bitte Anzeigenamen eingeben." |
| 239 | `text` | `configure` | "📥 Zu Realdaten übernehmen" |
| 252 | `text` | `configure` | "✓ In Realdaten enthalten" |
| 254 | `text` | `configure` | "📥 Zu Realdaten übernehmen" |
| 303 | `text` | `CTkButton` | "Pflicht +/-" |
| 24 | `text` | `CTkLabel` | "Neues Formular-Schema definieren" |
| 26 | `text` | `CTkLabel` | "Anzeigename (Titel) *:" |
| 30 | `text` | `CTkLabel` | "Schema-ID (optional):" |
| 34 | `text` | `CTkLabel` | "Beschreibung:" |
| 107 | `text` | `CTkLabel` | "Formular auswählen:" |
| 175 | `text` | `CTkLabel` | "↳ Bedingte Logik (If/Else):" |
| 183 | `text` | `CTkLabel` | "↳ Dateitypen:" |

### `src/ui/dialogs/profile_settings_dialog.py` (19 occurrences)

| Line | Type | Function / Widget | String Literal |
| :---: | :--- | :--- | :--- |
| 253 | `placeholder_text` | `CTkEntry` | "z. B. Support, Entwicklung, Technik" |
| 258 | `placeholder_text` | `CTkEntry` | "z.B. 4012" |
| 263 | `placeholder_text` | `CTkEntry` | "beispiel@support.de" |
| 268 | `placeholder_text` | `CTkEntry` | "0170 / 1234567" |
| 273 | `placeholder_text` | `CTkEntry` | "z. B. Mit freundlichen Grüßen, Ihr Support-Team (Tel. 0800-12345)" |
| 278 | `text` | `CTkInputDialog` | "Geben Sie den Namen des neuen Mitarbeiters ein:" |
| 278 | `title` | `CTkInputDialog` | "Neues Mitarbeiter-Profil anlegen" |
| 496 | `placeholder_text` | `CTkEntry` | "Pfad zum Datenordner..." |
| 542 | `title` | `askdirectory` | "Datenordner auswählen" |
| 549 | `title` | `askopenfilename` | "Datei auswählen" |
| 565 | `placeholder_text` | `CTkEntry` | "https://wiki.meinepraxis.de/api" |
| 570 | `placeholder_text` | `CTkEntry` | "Token ID" |
| 575 | `placeholder_text` | `CTkEntry` | "Token Secret" |
| 780 | `text` | `configure` | "✅ Einstellungen & Pfade gespeichert!" |
| 873 | `title` | `asksaveasfilename` | "Datensicherung als ZIP speichern" |
| 896 | `title` | `askopenfilename` | "Datensicherung (ZIP-Datei) auswählen" |
| 697 | `text` | `configure` | "⚠ Benutzername darf nicht leer sein!" |
| 656 | `text` | `CTkLabel` | "Prioritäts-Scoring Punkte" |
| 660 | `text` | `CTkLabel` | "VIP-Bonus (Punkte):" |

### `src/ui/dialogs/ai_assistant_dialog.py` (14 occurrences)

| Line | Type | Function / Widget | String Literal |
| :---: | :--- | :--- | :--- |
| 125 | `text` | `CTkLabel` | "Prüfe Status..." |
| 190 | `text` | `CTkLabel` | "🤖 KI verarbeitet Anfrage..." |
| 350 | `text` | `CTkButton` | "🔄 Zusammenfassung neu generieren" |
| 448 | `text` | `CTkButton` | "🔄 Lösungssuche erneut ausführen" |
| 508 | `text` | `CTkButton` | "🔄 Antwort-Entwurf generieren" |
| 343 | `text` | `configure` | "⚠ KI global deaktiviert (Schalter oben rechts auf OFF). Buttons deaktiviert." |
| 421 | `text` | `configure` | "✓ Zusammenfassung in Zwischenablage kopiert." |
| 435 | `text` | `configure` | "✓ KI-Zusammenfassung als Zeitleisten-Eintrag gespeichert." |
| 173 | `text` | `CTkButton` | "Schließen" |
| 200 | `text` | `CTkLabel` | "Bitte einen Moment gedulden — Modell generiert Antwort" |
| 361 | `text` | `CTkButton` | "📋 In Zwischenablage kopieren" |
| 371 | `text` | `CTkButton` | "📌 In Fall-Zeitleiste einfügen" |
| 442 | `text` | `CTkLabel` | "💡 Automatisch ermittelte Lösungsschritte & Wiki-Referenzen:" |
| 520 | `text` | `CTkButton` | "✉ In E-Mail-Entwurf öffnen" |

### `src/ui/dialogs/cobra_import_dialog.py` (13 occurrences)

| Line | Type | Function / Widget | String Literal |
| :---: | :--- | :--- | :--- |
| 58 | `placeholder_text` | `CTkEntry` | "Datei auswählen (*.csv, *.txt, *.json)..." |
| 78 | `values_item` | `CTkOptionMenu` | "Bestehende Praxen aktualisieren (Update)" |
| 78 | `values_item` | `CTkOptionMenu` | "Bestehende überspringen (Skip)" |
| 78 | `values_item` | `CTkOptionMenu` | "Alle als neu anlegen" |
| 86 | `text` | `CTkLabel` | "Bitte wählen Sie eine Export-Datei aus." |
| 111 | `title` | `askopenfilename` | "Cobra CRM Export-Datei auswählen" |
| 46 | `text` | `CTkLabel` | "🐍 Cobra CRM Praxen-Import Assistent" |
| 47 | `text` | `CTkLabel` | "Importieren Sie Praxen aus Cobra CRM Exporte-Dateien (.csv, .txt, .json)." |
| 53 | `text` | `CTkLabel` | "1. Cobra Export-Datei auswählen:" |
| 61 | `text` | `CTkButton` | "📁 Durchsuchen..." |
| 70 | `text` | `CTkLabel` | "2. Cobra Spaltenzuordnung (Feld-Mapper):" |
| 76 | `text` | `CTkLabel` | "3. Konfliktbehandlung für bestehende Praxen:" |
| 125 | `text` | `configure` | "⚠ Keine Datensätze in der Datei gefunden." |

### `src/ui/dialogs/customer_management_dialog.py` (13 occurrences)

| Line | Type | Function / Widget | String Literal |
| :---: | :--- | :--- | :--- |
| 79 | `text` | `CTkButton` | "🗑 Entfernen" |
| 97 | `placeholder_text` | `CTkEntry` | "z.B. Dr. Hans Weber" |
| 105 | `placeholder_text` | `CTkEntry` | "z.B. Praxisinhaber, Abrechnung..." |
| 117 | `placeholder_text` | `CTkEntry` | "weber@praxis.de" |
| 125 | `placeholder_text` | `CTkEntry` | "030 / 1234567" |
| 134 | `placeholder_text` | `CTkEntry` | "z.B. Erreichbar Mo-Do Vormittag" |
| 46 | `text` | `configure` | "⚠ Keine Webseite eingetragen!" |
| 96 | `text` | `CTkLabel` | "Name *:" |
| 104 | `text` | `CTkLabel` | "Rolle / Funktion:" |
| 116 | `text` | `CTkLabel` | "E-Mail:" |
| 124 | `text` | `CTkLabel` | "Telefon:" |
| 133 | `text` | `CTkLabel` | "Notiz:" |
| 216 | `text` | `CTkLabel` | "Keine Praxen gefunden." |

### `src/ui/dialogs/template_manager_dialog.py` (13 occurrences)

| Line | Type | Function / Widget | String Literal |
| :---: | :--- | :--- | :--- |
| 58 | `placeholder_text` | `CTkEntry` | "z. B. gitlab_dev_ticket" |
| 69 | `placeholder_text` | `CTkEntry` | "z. B. GitLab / Dev-Ticket" |
| 79 | `placeholder_text` | `CTkEntry` | "Kurze Beschreibung des Formats..." |
| 216 | `title` | `title` | "📄 Export-Vorlagen verwalten" |
| 57 | `text` | `CTkLabel` | "Vorlage-ID *:" |
| 68 | `text` | `CTkLabel` | "Anzeigename *:" |
| 78 | `text` | `CTkLabel` | "Beschreibung:" |
| 87 | `text` | `CTkLabel` | "Ziel-Aktion / Typ:" |
| 94 | `text` | `CTkLabel` | "Zugeordnete Formular-Schemas:" |
| 105 | `text` | `CTkLabel` | "Erforderliche Pflichtfelder vor Export:" |
| 125 | `text` | `CTkLabel` | "Jinja2 Template Text (Markdown / Text):" |
| 296 | `text` | `CTkButton` | "✓ In Realdaten enthalten" |
| 298 | `text` | `CTkButton` | "📥 Zu Realdaten übernehmen" |

### `src/ui/dialogs/colleague_management_dialog.py` (10 occurrences)

| Line | Type | Function / Widget | String Literal |
| :---: | :--- | :--- | :--- |
| 100 | `placeholder_text` | `CTkEntry` | "z. B. mmueller" |
| 104 | `placeholder_text` | `CTkEntry` | "z. B. Max Müller" |
| 113 | `placeholder_text` | `CTkEntry` | "z. B. 4012" |
| 117 | `placeholder_text` | `CTkEntry` | "z. B. m.mueller@praxis.de" |
| 121 | `placeholder_text` | `CTkEntry` | "z. B. 0170 1234567" |
| 125 | `placeholder_text` | `CTkEntry` | "z. B. Zuständig für PVS-Schnittstellen..." |
| 130 | `text` | `CTkCheckBox` | "⚠ Kollege ist aktuell abwesend (Urlaub / Krankheit)" |
| 135 | `placeholder_text` | `CTkEntry` | "Abwesenheitsgrund (z. B. Urlaub bis 30.08.)..." |
| 233 | `text` | `configure` | "➕ Neuen Mitarbeiter anlegen" |
| 184 | `text` | `CTkLabel` | "Keine Einträge gefunden." |

### `src/ui/dialogs/case_print_dialog.py` (9 occurrences)

| Line | Type | Function / Widget | String Literal |
| :---: | :--- | :--- | :--- |
| 275 | `title` | `asksaveasfilename` | "Fallbericht speichern" |
| 48 | `text` | `CTkLabel` | "Wählen Sie aus, welche Elemente im Druckbericht erscheinen sollen:" |
| 54 | `text` | `CTkCheckBox` | "Praxis & Kundendaten" |
| 55 | `text` | `CTkCheckBox` | "Formularfelder" |
| 56 | `text` | `CTkCheckBox` | "Bilder & Anhänge am Ende" |
| 58 | `text` | `CTkLabel` | "Zeitleiste / Notizen-Verlauf (einzelne Einträge abwählen):" |
| 98 | `text` | `CTkButton` | "🌐 HTML-Bericht" |
| 107 | `text` | `CTkButton` | "💾 Speichern..." |
| 64 | `text` | `CTkLabel` | "Keine Notizen in der Zeitleiste." |

### `src/services/snippet_service.py` (8 occurrences)

| Line | Type | Function / Widget | String Literal |
| :---: | :--- | :--- | :--- |
| 7 | `title` | `Snippet` | "📸 Rückfrage: Screenshots & Uhrzeit anfordern" |
| 15 | `title` | `Snippet` | "🛠 Ersthilfe: PVS & Support-Dienst neustarten" |
| 22 | `title` | `Snippet` | "🔍 DB-Check: SQL Fehler-Log Abfrage" |
| 29 | `title` | `Snippet` | "✅ Fallabschluss & Dankeschön" |
| 37 | `title` | `Snippet` | "🩺 Telematikinfrastruktur: Konnektor & SMC-B Prüfung" |
| 44 | `title` | `Snippet` | "📑 Abrechnung: Zuzahlungs- & ESOL-Korrektur weitergeleitet" |
| 51 | `title` | `Snippet` | "💾 Backup-Anforderung für Fehleranalyse" |
| 58 | `title` | `Snippet` | "🔄 Quartalsupdate Hinweis & Vorbereitung" |

### `src/services/seed_case_data.py` (7 occurrences)

| Line | Type | Function / Widget | String Literal |
| :---: | :--- | :--- | :--- |
| 214 | `title` | `Classification` | "Alte Abrechnung Q1 gelöst" |
| 243 | `title` | `Classification` | "Uralter Fall aus dem Vormonat" |
| 272 | `title` | `Classification` | "Frische Nachforderung ohne DB-Dump" |
| 303 | `title` | `Classification` | "Kundenwunsch: Schnell-Button für eRezept-Export" |
| 342 | `title` | `Classification` | "Kartenleser-Treiber nach Windows-Update getrennt" |
| 377 | `title` | `Classification` | "Alte Nachforderung aus Vorquartal (Archiviert)" |
| 405 | `title` | `Classification` | "Absturz bei PVS-GKV Abrechnungsexport" |

### `src/ui/dialogs/email_calendar_dialog.py` (7 occurrences)

| Line | Type | Function / Widget | String Literal |
| :---: | :--- | :--- | :--- |
| 72 | `placeholder_text` | `CTkEntry` | "praxis@beispiel.de..." |
| 79 | `placeholder_text` | `CTkEntry` | "Betreff eingeben..." |
| 206 | `title` | `asksaveasfilename` | "Kalenderdatei (.ics) speichern" |
| 71 | `text` | `CTkLabel` | "Empfänger (E-Mail):" |
| 78 | `text` | `CTkLabel` | "Betreff:" |
| 88 | `text` | `CTkLabel` | "E-Mail Nachrichtentext:" |
| 91 | `text` | `CTkButton` | "🧩 Textbaustein" |

### `src/ui/dialogs/email_draft_dialog.py` (7 occurrences)

| Line | Type | Function / Widget | String Literal |
| :---: | :--- | :--- | :--- |
| 149 | `text` | `CTkLabel` | "Prüfe KI-Status..." |
| 182 | `placeholder_text` | `CTkEntry` | "praxis@beispiel.de oder Name / Praxis eingeben..." |
| 192 | `text` | `CTkButton` | "📇 Praxiskartei ▾" |
| 217 | `text` | `CTkLabel` | "🔍 Kontakte aus Praxiskartei (Klicken zum Übernehmen):" |
| 246 | `placeholder_text` | `CTkEntry` | "Betreff eingeben..." |
| 258 | `text` | `CTkButton` | "🧩 Textbaustein" |
| 400 | `text` | `CTkLabel` | "Keine passenden Praxiskontakte gefunden." |

### `src/ui/dialogs/followup_flyout_dialog.py` (6 occurrences)

| Line | Type | Function / Widget | String Literal |
| :---: | :--- | :--- | :--- |
| 84 | `text` | `CTkButton` | "+ 1 Std." |
| 85 | `text` | `CTkButton` | "+ 2 Std." |
| 86 | `text` | `CTkButton` | "Heute 16:30" |
| 94 | `text` | `CTkButton` | "Morgen 08:00" |
| 95 | `text` | `CTkButton` | "+ 1 Tag" |
| 96 | `text` | `CTkButton` | "+ 1 Woche" |

### `src/ui/dialogs/new_case_dialog.py` (6 occurrences)

| Line | Type | Function / Widget | String Literal |
| :---: | :--- | :--- | :--- |
| 32 | `placeholder_text` | `CTkEntry` | "z.B. Praxis Dr. Weber" |
| 36 | `placeholder_text` | `CTkEntry` | "z.B. Dr. Hans Weber" |
| 40 | `placeholder_text` | `CTkEntry` | "030 / 123456" |
| 173 | `placeholder_text` | `CTkEntry` | "z. B. Zuzahlungsdatei lässt sich nicht erzeugen" |
| 179 | `placeholder_text` | `DatePickerWidget` | "z. B. 25.08.2026 09:30" |
| 208 | `placeholder_text` | `DatePickerWidget` | "z. B. 23.08.2026 16:00" |

### `src/ui/dialogs/profile_settings_ai_tab.py` (4 occurrences)

| Line | Type | Function / Widget | String Literal |
| :---: | :--- | :--- | :--- |
| 126 | `placeholder_text` | `CTkEntry` | "AIzaSy..." |
| 481 | `text` | `configure` | "🔍 Prüfe Key..." |
| 682 | `text` | `configure` | "⏳ Erstelle 'pvs-support' Modell aus Modelfile..." |
| 478 | `text` | `configure` | "⚠ Bitte API Key eingeben" |

### `src/ui/dialogs/snippet_management_dialog.py` (4 occurrences)

| Line | Type | Function / Widget | String Literal |
| :---: | :--- | :--- | :--- |
| 70 | `placeholder_text` | `CTkEntry` | "z. B. 📸 Rückfrage: Screenshots" |
| 74 | `placeholder_text` | `CTkEntry` | "z. B. Rückfrage, Anleitung, SQL" |
| 82 | `placeholder_text` | `CTkEntry` | "z. B. fehler, sql, anleitung" |
| 89 | `placeholder_text` | `CTkEntry` | "z. B. <Control-Alt-1>" |

### `src/ui/app.py` (3 occurrences)

| Line | Type | Function / Widget | String Literal |
| :---: | :--- | :--- | :--- |
| 318 | `text` | `CTkButton` | "🔔 0" |
| 687 | `title` | `asksaveasfilename` | "Komplett-Datensicherung als ZIP speichern" |
| 731 | `text` | `configure` | "🔔 0" |

### `src/ui/dialogs/followup_dialog.py` (3 occurrences)

| Line | Type | Function / Widget | String Literal |
| :---: | :--- | :--- | :--- |
| 22 | `title` | `title` | "🔔 Wiedervorlage & Nachfrage-Erinnerung" |
| 115 | `placeholder_text` | `DatePickerWidget` | "TT.MM.JJJJ 09:00" |
| 131 | `placeholder_text` | `CTkEntry` | "z. B. Beim Entwickler nach dem Stand fragen..." |

### `src/ui/dialogs/zip_import_dialog.py` (3 occurrences)

| Line | Type | Function / Widget | String Literal |
| :---: | :--- | :--- | :--- |
| 232 | `title` | `askdirectory` | "Gesamt-Zielverzeichnis wählen" |
| 238 | `title` | `askdirectory` | "Zielverzeichnis für Datendateien (data/) wählen" |
| 244 | `title` | `askdirectory` | "Zielverzeichnis für Fall-Anhänge (attachments/) wählen" |

### `src/ui/dialogs/calendar_export_dialog.py` (2 occurrences)

| Line | Type | Function / Widget | String Literal |
| :---: | :--- | :--- | :--- |
| 138 | `title` | `asksaveasfilename` | "iCalendar-Datei speichern" |
| 75 | `text` | `CTkLabel` | "Kalender-Beschreibung / Notiz:" |

### `src/ui/dialogs/email_import_dialog.py` (2 occurrences)

| Line | Type | Function / Widget | String Literal |
| :---: | :--- | :--- | :--- |
| 210 | `text` | `CTkButton` | "➕ Als neuen Fall anlegen" |
| 219 | `text` | `CTkButton` | "🗑 Ignorieren" |

### `src/ui/widgets/dynamic_form_widget.py` (2 occurrences)

| Line | Type | Function / Widget | String Literal |
| :---: | :--- | :--- | :--- |
| 67 | `title` | `title` | "🧩 Programmbereiche auswählen" |
| 532 | `title` | `askopenfilename` | "Datenbank-Backup (.backup) importieren" |

### `src/ui/dialogs/snippet_picker_dialog.py` (1 occurrences)

| Line | Type | Function / Widget | String Literal |
| :---: | :--- | :--- | :--- |
| 23 | `title` | `title` | "🧩 Textbaustein auswählen & einfügen" |

### `src/ui/views/analytics_view.py` (1 occurrences)

| Line | Type | Function / Widget | String Literal |
| :---: | :--- | :--- | :--- |
| 272 | `message` | `ToastNotification` | "Statistik-Bericht wurde in die Zwischenablage kopiert." |

### `src/ui/views/cockpit_layout_builders.py` (1 occurrences)

| Line | Type | Function / Widget | String Literal |
| :---: | :--- | :--- | :--- |
| 156 | `text` | `CTkLabel` | "🔔 Nachfragen am:" |

### `src/ui/views/cockpit_view.py` (1 occurrences)

| Line | Type | Function / Widget | String Literal |
| :---: | :--- | :--- | :--- |
| 334 | `message` | `ToastNotification` | "Für diese Praxis ist keine E-Mail-Adresse hinterlegt." |

### `src/ui/widgets/case_list_widget.py` (1 occurrences)

| Line | Type | Function / Widget | String Literal |
| :---: | :--- | :--- | :--- |
| 295 | `text` | `CTkLabel` | "🔔 Nachfragen am:" |

### `src/ui/widgets/date_picker.py` (1 occurrences)

| Line | Type | Function / Widget | String Literal |
| :---: | :--- | :--- | :--- |
| 23 | `title` | `title` | "📅 Datum auswählen" |
