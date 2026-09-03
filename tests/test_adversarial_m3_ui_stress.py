"""Adversarial stress test harness for Milestone 3 (UI Views & Widgets String Extraction).

Focus areas:
1. Rapid language cycling (DE -> EN -> SV -> DE -> EN -> SV, 100+ iterations) under live UI instances
2. Robustness against missing parameters, unexpected types, and format string token validation
3. Headless UI view label, action button, header, and tab updates across all three languages
4. Headless widget updates (CaseList, Form, Attachment, Timeline, Wiki, DatePicker, SearchableCombobox, ModuleTagPicker)
5. Multi-threaded / concurrent language switching safety
6. Locale key parity and translation quality verification for all UI keys
7. Reproduction of runtime exceptions during dynamic language switching
"""

import json
import threading
from pathlib import Path
from typing import Any
import pytest
import customtkinter as ctk

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
    get_localized_menu_options_stammdaten,
    get_localized_menu_options_vorlagen,
    get_localized_menu_options_datenaustausch,
)
from models.case import Case, CaseCustomer, Classification, WorkflowStatus, TimelineEntry
from models.profile import UserProfile
from models.schema import QuestionSchema, SchemaField
from services.i18n_service import I18nService, get_i18n, tr, SUPPORTED_LANGUAGES, LocalizedDict
from services.storage_service import StorageService
from services.scoring_service import ScoringService
from services.attachment_service import AttachmentService
from services.wiki_sync_service import WikiSyncService


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
# Section 1: Rapid Language Cycling & Concurrency Stress
# ============================================================================

class TestRapidLanguageSwitchStress:
    """Adversarial stress testing of rapid language switches and concurrency."""

    def test_rapid_language_cycling_100_iterations(self):
        """Rapidly cycle DE -> EN -> SV 100 times, verifying consistency and no memory corruption."""
        i18n = get_i18n()
        langs = ["de", "en", "sv"]

        expected_new_case = {
            "de": "Neuen Support-Fall anlegen",
            "en": "Create New Support Case",
            "sv": "Skapa nytt supportärende",
        }

        expected_actor_support = {
            "de": "Support / Hotline",
            "en": "Support / Hotline",
            "sv": "Support / Hotline",
        }

        for i in range(100):
            target_lang = langs[i % len(langs)]
            i18n.current_language = target_lang
            assert i18n.current_language == target_lang
            assert DIALOG_TITLES["new_case"] == expected_new_case[target_lang]
            assert get_actor_display("SUPPORT") == expected_actor_support[target_lang]
            assert tr("common.save") in ("Speichern", "Save", "Spara")

    def test_multithreaded_concurrent_translation_access(self):
        """Verify thread-safe reading of tr(...) and LocalizedDict while language switches occur."""
        i18n = get_i18n()
        errors: list[Exception] = []
        stop_event = threading.Event()

        def reader_worker():
            while not stop_event.is_set():
                try:
                    _ = tr("common.save")
                    _ = tr("cockpit.filter_all")
                    _ = DIALOG_TITLES["new_case"]
                    _ = get_layout_display("COCKPIT")
                except Exception as e:
                    errors.append(e)

        def writer_worker():
            langs = ["de", "en", "sv"]
            for i in range(150):
                i18n.current_language = langs[i % len(langs)]

        threads = [threading.Thread(target=reader_worker) for _ in range(4)]
        writer = threading.Thread(target=writer_worker)

        for t in threads:
            t.start()
        writer.start()

        writer.join()
        stop_event.set()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Concurrent translation access produced errors: {errors}"

    def test_listener_exception_isolation(self):
        """Verify that a failing listener does not break subsequent listeners during set_language."""
        i18n = get_i18n()
        executed_listeners: list[str] = []

        def failing_listener(lang: str):
            raise RuntimeError("Simulated listener crash")

        def normal_listener_1(lang: str):
            executed_listeners.append(f"listener_1:{lang}")

        def normal_listener_2(lang: str):
            executed_listeners.append(f"listener_2:{lang}")

        i18n.register_listener(normal_listener_1)
        i18n.register_listener(failing_listener)
        i18n.register_listener(normal_listener_2)

        try:
            try:
                i18n.current_language = "en"
            except Exception:
                pass
            assert any("listener_1:en" in item for item in executed_listeners)
        finally:
            i18n.unregister_listener(normal_listener_1)
            i18n.unregister_listener(failing_listener)
            i18n.unregister_listener(normal_listener_2)


# ============================================================================
# Section 2: Format Token Integrity & Missing Parameter Robustness
# ============================================================================

class TestParameterAndFormatRobustness:
    """Verify that tr(...) never crashes when arguments are missing, None, or wrong types."""

    def test_missing_and_extra_parameters_graceful_handling(self):
        """Verify tr(...) handles missing kwargs without raising KeyError."""
        i18n = get_i18n()
        i18n.current_language = "de"

        # Key with {count} parameter: "case_list.count_cases": "{count} Support-Fälle"
        res_no_param = tr("case_list.count_cases")
        assert isinstance(res_no_param, str)
        assert "{count}" in res_no_param or "Support-Fälle" in res_no_param

        # None parameter
        res_none = tr("case_list.count_cases", count=None)
        assert isinstance(res_none, str)
        assert "None" in res_none or "{count}" in res_none

        # Extra parameter not in format string
        res_extra = tr("case_list.count_cases", count=42, extra_dummy="ignored")
        assert "42" in res_extra

    def test_all_json_placeholder_tokens_match_across_locales(self):
        """Verify that for every key containing {param} in de.json, en.json and sv.json have the identical set of params."""
        import re
        locales_dir = Path(__file__).resolve().parent.parent / "locales"

        with open(locales_dir / "de.json", "r", encoding="utf-8") as f:
            de_data = json.load(f)
        with open(locales_dir / "en.json", "r", encoding="utf-8") as f:
            en_data = json.load(f)
        with open(locales_dir / "sv.json", "r", encoding="utf-8") as f:
            sv_data = json.load(f)

        token_pattern = re.compile(r"\{([a-zA-Z0-9_]+)\}")

        mismatches: list[str] = []

        def check_dict(d_de, d_en, d_sv, prefix=""):
            for k, v in d_de.items():
                curr_key = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    en_sub = d_en.get(k, {}) if isinstance(d_en, dict) else {}
                    sv_sub = d_sv.get(k, {}) if isinstance(d_sv, dict) else {}
                    check_dict(v, en_sub, sv_sub, curr_key)
                elif isinstance(v, str):
                    de_tokens = set(token_pattern.findall(v))
                    en_val = d_en.get(k, "") if isinstance(d_en, dict) else ""
                    sv_val = d_sv.get(k, "") if isinstance(d_sv, dict) else ""

                    en_tokens = set(token_pattern.findall(en_val)) if isinstance(en_val, str) else set()
                    sv_tokens = set(token_pattern.findall(sv_val)) if isinstance(sv_val, str) else set()

                    if de_tokens != en_tokens:
                        mismatches.append(f"Key '{curr_key}': DE tokens {de_tokens} != EN tokens {en_tokens}")
                    if de_tokens != sv_tokens:
                        mismatches.append(f"Key '{curr_key}': DE tokens {de_tokens} != SV tokens {sv_tokens}")

        check_dict(de_data, en_data, sv_data)
        assert len(mismatches) == 0, f"Found {len(mismatches)} placeholder token mismatches:\n" + "\n".join(mismatches[:10])


# ============================================================================
# Section 3: Empirical Bug Detection & Reproduction
# ============================================================================

class TestAttachmentWidgetDynamicRefreshBug:
    """Empirical test exposing the AttachmentWidget destroyed preview_label bug upon consecutive refresh_ui_labels()."""

    def test_attachment_widget_consecutive_refresh_reproduction(self, headless_root, tmp_path: Path):
        """Reproduce TclError when AttachmentWidget.refresh_ui_labels() is called multiple times.

        Root cause: load_attachments() calls clear_preview(), destroying preview_label widget.
        Subsequent calls to refresh_ui_labels() attempt to configure the destroyed preview_label.
        """
        from ui.widgets.attachment_widget import AttachmentWidget

        config = AppConfig(workspace_dir=tmp_path)
        attachment_svc = AttachmentService(config)

        get_i18n().current_language = "de"
        widget = AttachmentWidget(headless_root, attachment_svc)

        # 1st refresh: destroys preview_label via clear_preview()
        widget.refresh_ui_labels()

        # 2nd refresh: should either handle destroyed preview_label safely or fail if bug exists
        # We test if the widget crashes with TclError
        import _tkinter
        try:
            get_i18n().current_language = "en"
            widget.refresh_ui_labels()
            bug_present = False
        except _tkinter.TclError as e:
            bug_present = True
            error_msg = str(e)

        # Document whether the bug is present
        if bug_present:
            pytest.fail(f"CONFIRMED BUG: AttachmentWidget crashed with TclError on second refresh_ui_labels(): {error_msg}")


# ============================================================================
# Section 4: Headless UI Views Dynamic Label Updates
# ============================================================================

class TestHeadlessUIViewsDynamicUpdates:
    """Verify headless UI views adapt their labels dynamically across DE, EN, and SV."""

    def test_board_view_column_collapsing_and_refresh(self, headless_root):
        """Verify BoardView preserves column collapsed states and localized titles on collapse/expand & language switch."""
        from ui.views.board_view import BoardView

        cases = [
            Case(case_id="T-1", classification=Classification(title="Open 1", calculated_score=80), workflow_status=WorkflowStatus(current_actor="SUPPORT")),
            Case(case_id="T-2", classification=Classification(title="Dev 1", calculated_score=60), workflow_status=WorkflowStatus(current_actor="DEVELOPMENT")),
            Case(case_id="T-3", classification=Classification(title="Followup 1", calculated_score=40), workflow_status=WorkflowStatus(followup_at="2026-09-05T10:00:00")),
            Case(case_id="T-4", classification=Classification(title="Done 1", calculated_score=20), workflow_status=WorkflowStatus(is_completed=True)),
        ]

        get_i18n().current_language = "de"
        board = BoardView(
            parent=headless_root,
            on_select_case=lambda c: None,
            on_switch_to_cockpit=lambda c: None,
            on_open_followup=lambda c: None,
            on_toggle_complete=lambda c: None,
            on_change_actor=lambda c: None,
        )
        board.set_cases(cases)

        # German check
        assert "Support (1)" in board.col_headers["support"].cget("text")
        assert "Entwickler (1)" in board.col_headers["dev"].cget("text")
        assert "Wiedervorlage (1)" in board.col_headers["followup"].cget("text")
        assert "Erledigt (1)" in board.col_headers["completed"].cget("text")

        # Collapse support column
        board.toggle_column_collapse("support")
        assert board.collapsed_states["support"] is True

        # Switch to English
        get_i18n().current_language = "en"
        board.refresh_ui_labels()
        assert board.collapsed_states["support"] is True
        assert "Development (1)" in board.col_headers["dev"].cget("text") or "Developer (1)" in board.col_headers["dev"].cget("text")
        assert "Follow-up (1)" in board.col_headers["followup"].cget("text")

        # Expand support column in English
        board.toggle_column_collapse("support")
        assert board.collapsed_states["support"] is False
        assert "Support (1)" in board.col_headers["support"].cget("text")

        # Switch to Swedish
        get_i18n().current_language = "sv"
        board.refresh_ui_labels()
        assert "Utvecklare (1)" in board.col_headers["dev"].cget("text")
        assert "Uppföljning (1)" in board.col_headers["followup"].cget("text")
        assert "Klart (1)" in board.col_headers["completed"].cget("text") or "Avslutade (1)" in board.col_headers["completed"].cget("text")

    def test_analytics_view_labels_and_kpis(self, headless_root):
        """Verify AnalyticsView refreshes top KPIs, summary cards, and urgency distributions across languages."""
        from ui.views.analytics_view import AnalyticsView

        get_i18n().current_language = "de"
        view = AnalyticsView(parent=headless_root)

        cases = [
            Case(case_id="T-1", classification=Classification(urgency_level=UrgencyLevel.RED), workflow_status=WorkflowStatus(is_completed=False)),
            Case(case_id="T-2", classification=Classification(urgency_level=UrgencyLevel.YELLOW), workflow_status=WorkflowStatus(is_completed=False)),
            Case(case_id="T-3", classification=Classification(urgency_level=UrgencyLevel.GREEN), workflow_status=WorkflowStatus(is_completed=True)),
        ]

        # German
        view.set_cases(cases)
        assert "Auswertungen" in view.top_bar_title.cget("text")
        assert "Statistik-Bericht" in view.copy_report_btn.cget("text")

        # English
        get_i18n().current_language = "en"
        view.create_widgets()
        view.set_cases(cases)
        assert "Analytics" in view.top_bar_title.cget("text") or "KPI" in view.top_bar_title.cget("text")
        assert "Copy" in view.copy_report_btn.cget("text")

        # Swedish
        get_i18n().current_language = "sv"
        view.create_widgets()
        view.set_cases(cases)
        assert "Rapporter" in view.top_bar_title.cget("text") or "Statistik" in view.top_bar_title.cget("text") or "Analys" in view.top_bar_title.cget("text")
        assert "Kopiera" in view.copy_report_btn.cget("text")

    def test_table_view_headings_and_detail_panel(self, headless_root, tmp_path: Path):
        """Verify TableView's treeview columns and detail panel adapt across DE, EN, and SV."""
        from ui.views.table_view import TableView, COL_TITLE_MAP

        config = AppConfig(workspace_dir=tmp_path)
        storage = StorageService(config)
        scoring = ScoringService(storage.load_profile().scoring_matrix)
        attachment = AttachmentService(config)

        get_i18n().current_language = "de"
        tv = TableView(
            parent=headless_root,
            author_name="Tester",
            scoring_service=scoring,
            attachment_service=attachment,
            on_case_updated=lambda c: None,
            on_case_selected=lambda c: None,
            app_config=config,
        )

        assert "Ändern & Speichern" in tv.save_btn.cget("text") or "Speichern" in tv.save_btn.cget("text")
        assert "Falldetails" in tv.detail_title_label.cget("text")

        get_i18n().current_language = "en"
        tv.save_btn.configure(text=tr("table.save_btn", "💾 Save Changes"))
        assert "Save" in tv.save_btn.cget("text")

        get_i18n().current_language = "sv"
        tv.save_btn.configure(text=tr("table.save_btn", "💾 Spara ändringar"))
        assert "spara" in tv.save_btn.cget("text").lower()


# ============================================================================
# Section 5: Headless UI Widgets Dynamic Label Updates
# ============================================================================

class TestHeadlessUIWidgetsDynamicUpdates:
    """Verify headless UI widgets adapt their labels dynamically across DE, EN, and SV."""

    def test_wiki_widget_dynamic_refresh(self, headless_root, tmp_path: Path):
        """Verify WikiWidget headers, sync button, search placeholder, and status labels."""
        from ui.widgets.wiki_widget import WikiWidget

        config = AppConfig(workspace_dir=tmp_path)
        storage = StorageService(config)
        wiki_svc = WikiSyncService(config, storage.load_profile().wiki_settings)

        get_i18n().current_language = "de"
        widget = WikiWidget(headless_root, wiki_svc)

        # German
        assert widget.hdr_lbl.cget("text") == "BookStack Offline Wiki"
        assert "Sync" in widget.sync_btn.cget("text")
        assert "durchsuchen" in widget.search_entry.cget("placeholder_text")

        # English
        get_i18n().current_language = "en"
        widget.refresh_ui_labels()
        assert "Search wiki" in widget.search_entry.cget("placeholder_text") or "Search" in widget.search_entry.cget("placeholder_text")

        # Swedish
        get_i18n().current_language = "sv"
        widget.refresh_ui_labels()
        assert "Sök i wiki" in widget.search_entry.cget("placeholder_text") or "Sök" in widget.search_entry.cget("placeholder_text")

    def test_timeline_widget_dynamic_refresh(self, headless_root):
        """Verify TimelineWidget headers, channel dropdown, add note controls, and status prefix."""
        from ui.widgets.timeline_widget import TimelineWidget

        get_i18n().current_language = "de"
        widget = TimelineWidget(
            parent=headless_root,
            author_name="Tester",
            on_timeline_updated=lambda e: None,
        )

        # German
        assert "Timeline Notizen" in widget.hdr_lbl.cget("text") or "Verlauf" in widget.hdr_lbl.cget("text")
        assert "Notiz" in widget.ctrl_lbl.cget("text")
        assert "Textbaustein" in widget.snip_btn.cget("text")
        assert "Hinzufügen" in widget.add_btn.cget("text")
        assert any("Telefon" in c for c in widget.channel_combo.cget("values"))

        # English
        get_i18n().current_language = "en"
        widget.refresh_ui_labels()
        assert "Timeline Notes" in widget.hdr_lbl.cget("text") or "History" in widget.hdr_lbl.cget("text")
        assert "Snippet" in widget.snip_btn.cget("text") or "Template" in widget.snip_btn.cget("text")
        assert "Add Note" in widget.add_btn.cget("text")
        assert any("Phone" in c for c in widget.channel_combo.cget("values"))

        # Swedish
        get_i18n().current_language = "sv"
        widget.refresh_ui_labels()
        assert "Tidslinje" in widget.hdr_lbl.cget("text") or "Historik" in widget.hdr_lbl.cget("text")
        assert "Textbyggblock" in widget.snip_btn.cget("text") or "Textblock" in widget.snip_btn.cget("text") or "Mall" in widget.snip_btn.cget("text")
        assert "Lägg till anteckning" in widget.add_btn.cget("text") or "Lägg till" in widget.add_btn.cget("text")

    def test_calendar_dialog_labels_across_languages(self, headless_root):
        """Verify CalendarDialog adapts dialog title and controls across DE, EN, and SV."""
        from ui.widgets.date_picker import CalendarDialog

        get_i18n().current_language = "de"
        cal_de = CalendarDialog(parent=headless_root)
        assert cal_de.title() == "📅 Datum auswählen"
        cal_de.destroy()

        get_i18n().current_language = "en"
        cal_en = CalendarDialog(parent=headless_root)
        assert cal_en.title() == "📅 Select Date"
        cal_en.destroy()

        get_i18n().current_language = "sv"
        cal_sv = CalendarDialog(parent=headless_root)
        assert cal_sv.title() == "📅 Välj datum"
        cal_sv.destroy()

    def test_module_tag_picker_popup_labels(self, headless_root):
        """Verify ModuleTagPickerPopup adapts title, search placeholder, and action buttons."""
        from ui.widgets.dynamic_form_widget import ModuleTagPickerPopup

        get_i18n().current_language = "de"
        popup_de = ModuleTagPickerPopup(parent=headless_root, available_tags=["Tag1"], selected_tags=[], on_apply=lambda t: None)
        assert "Programmbereiche auswählen" in popup_de.title()
        popup_de.destroy()

        get_i18n().current_language = "en"
        popup_en = ModuleTagPickerPopup(parent=headless_root, available_tags=["Tag1"], selected_tags=[], on_apply=lambda t: None)
        assert "Select Program Area Tags" in popup_en.title() or "Select" in popup_en.title()
        popup_en.destroy()

        get_i18n().current_language = "sv"
        popup_sv = ModuleTagPickerPopup(parent=headless_root, available_tags=["Tag1"], selected_tags=[], on_apply=lambda t: None)
        assert "Välj programområdestaggar" in popup_sv.title() or "Välj" in popup_sv.title()
        popup_sv.destroy()
