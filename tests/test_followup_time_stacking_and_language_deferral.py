"""Regression tests for two behavior changes made in the 2026-09 session:

1. The "+1 Std." / "+2 Std." (and other) quick-preset buttons in the follow-up
   dialogs must stack their increment on top of whatever the date/time field
   currently shows, and only fall back to "now" when that field is empty or
   unparseable (FollowupDialog.set_preset_hours,
   FollowupFlyoutDialog.bump_hours/set_field_*/apply_new_time).

2. The language dropdown in the profile settings dialog must not switch the
   app's active language immediately on selection - only clicking
   "Einstellungen speichern" (ProfileSettingsDialog.save_settings) may apply it.

Neither behavior had any test coverage before this file was added (see the
test-coverage audit: test_dialogs_comprehensive.py etc. only exercise
rendering/lifecycle of these dialogs, not this specific logic; and no test in
the whole suite references the i18n_service module at all).
"""

from pathlib import Path
from datetime import timedelta
import customtkinter as ctk
import pytest

from config import AppConfig
from enums import BoardColumn
from models.case import Case, CaseCustomer, Classification, WorkflowStatus
from services.storage_service import StorageService
from utils.datetime_utils import get_local_now, format_german_datetime, parse_followup_datetime


@pytest.fixture
def app_and_storage(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)

    app = ctk.CTk()
    app.withdraw()

    yield app, storage, config

    try:
        app.destroy()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def reset_i18n_singleton():
    """Isolate the global I18nService singleton between tests so a language
    change made by one test can never leak into the next one."""
    import services.i18n_service as i18n_module

    previous = i18n_module._i18n_instance
    i18n_module._i18n_instance = None
    yield
    i18n_module._i18n_instance = previous


def _make_case(followup_at: str = "2026-08-01T10:00:00") -> Case:
    return Case(
        case_id="T-STACK-01",
        customer=CaseCustomer(customer_id="K-1", practice_name="Praxis Stack"),
        classification=Classification(title="Stacking Test"),
        workflow_status=WorkflowStatus(
            board_column=BoardColumn.NEW,
            followup_at=followup_at,
        ),
    )


# ---------------------------------------------------------------------------
# FollowupDialog.set_preset_hours
# ---------------------------------------------------------------------------


def test_followup_dialog_preset_hours_uses_now_when_field_empty(app_and_storage):
    app, storage, config = app_and_storage
    from ui.dialogs.followup_dialog import FollowupDialog

    case = _make_case(followup_at="")
    dialog = FollowupDialog(app, case=case, on_followup_set=lambda iso, note: None)
    dialog.update_idletasks()

    # The dialog pre-fills the field with a "+2 days" default when there's no
    # existing followup_at - clear it so we test the empty-field branch.
    dialog.date_picker.set_date("")

    before = get_local_now()
    dialog.set_preset_hours(1)
    result_dt = parse_followup_datetime(dialog.date_picker.get())

    assert result_dt is not None
    delta = result_dt - before
    assert timedelta(minutes=55) <= delta <= timedelta(minutes=65)

    dialog.destroy()


def test_followup_dialog_preset_hours_stacks_on_existing_value(app_and_storage):
    app, storage, config = app_and_storage
    from ui.dialogs.followup_dialog import FollowupDialog

    case = _make_case(followup_at="")
    dialog = FollowupDialog(app, case=case, on_followup_set=lambda iso, note: None)
    dialog.update_idletasks()

    # format_german_datetime() drops seconds by default, so truncate to the
    # minute before round-tripping through the field, or the comparison below
    # would fail on a seconds-precision mismatch.
    base_dt = get_local_now().replace(second=0, microsecond=0) + timedelta(days=10)
    dialog.date_picker.set_date(format_german_datetime(base_dt))

    dialog.set_preset_hours(1)
    after_first = parse_followup_datetime(dialog.date_picker.get())
    assert after_first == base_dt + timedelta(hours=1)

    # A second click must add another hour ON TOP of the first click's
    # result, not reset back to "now + 1h".
    dialog.set_preset_hours(1)
    after_second = parse_followup_datetime(dialog.date_picker.get())
    assert after_second == base_dt + timedelta(hours=2)

    dialog.destroy()


def test_followup_dialog_preset_hours_ignores_unparseable_field_content(app_and_storage):
    app, storage, config = app_and_storage
    from ui.dialogs.followup_dialog import FollowupDialog

    case = _make_case(followup_at="")
    dialog = FollowupDialog(app, case=case, on_followup_set=lambda iso, note: None)
    dialog.update_idletasks()

    dialog.date_picker.set_date("kann nicht geparst werden")

    before = get_local_now()
    dialog.set_preset_hours(2)
    result_dt = parse_followup_datetime(dialog.date_picker.get())

    assert result_dt is not None
    delta = result_dt - before
    assert timedelta(minutes=115) <= delta <= timedelta(minutes=125)

    dialog.destroy()


# ---------------------------------------------------------------------------
# FollowupFlyoutDialog: bump_hours / set_field_* / apply_new_time
# ---------------------------------------------------------------------------


def test_flyout_bump_hours_stacks_like_followup_dialog(app_and_storage):
    app, storage, config = app_and_storage
    from ui.dialogs.followup_flyout_dialog import FollowupFlyoutDialog
    from ui.widgets.date_picker import DatePickerWidget

    case = _make_case()
    dialog = FollowupFlyoutDialog(
        app, due_cases=[case], on_case_selected=lambda c: None, on_refresh=lambda: None
    )
    dialog.update_idletasks()

    picker = DatePickerWidget(app, include_time=True)
    base_dt = get_local_now().replace(second=0, microsecond=0) + timedelta(days=5)
    picker.set_date(format_german_datetime(base_dt))

    dialog.bump_hours(picker, 1)
    assert parse_followup_datetime(picker.get()) == base_dt + timedelta(hours=1)

    dialog.bump_hours(picker, 1)
    assert parse_followup_datetime(picker.get()) == base_dt + timedelta(hours=2)

    picker.destroy()
    dialog.destroy()


def test_flyout_bump_hours_uses_now_when_field_empty(app_and_storage):
    app, storage, config = app_and_storage
    from ui.dialogs.followup_flyout_dialog import FollowupFlyoutDialog
    from ui.widgets.date_picker import DatePickerWidget

    case = _make_case()
    dialog = FollowupFlyoutDialog(
        app, due_cases=[case], on_case_selected=lambda c: None, on_refresh=lambda: None
    )
    dialog.update_idletasks()

    picker = DatePickerWidget(app, include_time=True)  # starts empty

    before = get_local_now()
    dialog.bump_hours(picker, 2)
    result_dt = parse_followup_datetime(picker.get())

    assert result_dt is not None
    delta = result_dt - before
    assert timedelta(minutes=115) <= delta <= timedelta(minutes=125)

    picker.destroy()
    dialog.destroy()


def test_flyout_set_field_today_tomorrow_and_days(app_and_storage):
    app, storage, config = app_and_storage
    from ui.dialogs.followup_flyout_dialog import FollowupFlyoutDialog
    from ui.widgets.date_picker import DatePickerWidget

    case = _make_case()
    dialog = FollowupFlyoutDialog(
        app, due_cases=[case], on_case_selected=lambda c: None, on_refresh=lambda: None
    )
    dialog.update_idletasks()

    picker = DatePickerWidget(app, include_time=True)
    now = get_local_now()

    dialog.set_field_today_1630(picker)
    today_dt = parse_followup_datetime(picker.get())
    assert today_dt.date() == now.date()
    assert (today_dt.hour, today_dt.minute) == (16, 30)

    dialog.set_field_tomorrow_8am(picker)
    tmw_dt = parse_followup_datetime(picker.get())
    assert tmw_dt.date() == (now + timedelta(days=1)).date()
    assert (tmw_dt.hour, tmw_dt.minute) == (8, 0)

    dialog.set_field_days(picker, 7)
    week_dt = parse_followup_datetime(picker.get())
    assert week_dt.date() == (now + timedelta(days=7)).date()
    assert (week_dt.hour, week_dt.minute) == (9, 0)

    picker.destroy()
    dialog.destroy()


def test_flyout_apply_new_time_commits_case_and_removes_from_due_list(app_and_storage):
    app, storage, config = app_and_storage
    from ui.dialogs.followup_flyout_dialog import FollowupFlyoutDialog
    from ui.widgets.date_picker import DatePickerWidget

    case = _make_case()
    due_cases = [case]

    refreshed = False

    def on_refresh():
        nonlocal refreshed
        refreshed = True

    dialog = FollowupFlyoutDialog(
        app, due_cases=due_cases, on_case_selected=lambda c: None, on_refresh=on_refresh
    )
    dialog.update_idletasks()

    picker = DatePickerWidget(app, include_time=True)
    new_dt = get_local_now().replace(second=0, microsecond=0) + timedelta(days=3)
    picker.set_date(format_german_datetime(new_dt))

    dialog.apply_new_time(case, picker)

    assert parse_followup_datetime(case.workflow_status.followup_at) == new_dt
    assert case not in due_cases
    assert refreshed

    picker.destroy()
    # The dialog either auto-closes (due list now empty) or rebuilds its
    # widgets in response - either way a final destroy must not raise.
    try:
        dialog.destroy()
    except Exception:
        pass


def test_flyout_apply_new_time_does_nothing_when_field_empty(app_and_storage):
    app, storage, config = app_and_storage
    from ui.dialogs.followup_flyout_dialog import FollowupFlyoutDialog
    from ui.widgets.date_picker import DatePickerWidget

    case = _make_case()
    due_cases = [case]

    dialog = FollowupFlyoutDialog(
        app, due_cases=due_cases, on_case_selected=lambda c: None, on_refresh=lambda: None
    )
    dialog.update_idletasks()

    picker = DatePickerWidget(app, include_time=True)  # left empty

    dialog.apply_new_time(case, picker)

    # Nothing should have changed - the case stays due with its original value.
    assert case.workflow_status.followup_at == "2026-08-01T10:00:00"
    assert case in due_cases

    picker.destroy()
    dialog.destroy()


# ---------------------------------------------------------------------------
# ProfileSettingsDialog: language change deferred until "Einstellungen speichern"
# ---------------------------------------------------------------------------


def test_language_selection_not_applied_until_save(app_and_storage):
    app, storage, config = app_and_storage
    from ui.dialogs.profile_settings_dialog import ProfileSettingsDialog
    from services.i18n_service import get_i18n

    assert get_i18n().current_language == "de"

    profile = storage.load_profile()
    profile.ui_settings.language = "de"

    dialog = ProfileSettingsDialog(
        app, profile=profile, storage_service=storage, on_profile_updated=lambda: None
    )
    dialog.update_idletasks()

    # Simulate the user picking a different language in the dropdown WITHOUT
    # saving yet.
    dialog.language_combo.set("English")
    dialog.update_idletasks()

    # The app-wide language must not have switched yet.
    assert get_i18n().current_language == "de"
    assert profile.ui_settings.language == "de"

    # Only clicking "Einstellungen speichern" may apply it.
    dialog.save_settings()

    assert get_i18n().current_language == "en"
    assert profile.ui_settings.language == "en"

    dialog.destroy()


def test_language_selection_change_of_mind_before_saving_has_no_side_effect(app_and_storage):
    """Selecting Svenska then switching back to Deutsch before saving must
    result in Deutsch being saved - proving the dropdown selection itself
    never touches the live language, only save_settings() does."""
    app, storage, config = app_and_storage
    from ui.dialogs.profile_settings_dialog import ProfileSettingsDialog
    from services.i18n_service import get_i18n

    profile = storage.load_profile()
    profile.ui_settings.language = "de"

    dialog = ProfileSettingsDialog(
        app, profile=profile, storage_service=storage, on_profile_updated=lambda: None
    )
    dialog.update_idletasks()

    dialog.language_combo.set("Svenska")
    dialog.update_idletasks()
    dialog.language_combo.set("Deutsch")
    dialog.update_idletasks()

    assert get_i18n().current_language == "de"

    dialog.save_settings()

    assert get_i18n().current_language == "de"
    assert profile.ui_settings.language == "de"

    dialog.destroy()
