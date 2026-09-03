"""Comprehensive AST (Abstract Syntax Tree) scanner and automated test suite

to detect hardcoded user-visible text literals across UI components, dialogs,
views, and widgets in SupportCockpit.
"""

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import pytest


@dataclass
class ASTViolation:
    """Represents a detected hardcoded string literal in a UI element."""
    file_path: str
    line: int
    col: int
    component: str
    argument: str
    raw_value: str
    reason: str

    def __str__(self) -> str:
        return f"{self.file_path}:{self.line}:{self.col} - [{self.component}({self.argument}=\"{self.raw_value}\")] -> {self.reason}"


class I18nASTScanner(ast.NodeVisitor):
    """AST Visitor that inspects Python ASTs to ensure UI components use tr(...) or LocalizedDict."""

    # UI widget constructor class names to monitor
    UI_WIDGET_CLASSES = {
        "CTkButton", "CTkLabel", "CTkEntry", "CTkCheckBox", "CTkRadioButton",
        "CTkSwitch", "CTkOptionMenu", "CTkComboBox", "CTkSegmentedButton",
        "CTkTabview", "CTkTextbox", "ToastNotification", "DatePickerWidget",
        "SearchableComboBox", "CTkProgressBar", "CTkSlider", "CTkScrollableFrame"
    }

    # Keyword arguments that usually carry user-facing text
    USER_VISIBLE_KWARGS = {
        "text", "placeholder_text", "title", "message", "dialog_title",
        "header_text", "confirm_text", "cancel_text", "tooltip_text"
    }

    # File dialog / messagebox function names
    POPUP_FUNCTION_NAMES = {
        "askopenfilename", "askopenfilenames", "asksaveasfilename", "askdirectory",
        "showinfo", "showwarning", "showerror", "askquestion", "askokcancel", "askyesno"
    }

    # Common layout tokens, colors, punctuation, and system identifiers exempt from i18n
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
        "ew", "nsew", "ns", "sn", "nw", "se",
        "Arial", "Roboto", "Segoe UI", "Helvetica", "Courier", "Consolas",
        "bold", "italic", "underline",
        "case_id", "customer_id", "id", "status", "urgency", "title", "description",
        "created_at", "updated_at", "workflow_status", "is_completed", "channel",
        "actor", "tags", "schema_id", "priority", "key", "name", "type", "val",
        "utf-8", "utf8", "latin-1", "cp1252", "ascii",
        "dark", "light", "system",
    }

    # Known UI test/mock exemption paths or patterns
    EXEMPT_PREFIXES = (
        "http://", "https://", "sqlite:///", "file://", "mailto:",
        "data:", "icon_", "img_", "theme_", "assets/", "locales/"
    )

    EXEMPT_EXTENSIONS = (
        ".json", ".csv", ".txt", ".backup", ".zip", ".ics",
        ".png", ".ico", ".html", ".md", ".py", ".svg"
    )

    def __init__(self, file_path: str = "<string>"):
        self.file_path = file_path
        self.violations: list[ASTViolation] = []
        self._inside_logging = False

    def is_exempt_string(self, text: str) -> bool:
        """Check if a string literal is an exempt identifier, layout token, regex, color, or symbol."""
        if not isinstance(text, str):
            return True

        stripped = text.strip()
        if not stripped:
            return True

        if text in self.EXEMPT_EXACT_STRINGS or stripped.lower() in self.EXEMPT_EXACT_STRINGS:
            return True

        # Hex color: #123, #123456, #12345678
        if re.match(r"^#[0-9a-fA-F]{3,8}$", stripped):
            return True

        # Numeric values / coordinates / dimension strings (e.g. 1440x880, +100+100)
        if re.match(r"^-?\d+(\.\d+)?$", stripped):
            return True
        if re.match(r"^\d+x\d+(\+\d+\+\d+)?$", stripped):
            return True

        # System URLs, URIs, DB schemes
        if stripped.startswith(self.EXEMPT_PREFIXES):
            return True

        # File paths and extensions
        if stripped.endswith(self.EXEMPT_EXTENSIONS):
            return True

        # Regular expressions
        if stripped.startswith(("^", "r'", 'r"', "(?", ".*", "\\")):
            return True

        # Single emojis or short symbols only (e.g. "🔔 0", "✓", "❌")
        if re.match(r"^[\u2600-\u27bf\U0001f300-\U0001f9ff\s0-9\+\-\:\.]{1,4}$", stripped):
            return True

        return False

    def is_tr_or_localized_call(self, node: ast.AST) -> bool:
        """Check if an AST node represents a call to tr(...) or access to LocalizedDict."""
        if isinstance(node, ast.Call):
            # Direct tr(...) call
            if isinstance(node.func, ast.Name) and node.func.id in ("tr", "_", "gettext"):
                return True
            # Method call get_i18n().tr(...) or self.i18n.tr(...)
            if isinstance(node.func, ast.Attribute) and node.func.attr == "tr":
                return True
            # Enum display helpers (e.g. get_board_column_display, get_actor_display)
            if isinstance(node.func, ast.Name) and node.func.id.startswith("get_") and node.func.id.endswith("_display"):
                return True
            # Formatted tr call: tr(...).format(...)
            if isinstance(node.func, ast.Attribute) and node.func.attr == "format":
                if self.is_tr_or_localized_call(node.func.value):
                    return True

        # Subscript on LocalizedDict (e.g. DIALOG_TITLES["key"], DISPLAY_BOARD_COLUMN_NAMES["val"])
        if isinstance(node, ast.Subscript):
            if isinstance(node.value, ast.Name) and (
                node.value.id.startswith("DISPLAY_") or
                node.value.id.startswith("DIALOG_") or
                node.value.id.startswith("STATUS_") or
                node.value.id.startswith("UI_") or
                "LOCALIZED" in node.value.id or
                "MAP" in node.value.id
            ):
                return True

        return False

    def visit_Call(self, node: ast.Call) -> None:
        """Inspect all function and class instantiation calls."""
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        # Ignore logging calls
        if func_name in ("debug", "info", "warning", "error", "critical", "exception", "log"):
            return

        # 1. UI Widget Class Constructor (e.g. CTkButton(..., text="Speichern"))
        if func_name in self.UI_WIDGET_CLASSES:
            for kw in node.keywords:
                if kw.arg in self.USER_VISIBLE_KWARGS:
                    self._check_kwarg_value(node, func_name, kw.arg, kw.value)

        # 2. Widget .configure(...) call (e.g. btn.configure(text="Speichern"))
        elif func_name == "configure":
            for kw in node.keywords:
                if kw.arg in self.USER_VISIBLE_KWARGS:
                    self._check_kwarg_value(node, "configure", kw.arg, kw.value)

        # 3. Window .title(...) call (e.g. self.title("Neuer Fall"))
        elif func_name == "title":
            if node.args and len(node.args) == 1:
                self._check_arg_value(node, "window.title", "title", node.args[0])

        # 4. File dialog / message box popup calls
        elif func_name in self.POPUP_FUNCTION_NAMES:
            for kw in node.keywords:
                if kw.arg in ("title", "message"):
                    self._check_kwarg_value(node, func_name, kw.arg, kw.value)

        self.generic_visit(node)

    def _check_kwarg_value(self, node: ast.AST, component: str, arg_name: str, value_node: ast.AST) -> None:
        """Check if a keyword argument value is a hardcoded non-exempt string literal."""
        if self.is_tr_or_localized_call(value_node):
            return

        if isinstance(value_node, ast.Constant) and isinstance(value_node.value, str):
            if not self.is_exempt_string(value_node.value):
                self.violations.append(
                    ASTViolation(
                        file_path=self.file_path,
                        line=getattr(node, "lineno", 0),
                        col=getattr(node, "col_offset", 0),
                        component=component,
                        argument=arg_name,
                        raw_value=value_node.value,
                        reason=f"Hardcoded literal passed to {component}({arg_name}=...) without tr(...) or LocalizedDict"
                    )
                )

        # Check list of string literals passed to 'values' argument
        elif isinstance(value_node, ast.List) and arg_name == "values":
            for elem in value_node.elts:
                if isinstance(elem, ast.Constant) and isinstance(elem.value, str):
                    if not self.is_exempt_string(elem.value):
                        self.violations.append(
                            ASTViolation(
                                file_path=self.file_path,
                                line=getattr(node, "lineno", 0),
                                col=getattr(node, "col_offset", 0),
                                component=component,
                                argument=arg_name,
                                raw_value=elem.value,
                                reason=f"Hardcoded list option in {component}(values=[...]) without tr(...) or LocalizedDict"
                            )
                        )

    def _check_arg_value(self, node: ast.AST, component: str, arg_name: str, value_node: ast.AST) -> None:
        """Check if a positional argument value is a hardcoded non-exempt string literal."""
        if self.is_tr_or_localized_call(value_node):
            return

        if isinstance(value_node, ast.Constant) and isinstance(value_node.value, str):
            if not self.is_exempt_string(value_node.value):
                self.violations.append(
                    ASTViolation(
                        file_path=self.file_path,
                        line=getattr(node, "lineno", 0),
                        col=getattr(node, "col_offset", 0),
                        component=component,
                        argument=arg_name,
                        raw_value=value_node.value,
                        reason=f"Hardcoded positional string literal in {component}(...) without tr(...) or LocalizedDict"
                    )
                )


def scan_source_code(code: str, file_path: str = "<string>") -> list[ASTViolation]:
    """Parse and scan Python source code for i18n violations."""
    tree = ast.parse(code, filename=file_path)
    scanner = I18nASTScanner(file_path=file_path)
    scanner.visit(tree)
    return scanner.violations


def scan_python_file(file_path: Path | str) -> list[ASTViolation]:
    """Read, parse, and scan a Python file for i18n violations."""
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        return []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    return scan_source_code(content, file_path=str(path))


# ============================================================================
# Tier 1 & Tier 2: Unit Tests for AST Scanner Engine
# ============================================================================

class TestASTScannerUnitTests:
    """Test the precision and accuracy of the AST scanner against clean and violative code."""

    def test_clean_button_with_tr_passes(self):
        """A CTkButton using tr(...) produces 0 violations."""
        code = """
import customtkinter as ctk
from services.i18n_service import tr

btn = ctk.CTkButton(parent, text=tr("ui_buttons.save", "Speichern"), command=on_save)
"""
        violations = scan_source_code(code)
        assert len(violations) == 0

    def test_violative_button_with_hardcoded_literal_fails(self):
        """A CTkButton with hardcoded 'Speichern' produces a violation with line and col."""
        code = """
import customtkinter as ctk

btn = ctk.CTkButton(parent, text="Speichern", command=on_save)
"""
        violations = scan_source_code(code)
        assert len(violations) == 1
        assert violations[0].component == "CTkButton"
        assert violations[0].argument == "text"
        assert violations[0].raw_value == "Speichern"
        assert violations[0].line == 4

    def test_clean_label_with_localized_dict_subscript_passes(self):
        """A CTkLabel using LocalizedDict subscript access produces 0 violations."""
        code = """
import customtkinter as ctk
from constants import DIALOG_TITLES

lbl = ctk.CTkLabel(parent, text=DIALOG_TITLES["new_case"])
"""
        violations = scan_source_code(code)
        assert len(violations) == 0

    def test_violative_label_with_hardcoded_text_fails(self):
        """A CTkLabel with hardcoded 'Patientenakte & Stammdaten' produces a violation."""
        code = """
import customtkinter as ctk

lbl = ctk.CTkLabel(parent, text="Patientenakte & Stammdaten")
"""
        violations = scan_source_code(code)
        assert len(violations) == 1
        assert violations[0].component == "CTkLabel"
        assert violations[0].raw_value == "Patientenakte & Stammdaten"

    def test_clean_entry_with_tr_placeholder_passes(self):
        """A CTkEntry with tr(...) placeholder_text produces 0 violations."""
        code = """
import customtkinter as ctk
from services.i18n_service import tr

entry = ctk.CTkEntry(parent, placeholder_text=tr("cockpit.search_placeholder", "Suche..."))
"""
        violations = scan_source_code(code)
        assert len(violations) == 0

    def test_violative_entry_with_hardcoded_placeholder_fails(self):
        """A CTkEntry with hardcoded placeholder produces a violation."""
        code = """
import customtkinter as ctk

entry = ctk.CTkEntry(parent, placeholder_text="Bitte Suchbegriff eingeben...")
"""
        violations = scan_source_code(code)
        assert len(violations) == 1
        assert violations[0].component == "CTkEntry"
        assert violations[0].argument == "placeholder_text"
        assert violations[0].raw_value == "Bitte Suchbegriff eingeben..."

    def test_clean_configure_with_tr_passes(self):
        """A .configure(text=tr(...)) call produces 0 violations."""
        code = """
lbl.configure(text=tr("cockpit.save", "Speichern"))
"""
        violations = scan_source_code(code)
        assert len(violations) == 0

    def test_violative_configure_with_literal_fails(self):
        """A .configure(text="Ungültige Eingabe") call produces a violation."""
        code = """
lbl.configure(text="Ungültige Eingabe")
"""
        violations = scan_source_code(code)
        assert len(violations) == 1
        assert violations[0].component == "configure"
        assert violations[0].raw_value == "Ungültige Eingabe"

    def test_exempt_geometry_and_colors_pass(self):
        """Layout tokens, hex colors, and geometry strings produce 0 violations."""
        code = """
import customtkinter as ctk

lbl1 = ctk.CTkLabel(parent, text="", fg_color="#ffffff", text_color="transparent")
lbl2 = ctk.CTkLabel(parent, text="+", font=("Segoe UI", 12, "bold"))
btn = ctk.CTkButton(parent, text="1440x880", width=120)
"""
        violations = scan_source_code(code)
        assert len(violations) == 0

    def test_exempt_logging_calls_pass(self):
        """Logging messages with hardcoded text are completely ignored."""
        code = """
import logging
logger = logging.getLogger("SupportCockpit")

logger.info("Starte Support-Cockpit Anwendung...")
logger.error("Fehler beim Laden der Praxis-Datenbank")
"""
        violations = scan_source_code(code)
        assert len(violations) == 0

    def test_popup_filedialog_title_violation(self):
        """Hardcoded title in askopenfilename produces a violation."""
        code = """
from tkinter import filedialog

file_path = filedialog.askopenfilename(title="Wählen Sie eine Backup-Datei aus")
"""
        violations = scan_source_code(code)
        assert len(violations) == 1
        assert violations[0].component == "askopenfilename"
        assert violations[0].raw_value == "Wählen Sie eine Backup-Datei aus"

    def test_popup_filedialog_with_tr_title_passes(self):
        """askopenfilename with tr(...) title produces 0 violations."""
        code = """
from tkinter import filedialog
from services.i18n_service import tr

file_path = filedialog.askopenfilename(title=tr("dialog_titles.zip_import", "Datei wählen"))
"""
        violations = scan_source_code(code)
        assert len(violations) == 0


# ============================================================================
# Tier 2 & 3: Codebase Scanning & Cleanliness Verification
# ============================================================================

class TestASTScannerCodebaseIntegrity:
    """Run the AST scanner against clean core subsystems in the codebase."""

    def test_services_subsystem_has_zero_ui_violations(self):
        """Core services (storage, i18n, scoring, p2p, wiki) must have zero UI literal violations."""
        project_root = Path(__file__).resolve().parent.parent
        services_dir = project_root / "src" / "services"
        assert services_dir.exists()

        all_violations: list[ASTViolation] = []
        for py_file in services_dir.glob("*.py"):
            all_violations.extend(scan_python_file(py_file))

        assert not all_violations, (
            f"Found {len(all_violations)} UI text violations in src/services:\n" +
            "\n".join(str(v) for v in all_violations[:10])
        )

    def test_models_subsystem_has_zero_ui_violations(self):
        """Data models (case, customer, schema, profile) must have zero UI literal violations."""
        project_root = Path(__file__).resolve().parent.parent
        models_dir = project_root / "src" / "models"
        assert models_dir.exists()

        all_violations: list[ASTViolation] = []
        for py_file in models_dir.glob("*.py"):
            all_violations.extend(scan_python_file(py_file))

        assert not all_violations, (
            f"Found {len(all_violations)} UI text violations in src/models:\n" +
            "\n".join(str(v) for v in all_violations[:10])
        )

    def test_utils_subsystem_has_zero_ui_violations(self):
        """Utility modules in src/utils must have zero UI literal violations."""
        project_root = Path(__file__).resolve().parent.parent
        utils_dir = project_root / "src" / "utils"
        if utils_dir.exists():
            all_violations: list[ASTViolation] = []
            for py_file in utils_dir.glob("*.py"):
                all_violations.extend(scan_python_file(py_file))

            assert not all_violations, (
                f"Found {len(all_violations)} UI text violations in src/utils:\n" +
                "\n".join(str(v) for v in all_violations[:10])
            )

    def test_ui_views_subsystem_has_zero_ui_violations(self):
        """UI Views (cockpit, board, table, analytics) must have zero UI literal violations."""
        project_root = Path(__file__).resolve().parent.parent
        views_dir = project_root / "src" / "ui" / "views"
        assert views_dir.exists()

        all_violations: list[ASTViolation] = []
        for py_file in views_dir.glob("*.py"):
            all_violations.extend(scan_python_file(py_file))

        assert not all_violations, (
            f"Found {len(all_violations)} UI text violations in src/ui/views:\n" +
            "\n".join(str(v) for v in all_violations[:10])
        )

    def test_ui_widgets_subsystem_has_zero_ui_violations(self):
        """UI Widgets must have zero UI literal violations."""
        project_root = Path(__file__).resolve().parent.parent
        widgets_dir = project_root / "src" / "ui" / "widgets"
        assert widgets_dir.exists()

        all_violations: list[ASTViolation] = []
        for py_file in widgets_dir.glob("*.py"):
            all_violations.extend(scan_python_file(py_file))

        assert not all_violations, (
            f"Found {len(all_violations)} UI text violations in src/ui/widgets:\n" +
            "\n".join(str(v) for v in all_violations[:10])
        )

    def test_ui_app_and_dialogs_has_zero_ui_violations(self):
        """Main application shell and dialog launchers must have zero UI literal violations."""
        project_root = Path(__file__).resolve().parent.parent
        app_file = project_root / "src" / "ui" / "app.py"
        app_dialogs_file = project_root / "src" / "ui" / "app_dialogs.py"

        all_violations: list[ASTViolation] = []
        for py_file in (app_file, app_dialogs_file):
            if py_file.exists():
                all_violations.extend(scan_python_file(py_file))

        assert not all_violations, (
            f"Found {len(all_violations)} UI text violations in app / app_dialogs:\n" +
            "\n".join(str(v) for v in all_violations[:10])
        )
