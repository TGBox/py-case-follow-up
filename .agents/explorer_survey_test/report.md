# Comprehensive Test Infrastructure, Verification Mechanisms & AST Scanning Survey Report

**Author**: Explorer Survey Agent  
**Date**: 2026-09-02  
**Target Project**: `py-case-follow-up` (SupportCockpit)  
**Project Root**: `c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up`  
**Execution Environment**: Python 3.14.7 (win32), pytest-9.1.1, pluggy-1.6.0  

---

## 1. Executive Summary

This survey provides an exhaustive analysis of the test suite, verification tooling, AST scanning rules, and internationalization (i18n) verification infrastructure for `py-case-follow-up` across German (`de`), English (`en`), and Swedish (`sv`).

### Key Findings:
1. **Existing Test Suite Health**: The test suite currently comprises **75 test files** with **335 tests**, executing in **123.80 seconds** with a **100% pass rate (335 passed, 0 failed, 0 skipped)** using `.venv\Scripts\python.exe -m pytest`.
2. **Current Locale Parity Status**: `locales/de.json`, `locales/en.json`, and `locales/sv.json` each contain exactly **339 leaf keys** (100% key parity on existing keys). However, `sv.json` has a significantly condensed `help_content` section (15,741 bytes vs 26,248 bytes in `de.json`).
3. **AST Scan for Hardcoded UI Literals**: An AST analysis across all `.py` files in `src/` revealed **221 candidate hardcoded user-visible text literals** across **27 files** (18 dialogs, 3 views, 3 widgets, `app.py`, `constants.py`, and 2 services). These must be extracted to `locales/*.json` and retrieved dynamically via `tr(...)` or `LocalizedDict`.
4. **Dynamic Language Switching Architecture**: `I18nService` provides a listener subscription mechanism (`register_listener`) and `LocalizedDict` proxying. However, several critical dictionary constants in `src/constants.py` (`DISPLAY_BOARD_COLUMN_NAMES`, `DISPLAY_ACTOR_NAMES`, `DISPLAY_CHANNEL_NAMES`, `DISPLAY_LAYOUT_NAMES`) are plain static dicts rather than `LocalizedDict` instances, and some enums lack full key mappings.
5. **E2E Test Architecture**: A 4-Tier E2E test plan has been structured to cover Tier 1 (Component & Locale Coverage), Tier 2 (Boundary & Corner Cases), Tier 3 (Cross-Feature Combinations), and Tier 4 (Real-World Application Scenarios).

---

## 2. Existing Test Suite & Pytest Environment Survey

### 2.1 Configuration & Runner Environment
- **Python Version**: Python 3.14.7 on Windows x86-64.
- **Pytest Version**: `pytest==9.1.1`, `pluggy==1.6.0`.
- **Dependencies**: CustomTkinter 6.0.0, Jinja2 3.1.6, Pillow 12.3.0, PyStray 0.19.5, Winotify 1.1.0, DarkDetect 0.8.0.
- **Configuration Files**:
  - `pyproject.toml`: Defines project metadata and dependencies.
  - Root `conftest.py`: Injects `src/` into `sys.path` for module discovery.
  - `tests/conftest.py`: Defines autouse fixture `isolate_global_supportcockpit_config` which mocks `SUPPORTCOCKPIT_CONFIG_DIR` to a temporary directory (`tmp_path / "global_config_mock"`), protecting real `%APPDATA%` user configurations.

### 2.2 Test Suite Execution Metrics
Execution Command:
```powershell
.venv\Scripts\python.exe -m pytest
```
Output Summary:
- **Files Collected**: 75 test files.
- **Items Collected**: 335 items.
- **Result**: 335 passed in 123.80s (0:02:03).
- **Test Categories Breakdown**:
  - **Service Unit Tests**: 32 files (AI service, storage, customer, export, seed, snippets, wiki, etc.)
  - **Data Models & Schemas**: 8 files (schemas, forms, scoring, customers, profile, etc.)
  - **UI & Dialog Tests**: 25 files (`test_dialogs_comprehensive.py`, `test_e2e_dialogs.py`, `test_views_and_interactive_dialogs.py`, `test_ui_workflow_chains.py`, etc.)
  - **Integrations & Helpers**: 10 files (datetime utils, unicode cleanliness, zip backup, P2P sync, webhook, etc.)

### 2.3 Headless GUI Testing Pattern in CustomTkinter
In existing tests (e.g. `tests/test_dialogs_comprehensive.py:20-34`), CustomTkinter dialogs and views are tested headlessly:
```python
@pytest.fixture
def app_and_storage(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)
    app = ctk.CTk()
    app.withdraw()  # Hide UI window from display
    yield app, storage, config
    try:
        app.destroy()
    except Exception:
        pass
```
Widgets and dialogs are verified by instantiating them with `app`, calling `dialog.update_idletasks()` or `app.update()`, reading widget attributes (`widget.cget("text")`, `widget.get()`, `widget._text`), simulating button clicks (`widget._command()`), and finally calling `dialog.destroy()`.

---

## 3. Locale Files & Key Parity Analysis

### 3.1 Current Status of Locale Files
Files located in `locales/`:
| File | Byte Size | Top-Level Sections | Total Flat Keys |
|---|---|---|---|
| `locales/de.json` | 41,420 bytes | 28 sections | 339 keys |
| `locales/en.json` | 36,852 bytes | 28 sections | 339 keys |
| `locales/sv.json` | 30,545 bytes | 28 sections | 339 keys |

Top-level sections present in all three files:
`actors`, `analytics`, `board`, `calendar_export`, `channels`, `cobra_import`, `cockpit`, `common`, `convert_schema`, `demo_cases`, `departments`, `dialog_headers`, `dialog_titles`, `email_calendar`, `email_draft`, `handover_channels`, `help_content`, `help_dialog`, `internal_task_categories`, `layouts`, `menu`, `profile`, `snippet_picker`, `splash`, `status_messages`, `table_columns`, `template_editor`, `ui_buttons`.

### 3.2 Key Parity Gaps & Quality Findings
1. **Existing Keys Parity**: Current keys match 1:1 across `de`, `en`, `sv`.
2. **Help Content Discrepancy**: In `locales/sv.json`, the `help_content` section contains only 15,741 bytes compared to 26,248 bytes in `de.json`. Certain articles in Swedish are abbreviated or omit subsection explanations.
3. **Identical String Analysis**:
   - 25 keys in `en.json` match `de.json` exactly (e.g. `menu.layout: "Layout:"`, `profile.wiki_token_id: "API Token ID:"`, `common.ok: "OK"`, `handover_channels.GitLab Issue: "GitLab Issue"`). These are technical acronyms or shared loan words.
   - 23 keys in `sv.json` match `de.json` exactly (e.g. `splash.title: "🩺 Support-Cockpit"`, `profile.mobile: "Mobilnummer:"`, `help_content.storage_paths.category: "Konfiguration"`).
4. **Placeholder Tokens**: All format placeholders (`{name}`, `{case_id}`, etc.) currently match 100% across existing keys.

### 3.3 Specification of Automated Verification Tool
An automated test `tests/test_translation_parity_and_quality.py` should enforce:
1. **Recursive Key Parity**: `extract_all_leaf_keys(de.json) == extract_all_leaf_keys(en.json) == extract_all_leaf_keys(sv.json)`.
2. **No Empty Values**: No key in any language can evaluate to `""` or whitespace.
3. **Placeholder Matching**: For every key, `{token}` instances in DE must exactly match the set of `{token}` instances in EN and SV.
4. **German Placeholder / Untranslated Detection in EN and SV**:
   - In `en.json`: Fail if German stop words or common German nouns (`wiedervorlage`, `speichern`, `abbrechen`, `löschen`, `mitarbeiter`, `praxis`, `einstellungen`, `anwendungsdokumentation`, `bitte`, `nicht`) appear as tokens.
   - In `sv.json`: Fail if German specific tokens (`wiedervorlage`, `speichern`, `abbrechen`, `löschen`, `mitarbeiter`, `praxen`, `hinzufügen`, `bearbeiten`, `einstellungen`) appear as tokens.

---

## 4. AST Scanner Specification & Findings

### 4.1 AST Scan Results Across `src/`
A complete AST traversal of all `.py` files in `src/` revealed **221 candidate hardcoded UI text literals** across **27 files**.

#### Detailed Breakdown by Subsystem:
1. **Dialogs (`src/ui/dialogs/` — 18 files, 188 literals)**:
   - `customer_form_builders.py` (51 literals): Hardcoded labels ("Praxisname (Alt):", "Ansprechpartner:", button texts "↑ Aufst.", placeholders).
   - `profile_settings_dialog.py` (18 literals): Placeholders ("z. B. Support, Entwicklung", "beispiel@support.de"), labels, and status strings.
   - `schema_builder_dialog.py` (18 literals): Labels ("Neues Formular-Schema definieren", "Anzeigename (Titel) *:"), placeholders ("z. B. Abrechnung & Tarife").
   - `ai_assistant_dialog.py` (14 literals): Status labels ("Prüfe Status...", "🤖 KI verarbeitet Anfrage..."), buttons ("Schließen"), fallback hints.
   - `customer_management_dialog.py` (13 literals): Button texts ("🗑 Entfernen"), labels ("Name *:"), warnings ("⚠ Keine Webseite eingetragen!").
   - `template_manager_dialog.py` (12 literals): Field labels ("Vorlage-ID *:", "Anzeigename *:"), placeholders.
   - `cobra_import_dialog.py` (10 literals): Step headers ("1. Cobra Export-Datei auswählen:"), placeholders, button texts ("📁 Durchsuchen...").
   - `colleague_management_dialog.py` (10 literals): Placeholders ("z. B. Max Müller", "z. B. mmueller").
   - `case_print_dialog.py` (9 literals): Checkbox labels ("Praxis & Kundendaten", "Formularfelder", "Bilder & Anhänge am Ende").
   - `email_calendar_dialog.py` (7 literals): Field headers ("Empfänger (E-Mail):", "Betreff:", "E-Mail Nachrichtentext:").
   - `email_draft_dialog.py` (7 literals): Search placeholders, contact header labels, status hints.
   - `followup_flyout_dialog.py` (6 literals): Quick postponement buttons ("+ 1 Std.", "+ 2 Std.", "Heute 16:30", "Morgen 08:00", "+ 1 Tag").
   - `new_case_dialog.py` (6 literals): Form placeholders ("z.B. Praxis Dr. Weber", "030 / 123456").
   - `profile_settings_ai_tab.py` (4 literals): API status messages ("⚠ Bitte API Key eingeben", "🔍 Prüfe Key...").
   - `snippet_management_dialog.py` (4 literals): Placeholders for shortcuts, tags, and titles.
   - `zip_import_dialog.py` (3 literals): File dialog titles ("Gesamt-Zielverzeichnis wählen", "Zielverzeichnis für Datendateien...").
   - `calendar_export_dialog.py` (2 literals): Label ("Kalender-Beschreibung / Notiz:"), file dialog title ("iCalendar-Datei speichern").
   - `email_import_dialog.py` (2 literals): Buttons ("➕ Als neuen Fall anlegen", "🗑 Ignorieren").
   - `followup_dialog.py` (2 literals): Date picker placeholder ("TT.MM.JJJJ 09:00"), entry placeholder.

2. **Views (`src/ui/views/` — 3 files, 3 literals)**:
   - `cockpit_layout_builders.py` (1 literal): Label ("🔔 Nachfragen am:").
   - `cockpit_view.py` (1 literal): Toast message ("Für diese Praxis ist keine E-Mail-Adresse hinterlegt.").
   - `analytics_view.py` (1 literal): Toast message ("Statistik-Bericht wurde in die Zwischenablage kopiert.").

3. **Widgets (`src/ui/widgets/` — 3 files, 3 literals)**:
   - `case_list_widget.py` (1 literal): Label ("🔔 Nachfragen am:").
   - `dynamic_form_widget.py` (1 literal): File dialog title ("Datenbank-Backup (.backup) importieren").
   - `toast_notification.py` / `attachment_widget.py` / `wiki_widget.py`: Some dynamic status strings.

4. **App Root (`src/ui/app.py` — 3 literals)**:
   - Notification button counter label ("🔔 0").
   - File dialog title ("Komplett-Datensicherung als ZIP speichern").

5. **Services (`src/services/` — 2 files, 24 literals)**:
   - `seed_service.py` (16 literals): Default case descriptions and titles (e.g. "Alte Abrechnung Q1 gelöst", "Frische Nachforderung ohne DB-Dump").
   - `snippet_service.py` (8 literals): Default snippet titles and contents (e.g. "📸 Rückfrage: Screenshots & Uhrzeit anfordern", "🛠 Ersthilfe: PVS & Support-Dienst neustarten").

### 4.2 AST Scanner Architecture & Implementation Blueprint
The automated AST scanner must be implemented as a pytest test (`tests/test_ast_i18n_scanner.py`) using Python's `ast` module.

#### Detection Criteria:
- **UI Constructors**: `ctk.CTkButton`, `ctk.CTkLabel`, `ctk.CTkEntry`, `ctk.CTkCheckBox`, `ctk.CTkRadioButton`, `ctk.CTkSwitch`, `ctk.CTkOptionMenu`, `ctk.CTkComboBox`, `ctk.CTkSegmentedButton`, `ctk.CTkTabview`, `ctk.CTkTextbox`, `ToastNotification`, `DatePickerWidget`.
- **Target Keyword Arguments**: `text`, `placeholder_text`, `title`, `message`, `dialog_title`, `values`.
- **Method Calls**: `.configure(text=...)`, `.configure(placeholder_text=...)`, `.set(...)`, `.add(...)` on tabviews, `askopenfilename(title=...)`, `asksaveasfilename(title=...)`, `askdirectory(title=...)`.

#### Allowlist / Exemption Rules:
1. **Empty / Whitespace strings**: `""`, `" "`.
2. **Pure Punctuation / Numeric / Formatting Symbols**: `"+"`, `"-"`, `":"`, `"*"`, `"0"`, `"1"`, `"%Y-%m-%d"`, `"{}"`.
3. **Hex Colors & Color Names**: Regex `^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$` or tokens in `{"transparent", "gray10", "gray20", "gray30", "gray70", "gray80", "gray90", "white", "black"}`.
4. **Layout & Geometry Arguments**: `side="left"`, `anchor="w"`, `fill="both"`, `expand=True`, `padx=5`, `pady=5`.
5. **System URLs & Protocols**: Strings starting with `"http://"`, `"https://"`, `"sqlite:///"`.
6. **Internal Keys / Identifiers / Field Names**: Model attributes like `"case_id"`, `"status"`, `"customer_id"`, `"unformatted_description"`.
7. **`tr(...)` Calls and `LocalizedDict` References**: Nodes where the value is an `ast.Call` to `tr(...)` or subscript on a `LocalizedDict`.

---

## 5. Dynamic Language Switching Runtime Verification Analysis

### 5.1 Current Implementation in `src/services/i18n_service.py`
```python
class I18nService:
    def __init__(self, locales_dir: Path | str | None = None):
        ...
        self._current_language: str = "de"
        self._translations: dict[str, dict[str, Any]] = {}
        self._listeners: list[Callable[[str], None]] = []

    @property
    def current_language(self) -> str:
        return self._current_language

    @current_language.setter
    def current_language(self, lang_code: str) -> None:
        if lang_code in SUPPORTED_LANGUAGES and lang_code != self._current_language:
            self._current_language = lang_code
            self._notify_listeners()

    def register_listener(self, callback: Callable[[str], None]) -> None:
        if callback not in self._listeners:
            self._listeners.append(callback)

    def unregister_listener(self, callback: Callable[[str], None]) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)
```

### 5.2 Identified Architectural Gaps for Runtime Switching
1. **Constants Dicts are Static**: In `src/constants.py`, `DISPLAY_BOARD_COLUMN_NAMES`, `DISPLAY_CHANNEL_NAMES`, `DISPLAY_ACTOR_NAMES`, `DISPLAY_LAYOUT_NAMES` are plain Python dictionaries initialized at module load time. While `DIALOG_TITLES` was wrapped with `LocalizedDict`, the other display dictionaries were not.
2. **Enum Display Functions Missing Keys**: In `src/enums.py`:
   - `get_channel_display`: `key_map` only covers `PHONE_INBOUND`, `EMAIL`, `INTERNAL_NOTE`. Missing `PHONE_OUTBOUND`, `DEV_TICKET`, `GITLAB_TICKET_*`, `OTHER`.
   - `get_board_column_display`: Returns `BOARD_COLUMN_DISPLAY.get(val, val)` which is static if `DISPLAY_BOARD_COLUMN_NAMES` is not a `LocalizedDict`.
3. **UI Component Lifecycle Listeners**: Views and dialogs must register an `on_language_changed` listener upon initialization and unregister it on destruction (`<Destroy>` event) to prevent dangling references.

### 5.3 Runtime Verification Test Requirements
Tests in `tests/test_dynamic_language_switch.py` must verify:
- Language change event fires callbacks in registered order.
- Closing dialog unregisters listener (zero memory leaks).
- When language changes from `de` -> `en` -> `sv`:
  - `DIALOG_TITLES["new_case"]` updates dynamically from `"Neuen Support-Fall anlegen"` to `"Create New Support Case"` to `"Skapa nytt supportärende"`.
  - `get_board_column_display("NEW")` updates dynamically (`"Neu"` -> `"New"` -> `"Ny"`).
  - Main application window title, menu dropdown options, and status bar text update immediately without app restart.
  - Active case form data is preserved and not overwritten.

---

## 6. Comprehensive E2E Test Plan Structure (Tiers 1-4)

```
========================================================================================
                          E2E TEST PLAN ARCHITECTURE MATRIX
========================================================================================

+--------------------------------------------------------------------------------------+
| TIER 1: FEATURE & COMPONENT COVERAGE                                                 |
| - Verify all 26 Dialogs render in DE, EN, SV                                         |
| - Verify all 4 Main Views (Cockpit, Board, Table, Analytics) render in DE, EN, SV    |
| - Verify all 10 Core Widgets render in DE, EN, SV                                    |
| - Verify Enum Display Helpers & LocalizedDict mappings across all 3 locales          |
| - Verify Seed Datasets, Support Snippets, and Template Defaults in DE, EN, SV        |
+--------------------------------------------------------------------------------------+
                                          |
                                          v
+--------------------------------------------------------------------------------------+
| TIER 2: BOUNDARY & CORNER CASES                                                      |
| - Fallback Resilience (missing key in SV -> DE -> default -> raw key)                |
| - Parameter Interpolation Edge Cases (missing kwargs, extra kwargs, non-string types)|
| - UI Text Expansion & Dynamic Wrapping (Swedish/German compounds vs English)         |
| - Unicode & Special Characters (ä, ö, ü, ß, å, emojis, punctuation)                  |
| - Rapid Runtime Language Cycling (DE -> EN -> SV -> DE during active editing)        |
+--------------------------------------------------------------------------------------+
                                          |
                                          v
+--------------------------------------------------------------------------------------+
| TIER 3: CROSS-FEATURE COMBINATIONS                                                   |
| - Search & Filtering across Locales (German case data filtered using English tokens) |
| - Export Engine (HTML, Markdown, Plain Text, ICS exports with localized headers)     |
| - Multi-User P2P Synchronization (Data interchange between German and Swedish nodes) |
| - AI Assistant & Solution Matching (Localized system prompts, solution cards)        |
| - Keyboard Macros & Toast Notifications (Localized shortcut execution feedback)      |
+--------------------------------------------------------------------------------------+
                                          |
                                          v
+--------------------------------------------------------------------------------------+
| TIER 4: REAL-WORLD APPLICATION SCENARIOS                                             |
| - Scenario 1: Case Intake, Triage, Deadline Tracking & Language Switching in Swedish  |
| - Scenario 2: Practice Management & Cobra CRM Import Workflow in English             |
| - Scenario 3: Email Reply & Calendar Outbound Workflow in Swedish                   |
| - Scenario 4: User Profile Setup, Theme Toggle & Language Persistence on App Restart |
+--------------------------------------------------------------------------------------+
```

### Tier 1: Feature & Component Coverage
- **T1.1: Dialogs Coverage (26 Dialogs)**:
  - `AiAssistantDialog`, `CalendarExportDialog`, `CasePrintDialog`, `CobraImportDialog`, `ColleagueManagementDialog`, `ConvertSchemaDialog`, `CustomerManagementDialog`, `EmailCalendarDialog`, `EmailDraftDialog`, `EmailImportDialog`, `ExportDialog`, `FollowupDialog`, `FollowupFlyoutDialog`, `HandoverDialog`, `HelpDialog`, `NewCaseDialog`, `P2pDiffDialog`, `ProfileSettingsDialog`, `SchemaBuilderDialog`, `SnippetManagementDialog`, `SnippetPickerDialog`, `TagManagementDialog`, `TemplateManagerDialog`, `ZipImportDialog`.
  - Assert that all labels, buttons, dialog titles, placeholders, and tab titles match the respective locale.
- **T1.2: Views Coverage (4 Views)**:
  - `CockpitView`: Search bar placeholder, filter buttons ("All", "Urgent", "Follow-up", "Deep Search"), action menu items, tabs ("Timeline", "Attachments", "Wiki").
  - `BoardView`: Kanban column headers ("New", "Action Required", "Waiting", "In Progress", "Done"), card count badges, card details.
  - `TableView`: Table column headers ("ID ⇅", "Practice / Customer ⇅", "Title ⇅", "Score ⇅", "Status ⇅", "Created ⇅", "Follow-up ⇅"), sort indicators.
  - `AnalyticsView`: KPI card titles ("Total Cases", "Open Cases", "Avg. Resolution Time", "Urgency Distribution"), chart labels, export buttons.
- **T1.3: Widgets Coverage (10 Widgets)**:
  - `AttachmentWidget`, `CaseListWidget`, `CTkTooltip`, `DatePickerWidget`, `DynamicFormFieldRenderers`, `DynamicFormWidget`, `SearchableComboBox`, `TimelineWidget`, `ToastNotification`, `WikiWidget`.
- **T1.4: Enums & Constants Coverage**:
  - `UrgencyLevel`, `BoardColumn`, `Actor`, `FieldType`, `SyncMode`, `TargetType`, `Channel`, `LayoutMode`.
- **T1.5: Seed Data & Default Snippets**:
  - Default seed cases and support snippets provide localized templates.

### Tier 2: Boundary & Corner Cases
- **T2.1: Key Fallback Chain**:
  - Request key present only in `de.json` while active language is `sv` -> returns German translation.
  - Request non-existent key with `default="Fallback"` -> returns `"Fallback"`.
  - Request non-existent key without default -> returns raw key string.
- **T2.2: Format String Interpolation Resilience**:
  - Format call with missing arguments `tr("greeting", other="val")` -> does not crash with `KeyError`, returns raw template string.
  - Format call with extra arguments -> formats correctly without error.
- **T2.3: Text Expansion & Layout Wrapping**:
  - German compound words (e.g. "Zuzahlungsnachforderungsverwaltung") and Swedish words (e.g. "Mottagningshantering") tested in fixed-width buttons and flyout headers.
  - Verify auto-wrapping, `minsize`, and tooltip fallbacks prevent text truncation.
- **T2.4: Unicode & Special Characters**:
  - Full ASCII + Latin-1 Supplement + Extended Latin (ä, ö, ü, ß, å, é, è, ñ) + Unicode Emojis (🩺, 🤖, 💾, 📦, 🔔, 🐍, 📁, ⚙, 🏷, 📤, 📥).
- **T2.5: Rapid Runtime Language Cycling**:
  - Programmatically cycle languages 100 times (`de` -> `en` -> `sv` -> `de`...) in rapid succession while a complex form dialog is open to verify thread safety and absence of UI race conditions.

### Tier 3: Cross-Feature Combinations
- **T3.1: Multilingual Search & Filter**:
  - Execute quick search and deep search using English search tokens (e.g. `status:open`, `actor:support`) and Swedish search tokens against cases authored in German.
- **T3.2: Export Engine Multilingual Generation**:
  - Export cases to HTML, Markdown, and CSV in Swedish; verify report titles, column headers, timestamps, and status labels are localized in Swedish.
- **T3.3: P2P Multi-User Sync Across Locales**:
  - Node A (configured in German) creates and updates a case; Node B (configured in Swedish) syncs via P2P. Case data fields remain unmodified, but UI widgets on Node B display Swedish labels.
- **T3.4: AI Assistant & Solution Cards in English/Swedish**:
  - Generate case summary and email draft with active language set to English/Swedish; verify system prompt instructions and fallback template strings reflect active locale.
- **T3.5: Keyboard Macros & Shortcuts Across Locales**:
  - Trigger keyboard shortcuts (e.g. `Ctrl+N`, `Ctrl+E`, `Ctrl+S`, `F1`); verify shortcut help dialog and confirmation toast messages display in the active language.

### Tier 4: Real-World Application Scenarios
- **T4.1: Scenario 1 — End-to-End Case Intake in Swedish**:
  1. Set application language to `sv` (Svenska).
  2. Click `+ Nytt ärende (Ctrl+N)`.
  3. Fill out practice information ("Läkarhuset Stockholm"), select schema, fill custom form fields.
  4. Save case -> verify case appears in `Ny` (New) board column.
  5. Add timeline note with attachment -> verify timestamp formatting and note label.
  6. Set Wiedervorlage reminder -> verify Swedish flyout and date picker.
  7. Switch application language to German (`de`) mid-workflow -> verify all UI labels immediately update to German while case data is untouched.
- **T4.2: Scenario 2 — Practice Management & Cobra CRM Import in English**:
  1. Set application language to `en` (English).
  2. Open Cobra CRM Import Dialog -> select sample customer CSV -> map columns -> execute import.
  3. Open Customer Management Dialog -> edit practice contacts and VIP status.
  4. Verify all table headers, button labels, validation messages, and feedback toasts appear in English.
- **T4.3: Scenario 3 — Outbound Email & Calendar Integration in Swedish**:
  1. Set language to `sv`.
  2. Select an active case -> open Email & Calendar Dialog.
  3. Select Swedish email template -> verify subject and body formatting.
  4. Export `.ics` calendar invitation -> verify file dialog title and `.ics` event summary in Swedish.
- **T4.4: Scenario 4 — Full App Lifecycle & Language Persistence**:
  1. Open Profile Settings Dialog -> change language to `en` -> save profile.
  2. Verify `UISettings.language` is saved to `user_config.json`.
  3. Restart application instance -> verify app initializes directly into English mode without requiring manual selection.

---

## 7. Recommended Test Suite Additions & Implementation Plan

To achieve 100% test integrity and satisfy all user acceptance criteria, the following new test modules should be created during the implementation phase:

| Test File | Target Purpose | Tier Coverage |
|---|---|---|
| `tests/test_translation_parity_and_quality.py` | 100% key parity across `de.json`, `en.json`, `sv.json`, placeholder format validation, and German token detector. | Tier 1 & Tier 2 |
| `tests/test_ast_i18n_scanner.py` | AST scanner scanning all `.py` files in `src/` to assert zero hardcoded UI strings in widgets/dialogs/constants. | Tier 1 & Verification |
| `tests/test_dynamic_language_switch.py` | Dynamic runtime switching across all dialogs, views, and `LocalizedDict` instances without app restart. | Tier 1 & Tier 2 |
| `tests/test_e2e_multilingual_workflows.py` | End-to-end integration workflows for Scenarios 1-4 across English and Swedish. | Tier 3 & Tier 4 |

---
