"""Tests for CasePrintDialog build_html_content, auto_print toggle, and report saving."""

from pathlib import Path
import customtkinter as ctk
import pytest
from config import AppConfig
from enums import Actor, BoardColumn
from models.case import Case, CaseCustomer, Classification, TimelineEntry, WorkflowStatus
from services.attachment_service import AttachmentService
from ui.dialogs.case_print_dialog import CasePrintDialog


def test_case_print_build_html_content(tmp_path: Path):
    """Verify build_html_content supports both auto_print mode and clean static file saving mode."""
    config = AppConfig(workspace_dir=tmp_path)
    att_service = AttachmentService(config)

    case = Case(
        case_id="T-2026-PRINT-OPT",
        customer=CaseCustomer(customer_id="K-55", practice_name="Praxis Dr. Med. Test", is_vip=True),
        classification=Classification(title="Druckoptionen Testfall", calculated_score=92.0),
        workflow_status=WorkflowStatus(board_column=BoardColumn.ACTION_REQUIRED, current_actor=Actor.SUPPORT),
        created_by="DaniBani",
        form_data={"Modul": "Abrechnung", "Betrag": "120,50 €"},
        timeline=[
            TimelineEntry(timestamp="2026-08-25T11:00:00", author="DaniBani", note="Kunde hat Korrekturdatei geschickt."),
        ],
    )

    app = ctk.CTk()
    app.withdraw()

    dialog = CasePrintDialog(app, case, attachment_service=att_service)

    # HTML with auto_print for direct browser printing
    html_print = dialog.build_html_content(auto_print=True)
    assert "window.print()" in html_print
    assert "T-2026-PRINT-OPT" in html_print
    assert "Praxis Dr. Med. Test" in html_print
    assert "VIP-Kunde" in html_print

    # HTML without auto_print for static archiving
    html_static = dialog.build_html_content(auto_print=False)
    assert "window.addEventListener('DOMContentLoaded'" not in html_static
    assert "T-2026-PRINT-OPT" in html_static

    # Test generate_and_open_html and generate_and_print_pdf
    opened_uris = []
    import webbrowser
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(webbrowser, "open", lambda uri: opened_uris.append(uri))

    dialog.generate_and_open_html()
    assert len(opened_uris) == 1
    assert "Fallbericht_T-2026-PRINT-OPT.html" in opened_uris[0]

    # Recreate dialog for print test
    dialog2 = CasePrintDialog(app, case, attachment_service=att_service)
    dialog2.generate_and_print_pdf()
    assert len(opened_uris) == 2
    assert "Fallbericht_T-2026-PRINT-OPT_Print.html" in opened_uris[1]

    monkeypatch.undo()
    app.destroy()


def test_compact_report_layout_features(tmp_path: Path):
    """Verify that generate_case_report_html includes @page A4 rule, top-grid, and fields-grid."""
    from services.case_report_builder import generate_case_report_html

    case = Case(
        case_id="T-COMPACT-01",
        customer=CaseCustomer(customer_id="K-100", practice_name="Gemeinschaftspraxis Nord"),
        classification=Classification(title="Kompakt-Test", calculated_score=75.0),
        workflow_status=WorkflowStatus(board_column=BoardColumn.ACTION_REQUIRED, current_actor=Actor.SUPPORT),
        created_by="Agent1",
        form_data={
            "Kurzfeld": "Wert1",
            "Langfeld": "Dies ist ein sehr langer Text, der mehr als achtzig Zeichen umfasst und deshalb im 2-Spalten-Raster über die gesamte Breite angezeigt werden soll.",
        },
        timeline=[
            TimelineEntry(timestamp="2026-08-25T14:00:00", author="Agent1", channel="TELEPHONE", note="Erster Anruf"),
        ],
    )

    # 1. Test with customer data -> top-grid should be present
    html_with_cust = generate_case_report_html(case, include_customer=True, include_fields=True)
    assert "@page { size: A4 portrait; margin: 8mm 10mm; }" in html_with_cust
    assert "class='top-grid'" in html_with_cust
    assert "class='top-col'" in html_with_cust
    assert "Gemeinschaftspraxis Nord" in html_with_cust
    assert "class='fields-grid'" in html_with_cust
    assert "class='field-card'" in html_with_cust
    assert "class='field-card full-width'" in html_with_cust
    assert "class='timeline-list'" in html_with_cust
    assert "class='entry'" in html_with_cust

    # 2. Test without customer data -> top-grid should NOT be present, standalone metadata table
    html_no_cust = generate_case_report_html(case, include_customer=False, include_fields=True)
    assert "class='top-grid'" not in html_no_cust
    assert "Gemeinschaftspraxis Nord" not in html_no_cust
    assert "T-COMPACT-01" in html_no_cust
    assert "class='fields-grid'" in html_no_cust


def test_export_dialog_build_html_content(tmp_path: Path):
    """Verify that ExportDialog print tab builds the same compact report."""
    from ui.dialogs.export_dialog import ExportDialog

    case = Case(
        case_id="T-EXPORT-COMPACT",
        customer=CaseCustomer(customer_id="K-200", practice_name="Test Praxis"),
        classification=Classification(title="Export Compact"),
        workflow_status=WorkflowStatus(board_column=BoardColumn.ACTION_REQUIRED, current_actor=Actor.SUPPORT),
    )

    from services.export_service import ExportService

    app = ctk.CTk()
    app.withdraw()

    dialog = ExportDialog(
        app,
        case,
        templates=[],
        schemas=[],
        export_service=ExportService(),
        on_case_updated=lambda c: None,
    )
    html = dialog.build_html_content(auto_print=False)

    assert "@page { size: A4 portrait; margin: 8mm 10mm; }" in html
    assert "class='top-grid'" in html
    assert "Test Praxis" in html
    assert "T-EXPORT-COMPACT" in html

    dialog.destroy()
    app.destroy()

