"""constants/enums localization, LocalizedDict, datetime_utils formatting, and static design-token/label-matching guards over src/."""

import ast
from dataclasses import dataclass
from functools import cache
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from constants import (
    DISPLAY_ACTOR_NAMES,
    DISPLAY_BOARD_COLUMN_NAMES,
    DISPLAY_CHANNEL_NAMES,
    DISPLAY_LAYOUT_NAMES,
    HOTKEY_ACTION_LABELS,
    VALIDATION_MESSAGES,
    get_localized_departments,
    get_localized_handover_channels,
    get_localized_hotkey_action_labels,
    get_localized_menu_options_datenaustausch,
    get_localized_menu_options_stammdaten,
    get_localized_menu_options_vorlagen,
    get_localized_task_categories,
)
from enums import ACTOR_DISPLAY, Actor, get_actor_display, get_actor_val_from_display
from services.i18n_service import LocalizedDict, get_i18n
from utils.datetime_utils import (
    calculate_idle_days,
    format_date,
    format_datetime,
    format_german_date,
    format_german_datetime,
    format_german_time,
    format_time,
    get_relative_date_text,
    hours_until_deadline,
    parse_date,
)

LANGS = ["de", "en", "sv"]


def _set_lang(lang: str) -> None:
    get_i18n().current_language = lang


# ============================================================================
# Localized constants and enums
# ============================================================================

def test_localized_dict_lookup_and_fallbacks():
    ld = LocalizedDict("test_prefix", {"MY_KEY": "Default Value"})
    assert ld["MY_KEY"] == ld.get("MY_KEY") == "Default Value"
    assert ld.get("UNKNOWN", "Fallback") == "Fallback"
    assert ld["UNKNOWN"] == "UNKNOWN"


@pytest.mark.parametrize("lang,new_col,action_col,validation_word,new_case_label", [
    ("de", "Neu", "Aktion erforderlich", "erforderlich", "Neuer Fall"),
    ("en", "New", "Action required", "required", "New Case"),
    ("sv", "Nytt", "Åtgärd krävs", "krävs", "Nytt ärende"),
])
def test_display_constants_follow_language(lang, new_col, action_col, validation_word, new_case_label):
    _set_lang(lang)
    assert get_i18n().current_language == lang
    columns = DISPLAY_BOARD_COLUMN_NAMES.values()
    assert new_col in columns
    assert action_col.lower() in [c.lower() for c in columns]
    assert ("NEW", new_col) in DISPLAY_BOARD_COLUMN_NAMES.items()
    assert validation_word in VALIDATION_MESSAGES["snippet_id_required"]

    # Supports the legacy `for key, label in HOTKEY_ACTION_LABELS:` form.
    pairs = list(HOTKEY_ACTION_LABELS)
    assert len(pairs) == len(get_localized_hotkey_action_labels()) == 13
    assert any(k == "new_case" and new_case_label in v for k, v in pairs)


@pytest.mark.parametrize("lang,development,tech,customer,table_layout", [
    ("de", "Data-AL Entwicklung", "Data-AL Technik", "Data-AL Kunde", "Tabelle & Details (Sortier-Matrix)"),
    ("en", "Data-AL Development", "Data-AL Tech Support", "Data-AL Customer", "Table & Details (Sort Matrix)"),
    ("sv", "Data-AL Utveckling", "Data-AL Teknisk support", "Data-AL Kund", "Tabell & Detaljer (Sorteringsmatris)"),
])
def test_translation_equal_to_default_is_not_treated_as_missing(lang, development, tech, customer, table_layout):
    """Locale values identical to the German default must not trigger a false fallback."""
    _set_lang(lang)
    assert DISPLAY_ACTOR_NAMES["DATA_SUPPORT"] == "Data-AL Support / Hotline"
    assert DISPLAY_ACTOR_NAMES["DATA_HOTLINE"] == "Data-AL Hotline"
    assert DISPLAY_ACTOR_NAMES["DATA_DEVELOPMENT"] == development
    assert DISPLAY_ACTOR_NAMES["DATA_TECH"] == tech
    assert DISPLAY_ACTOR_NAMES["DATA_CUSTOMER"] == customer
    assert DISPLAY_LAYOUT_NAMES["TABLE"] == table_layout


@pytest.mark.parametrize("lang", LANGS)
def test_every_display_constant_and_option_list_is_translated(lang):
    _set_lang(lang)
    for prefix, table in (("actors", DISPLAY_ACTOR_NAMES), ("layouts", DISPLAY_LAYOUT_NAMES),
                          ("channels", DISPLAY_CHANNEL_NAMES), ("board_columns", DISPLAY_BOARD_COLUMN_NAMES)):
        for k in table.keys():
            val = table[k]
            assert val and isinstance(val, str) and val != f"{prefix}.{k}", f"{prefix}.{k} untranslated in {lang}"

    for getter, expected_len in (
        (get_localized_departments, 7), (get_localized_handover_channels, 6),
        (get_localized_task_categories, 7), (get_localized_menu_options_stammdaten, 4),
        (get_localized_menu_options_vorlagen, 3), (get_localized_menu_options_datenaustausch, 3),
    ):
        options = getter()
        assert len(options) == expected_len and all(options), getter.__name__


def test_actor_display_names_map_both_ways():
    assert get_actor_display(Actor.SUPPORT) == ACTOR_DISPLAY[Actor.SUPPORT] == "Hotline"
    assert get_actor_display(Actor.DEVELOPMENT) == ACTOR_DISPLAY[Actor.DEVELOPMENT] == "Entwicklung"
    assert get_actor_val_from_display("Entwicklung") == Actor.DEVELOPMENT
    assert get_actor_val_from_display("Hotline") == Actor.SUPPORT
    assert get_actor_val_from_display("Support / Hotline") == Actor.SUPPORT


# ============================================================================
# datetime_utils
# ============================================================================

RELATIVE_DATE_TEXT = {
    #     0        +1          +2                    -1           -2                      +4 (same week)  +20             -20
    "de": ("heute", "morgen", "übermorgen", "gestern", "vorgestern", "diese Woche", "in 20 Tagen", "vor 20 Tagen"),
    "en": ("today", "tomorrow", "day after tomorrow", "yesterday", "day before yesterday", "this week",
           "in 20 days", "20 days ago"),
    "sv": ("idag", "imorgon", "i övermorgon", "igår", "i förrgår", "denna vecka", "om 20 dagar", "för 20 dagar sedan"),
}


@pytest.mark.parametrize("lang", LANGS)
def test_relative_date_text(lang):
    _set_lang(lang)
    ref = datetime(2026, 6, 15, 12, 0, 0)  # a Monday, so +4 days is still this week
    offsets = (0, 1, 2, -1, -2, 4, 20, -20)
    actual = tuple(get_relative_date_text(ref + timedelta(days=d), ref_date=ref) for d in offsets)
    assert actual == RELATIVE_DATE_TEXT[lang]


@pytest.mark.parametrize("lang,suffix", [("de", " Uhr"), ("en", ""), ("sv", "")])
def test_time_suffix_only_in_german(lang, suffix):
    _set_lang(lang)
    sample = "2026-08-23T14:30:00"
    assert format_german_time(sample, with_uhr=True) == f"14:30{suffix}"
    assert format_german_datetime(sample, with_uhr=True) == f"23.08.2026 14:30{suffix}"


def test_generic_format_aliases_match_german_functions():
    sample = "2026-08-23T14:30:00"
    assert format_date(sample) == format_german_date(sample)
    assert format_time(sample) == format_german_time(sample)
    assert format_datetime(sample) == format_german_datetime(sample)


@pytest.mark.parametrize("raw,expected", [
    ("23.08.2026 14:30 Uhr", "2026-08-23T14:30:00"),
    ("23.08.2026 14:30 kl.", "2026-08-23T14:30:00"),
    ("23.08.2026 14:30 kl", "2026-08-23T14:30:00"),
    ("23.08.2026 14:30", "2026-08-23T14:30:00"),
    ("23.08.2026", "2026-08-23T00:00:00"),
    ("2026-08-23T14:30:00", "2026-08-23T14:30:00"),
])
def test_parse_date_strips_time_suffixes(raw, expected):
    assert parse_date(raw) == expected


def test_deadline_hours_and_idle_days():
    now = datetime(2026, 8, 23, 12, 0, 0)
    assert hours_until_deadline("2026-08-23T14:00:00", now=now) == 2.0
    assert hours_until_deadline("2026-08-23T09:00:00", now=now) == -3.0
    assert hours_until_deadline("", now=now) == float("inf")
    assert calculate_idle_days("2026-08-21T12:00:00", now=now) == 2.0
    assert calculate_idle_days("2026-08-25T12:00:00", now=now) == 0.0  # future -> not idle


# ============================================================================
# Static guards over src/ (AST scans; no import of the scanned modules)
#
# 1. Literal design values (padx=12, fg_color="gray30", size=14) in widget
#    calls instead of a token from constants.py.
# 2. A name assigned twice in constants.py - the later one silently wins
#    (how COLOR_DANGER rendered as crimson while the token said #dc2626).
# 3. A widget selection mapped back by matching its translated label text -
#    made the Cobra import overwrite practices in EN/SV instead of skipping.
# ============================================================================


SRC_DIR = Path(__file__).resolve().parents[2] / "src"
CONSTANTS_FILE = SRC_DIR / "constants.py"


def iter_source_files(skip_constants: bool = True):
    """All application modules under src/, newest checkout layout."""
    for path in sorted(SRC_DIR.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        if skip_constants and path.name == "constants.py":
            continue
        yield path


@cache  # the three scans share one parse per file
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

    def test_scanner_flags_planted_literals_but_allows_zero_and_one(self):
        """Guards the guard: a scanner that silently stops matching is worthless."""
        scanner = DesignTokenScanner("<planted>")
        scanner.visit(ast.parse(
            'ctk.CTkButton(parent, width=137, fg_color="gray30", font=ctk.CTkFont(size=13))'
        ))
        assert {v.argument for v in scanner.violations} == {"width", "fg_color", "font.size"}

        # padx=0 and border_width=1 are intent, not magic numbers.
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


def find_label_comparisons(source: str | ast.Module, file_label: str) -> list[str]:
    """Locates comparisons of a string literal against a translated widget label."""
    tree = source if isinstance(source, ast.Module) else ast.parse(source)
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
    def test_choices_are_translation_pairs_index_aligned_with_values(self, choices_module, choices_name, values_module, values_name):
        """The dialog maps the selected menu position onto the value tuple, and
        each choice is a (locale key, German default) pair - a bare label would
        never get translated."""
        choices = literal_value(choices_module, choices_name)
        values = literal_value(values_module, values_name)
        assert len(choices) == len(values), (
            f"{choices_name} has {len(choices)} entries but {values_name} has {len(values)}; "
            f"adding an option without its program value mis-assigns every entry after it."
        )
        for entry in choices:
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
            offenders.extend(find_label_comparisons(parse(path), rel(path)))

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
