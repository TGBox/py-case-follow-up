import os
from pathlib import Path
from datetime import datetime
from models.case import Case, WorkflowStatus
from models.customer import Customer, Contact
from services.calendar_email_service import CalendarEmailService


from models.case import Case, WorkflowStatus, Classification, CaseCustomer, TimelineEntry


def create_sample_case() -> Case:
    cust = Customer(
        customer_id="00121",
        practice_name="Gemeinschaftspraxis Musterstadt",
        contacts=[
            Contact(
                name="Dr. Anna Weber",
                email="weber@musterpraxis.de",
                phone="030-12345678",
            )
        ],
    )
    return Case(
        case_id="T-2026-9999",
        customer=CaseCustomer(
            customer_id=cust.customer_id,
            practice_name=cust.practice_name,
            contact_person=cust.contact_person,
            phone=cust.phone,
            email=cust.email,
        ),
        classification=Classification(
            schema_id="schema_bug",
            title="Zuzahlungsdatei lässt sich nicht erzeugen",
            deadline_callback="25.08.2026 14:00",
        ),
        timeline=[TimelineEntry(timestamp="2026-08-24T20:00:00", author="DaniBani", note="Beim Export der Zuzahlungsdatei tritt Fehler AL-99 auf.")],
        workflow_status=WorkflowStatus(followup_at="2026-08-25T14:00:00"),
        created_by="DaniBani",
    )


def test_calendar_email_service_ics_generation(tmp_path: Path):
    service = CalendarEmailService(workspace_dir=tmp_path)
    case = create_sample_case()

    ics_content = service.generate_ics_content(case, user_name="TestAgent")

    assert "BEGIN:VCALENDAR" in ics_content
    assert "VERSION:2.0" in ics_content
    assert "BEGIN:VEVENT" in ics_content
    assert "SUMMARY:[Fall T-2026-9999] Rückruf: Gemeinschaftspraxis Musterstadt - Zuzahlungsdatei lässt sich nicht erzeugen" in ics_content
    assert "VALARM" in ics_content
    assert "TRIGGER:-PT15M" in ics_content
    assert "END:VCALENDAR" in ics_content


def test_calendar_email_service_ics_file_saving(tmp_path: Path):
    service = CalendarEmailService(workspace_dir=tmp_path)
    case = create_sample_case()

    ics_file = service.generate_ics_file(case, target_dir=tmp_path, user_name="TestAgent")

    assert ics_file.exists()
    assert ics_file.name == "Rueckruf_T-2026-9999.ics"
    text = ics_file.read_text(encoding="utf-8")
    assert "Gemeinschaftspraxis Musterstadt" in text


def test_calendar_email_service_email_draft():
    service = CalendarEmailService()
    case = create_sample_case()

    draft = service.generate_email_draft(case, user_name="DaniBani")

    assert draft["to"] == "weber@musterpraxis.de"
    assert "T-2026-9999" in draft["subject"]
    assert "Zuzahlungsdatei" in draft["subject"]
    assert "Sehr geehrte(r) Dr. Anna Weber," in draft["body"]
    assert "DaniBani" in draft["body"]
