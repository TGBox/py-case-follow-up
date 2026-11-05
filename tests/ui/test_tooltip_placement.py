"""Tooltips stay on screen; the undocked end-of-day panel stays up when the main window goes to the tray."""

import sys

import customtkinter as ctk
import pytest

from constants import TOOLTIP_POINTER_OFFSET_X as OX
from constants import TOOLTIP_POINTER_OFFSET_Y as OY
from utils.ui_utils import get_monitor_work_area, place_beside_pointer

AREA = (0, 0, 1920, 1040)  # 1080 minus taskbar


# --- placement maths --------------------------------------------------------------

def test_fits_right_of_and_below_the_pointer_when_there_is_room():
    assert place_beside_pointer(500, 400, 120, 40, OX, OY, AREA) == (500 + OX, 400 + OY)


def test_flips_left_of_the_pointer_at_the_right_screen_edge():
    """Reported: the panel docked right of a maximized window pushed 'Entkoppeln' off the screen."""
    x, y = place_beside_pointer(1905, 30, 120, 40, OX, OY, AREA)
    assert x + 120 <= 1920
    assert x + 120 < 1905, "the tooltip must not end up under the pointer"
    assert y == 30 + OY


def test_flips_above_the_pointer_at_the_bottom_edge():
    x, y = place_beside_pointer(500, 1030, 120, 40, OX, OY, AREA)
    assert (x, y + 40) == (500 + OX, 1030 - OY)


def test_bottom_right_corner_flips_both_ways():
    x, y = place_beside_pointer(1915, 1035, 120, 40, OX, OY, AREA)
    assert x + 120 <= 1920 and y + 40 <= 1040
    assert x + 120 < 1915 and y + 40 < 1035


def test_second_monitor_left_of_the_primary_has_negative_coordinates():
    left_screen = (-1920, 0, 0, 1040)
    x, _ = place_beside_pointer(-10, 300, 120, 40, OX, OY, left_screen)
    assert -1920 <= x and x + 120 <= 0


def test_popup_bigger_than_the_area_is_clamped_to_its_top_left():
    assert place_beside_pointer(50, 50, 3000, 2000, OX, OY, AREA) == (0, 0)


@pytest.mark.skipif(sys.platform != "win32", reason="Win32 monitor API")
def test_work_area_of_the_primary_monitor_excludes_nothing_outside_the_screen(root):
    left, top, right, bottom = get_monitor_work_area(root, 10, 10)
    assert left <= 10 < right and top <= 10 < bottom
    assert right - left <= root.winfo_screenwidth() + 1


def test_work_area_falls_back_to_the_screen_off_windows(root, monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    left, top, right, bottom = get_monitor_work_area(root, 10, 10)
    assert (right - left, bottom - top) == (root.winfo_vrootwidth() or root.winfo_screenwidth(),
                                            root.winfo_vrootheight() or root.winfo_screenheight())


# --- the real tooltip window --------------------------------------------------------

def _tooltip_at_edge(root, monkeypatch, text: str):
    """Shows a tooltip with the pointer 5 px left of the right edge of a fake monitor."""
    import utils.ui_utils as uu
    from ui.widgets.ctk_tooltip import CTkTooltip

    lbl = ctk.CTkLabel(root, text="Ziel")
    lbl.pack(padx=20, pady=20)
    root.update_idletasks()
    px, py = lbl.winfo_rootx() + 1, lbl.winfo_rooty() + 1
    lbl.winfo_pointerx = lambda: px
    lbl.winfo_pointery = lambda: py
    area = (px - 600, py - 400, px + 5, py + 300)
    monkeypatch.setattr(uu, "get_monitor_work_area", lambda *_a: area)
    tip = CTkTooltip(lbl, text, delay_ms=0)
    tip.show_tooltip()
    window = tip.tooltip_window
    assert window is not None
    label = window.winfo_children()[0]
    geo = window.wm_geometry()
    x, y = (int(v) for v in geo.split("+")[1:3])
    return tip, lbl, window, label, (x, y), (px, py), area


def test_tooltip_at_the_right_edge_opens_to_the_left(root, monkeypatch):
    from ui.widgets.ctk_tooltip import CTkTooltip

    tip, lbl, window, label, (x, y), (px, py), area = _tooltip_at_edge(root, monkeypatch, "Entkoppeln")
    try:
        assert x + label.winfo_reqwidth() <= area[2]
        assert x + label.winfo_reqwidth() < px, "left of the pointer, not under it"
        assert y == py + OY
    finally:
        CTkTooltip.dismiss_all()
        lbl.destroy()


def test_tooltip_wider_than_the_monitor_wraps(root, monkeypatch):
    from ui.widgets.ctk_tooltip import CTkTooltip

    tip, lbl, window, label, (x, _y), _p, area = _tooltip_at_edge(root, monkeypatch, "Sehr langer Hinweis " * 60)
    try:
        assert int(label.cget("wraplength")) > 0
        assert area[0] <= x and x + label.winfo_reqwidth() <= area[2]
    finally:
        CTkTooltip.dismiss_all()
        lbl.destroy()


# --- undocked panel and the tray -------------------------------------------------------

def test_floating_panel_is_not_owned_by_the_main_window(root):
    """Windows hides owned (transient) windows with their owner - the undocked panel went to the tray too."""
    from ui.widgets.checkout_panel import CheckoutFloatingWindow

    floating = CheckoutFloatingWindow(master=root, on_dock_callback=lambda: None, on_close_callback=lambda: None)
    try:
        assert floating.transient() == ""
        if sys.platform == "win32":  # X11 without a window manager does not report these back
            assert floating.attributes("-topmost")
            if floating._frameless:
                assert floating.overrideredirect(), "no own taskbar button and no OS frame"
            else:
                assert floating.attributes("-toolwindow"), "no own taskbar button"
    finally:
        floating.destroy()


def test_minimizing_to_tray_leaves_the_undocked_panel_alone(config):
    """on_closing() hides the main window only; the floating panel is neither withdrawn nor iconified."""
    from services.storage_service import StorageService
    from ui.app import SupportCockpitApp

    storage = StorageService(config)
    profile = storage.load_profile()
    profile.checkout_settings.is_docked = False
    storage.save_profile(profile, sync=True)
    app = SupportCockpitApp(config)
    try:
        app.update()
        app.show_checkout_panel()
        floating = app.checkout_floating_window
        assert floating is not None and floating.winfo_exists()
        assert floating.transient() == ""

        calls: list[str] = []
        floating.withdraw = lambda: calls.append("withdraw")
        floating.iconify = lambda: calls.append("iconify")
        app.on_closing()
        assert calls == []
        assert floating.winfo_exists()
    finally:
        app.destroy()
