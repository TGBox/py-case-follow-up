"""Long timelines only build the newest page of cards.

Every card costs ~20 Tk widgets. Building all of them made each case switch
and each window resize grow linearly with the case history (and at a few
hundred entries the scroll content outgrew what X11 can allocate).
"""

import customtkinter as ctk
import pytest

from constants import TIMELINE_PAGE_SIZE
from models.case import TimelineEntry
from services.i18n_service import get_i18n
from ui.widgets.timeline_widget import TimelineWidget


@pytest.fixture
def root():
    get_i18n().current_language = "de"
    r = ctk.CTk()
    r.geometry("600x400+0+0")
    yield r
    try:
        r.destroy()
    except Exception:
        pass


def _entries(n: int) -> list[TimelineEntry]:
    return [
        TimelineEntry(timestamp=f"2026-09-01T10:{i // 60:02d}:{i % 60:02d}", author="Robert", channel="EMAIL", note=f"Notiz {i}")
        for i in range(n)
    ]


def _cards(widget: TimelineWidget) -> list:
    return [c for c in widget.scroll_frame.winfo_children() if c is not widget._older_btn]


def _note_texts(widget: TimelineWidget) -> list[str]:
    import tkinter as tk

    def walk(w):
        for c in w.winfo_children():
            yield c
            yield from walk(c)

    return [t.get("1.0", "end-1c") for c in _cards(widget) for t in walk(c) if isinstance(t, tk.Text)]


def _widget(root) -> TimelineWidget:
    return TimelineWidget(root, author_name="Daniel Rösch", on_timeline_updated=lambda _e: None)


def test_short_timeline_has_no_older_button(root):
    w = _widget(root)
    w.load_timeline(_entries(TIMELINE_PAGE_SIZE))
    assert len(_cards(w)) == TIMELINE_PAGE_SIZE
    assert w._older_btn is None


def test_long_timeline_shows_newest_page_and_button(root):
    n = TIMELINE_PAGE_SIZE * 2 + 3
    w = _widget(root)
    w.load_timeline(_entries(n))
    assert len(_cards(w)) == TIMELINE_PAGE_SIZE
    assert _note_texts(w)[0] == f"Notiz {n - 1}"  # newest first
    assert w._older_btn is not None
    assert f"({n - TIMELINE_PAGE_SIZE})" in w._older_btn.cget("text")
    # The button sits below the cards.
    assert w.scroll_frame.winfo_children()[-1] is w._older_btn


def test_show_older_appends_pages_until_all_are_shown(root):
    n = TIMELINE_PAGE_SIZE * 2 + 3
    w = _widget(root)
    w.load_timeline(_entries(n))
    w._older_btn.invoke()
    assert len(_cards(w)) == TIMELINE_PAGE_SIZE * 2
    assert "(3)" in w._older_btn.cget("text")
    w._older_btn.invoke()
    assert len(_cards(w)) == n
    assert w._older_btn is None
    assert _note_texts(w) == [f"Notiz {i}" for i in reversed(range(n))]


def test_rerender_of_same_case_keeps_expanded_entries(root):
    """A new note or an edit must not collapse what the user opened."""
    w = _widget(root)
    w.load_timeline(_entries(TIMELINE_PAGE_SIZE * 2 + 3))
    w.show_older_entries()
    w.note_textbox.insert("1.0", "neu")
    w.on_add_note()
    assert len(_cards(w)) == TIMELINE_PAGE_SIZE * 2


def test_other_case_starts_with_newest_page_again(root):
    w = _widget(root)
    w.load_timeline(_entries(TIMELINE_PAGE_SIZE * 3))
    w.show_older_entries()
    w.load_timeline(_entries(TIMELINE_PAGE_SIZE * 3))
    assert len(_cards(w)) == TIMELINE_PAGE_SIZE


def test_notes_share_one_highlight_font(root):
    """create_highlighted_label must not build a bold CTkFont per note: their
    finalisers ran on whatever thread the GC hit (see the flush deadlock)."""
    import utils.ui_utils as ui_utils

    created: list = []
    orig = ui_utils.ctk.CTkFont

    class CountingFont(orig):
        def __init__(self, *a, **kw):
            created.append(kw)
            super().__init__(*a, **kw)

    w = _widget(root)
    w._card_fonts()
    ui_utils.ctk.CTkFont = CountingFont
    try:
        w.load_timeline(_entries(5))
    finally:
        ui_utils.ctk.CTkFont = orig
    assert created == []
