# Technical Handoff Report: Milestone 3 (UI Views & Widgets String Extraction) — Challenger 2

**Verdict**: **REQUEST_CHANGES**

---

## 1. Observation

A full empirical stress-test and adversarial audit was conducted on the Milestone 3 implementation covering `src/ui/views/`, `src/ui/widgets/`, `src/ui/app.py`, `src/ui/app_dialogs.py`, and `locales/*.json`.

### A. Locale Parity & Static Extraction Checks (Passed)
1. **Key Parity**:
   - `locales/de.json`: 1206 flattened keys
   - `locales/en.json`: 1206 flattened keys
   - `locales/sv.json`: 1206 flattened keys
   - Symmetric difference across DE, EN, SV: 0 keys (100% mutual parity).
2. **Placeholder Parameter Parity**:
   - Analyzed all `{placeholder}` format tokens across all 1206 keys.
   - Result: 0 placeholder mismatches between German, English, and Swedish definitions.
3. **Static AST Call Coverage**:
   - 306 static `tr(...)` calls in M3 target files analyzed.
   - 0 missing keys, 0 placeholder/kwarg mismatches, 0 untranslated German terms in `en.json` or `sv.json`.
4. **Pytest Suite**:
   - `.venv\Scripts\python.exe -m pytest` executed with 439 passed in 127s.

### B. Confirmed Empirical Defects (Failed)

#### Defect 1: `UnboundLocalError` in `SupportCockpitApp.__init__` (`src/ui/app.py:89`)
- **Verbatim Error**:
  ```
  Traceback (most recent call last):
    File "<string>", line 9, in <module>
      app = SupportCockpitApp(cfg)
    File "src/ui/app.py", line 89, in __init__
      self.title(tr("app.window_title", APP_WINDOW_TITLE))
                 ^^
  UnboundLocalError: cannot access local variable 'tr' where it is not associated with a value
  ```
- **Code Inspection**:
  - `src/ui/app.py:38`: Module-level import `from services.i18n_service import tr`.
  - `src/ui/app.py:89`: `self.title(tr("app.window_title", APP_WINDOW_TITLE))`.
  - `src/ui/app.py:127`: Inside `__init__`, a redundant local import `from services.i18n_service import tr` exists.
  - In Python, defining/importing `tr` at line 127 treats `tr` as local to the entire `__init__` function scope, causing `UnboundLocalError` when accessed at line 89. (Existing unit tests missed this because they instantiated via `SupportCockpitApp.__new__(SupportCockpitApp)` instead of `SupportCockpitApp(cfg)`).

#### Defect 2: `TclError` in `AttachmentWidget.refresh_ui_labels` on Repeated Language Switches (`src/ui/widgets/attachment_widget.py:62`)
- **Verbatim Error**:
  ```
  Traceback (most recent call last):
    File "<string>", line 26, in <module>
      aw.refresh_ui_labels()
    File "src/ui/widgets/attachment_widget.py", line 63, in refresh_ui_labels
      self.preview_label.configure(text=tr("attachments.no_preview", "Keine Datei zur Vorschau ausgewählt"))
    File ".../customtkinter/windows/widgets/ctk_label.py", line 240, in configure
      self._label.configure(text=self._text)
    _tkinter.TclError: invalid command name ".!attachmentwidget.!ctkframe3.!ctklabel.!label"
  ```
- **Code Inspection**:
  - In `create_widgets()`, `self.preview_label` is created.
  - In `refresh_ui_labels()`, line 68 calls `self.load_attachments(self.current_case)`, which invokes `self.clear_preview()`.
  - `self.clear_preview()` destroys all child widgets of `self.preview_frame`, destroying the Tkinter peer of `self.preview_label`.
  - On any subsequent call to `refresh_ui_labels()` (such as when switching language again, or during dynamic cascade in `CockpitView` and `TableView`), line 62 tests `hasattr(self, "preview_label")` (which evaluates to `True`), then invokes `.cget("text")` or `.configure()` on the destroyed widget, raising `_tkinter.TclError`.

---

## 2. Logic Chain

1. **Premise**: Milestone 3 requires that the main application shell and all UI views/widgets instantiate reliably and support continuous dynamic runtime language switching without unhandled exceptions or UI crashes.
2. **Defect 1 Chain**:
   - `src/ui/app.py` line 89 calls `tr(...)`.
   - `src/ui/app.py` line 127 contains a nested `from services.i18n_service import tr`.
   - Python's lexical scoping marks `tr` as a local variable within `__init__`.
   - Standard instantiation `SupportCockpitApp(config)` immediately aborts with `UnboundLocalError`.
3. **Defect 2 Chain**:
   - When language changes (e.g. DE -> EN -> SV), `on_language_changed()` calls `refresh_ui_labels()` across views.
   - `CockpitView` and `TableView` delegate to `AttachmentWidget.refresh_ui_labels()`.
   - The first invocation destroys `self.preview_label` via `clear_preview()`.
   - The second invocation accesses `self.preview_label` which is a destroyed Tcl widget, crashing the entire UI cascade with `TclError`.

---

## 3. Caveats

- `src/ui/dialogs/` (the 18 dialog files) is planned for Milestone 4 and was excluded from the M3 extraction scope.
- Key parity and placeholder accuracy across `locales/de.json`, `locales/en.json`, and `locales/sv.json` are in excellent condition (1206 keys, 0 discrepancies).

---

## 4. Conclusion

**Verdict**: **REQUEST_CHANGES**

The string extraction and locale parity are comprehensive, but two blocking runtime bugs prevent clean application startup and multi-cycle language switching:
1. Fix `UnboundLocalError` in `src/ui/app.py:89` by removing the redundant local import `from services.i18n_service import tr` at line 127 (or importing `tr` at the start of `__init__`).
2. Fix `TclError` in `src/ui/widgets/attachment_widget.py` by ensuring `self.preview_label` destruction is tracked (e.g., check `winfo_exists()` or set `self.preview_label = None` in `clear_preview()`).

---

## 5. Verification Method

To reproduce and verify the findings independently:

### Command 1: Reproduce App Instantiation Bug
```bash
.venv\Scripts\python.exe -c "
import sys; sys.path.insert(0, 'src')
from config import AppConfig
from ui.app import SupportCockpitApp
cfg = AppConfig()
app = SupportCockpitApp(cfg)
"
```
*Expected Result*: Fails with `UnboundLocalError: cannot access local variable 'tr' where it is not associated with a value`.

### Command 2: Reproduce AttachmentWidget Multi-Cycle Language Switch Bug
```bash
.venv\Scripts\python.exe -c "
import sys; sys.path.insert(0, 'src')
import customtkinter as ctk
from config import AppConfig
from services.attachment_service import AttachmentService
from services.i18n_service import get_i18n
from ui.widgets.attachment_widget import AttachmentWidget

root = ctk.CTk(); root.withdraw()
cfg = AppConfig()
aw = AttachmentWidget(root, attachment_service=AttachmentService(cfg))
i18n = get_i18n()
i18n.current_language = 'en'; aw.refresh_ui_labels()
i18n.current_language = 'sv'; aw.refresh_ui_labels()
"
```
*Expected Result*: Fails on second call with `_tkinter.TclError: invalid command name ".!attachmentwidget.!ctkframe3.!ctklabel.!label"`.
