"""Follow-up dialog and flyout (prefill, presets, time stacking, apply), flexible follow-up input, cockpit column resizing, deferred language switch."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import customtkinter as ctk
import pytest

from enums import BoardColumn
from models.case import Case, CaseCustomer, Classification, WorkflowStatus
from services.i18n_service import tr
from utils.datetime_utils import (
    format_german_date,
    format_german_datetime,
    get_local_now,
    parse_flexible_followup_input,
    parse_followup_datetime,
)


def _case(followup_at: str = "", followup_note: str = "") -> Case:
    return Case(
        case_id="T-FU-01",
        customer=CaseCustomer(customer_id="K-1", practice_name="Praxis Followup"),
        classification=Classification(title="Followup Test"),
        workflow_status=WorkflowStatus(board_column=BoardColumn.NEW, followup_at=followup_at, followup_note=followup_note),
    )


def _dialog(root, case: Case, on_set=lambda iso, note: None):
    from ui.dialogs.followup_dialog import FollowupDialog

    dialog = FollowupDialog(root, case=case, on_followup_set=on_set)
    dialog.update_idletasks()
    return dialog


def _flyout(root, due_cases, on_refresh=lambda: None):
    from ui.dialogs.followup_flyout_dialog import FollowupFlyoutDialog

    dialog = FollowupFlyoutDialog(root, due_cases=due_cases, on_case_selected=lambda c: None, on_refresh=on_refresh)
    dialog.update_idletasks()
    return dialog


def _picker(root):
    from ui.widgets.date_picker import DatePickerWidget

    return DatePickerWidget(root, include_time=True)


def _shown(picker) -> datetime | None:
    return parse_followup_datetime(picker.get())


def _buttons_with_text(widget, text: str) -> list:
    found = []
    for child in widget.winfo_children():
        if isinstance(child, ctk.CTkButton) and child.cget("text") == text:
            found.append(child)
        found.extend(_buttons_with_text(child, text))
    return found


# ---------------------------------------------------------------------------
# FollowupDialog: prefill, save/clear, presets
# ---------------------------------------------------------------------------


def test_dialog_prefill_and_remove_button(root):
    future_iso = (get_local_now() + timedelta(days=5)).strftime("%Y-%m-%dT14:00:00")
    clear_text = tr("ui_buttons.clear", "❌ Entfernen")

    existing = _dialog(root, _case(followup_at=future_iso, followup_note="Beim Entwickler nachfragen"))
    assert existing.date_picker.get() == format_german_datetime(future_iso)
    assert existing.note_entry.get() == "Beim Entwickler nachfragen"
    assert len(_buttons_with_text(existing, clear_text)) == 1

    fresh = _dialog(root, _case())
    assert fresh.date_picker.get() == f"{format_german_date(get_local_now() + timedelta(days=2))} 09:00"
    assert _buttons_with_text(fresh, clear_text) == []


def test_dialog_moves_past_followup_to_now(root):
    """A past reminder is prefilled with now, and a typed past date is saved as now."""
    before = get_local_now().replace(second=0, microsecond=0)
    received = []
    dialog = _dialog(root, _case(followup_at="2026-08-05T14:00:00"), on_set=lambda iso, note: received.append(iso))

    shown = _shown(dialog.date_picker)
    assert shown is not None and timedelta(0) <= shown - before < timedelta(minutes=2)

    dialog.date_picker.entry.delete(0, "end")
    dialog.date_picker.entry.insert(0, "01.01.2020 08:00")
    dialog.on_save()
    assert parse_followup_datetime(received[0]) >= before


def test_dialog_save_and_clear_callbacks(root):
    received = []
    dialog = _dialog(root, _case(followup_at="2026-08-05T14:00:00", followup_note="Alt"),
                     on_set=lambda iso, note: received.append((iso, note)))

    dialog.date_picker.set_date("")
    dialog.on_save()
    assert received == []  # empty field: nothing saved

    future_str = (get_local_now() + timedelta(days=30)).strftime("%d.%m.%Y 10:15")
    dialog.date_picker.set_date(future_str)
    dialog.note_entry.delete(0, "end")
    dialog.note_entry.insert(0, "Rückruf vereinbart")
    dialog.on_save()
    assert parse_followup_datetime(received[0][0]) == parse_followup_datetime(future_str)
    assert received[0][1] == "Rückruf vereinbart"

    _dialog(root, _case(followup_at="2026-08-05T14:00:00"), on_set=lambda iso, note: received.append((iso, note))).on_clear()
    assert received[-1] == ("", "")


@pytest.fixture
def fixed_morning(monkeypatch):
    morning = get_local_now().replace(hour=8, minute=0, second=0, microsecond=0)
    for mod in ("ui.dialogs.followup_dialog", "ui.dialogs.followup_flyout_dialog", "utils.datetime_utils"):
        monkeypatch.setattr(f"{mod}.get_local_now", lambda: morning)
    return morning


@pytest.mark.parametrize(
    "dialog_call, flyout_call, days, hm",
    [
        (lambda d: d.set_preset_today_1630(), lambda f, p: f.set_field_today_1630(p), 0, (16, 30)),
        (lambda d: d.set_preset_today_before_lunch(), None, 0, (11, 30)),
        (lambda d: d.set_preset_today_after_lunch(), None, 0, (13, 30)),
        (lambda d: d.set_preset_tomorrow_8am(), lambda f, p: f.set_field_tomorrow_8am(p), 1, (8, 0)),
        (lambda d: d.set_preset_days(1), lambda f, p: f.set_field_days(p, 1), 1, (9, 0)),
        (lambda d: d.set_preset_days(2), None, 2, (9, 0)),
        (lambda d: d.set_preset_days(3), None, 3, (9, 0)),
        (lambda d: d.set_preset_days(7), lambda f, p: f.set_field_days(p, 7), 7, (9, 0)),
    ],
)
def test_presets_in_dialog_and_flyout(root, fixed_morning, dialog_call, flyout_call, days, hm):
    expected_date = (fixed_morning + timedelta(days=days)).date()
    dialog = _dialog(root, _case())
    dialog_call(dialog)
    result = _shown(dialog.date_picker)
    assert (result.date(), (result.hour, result.minute)) == (expected_date, hm)

    if flyout_call:
        flyout, picker = _flyout(root, [_case("2026-08-01T10:00:00")]), _picker(root)
        flyout_call(flyout, picker)
        result = _shown(picker)
        assert (result.date(), (result.hour, result.minute)) == (expected_date, hm)


# ---------------------------------------------------------------------------
# "+1/+2 Std." stacking (FollowupDialog.set_preset_hours, FollowupFlyoutDialog.bump_hours)
# ---------------------------------------------------------------------------


@pytest.fixture(params=["dialog", "flyout"])
def bumper(request, root):
    """Returns (picker, bump(hours)) for the dialog's preset or the flyout's bump."""
    if request.param == "dialog":
        dialog = _dialog(root, _case())
        return dialog.date_picker, dialog.set_preset_hours
    flyout, picker = _flyout(root, [_case("2026-08-01T10:00:00")]), _picker(root)
    return picker, lambda h: flyout.bump_hours(picker, h)


def test_hour_presets_stack_on_the_field_value(bumper):
    """Regression: repeated "+1 Std." clicks reset to now+1h instead of stacking on the shown value."""
    picker, bump = bumper
    base = get_local_now().replace(second=0, microsecond=0) + timedelta(days=10)
    picker.set_date(format_german_datetime(base))
    bump(1)
    assert _shown(picker) == base + timedelta(hours=1)
    bump(1)
    assert _shown(picker) == base + timedelta(hours=2)


@pytest.mark.parametrize("content", ["", "kann nicht geparst werden"])
def test_hour_presets_fall_back_to_now(bumper, content):
    picker, bump = bumper
    picker.set_date(content)
    before = get_local_now()
    bump(2)
    assert timedelta(minutes=115) <= _shown(picker) - before <= timedelta(minutes=125)


# ---------------------------------------------------------------------------
# FollowupFlyoutDialog: apply / title
# ---------------------------------------------------------------------------


def test_flyout_apply_new_time(root):
    case = _case("2026-08-01T10:00:00")
    due = [case]
    refreshed = []
    flyout = _flyout(root, due, on_refresh=lambda: refreshed.append(True))
    picker = _picker(root)

    flyout.apply_new_time(case, picker)  # empty field: nothing changes
    assert case.workflow_status.followup_at == "2026-08-01T10:00:00"
    assert case in due

    new_dt = get_local_now().replace(second=0, microsecond=0) + timedelta(days=3)
    picker.set_date(format_german_datetime(new_dt))
    flyout.apply_new_time(case, picker)
    assert parse_followup_datetime(case.workflow_status.followup_at) == new_dt
    assert case not in due
    assert refreshed


def test_flyout_title_truncated_to_two_lines():
    from ui.dialogs.followup_flyout_dialog import FollowupFlyoutDialog

    assert FollowupFlyoutDialog._truncate_title_to_two_lines("Kurzer Betreff", line_length=50) == "Kurzer Betreff"
    result = FollowupFlyoutDialog._truncate_title_to_two_lines("Sehr langer Titel eines Supportfalls " * 6, line_length=45)
    assert len(result.split("\n")) <= 2
    assert result.endswith("...")


# ---------------------------------------------------------------------------
# Flexible follow-up input parsing
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("text", ["", "   ", "invalid", "99:99"])
def test_flexible_followup_input_rejects_garbage(text):
    assert parse_flexible_followup_input(text) is None


@pytest.mark.parametrize(
    "text, ymd, hm",
    [
        ("14:30", None, (14, 30)),          # time only -> today
        ("15.11.2026", (2026, 11, 15), None),  # date only -> current time
        ("2026-11-15", (2026, 11, 15), None),
        ("15.11.2026 10:45", (2026, 11, 15), (10, 45)),
        ("2026-11-15 08:30", (2026, 11, 15), (8, 30)),
    ],
)
def test_flexible_followup_input(text, ymd, hm):
    now = datetime.now()
    res = parse_flexible_followup_input(text)
    assert (res.year, res.month, res.day) == (ymd or (now.year, now.month, now.day))
    assert (res.hour, res.minute) == (hm or (now.hour, now.minute))


# ---------------------------------------------------------------------------
# Cockpit column resizing
# ---------------------------------------------------------------------------


@pytest.fixture
def cockpit_window(root, config, storage):
    from services.attachment_service import AttachmentService
    from services.scoring_service import ScoringService
    from services.wiki_sync_service import WikiSyncService
    from ui.views.cockpit_view import CockpitView

    root.geometry("1000x700")
    view = CockpitView(
        root,
        author_name="Tester",
        scoring_service=ScoringService(),
        attachment_service=AttachmentService(config),
        wiki_service=WikiSyncService(config),
        app_config=config,
        profile=storage.load_profile(),
        storage_service=storage,
    )
    view.pack(fill="both", expand=True)
    root.update()
    view.restore_sash_positions()
    root.update()
    yield root, view
    pending = getattr(view, "_sash_restore_after_id", None)
    if pending:
        try:
            view.after_cancel(pending)
        except Exception:
            pass


@pytest.fixture
def fake_paned(cockpit_window):
    """Swaps the PanedWindow for a mock: the headless test window has width 1, where restore bails out early."""
    _, view = cockpit_window
    real = view.paned
    fake = MagicMock()
    fake.winfo_exists.return_value = True
    fake.winfo_width.return_value = 1600
    fake.cget.side_effect = lambda option: {"sashwidth": 6, "sashpad": 1}[option]
    view.paned = fake
    yield view, fake
    pending = getattr(view, "_sash_restore_after_id", None)
    if pending:
        try:
            view.after_cancel(pending)
        except Exception:
            pass
        view._sash_restore_after_id = None
    view._sash_user_dragged = False
    view.paned = real


def _configure(view, fake, width: int):
    fake.winfo_width.return_value = width
    event = MagicMock()
    event.widget = fake
    event.width = width
    view._on_paned_configure(event)


def test_only_the_middle_column_is_stretchable(cockpit_window):
    """Regression: Tk's default stretch="last" gave all extra window width to the right column."""
    _, view = cockpit_window
    for attr, expected in {"left_frame": "never", "center_frame": "always", "right_tabview": "never"}.items():
        assert view.paned.paneconfigure(getattr(view, attr))["stretch"][-1] == expected, attr


def test_restore_pins_side_column_widths(fake_paned):
    """Regression: without -width, a tab switch in the right tabview made Tk recompute pane sizes
    and the restored column widths were lost after each restart."""
    view, fake = fake_paned
    view.profile.ui_settings.column_widths["cockpit_left"] = 430
    view.profile.ui_settings.column_widths["cockpit_right"] = 250

    view.restore_sash_positions()

    pinned = {c.args[0]: c.kwargs["width"] for c in fake.paneconfigure.call_args_list}
    assert pinned.get(view.left_frame) == 430
    assert pinned.get(view.right_tabview) == 250
    assert view.center_frame not in pinned
    # Right sash sits sashwidth + 2*sashpad = 8px before its pane (1600 - 250 - 8), else it drifts 8px per restart.
    assert fake.sash_place.call_args_list[0].args == (0, 430, 0)
    assert fake.sash_place.call_args_list[1].args == (1, 1342, 0)


def test_resizing_neither_moves_sashes_nor_overwrites_saved_widths(fake_paned):
    """Regression: the configure handler re-placed sashes and wrote recomputed widths into the profile,
    so user-dragged widths were lost on restart."""
    view, fake = fake_paned
    view.profile.ui_settings.column_widths["cockpit_left"] = 430
    view.profile.ui_settings.column_widths["cockpit_right"] = 250
    fake.sash_coord.side_effect = lambda i: [(430, 0), (1150, 0)][i]
    view._last_paned_width = 1400

    for width in (1000, 1600, 1200):
        _configure(view, fake, width)

    assert fake.sash_place.call_count == 0
    assert view._last_paned_width == 1200
    assert view.profile.ui_settings.column_widths["cockpit_left"] == 430
    assert view.profile.ui_settings.column_widths["cockpit_right"] == 250


def test_resizing_stops_scheduling_restore_once_user_dragged(fake_paned):
    view, fake = fake_paned
    view._sash_user_dragged = True
    view._sash_restore_after_id = None
    _configure(view, fake, 1700)
    assert fake.sash_place.call_count == 0
    assert view._sash_restore_after_id is None


def test_extra_window_width_goes_to_middle_column_and_its_scrollbar(cockpit_window):
    app, view = cockpit_window
    if view.paned.winfo_width() <= 100:
        pytest.skip("Window is not mapped in this environment - widths cannot be measured")

    def widths():
        return view.left_frame.winfo_width(), view.center_frame.winfo_width(), view.right_tabview.winfo_width()

    bar = view.form_widget.scroll_frame._scrollbar
    bar.grid(row=0, column=1, rowspan=2, sticky="ns")
    left0, mid0, right0 = widths()
    app.geometry("1600x700")
    app.update()
    left, mid, right = widths()

    assert mid > mid0
    assert abs(left - left0) <= 2 and abs(right - right0) <= 2
    gap = view.center_frame.winfo_rootx() + view.center_frame.winfo_width() - bar.winfo_rootx()
    assert 0 <= gap <= 40


# ---------------------------------------------------------------------------
# Profile settings: language change deferred until save
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("picks, expected", [(["English"], "en"), (["Svenska", "Deutsch"], "de")])
def test_language_selection_applies_only_on_save(root, storage, picks, expected):
    """Regression: picking a language in the dropdown switched the app language before saving."""
    from services.i18n_service import get_i18n
    from ui.dialogs.profile_settings_dialog import ProfileSettingsDialog

    profile = storage.load_profile()
    profile.ui_settings.language = "de"
    dialog = ProfileSettingsDialog(root, profile=profile, storage_service=storage, on_profile_updated=lambda: None)

    for pick in picks:
        dialog.language_combo.set(pick)
        dialog.update_idletasks()
    assert get_i18n().current_language == "de"
    assert profile.ui_settings.language == "de"

    dialog.save_settings()
    assert get_i18n().current_language == expected
    assert profile.ui_settings.language == expected
