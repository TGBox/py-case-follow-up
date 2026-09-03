# -*- coding: utf-8 -*-
"""
Build and synchronize locales/de.json, locales/en.json, and locales/sv.json.
Ensures 100% key parity, matching format tokens, valid JSON, and natural translations.
"""

import json
import os
import re

def build_all_locales():
    # Load base files
    with open('locales/de.json', 'r', encoding='utf-8') as f:
        de = json.load(f)
    with open('locales/en.json', 'r', encoding='utf-8') as f:
        en = json.load(f)
    with open('locales/sv.json', 'r', encoding='utf-8') as f:
        sv = json.load(f)

    # 1. Update/Add missing keys and newly identified keys

    # ==================== common ====================
    common_add_de = {
        "delete": "🗑 Löschen",
        "open": "📂 Öffnen",
        "browse": "Durchsuchen...",
        "edit": "✏ Bearbeiten",
        "refresh": "🔄 Aktualisieren"
    }
    common_add_en = {
        "delete": "🗑 Delete",
        "open": "📂 Open",
        "browse": "Browse...",
        "edit": "✏ Edit",
        "refresh": "🔄 Refresh"
    }
    common_add_sv = {
        "delete": "🗑 Ta bort",
        "open": "📂 Öppna",
        "browse": "Bläddra...",
        "edit": "✏ Redigera",
        "refresh": "🔄 Uppdatera"
    }
    de.setdefault("common", {}).update(common_add_de)
    en.setdefault("common", {}).update(common_add_en)
    sv.setdefault("common", {}).update(common_add_sv)

    # ==================== tag_mgmt ====================
    tag_mgmt_de = {
        "tab_tags": "🏷 Allgemeine Tags",
        "tab_modules": "🧩 Programmbereiche",
        "search_tags_placeholder": "🔍 Tags durchsuchen...",
        "new_tag_placeholder": "Neuen Tag erstellen (z. B. Schnittstelle)...",
        "add_tag_btn": "+ Tag Hinzufügen",
        "search_modules_placeholder": "🔍 Programmbereiche durchsuchen...",
        "new_module_placeholder": "Neuen Programmbereich erstellen (z. B. Rezeptdruck)...",
        "add_module_btn": "+ Bereich Hinzufügen",
        "tag_added": "✅ Tag erfolgreich hinzugefügt!",
        "module_added": "✅ Programmbereich erfolgreich hinzugefügt!",
        "tag_empty": "⚠ Tag Name darf nicht leer sein!",
        "tag_exists": "⚠ Tag existiert bereits!",
        "module_empty": "⚠ Programmbereich darf nicht leer sein!",
        "module_exists": "⚠ Programmbereich existiert bereits!",
        "header": "🏷 System-Tags & Programmbereiche",
        "no_tags": "Keine Tags gefunden.",
        "no_modules": "Keine Programmbereiche gefunden."
    }
    tag_mgmt_en = {
        "tab_tags": "🏷 General Tags",
        "tab_modules": "🧩 Program Modules",
        "search_tags_placeholder": "🔍 Search tags...",
        "new_tag_placeholder": "Create new tag (e.g. Interface)...",
        "add_tag_btn": "+ Add Tag",
        "search_modules_placeholder": "🔍 Search program modules...",
        "new_module_placeholder": "Create new program module (e.g. Prescription Print)...",
        "add_module_btn": "+ Add Module",
        "tag_added": "✅ Tag added successfully!",
        "module_added": "✅ Program module added successfully!",
        "tag_empty": "⚠ Tag name cannot be empty!",
        "tag_exists": "⚠ Tag already exists!",
        "module_empty": "⚠ Program module cannot be empty!",
        "module_exists": "⚠ Program module already exists!",
        "header": "🏷 System Tags & Program Modules",
        "no_tags": "No tags found.",
        "no_modules": "No program modules found."
    }
    tag_mgmt_sv = {
        "tab_tags": "🏷 Allmänna taggar",
        "tab_modules": "🧩 Programmoduler",
        "search_tags_placeholder": "🔍 Sök taggar...",
        "new_tag_placeholder": "Skapa ny tagg (t.ex. Gränssnitt)...",
        "add_tag_btn": "+ Lägg till tagg",
        "search_modules_placeholder": "🔍 Sök programmoduler...",
        "new_module_placeholder": "Skapa ny programmodul (t.ex. Receptutskrift)...",
        "add_module_btn": "+ Lägg till modul",
        "tag_added": "✅ Taggen har lagts till!",
        "module_added": "✅ Programmodulen har lagts till!",
        "tag_empty": "⚠ Taggnamnet får inte vara tomt!",
        "tag_exists": "⚠ Taggen finns redan!",
        "module_empty": "⚠ Programmodulen får inte vara tom!",
        "module_exists": "⚠ Programmodulen finns redan!",
        "header": "🏷 Systemtaggar & programmoduler",
        "no_tags": "Inga taggar hittades.",
        "no_modules": "Inga programmoduler hittades."
    }
    de["tag_mgmt"] = tag_mgmt_de
    en["tag_mgmt"] = tag_mgmt_en
    sv["tag_mgmt"] = tag_mgmt_sv

    # ==================== dynamic_form ====================
    dynamic_form_de = {
        "number_placeholder": "Zahl...",
        "import_backup": "📁 .backup-Datei importieren...",
        "choose_file": "📁 Datei wählen...",
        "manage_tags": "⚙ Programmbereiche verwalten",
        "search_tags": "🔍 Programmbereich suchen...",
        "no_files": "📎 Abgelegte Dateien im Fallordner: Keine (0)",
        "import_title": "Dateien in Fallordner importieren",
        "select_tags": "🧩 Programmbereiche auswählen:",
        "select_all": "Alle auswählen",
        "select_none": "Keine auswählen",
        "apply_close": "✓ Übernehmen & Schließen",
        "import_files": "+ Datei(en) importieren...",
        "files_attached": "Abgelegte Dateien im Fallordner",
        "no_tags": "Kein Programmbereich gefunden.",
        "select_tags_dialog_title": "🧩 Programmbereiche auswählen",
        "import_backup_dialog_title": "Datenbank-Backup (.backup) importieren"
    }
    dynamic_form_en = {
        "number_placeholder": "Number...",
        "import_backup": "📁 Import .backup file...",
        "choose_file": "📁 Choose file...",
        "manage_tags": "⚙ Manage program modules",
        "search_tags": "🔍 Search program module...",
        "no_files": "📎 Attached files in case folder: None (0)",
        "import_title": "Import files into case folder",
        "select_tags": "🧩 Select program modules:",
        "select_all": "Select all",
        "select_none": "Select none",
        "apply_close": "✓ Apply & Close",
        "import_files": "+ Import file(s)...",
        "files_attached": "Attached files in case folder",
        "no_tags": "No program module found.",
        "select_tags_dialog_title": "🧩 Select Program Modules",
        "import_backup_dialog_title": "Import Database Backup (.backup)"
    }
    dynamic_form_sv = {
        "number_placeholder": "Nummer...",
        "import_backup": "📁 Importera .backup-fil...",
        "choose_file": "📁 Välj fil...",
        "manage_tags": "⚙ Hantera programmoduler",
        "search_tags": "🔍 Sök programmodul...",
        "no_files": "📎 Bifogade filer i ärendemappen: Inga (0)",
        "import_title": "Importera filer till ärendemapp",
        "select_tags": "🧩 Välj programmoduler:",
        "select_all": "Välj alla",
        "select_none": "Välj ingen",
        "apply_close": "✓ Tillämpa & stäng",
        "import_files": "+ Importera fil(er)...",
        "files_attached": "Bifogade filer i ärendemappen",
        "no_tags": "Ingen programmodul hittades.",
        "select_tags_dialog_title": "🧩 Välj programmoduler",
        "import_backup_dialog_title": "Importera databassäkerhetskopia (.backup)"
    }
    de["dynamic_form"] = dynamic_form_de
    en["dynamic_form"] = dynamic_form_en
    sv["dynamic_form"] = dynamic_form_sv

    # ==================== handover_dialog ====================
    handover_dialog_de = {
        "no_colleagues": "- Keine Mitarbeiter in Liste -",
        "person_placeholder": "Empfänger-Name...",
        "note_placeholder": "z. B. Ticket #104 im GitLab angelegt, Rückruf erbeten...",
        "select_colleague": "- Aus Mitarbeiterliste wählen -",
        "new_actor": "Neue verantwortliche Stelle *:",
        "channel": "Art der Weitergabe / Kanal *:",
        "recipient": "Empfänger / Name der Person (aus Mitarbeiterliste wählen oder eingeben):",
        "note": "Notiz / Details zur Übergabe (optional):",
        "confirm_btn": "🤝 Übergabe bestätigen",
        "header": "Zuständigkeit für",
        "header_suffix": "übergeben",
        "curr_actor": "Aktuelle Zuständigkeit:",
        "customer": "Kunde:"
    }
    handover_dialog_en = {
        "no_colleagues": "- No colleagues in list -",
        "person_placeholder": "Recipient name...",
        "note_placeholder": "e.g. Ticket #104 created in GitLab, callback requested...",
        "select_colleague": "- Select from colleague list -",
        "new_actor": "New responsible department *:",
        "channel": "Handover method / Channel *:",
        "recipient": "Recipient / Person name (select from colleague list or enter):",
        "note": "Note / Handover details (optional):",
        "confirm_btn": "🤝 Confirm Handover",
        "header": "Hand over responsibility for",
        "header_suffix": "",
        "curr_actor": "Current responsibility:",
        "customer": "Customer:"
    }
    handover_dialog_sv = {
        "no_colleagues": "- Inga kollegor i listan -",
        "person_placeholder": "Mottagarnamn...",
        "note_placeholder": "t.ex. Ärende #104 skapat i GitLab, återuppringning begärd...",
        "select_colleague": "- Välj från kollegelistan -",
        "new_actor": "Ny ansvarig enhet *:",
        "channel": "Överlämningsmetod / Kanal *:",
        "recipient": "Mottagare / Personens namn (välj från kollegelistan eller ange):",
        "note": "Anteckning / Detaljer om överlämning (valfritt):",
        "confirm_btn": "🤝 Bekräfta överlämning",
        "header": "Överlämna ansvar för",
        "header_suffix": "",
        "curr_actor": "Aktuellt ansvar:",
        "customer": "Kund:"
    }
    de["handover_dialog"] = handover_dialog_de
    en["handover_dialog"] = handover_dialog_en
    sv["handover_dialog"] = handover_dialog_sv

    # ==================== profile (merge updates) ====================
    profile_add_de = {
        "provider_gemini": "GOOGLE GEMINI (Cloud)",
        "provider_ollama": "OLLAMA (Lokal)",
        "anonymize_toggle": "🔒 Lokale PII-Anonymisierung aktivieren (DSGVO / § 203 StGB)",
        "gemini_modelfile_rules": "📄 Modelfile-Systemregeln für Gemini in Basis-Regeln übernehmen (aus ollama/Modelfile)",
        "checking_ollama": "🔍 Prüfe Ollama-Status...",
        "scan_ollama_btn": "🔄 Status & Modelle scannen",
        "ai_header": "🤖 KI- & NLP-Einstellungen (Ollama Local LLM & Google Gemini API)",
        "ai_provider_label": "KI-Anbieter wählen:",
        "gemini_key_lbl": "🔑 Google Gemini API Key:",
        "gemini_select_model": "Gemini Modell wählen:",
        "widths_reset_msg": "Alle Spaltenbreiten aller Ansichten auf Standard zurückgesetzt!",
        "ph_dept": "z. B. Support, Entwicklung, Technik",
        "ph_phone": "z.B. 4012",
        "ph_email": "beispiel@support.de",
        "ph_mobile": "0170 / 1234567",
        "ph_signature": "z. B. Mit freundlichen Grüßen, Ihr Support-Team (Tel. 0800-12345)",
        "prompt_new_colleague": "Geben Sie den Namen des neuen Mitarbeiters ein:",
        "title_new_colleague": "Neues Mitarbeiter-Profil anlegen",
        "ph_data_dir": "Pfad zum Datenordner...",
        "title_select_data_dir": "Datenordner auswählen",
        "title_select_file": "Datei auswählen",
        "ph_wiki_url": "https://wiki.meinepraxis.de/api",
        "ph_token_id": "Token ID",
        "ph_token_secret": "Token Secret",
        "saved_settings_msg": "✅ Einstellungen & Pfade gespeichert!",
        "title_save_backup_zip": "Datensicherung als ZIP speichern",
        "title_select_backup_zip": "Datensicherung (ZIP-Datei) auswählen",
        "err_username_empty": "⚠ Benutzername darf nicht leer sein!",
        "lbl_priority_scoring": "Prioritäts-Scoring Punkte",
        "lbl_vip_bonus": "VIP-Bonus (Punkte):",
        "ph_gemini_key": "AIzaSy...",
        "checking_api_key": "🔍 Prüfe Key...",
        "creating_model_msg": "⏳ Erstelle 'pvs-support' Modell aus Modelfile...",
        "err_enter_api_key": "⚠ Bitte API Key eingeben"
    }
    profile_add_en = {
        "provider_gemini": "GOOGLE GEMINI (Cloud)",
        "provider_ollama": "OLLAMA (Local)",
        "anonymize_toggle": "🔒 Enable local PII anonymization (GDPR)",
        "gemini_modelfile_rules": "📄 Adopt Modelfile system rules for Gemini into base rules (from ollama/Modelfile)",
        "checking_ollama": "🔍 Checking Ollama status...",
        "scan_ollama_btn": "🔄 Scan Status & Models",
        "ai_header": "🤖 AI & NLP Settings (Ollama Local LLM & Google Gemini API)",
        "ai_provider_label": "Select AI provider:",
        "gemini_key_lbl": "🔑 Google Gemini API Key:",
        "gemini_select_model": "Select Gemini model:",
        "widths_reset_msg": "All column widths for all views reset to default!",
        "ph_dept": "e.g. Support, Development, Tech",
        "ph_phone": "e.g. 4012",
        "ph_email": "example@support.com",
        "ph_mobile": "0170 / 1234567",
        "ph_signature": "e.g. Best regards, Your Support Team (Phone 0800-12345)",
        "prompt_new_colleague": "Enter the name of the new colleague:",
        "title_new_colleague": "Create New Colleague Profile",
        "ph_data_dir": "Path to data directory...",
        "title_select_data_dir": "Select Data Directory",
        "title_select_file": "Select File",
        "ph_wiki_url": "https://wiki.mypractice.com/api",
        "ph_token_id": "Token ID",
        "ph_token_secret": "Token Secret",
        "saved_settings_msg": "✅ Settings & paths saved!",
        "title_save_backup_zip": "Save backup as ZIP",
        "title_select_backup_zip": "Select backup (ZIP file)",
        "err_username_empty": "⚠ Username cannot be empty!",
        "lbl_priority_scoring": "Priority Scoring Points",
        "lbl_vip_bonus": "VIP Bonus (Points):",
        "ph_gemini_key": "AIzaSy...",
        "checking_api_key": "🔍 Checking key...",
        "creating_model_msg": "⏳ Creating 'pvs-support' model from Modelfile...",
        "err_enter_api_key": "⚠ Please enter API Key"
    }
    profile_add_sv = {
        "provider_gemini": "GOOGLE GEMINI (Moln)",
        "provider_ollama": "OLLAMA (Lokal)",
        "anonymize_toggle": "🔒 Aktivera lokal PII-anonymisering (GDPR)",
        "gemini_modelfile_rules": "📄 Tillämpa Modelfile-systemregler för Gemini i basreglerna (från ollama/Modelfile)",
        "checking_ollama": "🔍 Kontrollerar Ollama-status...",
        "scan_ollama_btn": "🔄 Skanna status & modeller",
        "ai_header": "🤖 AI- & NLP-inställningar (Ollama Local LLM & Google Gemini API)",
        "ai_provider_label": "Välj AI-leverantör:",
        "gemini_key_lbl": "🔑 Google Gemini API-nyckel:",
        "gemini_select_model": "Välj Gemini-modell:",
        "widths_reset_msg": "Alla kolumnbredder för alla vyer har återställts till standard!",
        "ph_dept": "t.ex. Support, Utveckling, Teknik",
        "ph_phone": "t.ex. 4012",
        "ph_email": "exempel@support.se",
        "ph_mobile": "0170 / 1234567",
        "ph_signature": "t.ex. Vänliga hälsningar, Supportteamet (Tel. 0800-12345)",
        "prompt_new_colleague": "Ange namnet på den nya medarbetaren:",
        "title_new_colleague": "Skapa ny medarbetarprofil",
        "ph_data_dir": "Sökväg till datamapp...",
        "title_select_data_dir": "Välj datamapp",
        "title_select_file": "Välj fil",
        "ph_wiki_url": "https://wiki.minmottagning.se/api",
        "ph_token_id": "Token ID",
        "ph_token_secret": "Token Secret",
        "saved_settings_msg": "✅ Inställningar & sökvägar sparade!",
        "title_save_backup_zip": "Spara säkerhetskopia som ZIP",
        "title_select_backup_zip": "Välj säkerhetskopia (ZIP-fil)",
        "err_username_empty": "⚠ Användarnamnet får inte vara tomt!",
        "lbl_priority_scoring": "Prioritetspoäng",
        "lbl_vip_bonus": "VIP-bonus (poäng):",
        "ph_gemini_key": "AIzaSy...",
        "checking_api_key": "🔍 Kontrollerar nyckel...",
        "creating_model_msg": "⏳ Skapar 'pvs-support'-modell från Modelfile...",
        "err_enter_api_key": "⚠ Ange API-nyckel"
    }
    de.setdefault("profile", {}).update(profile_add_de)
    en.setdefault("profile", {}).update(profile_add_en)
    sv.setdefault("profile", {}).update(profile_add_sv)

    # ==================== email_draft (merge updates) ====================
    email_draft_add_de = {
        "snippet_inserted": "✓ Textbaustein eingefügt.",
        "ai_generating": "🤖 KI generiert E-Mail-Entwurf...",
        "mailto_opened": "✓ Standard-Mail-Programm aufgerufen.",
        "outlook_opened": "✓ E-Mail erfolgreich in Outlook geöffnet.",
        "copied_to_clipboard": "✓ E-Mail in Zwischenablage kopiert.",
        "case_required_for_ai": "⚠ KI-Entwurf benötigt einen aktiven Fall.",
        "recipient_lbl": "Empfänger (E-Mail):",
        "close_btn": "✕ Schließen",
        "subject_lbl": "Betreff:",
        "body_lbl": "E-Mail Nachrichtentext:",
        "eml_handed_over": "✓ E-Mail-Entwurf an E-Mail-Client übergeben (.eml).",
        "ai_please_wait": "Bitte einen Moment gedulden — Modell generiert Antwort",
        "checking_ai_status": "Prüfe KI-Status...",
        "ph_recipient": "praxis@beispiel.de oder Name / Praxis eingeben...",
        "btn_practice_card": "📇 Praxiskartei ▾",
        "lbl_practice_contacts": "🔍 Kontakte aus Praxiskartei (Klicken zum Übernehmen):",
        "ph_subject": "Betreff eingeben...",
        "btn_insert_snippet": "🧩 Textbaustein",
        "no_contacts_found": "Keine passenden Praxiskontakte gefunden."
    }
    email_draft_add_en = {
        "snippet_inserted": "✓ Text snippet inserted.",
        "ai_generating": "🤖 AI is generating email draft...",
        "mailto_opened": "✓ Default mail client opened.",
        "outlook_opened": "✓ Email successfully opened in Outlook.",
        "copied_to_clipboard": "✓ Email copied to clipboard.",
        "case_required_for_ai": "⚠ AI draft requires an active case.",
        "recipient_lbl": "Recipient (Email):",
        "close_btn": "✕ Close",
        "subject_lbl": "Subject:",
        "body_lbl": "Email message body:",
        "eml_handed_over": "✓ Email draft handed over to mail client (.eml).",
        "ai_please_wait": "Please wait a moment — model is generating response",
        "checking_ai_status": "Checking AI status...",
        "ph_recipient": "practice@example.com or enter Name / Practice...",
        "btn_practice_card": "📇 Practice File ▾",
        "lbl_practice_contacts": "🔍 Contacts from practice file (Click to adopt):",
        "ph_subject": "Enter subject...",
        "btn_insert_snippet": "🧩 Text Snippet",
        "no_contacts_found": "No matching practice contacts found."
    }
    email_draft_add_sv = {
        "snippet_inserted": "✓ Textmall infogad.",
        "ai_generating": "🤖 AI genererar e-postutkast...",
        "mailto_opened": "✓ Standardprogram för e-post öppnat.",
        "outlook_opened": "✓ E-post öppnades i Outlook.",
        "copied_to_clipboard": "✓ E-post kopierad till urklipp.",
        "case_required_for_ai": "⚠ AI-utkast kräver ett aktivt ärende.",
        "recipient_lbl": "Mottagare (E-post):",
        "close_btn": "✕ Stäng",
        "subject_lbl": "Ämne:",
        "body_lbl": "E-postmeddelandetext:",
        "eml_handed_over": "✓ E-postutkast överlämnat till e-postklient (.eml).",
        "ai_please_wait": "Vänligen vänta ett ögonblick — modellen genererar svar",
        "checking_ai_status": "Kontrollerar AI-status...",
        "ph_recipient": "mottagning@exempel.se eller ange namn / mottagning...",
        "btn_practice_card": "📇 Mottagningskort ▾",
        "lbl_practice_contacts": "🔍 Kontakter från mottagningskort (Klicka för att tillämpa):",
        "ph_subject": "Ange ämne...",
        "btn_insert_snippet": "🧩 Textmall",
        "no_contacts_found": "Inga matchande kontakter hittades."
    }
    de.setdefault("email_draft", {}).update(email_draft_add_de)
    en.setdefault("email_draft", {}).update(email_draft_add_en)
    sv.setdefault("email_draft", {}).update(email_draft_add_sv)

    # ==================== attachments ====================
    attachments_de = {
        "title": "Fall-Dateianhänge",
        "open_explorer": "📁 Explorer öffnen",
        "no_preview": "Keine Datei zur Vorschau ausgewählt",
        "add_file": "+ Datei hinzufügen...",
        "tip": "💡 Tipp: Strg+V fügt Screenshot als PNG ein",
        "no_case": "Kein Fall ausgewählt.",
        "no_files": "Keine Dateianhänge im Fallordner."
    }
    attachments_en = {
        "title": "Case File Attachments",
        "open_explorer": "📁 Open in Explorer",
        "no_preview": "No file selected for preview",
        "add_file": "+ Add file...",
        "tip": "💡 Tip: Ctrl+V pastes screenshot as PNG",
        "no_case": "No case selected.",
        "no_files": "No file attachments in case folder."
    }
    attachments_sv = {
        "title": "Bifogade ärendefiler",
        "open_explorer": "📁 Öppna i Utforskaren",
        "no_preview": "Ingen fil vald för förhandsgranskning",
        "add_file": "+ Lägg till fil...",
        "tip": "💡 Tips: Ctrl+V klistrar in skärmbild som PNG",
        "no_case": "Inget ärende valt.",
        "no_files": "Inga bifogade filer i ärendemappen."
    }
    de["attachments"] = attachments_de
    en["attachments"] = attachments_en
    sv["attachments"] = attachments_sv

    # ==================== colleague_mgmt ====================
    colleague_mgmt_de = {
        "new_colleague_btn": "+ Neuen Mitarbeiter anlegen",
        "search_placeholder": "🔍 Name, Kürzel, Abteilung...",
        "details_header": "Mitarbeiterdetails",
        "header": "👥 Mitarbeiter- & Kollegeneinträge",
        "username": "Kürzel / Username *:",
        "name": "Name / Anzeigename *:",
        "department": "Abteilung / Department:",
        "phone": "Durchwahl / Telefon:",
        "email": "E-Mail-Adresse:",
        "mobile": "Mobiltelefon:",
        "notes": "Aufgabengebiet / Notizen:",
        "ph_user": "z. B. mmueller",
        "ph_name": "z. B. Max Müller",
        "ph_phone": "z. B. 4012",
        "ph_email": "z. B. m.mueller@praxis.de",
        "ph_mobile": "z. B. 0170 1234567",
        "ph_notes": "z. B. Zuständig für PVS-Schnittstellen...",
        "chk_absent": "⚠ Kollege ist aktuell abwesend (Urlaub / Krankheit)",
        "ph_absent_reason": "Abwesenheitsgrund (z. B. Urlaub bis 30.08.)...",
        "btn_new_colleague": "➕ Neuen Mitarbeiter anlegen",
        "no_entries": "Keine Einträge gefunden."
    }
    colleague_mgmt_en = {
        "new_colleague_btn": "+ Add New Colleague",
        "search_placeholder": "🔍 Name, acronym, department...",
        "details_header": "Colleague Details",
        "header": "👥 Colleague & Employee Entries",
        "username": "Acronym / Username *:",
        "name": "Name / Display name *:",
        "department": "Department:",
        "phone": "Extension / Phone:",
        "email": "Email address:",
        "mobile": "Mobile phone:",
        "notes": "Role / Notes:",
        "ph_user": "e.g. mmueller",
        "ph_name": "e.g. Max Miller",
        "ph_phone": "e.g. 4012",
        "ph_email": "e.g. m.miller@practice.com",
        "ph_mobile": "e.g. 0170 1234567",
        "ph_notes": "e.g. Responsible for PMS interfaces...",
        "chk_absent": "⚠ Colleague is currently absent (Vacation / Sick)",
        "ph_absent_reason": "Absence reason (e.g. Vacation until Aug 30)...",
        "btn_new_colleague": "➕ Add New Colleague",
        "no_entries": "No entries found."
    }
    colleague_mgmt_sv = {
        "new_colleague_btn": "+ Skapa ny medarbetare",
        "search_placeholder": "🔍 Namn, signatur, avdelning...",
        "details_header": "Medarbetarinformation",
        "header": "👥 Medarbetare & kollegor",
        "username": "Signatur / Användarnamn *:",
        "name": "Namn / Visningsnamn *:",
        "department": "Avdelning:",
        "phone": "Anknytning / Telefon:",
        "email": "E-postadress:",
        "mobile": "Mobiltelefon:",
        "notes": "Ansvarsområde / Anteckningar:",
        "ph_user": "t.ex. msvensson",
        "ph_name": "t.ex. Max Svensson",
        "ph_phone": "t.ex. 4012",
        "ph_email": "t.ex. m.svensson@mottagning.se",
        "ph_mobile": "t.ex. 0170 1234567",
        "ph_notes": "t.ex. Ansvarig för journalsystemsgränssnitt...",
        "chk_absent": "⚠ Kollegan är för närvarande frånvarande (Semester / Sjukdom)",
        "ph_absent_reason": "Frånvaroorsak (t.ex. Semester till 30 aug)...",
        "btn_new_colleague": "➕ Skapa ny medarbetare",
        "no_entries": "Inga poster hittades."
    }
    de["colleague_mgmt"] = colleague_mgmt_de
    en["colleague_mgmt"] = colleague_mgmt_en
    sv["colleague_mgmt"] = colleague_mgmt_sv

    # ==================== customer_mgmt ====================
    customer_mgmt_de = {
        "new_practice_btn": "+ Neue Praxis anlegen",
        "cobra_import_btn": "🐍 Cobra CRM Import...",
        "search_placeholder": "🔍 Praxis / ID suchen...",
        "save_practice_btn": "💾 Praxis Speichern",
        "details_title": "Praxis-Details",
        "header": "🏥 Registrierte Praxen",
        "cust_id_lbl": "Kunden-ID (z.B. CUST-1001):",
        "practice_name_lbl": "Praxisname *:",
        "new_practice_hdr": "🆕 Neue Praxis anlegen",
        "saved_msg": "✅ Praxis gespeichert!",
        "missing_id_name": "⚠ ID und Praxisname erforderlich!",
        "btn_remove": "🗑 Entfernen",
        "ph_contact_name": "z.B. Dr. Hans Weber",
        "ph_contact_role": "z.B. Praxisinhaber, Abrechnung...",
        "ph_contact_email": "weber@praxis.de",
        "ph_contact_phone": "030 / 1234567",
        "ph_contact_note": "z.B. Erreichbar Mo-Do Vormittag",
        "err_no_website": "⚠ Keine Webseite eingetragen!",
        "lbl_contact_name": "Name *:",
        "lbl_contact_role": "Rolle / Funktion:",
        "lbl_contact_email": "E-Mail:",
        "lbl_contact_phone": "Telefon:",
        "lbl_contact_note": "Notiz:",
        "no_practices": "Keine Praxen gefunden."
    }
    customer_mgmt_en = {
        "new_practice_btn": "+ Add New Practice",
        "cobra_import_btn": "🐍 Cobra CRM Import...",
        "search_placeholder": "🔍 Search practice / ID...",
        "save_practice_btn": "💾 Save Practice",
        "details_title": "Practice Details",
        "header": "🏥 Registered Practices",
        "cust_id_lbl": "Customer ID (e.g. CUST-1001):",
        "practice_name_lbl": "Practice name *:",
        "new_practice_hdr": "🆕 Create New Practice",
        "saved_msg": "✅ Practice saved!",
        "missing_id_name": "⚠ ID and practice name required!",
        "btn_remove": "🗑 Remove",
        "ph_contact_name": "e.g. Dr. John Weber",
        "ph_contact_role": "e.g. Practice owner, Billing...",
        "ph_contact_email": "weber@practice.com",
        "ph_contact_phone": "030 / 1234567",
        "ph_contact_note": "e.g. Available Mon-Thu morning",
        "err_no_website": "⚠ No website entered!",
        "lbl_contact_name": "Name *:",
        "lbl_contact_role": "Role / Function:",
        "lbl_contact_email": "Email:",
        "lbl_contact_phone": "Phone:",
        "lbl_contact_note": "Note:",
        "no_practices": "No practices found."
    }
    customer_mgmt_sv = {
        "new_practice_btn": "+ Skapa ny mottagning",
        "cobra_import_btn": "🐍 Cobra CRM-import...",
        "search_placeholder": "🔍 Sök mottagning / ID...",
        "save_practice_btn": "💾 Spara mottagning",
        "details_title": "Mottagningsdetaljer",
        "header": "🏥 Registrerade mottagningar",
        "cust_id_lbl": "Kund-ID (t.ex. CUST-1001):",
        "practice_name_lbl": "Mottagningsnamn *:",
        "new_practice_hdr": "🆕 Skapa ny mottagning",
        "saved_msg": "✅ Mottagning sparad!",
        "missing_id_name": "⚠ ID och mottagningsnamn krävs!",
        "btn_remove": "🗑 Ta bort",
        "ph_contact_name": "t.ex. Dr. Hans Weber",
        "ph_contact_role": "t.ex. Mottagningsägare, Fakturering...",
        "ph_contact_email": "weber@mottagning.se",
        "ph_contact_phone": "030 / 1234567",
        "ph_contact_note": "t.ex. Nås mån-tors förmiddag",
        "err_no_website": "⚠ Ingen webbplats angiven!",
        "lbl_contact_name": "Namn *:",
        "lbl_contact_role": "Roll / Funktion:",
        "lbl_contact_email": "E-post:",
        "lbl_contact_phone": "Telefon:",
        "lbl_contact_note": "Anteckning:",
        "no_practices": "Inga mottagningar hittades."
    }
    de["customer_mgmt"] = customer_mgmt_de
    en["customer_mgmt"] = customer_mgmt_en
    sv["customer_mgmt"] = customer_mgmt_sv

    # ==================== new_case_dialog ====================
    new_case_dialog_de = {
        "create_btn": "Fall anlegen",
        "header": "Neuen Support-Fall erfassen",
        "is_internal": "🏢 Interner Vorgang (ohne Kundenelement)",
        "add_practice_btn": "+ Neue Praxis",
        "customer": "Kunde / Praxis:",
        "title_label": "Titel / Kurzbeschreibung:",
        "created_at": "Erstellungsdatum / Vorgangsbeginn (TT.MM.JJJJ HH:MM):",
        "schema": "Formular-Schema:",
        "tags": "Tags / Stichworte zuweisen:",
        "deadline": "Rückruf-Deadline (optional, TT.MM.JJJJ HH:MM):",
        "initial_note": "Initiale Notiz / Eingangskanal:",
        "ph_practice": "z.B. Praxis Dr. Weber",
        "ph_contact": "z.B. Dr. Hans Weber",
        "ph_phone": "030 / 123456",
        "ph_case_title": "z. B. Zuzahlungsdatei lässt sich nicht erzeugen",
        "ph_created_at": "z. B. 25.08.2026 09:30",
        "ph_deadline": "z. B. 23.08.2026 16:00"
    }
    new_case_dialog_en = {
        "create_btn": "Create Case",
        "header": "Record New Support Case",
        "is_internal": "🏢 Internal process (no customer)",
        "add_practice_btn": "+ New Practice",
        "customer": "Customer / Practice:",
        "title_label": "Title / Short description:",
        "created_at": "Creation date / Start (DD.MM.YYYY HH:MM):",
        "schema": "Form schema:",
        "tags": "Assign tags / keywords:",
        "deadline": "Callback deadline (optional, DD.MM.YYYY HH:MM):",
        "initial_note": "Initial note / Inbound channel:",
        "ph_practice": "e.g. Practice Dr. Weber",
        "ph_contact": "e.g. Dr. John Weber",
        "ph_phone": "030 / 123456",
        "ph_case_title": "e.g. Copayment file cannot be generated",
        "ph_created_at": "e.g. 25.08.2026 09:30",
        "ph_deadline": "e.g. 23.08.2026 16:00"
    }
    new_case_dialog_sv = {
        "create_btn": "Skapa ärende",
        "header": "Registrera nytt supportärende",
        "is_internal": "🏢 Internt ärende (utan kund)",
        "add_practice_btn": "+ Ny mottagning",
        "customer": "Kund / Mottagning:",
        "title_label": "Titel / Kort beskrivning:",
        "created_at": "Skapad datum / Ärendestart (ÅÅÅÅ-MM-DD TT:MM):",
        "schema": "Formulärschema:",
        "tags": "Tilldela taggar / nyckelord:",
        "deadline": "Återuppringningsfrist (valfritt, ÅÅÅÅ-MM-DD TT:MM):",
        "initial_note": "Inledande anteckning / Ingående kanal:",
        "ph_practice": "t.ex. Mottagning Dr. Weber",
        "ph_contact": "t.ex. Dr. Hans Weber",
        "ph_phone": "030 / 123456",
        "ph_case_title": "t.ex. Egenavgiftsfil kan inte genereras",
        "ph_created_at": "t.ex. 2026-08-25 09:30",
        "ph_deadline": "t.ex. 2026-08-23 16:00"
    }
    de["new_case_dialog"] = new_case_dialog_de
    en["new_case_dialog"] = new_case_dialog_en
    sv["new_case_dialog"] = new_case_dialog_sv

    # ==================== snippet_mgmt ====================
    snippet_mgmt_de = {
        "new_snippet_status": "Neuer Textbaustein (wird beim Speichern angelegt)",
        "title_required": "⚠ Bitte einen Titel eingeben.",
        "content_required": "⚠ Der Inhalt darf nicht leer sein.",
        "header": "📝 Textbaustein-Bibliothek verwalten",
        "new_snippet": "+ Neuer Textbaustein",
        "title_lbl": "Titel:",
        "cat_lbl": "Kategorie:",
        "content_lbl": "Inhalt / Baustein-Text:",
        "tags_lbl": "Tags (kommagetrennt):",
        "no_snippets": "Keine Textbausteine vorhanden.",
        "ph_title": "z. B. 📸 Rückfrage: Screenshots",
        "ph_cat": "z. B. Rückfrage, Anleitung, SQL",
        "ph_tags": "z. B. fehler, sql, anleitung",
        "ph_shortcut": "z. B. <Control-Alt-1>"
    }
    snippet_mgmt_en = {
        "new_snippet_status": "New text snippet (will be created on save)",
        "title_required": "⚠ Please enter a title.",
        "content_required": "⚠ Content cannot be empty.",
        "header": "📝 Manage Snippet Library",
        "new_snippet": "+ New Snippet",
        "title_lbl": "Title:",
        "cat_lbl": "Category:",
        "content_lbl": "Content / Snippet text:",
        "tags_lbl": "Tags (comma-separated):",
        "no_snippets": "No text snippets available.",
        "ph_title": "e.g. 📸 Follow-up: Screenshots",
        "ph_cat": "e.g. Follow-up, Manual, SQL",
        "ph_tags": "e.g. error, sql, manual",
        "ph_shortcut": "e.g. <Control-Alt-1>"
    }
    snippet_mgmt_sv = {
        "new_snippet_status": "Ny textmall (skapas när du sparar)",
        "title_required": "⚠ Ange en titel.",
        "content_required": "⚠ Innehållet får inte vara tomt.",
        "header": "📝 Hantera textmallsbibliotek",
        "new_snippet": "+ Ny textmall",
        "title_lbl": "Titel:",
        "cat_lbl": "Kategori:",
        "content_lbl": "Innehåll / Malltext:",
        "tags_lbl": "Taggar (kommaseparerade):",
        "no_snippets": "Inga textmallar tillgängliga.",
        "ph_title": "t.ex. 📸 Uppföljning: Skärmbilder",
        "ph_cat": "t.ex. Uppföljning, Instruktion, SQL",
        "ph_tags": "t.ex. fel, sql, instruktion",
        "ph_shortcut": "t.ex. <Control-Alt-1>"
    }
    de["snippet_mgmt"] = snippet_mgmt_de
    en["snippet_mgmt"] = snippet_mgmt_en
    sv["snippet_mgmt"] = snippet_mgmt_sv

    # ==================== wiki ====================
    wiki_de = {
        "header": "BookStack Offline Wiki",
        "sync_btn": "🔄 Wiki Sync",
        "search_placeholder": "📖 Wiki durchsuchen (z. B. ERR_DB_902)...",
        "syncing": "⏳ Synchronisiere Wiki im Hintergrund...",
        "enter_query": "Bitte Suchbegriff eingeben.",
        "articles_found": "Wiki-Artikel gefunden",
        "no_results": "Keine treffenden Artikel im Offline-Index."
    }
    wiki_en = {
        "header": "BookStack Offline Wiki",
        "sync_btn": "🔄 Wiki Sync",
        "search_placeholder": "📖 Search wiki (e.g. ERR_DB_902)...",
        "syncing": "⏳ Syncing wiki in background...",
        "enter_query": "Please enter a search query.",
        "articles_found": "Wiki articles found",
        "no_results": "No matching articles in offline index."
    }
    wiki_sv = {
        "header": "BookStack Offline-wiki",
        "sync_btn": "🔄 Wiki-synk",
        "search_placeholder": "📖 Sök i wiki (t.ex. ERR_DB_902)...",
        "syncing": "⏳ Synkroniserar wiki i bakgrunden...",
        "enter_query": "Ange ett sökord.",
        "articles_found": "Wiki-artiklar hittades",
        "no_results": "Inga matchande artiklar i offline-indexet."
    }
    de["wiki"] = wiki_de
    en["wiki"] = wiki_en
    sv["wiki"] = wiki_sv

    # ==================== schema_builder ====================
    schema_builder_de = {
        "new_form": "+ Neues Formular",
        "adopt_schema": "📥 Zu Realdaten übernehmen",
        "default_schemas": "🔄 Standard-Formulare",
        "field_id_ph": "Feld-ID (z. B. reason_detail)",
        "label_ph": "Beschriftung (Label)",
        "required_chk": "Pflicht",
        "add_btn": "+ Hinzufügen",
        "fields_header": "Enthaltene Formularfelder:",
        "add_field_header": "Neues Feld hinzufügen (V2 mit bedingter Logik):",
        "title_new_schema": "🆕 Neues Formular (Schema) erstellen",
        "ph_display_name": "z. B. Abrechnung & Tarife",
        "ph_schema_id": "z. B. schema_abrechnung",
        "ph_description": "Optionale Beschreibung des Formulars",
        "title_manage_schemas": "In-App Formular-Baukasten (Schemata verwalten)",
        "ph_depends_on": "Abhängig von Feld-ID",
        "ph_depends_value": "Bei Wert (z. B. Sonstiges)",
        "ph_file_types": ".pdf, .log, .png",
        "err_name_required": "Bitte Anzeigenamen eingeben.",
        "status_in_live_data": "✓ In Realdaten enthalten",
        "btn_toggle_required": "Pflicht +/-",
        "lbl_define_new_schema": "Neues Formular-Schema definieren",
        "lbl_display_name": "Anzeigename (Titel) *:",
        "lbl_schema_id": "Schema-ID (optional):",
        "lbl_description": "Beschreibung:",
        "lbl_select_form": "Formular auswählen:",
        "lbl_conditional_logic": "↳ Bedingte Logik (If/Else):",
        "lbl_file_types": "↳ Dateitypen:"
    }
    schema_builder_en = {
        "new_form": "+ New Form",
        "adopt_schema": "📥 Adopt into live data",
        "default_schemas": "🔄 Default Forms",
        "field_id_ph": "Field ID (e.g. reason_detail)",
        "label_ph": "Label",
        "required_chk": "Required",
        "add_btn": "+ Add",
        "fields_header": "Included form fields:",
        "add_field_header": "Add new field (V2 with conditional logic):",
        "title_new_schema": "🆕 Create New Form (Schema)",
        "ph_display_name": "e.g. Billing & Tariffs",
        "ph_schema_id": "e.g. schema_billing",
        "ph_description": "Optional description of the form",
        "title_manage_schemas": "In-App Form Builder (Manage Schemas)",
        "ph_depends_on": "Depends on field ID",
        "ph_depends_value": "When value (e.g. Other)",
        "ph_file_types": ".pdf, .log, .png",
        "err_name_required": "Please enter display name.",
        "status_in_live_data": "✓ Included in live data",
        "btn_toggle_required": "Required +/-",
        "lbl_define_new_schema": "Define new form schema",
        "lbl_display_name": "Display name (Title) *:",
        "lbl_schema_id": "Schema ID (optional):",
        "lbl_description": "Description:",
        "lbl_select_form": "Select form:",
        "lbl_conditional_logic": "↳ Conditional logic (If/Else):",
        "lbl_file_types": "↳ File types:"
    }
    schema_builder_sv = {
        "new_form": "+ Nytt formulär",
        "adopt_schema": "📥 Tillämpa på livedata",
        "default_schemas": "🔄 Standardformulär",
        "field_id_ph": "Fält-ID (t.ex. reason_detail)",
        "label_ph": "Etikett",
        "required_chk": "Obligatorisk",
        "add_btn": "+ Lägg till",
        "fields_header": "Inkluderade formulärfält:",
        "add_field_header": "Lägg till nytt fält (V2 med villkorsstyrd logik):",
        "title_new_schema": "🆕 Skapa nytt formulär (schema)",
        "ph_display_name": "t.ex. Fakturering & avtal",
        "ph_schema_id": "t.ex. schema_fakturering",
        "ph_description": "Valfri beskrivning av formuläret",
        "title_manage_schemas": "In-App formulärbyggare (Hantera scheman)",
        "ph_depends_on": "Beroende av fält-ID",
        "ph_depends_value": "Vid värde (t.ex. Övrigt)",
        "ph_file_types": ".pdf, .log, .png",
        "err_name_required": "Ange ett visningsnamn.",
        "status_in_live_data": "✓ Ingår i livedata",
        "btn_toggle_required": "Obligatorisk +/-",
        "lbl_define_new_schema": "Definiera nytt formulärschema",
        "lbl_display_name": "Visningsnamn (Titel) *:",
        "lbl_schema_id": "Schema-ID (valfritt):",
        "lbl_description": "Beskrivning:",
        "lbl_select_form": "Välj formulär:",
        "lbl_conditional_logic": "↳ Villkorsstyrd logik (If/Else):",
        "lbl_file_types": "↳ Filtyper:"
    }
    de["schema_builder"] = schema_builder_de
    en["schema_builder"] = schema_builder_en
    sv["schema_builder"] = schema_builder_sv

    # ==================== export_dialog ====================
    export_dialog_de = {
        "manage_templates_btn": "🛠 Vorlagen verwalten",
        "force_export_chk": "Trotz unvollständiger Daten exportieren ([FEHLT: ...] Platzhalter)",
        "save_file_btn": "In Datei speichern...",
        "copy_btn": "In Zwischenablage kopieren",
        "export_for": "Export für Fall",
        "select_template": "Vorlage auswählen:",
        "no_template": "Keine Vorlage",
        "preview_header": "Vorschau des exportierten Textes:"
    }
    export_dialog_en = {
        "manage_templates_btn": "🛠 Manage Templates",
        "force_export_chk": "Export despite incomplete data ([MISSING: ...] placeholder)",
        "save_file_btn": "Save to file...",
        "copy_btn": "Copy to clipboard",
        "export_for": "Export for case",
        "select_template": "Select template:",
        "no_template": "No template",
        "preview_header": "Preview of exported text:"
    }
    export_dialog_sv = {
        "manage_templates_btn": "🛠 Hantera mallar",
        "force_export_chk": "Exportera trots ofullständiga data ([SAKNAS: ...] platshållare)",
        "save_file_btn": "Spara till fil...",
        "copy_btn": "Kopiera till urklipp",
        "export_for": "Exportera för ärende",
        "select_template": "Välj mall:",
        "no_template": "Ingen mall",
        "preview_header": "Förhandsgranskning av exporterad text:"
    }
    de["export_dialog"] = export_dialog_de
    en["export_dialog"] = export_dialog_en
    sv["export_dialog"] = export_dialog_sv

    # ==================== zip_import ====================
    zip_import_de = {
        "root_folder_btn": "📁 Gesamt-Zielordner wählen",
        "custom_paths_btn": "⚙ Einzelne Pfade anpassen",
        "warning_overwrite": "⚠ Hinweis: Beim Importieren werden vorhandene Dateien mit gleichem Namen am Zielspeicherort überschrieben.",
        "select_mode": "Wählen Sie aus, wie die Zielspeicherorte festgelegt werden sollen:",
        "unpack_btn": "📥 Daten entpacken & importieren",
        "main_target_dir": "Haupt-Zielverzeichnis (Erzeugt automatisch data/ und attachments/ Unterordner):",
        "data_loc": "1. Speicherort für Datendateien & Profile (data/):",
        "att_loc": "2. Speicherort für Fall-Anhänge (attachments/):",
        "title_select_main_target": "Gesamt-Zielverzeichnis wählen",
        "title_select_data_target": "Zielverzeichnis für Datendateien (data/) wählen",
        "title_select_att_target": "Zielverzeichnis für Fall-Anhänge (attachments/) wählen"
    }
    zip_import_en = {
        "root_folder_btn": "📁 Choose Overall Target Folder",
        "custom_paths_btn": "⚙ Customize Individual Paths",
        "warning_overwrite": "⚠ Notice: Importing will overwrite existing files with the same name at the destination.",
        "select_mode": "Select how target locations should be determined:",
        "unpack_btn": "📥 Unpack & Import Data",
        "main_target_dir": "Main target directory (Automatically creates data/ and attachments/ subfolders):",
        "data_loc": "1. Storage location for data files & profiles (data/):",
        "att_loc": "2. Storage location for case attachments (attachments/):",
        "title_select_main_target": "Select Overall Target Directory",
        "title_select_data_target": "Select Target Directory for Data Files (data/)",
        "title_select_att_target": "Select Target Directory for Attachments (attachments/)"
    }
    zip_import_sv = {
        "root_folder_btn": "📁 Välj övergripande målmapp",
        "custom_paths_btn": "⚙ Anpassa enskilda sökvägar",
        "warning_overwrite": "⚠ Obs: Importering skriver över befintliga filer med samma namn på målplatsen.",
        "select_mode": "Välj hur målplatser ska bestämmas:",
        "unpack_btn": "📥 Packa upp & importera data",
        "main_target_dir": "Huvudmålkatalog (Skapar automatiskt undermapparna data/ och attachments/):",
        "data_loc": "1. Lagringsplats för datafiler & profiler (data/):",
        "att_loc": "2. Lagringsplats för ärendebilagor (attachments/):",
        "title_select_main_target": "Välj övergripande målkatalog",
        "title_select_data_target": "Välj målkatalog för datafiler (data/)",
        "title_select_att_target": "Välj målkatalog för ärendebilagor (attachments/)"
    }
    de["zip_import"] = zip_import_de
    en["zip_import"] = zip_import_en
    sv["zip_import"] = zip_import_sv

    # ==================== new_case ====================
    new_case_de = {
        "add_tag": "+ Tag",
        "tag_input_prompt": "Geben Sie den Namen des neuen Tags ein:",
        "tag_input_title": "Neuen Tag hinzufügen",
        "title_required": "Bitte einen Titel für den Fall eingeben.",
        "future_date": "Das Erstellungsdatum darf nicht in der Zukunft liegen.",
        "invalid_date": "Ungültiges Erstellungsdatum-Format (z. B. TT.MM.JJJJ HH:MM)."
    }
    new_case_en = {
        "add_tag": "+ Tag",
        "tag_input_prompt": "Enter the name of the new tag:",
        "tag_input_title": "Add New Tag",
        "title_required": "Please enter a title for the case.",
        "future_date": "Creation date cannot be in the future.",
        "invalid_date": "Invalid creation date format (e.g. DD.MM.YYYY HH:MM)."
    }
    new_case_sv = {
        "add_tag": "+ Tagg",
        "tag_input_prompt": "Ange namnet på den nya taggen:",
        "tag_input_title": "Lägg till ny tagg",
        "title_required": "Ange en titel för ärendet.",
        "future_date": "Skapandedatumet kan inte vara i framtiden.",
        "invalid_date": "Ogiltigt datumformat (t.ex. ÅÅÅÅ-MM-DD TT:MM)."
    }
    de["new_case"] = new_case_de
    en["new_case"] = new_case_en
    sv["new_case"] = new_case_sv

    # ==================== p2p ====================
    p2p_de = {
        "reload_compare": "Neu Laden / Vergleichen",
        "import_selected": "Ausgewählte Fälle übernehmen",
        "no_colleague_selected": "Kein Kollege ausgewählt.",
        "select_at_least_one": "Bitte mindestens einen Fall zur Übernahme auswählen.",
        "select_colleague": "Kollege auswählen:",
        "no_colleagues_cfg": "Keine Kollegen konfiguriert",
        "no_diff_cases": "Keine abweichenden Fälle vorhanden."
    }
    p2p_en = {
        "reload_compare": "Reload / Compare",
        "import_selected": "Adopt Selected Cases",
        "no_colleague_selected": "No colleague selected.",
        "select_at_least_one": "Please select at least one case to adopt.",
        "select_colleague": "Select colleague:",
        "no_colleagues_cfg": "No colleagues configured",
        "no_diff_cases": "No differing cases found."
    }
    p2p_sv = {
        "reload_compare": "Ladda om / Jämför",
        "import_selected": "Tillämpa valda ärenden",
        "no_colleague_selected": "Ingen kollega vald.",
        "select_at_least_one": "Välj minst ett ärende att importera.",
        "select_colleague": "Välj kollega:",
        "no_colleagues_cfg": "Inga kollegor konfigurerade",
        "no_diff_cases": "Inga avvikande ärenden hittades."
    }
    de["p2p"] = p2p_de
    en["p2p"] = p2p_en
    sv["p2p"] = p2p_sv

    # ==================== quick_customer ====================
    quick_customer_de = {
        "err_name": "Bitte Praxisnamen eingeben.",
        "header": "Neue Praxis anlegen",
        "practice_name": "Praxisname *:",
        "contact_person": "Ansprechpartner:",
        "phone": "Telefon:",
        "is_vip": "⭐ VIP-Praxis"
    }
    quick_customer_en = {
        "err_name": "Please enter a practice name.",
        "header": "Create New Practice",
        "practice_name": "Practice name *:",
        "contact_person": "Contact person:",
        "phone": "Phone:",
        "is_vip": "⭐ VIP Practice"
    }
    quick_customer_sv = {
        "err_name": "Ange ett mottagningsnamn.",
        "header": "Skapa ny mottagning",
        "practice_name": "Mottagningsnamn *:",
        "contact_person": "Kontaktperson:",
        "phone": "Telefon:",
        "is_vip": "⭐ VIP-mottagning"
    }
    de["quick_customer"] = quick_customer_de
    en["quick_customer"] = quick_customer_en
    sv["quick_customer"] = quick_customer_sv

    # ==================== export ====================
    export_de = {
        "no_template": "Keine Vorlage ausgewählt.",
        "ready": "✅ Vorlage bereit zum Export.",
        "incomplete": "⚠ Unvollständig! Bitte Felder ergänzen oder Force-Export aktivieren.",
        "copied": "📋 Erfolgreich in Zwischenablage kopiert!",
        "missing_fields_hdr": "⚠ Fehlende Pflichtfelder direkt ergänzen:"
    }
    export_en = {
        "no_template": "No template selected.",
        "ready": "✅ Template ready for export.",
        "incomplete": "⚠ Incomplete! Please fill in fields or enable force export.",
        "copied": "📋 Successfully copied to clipboard!",
        "missing_fields_hdr": "⚠ Fill missing required fields directly:"
    }
    export_sv = {
        "no_template": "Ingen mall vald.",
        "ready": "✅ Mall redo för export.",
        "incomplete": "⚠ Ofullständig! Fyll i fält eller aktivera tvingad export.",
        "copied": "📋 Kopierades till urklipp!",
        "missing_fields_hdr": "⚠ Fyll i obligatoriska fält direkt:"
    }
    de["export"] = export_de
    en["export"] = export_en
    sv["export"] = export_sv

    # ==================== followup ====================
    followup_de = {
        "presets_lbl": "⚡ Schnellauswahl / Presets:",
        "date_lbl": "📅 Erinnerungs-Datum & Uhrzeit (TT.MM.JJJJ HH:MM):",
        "note_lbl": "📝 Notiz / Nachfrage-Grund (Optional):",
        "save_btn": "💾 Wiedervorlage Speichern",
        "no_due_cases": "Keine fälligen Wiedervorlagen aktuell vorhanden.",
        "dialog_title": "🔔 Wiedervorlage & Nachfrage-Erinnerung",
        "ph_date": "TT.MM.JJJJ 09:00",
        "ph_note": "z. B. Beim Entwickler nach dem Stand fragen..."
    }
    followup_en = {
        "presets_lbl": "⚡ Quick Selection / Presets:",
        "date_lbl": "📅 Reminder Date & Time (DD.MM.YYYY HH:MM):",
        "note_lbl": "📝 Note / Follow-up reason (Optional):",
        "save_btn": "💾 Save Follow-up",
        "no_due_cases": "No due follow-ups currently present.",
        "dialog_title": "🔔 Follow-up & Reminder",
        "ph_date": "DD.MM.YYYY 09:00",
        "ph_note": "e.g. Ask developer about status..."
    }
    followup_sv = {
        "presets_lbl": "⚡ Snabbval / Förinställningar:",
        "date_lbl": "📅 Påminnelsedatum & tid (ÅÅÅÅ-MM-DD TT:MM):",
        "note_lbl": "📝 Anteckning / Uppföljningsorsak (Valfritt):",
        "save_btn": "💾 Spara uppföljning",
        "no_due_cases": "Inga förfallna uppföljningar för närvarande.",
        "dialog_title": "🔔 Uppföljning & påminnelse",
        "ph_date": "ÅÅÅÅ-MM-DD 09:00",
        "ph_note": "t.ex. Fråga utvecklaren om status..."
    }
    de["followup"] = followup_de
    en["followup"] = followup_en
    sv["followup"] = followup_sv

    # ==================== convert_schema (merge updates) ====================
    convert_schema_add_de = {
        "select_valid": "Bitte ein gültiges Ziel-Formular auswählen.",
        "already_used": "Der Fall verwendet bereits dieses Formular-Schema.",
        "header": "🔄 Formular-Schema umwandeln",
        "select_target": "Neues Ziel-Formular auswählen:"
    }
    convert_schema_add_en = {
        "select_valid": "Please select a valid target form.",
        "already_used": "The case already uses this form schema.",
        "header": "🔄 Convert Form Schema",
        "select_target": "Select new target form:"
    }
    convert_schema_add_sv = {
        "select_valid": "Välj ett giltigt målformulär.",
        "already_used": "Ärendet använder redan detta formulärschema.",
        "header": "🔄 Konvertera formulärschema",
        "select_target": "Välj nytt målformulär:"
    }
    de.setdefault("convert_schema", {}).update(convert_schema_add_de)
    en.setdefault("convert_schema", {}).update(convert_schema_add_en)
    sv.setdefault("convert_schema", {}).update(convert_schema_add_sv)

    # ==================== email_import ====================
    email_import_de = {
        "info_msg": "Eingehende E-Mails aus Microsoft Outlook / Posteingang werden automatisch mit bestehenden Fällen abgeglichen.",
        "fetching": "⏳ Rufe Posteingang ab...",
        "refresh_btn": "🔄 Posteingang aktualisieren",
        "no_emails": "Keine neuen E-Mails im Posteingang gefunden.",
        "btn_create_new_case": "➕ Als neuen Fall anlegen",
        "btn_ignore": "🗑 Ignorieren"
    }
    email_import_en = {
        "info_msg": "Incoming emails from Microsoft Outlook / Inbox are automatically matched with existing cases.",
        "fetching": "⏳ Fetching inbox...",
        "refresh_btn": "🔄 Refresh Inbox",
        "no_emails": "No new emails found in inbox.",
        "btn_create_new_case": "➕ Create as new case",
        "btn_ignore": "🗑 Ignore"
    }
    email_import_sv = {
        "info_msg": "Inkommande e-postmeddelanden från Microsoft Outlook / Inkorg matchas automatiskt med befintliga ärenden.",
        "fetching": "⏳ Hämtar inkorg...",
        "refresh_btn": "🔄 Uppdatera inkorg",
        "no_emails": "Inga nya e-postmeddelanden hittades i inkorgen.",
        "btn_create_new_case": "➕ Skapa som nytt ärende",
        "btn_ignore": "🗑 Ignorera"
    }
    de["email_import"] = email_import_de
    en["email_import"] = email_import_en
    sv["email_import"] = email_import_sv

    # ==================== template_mgmt ====================
    template_mgmt_de = {
        "new_template": "+ Neue Vorlage",
        "load_defaults": "🔄 Standard-Vorlagen laden",
        "header": "📄 Export-Vorlagen-Verwaltung",
        "no_templates": "Keine Vorlagen vorhanden.",
        "ph_template_id": "z. B. gitlab_dev_ticket",
        "ph_name": "z. B. GitLab / Dev-Ticket",
        "ph_desc": "Kurze Beschreibung des Formats...",
        "title_manage": "📄 Export-Vorlagen verwalten",
        "title_edit": "✏ Vorlage bearbeiten",
        "title_new": "➕ Neue Export-Vorlage",
        "lbl_template_id": "Vorlage-ID *:",
        "lbl_name": "Anzeigename *:",
        "lbl_desc": "Beschreibung:",
        "lbl_action_type": "Ziel-Aktion / Typ:",
        "lbl_schemas": "Zugeordnete Formular-Schemas:",
        "lbl_required_fields": "Erforderliche Pflichtfelder vor Export:",
        "lbl_jinja_text": "Jinja2 Template Text (Markdown / Text):",
        "btn_in_live_data": "✓ In Realdaten enthalten",
        "btn_adopt": "📥 Zu Realdaten übernehmen",
        "btn_render_preview": "👁 Live-Vorschau rendern",
        "btn_save_template": "💾 Vorlage Speichern"
    }
    template_mgmt_en = {
        "new_template": "+ New Template",
        "load_defaults": "🔄 Load Default Templates",
        "header": "📄 Export Template Management",
        "no_templates": "No templates available.",
        "ph_template_id": "e.g. gitlab_dev_ticket",
        "ph_name": "e.g. GitLab / Dev-Ticket",
        "ph_desc": "Short description of the format...",
        "title_manage": "📄 Manage Export Templates",
        "title_edit": "✏ Edit Template",
        "title_new": "➕ New Export Template",
        "lbl_template_id": "Template ID *:",
        "lbl_name": "Display name *:",
        "lbl_desc": "Description:",
        "lbl_action_type": "Target action / Type:",
        "lbl_schemas": "Associated form schemas:",
        "lbl_required_fields": "Required fields before export:",
        "lbl_jinja_text": "Jinja2 Template Text (Markdown / Text):",
        "btn_in_live_data": "✓ Included in live data",
        "btn_adopt": "📥 Adopt into live data",
        "btn_render_preview": "👁 Render live preview",
        "btn_save_template": "💾 Save Template"
    }
    template_mgmt_sv = {
        "new_template": "+ Ny mall",
        "load_defaults": "🔄 Ladda standardmallar",
        "header": "📄 Hantering av exportmallar",
        "no_templates": "Inga mallar tillgängliga.",
        "ph_template_id": "t.ex. gitlab_dev_ticket",
        "ph_name": "t.ex. GitLab / Dev-Ticket",
        "ph_desc": "Kort beskrivning av formatet...",
        "title_manage": "📄 Hantera exportmallar",
        "title_edit": "✏ Redigera mall",
        "title_new": "➕ Ny exportmall",
        "lbl_template_id": "Mall-ID *:",
        "lbl_name": "Visningsnamn *:",
        "lbl_desc": "Beskrivning:",
        "lbl_action_type": "Målåtgärd / Typ:",
        "lbl_schemas": "Tillhörande formulärscheman:",
        "lbl_required_fields": "Obligatoriska fält före export:",
        "lbl_jinja_text": "Jinja2-malltext (Markdown / Text):",
        "btn_in_live_data": "✓ Ingår i livedata",
        "btn_adopt": "📥 Tillämpa på livedata",
        "btn_render_preview": "👁 Förhandsgranska live",
        "btn_save_template": "💾 Spara mall"
    }
    de["template_mgmt"] = template_mgmt_de
    en["template_mgmt"] = template_mgmt_en
    sv["template_mgmt"] = template_mgmt_sv

    # ==================== snippet_picker (merge updates) ====================
    snippet_picker_add_de = {
        "search": "🔍 Textbaustein suchen...",
        "preview": "Vorschau des Textbausteins:",
        "no_snippets": "Keine Textbausteine gefunden.",
        "dialog_title": "🧩 Textbaustein auswählen & einfügen"
    }
    snippet_picker_add_en = {
        "search": "🔍 Search snippet...",
        "preview": "Snippet preview:",
        "no_snippets": "No snippets found.",
        "dialog_title": "🧩 Select & Insert Text Snippet"
    }
    snippet_picker_add_sv = {
        "search": "🔍 Sök textmall...",
        "preview": "Förhandsgranskning av textmall:",
        "no_snippets": "Inga textmallar hittades.",
        "dialog_title": "🧩 Välj & infoga textmall"
    }
    de.setdefault("snippet_picker", {}).update(snippet_picker_add_de)
    en.setdefault("snippet_picker", {}).update(snippet_picker_add_en)
    sv.setdefault("snippet_picker", {}).update(snippet_picker_add_sv)

    # ==================== cockpit (merge updates) ====================
    cockpit_add_de = {
        "followup_at": "🔔 Nachfragen am:",
        "email_copied_title": "📋 E-Mail kopiert",
        "no_email_title": "⚠ Keine E-Mail-Adresse",
        "no_email_msg": "Für diese Praxis ist keine E-Mail-Adresse hinterlegt."
    }
    cockpit_add_en = {
        "followup_at": "🔔 Follow up on:",
        "email_copied_title": "📋 Email Copied",
        "no_email_title": "⚠ No Email Address",
        "no_email_msg": "No email address is registered for this practice."
    }
    cockpit_add_sv = {
        "followup_at": "🔔 Följ upp den:",
        "email_copied_title": "📋 E-post kopierad",
        "no_email_title": "⚠ Ingen e-postadress",
        "no_email_msg": "Ingen e-postadress är registrerad för denna mottagning."
    }
    de.setdefault("cockpit", {}).update(cockpit_add_de)
    en.setdefault("cockpit", {}).update(cockpit_add_en)
    sv.setdefault("cockpit", {}).update(cockpit_add_sv)

    # ==================== case_list ====================
    case_list_de = {
        "zero_cases": "0 Fälle",
        "completed_badge": "✓ ERLEDIGT",
        "no_cases": "Keine Fälle gefunden.",
        "followup_at": "🔔 Nachfragen am:"
    }
    case_list_en = {
        "zero_cases": "0 Cases",
        "completed_badge": "✓ COMPLETED",
        "no_cases": "No cases found.",
        "followup_at": "🔔 Follow up on:"
    }
    case_list_sv = {
        "zero_cases": "0 ärenden",
        "completed_badge": "✓ KLAR",
        "no_cases": "Inga ärenden hittades.",
        "followup_at": "🔔 Följ upp den:"
    }
    de["case_list"] = case_list_de
    en["case_list"] = case_list_en
    sv["case_list"] = case_list_sv

    # ==================== email_calendar (merge updates) ====================
    email_calendar_add_de = {
        "client_opened": "✓ Mail-Client wurde mit dem Entwurf aufgerufen.",
        "text_copied": "✓ E-Mail Text wurde in die Zwischenablage kopiert.",
        "ph_recipient": "praxis@beispiel.de...",
        "ph_subject": "Betreff eingeben...",
        "title_save_ics": "Kalenderdatei (.ics) speichern",
        "lbl_recipient": "Empfänger (E-Mail):",
        "lbl_subject": "Betreff:",
        "lbl_body": "E-Mail Nachrichtentext:",
        "btn_snippet": "🧩 Textbaustein"
    }
    email_calendar_add_en = {
        "client_opened": "✓ Mail client opened with the draft.",
        "text_copied": "✓ Email text copied to clipboard.",
        "ph_recipient": "practice@example.com...",
        "ph_subject": "Enter subject...",
        "title_save_ics": "Save Calendar File (.ics)",
        "lbl_recipient": "Recipient (Email):",
        "lbl_subject": "Subject:",
        "lbl_body": "Email message body:",
        "btn_snippet": "🧩 Text Snippet"
    }
    email_calendar_add_sv = {
        "client_opened": "✓ E-postklienten öppnades med utkastet.",
        "text_copied": "✓ E-posttexten kopierades till urklipp.",
        "ph_recipient": "mottagning@exempel.se...",
        "ph_subject": "Ange ämne...",
        "title_save_ics": "Spara kalenderfil (.ics)",
        "lbl_recipient": "Mottagare (E-post):",
        "lbl_subject": "Ämne:",
        "lbl_body": "E-postmeddelandetext:",
        "btn_snippet": "🧩 Textmall"
    }
    de.setdefault("email_calendar", {}).update(email_calendar_add_de)
    en.setdefault("email_calendar", {}).update(email_calendar_add_en)
    sv.setdefault("email_calendar", {}).update(email_calendar_add_sv)

    # ==================== board (merge updates) ====================
    board_add_de = {
        "cockpit_btn": "🎯 Cockpit",
        "collapse_btn": "◀ Zuklappen",
        "col_support": "📥 Support ({count})",
        "col_dev": "💻 Entwickler ({count})",
        "col_followup": "🔔 Wiedervorlage ({count})",
        "col_done": "✓ Erledigt ({count})"
    }
    board_add_en = {
        "cockpit_btn": "🎯 Cockpit",
        "collapse_btn": "◀ Collapse",
        "col_support": "📥 Support ({count})",
        "col_dev": "💻 Developer ({count})",
        "col_followup": "🔔 Follow-up ({count})",
        "col_done": "✓ Completed ({count})"
    }
    board_add_sv = {
        "cockpit_btn": "🎯 Cockpit",
        "collapse_btn": "◀ Fäll ihop",
        "col_support": "📥 Support ({count})",
        "col_dev": "💻 Utvecklare ({count})",
        "col_followup": "🔔 Uppföljning ({count})",
        "col_done": "✓ Klart ({count})"
    }
    de.setdefault("board", {}).update(board_add_de)
    en.setdefault("board", {}).update(board_add_en)
    sv.setdefault("board", {}).update(board_add_sv)

    # ==================== table ====================
    table_de = {
        "details_header": "📋 Falldetails & Formular (Wählen Sie einen Fall aus der Tabelle)",
        "save_btn": "💾 Ändern & Speichern",
        "tab_form": "📝 Formular & Ausfüllen",
        "tab_timeline": "🕒 Zeitleiste",
        "tab_attachments": "📎 Anhänge",
        "details_title": "📋 Falldetails: {case_id} - {title}"
    }
    table_en = {
        "details_header": "📋 Case Details & Form (Select a case from table)",
        "save_btn": "💾 Modify & Save",
        "tab_form": "📝 Form & Fill-in",
        "tab_timeline": "🕒 Timeline",
        "tab_attachments": "📎 Attachments",
        "details_title": "📋 Case Details: {case_id} - {title}"
    }
    table_sv = {
        "details_header": "📋 Ärendedetaljer & formulär (Välj ett ärende från tabellen)",
        "save_btn": "💾 Ändra & spara",
        "tab_form": "📝 Formulär & ifyllning",
        "tab_timeline": "🕒 Tidslinje",
        "tab_attachments": "📎 Bilagor",
        "details_title": "📋 Ärendedetaljer: {case_id} - {title}"
    }
    de["table"] = table_de
    en["table"] = table_en
    sv["table"] = table_sv

    # ==================== date_picker ====================
    date_picker_de = {
        "time_lbl": "⏰ Uhrzeit:",
        "o_clock": "Uhr",
        "dialog_title": "📅 Datum auswählen",
        "preset_today_1130": "Heute 11:30",
        "preset_today_1330": "Heute 13:30",
        "preset_today_1630": "Heute 16:30",
        "preset_tomorrow_0800": "Morgen 08:00",
        "preset_plus_1day": "+ 1 Tag",
        "preset_plus_1week": "+ 1 Woche",
        "preset_plus_1hour": "+ 1 Std.",
        "preset_plus_2hours": "+ 2 Std."
    }
    date_picker_en = {
        "time_lbl": "⏰ Time:",
        "o_clock": "o'clock",
        "dialog_title": "📅 Select Date",
        "preset_today_1130": "Today 11:30",
        "preset_today_1330": "Today 13:30",
        "preset_today_1630": "Today 16:30",
        "preset_tomorrow_0800": "Tomorrow 08:00",
        "preset_plus_1day": "+ 1 Day",
        "preset_plus_1week": "+ 1 Week",
        "preset_plus_1hour": "+ 1 hr",
        "preset_plus_2hours": "+ 2 hrs"
    }
    date_picker_sv = {
        "time_lbl": "⏰ Tid:",
        "o_clock": "kl.",
        "dialog_title": "📅 Välj datum",
        "preset_today_1130": "Idag 11:30",
        "preset_today_1330": "Idag 13:30",
        "preset_today_1630": "Idag 16:30",
        "preset_tomorrow_0800": "Imorgon 08:00",
        "preset_plus_1day": "+ 1 dag",
        "preset_plus_1week": "+ 1 vecka",
        "preset_plus_1hour": "+ 1 tim",
        "preset_plus_2hours": "+ 2 tim"
    }
    de["date_picker"] = date_picker_de
    en["date_picker"] = date_picker_en
    sv["date_picker"] = date_picker_sv

    # ==================== searchable_combo ====================
    searchable_combo_de = {
        "placeholder": "🔍 Buchstaben eintippen zum Suchen...",
        "no_results": "Keine Praxen gefunden"
    }
    searchable_combo_en = {
        "placeholder": "🔍 Type letters to search...",
        "no_results": "No practices found"
    }
    searchable_combo_sv = {
        "placeholder": "🔍 Skriv bokstäver för att söka...",
        "no_results": "Inga mottagningar hittades"
    }
    de["searchable_combo"] = searchable_combo_de
    en["searchable_combo"] = searchable_combo_en
    sv["searchable_combo"] = searchable_combo_sv

    # ==================== help_dialog (merge updates) ====================
    help_dialog_add_de = {
        "no_topics": "Keine Themen gefunden."
    }
    help_dialog_add_en = {
        "no_topics": "No topics found."
    }
    help_dialog_add_sv = {
        "no_topics": "Inga ämnen hittades."
    }
    de.setdefault("help_dialog", {}).update(help_dialog_add_de)
    en.setdefault("help_dialog", {}).update(help_dialog_add_en)
    sv.setdefault("help_dialog", {}).update(help_dialog_add_sv)

    # ==================== analytics (merge updates) ====================
    analytics_add_de = {
        "copied_title": "📋 Statistik kopiert",
        "days_unit": "Tage",
        "hours_unit": "Std",
        "critical_red": "🔴 Rot (Kritisch)",
        "medium_yellow": "🟡 Gelb (Mittel)",
        "normal_green": "🟢 Grün (Normal)",
        "report_copied_msg": "Statistik-Bericht wurde in die Zwischenablage kopiert.",
        "report_title": "📊 Support-Cockpit KPI- & Statistikbericht",
        "report_generated_at": "Generiert am: {timestamp}"
    }
    analytics_add_en = {
        "copied_title": "📋 Statistics Copied",
        "days_unit": "days",
        "hours_unit": "hrs",
        "critical_red": "🔴 Red (Critical)",
        "medium_yellow": "🟡 Yellow (Medium)",
        "normal_green": "🟢 Green (Normal)",
        "report_copied_msg": "Statistics report copied to clipboard.",
        "report_title": "📊 Support-Cockpit KPI & Statistics Report",
        "report_generated_at": "Generated at: {timestamp}"
    }
    analytics_add_sv = {
        "copied_title": "📋 Statistik kopierad",
        "days_unit": "dagar",
        "hours_unit": "tim",
        "critical_red": "🔴 Röd (Kritisk)",
        "medium_yellow": "🟡 Gul (Medel)",
        "normal_green": "🟢 Grön (Normal)",
        "report_copied_msg": "Statistikrapporten kopierades till urklipp.",
        "report_title": "📊 Support-Cockpit KPI- & statistikrapport",
        "report_generated_at": "Genererad: {timestamp}"
    }
    de.setdefault("analytics", {}).update(analytics_add_de)
    en.setdefault("analytics", {}).update(analytics_add_en)
    sv.setdefault("analytics", {}).update(analytics_add_sv)

    # ==================== form ====================
    form_de = {
        "no_fields": "Keine Formularfelder definiert."
    }
    form_en = {
        "no_fields": "No form fields defined."
    }
    form_sv = {
        "no_fields": "Inga formulärfält definierade."
    }
    de["form"] = form_de
    en["form"] = form_en
    sv["form"] = form_sv

    # ==================== timeline ====================
    timeline_de = {
        "no_notes": "Keine Notizen vorhanden."
    }
    timeline_en = {
        "no_notes": "No notes available."
    }
    timeline_sv = {
        "no_notes": "Inga anteckningar tillgängliga."
    }
    de["timeline"] = timeline_de
    en["timeline"] = timeline_en
    sv["timeline"] = timeline_sv

    # ==================== toast ====================
    toast_de = {
        "reminder_title": "Erinnerung"
    }
    toast_en = {
        "reminder_title": "Reminder"
    }
    toast_sv = {
        "reminder_title": "Påminnelse"
    }
    de["toast"] = toast_de
    en["toast"] = toast_en
    sv["toast"] = toast_sv

    # ==================== board_columns ====================
    board_columns_de = {
        "NEW": "Neu",
        "ACTION_REQUIRED": "Aktion erforderlich",
        "WAITING": "Warten auf zuständige Stelle",
        "IN_PROGRESS": "In Bearbeitung",
        "DONE": "Erledigt"
    }
    board_columns_en = {
        "NEW": "New",
        "ACTION_REQUIRED": "Action required",
        "WAITING": "Waiting for assigned party",
        "IN_PROGRESS": "In progress",
        "DONE": "Completed"
    }
    board_columns_sv = {
        "NEW": "Nytt",
        "ACTION_REQUIRED": "Åtgärd krävs",
        "WAITING": "Väntar på ansvarig enhet",
        "IN_PROGRESS": "Pågående",
        "DONE": "Klart"
    }
    de["board_columns"] = board_columns_de
    en["board_columns"] = board_columns_en
    sv["board_columns"] = board_columns_sv

    # ==================== channels (merge additional constants) ====================
    channels_add_de = {
        "PHONE_INBOUND": "Eingehender Telefonanruf",
        "PHONE_OUTBOUND": "Ausgehender Telefonanruf",
        "EMAIL_IN": "Eingehende E-Mail",
        "EMAIL_OUT": "Ausgehende E-Mail",
        "GITLAB_TICKET_CREATED": "GitLab Ticket erstellt",
        "GITLAB_TICKET_UPDATED": "GitLab Ticket aktualisiert",
        "GITLAB_TICKET_CLOSED": "GitLab Ticket geschlossen",
        "OTHER": "Sonstiges",
        "IN_PERSON": "Persönlich / Vor Ort",
        "SLACK_CHAT": "Slack / Chat"
    }
    channels_add_en = {
        "PHONE_INBOUND": "Inbound Phone Call",
        "PHONE_OUTBOUND": "Outbound Phone Call",
        "EMAIL_IN": "Inbound Email",
        "EMAIL_OUT": "Outbound Email",
        "GITLAB_TICKET_CREATED": "GitLab Ticket Created",
        "GITLAB_TICKET_UPDATED": "GitLab Ticket Updated",
        "GITLAB_TICKET_CLOSED": "GitLab Ticket Closed",
        "OTHER": "Other",
        "IN_PERSON": "In Person / On Site",
        "SLACK_CHAT": "Slack / Chat"
    }
    channels_add_sv = {
        "PHONE_INBOUND": "Inkommande telefonsamtal",
        "PHONE_OUTBOUND": "Utgående telefonsamtal",
        "EMAIL_IN": "Inkommande e-post",
        "EMAIL_OUT": "Utgående e-post",
        "GITLAB_TICKET_CREATED": "GitLab-ärende skapat",
        "GITLAB_TICKET_UPDATED": "GitLab-ärende uppdaterat",
        "GITLAB_TICKET_CLOSED": "GitLab-ärende stängt",
        "OTHER": "Övrigt",
        "IN_PERSON": "Personligen / På plats",
        "SLACK_CHAT": "Slack / Chatt"
    }
    de.setdefault("channels", {}).update(channels_add_de)
    en.setdefault("channels", {}).update(channels_add_en)
    sv.setdefault("channels", {}).update(channels_add_sv)

    # ==================== actors (merge data variants) ====================
    actors_add_de = {
        "data_support": "Support",
        "data_hotline": "Hotline",
        "data_development": "Entwicklung",
        "data_tech": "Technik",
        "data_customer": "Kunde"
    }
    actors_add_en = {
        "data_support": "Support",
        "data_hotline": "Hotline",
        "data_development": "Development",
        "data_tech": "Tech",
        "data_customer": "Customer"
    }
    actors_add_sv = {
        "data_support": "Support",
        "data_hotline": "Hotline",
        "data_development": "Utveckling",
        "data_tech": "Teknik",
        "data_customer": "Kund"
    }
    de.setdefault("actors", {}).update(actors_add_de)
    en.setdefault("actors", {}).update(actors_add_en)
    sv.setdefault("actors", {}).update(actors_add_sv)

    # ==================== validation ====================
    validation_de = {
        "required_field": "Dieses Feld ist erforderlich.",
        "invalid_email": "Ungültige E-Mail-Adresse.",
        "invalid_date": "Ungültiges Datumsformat.",
        "invalid_number": "Ungültiger Zahlenwert.",
        "field_missing": "Pflichtfeld fehlt: {field}"
    }
    validation_en = {
        "required_field": "This field is required.",
        "invalid_email": "Invalid email address.",
        "invalid_date": "Invalid date format.",
        "invalid_number": "Invalid numeric value.",
        "field_missing": "Required field missing: {field}"
    }
    validation_sv = {
        "required_field": "Detta fält är obligatoriskt.",
        "invalid_email": "Ogiltig e-postadress.",
        "invalid_date": "Ogiltigt datumformat.",
        "invalid_number": "Ogiltigt numeriskt värde.",
        "field_missing": "Obligatoriskt fält saknas: {field}"
    }
    de["validation"] = validation_de
    en["validation"] = validation_en
    sv["validation"] = validation_sv

    # ==================== hotkey_actions ====================
    hotkey_actions_de = {
        "new_case": "Neuen Fall anlegen",
        "search": "Suche fokussieren",
        "quick_filter": "Schnellfilter umschalten",
        "switch_view": "Ansicht wechseln",
        "save_case": "Aktuellen Fall speichern",
        "refresh": "Ansicht aktualisieren",
        "help": "Hilfe öffnen",
        "ai_summary": "KI-Zusammenfassung",
        "email_draft": "E-Mail-Entwurf öffnen"
    }
    hotkey_actions_en = {
        "new_case": "Create new case",
        "search": "Focus search",
        "quick_filter": "Toggle quick filter",
        "switch_view": "Switch view",
        "save_case": "Save current case",
        "refresh": "Refresh view",
        "help": "Open help",
        "ai_summary": "AI summary",
        "email_draft": "Open email draft"
    }
    hotkey_actions_sv = {
        "new_case": "Skapa nytt ärende",
        "search": "Fokusera sökning",
        "quick_filter": "Växla snabbfilter",
        "switch_view": "Byt vy",
        "save_case": "Spara aktuellt ärende",
        "refresh": "Uppdatera vy",
        "help": "Öppna hjälp",
        "ai_summary": "AI-sammanfattning",
        "email_draft": "Öppna e-postutkast"
    }
    de["hotkey_actions"] = hotkey_actions_de
    en["hotkey_actions"] = hotkey_actions_en
    sv["hotkey_actions"] = hotkey_actions_sv

    # ==================== hotkey_recorder ====================
    hotkey_recorder_de = {
        "title": "⌨ Hotkey aufnehmen",
        "header": "⌨ Tastenkombination drücken",
        "info": "Drücken Sie Ihre Tasten (z.B. Strg+S, Alt+1)...",
        "cancel": "Abbrechen (Esc)"
    }
    hotkey_recorder_en = {
        "title": "⌨ Record Hotkey",
        "header": "⌨ Press Key Combination",
        "info": "Press your keys (e.g. Ctrl+S, Alt+1)...",
        "cancel": "Cancel (Esc)"
    }
    hotkey_recorder_sv = {
        "title": "⌨ Spela in snabbkommando",
        "header": "⌨ Tryck på tangentkombination",
        "info": "Tryck på dina tangenter (t.ex. Ctrl+S, Alt+1)...",
        "cancel": "Avbryt (Esc)"
    }
    de["hotkey_recorder"] = hotkey_recorder_de
    en["hotkey_recorder"] = hotkey_recorder_en
    sv["hotkey_recorder"] = hotkey_recorder_sv

    # ==================== ai_constants ====================
    ai_constants_de = {
        "status_online": "Bereit",
        "status_offline": "Nicht verbunden",
        "status_processing": "Verarbeite...",
        "btn_summarize": "🤖 KI-Zusammenfassung generieren",
        "btn_solutions": "💡 Lösungsansätze suchen",
        "btn_draft_reply": "✉ Antwort-Entwurf erstellen",
        "btn_to_timeline": "📌 In Fall-Zeitleiste einfügen",
        "btn_copy": "📋 In Zwischenablage kopieren",
        "btn_regenerate_summary": "🔄 Zusammenfassung neu generieren",
        "btn_retry_solutions": "🔄 Lösungssuche erneut ausführen",
        "btn_regenerate_reply": "🔄 Antwort-Entwurf generieren",
        "disabled_warning": "⚠ KI global deaktiviert (Schalter oben rechts auf OFF). Buttons deaktiviert.",
        "summary_copied": "✓ Zusammenfassung in Zwischenablage kopiert.",
        "summary_saved_timeline": "✓ KI-Zusammenfassung als Zeitleisten-Eintrag gespeichert.",
        "solutions_header": "💡 Automatisch ermittelte Lösungsschritte & Wiki-Referenzen:",
        "btn_open_email": "✉ In E-Mail-Entwurf öffnen",
        "checking_status": "Prüfe Status...",
        "ai_processing": "🤖 KI verarbeitet Anfrage...",
        "please_wait": "Bitte einen Moment gedulden — Modell generiert Antwort"
    }
    ai_constants_en = {
        "status_online": "Ready",
        "status_offline": "Not connected",
        "status_processing": "Processing...",
        "btn_summarize": "🤖 Generate AI Summary",
        "btn_solutions": "💡 Search Solutions",
        "btn_draft_reply": "✉ Create Reply Draft",
        "btn_to_timeline": "📌 Insert into Case Timeline",
        "btn_copy": "📋 Copy to Clipboard",
        "btn_regenerate_summary": "🔄 Regenerate Summary",
        "btn_retry_solutions": "🔄 Retry Solution Search",
        "btn_regenerate_reply": "🔄 Generate Reply Draft",
        "disabled_warning": "⚠ AI globally disabled (switch top right is OFF). Buttons disabled.",
        "summary_copied": "✓ Summary copied to clipboard.",
        "summary_saved_timeline": "✓ AI summary saved as timeline entry.",
        "solutions_header": "💡 Automatically identified solution steps & wiki references:",
        "btn_open_email": "✉ Open in Email Draft",
        "checking_status": "Checking status...",
        "ai_processing": "🤖 AI is processing request...",
        "please_wait": "Please wait a moment — model is generating response"
    }
    ai_constants_sv = {
        "status_online": "Redo",
        "status_offline": "Inte ansluten",
        "status_processing": "Bearbetar...",
        "btn_summarize": "🤖 Generera AI-sammanfattning",
        "btn_solutions": "💡 Sök lösningar",
        "btn_draft_reply": "✉ Skapa svarsutkast",
        "btn_to_timeline": "📌 Infoga i ärendetidslinje",
        "btn_copy": "📋 Kopiera till urklipp",
        "btn_regenerate_summary": "🔄 Generera om sammanfattning",
        "btn_retry_solutions": "🔄 Försök igen med lösningssökning",
        "btn_regenerate_reply": "🔄 Generera svarsutkast",
        "disabled_warning": "⚠ AI globalt inaktiverad (brytare uppe till höger är AV). Knappar inaktiverade.",
        "summary_copied": "✓ Sammanfattning kopierad till urklipp.",
        "summary_saved_timeline": "✓ AI-sammanfattning sparad som tidslinjepost.",
        "solutions_header": "💡 Automatiskt identifierade lösningssteg & wiki-referenser:",
        "btn_open_email": "✉ Öppna i e-postutkast",
        "checking_status": "Kontrollerar status...",
        "ai_processing": "🤖 AI bearbetar förfrågan...",
        "please_wait": "Vänligen vänta ett ögonblick — modellen genererar svar"
    }
    de["ai_constants"] = ai_constants_de
    en["ai_constants"] = ai_constants_en
    sv["ai_constants"] = ai_constants_sv

    # ==================== datetime ====================
    datetime_de = {
        "today": "heute",
        "tomorrow": "morgen",
        "yesterday": "gestern",
        "in_days": "in {diff_days} Tagen",
        "days_ago": "vor {diff_days} Tagen",
        "in_hours": "in {diff_hours} Stunden",
        "hours_ago": "vor {diff_hours} Stunden",
        "in_minutes": "in {diff_minutes} Minuten",
        "minutes_ago": "vor {diff_minutes} Minuten",
        "just_now": "gerade eben",
        "o_clock": "Uhr"
    }
    datetime_en = {
        "today": "today",
        "tomorrow": "tomorrow",
        "yesterday": "yesterday",
        "in_days": "in {diff_days} days",
        "days_ago": "{diff_days} days ago",
        "in_hours": "in {diff_hours} hours",
        "hours_ago": "{diff_hours} hours ago",
        "in_minutes": "in {diff_minutes} minutes",
        "minutes_ago": "{diff_minutes} minutes ago",
        "just_now": "just now",
        "o_clock": ""
    }
    datetime_sv = {
        "today": "idag",
        "tomorrow": "imorgon",
        "yesterday": "igår",
        "in_days": "om {diff_days} dagar",
        "days_ago": "för {diff_days} dagar sedan",
        "in_hours": "om {diff_hours} timmar",
        "hours_ago": "för {diff_hours} timmar sedan",
        "in_minutes": "om {diff_minutes} minuter",
        "minutes_ago": "för {diff_minutes} minuter sedan",
        "just_now": "just nu",
        "o_clock": "kl."
    }
    de["datetime"] = datetime_de
    en["datetime"] = datetime_en
    sv["datetime"] = datetime_sv

    # ==================== customer_form ====================
    customer_form_de = {
        "sort_name_az": "Name (A-Z)",
        "sort_name_za": "Name (Z-A)",
        "sort_id": "Praxisnummer / ID",
        "sort_contact_asc": "Zeit seit letztem Kontakt ↑",
        "sort_contact_desc": "Zeit seit letztem Kontakt ↓",
        "btn_sort_asc": "↑ Aufst.",
        "btn_sort_desc": "↓ Abst.",
        "ph_id": "CUST-...",
        "ph_name": "z.B. Hausarztpraxis Dr. Med. Weber",
        "ph_alt_name": "z.B. Ehem. Praxis Dr. Alt",
        "ph_salutation": "Frau / Herr / Dr.",
        "ph_first_name": "Vorname...",
        "ph_last_name": "Nachname...",
        "ph_street": "z.B. Hauptstr. 10",
        "ph_zip": "12345",
        "ph_city": "Ort...",
        "ph_phone": "0711-...",
        "ph_ext": "Durchwahl...",
        "ph_phone_private": "Privat...",
        "ph_phone_2": "Zweitnr....",
        "ph_phone_3": "Drittnr....",
        "ph_mobile": "0171-...",
        "ph_mobile_private": "Mobil privat...",
        "ph_email_2": "zweit-email@praxis.de",
        "ph_email_3": "dritt-email@praxis.de",
        "ph_website": "https://praxis-beispiel.de",
        "btn_open_url": "🔗 Öffnen",
        "ph_vm_nr": "104",
        "ph_dsc": "DSC...",
        "ph_dscneu": "DSCNEU...",
        "ph_notes": "z.B. Erreichbarkeit, Wünsche...",
        "vip_checkbox": "⭐ VIP-Kunde (erhöht den Dringlichkeits-Score um +30)",
        "btn_add_contact": "+ Kontakt hinzufügen",
        "lbl_alt_name": "Praxisname (Alt):",
        "lbl_salutation": "Anrede:",
        "lbl_first_name": "Vorname:",
        "lbl_last_name": "Nachname:",
        "lbl_street": "🏠 Straße & Hausnr.:",
        "lbl_zip": "PLZ:",
        "lbl_city": "Ort:",
        "lbl_phone_section": "📞 Telefonnummern (Cobra Export)",
        "lbl_phone_main": "Telefon Hauptnr.:",
        "lbl_phone_direct": "Telefon direkt:",
        "lbl_phone_private": "Telefon privat:",
        "lbl_phone_2": "Telefon 2:",
        "lbl_phone_3": "Telefon 3:",
        "lbl_mobile": "Mobil:",
        "lbl_mobile_private": "Mobil privat:",
        "lbl_email_2": "✉ E-Mail 2:",
        "lbl_email_3": "✉ E-Mail 3:",
        "lbl_website": "🌐 Webseite:",
        "lbl_vm_nr": "🖥 VM-Nr.:",
        "lbl_instance_nr": "🔢 Instanz-Nr.:",
        "lbl_dsc": "🏷 DSC:",
        "lbl_dscneu": "🏷 DSCNEU:",
        "lbl_more_contacts": "👥 Weitere Ansprechpartner (1 Name pro Zeile):",
        "lbl_general_notes": "📝 Allgemeine Notizen:",
        "lbl_ai_rules": "⚡ Praxisspezifische KI-Regeln (haben VORRANG vor Basis-Regeln):",
        "lbl_ai_rules_hint": "1 Regel pro Zeile (z. B. 'Duzen erwünscht (Herr Schmidt)', 'Betreff mit [SCHMIDT] beginnen')",
        "lbl_contacts_header": "👥 Ansprechpartner & Kontakte",
        "lbl_master_data": "🏥 Stammdaten & Praxisinformationen",
        "lbl_tech_details": "⚙ Technische Details & PVS"
    }
    customer_form_en = {
        "sort_name_az": "Name (A-Z)",
        "sort_name_za": "Name (Z-A)",
        "sort_id": "Practice Number / ID",
        "sort_contact_asc": "Time since last contact ↑",
        "sort_contact_desc": "Time since last contact ↓",
        "btn_sort_asc": "↑ Asc.",
        "btn_sort_desc": "↓ Desc.",
        "ph_id": "CUST-...",
        "ph_name": "e.g. Family Practice Dr. Weber",
        "ph_alt_name": "e.g. Former Practice Dr. Alt",
        "ph_salutation": "Ms. / Mr. / Dr.",
        "ph_first_name": "First name...",
        "ph_last_name": "Last name...",
        "ph_street": "e.g. Main St. 10",
        "ph_zip": "12345",
        "ph_city": "City...",
        "ph_phone": "0711-...",
        "ph_ext": "Extension...",
        "ph_phone_private": "Private...",
        "ph_phone_2": "Secondary...",
        "ph_phone_3": "Third nr....",
        "ph_mobile": "0171-...",
        "ph_mobile_private": "Private mobile...",
        "ph_email_2": "second-email@practice.com",
        "ph_email_3": "third-email@practice.com",
        "ph_website": "https://practice-example.com",
        "btn_open_url": "🔗 Open",
        "ph_vm_nr": "104",
        "ph_dsc": "DSC...",
        "ph_dscneu": "DSCNEU...",
        "ph_notes": "e.g. Availability, preferences...",
        "vip_checkbox": "⭐ VIP Customer (increases urgency score by +30)",
        "btn_add_contact": "+ Add Contact",
        "lbl_alt_name": "Practice name (Old):",
        "lbl_salutation": "Salutation:",
        "lbl_first_name": "First name:",
        "lbl_last_name": "Last name:",
        "lbl_street": "🏠 Street & Number:",
        "lbl_zip": "ZIP:",
        "lbl_city": "City:",
        "lbl_phone_section": "📞 Phone Numbers (Cobra Export)",
        "lbl_phone_main": "Main phone:",
        "lbl_phone_direct": "Direct phone:",
        "lbl_phone_private": "Private phone:",
        "lbl_phone_2": "Phone 2:",
        "lbl_phone_3": "Phone 3:",
        "lbl_mobile": "Mobile:",
        "lbl_mobile_private": "Private mobile:",
        "lbl_email_2": "✉ Email 2:",
        "lbl_email_3": "✉ Email 3:",
        "lbl_website": "🌐 Website:",
        "lbl_vm_nr": "🖥 VM No.:",
        "lbl_instance_nr": "🔢 Instance No.:",
        "lbl_dsc": "🏷 DSC:",
        "lbl_dscneu": "🏷 DSCNEU:",
        "lbl_more_contacts": "👥 Additional contacts (1 name per line):",
        "lbl_general_notes": "📝 General Notes:",
        "lbl_ai_rules": "⚡ Practice-specific AI rules (PREVAIL over base rules):",
        "lbl_ai_rules_hint": "1 rule per line (e.g. 'Use first name (Mr. Schmidt)', 'Start subject with [SCHMIDT]')",
        "lbl_contacts_header": "👥 Contacts & Persons",
        "lbl_master_data": "🏥 Master Data & Practice Information",
        "lbl_tech_details": "⚙ Technical Details & PMS"
    }
    customer_form_sv = {
        "sort_name_az": "Namn (A-Ö)",
        "sort_name_za": "Namn (Ö-A)",
        "sort_id": "Mottagningsnummer / ID",
        "sort_contact_asc": "Tid sedan senaste kontakt ↑",
        "sort_contact_desc": "Tid sedan senaste kontakt ↓",
        "btn_sort_asc": "↑ Stig.",
        "btn_sort_desc": "↓ Fall.",
        "ph_id": "CUST-...",
        "ph_name": "t.ex. Vårdcentral Dr. Weber",
        "ph_alt_name": "t.ex. Fd. Mottagning Dr. Alt",
        "ph_salutation": "Fru / Herr / Dr.",
        "ph_first_name": "Förnamn...",
        "ph_last_name": "Efternamn...",
        "ph_street": "t.ex. Storgatan 10",
        "ph_zip": "12345",
        "ph_city": "Ort...",
        "ph_phone": "0711-...",
        "ph_ext": "Anknytning...",
        "ph_phone_private": "Privat...",
        "ph_phone_2": "Sekundärt nr...",
        "ph_phone_3": "Tredje nr...",
        "ph_mobile": "0171-...",
        "ph_mobile_private": "Privat mobil...",
        "ph_email_2": "andra-epost@mottagning.se",
        "ph_email_3": "tredje-epost@mottagning.se",
        "ph_website": "https://mottagning-exempel.se",
        "btn_open_url": "🔗 Öppna",
        "ph_vm_nr": "104",
        "ph_dsc": "DSC...",
        "ph_dscneu": "DSCNEU...",
        "ph_notes": "t.ex. Tillgänglighet, önskemål...",
        "vip_checkbox": "⭐ VIP-kund (ökar brådskande-poäng med +30)",
        "btn_add_contact": "+ Lägg till kontakt",
        "lbl_alt_name": "Mottagningsnamn (Gammalt):",
        "lbl_salutation": "Hälsningsfras:",
        "lbl_first_name": "Förnamn:",
        "lbl_last_name": "Efternamn:",
        "lbl_street": "🏠 Gata & nummer:",
        "lbl_zip": "Postnummer:",
        "lbl_city": "Ort:",
        "lbl_phone_section": "📞 Telefonnummer (Cobra-export)",
        "lbl_phone_main": "Huvudtelefon:",
        "lbl_phone_direct": "Direkttelefon:",
        "lbl_phone_private": "Privat telefon:",
        "lbl_phone_2": "Telefon 2:",
        "lbl_phone_3": "Telefon 3:",
        "lbl_mobile": "Mobil:",
        "lbl_mobile_private": "Privat mobil:",
        "lbl_email_2": "✉ E-post 2:",
        "lbl_email_3": "✉ E-post 3:",
        "lbl_website": "🌐 Webbplats:",
        "lbl_vm_nr": "🖥 VM-nr:",
        "lbl_instance_nr": "🔢 Instansnr:",
        "lbl_dsc": "🏷 DSC:",
        "lbl_dscneu": "🏷 DSCNEU:",
        "lbl_more_contacts": "👥 Ytterligare kontakter (1 namn per rad):",
        "lbl_general_notes": "📝 Allmänna anteckningar:",
        "lbl_ai_rules": "⚡ Mottagningsspecifika AI-regler (har FÖRETRÄDE framför basregler):",
        "lbl_ai_rules_hint": "1 regel per rad (t.ex. 'Ni-tilltal ej önskat', 'Börja ämne med [SCHMIDT]')",
        "lbl_contacts_header": "👥 Kontakter & personer",
        "lbl_master_data": "🏥 Stamdata & mottagningsinformation",
        "lbl_tech_details": "⚙ Tekniska detaljer & journalsystem"
    }
    de["customer_form"] = customer_form_de
    en["customer_form"] = customer_form_en
    sv["customer_form"] = customer_form_sv

    # ==================== cobra_import (merge updates) ====================
    cobra_import_add_de = {
        "dialog_title": "Cobra CRM Export-Datei auswählen",
        "header_title": "🐍 Cobra CRM Praxen-Import Assistent",
        "header_desc": "Importieren Sie Praxen aus Cobra CRM Exporte-Dateien (.csv, .txt, .json).",
        "step1_file": "1. Cobra Export-Datei auswählen:",
        "btn_browse": "📁 Durchsuchen...",
        "step2_mapping": "2. Cobra Spaltenzuordnung (Feld-Mapper):",
        "step3_conflicts": "3. Konfliktbehandlung für bestehende Praxen:",
        "mode_update": "Bestehende Praxen aktualisieren (Update)",
        "mode_skip": "Bestehende überspringen (Skip)",
        "mode_all_new": "Alle als neu anlegen",
        "select_file_prompt": "Bitte wählen Sie eine Export-Datei aus.",
        "no_records": "⚠ Keine Datensätze in der Datei gefunden."
    }
    cobra_import_add_en = {
        "dialog_title": "Select Cobra CRM Export File",
        "header_title": "🐍 Cobra CRM Practice Import Assistant",
        "header_desc": "Import practices from Cobra CRM export files (.csv, .txt, .json).",
        "step1_file": "1. Select Cobra export file:",
        "btn_browse": "📁 Browse...",
        "step2_mapping": "2. Cobra column mapping (Field mapper):",
        "step3_conflicts": "3. Conflict handling for existing practices:",
        "mode_update": "Update existing practices (Update)",
        "mode_skip": "Skip existing practices (Skip)",
        "mode_all_new": "Create all as new",
        "select_file_prompt": "Please select an export file.",
        "no_records": "⚠ No records found in file."
    }
    cobra_import_add_sv = {
        "dialog_title": "Välj Cobra CRM-exportfil",
        "header_title": "🐍 Cobra CRM importassistent för mottagningar",
        "header_desc": "Importera mottagningar från Cobra CRM-exportfiler (.csv, .txt, .json).",
        "step1_file": "1. Välj Cobra-exportfil:",
        "btn_browse": "📁 Bläddra...",
        "step2_mapping": "2. Cobra kolumnmappning (Fältmappning):",
        "step3_conflicts": "3. Konflikthantering för befintliga mottagningar:",
        "mode_update": "Uppdatera befintliga mottagningar (Uppdatering)",
        "mode_skip": "Hoppa över befintliga (Hoppa över)",
        "mode_all_new": "Skapa alla som nya",
        "select_file_prompt": "Välj en exportfil.",
        "no_records": "⚠ Inga poster hittades i filen."
    }
    de.setdefault("cobra_import", {}).update(cobra_import_add_de)
    en.setdefault("cobra_import", {}).update(cobra_import_add_en)
    sv.setdefault("cobra_import", {}).update(cobra_import_add_sv)

    # ==================== case_print ====================
    case_print_de = {
        "dialog_title": "🖨 Fall-Akte Druck- & HTML Export: {case_id}",
        "elements_prompt": "Wählen Sie aus, welche Elemente im Druckbericht erscheinen sollen:",
        "chk_practice_data": "Praxis & Kundendaten",
        "chk_form_fields": "Formularfelder",
        "chk_images": "Bilder & Anhänge am Ende",
        "lbl_timeline": "Zeitleiste / Notizen-Verlauf (einzelne Einträge abwählen):",
        "btn_html_report": "🌐 HTML-Bericht",
        "btn_save": "💾 Speichern...",
        "no_notes": "Keine Notizen in der Zeitleiste.",
        "save_dialog_title": "Fallbericht speichern"
    }
    case_print_en = {
        "dialog_title": "🖨 Case File Print & HTML Export: {case_id}",
        "elements_prompt": "Select which elements should appear in the print report:",
        "chk_practice_data": "Practice & Customer Data",
        "chk_form_fields": "Form Fields",
        "chk_images": "Images & Attachments at end",
        "lbl_timeline": "Timeline / Notes history (deselect individual entries):",
        "btn_html_report": "🌐 HTML Report",
        "btn_save": "💾 Save...",
        "no_notes": "No notes in timeline.",
        "save_dialog_title": "Save Case Report"
    }
    case_print_sv = {
        "dialog_title": "🖨 Ärendeakt utskrift & HTML-export: {case_id}",
        "elements_prompt": "Välj vilka element som ska visas i utskriftsrapporten:",
        "chk_practice_data": "Mottagnings- & kunddata",
        "chk_form_fields": "Formulärfält",
        "chk_images": "Bilder & bilagor i slutet",
        "lbl_timeline": "Tidslinje / Anteckningshistorik (avmarkera enskilda poster):",
        "btn_html_report": "🌐 HTML-rapport",
        "btn_save": "💾 Spara...",
        "no_notes": "Inga anteckningar i tidslinjen.",
        "save_dialog_title": "Spara ärenderapport"
    }
    de["case_print"] = case_print_de
    en["case_print"] = case_print_en
    sv["case_print"] = case_print_sv

    # ==================== demo_cases (additional c6 - c10) ====================
    demo_cases_add_de = {
        "c6_title": "Alte Abrechnung Q1 gelöst",
        "c7_title": "Uralter Fall aus dem Vormonat",
        "c8_title": "Frische Nachforderung ohne DB-Dump",
        "c9_title": "Kundenwunsch: Schnell-Button für eRezept-Export",
        "c10_title": "Kartenleser-Treiber nach Windows-Update getrennt"
    }
    demo_cases_add_en = {
        "c6_title": "Old Q1 billing resolved",
        "c7_title": "Ancient case from previous month",
        "c8_title": "Fresh subsequent claim without DB dump",
        "c9_title": "Feature request: Quick button for ePrescription export",
        "c10_title": "Card reader driver disconnected after Windows update"
    }
    demo_cases_add_sv = {
        "c6_title": "Gammal Q1-fakturering löst",
        "c7_title": "Gammalt ärende från föregående månad",
        "c8_title": "Färsk efterkravsansökan utan DB-dump",
        "c9_title": "Önskemål: Snabbknapp för e-recept export",
        "c10_title": "Kortläsardrivrutin frånkopplad efter Windows-uppdatering"
    }
    de.setdefault("demo_cases", {}).update(demo_cases_add_de)
    en.setdefault("demo_cases", {}).update(demo_cases_add_en)
    sv.setdefault("demo_cases", {}).update(demo_cases_add_sv)

    # ==================== snippets ====================
    snippets_de = {
        "s1_title": "📸 Rückfrage: Screenshots & Uhrzeit anfordern",
        "s2_title": "🛠 Ersthilfe: PVS & Support-Dienst neustarten",
        "s3_title": "🔍 DB-Check: SQL Fehler-Log Abfrage",
        "s4_title": "✅ Fallabschluss & Dankeschön",
        "s5_title": "🩺 Telematikinfrastruktur: Konnektor & SMC-B Prüfung",
        "s6_title": "📑 Abrechnung: Zuzahlungs- & ESOL-Korrektur weitergeleitet",
        "s7_title": "💾 Backup-Anforderung für Fehleranalyse",
        "s8_title": "🔄 Quartalsupdate Hinweis & Vorbereitung"
    }
    snippets_en = {
        "s1_title": "📸 Follow-up: Request screenshots & timestamp",
        "s2_title": "🛠 First Aid: Restart PMS & Support Service",
        "s3_title": "🔍 DB Check: Query SQL error log",
        "s4_title": "✅ Case Closure & Thank You",
        "s5_title": "🩺 Telematics Infrastructure: Connector & SMC-B Check",
        "s6_title": "📑 Billing: Copayment & ESOL correction forwarded",
        "s7_title": "💾 Backup Request for Error Analysis",
        "s8_title": "🔄 Quarterly Update Notice & Preparation"
    }
    snippets_sv = {
        "s1_title": "📸 Uppföljning: Begär skärmbilder & klockslag",
        "s2_title": "🛠 Första hjälpen: Starta om journalsystem & supporttjänst",
        "s3_title": "🔍 DB-kontroll: Fråga i SQL-fellogg",
        "s4_title": "✅ Ärendeavslut & tack",
        "s5_title": "🩺 Telematikinfrastruktur: Kontroll av anslutning & SMC-B",
        "s6_title": "📑 Fakturering: Egenavgifts- & ESOL-korrigering vidarebefordrad",
        "s7_title": "💾 Begäran om säkerhetskopia för felanalys",
        "s8_title": "🔄 Kvartalsuppdatering information & förberedelse"
    }
    de["snippets"] = snippets_de
    en["snippets"] = snippets_en
    sv["snippets"] = snippets_sv

    # ==================== default_tags ====================
    default_tags_de = {
        "abrechnung": "Abrechnung",
        "datenbank": "Datenbank",
        "schnittstelle": "Schnittstelle",
        "performance": "Performance",
        "rezeptdruck": "Rezeptdruck",
        "telematik": "Telematik",
        "kartenleser": "Kartenleser",
        "update": "Update",
        "absturz": "Absturz",
        "netzwerk": "Netzwerk",
        "ti_konnektor": "TI-Konnektor",
        "kv_abrechnung": "KV-Abrechnung",
        "terminplaner": "Terminplaner",
        "patientenakte": "Patientenakte",
        "formulardruck": "Formulardruck",
        "zuzahlung": "Zuzahlung",
        "labordaten": "Labordaten",
        "stammdaten": "Stammdaten",
        "backup": "Backup",
        "installation": "Installation",
        "e_rezept": "e-Rezept"
    }
    default_tags_en = {
        "abrechnung": "Billing",
        "datenbank": "Database",
        "schnittstelle": "Interface",
        "performance": "Performance",
        "rezeptdruck": "Prescription Print",
        "telematik": "Telematics",
        "kartenleser": "Card Reader",
        "update": "Update",
        "absturz": "Crash",
        "netzwerk": "Network",
        "ti_konnektor": "TI Connector",
        "kv_abrechnung": "KV Billing",
        "terminplaner": "Scheduler",
        "patientenakte": "Patient Record",
        "formulardruck": "Form Printing",
        "zuzahlung": "Copayment",
        "labordaten": "Lab Data",
        "stammdaten": "Master Data",
        "backup": "Backup",
        "installation": "Installation",
        "e_rezept": "e-Prescription"
    }
    default_tags_sv = {
        "abrechnung": "Fakturering",
        "datenbank": "Databas",
        "schnittstelle": "Gränssnitt",
        "performance": "Prestanda",
        "rezeptdruck": "Receptutskrift",
        "telematik": "Telematik",
        "kartenleser": "Kortläsare",
        "update": "Uppdatering",
        "absturz": "Krasch",
        "netzwerk": "Nätverk",
        "ti_konnektor": "TI-anslutning",
        "kv_abrechnung": "KV-fakturering",
        "terminplaner": "Tidbok",
        "patientenakte": "Patientjournal",
        "formulardruck": "Formulärutskrift",
        "zuzahlung": "Egenavgift",
        "labordaten": "Laboratoriedata",
        "stammdaten": "Stamdata",
        "backup": "Säkerhetskopia",
        "installation": "Installation",
        "e_rezept": "e-Recept"
    }
    de["default_tags"] = default_tags_de
    en["default_tags"] = default_tags_en
    sv["default_tags"] = default_tags_sv

    # ==================== calendar_export (merge updates) ====================
    cal_export_add_de = {
        "title_save_ics": "iCalendar-Datei speichern",
        "lbl_desc_note": "Kalender-Beschreibung / Notiz:"
    }
    cal_export_add_en = {
        "title_save_ics": "Save iCalendar File",
        "lbl_desc_note": "Calendar description / Note:"
    }
    cal_export_add_sv = {
        "title_save_ics": "Spara iCalendar-fil",
        "lbl_desc_note": "Kalenderbeskrivning / Anteckning:"
    }
    de.setdefault("calendar_export", {}).update(cal_export_add_de)
    en.setdefault("calendar_export", {}).update(cal_export_add_en)
    sv.setdefault("calendar_export", {}).update(cal_export_add_sv)

    # ==================== help_content expansion for Swedish ====================
    # Full Swedish translations for all 25 articles with 100% fidelity to DE / EN structure
    sv_help_content = {
        "basics": {
            "title": "🚀 Kom igång & ärendehantering",
            "category": "Arbetsflöde",
            "content": "### Grundläggande om Support-Cockpit\n\nSupport-Cockpit möjliggör effektiv registrering, uppföljning och hantering av kundförfrågningar och supportärenden.\n\n#### Snabbstart:\n1. **Skapa nytt ärende:** Klicka på `+ Nytt ärende (F1)` eller tryck på **F1**.\n2. **Välj mottagning:** Välj en registrerad mottagning från listan.\n3. **Välj formulärschema:** Välj lämpligt formulär för ärendet (t.ex. fakturering, installation).\n4. **Prioritet & förfallotid:** Ange vid behov en återuppringningsfrist eller uppföljning.\n\n#### Statusarbetsflöde:\n- **Nytt (NEW):** Nyskapat ärende utan påbörjad handläggning.\n- **Åtgärd krävs (ACTION_REQUIRED):** Ärendet kräver aktiv åtgärd från supporten.\n- **Väntar (WAITING):** Väntar på återkoppling från kund eller utvecklare.\n- **Pågående (IN_PROGRESS):** Aktiv analys eller problemlösning pågår.\n- **Klart (DONE):** Ärendet har slutförts framgångsrikt."
        },
        "ui_customization": {
            "title": "🎨 Vyer & UI-anpassning",
            "category": "Gränssnitt",
            "content": "### Anpassning av användargränssnittet\n\nCockpiten erbjuder olika vyer och layouter för att anpassa arbetsflödet optimalt efter dina behov.\n\n#### Tillgängliga vyer:\n- **Cockpit-vy:** Kompakt översikt med ärendelista, snabbfilter, detaljer och formulär.\n- **Kanban-tavla:** Visuell kolumnvy sorterad efter status (`Support`, `Utveckling`, `Uppföljning`, `Klart`).\n- **Tabellvy:** Detaljerad tabellöversikt med flexibel sortering och kolumnkonfiguration.\n- **Statistikpanel:** KPI:er, handläggningstider, prioritetsfördelning och prestandamått.\n\n#### Spara kolumnbredder & layout:\n- Kolumnbredder i tabeller kan justeras genom att dra i skiljelinjerna.\n- Under **Inställningar → Vy** kan du återställa kolumnbredder eller definiera layoutpreferenser.\n- Mörkt och ljust läge (Dark / Light Theme) stöds automatiskt eller manuellt."
        },
        "praxis": {
            "title": "🏥 Mottagnings- & kundhantering",
            "category": "Stamdata",
            "content": "### Hantering av mottagningar och kontakter\n\nHantera stamdata, kontaktpersoner, tillgänglighet och mottagningsspecifika AI-regler centralt.\n\n#### Funktioner:\n- **Skapa & redigera mottagning:** Registrera kundnummer (ID), mottagningsnamn, adress, telefonnummer och anteckningar.\n- **VIP-status:** Markera viktiga mottagningar som VIP (+30 poäng i brådskandepoäng).\n- **Kontaktpersoner:** Spara flera personer med anknytning, e-post och tillgänglighetstider.\n- **Mottagningsspecifika AI-regler:** Individuella instruktioner för AI-textgenerering (t.ex. tilltalssätt, specifika gränssnittsanvisningar).\n- **Cobra CRM-import:** Importera mottagningar automatiskt från Cobra CRM-exportfiler (.csv, .json)."
        },
        "scoring": {
            "title": "⚡ Brådskande- & prioritetspoäng",
            "category": "Arbetsflöde",
            "content": "### Intelligent ärendeprioritering\n\nPrioritetspoängen beräknar automatiskt en brådskandebedömning för varje öppet ärende.\n\n#### Bedömningskriterier:\n- **Förfallen tidsfrist:** +50 poäng vid överskriden återuppringningsfrist.\n- **VIP-mottagning:** +30 poäng i bonus för VIP-markerade kunder.\n- **Lång liggtid:** Automatisk poängökning för ärenden som inte bearbetats på länge.\n- **Kritiska nyckelord:** +20 poäng vid termer som *akut*, *systemstopp*, *blockerad anslutning*.\n\n#### Färgkodning:\n- 🔴 **Röd (≥ 70 poäng):** Högsta prioritet — omedelbar handläggning krävs.\n- 🟡 **Gul (40–69 poäng):** Medelhög prioritet — granska inom kort.\n- 🟢 **Grön (< 40 poäng):** Normal handläggning i turordning."
        },
        "schemas": {
            "title": "📋 Formulärbyggare (Scheman)",
            "category": "Formulär",
            "content": "### Dynamiska formulärscheman\n\nSkapa och hantera strukturerade inmatningsmasker för olika supportämnen.\n\n#### Schemafunktioner:\n- **Fälttyper:** Textrad, textområde, nummer, datum, rullgardinsmeny, kryssruta, filbilaga, upprepningsbara underformulär.\n- **Villkorsstyrd logik (V2):** Visa eller dölj fält dynamiskt baserat på värden i andra fält.\n- **Obligatoriska fält:** Definiera obligatoriska inmatningar före ärendeavslut eller export.\n- **Schemakonvertering:** Byt formulär för ett befintligt ärende vid behov via menyn `Konvertera schema`."
        },
        "export": {
            "title": "📤 Export & urklipp",
            "category": "Export",
            "content": "### Ärendeexport & dokumentation\n\nExportera ärendedata, formulärinnehåll och historikloggar till strukturerade format.\n\n#### Exportalternativ:\n- **Text / Markdown:** Kopiera formaterad text till urklipp för ärendehanteringssystem (t.ex. GitLab, Jira, Redmine).\n- **Filexport:** Spara som `.txt`, `.md` eller `.json`.\n- **E-postutkast:** Överför till Outlook eller standard e-postklient med förkonfigurerad mall.\n- **Tvingad export:** Exportera trots saknade obligatoriska fält med `[SAKNAS: ...]` platshållare."
        },
        "wiki": {
            "title": "📖 BookStack offline-wiki",
            "category": "Kunskapsbas",
            "content": "### Integrerad offline-kunskapsbas\n\nFå tillgång till dokumentation, felloggar och instruktioner direkt från cockpiten — även utan aktiv internetanslutning.\n\n#### Funktioner:\n- **Lokalt cacheminne:** Fullständig synkronisering med BookStack via API-token.\n- **Snabbsökning:** Sök i artiklar efter nyckelord, felkoder (t.ex. `ERR_DB_902`) eller modulnamn.\n- **Länkning:** Direkt överföring av wiki-lösningsreferenser till ärendeanteckningar eller e-postutkast."
        },
        "p2p": {
            "title": "🔄 Peer-to-Peer kollegesynkronisering",
            "category": "Synkronisering",
            "content": "### Decentraliserad datasynkronisering mellan kollegor\n\nSynkronisera ärenden och anteckningar direkt i det lokala nätverket (LAN/utdelad mapp) med kollegor utan central server.\n\n#### Process:\n1. **Konfigurera kollegemapp:** Ange den gemensamma nätverkskatalogen i inställningarna.\n2. **Öppna synkronisering:** Öppna jämförelsedialogen via menyn `P2P-synk`.\n3. **Kontrollera skillnader:** Visa avvikande eller nya ärenden från kollegor.\n4. **Tillämpa:** Importera valda ärenden till den egna databasen med ett klick."
        },
        "shortcuts": {
            "title": "⌨ Kortkommandon & snabbtangenter",
            "category": "Produktivitet",
            "content": "### Globala kortkommandon\n\nAnvänd snabbkommandon för blixtsnabb navigering i det dagliga arbetet.\n\n| Tangentkombination | Åtgärd |\n| :--- | :--- |\n| **F1** | Skapa nytt ärende |\n| **F2** | Fokusera sökning / snabbfilter |\n| **F5** | Uppdatera vy |\n| **Ctrl + S** | Spara aktuellt ärende |\n| **Ctrl + F** | Öppna fulltextsökning |\n| **Ctrl + 1 .. 4** | Växla mellan vyer (Cockpit, Tavla, Tabell, Statistik) |\n| **Ctrl + E** | Öppna e-postutkast för aktuellt ärende |\n| **Ctrl + V** | Klistra in bild från urklipp som ärendebilaga |\n| **Esc** | Stäng dialog / avbryt inmatning |\n\n*Obs: Snabbkommandon kan anpassas individuellt under **Inställningar → Snabbkommandon**.*"
        },
        "storage_paths": {
            "title": "💾 Lagringssökvägar & dataorganisation",
            "category": "Konfiguration",
            "content": "### Lokal datalagring & sökvägshantering\n\nSupport-Cockpit lagrar all applikationsdata lokalt i strukturerade JSON- och filformat.\n\n#### Katalogstruktur:\n- **`data/cases/`:** Enskilda JSON-filer per supportärende (t.ex. `T-2026-0001.json`).\n- **`data/practices.json`:** Registrerade mottagningar och stamdata.\n- **`data/colleagues.json`:** Medarbetarregister och ansvarsområden.\n- **`data/snippets.json`:** Textmallsbibliotek.\n- **`data/question_schemas.json`:** Anpassade formulärscheman.\n- **`data/export_templates.json`:** Jinja2-baserade exportmallar.\n- **`attachments/{case_id}/`:** Tillhörande filbilagor, skärmbilder och loggar per ärende.\n\n#### Sökvägskonfiguration:\nI inställningarna (`Inställningar → Sökvägar & Säkerhetskopiering`) kan målkatalogerna ändras till en nätverksenhet eller en molnsynkroniserad mapp."
        },
        "template_editor": {
            "title": "📄 Jinja2 exportmallsredigerare",
            "category": "Export",
            "content": "### Mallhantering med Jinja2\n\nSkapa dynamiska export- och ärendemallar med Jinja2-syntax.\n\n#### Tillgängliga platshållare & variabler:\n- `{{ case.case_id }}`: Unikt ärende-ID\n- `{{ case.practice_name }}`: Mottagningens namn\n- `{{ case.customer_id }}`: Kundnummer / ID\n- `{{ case.title }}`: Titel / kort beskrivning av ärendet\n- `{{ case.status }}`: Aktuell status\n- `{{ form.field_id }}`: Innehåll i ett specifikt formulärfält\n- `{{ timeline }}`: Formaterad anteckningshistorik\n\n#### Live-förhandsgranskning:\nRedigeraren erbjuder en integrerad live-förhandsgranskning baserad på det för tillfället valda livedata-ärendet."
        },
        "handover_followup": {
            "title": "🤝 Ansvarsöverlämning & uppföljning",
            "category": "Arbetsflöde",
            "content": "### Ärendeöverlämning & uppföljningshantering\n\nSäkerställ att inga förfrågningar tappas bort när kollegor eller specialistavdelningar är involverade.\n\n#### Överlämning (Handover):\n1. Klicka på `🤝 Överlämna`.\n2. Välj ansvarig enhet (`Utveckling`, `Teknik`, `Support`).\n3. Välj kanal (`E-post`, `Telefon`, `GitLab-ärende`, `Personligen`).\n4. Välj eventuellt en specifik kollega från medarbetarlistan.\n5. Ange en överlämningsanteckning (t.ex. ärendenummer).\n6. Händelsen loggas automatiskt i tidslinjen.\n\n#### Uppföljning (Follow-up):\n- Ange ett påminnelsedatum via snabbvalen (`+ 1 tim`, `Idag 16:30`, `Imorgon 08:00`, `+ 1 dag`, `+ 1 vecka`).\n- Förfallna uppföljningar framhävs visuellt i cockpiten och aktiverar systemaviseringar."
        },
        "email_calendar_outlook": {
            "title": "✉ E-post & kalenderintegration (Outlook / .eml / .ics)",
            "category": "Kommunikation",
            "content": "### E-postutkast och kalenderinbjudningar\n\nKommunicera smidigt med mottagningar och kollegor via förberedda e-post- och kalenderfiler.\n\n#### E-postutkast (`Ctrl + E`):\n- Automatisk överföring av mottagare, ämne (med ärende-ID och mottagningsnamn) och hälsningsfras.\n- Infoga textmallar med ett klick.\n- AI-stödd formulering av svarsutkast.\n- Direkt överföring till Microsoft Outlook (via COM-automatisering) eller standard e-postklient (.eml).\n\n#### Kalenderexport (.ics):\n- Skapa iCalendar-filer för återuppringningstider eller underhållsfönster.\n- Kompatibel med Outlook, Google Calendar, Apple Calendar och Thunderbird."
        },
        "case_print_reporting": {
            "title": "🖨 Skriv ut ärendeakt & HTML-rapportering",
            "category": "Export",
            "content": "### Utskrifts- och dokumentexport\n\nGenerera snygga utskriftsrapporter och HTML-akter för arkivering eller överlämning till kund.\n\n#### Funktioner:\n- **Modulärt urval:** Välj exakt vilka element som ska inkluderas i rapporten (stamdata, formulärfält, tidslinjeposter, bilder).\n- **HTML-förhandsgranskning:** Öppnar den färdigformaterade rapporten direkt i standardwebbläsaren för PDF-utskrift.\n- **Fristående fil:** Den genererade HTML-rapporten innehåller alla stilar och inbäddade Base64-bilder och kan skickas fristående."
        },
        "ai_ollama_management": {
            "title": "🤖 Lokal AI-hantering & Google Gemini",
            "category": "AI-assistent",
            "content": "### AI-integration (Ollama & Google Gemini)\n\nAnvänd toppmoderna språkmodeller för automatisk sammanfattning, problemlösning och e-postgenerering.\n\n#### Leverantörer som stöds:\n1. **Ollama (Lokal):** 100% GDPR- och sekretesskompatibel, körs helt på din lokala hårdvara utan dataöverföring till tredje part.\n2. **Google Gemini API (Moln):** Kraftfulla molnmodeller (t.ex. Gemini 1.5 Pro / Flash) för mycket komplexa förfrågningar.\n\n#### Lokal PII-anonymisering:\nNär anonymisering är aktiverad ersätts känsliga data (mottagningsnamn, personnamn, e-post, telefonnummer) med pseudonymer innan de skickas till moln-API:er och återställs vid svar.\n\n#### Modelfile-hantering:\nKonfigurera specifika systemregler och modellparametrar (temperatur, kontextlängd) direkt i cockpiten."
        },
        "stepper_time_picker": {
            "title": "⏰ Datum- & tidsväljare med stegreglage",
            "category": "Gränssnitt",
            "content": "### Bekväm tids- och datumväljare\n\nVälj tidsfrister, skapandetider och uppföljningar med precision via grafiska stegreglage.\n\n#### Funktioner:\n- **Grafisk kalender:** Snabb navigering genom månader och dagar.\n- **Tim- & minutreglage:** Snabb justering i steg om 5, 15 eller 30 minuter.\n- **Relativa snabbval:** Förinställningar som `Idag 11:30`, `Imorgon 08:00`, `+ 1 dag` för maximal effektivitet."
        },
        "internal_cases": {
            "title": "🏢 Interna ärenden & uppgifter",
            "category": "Arbetsflöde",
            "content": "### Interna ärenden utan kundkoppling\n\nRegistrera interna utvecklingsuppgifter, underhållsfönster eller administrativa uppgifter direkt i Support-Cockpit.\n\n#### Egenskaper för interna ärenden:\n- **Ingen obligatorisk kund:** Kundvalsfältet utelämnas eller döljs.\n- **Egna kategorier:** Fjärrunderhåll, datautbyte, dokumentation, buggfix, serverunderhåll.\n- **Tilldelning:** Tilldela till kollegor eller specialistavdelningar på samma sätt som för vanliga supportärenden."
        },
        "cobra_crm_import": {
            "title": "🐍 Cobra CRM importassistent för mottagningar",
            "category": "Stamdata",
            "content": "### Automatiserad import från Cobra CRM\n\nImportera mottagningsregister och kontaktuppgifter från Cobra CRM-exporter (.csv, .txt, .json).\n\n#### Importsteg:\n1. **Välj fil:** Välj exportfil från Cobra CRM.\n2. **Kolumnmappning:** Mappning av fält (mottagningsnamn, kund-ID, postnummer, ort, telefon, VIP-status).\n3. **Konflikthantering:** Välj mellan *Uppdatera befintliga mottagningar*, *Hoppa över befintliga* eller *Skapa alla som nya*."
        },
        "snippets_manager": {
            "title": "📝 Textmallsbibliotek & makron",
            "category": "Produktivitet",
            "content": "### Textmallar & snabbmakron\n\nStandardisera återkommande svar med den centrala textmallshanteringen.\n\n#### Funktioner:\n- **Kategorisering & taggar:** Strukturera mallar efter ämnen (t.ex. fakturering, första hjälpen, TI-kontroll).\n- **Kortkommandon:** Tilldela mallar direkta snabbkommandon (t.ex. `<Ctrl-Alt-1>`).\n- **Platshållare:** Automatisk ersättning av variabler som mottagningsnamn eller kontaktperson."
        },
        "repeatable_sub_forms": {
            "title": "📑 Upprepningsbara underformulär",
            "category": "Formulär",
            "content": "### Tabell- & flervalsinmatningar i formulär\n\nRegistrera listor med likartade dataposter (t.ex. flera arbetsstationer, drabbade datorer eller feltidpunkter) strukturerat inom ett ärende.\n\n#### Funktion:\n- **Kortvy:** Varje post visas som ett överskådligt kort med knappar för att redigera och ta bort.\n- **Dynamiskt tillägg:** Lägg till valfritt antal underposter med ett klick.\n- **Validering:** Obligatoriska fält inom underformulär kontrolleras innan du sparar."
        },
        "analytics_kpi_dashboard": {
            "title": "📊 KPI & statistikpanel",
            "category": "Statistik",
            "content": "### Omfattande supportmått & rapporter\n\nHåll alltid koll på arbetsbelastning, svarstider och ärendefördelning.\n\n#### Inkluderade KPI:er:\n- **Öppna vs. klara ärenden:** Teamets aktuella belastning.\n- **Genomsnittlig handläggningstid:** Tid från registrering till avslut.\n- **Brådskandefördelning:** Uppdelning i kritiska (Röd), medelhöga (Gul) och normala (Grön) ärenden.\n- **Topptaggar & kategorier:** De vanligaste felorsakerna och berörda programmoduler.\n- **Kopiera rapport:** Formaterad sammanfattningsrapport i Markdown för teammöten kopieras till urklipp med ett klick."
        },
        "advanced_search_filters": {
            "title": "🔍 Avancerad sökning & söksyntax",
            "category": "Sökning",
            "content": "### Kraftfulla sökfilter & operatorer\n\nHitta ärenden på några sekunder med den avancerade söksyntaxen.\n\n#### Sökfilter som stöds:\n- **Fulltext:** Enkel textinmatning söker i titel, anteckningar och formulärfält.\n- **`tag:fakturering`:** Filtrerar på specifika taggar.\n- **`status:done`:** Filtrerar på ärendestatus.\n- **`actor:dev`:** Filtrerar på ansvarig specialistavdelning.\n- **`practice:weber`:** Filtrerar på mottagningsnamn eller kund-ID.\n- **`vip:true`:** Visar endast VIP-mottagningar."
        },
        "attachments_and_screenshots": {
            "title": "📎 Filbilagor & skärmbildsarbetsflöde",
            "category": "Dokument",
            "content": "### Hantering av ärendefiler och skärmbilder\n\nSpara skärmdumpar, loggfiler och diagnostikdumpar direkt i ärendemappen.\n\n#### Snabb skärmbildsimport (`Ctrl + V`):\n- Tryck bara **Ctrl + V** i cockpiten för att automatiskt spara en bild från Windows-urklipp som PNG i ärendemappen.\n- Lägg till filer via dra och släpp eller fildialog.\n- Snabb åtkomst till filmappen via knappen `📁 Öppna i Utforskaren`."
        },
        "zip_backup_restore": {
            "title": "📦 Säkerhetskopiering & ZIP-återställning",
            "category": "Säkerhet",
            "content": "### Fullständig säkerhetskopiering (Backup & Restore)\n\nSäkerhetskopiera hela databasen till ett komprimerat ZIP-arkiv med ett klick.\n\n#### Skapa säkerhetskopia:\n- Via menyn `Arkiv → Exportera säkerhetskopia som ZIP`.\n- Säkerhetskopierar alla ärenden, mottagningar, scheman, mallar och filbilagor.\n\n#### Återställning (ZIP-import):\n- Via `Arkiv → Importera säkerhetskopia (ZIP)`.\n- Flexibelt val av målkatalog med automatisk identifiering av `data/` och `attachments/`."
        },
        "email_webhook_integration": {
            "title": "🌐 E-post & IMAP inkorgssynkronisering",
            "category": "Gränssnitt",
            "content": "### Automatisk inkorgssynkronisering\n\nMatcha inkommande e-postmeddelanden från Microsoft Outlook eller ett IMAP-konto automatiskt med befintliga supportärenden.\n\n#### Funktioner:\n- Identifiering av ärende-ID i ämnesraden (t.ex. `[T-2026-0042]`).\n- Automatisk koppling av nya meddelanden till ärendets tidslinje.\n- Skapa nya ärenden direkt från okopplade e-postmeddelanden med ett klick."
        }
    }
    sv["help_content"] = sv_help_content

    # Sort keys recursively in all 3 dicts for consistent structure
    def sort_dict(d):
        res = {}
        for k in sorted(d.keys()):
            v = d[k]
            if isinstance(v, dict):
                res[k] = sort_dict(v)
            else:
                res[k] = v
        return res

    de_sorted = sort_dict(de)
    en_sorted = sort_dict(en)
    sv_sorted = sort_dict(sv)

    # Write out files
    with open('locales/de.json', 'w', encoding='utf-8') as f:
        json.dump(de_sorted, f, ensure_ascii=False, indent=2)
    with open('locales/en.json', 'w', encoding='utf-8') as f:
        json.dump(en_sorted, f, ensure_ascii=False, indent=2)
    with open('locales/sv.json', 'w', encoding='utf-8') as f:
        json.dump(sv_sorted, f, ensure_ascii=False, indent=2)

    print("Successfully built locales/de.json, locales/en.json, locales/sv.json!")

if __name__ == '__main__':
    build_all_locales()
