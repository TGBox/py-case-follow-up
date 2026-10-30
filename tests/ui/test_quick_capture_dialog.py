"""Quick-capture window: prefill, validation, reminder choice and how the app stores the task."""

from types import SimpleNamespace

import pytest

from services.i18n_service import tr
from ui.app_dialogs import DialogLaunchersMixin
from ui.dialogs.quick_capture_dialog import QuickCaptureDialog


def _dialog(root, initial_text="", colleagues=("Anna Beispiel", "Ben Test")):
    saved: list[tuple[str, str, str]] = []
    dialog = QuickCaptureDialog(root, colleagues=list(colleagues), initial_text=initial_text,
                                on_save=lambda text, person, preset: saved.append((text, person, preset)))
    dialog.update_idletasks()
    return dialog, saved


def _alive(dialog) -> bool:
    try:
        return bool(dialog.winfo_exists())
    except Exception:
        return False


def test_the_text_is_prefilled_from_the_clipboard(root):
    dialog, _ = _dialog(root, initial_text="Kann jemand kurz auf Fall Z schauen?")
    assert dialog.text_box.get("1.0", "end-1c") == "Kann jemand kurz auf Fall Z schauen?"
    dialog.destroy()


def test_saving_hands_over_text_person_and_the_default_reminder(root):
    dialog, saved = _dialog(root, initial_text="Fall Z besprechen")
    dialog.person_combo.set("Anna Beispiel")
    dialog.on_click_save()
    assert saved == [("Fall Z besprechen", "Anna Beispiel", "1h")]
    assert not _alive(dialog)


def test_the_reminder_choice_is_independent_of_the_language(root):
    dialog, saved = _dialog(root, initial_text="x")
    dialog.reminder_combo.set(tr("quick_capture.preset_none", "Keine Erinnerung"))
    dialog.on_click_save()
    assert saved[0][2] == "none"


@pytest.mark.parametrize("key,default,preset", [
    ("quick_capture.preset_2h", "In 2 Stunden", "2h"),
    ("quick_capture.preset_today_1630", "Heute 16:30", "today_1630"),
    ("quick_capture.preset_tomorrow_0800", "Morgen 08:00", "tomorrow_0800"),
])
def test_every_reminder_choice_maps_to_its_preset(root, key, default, preset):
    dialog, saved = _dialog(root, initial_text="x")
    dialog.reminder_combo.set(tr(key, default))
    dialog.on_click_save()
    assert saved[0][2] == preset


def test_empty_text_is_not_saved(root):
    dialog, saved = _dialog(root, initial_text="   ")
    dialog.on_click_save()
    assert saved == []
    assert _alive(dialog)
    assert dialog.error_label.cget("text")
    dialog.destroy()


def test_the_person_is_optional(root):
    dialog, saved = _dialog(root, initial_text="Pause nicht vergessen")
    dialog.on_click_save()
    assert saved == [("Pause nicht vergessen", "", "1h")]


def test_escape_closes_without_saving_even_with_text(root):
    dialog, saved = _dialog(root, initial_text="Fall Z")
    dialog._on_escape()
    assert saved == []
    assert not _alive(dialog)


def test_a_dialog_without_colleagues_still_opens(root):
    dialog, _ = _dialog(root, colleagues=())
    assert dialog.person_combo.get() == ""
    dialog.destroy()


# --- how the app stores the task -----------------------------------------------------------

class _Recorder:
    def __init__(self):
        self.scored = []
        self.saved = 0
        self.refreshed = 0


def _app_stub(existing=None):
    recorder = _Recorder()
    cases = list(existing or [])
    stub = SimpleNamespace(
        profile=SimpleNamespace(user=SimpleNamespace(name="Ich")),
        cases=cases,
        scoring_service=SimpleNamespace(update_case_scoring=lambda c: recorder.scored.append(c)),
        storage_service=SimpleNamespace(save_cases=lambda cs: setattr(recorder, "saved", recorder.saved + 1)),
        refresh_views=lambda: setattr(recorder, "refreshed", recorder.refreshed + 1),
        _all_known_case_ids=lambda: {c.case_id for c in cases},
    )
    return stub, recorder


def test_the_app_stores_the_task_scored_and_saved():
    stub, recorder = _app_stub()
    case = DialogLaunchersMixin.on_quick_capture_saved(stub, "Fall Z besprechen", "Anna Beispiel", "none")

    assert stub.cases == [case]
    assert recorder.scored == [case]
    assert recorder.saved == 1
    assert recorder.refreshed == 1
    assert case.is_internal
    assert case.customer.contact_person == "Anna Beispiel"
    assert case.workflow_status.followup_at == ""


def test_two_tasks_in_the_same_second_get_different_ids():
    stub, _ = _app_stub()
    first = DialogLaunchersMixin.on_quick_capture_saved(stub, "Eins", "", "none")
    second = DialogLaunchersMixin.on_quick_capture_saved(stub, "Zwei", "", "none")
    assert first.case_id != second.case_id
    assert len({c.case_id for c in stub.cases}) == 2


def test_the_reminder_makes_the_task_due_later_not_now():
    from utils.datetime_utils import get_local_now, parse_followup_datetime

    stub, _ = _app_stub()
    case = DialogLaunchersMixin.on_quick_capture_saved(stub, "Später", "", "1h")
    due = parse_followup_datetime(case.workflow_status.followup_at)
    assert due is not None and due > get_local_now()
