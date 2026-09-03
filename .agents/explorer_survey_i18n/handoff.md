# Handoff Report: i18n & Translation Infrastructure Survey

**Agent:** Explorer (i18n & Translation Infrastructure)  
**Date:** 2026-09-02  
**Working Directory:** `c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up\.agents\explorer_survey_i18n`  
**Target Report:** `c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up\.agents\explorer_survey_i18n\report.md`  

---

## 1. Observation

1. **Central Translation Service (`src/services/i18n_service.py`):**
   - Implements `I18nService` with `current_language` property, `load_all_translations()`, `register_listener(callback)`, `unregister_listener(callback)`, `_notify_listeners()`, and `tr(key, default=None, **kwargs)`.
   - Global singleton `get_i18n()` (`src/services/i18n_service.py:107-111`) and wrapper `tr(...)` (`src/services/i18n_service.py:114-115`).
   - Fallback hierarchy in `tr()` (`lines 78-84`): `current_language` $\rightarrow$ `"de"` $\rightarrow$ `default` $\rightarrow$ `key`.
   - Supported languages: `"de": "Deutsch"`, `"en": "English"`, `"sv": "Svenska"`.

2. **Dynamic Dictionary Localization Wrapper (`src/constants.py:56-76`):**
   - `LocalizedDict(dict)` automatically intercepts `__getitem__(key)` and `get(key, default)` and calls `tr(f"{self._prefix}.{key}", default=...)`.
   - Instances: `DIALOG_TITLES` (prefix `"dialog_titles"`), `DIALOG_HEADERS` (prefix `"dialog_headers"`), `UI_BUTTON_TEXTS` (prefix `"ui_buttons"`), `STATUS_MESSAGES` (prefix `"status_messages"`), `COL_TITLE_MAP` (prefix `"table_columns"`).

3. **Locale Files State (`locales/de.json`, `locales/en.json`, `locales/sv.json`):**
   - Each file contains exactly **339 keys** in 28 top-level sections.
   - Key parity between `de.json`, `en.json`, and `sv.json` for existing keys is **100%** (zero missing keys across the three files).
   - Analysis of identical values: 25 keys in EN and 23 keys in SV match DE strings. All are legitimate technical loan words or standard symbols (`ID ⇅`, `Score ⇅`, `GitLab Issue`, `Bugfix`, `BookStack API URL:`, `Support / Hotline`, `OK`, `Information`).

4. **Missing Key Coverage in `locales/*.json` (241 missing calls):**
   - An AST scan found **477 `tr(...)` invocations** across `src/`.
   - **241 `tr(...)` calls** reference keys that DO NOT EXIST in `locales/de.json` (nor in `en.json` or `sv.json`).
   - Top missing namespaces: `tag_mgmt` (17 keys), `dynamic_form` (14 keys), `handover_dialog` (13 keys), `email_draft` (12 keys), `colleague_mgmt` (11 keys), `customer_mgmt` (11 keys), `new_case_dialog` (11 keys), `profile` (11 keys), `snippet_mgmt` (10 keys), `schema_builder` (9 keys), `export_dialog` (8 keys), `zip_import` (8 keys), `attachments` (7 keys), `p2p` (7 keys), `wiki` (7 keys), `new_case` (6 keys), `quick_customer` (6 keys), `common` (4 keys), `export` (5 keys), `followup` (5 keys), `convert_schema` (4 keys), `email_import` (4 keys), `template_mgmt` (4 keys), `snippet_picker` (3 keys), `cockpit` (3 keys), `case_list` (3 keys), `email_calendar` (2 keys), `board` (2 keys), `table` (2 keys), `date_picker` (2 keys), `searchable_combo` (2 keys), `analytics` (1 key), `form` (1 key), `help_dialog` (1 key), `timeline` (1 key), `toast` (1 key).

5. **Hardcoded UI String Literals Without `tr(...)` (238 occurrences across 29 files):**
   - Top affected files:
     - `src/ui/dialogs/customer_form_builders.py`: 57 strings (section titles, labels, sort options).
     - `src/ui/dialogs/schema_builder_dialog.py`: 20 strings (titles, property headers, field options).
     - `src/ui/dialogs/profile_settings_dialog.py`: 19 strings (hotkey recorder strings, headers).
     - `src/ui/dialogs/ai_assistant_dialog.py`: 14 strings (action buttons, prompts, directives).
     - `src/ui/dialogs/cobra_import_dialog.py`: 13 strings (column mapping labels, buttons).
     - `src/ui/dialogs/customer_management_dialog.py`: 13 strings (table columns, action buttons).
     - `src/ui/dialogs/template_manager_dialog.py`: 13 strings (window titles, buttons).
     - `src/ui/dialogs/colleague_management_dialog.py`: 10 strings (table headers, placeholders).
     - `src/ui/dialogs/case_print_dialog.py`: 9 strings (window title, print checkboxes).
     - `src/services/snippet_service.py`: 8 default snippets with German text.
     - `src/services/seed_case_data.py`: cases 6-10 titles, form data, timeline notes.
     - `src/ui/widgets/date_picker.py`: weekdays (`Mo..So`), month names (`Januar..Dezember`), presets (`Heute 11:30`, `+ 1 Tag`).
     - `src/ui/views/table_view.py`: tab titles (`📝 Formular & Ausfüllen`, `🕒 Zeitleiste`, `📎 Anhänge`).
     - `src/ui/views/board_view.py`: column title formatting in `refresh_board()`.
     - `src/ui/views/analytics_view.py`: status breakdown labels, time units (`Tage`, `Std`), report markdown.

6. **Constants & Enums Needing Localization:**
   - `src/constants.py`: `DISPLAY_BOARD_COLUMN_NAMES`, `DISPLAY_CHANNEL_NAMES`, `DISPLAY_ACTOR_NAMES`, `VALIDATION_MESSAGES`, `DEFAULT_TAGS`, `DEFAULT_MODULE_TAGS`, `HOTKEY_ACTION_LABELS`, `HOTKEY_RECORDER_*`, `AI_STATUS_*`, `AI_LABEL_*`, `AI_BTN_*`.
   - `src/enums.py`: `get_board_column_display()` directly returns `BOARD_COLUMN_DISPLAY.get(val, val)` without calling `tr(...)`. Unmapped channel & actor codes.

7. **Dynamic Language Switching Infrastructure:**
   - Listener pattern is implemented in `I18nService` (`register_listener` / `_notify_listeners`).
   - `ProfileSettingsDialog.on_language_selected` (`src/ui/dialogs/profile_settings_dialog.py:333-338`) sets `get_i18n().current_language = lang_code`.
   - `app.py:on_language_changed` (`src/ui/app.py:240-244`) calls `self.create_menu_bar()` and `self.cockpit_view.refresh_ui_labels()`.
   - `BoardView`, `TableView`, `AnalyticsView`, and modal dialogs do NOT have `refresh_ui_labels()` or listener subscriptions.

---

## 2. Logic Chain

1. **Why English/Swedish Language Switching is Currently Incomplete:**
   - When a user switches to English or Swedish, `I18nService` looks up keys in `locales/en.json` or `locales/sv.json`.
   - For 241 `tr(...)` calls in the codebase, the key is missing from `en.json` and `sv.json`.
   - By fallback rule (Observation 1), `tr()` falls back to `default`, which was written in German.
   - Furthermore, for 238 UI string literals (Observation 5), no `tr(...)` call is made at all.
   - Therefore, a substantial portion of the UI remains in German regardless of the language setting.

2. **Why `BoardView`, `TableView`, and `AnalyticsView` Do Not Update Dynamically:**
   - Observation 7 shows that `app.on_language_changed` only invokes `create_menu_bar()` and `cockpit_view.refresh_ui_labels()`.
   - Neither `BoardView`, `TableView`, nor `AnalyticsView` implement `refresh_ui_labels()`.
   - `TableView` table column headings and tabview labels are generated at instantiation and not updated dynamically.
   - `BoardView` column counts and headings in `refresh_board()` use hardcoded German strings (`Entwickler`, `Wiedervorlage`, `Erledigt`).
   - Thus, switching languages dynamically does not re-translate other views without restarting the application.

3. **Why `LocalizedDict` is the Optimal Pattern for Dict Constants:**
   - `LocalizedDict` allows existing constant dict lookups (e.g. `DIALOG_TITLES["new_case"]`, `COL_TITLE_MAP["case_id"]`) to dynamically evaluate `tr()` at access time rather than at import time.
   - Applying `LocalizedDict` to `DISPLAY_BOARD_COLUMN_NAMES` and `VALIDATION_MESSAGES` ensures backward compatibility with dict interfaces while supporting instant runtime language switching.

---

## 3. Caveats

- **External Data Files (`data/*.json` vs `data_examples/*.json`):** User workspace files (`data/cases.json`, `data/customers.json`) contain persistent user data and should not be dynamically translated at runtime, but system example templates (`data_examples/question_schemas.json`, `data_examples/export_templates.json`) and seed cases should have localized definitions.
- **Tkinter/CustomTkinter Native Components:** `ttk.Treeview` headings and `ctk.CTkTabview` internal segmented button tabs require explicit re-configuration calls (`self.tree.heading(...)`, `tabview._segmented_button._buttons_dict[...]`) during `refresh_ui_labels()`.
- **Third-Party OS APIs:** Windows `winotify` toast notifications pass text strings to the OS notification center; ensuring localized titles and messages must happen at dispatch time in `ToastNotification`.

---

## 4. Conclusion

1. The existing i18n core architecture (`I18nService`, `LocalizedDict`, listener pattern) is well-designed and functional.
2. The primary deficiency is **content and integration coverage**:
   - 241 missing `tr(...)` keys must be added to `locales/de.json`, `locales/en.json`, and `locales/sv.json`.
   - 238 hardcoded UI string literals across 29 files must be extracted into `tr(...)` calls.
   - `constants.py` and `enums.py` need `LocalizedDict` and complete translation mapping.
   - `refresh_ui_labels()` must be implemented in `BoardView`, `TableView`, `AnalyticsView`, and hooked into `app.on_language_changed`.

---

## 5. Verification Method

1. **Locale Parity & Coverage Verification:**
   Run the automated key parity script:
   ```powershell
   .venv\Scripts\python.exe .agents/explorer_survey_i18n/audit_tr_keys.py
   ```
   *Expected output:* `Missing in locales/de.json: 0` and 100% key parity across `de.json`, `en.json`, and `sv.json`.

2. **AST Scan for Zero Hardcoded UI String Literals:**
   Run the AST scanner:
   ```powershell
   .venv\Scripts\python.exe .agents/explorer_survey_i18n/scan_script.py
   ```
   *Expected output:* `0 occurrences` of hardcoded user-visible text in UI widget calls.

3. **Pytest Test Suite:**
   Run full automated tests:
   ```powershell
   .venv\Scripts\python.exe -m pytest tests/test_i18n_service.py -v
   .venv\Scripts\python.exe -m pytest
   ```
   *Expected output:* All tests passing cleanly.
