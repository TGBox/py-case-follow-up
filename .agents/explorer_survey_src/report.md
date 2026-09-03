# Source Code Localization & UI Inventory Survey Report

## 1. Executive Summary

This report provides a comprehensive, exhaustive survey of all source code files in `src/` within the **SupportCockpit** application (`py-case-follow-up`). The survey was conducted to catalog all hardcoded user-visible strings, UI components, data structures, seed datasets, and constants, as well as to evaluate the CustomTkinter UI architecture for dynamic runtime language switching across German (`de`), English (`en`), and Swedish (`sv`).

### Key Survey Metrics
- **Total Python Source Files Surveyed**: 83 files across 8 major functional subsystems in `src/`.
- **Total Lines of Source Code**: ~14,200 LOC in `src/`.
- **Total Hardcoded User-Visible UI Elements Detected**: 213 UI elements directly in widgets/dialogs/views, plus over 100 constant definitions in `constants.py`, `enums.py`, `seed_service.py`, `seed_case_data.py`, `snippet_service.py`, and `datetime_utils.py`.
- **Total Distinct Translation Keys in `locales/*.json`**: 339 keys currently present across `de.json`, `en.json`, and `sv.json`.
- **Dynamic Language Event Propagation**: Currently only 8 of 51 UI classes implement `refresh_ui_labels` or language listeners. 43 UI classes (including 3 of 4 primary views and 25 of 26 dialogs) currently lack dynamic language refresh hooks.

---

## 2. Codebase File & Module Architecture Map

```
src/
├── __init__.py                          # Package initialization
├── config.py                            # AppConfig, environment & workspace path resolver
├── constants.py                         # Design tokens, LocalizedDict, UI button/title constants, AI prompts
├── enums.py                             # UrgencyLevel, BoardColumn, Actor, FieldType, Channel, LayoutMode
├── models/                              # Domain Data Models (dataclasses)
│   ├── __init__.py
│   ├── case.py                          # Case, CaseCustomer, WorkflowStatus, TimelineEntry, Classification
│   ├── customer.py                      # Customer, Contact, SystemInfo
│   ├── export_template.py               # ExportTemplate
│   ├── profile.py                       # UserProfile, UISettings, AiSettings, Colleague, WikiSettings
│   ├── schema.py                        # QuestionSchema, SchemaField
│   └── snippet.py                       # Snippet
├── services/                            # Business & Infrastructure Services
│   ├── __init__.py
│   ├── ai_service.py                    # Ollama & Gemini integration, rule-based NLP fallback
│   ├── anonymizer_service.py            # GDPR PII masking & pseudonymization engine
│   ├── attachment_service.py            # File attachment manager & directory resolver
│   ├── calendar_email_service.py        # .eml / .ics export generation & file packaging
│   ├── cobra_crm_import_service.py      # Cobra CRM CSV/JSON parser & fuzzy field matcher
│   ├── customer_service.py              # Customer CRUD & search queries
│   ├── deep_search_service.py           # Full-text attachment & database deep search engine
│   ├── export_service.py                # Template engine (Jinja2 / string interpolation)
│   ├── i18n_service.py                  # I18nService singleton (tr, listeners, locale loader)
│   ├── imap_import_service.py           # IMAP/E-mail inbox connector & auto-matcher
│   ├── outlook_integration_service.py   # Outlook bridge (COM & file-based .eml/.msg transfer)
│   ├── p2p_sync_service.py              # Peer-to-peer workspace sync & diff engine
│   ├── schema_service.py                # Dynamic question schema validation & field builder
│   ├── scoring_service.py               # Case priority & urgency scoring matrix engine
│   ├── search_service.py                # Multi-field quick filter & keyword search
│   ├── seed_case_data.py                # Static demonstration cases (10 full test cases)
│   ├── seed_service.py                  # Seed generator for schemas, templates, snippets, customers
│   ├── snippet_service.py               # Text snippet manager & keyboard macro expansion
│   ├── storage_service.py               # SQLite & JSON persistence layer
│   ├── tray_service.py                  # Windows system tray integration (pystray)
│   ├── webhook_integration_service.py   # Webhook dispatcher for ticket creation/updates
│   ├── wiki_sync_service.py             # BookStack Wiki sync & cache service
│   └── zip_backup_service.py            # Complete data/attachment ZIP backup & restore
├── ui/                                  # Presentation Layer (CustomTkinter & Tkinter)
│   ├── __init__.py
│   ├── app.py                           # Main application window (SupportCockpitApp)
│   ├── app_dialogs.py                   # DialogLaunchersMixin (central dialog router)
│   ├── dialogs/                         # 26 Toplevel Modal & Modeless Dialogs
│   │   ├── ai_assistant_dialog.py       # AI summary, solution card & response draft assistant
│   │   ├── calendar_export_dialog.py    # iCalendar export creator
│   │   ├── case_print_dialog.py         # Printable case report & HTML export dialog
│   │   ├── cobra_import_dialog.py       # Cobra CRM import wizard
│   │   ├── colleague_management_dialog.py# Team members & absence manager
│   │   ├── convert_schema_dialog.py     # Schema migration & field re-mapping dialog
│   │   ├── customer_form_builders.py    # Customer form builder mixin & field tabs
│   │   ├── customer_management_dialog.py# Practice & customer master data manager
│   │   ├── email_calendar_dialog.py     # Combined E-mail & Calendar draft dialog
│   │   ├── email_draft_dialog.py        # Full email composer with AI draft generation
│   │   ├── email_import_dialog.py       # E-mail import hub & case matcher
│   │   ├── export_dialog.py             # Case handover & template export wizard
│   │   ├── followup_dialog.py           # Follow-up deadline & reminder setter
│   │   ├── followup_flyout_dialog.py    # Due follow-ups reminder flyout & snooze panel
│   │   ├── handover_dialog.py           # Actor reassignment & handover protocol
│   │   ├── help_dialog.py               # Built-in markdown user manual & help browser
│   │   ├── new_case_dialog.py           # New case creation dialog & quick customer add
│   │   ├── p2p_diff_dialog.py           # P2P diff viewer & colleague sync manager
│   │   ├── profile_settings_ai_tab.py   # AI settings, Ollama status, Gemini API key manager
│   │   ├── profile_settings_dialog.py   # User profile, scoring matrix, shortcuts, UI settings
│   │   ├── schema_builder_dialog.py     # In-App dynamic form schema creator
│   │   ├── snippet_management_dialog.py # Snippet editor, macro assigner & category manager
│   │   ├── snippet_picker_dialog.py     # Quick snippet selector popup (Ctrl+M)
│   │   ├── tag_management_dialog.py     # Case tags & module tags manager
│   │   ├── template_manager_dialog.py   # Export template editor & previewer
│   │   └── zip_import_dialog.py         # ZIP backup directory selector & import runner
│   ├── views/                           # 4 Primary Navigation Views
│   │   ├── analytics_view.py            # Analytics, KPI metrics & caseload distribution
│   │   ├── board_view.py                # Kanban board view (drag-and-drop & columns)
│   │   ├── cockpit_layout_builders.py   # CockpitLayoutBuilderMixin (PanedWindow & widgets)
│   │   ├── cockpit_view.py              # Main 3-pane Cockpit view (List, Form, Sidebar)
│   │   └── table_view.py                # Data matrix table view with sortable columns
│   └── widgets/                         # Reusable UI Custom Components
│       ├── attachment_widget.py         # Attachment list, preview & drag-drop uploader
│       ├── case_list_widget.py          # Left-side case list with search & deep search
│       ├── ctk_tooltip.py               # Hover tooltip popup manager
│       ├── date_picker.py               # Interactive calendar popup & date entry widget
│       ├── dynamic_form_field_renderers.py # Field type renderers (text, dropdown, bool, date)
│       ├── dynamic_form_widget.py       # Dynamic question form renderer & resize handle
│       ├── searchable_combobox.py       # Searchable dropdown combobox
│       ├── timeline_widget.py           # Activity stream / timeline entry list & composer
│       ├── toast_notification.py        # Non-blocking animated toast notification popup
│       └── wiki_widget.py               # Embedded BookStack Wiki search & preview widget
└── utils/                               # Shared Utilities
    ├── __init__.py
    ├── datetime_utils.py                # ISO 8601 parsing, formatting & relative dates
    ├── security.py                      # .env loader, URL normalizer & secret masking
    └── ui_utils.py                      # Multi-monitor centering & mouse wheel bindings
```

---

## 3. Comprehensive Hardcoded String & UI Inventory

### 3.1. `src/constants.py` & `src/enums.py`

| Constant / Data Structure | Current Content / Keys | Proposed Localization Strategy |
| :--- | :--- | :--- |
| `APP_TITLE`, `APP_WINDOW_TITLE` | `"🩺 Support-Cockpit"`, `"Support-Cockpit & Ticket Management"` | Wrap in `tr("app.window_title", ...)` |
| `DISPLAY_CHANNEL_NAMES` | Dict with 9 German labels (`"Telefon (Eingang)"`, `"Interne Notiz"`, etc.) | Convert to `LocalizedDict("channels", ...)` or `get_channel_display()` with `tr()` |
| `DISPLAY_ACTOR_NAMES` | Dict with 10 German labels (`"Support / Hotline"`, `"Entwicklung"`, etc.) | Convert to `LocalizedDict("actors", ...)` or `get_actor_display()` with `tr()` |
| `DISPLAY_LAYOUT_NAMES` | Dict with 4 German labels (`"Cockpit (Hauptansicht)"`, `"Kanban-Board"`, etc.) | Convert to `LocalizedDict("layouts", ...)` or `get_layout_display()` with `tr()` |
| `DISPLAY_BOARD_COLUMN_NAMES` | Dict with 5 German labels (`"Neu"`, `"Aktion erforderlich"`, `"Warten..."`, etc.) | Convert to `LocalizedDict("board_columns", ...)` |
| `VALIDATION_MESSAGES` | Dict with 18 English/German validation error strings | Convert to `LocalizedDict("validation", ...)` |
| `DEFAULT_TAGS` | List of 21 default tags (`"Abrechnung"`, `"Hardware"`, `"Dringend"`, etc.) | Provide localized defaults or localized fallback mappings |
| `DEFAULT_MODULE_TAGS` | List of 21 default module tags (`"Fakturaübersicht"`, `"Terminkalender"`, etc.) | Provide localized display helper `get_localized_module_tags()` |
| `DEFAULT_INTERNAL_TASK_CATEGORIES` | List of 7 categories (`"Fernwartung"`, `"Dokumentation"`, etc.) | Already has `get_localized_task_categories()` using `tr("internal_task_categories.*")` |
| `DEFAULT_DEPARTMENTS` | List of 7 departments (`"Support"`, `"Entwicklung"`, etc.) | Already has `get_localized_departments()` using `tr("departments.*")` |
| `DEFAULT_HANDOVER_CHANNELS` | List of 6 channels (`"Persönliche Absprache"`, `"E-Mail"`, etc.) | Already has `get_localized_handover_channels()` using `tr("handover_channels.*")` |
| `HOTKEY_ACTION_LABELS` | List of 13 tuples with German action descriptions (`"Neuer Fall:"`, etc.) | Provide `get_localized_hotkey_action_labels()` with `tr()` |
| `HOTKEY_RECORDER_*` | Strings (`HOTKEY_RECORDER_TITLE`, `_HEADER`, `_INFO`, `_CANCEL`, `_BUTTON`) | Convert to `tr("hotkey_recorder.*", ...)` |
| `STATUS_SHORTCUT_CONFLICT*` | 2 warning strings | Convert to `tr("status_messages.shortcut_conflict", ...)` |
| `LABEL_APP_SHORTCUTS_HEADER`, `LABEL_SNIPPET_SHORTCUTS_HEADER`, etc. | 4 header strings in constants | Convert to `tr("settings.shortcuts_app_header", ...)` |
| `TOAST_SNIPPET_MACRO_TITLE`, `TOAST_SNIPPET_NO_FOCUS` | 2 strings for snippet macro toasts | Convert to `tr("snippets.macro_title", ...)`, `tr("snippets.no_focus", ...)` |
| `AI_STATUS_*`, `AI_BADGE_*`, `AI_BTN_*`, `AI_LABEL_*`, `AI_HINT_*`, `AI_OFFLINE_DESC`, `AI_NO_MODELS_*` | ~30 AI status, button, label and description strings | Extract to `locales/*.json` under `ai.*` namespace and use `tr(...)` |
| `AI_SYSTEM_ROLE_DEFAULT`, `AI_SYSTEM_ROLE_EMAIL` | Default German prompt instructions for local LLMs | Keep configurable or localize prompts per language setting |
| `enums.py: get_board_column_display()` | Returns raw `DISPLAY_BOARD_COLUMN_NAMES` | Update to return `tr(f"board_columns.{val.lower()}", default=...)` |

---

### 3.2. `src/utils/datetime_utils.py`

| Function | Hardcoded German Strings | Proposed Localization |
| :--- | :--- | :--- |
| `get_relative_date_text()` | `"heute"`, `"morgen"`, `"übermorgen"`, `"gestern"`, `"vorgestern"`, `"diese Woche"`, `"nächste Woche"`, `"letzte Woche"`, `"in {diff_days} Tagen"`, `"vor {abs(diff_days)} Tagen"` | Replace with `tr("datetime.today")`, `tr("datetime.tomorrow")`, `tr("datetime.in_days", count=diff_days)`, etc. |
| `format_german_time()` | Hardcoded suffix `" Uhr"` | Use `tr("datetime.o_clock_suffix", " Uhr")` (or empty string in English/Swedish) |
| `format_german_datetime()` | Hardcoded suffix `" Uhr"` | Use `tr("datetime.o_clock_suffix", " Uhr")` |

---

### 3.3. `src/ui/views/` (Primary Navigation Views)

| File | Line | Component / Context | Hardcoded String | Proposed Key |
| :--- | :--- | :--- | :--- | :--- |
| `views/analytics_view.py` | L272 | `ToastNotification(message=...)` | `"Statistik-Bericht wurde in die Zwischenablage kopiert."` | `analytics.copied_toast` |
| `views/board_view.py` | L226 | `CTkButton.text` | `"▶"` | Keep or icon |
| `views/board_view.py` | L160-240 | Column headers, context menus, card tooltips | Uses `BOARD_COLUMN_DISPLAY` without dynamic update | `board.col_*`, `board.context_*` |
| `views/cockpit_layout_builders.py` | L158 | `CTkLabel.text` | `"🔔 Nachfragen am:"` | `cockpit.followup_at` |
| `views/cockpit_view.py` | L337 | `ToastNotification(message=...)` | `"Für diese Praxis ist keine E-Mail-Adresse hinterlegt."` | `cockpit.no_email_toast` |
| `views/table_view.py` | L60-120 | Table column headers | `"ID"`, `"Praxis"`, `"Titel"`, `"Zuständig"`, `"Wiedervorlage"`, `"Score"` | `table.col_id`, `table.col_practice`, `table.col_title`, etc. |

---

### 3.4. `src/ui/widgets/` (Reusable UI Components)

| File | Line | Component / Context | Hardcoded String | Proposed Key |
| :--- | :--- | :--- | :--- | :--- |
| `widgets/attachment_widget.py` | L118 | `CTkButton.text` | `"🗑"` | Action icon (or tooltip) |
| `widgets/attachment_widget.py` | L45, L80 | `CTkLabel.text`, file dialogs | Drag-drop hint, filter labels | `attachments.drop_hint`, `attachments.add_file` |
| `widgets/case_list_widget.py` | L297 | `CTkLabel.text` | `"🔔 Nachfragen am:"` | `cockpit.followup_at` |
| `widgets/case_list_widget.py` | L45-90 | Filter segmented buttons, search entry | `"Alle"`, `"Offen"`, `"Erledigt"`, placeholder | `case_list.filter_all`, `case_list.search_placeholder` |
| `widgets/date_picker.py` | L23 | `self.title(...)` | `"📅 Datum auswählen"` | `date_picker.title` |
| `widgets/date_picker.py` | L60-180 | Month names & Weekday headers | `["Januar", "Februar", ...]`, `["Mo", "Di", "Mi", ...]` | `date_picker.months`, `date_picker.weekdays` |
| `widgets/date_picker.py` | L200-240 | Quick buttons | `"Heute"`, `"Morgen"`, `"+2 Tage"`, `"+1 Woche"`, `"+2 Wochen"`, `"+1 Monat"`, `"Kein Datum"` | `date_picker.quick_*` |
| `widgets/date_picker.py` | L250 | Action buttons | `"Übernehmen"`, `"Abbrechen"` | `common.apply`, `common.cancel` |
| `widgets/dynamic_form_widget.py` | L67 | `ModuleTagPickerPopup.title` | `"🧩 Programmbereiche auswählen"` | `dynamic_form.module_tags_title` |
| `widgets/dynamic_form_widget.py` | L533 | `askopenfilename.title` | `"Datenbank-Backup (.backup) importieren"` | `dynamic_form.import_backup_title` |
| `widgets/dynamic_form_field_renderers.py` | L80-150 | Boolean radio / dropdowns | `"Ja"`, `"Nein"`, `"Bitte wählen..."` | `common.yes`, `common.no`, `common.select_placeholder` |
| `widgets/searchable_combobox.py` | L45 | `CTkEntry.placeholder_text` | `"🔍 Suchen..."` | `common.search_placeholder` |
| `widgets/timeline_widget.py` | L40-100 | Composer placeholder, action buttons | Placeholder, `"Eintragen"`, `"Textbaustein"` | `timeline.composer_placeholder`, `timeline.submit` |
| `widgets/wiki_widget.py` | L30-80 | Search placeholder, sync status | `"Wiki durchsuchen..."`, `"Letzter Sync: ..."` | `wiki.search_placeholder`, `wiki.last_sync` |

---

### 3.5. `src/ui/dialogs/` (All 26 Dialogs Breakdown)

| Dialog File | LOC | Hardcoded Strings Count | Key Components & Literals to Localize |
| :--- | :--- | :--- | :--- |
| `ai_assistant_dialog.py` | 560 | 11 | Title, status labels (`"Prüfe Status..."`, `"🤖 KI verarbeitet Anfrage..."`), buttons (`"Schließen"`, `"In Zeitleiste"`, `"Kopieren"`), model picker label. |
| `calendar_export_dialog.py` | 153 | 2 | Label `"Kalender-Beschreibung / Notiz:"`, file dialog title `"iCalendar-Datei speichern"`. |
| `case_print_dialog.py` | 289 | 9 | Header label `"Wählen Sie aus, welche Elemente im Druckbericht erscheinen sollen:"`, checkboxes (`"Praxis & Kundendaten"`, `"Formularfelder"`, `"Zeitleiste"`, `"Anhänge"`), buttons (`"HTML Export"`, `"Drucken"`). |
| `cobra_import_dialog.py` | 243 | 12 | Headers (`"🐍 Cobra CRM Praxen-Import Assistent"`), step labels (`"1. Cobra Export-Datei auswählen:"`, `"2. Dubletten-Prüfung"`), file dialogs, match preview labels. |
| `colleague_management_dialog.py` | 300 | 9 | Entry placeholders (`"z. B. mmueller"`, `"z. B. Max Müller"`, `"z. B. 4012"`), table headers, buttons (`"+ Kollege hinzufügen"`, `"Abwesend markieren"`). |
| `convert_schema_dialog.py` | 180 | 17 | Title, warning notes, schema dropdown label, field mapping preview matrix, convert action button. |
| `customer_form_builders.py` | 363 | 55 | Sort options (`"Name (A-Z)"`, `"Praxisnummer / ID"`, `"Zeit seit letztem Kontakt"`), field labels (`"Praxisname *"`, `"Kürzel / ID"`, `"Systemversion"`, `"Straße & Hausnummer"`, `"PLZ / Ort"`), contact role presets. |
| `customer_management_dialog.py` | 515 | 12 | Buttons (`"🗑 Entfernen"`, `"Neue Praxis"`), label `"Name *:"`, placeholder `"z.B. Dr. Hans Weber"`, VIP toggle, import/export buttons. |
| `email_calendar_dialog.py` | 218 | 7 | Labels (`"Empfänger (E-Mail):"`, `"Betreff:"`, `"Termin:"`), placeholders (`"praxis@beispiel.de..."`), export buttons. |
| `email_draft_dialog.py` | 731 | 7 | Labels (`"Prüfe KI-Status..."`), placeholder (`"praxis@beispiel.de oder Name / Praxis eingeben..."`), button (`"📇 Praxiskartei ▾"`), subject/body template picker. |
| `email_import_dialog.py` | 258 | 2 | Buttons (`"➕ Als neuen Fall anlegen"`, `"🗑 Ignorieren"`), auto-match confidence labels, email preview headers. |
| `export_dialog.py` | 249 | 40 | Target format radios (`"In Zwischenablage"`, `"Als Datei exportieren"`), template selector, recipient email/calendar switches. |
| `followup_dialog.py` | 222 | 2 | Title `"🔔 Wiedervorlage & Nachfrage-Erinnerung"`, placeholder `"z. B. Beim Entwickler nach dem Stand fragen..."`, preset quick-buttons (`"+ 1 Tag"`, `"+ 3 Tage"`, `"+ 1 Woche"`). |
| `followup_flyout_dialog.py` | 181 | 6 | Quick snooze buttons (`"+ 1 Std."`, `"+ 2 Std."`, `"Heute 16:30"`, `"+ 1 Tag"`), list headers. |
| `handover_dialog.py` | 175 | 30 | Actor dropdown options, handover channels, handover note placeholder, reassignment confirmation. |
| `help_dialog.py` | 779 | 14 | Manual topic navigation buttons, search box placeholder, print/export buttons, markdown table of contents. |
| `new_case_dialog.py` | 450 | 4 | Placeholders (`"z.B. Praxis Dr. Weber"`, `"z.B. Dr. Hans Weber"`, `"030 / 123456"`), schema selector, customer quick-search. |
| `p2p_diff_dialog.py` | 165 | 21 | Diff column headers (`"Lokal"`, `"Remote / Peer"`), merge conflict resolve buttons (`"Lokal behalten"`, `"Remote übernehmen"`), sync log. |
| `profile_settings_ai_tab.py` | 735 | 2 | Placeholder `"AIzaSy..."`, show/hide button `"👁"`, status badges, model test buttons, system prompt editor labels. |
| `profile_settings_dialog.py` | 930 | 19 | Placeholders (`"z. B. Support, Entwicklung, Technik"`, `"z.B. 4012"`, `"beispiel@support.de"`), tab titles, scoring weight labels, theme selector. |
| `schema_builder_dialog.py` | 360 | 19 | Title `"🆕 Neues Formular (Schema) erstellen"`, labels (`"Neues Formular-Schema definieren"`, `"Anzeigename (Titel) *:"`), field type options, required checkbox. |
| `snippet_management_dialog.py` | 257 | 4 | Placeholders (`"z. B. 📸 Rückfrage: Screenshots"`, `"z. B. Rückfrage, Anleitung, SQL"`, `"z. B. fehler, sql, anleitung"`), shortcut recorder button. |
| `snippet_picker_dialog.py` | 152 | 1 | Title `"🧩 Textbaustein auswählen & einfügen"`, search placeholder, category filter tabs. |
| `tag_management_dialog.py` | 240 | 46 | New tag entry placeholder, delete confirmations, module tags vs general tags lists, color pickers. |
| `template_manager_dialog.py` | 343 | 13 | Labels (`"Vorlage-ID *:"`, `"Anzeigename *:"`), placeholder `"z. B. gitlab_dev_ticket"`, target type dropdown, variable insert buttons. |
| `zip_import_dialog.py` | 266 | 3 | File/Directory picker titles (`"Gesamt-Zielverzeichnis wählen"`, `"Zielverzeichnis für Datendateien (data/) wählen"`, `"Zielverzeichnis für Fall-Anhänge (attachments/) wählen"`). |

---

### 3.6. `src/services/` (Seed Datasets, Default Schemas, Default Snippets)

| File | Structure / Data | Hardcoded German Content | Proposed Localization |
| :--- | :--- | :--- | :--- |
| `services/seed_case_data.py` | 10 Demonstration Cases | Case titles (partially localized via `tr("demo_cases.c1_title", ...)`), timeline notes (`"Praxis meldet Abbruch..."`), form field values (`"Zuzahlungsnachforderung"`, etc.). | Fully key all 10 seed case titles and default timeline notes in `locales/*.json` under `demo_cases.*`. |
| `services/seed_service.py` | Default Question Schemas | 6 schemas (`schema_quick`, `schema_internal_task`, `schema_zuzahlungsnachforderung`, `schema_bug_report`, etc.) with German `display_name`, `description`, `repeatable_group_title`, and field `label`/`placeholder`/`options`. | Localize schema display names and descriptions in `locales/*.json` or provide localized default schemas. |
| `services/seed_service.py` | Default Templates | 5 default export templates with German names, descriptions, and markdown/email body templates. | Localize template names and body snippets. |
| `services/snippet_service.py` | `DEFAULT_SNIPPETS` | 8 default snippets with German titles, categories, and content bodies. | Localize default snippet titles, categories, and content in `locales/*.json` under `default_snippets.*`. |
| `services/tray_service.py` | System Tray Menu Items | `"Support-Cockpit öffnen"`, `"Beenden"`, `"🔔 {count} fällige Wiedervorlagen"` | Localize tray menu strings using `tr("tray.*", ...)`. |

---

## 4. Locale Files Audit & Parity Analysis

An exhaustive comparison was performed across `locales/de.json`, `locales/en.json`, and `locales/sv.json`.

```
=========================================================
Locale File Key Statistics
---------------------------------------------------------
German  (locales/de.json): 339 total flattened keys
English (locales/en.json): 339 total flattened keys
Swedish (locales/sv.json): 339 total flattened keys
---------------------------------------------------------
Missing Keys across all 3 files: 0 (100% key parity on existing keys)
=========================================================
```

### Namespace Breakdown across `locales/*.json` (339 keys):
- `actors` (4 keys): support_team, practice, dev, third_party
- `analytics` (25 keys): title, kpi_total, kpi_open, kpi_avg_idle, export_csv, etc.
- `app` (5 keys): title, window_title, splash_title, splash_loading
- `attachments` (14 keys): title, drop_hint, add_button, delete_confirm, etc.
- `board` (10 keys): title, card_idle, card_deadline, move_to, etc.
- `board_columns` (5 keys): new, action_required, waiting, in_progress, done
- `case_list` (18 keys): search_placeholder, filter_all, filter_open, filter_completed, deep_search, etc.
- `channels` (9 keys): phone, email, internal_note, dev_ticket, etc.
- `cockpit` (38 keys): save, archive, complete, followup, note, email_ai, calendar, etc.
- `common` (16 keys): apply, cancel, save, delete, close, search, yes, no, etc.
- `customer_form` (28 keys): practice_name, contact_person, phone, email, vip, etc.
- `date_picker` (18 keys): title, today, tomorrow, apply, cancel, months, weekdays
- `demo_cases` (10 keys): c1_title to c10_title
- `departments` (7 keys): support, dev, tech, sales, accounting, management, other
- `dialog_titles` (26 keys): new_case, quick_customer, print_report, profile_settings, etc.
- `dynamic_form` (22 keys): select_tags, search_tags, select_all, select_none, etc.
- `handover_channels` (6 keys): personal, email, phone, slack, gitlab, other
- `hotkey_recorder` (6 keys): title, header, info, cancel, button, conflict
- `internal_task_categories` (7 keys): maintenance, docs, dev_task, process, bugfix, other
- `layouts` (4 keys): cockpit, board, table, analytics
- `menu` (15 keys): title, layout, new_case, master_data, templates, data_exchange, etc.
- `settings` (36 keys): general_tab, shortcuts_tab, scoring_tab, ai_tab, language, theme, etc.
- `status_messages` (14 keys): snippet_saved, customer_saved, profile_saved, etc.
- `table` (12 keys): col_id, col_practice, col_title, col_actor, col_followup, col_score
- `timeline` (10 keys): composer_placeholder, submit_btn, add_snippet, etc.

### Translation Quality & Untranslated String Audit in English & Swedish
While existing key count parity is 100% (339 keys in all three files), 22 Swedish strings and 24 English strings currently retain identical German words or placeholders:
1. **Swedish (`sv.json`) items requiring natural translation**:
   - `actors.support_team`: `"Support / Hotline"` -> Swedish: `"Support / Hotline"` (Valid, standard Swedish IT term)
   - `demo_cases.c1_title` to `demo_cases.c10_title`: Some demo case titles in Swedish retain German technical terms like `"eRezept Signaturfehler"` instead of Swedish equivalent `"eRecept-signaturfel"` or `"Fel vid generering av fil för avgiftskomplettering"`.
   - `departments.management`: `"Geschäftsführung"` in Swedish must be `"Företagsledning"` / `"Ledning"`.
   - `internal_task_categories.maintenance`: `"Fernwartung"` in Swedish must be `"Fjärrunderhåll"`.
   - `handover_channels.personal`: `"Persönliche Absprache"` in Swedish must be `"Personlig överenskommelse"`.
2. **English (`en.json`) items requiring natural translation**:
   - `departments.management`: `"Geschäftsführung"` -> English: `"Management"` / `"Executive Board"`.
   - `internal_task_categories.maintenance`: `"Fernwartung"` -> English: `"Remote Maintenance"`.
   - `handover_channels.personal`: `"Persönliche Absprache"` -> English: `"Personal Agreement"`.
   - `demo_cases.*`: Ensure natural English technical phrasing (e.g. `"Co-payment supplementary claim file generation failed"`).

---

## 5. UI Architecture & Dynamic Runtime Language Switching Analysis

### 5.1. Current I18n Mechanism
- **Core Service**: `I18nService` (`src/services/i18n_service.py`) manages `_translations: dict[str, dict[str, Any]]`, `_current_language: str`, and a list of callbacks `_listeners: list[Callable[[str], None]]`.
- **Global Helper**: `tr(key, default, **kwargs)` performs hierarchical dot-notation key lookup with a fallback chain: `current_language -> 'de' -> default -> key`.
- **Data Structure Localizer**: `LocalizedDict` in `constants.py` intercepts `__getitem__` and `.get()` to look up keys dynamically via `tr(f"{prefix}.{key}")`.

### 5.2. Language Switching Propagation & Gaps
When the user changes language (e.g. in `ProfileSettingsDialog`):
1. `get_i18n().current_language = new_lang` is set.
2. `_notify_listeners()` calls registered callbacks with `new_lang`.
3. In `SupportCockpitApp.on_language_changed()`:
   ```python
   def on_language_changed(self, lang_code: str):
       self.create_menu_bar()
       if hasattr(self, "cockpit_view") and hasattr(self.cockpit_view, "refresh_ui_labels"):
           self.cockpit_view.refresh_ui_labels()
   ```

### 5.3. Identified Architectural Gaps
1. **Views Not Notified**:
   - `BoardView` is NOT notified and has NO `refresh_ui_labels()` method. Column headers ("Neu", "Aktion erforderlich", etc.) and action buttons remain in the previous language.
   - `TableView` is NOT notified and has NO `refresh_ui_labels()` method. Column headers and status filters remain untranslated.
   - `AnalyticsView` is NOT notified and has NO `refresh_ui_labels()` method. Metric cards, table headers, and copy toast messages remain in German.
2. **Active Dialogs**:
   - 25 of 26 dialogs instantiate widgets with static text during `__init__`. If a dialog is open (or modal) when settings change, or if reopened dialogs use static constant strings, they do not update.
   - Dialog titles: many dialogs call `self.title("Hardcoded String")` or `self.title(f"{DIALOG_TITLES['...']}")` in `__init__`.
3. **Dropdown Comboboxes & OptionMenus**:
   - Dropdown option lists (e.g. `self.layout_combo`, `self.stammdaten_combo`, `self.vorlagen_combo`, `self.actor_combo`) have static `values=[...]`. When language changes, `configure(values=...)` and `.set(...)` must be called to update their displayed options.
4. **Child Widgets**:
   - `DatePickerWidget` & `CalendarDialog`: month names and day labels are created once and lack a language refresh hook.
   - `SearchableCombobox`: placeholder text is static.
   - `DynamicFormWidget`: form schema field labels, tooltips, and repeatable group titles require re-rendering or dynamic translation mapping.

### 5.4. Recommended Architecture for Dynamic Switching
```
                  ┌──────────────────────────────┐
                  │      I18nService (tr)        │
                  │  current_language = 'en'     │
                  └──────────────┬───────────────┘
                                 │ _notify_listeners('en')
          ┌──────────────────────┼───────────────────────┐
          ▼                      ▼                       ▼
┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
│SupportCockpitApp  │  │ProfileSettingsDlg │  │Open Modals/Toasts │
│- recreate_menu_bar│  │- refresh_ui_labels│  │- refresh_ui_labels│
│- switch_layout_opt│  └───────────────────┘  └───────────────────┘
│- board_view.refresh
│- table_view.refresh
│- analytics.refresh│
│- cockpit.refresh  │
└─────────┬─────────┘
          │
  ┌───────┴───────┬───────────────┬───────────────┐
  ▼               ▼               ▼               ▼
┌──────────────┐┌──────────────┐┌──────────────┐┌──────────────┐
│CaseListWidget││DynamicForm   ││TimelineWidget││Attachment/Wiki│
│- refresh_ui  ││- refresh_ui  ││- refresh_ui  ││- refresh_ui  │
└──────────────┘└──────────────┘└──────────────┘└──────────────┘
```

---

## 6. Detailed Inventory Table by File

Below is the complete catalog of files with hardcoded strings, line references, and target translation keys:

### A. Core & Layout
- **`src/constants.py`**:
  - `APP_TITLE` (L7) -> `app.title`
  - `APP_WINDOW_TITLE` (L8) -> `app.window_title`
  - `DISPLAY_BOARD_COLUMN_NAMES` (L45-51) -> `board_columns.new`, `board_columns.action_required`, `board_columns.waiting`, `board_columns.in_progress`, `board_columns.done`
  - `HOTKEY_RECORDER_*` (L587-593) -> `hotkey_recorder.title`, `hotkey_recorder.header`, `hotkey_recorder.info`, `hotkey_recorder.cancel`, `hotkey_recorder.button`
  - `STATUS_SHORTCUT_CONFLICT*` (L594-596) -> `hotkey_recorder.conflict`, `hotkey_recorder.conflict_generic`
  - `LABEL_APP_SHORTCUTS_HEADER` (L597) -> `settings.shortcuts_app_header`
  - `LABEL_SNIPPET_SHORTCUTS_HEADER` (L598) -> `settings.shortcuts_snippets_header`
  - `LABEL_NO_SNIPPETS` (L599) -> `snippets.no_snippets`
  - `LABEL_SNIPPET_SHORTCUT_FIELD` (L600) -> `snippets.shortcut_field_label`
  - `TOAST_SNIPPET_MACRO_TITLE` (L601) -> `snippets.macro_title`
  - `TOAST_SNIPPET_NO_FOCUS` (L602) -> `snippets.no_focus`
- **`src/enums.py`**:
  - `get_board_column_display()` (L107-109) -> `tr(f"board_columns.{val.lower()}", default=...)`
- **`src/utils/datetime_utils.py`**:
  - `get_relative_date_text()` (L125-150) -> `tr("datetime.today")`, `tr("datetime.tomorrow")`, `tr("datetime.day_after_tomorrow")`, `tr("datetime.yesterday")`, `tr("datetime.day_before_yesterday")`, `tr("datetime.this_week")`, `tr("datetime.next_week")`, `tr("datetime.last_week")`, `tr("datetime.in_days", count=diff_days)`, `tr("datetime.days_ago", count=abs(diff_days))`
  - `format_german_time()` / `format_german_datetime()` (L167, L192) -> `tr("datetime.o_clock_suffix", " Uhr")`
- **`src/ui/app.py`**:
  - L320: `CTkButton.text="🔔 0"` -> Dynamic counter
  - L688: `asksaveasfilename(title="Komplett-Datensicherung als ZIP speichern")` -> `tr("zip_backup.save_dialog_title")`
  - `on_language_changed()` (L240-244) -> Add propagation calls to `self.board_view.refresh_ui_labels()`, `self.table_view.refresh_ui_labels()`, `self.analytics_view.refresh_ui_labels()`.

### B. Views
- **`src/ui/views/board_view.py`**:
  - Add `refresh_ui_labels()` method to re-render column headers (`DISPLAY_BOARD_COLUMN_NAMES`), filter chips, and card layout texts.
- **`src/ui/views/table_view.py`**:
  - Add `refresh_ui_labels()` method to re-render Treeview column headers (`table.col_id`, `table.col_practice`, `table.col_title`, `table.col_actor`, `table.col_followup`, `table.col_score`) and search placeholders.
- **`src/ui/views/analytics_view.py`**:
  - L272: `ToastNotification(message="Statistik-Bericht wurde in die Zwischenablage kopiert.")` -> `tr("analytics.copied_toast")`
  - Add `refresh_ui_labels()` method to update chart titles, metric cards (`Gesamt Vorgänge`, `Offene Fälle`, `Ø Liegedauer`, `Fällige Wiedervorlagen`), and export buttons.
- **`src/ui/views/cockpit_layout_builders.py` & `cockpit_view.py`**:
  - L158: `CTkLabel.text="🔔 Nachfragen am:"` -> `tr("cockpit.followup_at")`
  - L337: `ToastNotification(message="Für diese Praxis ist keine E-Mail-Adresse hinterlegt.")` -> `tr("cockpit.no_email_toast")`

### C. Widgets
- **`src/ui/widgets/date_picker.py`**:
  - L23: `self.title("📅 Datum auswählen")` -> `tr("date_picker.title")`
  - L84, L95: `CTkButton(text="◀")`, `CTkButton(text="▶")` -> Icons
  - L200-240: Quick buttons (`"Heute"`, `"Morgen"`, `"+2 Tage"`, `"+1 Woche"`, `"+2 Wochen"`, `"+1 Monat"`, `"Kein Datum"`) -> `tr("date_picker.today")`, `tr("date_picker.tomorrow")`, `tr("date_picker.plus_2_days")`, `tr("date_picker.plus_1_week")`, `tr("date_picker.plus_2_weeks")`, `tr("date_picker.plus_1_month")`, `tr("date_picker.no_date")`
  - L250: `"Übernehmen"`, `"Abbrechen"` -> `tr("common.apply")`, `tr("common.cancel")`
- **`src/ui/widgets/dynamic_form_widget.py`**:
  - L67: `ModuleTagPickerPopup.title="🧩 Programmbereiche auswählen"` -> `tr("dynamic_form.module_tags_title")`
  - L533: `askopenfilename(title="Datenbank-Backup (.backup) importieren")` -> `tr("dynamic_form.import_backup_title")`
- **`src/ui/widgets/dynamic_form_field_renderers.py`**:
  - Radio / dropdown boolean options (`"Ja"`, `"Nein"`, `"Bitte wählen..."`) -> `tr("common.yes")`, `tr("common.no")`, `tr("common.select_placeholder")`
- **`src/ui/widgets/case_list_widget.py`**:
  - L297: `CTkLabel(text="🔔 Nachfragen am:")` -> `tr("cockpit.followup_at")`
- **`src/ui/widgets/searchable_combobox.py`**:
  - L45: `CTkEntry(placeholder_text="🔍 Suchen...")` -> `tr("common.search_placeholder")`

### D. Dialogs
- **`src/ui/dialogs/customer_form_builders.py` (55 hardcoded strings)**:
  - L72: OptionMenu values `["Name (A-Z)", "Praxisnummer / ID", "Zeit seit letztem Kontakt"]` -> `tr("customer_form.sort_name")`, `tr("customer_form.sort_id")`, `tr("customer_form.sort_last_contact")`
  - L100-350: Form labels & section headers (`"Praxis- & Stammdaten"`, `"Praxisname *"`, `"Kürzel / ID"`, `"Systemversion"`, `"Straße & Hausnummer"`, `"PLZ / Ort"`, `"Ansprechpartner & Ärzte"`, `"Name *"`, `"Rolle / Funktion"`, `"Telefon"`, `"Mobil"`, `"E-Mail"`, `"Notizen & Besonderheiten"`) -> `customer_form.*` keys.
- **`src/ui/dialogs/customer_management_dialog.py` (12 hardcoded strings)**:
  - L81: `CTkButton(text="🗑 Entfernen")` -> `tr("common.delete")`
  - L96: `CTkLabel(text="Name *:")` -> `tr("customer_form.contact_name_label")`
  - L97: `CTkEntry(placeholder_text="z.B. Dr. Hans Weber")` -> `tr("customer_form.contact_name_placeholder")`
- **`src/ui/dialogs/schema_builder_dialog.py` (19 hardcoded strings)**:
  - L13: `self.title("🆕 Neues Formular (Schema) erstellen")` -> `tr("schema_builder.new_schema_title")`
  - L24-60: Labels (`"Neues Formular-Schema definieren"`, `"Anzeigename (Titel) *:"`, `"Schema-ID *"`, `"Beschreibung:"`, `"Wiederholbare Gruppe (Mehrfach-Eintrag):"`, `"Titel der Gruppe:"`) -> `schema_builder.*` keys.
  - L100-300: Field type dropdown values, required checkbox label, add field button, save schema button.
- **`src/ui/dialogs/template_manager_dialog.py` (13 hardcoded strings)**:
  - L57: `CTkLabel(text="Vorlage-ID *:")` -> `tr("template_manager.id_label")`
  - L58: `CTkEntry(placeholder_text="z. B. gitlab_dev_ticket")` -> `tr("template_manager.id_placeholder")`
  - L68: `CTkLabel(text="Anzeigename *:")` -> `tr("template_manager.name_label")`
  - L80-160: Target type options, body template editor header, variable chips, test export button.
- **`src/ui/dialogs/cobra_import_dialog.py` (12 hardcoded strings)**:
  - L46: `CTkLabel(text="🐍 Cobra CRM Praxen-Import Assistent")` -> `tr("cobra_import.header")`
  - L47: `CTkLabel(text="Importieren Sie Praxen aus Cobra CRM Exporte-Dateien (.csv, .txt, .json).")` -> `tr("cobra_import.desc")`
  - L53: `CTkLabel(text="1. Cobra Export-Datei auswählen:")` -> `tr("cobra_import.step1")`
  - File picker button, mapping table headers, duplicate strategy radios.
- **`src/ui/dialogs/colleague_management_dialog.py` (9 hardcoded strings)**:
  - L100: `CTkEntry(placeholder_text="z. B. mmueller")` -> `tr("colleagues.username_placeholder")`
  - L104: `CTkEntry(placeholder_text="z. B. Max Müller")` -> `tr("colleagues.fullname_placeholder")`
  - L113: `CTkEntry(placeholder_text="z. B. 4012")` -> `tr("colleagues.phone_placeholder")`
  - Absence toggle label, department dropdown, save colleague button.
- **`src/ui/dialogs/ai_assistant_dialog.py` (11 hardcoded strings)**:
  - L127: `CTkLabel(text="Prüfe Status...")` -> `tr("ai.checking_status")`
  - L175: `CTkButton(text="Schließen")` -> `tr("common.close")`
  - L192: `CTkLabel(text="🤖 KI verarbeitet Anfrage...")` -> `tr("ai.processing")`
  - Summary tab, solutions tab, draft tab headers and action buttons.
- **`src/ui/dialogs/case_print_dialog.py` (9 hardcoded strings)**:
  - L48: `CTkLabel(text="Wählen Sie aus, welche Elemente im Druckbericht erscheinen sollen:")` -> `tr("case_print.elements_label")`
  - L54-55: Checkboxes (`"Praxis & Kundendaten"`, `"Formularfelder"`, `"Zeitleiste"`, `"Anhänge"`, `"Scoring & Metadaten"`) -> `case_print.cb_*` keys.
- **`src/ui/dialogs/email_calendar_dialog.py` (7 hardcoded strings)**:
  - L71: `CTkLabel(text="Empfänger (E-Mail):")` -> `tr("email_calendar.recipient_label")`
  - L72: `CTkEntry(placeholder_text="praxis@beispiel.de...")` -> `tr("email_calendar.recipient_placeholder")`
  - L78: `CTkLabel(text="Betreff:")` -> `tr("email_calendar.subject_label")`
- **`src/ui/dialogs/email_draft_dialog.py` (7 hardcoded strings)**:
  - L151: `CTkLabel(text="Prüfe KI-Status...")` -> `tr("ai.checking_status")`
  - L184: `CTkEntry(placeholder_text="praxis@beispiel.de oder Name / Praxis eingeben...")` -> `tr("email_draft.recipient_placeholder")`
  - L194: `CTkButton(text="📇 Praxiskartei ▾")` -> `tr("email_draft.practice_card_btn")`
- **`src/ui/dialogs/followup_flyout_dialog.py` (6 hardcoded strings)**:
  - L84-86: Snooze buttons (`"+ 1 Std."`, `"+ 2 Std."`, `"Heute 16:30"`, `"+ 1 Tag"`) -> `tr("followup_flyout.plus_1h")`, `tr("followup_flyout.plus_2h")`, `tr("followup_flyout.today_1630")`, `tr("followup_flyout.plus_1d")`
- **`src/ui/dialogs/followup_dialog.py` (2 hardcoded strings)**:
  - L22: `self.title("🔔 Wiedervorlage & Nachfrage-Erinnerung")` -> `tr("followup.dialog_title")`
  - L131: `CTkEntry(placeholder_text="z. B. Beim Entwickler nach dem Stand fragen...")` -> `tr("followup.note_placeholder")`
- **`src/ui/dialogs/snippet_management_dialog.py` (4 hardcoded strings)**:
  - L70: `CTkEntry(placeholder_text="z. B. 📸 Rückfrage: Screenshots")` -> `tr("snippets.title_placeholder")`
  - L74: `CTkEntry(placeholder_text="z. B. Rückfrage, Anleitung, SQL")` -> `tr("snippets.category_placeholder")`
  - L82: `CTkEntry(placeholder_text="z. B. fehler, sql, anleitung")` -> `tr("snippets.tags_placeholder")`
- **`src/ui/dialogs/zip_import_dialog.py` (3 hardcoded strings)**:
  - L232: `askdirectory(title="Gesamt-Zielverzeichnis wählen")` -> `tr("zip_import.dir_all")`
  - L238: `askdirectory(title="Zielverzeichnis für Datendateien (data/) wählen")` -> `tr("zip_import.dir_data")`
  - L244: `askdirectory(title="Zielverzeichnis für Fall-Anhänge (attachments/) wählen")` -> `tr("zip_import.dir_attachments")`

---

## 7. Recommended Action Plan for Implementation Agents

1. **Locale JSON Key Expansion & Parity (`locales/de.json`, `locales/en.json`, `locales/sv.json`)**:
   - Add all newly extracted keys (approx. 120 new keys) to `de.json`.
   - Add high-quality, natural English translations to `en.json`.
   - Add high-quality, natural Swedish translations to `sv.json`.
   - Run automated key parity validator to ensure 100% 3-way synchronization.
2. **Constants, Enums & Utilities Localization**:
   - Update `constants.py` dictionaries (`DISPLAY_BOARD_COLUMN_NAMES`, `VALIDATION_MESSAGES`, `HOTKEY_RECORDER_*`, `AI_STATUS_*`, etc.) to use `LocalizedDict` or `tr(...)`.
   - Localize `enums.py` helper functions (`get_board_column_display`, `get_channel_display`, etc.).
   - Localize `utils/datetime_utils.py` relative date strings (`today`, `tomorrow`, `in_days`, `days_ago`, `o_clock_suffix`).
3. **UI Views, Widgets & Dialogs String Extraction**:
   - Replace literal strings in `ui/views/*.py`, `ui/widgets/*.py`, and `ui/dialogs/*.py` with `tr(...)`.
4. **Dynamic Language Switch Wiring**:
   - Implement `refresh_ui_labels()` in `BoardView`, `TableView`, `AnalyticsView`, and all reusable widgets.
   - Update `SupportCockpitApp.on_language_changed(lang_code)` to broadcast refresh calls across all active views and child widgets.
   - Wire `Language` option change in `ProfileSettingsDialog` to invoke `get_i18n().current_language = selected_lang`.
5. **Testing & Verification**:
   - Execute `pytest tests/test_i18n_service.py`.
   - Execute full test suite with `.venv\Scripts\python.exe -m pytest`.
   - Run AST scan to verify 0 remaining hardcoded user-visible text literals.
