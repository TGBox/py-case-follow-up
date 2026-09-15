"""Jede Suchleiste wartet die Tipppause ab, bevor sie sucht.

Gemeldet aus den Praxisstammdaten: drei Buchstaben tippen loeste drei volle
Suchlaeufe aus - der erste Buchstabe baute die komplette Trefferliste auf, und
der zweite Tastendruck kam erst an, nachdem die fertig war.

Der erste Test ist der eigentliche Waechter: er findet jedes Suchfeld im
Quelltext selbst, also auch solche, die spaeter dazukommen.
"""

import ast
import pathlib
import re
import time

import customtkinter as ctk
import pytest

from constants import SEARCH_DEBOUNCE_MS
from utils.ui_utils import cancel_debounce, debounce

SRC = pathlib.Path(__file__).resolve().parent.parent / "src"

# Nur der echte Aufruf zaehlt - cancel_debounce( enthaelt zwar "debounce(",
# verzoegert aber nichts.
ENTPRELLT = re.compile(r"(?<![\w.])debounce\(")

# Felder, die zwar auf <KeyRelease> hoeren, aber keine Suche ausloesen.
KEINE_SUCHE = {
    ("profile_settings_shortcuts_tab.py", "entry"),
    ("profile_settings_shortcuts_tab.py", "s_entry"),
    ("export_dialog.py", "entry"),
    ("date_picker.py", "self.entry"),
    ("ui_utils.py", "inner"),
}


def _keyrelease_bindungen():
    """Alle <KeyRelease>-Bindungen im Quelltext, mit Datei, Widget und Handler."""
    treffer = []
    for pfad in sorted(SRC.rglob("*.py")):
        baum = ast.parse(pfad.read_text(encoding="utf-8"))
        for knoten in ast.walk(baum):
            if not isinstance(knoten, ast.Call):
                continue
            ziel = knoten.func
            if not isinstance(ziel, ast.Attribute) or ziel.attr != "bind":
                continue
            if not knoten.args or not isinstance(knoten.args[0], ast.Constant):
                continue
            if knoten.args[0].value != "<KeyRelease>":
                continue
            widget = ast.unparse(ziel.value)
            handler = ast.unparse(knoten.args[1]) if len(knoten.args) > 1 else ""
            treffer.append((pfad.name, widget, handler, knoten.lineno))
    return treffer


def _handler_quellen(name):
    """Quelltext jeder Methode dieses Namens - egal in welcher Datei sie steht.

    Die Bindung und ihr Handler liegen nicht zwangslaeufig in derselben Datei:
    die Praxisstammdaten binden in customer_form_builders.py (Mixin), der
    Handler steht im Dialog. Deshalb wird src/ komplett durchsucht.
    """
    quellen = []
    for pfad in sorted(SRC.rglob("*.py")):
        text = pfad.read_text(encoding="utf-8")
        if f"def {name}(" not in text:
            continue
        baum = ast.parse(text)
        for knoten in ast.walk(baum):
            if not isinstance(knoten, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if knoten.name != name or _ist_stub(knoten):
                continue
            quellen.append((pfad.name, ast.get_source_segment(text, knoten) or ""))
    return quellen


def _ist_stub(knoten):
    """Reine Typdeklaration (`def x(...) -> None: ...`), keine Implementierung.

    Die Mixins deklarieren die Methoden des Dialogs, damit pyright sie kennt;
    entprellt wird in der echten Methode der Dialogklasse.
    """
    rumpf = [a for a in knoten.body if not (isinstance(a, ast.Expr) and isinstance(a.value, ast.Constant) and isinstance(a.value.value, str))]
    return all(
        isinstance(a, ast.Pass)
        or (isinstance(a, ast.Expr) and isinstance(a.value, ast.Constant) and a.value.value is Ellipsis)
        for a in rumpf
    )


def test_every_search_field_waits_for_a_typing_pause():
    ohne_verzoegerung = set()
    for datei, widget, handler, zeile in _keyrelease_bindungen():
        kurz = widget.replace("self.", "")
        if (datei, widget) in KEINE_SUCHE or (datei, kurz) in KEINE_SUCHE:
            continue
        if "search" not in widget.lower() and "to_entry" not in widget:
            continue
        # Entweder direkt im Lambda entprellt oder ueber einen eigenen Handler,
        # dessen Quelltext debounce aufruft.
        if ENTPRELLT.search(handler):
            continue
        name = handler.split(".")[-1]
        quellen = _handler_quellen(name)
        # Steht der Handler in derselben Datei, zaehlt genau der; sonst (Mixin)
        # muessen alle gleichnamigen Handler entprellen.
        eigene = [q for q in quellen if q[0] == datei]
        massgeblich = eigene or quellen
        if not massgeblich:
            ohne_verzoegerung.add(f"{datei}:{zeile} -> {widget} ({handler}: Handler nicht gefunden)")
        for handler_datei, quelltext in massgeblich:
            if not ENTPRELLT.search(quelltext):
                ohne_verzoegerung.add(
                    f"{handler_datei}: {name} (gebunden in {datei}:{zeile} an {widget})"
                )

    assert sorted(ohne_verzoegerung) == [], (
        "Suchfelder ohne Verzoegerung:\n  " + "\n  ".join(sorted(ohne_verzoegerung))
    )


def test_all_search_fields_use_the_same_delay():
    """Eine Konstante, damit sich die Suchfelder nicht auseinanderentwickeln."""
    eigene_zahlen = []
    for pfad in sorted(SRC.rglob("*.py")):
        text = pfad.read_text(encoding="utf-8")
        baum = ast.parse(text)
        for knoten in ast.walk(baum):
            if not isinstance(knoten, ast.Call):
                continue
            name = knoten.func.id if isinstance(knoten.func, ast.Name) else getattr(knoten.func, "attr", "")
            if name != "debounce" or len(knoten.args) < 3:
                continue
            if isinstance(knoten.args[2], ast.Constant):
                eigene_zahlen.append(f"{pfad.name}:{knoten.lineno} ({knoten.args[2].value} ms)")

    assert eigene_zahlen == [], (
        "debounce mit fester Zahl statt SEARCH_DEBOUNCE_MS:\n  " + "\n  ".join(eigene_zahlen)
    )


# --- Verhalten des Helfers selbst ---

@pytest.fixture
def root():
    app = ctk.CTk()
    app.withdraw()
    yield app
    try:
        app.destroy()
    except Exception:
        pass


def test_three_keystrokes_trigger_one_search(root):
    laeufe = []
    for _ in range(3):
        debounce(root, "probe", 40, lambda: laeufe.append("gesucht"))
    assert laeufe == [], "es wurde sofort gesucht, statt die Pause abzuwarten"

    ende = time.monotonic() + 2.0
    while not laeufe and time.monotonic() < ende:
        root.update()
        time.sleep(0.01)

    assert laeufe == ["gesucht"], f"erwartet genau eine Suche, bekam {laeufe}"


def test_a_pause_between_keystrokes_searches_twice(root):
    laeufe = []

    def tippen():
        debounce(root, "probe", 30, lambda: laeufe.append("x"))

    tippen()
    ende = time.monotonic() + 2.0
    while not laeufe and time.monotonic() < ende:
        root.update()
        time.sleep(0.01)

    tippen()
    ende = time.monotonic() + 2.0
    while len(laeufe) < 2 and time.monotonic() < ende:
        root.update()
        time.sleep(0.01)

    assert len(laeufe) == 2, f"nach einer Pause muss erneut gesucht werden, bekam {laeufe}"


def test_cancelling_drops_the_pending_search(root):
    laeufe = []
    debounce(root, "probe", 40, lambda: laeufe.append("x"))
    cancel_debounce(root, "probe")

    ende = time.monotonic() + 0.5
    while time.monotonic() < ende:
        root.update()
        time.sleep(0.01)

    assert laeufe == [], "abgebrochene Suche lief trotzdem"


def test_the_delay_is_noticeable_but_not_annoying():
    assert 120 <= SEARCH_DEBOUNCE_MS <= 400, (
        f"{SEARCH_DEBOUNCE_MS} ms - zu kurz bringt nichts, zu lang fuehlt sich traege an"
    )


# --- Was passiert, wenn der Nutzer waehrend der Wartezeit weiterklickt? ---
#
# Die Verzoegerung oeffnet ein Zeitfenster, das es vorher nicht gab: zwischen
# dem letzten Buchstaben und der Suche kann der Nutzer die Liste schliessen
# oder einen Treffer auswaehlen. Laeuft die Suche danach trotzdem, arbeitet sie
# auf Widgets, die es nicht mehr gibt - oder macht die Auswahl wieder zunichte.


def _warten(widget, sekunden=1.0):
    ende = time.monotonic() + sekunden
    while time.monotonic() < ende:
        widget.update()
        time.sleep(0.01)


def test_closing_the_combobox_popover_drops_the_pending_search(root):
    """Escape/Enter zerstoert das Popover - die wartende Suche darf nicht hinterherlaufen."""
    from ui.widgets.searchable_combobox import SearchableCombobox

    fehler = []
    root.report_callback_exception = lambda *args: fehler.append(args)

    combo = SearchableCombobox(root, values=[f"Praxis {i}" for i in range(30)])
    combo.pack()
    combo.open_popover()
    root.update()

    combo.search_entry.insert(0, "Pra")
    combo._on_search_keyrelease()
    combo.close_popover()

    _warten(root)

    assert fehler == [], (
        "die wartende Suche lief auf dem zerstoerten Popover weiter: "
        + "; ".join(str(f[1]) for f in fehler)
    )


def test_picking_a_recipient_does_not_reopen_the_suggestion_list(tmp_path, root):
    """Ein Klick auf einen Vorschlag setzt den Empfaenger - die Liste bleibt zu."""
    from config import AppConfig
    from enums import Actor, UrgencyLevel
    from models.case import Case, CaseCustomer, Classification, WorkflowStatus
    from services.calendar_email_service import CalendarEmailService
    from services.snippet_service import SnippetService
    from ui.dialogs.email_draft_dialog import EmailDraftDialog

    config = AppConfig(workspace_dir=tmp_path)
    fall = Case(
        case_id="T-DEB-01",
        customer=CaseCustomer(customer_id="K-1", practice_name="Praxis Sonnenberg", email="info@sonnenberg.de"),
        classification=Classification(title="Testfall", urgency_level=UrgencyLevel.YELLOW),
        workflow_status=WorkflowStatus(current_actor=Actor.SUPPORT),
    )
    dialog = EmailDraftDialog(
        root,
        case=fall,
        calendar_email_service=CalendarEmailService(config),
        user_name="Daniel",
        snippet_service=SnippetService(tmp_path),
    )
    dialog.all_contacts = [
        {"name": "Frau Weber", "email": "weber@sonnenberg.de", "practice": "Praxis Sonnenberg",
         "search_key": "frau weber weber@sonnenberg.de praxis sonnenberg"},
    ]
    dialog.update_idletasks()

    dialog.to_entry.delete(0, "end")
    dialog.to_entry.insert(0, "web")
    dialog._on_to_keyrelease()                      # Tastendruck, Suche wartet
    dialog.select_contact(dialog.all_contacts[0])   # Nutzer klickt den Treffer an

    _warten(dialog)

    assert dialog.to_entry.get() == "weber@sonnenberg.de"
    assert not dialog.suggestions_frame_visible, (
        "die Vorschlagsliste ist nach der Auswahl wieder aufgesprungen"
    )

    try:
        dialog.destroy()
    except Exception:
        pass
