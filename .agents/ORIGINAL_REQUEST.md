# Original User Request

## 2026-09-02T17:50:16Z

<USER_REQUEST>
Translate all untranslated hardcoded strings across all application files into English and Swedish, ensuring all strings are extracted, synchronized across the locale files (locales/de.json, locales/en.json, locales/sv.json), and dynamically retrieved via the application's central translation service (	r(...)).

Working directory: c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up
Integrity mode: development

## Requirements

### R1. Translation Key Parity and Quality
Synchronize all translation keys across locales/de.json, locales/en.json, and locales/sv.json. Every key must be present in all three files with natural, accurate translations into English and Swedish (no raw German placeholders or untranslated texts).

### R2. UI and System String Extraction
Replace all hardcoded user-facing strings across all application files in src/ (including dialogs, views, widgets, menus, buttons, labels, tooltips, placeholders, toasts, file dialog titles, option values, table headers, default snippets, form schemas, and seed case datasets) with calls to the central translation function 	r(...) or localized data structures (LocalizedDict).

### R3. Dynamic Language Switching Support
Ensure that switching languages at runtime updates all UI components, dialogs, status messages, and options dynamically without requiring an application restart or leaving residual untranslated components.

## Acceptance Criteria

### Translation Parity
- [ ] Automated key parity check succeeds: 100% of keys in locales/de.json exist in locales/en.json and locales/sv.json, and vice versa.
- [ ] No non-English or untranslated strings exist in locales/en.json, and no non-Swedish or untranslated strings exist in locales/sv.json for all newly extracted and existing keys.

### String Extraction Verification
- [ ] An automated AST scan over all .py files in src/ verifies that no hardcoded user-visible text literals remain in UI widgets (buttons, labels, checkboxes, entry placeholders, toasts, file dialogs).
- [ ] All strings in constants.py (e.g. DISPLAY_BOARD_COLUMN_NAMES, shortcut labels, macro toasts) and enums.py are localized.

### Test Integrity
- [ ] All existing and new automated tests pass cleanly with .venv\Scripts\python.exe -m pytest.
</USER_REQUEST>
