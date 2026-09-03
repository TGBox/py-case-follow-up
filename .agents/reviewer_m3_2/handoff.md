# Technical Review & Adversarial Critic Report: Milestone 3 (UI Views & Widgets String Extraction)

**Reviewer**: Reviewer 2 (Reviewer & Critic)  
**Milestone**: Milestone 3 — UI Views & Widgets String Extraction  
**Working Directory**: `.agents/reviewer_m3_2`  
**Verdict**: **REQUEST_CHANGES**

---

## 1. Observation

A full code audit, test execution, AST verification, and adversarial stress-testing were conducted across all Milestone 3 components:
- **Application Shell & Dialog Openers**: `src/ui/app.py`, `src/ui/app_dialogs.py`
- **UI Views**: `src/ui/views/cockpit_view.py`, `src/ui/views/cockpit_layout_builders.py`, `src/ui/views/board_view.py`, `src/ui/views/table_view.py`, `src/ui/views/analytics_view.py`
- **UI Widgets**: `src/ui/widgets/case_list_widget.py`, `src/ui/widgets/date_picker.py`, `src/ui/widgets/dynamic_form_widget.py`, `src/ui/widgets/dynamic_form_field_renderers.py`, `src/ui/widgets/attachment_widget.py`, `src/ui/widgets/wiki_widget.py`, `src/ui/widgets/timeline_widget.py`, `src/ui/widgets/searchable_combobox.py`, `src/ui/widgets/toast_notification.py`, `src/ui/widgets/ctk_tooltip.py`
- **Locale Definitions**: `locales/de.json`, `locales/en.json`, `locales/sv.json`

### Direct Observations & Verifications:

1. **Test Suite Execution**:
   - `pytest` full test suite: **439 passed in 170.00s**.
   - Targeted suites (`tests/test_ast_i18n_scanner.py`, `tests/test_translation_parity_and_quality.py`, `tests/test_dynamic_language_switch.py`, `tests/test_e2e_multilingual_workflows.py`): **67 passed in 1.70s**.

2. **Translation Parity & Quality**:
   - Key parity count: `de.json` (1206 keys), `en.json` (1206 keys), `sv.json` (1206 keys) — 100% mutual leaf key parity.
   - 0 format token mismatches between language files.
   - High translation quality: natural terminology across English and Swedish without German placeholders.
   - All `tr(...)` calls in `src/ui/` resolve to valid keys in `locales/*.json`.

3. **AST Extraction Cleanliness**:
   - Automated AST scanner verified 0 hardcoded user-visible text literals across `src/ui/views/`, `src/ui/widgets/`, and `src/ui/app.py` / `src/ui/app_dialogs.py`.

4. **Integrity Audit**:
   - No dummy facades, no hardcoded test assertions in source code, no shortcutting.

5. **Adversarial Stress-Testing Findings (Failure Modes Discovered)**:
   - **Critical Finding 1 (`_tkinter.TclError` Crash on Multiple Language Switches)**:
     - **Location**: `src/ui/widgets/attachment_widget.py`, line 62.
     - **Observation**:
       ```python
       # src/ui/widgets/attachment_widget.py:62
       if hasattr(self, "preview_label") and not self.preview_label.cget("text").startswith("📄") and not self.preview_label.cget("text").startswith("🖼"):
           self.preview_label.configure(text=tr("attachments.no_preview", "Keine Datei zur Vorschau ausgewählt"))
       ```
     - **Behavior**: `self.preview_label` is created during `create_widgets()`. When `self.load_attachments()` runs, it calls `self.clear_preview()`, destroying all children in `self.preview_frame` including `self.preview_label`. On the next `refresh_ui_labels()` invocation (e.g. switching DE -> EN -> SV), `hasattr(self, "preview_label")` is `True`, but `self.preview_label` is destroyed in Tkinter. Calling `.cget()` raises `_tkinter.TclError: invalid command name ".!attachmentwidget.!ctkframe3.!ctklabel.!label"`.
   - **Major Finding 2 (Tabview Labels Stuck on Secondary Language Switches)**:
     - **Location**: `src/ui/views/cockpit_layout_builders.py` (lines 334-344) and `src/ui/views/table_view.py` (lines 360-372).
     - **Observation**:
       ```python
       # src/ui/views/cockpit_layout_builders.py:339-343
       prev_text = getattr(self, "_sidebar_tab_names", {}).get(tab_key, def_name)
       if hasattr(self, "_sidebar_tab_names"):
           self._sidebar_tab_names[tab_key] = new_text
       if prev_text in btns:
           btns[prev_text].configure(text=new_text)
       ```
     - **Behavior**: In `CustomTkinter.CTkTabview`, `_segmented_button._buttons_dict` keys are fixed to the original strings passed when `.add()` was called (e.g. `"Zeitleiste"` in Cockpit, `"📝 Formular & Ausfüllen"` in Table). Calling `btn.configure(text=new_text)` updates the visible label but does NOT alter the dictionary key in `_buttons_dict`. Mutating `self._sidebar_tab_names[tab_key]` to `"Timeline"` on the first language switch causes `prev_text in btns` to evaluate to `False` on all subsequent language switches (e.g. switching to Swedish). Consequently, the tabs remain stuck in English and do not translate to Swedish.

---

## 2. Logic Chain

1. **Premise**: Milestone 3 requires complete string extraction in UI views and widgets with dynamic runtime switching across German, English, and Swedish that operates seamlessly without application restart or UI errors.
2. **Key Parity & Extraction**:
   - The worker successfully extracted and synchronized 1206 translation keys with 100% parity across `de.json`, `en.json`, and `sv.json`.
   - The AST scanner confirms 0 remaining hardcoded user-visible text literals.
3. **Dynamic Cascade Failure Modes**:
   - When a user changes language once (e.g. DE -> EN), `CockpitView.refresh_ui_labels()` calls `AttachmentWidget.refresh_ui_labels()`, which calls `load_attachments()`. `load_attachments()` executes `clear_preview()`, destroying the Tkinter peer of `self.preview_label`.
   - When the user changes language a second time (e.g. EN -> SV), `AttachmentWidget.refresh_ui_labels()` attempts `self.preview_label.cget(...)`, crashing the entire application with `_tkinter.TclError`.
   - Simultaneously, in `CockpitView` and `TableView`, mutating the tab dictionary keys during the first switch breaks the button lookup for all subsequent switches, preventing tabs from ever switching to Swedish.
4. **Resolution Required**:
   - `AttachmentWidget.refresh_ui_labels()` must safely check `self.preview_label.winfo_exists()` (or avoid referencing destroyed labels) and recreate/manage `preview_label` robustly.
   - `CockpitLayoutBuilderMixin` and `TableView` must maintain stable initial keys (or tab indices) when accessing `_segmented_button._buttons_dict` so that tab text updates reliably across arbitrary sequences of language changes (e.g. DE -> EN -> SV -> DE).

---

## 3. Caveats

- **Milestone 4 Scope**: Dialog windows in `src/ui/dialogs/` (all 18 standalone dialogs) are designated for Milestone 4 and were excluded from this M3 review.
- **Review-Only Constraint**: As Reviewer 2, no implementation source files were modified. The findings and precise fix recommendations are detailed below for the implementation worker.

---

## 4. Conclusion

Milestone 3 has achieved excellent translation parity, natural localization quality, and comprehensive AST extraction. However, due to the critical Tkinter widget lifecycle crash in `AttachmentWidget` and the tab button desynchronization on multi-step language switching, the verdict is **REQUEST_CHANGES**.

### Required Changes:

1. **Fix `AttachmentWidget.refresh_ui_labels` (`src/ui/widgets/attachment_widget.py`)**:
   - Replace unsafe `hasattr(self, "preview_label")` and `.cget()` calls on potentially destroyed widgets.
   - Ensure `refresh_ui_labels()` either checks `try: ... except Exception:` / `winfo_exists()` or reconstructs the preview area cleanly.

2. **Fix `CTkTabview` Tab Renaming in `CockpitView` and `TableView`**:
   - In `src/ui/views/cockpit_layout_builders.py` and `src/ui/views/table_view.py`: Keep the initial tab keys constant (the strings used during `.add()`), e.g.:
     ```python
     initial_tab_keys = {"timeline": "Zeitleiste", "attachments": "Anhänge", "wiki": "Wiki / Wissensdatenbank"}
     for tab_key, init_name in initial_tab_keys.items():
         if init_name in btns:
             btns[init_name].configure(text=tr(f"cockpit.tab_{tab_key}", init_name))
     ```
   - In `src/ui/views/table_view.py`:
     ```python
     initial_tab_keys = {
         "form": "📝 Formular & Ausfüllen",
         "timeline": "🕒 Zeitleiste",
         "attachments": "📎 Anhänge",
     }
     for key, init_name in initial_tab_keys.items():
         if init_name in btns:
             btns[init_name].configure(text=tr(f"table.tab_{key}", init_name))
     ```

3. **Add Anti-Regression Test in `tests/test_dynamic_language_switch.py`**:
   - Add an explicit test that cycles languages `DE -> EN -> SV -> DE` on `CockpitView` and `TableView` with `AttachmentWidget` and asserts:
     - No `_tkinter.TclError` occurs.
     - Right sidebar tabs and table detail tabs update their displayed button text to the active language on every transition (e.g. verifying `btns["Zeitleiste"].cget("text") == "Tidslinje"` in Swedish).

---

## 5. Verification Method

To independently reproduce the findings and verify the fixes:

1. **Reproduce `AttachmentWidget` Crash on Multiple Language Switches**:
   ```python
   .venv\Scripts\python.exe -c "
   import sys; sys.path.insert(0, 'src')
   import customtkinter as ctk; from pathlib import Path; from config import AppConfig
   from services.attachment_service import AttachmentService; from ui.widgets.attachment_widget import AttachmentWidget
   root = ctk.CTk(); root.withdraw()
   aw = AttachmentWidget(root, AttachmentService(AppConfig(workspace_dir=Path('data'))))
   aw.refresh_ui_labels()
   aw.refresh_ui_labels() # Raises _tkinter.TclError
   "
   ```

2. **Reproduce Tabview Desynchronization**:
   ```python
   .venv\Scripts\python.exe -c "
   import sys; sys.path.insert(0, 'src')
   import customtkinter as ctk; from pathlib import Path; from config import AppConfig
   from services.storage_service import StorageService; from services.scoring_service import ScoringService
   from services.attachment_service import AttachmentService; from services.wiki_sync_service import WikiSyncService
   from services.i18n_service import get_i18n; from ui.views.cockpit_view import CockpitView
   root = ctk.CTk(); root.withdraw(); cfg = AppConfig(workspace_dir=Path('data'))
   cockpit = CockpitView(root, 'Tester', ScoringService({}), AttachmentService(cfg), WikiSyncService(cfg, {}), app_config=cfg)
   get_i18n().current_language = 'en'; cockpit.refresh_ui_labels()
   get_i18n().current_language = 'sv'; cockpit.refresh_ui_labels()
   btns = cockpit.right_tabview._segmented_button._buttons_dict
   print('Timeline tab text in SV:', btns['Zeitleiste'].cget('text')) # Currently stuck on 'Timeline' instead of 'Tidslinje'
   "
   ```

3. **Run Full Test Suite**:
   ```bash
   .venv\Scripts\python.exe -m pytest
   ```
