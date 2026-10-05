"""Coming back from the tray must restore the window exactly as it was.

Tk's deiconify always returns a hidden window as a plain "normal" window: a
maximized app reappeared after a notification click as a small window at the
default geometry. The app now records maximized/normal/fullscreen (and the
normal size) while the window is visible and re-applies that on restore.

The Windows-specific half (deiconify dropping "zoomed") cannot be reproduced on
Linux/CI, so the window manager calls are recorded on a stub instead.
"""

import pytest

from ui.app import SupportCockpitApp


class WindowStub:
    _remember_window_state = SupportCockpitApp._remember_window_state
    _apply_remembered_window_state = SupportCockpitApp._apply_remembered_window_state
    bring_to_foreground = SupportCockpitApp.bring_to_foreground

    def __init__(self, state="zoomed", geometry="1200x800+40+30", viewable=True):
        self.tk = object()
        self._state = state
        self._geometry = geometry
        self._viewable = viewable
        self._x, self._y = 40, 30
        self.calls: list[tuple] = []
        self._restore_state = "zoomed"
        self._restore_geometry = None
        self._restore_fullscreen = False
        self._is_fullscreen = False

    # --- window manager surface used by the methods under test ---
    def state(self, new=None):
        if new is None:
            return self._state
        self.calls.append(("state", new))
        self._state = new

    def geometry(self, new=None):
        if new is None:
            return self._geometry
        self.calls.append(("geometry", new))
        self._geometry = new

    def winfo_viewable(self):
        return self._viewable

    def winfo_x(self):
        return self._x

    def winfo_y(self):
        return self._y

    def deiconify(self):
        # What Tk on Windows does: shown again, but always as "normal".
        self.calls.append(("deiconify",))
        self._viewable = True
        self._state = "normal"

    def withdraw(self):
        self._viewable = False
        self._state = "withdrawn"

    def attributes(self, *args):
        self.calls.append(("attributes", *args))

    def lift(self):
        pass

    def focus_force(self):
        pass

    def _update_fullscreen_button(self):
        pass

    def after(self, _ms, fn):
        fn()


def _hide_and_restore(win: WindowStub):
    win._remember_window_state()
    win.withdraw()
    win.calls.clear()
    win.bring_to_foreground()


def test_maximized_window_comes_back_maximized():
    win = WindowStub(state="zoomed")
    _hide_and_restore(win)
    assert win._state == "zoomed"
    assert ("state", "zoomed") in win.calls


def test_normal_window_comes_back_at_its_previous_size_and_position():
    win = WindowStub(state="normal", geometry="1111x777+120+80")
    _hide_and_restore(win)
    assert win._state == "normal"
    assert win._geometry == "1111x777+120+80"


def test_fullscreen_window_comes_back_fullscreen():
    win = WindowStub(state="zoomed")
    win._is_fullscreen = True
    _hide_and_restore(win)
    assert ("attributes", "-fullscreen", True) in win.calls


@pytest.mark.parametrize("state", ["iconic", "withdrawn"])
def test_hidden_states_do_not_overwrite_what_was_recorded(state):
    win = WindowStub(state="normal", geometry="900x600+10+10")
    win._remember_window_state()
    win._state = state
    win._geometry = "160x30+-32000+-32000"
    win._remember_window_state()
    assert win._restore_state == "normal"
    assert win._restore_geometry == "900x600+10+10"


def test_offscreen_parking_position_is_not_recorded():
    """A minimizing window briefly reports Windows' -32000 parking spot."""
    win = WindowStub(state="normal", geometry="900x600+10+10")
    win._remember_window_state()
    win._x = win._y = -32000
    win._geometry = "900x600+-32000+-32000"
    win._remember_window_state()
    assert win._restore_geometry == "900x600+10+10"


def test_visible_window_is_left_alone():
    """Bringing an already visible window forward must not re-maximize it."""
    win = WindowStub(state="normal", geometry="900x600+10+10")
    win._restore_state = "zoomed"
    win.bring_to_foreground()
    assert not any(c[0] in ("deiconify", "state", "geometry") for c in win.calls)
