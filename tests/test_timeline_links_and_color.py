"""Clickable links in timeline notes and the colour-tinted own-entry cards."""

import tkinter as tk
from types import SimpleNamespace

import customtkinter as ctk
import pytest

from constants import COLOR_CARD_BG, COLOR_ON_ACCENT_DARK, COLOR_ON_ACCENT_LIGHT
from models.case import TimelineEntry
from services.i18n_service import get_i18n
from ui.widgets.timeline_widget import TimelineWidget
from utils.ui_utils import find_links, linkify_text_widget, mix_colors, readable_text_on


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


# ---------------------------------------------------------------- find_links

@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("siehe https://wiki.carasent.de/x.", [("https://wiki.carasent.de/x", "https://wiki.carasent.de/x")]),
        ("(http://a.de/b)", [("http://a.de/b", "http://a.de/b")]),
        ("https://de.wikipedia.org/wiki/Foo_(Bar)", [("https://de.wikipedia.org/wiki/Foo_(Bar)", "https://de.wikipedia.org/wiki/Foo_(Bar)")]),
        ("Doku: www.carasent.de, danach", [("www.carasent.de", "https://www.carasent.de")]),
        ("mailto:support@carasent.de!", [("mailto:support@carasent.de", "mailto:support@carasent.de")]),
        ("Kein Link hier, nur Text.", []),
        ("nur https:// ohne Ziel", []),
    ],
)
def test_find_links(text, expected):
    assert find_links(text) == expected


def test_find_links_multiple_in_order():
    text = "A https://a.de B\nC http://b.de/q?x=1&y=2 D"
    assert [t for _, t in find_links(text)] == ["https://a.de", "http://b.de/q?x=1&y=2"]


# ------------------------------------------------------- linkify_text_widget

def _make_text(root, content):
    txt = tk.Text(root, height=3, width=60)
    txt.insert("1.0", content)
    txt.configure(state="disabled")
    txt.pack()
    return txt


def _ev(x, y):
    return SimpleNamespace(x=x, y=y)


def test_links_are_tagged_and_bound(root):
    opened = []
    txt = _make_text(root, "🔧 Ticket: www.carasent.de und https://x.de/a.")
    targets = linkify_text_widget(txt, ("#1d4ed8", "#8ab4ff"), opener=opened.append)
    assert targets == ["https://www.carasent.de", "https://x.de/a"]

    # The emoji at the start must not shift the tagged ranges.
    r0 = txt.tag_ranges("link-0")
    assert txt.get(r0[0], r0[1]) == "www.carasent.de"
    r1 = txt.tag_ranges("link-1")
    assert txt.get(r1[0], r1[1]) == "https://x.de/a"
    assert txt.tag_cget("link", "underline") in ("1", 1, True)

    for tag in ("link-0", "link-1"):
        assert txt.tk.call(txt._w, "tag", "bind", tag, "<ButtonPress-1>")
        assert txt.tk.call(txt._w, "tag", "bind", tag, "<ButtonRelease-1>")
    assert txt.tk.call(txt._w, "tag", "bind", "link", "<Enter>")


def test_plain_click_opens_target(root):
    opened = []
    txt = _make_text(root, "https://x.de/a")
    linkify_text_widget(txt, "#1d4ed8", opener=opened.append)
    handler = txt.link_click_handler
    handler.press(_ev(10, 5))
    assert handler.release(_ev(11, 6), "https://x.de/a") is True
    assert opened == ["https://x.de/a"]


def test_drag_or_selection_does_not_open(root):
    opened = []
    txt = _make_text(root, "https://x.de/a")
    linkify_text_widget(txt, "#1d4ed8", opener=opened.append)
    handler = txt.link_click_handler

    handler.press(_ev(10, 5))
    assert handler.release(_ev(60, 5), "https://x.de/a") is False

    txt.tag_add("sel", "1.0", "1.5")
    handler.press(_ev(10, 5))
    assert handler.release(_ev(10, 5), "https://x.de/a") is False

    # Release without a press on the link (press started elsewhere)
    txt.tag_remove("sel", "1.0", "end")
    assert handler.release(_ev(10, 5), "https://x.de/a") is False
    assert opened == []


def test_opener_failure_is_swallowed(root):
    def boom(_url):
        raise OSError("no browser")
    txt = _make_text(root, "https://x.de")
    linkify_text_widget(txt, "#1d4ed8", opener=boom)
    txt.link_click_handler.press(_ev(1, 1))
    assert txt.link_click_handler.release(_ev(1, 1), "https://x.de") is False


def test_no_links_leaves_widget_untouched(root):
    txt = _make_text(root, "nur Text")
    assert linkify_text_widget(txt, "#1d4ed8") == []
    assert "link" not in txt.tag_names()


# --------------------------------------------------------------- colour help

def test_mix_and_contrast_helpers(root):
    assert mix_colors(root, "#ff0000", "#ffffff", 0) == "#ffffff"
    assert mix_colors(root, "#ff0000", "#ffffff", 1) == "#ff0000"
    assert mix_colors(root, "#000000", "#ffffff", 0.5) in ("#7f7f7f", "#808080")
    # CTk-style colour names resolve too
    assert mix_colors(root, "#3b82f6", "gray23", 0.2).startswith("#")
    assert readable_text_on(root, "#f59e0b") == COLOR_ON_ACCENT_DARK
    assert readable_text_on(root, "#1e3a8a") == COLOR_ON_ACCENT_LIGHT


# ------------------------------------------------------------ timeline cards

def _entries():
    return [
        TimelineEntry(timestamp="2026-08-25T11:18:59", author="Felipe", channel="EMAIL", note="Von Felipe"),
        TimelineEntry(timestamp="2026-08-25T14:44:26", author="Daniel Rösch", channel="EMAIL", note="Doku: https://wiki.carasent.de/seite"),
    ]


def _walk(w):
    for c in w.winfo_children():
        yield c
        yield from _walk(c)


def test_own_card_is_tinted_with_chip_and_rail(root):
    widget = TimelineWidget(root, author_name="Daniel Rösch", on_timeline_updated=lambda _e: None,
                            user_color="#10b981", color_marker_enabled=True)
    widget.load_timeline(_entries())
    own_card, other_card = widget.scroll_frame.winfo_children()

    assert own_card.cget("fg_color") != COLOR_CARD_BG
    assert own_card.cget("fg_color")[0] == mix_colors(root, "#10b981", COLOR_CARD_BG[0], 0.09)
    assert other_card.cget("fg_color") == COLOR_CARD_BG

    chips = [c for c in _walk(own_card) if isinstance(c, ctk.CTkLabel) and c.cget("text") == "Daniel Rösch"]
    assert chips and chips[0].cget("fg_color") == "#10b981"

    rails = [c for c in _walk(own_card) if isinstance(c, ctk.CTkFrame) and c.cget("fg_color") == "#10b981"]
    assert len(rails) == 1
    assert not [c for c in _walk(other_card) if isinstance(c, ctk.CTkFrame) and c.cget("fg_color") == "#10b981"]

    # The note text sits on the tinted background, not on a white box.
    notes = [c for c in _walk(own_card) if isinstance(c, tk.Text)]
    mode_idx = 1 if ctk.get_appearance_mode().lower() == "dark" else 0
    assert notes[0].cget("bg") == own_card.cget("fg_color")[mode_idx]
    assert "link" in notes[0].tag_names()


def test_invalid_user_color_falls_back_to_neutral(root):
    widget = TimelineWidget(root, author_name="Daniel Rösch", on_timeline_updated=lambda _e: None,
                            user_color="keine-farbe", color_marker_enabled=True)
    widget.load_timeline(_entries())
    own_card = widget.scroll_frame.winfo_children()[0]
    assert own_card.cget("fg_color") == COLOR_CARD_BG
