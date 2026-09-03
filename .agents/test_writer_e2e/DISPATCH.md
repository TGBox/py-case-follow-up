## 2026-09-02T17:56:41Z
You are the E2E Test Writer for the internationalization and multi-language localization project.

Working directory: c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up\.agents\test_writer_e2e
Project Root: c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up
Mandatory: Read ORIGINAL_REQUEST.md at: c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up\.agents\ORIGINAL_REQUEST.md
Also read PROJECT.md and TEST_INFRA.md at project root, and the survey report at c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up\.agents\explorer_survey_test\report.md.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Files you own exclusively:
- `tests/test_translation_parity_and_quality.py`
- `tests/test_ast_i18n_scanner.py`
- `tests/test_dynamic_language_switch.py`
- `tests/test_e2e_multilingual_workflows.py`
- `TEST_READY.md` (at project root)

Tasks:
1. Implement `tests/test_translation_parity_and_quality.py`:
   - Enforce 100% recursive leaf key parity across `locales/de.json`, `locales/en.json`, and `locales/sv.json`.
   - Verify no empty or whitespace-only translation values.
   - Verify format placeholder tokens (e.g. `{case_id}`) match identically across all languages for every key.
   - Quality check: detect untranslated German text / stop words in `en.json` and `sv.json`.
2. Implement `tests/test_ast_i18n_scanner.py`:
   - Implement an AST visitor scanning all `.py` files in `src/` to verify that UI constructors (buttons, labels, checkboxes, entry placeholders, toasts, dialog titles, etc.) do NOT receive hardcoded user-visible text string literals directly without `tr(...)` or `LocalizedDict`.
   - Ensure proper exclusions for internal identifiers, geometry strings, regexes, color codes, file extensions, and logging.
3. Implement `tests/test_dynamic_language_switch.py`:
   - Test headless UI language switching across `I18nService.set_language(...)` and `SupportCockpitApp.on_language_changed(...)`.
   - Verify that views (`CockpitView`, `BoardView`, `TableView`, `AnalyticsView`), widgets, dialogs, menu items, table columns, and `constants.py` / `enums.py` dynamic values update without application restart.
4. Implement `tests/test_e2e_multilingual_workflows.py`:
   - End-to-end user workflows in German, English, and Swedish (Case creation, filtering, editing, template exporting, importing, dialog navigation).
5. Run the tests using `.venv\Scripts\python.exe -m pytest <test_file>` to verify your test implementations.
6. Create `TEST_READY.md` at project root summarizing all test tiers, test counts, and execution commands.
7. Write your handoff to `c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up\.agents\test_writer_e2e\handoff.md` and report back to parent.
