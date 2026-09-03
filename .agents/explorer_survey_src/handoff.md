# Handoff Report — Explorer Survey `src/`

## 1. Observation

1. **Codebase Scope & Structure**:
   - Total files surveyed: 83 Python files across 8 directories (`src/models`, `src/services`, `src/ui/core`, `src/ui/views`, `src/ui/widgets`, `src/ui/dialogs`, `src/utils`, and root module files `constants.py`, `enums.py`, `config.py`).
   - UI Architecture: CustomTkinter (`ctk.CTk`, `ctk.CTkToplevel`, `ctk.CTkFrame`) with native Tkinter components (`tk.PanedWindow`, `ttk.Treeview`).

2. **Hardcoded UI & System Strings**:
   - Total detected hardcoded UI widget literals: 213 items across dialogs, views, widgets, and core app files (cataloged in `c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up\.agents\explorer_survey_src\ui_inventory.json`).
   - Highest concentration in `ui/dialogs/customer_form_builders.py` (55 items), `ui/dialogs/schema_builder_dialog.py` (19 items), `ui/dialogs/profile_settings_dialog.py` (19 items), `ui/dialogs/template_manager_dialog.py` (13 items), `ui/dialogs/cobra_import_dialog.py` (12 items), `ui/dialogs/customer_management_dialog.py` (12 items), `ui/dialogs/ai_assistant_dialog.py` (11 items).
   - In `constants.py`: `DISPLAY_BOARD_COLUMN_NAMES`, `VALIDATION_MESSAGES`, `HOTKEY_ACTION_LABELS`, `HOTKEY_RECORDER_*`, `AI_STATUS_*`, `AI_BADGE_*`, `AI_BTN_*`, `AI_LABEL_*`, `AI_HINT_*`, `DEFAULT_TAGS`, `DEFAULT_MODULE_TAGS` contain untranslated German strings.
   - In `utils/datetime_utils.py`: `get_relative_date_text()` (L125-150) contains German strings `"heute"`, `"morgen"`, `"übermorgen"`, `"gestern"`, `"vorgestern"`, `"diese Woche"`, `"nächste Woche"`, `"letzte Woche"`, `"in {diff_days} Tagen"`, `"vor {abs(diff_days)} Tagen"`. `format_german_time` and `format_german_datetime` append hardcoded `" Uhr"`.
   - In `services/seed_case_data.py`, `services/seed_service.py`, `services/snippet_service.py`: default schemas, default templates, default snippets, and demonstration cases have hardcoded German titles, notes, and categories.

3. **Current Locale Parity Status**:
   - Existing keys in `locales/de.json`, `locales/en.json`, `locales/sv.json`: exactly 339 flattened keys in each file (100% key parity on existing keys).
   - 22 Swedish values and 24 English values in existing locale files retain German placeholder words (e.g. `departments.management: "Geschäftsführung"`, `internal_task_categories.maintenance: "Fernwartung"`).

4. **Dynamic Language Switching Support**:
   - Only 8 out of 51 UI classes implement `refresh_ui_labels` or language listeners.
   - `SupportCockpitApp.on_language_changed(lang_code)` (in `src/ui/app.py:240-244`) currently calls `self.create_menu_bar()` and `self.cockpit_view.refresh_ui_labels()`, but does NOT notify `self.board_view`, `self.table_view`, or `self.analytics_view`.

5. **Test Suite Baseline**:
   - Executed `.venv\Scripts\python.exe -m pytest tests/test_i18n_service.py -v`: 5 passed in 0.27s.

---

## 2. Logic Chain

1. **From Observation 1 & 2**:
   - The application relies on `tr(...)` from `src/services/i18n_service.py` and `LocalizedDict` from `src/constants.py`.
   - However, numerous UI widgets and dialogs were authored with direct string literals or static German lists, bypassing `tr(...)`.
   - Therefore, to achieve full translation coverage across English and Swedish, all 213 UI element literals, 100+ constant definitions, and date utility strings must be extracted and replaced with `tr(...)` or `LocalizedDict`.

2. **From Observation 3**:
   - While existing translation keys match 1:1:1 across `de.json`, `en.json`, and `sv.json`, newly extracted strings must be added to all three files with natural English and Swedish translations.
   - Existing German leftovers in `en.json` and `sv.json` must simultaneously be corrected to ensure natural translations.

3. **From Observation 4**:
   - Because CustomTkinter widgets retain their configured text unless explicitly re-configured, switching language at runtime without an application restart requires every view and widget to provide a `refresh_ui_labels()` method.
   - `SupportCockpitApp.on_language_changed()` must broadcast the change to all four main views (`CockpitView`, `BoardView`, `TableView`, `AnalyticsView`), and each view must cascade the refresh to its child widgets (`CaseListWidget`, `TimelineWidget`, `AttachmentWidget`, `WikiWidget`, `DynamicFormWidget`, `DatePickerWidget`, etc.).

---

## 3. Caveats

- **External Data Files**: Existing persisted SQLite databases or user-created cases in `data/cases/*.json` contain user-authored strings in whatever language they were originally typed. Localization applies to application UI, schemas, templates, default snippets, and system strings, not user-submitted past case text.
- **Third-Party Integrations**: AI prompts sent to Ollama or Gemini default to German system instructions in `constants.py`. If multi-language AI prompting is desired, system prompt templates should also be retrieved via `tr()`.
- **No Other Caveats**: All 83 source code files in `src/` were parsed and inspected with AST analysis.

---

## 4. Conclusion

- A total of ~120 new translation keys need to be added to `locales/de.json`, `locales/en.json`, and `locales/sv.json` to cover all 213 hardcoded UI literals and constant definitions.
- `constants.py`, `enums.py`, and `datetime_utils.py` must be updated to use `LocalizedDict` and `tr(...)`.
- `BoardView`, `TableView`, `AnalyticsView`, and child widgets must implement `refresh_ui_labels()`, and `SupportCockpitApp.on_language_changed()` must be updated to orchestrate a complete UI re-translation.
- Full details and line-by-line catalogs are documented in `report.md` and `ui_inventory.json`.

---

## 5. Verification Method

1. **Automated AST Hardcoded String Scan**:
   ```powershell
   .venv\Scripts\python.exe .agents\explorer_survey_src\full_inventory_generator.py
   ```
   *Expected outcome after implementation*: 0 hardcoded user-visible text literals.

2. **Locale Parity Check**:
   ```powershell
   .venv\Scripts\python.exe .agents\explorer_survey_src\locale_audit.py
   ```
   *Expected outcome*: 100% key parity across `de.json`, `en.json`, and `sv.json`, with 0 missing keys.

3. **Unit & Integration Test Execution**:
   ```powershell
   .venv\Scripts\python.exe -m pytest tests/test_i18n_service.py -v
   .venv\Scripts\python.exe -m pytest
   ```
   *Expected outcome*: All tests pass cleanly.
