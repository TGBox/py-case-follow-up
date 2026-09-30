"""Tests for back-dated / editable timeline entries and the date picker time bounds.

- Wiedervorlage pickers (time_bound="future") move a past value to now.
- Timeline pickers (time_bound="past") move a future value to now.
- Timeline entries can be created with an earlier time, edited (with an
  "edited" marker) and deleted.
"""

from datetime import datetime, timedelta

import customtkinter as ctk
import pytest

from models.case import Case, CaseCustomer, Classification, TimelineEntry
from services.i18n_service import get_i18n
from ui.widgets.date_picker import DatePickerWidget
from ui.widgets.timeline_widget import TimelineWidget
from utils.datetime_utils import (
    clamp_datetime_to_now,
    format_german_datetime,
    get_local_now,
    parse_followup_datetime,
    parse_iso,
)


@pytest.fixture(autouse=True)
def reset_locale():
    get_i18n().current_language = "de"
    yield
    get_i18n().current_language = "de"


@pytest.fixture
def root():
    r = ctk.CTk()
    r.withdraw()
    yield r
    try:
        r.destroy()
    except Exception:
        pass


# --- clamp_datetime_to_now -------------------------------------------------

def test_clamp_future_moves_past_to_now():
    now = datetime(2026, 9, 30, 14, 12, 45).astimezone()
    past = now - timedelta(days=3)
    assert clamp_datetime_to_now(past, "future", now=now) == now.replace(second=0, microsecond=0)


def test_clamp_future_keeps_current_minute_and_future():
    now = datetime(2026, 9, 30, 14, 12, 45).astimezone()
    same_minute = now.replace(second=0)
    later = now + timedelta(hours=2)
    assert clamp_datetime_to_now(same_minute, "future", now=now) == same_minute
    assert clamp_datetime_to_now(later, "future", now=now) == later


def test_clamp_past_moves_future_to_now_and_keeps_past():
    now = datetime(2026, 9, 30, 14, 12, 45).astimezone()
    assert clamp_datetime_to_now(now + timedelta(days=1), "past", now=now) == now
    earlier = now - timedelta(days=1)
    assert clamp_datetime_to_now(earlier, "past", now=now) == earlier


# --- DatePickerWidget bounds ----------------------------------------------

def test_future_picker_moves_past_initial_value_to_now(root):
    before = get_local_now().replace(second=0, microsecond=0)
    picker = DatePickerWidget(root, include_time=True, initial_value="2020-01-01T08:00:00", time_bound="future")
    shown = parse_followup_datetime(picker.get())
    assert shown is not None and shown >= before


def test_future_picker_moves_past_set_date_to_now(root):
    picker = DatePickerWidget(root, include_time=True, time_bound="future")
    before = get_local_now().replace(second=0, microsecond=0)
    picker.set_date("01.01.2020 16:30")
    assert parse_followup_datetime(picker.get()) >= before


def test_future_picker_keeps_future_value(root):
    picker = DatePickerWidget(root, include_time=True, time_bound="future")
    future = (get_local_now() + timedelta(days=3)).strftime("%d.%m.%Y 09:00")
    picker.set_date(future)
    assert picker.get() == future


def test_past_picker_moves_future_value_to_now(root):
    picker = DatePickerWidget(root, include_time=True, time_bound="past")
    picker.set_date((get_local_now() + timedelta(days=3)).strftime("%d.%m.%Y 09:00"))
    assert parse_followup_datetime(picker.get()) <= get_local_now()


def test_unbounded_picker_is_unchanged(root):
    picker = DatePickerWidget(root, include_time=True)
    picker.set_date("01.01.2020 16:30")
    assert picker.get() == "01.01.2020 16:30"


def test_flyout_bump_uses_now_instead_of_past_value(root):
    from ui.dialogs.followup_flyout_dialog import FollowupFlyoutDialog

    picker = DatePickerWidget(root, include_time=True, time_bound="future")
    picker.entry.insert(0, "01.01.2020 08:00")
    before = get_local_now().replace(second=0, microsecond=0)
    FollowupFlyoutDialog.bump_hours(None, picker, 1)  # type: ignore[arg-type]
    result = parse_followup_datetime(picker.get())
    assert result is not None and result >= before + timedelta(minutes=59)


# --- TimelineWidget ---------------------------------------------------------

def _widget(root, received):
    return TimelineWidget(root, author_name="Daniel", on_timeline_updated=lambda entries: received.append(list(entries)))


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

    notes = [e.note for e in received[-1]]
    assert notes == ["alt", "nachgetragen", "neu"]
    added = received[-1][1]
    assert added.timestamp == "2026-09-05T11:30:00"
    assert added.author == "Daniel"
    assert w.time_picker.get() == ""


def test_add_note_without_time_uses_now(root):
    received = []
    w = _widget(root, received)
    w.load_timeline([])
    before = get_local_now().replace(microsecond=0) - timedelta(seconds=1)
    w.note_textbox.insert("1.0", "jetzt")
    w.on_add_note()
    assert parse_iso(received[-1][-1].timestamp) >= before


def test_add_note_with_future_time_is_capped_at_now(root):
    received = []
    w = _widget(root, received)
    w.load_timeline([])
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
    w = TimelineWidget(root, author_name="Felipe", on_timeline_updated=lambda entries: received.append(list(entries)))
    first = TimelineEntry(timestamp="2026-09-01T10:00:00", author="Daniel", channel="EMAIL", note="eins")
    second = TimelineEntry(timestamp="2026-09-10T10:00:00", author="Daniel", note="zwei")
    w.load_timeline([first, second])

    new_dt = datetime(2026, 9, 12, 9, 15).astimezone()
    w.apply_entry_edit(first, new_dt, "PHONE_INBOUND", "eins korrigiert")

    entries = received[-1]
    assert [e.note for e in entries] == ["zwei", "eins korrigiert"]
    edited = entries[1]
    assert edited.timestamp == "2026-09-12T09:15:00"
    assert edited.channel == "PHONE_INBOUND"
    assert edited.author == "Daniel", "original author stays"
    assert edited.edited_by == "Felipe"
    assert edited.edited_at

    # The edited marker is rendered.
    def texts(parent):
        out = []
        for child in parent.winfo_children():
            if isinstance(child, ctk.CTkLabel):
                out.append(child.cget("text"))
            out.extend(texts(child))
        return out
    assert any("bearbeitet" in t and "Felipe" in t for t in texts(w.scroll_frame))


def test_edit_without_changes_does_not_mark(root):
    received = []
    w = _widget(root, received)
    entry = TimelineEntry(timestamp="2026-09-01T10:00:37", author="Daniel", channel="EMAIL", note="eins")
    w.load_timeline([entry])
    w.apply_entry_edit(entry, parse_iso("2026-09-01T10:00:00"), "EMAIL", "eins")
    assert received == []
    assert entry.edited_at == ""
    assert entry.timestamp == "2026-09-01T10:00:37", "seconds survive when the minute is unchanged"


def test_delete_entry(root):
    received = []
    w = _widget(root, received)
    a = TimelineEntry(timestamp="2026-09-01T10:00:00", author="A", note="a")
    b = TimelineEntry(timestamp="2026-09-02T10:00:00", author="A", note="b")
    w.load_timeline([a, b])
    w.delete_entry(a)
    assert [e.note for e in received[-1]] == ["b"]


def test_each_card_has_an_edit_button(root):
    w = _widget(root, [])
    w.load_timeline([
        TimelineEntry(timestamp="2026-09-01T10:00:00", author="A", note="a"),
        TimelineEntry(timestamp="2026-09-02T10:00:00", author="B", note="b"),
    ])

    def buttons(parent):
        out = []
        for child in parent.winfo_children():
            if isinstance(child, ctk.CTkButton):
                out.append(child)
            out.extend(buttons(child))
        return out
    assert len([b for b in buttons(w.scroll_frame) if b.cget("text") == "✏"]) == 2


# --- TimelineEntry model ----------------------------------------------------

def test_timeline_entry_edit_fields_roundtrip_and_stay_out_when_empty():
    plain = TimelineEntry(timestamp="2026-09-01T10:00:00", author="A", note="x")
    assert "edited_at" not in plain.to_dict()
    edited = TimelineEntry(timestamp="2026-09-01T10:00:00", author="A", note="x", edited_at="2026-09-30T12:00:00", edited_by="B")
    restored = TimelineEntry.from_dict(edited.to_dict())
    assert restored.edited_at == "2026-09-30T12:00:00"
    assert restored.edited_by == "B"


# --- Edit dialog ------------------------------------------------------------

def test_edit_dialog_save_and_delete(root, monkeypatch):
    from ui.dialogs import confirm_dialog
    from ui.dialogs.timeline_entry_dialog import TimelineEntryDialog

    entry = TimelineEntry(timestamp="2026-09-01T10:00:00", author="Daniel", channel="EMAIL", note="alt")
    saved = []
    deleted = []
    dlg = TimelineEntryDialog(root, entry, on_save=lambda dt, ch, note: saved.append((dt, ch, note)), on_delete=lambda: deleted.append(True))
    dlg.update_idletasks()
    assert dlg.date_picker.get() == format_german_datetime("2026-09-01T10:00:00")
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


def test_edit_dialog_rejects_empty_note(root):
    from ui.dialogs.timeline_entry_dialog import TimelineEntryDialog

    entry = TimelineEntry(timestamp="2026-09-01T10:00:00", author="Daniel", note="alt")
    saved = []
    dlg = TimelineEntryDialog(root, entry, on_save=lambda *a: saved.append(a))
    dlg.note_textbox.delete("1.0", "end")
    dlg.on_click_save()
    assert saved == []
    assert dlg.error_label.cget("text")
    dlg.destroy()


def test_table_view_timeline_changes_reach_the_case():
    """Regression: the table view used to drop notes added in its timeline tab."""
    from ui.views.table_view import TableView

    class Dummy:
        saved = 0

        def on_click_save(self):
            Dummy.saved += 1

    view = Dummy()
    view.selected_case = Case(case_id="T-1", customer=CaseCustomer(), classification=Classification())  # type: ignore[attr-defined]
    new_entries = [TimelineEntry(timestamp="2026-09-01T10:00:00", author="A", note="x")]
    TableView.on_timeline_updated(view, new_entries)  # type: ignore[arg-type]
    assert view.selected_case.timeline == new_entries  # type: ignore[attr-defined]
    assert Dummy.saved == 1
