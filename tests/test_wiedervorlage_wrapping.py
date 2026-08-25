"""Unit and integration tests for Wiedervorlage 2-line text wrapping, truncation, and hover tooltip behavior."""

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
    """Test CockpitView followup label text wrapping, 2-line capping, and tooltip resolution."""
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
    assert not cockpit._wiedervorlage_is_truncated
    assert cockpit._get_wiedervorlage_tooltip_text() == ""

    # 2. Case with short follow-up (fits without truncation)
    case_short_fw = Case(
        case_id="F-101",
        customer=CaseCustomer(customer_id="K-2", practice_name="Praxis B", contact_person="Dr. B"),
        classification=Classification(title="Test Kurzes Followup"),
        workflow_status=WorkflowStatus(
            current_actor=Actor.SUPPORT,
            followup_at="2026-08-25T14:00:00",
            followup_note="Kurz",
        ),
    )
    cockpit.on_select_case_from_list(case_short_fw)
    assert "🔔 Wiedervorlage:" in cockpit._wiedervorlage_full_text
    assert "Kurz" in cockpit._wiedervorlage_full_text
    # When not truncated, tooltip returns empty string
    assert cockpit._get_wiedervorlage_tooltip_text() == ""

    # 3. Case with very long follow-up note (exceeds 2 lines)
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
    # Simulate narrow container width to test wrapping and truncation
    cockpit.info_left_frame.winfo_width = lambda: 280  # type: ignore
    cockpit.on_select_case_from_list(case_long_fw)

    assert cockpit._wiedervorlage_is_truncated
    lines = cockpit.wiedervorlage_label.cget("text").splitlines()
    assert len(lines) <= 2
    assert lines[-1].endswith("...")
    # Tooltip must return the complete full text
    full_tt = cockpit._get_wiedervorlage_tooltip_text()
    assert very_long_note in full_tt
    assert full_tt == cockpit._wiedervorlage_full_text

    app.destroy()
