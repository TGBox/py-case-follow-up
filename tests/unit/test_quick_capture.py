from datetime import datetime, timedelta, timezone

import pytest

from constants import INTERNAL_CUSTOMER_ID, QUICK_CAPTURE_PRESETS, QUICK_CAPTURE_TITLE_MAX_CHARS
from enums import Actor, BoardColumn, Channel
from services.global_hotkey_service import (
    MOD_ALT,
    MOD_CONTROL,
    MOD_SHIFT,
    GlobalHotkeyService,
    parse_hotkey,
)
from services.quick_capture import build_quick_case, build_title, new_case_id, resolve_reminder
from utils.datetime_utils import parse_followup_datetime

TZ = timezone(timedelta(hours=1))
MORNING = datetime(2026, 10, 29, 9, 15, 42, tzinfo=TZ)
EVENING = datetime(2026, 10, 29, 17, 5, 0, tzinfo=TZ)


# --- reminder presets -----------------------------------------------------------------

def test_relative_presets_add_hours():
    assert resolve_reminder("1h", MORNING) == MORNING + timedelta(hours=1)
    assert resolve_reminder("2h", MORNING) == MORNING + timedelta(hours=2)


def test_none_means_no_reminder():
    assert resolve_reminder("none", MORNING) is None


def test_today_1630_is_today_while_it_is_still_ahead():
    assert resolve_reminder("today_1630", MORNING) == datetime(2026, 10, 29, 16, 30, tzinfo=TZ)


def test_today_1630_moves_to_tomorrow_once_it_has_passed():
    assert resolve_reminder("today_1630", EVENING) == datetime(2026, 10, 30, 16, 30, tzinfo=TZ)


def test_tomorrow_0800_is_always_the_next_day():
    assert resolve_reminder("tomorrow_0800", MORNING) == datetime(2026, 10, 30, 8, 0, tzinfo=TZ)
    assert resolve_reminder("tomorrow_0800", EVENING) == datetime(2026, 10, 30, 8, 0, tzinfo=TZ)


def test_an_unknown_preset_is_rejected():
    with pytest.raises(ValueError):
        resolve_reminder("whenever", MORNING)


def test_every_preset_resolves():
    for preset in QUICK_CAPTURE_PRESETS:
        resolve_reminder(preset, MORNING)


# --- title -----------------------------------------------------------------------------

def test_title_is_the_first_non_empty_line():
    assert build_title("\n\n  Rückruf wegen Drucker \nZweite Zeile") == "Rückruf wegen Drucker"


def test_title_is_prefixed_with_the_person():
    assert build_title("Fall Z besprechen", "Anna Beispiel") == "Anna Beispiel: Fall Z besprechen"


def test_a_long_first_line_is_shortened():
    title = build_title("x" * 300)
    assert len(title) == QUICK_CAPTURE_TITLE_MAX_CHARS
    assert title.endswith("…")


# --- case id ---------------------------------------------------------------------------

def test_case_id_has_the_usual_shape():
    case_id = new_case_id(set(), MORNING)
    assert case_id == "T-2026-1542"


def test_a_taken_case_id_gets_a_running_suffix():
    assert new_case_id({"T-2026-1542"}, MORNING) == "T-2026-1542-2"
    assert new_case_id({"T-2026-1542", "T-2026-1542-2"}, MORNING) == "T-2026-1542-3"


# --- the case --------------------------------------------------------------------------

def _case(**overrides):
    args = dict(text="Fall Z besprechen\nDetails folgen", person="Anna Beispiel", reminder=MORNING + timedelta(hours=1),
                created_by="Ich", taken_ids=set(), now=MORNING)
    args.update(overrides)
    return build_quick_case(**args)


def test_the_case_is_a_valid_internal_task():
    case = _case()
    assert case.validate() == []
    assert case.is_internal
    assert case.customer.customer_id == INTERNAL_CUSTOMER_ID
    assert case.customer.contact_person == "Anna Beispiel"
    assert case.classification.schema_id == "schema_internal_task"
    assert case.classification.title == "Anna Beispiel: Fall Z besprechen"
    assert case.created_by == case.assigned_to == "Ich"
    assert case.workflow_status.board_column == BoardColumn.ACTION_REQUIRED
    assert case.workflow_status.current_actor == Actor.SUPPORT
    assert case.attachment_directory.endswith("_Intern")


def test_the_full_text_becomes_the_first_note_and_the_description():
    case = _case()
    assert case.timeline[0].note == "Fall Z besprechen\nDetails folgen"
    assert case.timeline[0].channel == Channel.INTERNAL_NOTE
    assert case.timeline[0].author == "Ich"
    assert case.form_data["description"] == "Fall Z besprechen\nDetails folgen"
    assert case.form_data["internal_category"]


def test_the_reminder_is_stored_in_a_form_the_app_can_read_back():
    case = _case(reminder=datetime(2026, 10, 29, 16, 30, tzinfo=TZ))
    assert parse_followup_datetime(case.workflow_status.followup_at).replace(tzinfo=None) == datetime(2026, 10, 29, 16, 30)


def test_without_a_reminder_no_follow_up_is_set():
    assert _case(reminder=None).workflow_status.followup_at == ""


def test_the_person_is_optional():
    case = _case(person="")
    assert case.validate() == []
    assert case.classification.title == "Fall Z besprechen"
    assert case.customer.contact_person == ""


def test_the_person_can_be_found_by_text_search():
    assert "anna beispiel" in _case().get_searchable_text()


def test_the_case_survives_a_round_trip_through_json():
    from models.case import Case

    case = _case()
    assert Case.from_dict(case.to_dict()) == case


def test_blank_text_is_rejected():
    with pytest.raises(ValueError):
        _case(text="  \n ")


# --- hotkey parsing ----------------------------------------------------------------------

def test_the_default_hotkey_parses():
    assert parse_hotkey("Ctrl+Alt+N") == (MOD_CONTROL | MOD_ALT, ord("N"))


def test_parsing_ignores_case_spaces_and_german_names():
    assert parse_hotkey(" strg + shift + k ") == (MOD_CONTROL | MOD_SHIFT, ord("K"))


def test_function_keys_and_digits_work():
    assert parse_hotkey("Ctrl+F9") == (MOD_CONTROL, 0x70 + 8)
    assert parse_hotkey("Ctrl+Alt+7") == (MOD_CONTROL | MOD_ALT, ord("7"))


@pytest.mark.parametrize("text", ["", "N", "Ctrl", "Ctrl+", "Ctrl+Foo+N", "Ctrl+F13", "Ctrl+F0", "Ctrl+ä", "Ctrl+NN"])
def test_unusable_hotkeys_are_rejected(text):
    assert parse_hotkey(text) is None


def test_a_plain_letter_is_never_grabbed_system_wide():
    assert parse_hotkey("N") is None


def test_the_service_does_nothing_outside_windows(monkeypatch):
    monkeypatch.setattr("services.global_hotkey_service.sys.platform", "linux")
    service = GlobalHotkeyService("Ctrl+Alt+N")
    assert service.start() is False
    assert service.consume() is False
    service.stop()  # harmless without a thread


def test_consume_reports_each_press_once():
    service = GlobalHotkeyService("Ctrl+Alt+N")
    service._pressed.set()
    assert service.consume() is True
    assert service.consume() is False
