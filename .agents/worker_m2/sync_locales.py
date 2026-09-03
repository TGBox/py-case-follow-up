import json
from pathlib import Path

locales_dir = Path("locales")
with open(locales_dir / "de.json", "r", encoding="utf-8") as f:
    de = json.load(f)
with open(locales_dir / "en.json", "r", encoding="utf-8") as f:
    en = json.load(f)
with open(locales_dir / "sv.json", "r", encoding="utf-8") as f:
    sv = json.load(f)

# 1. validation_messages
de["validation_messages"] = {
    "case_customer_id_required": "Fall-Kundennummer ist erforderlich.",
    "case_practice_name_required": "Fall-Praxisname ist erforderlich.",
    "contact_name_required": "Name des Ansprechpartners ist erforderlich.",
    "customer_id_required": "Kundennummer / ID ist erforderlich.",
    "display_name_required": "Anzeigename ist erforderlich.",
    "field_id_required": "Feld-ID ist erforderlich.",
    "label_required": "Bezeichnung / Label ist erforderlich.",
    "name_required": "Name ist erforderlich.",
    "practice_name_required": "Praxisname ist erforderlich.",
    "schema_id_caps_required": "Schema-ID ist erforderlich.",
    "schema_id_required": "schema_id ist erforderlich.",
    "snippet_content_required": "Snippet-Inhalt darf nicht leer sein.",
    "snippet_id_required": "Snippet-ID ist erforderlich.",
    "snippet_title_required": "Snippet-Titel ist erforderlich.",
    "timeline_author_required": "Autor für Zeitleisteneintrag ist erforderlich.",
    "timeline_timestamp_required": "Zeitstempel für Zeitleisteneintrag ist erforderlich.",
    "title_required": "Titel ist erforderlich.",
    "username_required": "Kürzel / Username ist erforderlich."
}

en["validation_messages"] = {
    "case_customer_id_required": "Case customer_id is required.",
    "case_practice_name_required": "Case practice_name is required.",
    "contact_name_required": "Contact name is required.",
    "customer_id_required": "Customer ID is required.",
    "display_name_required": "Display name is required.",
    "field_id_required": "Field ID is required.",
    "label_required": "Label is required.",
    "name_required": "Name is required.",
    "practice_name_required": "Practice name is required.",
    "schema_id_caps_required": "Schema ID is required.",
    "schema_id_required": "schema_id is required.",
    "snippet_content_required": "Snippet content cannot be empty.",
    "snippet_id_required": "Snippet ID is required.",
    "snippet_title_required": "Snippet title is required.",
    "timeline_author_required": "Timeline entry author is required.",
    "timeline_timestamp_required": "Timeline entry timestamp is required.",
    "title_required": "Title is required.",
    "username_required": "Username is required."
}

sv["validation_messages"] = {
    "case_customer_id_required": "Ärendets kund-ID krävs.",
    "case_practice_name_required": "Ärendets mottagningsnamn krävs.",
    "contact_name_required": "Kontaktpersonsnamn krävs.",
    "customer_id_required": "Kund-ID krävs.",
    "display_name_required": "Visningsnamn krävs.",
    "field_id_required": "Fält-ID krävs.",
    "label_required": "Etikett krävs.",
    "name_required": "Namn krävs.",
    "practice_name_required": "Mottagningsnamn krävs.",
    "schema_id_caps_required": "Schema-ID krävs.",
    "schema_id_required": "schema_id krävs.",
    "snippet_content_required": "Kodavsnittsinnehåll får inte vara tomt.",
    "snippet_id_required": "Kodavsnitts-ID krävs.",
    "snippet_title_required": "Kodavsnittstitel krävs.",
    "timeline_author_required": "Författare för tidslinjepost krävs.",
    "timeline_timestamp_required": "Tidsstämpel för tidslinjepost krävs.",
    "title_required": "Titel krävs.",
    "username_required": "Användarnamn krävs."
}

# 2. actors uppercase keys
actors_de_upper = {
    "CUSTOMER": "Kunde",
    "DATA_CUSTOMER": "Data-AL Kunde",
    "DATA_DEVELOPMENT": "Data-AL Entwicklung",
    "DATA_HOTLINE": "Data-AL Hotline",
    "DATA_SUPPORT": "Data-AL Support / Hotline",
    "DATA_TECH": "Data-AL Technik",
    "DEVELOPMENT": "Entwicklung",
    "HOTLINE": "Hotline",
    "SUPPORT": "Support / Hotline",
    "TECH": "Technik"
}
actors_en_upper = {
    "CUSTOMER": "Customer",
    "DATA_CUSTOMER": "Data-AL Customer",
    "DATA_DEVELOPMENT": "Data-AL Development",
    "DATA_HOTLINE": "Data-AL Hotline",
    "DATA_SUPPORT": "Data-AL Support / Hotline",
    "DATA_TECH": "Data-AL Tech Support",
    "DEVELOPMENT": "Development",
    "HOTLINE": "Hotline",
    "SUPPORT": "Support / Hotline",
    "TECH": "Tech Support"
}
actors_sv_upper = {
    "CUSTOMER": "Kund",
    "DATA_CUSTOMER": "Data-AL Kund",
    "DATA_DEVELOPMENT": "Data-AL Utveckling",
    "DATA_HOTLINE": "Data-AL Hotline",
    "DATA_SUPPORT": "Data-AL Support / Hotline",
    "DATA_TECH": "Data-AL Teknisk support",
    "DEVELOPMENT": "Utveckling",
    "HOTLINE": "Hotline",
    "SUPPORT": "Support / Hotline",
    "TECH": "Teknisk support"
}
de["actors"].update(actors_de_upper)
en["actors"].update(actors_en_upper)
sv["actors"].update(actors_sv_upper)

# 3. channels
channels_de_extra = {
    "DEV_TICKET": "GitLab-Ticket",
    "EMAIL": "E-Mail",
    "PHONE": "Telefon"
}
channels_en_extra = {
    "DEV_TICKET": "GitLab Ticket",
    "EMAIL": "Email",
    "PHONE": "Phone"
}
channels_sv_extra = {
    "DEV_TICKET": "GitLab-ärende",
    "EMAIL": "E-post",
    "PHONE": "Telefon"
}
de["channels"].update(channels_de_extra)
en["channels"].update(channels_en_extra)
sv["channels"].update(channels_sv_extra)

# 4. layouts
de["layouts"]["ANALYTICS"] = "Auswertungen & Kennzahlen"
de["layouts"]["BOARD"] = "Kanban-Board (Zuständigkeiten)"
de["layouts"]["COCKPIT"] = "Cockpit (Hauptansicht)"
de["layouts"]["TABLE"] = "Tabelle & Details (Sortier-Matrix)"

en["layouts"]["ANALYTICS"] = "Analytics & Metrics"
en["layouts"]["BOARD"] = "Kanban Board (Responsibilities)"
en["layouts"]["COCKPIT"] = "Cockpit (Main View)"
en["layouts"]["TABLE"] = "Table & Details (Sort Matrix)"

sv["layouts"]["ANALYTICS"] = "Analyser & Nyckeltal"
sv["layouts"]["BOARD"] = "Kanban-tavla (Ansvarsområden)"
sv["layouts"]["COCKPIT"] = "Cockpit (Huvudvy)"
sv["layouts"]["TABLE"] = "Tabell & Detaljer (Sorteringsmatris)"

# 5. datetime
dt_de = {
    "day_after_tomorrow": "übermorgen",
    "day_before_yesterday": "vorgestern",
    "days_ago": "vor {diff_days} Tagen",
    "hours_ago": "vor {diff_hours} Stunden",
    "in_days": "in {diff_days} Tagen",
    "in_hours": "in {diff_hours} Stunden",
    "in_minutes": "in {diff_minutes} Minuten",
    "just_now": "gerade eben",
    "last_week": "letzte Woche",
    "minutes_ago": "vor {diff_minutes} Minuten",
    "next_week": "nächste Woche",
    "o_clock": "Uhr",
    "this_week": "diese Woche",
    "today": "heute",
    "tomorrow": "morgen",
    "yesterday": "gestern"
}
dt_en = {
    "day_after_tomorrow": "day after tomorrow",
    "day_before_yesterday": "day before yesterday",
    "days_ago": "{diff_days} days ago",
    "hours_ago": "{diff_hours} hours ago",
    "in_days": "in {diff_days} days",
    "in_hours": "in {diff_hours} hours",
    "in_minutes": "in {diff_minutes} minutes",
    "just_now": "just now",
    "last_week": "last week",
    "minutes_ago": "{diff_minutes} minutes ago",
    "next_week": "next week",
    "o_clock": "",
    "this_week": "this week",
    "today": "today",
    "tomorrow": "tomorrow",
    "yesterday": "yesterday"
}
dt_sv = {
    "day_after_tomorrow": "i övermorgon",
    "day_before_yesterday": "i förrgår",
    "days_ago": "för {diff_days} dagar sedan",
    "hours_ago": "för {diff_hours} timmar sedan",
    "in_days": "om {diff_days} dagar",
    "in_hours": "om {diff_hours} timmar",
    "in_minutes": "om {diff_minutes} minuter",
    "just_now": "just nu",
    "last_week": "förra veckan",
    "minutes_ago": "för {diff_minutes} minuter sedan",
    "next_week": "nästa vecka",
    "o_clock": "",
    "this_week": "denna vecka",
    "today": "idag",
    "tomorrow": "imorgon",
    "yesterday": "igår"
}
de["datetime"] = dt_de
en["datetime"] = dt_en
sv["datetime"] = dt_sv

# 6. date_picker
de["date_picker"]["preset_plus_2days"] = "+ 2 Tage"
de["date_picker"]["preset_plus_3days"] = "+ 3 Tage"
de["date_picker"]["dialog_title"] = "📅 Datum auswählen"

en["date_picker"]["preset_plus_2days"] = "+ 2 Days"
en["date_picker"]["preset_plus_3days"] = "+ 3 Days"
en["date_picker"]["dialog_title"] = "📅 Select Date"

sv["date_picker"]["preset_plus_2days"] = "+ 2 dagar"
sv["date_picker"]["preset_plus_3days"] = "+ 3 dagar"
sv["date_picker"]["dialog_title"] = "📅 Välj datum"

# 7. demo_cases
de["demo_cases"]["c11_title"] = "Alte Nachforderung aus Vorquartal (Archiviert)"
de["demo_cases"]["c12_title"] = "Absturz bei PVS-GKV Abrechnungsexport"

en["demo_cases"]["c11_title"] = "Old subsequent claim from previous quarter (Archived)"
en["demo_cases"]["c12_title"] = "Crash during PMS statutory billing export"

sv["demo_cases"]["c11_title"] = "Gammalt efterkrav från föregående kvartal (Arkiverat)"
sv["demo_cases"]["c12_title"] = "Krasch vid export av fakturering från journalsystem"

# 8. snippet_categories
de["snippet_categories"] = {
    "billing": "Abrechnung",
    "inquiry": "Rückfrage",
    "instructions": "Anleitung",
    "maintenance": "Wartung",
    "sql_db": "SQL / Datenbank",
    "standard_reply": "Standardantwort",
    "system": "System",
    "telematics": "Telematik (TI)"
}
en["snippet_categories"] = {
    "billing": "Billing",
    "inquiry": "Inquiry",
    "instructions": "Instructions",
    "maintenance": "Maintenance",
    "sql_db": "SQL / Database",
    "standard_reply": "Standard Reply",
    "system": "System",
    "telematics": "Telematics (TI)"
}
sv["snippet_categories"] = {
    "billing": "Fakturering",
    "inquiry": "Förfrågan",
    "instructions": "Instruktioner",
    "maintenance": "Underhåll",
    "sql_db": "SQL / Databas",
    "standard_reply": "Standardsvar",
    "system": "System",
    "telematics": "Telematik (TI)"
}

# 9. snippet_picker
de["snippet_picker"]["all_categories"] = "Alle"
en["snippet_picker"]["all_categories"] = "All"
sv["snippet_picker"]["all_categories"] = "Alla"

# 10. snippets
snips_de = {
    "s1_content": "Bitte lassen Sie uns Screenshots der Fehlermeldung sowie das genaue Datum und die Uhrzeit des ersten Auftretens zukommen.",
    "s1_tags": "rückfrage, screenshot, fehler",
    "s1_title": "📸 Rückfrage: Screenshots & Uhrzeit anfordern",
    "s2_content": "Schritte zur Ersthilfe:\n1. PVS an allen Arbeitsplätzen beenden.\n2. Support-Dienst auf dem Hauptserver neustarten.\n3. PVS erneut öffnen und Funktion testen.",
    "s2_tags": "ersthilfe, neustart, pvs",
    "s2_title": "🛠 Ersthilfe: PVS & Support-Dienst neustarten",
    "s3_content": "SELECT TOP 20 * FROM dbo.SystemLog WHERE ErrorCode LIKE '%AL-%' ORDER BY LogTimestamp DESC;",
    "s3_tags": "sql, datenbank, log",
    "s3_title": "🔍 DB-Check: SQL Fehler-Log Abfrage",
    "s4_content": "Vielen Dank für Ihre Rückmeldung. Das Anliegen konnte erfolgreich gelöst werden. Wir schließen diesen Vorgang.",
    "s4_tags": "abschluss, danke, erledigt",
    "s4_title": "✅ Fallabschluss & Dankeschön",
    "s5_content": "Schritte zur TI-Entstörung:\n1. Status der SMC-B Karte im Kartenterminal prüfen (grüne LED).\n2. Konnektor über Web-Oberfläche oder Schalter kurz stromlos machen (30 Sek. warten).\n3. PVS-Dienst neu starten und TI-Verbindungstest in der Administration ausführen.",
    "s5_tags": "ti, telematik, konnektor, smc-b",
    "s5_title": "🩺 Telematikinfrastruktur: Konnektor & SMC-B Prüfung",
    "s6_content": "Sehr geehrte Praxisleitung,\n\ndie angeforderte Korrekturdatei bzw. Nachberechnung für die ESOL-Abrechnung wurde an unsere Entwicklungsabteilung weitergeleitet. Sobald die korrigierten Datensätze vorliegen, stellen wir Ihnen diese zur Verfügung.",
    "s6_tags": "abrechnung, zuzahlung, esol, korrektur",
    "s6_title": "📑 Abrechnung: Zuzahlungs- & ESOL-Korrektur weitergeleitet",
    "s7_content": "Für die detaillierte Fehleranalyse benötigen wir ein aktuelles Datenbank-Backup (.backup). Bitte legen Sie die Datei im gesicherten Fallordner oder Transferverzeichnis ab.",
    "s7_tags": "backup, datenbank, analyse",
    "s7_title": "💾 Backup-Anforderung für Fehleranalyse",
    "s8_content": "Vor Einspielen des Quartalsupdates bitte sicherstellen:\n1. Vollständige Datensicherung durchführen.\n2. Alle Arbeitsplätze schließen.\n3. Server-Dienste beenden und Update-Installer als Administrator ausführen.",
    "s8_tags": "quartalsupdate, update, wartung",
    "s8_title": "🔄 Quartalsupdate Hinweis & Vorbereitung"
}
snips_en = {
    "s1_content": "Please provide screenshots of the error message as well as the exact date and time when it first occurred.",
    "s1_tags": "inquiry, screenshot, error",
    "s1_title": "📸 Inquiry: Request Screenshots & Timestamp",
    "s2_content": "First aid steps:\n1. Close PMS on all workstations.\n2. Restart the support service on the main server.\n3. Reopen PMS and test functionality.",
    "s2_tags": "first_aid, restart, pms",
    "s2_title": "🛠 First Aid: Restart PMS & Support Service",
    "s3_content": "SELECT TOP 20 * FROM dbo.SystemLog WHERE ErrorCode LIKE '%AL-%' ORDER BY LogTimestamp DESC;",
    "s3_tags": "sql, database, log",
    "s3_title": "🔍 DB Check: SQL Error Log Query",
    "s4_content": "Thank you for your feedback. The issue has been successfully resolved. We are closing this ticket.",
    "s4_tags": "completion, thanks, done",
    "s4_title": "✅ Case Completion & Thank You",
    "s5_content": "TI troubleshooting steps:\n1. Check status of SMC-B card in terminal (green LED).\n2. Disconnect connector from power briefly (wait 30s).\n3. Restart PMS service and run TI connection test in admin console.",
    "s5_tags": "ti, telematics, connector, smc-b",
    "s5_title": "🩺 Telematics Infrastructure: Connector & SMC-B Check",
    "s6_content": "Dear Practice Management,\n\nThe requested correction file / recalculation for the ESOL billing has been forwarded to our development team. As soon as the corrected datasets are available, we will provide them to you.",
    "s6_tags": "billing, copayment, esol, correction",
    "s6_title": "📑 Billing: Copayment & ESOL Correction Forwarded",
    "s7_content": "For detailed error analysis, we require an up-to-date database backup (.backup). Please place the file in the secure case folder or transfer directory.",
    "s7_tags": "backup, database, analysis",
    "s7_title": "💾 Backup Request for Error Analysis",
    "s8_content": "Before installing the quarterly update, please ensure:\n1. Perform full data backup.\n2. Close all workstations.\n3. Stop server services and run update installer as administrator.",
    "s8_tags": "quarterly_update, update, maintenance",
    "s8_title": "🔄 Quarterly Update Notice & Preparation"
}
snips_sv = {
    "s1_content": "Vänligen skicka skärmdumpar på felmeddelandet samt exakt datum och klockslag då felet först uppstod.",
    "s1_tags": "förfrågan, skärmdump, fel",
    "s1_title": "📸 Förfrågan: Begär skärmdumpar & tidpunkt",
    "s2_content": "Första hjälpen-steg:\n1. Avsluta journalsystemet på alla arbetsstationer.\n2. Starta om supporttjänsten på huvudservern.\n3. Öppna journalsystemet igen och testa funktionen.",
    "s2_tags": "första_hjälpen, omstart, journalsystem",
    "s2_title": "🛠 Första hjälpen: Starta om journalsystem & supporttjänst",
    "s3_content": "SELECT TOP 20 * FROM dbo.SystemLog WHERE ErrorCode LIKE '%AL-%' ORDER BY LogTimestamp DESC;",
    "s3_tags": "sql, databas, logg",
    "s3_title": "🔍 DB-kontroll: SQL-felloggfråga",
    "s4_content": "Tack för din återkoppling. Ärendet har lösts framgångsrikt. Vi avslutar detta ärende.",
    "s4_tags": "avslut, tack, klart",
    "s4_title": "✅ Ärendeavslut & Tack",
    "s5_content": "Steg för TI-felsökning:\n1. Kontrollera status för SMC-B-kortet i kortterminalen (grön LED).\n2. Gör kontakten strömlös en kort stund via webbgränssnittet eller strömbrytaren (vänta 30 sek).\n3. Starta om tjänsten och kör anslutningstest i administrationen.",
    "s5_tags": "ti, telematik, anslutning, smc-b",
    "s5_title": "🩺 Telematikinfrastruktur: Kontroll av anslutning & SMC-B",
    "s6_content": "Bästa mottagningsledning,\n\nDen begärda korrigeringsfilen resp. efterberäkningen för ESOL-faktureringen har vidarebefordrats till vår utvecklingsavdelning. Så snart de korrigerade posterna finns tillgängliga tillhandahåller vi dem.",
    "s6_tags": "fakturering, egenavgift, esol, korrigering",
    "s6_title": "📑 Fakturering: Egenavgifts- & ESOL-korrigering vidarebefordrad",
    "s7_content": "För detaljerad felanalys behöver vi en aktuell säkerhetskopia av databasen (.backup). Vänligen placera filen i den säkrade ärendemappen eller överföringskatalogen.",
    "s7_tags": "backup, databas, analys",
    "s7_title": "💾 Begäran om säkerhetskopia för felanalys",
    "s8_content": "Innan kvartalsuppdateringen installeras, säkerställ följande:\n1. Utför en fullständig säkerhetskopiering.\n2. Stäng alla arbetsstationer.\n3. Avsluta servertjänster och kör installationsprogrammet som administratör.",
    "s8_tags": "kvartalsuppdatering, uppdatering, underhåll",
    "s8_title": "🔄 Kvartalsuppdatering Information & Förberedelse"
}
de["snippets"] = snips_de
en["snippets"] = snips_en
sv["snippets"] = snips_sv

# 11. schemas
de["schemas"] = {
    "bug_report": {
        "database_dump_provided": "Datenbank-Backup im Fallordner abgelegt?",
        "db_dump_label": "Datenbank-Backup im Fallordner abgelegt?",
        "description": "Zur Weiterleitung ungeklärter Software-Fehler an die Entwicklungsabteilung.",
        "display_name": "Programmfehler / Bug-Report",
        "error_message": "Fehlermeldung / Code",
        "error_msg_label": "Fehlermeldung / Code",
        "module_label": "Betroffenes Modul",
        "module_name": "Betroffenes Modul",
        "repro_steps_label": "Schritte zur Reproduktion",
        "reproduction_steps": "Schritte zur Reproduktion",
        "stack_trace": "Stack-Trace / Logauszug",
        "stack_trace_label": "Stack-Trace / Logauszug"
    },
    "feature_request": {
        "benefit_label": "Gewünschter Nutzen / Ziel für die Praxis",
        "desc_label": "Beschreibung des Kundenwunsches",
        "description": "Zur Erfassung neuer Funktionswünsche von Praxen für die Entwicklungsabteilung.",
        "display_name": "Kundenwunsch / Feature-Request",
        "feature_description": "Beschreibung des Kundenwunsches",
        "has_mockup_or_screenshot": "Screenshot/Skizze im Fallordner?",
        "mockup_label": "Screenshot/Skizze im Fallordner?",
        "module_label": "Betroffenes Modul / Programmbereich",
        "module_name": "Betroffenes Modul / Programmbereich",
        "practice_benefit": "Gewünschter Nutzen / Ziel für die Praxis"
    },
    "internal_task": {
        "affected_systems": "Betroffene Systeme / Server / Komponenten",
        "category_label": "Kategorie der Aufgabe",
        "desc_label": "Ausführliche Aufgabenbeschreibung & Details",
        "desc_ph": "Schritt-für-Schritt Aufgabenbeschreibung...",
        "description": "Für interne Aufgaben, Systemwartung, Prozessverbesserungen oder Notizen ohne Kundenbezug.",
        "display_name": "🏢 Interne Aufgabe / Notiz",
        "internal_category": "Kategorie der Aufgabe",
        "systems_label": "Betroffene Systeme / Server / Komponenten",
        "systems_ph": "z. B. Server-02, P2P-Sync, Wiki-Cache..."
    },
    "quick": {
        "description": "Für die rasche Erfassung von Anfragen und Problemen ohne detaillierte Vorab-Spezifizierung.",
        "display_name": "⚡ Schnellerfassung / Allgemeiner Vorgang",
        "module_name": "Betroffenes Modul / Programmbereich (optional)",
        "module_name_label": "Betroffenes Modul / Programmbereich (optional)",
        "module_name_ph": "z. B. Abrechnung, Terminkalender, Schnittstelle...",
        "short_desc_label": "Kurzbeschreibung / Stichwort (optional)",
        "short_desc_ph": "z. B. Rückfrage zu Rezeptimport",
        "short_description": "Kurzbeschreibung / Stichwort (optional)",
        "unformatted_desc_label": "Unformatierte Informationen / Beschreibung",
        "unformatted_desc_ph": "Hier alle ungefilterten Informationen, Mails oder Stichpunkte eingeben...",
        "unformatted_description": "Unformatierte Informationen / Beschreibung"
    },
    "zuzahlung": {
        "action_reason_detail": "Genaue Begründung & Details",
        "action_type": "Geforderte Aktion",
        "action_type_label": "Geforderte Aktion",
        "date_ph": "YYYY-MM-DD",
        "description": "Für Nachforderungen und Korrekturen gegenüber Abrechnungszentrum, Krankenkasse oder KV.",
        "display_name": "Zuzahlungsnachforderung & Abrechnungskorrektur",
        "esol_filename": "Name der originalen ESOL-Datei",
        "esol_filename_label": "Name der originalen ESOL-Datei",
        "esol_filename_ph": "z. B. ESOL_20260801.dat",
        "forwarded_label": "Weitergeleitete Mail/Screenshot im Fallordner?",
        "has_forwarded_email_or_screenshot": "Weitergeleitete Mail/Screenshot im Fallordner?",
        "invoice_date": "Rechnungsdatum",
        "invoice_date_label": "Rechnungsdatum",
        "invoice_number": "Betroffene Rechnungsnummer",
        "invoice_num_label": "Betroffene Rechnungsnummer",
        "invoice_num_ph": "z. B. RE-2026-0815",
        "opt_korrektur": "Abrechnungskorrektur",
        "opt_nachforderung": "Zuzahlungsnachforderung",
        "patient_names": "Namen der betroffenen Patienten",
        "patient_names_label": "Namen der betroffenen Patienten",
        "patient_names_ph": "z. B. Max Mustermann",
        "prescription_date": "Datum der Verordnung",
        "prescription_date_label": "Datum der Verordnung",
        "prescription_info": "Betroffene Verordnung",
        "prescription_info_label": "Betroffene Verordnung",
        "prescription_info_ph": "z. B. VO-987654",
        "reason_label": "Genaue Begründung & Details",
        "reason_ph": "Ausführliche Beschreibung...",
        "repeatable_title": "Datei / Korrektur-Anforderung"
    }
}

en["schemas"] = {
    "bug_report": {
        "database_dump_provided": "Database Backup placed in Case Folder?",
        "db_dump_label": "Database Backup placed in Case Folder?",
        "description": "For forwarding unresolved software bugs to the development team.",
        "display_name": "Software Bug / Bug Report",
        "error_message": "Error Message / Code",
        "error_msg_label": "Error Message / Code",
        "module_label": "Affected Module",
        "module_name": "Affected Module",
        "repro_steps_label": "Steps to Reproduce",
        "reproduction_steps": "Steps to Reproduce",
        "stack_trace": "Stack Trace / Log Excerpt",
        "stack_trace_label": "Stack Trace / Log Excerpt"
    },
    "feature_request": {
        "benefit_label": "Desired Benefit / Goal for Practice",
        "desc_label": "Description of Customer Wish",
        "description": "For recording new feature requests from practices for the development team.",
        "display_name": "Customer Wish / Feature Request",
        "feature_description": "Description of Customer Wish",
        "has_mockup_or_screenshot": "Screenshot/Sketch in Case Folder?",
        "mockup_label": "Screenshot/Sketch in Case Folder?",
        "module_label": "Affected Module / Area",
        "module_name": "Affected Module / Area",
        "practice_benefit": "Desired Benefit / Goal for Practice"
    },
    "internal_task": {
        "affected_systems": "Affected Systems / Servers / Components",
        "category_label": "Task Category",
        "desc_label": "Detailed Task Description & Details",
        "desc_ph": "Step-by-step task description...",
        "description": "For internal tasks, system maintenance, process improvements, or notes without customer relation.",
        "display_name": "🏢 Internal Task / Note",
        "internal_category": "Task Category",
        "systems_label": "Affected Systems / Servers / Components",
        "systems_ph": "e.g. Server-02, P2P Sync, Wiki Cache..."
    },
    "quick": {
        "description": "For rapid recording of inquiries and issues without detailed prior specification.",
        "display_name": "⚡ Quick Intake / General Issue",
        "module_name": "Affected Module / Area (optional)",
        "module_name_label": "Affected Module / Area (optional)",
        "module_name_ph": "e.g. Billing, Calendar, Interface...",
        "short_desc_label": "Short Description / Keyword (optional)",
        "short_desc_ph": "e.g. Query regarding prescription import",
        "short_description": "Short Description / Keyword (optional)",
        "unformatted_desc_label": "Unformatted Information / Description",
        "unformatted_desc_ph": "Enter all unfiltered information, emails, or bullet points here...",
        "unformatted_description": "Unformatted Information / Description"
    },
    "zuzahlung": {
        "action_reason_detail": "Detailed Reason & Description",
        "action_type": "Requested Action",
        "action_type_label": "Requested Action",
        "date_ph": "YYYY-MM-DD",
        "description": "For subsequent claims and corrections towards billing center, health insurer, or association.",
        "display_name": "Copayment Subsequent Claim & Billing Correction",
        "esol_filename": "Name of Original ESOL File",
        "esol_filename_label": "Name of Original ESOL File",
        "esol_filename_ph": "e.g. ESOL_20260801.dat",
        "forwarded_label": "Forwarded Email/Screenshot in Case Folder?",
        "has_forwarded_email_or_screenshot": "Forwarded Email/Screenshot in Case Folder?",
        "invoice_date": "Invoice Date",
        "invoice_date_label": "Invoice Date",
        "invoice_number": "Affected Invoice Number",
        "invoice_num_label": "Affected Invoice Number",
        "invoice_num_ph": "e.g. INV-2026-0815",
        "opt_korrektur": "Billing Correction",
        "opt_nachforderung": "Copayment Subsequent Claim",
        "patient_names": "Names of Affected Patients",
        "patient_names_label": "Names of Affected Patients",
        "patient_names_ph": "e.g. John Doe",
        "prescription_date": "Prescription Date",
        "prescription_date_label": "Prescription Date",
        "prescription_info": "Affected Prescription",
        "prescription_info_label": "Affected Prescription",
        "prescription_info_ph": "e.g. RX-987654",
        "reason_label": "Detailed Reason & Description",
        "reason_ph": "Detailed description...",
        "repeatable_title": "File / Correction Request"
    }
}

sv["schemas"] = {
    "bug_report": {
        "database_dump_provided": "Databasbackup sparad i ärendemappen?",
        "db_dump_label": "Databasbackup sparad i ärendemappen?",
        "description": "För att vidarebefordra olösta programfel till utvecklingsavdelningen.",
        "display_name": "Programfel / Felrapport",
        "error_message": "Felmeddelande / Kod",
        "error_msg_label": "Felmeddelande / Kod",
        "module_label": "Berörd modul",
        "module_name": "Berörd modul",
        "repro_steps_label": "Steg för att reproducera",
        "reproduction_steps": "Steg för att reproducera",
        "stack_trace": "Stackspårning / Loggutdrag",
        "stack_trace_label": "Stackspårning / Loggutdrag"
    },
    "feature_request": {
        "benefit_label": "Önskad nytta / Mål för mottagningen",
        "desc_label": "Beskrivning av kundönskemål",
        "description": "För att registrera nya funktionsönskemål från mottagningar till utvecklingsavdelningen.",
        "display_name": "Kundönskemål / Funktionsbegäran",
        "feature_description": "Beskrivning av kundönskemål",
        "has_mockup_or_screenshot": "Skärmdump/Skiss i ärendemappen?",
        "mockup_label": "Skärmdump/Skiss i ärendemappen?",
        "module_label": "Berörd modul / programområde",
        "module_name": "Berörd modul / programområde",
        "practice_benefit": "Önskad nytta / Mål för mottagningen"
    },
    "internal_task": {
        "affected_systems": "Berörda system / servrar / komponenter",
        "category_label": "Uppgiftskategori",
        "desc_label": "Detaljerad uppgiftsbeskrivning & detaljer",
        "desc_ph": "Steg-för-steg uppgiftsbeskrivning...",
        "description": "För interna uppgifter, systemunderhåll, processförbättringar eller anteckningar utan kundkoppling.",
        "display_name": "🏢 Intern uppgift / Anteckning",
        "internal_category": "Uppgiftskategori",
        "systems_label": "Berörda system / servrar / komponenter",
        "systems_ph": "t.ex. Server-02, P2P-synk, Wiki-cache..."
    },
    "quick": {
        "description": "För snabb registrering av förfrågningar och problem utan detaljerad förhandsspecifikation.",
        "display_name": "⚡ Snabbregistrering / Allmänt ärende",
        "module_name": "Berörd modul / programområde (valfritt)",
        "module_name_label": "Berörd modul / programområde (valfritt)",
        "module_name_ph": "t.ex. Fakturering, Kalender, Gränssnitt...",
        "short_desc_label": "Kort beskrivning / Nyckelord (valfritt)",
        "short_desc_ph": "t.ex. Fråga om receptimport",
        "short_description": "Kort beskrivning / Nyckelord (valfritt)",
        "unformatted_desc_label": "Oformaterad information / Beskrivning",
        "unformatted_desc_ph": "Ange all ofiltrerad information, e-post eller punkter här...",
        "unformatted_description": "Oformaterad information / Beskrivning"
    },
    "zuzahlung": {
        "action_reason_detail": "Detaljerad motivering & detaljer",
        "action_type": "Begärd åtgärd",
        "action_type_label": "Begärd åtgärd",
        "date_ph": "YYYY-MM-DD",
        "description": "För efterkrav och korrigeringar gentemot faktureringscentral, försäkringskassa eller motsvarande.",
        "display_name": "Efterkrav för egenavgift & faktureringskorrigering",
        "esol_filename": "Namn på ursprunglig ESOL-fil",
        "esol_filename_label": "Namn på ursprunglig ESOL-fil",
        "esol_filename_ph": "t.ex. ESOL_20260801.dat",
        "forwarded_label": "Vidarebefordrad e-post/skärmdump i ärendemappen?",
        "has_forwarded_email_or_screenshot": "Vidarebefordrad e-post/skärmdump i ärendemappen?",
        "invoice_date": "Fakturadatum",
        "invoice_date_label": "Fakturadatum",
        "invoice_number": "Berört fakturanummer",
        "invoice_num_label": "Berört fakturanummer",
        "invoice_num_ph": "t.ex. FAK-2026-0815",
        "opt_korrektur": "Faktureringskorrigering",
        "opt_nachforderung": "Efterkrav för egenavgift",
        "patient_names": "Namn på berörda patienter",
        "patient_names_label": "Namn på berörda patienter",
        "patient_names_ph": "t.ex. Sven Svensson",
        "prescription_date": "Ordinationsdatum",
        "prescription_date_label": "Ordinationsdatum",
        "prescription_info": "Berörd ordination",
        "prescription_info_label": "Berörd ordination",
        "prescription_info_ph": "t.ex. ORD-987654",
        "reason_label": "Detaljerad motivering & detaljer",
        "reason_ph": "Utförlig beskrivning...",
        "repeatable_title": "Fil / Korrigeringsbegäran"
    }
}

# 12. export_templates
de["export_templates"] = {
    "gitlab_dev_bug_desc": "Entwickler-Ticket für Softwarefehler, Abstürze und Schnittstellenprobleme.",
    "gitlab_dev_bug_name": "GitLab / Dev-Ticket: Programmierfehler (Bug)",
    "gitlab_dev_kundenwunsch_desc": "Formatiertes Markdown-Ticket für neue Funktionswünsche an die Entwicklungsabteilung.",
    "gitlab_dev_kundenwunsch_name": "GitLab / Dev-Ticket: Kundenwunsch",
    "mail_dev_zuzahlung_abrechnung_desc": "Erzeugt eine vollständige E-Mail an das Entwicklerteam zur Nachberechnung oder Abrechnungskorrektur mit allen Pflichtdaten.",
    "mail_dev_zuzahlung_abrechnung_name": "E-Mail an Entwickler: Zuzahlung & Abrechnungskorrektur",
    "mail_kunden_rueckmeldung_desc": "Kunden-E-Mail mit Zusammenfassung der Lösung und Kontaktdaten.",
    "mail_kunden_rueckmeldung_name": "E-Mail an Praxis: Lösungs-Zusammenfassung"
}
en["export_templates"] = {
    "gitlab_dev_bug_desc": "Developer ticket for software bugs, crashes, and interface issues.",
    "gitlab_dev_bug_name": "GitLab / Dev Ticket: Software Bug",
    "gitlab_dev_kundenwunsch_desc": "Formatted Markdown ticket for new feature requests to the development department.",
    "gitlab_dev_kundenwunsch_name": "GitLab / Dev Ticket: Feature Request",
    "mail_dev_zuzahlung_abrechnung_desc": "Generates a complete email to the dev team for recalculation or billing correction with all required data.",
    "mail_dev_zuzahlung_abrechnung_name": "Email to Developer: Copayment & Billing Correction",
    "mail_kunden_rueckmeldung_desc": "Customer email with summary of solution and contact information.",
    "mail_kunden_rueckmeldung_name": "Email to Practice: Solution Summary"
}
sv["export_templates"] = {
    "gitlab_dev_bug_desc": "Utvecklarärende för programfel, krascher och gränssnittsproblem.",
    "gitlab_dev_bug_name": "GitLab / Utvecklarärende: Programfel (Bugg)",
    "gitlab_dev_kundenwunsch_desc": "Formaterat Markdown-ärende för nya funktionsönskemål till utvecklingsavdelningen.",
    "gitlab_dev_kundenwunsch_name": "GitLab / Utvecklarärende: Funktionsbegäran",
    "mail_dev_zuzahlung_abrechnung_desc": "Skapar ett fullständigt e-postmeddelande till utvecklingsteamet för efterberäkning eller faktureringskorrigering med alla obligatoriska uppgifter.",
    "mail_dev_zuzahlung_abrechnung_name": "E-post till utvecklare: Egenavgift & faktureringskorrigering",
    "mail_kunden_rueckmeldung_desc": "Kunde-post med sammanfattning av lösningen och kontaktuppgifter.",
    "mail_kunden_rueckmeldung_name": "E-post till mottagning: Lösningssammanfattning"
}

# 13. hotkey_actions
de["hotkey_actions"].update({
    "archive_case": "Fall archivieren:",
    "export_dialog": "Export Dialog:",
    "new_case": "Neuer Fall:",
    "open_settings": "Einstellungen öffnen:",
    "save_case": "Fall speichern:",
    "search_customer": "Kundensuche fokussieren:",
    "snippet_picker": "Snippet-Picker öffnen:",
    "toggle_theme": "Theme umschalten:",
    "view_analytics": "Auswertungs-Ansicht:",
    "view_board": "Board-Ansicht:",
    "view_cockpit": "Cockpit-Ansicht:",
    "view_table": "Tabelle-Ansicht:",
    "wiki_search": "Wiki-Suche fokussieren:"
})
en["hotkey_actions"].update({
    "archive_case": "Archive Case:",
    "export_dialog": "Export Dialog:",
    "new_case": "New Case:",
    "open_settings": "Open Settings:",
    "save_case": "Save Case:",
    "search_customer": "Focus Customer Search:",
    "snippet_picker": "Open Snippet Picker:",
    "toggle_theme": "Toggle Theme:",
    "view_analytics": "Analytics View:",
    "view_board": "Board View:",
    "view_cockpit": "Cockpit View:",
    "view_table": "Table View:",
    "wiki_search": "Focus Wiki Search:"
})
sv["hotkey_actions"].update({
    "archive_case": "Arkivera ärende:",
    "export_dialog": "Exportdialog:",
    "new_case": "Nytt ärende:",
    "open_settings": "Öppna inställningar:",
    "save_case": "Spara ärende:",
    "search_customer": "Fokusera kundsökning:",
    "snippet_picker": "Öppna textavsnittsväljare:",
    "toggle_theme": "Växla tema:",
    "view_analytics": "Analysvy:",
    "view_board": "Tavelvy:",
    "view_cockpit": "Cockpit-vy:",
    "view_table": "Tabellvy:",
    "wiki_search": "Fokusera Wiki-sökning:"
})

# 14. hotkey_recorder
de["hotkey_recorder"]["button"] = "🎙 Taste erfassen"
en["hotkey_recorder"]["button"] = "🎙 Record Key"
sv["hotkey_recorder"]["button"] = "🎙 Spela in tangent"

# 15. shortcuts
de["shortcuts"] = {
    "app_shortcuts_header": "⚡ App-Aktionen Tastenkürzel (Hotkeys)",
    "conflict": "⚠ Shortcut-Konflikt: Folgende Hotkeys sind mehrfach zugewiesen: {dup_str}",
    "conflict_generic": "⚠ Shortcut-Konflikt: Hotkeys dürfen nicht mehrfach zugewiesen werden!",
    "no_snippets": "Keine Textbausteine vorhanden.",
    "snippet_shortcut_field": "Tastenkürzel / Macro (z. B. <Control-Alt-1>):",
    "snippet_shortcuts_header": "📝 Textbaustein-Makros (Snippet Shortcuts)",
    "toast_macro_title": "Textbaustein Macro",
    "toast_no_focus": "Kein fokussiertes Eingabefeld vorhanden."
}
en["shortcuts"] = {
    "app_shortcuts_header": "⚡ App Action Shortcuts (Hotkeys)",
    "conflict": "⚠ Shortcut conflict: The following hotkeys are assigned multiple times: {dup_str}",
    "conflict_generic": "⚠ Shortcut conflict: Hotkeys must not be assigned multiple times!",
    "no_snippets": "No snippets available.",
    "snippet_shortcut_field": "Shortcut / Macro (e.g. <Control-Alt-1>):",
    "snippet_shortcuts_header": "📝 Text Snippet Macros (Snippet Shortcuts)",
    "toast_macro_title": "Snippet Macro",
    "toast_no_focus": "No focused input field available."
}
sv["shortcuts"] = {
    "app_shortcuts_header": "⚡ Snabbkommandon för appåtgärder (Kortkommandon)",
    "conflict": "⚠ Kortkommandokonflikt: Följande kortkommandon har tilldelats flera gånger: {dup_str}",
    "conflict_generic": "⚠ Kortkommandokonflikt: Kortkommandon får inte tilldelas flera gånger!",
    "no_snippets": "Inga textavsnitt tillgängliga.",
    "snippet_shortcut_field": "Kortkommando / Makro (t.ex. <Control-Alt-1>):",
    "snippet_shortcuts_header": "📝 Textavsnittsmakron (Kortkommandon)",
    "toast_macro_title": "Textavsnittsmakro",
    "toast_no_focus": "Inget fokuserat inmatningsfält tillgängligt."
}

# Ensure keys are sorted for deterministic output
def sort_dict(d):
    return {k: sort_dict(v) if isinstance(v, dict) else v for k, v in sorted(d.items())}

with open(locales_dir / "de.json", "w", encoding="utf-8") as f:
    json.dump(sort_dict(de), f, ensure_ascii=False, indent=2)
with open(locales_dir / "en.json", "w", encoding="utf-8") as f:
    json.dump(sort_dict(en), f, ensure_ascii=False, indent=2)
with open(locales_dir / "sv.json", "w", encoding="utf-8") as f:
    json.dump(sort_dict(sv), f, ensure_ascii=False, indent=2)

print("Successfully updated and synchronized de.json, en.json, sv.json")
