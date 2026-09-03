# Audit of `tr(...)` Calls and Missing Keys in `locales/*.json`

**Total `tr(...)` Calls Found in `src/`:** 477

**Total `tr(...)` Keys Missing from `locales/de.json`:** 241

## Missing Keys by Namespace / Prefix

| Namespace | Missing Keys Count | Example Keys |
| :--- | :---: | :--- |
| `tag_mgmt` | 17 | `tag_mgmt.header`, `tag_mgmt.tag_empty`, `tag_mgmt.add_tag_btn`, ... (+14 more) |
| `common` | 4 | `common.delete`, `common.open`, `common.browse`, ... (+1 more) |
| `dynamic_form` | 14 | `dynamic_form.search_tags`, `dynamic_form.apply_close`, `dynamic_form.no_tags`, ... (+11 more) |
| `handover_dialog` | 13 | `handover_dialog.header_suffix`, `handover_dialog.person_placeholder`, `handover_dialog.no_colleagues`, ... (+10 more) |
| `profile` | 11 | `profile.gemini_modelfile_rules`, `profile.provider_gemini`, `profile.checking_ollama`, ... (+8 more) |
| `email_draft` | 12 | `email_draft.ai_generating`, `email_draft.case_required_for_ai`, `email_draft.copied_to_clipboard`, ... (+9 more) |
| `attachments` | 7 | `attachments.open_explorer`, `attachments.no_case`, `attachments.add_file`, ... (+4 more) |
| `colleague_mgmt` | 11 | `colleague_mgmt.username`, `colleague_mgmt.new_colleague_btn`, `colleague_mgmt.header`, ... (+8 more) |
| `customer_mgmt` | 11 | `customer_mgmt.missing_id_name`, `customer_mgmt.cobra_import_btn`, `customer_mgmt.search_placeholder`, ... (+8 more) |
| `new_case_dialog` | 11 | `new_case_dialog.is_internal`, `new_case_dialog.customer`, `new_case_dialog.header`, ... (+8 more) |
| `snippet_mgmt` | 10 | `snippet_mgmt.tags_lbl`, `snippet_mgmt.no_snippets`, `snippet_mgmt.cat_lbl`, ... (+7 more) |
| `wiki` | 7 | `wiki.search_placeholder`, `wiki.header`, `wiki.sync_btn`, ... (+4 more) |
| `schema_builder` | 9 | `schema_builder.label_ph`, `schema_builder.add_btn`, `schema_builder.field_id_ph`, ... (+6 more) |
| `export_dialog` | 8 | `export_dialog.copy_btn`, `export_dialog.save_file_btn`, `export_dialog.select_template`, ... (+5 more) |
| `zip_import` | 8 | `zip_import.select_mode`, `zip_import.unpack_btn`, `zip_import.root_folder_btn`, ... (+5 more) |
| `new_case` | 6 | `new_case.future_date`, `new_case.tag_input_title`, `new_case.tag_input_prompt`, ... (+3 more) |
| `p2p` | 7 | `p2p.select_colleague`, `p2p.no_colleagues_cfg`, `p2p.no_diff_cases`, ... (+4 more) |
| `quick_customer` | 6 | `quick_customer.err_name`, `quick_customer.header`, `quick_customer.phone`, ... (+3 more) |
| `export` | 5 | `export.copied`, `export.no_template`, `export.missing_fields_hdr`, ... (+2 more) |
| `followup` | 5 | `followup.date_lbl`, `followup.presets_lbl`, `followup.no_due_cases`, ... (+2 more) |
| `convert_schema` | 4 | `convert_schema.header`, `convert_schema.select_target`, `convert_schema.already_used`, ... (+1 more) |
| `email_import` | 4 | `email_import.no_emails`, `email_import.info_msg`, `email_import.fetching`, ... (+1 more) |
| `template_mgmt` | 4 | `template_mgmt.header`, `template_mgmt.load_defaults`, `template_mgmt.no_templates`, ... (+1 more) |
| `snippet_picker` | 3 | `snippet_picker.preview`, `snippet_picker.no_snippets`, `snippet_picker.search` |
| `cockpit` | 3 | `cockpit.followup_at`, `cockpit.email_copied_title`, `cockpit.no_email_title` |
| `case_list` | 3 | `case_list.completed_badge`, `case_list.no_cases`, `case_list.zero_cases` |
| `email_calendar` | 2 | `email_calendar.client_opened`, `email_calendar.text_copied` |
| `board` | 2 | `board.cockpit_btn`, `board.collapse_btn` |
| `table` | 2 | `table.details_header`, `table.save_btn` |
| `date_picker` | 2 | `date_picker.time_lbl`, `date_picker.o_clock` |
| `searchable_combo` | 2 | `searchable_combo.placeholder`, `searchable_combo.no_results` |
| `help_dialog` | 1 | `help_dialog.no_topics` |
| `analytics` | 1 | `analytics.copied_title` |
| `form` | 1 | `form.no_fields` |
| `timeline` | 1 | `timeline.no_notes` |
| `toast` | 1 | `toast.reminder_title` |

---

## Detailed List of Missing Keys (with File, Line, and Default Fallback)

### Namespace: `tag_mgmt`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `tag_mgmt.tab_tags` | `src/ui/dialogs/tag_management_dialog.py:69` | "🏷 Allgemeine Tags" |
| `tag_mgmt.tab_modules` | `src/ui/dialogs/tag_management_dialog.py:70` | "🧩 Programmbereiche" |
| `tag_mgmt.search_tags_placeholder` | `src/ui/dialogs/tag_management_dialog.py:77` | "🔍 Tags durchsuchen..." |
| `tag_mgmt.new_tag_placeholder` | `src/ui/dialogs/tag_management_dialog.py:84` | "Neuen Tag erstellen (z. B. Schnittstelle)..." |
| `tag_mgmt.add_tag_btn` | `src/ui/dialogs/tag_management_dialog.py:87` | "+ Tag Hinzufügen" |
| `tag_mgmt.search_modules_placeholder` | `src/ui/dialogs/tag_management_dialog.py:99` | "🔍 Programmbereiche durchsuchen..." |
| `tag_mgmt.new_module_placeholder` | `src/ui/dialogs/tag_management_dialog.py:106` | "Neuen Programmbereich erstellen (z. B. Rezeptdruck)..." |
| `tag_mgmt.add_module_btn` | `src/ui/dialogs/tag_management_dialog.py:109` | "+ Bereich Hinzufügen" |
| `tag_mgmt.tag_added` | `src/ui/dialogs/tag_management_dialog.py:174` | "✅ Tag erfolgreich hinzugefügt!" |
| `tag_mgmt.module_added` | `src/ui/dialogs/tag_management_dialog.py:227` | "✅ Programmbereich erfolgreich hinzugefügt!" |
| `tag_mgmt.tag_empty` | `src/ui/dialogs/tag_management_dialog.py:164` | "⚠ Tag Name darf nicht leer sein!" |
| `tag_mgmt.tag_exists` | `src/ui/dialogs/tag_management_dialog.py:168` | "⚠ Tag existiert bereits!" |
| `tag_mgmt.module_empty` | `src/ui/dialogs/tag_management_dialog.py:217` | "⚠ Programmbereich darf nicht leer sein!" |
| `tag_mgmt.module_exists` | `src/ui/dialogs/tag_management_dialog.py:221` | "⚠ Programmbereich existiert bereits!" |
| `tag_mgmt.header` | `src/ui/dialogs/tag_management_dialog.py:50` | "🏷 System-Tags & Programmbereiche" |
| `tag_mgmt.no_tags` | `src/ui/dialogs/tag_management_dialog.py:146` | "Keine Tags gefunden." |
| `tag_mgmt.no_modules` | `src/ui/dialogs/tag_management_dialog.py:200` | "Keine Programmbereiche gefunden." |

### Namespace: `common`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `common.delete` | `src/ui/dialogs/colleague_management_dialog.py:147` | "🗑 Löschen" |
| `common.open` | `src/ui/dialogs/followup_flyout_dialog.py:67` | "👁 Öffnen" |
| `common.delete` | `src/ui/dialogs/schema_builder_dialog.py:135` | "🗑 Löschen" |
| `common.delete` | `src/ui/dialogs/snippet_management_dialog.py:120` | "🗑 Löschen" |
| `common.delete` | `src/ui/dialogs/tag_management_dialog.py:154` | "🗑 Löschen" |
| `common.delete` | `src/ui/dialogs/tag_management_dialog.py:208` | "🗑 Löschen" |
| `common.delete` | `src/ui/dialogs/template_manager_dialog.py:284` | "🗑 Löschen" |
| `common.edit` | `src/ui/dialogs/template_manager_dialog.py:287` | "✏ Bearbeiten" |
| `common.browse` | `src/ui/dialogs/zip_import_dialog.py:183` | "Durchsuchen..." |
| `common.browse` | `src/ui/dialogs/zip_import_dialog.py:205` | "Durchsuchen..." |
| `common.browse` | `src/ui/dialogs/zip_import_dialog.py:226` | "Durchsuchen..." |
| `common.open` | `src/ui/widgets/attachment_widget.py:108` | "📂 Öffnen" |
| `common.open` | `src/ui/widgets/dynamic_form_widget.py:629` | "👁 Öffnen" |
| `common.open` | `src/ui/widgets/toast_notification.py:26` | "👁 Öffnen" |
| `common.open` | `src/ui/widgets/toast_notification.py:110` | "👁 Öffnen" |

### Namespace: `dynamic_form`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `dynamic_form.number_placeholder` | `src/ui/widgets/dynamic_form_field_renderers.py:295` | "Zahl..." |
| `dynamic_form.import_backup` | `src/ui/widgets/dynamic_form_field_renderers.py:237` | "📁 .backup-Datei importieren..." |
| `dynamic_form.choose_file` | `src/ui/widgets/dynamic_form_field_renderers.py:284` | "📁 Datei wählen..." |
| `dynamic_form.manage_tags` | `src/ui/widgets/dynamic_form_field_renderers.py:66` | "⚙ Programmbereiche verwalten" |
| `dynamic_form.search_tags` | `src/ui/widgets/dynamic_form_widget.py:91` | "🔍 Programmbereich suchen..." |
| `dynamic_form.no_files` | `src/ui/widgets/dynamic_form_widget.py:561` | "📎 Abgelegte Dateien im Fallordner: Keine (0)" |
| `dynamic_form.import_title` | `src/ui/widgets/dynamic_form_widget.py:582` | "Dateien in Fallordner importieren" |
| `dynamic_form.no_files` | `src/ui/widgets/dynamic_form_widget.py:607` | "📎 Abgelegte Dateien im Fallordner: Keine (0)" |
| `dynamic_form.select_tags` | `src/ui/widgets/dynamic_form_widget.py:85` | "🧩 Programmbereiche auswählen:" |
| `dynamic_form.select_all` | `src/ui/widgets/dynamic_form_widget.py:98` | "Alle auswählen" |
| `dynamic_form.select_none` | `src/ui/widgets/dynamic_form_widget.py:99` | "Keine auswählen" |
| `dynamic_form.apply_close` | `src/ui/widgets/dynamic_form_widget.py:111` | "✓ Übernehmen & Schließen" |
| `dynamic_form.import_files` | `src/ui/widgets/dynamic_form_widget.py:568` | "+ Datei(en) importieren..." |
| `dynamic_form.files_attached` | `src/ui/widgets/dynamic_form_widget.py:611` | "Abgelegte Dateien im Fallordner" |
| `dynamic_form.no_tags` | `src/ui/widgets/dynamic_form_widget.py:123` | "Kein Programmbereich gefunden." |

### Namespace: `handover_dialog`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `handover_dialog.no_colleagues` | `src/ui/dialogs/handover_dialog.py:87` | "- Keine Mitarbeiter in Liste -" |
| `handover_dialog.person_placeholder` | `src/ui/dialogs/handover_dialog.py:94` | "Empfänger-Name..." |
| `handover_dialog.note_placeholder` | `src/ui/dialogs/handover_dialog.py:104` | "z. B. Ticket #104 im GitLab angelegt, Rückruf erbeten..." |
| `handover_dialog.select_colleague` | `src/ui/dialogs/handover_dialog.py:87` | "- Aus Mitarbeiterliste wählen -" |
| `handover_dialog.new_actor` | `src/ui/dialogs/handover_dialog.py:69` | "Neue verantwortliche Stelle *:" |
| `handover_dialog.channel` | `src/ui/dialogs/handover_dialog.py:76` | "Art der Weitergabe / Kanal *:" |
| `handover_dialog.recipient` | `src/ui/dialogs/handover_dialog.py:82` | "Empfänger / Name der Person (aus Mitarbeiterliste wählen oder eingeben):" |
| `handover_dialog.note` | `src/ui/dialogs/handover_dialog.py:102` | "Notiz / Details zur Übergabe (optional):" |
| `handover_dialog.confirm_btn` | `src/ui/dialogs/handover_dialog.py:121` | "🤝 Übergabe bestätigen" |
| `handover_dialog.header` | `src/ui/dialogs/handover_dialog.py:56` | "Zuständigkeit für" |
| `handover_dialog.header_suffix` | `src/ui/dialogs/handover_dialog.py:56` | "übergeben" |
| `handover_dialog.curr_actor` | `src/ui/dialogs/handover_dialog.py:63` | "Aktuelle Zuständigkeit:" |
| `handover_dialog.customer` | `src/ui/dialogs/handover_dialog.py:63` | "Kunde:" |

### Namespace: `profile`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `profile.provider_gemini` | `src/ui/dialogs/profile_settings_ai_tab.py:107` | "GOOGLE GEMINI (Cloud)" |
| `profile.provider_ollama` | `src/ui/dialogs/profile_settings_ai_tab.py:107` | "OLLAMA (Lokal)" |
| `profile.anonymize_toggle` | `src/ui/dialogs/profile_settings_ai_tab.py:113` | "🔒 Lokale PII-Anonymisierung aktivieren (DSGVO / § 203 StGB)" |
| `profile.gemini_modelfile_rules` | `src/ui/dialogs/profile_settings_ai_tab.py:180` | "📄 Modelfile-Systemregeln für Gemini in Basis-Regeln übernehmen (aus ollama/Modelfile)" |
| `profile.checking_ollama` | `src/ui/dialogs/profile_settings_ai_tab.py:197` | "🔍 Prüfe Ollama-Status..." |
| `profile.scan_ollama_btn` | `src/ui/dialogs/profile_settings_ai_tab.py:204` | "🔄 Status & Modelle scannen" |
| `profile.provider_ollama` | `src/ui/dialogs/profile_settings_ai_tab.py:104` | "OLLAMA (Lokal)" |
| `profile.provider_gemini` | `src/ui/dialogs/profile_settings_ai_tab.py:104` | "GOOGLE GEMINI (Cloud)" |
| `profile.ai_header` | `src/ui/dialogs/profile_settings_ai_tab.py:91` | "🤖 KI- & NLP-Einstellungen (Ollama Local LLM & Google Gemini API)" |
| `profile.ai_provider_label` | `src/ui/dialogs/profile_settings_ai_tab.py:99` | "KI-Anbieter wählen:" |
| `profile.gemini_key_lbl` | `src/ui/dialogs/profile_settings_ai_tab.py:125` | "🔑 Google Gemini API Key:" |
| `profile.gemini_select_model` | `src/ui/dialogs/profile_settings_ai_tab.py:156` | "Gemini Modell wählen:" |
| `profile.widths_reset_msg` | `src/ui/dialogs/profile_settings_dialog.py:481` | "Alle Spaltenbreiten aller Ansichten auf Standard zurückgesetzt!" |

### Namespace: `email_draft`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `email_draft.snippet_inserted` | `src/ui/dialogs/email_draft_dialog.py:495` | "✓ Textbaustein eingefügt." |
| `email_draft.ai_generating` | `src/ui/dialogs/email_draft_dialog.py:595` | "🤖 KI generiert E-Mail-Entwurf..." |
| `email_draft.mailto_opened` | `src/ui/dialogs/email_draft_dialog.py:514` | "✓ Standard-Mail-Programm aufgerufen." |
| `email_draft.outlook_opened` | `src/ui/dialogs/email_draft_dialog.py:539` | "✓ E-Mail erfolgreich in Outlook geöffnet." |
| `email_draft.copied_to_clipboard` | `src/ui/dialogs/email_draft_dialog.py:579` | "✓ E-Mail in Zwischenablage kopiert." |
| `email_draft.case_required_for_ai` | `src/ui/dialogs/email_draft_dialog.py:666` | "⚠ KI-Entwurf benötigt einen aktiven Fall." |
| `email_draft.recipient_lbl` | `src/ui/dialogs/email_draft_dialog.py:175` | "Empfänger (E-Mail):" |
| `email_draft.close_btn` | `src/ui/dialogs/email_draft_dialog.py:227` | "✕ Schließen" |
| `email_draft.subject_lbl` | `src/ui/dialogs/email_draft_dialog.py:245` | "Betreff:" |
| `email_draft.body_lbl` | `src/ui/dialogs/email_draft_dialog.py:255` | "E-Mail Nachrichtentext:" |
| `email_draft.eml_handed_over` | `src/ui/dialogs/email_draft_dialog.py:565` | "✓ E-Mail-Entwurf an E-Mail-Client übergeben (.eml)." |
| `email_draft.ai_please_wait` | `src/ui/dialogs/email_draft_dialog.py:605` | "Bitte einen Moment gedulden — Modell generiert Antwort" |

### Namespace: `attachments`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `attachments.title` | `src/ui/widgets/attachment_widget.py:29` | "Fall-Dateianhänge" |
| `attachments.open_explorer` | `src/ui/widgets/attachment_widget.py:32` | "📁 Explorer öffnen" |
| `attachments.no_preview` | `src/ui/widgets/attachment_widget.py:43` | "Keine Datei zur Vorschau ausgewählt" |
| `attachments.add_file` | `src/ui/widgets/attachment_widget.py:50` | "+ Datei hinzufügen..." |
| `attachments.tip` | `src/ui/widgets/attachment_widget.py:53` | "💡 Tipp: Strg+V fügt Screenshot als PNG ein" |
| `attachments.title` | `src/ui/widgets/attachment_widget.py:59` | "Fall-Dateianhänge" |
| `attachments.open_explorer` | `src/ui/widgets/attachment_widget.py:61` | "📁 Explorer öffnen" |
| `attachments.no_preview` | `src/ui/widgets/attachment_widget.py:63` | "Keine Datei zur Vorschau ausgewählt" |
| `attachments.add_file` | `src/ui/widgets/attachment_widget.py:65` | "+ Datei hinzufügen..." |
| `attachments.tip` | `src/ui/widgets/attachment_widget.py:67` | "💡 Tipp: Strg+V fügt Screenshot als PNG ein" |
| `attachments.no_case` | `src/ui/widgets/attachment_widget.py:79` | "Kein Fall ausgewählt." |
| `attachments.no_files` | `src/ui/widgets/attachment_widget.py:84` | "Keine Dateianhänge im Fallordner." |

### Namespace: `colleague_mgmt`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `colleague_mgmt.new_colleague_btn` | `src/ui/dialogs/colleague_management_dialog.py:58` | "+ Neuen Mitarbeiter anlegen" |
| `colleague_mgmt.search_placeholder` | `src/ui/dialogs/colleague_management_dialog.py:75` | "🔍 Name, Kürzel, Abteilung..." |
| `colleague_mgmt.details_header` | `src/ui/dialogs/colleague_management_dialog.py:89` | "Mitarbeiterdetails" |
| `colleague_mgmt.header` | `src/ui/dialogs/colleague_management_dialog.py:52` | "👥 Mitarbeiter- & Kollegeneinträge" |
| `colleague_mgmt.username` | `src/ui/dialogs/colleague_management_dialog.py:99` | "Kürzel / Username *:" |
| `colleague_mgmt.name` | `src/ui/dialogs/colleague_management_dialog.py:103` | "Name / Anzeigename *:" |
| `colleague_mgmt.department` | `src/ui/dialogs/colleague_management_dialog.py:107` | "Abteilung / Department:" |
| `colleague_mgmt.phone` | `src/ui/dialogs/colleague_management_dialog.py:112` | "Durchwahl / Telefon:" |
| `colleague_mgmt.email` | `src/ui/dialogs/colleague_management_dialog.py:116` | "E-Mail-Adresse:" |
| `colleague_mgmt.mobile` | `src/ui/dialogs/colleague_management_dialog.py:120` | "Mobiltelefon:" |
| `colleague_mgmt.notes` | `src/ui/dialogs/colleague_management_dialog.py:124` | "Aufgabengebiet / Notizen:" |

### Namespace: `customer_mgmt`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `customer_mgmt.new_practice_btn` | `src/ui/dialogs/customer_form_builders.py:41` | "+ Neue Praxis anlegen" |
| `customer_mgmt.cobra_import_btn` | `src/ui/dialogs/customer_form_builders.py:46` | "🐍 Cobra CRM Import..." |
| `customer_mgmt.search_placeholder` | `src/ui/dialogs/customer_form_builders.py:62` | "🔍 Praxis / ID suchen..." |
| `customer_mgmt.save_practice_btn` | `src/ui/dialogs/customer_form_builders.py:105` | "💾 Praxis Speichern" |
| `customer_mgmt.details_title` | `src/ui/dialogs/customer_form_builders.py:123` | "Praxis-Details" |
| `customer_mgmt.header` | `src/ui/dialogs/customer_form_builders.py:39` | "🏥 Registrierte Praxen" |
| `customer_mgmt.cust_id_lbl` | `src/ui/dialogs/customer_form_builders.py:127` | "Kunden-ID (z.B. CUST-1001):" |
| `customer_mgmt.practice_name_lbl` | `src/ui/dialogs/customer_form_builders.py:137` | "Praxisname *:" |
| `customer_mgmt.new_practice_hdr` | `src/ui/dialogs/customer_management_dialog.py:367` | "🆕 Neue Praxis anlegen" |
| `customer_mgmt.saved_msg` | `src/ui/dialogs/customer_management_dialog.py:487` | "✅ Praxis gespeichert!" |
| `customer_mgmt.missing_id_name` | `src/ui/dialogs/customer_management_dialog.py:413` | "⚠ ID und Praxisname erforderlich!" |

### Namespace: `new_case_dialog`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `new_case_dialog.create_btn` | `src/ui/dialogs/new_case_dialog.py:127` | "Fall anlegen" |
| `new_case_dialog.header` | `src/ui/dialogs/new_case_dialog.py:141` | "Neuen Support-Fall erfassen" |
| `new_case_dialog.is_internal` | `src/ui/dialogs/new_case_dialog.py:148` | "🏢 Interner Vorgang (ohne Kundenelement)" |
| `new_case_dialog.add_practice_btn` | `src/ui/dialogs/new_case_dialog.py:166` | "+ Neue Praxis" |
| `new_case_dialog.customer` | `src/ui/dialogs/new_case_dialog.py:156` | "Kunde / Praxis:" |
| `new_case_dialog.title_label` | `src/ui/dialogs/new_case_dialog.py:172` | "Titel / Kurzbeschreibung:" |
| `new_case_dialog.created_at` | `src/ui/dialogs/new_case_dialog.py:177` | "Erstellungsdatum / Vorgangsbeginn (TT.MM.JJJJ HH:MM):" |
| `new_case_dialog.schema` | `src/ui/dialogs/new_case_dialog.py:189` | "Formular-Schema:" |
| `new_case_dialog.tags` | `src/ui/dialogs/new_case_dialog.py:198` | "Tags / Stichworte zuweisen:" |
| `new_case_dialog.deadline` | `src/ui/dialogs/new_case_dialog.py:206` | "Rückruf-Deadline (optional, TT.MM.JJJJ HH:MM):" |
| `new_case_dialog.initial_note` | `src/ui/dialogs/new_case_dialog.py:215` | "Initiale Notiz / Eingangskanal:" |

### Namespace: `snippet_mgmt`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `snippet_mgmt.new_snippet_status` | `src/ui/dialogs/snippet_management_dialog.py:213` | "Neuer Textbaustein (wird beim Speichern angelegt)" |
| `snippet_mgmt.title_required` | `src/ui/dialogs/snippet_management_dialog.py:226` | "⚠ Bitte einen Titel eingeben." |
| `snippet_mgmt.content_required` | `src/ui/dialogs/snippet_management_dialog.py:229` | "⚠ Der Inhalt darf nicht leer sein." |
| `snippet_mgmt.header` | `src/ui/dialogs/snippet_management_dialog.py:41` | "📝 Textbaustein-Bibliothek verwalten" |
| `snippet_mgmt.new_snippet` | `src/ui/dialogs/snippet_management_dialog.py:45` | "+ Neuer Textbaustein" |
| `snippet_mgmt.title_lbl` | `src/ui/dialogs/snippet_management_dialog.py:69` | "Titel:" |
| `snippet_mgmt.cat_lbl` | `src/ui/dialogs/snippet_management_dialog.py:73` | "Kategorie:" |
| `snippet_mgmt.content_lbl` | `src/ui/dialogs/snippet_management_dialog.py:77` | "Inhalt / Baustein-Text:" |
| `snippet_mgmt.tags_lbl` | `src/ui/dialogs/snippet_management_dialog.py:81` | "Tags (kommagetrennt):" |
| `snippet_mgmt.no_snippets` | `src/ui/dialogs/snippet_management_dialog.py:154` | "Keine Textbausteine vorhanden." |

### Namespace: `wiki`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `wiki.header` | `src/ui/widgets/wiki_widget.py:19` | "BookStack Offline Wiki" |
| `wiki.sync_btn` | `src/ui/widgets/wiki_widget.py:22` | "🔄 Wiki Sync" |
| `wiki.search_placeholder` | `src/ui/widgets/wiki_widget.py:29` | "📖 Wiki durchsuchen (z. B. ERR_DB_902)..." |
| `wiki.syncing` | `src/ui/widgets/wiki_widget.py:95` | "⏳ Synchronisiere Wiki im Hintergrund..." |
| `wiki.header` | `src/ui/widgets/wiki_widget.py:44` | "BookStack Offline Wiki" |
| `wiki.sync_btn` | `src/ui/widgets/wiki_widget.py:46` | "🔄 Wiki Sync" |
| `wiki.search_placeholder` | `src/ui/widgets/wiki_widget.py:48` | "📖 Wiki durchsuchen (z. B. ERR_DB_902)..." |
| `wiki.enter_query` | `src/ui/widgets/wiki_widget.py:61` | "Bitte Suchbegriff eingeben." |
| `wiki.articles_found` | `src/ui/widgets/wiki_widget.py:65` | "Wiki-Artikel gefunden" |
| `wiki.no_results` | `src/ui/widgets/wiki_widget.py:68` | "Keine treffenden Artikel im Offline-Index." |

### Namespace: `schema_builder`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `schema_builder.new_form` | `src/ui/dialogs/schema_builder_dialog.py:120` | "+ Neues Formular" |
| `schema_builder.adopt_schema` | `src/ui/dialogs/schema_builder_dialog.py:125` | "📥 Zu Realdaten übernehmen" |
| `schema_builder.default_schemas` | `src/ui/dialogs/schema_builder_dialog.py:132` | "🔄 Standard-Formulare" |
| `schema_builder.field_id_ph` | `src/ui/dialogs/schema_builder_dialog.py:155` | "Feld-ID (z. B. reason_detail)" |
| `schema_builder.label_ph` | `src/ui/dialogs/schema_builder_dialog.py:158` | "Beschriftung (Label)" |
| `schema_builder.required_chk` | `src/ui/dialogs/schema_builder_dialog.py:165` | "Pflicht" |
| `schema_builder.add_btn` | `src/ui/dialogs/schema_builder_dialog.py:168` | "+ Hinzufügen" |
| `schema_builder.fields_header` | `src/ui/dialogs/schema_builder_dialog.py:141` | "Enthaltene Formularfelder:" |
| `schema_builder.add_field_header` | `src/ui/dialogs/schema_builder_dialog.py:150` | "Neues Feld hinzufügen (V2 mit bedingter Logik):" |

### Namespace: `export_dialog`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `export_dialog.manage_templates_btn` | `src/ui/dialogs/export_dialog.py:78` | "🛠 Vorlagen verwalten" |
| `export_dialog.force_export_chk` | `src/ui/dialogs/export_dialog.py:93` | "Trotz unvollständiger Daten exportieren ([FEHLT: ...] Platzhalter)" |
| `export_dialog.save_file_btn` | `src/ui/dialogs/export_dialog.py:115` | "In Datei speichern..." |
| `export_dialog.copy_btn` | `src/ui/dialogs/export_dialog.py:118` | "In Zwischenablage kopieren" |
| `export_dialog.export_for` | `src/ui/dialogs/export_dialog.py:56` | "Export für Fall" |
| `export_dialog.select_template` | `src/ui/dialogs/export_dialog.py:63` | "Vorlage auswählen:" |
| `export_dialog.no_template` | `src/ui/dialogs/export_dialog.py:68` | "Keine Vorlage" |
| `export_dialog.preview_header` | `src/ui/dialogs/export_dialog.py:100` | "Vorschau des exportierten Textes:" |

### Namespace: `zip_import`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `zip_import.root_folder_btn` | `src/ui/dialogs/zip_import_dialog.py:90` | "📁 Gesamt-Zielordner wählen" |
| `zip_import.custom_paths_btn` | `src/ui/dialogs/zip_import_dialog.py:99` | "⚙ Einzelne Pfade anpassen" |
| `zip_import.warning_overwrite` | `src/ui/dialogs/zip_import_dialog.py:116` | "⚠ Hinweis: Beim Importieren werden vorhandene Dateien mit gleichem Namen am Zielspeicherort überschrieben." |
| `zip_import.select_mode` | `src/ui/dialogs/zip_import_dialog.py:81` | "Wählen Sie aus, wie die Zielspeicherorte festgelegt werden sollen:" |
| `zip_import.unpack_btn` | `src/ui/dialogs/zip_import_dialog.py:141` | "📥 Daten entpacken & importieren" |
| `zip_import.main_target_dir` | `src/ui/dialogs/zip_import_dialog.py:169` | "Haupt-Zielverzeichnis (Erzeugt automatisch data/ und attachments/ Unterordner):" |
| `zip_import.data_loc` | `src/ui/dialogs/zip_import_dialog.py:192` | "1. Speicherort für Datendateien & Profile (data/):" |
| `zip_import.att_loc` | `src/ui/dialogs/zip_import_dialog.py:213` | "2. Speicherort für Fall-Anhänge (attachments/):" |

### Namespace: `new_case`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `new_case.add_tag` | `src/ui/dialogs/new_case_dialog.py:275` | "+ Tag" |
| `new_case.tag_input_prompt` | `src/ui/dialogs/new_case_dialog.py:293` | "Geben Sie den Namen des neuen Tags ein:" |
| `new_case.tag_input_title` | `src/ui/dialogs/new_case_dialog.py:293` | "Neuen Tag hinzufügen" |
| `new_case.title_required` | `src/ui/dialogs/new_case_dialog.py:348` | "Bitte einen Titel für den Fall eingeben." |
| `new_case.future_date` | `src/ui/dialogs/new_case_dialog.py:370` | "Das Erstellungsdatum darf nicht in der Zukunft liegen." |
| `new_case.invalid_date` | `src/ui/dialogs/new_case_dialog.py:357` | "Ungültiges Erstellungsdatum-Format (z. B. TT.MM.JJJJ HH:MM)." |
| `new_case.invalid_date` | `src/ui/dialogs/new_case_dialog.py:361` | "Ungültiges Erstellungsdatum-Format (z. B. TT.MM.JJJJ HH:MM)." |

### Namespace: `p2p`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `p2p.reload_compare` | `src/ui/dialogs/p2p_diff_dialog.py:60` | "Neu Laden / Vergleichen" |
| `p2p.import_selected` | `src/ui/dialogs/p2p_diff_dialog.py:78` | "Ausgewählte Fälle übernehmen" |
| `p2p.no_colleague_selected` | `src/ui/dialogs/p2p_diff_dialog.py:88` | "Kein Kollege ausgewählt." |
| `p2p.select_at_least_one` | `src/ui/dialogs/p2p_diff_dialog.py:159` | "Bitte mindestens einen Fall zur Übernahme auswählen." |
| `p2p.select_colleague` | `src/ui/dialogs/p2p_diff_dialog.py:48` | "Kollege auswählen:" |
| `p2p.no_colleagues_cfg` | `src/ui/dialogs/p2p_diff_dialog.py:52` | "Keine Kollegen konfiguriert" |
| `p2p.no_diff_cases` | `src/ui/dialogs/p2p_diff_dialog.py:110` | "Keine abweichenden Fälle vorhanden." |

### Namespace: `quick_customer`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `quick_customer.err_name` | `src/ui/dialogs/new_case_dialog.py:59` | "Bitte Praxisnamen eingeben." |
| `quick_customer.header` | `src/ui/dialogs/new_case_dialog.py:29` | "Neue Praxis anlegen" |
| `quick_customer.practice_name` | `src/ui/dialogs/new_case_dialog.py:31` | "Praxisname *:" |
| `quick_customer.contact_person` | `src/ui/dialogs/new_case_dialog.py:35` | "Ansprechpartner:" |
| `quick_customer.phone` | `src/ui/dialogs/new_case_dialog.py:39` | "Telefon:" |
| `quick_customer.is_vip` | `src/ui/dialogs/new_case_dialog.py:44` | "⭐ VIP-Praxis" |

### Namespace: `export`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `export.no_template` | `src/ui/dialogs/export_dialog.py:129` | "Keine Vorlage ausgewählt." |
| `export.ready` | `src/ui/dialogs/export_dialog.py:187` | "✅ Vorlage bereit zum Export." |
| `export.incomplete` | `src/ui/dialogs/export_dialog.py:192` | "⚠ Unvollständig! Bitte Felder ergänzen oder Force-Export aktivieren." |
| `export.copied` | `src/ui/dialogs/export_dialog.py:211` | "📋 Erfolgreich in Zwischenablage kopiert!" |
| `export.missing_fields_hdr` | `src/ui/dialogs/export_dialog.py:149` | "⚠ Fehlende Pflichtfelder direkt ergänzen:" |

### Namespace: `followup`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `followup.presets_lbl` | `src/ui/dialogs/followup_dialog.py:50` | "⚡ Schnellauswahl / Presets:" |
| `followup.date_lbl` | `src/ui/dialogs/followup_dialog.py:103` | "📅 Erinnerungs-Datum & Uhrzeit (TT.MM.JJJJ HH:MM):" |
| `followup.note_lbl` | `src/ui/dialogs/followup_dialog.py:127` | "📝 Notiz / Nachfrage-Grund (Optional):" |
| `followup.save_btn` | `src/ui/dialogs/followup_dialog.py:142` | "💾 Wiedervorlage Speichern" |
| `followup.no_due_cases` | `src/ui/dialogs/followup_flyout_dialog.py:54` | "Keine fälligen Wiedervorlagen aktuell vorhanden." |

### Namespace: `convert_schema`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `convert_schema.select_valid` | `src/ui/dialogs/convert_schema_dialog.py:128` | "Bitte ein gültiges Ziel-Formular auswählen." |
| `convert_schema.already_used` | `src/ui/dialogs/convert_schema_dialog.py:132` | "Der Fall verwendet bereits dieses Formular-Schema." |
| `convert_schema.header` | `src/ui/dialogs/convert_schema_dialog.py:50` | "🔄 Formular-Schema umwandeln" |
| `convert_schema.select_target` | `src/ui/dialogs/convert_schema_dialog.py:77` | "Neues Ziel-Formular auswählen:" |

### Namespace: `email_import`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `email_import.info_msg` | `src/ui/dialogs/email_import_dialog.py:71` | "Eingehende E-Mails aus Microsoft Outlook / Posteingang werden automatisch mit bestehenden Fällen abgeglichen." |
| `email_import.fetching` | `src/ui/dialogs/email_import_dialog.py:103` | "⏳ Rufe Posteingang ab..." |
| `email_import.refresh_btn` | `src/ui/dialogs/email_import_dialog.py:60` | "🔄 Posteingang aktualisieren" |
| `email_import.no_emails` | `src/ui/dialogs/email_import_dialog.py:118` | "Keine neuen E-Mails im Posteingang gefunden." |

### Namespace: `template_mgmt`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `template_mgmt.new_template` | `src/ui/dialogs/template_manager_dialog.py:235` | "+ Neue Vorlage" |
| `template_mgmt.load_defaults` | `src/ui/dialogs/template_manager_dialog.py:238` | "🔄 Standard-Vorlagen laden" |
| `template_mgmt.header` | `src/ui/dialogs/template_manager_dialog.py:233` | "📄 Export-Vorlagen-Verwaltung" |
| `template_mgmt.no_templates` | `src/ui/dialogs/template_manager_dialog.py:268` | "Keine Vorlagen vorhanden." |

### Namespace: `snippet_picker`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `snippet_picker.search` | `src/ui/dialogs/snippet_picker_dialog.py:47` | "🔍 Textbaustein suchen..." |
| `snippet_picker.preview` | `src/ui/dialogs/snippet_picker_dialog.py:77` | "Vorschau des Textbausteins:" |
| `snippet_picker.no_snippets` | `src/ui/dialogs/snippet_picker_dialog.py:114` | "Keine Textbausteine gefunden." |

### Namespace: `cockpit`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `cockpit.followup_at` | `src/ui/views/cockpit_view.py:533` | "🔔 Nachfragen am:" |
| `cockpit.email_copied_title` | `src/ui/views/cockpit_view.py:328` | "📋 E-Mail kopiert" |
| `cockpit.no_email_title` | `src/ui/views/cockpit_view.py:336` | "⚠ Keine E-Mail-Adresse" |

### Namespace: `case_list`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `case_list.zero_cases` | `src/ui/widgets/case_list_widget.py:64` | "0 Fälle" |
| `case_list.completed_badge` | `src/ui/widgets/case_list_widget.py:195` | "✓ ERLEDIGT" |
| `case_list.no_cases` | `src/ui/widgets/case_list_widget.py:155` | "Keine Fälle gefunden." |

### Namespace: `email_calendar`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `email_calendar.client_opened` | `src/ui/dialogs/email_calendar_dialog.py:191` | "✓ Mail-Client wurde mit dem Entwurf aufgerufen." |
| `email_calendar.text_copied` | `src/ui/dialogs/email_calendar_dialog.py:198` | "✓ E-Mail Text wurde in die Zwischenablage kopiert." |

### Namespace: `board`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `board.cockpit_btn` | `src/ui/views/board_view.py:114` | "🎯 Cockpit" |
| `board.collapse_btn` | `src/ui/views/board_view.py:263` | "◀ Zuklappen" |

### Namespace: `table`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `table.details_header` | `src/ui/views/table_view.py:137` | "📋 Falldetails & Formular (Wählen Sie einen Fall aus der Tabelle)" |
| `table.save_btn` | `src/ui/views/table_view.py:145` | "💾 Ändern & Speichern" |

### Namespace: `date_picker`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `date_picker.time_lbl` | `src/ui/widgets/date_picker.py:126` | "⏰ Uhrzeit:" |
| `date_picker.o_clock` | `src/ui/widgets/date_picker.py:213` | "Uhr" |

### Namespace: `searchable_combo`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `searchable_combo.placeholder` | `src/ui/widgets/searchable_combobox.py:112` | "🔍 Buchstaben eintippen zum Suchen..." |
| `searchable_combo.no_results` | `src/ui/widgets/searchable_combobox.py:172` | "Keine Praxen gefunden" |

### Namespace: `help_dialog`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `help_dialog.no_topics` | `src/ui/dialogs/help_dialog.py:631` | "Keine Themen gefunden." |

### Namespace: `analytics`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `analytics.copied_title` | `src/ui/views/analytics_view.py:272` | "📋 Statistik kopiert" |

### Namespace: `form`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `form.no_fields` | `src/ui/widgets/dynamic_form_widget.py:360` | "Keine Formularfelder definiert." |

### Namespace: `timeline`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `timeline.no_notes` | `src/ui/widgets/timeline_widget.py:99` | "Keine Notizen vorhanden." |

### Namespace: `toast`

| Key | File:Line | Default Text (German Fallback) |
| :--- | :--- | :--- |
| `toast.reminder_title` | `src/ui/widgets/toast_notification.py:16` | "Erinnerung" |
