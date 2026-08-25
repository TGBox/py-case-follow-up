"""Tests for UI appearance modes (Light & Dark Theme) consistency and contrast support."""

from pathlib import Path
import customtkinter as ctk
import pytest
from config import AppConfig
from enums import Actor, UrgencyLevel
from models.case import Case, CaseCustomer, Classification, WorkflowStatus
from services.attachment_service import AttachmentService
from services.calendar_email_service import CalendarEmailService
from services.scoring_service import ScoringService
from services.snippet_service import SnippetService
from services.storage_service import StorageService
from services.wiki_sync_service import WikiSyncService
from ui.dialogs.calendar_export_dialog import CalendarExportDialog
from ui.dialogs.case_print_dialog import CasePrintDialog
from ui.dialogs.email_draft_dialog import EmailDraftDialog
from ui.dialogs.help_dialog import HelpDialog
from ui.views.cockpit_view import CockpitView
from ui.widgets.case_list_widget import CaseListWidget
from ui.widgets.date_picker import CalendarDialog
from ui.widgets.toast_notification import ToastNotification


def test_ui_components_in_light_and_dark_mode(tmp_path: Path):
    """Verify core UI components, views, and dialogs instantiate cleanly in both Light and Dark appearance modes."""
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)
    scoring_svc = ScoringService()
    att_svc = AttachmentService(config)
    wiki_svc = WikiSyncService(config)
    cal_svc = CalendarEmailService(config)
    snippet_svc = SnippetService(tmp_path)

    sample_case = Case(
        case_id="T-THEME-01",
        customer=CaseCustomer(customer_id="K-77", practice_name="Praxis Theme Test", is_vip=True),
        classification=Classification(title="Theme Switch Test", urgency_level=UrgencyLevel.YELLOW),
        workflow_status=WorkflowStatus(current_actor=Actor.SUPPORT, followup_at="2026-08-26T10:00:00"),
    )

    for mode in ("Dark", "Light"):
        ctk.set_appearance_mode(mode)

        app = ctk.CTk()
        app.withdraw()

        # 1. CockpitView
        cockpit = CockpitView(
            app,
            author_name="DaniBani",
            scoring_service=scoring_svc,
            attachment_service=att_svc,
            wiki_service=wiki_svc,
            app_config=config,
            storage_service=storage,
        )
        cockpit.on_select_case_from_list(sample_case)
        cockpit.update_idletasks()

        # 2. CaseListWidget
        case_list = CaseListWidget(app, on_case_selected=lambda c: None, on_search_changed=lambda s: None)
        case_list.set_cases([sample_case])
        case_list.update_idletasks()

        # 3. CalendarDialog (with time steppers)
        cal_diag = CalendarDialog(app, initial_date="2026-08-25T14:30:00", include_time=True)
        cal_diag.update_idletasks()
        cal_diag.destroy()

        # 4. EmailDraftDialog
        email_diag = EmailDraftDialog(app, sample_case, calendar_email_service=cal_svc, user_name="DaniBani", snippet_service=snippet_svc)
        email_diag.update_idletasks()
        email_diag.destroy()

        # 5. CalendarExportDialog
        cal_export = CalendarExportDialog(app, sample_case, calendar_email_service=cal_svc)
        cal_export.update_idletasks()
        cal_export.destroy()

        # 6. CasePrintDialog
        print_diag = CasePrintDialog(app, sample_case, attachment_service=att_svc)
        print_diag.update_idletasks()
        print_diag.destroy()

        # 7. HelpDialog
        help_diag = HelpDialog(app)
        help_diag.update_idletasks()
        help_diag.destroy()

        # 8. ToastNotification
        toast = ToastNotification(app, title="Theme Test", message="Modus: " + mode, on_open=lambda: None)
        toast.update_idletasks()
        toast.safe_destroy()

        cockpit.destroy()
        case_list.destroy()
        app.destroy()

    # Reset appearance mode
    ctk.set_appearance_mode("Dark")
