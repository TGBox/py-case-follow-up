# E2E Test Infra: SupportCockpit Multi-Language Localization

## Test Philosophy
- Opaque-box, requirement-driven. No dependency on implementation design.
- Methodology: Category-Partition + BVA + Pairwise + Real-World Workload Testing.

## Feature Inventory & Test Mapping
| # | Feature | Source | Tier 1 (Component) | Tier 2 (Boundary) | Tier 3 (Interactions) | Tier 4 (Workflows) |
|---|---------|--------|:------------------:|:-----------------:|:---------------------:|:------------------:|
| 1 | Locale Key Parity & No Empty Values | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ | ✓ |
| 2 | English & Swedish Translation Quality | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ | ✓ |
| 3 | AST UI Widget String Extraction | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ | ✓ |
| 4 | Constants & Enums Localization | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ | ✓ |
| 5 | DateTime Utils Localization | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ | ✓ |
| 6 | Seed Data & Snippets Localization | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ | ✓ |
| 7 | Dynamic Language Switching Across Views | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ | ✓ |
| 8 | Dynamic Language Switching in Dialogs | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ | ✓ |

## Test Architecture
- Test runner: `.venv\Scripts\python.exe -m pytest`
- Test files:
  1. `tests/test_translation_parity_and_quality.py`:
     - Tier 1 & 2: 100% key parity across `de.json`, `en.json`, `sv.json`, non-empty strings, format token preservation, detection of German stop words / untranslated text in EN & SV.
  2. `tests/test_ast_i18n_scanner.py`:
     - Tier 1 & 2: AST traversal over all `.py` files in `src/` ensuring no hardcoded user-visible text literals passed directly into CTk buttons, labels, entries, dialog titles, toasts, etc.
  3. `tests/test_dynamic_language_switch.py`:
     - Tier 1, 2, 3: Headless UI testing verifying language change dynamically updates CockpitView, BoardView, TableView, AnalyticsView, active widgets, menu bar, and dialog labels without restarting the app.
  4. `tests/test_e2e_multilingual_workflows.py`:
     - Tier 3 & 4: Comprehensive end-to-end workflows (Case creation, filtering, editing, template exporting, importing, dialog navigation) in German, English, and Swedish.

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|----------|--------------------|------------|
| 1 | Switch language DE -> EN -> SV and create a new support case | F1, F2, F7, F8, F9, F10 | Medium |
| 2 | Board view column drag/drop and status changes across languages | F4, F7, F10 | Medium |
| 3 | Export/Import calendar and cobra data in Swedish | F1, F5, F8, F9 | High |
| 4 | Snippet picker and template manager usage in English | F2, F6, F9, F10 | Medium |
| 5 | Customer and Colleague management in all 3 locales | F1, F2, F9, F10 | High |

## Coverage Thresholds
- Tier 1: ≥5 test cases per feature
- Tier 2: ≥5 test cases per feature (boundary/corner cases)
- Tier 3: pairwise coverage of major feature interactions
- Tier 4: ≥5 realistic application scenarios
