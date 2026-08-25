"""Comprehensive test suite for German datetime standardization ("DD.MM.YYYY HH:MM Uhr")

and architectural anti-regression verification across UI dialogs, views, and service drafts.
"""

import re
import pytest
from datetime import datetime
from pathlib import Path
import customtkinter as ctk

from config import AppConfig
from enums import Actor, BoardColumn, UrgencyLevel
from models.case import Case, CaseCustomer, Classification, WorkflowStatus, TimelineEntry
from models.customer import Customer, Contact
from services.calendar_email_service import CalendarEmailService
from services.storage_service import StorageService
from services.scoring_service import ScoringService
from services.attachment_service import AttachmentService
from services.wiki_sync_service import WikiSyncService
from ui.dialogs.email_calendar_dialog import EmailCalendarDialog
from ui.views.cockpit_view import CockpitView
from utils.datetime_utils import (
    format_german_date,
    format_german_time,
    format_german_datetime,
    parse_german_date,
    parse_iso,
    get_local_now,
)


def test_format_german_date():
    """Verify format_german_date always outputs DD.MM.YYYY."""
    assert format_german_date("2026-08-25T14:30:00") == "25.08.2026"
    assert format_german_date("2026-12-01") == "01.12.2026"
    assert format_german_date(datetime(2026, 8, 25, 14, 30)) == "25.08.2026"
    assert format_german_date("25.08.2026") == "25.08.2026"
    assert format_german_date("") == ""
    assert format_german_date(None) == ""


def test_format_german_time():
    """Verify format_german_time outputs HH:MM Uhr."""
    assert format_german_time("2026-08-25T14:30:00") == "14:30 Uhr"
    assert format_german_time("2026-08-25T09:05:00", with_uhr=False) == "09:05"
    assert format_german_time("14:30") == "14:30 Uhr"
    assert format_german_time("14:30 Uhr") == "14:30 Uhr"
    assert format_german_time("") == ""
    assert format_german_time(None) == ""


def test_format_german_datetime():
    """Verify format_german_datetime outputs DD.MM.YYYY HH:MM Uhr."""
    # From ISO string
    assert format_german_datetime("2026-08-25T10:00:00") == "25.08.2026 10:00 Uhr"
    assert format_german_datetime("2026-08-25T10:00:00", with_uhr=False) == "25.08.2026 10:00"
    assert format_german_datetime("2026-08-25T10:00:00", include_seconds=True) == "25.08.2026 10:00:00 Uhr"

    # From datetime object
    dt = datetime(2026, 8, 25, 10, 0, 0)
    assert format_german_datetime(dt) == "25.08.2026 10:00 Uhr"

    # From pre-formatted string with or without 'Uhr'
    assert format_german_datetime("25.08.2026 10:00") == "25.08.2026 10:00 Uhr"
    assert format_german_datetime("25.08.2026 10:00 Uhr") == "25.08.2026 10:00 Uhr"

    # Empty / None
    assert format_german_datetime("") == ""
    assert format_german_datetime(None) == ""


def test_parse_german_date():
    """Verify parse_german_date handles DD.MM.YYYY, DD.MM.YYYY HH:MM and with 'Uhr'."""
    assert parse_german_date("25.08.2026 10:00 Uhr") == "2026-08-25T10:00:00"
    assert parse_german_date("25.08.2026 10:00") == "2026-08-25T10:00:00"
    assert parse_german_date("25.08.2026") == "2026-08-25T00:00:00"
    assert parse_german_date("2026-08-25T10:00:00") == "2026-08-25T10:00:00"


def test_case_model_formatted_datetime_properties():
    """Verify Case model convenience properties return standardized German datetime strings."""
    case = Case(
        case_id="T-2026-001",
        customer=CaseCustomer(customer_id="K-001", practice_name="Praxis Dr. Test"),
        classification=Classification(title="Test Fall", deadline_callback="2026-08-25T10:00:00"),
        workflow_status=WorkflowStatus(followup_at="2026-08-25T14:30:00"),
        created_at="2026-08-24T08:00:00",
        updated_at="2026-08-24T12:00:00",
    )

    assert case.formatted_deadline == "25.08.2026 10:00 Uhr"
    assert case.formatted_followup == "25.08.2026 14:30 Uhr"
    assert case.formatted_created_at == "24.08.2026 08:00 Uhr"
    assert case.formatted_updated_at == "24.08.2026 12:00 Uhr"


def test_calendar_email_service_email_draft_german_datetime_and_status():
    """Verify generate_email_draft formats deadline and status cleanly in German."""
    case = Case(
        case_id="T-2026-1214",
        customer=CaseCustomer(
            customer_id="00121",
            practice_name="Praxis Wolf",
            contact_person="Frau Müller",
            email="wolf@praxis.de",
        ),
        classification=Classification(
            title="Verschwundene Rechnung",
            deadline_callback="2026-08-25T10:00:00",
        ),
        workflow_status=WorkflowStatus(
            board_column=BoardColumn.ACTION_REQUIRED,
            current_actor=Actor.SUPPORT,
        ),
        created_by="Daniel Rösch",
    )

    service = CalendarEmailService()
    draft = service.generate_email_draft(case, user_name="Daniel Rösch")

    body = draft["body"]
    assert "Geplante Rückruf-Deadline: 25.08.2026 10:00 Uhr" in body
    assert "2026-08-25T10:00:00" not in body  # Raw ISO string must not appear
    assert "Aktueller Status: Aktion erforderlich" in body  # German status display


def test_email_calendar_dialog_ui_layout_and_header(tmp_path: Path):
    """Verify EmailCalendarDialog displays formatted deadline in header and has structured 2-row button layout."""
    case = Case(
        case_id="T-2026-1214",
        customer=CaseCustomer(customer_id="00121", practice_name="Praxis Wolf", email="wolf@praxis.de"),
        classification=Classification(title="Verschwundene Rechnung", deadline_callback="2026-08-25T10:00:00"),
        workflow_status=WorkflowStatus(board_column=BoardColumn.ACTION_REQUIRED),
    )

    app = ctk.CTk()
    app.withdraw()

    service = CalendarEmailService(workspace_dir=tmp_path)
    dialog = EmailCalendarDialog(app, case, service, user_name="Daniel Rösch")
    dialog.update_idletasks()
    # Check window size has comfortable minimums
    min_w, min_h = dialog.wm_minsize()
    assert min_w >= 720
    assert min_h >= 540

    # Check header text contains formatted deadline
    header_found = False
    for widget in dialog.winfo_children():
        for child in getattr(widget, "winfo_children", lambda: [])():
            if isinstance(child, ctk.CTkFrame):
                for sub in child.winfo_children():
                    if isinstance(sub, ctk.CTkLabel):
                        txt = sub.cget("text")
                        if "Rückruf-Deadline:" in txt:
                            header_found = True
                            assert "25.08.2026 10:00 Uhr" in txt
                            assert "2026-08-25T10:00:00" not in txt

    assert header_found, "Header label with Rückruf-Deadline was not found."

    dialog.destroy()
    app.destroy()


def test_anti_regression_no_raw_iso_in_ui_outputs():
    """Anti-regression test: Ensure no raw ISO 8601 strings (YYYY-MM-DDTHH:MM...) appear in user-facing UI text."""
    iso_pattern = re.compile(r"\b20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}")

    case = Case(
        case_id="T-2026-9999",
        customer=CaseCustomer(customer_id="K-001", practice_name="Praxis Alpha"),
        classification=Classification(title="Test Ticket", deadline_callback="2026-08-25T15:30:00"),
        workflow_status=WorkflowStatus(followup_at="2026-08-26T09:00:00", followup_note="Test"),
        created_at="2026-08-24T08:00:00",
        updated_at="2026-08-24T12:00:00",
        timeline=[
            TimelineEntry(timestamp="2026-08-24T08:30:00", author="Tester", note="Notiz 1"),
        ],
    )

    # 1. Check formatted properties
    assert not iso_pattern.search(case.formatted_deadline)
    assert not iso_pattern.search(case.formatted_followup)
    assert not iso_pattern.search(case.formatted_created_at)
    assert not iso_pattern.search(case.formatted_updated_at)

    # 2. Check email draft output
    service = CalendarEmailService()
    draft = service.generate_email_draft(case, user_name="Tester")
    assert not iso_pattern.search(draft["body"]), f"Raw ISO found in draft body: {draft['body']}"
