"""Static checks over repo files: no hardcoded UI strings, clean unicode, pre-push hook vs CI, PyInstaller bundling."""

import ast
import json
import re
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "src"


# --- AST scanner for hardcoded user-visible strings ---------------------------

@dataclass
class ASTViolation:
    file_path: str
    line: int
    component: str
    argument: str
    raw_value: str

    def __str__(self) -> str:
        return f"{self.file_path}:{self.line} - {self.component}({self.argument}={self.raw_value!r})"


class I18nASTScanner(ast.NodeVisitor):
    """Flags string literals passed to UI widgets/popups instead of tr(...) or a LocalizedDict."""

    UI_WIDGET_CLASSES = {
        "CTkButton", "CTkLabel", "CTkEntry", "CTkCheckBox", "CTkRadioButton",
        "CTkSwitch", "CTkOptionMenu", "CTkComboBox", "CTkSegmentedButton",
        "CTkTabview", "CTkTextbox", "ToastNotification", "DatePickerWidget",
        "SearchableComboBox", "CTkProgressBar", "CTkSlider", "CTkScrollableFrame",
    }
    USER_VISIBLE_KWARGS = {
        "text", "placeholder_text", "title", "message", "dialog_title",
        "header_text", "confirm_text", "cancel_text", "tooltip_text",
    }
    POPUP_FUNCTION_NAMES = {
        "askopenfilename", "askopenfilenames", "asksaveasfilename", "askdirectory",
        "showinfo", "showwarning", "showerror", "askquestion", "askokcancel", "askyesno",
    }
    LOGGING_NAMES = {"debug", "info", "warning", "error", "critical", "exception", "log"}
    EXEMPT_EXACT_STRINGS = {
        "", " ", "  ", "\n", "\t", "\r",
        "+", "-", "*", "/", "%", "=", "==", "!=", "<", ">", "<=", ">=",
        ":", ";", ",", ".", "...", "::", "⇅", "↑", "↓", "←", "→", "•", "·", "|",
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "-1", "0.0", "100%",
        "transparent", "gray10", "gray14", "gray20", "gray28", "gray30", "gray40",
        "gray50", "gray60", "gray70", "gray80", "gray85", "gray90", "gray95",
        "white", "black", "forestgreen", "darkred", "gray", "red", "green", "blue",
        "orange", "yellow", "lightblue", "darkgreen", "navy", "crimson",
        "w", "e", "n", "s", "ne", "nw", "se", "sw", "center",
        "left", "right", "top", "bottom", "both", "x", "y", "none",
        "normal", "disabled", "readonly", "zoomed", "horizontal", "vertical",
        "ew", "nsew", "ns", "sn", "Arial", "Roboto", "Segoe UI", "Helvetica", "Courier", "Consolas",
        "bold", "italic", "underline",
        "case_id", "customer_id", "id", "status", "urgency", "title", "description",
        "created_at", "updated_at", "workflow_status", "is_completed", "channel",
        "actor", "tags", "schema_id", "priority", "key", "name", "type", "val",
        "utf-8", "utf8", "latin-1", "cp1252", "ascii",
        "dark", "light", "system",
    }
    EXEMPT_PREFIXES = (
        "http://", "https://", "sqlite:///", "file://", "mailto:",
        "data:", "icon_", "img_", "theme_", "assets/", "locales/",
    )
    EXEMPT_EXTENSIONS = (
        ".json", ".csv", ".txt", ".backup", ".zip", ".ics",
        ".png", ".ico", ".html", ".md", ".py", ".svg",
    )

    def __init__(self, file_path: str = "<string>"):
        self.file_path = file_path
        self.violations: list[ASTViolation] = []

    def is_exempt_string(self, text: str) -> bool:
        stripped = text.strip()
        if not stripped or text in self.EXEMPT_EXACT_STRINGS or stripped.lower() in self.EXEMPT_EXACT_STRINGS:
            return True
        if re.match(r"^#[0-9a-fA-F]{3,8}$", stripped):  # hex color
            return True
        if re.match(r"^-?\d+(\.\d+)?$", stripped) or re.match(r"^\d+x\d+(\+\d+\+\d+)?$", stripped):
            return True
        if stripped.startswith(self.EXEMPT_PREFIXES) or stripped.endswith(self.EXEMPT_EXTENSIONS):
            return True
        if stripped.startswith(("^", "r'", 'r"', "(?", ".*", "\\")):  # regex
            return True
        # Single emojis or short symbols only (e.g. "🔔 0", "✓")
        return bool(re.match(r"^[☀-➿\U0001f300-\U0001f9ff\s0-9\+\-\:\.]{1,4}$", stripped))

    def is_tr_or_localized(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and (
                func.id in ("tr", "_", "gettext") or (func.id.startswith("get_") and func.id.endswith("_display"))
            ):
                return True
            if isinstance(func, ast.Attribute) and func.attr == "tr":
                return True
            if isinstance(func, ast.Attribute) and func.attr == "format" and self.is_tr_or_localized(func.value):
                return True
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
            name = node.value.id
            return name.startswith(("DISPLAY_", "DIALOG_", "STATUS_", "UI_")) or "LOCALIZED" in name or "MAP" in name
        return False

    def visit_Call(self, node: ast.Call) -> None:
        func_name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
        if func_name in self.LOGGING_NAMES:
            return
        if func_name in self.UI_WIDGET_CLASSES or func_name == "configure":
            for kw in node.keywords:
                if kw.arg in self.USER_VISIBLE_KWARGS:
                    self._check(node, func_name, kw.arg, kw.value)
        elif func_name == "title" and len(node.args) == 1:
            self._check(node, "window.title", "title", node.args[0])
        elif func_name in self.POPUP_FUNCTION_NAMES:
            for kw in node.keywords:
                if kw.arg in ("title", "message"):
                    self._check(node, func_name, kw.arg, kw.value)
        self.generic_visit(node)

    def _check(self, node: ast.Call, component: str, arg: str, value: ast.AST) -> None:
        if self.is_tr_or_localized(value):
            return
        literals = []
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            literals = [value.value]
        elif isinstance(value, ast.List) and arg == "values":
            literals = [e.value for e in value.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
        for lit in literals:
            if not self.is_exempt_string(lit):
                self.violations.append(ASTViolation(self.file_path, node.lineno, component, arg, lit))


def scan_source(code: str, file_path: str = "<string>") -> list[ASTViolation]:
    scanner = I18nASTScanner(file_path)
    scanner.visit(ast.parse(code, filename=file_path))
    return scanner.violations


@pytest.mark.parametrize("code", [
    'btn = ctk.CTkButton(parent, text=tr("ui_buttons.save", "Speichern"), command=on_save)',
    'lbl = ctk.CTkLabel(parent, text=DIALOG_TITLES["new_case"])',
    'entry = ctk.CTkEntry(parent, placeholder_text=tr("cockpit.search_placeholder", "Suche..."))',
    'lbl.configure(text=tr("cockpit.save", "Speichern"))',
    'path = filedialog.askopenfilename(title=tr("dialog_titles.zip_import", "Datei wählen"))',
    'lbl1 = ctk.CTkLabel(parent, text="", fg_color="#ffffff", text_color="transparent")\n'
    'lbl2 = ctk.CTkLabel(parent, text="+", font=("Segoe UI", 12, "bold"))\n'
    'btn = ctk.CTkButton(parent, text="1440x880", width=120)',
    'logger.info("Starte Support-Cockpit Anwendung...")\nlogger.error("Fehler beim Laden der Praxis-Datenbank")',
], ids=["tr", "localized_dict", "tr_placeholder", "configure_tr", "popup_tr", "exempt_tokens", "logging"])
def test_scanner_accepts_localized_and_exempt_strings(code):
    assert scan_source(code) == []


@pytest.mark.parametrize("code,component,argument,value", [
    ('\nbtn = ctk.CTkButton(parent, text="Speichern", command=on_save)', "CTkButton", "text", "Speichern"),
    ('lbl = ctk.CTkLabel(parent, text="Patientenakte & Stammdaten")', "CTkLabel", "text", "Patientenakte & Stammdaten"),
    ('e = ctk.CTkEntry(parent, placeholder_text="Bitte Suchbegriff eingeben...")', "CTkEntry", "placeholder_text",
     "Bitte Suchbegriff eingeben..."),
    ('lbl.configure(text="Ungültige Eingabe")', "configure", "text", "Ungültige Eingabe"),
    ('p = filedialog.askopenfilename(title="Wählen Sie eine Backup-Datei aus")', "askopenfilename", "title",
     "Wählen Sie eine Backup-Datei aus"),
])
def test_scanner_flags_hardcoded_literals(code, component, argument, value):
    violations = scan_source(code)
    assert [(v.component, v.argument, v.raw_value) for v in violations] == [(component, argument, value)]
    assert violations[0].line == code.count("\n", 0, code.index(component)) + 1


@pytest.mark.parametrize("subdir", [
    "services", "models", "utils", "ui/views", "ui/widgets", "ui/app.py", "ui/app_dialogs.py",
])
def test_source_subsystem_has_no_hardcoded_ui_strings(subdir):
    target = SRC / subdir
    files = [target] if target.suffix == ".py" else sorted(target.glob("*.py"))
    assert files and all(f.exists() for f in files), f"src/{subdir} not found"
    violations = [v for f in files for v in scan_source(f.read_text(encoding="utf-8"), str(f.relative_to(REPO)))]
    assert not violations, f"{len(violations)} hardcoded UI strings:\n" + "\n".join(map(str, violations[:10]))


def test_registered_labels_do_not_glue_tr_into_an_f_string():
    """A label handed to register_i18n must carry its key, not a finished string.

    register_i18n rebuilds a widget's text from key + placeholders on every
    language change. An f-string that merely embeds tr(...) freezes the
    build-time language and keeps translators from moving the embedded value.
    Views that re-render wholesale (board, cockpit, case list) are not covered.
    """
    def embeds_tr(node: ast.AST) -> bool:
        return isinstance(node, ast.JoinedStr) and any(
            isinstance(p, ast.Call) and getattr(p.func, "id", None) == "tr" for p in ast.walk(node)
        )

    offenders = []
    for path in sorted(SRC.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"), filename=str(path))):
            if not (isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "register_i18n" and node.args):
                continue
            widget_call = node.args[0]
            if isinstance(widget_call, ast.Call) and any(
                kw.arg in ("text", "placeholder_text") and embeds_tr(kw.value) for kw in widget_call.keywords
            ):
                offenders.append(f"{path.relative_to(SRC)}:{node.lineno}")
    assert not offenders, "register_i18n mit tr() im f-String: " + ", ".join(offenders)


# --- Unicode cleanliness ------------------------------------------------------

def test_no_invisible_unicode_control_characters_in_src():
    """Anti-regression: variation selectors / zero-width chars must not sneak back into src/*.py."""
    forbidden = {"️": "VS-16", "︎": "VS-15", "​": "ZERO WIDTH SPACE", "﻿": "BOM/ZWNBSP"}
    violations = [
        f"{f.relative_to(REPO)} contains {name}"
        for f in SRC.rglob("*.py")
        for ch, name in forbidden.items()
        if ch in f.read_text(encoding="utf-8")
    ]
    assert not violations, "\n".join(violations)


# --- Git pre-push hook vs. CI -------------------------------------------------
# The hook once missed the ruff job from CI, so an E731 passed the push and only
# failed in GitHub Actions. These tests keep hook and workflow in lockstep.

HOOK_PATH = REPO / ".githooks" / "pre-push"
WORKFLOW_PATH = REPO / ".github" / "workflows" / "tests.yml"
# Must run verbatim as in CI. pytest/pyinstaller differ deliberately (--no-cov, --noconfirm).
EXACT_CI_CHECKS = ("uv run ruff check", "uvx pyright")


def test_pre_push_runs_lint_typecheck_build_tests_in_order():
    """Cheap checks first; the build must still precede pytest (dist/ is gitignored, the bundle test needs it)."""
    assert HOOK_PATH.exists(), ".githooks/pre-push must exist"
    hook = HOOK_PATH.read_text(encoding="utf-8")
    assert "py-case-follow-up.spec" in hook
    steps = [hook.find(s) for s in ("uv run ruff check", "uvx pyright", "uv run pyinstaller", "uv run pytest")]
    assert min(steps) != -1, "Ein Schritt fehlt im Hook"
    assert steps == sorted(steps), "Reihenfolge muss Lint -> Typecheck -> Build -> Tests sein"


def test_pre_push_covers_every_static_check_from_ci():
    """Every CI 'run:' line starting an EXACT_CI_CHECKS command must appear verbatim in the hook."""
    assert WORKFLOW_PATH.exists(), ".github/workflows/tests.yml must exist"
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    hook = HOOK_PATH.read_text(encoding="utf-8")
    ci_commands = [m.group(1).strip() for m in re.finditer(r"^\s*run:\s*(.+)$", workflow, re.MULTILINE)]
    relevant = [c for c in ci_commands if c.startswith(EXACT_CI_CHECKS)]
    assert relevant, "Keine der erwarteten CI-Prüfungen in tests.yml gefunden"
    missing = [c for c in relevant if c not in hook]
    assert not missing, f"Diese CI-Prüfungen fehlen im pre-push-Hook (oder laufen mit anderem Umfang): {missing}"


# --- PyInstaller bundle -------------------------------------------------------

REBUILD_HINT = "uv run pyinstaller py-case-follow-up.spec"


def test_spec_file_bundles_locales():
    spec = (REPO / "py-case-follow-up.spec").read_text(encoding="utf-8")
    assert "('locales', 'locales')" in spec or '("locales", "locales")' in spec


def _stale_build_inputs(exe_path: Path) -> list[str]:
    """Build inputs newer than the executable (dist/ is a gitignored local leftover)."""
    exe_mtime = exe_path.stat().st_mtime
    inputs = [REPO / "py-case-follow-up.spec", *sorted((REPO / "locales").glob("*.json"))]
    return [str(p.relative_to(REPO)) for p in inputs if p.exists() and p.stat().st_mtime > exe_mtime]


def test_built_executable_contains_locales():
    """If a current dist/py-case-follow-up.exe exists, verify all locale files are bundled.

    Skips without a build or with a build older than spec/locales. A current
    build that misses a locale is a real packaging bug and fails.
    """
    exe_path = REPO / "dist" / "py-case-follow-up.exe"
    if not exe_path.exists():
        pytest.skip(f"dist/py-case-follow-up.exe has not been built yet - build it with: {REBUILD_HINT}")
    stale_inputs = _stale_build_inputs(exe_path)
    if stale_inputs:
        pytest.skip(
            f"dist/py-case-follow-up.exe is older than {', '.join(stale_inputs)} - "
            f"rebuild to make this test meaningful: {REBUILD_HINT}"
        )

    from PyInstaller.archive.readers import CArchiveReader  # type: ignore

    reader = CArchiveReader(str(exe_path))
    locale_entries = [k for k in reader.toc if "locale" in k.lower()]
    for lang in ("de", "en", "sv"):
        assert any(f"{lang}.json" in k for k in locale_entries), (
            f"{lang}.json missing from an up-to-date build - check the datas entry in "
            f"py-case-follow-up.spec. Bundled locale entries: {sorted(locale_entries)}"
        )
    translations = {
        Path(k).stem: json.loads(reader.extract(k).decode("utf-8")) for k in locale_entries if k.endswith(".json")
    }
    assert translations["de"]["common"]["save"] == "Speichern"
    assert translations["en"]["common"]["save"] == "Save"
    assert translations["sv"]["common"]["save"] == "Spara"
