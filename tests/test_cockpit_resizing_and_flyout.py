"""Unit tests for Cockpit proportional 3-column resizing, flexible follow-up input,
title truncation, and vector rendering configuration.
"""
from datetime import datetime

import pytest
from unittest.mock import MagicMock
from customtkinter.windows.widgets.core_rendering import DrawEngine

from utils.datetime_utils import parse_flexible_followup_input
from ui.dialogs.followup_flyout_dialog import FollowupFlyoutDialog
from ui.views.cockpit_view import CockpitView


def test_draw_engine_is_polygon_shapes():
    """Verify that DrawEngine uses polygon_shapes for reliable multi-monitor DPI scaling."""
    assert DrawEngine.preferred_drawing_method == "polygon_shapes"


class TestFlexibleFollowupInput:
    def test_empty_and_invalid(self):
        assert parse_flexible_followup_input("") is None
        assert parse_flexible_followup_input("   ") is None
        assert parse_flexible_followup_input("invalid") is None
        assert parse_flexible_followup_input("99:99") is None

    def test_time_only_uses_current_date(self):
        now = datetime.now()
        res = parse_flexible_followup_input("14:30")
        assert res is not None
        assert res.year == now.year
        assert res.month == now.month
        assert res.day == now.day
        assert res.hour == 14
        assert res.minute == 30

    def test_date_only_uses_current_time(self):
        now = datetime.now()
        res = parse_flexible_followup_input("15.11.2026")
        assert res is not None
        assert res.year == 2026
        assert res.month == 11
        assert res.day == 15
        assert res.hour == now.hour
        assert res.minute == now.minute

    def test_iso_date_only_uses_current_time(self):
        now = datetime.now()
        res = parse_flexible_followup_input("2026-11-15")
        assert res is not None
        assert res.year == 2026
        assert res.month == 11
        assert res.day == 15
        assert res.hour == now.hour
        assert res.minute == now.minute

    def test_combined_date_and_time(self):
        res = parse_flexible_followup_input("15.11.2026 10:45")
        assert res is not None
        assert res.year == 2026
        assert res.month == 11
        assert res.day == 15
        assert res.hour == 10
        assert res.minute == 45

    def test_combined_iso_datetime(self):
        res = parse_flexible_followup_input("2026-11-15 08:30")
        assert res is not None
        assert res.year == 2026
        assert res.month == 11
        assert res.day == 15
        assert res.hour == 8
        assert res.minute == 30


class TestTitleTruncation:
    def test_short_title_unchanged(self):
        short = "Kurzer Betreff"
        assert FollowupFlyoutDialog._truncate_title_to_two_lines(short, line_length=50) == short

    def test_long_title_capped_at_two_lines(self):
        long_title = "Das ist ein extrem langer Titel fuer einen Supportfall, welcher sich ueber viele Zeilen hinweg erstrecken koennte und deshalb gekuerzt werden muss, damit der Button nicht verschwindet."
        result = FollowupFlyoutDialog._truncate_title_to_two_lines(long_title, line_length=45)
        lines = result.split("\n")
        assert len(lines) <= 2
        assert result.endswith("...")


# Hier standen zwei Tests (TestCockpitProportionalResizing), die die anteilige
# Spaltenverteilung geprueft haben - mit einem MagicMock als PanedWindow. Sie
# haben damit nur nachgerechnet, *dass* sash_place mit den richtigen Zahlen
# aufgerufen wurde, nicht, ob Tk diese Positionen auch behaelt. Genau daran ist
# es in der Praxis gescheitert: die Rechnung stimmte, die Oberflaeche nicht.
# Die Verteilung uebernimmt jetzt Tk selbst (stretch), und die Tests weiter
# unten messen das Ergebnis an einem echten Fenster statt den Aufruf.

# ---------------------------------------------------------------------------
# Spaltenverteilung beim Vergroessern des Fensters
#
# Gemeldet: nach dem Anpassen der Spaltenbreiten sitzt der Scrollbalken der
# mittleren Spalte falsch. Die Ursache lag eine Ebene tiefer: alle drei Bereiche
# standen auf Tks Vorgabe stretch="last", der gesamte Zuwachs ging also an die
# rechte Spalte. Gemessen wurde, dass ein um 600 px breiteres Fenster die
# Mittelspalte von 584 auf 523 px *verkleinert* hat - der Inhalt samt Balken
# blieb entsprechend schmal stehen.
# ---------------------------------------------------------------------------

@pytest.fixture
def cockpit_im_fenster(tmp_path):
    import customtkinter as ctk
    from config import AppConfig
    from services.attachment_service import AttachmentService
    from services.scoring_service import ScoringService
    from services.storage_service import StorageService
    from services.wiki_sync_service import WikiSyncService

    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)
    app = ctk.CTk()
    app.geometry("1000x700")
    view = CockpitView(
        app,
        author_name="Tester",
        scoring_service=ScoringService(),
        attachment_service=AttachmentService(config),
        wiki_service=WikiSyncService(config),
        app_config=config,
        profile=storage.load_profile(),
        storage_service=storage,
    )
    view.pack(fill="both", expand=True)
    app.update()
    view.restore_sash_positions()
    app.update()
    yield app, view
    try:
        app.destroy()
    except Exception:
        pass


def _breiten(view):
    return (view.left_frame.winfo_width(), view.center_frame.winfo_width(), view.right_tabview.winfo_width())


def _fenster_vermessbar(view) -> bool:
    """Die Testumgebung haelt jedes Fenster zurueck (conftest), dann ist jede Breite 1."""
    return view.paned.winfo_width() > 100


# --- Was headless pruefbar ist: die Konfiguration, die das Verhalten erzeugt ---

def test_only_the_middle_column_is_stretchable(cockpit_im_fenster):
    """Tks Vorgabe ist stretch="last" - damit ging der ganze Zuwachs nach rechts."""
    _, view = cockpit_im_fenster
    erwartet = {"left_frame": "never", "center_frame": "always", "right_tabview": "never"}
    for attr, soll in erwartet.items():
        ist = view.paned.paneconfigure(getattr(view, attr))["stretch"][-1]
        assert ist == soll, f"{attr}: stretch={ist!r}, erwartet {soll!r}"


def test_the_side_columns_carry_their_restored_width(cockpit_im_fenster):
    """Hier stand die umgekehrte Forderung: auf keinem Bereich duerfe width= stehen.

    Diese Annahme stammte aus dem Mittelspalten-Bug, wo ein gesetztes width= gegen
    das damalige _on_paned_configure gekaempft hat - das bei jedem Configure alle
    drei Breiten neu ausgerechnet und beide Sashes neu gesetzt hat. Dieser Code
    ist weg, und ohne width= zeigte sich der Fehler in der Gegenrichtung.

    Gemessen im laufenden Programm: sash_place() setzt nur die momentane Groesse.
    Sobald ein Kind eine neue Wunschbreite anmeldet - der CTkTabview rechts tut
    das bei jedem Tab-Wechsel, seine reqwidth pendelt zwischen 303 und 361 -
    leitet Tk die Pane-Groessen neu aus den Wunschbreiten ab und die
    wiederhergestellte Breite ist weg. Im Log fiel die rechte Spalte dabei
    innerhalb eines Idle-Durchlaufs von 614 auf 120 px (ihre minsize), waehrend
    die Mitte als einziger stretch="always"-Bereich alles geschluckt hat. Damit
    war die Spaltenbreite nach jedem Neustart wieder verstellt.

    Die beiden Seitenspalten tragen ihre Breite deshalb als -width; die Mitte
    bleibt frei, damit weiterhin sie den Zuwachs bekommt. Dass das der Fall ist,
    messen test_extra_window_width_goes_to_the_middle_column und
    test_the_form_scrollbar_follows_the_middle_column an einem echten Fenster.

    Gemessen wird an einer Attrappe statt am echten PanedWindow: die
    Testumgebung bildet das Fenster nicht ab, dort ist jede Breite 1 und
    restore_sash_positions() steigt vorzeitig aus.
    """
    _, view = cockpit_im_fenster
    view.profile.ui_settings.column_widths["cockpit_left"] = 430
    view.profile.ui_settings.column_widths["cockpit_right"] = 250

    echtes_paned = view.paned
    attrappe = MagicMock()
    attrappe.winfo_exists.return_value = True
    attrappe.winfo_width.return_value = 1600
    attrappe.cget.side_effect = lambda option: {"sashwidth": 6, "sashpad": 1}[option]
    view.paned = attrappe
    try:
        view.restore_sash_positions()

        gepinnt = {
            aufruf.args[0]: aufruf.kwargs["width"]
            for aufruf in attrappe.paneconfigure.call_args_list
        }
        assert gepinnt.get(view.left_frame) == 430, f"linke Spalte nicht gepinnt: {gepinnt}"
        assert gepinnt.get(view.right_tabview) == 250, f"rechte Spalte nicht gepinnt: {gepinnt}"
        assert view.center_frame not in gepinnt, "Mittelspalte darf nicht festgenagelt werden"

        # Die rechte Sash sitzt um sashwidth + 2*sashpad = 8px vor dem Pane:
        # 1600 - 250 - 8. Ohne diesen Zuschlag wandert die Spalte bei jedem
        # Speichern und Wiederherstellen um 8px.
        assert attrappe.sash_place.call_args_list[0].args == (0, 430, 0)
        assert attrappe.sash_place.call_args_list[1].args == (1, 1342, 0)
    finally:
        offen = getattr(view, "_sash_restore_after_id", None)
        if offen:
            try:
                view.after_cancel(offen)
            except Exception:
                pass
            view._sash_restore_after_id = None
        view.paned = echtes_paned


def test_resizing_does_not_re_place_the_sashes(cockpit_im_fenster):
    """Wer bei jedem Configure nachschiebt, kaempft gegen den Geometriemanager.

    Genau das war der Fehler: die Rechnung stimmte, Tk hat sie danach wieder
    ueberschrieben. Der Handler rechnet deshalb keine Breiten mehr aus und fasst
    die Sashes nicht direkt an.

    Eine Ausnahme gibt es seit dem Startzeitpunkt-Fix: solange der Nutzer noch
    nicht selbst gezogen hat, plant der Handler *einen* entprellten Restore ein.
    Noetig, weil das Fenster versteckt mit 1440x880 gebaut und erst danach
    maximiert wird - der erste Restore lief auf total=1426, das PanedWindow
    erreichte seine echten 1906 erst 40ms spaeter. Die rechte Spalte wird als
    Abstand vom rechten Rand wiederhergestellt und braucht daher die endgueltige
    Gesamtbreite. Direkt waehrend des Configure passiert aber weiterhin nichts.
    """
    _, view = cockpit_im_fenster
    echtes_paned = view.paned
    attrappe = MagicMock()
    attrappe.winfo_exists.return_value = True
    attrappe.winfo_width.return_value = 1600
    view.paned = attrappe
    try:
        ereignis = MagicMock()
        ereignis.widget = attrappe
        ereignis.width = 1600
        view._on_paned_configure(ereignis)
        assert attrappe.sash_place.call_count == 0, "Handler verschiebt die Sashes weiterhin"
        assert view._last_paned_width == 1600
    finally:
        # Den entprellten Restore abraeumen, sonst laeuft er spaeter gegen das
        # bereits zerstoerte Fenster.
        offen = getattr(view, "_sash_restore_after_id", None)
        if offen:
            try:
                view.after_cancel(offen)
            except Exception:
                pass
            view._sash_restore_after_id = None
        view.paned = echtes_paned


def test_resizing_stops_nudging_once_the_user_has_dragged(cockpit_im_fenster):
    """Nach dem ersten eigenen Zug darf nichts mehr automatisch nachziehen."""
    _, view = cockpit_im_fenster
    echtes_paned = view.paned
    attrappe = MagicMock()
    attrappe.winfo_exists.return_value = True
    attrappe.winfo_width.return_value = 1700
    view.paned = attrappe
    view._sash_user_dragged = True
    view._sash_restore_after_id = None
    try:
        ereignis = MagicMock()
        ereignis.widget = attrappe
        ereignis.width = 1700
        view._on_paned_configure(ereignis)
        assert attrappe.sash_place.call_count == 0
        assert view._sash_restore_after_id is None, "Restore wird trotz Nutzerzug nachgeplant"
    finally:
        view._sash_user_dragged = False
        view.paned = echtes_paned


def test_resizing_does_not_overwrite_the_saved_column_widths(cockpit_im_fenster):
    """Gemeldet: die eingestellten Spaltenbreiten waren nach dem Neustart wieder weg.

    Der Configure-Handler hat die drei Breiten bei jeder Fenstergroessenaenderung
    neu ausgerechnet (2/3 Mitte, je 1/6 aussen) und das Ergebnis ins Profil
    geschrieben. Beim Beenden wurde dann diese Rechnung gespeichert, nicht das,
    was der Nutzer gezogen hatte. Gemessen mit gespeicherten 430/250 px, Fenster
    1400 -> 1000 -> 1600 -> 1200 px: 430/250 -> 363/184 -> 463/284 -> 396/661.
    """
    _, view = cockpit_im_fenster
    view.profile.ui_settings.column_widths["cockpit_left"] = 430
    view.profile.ui_settings.column_widths["cockpit_right"] = 250

    echtes_paned = view.paned
    attrappe = MagicMock()
    attrappe.winfo_exists.return_value = True
    attrappe.winfo_width.return_value = 1000
    attrappe.sash_coord.side_effect = lambda i: [(430, 0), (1150, 0)][i]
    view.paned = attrappe
    view._last_paned_width = 1400
    try:
        for breite in (1000, 1600, 1200):
            attrappe.winfo_width.return_value = breite
            ereignis = MagicMock()
            ereignis.widget = attrappe
            ereignis.width = breite
            view._on_paned_configure(ereignis)

        assert view.profile.ui_settings.column_widths["cockpit_left"] == 430
        assert view.profile.ui_settings.column_widths["cockpit_right"] == 250
    finally:
        view.paned = echtes_paned


# --- Das sichtbare Ergebnis, sobald ein echtes Fenster vorhanden ist ---
#
# Gemessen ausserhalb der Testsuite (Fenster 1000 -> 1600 px):
#   vorher:  links 227 -> 327, mitte 584 -> 523, rechts 159 -> 720
#   nachher: links 299 -> 299, mitte 358 -> 958, rechts 313 -> 313

def test_extra_window_width_goes_to_the_middle_column(cockpit_im_fenster):
    app, view = cockpit_im_fenster
    if not _fenster_vermessbar(view):
        pytest.skip("Fenster ist in dieser Umgebung nicht abgebildet - Breiten nicht messbar")

    links_vor, mitte_vor, rechts_vor = _breiten(view)
    app.geometry("1600x700")
    app.update()
    links, mitte, rechts = _breiten(view)

    assert mitte > mitte_vor, f"Mittelspalte waechst nicht mit: {mitte_vor} -> {mitte}"
    assert abs(links - links_vor) <= 2, f"linke Spalte veraendert: {links_vor} -> {links}"
    assert abs(rechts - rechts_vor) <= 2, f"rechte Spalte veraendert: {rechts_vor} -> {rechts}"


def test_the_form_scrollbar_follows_the_middle_column(cockpit_im_fenster):
    """Das ist das, was man sieht: der Balken blieb sonst mitten im Formular stehen."""
    app, view = cockpit_im_fenster
    if not _fenster_vermessbar(view):
        pytest.skip("Fenster ist in dieser Umgebung nicht abgebildet - Breiten nicht messbar")

    sf = view.form_widget.scroll_frame
    balken = getattr(sf, "_scrollbar", None)
    assert balken is not None
    balken.grid(row=0, column=1, rowspan=2, sticky="ns")

    app.geometry("1600x700")
    app.update()

    rechter_rand = view.center_frame.winfo_rootx() + view.center_frame.winfo_width()
    abstand = rechter_rand - balken.winfo_rootx()
    assert 0 <= abstand <= 40, f"Balken steht {abstand} px vom rechten Rand entfernt"
