# Dispatch Assignment

## 2026-09-02T17:50:42Z

You are the Project Orchestrator.
Working Directory: c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up\.agents\orchestrator_1
Project Root: c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up
Original Request: c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up\.agents\ORIGINAL_REQUEST.md

Mission:
Translate all untranslated hardcoded strings across all application files into English and Swedish, ensuring all strings are extracted, synchronized across the locale files (locales/de.json, locales/en.json, locales/sv.json), and dynamically retrieved via the application's central translation service (tr(...)).

Requirements:
1. R1. Translation Key Parity and Quality: Synchronize all translation keys across locales/de.json, locales/en.json, and locales/sv.json with natural, accurate translations.
2. R2. UI and System String Extraction: Replace hardcoded strings in src/ with tr(...) or LocalizedDict. Localize constants.py and enums.py.
3. R3. Dynamic Language Switching Support: Runtime language switching must update all UI components, dialogs, status messages, and options dynamically without application restart.
4. Acceptance Criteria: Key parity verification (100%), no non-English/non-Swedish untranslated strings in en.json/sv.json, automated AST scan verifying no hardcoded literals remain in UI widgets, and all tests passing with pytest.
