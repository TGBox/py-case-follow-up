"""Unit and integration tests for Wiedervorlage multi-line formatting, compact line spacing, and hover tooltip behavior."""

import pytest
import customtkinter as ctk
from pathlib import Path
from utils.ui_utils import wrap_and_truncate_text
from models.case import Case, CaseCustomer, Classification, WorkflowStatus
from enums import Actor, UrgencyLevel
from config import AppConfig
from services.storage_service import StorageService
from services.scoring_service import ScoringService
from services.attachment_service import AttachmentService
from services.wiki_sync_service import WikiSyncService
from ui.views.cockpit_view import CockpitView
from ui.widgets.case_list_widget import CaseListWidget


def test_wrap_and_truncate_empty_and_short():
    # Empty string
    text, is_trunc = wrap_and_truncate_text("", max_width=300, max_lines=2)
    assert text == ""
    assert is_trunc is False

    # Short string that fits on 1 line
    text, is_trunc = wrap_and_truncate_text("Kurzer Text", max_width=500, max_lines=2)
    assert text == "Kurzer Text"
    assert is_trunc is False
    assert len(text.splitlines()) <= 1


def test_wrap_and_truncate_fits_two_lines():
    # Text that needs 2 lines but fits within 2 lines
    input_text = "🔔 Wiedervorlage: 25.08.2026 14:00 (Kunde ruft an)"
    text, is_trunc = wrap_and_truncate_text(input_text, max_width=250, max_lines=2)
    lines = text.splitlines()
    assert len(lines) <= 2
    assert is_trunc is False
    assert not text.endswith("...")


def test_wrap_and_truncate_exceeds_two_lines():
    # Long text that exceeds 2 lines and must be truncated to exactly 2 lines with ellipsis
    long_note = (
        "🔔 Wiedervorlage: 25.08.2026 14:00 (Kunde bittet dringend um Rückruf bezüglich "
        "der Schnittstellenfehler mit Cobra und Outlook-Synchronisation sowie Überprüfung der Rechteverwaltung)"
    )
    text, is_trunc = wrap_and_truncate_text(long_note, max_width=250, max_lines=2)
    lines = text.splitlines()
    assert len(lines) == 2
    assert is_trunc is True
    assert lines[1].endswith("...")
    assert len(text) < len(long_note)


def test_wrap_and_truncate_super_long_unbroken_word():
    # Continuous word without spaces
    long_word = "A" * 200
    text, is_trunc = wrap_and_truncate_text(long_word, max_width=150, max_lines=2)
    lines = text.splitlines()
    assert len(lines) == 2
    assert is_trunc is True
    assert text.endswith("...")


def test_cockpit_view_wiedervorlage_tooltip_integration(tmp_path: Path):
    """Test CockpitView multi-line followup display, compact labels, and tooltip resolution."""
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)
    scoring = ScoringService()
    attachment = AttachmentService(config)
    wiki = WikiSyncService(config)

    app = ctk.CTk()
    app.withdraw()

    cockpit = CockpitView(
        app,
        author_name="Tester",
        scoring_service=scoring,
        attachment_service=attachment,
        wiki_service=wiki,
        on_case_updated=lambda c: None,
        on_case_selected=lambda c: None,
        on_search_changed=lambda s: None,
        on_open_export_dialog=lambda c: None,
        on_archive_case=lambda c: None,
        app_config=config,
    )

    # 1. Case without follow-up
    case_no_fw = Case(
        case_id="F-100",
        customer=CaseCustomer(customer_id="K-1", practice_name="Praxis A", contact_person="Dr. A"),
        classification=Classification(title="Test Ohne Followup"),
        workflow_status=WorkflowStatus(current_actor=Actor.SUPPORT, followup_at=""),
    )
    cockpit.on_select_case_from_list(case_no_fw)
    assert cockpit._wiedervorlage_full_text == ""
    assert cockpit._get_wiedervorlage_tooltip_text() == ""

    # 2. Case with follow-up and note
    case_short_fw = Case(
        case_id="F-101",
        customer=CaseCustomer(customer_id="K-2", practice_name="Praxis B", contact_person="Dr. B"),
        classification=Classification(title="Test Kurzes Followup"),
        workflow_status=WorkflowStatus(
            current_actor=Actor.SUPPORT,
            followup_at="2026-08-25T14:00:00",
            followup_note="Kurze Notiz",
        ),
    )
    cockpit.on_select_case_from_list(case_short_fw)
    assert "🔔 Nachfragen am:" in cockpit._wiedervorlage_full_text
    assert "Kurze Notiz" in cockpit._wiedervorlage_full_text
    assert cockpit.wv_hdr_label.cget("text") == "🔔 Nachfragen am:"
    assert "25.08.2026" in cockpit.wv_date_label.cget("text")
    assert "14:00" in cockpit.wv_time_label.cget("text")
    assert "Kurze Notiz" in cockpit.wv_note_label.cget("text")
    assert cockpit._get_wiedervorlage_tooltip_text() == cockpit._wiedervorlage_full_text

    # 3. Case with very long follow-up note
    very_long_note = (
        "Kunde hat gemeldet, dass der Cobra-Export seit dem letzten Update auf Version 4.2 abbricht "
        "und die SQL-Verbindung zum Server im Minutentakt getrennt wird. Dringend mit IT-Leiter klären!"
    )
    case_long_fw = Case(
        case_id="F-102",
        customer=CaseCustomer(customer_id="K-3", practice_name="Praxis C", contact_person="Dr. C"),
        classification=Classification(title="Test Langes Followup"),
        workflow_status=WorkflowStatus(
            current_actor=Actor.SUPPORT,
            followup_at="2026-08-25T14:00:00",
            followup_note=very_long_note,
        ),
    )
    cockpit.info_left_frame.winfo_width = lambda: 280  # type: ignore
    cockpit.on_select_case_from_list(case_long_fw)

    assert "🔔 Nachfragen am:" in cockpit.wv_hdr_label.cget("text")
    assert very_long_note in cockpit.wv_note_label.cget("text")
    full_tt = cockpit._get_wiedervorlage_tooltip_text()
    assert very_long_note in full_tt

    app.destroy()


def test_case_list_widget_wiedervorlage_compact_labels(tmp_path: Path):
    """Test CaseListWidget multi-line Wiedervorlage labels with newline before note."""
    app = ctk.CTk()
    app.withdraw()
    widget = CaseListWidget(app, on_case_selected=lambda c: None, on_search_changed=lambda s: None)
    case_fw = Case(
        case_id="F-200",
        customer=CaseCustomer(customer_id="K-1", practice_name="Praxis Test"),
        classification=Classification(title="Thema"),
        workflow_status=WorkflowStatus(
            current_actor=Actor.SUPPORT,
            followup_at="2026-08-25T09:00:00",
            followup_note="Wichtige Nachfrage",
        ),
    )
    widget.set_cases([case_fw])
    app.update()

    lbl_texts = [lbl.cget("text") for lbl in widget.wrap_labels]
    assert "🔔 Nachfragen am:" in lbl_texts
    assert any("25.08.2026" in t for t in lbl_texts)
    assert any("09:00" in t for t in lbl_texts)
    assert any("Wichtige Nachfrage" in t for t in lbl_texts)

    app.destroy()
