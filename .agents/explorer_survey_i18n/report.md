# Comprehensive i18n & Translation Infrastructure Survey Report

**Project Root:** `c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up`  
**Working Directory:** `c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up\.agents\explorer_survey_i18n`  
**Date:** 2026-09-02  
**Author:** Explorer (i18n & Translation Infrastructure Survey)

---

## 1. Executive Summary

A comprehensive investigation into the internationalization (i18n) infrastructure, locale files (`locales/de.json`, `locales/en.json`, `locales/sv.json`), UI components, dialogs, widgets, constants, models, and services across `py-case-follow-up` was conducted.

### Core Metrics at a Glance:
- **Supported Languages:** German (`de`, default), English (`en`), Swedish (`sv`).
- **Existing Keys in Locale Files:** **339 keys** each in `locales/de.json`, `locales/en.json`, and `locales/sv.json` (100% key parity across existing keys in the three files).
- **Total `tr(...)` Invocations in Codebase:** **477 calls** across `src/`.
- **Missing Keys in `locales/de.json` (used in `tr(...)` calls):** **241 calls** across **36 distinct namespaces** where `tr("some_key", default="...")` references keys that do not exist in `locales/*.json`.
- **Unextracted Hardcoded String Literals:** **238 occurrences** across **29 files** in `src/` where user-visible strings are passed directly to CTk widgets (`CTkButton`, `CTkLabel`, `CTkOptionMenu`, `CTkTabview`, `CTkCheckBox`, `title()`, `ToastNotification`, `placeholder_text`) without `tr(...)` or `LocalizedDict`.
- **Dynamic Language Switching Gaps:** `ProfileSettingsDialog` and `app.py` implement the initial listener pattern, but only `CockpitView` is refreshed on language change. `BoardView`, `TableView`, `AnalyticsView`, and several modal dialogs currently lack `refresh_ui_labels()` hooks or listener registrations.

---

## 2. Core i18n Architecture

### 2.1 Central Translation Service (`src/services/i18n_service.py`)
The translation engine is centered in `I18nService`, accessed globally via `get_i18n()` singleton and the convenience function `tr(key, default=None, **kwargs)`.

```python
# src/services/i18n_service.py:5-13
SUPPORTED_LANGUAGES = {
    "de": "Deutsch",
    "en": "English",
    "sv": "Svenska",
}
LANGUAGE_DISPLAY_TO_CODE = {v: k for k, v in SUPPORTED_LANGUAGES.items()}
LANGUAGE_CODE_TO_DISPLAY = dict(SUPPORTED_LANGUAGES)
```

#### Key Mechanics:
1. **File Loading (`load_all_translations`):** Loads `{lang_code}.json` from `locales/` directory using UTF-8 encoding.
2. **Nested Dot-Notation Resolution (`_get_nested_val`):** Dot-separated keys (e.g. `menu.new_case`, `help_content.basics.title`) are resolved recursively through nested dicts.
3. **Fallback Chain (`tr` method, lines 73-90):**
   $$\text{Current Language} \longrightarrow \text{"de"} \longrightarrow \text{default argument} \longrightarrow \text{key string}$$
4. **Keyword Formatting (`kwargs`):** If keyword arguments are passed (e.g. `tr("status_messages.ai_ollama_online", model="qwen2.5")`), `result.format(**kwargs)` is applied safely.
5. **Listener Registry:** Maintains `_listeners: list[Callable[[str], None]]`. Setting `current_language` triggers `_notify_listeners()`, broadcasting the new language code to all subscribers.

---

### 2.2 `LocalizedDict` Dynamic Wrapper (`src/constants.py`)

`LocalizedDict` is a custom dictionary subclass located at `src/constants.py:56-76` designed to localize dictionaries with fixed string keys dynamically:

```python
# src/constants.py:56-76
class LocalizedDict(dict):
    def __init__(self, prefix: str, initial_dict: dict[str, str]):
        super().__init__(initial_dict)
        self._prefix = prefix

    def __getitem__(self, key: str) -> str:
        default = super().get(key, key)
        try:
            from services.i18n_service import tr
            return tr(f"{self._prefix}.{key}", default=default)
        except Exception:
            return default

    def get(self, key: str, default: Any = None) -> Any:
        try:
            from services.i18n_service import tr
            fallback = super().get(key, default)
            return tr(f"{self._prefix}.{key}", default=fallback if fallback is not None else key)
        except Exception:
            return super().get(key, default)
```

#### Instances in Codebase:
- `DIALOG_TITLES = LocalizedDict("dialog_titles", {...})` (`src/constants.py:79-107`)
- `DIALOG_HEADERS = LocalizedDict("dialog_headers", {...})` (`src/constants.py:110-112`)
- `UI_BUTTON_TEXTS = LocalizedDict("ui_buttons", {...})` (`src/constants.py:148-171`)
- `STATUS_MESSAGES = LocalizedDict("status_messages", {...})` (`src/constants.py:174-188`)
- `COL_TITLE_MAP = LocalizedDict("table_columns", {...})` (`src/ui/views/table_view.py:19-26`)

---

## 3. Locales Inspection (`locales/*.json`)

### 3.1 Structure and Section Breakdown
All three locale files (`locales/de.json`, `locales/en.json`, `locales/sv.json`) are well-formatted UTF-8 JSON files containing exactly **339 keys** structured across 28 top-level sections:

| Section Name | Key Count | Description |
| :--- | :---: | :--- |
| `menu` | 23 | Main menu items, layout labels, sub-options |
| `cockpit` | 25 | Cockpit action buttons, tab headers, search placeholders |
| `dialog_titles` | 27 | Window titles for all dialogs |
| `dialog_headers` | 1 | Sub-headers in dialogs |
| `ui_buttons` | 24 | Standard action buttons (Save, Cancel, Delete, etc.) |
| `status_messages` | 13 | Toast and status bar feedback messages |
| `departments` | 7 | Support, Development, Tech, Sales, Accounting, Management, Other |
| `handover_channels` | 6 | Personal, Email, Phone, Slack, GitLab, Other |
| `internal_task_categories` | 7 | Remote maintenance, Data exchange, Documentation, Bugfix, etc. |
| `board` | 7 | Kanban board buttons and column headers |
| `table_columns` | 6 | Data table header titles |
| `analytics` | 14 | KPI titles and metric card headers |
| `profile` | 63 | Settings dialog tabs, fields, labels, and descriptions |
| `help_dialog` | 3 | Help navigation and search |
| `template_editor` | 1 | Template preview button |
| `snippet_picker` | 1 | Snippet insert button |
| `convert_schema` | 1 | Convert schema button |
| `cobra_import` | 1 | Cobra import button |
| `email_draft` | 2 | Mail client / Outlook actions |
| `email_calendar` | 3 | Calendar & email draft action buttons |
| `calendar_export` | 2 | Calendar export action buttons |
| `layouts` | 4 | Layout names (Cockpit, Board, Table, Analytics) |
| `actors` | 4 | Actor names (Support, Customer, Dev, Tech) |
| `channels` | 5 | Communication channels (Email, Phone, Ticket, etc.) |
| `common` | 7 | Common actions (OK, Cancel, Save, Close, Search, Error, Info) |
| `help_content` | 75 | Full structured user manual markdown sections |
| `demo_cases` | 5 | Sample case titles (c1_title .. c5_title) |
| `splash` | 2 | Splash loading titles |

### 3.2 Key Parity Status
- $\text{DE keys} \cap \text{EN keys} = 339$ (100% key parity)
- $\text{DE keys} \cap \text{SV keys} = 339$ (100% key parity)
- No missing or extraneous keys between the three files for the existing 339 keys.

### 3.3 Loan Words vs Placeholder Text Analysis
Comparing values between `de.json` and `en.json` / `sv.json`:
- **25 keys in EN** share identical strings with DE. All are legitimate technical terms, proper nouns, or universal abbreviations:
  - `table_columns.case_id` ("ID ⇅"), `table_columns.score` ("Score ⇅")
  - `handover_channels.GitLab Issue` ("GitLab Issue"), `internal_task_categories.Bugfix` ("Bugfix")
  - `profile.wiki_url` ("BookStack API URL:"), `profile.wiki_token_id` ("API Token ID:")
  - `actors.support_team` ("Support / Hotline"), `common.ok` ("OK"), `common.info` ("Information")
  - Help categories: "Workflow", "Export", "Wiki", "Sync".
- **23 keys in SV** share identical strings with DE. All are legitimate technical terms or proper loan words:
  - `departments.Support` ("Support / Hotline"), `internal_task_categories.Dokumentation` ("Dokumentation")
  - `table_columns.case_id` ("ID ⇅"), `profile.mobile` ("Mobilnummer:")
  - `splash.title` ("🩺 Support-Cockpit"), `help_content.storage_paths.category` ("Konfiguration")
- **Assessment:** Existing keys have natural, accurate translations without raw German placeholders.

---

## 4. Key Coverage & Parity Gaps Analysis

While `locales/*.json` has 339 keys, an AST scan across `src/` revealed that developers wrote **477 `tr(...)` calls**, of which **241 calls reference keys that are NOT in `locales/de.json`**!

Because these keys are missing from `de.json`, `en.json`, and `sv.json`, the application always falls back to the `default` argument in the code (which is written in German). As a result, switching to English or Swedish leaves dozens of dialogs in German!

### Namespace Breakdown of Missing Keys:

| Namespace | Missing Keys | Files Involved | Examples of Missing Keys & Fallback |
| :--- | :---: | :--- | :--- |
| `tag_mgmt` | **17** | `tag_management_dialog.py` | `tag_mgmt.tab_tags`, `tag_mgmt.add_tag_btn`, `tag_mgmt.search_tags_placeholder`, `tag_mgmt.tag_added` |
| `dynamic_form` | **14** | `dynamic_form_widget.py`, `dynamic_form_field_renderers.py` | `dynamic_form.search_tags`, `dynamic_form.apply_close`, `dynamic_form.no_tags`, `dynamic_form.add_card` |
| `handover_dialog` | **13** | `handover_dialog.py` | `handover_dialog.header_suffix`, `handover_dialog.person_placeholder`, `handover_dialog.no_colleagues` |
| `email_draft` | **12** | `email_draft_dialog.py` | `email_draft.ai_generating`, `email_draft.copied_to_clipboard`, `email_draft.subject_label` |
| `profile` | **11** | `profile_settings_dialog.py`, `profile_settings_ai_tab.py` | `profile.gemini_modelfile_rules`, `profile.provider_gemini`, `profile.checking_ollama` |
| `colleague_mgmt` | **11** | `colleague_management_dialog.py` | `colleague_mgmt.username`, `colleague_mgmt.new_colleague_btn`, `colleague_mgmt.header` |
| `customer_mgmt` | **11** | `customer_management_dialog.py` | `customer_mgmt.missing_id_name`, `customer_mgmt.cobra_import_btn`, `customer_mgmt.search_placeholder` |
| `new_case_dialog` | **11** | `new_case_dialog.py` | `new_case_dialog.is_internal`, `new_case_dialog.customer`, `new_case_dialog.header` |
| `snippet_mgmt` | **10** | `snippet_management_dialog.py` | `snippet_mgmt.tags_lbl`, `snippet_mgmt.no_snippets`, `snippet_mgmt.cat_lbl` |
| `schema_builder` | **9** | `schema_builder_dialog.py` | `schema_builder.label_ph`, `schema_builder.add_btn`, `schema_builder.field_id_ph` |
| `export_dialog` | **8** | `export_dialog.py` | `export_dialog.copy_btn`, `export_dialog.save_file_btn`, `export_dialog.select_template` |
| `zip_import` | **8** | `zip_import_dialog.py` | `zip_import.select_mode`, `zip_import.unpack_btn`, `zip_import.root_folder_btn` |
| `attachments` | **7** | `attachment_widget.py` | `attachments.open_explorer`, `attachments.no_case`, `attachments.add_file` |
| `p2p` | **7** | `p2p_diff_dialog.py` | `p2p.select_colleague`, `p2p.no_colleagues_cfg`, `p2p.no_diff_cases` |
| `wiki` | **7** | `wiki_widget.py` | `wiki.search_placeholder`, `wiki.header`, `wiki.sync_btn` |
| `new_case` | **6** | `new_case_dialog.py` | `new_case.future_date`, `new_case.tag_input_title`, `new_case.tag_input_prompt` |
| `quick_customer` | **6** | `new_case_dialog.py` | `quick_customer.err_name`, `quick_customer.header`, `quick_customer.phone` |
| `common` | **4** | multiple dialogs | `common.delete`, `common.open`, `common.browse`, `common.refresh` |
| `export` | **5** | `export_dialog.py` | `export.copied`, `export.no_template`, `export.missing_fields_hdr` |
| `followup` | **5** | `followup_dialog.py`, `followup_flyout_dialog.py` | `followup.date_lbl`, `followup.presets_lbl`, `followup.no_due_cases` |
| `convert_schema` | **4** | `convert_schema_dialog.py` | `convert_schema.header`, `convert_schema.select_target`, `convert_schema.already_used` |
| `email_import` | **4** | `email_import_dialog.py` | `email_import.no_emails`, `email_import.info_msg`, `email_import.fetching` |
| `template_mgmt` | **4** | `template_manager_dialog.py` | `template_mgmt.header`, `template_mgmt.load_defaults`, `template_mgmt.no_templates` |
| `snippet_picker` | **3** | `snippet_picker_dialog.py` | `snippet_picker.preview`, `snippet_picker.no_snippets`, `snippet_picker.search` |
| `cockpit` | **3** | `cockpit_view.py`, `cockpit_layout_builders.py` | `cockpit.followup_at`, `cockpit.email_copied_title`, `cockpit.no_email_title` |
| `case_list` | **3** | `case_list_widget.py` | `case_list.completed_badge`, `case_list.no_cases`, `case_list.zero_cases` |
| `email_calendar` | **2** | `email_calendar_dialog.py` | `email_calendar.client_opened`, `email_calendar.text_copied` |
| `board` | **2** | `board_view.py` | `board.cockpit_btn`, `board.collapse_btn` |
| `table` | **2** | `table_view.py` | `table.details_header`, `table.save_btn` |
| `date_picker` | **2** | `date_picker.py` | `date_picker.time_lbl`, `date_picker.o_clock` |
| `searchable_combo`| **2** | `searchable_combobox.py` | `searchable_combo.placeholder`, `searchable_combo.no_results` |
| `help_dialog` | **1** | `help_dialog.py` | `help_dialog.no_topics` |
| `analytics` | **1** | `analytics_view.py` | `analytics.copied_title` |
| `form` | **1** | `dynamic_form_widget.py` | `form.no_fields` |
| `timeline` | **1** | `timeline_widget.py` | `timeline.no_notes` |
| `toast` | **1** | `toast_notification.py` | `toast.reminder_title` |

---

## 5. Unextracted Hardcoded UI & System Strings

An AST scan across all Python files in `src/` revealed **238 occurrences in 29 files** where raw German string literals are passed directly to UI widgets, dialog titles, toasts, and placeholders without any localization call.

### High-Priority Files for String Extraction:

#### 1. `src/ui/dialogs/customer_form_builders.py` (57 unextracted strings)
- Section headers: `"🏥 Stammdaten & Praxisinformationen"`, `"👤 Ansprechpartner & Kontaktdaten"`, `"⚙ Technische Details & PVS"`, `"📋 Spezifische Praxis-Regeln für KI"`.
- Form labels: `"Praxisname *:"`, `"Kundennummer / BSNR *:"`, `"Hauptansprechpartner:"`, `"Telefon (Zentrale):"`, `"E-Mail (Praxis):"`, `"PVS-System:"`, `"Server-IP / Host:"`.
- Combobox sorting options (L70): `values=["Name (A-Z)", "Name (Z-A)", "Praxisnummer / ID", "Zeit seit letztem Kontakt ↑", "Zeit seit letztem Kontakt ↓"]`.

#### 2. `src/ui/dialogs/schema_builder_dialog.py` (20 unextracted strings)
- Dialog titles: `self.title("🆕 Neues Formular (Schema) erstellen")` (L13), `self.title("In-App Formular-Baukasten (Schemata verwalten)")` (L82).
- Action buttons & labels: `"➕ Neues Formular erstellen"`, `"Feld-Eigenschaften"`, `"Pflichtfeld (*)"`, `"Auswahloptionen (kommagetrennt)"`.

#### 3. `src/ui/dialogs/profile_settings_dialog.py` (19 unextracted strings)
- Hotkey recorder strings: `HOTKEY_RECORDER_TITLE` ("⌨ Hotkey aufnehmen"), `HOTKEY_RECORDER_HEADER` ("⌨ Tastenkombination drücken"), `HOTKEY_RECORDER_INFO` ("Drücken Sie Ihre Tasten (z.B. Strg+S, Alt+1)..."), `HOTKEY_RECORDER_CANCEL` ("Abbrechen (Esc)").
- Section headers: `"⚡ App-Aktionen Tastenkürzel (Hotkeys)"`, `"📝 Textbaustein-Makros (Snippet Shortcuts)"`, `"📊 Priorisierungs- & Dringlichkeits-Scoring Matrix"`.

#### 4. `src/ui/dialogs/ai_assistant_dialog.py` (14 unextracted strings)
- UI buttons & labels: `"🤖 KI-Zusammenfassung generieren"`, `"💡 Lösungsansätze suchen"`, `"✉ Antwort-Entwurf erstellen"`, `"📌 In Zeitleiste"`, `"📋 Kopieren"`.
- Instructions & warnings: `"⚡ Priorisierte KI-Sonderanweisung:"`, `"⚠ KI global deaktiviert (Schalter oben rechts auf OFF)."`.

#### 5. `src/ui/dialogs/cobra_import_dialog.py` (13 unextracted strings)
- Buttons & labels: `"📁 Datei wählen (CSV, TXT, JSON)..."`, `"🔄 Spalten-Mapping aktualisieren"`, `"🐍 Praxen importieren"`, `"Gefundene Spalten"`.

#### 6. `src/ui/dialogs/customer_management_dialog.py` (13 unextracted strings)
- Buttons: `"+ Neue Praxis"`, `"🗑 Praxis löschen"`, `"💾 Änderungen speichern"`, `"Cobra CRM Import"`.
- Table columns: `("id", "Kdnr / ID")`, `("name", "Praxisname")`, `("contact", "Ansprechpartner")`, `("vip", "VIP")`.

#### 7. `src/ui/dialogs/template_manager_dialog.py` (13 unextracted strings)
- Dialog titles: `self.title('✏ Vorlage bearbeiten' if not is_new else '➕ Neue Export-Vorlage')` (L29), `self.title('📄 Export-Vorlagen verwalten')` (L216).
- Buttons: `"➕ Neue Vorlage"`, `"👁 Live-Vorschau rendern"`, `"💾 Vorlage Speichern"`.

#### 8. `src/ui/dialogs/colleague_management_dialog.py` (10 unextracted strings)
- Table headers: `("user", "Kürzel")`, `("name", "Name")`, `("dept", "Abteilung")`, `("phone", "Telefon")`.
- Placeholders: `"z. B. Max Mustermann"`, `"z. B. mmustermann"`, `"z. B. 0731 12345-67"`.

#### 9. `src/ui/dialogs/case_print_dialog.py` (9 unextracted strings)
- Title: `self.title(f'🖨 Fall-Akte Druck- & HTML Export: {case.case_id}')` (L22).
- Checkboxes: `"Stammdaten & Praxisinformationen einschließen"`, `"Formularfelder & Falldetails einschließen"`, `"Zeitleiste & Verlaufsnotizen einschließen"`, `"Bildanhänge & Screenshots am Dokumentende einbetten"`.
- Buttons: `"🖨 Im Browser öffnen & Drucken"`, `"💾 Als HTML/PDF-Bericht speichern..."`.

#### 10. `src/ui/widgets/date_picker.py` (Calendar Dialog)
- Title: `self.title("📅 Datum auswählen")` (L23).
- Weekdays: `["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]` (L103).
- Month names: `["", "Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]` (L271-273).
- Quick presets: `[("Heute 11:30", ...), ("Heute 13:30", ...), ("Heute 16:30", ...), ("Morgen 08:00", ...), ("+ 1 Tag", ...), ("+ 1 Woche", ...)]` (L224-231).

#### 11. `src/ui/views/table_view.py`
- Tabview tabs: `tab_form = self.detail_tabview.add("📝 Formular & Ausfüllen")`, `tab_timeline = self.detail_tabview.add("🕒 Zeitleiste")`, `tab_attachments = self.detail_tabview.add("📎 Anhänge")` (L157-159).
- Dynamic details title label: `f"📋 Falldetails: {case.case_id} - ..."` (L302).

#### 12. `src/ui/views/board_view.py`
- Column count headers in `refresh_board`: `f"📥 Support ({len(...)})"`, `f"💻 Entwickler ({len(...)})"`, `f"🔔 Wiedervorlage ({len(...)})"`, `f"✓ Erledigt ({len(...)})"` (L314-317).

#### 13. `src/ui/views/analytics_view.py`
- Time formatting: `f"{avg_days:.1f} Tage"`, `f"{avg_hrs:.1f} Std"` (L93, 96).
- Scoring breakdown: `"🔴 Rot (Kritisch)"`, `"🟡 Gelb (Mittel)"`, `"🟢 Grün (Normal)"` (L141-143).
- Markdown report generator: `generate_report_markdown()` hardcoded in German (L239-259).
- Toast notification message: `message="Statistik-Bericht wurde in die Zwischenablage kopiert."` (L272).

---

## 6. Constants, Enums & Seed Data Localization Audit

### 6.1 `src/constants.py`
1. **`DISPLAY_BOARD_COLUMN_NAMES` (`src/constants.py:45-51`):**
   ```python
   DISPLAY_BOARD_COLUMN_NAMES = {
       "NEW": "Neu",
       "ACTION_REQUIRED": "Aktion erforderlich",
       "WAITING": "Warten auf zuständige Stelle",
       "IN_PROGRESS": "In Bearbeitung",
       "DONE": "Erledigt",
   }
   ```
   *Action:* Wrap in `LocalizedDict("board_columns", ...)` or localize via `get_board_column_display()`.

2. **`DISPLAY_CHANNEL_NAMES` (`src/constants.py:13-23`):**
   Only 3 channels are mapped in `enums.py:get_channel_display()`. Missing channels: `PHONE_OUTBOUND`, `EMAIL_IN`, `EMAIL_OUT`, `GITLAB_TICKET_CREATED`, `GITLAB_TICKET_UPDATED`, `GITLAB_TICKET_CLOSED`, `OTHER`.

3. **`DISPLAY_ACTOR_NAMES` (`src/constants.py:25-36`):**
   `DATA_*` variants (`DATA_SUPPORT`, `DATA_HOTLINE`, `DATA_DEVELOPMENT`, `DATA_TECH`, `DATA_CUSTOMER`) are not mapped in `enums.py:get_actor_display()`.

4. **`VALIDATION_MESSAGES` (`src/constants.py:191-210`):**
   Contains mixed English and German validation messages. Wrap in `LocalizedDict("validation", ...)`.

5. **`DEFAULT_TAGS` and `DEFAULT_MODULE_TAGS` (`src/constants.py:397-443`):**
   Contains 21 tags and 22 module tags in German. Provide localized helper functions `get_localized_default_tags()` and `get_localized_default_module_tags()`.

6. **`HOTKEY_ACTION_LABELS` (`src/constants.py:571-585`):**
   Hardcoded German action labels for hotkey preferences. Localize via `get_localized_hotkey_action_labels()`.

7. **`AI_STATUS_*`, `AI_BADGE_*`, `AI_BTN_*`, `AI_LABEL_*`, `AI_HINT_*` (`src/constants.py:284-374`):**
   Over 30 AI status, badge, and button string constants are raw German. Localize with `tr(...)`.

---

### 6.2 `src/enums.py`
- `get_board_column_display(val: str) -> str` (`src/enums.py:107-109`):
  Currently returns `BOARD_COLUMN_DISPLAY.get(val, val)` without calling `tr(...)`.
  *Fix:* Map to `tr(f"board_columns.{val}", default=BOARD_COLUMN_DISPLAY.get(val, val))`.
- Complete mapping table in `get_channel_display` and `get_actor_display`.

---

### 6.3 Seed Data & System Templates
1. **`src/services/seed_case_data.py`:**
   - Cases 1-5 use `tr("demo_cases.c1_title", ...)` up to `c5_title`.
   - Cases 6-10 (`T-2026-0006` to `T-2026-0010`) have hardcoded German titles (`"Alte Abrechnung Q1 gelöst"`, `"Uralter Fall aus dem Vormonat"`, etc.).
   - Timeline notes and form data values contain hardcoded German strings.
2. **`src/services/snippet_service.py`:**
   - `DEFAULT_SNIPPETS` has 8 default snippets with German titles, categories, and contents.
3. **`data_examples/question_schemas.json` and `data_examples/export_templates.json`:**
   - Default schemas and templates contain German titles, field labels, placeholders, and descriptions.

---

## 7. Dynamic Language Switching Architecture

### 7.1 Current Event Flow:
```
[User Selects Language in ProfileSettingsDialog]
               │
               ▼
   `on_language_selected(display_name)`
               │
               ▼
   `get_i18n().current_language = lang_code`
               │
               ▼
   `_notify_listeners()`
         ┌─────┴────────────────────────┐
         ▼                              ▼
 `app.on_language_changed`    `ProfileSettingsDialog.refresh_ui_labels`
         │
 ┌───────┴────────────────────────┐
 ▼                                ▼
`create_menu_bar()`     `cockpit_view.refresh_ui_labels()`
```

### 7.2 Identified Architectural Gaps:
1. **Views Not Notified:** `BoardView`, `TableView`, and `AnalyticsView` do not subscribe to `get_i18n()` and have no `refresh_ui_labels()` implementation.
2. **Sub-Widgets in Views:**
   - In `BoardView`, column headers and card action buttons are rendered with the language at creation time.
   - In `TableView`, ttk.Treeview column headings (`self.tree.heading(...)`) and tabview labels are static.
   - In `AnalyticsView`, KPI card titles and breakdown labels are static.
3. **Dropdown Options:** `stammdaten_combo`, `vorlagen_combo`, `datenaustausch_combo`, `layout_combo` are rebuilt in `app.create_menu_bar()`, which works well, but option mapping handlers (`_on_stammdaten_selected`, etc.) must handle matches in all languages.

### 7.3 Recommended Dynamic Switching Pattern:
1. **Standardize `refresh_ui_labels(self)` on All Views & Widgets:**
   Implement `refresh_ui_labels(self)` across `BoardView`, `TableView`, `AnalyticsView`, `DynamicFormWidget`, `TimelineWidget`, `AttachmentWidget`, `WikiWidget`, `CaseListWidget`.
2. **Dispatch Event in `app.on_language_changed`:**
   ```python
   def on_language_changed(self, lang_code: str):
       self.create_menu_bar()
       for view_name in ("cockpit_view", "board_view", "table_view", "analytics_view"):
           view = getattr(self, view_name, None)
           if view and hasattr(view, "refresh_ui_labels"):
               view.refresh_ui_labels()
   ```
3. **Dynamic Re-render of Dynamic Strings:**
   - In `BoardView.refresh_board()`, format column titles using `tr("board.col_support", ...)` and localized number templates.
   - In `TableView.refresh_ui_labels()`, update tree headings via `self.configure_tree_columns()` and update tab names.
   - In `AnalyticsView.refresh_ui_labels()`, re-render KPI headers and charts.

---

## 8. Implementation Roadmap for Implementation Agents

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. EXTRACT & SYNC ALL LOCALE KEYS (locales/de.json, en.json, sv.json)       │
│    - Add the 241 missing tr(...) keys to de.json, en.json, sv.json          │
│    - Add newly extracted keys for hardcoded strings to de.json, en.json, sv │
│    - Maintain 100% key parity and high-quality translations                 │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│ 2. REFACTOR CONSTANTS & ENUMS (src/constants.py, src/enums.py)              │
│    - Localize DISPLAY_BOARD_COLUMN_NAMES, VALIDATION_MESSAGES, HOTKEY_*     │
│    - Update get_board_column_display(), get_channel_display()               │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│ 3. EXTRACT HARDCODED UI STRINGS IN src/ui/                                  │
│    - Dialogs: customer_form_builders, schema_builder, ai_assistant, etc.   │
│    - Views: board_view, table_view, analytics_view                          │
│    - Widgets: date_picker, toast_notification, searchable_combobox          │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│ 4. COMPLETE DYNAMIC LANGUAGE SWITCHING ENGINE                               │
│    - Implement refresh_ui_labels() in BoardView, TableView, AnalyticsView   │
│    - Wire app.on_language_changed to all views and active widgets           │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│ 5. VERIFICATION & TEST INTEGRITY                                            │
│    - Run automated key parity validator (100% match)                        │
│    - Run AST scan to verify 0 hardcoded text literals remain                │
│    - Run full pytest test suite (.venv\Scripts\python.exe -m pytest)        │
└─────────────────────────────────────────────────────────────────────────────┘
```
