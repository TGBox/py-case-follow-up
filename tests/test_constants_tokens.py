"""Anti-regression guards for the design-token and localization rules.

Two cleanup passes moved every magic number, colour value, font size and
padding out of the widget code and into `src/constants.py`. Nothing stopped
the next feature from putting them straight back, so the scanners that drove
those passes live here as tests.

Three classes of defect are covered:

1. Literal design values (`padx=12`, `fg_color="gray30"`, `size=14`) in widget
   constructor / layout calls instead of a token from `constants.py`.
2. A name assigned twice in `constants.py`. The later assignment silently wins,
   which is how `COLOR_DANGER` rendered as `crimson` for months while the
   design token said `#dc2626`. Ruff's F811 does not catch plain module-level
   re-assignment, so it is checked here.
3. A widget selection mapped back to a program value by matching its label
   text. The label is whatever tr(...) produced, so that works only in the one
   language it was written for - it made the Cobra import silently overwrite
   practices instead of skipping them as soon as the UI ran in English or
   Swedish, and it left the tag dialog opening the wrong tab.
"""

import ast
from dataclasses import dataclass
from pathlib import Path

import pytest

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
CONSTANTS_FILE = SRC_DIR / "constants.py"


def iter_source_files(skip_constants: bool = True):
    """All application modules under src/, newest checkout layout."""
    for path in sorted(SRC_DIR.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        if skip_constants and path.name == "constants.py":
            continue
        yield path


def parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def rel(path: Path) -> str:
    return path.relative_to(SRC_DIR.parent).as_posix()


# ============================================================================
# 1. Design tokens instead of literal values
# ============================================================================

@dataclass
class TokenViolation:
    file: str
    line: int
    call: str
    argument: str
    value: str

    def __str__(self) -> str:
        return f"{self.file}:{self.line} - {self.call}({self.argument}={self.value})"


#: Keyword arguments carrying a dimension. 0 and 1 stay allowed: they mean
#: "no padding" / "hairline border" and a token would only obscure that.
DIMENSION_KWARGS = {
    "padx", "pady", "ipadx", "ipady", "width", "height", "corner_radius",
    "border_width", "border_spacing", "wraplength", "minsize",
}

#: Keyword arguments carrying a colour. Tuples are (light, dark) pairs.
COLOR_KWARGS = {
    "fg_color", "bg_color", "text_color", "text_color_disabled", "hover_color",
    "border_color", "progress_color", "button_color", "button_hover_color",
    "checkmark_color", "placeholder_text_color", "scrollbar_button_color",
    "scrollbar_button_hover_color", "dropdown_fg_color", "dropdown_hover_color",
    "dropdown_text_color",
}

ALLOWED_DIMENSIONS = {0, 1}
ALLOWED_COLORS = {"transparent"}


class DesignTokenScanner(ast.NodeVisitor):
    """Flags literal dimensions, colours and font sizes in widget calls."""

    def __init__(self, file_label: str):
        self.file = file_label
        self.violations: list[TokenViolation] = []

    def _flag(self, node: ast.AST, call: str, argument: str, value) -> None:
        self.violations.append(TokenViolation(self.file, node.lineno, call, argument, repr(value)))

    @staticmethod
    def _call_name(node: ast.Call) -> str:
        if isinstance(node.func, ast.Attribute):
            return node.func.attr
        if isinstance(node.func, ast.Name):
            return node.func.id
        return "<call>"

    def _check_dimension(self, node: ast.Call, call: str, kw: ast.keyword) -> None:
        value = kw.value
        if isinstance(value, ast.Constant) and isinstance(value.value, (int, float)) and not isinstance(value.value, bool):
            if value.value not in ALLOWED_DIMENSIONS:
                self._flag(node, call, kw.arg or "", value.value)
        elif isinstance(value, ast.Tuple):
            numbers = [e.value for e in value.elts if isinstance(e, ast.Constant) and isinstance(e.value, (int, float))]
            if len(numbers) == len(value.elts) and any(n not in ALLOWED_DIMENSIONS for n in numbers):
                self._flag(node, call, kw.arg or "", tuple(numbers))

    def _check_color(self, node: ast.Call, call: str, kw: ast.keyword) -> None:
        value = kw.value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            if value.value not in ALLOWED_COLORS:
                self._flag(node, call, kw.arg or "", value.value)
        elif isinstance(value, ast.Tuple):
            strings = [e.value for e in value.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
            if strings and len(strings) == len(value.elts):
                self._flag(node, call, kw.arg or "", tuple(strings))

    def _check_font(self, node: ast.Call, call: str, kw: ast.keyword) -> None:
        """Font sizes hide one level down, in the CTkFont(...) call itself."""
        value = kw.value
        if isinstance(value, ast.Call):
            for inner in value.keywords:
                if inner.arg == "size" and isinstance(inner.value, ast.Constant) and isinstance(inner.value.value, (int, float)):
                    self._flag(node, call, "font.size", inner.value.value)
        elif isinstance(value, ast.Tuple):
            for element in value.elts:
                if isinstance(element, ast.Constant) and isinstance(element.value, (int, float)):
                    self._flag(node, call, "font", element.value)

    def visit_Call(self, node: ast.Call) -> None:
        call = self._call_name(node)
        for kw in node.keywords:
            if kw.arg in DIMENSION_KWARGS:
                self._check_dimension(node, call, kw)
            elif kw.arg in COLOR_KWARGS:
                self._check_color(node, call, kw)
            elif kw.arg == "font":
                self._check_font(node, call, kw)
        self.generic_visit(node)


class TestDesignTokensInsteadOfLiterals:
    """Every dimension, colour and font size comes from constants.py."""

    def test_no_literal_design_values_in_widget_calls(self):
        violations: list[TokenViolation] = []
        for path in iter_source_files():
            scanner = DesignTokenScanner(rel(path))
            scanner.visit(parse(path))
            violations.extend(scanner.violations)

        assert not violations, (
            f"{len(violations)} literal design values found - move them to src/constants.py "
            f"and import the token instead:\n" + "\n".join(str(v) for v in violations[:25])
        )

    def test_scanner_still_detects_a_planted_violation(self):
        """Guards the guard: a scanner that silently stops matching is worthless."""
        scanner = DesignTokenScanner("<planted>")
        scanner.visit(ast.parse(
            'ctk.CTkButton(parent, width=137, fg_color="gray30", font=ctk.CTkFont(size=13))'
        ))
        found = {v.argument for v in scanner.violations}
        assert found == {"width", "fg_color", "font.size"}, f"scanner missed something: {found}"

    def test_zero_and_one_stay_allowed(self):
        """padx=0 and border_width=1 are intent, not magic numbers."""
        scanner = DesignTokenScanner("<planted>")
        scanner.visit(ast.parse('w.pack(padx=0, pady=(0, 1))\nctk.CTkFrame(p, border_width=1, fg_color="transparent")'))
        assert not scanner.violations, [str(v) for v in scanner.violations]


# ============================================================================
# 2. constants.py defines every name exactly once
# ============================================================================

class TestConstantsModuleIntegrity:
    """A name assigned twice means the later value silently wins."""

    def test_no_duplicate_definitions(self):
        tree = parse(CONSTANTS_FILE)
        first_seen: dict[str, int] = {}
        duplicates: list[str] = []

        for node in tree.body:
            targets: list[str] = []
            if isinstance(node, ast.Assign):
                targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                targets = [node.target.id]
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                targets = [node.name]

            for name in targets:
                if name in first_seen:
                    duplicates.append(f"{name}: line {first_seen[name]} and line {node.lineno}")
                first_seen[name] = node.lineno

        assert not duplicates, (
            "constants.py defines these names more than once - the last assignment wins, "
            "so the earlier one is a silent lie:\n" + "\n".join(duplicates)
        )

    def test_every_imported_constant_exists(self):
        """An import of a token that was renamed away fails at import time in
        production but can hide in a rarely-loaded dialog, so check statically."""
        tree = parse(CONSTANTS_FILE)
        defined: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                defined.update(t.id for t in node.targets if isinstance(t, ast.Name))
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                defined.add(node.target.id)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                defined.add(node.name)
            elif isinstance(node, ast.ImportFrom):
                defined.update(alias.asname or alias.name for alias in node.names)

        missing: list[str] = []
        for path in iter_source_files():
            for node in ast.walk(parse(path)):
                if isinstance(node, ast.ImportFrom) and node.module == "constants":
                    for alias in node.names:
                        if alias.name not in defined:
                            missing.append(f"{rel(path)}:{node.lineno} imports unknown '{alias.name}'")

        assert not missing, "constants.py does not define:\n" + "\n".join(missing)


# ============================================================================
# 3. Translated menus map back by position, never by label text
# ============================================================================

#: (module, list of key/default pairs, tuple of program values). The menu shows
#: the translated pairs; the dialog maps the selected *position* onto the value
#: tuple. Both must stay the same length or that mapping goes silently wrong.
INDEX_ALIGNED_CHOICES = [
    ("src/constants.py", "COBRA_CONFLICT_MODE_CHOICES", "src/constants.py", "COBRA_CONFLICT_MODE_KEYS"),
    ("src/ui/dialogs/profile_settings_ui_tab.py", "POPUP_TARGET_CHOICES", "src/constants.py", "POPUP_DISPLAY_TARGETS"),
    ("src/ui/dialogs/profile_settings_ai_tab.py", "AI_PROVIDER_CHOICES", "src/ui/dialogs/profile_settings_ai_tab.py", "AI_PROVIDER_KEYS"),
    ("src/ui/dialogs/tag_management_dialog.py", "TAG_TAB_CHOICES", "src/ui/dialogs/tag_management_dialog.py", "TAG_TAB_KEYS"),
]

#: Widget attributes whose .get() returns a technical value that never goes
#: through tr(...) - a model id, a file path. Comparing those against a literal
#: is fine. Add to this set rather than weakening the check.
TECHNICAL_VALUE_WIDGETS: set[str] = set()

#: Attribute call that reads a widget's *displayed* selection. dict.get(key)
#: takes an argument and is therefore not one of these, and .cget(...) returns
#: configuration rather than a label, so neither is treated as one.
WIDGET_READ_ATTR = "get"


def _is_widget_read(node: ast.AST) -> bool:
    """`combo.get()` - an attribute call named get, taking no arguments."""
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == WIDGET_READ_ATTR
        and not node.args
        and not node.keywords
        and not (isinstance(node.func.value, ast.Attribute) and node.func.value.attr in TECHNICAL_VALUE_WIDGETS)
        and not (isinstance(node.func.value, ast.Name) and node.func.value.id in TECHNICAL_VALUE_WIDGETS)
    )


def _reads_widget_label(node: ast.AST, tracked: set[str]) -> bool:
    """True if the expression carries a widget's displayed selection.

    Directly (`combo.get()`, `combo.get().upper()`) or through a local the
    function assigned from such a call - the indirect form is how the real
    occurrences of this bug were written.
    """
    if any(_is_widget_read(sub) for sub in ast.walk(node)):
        return True
    return any(isinstance(sub, ast.Name) and sub.id in tracked for sub in ast.walk(node))


def find_label_comparisons(source: str, file_label: str) -> list[str]:
    """Locates comparisons of a string literal against a translated widget label."""
    tree = ast.parse(source)
    offenders: list[str] = []

    # Scope the tracked locals per function, so a name reused elsewhere in the
    # module does not leak into an unrelated comparison.
    scopes: list[ast.AST] = [tree] + [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    for scope in scopes:
        tracked: set[str] = set()
        for node in ast.walk(scope):
            if isinstance(node, ast.Assign) and _is_widget_read(node.value):
                tracked.update(t.id for t in node.targets if isinstance(t, ast.Name))

        for node in ast.walk(scope):
            if not isinstance(node, ast.Compare):
                continue
            operands = [node.left, *node.comparators]
            literals = [
                o.value for o in operands
                if isinstance(o, ast.Constant) and isinstance(o.value, str) and o.value.strip()
            ]
            if not literals:
                continue
            if any(_reads_widget_label(o, tracked) for o in operands if not isinstance(o, ast.Constant)):
                entry = f"{file_label}:{node.lineno} compares a widget label against {literals[0]!r}"
                if entry not in offenders:
                    offenders.append(entry)
    return offenders


def literal_value(module_path: str, name: str):
    """Reads a module-level literal without importing the module.

    Importing would drag customtkinter and a display into a test that only
    needs to count entries.
    """
    path = SRC_DIR.parent / module_path
    for node in parse(path).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError(f"{module_path} does not define {name}")


class TestTranslatedChoiceMenus:
    """Selections are resolved by position, so they survive a language switch."""

    @pytest.mark.parametrize(
        ("choices_module", "choices_name", "values_module", "values_name"),
        INDEX_ALIGNED_CHOICES,
    )
    def test_choices_and_values_stay_index_aligned(self, choices_module, choices_name, values_module, values_name):
        choices = literal_value(choices_module, choices_name)
        values = literal_value(values_module, values_name)
        assert len(choices) == len(values), (
            f"{choices_name} has {len(choices)} entries but {values_name} has {len(values)}. "
            f"The dialog maps the selected menu position onto {values_name}, so adding an option "
            f"without its program value mis-assigns every entry after it."
        )

    def test_choice_keys_are_translation_keys(self):
        """Each pair is (locale key, German default) - a bare label would mean
        the option never gets translated at all."""
        for choices_module, choices_name, _, _ in INDEX_ALIGNED_CHOICES:
            for entry in literal_value(choices_module, choices_name):
                assert isinstance(entry, (tuple, list)) and len(entry) == 2, f"{choices_name}: {entry!r} is not a (key, default) pair"
                key, default = entry
                assert "." in key and " " not in key, f"{choices_name}: '{key}' does not look like a locale key"
                assert default.strip(), f"{choices_name}: '{key}' has an empty German default"

    def test_no_literal_matching_against_widget_labels(self):
        """Forbids `if "Hauptbildschirm" in combo.get()` and friends.

        The label a widget returns is whatever tr(...) produced, so comparing it
        against any literal quietly stops matching in another language. Resolve
        the selection with BaseDialog.selected_choice_index() instead.
        """
        offenders: list[str] = []
        for path in iter_source_files():
            offenders.extend(find_label_comparisons(path.read_text(encoding="utf-8"), rel(path)))

        assert not offenders, (
            "A translated widget label is being matched against literal text:\n"
            + "\n".join(offenders)
        )

    def test_scanner_catches_every_shape_that_shipped(self):
        """Guards the guard, with the four forms this codebase actually had."""
        shipped = {
            "inline": 'if "Hauptbildschirm" in self.popup_target_combo.get():\n    pass\n',
            "via variable": (
                "def save(self):\n"
                "    raw_mode = self.mode_combo.get()\n"
                '    if "\u00fcberspringen" in raw_mode.lower():\n'
                "        pass\n"
            ),
            "chained": 'x = "GEMINI" if "GEMINI" in self.ai_provider_seg.get().upper() else "OLLAMA"\n',
            "tab caption": 'def f(self):\n    curr = self.tabview.get()\n    if "Programmbereiche" in curr:\n        pass\n',
        }
        for label, source in shipped.items():
            assert find_label_comparisons(source, "<planted>"), f"scanner missed the {label} form"

        allowed = {
            # A program value the widget never displayed.
            "program value": (
                "def save(self):\n"
                "    target = self.profile.ui_settings.popup_display_target\n"
                '    if target == "PRIMARY_SCREEN":\n'
                "        pass\n"
            ),
            # dict.get(key) takes an argument - not a widget read.
            "dict lookup": 'if "/pages/" in page.get("url"):\n    pass\n',
            # cget returns configuration, not a translated caption.
            "widget config": 'if str(widget.cget("state")) == "normal":\n    pass\n',
        }
        for label, source in allowed.items():
            assert not find_label_comparisons(source, "<planted>"), f"false positive on the {label} form"
