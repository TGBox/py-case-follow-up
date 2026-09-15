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


def test_the_panes_are_not_pinned_to_a_fixed_width(cockpit_im_fenster):
    """Ein gesetztes width= naegelt einen Bereich fest und war Teil der Ursache."""
    _, view = cockpit_im_fenster
    for attr in ("left_frame", "center_frame", "right_tabview"):
        breite = view.paned.paneconfigure(getattr(view, attr))["width"][-1]
        assert breite in ("", None), f"{attr} ist auf width={breite!r} festgenagelt"


def test_resizing_does_not_re_place_the_sashes(cockpit_im_fenster):
    """Wer bei jedem Configure nachschiebt, kaempft gegen den Geometriemanager.

    Genau das war der Fehler: die Rechnung stimmte, Tk hat sie danach wieder
    ueberschrieben. Der Handler darf die Sashes nicht mehr anfassen.
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
