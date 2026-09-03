# Project: Multi-Language Translation & Localization (DE, EN, SV)

## Architecture
SupportCockpit internationalization architecture:
- **Central Translation Service**: `src/services/i18n_service.py` (`I18nService`, `tr(key, default, **kwargs)`, `LocalizedDict`).
- **Locale Data**: `locales/de.json`, `locales/en.json`, `locales/sv.json`.
- **Dynamic Language Switching**: `I18nService.set_language(lang)` triggers registered callback listeners. `SupportCockpitApp.on_language_changed(new_lang)` cascades updates to all views, widgets, and dialogs via `refresh_ui_labels()`.
- **Constants & Enums**: `src/constants.py` and `src/enums.py` localized using `LocalizedDict` proxy objects that dynamically resolve against the active language.
- **UI Framework**: CustomTkinter (`ctk`) desktop UI with views (`src/ui/views/`), widgets (`src/ui/widgets/`), dialogs (`src/ui/dialogs/`), and app root (`src/ui/app.py`).

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Locale Key Parity | 100% mutual key parity across de.json, en.json, sv.json | M1 | ORIGINAL_REQUEST §R1 |
| 2 | High-Quality EN/SV Translations | Accurate, natural English and Swedish translations without German placeholders | M1 | ORIGINAL_REQUEST §R1 |
| 3 | Missing tr(...) Keys Extraction | All ~241 existing tr(...) keys added to all 3 locale files | M1 | Survey Finding |
| 4 | Constants & Enums Localization | LocalizedDict wrapping for DISPLAY_BOARD_COLUMN_NAMES, DISPLAY_ACTOR_NAMES, etc., and enums.py | M2 | ORIGINAL_REQUEST §R2 |
| 5 | DateTime Utils Localization | Localized relative date/time formatting ("heute", "morgen", "Uhr") | M2 | ORIGINAL_REQUEST §R2 |
| 6 | Seed Data & Snippets Localization | Default schemas, templates, snippets, and demo cases localized | M2 | ORIGINAL_REQUEST §R2 |
| 7 | UI Views & App Shell Extraction | Replace hardcoded literals in app.py and src/ui/views/ with tr(...) | M3 | ORIGINAL_REQUEST §R2 |
| 8 | UI Widgets Extraction | Replace hardcoded literals in src/ui/widgets/ with tr(...) | M3 | ORIGINAL_REQUEST §R2 |
| 9 | UI Dialogs Extraction | Replace all hardcoded literals across all 18 dialogs in src/ui/dialogs/ with tr(...) | M4 | ORIGINAL_REQUEST §R2 |
| 10 | Dynamic Language Switching | Cascade runtime language change to all views, widgets, dialogs via refresh_ui_labels | M5 | ORIGINAL_REQUEST §R3 |
| 11 | Key Parity Automated Tests | Automated pytest checking 100% key parity, token matches, and no German in EN/SV | E2E-Track | ORIGINAL_REQUEST §AC |
| 12 | AST Scanner Automated Tests | Automated AST scanner over src/ verifying no hardcoded UI literals | E2E-Track | ORIGINAL_REQUEST §AC |
| 13 | Dynamic Switching Automated Tests | Automated test verifying dynamic UI & constant updates upon language switch | E2E-Track | ORIGINAL_REQUEST §AC |
| 14 | E2E Multilingual Workflows | End-to-end user workflows in DE, EN, SV | E2E-Track | ORIGINAL_REQUEST §AC |
| 15 | Full E2E Verification & Hardening | Pass 100% E2E test suite + adversarial coverage hardening | M6 | Final Milestone |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| E2E | E2E Testing Track | Test infra, parity checker, AST scanner, dynamic switch tests, workflow tests, publish TEST_READY.md | none | DONE |
| M1 | Locale Parity & Synchronization | locales/de.json, locales/en.json, locales/sv.json full parity and natural translations | none | DONE |
| M2 | System, Constants & Enums Localization | src/constants.py, src/enums.py, src/utils/datetime_utils.py, seed & snippet services | M1 | DONE |
| M3 | UI Views & Widgets String Extraction | src/ui/app.py, src/ui/views/, src/ui/widgets/ | M1 | DONE |
| M4 | UI Dialogs String Extraction | src/ui/dialogs/ (all 18 dialog files) | M1 | PLANNED |
| M5 | Dynamic Language Switching Integration | Event propagation, refresh_ui_labels across all views, widgets, and dialogs | M2, M3, M4 | PLANNED |
| M6 | Final Milestone & Hardening | Pass 100% E2E test suite (Tiers 1-4) and adversarial hardening (Tier 5) | E2E, M5 | PLANNED |

## Interface Contracts
### I18nService ↔ UI Components
- `tr(key: str, default: str = "", **kwargs) -> str`: Returns translated text for `key` in active language. If missing, returns `default` with kwargs formatted.
- `LocalizedDict`: Dict proxy dynamically resolving key translations based on current active language.
- `I18nService.register_listener(callback: Callable[[str], None])`: Registers a callback invoked on language change.
- `I18nService.set_language(lang: str)`: Updates active language and notifies all registered listeners.
- `UIComponent.refresh_ui_labels()`: Refreshes all text/labels/options of the component and child widgets.

### Constants ↔ UI Consumers
- `DISPLAY_BOARD_COLUMN_NAMES: LocalizedDict`
- `DISPLAY_ACTOR_NAMES: LocalizedDict`
- `DISPLAY_CHANNEL_NAMES: LocalizedDict`
- `DISPLAY_LAYOUT_NAMES: LocalizedDict`
- `VALIDATION_MESSAGES: LocalizedDict`
- `HOTKEY_ACTION_LABELS: LocalizedDict`

## Code Layout
- `locales/`: `de.json`, `en.json`, `sv.json`
- `src/services/i18n_service.py`: `I18nService`, `tr`, `LocalizedDict`
- `src/constants.py`: Application constants, localized dicts
- `src/enums.py`: Enums and display helpers
- `src/utils/datetime_utils.py`: Localized date/time helpers
- `src/services/`: `seed_case_data.py`, `seed_service.py`, `snippet_service.py`
- `src/ui/app.py`: Main application window and language change orchestrator
- `src/ui/views/`: `cockpit_view.py`, `cockpit_layout_builders.py`, `board_view.py`, `table_view.py`, `analytics_view.py`
- `src/ui/widgets/`: `case_list_widget.py`, `dynamic_form_widget.py`, `toast_notification.py`, `attachment_widget.py`, `wiki_widget.py`, etc.
- `src/ui/dialogs/`: 18 dialog files
- `tests/`: Pytest test suite, `test_translation_parity_and_quality.py`, `test_ast_i18n_scanner.py`, `test_dynamic_language_switch.py`, `test_e2e_multilingual_workflows.py`
