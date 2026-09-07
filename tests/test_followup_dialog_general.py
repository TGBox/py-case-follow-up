"""General behavior tests for FollowupDialog (src/ui/dialogs/followup_dialog.py).

This dialog previously had ZERO test coverage at all (confirmed via a
test-coverage audit: no test file in tests/ imported or referenced
`followup_dialog`), despite being an actively used, non-trivial dialog.
test_followup_time_stacking_and_language_deferral.py already covers the
"+1/+2 Std." stacking regression; this file covers the rest of the dialog's
behavior: initial field pre-fill, the note field, save/clear callbacks, the
remaining quick-presets, and the conditional "Entfernen" button.
"""

from pathlib import Path
from datetime import timedelta
import customtkinter as ctk
import pytest

from config import AppConfig
from enums import BoardColumn
from models.case import Case, CaseCustomer, Classification, WorkflowStatus
from services.storage_service import StorageService
from services.i18n_service import tr
from utils.datetime_utils import (
    get_local_now,
    format_german_date,
    format_german_datetime,
    parse_followup_datetime,
)


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
    """Isolate the global I18nService singleton between tests."""
    import services.i18n_service as i18n_module

    previous = i18n_module._i18n_instance
    i18n_module._i18n_instance = None
    yield
    i18n_module._i18n_instance = previous


def _make_case(followup_at: str = "", followup_note: str = "") -> Case:
    return Case(
        case_id="T-GEN-01",
        customer=CaseCustomer(customer_id="K-1", practice_name="Praxis General"),
        classification=Classification(title="Allgemeiner Test"),
        workflow_status=WorkflowStatus(
            board_column=BoardColumn.NEW,
            followup_at=followup_at,
            followup_note=followup_note,
        ),
    )


def _find_buttons_with_text(widget, text: str) -> list:
    """Recursively collect all CTkButton descendants whose configured text matches."""
    found = []
    for child in widget.winfo_children():
        if isinstance(child, ctk.CTkButton):
            try:
                if child.cget("text") == text:
                    found.append(child)
            except Exception:
                pass
        found.extend(_find_buttons_with_text(child, text))
    return found


# ---------------------------------------------------------------------------
# Initial field pre-fill
# ---------------------------------------------------------------------------


def test_dialog_prefills_field_with_existing_followup_at(app_and_storage):
    app, storage, config = app_and_storage
    from ui.dialogs.followup_dialog import FollowupDialog

    case = _make_case(followup_at="2026-08-05T14:00:00")
    dialog = FollowupDialog(app, case=case, on_followup_set=lambda iso, note: None)
    dialog.update_idletasks()

    assert dialog.date_picker.get() == format_german_datetime("2026-08-05T14:00:00")

    dialog.destroy()


def test_dialog_prefills_default_two_days_ahead_when_no_existing_followup(app_and_storage):
    app, storage, config = app_and_storage
    from ui.dialogs.followup_dialog import FollowupDialog

    case = _make_case(followup_at="")
    dialog = FollowupDialog(app, case=case, on_followup_set=lambda iso, note: None)
    dialog.update_idletasks()

    expected_date = format_german_date(get_local_now() + timedelta(days=2))
    assert dialog.date_picker.get() == f"{expected_date} 09:00"

    dialog.destroy()


def test_dialog_prefills_existing_note(app_and_storage):
    app, storage, config = app_and_storage
    from ui.dialogs.followup_dialog import FollowupDialog

    case = _make_case(followup_at="2026-08-05T14:00:00", followup_note="Beim Entwickler nachfragen")
    dialog = FollowupDialog(app, case=case, on_followup_set=lambda iso, note: None)
    dialog.update_idletasks()

    assert dialog.note_entry.get() == "Beim Entwickler nachfragen"

    dialog.destroy()


# ---------------------------------------------------------------------------
# Save / Clear callbacks
# ---------------------------------------------------------------------------


def test_on_save_invokes_callback_with_iso_and_note(app_and_storage):
    app, storage, config = app_and_storage
    from ui.dialogs.followup_dialog import FollowupDialog

    case = _make_case(followup_at="")
    received = None

    def on_set(iso_val, note):
        nonlocal received
        received = (iso_val, note)

    dialog = FollowupDialog(app, case=case, on_followup_set=on_set)
    dialog.update_idletasks()

    dialog.date_picker.set_date("05.09.2026 10:15")
    dialog.note_entry.delete(0, "end")
    dialog.note_entry.insert(0, "Rückruf vereinbart")

    dialog.on_save()

    assert received is not None
    iso_val, note = received
    assert parse_followup_datetime(iso_val) == parse_followup_datetime("05.09.2026 10:15")
    assert note == "Rückruf vereinbart"


def test_on_save_does_nothing_when_field_is_empty(app_and_storage):
    app, storage, config = app_and_storage
    from ui.dialogs.followup_dialog import FollowupDialog

    case = _make_case(followup_at="")
    called = False

    def on_set(iso_val, note):
        nonlocal called
        called = True

    dialog = FollowupDialog(app, case=case, on_followup_set=on_set)
    dialog.update_idletasks()

    dialog.date_picker.set_date("")
    dialog.on_save()

    assert not called


def test_on_clear_invokes_callback_with_empty_strings(app_and_storage):
    app, storage, config = app_and_storage
    from ui.dialogs.followup_dialog import FollowupDialog

    case = _make_case(followup_at="2026-08-05T14:00:00", followup_note="Alte Notiz")
    received = None

    def on_set(iso_val, note):
        nonlocal received
        received = (iso_val, note)

    dialog = FollowupDialog(app, case=case, on_followup_set=on_set)
    dialog.update_idletasks()

    dialog.on_clear()

    assert received == ("", "")


# ---------------------------------------------------------------------------
# Remaining quick-presets (non-hour-increment ones)
# ---------------------------------------------------------------------------


def test_preset_today_1630(app_and_storage):
    app, storage, config = app_and_storage
    from ui.dialogs.followup_dialog import FollowupDialog

    case = _make_case()
    dialog = FollowupDialog(app, case=case, on_followup_set=lambda iso, note: None)
    dialog.update_idletasks()

    dialog.set_preset_today_1630()
    result = parse_followup_datetime(dialog.date_picker.get())
    now = get_local_now()
    assert result.date() == now.date()
    assert (result.hour, result.minute) == (16, 30)

    dialog.destroy()


def test_preset_today_before_and_after_lunch(app_and_storage):
    app, storage, config = app_and_storage
    from ui.dialogs.followup_dialog import FollowupDialog

    case = _make_case()
    dialog = FollowupDialog(app, case=case, on_followup_set=lambda iso, note: None)
    dialog.update_idletasks()

    dialog.set_preset_today_before_lunch()
    before_lunch = parse_followup_datetime(dialog.date_picker.get())
    assert (before_lunch.hour, before_lunch.minute) == (11, 30)

    dialog.set_preset_today_after_lunch()
    after_lunch = parse_followup_datetime(dialog.date_picker.get())
    assert (after_lunch.hour, after_lunch.minute) == (13, 30)

    dialog.destroy()


def test_preset_tomorrow_8am(app_and_storage):
    app, storage, config = app_and_storage
    from ui.dialogs.followup_dialog import FollowupDialog

    case = _make_case()
    dialog = FollowupDialog(app, case=case, on_followup_set=lambda iso, note: None)
    dialog.update_idletasks()

    dialog.set_preset_tomorrow_8am()
    result = parse_followup_datetime(dialog.date_picker.get())
    now = get_local_now()
    assert result.date() == (now + timedelta(days=1)).date()
    assert (result.hour, result.minute) == (8, 0)

    dialog.destroy()


@pytest.mark.parametrize("days", [1, 2, 3, 7])
def test_preset_days(app_and_storage, days):
    app, storage, config = app_and_storage
    from ui.dialogs.followup_dialog import FollowupDialog

    case = _make_case()
    dialog = FollowupDialog(app, case=case, on_followup_set=lambda iso, note: None)
    dialog.update_idletasks()

    dialog.set_preset_days(days)
    result = parse_followup_datetime(dialog.date_picker.get())
    now = get_local_now()
    assert result.date() == (now + timedelta(days=days)).date()
    assert (result.hour, result.minute) == (9, 0)

    dialog.destroy()


# ---------------------------------------------------------------------------
# Conditional "Entfernen" (clear) button
# ---------------------------------------------------------------------------


def test_remove_button_present_when_followup_already_exists(app_and_storage):
    app, storage, config = app_and_storage
    from ui.dialogs.followup_dialog import FollowupDialog

    case = _make_case(followup_at="2026-08-05T14:00:00")
    dialog = FollowupDialog(app, case=case, on_followup_set=lambda iso, note: None)
    dialog.update_idletasks()

    clear_text = tr("ui_buttons.clear", "❌ Entfernen")
    matches = _find_buttons_with_text(dialog, clear_text)
    assert len(matches) == 1

    dialog.destroy()


def test_remove_button_absent_when_no_followup_exists_yet(app_and_storage):
    app, storage, config = app_and_storage
    from ui.dialogs.followup_dialog import FollowupDialog

    case = _make_case(followup_at="")
    dialog = FollowupDialog(app, case=case, on_followup_set=lambda iso, note: None)
    dialog.update_idletasks()

    clear_text = tr("ui_buttons.clear", "❌ Entfernen")
    matches = _find_buttons_with_text(dialog, clear_text)
    assert len(matches) == 0

    dialog.destroy()
