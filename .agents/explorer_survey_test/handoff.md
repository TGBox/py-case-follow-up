# Handoff Report — Test Infrastructure, Verification Mechanisms & AST Scanning Survey

**Agent**: Explorer Survey Test Agent  
**Working Directory**: `c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up\.agents\explorer_survey_test`  
**Date**: 2026-09-02  
**Handoff Type**: Hard (Task Complete)

---

## 1. Observation

### 1.1 Existing Test Suite Status
- Command executed: `.venv\Scripts\python.exe -m pytest`
- Environment: Python 3.14.7 (win32), pytest-9.1.1, pluggy-1.6.0.
- Result: `335 passed in 123.80s (0:02:03)`.
- Total test files: 75 files in `tests/`.
- Test isolation: `tests/conftest.py:12-18` sets fixture `isolate_global_supportcockpit_config` ensuring `%APPDATA%` user configurations are never modified during test runs.
- Headless GUI testing pattern: `tests/test_dialogs_comprehensive.py:20-34` uses `ctk.CTk()` with `.withdraw()` and `.update_idletasks()`.

### 1.2 Locale Files & Parity
- Files observed:
  - `locales/de.json` (41,420 bytes, 339 leaf keys)
  - `locales/en.json` (36,852 bytes, 339 leaf keys)
  - `locales/sv.json` (30,545 bytes, 339 leaf keys)
- Top-level sections (28 sections): `actors`, `analytics`, `board`, `calendar_export`, `channels`, `cobra_import`, `cockpit`, `common`, `convert_schema`, `demo_cases`, `departments`, `dialog_headers`, `dialog_titles`, `email_calendar`, `email_draft`, `handover_channels`, `help_content`, `help_dialog`, `internal_task_categories`, `layouts`, `menu`, `profile`, `snippet_picker`, `splash`, `status_messages`, `table_columns`, `template_editor`, `ui_buttons`.
- Format parameter check: 0 `{...}` parameter mismatches across current keys.
- Discrepancy observed: In `locales/sv.json`, section `help_content` is significantly condensed (15,741 bytes in `sv.json` vs 26,248 bytes in `de.json`).

### 1.3 AST Scanner for Hardcoded UI Literals
- AST scan over all `.py` files in `src/` identified **221 candidate hardcoded user-visible text literals** across **27 files**:
  - `src/ui/dialogs/customer_form_builders.py`: 51 literals (e.g. L80 `text="↑ Aufst."`, L143 `text="Praxisname (Alt):"`, placeholders).
  - `src/ui/dialogs/profile_settings_dialog.py`: 18 literals (e.g. L253 `placeholder_text="z. B. Support, Entwicklung, Technik"`).
  - `src/ui/dialogs/schema_builder_dialog.py`: 18 literals (e.g. L24 `text="Neues Formular-Schema definieren"`, L26 `text="Anzeigename (Titel) *:"`).
  - `src/ui/dialogs/ai_assistant_dialog.py`: 14 literals (e.g. L125 `text="Prüfe Status..."`, L173 `text="Schließen"`).
  - `src/ui/dialogs/customer_management_dialog.py`: 13 literals (e.g. L46 `text="⚠ Keine Webseite eingetragen!"`, L79 `text="🗑 Entfernen"`).
  - `src/ui/dialogs/template_manager_dialog.py`: 12 literals (e.g. L57 `text="Vorlage-ID *:"`, L68 `text="Anzeigename *:"`).
  - `src/ui/dialogs/cobra_import_dialog.py`: 10 literals (e.g. L53 `text="1. Cobra Export-Datei auswählen:"`, L61 `text="📁 Durchsuchen..."`).
  - `src/ui/dialogs/colleague_management_dialog.py`: 10 literals (e.g. L104 `placeholder_text="z. B. Max Müller"`).
  - `src/ui/dialogs/case_print_dialog.py`: 9 literals (e.g. L54 `text="Praxis & Kundendaten"`, L55 `text="Formularfelder"`).
  - `src/ui/dialogs/email_calendar_dialog.py`: 7 literals (e.g. L71 `text="Empfänger (E-Mail):"`, L78 `text="Betreff:"`).
  - `src/ui/dialogs/email_draft_dialog.py`: 7 literals (e.g. L149 `text="Prüfe KI-Status..."`, L192 `text="📇 Praxiskartei ▾"`).
  - `src/ui/dialogs/followup_flyout_dialog.py`: 6 literals (e.g. L84 `text="+ 1 Std."`, L94 `text="Morgen 08:00"`).
  - `src/ui/dialogs/new_case_dialog.py`: 6 literals (e.g. L32 `placeholder_text="z.B. Praxis Dr. Weber"`).
  - `src/ui/dialogs/profile_settings_ai_tab.py`: 4 literals (e.g. L478 `text="⚠ Bitte API Key eingeben"`).
  - `src/ui/dialogs/snippet_management_dialog.py`: 4 literals (e.g. L70 `placeholder_text="z. B. 📸 Rückfrage: Screenshots"`).
  - `src/ui/dialogs/zip_import_dialog.py`: 3 literals (filedialog titles).
  - `src/ui/dialogs/calendar_export_dialog.py`: 2 literals (filedialog title and label).
  - `src/ui/dialogs/email_import_dialog.py`: 2 literals (e.g. L210 `text="➕ Als neuen Fall anlegen"`).
  - `src/ui/dialogs/followup_dialog.py`: 2 literals (date picker & entry placeholder).
  - `src/ui/views/analytics_view.py`: 1 literal (L272 toast message).
  - `src/ui/views/cockpit_layout_builders.py`: 1 literal (L156 `text="🔔 Nachfragen am:"`).
  - `src/ui/views/cockpit_view.py`: 1 literal (L334 toast message).
  - `src/ui/widgets/case_list_widget.py`: 1 literal (L295 `text="🔔 Nachfragen am:"`).
  - `src/ui/widgets/dynamic_form_widget.py`: 1 literal (L532 filedialog title).
  - `src/ui/app.py`: 3 literals (notification counter `text="🔔 0"`, zip export filedialog title).
  - `src/services/seed_service.py`: 16 literals (default case titles/descriptions).
  - `src/services/snippet_service.py`: 8 literals (default snippet titles).

### 1.4 Constants & Enums Localization State
- In `src/constants.py:56-77`: `LocalizedDict` proxy class is implemented and used for `DIALOG_TITLES` and `DIALOG_HEADERS`.
- In `src/constants.py:13-51`: `DISPLAY_CHANNEL_NAMES`, `DISPLAY_ACTOR_NAMES`, `DISPLAY_LAYOUT_NAMES`, and `DISPLAY_BOARD_COLUMN_NAMES` are static standard dicts.
- In `src/enums.py:72-108`: `get_channel_display`, `get_actor_display`, and `get_layout_display` have incomplete key mappings. `get_board_column_display` uses `BOARD_COLUMN_DISPLAY.get(val, val)` which is static.

---

## 2. Logic Chain

1. **Test Infrastructure Baseline**:
   - `pytest` executes cleanly with 335/335 passing tests and robust config isolation (`tests/conftest.py`).
   - Headless GUI testing with `ctk.CTk().withdraw()` and `update_idletasks()` is established and reliable for verifying widgets without requiring an active physical display.

2. **Translation Verification Tooling**:
   - Currently, `locales/de.json`, `en.json`, and `sv.json` have 339 matching keys.
   - When the implementer extracts the 221+ discovered UI literals, new translation keys will be introduced.
   - A dedicated verification test (`tests/test_translation_parity_and_quality.py`) is required to automatically enforce: (a) 100% recursive key parity across `de`, `en`, `sv`; (b) placeholder token consistency (`{param}`); and (c) absence of untranslated German strings or placeholders in `en.json` and `sv.json`.

3. **AST Scanning for Zero Hardcoded Strings**:
   - The AST scanner prototype successfully identified 221 hardcoded literals in `src/`.
   - Implementing this scanner as a pytest suite (`tests/test_ast_i18n_scanner.py`) with explicit allowlist rules (colors, fonts, layout args, numbers, symbols, URLs, loggers, `tr(...)` calls) will guarantee that no raw strings remain in UI widgets.

4. **Dynamic Language Switching Integrity**:
   - Runtime language switching requires updating `src/constants.py` display dictionaries to `LocalizedDict` instances, completing key maps in `src/enums.py`, and ensuring UI components register and unregister `I18nService` callbacks.
   - Test suite `tests/test_dynamic_language_switch.py` will verify real-time UI text refresh across `de` -> `en` -> `sv` without app restart.

5. **E2E Multilingual Workflow Validation**:
   - Tiers 1-4 test architecture ensures comprehensive coverage from individual components and boundary cases to cross-feature interactions and real-world multi-step user workflows.

---

## 3. Caveats

- **Ollama / LLM Network Calls in Tests**: `test_ai_service_and_assistant.py` relies on connection refused exceptions or timeouts when local Ollama is offline; test suite execution remains clean (335 passed).
- **Swedish Help Content Detail**: The Swedish translations in `help_content` are valid Swedish, but shorter than the German originals. While functional, expanding them to full parity during extraction improves documentation quality.
- **Brand Names & Technical Identifiers**: Certain strings (e.g. "Cobra CRM", "GitLab Issue", "BookStack", "API Token ID", "SQL") are intentionally identical across all three locales.

---

## 4. Conclusion

The test infrastructure is stable, healthy (335 passing tests), and fully equipped for headless CustomTkinter verification.

### Actionable Plan for Next Phases:
1. **Extraction & Parity (Implementer)**:
   - Extract the 221 identified hardcoded UI strings across `src/ui/dialogs/`, `src/ui/views/`, `src/ui/widgets/`, `src/ui/app.py`, `src/constants.py`, and `src/services/` into `locales/de.json`, `locales/en.json`, and `locales/sv.json`.
   - Wrap `DISPLAY_BOARD_COLUMN_NAMES`, `DISPLAY_ACTOR_NAMES`, `DISPLAY_CHANNEL_NAMES`, and `DISPLAY_LAYOUT_NAMES` with `LocalizedDict` in `src/constants.py`.
   - Complete enum translation lookups in `src/enums.py`.
2. **Automated Verification Suites (Test Engineer)**:
   - Add `tests/test_translation_parity_and_quality.py` (100% key parity, format tokens, German placeholder detector).
   - Add `tests/test_ast_i18n_scanner.py` (AST scan over `src/` asserting 0 hardcoded UI strings).
   - Add `tests/test_dynamic_language_switch.py` (runtime switching lifecycle & UI refresh).
   - Add `tests/test_e2e_multilingual_workflows.py` (Tiers 1-4 E2E scenarios).

---

## 5. Verification Method

### 5.1 Run Test Suite
Execute the full pytest suite:
```powershell
.venv\Scripts\python.exe -m pytest
```
*Expected: 335 passed.*

### 5.2 Inspect Report Artifacts
Review the comprehensive findings and AST survey in:
- `c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up\.agents\explorer_survey_test\report.md`
- `c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up\.agents\explorer_survey_test\handoff.md`

### 5.3 Invalidation Conditions
- Any pytest failure or regressions in the existing 335 tests.
- Failure of AST scanner to detect hardcoded UI widget literals.
- Key parity mismatch where keys in `locales/de.json` do not exist in `en.json` or `sv.json`.
