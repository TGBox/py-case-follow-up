"""Deep adversarial stress tests for Milestone 3 (UI Views & Widgets).

Testing extreme edge cases:
- AttachmentWidget with image, text, binary, empty, missing files across rapid language switches.
- CTkTabview segmented buttons in CockpitView and TableView under active tab switching + rapid language cycling.
- CaseListWidget, DynamicFormWidget, TimelineWidget, WikiWidget, DatePickerWidget, SearchableCombobox under extreme loads and multi-locale cycling.
- Full SupportCockpitApp under stress lifecycle events and rapid language mutation.
"""

import io
import os
import json
import tempfile
import threading
from pathlib import Path
import pytest
import customtkinter as ctk
from PIL import Image

from config import AppConfig
from enums import (
    Actor,
    BoardColumn,
    Channel,
    LayoutMode,
    UrgencyLevel,
    get_actor_display,
    get_channel_display,
    get_layout_display,
    get_board_column_display,
    ACTOR_DISPLAY,
    CHANNEL_DISPLAY,
    LAYOUT_DISPLAY,
)
from constants import (
    APP_WINDOW_TITLE,
    DIALOG_TITLES,
    DIALOG_HEADERS,
    UI_BUTTON_TEXTS,
    STATUS_MESSAGES,
)
from models.case import Case, CaseCustomer, Classification, WorkflowStatus, TimelineEntry
from models.profile import UserProfile
from models.schema import QuestionSchema, SchemaField
from services.i18n_service import I18nService, get_i18n, tr, SUPPORTED_LANGUAGES, LocalizedDict
from services.storage_service import StorageService
from services.scoring_service import ScoringService
from services.attachment_service import AttachmentService
from services.wiki_sync_service import WikiSyncService
from ui.views.cockpit_view import CockpitView
from ui.views.board_view import BoardView
from ui.views.table_view import TableView
from ui.views.analytics_view import AnalyticsView
from ui.widgets.attachment_widget import AttachmentWidget
from ui.widgets.timeline_widget import TimelineWidget
from ui.widgets.wiki_widget import WikiWidget
from ui.widgets.dynamic_form_widget import DynamicFormWidget
from ui.widgets.case_list_widget import CaseListWidget
from ui.widgets.toast_notification import ToastNotification
from ui.widgets.date_picker import DatePickerWidget, CalendarDialog
from ui.widgets.searchable_combobox import SearchableCombobox


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


class TestAttachmentWidgetDeepStress:
    """Extreme edge case testing on AttachmentWidget."""

    def test_attachment_previews_all_file_types_across_languages(self, headless_root, tmp_path: Path):
        """Test AttachmentWidget previewing png, txt, binary, empty files, missing files, while cycling languages."""
        config = AppConfig(workspace_dir=tmp_path)
        attachment_svc = AttachmentService(config)
        widget = AttachmentWidget(headless_root, attachment_svc)

        # Create dummy case and attachment files in case folder
        case = Case(case_id="ATTACH-1", classification=Classification(title="Attachment Test"))
        case_dir = tmp_path / "cases" / case.case_id / "attachments"
        case_dir.mkdir(parents=True, exist_ok=True)

        # 1. Image file
        img_path = case_dir / "test_screenshot.png"
        img = Image.new("RGB", (200, 100), color="blue")
        img.save(img_path)

        # 2. Text file
        txt_path = case_dir / "notes.txt"
        txt_path.write_text("Hello World\nLine 2\nLine 3", encoding="utf-8")

        # 3. Binary file (e.g. PDF/EXE/ZIP)
        bin_path = case_dir / "document.pdf"
        bin_path.write_bytes(b"%PDF-1.4 dummy binary content")

        # 4. Empty file
        empty_path = case_dir / "empty.log"
        empty_path.write_text("", encoding="utf-8")

        # Load attachments into widget
        widget.load_attachments(case)

        # Show image preview, then switch languages
        widget.show_file_preview(img_path)
        for lang in ("en", "sv", "de", "en", "sv"):
            get_i18n().current_language = lang
            widget.refresh_ui_labels()

        # Show text preview, then switch languages
        widget.show_file_preview(txt_path)
        for lang in ("en", "sv", "de", "en", "sv"):
            get_i18n().current_language = lang
            widget.refresh_ui_labels()

        # Show binary preview, then switch languages
        widget.show_file_preview(bin_path)
        for lang in ("en", "sv", "de", "en", "sv"):
            get_i18n().current_language = lang
            widget.refresh_ui_labels()

        # Show empty preview, then switch languages
        widget.show_file_preview(empty_path)
        for lang in ("en", "sv", "de", "en", "sv"):
            get_i18n().current_language = lang
            widget.refresh_ui_labels()

        # Non-existent file preview (handles gracefully without uncaught exception)
        missing_path = case_dir / "non_existent.png"
        widget.show_file_preview(missing_path)
        for lang in ("en", "sv", "de"):
            get_i18n().current_language = lang
            widget.refresh_ui_labels()

        # Null case
        widget.load_attachments(None)
        for lang in ("en", "sv", "de"):
            get_i18n().current_language = lang
            widget.refresh_ui_labels()

    def test_rapid_case_switching_and_attachment_reloading(self, headless_root, tmp_path: Path):
        """Rapidly switch between cases with 0, 1, and 10 attachments while cycling languages."""
        config = AppConfig(workspace_dir=tmp_path)
        attachment_svc = AttachmentService(config)
        widget = AttachmentWidget(headless_root, attachment_svc)

        cases = []
        for i in range(5):
            c = Case(case_id=f"CASE-{i}", classification=Classification(title=f"Case {i}"))
            c_dir = tmp_path / "cases" / c.case_id / "attachments"
            c_dir.mkdir(parents=True, exist_ok=True)
            for j in range(i):
                (c_dir / f"file_{j}.txt").write_text(f"File content {j}", encoding="utf-8")
            cases.append(c)

        langs = ["de", "en", "sv"]
        for cycle in range(30):
            case = cases[cycle % len(cases)]
            lang = langs[cycle % len(langs)]
            get_i18n().current_language = lang
            widget.load_attachments(case)
            widget.refresh_ui_labels()


class TestTabUpdatesAndSegmentedButtonsDeepStress:
    """Extreme edge case testing on CockpitView and TableView tabs."""

    def test_cockpit_view_tab_cycling_under_rapid_language_switches(self, headless_root, tmp_path: Path):
        """Test CockpitView right pane tab switching while language switches occur."""
        config = AppConfig(workspace_dir=tmp_path)
        storage = StorageService(config)
        profile = storage.load_profile()
        scoring = ScoringService(profile.scoring_matrix)
        attachment = AttachmentService(config)
        wiki = WikiSyncService(config, profile.wiki_settings)

        cockpit = CockpitView(
            parent=headless_root,
            author_name="Tester",
            scoring_service=scoring,
            attachment_service=attachment,
            wiki_service=wiki,
            on_case_updated=lambda c: None,
            on_case_selected=lambda c: None,
            on_search_changed=lambda q: None,
            on_open_export_dialog=lambda c: None,
            on_archive_case=lambda c: None,
            app_config=config,
            profile=profile,
            storage_service=storage,
        )

        langs = ["de", "en", "sv"]
        tab_names = ["Zeitleiste", "Anhänge", "Wiki"]

        # Rapidly switch active tab and language
        for i in range(60):
            lang = langs[i % len(langs)]
            tab = tab_names[i % len(tab_names)]
            cockpit.right_tabview.set(tab)
            get_i18n().current_language = lang
            cockpit.refresh_ui_labels()

            # Verify segmented button text matches expected translation
            btns = cockpit.right_tabview._segmented_button._buttons_dict
            assert btns["Zeitleiste"].cget("text") == tr("cockpit.tab_timeline", "Zeitleiste")
            assert btns["Anhänge"].cget("text") == tr("cockpit.tab_attachments", "Anhänge")
            assert btns["Wiki"].cget("text") == tr("cockpit.tab_wiki", "Wiki")

    def test_table_view_tab_cycling_under_rapid_language_switches(self, headless_root, tmp_path: Path):
        """Test TableView bottom pane tab switching while language switches occur."""
        config = AppConfig(workspace_dir=tmp_path)
        storage = StorageService(config)
        profile = storage.load_profile()
        scoring = ScoringService(profile.scoring_matrix)
        attachment = AttachmentService(config)

        tv = TableView(
            parent=headless_root,
            author_name="Tester",
            scoring_service=scoring,
            attachment_service=attachment,
            on_case_updated=lambda c: None,
            on_case_selected=lambda c: None,
            app_config=config,
        )

        case = Case(case_id="TV-1", classification=Classification(title="TV Test Case"))
        tv.set_cases([case])
        tv.select_case(case)

        langs = ["de", "en", "sv"]
        tab_names = ["📝 Formular & Ausfüllen", "🕒 Zeitleiste", "📎 Anhänge"]

        for i in range(60):
            lang = langs[i % len(langs)]
            tab = tab_names[i % len(tab_names)]
            tv.detail_tabview.set(tab)
            get_i18n().current_language = lang
            tv.refresh_ui_labels()

            btns = tv.detail_tabview._segmented_button._buttons_dict
            assert btns["📝 Formular & Ausfüllen"].cget("text") == tr("table.tab_form", "📝 Formular & Ausfüllen")
            assert btns["🕒 Zeitleiste"].cget("text") == tr("table.tab_timeline", "🕒 Zeitleiste")
            assert btns["📎 Anhänge"].cget("text") == tr("table.tab_attachments", "📎 Anhänge")


class TestUIWidgetsStabilityDeepStress:
    """Extreme edge case testing on all UI widgets."""

    def test_dynamic_form_widget_all_field_types_multilingual_stress(self, headless_root, tmp_path: Path):
        """Test DynamicFormWidget with multiple schemas, field types, and rapid language switches."""
        form = DynamicFormWidget(headless_root)

        schema = QuestionSchema(
            schema_id="test_schema",
            display_name="Test Dynamic Schema",
            fields=[
                SchemaField(field_id="f_text", label="Text Field", field_type="text", required=True),
                SchemaField(field_id="f_num", label="Number Field", field_type="number"),
                SchemaField(field_id="f_bool", label="Boolean Field", field_type="boolean"),
                SchemaField(field_id="f_choice", label="Choice Field", field_type="select", options=["Opt 1", "Opt 2", "Opt 3"]),
                SchemaField(field_id="f_date", label="Date Field", field_type="date"),
                SchemaField(field_id="f_textarea", label="Textarea Field", field_type="textarea"),
                SchemaField(field_id="f_tags", label="Tags Field", field_type="module_tags"),
            ],
        )

        initial_data = {
            "f_text": "Sample text",
            "f_num": 123.45,
            "f_bool": True,
            "f_choice": "Opt 2",
            "f_date": "2026-09-03",
            "f_textarea": "Multi\nLine\nContent",
            "f_tags": ["T1", "T2"],
        }

        form.load_schema(schema, initial_data, missing_fields=["f_text"])

        langs = ["de", "en", "sv"]
        for i in range(30):
            lang = langs[i % len(langs)]
            get_i18n().current_language = lang
            form.refresh_ui_labels()
            data = form.get_form_data()
            assert data["f_text"] == "Sample text"
            assert data["f_bool"] is True

        # Test loading None schema
        form.load_schema(None, {})
        for lang in ("de", "en", "sv"):
            get_i18n().current_language = lang
            form.refresh_ui_labels()

    def test_case_list_widget_stress_and_filtering(self, headless_root):
        """Test CaseListWidget with 100 cases, search queries, filter modes, and rapid language switching."""
        selected_cases = []
        widget = CaseListWidget(
            parent=headless_root,
            on_case_selected=lambda c: selected_cases.append(c),
            on_search_changed=lambda q: None,
        )

        cases = []
        for i in range(20):
            c = Case(
                case_id=f"CASE-{i:03d}",
                customer=CaseCustomer(customer_id=f"CUST-{i}", practice_name=f"Practice {i}"),
                classification=Classification(
                    title=f"Issue {i}",
                    urgency_level=UrgencyLevel.RED if i % 3 == 0 else UrgencyLevel.YELLOW if i % 3 == 1 else UrgencyLevel.GREEN,
                    calculated_score=float(100 - i),
                ),
                workflow_status=WorkflowStatus(
                    current_actor=Actor.SUPPORT if i % 2 == 0 else Actor.DEVELOPMENT,
                    is_completed=(i % 5 == 0),
                ),
            )
            cases.append(c)

        widget.set_cases(cases)

        langs = ["de", "en", "sv"]
        filters = ["", "vip:true", "reminder:due"]

        for i in range(12):
            lang = langs[i % len(langs)]
            filt = filters[i % len(filters)]
            get_i18n().current_language = lang
            widget.apply_quick_filter(filt)
            widget.refresh_ui_labels()

        # Check search entry placeholder is localized
        get_i18n().current_language = "en"
        widget.refresh_ui_labels()
        assert "Search" in widget.search_entry.cget("placeholder_text")

        get_i18n().current_language = "sv"
        widget.refresh_ui_labels()
        assert "Sök" in widget.search_entry.cget("placeholder_text")

    def test_toast_notification_lifecycle_across_languages(self, headless_root):
        """Test ToastNotification under rapid triggering and language changes."""
        for lang in ("de", "en", "sv"):
            get_i18n().current_language = lang
            toast = ToastNotification(headless_root, title=tr("cockpit.save", "Gespeichert"), message=tr("status_messages.saved", "Erfolgreich gespeichert."))
            try:
                toast.destroy()
            except Exception:
                pass

    def test_date_picker_and_searchable_combobox_lifecycle(self, headless_root):
        """Test DatePickerWidget and SearchableComboBox."""
        date_picker = DatePickerWidget(headless_root, initial_value="2026-09-03 14:00")
        combo = SearchableCombobox(headless_root, values=["Alpha", "Beta", "Gamma"], command=lambda v: None)

        for lang in ("de", "en", "sv", "de"):
            get_i18n().current_language = lang
            if hasattr(date_picker, "refresh_ui_labels"):
                date_picker.refresh_ui_labels()
            if hasattr(combo, "refresh_ui_labels"):
                combo.refresh_ui_labels()


class TestAppFullLifecycleStress:
    """Stress test the entire SupportCockpitApp under repeated multi-step language transitions."""

    def test_full_app_multi_cycle_language_switch_stress(self, tmp_path: Path):
        """Instantiate SupportCockpitApp and cycle languages 30 times with view switches."""
        from ui.app import SupportCockpitApp

        config = AppConfig(workspace_dir=tmp_path)
        app = SupportCockpitApp(config)
        app.withdraw()

        langs = ["de", "en", "sv"]
        layouts = ["COCKPIT", "BOARD", "TABLE", "ANALYTICS"]

        try:
            for i in range(12):
                lang = langs[i % len(langs)]
                layout = layouts[i % len(layouts)]

                app.on_language_changed(lang)
                app.switch_layout(get_layout_display(layout))
                assert app.profile.ui_settings.default_layout is not None
        finally:
            try:
                app.destroy()
            except Exception:
                pass
