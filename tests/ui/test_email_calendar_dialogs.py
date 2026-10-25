"""Email draft, calendar export and combined email/calendar dialogs, plus German salutation formatting."""

import pytest

from enums import Actor, UrgencyLevel
from models.case import Case, CaseCustomer, Classification, WorkflowStatus
from models.customer import Contact, Customer
from services.calendar_email_service import CalendarEmailService, format_german_salutation
from services.snippet_service import SnippetService


def _body(dialog) -> str:
    return dialog.body_textbox.get("1.0", "end-1c")


@pytest.mark.parametrize(
    "contact, practice, expected",
    [
        ("Frau Weber", "", "Sehr geehrte Frau Weber,"),
        ("Herr Lehmann", "", "Sehr geehrter Herr Lehmann,"),
        ("Herrn Schmidt", "", "Sehr geehrter Herr Schmidt,"),
        ("Dr. Elena Rossi", "", "Sehr geehrte(r) Dr. Elena Rossi,"),
        ("Frau Dr. Meyer", "", "Sehr geehrte Frau Dr. Meyer,"),
        ("Herr Dr. med. Koch", "", "Sehr geehrter Herr Dr. med. Koch,"),
        ("Klaus Becker", "", "Sehr geehrte/r Klaus Becker,"),
        ("", "Praxis Sonnenberg", "Sehr geehrte Damen und Herren (Praxis Sonnenberg),"),
        ("", "", "Sehr geehrte Damen und Herren,"),
    ],
)
def test_german_salutation(contact, practice, expected):
    assert format_german_salutation(contact, practice) == expected


def test_email_draft_dialog_prefills_from_case_and_inserts_snippet(root, config, tmp_path):
    from ui.dialogs.email_draft_dialog import EmailDraftDialog

    case = Case(
        case_id="T-MAIL-01",
        customer=CaseCustomer(customer_id="K-100", practice_name="Praxis Dr. Sonnenschein",
                              email="info@sonnenschein.de", contact_person="Frau Weber"),
        classification=Classification(title="Rezeptdruck Fehler", urgency_level=UrgencyLevel.YELLOW),
        workflow_status=WorkflowStatus(current_actor=Actor.SUPPORT),
    )
    dialog = EmailDraftDialog(root, case=case, calendar_email_service=CalendarEmailService(config),
                              user_name="DaniBani", snippet_service=SnippetService(tmp_path))
    dialog.update_idletasks()

    assert dialog.to_entry.get() == "info@sonnenschein.de"
    assert "T-MAIL-01" in dialog.subject_entry.get()
    assert "Sehr geehrte Frau Weber," in _body(dialog)

    dialog.insert_snippet_text("Zusätzlicher Text")
    assert "Zusätzlicher Text" in _body(dialog)


def test_email_draft_dialog_without_case_uses_praxiskartei_autocomplete(root, config):
    from ui.dialogs.email_draft_dialog import EmailDraftDialog

    customers = [
        Customer(customer_id="K-10482", practice_name="Praxis Sonnenberg", contacts=[
            Contact(name="Frau Weber", role="Leitende MFA", email="weber@sonnenberg.de"),
            Contact(name="Dr. med. Frank Berg", role="Inhaber", email="berg@sonnenberg.de"),
        ]),
        Customer(customer_id="K-10890", practice_name="Zahnarztpraxis Dr. Lehmann", contacts=[
            Contact(name="Herr Lehmann", role="Praxisinhaber", email="lehmann@zahnpraxis.de"),
        ]),
    ]
    dialog = EmailDraftDialog(root, case=None, calendar_email_service=CalendarEmailService(config),
                              user_name="SupportAgent", customers=customers)
    dialog.update_idletasks()

    assert dialog.to_entry.get() == ""
    assert "Sehr geehrte Damen und Herren," in _body(dialog)

    assert not dialog.suggestions_frame_visible
    dialog.toggle_praxiskartei_dropdown()
    assert dialog.suggestions_frame_visible

    dialog.to_entry.delete(0, "end")
    dialog.to_entry.insert(0, "weber")
    dialog._on_to_keyrelease()
    assert dialog.suggestions_frame_visible

    # Picking a contact fills the address, closes the list and adapts the salutation.
    for key, email, salutation in [
        ("weber", "weber@sonnenberg.de", "Sehr geehrte Frau Weber,"),
        ("lehmann", "lehmann@zahnpraxis.de", "Sehr geehrter Herr Lehmann,"),
    ]:
        dialog.select_contact(next(c for c in dialog.all_contacts if key in c["search_key"]))
        assert dialog.to_entry.get() == email
        assert not dialog.suggestions_frame_visible
        assert salutation in _body(dialog)


def test_calendar_export_dialog_describes_followup(root, config):
    from ui.dialogs.calendar_export_dialog import CalendarExportDialog

    case = Case(
        case_id="T-CAL-01",
        customer=CaseCustomer(customer_id="K-200", practice_name="Klinik am Park", phone="0711-12345", contact_person="Herr Wagner"),
        classification=Classification(title="TI Konnektor Update", urgency_level=UrgencyLevel.RED),
        workflow_status=WorkflowStatus(followup_at="2026-08-27T10:00:00",
                                       followup_note="Mit Herrn Wagner Konnektor neu starten",
                                       current_actor=Actor.SUPPORT),
    )
    dialog = CalendarExportDialog(root, case=case, calendar_email_service=CalendarEmailService(config))
    dialog.update_idletasks()

    desc = dialog.desc_textbox.get("1.0", "end")
    for text in ("T-CAL-01", "Klinik am Park", "Konnektor neu starten"):
        assert text in desc
