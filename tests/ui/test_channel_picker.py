"""ChannelPicker: medium chips + direction row in place of the 13-item channel dropdown."""

import pytest

from constants import CHANNEL_PICKER_GROUPS, DISPLAY_CHANNEL_NAMES
from enums import get_channel_display
from models.case import TimelineEntry
from services.i18n_service import get_i18n
from ui.widgets.channel_picker import ChannelPicker, ChipRow, group_of


def _visible(widget) -> bool:
    # Windows stay withdrawn in the test session; the geometry manager is what tells.
    return bool(widget.winfo_manager())


def _click(picker: ChannelPicker, row: str, key: str) -> None:
    getattr(picker, row).buttons()[key].invoke()


# --- data ---------------------------------------------------------------------

def test_every_picker_code_has_a_display_name_and_every_display_name_a_group():
    """No code can be stored that the cards cannot name, and none is unreachable from the picker."""
    picker_codes = {code for _, codes in CHANNEL_PICKER_GROUPS for code in codes}
    assert picker_codes == set(DISPLAY_CHANNEL_NAMES)
    for code in ("SLACK_IN", "SLACK_OUT", "WHATSAPP_IN", "WHATSAPP_OUT"):
        assert "Slack" in get_channel_display(code) or "WhatsApp" in get_channel_display(code)


@pytest.mark.parametrize("lang", ["de", "en", "sv"])
def test_new_channels_are_translated(lang):
    get_i18n().current_language = lang
    names = {get_channel_display(c) for c in ("SLACK_IN", "SLACK_OUT", "WHATSAPP_IN", "WHATSAPP_OUT")}
    assert len(names) == 4, "inbound and outbound must read differently"
    assert all(n not in ("SLACK_IN", "SLACK_OUT", "WHATSAPP_IN", "WHATSAPP_OUT") for n in names)


# --- selection ----------------------------------------------------------------

def test_default_is_inbound_phone_with_direction_row(root):
    p = ChannelPicker(root)
    assert p.get() == "PHONE_INBOUND"
    assert p.group_row.selected() == "phone"
    assert p.variant_row.selected() == "PHONE_INBOUND"
    assert _visible(p.variant_row) and _visible(p.variant_lbl)


def test_picking_medium_then_direction_gives_the_stored_code(root):
    seen = []
    p = ChannelPicker(root, command=seen.append)
    _click(p, "group_row", "whatsapp")
    assert p.get() == "WHATSAPP_IN"
    _click(p, "variant_row", "WHATSAPP_OUT")
    assert p.get() == "WHATSAPP_OUT"
    assert seen == ["WHATSAPP_IN", "WHATSAPP_OUT"]


def test_switching_medium_keeps_the_direction(root):
    """Correcting the medium (it was Slack, not phone) must not flip outbound back to inbound."""
    p = ChannelPicker(root, value="PHONE_OUTBOUND")
    _click(p, "group_row", "slack")
    assert p.get() == "SLACK_OUT"


def test_gitlab_offers_ticket_events_instead_of_a_direction(root):
    p = ChannelPicker(root, value="PHONE_OUTBOUND")
    _click(p, "group_row", "gitlab")
    assert p.get() == "GITLAB_TICKET_CREATED"
    assert set(p.variant_row.buttons()) == {"GITLAB_TICKET_CREATED", "GITLAB_TICKET_UPDATED", "GITLAB_TICKET_CLOSED"}
    assert p.variant_lbl.cget("text") == "Ticket:"
    _click(p, "variant_row", "GITLAB_TICKET_CLOSED")
    assert p.get() == "GITLAB_TICKET_CLOSED"


@pytest.mark.parametrize("group, code", [("note", "INTERNAL_NOTE"), ("other", "OTHER")])
def test_single_code_media_hide_the_second_row(root, group, code):
    p = ChannelPicker(root)
    _click(p, "group_row", group)
    assert p.get() == code
    assert not _visible(p.variant_row) and not _visible(p.variant_lbl)


def test_clicking_the_selected_chip_again_changes_nothing(root):
    seen = []
    p = ChannelPicker(root, value="EMAIL_OUT", command=seen.append)
    _click(p, "group_row", "email")
    _click(p, "variant_row", "EMAIL_OUT")
    assert p.get() == "EMAIL_OUT" and seen == []


# --- old and unknown codes ------------------------------------------------------

@pytest.mark.parametrize("legacy, group", [("EMAIL", "email"), ("DEV_TICKET", "gitlab"), ("SLACK_CHAT", "slack")])
def test_old_code_shows_its_medium_and_stays_untouched_until_a_direction_is_picked(root, legacy, group):
    p = ChannelPicker(root, value=legacy)
    assert p.get() == legacy, "editing an old entry must not rewrite its channel by itself"
    assert p.group_row.selected() == group
    assert p.variant_row.selected() is None
    assert _visible(p.legacy_lbl)

    first_variant = next(iter(p.variant_row.buttons()))
    _click(p, "variant_row", first_variant)
    assert p.get() == first_variant
    assert not _visible(p.legacy_lbl)


def test_unknown_code_round_trips_with_nothing_selected(root):
    p = ChannelPicker(root, value="FAX_FROM_1998")
    assert p.get() == "FAX_FROM_1998"
    assert p.group_row.selected() is None
    assert group_of("FAX_FROM_1998") is None


# --- layout ---------------------------------------------------------------------

def test_chips_wrap_onto_more_lines_when_narrow(root):
    row = ChipRow(root, on_select=lambda _k: None)
    row.set_items([(f"k{i}", f"Kanal {i}") for i in range(7)])
    root.update_idletasks()  # a fresh button reports its real size only after the first idle pass
    widths = [b.winfo_reqwidth() for b in row.buttons().values()]
    assert min(widths) > 10

    assert row._compute_breaks(sum(widths) * 2) == ()
    two_lines = row._compute_breaks(sum(widths) // 2 + max(widths))
    assert len(two_lines) == 1
    assert len(row._compute_breaks(max(widths))) == 6, "one chip per line when only one fits"
    assert row._compute_breaks(0) == (), "unknown width keeps one line until laid out"


def test_reflow_repacks_only_when_the_breaks_change(root):
    row = ChipRow(root, on_select=lambda _k: None)
    row.set_items([("a", "Alpha"), ("b", "Beta"), ("c", "Gamma")])
    root.update_idletasks()
    row._available_width = lambda: 10_000
    row._breaks = None
    row._reflow()
    assert row.line_count() == 1
    lines_before = list(row._lines)
    row._reflow()
    assert row._lines == lines_before

    row._available_width = lambda: row.buttons()["a"].winfo_reqwidth()
    row._reflow()
    assert row.line_count() == 3


def test_label_column_does_not_change_width_with_the_second_row(root):
    """Otherwise the chips shift sideways (and can re-wrap) when switching to a medium without directions."""
    p = ChannelPicker(root)
    p.pack()
    root.update_idletasks()
    with_row = p.grid_columnconfigure(0)["minsize"]
    _click(p, "group_row", "note")
    root.update_idletasks()
    assert p.grid_columnconfigure(0)["minsize"] == with_row > 0


def test_language_switch_relabels_chips_and_keeps_the_selection(root):
    p = ChannelPicker(root, value="SLACK_OUT")
    get_i18n().current_language = "en"
    p.refresh_labels()
    assert p.get() == "SLACK_OUT"
    assert p.group_row.buttons()["note"].cget("text") == "Note"
    assert p.variant_row.buttons()["SLACK_OUT"].cget("text") == "Outbound"
    assert p.variant_lbl.cget("text") == "Direction:"


# --- the three places it replaced the dropdown ------------------------------------

def test_timeline_note_is_saved_with_the_picked_channel(root):
    from ui.widgets.timeline_widget import TimelineWidget

    received = []
    w = TimelineWidget(root, author_name="Daniel", on_timeline_updated=received.append)
    w.load_timeline([])
    _click(w.channel_picker, "group_row", "slack")
    _click(w.channel_picker, "variant_row", "SLACK_OUT")
    w.note_textbox.insert("1.0", "Rückfrage per Slack")
    w.on_add_note()
    assert received[-1][-1].channel == "SLACK_OUT"


def test_edit_dialog_keeps_an_old_channel_unless_changed(root):
    from ui.dialogs.timeline_entry_dialog import TimelineEntryDialog

    saved = []
    entry = TimelineEntry(timestamp="2026-09-01T10:00:00", author="Daniel", channel="EMAIL", note="alt")
    d = TimelineEntryDialog(root, entry, on_save=lambda dt, ch, note: saved.append(ch), on_delete=lambda: None)
    try:
        assert d.channel_picker.get() == "EMAIL"
        d.on_click_save()
        assert saved == ["EMAIL"]
    finally:
        if d.winfo_exists():
            d.destroy()


def test_new_case_initial_note_gets_the_picked_channel(root):
    from models.customer import Contact, Customer
    from ui.dialogs.new_case_dialog import NewCaseDialog

    created = []
    d = NewCaseDialog(
        root,
        customers=[Customer(customer_id="K-1", practice_name="Praxis Test", contacts=[Contact(name="Frau Test")])],
        schemas=[],
        created_by="Daniel",
        on_case_created=created.append,
    )
    try:
        d.update_idletasks()
        d.customer_combo.set("Praxis Test (K-1)")
        d.title_entry.insert(0, "Rückruf erbeten")
        _click(d.channel_picker, "group_row", "whatsapp")
        d.note_textbox.insert("1.0", "Nachricht per WhatsApp")
        d.on_save()
        assert created[0].timeline[0].channel == "WHATSAPP_IN"
    finally:
        if d.winfo_exists():
            d.destroy()


def test_chip_size_change_reflows_the_row(root):
    """Font zoom grows the chips while the row keeps its width - the row has to wrap again."""
    row = ChipRow(root, on_select=lambda _k: None)
    row.pack()
    row.set_items([("a", "Alpha"), ("b", "Beta"), ("c", "Gamma")])
    root.update_idletasks()
    one_line = sum(b.winfo_reqwidth() for b in row.buttons().values()) + 20
    row._available_width = lambda: one_line
    row._breaks = None
    row._reflow()
    assert row.line_count() == 1

    for btn in row.buttons().values():
        btn.configure(text=btn.cget("text") * 3)
    root.update_idletasks()
    # Every chip carries the handler; Tk calls it when the chip changes size.
    # (Windows stay withdrawn in the test session, where Tk delivers no
    # <Configure> at all - so the handler is invoked here directly.)
    import tkinter as tk
    assert all("<Configure>" in tk.Misc.bind(b) for b in row.buttons().values())
    row._schedule_reflow()
    row._schedule_reflow()  # several chips at once -> still one reflow
    root.update()
    assert row.line_count() > 1
