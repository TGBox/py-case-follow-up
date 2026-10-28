"""TimelineWidget: cards, colour markers, links, paging, note editing, note height and the date-picker time bounds."""

import tkinter as tk
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import customtkinter as ctk
import pytest

from constants import (
    COLOR_CARD_BG,
    COLOR_ON_ACCENT_DARK,
    COLOR_ON_ACCENT_LIGHT,
    TEXTBOX_HEIGHT_SM,
    TIMELINE_NOTE_HEIGHT_KEY,
    TIMELINE_NOTE_MAX_HEIGHT,
    TIMELINE_NOTE_MIN_HEIGHT,
    TIMELINE_PAGE_SIZE,
)
from models.case import TimelineEntry
from models.profile import UISettings, UserProfile
from services.i18n_service import get_i18n
from ui.widgets.date_picker import DatePickerWidget
from ui.widgets.timeline_widget import TimelineWidget
from utils.datetime_utils import (
    clamp_datetime_to_now,
    get_local_now,
    parse_followup_datetime,
    parse_iso,
)
from utils.ui_utils import contrast_ratio, find_links, linkify_text_widget, mix_colors, readable_text_on, readable_variant


def _walk(w):
    for c in w.winfo_children():
        yield c
        yield from _walk(c)


def _label_texts(parent) -> list[str]:
    return [c.cget("text") for c in _walk(parent) if isinstance(c, ctk.CTkLabel)]


def _widget(root, received=None, author="Daniel", **kw) -> TimelineWidget:
    sink = received if received is not None else []
    return TimelineWidget(root, author_name=author, on_timeline_updated=lambda e: sink.append(list(e)), **kw)


def _cards(widget: TimelineWidget) -> list:
    return [c for c in widget.scroll_frame.winfo_children() if c is not widget._older_btn]


def _note_texts(widget: TimelineWidget) -> list[str]:
    return [t.get("1.0", "end-1c") for c in _cards(widget) for t in _walk(c) if isinstance(t, tk.Text)]


def _many(n: int) -> list[TimelineEntry]:
    return [
        TimelineEntry(timestamp=f"2026-09-01T10:{i // 60:02d}:{i % 60:02d}", author="Robert", channel="EMAIL", note=f"Notiz {i}")
        for i in range(n)
    ]


# --- time bounds ------------------------------------------------------------

_NOW = datetime(2026, 9, 30, 14, 12, 45).astimezone()


@pytest.mark.parametrize(
    ("value", "bound", "expected"),
    [
        (_NOW - timedelta(days=3), "future", _NOW.replace(second=0, microsecond=0)),
        (_NOW.replace(second=0), "future", _NOW.replace(second=0)),
        (_NOW + timedelta(hours=2), "future", _NOW + timedelta(hours=2)),
        (_NOW + timedelta(days=1), "past", _NOW),
        (_NOW - timedelta(days=1), "past", _NOW - timedelta(days=1)),
    ],
)
def test_clamp_datetime_to_now(value, bound, expected):
    assert clamp_datetime_to_now(value, bound, now=_NOW) == expected


def test_date_picker_time_bounds(root):
    """Wiedervorlage pickers move past values to now, timeline pickers move future values to now."""
    floor = get_local_now().replace(second=0, microsecond=0)
    future_text = (get_local_now() + timedelta(days=3)).strftime("%d.%m.%Y 09:00")

    initial = DatePickerWidget(root, include_time=True, initial_value="2020-01-01T08:00:00", time_bound="future")
    assert parse_followup_datetime(initial.get()) >= floor

    fut = DatePickerWidget(root, include_time=True, time_bound="future")
    fut.set_date("01.01.2020 16:30")
    assert parse_followup_datetime(fut.get()) >= floor
    fut.set_date(future_text)
    assert fut.get() == future_text

    past = DatePickerWidget(root, include_time=True, time_bound="past")
    past.set_date(future_text)
    assert parse_followup_datetime(past.get()) <= get_local_now()

    unbounded = DatePickerWidget(root, include_time=True)
    unbounded.set_date("01.01.2020 16:30")
    assert unbounded.get() == "01.01.2020 16:30"


def test_flyout_bump_uses_now_instead_of_past_value(root):
    from ui.dialogs.followup_flyout_dialog import FollowupFlyoutDialog

    picker = DatePickerWidget(root, include_time=True, time_bound="future")
    picker.entry.insert(0, "01.01.2020 08:00")
    before = get_local_now().replace(second=0, microsecond=0)
    FollowupFlyoutDialog.bump_hours(None, picker, 1)  # type: ignore[arg-type]
    assert parse_followup_datetime(picker.get()) >= before + timedelta(minutes=59)


# --- adding, editing, deleting entries --------------------------------------

def test_add_note_with_past_time_is_sorted_in(root):
    received = []
    w = _widget(root, received)
    w.load_timeline([
        TimelineEntry(timestamp="2026-09-01T10:00:00", author="A", note="alt"),
        TimelineEntry(timestamp="2026-09-10T10:00:00", author="A", note="neu"),
    ])
    w.note_textbox.insert("1.0", "nachgetragen")
    w.time_picker.set_date("05.09.2026 11:30")
    w.on_add_note()

    assert [e.note for e in received[-1]] == ["alt", "nachgetragen", "neu"]
    added = received[-1][1]
    assert (added.timestamp, added.author) == ("2026-09-05T11:30:00", "Daniel")
    assert w.time_picker.get() == ""


def test_add_note_without_time_or_with_future_time_lands_at_now(root):
    received = []
    w = _widget(root, received)
    w.load_timeline([])
    before = get_local_now().replace(microsecond=0) - timedelta(seconds=1)
    w.note_textbox.insert("1.0", "jetzt")
    w.on_add_note()
    assert parse_iso(received[-1][-1].timestamp) >= before

    w.note_textbox.insert("1.0", "zukunft")
    w.time_picker.entry.insert(0, (get_local_now() + timedelta(days=2)).strftime("%d.%m.%Y %H:%M"))
    w.on_add_note()
    assert parse_iso(received[-1][-1].timestamp) <= get_local_now()


def test_add_note_with_unreadable_time_keeps_text(root):
    received = []
    w = _widget(root, received)
    w.load_timeline([])
    w.note_textbox.insert("1.0", "bleibt")
    w.time_picker.entry.insert(0, "gestern irgendwann")
    w.on_add_note()
    assert received == []
    assert w.note_textbox.get("1.0", "end-1c") == "bleibt"


def test_edit_entry_marks_it_and_resorts(root):
    received = []
    w = _widget(root, received, author="Felipe")
    first = TimelineEntry(timestamp="2026-09-01T10:00:00", author="Daniel", channel="EMAIL", note="eins")
    second = TimelineEntry(timestamp="2026-09-10T10:00:00", author="Daniel", note="zwei")
    w.load_timeline([first, second])

    w.apply_entry_edit(first, datetime(2026, 9, 12, 9, 15).astimezone(), "PHONE_INBOUND", "eins korrigiert")

    entries = received[-1]
    assert [e.note for e in entries] == ["zwei", "eins korrigiert"]
    edited = entries[1]
    assert edited.timestamp == "2026-09-12T09:15:00"
    assert edited.channel == "PHONE_INBOUND"
    assert edited.author == "Daniel", "original author stays"
    assert edited.edited_by == "Felipe" and edited.edited_at
    assert any("bearbeitet" in t and "Felipe" in t for t in _label_texts(w.scroll_frame))


def test_edit_without_changes_does_not_mark_and_delete_removes(root):
    received = []
    w = _widget(root, received)
    entry = TimelineEntry(timestamp="2026-09-01T10:00:37", author="Daniel", channel="EMAIL", note="eins")
    other = TimelineEntry(timestamp="2026-09-02T10:00:00", author="A", note="b")
    w.load_timeline([entry, other])
    w.apply_entry_edit(entry, parse_iso("2026-09-01T10:00:00"), "EMAIL", "eins")
    assert received == []
    assert entry.edited_at == ""
    assert entry.timestamp == "2026-09-01T10:00:37", "seconds survive when the minute is unchanged"

    w.delete_entry(entry)
    assert [e.note for e in received[-1]] == ["b"]


def test_timeline_entry_edit_fields_roundtrip_and_stay_out_when_empty():
    assert "edited_at" not in TimelineEntry(timestamp="2026-09-01T10:00:00", author="A", note="x").to_dict()
    edited = TimelineEntry(timestamp="2026-09-01T10:00:00", author="A", note="x", edited_at="2026-09-30T12:00:00", edited_by="B")
    restored = TimelineEntry.from_dict(edited.to_dict())
    assert (restored.edited_at, restored.edited_by) == ("2026-09-30T12:00:00", "B")


def test_edit_dialog_save_delete_and_empty_note(root, monkeypatch):
    from ui.dialogs import confirm_dialog
    from ui.dialogs.timeline_entry_dialog import TimelineEntryDialog

    entry = TimelineEntry(timestamp="2026-09-01T10:00:00", author="Daniel", channel="EMAIL", note="alt")
    saved, deleted = [], []
    dlg = TimelineEntryDialog(root, entry, on_save=lambda dt, ch, note: saved.append((dt, ch, note)), on_delete=lambda: deleted.append(True))
    dlg.update_idletasks()
    assert (dlg.date_picker.entry.get(), dlg.date_picker.time_entry.get()) == ("01.09.2026", "10:00")
    assert dlg.date_picker.get_iso() == "2026-09-01T10:00:00"
    dlg.note_textbox.delete("1.0", "end")
    dlg.note_textbox.insert("1.0", "neu")
    dlg.on_click_save()
    assert saved and saved[0][2] == "neu"
    assert saved[0][0].strftime("%Y-%m-%dT%H:%M") == "2026-09-01T10:00"

    # Delete asks first - declined means nothing happens.
    dlg2 = TimelineEntryDialog(root, entry, on_save=lambda *a: None, on_delete=lambda: deleted.append(True))
    monkeypatch.setattr(confirm_dialog, "ask_confirmation", lambda *a, **k: False)
    dlg2.on_click_delete()
    assert deleted == []
    monkeypatch.setattr(confirm_dialog, "ask_confirmation", lambda *a, **k: True)
    dlg2.on_click_delete()
    assert deleted == [True]

    saved.clear()
    dlg3 = TimelineEntryDialog(root, entry, on_save=lambda *a: saved.append(a))
    dlg3.note_textbox.delete("1.0", "end")
    dlg3.on_click_save()
    assert saved == []
    assert dlg3.error_label.cget("text")
    dlg3.destroy()


# --- card rendering and the personal colour marker -------------------------

def _two_authors():
    return [
        TimelineEntry(timestamp="2026-08-25T11:18:59", author="Felipe", channel="INTERNAL_NOTE", note="Von Felipe"),
        TimelineEntry(timestamp="2026-08-25T14:44:26", author="Daniel Rösch", channel="EMAIL", note="Doku: https://wiki.carasent.de/seite"),
    ]


def test_own_card_is_tinted_with_chip_and_rail(root):
    widget = _widget(root, author="Daniel Rösch", user_color="#10b981", color_marker_enabled=True)
    widget.load_timeline(_two_authors())
    own_card, other_card = widget.scroll_frame.winfo_children()

    def rails(card):
        return [c for c in _walk(card) if isinstance(c, ctk.CTkFrame) and c.cget("fg_color") == "#10b981"]

    assert own_card.cget("fg_color")[0] == mix_colors(root, "#10b981", COLOR_CARD_BG[0], 0.09)
    assert other_card.cget("fg_color") == COLOR_CARD_BG
    assert len(rails(own_card)) == 1 and not rails(other_card)

    chips = [c for c in _walk(own_card) if isinstance(c, ctk.CTkLabel) and c.cget("text") == "Daniel Rösch"]
    assert chips
    assert not any("👤" in t for t in _label_texts(own_card)), "person icon was removed from the card"
    # Borderless chip with a lightly tinted fill and readable name colour.
    assert not isinstance(chips[0].master, ctk.CTkFrame) or chips[0].master.cget("border_width") == 0
    fill = chips[0].cget("fg_color")
    assert "#10b981" not in fill
    for mode_idx in (0, 1):
        assert contrast_ratio(root, chips[0].cget("text_color")[mode_idx], fill[mode_idx]) >= 4.5

    # The note text sits on the tinted background and carries the link tag.
    notes = [c for c in _walk(own_card) if isinstance(c, tk.Text)]
    mode_idx = 1 if ctk.get_appearance_mode().lower() == "dark" else 0
    assert notes[0].cget("bg") == own_card.cget("fg_color")[mode_idx]
    assert "link" in notes[0].tag_names()

    # Every card has its own edit button.
    assert len([b for b in _walk(widget.scroll_frame) if isinstance(b, ctk.CTkButton) and b.cget("text") == "✏"]) == 2

    widget.set_user_color_settings(user_color="#10b981", color_marker_enabled=False)
    assert not rails(widget.scroll_frame.winfo_children()[0])


def test_invalid_user_color_falls_back_to_neutral(root):
    widget = _widget(root, author="Daniel Rösch", user_color="keine-farbe", color_marker_enabled=True)
    widget.load_timeline(_two_authors())
    assert widget.scroll_frame.winfo_children()[0].cget("fg_color") == COLOR_CARD_BG


def test_status_line_is_not_shown_and_edit_button_is_flat(root):
    widget = _widget(root, author="Daniel Rösch", user_color="#eab308", color_marker_enabled=True)
    widget.load_timeline([TimelineEntry(timestamp="2026-10-07T10:24:00", author="Daniel Rösch", channel="EMAIL",
                                        note="Text", status_change="NEW -> ACTION_REQUIRED (SUPPORT)")])
    card = widget.scroll_frame.winfo_children()[0]
    assert not any("ACTION_REQUIRED" in t or t.startswith("Status") for t in _label_texts(card))
    buttons = [c for c in _walk(card) if isinstance(c, ctk.CTkButton)]
    assert len(buttons) == 1 and buttons[0].cget("fg_color") == "transparent"


def test_colour_helpers(root):
    assert mix_colors(root, "#ff0000", "#ffffff", 0) == "#ffffff"
    assert mix_colors(root, "#ff0000", "#ffffff", 1) == "#ff0000"
    assert mix_colors(root, "#000000", "#ffffff", 0.5) in ("#7f7f7f", "#808080")
    assert mix_colors(root, "#3b82f6", "gray23", 0.2).startswith("#")  # CTk colour names resolve
    assert readable_text_on(root, "#f59e0b") == COLOR_ON_ACCENT_DARK
    assert readable_text_on(root, "#1e3a8a") == COLOR_ON_ACCENT_LIGHT

    light_bg, dark_bg = "#fdf8e6", "#3d3a2e"
    assert contrast_ratio(root, readable_variant(root, "#eab308", light_bg), light_bg) >= 4.5
    assert readable_variant(root, "#eab308", dark_bg) == "#eab308", "already readable on dark - left untouched"


def test_labels_follow_language_switch(root):
    widget = _widget(root, author="Tester")
    assert "Hinzufügen" in widget.add_btn.cget("text")
    assert "Textbaustein" in widget.snip_btn.cget("text")
    assert any("Telefon" in c for c in widget.channel_combo.cget("values"))

    get_i18n().current_language = "en"
    widget.refresh_ui_labels()
    assert "Add Note" in widget.add_btn.cget("text")
    assert any("Phone" in c for c in widget.channel_combo.cget("values"))

    get_i18n().current_language = "sv"
    widget.refresh_ui_labels()
    assert "Lägg till" in widget.add_btn.cget("text")


# --- links in notes ---------------------------------------------------------

@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("siehe https://wiki.carasent.de/x.", ["https://wiki.carasent.de/x"]),
        ("(http://a.de/b)", ["http://a.de/b"]),
        ("https://de.wikipedia.org/wiki/Foo_(Bar)", ["https://de.wikipedia.org/wiki/Foo_(Bar)"]),
        ("mailto:support@carasent.de!", ["mailto:support@carasent.de"]),
        ("A https://a.de B\nC http://b.de/q?x=1&y=2 D", ["https://a.de", "http://b.de/q?x=1&y=2"]),
        ("Kein Link hier, nur Text.", []),
        ("nur https:// ohne Ziel", []),
    ],
)
def test_find_links(text, expected):
    assert find_links(text) == [(t, t) for t in expected]


def test_find_links_adds_scheme_to_www():
    assert find_links("Doku: www.carasent.de, danach") == [("www.carasent.de", "https://www.carasent.de")]


def _text_widget(root, content):
    txt = tk.Text(root, height=3, width=60)
    txt.insert("1.0", content)
    txt.configure(state="disabled")
    txt.pack()
    return txt


def _ev(x, y):
    return SimpleNamespace(x=x, y=y)


def test_links_are_tagged_and_bound(root):
    txt = _text_widget(root, "🔧 Ticket: www.carasent.de und https://x.de/a.")
    assert linkify_text_widget(txt, ("#1d4ed8", "#8ab4ff"), opener=lambda _u: None) == ["https://www.carasent.de", "https://x.de/a"]

    # The emoji at the start must not shift the tagged ranges.
    r0, r1 = txt.tag_ranges("link-0"), txt.tag_ranges("link-1")
    assert txt.get(r0[0], r0[1]) == "www.carasent.de"
    assert txt.get(r1[0], r1[1]) == "https://x.de/a"
    assert txt.tag_cget("link", "underline") in ("1", 1, True)
    for tag in ("link-0", "link-1"):
        assert txt.tk.call(txt._w, "tag", "bind", tag, "<ButtonPress-1>")
        assert txt.tk.call(txt._w, "tag", "bind", tag, "<ButtonRelease-1>")
    assert txt.tk.call(txt._w, "tag", "bind", "link", "<Enter>")

    plain = _text_widget(root, "nur Text")
    assert linkify_text_widget(plain, "#1d4ed8") == []
    assert "link" not in plain.tag_names()


def test_link_click_opens_only_on_plain_click(root):
    opened = []
    txt = _text_widget(root, "https://x.de/a")
    linkify_text_widget(txt, "#1d4ed8", opener=opened.append)
    handler = txt.link_click_handler

    handler.press(_ev(10, 5))
    assert handler.release(_ev(60, 5), "https://x.de/a") is False  # drag
    txt.tag_add("sel", "1.0", "1.5")
    handler.press(_ev(10, 5))
    assert handler.release(_ev(10, 5), "https://x.de/a") is False  # selection
    txt.tag_remove("sel", "1.0", "end")
    assert handler.release(_ev(10, 5), "https://x.de/a") is False  # press started elsewhere
    assert opened == []

    handler.press(_ev(10, 5))
    assert handler.release(_ev(11, 6), "https://x.de/a") is True
    assert opened == ["https://x.de/a"]


def test_link_opener_failure_is_swallowed(root):
    def boom(_url):
        raise OSError("no browser")
    txt = _text_widget(root, "https://x.de")
    linkify_text_widget(txt, "#1d4ed8", opener=boom)
    txt.link_click_handler.press(_ev(1, 1))
    assert txt.link_click_handler.release(_ev(1, 1), "https://x.de") is False


# --- paging -----------------------------------------------------------------

def test_short_timeline_has_no_older_button(root):
    w = _widget(root)
    w.load_timeline(_many(TIMELINE_PAGE_SIZE))
    assert len(_cards(w)) == TIMELINE_PAGE_SIZE
    assert w._older_btn is None


def test_long_timeline_pages_in_older_entries(root):
    """Long timelines only build the newest page; each card costs ~20 Tk widgets."""
    n = TIMELINE_PAGE_SIZE * 2 + 3
    w = _widget(root)
    w.load_timeline(_many(n))
    assert len(_cards(w)) == TIMELINE_PAGE_SIZE
    assert _note_texts(w)[0] == f"Notiz {n - 1}"  # newest first
    assert f"({n - TIMELINE_PAGE_SIZE})" in w._older_btn.cget("text")
    assert w.scroll_frame.winfo_children()[-1] is w._older_btn

    w._older_btn.invoke()
    assert len(_cards(w)) == TIMELINE_PAGE_SIZE * 2
    assert "(3)" in w._older_btn.cget("text")
    w._older_btn.invoke()
    assert w._older_btn is None
    assert _note_texts(w) == [f"Notiz {i}" for i in reversed(range(n))]


def test_rerender_keeps_expanded_pages_but_other_case_starts_fresh(root):
    """A new note or an edit must not collapse what the user opened."""
    w = _widget(root)
    w.load_timeline(_many(TIMELINE_PAGE_SIZE * 2 + 3))
    w.show_older_entries()
    w.note_textbox.insert("1.0", "neu")
    w.on_add_note()
    assert len(_cards(w)) == TIMELINE_PAGE_SIZE * 2

    w.load_timeline(_many(TIMELINE_PAGE_SIZE * 3))
    assert len(_cards(w)) == TIMELINE_PAGE_SIZE


def test_notes_share_one_highlight_font(root):
    """No bold CTkFont per note: their finalisers ran on whatever thread the GC hit (flush deadlock)."""
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
        w.load_timeline(_many(5))
    finally:
        ui_utils.ctk.CTkFont = orig
    assert created == []


# --- resizable "new note" box -----------------------------------------------

def _drag(handle, dy: int):
    handle.on_press(SimpleNamespace(y_root=100))
    handle.on_drag(SimpleNamespace(y_root=100 + dy))
    handle.on_release(SimpleNamespace(y_root=100 + dy))


def _height(w) -> int:
    return int(w.note_textbox.cget("height"))


@pytest.mark.parametrize(("stored", "expected"), [(None, TEXTBOX_HEIGHT_SM), (180, 180), (99999, TIMELINE_NOTE_MAX_HEIGHT)])
def test_stored_note_height_is_applied_and_clamped(root, stored, expected):
    p = UserProfile()
    if stored is not None:
        p.ui_settings.custom_textbox_heights[TIMELINE_NOTE_HEIGHT_KEY] = stored
    assert _height(_widget(root, profile=p)) == expected


def test_drag_saves_height_to_profile_within_bounds(root):
    p = UserProfile()
    form_default = p.ui_settings.textbox_height
    storage = MagicMock()
    w = _widget(root, profile=p, storage_service=storage)

    _drag(w.note_resize_handle, 100)
    assert _height(w) == TEXTBOX_HEIGHT_SM + 100
    assert p.ui_settings.custom_textbox_heights[TIMELINE_NOTE_HEIGHT_KEY] == TEXTBOX_HEIGHT_SM + 100
    assert p.ui_settings.textbox_height == form_default, "form textbox default stays untouched"
    storage.save_profile.assert_called_once_with(p)
    assert UISettings.from_dict(p.ui_settings.to_dict()).custom_textbox_heights[TIMELINE_NOTE_HEIGHT_KEY] == TEXTBOX_HEIGHT_SM + 100

    _drag(w.note_resize_handle, -500)
    assert p.ui_settings.custom_textbox_heights[TIMELINE_NOTE_HEIGHT_KEY] == TIMELINE_NOTE_MIN_HEIGHT

    # Resetting the column widths also resets the note height.
    p.ui_settings.reset_column_widths()
    w.apply_stored_note_height(p)
    assert _height(w) == TEXTBOX_HEIGHT_SM


def test_drag_is_scaling_independent(root, monkeypatch):
    """At 150 % font scaling a click without movement must not change the height."""
    p = UserProfile()
    w = _widget(root, profile=p, storage_service=MagicMock())
    monkeypatch.setattr(ctk.ScalingTracker, "get_widget_scaling", classmethod(lambda cls, _w: 1.5))
    _drag(w.note_resize_handle, 0)
    assert p.ui_settings.custom_textbox_heights[TIMELINE_NOTE_HEIGHT_KEY] == TEXTBOX_HEIGHT_SM
    _drag(w.note_resize_handle, 150)  # 150 real pixels = 100 unscaled
    assert p.ui_settings.custom_textbox_heights[TIMELINE_NOTE_HEIGHT_KEY] == TEXTBOX_HEIGHT_SM + 100


def test_resize_works_without_profile(root):
    w = _widget(root)
    _drag(w.note_resize_handle, 40)
    assert _height(w) == TEXTBOX_HEIGHT_SM + 40


def test_note_text_follows_theme_switch(root):
    """tk.Text is not managed by CTk: after Dark -> Light the note must not keep
    its dark background / light text (dark grey box on a light card)."""
    from constants import COLOR_TEXT_BODY, COLOR_TIMELINE_LINK
    from utils.ui_utils import create_highlighted_label

    def rgb(color):
        return root.winfo_rgb(color)

    previous = ctk.get_appearance_mode()
    try:
        ctk.set_appearance_mode("Dark")
        txt = create_highlighted_label(
            root, text="Notiz mit https://x.de", query="", font=("Arial", 12),
            text_color=COLOR_TEXT_BODY, bg_color=COLOR_CARD_BG,
        )
        linkify_text_widget(txt, COLOR_TIMELINE_LINK, opener=lambda _u: None)
        assert rgb(txt.cget("bg")) == rgb(COLOR_CARD_BG[1])

        ctk.set_appearance_mode("Light")
        assert rgb(txt.cget("bg")) == rgb(COLOR_CARD_BG[0])
        assert rgb(txt.tag_cget("normal", "foreground")) == rgb(COLOR_TEXT_BODY[0])
        assert rgb(txt.tag_cget("link", "foreground")) == rgb(COLOR_TIMELINE_LINK[0])

        # A destroyed note must drop out of the tracker instead of erroring.
        txt.destroy()
        ctk.set_appearance_mode("Dark")
    finally:
        ctk.set_appearance_mode(previous)


# --- folded time row ---------------------------------------------------------

def test_time_row_is_folded_away_until_toggled(root):
    w = _widget(root)
    assert not w.time_row.winfo_manager()
    assert w.time_toggle_btn.cget("text").endswith("▸")

    w.toggle_time_row()
    assert w.time_row.winfo_manager() == "pack"
    assert w.time_toggle_btn.cget("text").endswith("▾")

    w.time_picker.set_date("05.09.2026 11:30")
    w.toggle_time_row()
    assert not w.time_row.winfo_manager()
    assert w.time_picker.get() == ""


def test_adding_a_back_dated_note_folds_the_time_row_again(root):
    received = []
    w = _widget(root, received)
    w.load_timeline([])
    w.toggle_time_row(expanded=True)
    w.note_textbox.insert("1.0", "nachgetragen")
    w.time_picker.set_date("05.09.2026 11:30")
    w.on_add_note()

    assert received[-1][-1].timestamp == "2026-09-05T11:30:00"
    assert not w.time_row.winfo_manager()
