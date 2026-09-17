"""Tests for EmailCalendarDialog: mailto, clipboard, ICS export, snippet picker, and save dialog."""

from pathlib import Path
from tkinter import filedialog
from unittest.mock import MagicMock
import customtkinter as ctk
import pytest
from config import AppConfig
from enums import Actor, UrgencyLevel
from models.case import Case, CaseCustomer, Classification, WorkflowStatus
from services.calendar_email_service import CalendarEmailService
from services.snippet_service import SnippetService
from ui.dialogs.email_calendar_dialog import EmailCalendarDialog


@pytest.fixture(scope="module")
def app_root():
    app = ctk.CTk()
    app.withdraw()
    yield app
    try:
        app.destroy()
    except Exception:
        pass


@pytest.fixture
def sample_case():
    return Case(
        case_id="T-MAIL-99",
        customer=CaseCustomer(
            customer_id="K-505",
            practice_name="Hautarztpraxis Dr. Becker",
            email="dr.becker@haut-praxis.de",
            contact_person="Dr. Becker",
        ),
        classification=Classification(title="Fehler beim Laborabruf", urgency_level=UrgencyLevel.RED),
        workflow_status=WorkflowStatus(current_actor=Actor.TECH),
    )


def test_email_calendar_dialog_actions(monkeypatch, app_root, sample_case, tmp_path: Path):
    """Verify mailto opening, text copying, and ICS generation in EmailCalendarDialog."""
    config = AppConfig(workspace_dir=tmp_path)
    cal_svc = CalendarEmailService(config)
    snippet_svc = SnippetService(tmp_path)

    dialog = EmailCalendarDialog(
        app_root,
        case=sample_case,
        calendar_email_service=cal_svc,
        user_name="Max Mustermann",
        snippet_service=snippet_svc,
    )

    # 1. Test on_open_mailto
    mailto_calls = []
    monkeypatch.setattr(cal_svc, "open_mailto_link", lambda to, sub, body: mailto_calls.append((to, sub, body)))
    dialog.on_open_mailto()
    assert len(mailto_calls) == 1
    assert mailto_calls[0][0] == "dr.becker@haut-praxis.de"
    assert "Mail-Client wurde mit dem Entwurf aufgerufen" in dialog.status_lbl.cget("text")

    # 2. Test on_copy_text
    dialog.on_copy_text()
    assert "in die Zwischenablage kopiert" in dialog.status_lbl.cget("text")

    # 3. Test on_open_ics
    ics_opened = []
    monkeypatch.setattr(cal_svc, "open_ics_file", lambda p: ics_opened.append(p))
    dialog.on_open_ics()
    assert len(ics_opened) == 1
    assert "Kalendereintrag (.ics) geöffnet" in dialog.status_lbl.cget("text")

    # 4. Test on_save_ics (with filename)
    target_ics = tmp_path / "custom_rueckruf.ics"
    monkeypatch.setattr(filedialog, "asksaveasfilename", lambda **k: str(target_ics))
    dialog.on_save_ics()
    assert target_ics.exists()
    assert "BEGIN:VCALENDAR" in target_ics.read_text(encoding="utf-8")
    assert "Kalenderdatei gespeichert" in dialog.status_lbl.cget("text")

    # 5. Test on_save_ics cancelled
    monkeypatch.setattr(filedialog, "asksaveasfilename", lambda **k: "")
    dialog.on_save_ics()

    # 6. Test insert_snippet_text
    initial_len = len(dialog.body_textbox.get("1.0", "end-1c"))
    dialog.insert_snippet_text("Zusätzlicher Textbaustein Hinweis.")
    new_len = len(dialog.body_textbox.get("1.0", "end-1c"))
    assert new_len > initial_len
    assert "Zusätzlicher Textbaustein Hinweis." in dialog.body_textbox.get("1.0", "end-1c")

    # 7. Test open_snippet_picker
    mock_picker_cls = MagicMock()
    monkeypatch.setattr("ui.dialogs.snippet_picker_dialog.SnippetPickerDialog", mock_picker_cls)
    dialog.open_snippet_picker()
    mock_picker_cls.assert_called_once()

    dialog.destroy()
