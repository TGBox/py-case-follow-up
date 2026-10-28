"""Input widgets: SearchableCombobox, CalendarDialog time steppers and the search debounce shared by all search fields."""

import ast
import functools
import pathlib
import re
import time
import tkinter as tk

import customtkinter as ctk
import pytest

from constants import SEARCH_DEBOUNCE_MS
from ui.widgets.searchable_combobox import SearchableCombobox
from utils.ui_utils import cancel_debounce, debounce

SRC = pathlib.Path(__file__).resolve().parents[2] / "src"
FAST_DEBOUNCE_MS = 20


def _option_texts(combo) -> list[str]:
    return [w.cget("text") for w in combo.options_scroll.winfo_children() if isinstance(w, ctk.CTkButton)]


def _search(combo, query: str) -> None:
    combo.search_entry.insert(0, query)
    combo._on_search_changed()


def _run_after_immediately(monkeypatch, combo):
    """Executes `combo.after(...)` callbacks synchronously (no mainloop in tests)."""
    monkeypatch.setattr(combo, "after", lambda _ms, func=None, *a: func(*a) if func else None)


def _pump(widget, seconds: float, until=lambda: False) -> None:
    end = time.monotonic() + seconds
    while time.monotonic() < end and not until():
        widget.update()
        time.sleep(0.005)


def _text_widgets(node) -> list[tk.Text]:
    found = [node] if isinstance(node, tk.Text) else []
    for child in node.winfo_children():
        found.extend(_text_widgets(child))
    return found


# --- SearchableCombobox: value handling ---

@pytest.mark.parametrize("initial, new_values, default, expected", [
    (["A", "B"], None, None, "A"),               # first value selected by default
    (["A", "B"], ["A", "B", "C"], "C", "C"),     # default kept when present
    (["A", "B"], ["X", "Y"], "Z", "X"),          # falls back to first when default missing
    (["A", "B"], [], None, ""),                  # empty list clears selection
])
def test_selected_value_follows_values_and_default(root, initial, new_values, default, expected):
    combo = SearchableCombobox(root, values=initial)
    if new_values is not None:
        combo.set_values(new_values, default_value=default)
    assert combo.get() == expected
    if expected:
        assert expected in combo.btn.cget("text")


def test_placeholder_shown_until_something_is_selected(root):
    combo = SearchableCombobox(root, values=[], placeholder_text="– Bitte wählen –")
    assert combo.get() == ""
    assert "– Bitte wählen –" in combo.btn.cget("text")

    combo.refresh_ui_labels()
    assert combo.placeholder_text in combo.btn.cget("text")

    combo.set("B")  # CTkOptionMenu-compatible alias
    combo.refresh_ui_labels()
    assert combo.get() == "B"
    assert "B" in combo.btn.cget("text")


# --- SearchableCombobox: popover, search, selection ---

def test_popover_lists_all_values_and_toggles_open_and_closed(root):
    combo = SearchableCombobox(root, values=["Alpha", "Beta", "Gamma"])
    combo.toggle_popover()
    _pump(root, 0.05)  # let the deferred keyboard activation run
    assert combo._popover is not None and combo._popover.winfo_exists()
    assert _option_texts(combo) == ["Alpha", "Beta", "Gamma"]

    combo.toggle_popover()
    assert combo._popover is None

    empty = SearchableCombobox(root, values=[])
    empty.open_popover()
    assert empty._popover is None


def test_search_filters_case_insensitively_and_reports_no_results(root):
    combo = SearchableCombobox(root, values=["Praxis Alpha", "Praxis Beta", "Klinik Gamma"])
    combo.open_popover()
    _search(combo, "praxis")
    assert _option_texts(combo) == ["Praxis Alpha", "Praxis Beta"]
    assert not any(_text_widgets(c) for c in combo.options_scroll.winfo_children())  # plain buttons, no rich rows

    combo.search_entry.delete(0, "end")
    _search(combo, "zzz-nonexistent")
    children = combo.options_scroll.winfo_children()
    assert [type(w) for w in children] == [ctk.CTkLabel]


def test_selecting_an_item_sets_value_closes_popover_and_calls_command(root):
    selected = []
    combo = SearchableCombobox(root, values=["Alpha", "Beta"], command=selected.append)
    combo.open_popover()
    combo._select_item("Beta")

    assert combo.get() == "Beta"
    assert combo._popover is None
    assert selected == ["Beta"]


@pytest.mark.parametrize("query, expected_pick", [("beta", ["Praxis Beta"]), ("zzz-nonexistent", [])])
def test_enter_selects_first_filtered_match(root, query, expected_pick):
    selected = []
    combo = SearchableCombobox(root, values=["Praxis Alpha", "Praxis Beta"], command=selected.append)
    combo.open_popover()
    combo.search_entry.insert(0, query)
    combo._on_enter_pressed()

    assert selected == expected_pick
    assert combo.get() == (expected_pick[0] if expected_pick else "Praxis Alpha")


# --- SearchableCombobox: hidden search fields with highlighted results ---

def test_search_index_finds_values_by_hidden_fields(root):
    """A practice must be findable by data that is not shown in its label."""
    combo = SearchableCombobox(
        root,
        values=["Praxis Welz (00109)", "Praxis Zeglin (00062)"],
        search_index={
            "Praxis Welz (00109)": "Katrin Schmidt katrin@ergotherapie-nwm.de Travemünde 41569",
            "Praxis Zeglin (00062)": "Uwe Zeglin Inhaber 04502889881",
        },
    )
    for query in ("katrin", "travemünde", "41569"):
        assert combo._filtered(query) == ["Praxis Welz (00109)"]
    assert combo._filtered("04502889881") == ["Praxis Zeglin (00062)"]
    assert combo._filtered("praxis") == ["Praxis Welz (00109)", "Praxis Zeglin (00062)"]
    assert combo._filtered("") == ["Praxis Welz (00109)", "Praxis Zeglin (00062)"]


def test_hidden_field_hit_is_rendered_highlighted_with_a_reason(root):
    combo = SearchableCombobox(
        root,
        values=["Praxis Welz (00109)"],
        search_index={"Praxis Welz (00109)": "Katrin Schmidt Travemünde"},
        summary_provider=lambda value, query: "Katrin Schmidt",
    )
    combo.open_popover()
    _search(combo, "katrin")

    texts = [t for child in combo.options_scroll.winfo_children() for t in _text_widgets(child)]
    contents = [t.get("1.0", "end - 1 chars") for t in texts]
    assert "Praxis Welz (00109)" in contents
    assert any("Katrin Schmidt" in c for c in contents), "the match is not explained"
    assert sum(len(t.tag_ranges("match")) for t in texts) > 0, "nothing was highlighted"


def test_enter_selects_first_hidden_field_match(root):
    picked = []
    combo = SearchableCombobox(
        root,
        values=["Praxis Welz (00109)", "Praxis Zeglin (00062)"],
        search_index={"Praxis Zeglin (00062)": "Uwe Zeglin Inhaber"},
        command=picked.append,
    )
    combo.open_popover()
    combo.search_entry.insert(0, "inhaber")
    combo._on_enter_pressed()
    assert picked == ["Praxis Zeglin (00062)"]


# --- SearchableCombobox: focus after the popover closes ---
# Regression guard: on Windows the destroyed overrideredirect popover left the
# owning dialog without keyboard activation, so the next entry swallowed every
# keystroke until the user clicked another window and back.

def test_close_popover_restores_focus_only_when_a_popover_was_open(root, monkeypatch):
    combo = SearchableCombobox(root, values=["A", "B"])
    calls = []
    monkeypatch.setattr(combo, "_restore_parent_focus", lambda *a: calls.append(a))

    combo.close_popover()  # nothing open: no-op
    assert calls == []

    combo.open_popover()
    combo.close_popover()
    assert combo._popover is None
    assert len(calls) == 1


def test_focus_out_closes_popover_without_pulling_focus_back(root, monkeypatch):
    """The user clicked elsewhere on purpose."""
    combo = SearchableCombobox(root, values=["A", "B"])
    combo.open_popover()
    calls = []
    monkeypatch.setattr(combo, "_restore_parent_focus", lambda *a: calls.append(a))
    _run_after_immediately(monkeypatch, combo)

    combo._on_focus_out()

    assert combo._popover is None
    assert calls == []


@pytest.mark.parametrize("with_next_widget", [True, False])
def test_select_item_hands_focus_to_configured_next_widget(root, monkeypatch, with_next_widget):
    combo = SearchableCombobox(root, values=["Alpha", "Beta"])
    next_entry = ctk.CTkEntry(root)
    if with_next_widget:
        combo.set_next_focus_widget(next_entry)
    combo.open_popover()
    captured = {}
    monkeypatch.setattr(combo, "_restore_parent_focus",
                        lambda top, prev_grab, focus_target: captured.update(target=focus_target))

    combo._select_item("Beta")

    assert captured["target"] is (next_entry if with_next_widget else None)


def test_restore_parent_focus_reactivates_toplevel_then_focuses_target(root, monkeypatch):
    combo = SearchableCombobox(root, values=["A"])
    next_entry = ctk.CTkEntry(root)
    events = []
    monkeypatch.setattr(root, "lift", lambda: events.append("lift"))
    monkeypatch.setattr(root, "focus_force", lambda: events.append("focus_force"))
    monkeypatch.setattr(next_entry, "focus_set", lambda: events.append("target"))
    _run_after_immediately(monkeypatch, combo)

    combo._restore_parent_focus(root, None, next_entry)

    assert events == ["lift", "focus_force", "target"]


def test_restore_parent_focus_falls_back_to_button_for_dead_target(root, monkeypatch):
    combo = SearchableCombobox(root, values=["A"])
    dead_entry = ctk.CTkEntry(root)
    dead_entry.destroy()
    focused = []
    monkeypatch.setattr(combo.btn, "focus_set", lambda: focused.append("btn"))
    _run_after_immediately(monkeypatch, combo)

    combo._restore_parent_focus(root, None, dead_entry)

    assert focused == ["btn"]


@pytest.mark.parametrize("grab_still_held, expected", [(False, ["grab_set"]), (True, [])])
def test_restore_parent_focus_rearms_only_a_lost_modal_grab(root, monkeypatch, grab_still_held, expected):
    combo = SearchableCombobox(root, values=["A"])
    grabs = []
    monkeypatch.setattr(root, "grab_current", lambda: root if grab_still_held else None)
    monkeypatch.setattr(root, "grab_set", lambda: grabs.append("grab_set"))
    _run_after_immediately(monkeypatch, combo)

    combo._restore_parent_focus(root, root, None)

    assert grabs == expected


# --- CalendarDialog time picker ---

def test_calendar_time_picker_offers_07_to_20_and_steppers_clamp_and_wrap(root):
    from ui.widgets.date_picker import CalendarDialog

    dialog = CalendarDialog(root, initial_date="2026-08-25T14:30:00", include_time=True)
    try:
        assert (dialog.hour_var.get(), dialog.minute_var.get()) == ("14", "30")
        hours = list(dialog.hour_menu.cget("values"))
        assert hours == [f"{h:02d}" for h in range(7, 21)]

        steps = [
            ("hour", None, 1, "15"), ("hour", None, -2, "13"),
            ("hour", "20", 1, "20"), ("hour", "07", -1, "07"),
            ("minute", "30", 5, "35"), ("minute", None, -10, "25"), ("minute", "55", 5, "00"),
        ]
        for kind, start, delta, expected in steps:
            var = dialog.hour_var if kind == "hour" else dialog.minute_var
            if start is not None:
                var.set(start)
            (dialog.step_hour if kind == "hour" else dialog.step_minute)(delta)
            assert var.get() == expected, (kind, start, delta)
    finally:
        dialog.destroy()


# --- Search debounce: every search field waits for a typing pause ---
# Gemeldet aus den Praxisstammdaten: drei Buchstaben tippen loeste drei volle
# Suchlaeufe aus. Der erste Test findet jedes Suchfeld im Quelltext selbst,
# also auch solche, die spaeter dazukommen.

ENTPRELLT = re.compile(r"(?<![\w.])debounce\(")  # cancel_debounce( zaehlt nicht

KEINE_SUCHE = {  # <KeyRelease>-Bindungen, die keine Suche ausloesen
    ("profile_settings_shortcuts_tab.py", "entry"),
    ("profile_settings_shortcuts_tab.py", "s_entry"),
    ("export_dialog.py", "entry"),
    ("date_picker.py", "self.entry"),
    ("ui_utils.py", "inner"),
}


@functools.cache
def _src_trees():
    trees = []
    for pfad in sorted(SRC.rglob("*.py")):
        text = pfad.read_text(encoding="utf-8")
        trees.append((pfad.name, text, ast.parse(text)))
    return trees


def _ist_stub(knoten):
    """Reine Typdeklaration (`def x(...) -> None: ...`) der Mixins, keine Implementierung."""
    rumpf = [a for a in knoten.body
             if not (isinstance(a, ast.Expr) and isinstance(a.value, ast.Constant) and isinstance(a.value.value, str))]
    return all(isinstance(a, ast.Pass)
               or (isinstance(a, ast.Expr) and isinstance(a.value, ast.Constant) and a.value.value is Ellipsis)
               for a in rumpf)


def test_every_search_field_waits_for_a_typing_pause():
    bindings = []
    for datei, _text, baum in _src_trees():
        for knoten in ast.walk(baum):
            if (isinstance(knoten, ast.Call) and isinstance(knoten.func, ast.Attribute) and knoten.func.attr == "bind"
                    and knoten.args and isinstance(knoten.args[0], ast.Constant)
                    and knoten.args[0].value == "<KeyRelease>"):
                handler = ast.unparse(knoten.args[1]) if len(knoten.args) > 1 else ""
                bindings.append((datei, ast.unparse(knoten.func.value), handler, knoten.lineno))

    def quellen_von(name):
        """Quelltext jeder gleichnamigen Methode in src/ - Bindung und Handler koennen in verschiedenen Dateien liegen."""
        return [(datei, ast.get_source_segment(text, k) or "")
                for datei, text, baum in _src_trees() if f"def {name}(" in text
                for k in ast.walk(baum)
                if isinstance(k, (ast.FunctionDef, ast.AsyncFunctionDef)) and k.name == name and not _ist_stub(k)]

    ohne_verzoegerung = set()
    for datei, widget, handler, zeile in bindings:
        if (datei, widget) in KEINE_SUCHE or (datei, widget.replace("self.", "")) in KEINE_SUCHE:
            continue
        if "search" not in widget.lower() and "to_entry" not in widget:
            continue
        if ENTPRELLT.search(handler):
            continue
        name = handler.split(".")[-1]
        quellen = quellen_von(name)
        # Handler in derselben Datei zaehlt allein; sonst (Mixin) muessen alle gleichnamigen entprellen.
        massgeblich = [q for q in quellen if q[0] == datei] or quellen
        if not massgeblich:
            ohne_verzoegerung.add(f"{datei}:{zeile} -> {widget} ({handler}: Handler nicht gefunden)")
        for handler_datei, quelltext in massgeblich:
            if not ENTPRELLT.search(quelltext):
                ohne_verzoegerung.add(f"{handler_datei}: {name} (gebunden in {datei}:{zeile} an {widget})")

    assert sorted(ohne_verzoegerung) == [], "Suchfelder ohne Verzoegerung:\n  " + "\n  ".join(sorted(ohne_verzoegerung))


def test_all_search_fields_use_the_same_reasonable_delay():
    """Eine Konstante, damit sich die Suchfelder nicht auseinanderentwickeln."""
    eigene_zahlen = []
    for datei, _text, baum in _src_trees():
        for knoten in ast.walk(baum):
            if not isinstance(knoten, ast.Call):
                continue
            name = knoten.func.id if isinstance(knoten.func, ast.Name) else getattr(knoten.func, "attr", "")
            if name == "debounce" and len(knoten.args) >= 3 and isinstance(knoten.args[2], ast.Constant):
                eigene_zahlen.append(f"{datei}:{knoten.lineno} ({knoten.args[2].value} ms)")

    assert eigene_zahlen == [], "debounce mit fester Zahl statt SEARCH_DEBOUNCE_MS:\n  " + "\n  ".join(eigene_zahlen)
    assert 120 <= SEARCH_DEBOUNCE_MS <= 400, "zu kurz bringt nichts, zu lang fuehlt sich traege an"


def test_debounce_coalesces_keystrokes_searches_again_after_a_pause_and_can_be_cancelled(root):
    laeufe = []

    def tippen():
        debounce(root, "probe", FAST_DEBOUNCE_MS, lambda: laeufe.append("x"))

    for _ in range(3):
        tippen()
    assert laeufe == [], "es wurde sofort gesucht, statt die Pause abzuwarten"
    _pump(root, 2.0, until=lambda: laeufe)
    _pump(root, 0.05)
    assert laeufe == ["x"], "drei Tastendruecke muessen genau eine Suche ausloesen"

    tippen()
    _pump(root, 2.0, until=lambda: len(laeufe) == 2)
    assert len(laeufe) == 2, "nach einer Pause muss erneut gesucht werden"

    tippen()
    cancel_debounce(root, "probe")
    _pump(root, FAST_DEBOUNCE_MS / 1000 + 0.1)
    assert len(laeufe) == 2, "abgebrochene Suche lief trotzdem"


# Die Verzoegerung oeffnet ein Zeitfenster: zwischen letztem Buchstaben und
# Suche kann der Nutzer die Liste schliessen oder einen Treffer auswaehlen.

def test_closing_the_combobox_popover_drops_the_pending_search(root, monkeypatch):
    """Escape/Enter zerstoert das Popover - die wartende Suche darf nicht hinterherlaufen."""
    import ui.widgets.searchable_combobox as sc
    monkeypatch.setattr(sc, "SEARCH_DEBOUNCE_MS", FAST_DEBOUNCE_MS)

    fehler = []
    root.report_callback_exception = lambda *args: fehler.append(args)
    combo = SearchableCombobox(root, values=[f"Praxis {i}" for i in range(30)])
    combo.pack()
    combo.open_popover()
    root.update()

    combo.search_entry.insert(0, "Pra")
    combo._on_search_keyrelease()
    combo.close_popover()
    _pump(root, FAST_DEBOUNCE_MS / 1000 + 0.15)

    assert fehler == [], "; ".join(str(f[1]) for f in fehler)


def test_picking_a_recipient_does_not_reopen_the_suggestion_list(root, config, tmp_path, monkeypatch):
    """Ein Klick auf einen Vorschlag setzt den Empfaenger - die Liste bleibt zu."""
    import ui.dialogs.email_draft_dialog as edd
    from enums import Actor, UrgencyLevel
    from models.case import Case, CaseCustomer, Classification, WorkflowStatus
    from services.calendar_email_service import CalendarEmailService
    from services.snippet_service import SnippetService

    monkeypatch.setattr(edd, "SEARCH_DEBOUNCE_MS", FAST_DEBOUNCE_MS)
    fall = Case(
        case_id="T-DEB-01",
        customer=CaseCustomer(customer_id="K-1", practice_name="Praxis Sonnenberg", email="info@sonnenberg.de"),
        classification=Classification(title="Testfall", urgency_level=UrgencyLevel.YELLOW),
        workflow_status=WorkflowStatus(current_actor=Actor.SUPPORT),
    )
    dialog = edd.EmailDraftDialog(root, case=fall, calendar_email_service=CalendarEmailService(config),
                                  user_name="Daniel", snippet_service=SnippetService(tmp_path))
    try:
        dialog.all_contacts = [{"name": "Frau Weber", "email": "weber@sonnenberg.de", "practice": "Praxis Sonnenberg",
                                "search_key": "frau weber weber@sonnenberg.de praxis sonnenberg"}]
        dialog.update_idletasks()

        dialog.to_entry.delete(0, "end")
        dialog.to_entry.insert(0, "web")
        dialog._on_to_keyrelease()                      # Tastendruck, Suche wartet
        dialog.select_contact(dialog.all_contacts[0])   # Nutzer klickt den Treffer an
        _pump(dialog, FAST_DEBOUNCE_MS / 1000 + 0.15)

        assert dialog.to_entry.get() == "weber@sonnenberg.de"
        assert not dialog.suggestions_frame_visible, "die Vorschlagsliste ist nach der Auswahl wieder aufgesprungen"
    finally:
        try:
            dialog.destroy()
        except Exception:
            pass


# --- Emoticons become emojis in note fields ---

def _typer(root):
    from types import SimpleNamespace

    from utils.emoticons import enable_emoticon_autoreplace

    box = ctk.CTkTextbox(root)
    handler = enable_emoticon_autoreplace(box)
    text = box._textbox

    def type_(keys) -> str:
        """Feeds keys like a user would: our binding first, then Tk's own insert."""
        for key in keys:
            keysym = "BackSpace" if key == "\b" else key
            event = SimpleNamespace(keysym=keysym, char="" if key == "\b" else key)
            if handler.on_key(event) != "break":
                if key == "\b":
                    text.delete("insert -1c")
                else:
                    text.insert("insert", key)
            root.update()
        return text.get("1.0", "end-1c")

    return type_


@pytest.mark.parametrize("typed, expected", [
    ("super :D", "super 😄"),
    ("super :-D", "super 😄"),
    (":)", "🙂"),
    ("danke :-) bis bald", "danke 🙂 bis bald"),
    ("schade :(", "schade 🙁"),
    ("zeile\n:-(", "zeile\n🙁"),
    ("Termin:)", "Termin:)"),          # glued to a word: left alone
    ("https://x.de/:D", "https://x.de/:D"),
    (":Dx", "😄x"),
])
def test_typed_emoticons_become_emojis(root, typed, expected):
    assert _typer(root)(typed) == expected


def test_backspace_right_after_a_replacement_restores_the_emoticon(root):
    type_ = _typer(root)
    assert type_("ok :)") == "ok 🙂"
    assert type_("\b") == "ok :)"
    # The restored ":)" stays, even though its last char was just "typed" again.
    assert type_(" ") == "ok :) "
    # Later, a backspace is an ordinary backspace again.
    assert type_(":D a\b\b\b") == "ok :) "


def test_pasted_emoticons_stay_as_text(root):
    from utils.emoticons import enable_emoticon_autoreplace

    box = ctk.CTkTextbox(root)
    enable_emoticon_autoreplace(box)
    box.insert("1.0", "eingefügt :D")
    root.update()
    assert box.get("1.0", "end-1c") == "eingefügt :D"


def test_every_note_field_replaces_emoticons():
    for rel in (
        "ui/widgets/timeline_widget.py",
        "ui/dialogs/timeline_entry_dialog.py",
        "ui/dialogs/new_case_dialog.py",
        "ui/widgets/dynamic_form_field_renderers.py",
    ):
        assert "enable_emoticon_autoreplace(" in (SRC / rel).read_text(encoding="utf-8"), rel
