# Empirical Challenge & Verification Report: Milestone 3 (UI Views & Widgets String Extraction)

**Verdict**: `REQUEST_CHANGES`

---

## 1. Observation

A full empirical investigation and adversarial stress-testing pass was executed on the Milestone 3 implementation covering all UI views, widgets, and dynamic runtime language switching.

### 1.1 Positive Verifications
1. **Full Baseline Test Suite**:
   - Command: `.venv\Scripts\python.exe -m pytest`
   - Result: `439 passed in 252.34s` (100% pass rate on existing test suite).
2. **AST Scanner Cleanliness**:
   - Command: `.venv\Scripts\python.exe -m pytest tests/test_ast_i18n_scanner.py`
   - Result: `18 passed in ~0.3s` (0 hardcoded UI literal violations across `src/ui/app.py`, `src/ui/app_dialogs.py`, `src/ui/views/`, and `src/ui/widgets/`).
3. **Translation Parity & Parameter Tokens**:
   - Command: `.venv\Scripts\python.exe -m pytest tests/test_translation_parity_and_quality.py`
   - Result: `29 passed` (100% key parity across `locales/de.json`, `locales/en.json`, and `locales/sv.json` with 1206 synchronized keys).
   - Placeholder token audit: Verified that 100% of format parameters (`{count}`, `{status}`, `{days}`, `{hours}`, etc.) match identically across DE, EN, and SV.
4. **Multi-Threaded Translation Safety & Parameter Robustness**:
   - Verified that `I18nService.tr(...)` handles missing keyword arguments, `None` values, extra parameters, and concurrent multi-threaded reads safely without throwing `KeyError` or crashes.

---

### 1.2 Confirmed Defect / Empirical Failure Mode

**Issue: Fatal `_tkinter.TclError` in `AttachmentWidget.refresh_ui_labels` on Consecutive Dynamic Language Switches**

- **File**: `src/ui/widgets/attachment_widget.py`
- **Lines**: 62–63 and 154–156
- **Verbatim Error**:
  ```
  _tkinter.TclError: invalid command name ".!cockpitview.!panedwindow.!ctktabview.!ctkframe2.!attachmentwidget.!ctkframe3.!ctklabel.!label"
  ```
- **Observed Mechanism**:
  1. In `AttachmentWidget.create_widgets()` (lines 40–44):
     ```python
     self.preview_frame = ctk.CTkFrame(self, height=120, fg_color=("gray90", "gray15"))
     self.preview_frame.pack(fill="x", padx=5, pady=2)
     
     self.preview_label = ctk.CTkLabel(self.preview_frame, text=tr("attachments.no_preview", "Keine Datei zur Vorschau ausgewählt"), font=ctk.CTkFont(size=11), text_color=("gray50", "gray60"))
     self.preview_label.pack(expand=True, pady=10)
     ```
  2. When `refresh_ui_labels()` runs (lines 56–68), it executes:
     ```python
     if hasattr(self, "preview_label") and not self.preview_label.cget("text").startswith("📄") and not self.preview_label.cget("text").startswith("🖼"):
         self.preview_label.configure(text=tr("attachments.no_preview", "Keine Datei zur Vorschau ausgewählt"))
     ...
     self.load_attachments(self.current_case)
     ```
  3. Inside `load_attachments()` (lines 74–75), `self.clear_preview()` is called:
     ```python
     def clear_preview(self):
         for w in self.preview_frame.winfo_children():
             w.destroy()
     ```
     This destroys all children of `self.preview_frame`, including `self.preview_label`.
  4. On any subsequent call to `refresh_ui_labels()` (such as switching language a second time, e.g. DE -> EN -> SV, or switching between cases and changing languages), `hasattr(self, "preview_label")` evaluates to `True`, but `self.preview_label` now references a destroyed Tk widget. Calling `self.preview_label.cget(...)` or `self.preview_label.configure(...)` immediately raises `_tkinter.TclError`.
  5. Because `SupportCockpitApp.on_language_changed` cascades to all views (`self.cockpit_view.refresh_ui_labels()` -> `self.attachment_widget.refresh_ui_labels()`), this crashes the application's runtime language switching.

---

## 2. Logic Chain

1. **Premise (R3)**: Requirement R3 mandates that switching languages at runtime updates all UI components dynamically without requiring an application restart or crashing the runtime.
2. **Observation**:
   - `AttachmentWidget.create_widgets()` assigns `self.preview_label`.
   - `clear_preview()` calls `w.destroy()` on all children of `preview_frame`, destroying `self.preview_label` at the Tk level without resetting `self.preview_label = None`.
   - On the next `refresh_ui_labels()` call, `hasattr(self, "preview_label")` is `True`, so `self.preview_label.cget(...)` is called on a destroyed widget, throwing `_tkinter.TclError`.
3. **Inference**:
   - Whenever an end-user switches languages more than once (e.g. German -> English -> Swedish) or switches languages while viewing cases in `CockpitView` or `TableView`, the application crashes with an unhandled Tk exception.
4. **Conclusion**:
   - Milestone 3 cannot be approved until `AttachmentWidget.refresh_ui_labels()` and `clear_preview()` are fixed to guard against destroyed widget references (e.g. by checking `self.preview_label.winfo_exists()` or safely managing `preview_label` lifecycle).

---

## 3. Caveats

- **Scope Boundary**: UI Dialogs in `src/ui/dialogs/` (all 18 dialog files) are designated for Milestone 4 and were not audited for hardcoded strings in this milestone.
- **Other Components**: All other views (`BoardView`, `TableView`, `AnalyticsView`, `CockpitView`) and widgets (`CaseListWidget`, `TimelineWidget`, `WikiWidget`, `DynamicFormWidget`, `DatePickerWidget`, `SearchableCombobox`, `ModuleTagPickerPopup`) demonstrated 100% stable behavior under rapid cycling and dynamic switching.

---

## 4. Conclusion

**Verdict**: `REQUEST_CHANGES`

### Required Fixes:
1. **Fix `AttachmentWidget` Widget Lifecycle**:
   In `src/ui/widgets/attachment_widget.py`:
   - In `refresh_ui_labels()`, guard `preview_label` access with `if hasattr(self, "preview_label") and self.preview_label is not None and self.preview_label.winfo_exists():` (or re-create `preview_label` when `preview_frame` is empty).
   - In `clear_preview()`, set `self.preview_label = None` or safely handle widget references when destroyed.

---

## 5. Verification Method

To independently reproduce and verify the defect and fixes:

1. **Run Adversarial Stress Test**:
   ```bash
   .venv\Scripts\python.exe -m pytest tests/test_adversarial_m3_ui_stress.py -v
   ```
   *Expected Failure*: `TestAttachmentWidgetDynamicRefreshBug::test_attachment_widget_consecutive_refresh_reproduction` fails with `_tkinter.TclError: invalid command name ".!attachmentwidget.!ctkframe3.!ctklabel.!label"`.

2. **Run Full Project Test Suite**:
   ```bash
   .venv\Scripts\python.exe -m pytest
   ```
