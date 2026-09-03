"""Comprehensive End-to-End (E2E) Multilingual Workflows Test Suite.

Simulates real-world user workflows across German (de), English (en), and Swedish (sv):
- Scenario 1: Case intake, triage, deadline tracking & dynamic language switching
- Scenario 2: Kanban board column transitions, actor handovers & urgency badges
- Scenario 3: Customer management & Cobra CRM import workflows
- Scenario 4: Export engine (HTML, Markdown, Plain Text, .ics) with localized templates
- Scenario 5: Support snippets & placeholder interpolation across locales
- Scenario 6: User profile settings and language persistence on reload
"""

import json
from pathlib import Path
from typing import Any
import pytest
import customtkinter as ctk

from config import AppConfig
from enums import (
    Actor,
    UrgencyLevel,
    Channel,
    BoardColumn,
    TargetType,
    get_actor_display,
    get_channel_display,
    get_layout_display,
    get_board_column_display,
    ACTOR_DISPLAY,
    CHANNEL_DISPLAY,
)
from constants import (
    DIALOG_TITLES,
    UI_BUTTON_TEXTS,
    STATUS_MESSAGES,
)
from models.case import Case, CaseCustomer, Classification, WorkflowStatus, TimelineEntry
from models.customer import Customer, Contact
from models.profile import UserProfile, UISettings, UserInfo
from models.snippet import Snippet
from models.schema import QuestionSchema, SchemaField, FieldType
from models.export_template import ExportTemplate
from services.i18n_service import I18nService, get_i18n, tr
from services.storage_service import StorageService
from services.scoring_service import ScoringService
from services.export_service import ExportService
from services.customer_service import CustomerService
from services.snippet_service import SnippetService
from services.seed_service import SeedService
from services.calendar_email_service import CalendarEmailService


@pytest.fixture(autouse=True)
def reset_i18n_language():
    """Ensure every test starts and ends with German ('de') active."""
    i18n = get_i18n()
    i18n.current_language = "de"
    yield
    i18n.current_language = "de"


@pytest.fixture
def headless_root():
    """Provide a headless Tk/CustomTkinter root window."""
    root = ctk.CTk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass


# ============================================================================
# Tier 4: Real-World Multilingual Workflow Scenarios
# ============================================================================

class TestE2EMultilingualWorkflows:
    """Test full multi-step user workflows across German, English, and Swedish."""

    def test_scenario_1_case_intake_triage_and_language_switch_in_swedish(self, tmp_path: Path):
        """Scenario 1: Complete case intake in Swedish, set deadlines, and switch language mid-workflow."""
        config = AppConfig(workspace_dir=tmp_path, username="agent_sv")
        storage = StorageService(config)
        scoring = ScoringService(storage.load_profile().scoring_matrix)

        # 1. Set language to Swedish
        get_i18n().current_language = "sv"
        assert get_i18n().current_language == "sv"
        assert DIALOG_TITLES["new_case"] == "Skapa nytt supportärende"

        # 2. Intake new case from Swedish customer
        new_case = Case(
            case_id="T-2026-SE-001",
            created_at="2026-09-02T10:00:00",
            updated_at="2026-09-02T10:00:00",
            customer=CaseCustomer(
                customer_id="KUND-8801",
                practice_name="Läkarhuset Stockholm",
                contact_person="Dr. Astrid Lind",
                email="kontakt@lakarhuset-sthlm.se",
                phone="08-123456",
                is_vip=True,
            ),
            classification=Classification(
                schema_id="standard_support",
                title="Databaslåsning vid kvartalsfakturering",
                urgency_level=UrgencyLevel.RED,
                tags=["Databas", "Fakturering"],
            ),
            workflow_status=WorkflowStatus(
                current_actor=Actor.SUPPORT,
                followup_at="2026-09-03T09:00:00",
                followup_note="Ring upp Dr. Astrid Lind för fjärrsupport",
                is_completed=False,
            ),
            form_data={
                "version": "v4.12",
                "database_engine": "PostgreSQL",
                "affected_users": 15,
            },
        )

        # 3. Calculate score & save case
        scoring.update_case_scoring(new_case)
        assert new_case.classification.calculated_score > 0

        storage.save_cases([new_case], sync=True)
        loaded_cases = storage.load_cases()
        assert len(loaded_cases) == 1
        assert loaded_cases[0].case_id == "T-2026-SE-001"
        assert loaded_cases[0].customer.practice_name == "Läkarhuset Stockholm"

        # 4. Add Swedish timeline entry
        timeline_entry = TimelineEntry(
            timestamp="2026-09-02T10:30:00",
            author="agent_sv",
            channel=Channel.PHONE_INBOUND,
            note="Tog emot felrapport per telefon. Begärde loggfiler via e-post.",
        )
        new_case.timeline.append(timeline_entry)
        storage.save_cases([new_case], sync=True)

        # 5. Switch language to English mid-workflow
        get_i18n().current_language = "en"
        assert DIALOG_TITLES["new_case"] == "Create New Support Case"
        assert "Support" in get_actor_display(new_case.workflow_status.current_actor)
        assert "Phone" in get_channel_display(timeline_entry.channel)

        # 6. Switch language to German
        get_i18n().current_language = "de"
        assert DIALOG_TITLES["new_case"] == "Neuen Support-Fall anlegen"
        assert "Support" in get_actor_display(new_case.workflow_status.current_actor)
        assert "Telefon" in get_channel_display(timeline_entry.channel)

        # 7. Complete the case
        new_case.workflow_status.is_completed = True
        storage.save_cases([new_case], sync=True)
        completed_cases = storage.load_cases()
        assert completed_cases[0].workflow_status.is_completed is True

    def test_scenario_2_board_view_kanban_transitions_across_locales(self, tmp_path: Path):
        """Scenario 2: Kanban board column categorisation, actor changes, and localized headers."""
        config = AppConfig(workspace_dir=tmp_path, username="board_tester")
        storage = StorageService(config)

        # Create 3 cases in different states
        case_support = Case(
            case_id="T-BOARD-1",
            classification=Classification(title="Support Task"),
            workflow_status=WorkflowStatus(current_actor=Actor.SUPPORT, is_completed=False),
        )
        case_dev = Case(
            case_id="T-BOARD-2",
            classification=Classification(title="Dev Bugfix"),
            workflow_status=WorkflowStatus(current_actor=Actor.DEVELOPMENT, is_completed=False),
        )
        case_done = Case(
            case_id="T-BOARD-3",
            classification=Classification(title="Resolved Ticket"),
            workflow_status=WorkflowStatus(current_actor=Actor.SUPPORT, is_completed=True),
        )

        storage.save_cases([case_support, case_dev, case_done], sync=True)
        all_cases = storage.load_cases()

        # Categorize by column logic
        support_cases = [c for c in all_cases if c.workflow_status.current_actor == Actor.SUPPORT and not c.workflow_status.is_completed]
        dev_cases = [c for c in all_cases if c.workflow_status.current_actor == Actor.DEVELOPMENT and not c.workflow_status.is_completed]
        done_cases = [c for c in all_cases if c.workflow_status.is_completed]

        assert len(support_cases) == 1
        assert len(dev_cases) == 1
        assert len(done_cases) == 1

        # Test German board labels
        get_i18n().current_language = "de"
        assert tr("board.col_dev", count=1) == "💻 Entwickler (1)"
        assert tr("board.col_completed") == "✓ Erledigte Fälle"

        # Test English board labels
        get_i18n().current_language = "en"
        assert tr("board.col_dev", count=1) == "💻 Developer (1)"
        assert tr("board.col_completed") == "✓ Completed Cases"

        # Test Swedish board labels
        get_i18n().current_language = "sv"
        assert tr("board.col_dev", count=1) == "💻 Utvecklare (1)"
        assert tr("board.col_completed") == "✓ Avslutade ärenden"

        # Transition case from Support -> Dev
        case_support.workflow_status.current_actor = Actor.DEVELOPMENT
        storage.save_cases([case_support, case_dev, case_done], sync=True)

        updated_cases = storage.load_cases()
        new_dev_cases = [c for c in updated_cases if c.workflow_status.current_actor == Actor.DEVELOPMENT and not c.workflow_status.is_completed]
        assert len(new_dev_cases) == 2

    def test_scenario_3_customer_management_and_cobra_import_in_english(self, tmp_path: Path):
        """Scenario 3: Practice management, search/filtering, and Cobra CRM import in English."""
        config = AppConfig(workspace_dir=tmp_path)
        storage = StorageService(config)
        cust_service = CustomerService(storage)

        get_i18n().current_language = "en"

        # 1. Create practice in English environment
        cust = Customer(
            customer_id="PRAC-901",
            practice_name="Central Health Clinic London",
            city="London",
            street="Oxford Street 45",
            phone_main="+44 20 7946 0123",
            email_address="info@centralhealth.co.uk",
            contacts=[
                Contact(name="Dr. James Wilson", role="Senior Doctor", phone="+44 20 7946 0124"),
                Contact(name="Sarah Jenkins", role="Office Manager", phone="+44 20 7946 0125"),
            ],
            is_vip=True,
        )
        cust_service.save_customer(cust)

        # 2. Search customer by city and doctor name
        results_city = cust_service.search_customers("London")
        assert len(results_city) == 1
        assert results_city[0].practice_name == "Central Health Clinic London"

        results_doctor = cust_service.search_customers("Wilson")
        assert len(results_doctor) == 1

        # 3. Simulate Cobra CRM CSV import line parsing
        cobra_csv_content = (
            "Name;Ort;Strasse;Telefon;Email;Ansprechpartner\n"
            "Mayfair Medical;London;Mayfair Place 10;020-555-0100;reception@mayfair.co.uk;Dr. Oliver Green\n"
            "Cambridge Care Center;Cambridge;King Street 5;01223-555-0200;care@cambridge.co.uk;Nurse Emily\n"
        )
        csv_file = tmp_path / "cobra_export.csv"
        csv_file.write_text(cobra_csv_content, encoding="utf-8")

        # Parse CSV lines and import
        lines = csv_file.read_text(encoding="utf-8").splitlines()
        imported_count = 0
        for line in lines[1:]:
            parts = line.split(";")
            if len(parts) >= 6:
                c = Customer(
                    customer_id=f"COBRA-{imported_count+1}",
                    practice_name=parts[0],
                    city=parts[1],
                    street=parts[2],
                    phone_main=parts[3],
                    email_address=parts[4],
                    contacts=[Contact(name=parts[5], role="Contact")],
                )
                cust_service.save_customer(c)
                imported_count += 1

        assert imported_count == 2
        all_customers = cust_service.get_all_customers()
        assert len(all_customers) == 3

        # Feedback toast in English
        assert "saved" in STATUS_MESSAGES["customer_saved"]

    def test_scenario_4_export_engine_and_calendar_in_swedish(self, tmp_path: Path):
        """Scenario 4: Export case report to HTML/Markdown and create .ics event in Swedish."""
        config = AppConfig(workspace_dir=tmp_path)
        storage = StorageService(config)
        export_service = ExportService(storage)
        cal_service = CalendarEmailService(tmp_path)

        get_i18n().current_language = "sv"

        # Create sample case
        case = Case(
            case_id="T-2026-EXP-SV",
            created_at="2026-09-02T14:00:00",
            updated_at="2026-09-02T15:30:00",
            customer=CaseCustomer(
                customer_id="KD-770",
                practice_name="Göteborgs Vårdcentral",
                contact_person="Dr. Sven Nilsson",
                phone="031-7778899",
                email="info@gbg-vard.se",
                is_vip=True,
            ),
            classification=Classification(
                schema_id="standard_support",
                title="Integrationsproblem med laboratorieprogram",
                urgency_level=UrgencyLevel.RED,
                calculated_score=95.0,
                tags=["HL7", "Laboratorium"],
            ),
            workflow_status=WorkflowStatus(
                current_actor=Actor.DEVELOPMENT,
                followup_at="2026-09-04T11:00:00",
                followup_note="Genomför gemensam felsökning med utvecklingsteamet",
                is_completed=False,
            ),
            timeline=[
                TimelineEntry(
                    timestamp="2026-09-02T14:15:00",
                    author="support_sv",
                    channel=Channel.PHONE_INBOUND,
                    note="Första samtalet med Dr. Nilsson. Felet bekräftat.",
                ),
            ],
        )

        # 1. Export using Swedish Markdown template
        template_md_sv = ExportTemplate(
            template_id="TPL-SV-MD",
            display_name="Svensk Ärenderapport (Markdown)",
            target_type=TargetType.CLIPBOARD_TEXT,
            template_string=(
                "# Ärenderapport: {{ case.case_id }}\n"
                "**Mottagning:** {{ customer.practice_name }} (Kontakt: {{ customer.contact_person }})\n"
                "**Titel:** {{ classification.title }}\n"
                "**Status:** {{ workflow_status.current_actor }}\n"
            ),
        )
        success, missing, md_output = export_service.render_template(case, template_md_sv)
        assert success is True
        assert case.case_id in md_output
        assert "Göteborgs Vårdcentral" in md_output
        assert "Dr. Sven Nilsson" in md_output

        # 2. Export using Swedish HTML template
        template_html_sv = ExportTemplate(
            template_id="TPL-SV-HTML",
            display_name="Svensk Ärenderapport (HTML)",
            target_type=TargetType.FILE_EXPORT,
            template_string=(
                "<!DOCTYPE html><html><head><title>{{ classification.title }}</title></head>"
                "<body><h1>Supportärende {{ case.case_id }}</h1>"
                "<p>Kund: {{ customer.practice_name }}</p></body></html>"
            ),
        )
        success_html, missing_html, html_output = export_service.render_template(case, template_html_sv)
        assert success_html is True
        assert case.case_id in html_output
        assert "Göteborgs Vårdcentral" in html_output

        # 3. Create .ics calendar invitation
        ics_path = cal_service.generate_ics_file(case=case, target_dir=tmp_path)
        assert ics_path is not None
        assert ics_path.exists()
        ics_text = ics_path.read_text(encoding="utf-8")
        assert "BEGIN:VCALENDAR" in ics_text
        assert "BEGIN:VEVENT" in ics_text
        assert f"Fall {case.case_id}" in ics_text or case.case_id in ics_text
        assert "Göteborgs Vårdcentral" in ics_text

    def test_scenario_5_support_snippets_and_placeholders_in_english(self, tmp_path: Path):
        """Scenario 5: Support snippets management and template placeholder resolution in English."""
        config = AppConfig(workspace_dir=tmp_path)
        storage = StorageService(config)
        snippet_service = SnippetService(tmp_path)

        get_i18n().current_language = "en"

        # Seed snippets
        seed_service = SeedService(storage)
        seed_service.run_seed(force=True)

        snippets = snippet_service.load_snippets()
        assert len(snippets) >= 1

        # Create custom English support snippet with format placeholders
        custom_snippet = Snippet(
            snippet_id="SNIP-ENG-01",
            title="Database Backup Request",
            shortcut="#reqdump",
            category="Database Support",
            content=(
                "Dear {contact_person},\n\n"
                "Thank you for contacting our support team regarding ticket {case_id}.\n"
                "To resolve the issue for {practice_name}, please send us the latest database backup.\n\n"
                "Best regards,\n{agent_name}"
            ),
            tags=["database", "backup", "customer_request"],
        )
        snippet_service.add_or_update_snippet(custom_snippet)

        # Resolve snippet placeholders for a test case
        sample_case = Case(
            case_id="T-2026-ENG-44",
            customer=CaseCustomer(practice_name="Oxford Medical Practice", contact_person="Dr. Emma Watson"),
            classification=Classification(title="Corrupt SQL Database Table"),
        )

        populated_text = custom_snippet.content.format(
            contact_person=sample_case.customer.contact_person,
            case_id=sample_case.case_id,
            practice_name=sample_case.customer.practice_name,
            agent_name="Support Specialist",
        )

        assert "Dear Dr. Emma Watson," in populated_text
        assert "ticket T-2026-ENG-44" in populated_text
        assert "Oxford Medical Practice" in populated_text
        assert "Best regards,\nSupport Specialist" in populated_text

    def test_scenario_6_user_profile_persistence_and_reinstantiation(self, tmp_path: Path):
        """Scenario 6: Set language in UserProfile settings, save to disk, and verify reload."""
        config = AppConfig(workspace_dir=tmp_path, username="multilingual_user")
        storage = StorageService(config)

        # 1. Initial profile default is German
        profile = storage.load_profile()
        assert profile.ui_settings.language in ("de", "")

        # 2. Update language to Swedish and save synchronously
        profile.ui_settings.language = "sv"
        profile.user.name = "Sven Svensson"
        storage.save_profile(profile, sync=True)

        # 3. Create brand new storage service instance (simulating app restart)
        new_storage = StorageService(config)
        reloaded_profile = new_storage.load_profile(use_cache=False)

        assert reloaded_profile.ui_settings.language == "sv"
        assert reloaded_profile.user.name == "Sven Svensson"

        # 4. Update language to English and save
        reloaded_profile.ui_settings.language = "en"
        new_storage.save_profile(reloaded_profile, sync=True)

        third_storage = StorageService(config)
        third_profile = third_storage.load_profile(use_cache=False)
        assert third_profile.ui_settings.language == "en"
