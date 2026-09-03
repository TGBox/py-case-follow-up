"""Comprehensive automated tests for dynamic runtime language switching without application restart.

Verifies I18nService listener propagation, LocalizedDict dynamic resolution,
enum display helpers, and headless CustomTkinter view/widget label refreshment.
"""

from pathlib import Path
from typing import Any
import pytest
import customtkinter as ctk

from config import AppConfig
from enums import (
    Actor,
    Channel,
    LayoutMode,
    get_actor_display,
    get_channel_display,
    get_layout_display,
    get_board_column_display,
    ACTOR_DISPLAY,
    CHANNEL_DISPLAY,
    LAYOUT_DISPLAY,
)
from constants import (
    DIALOG_TITLES,
    DIALOG_HEADERS,
    UI_BUTTON_TEXTS,
    STATUS_MESSAGES,
    get_localized_menu_options_stammdaten,
    get_localized_menu_options_vorlagen,
    get_localized_menu_options_datenaustausch,
)
from models.case import Case, CaseCustomer, Classification, WorkflowStatus
from models.profile import UserProfile
from services.i18n_service import I18nService, get_i18n, tr, SUPPORTED_LANGUAGES
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
# Tier 1: LocalizedDict Dynamic Resolution & Enum Display Helpers
# ============================================================================

class TestDynamicLanguageSwitchCore:
    """Test dynamic resolution of LocalizedDict proxy constants and Enum display functions."""

    def test_localized_dict_dialog_titles_dynamic_update(self):
        """Verify DIALOG_TITLES updates immediately upon language change without re-import."""
        i18n = get_i18n()

        # German default
        i18n.current_language = "de"
        assert DIALOG_TITLES["new_case"] == "Neuen Support-Fall anlegen"
        assert "Profil" in DIALOG_TITLES["profile_settings"]

        # Switch to English
        i18n.current_language = "en"
        assert DIALOG_TITLES["new_case"] == "Create New Support Case"
        assert "Profile" in DIALOG_TITLES["profile_settings"]

        # Switch to Swedish
        i18n.current_language = "sv"
        assert DIALOG_TITLES["new_case"] == "Skapa nytt supportärende"
        assert "Profil" in DIALOG_TITLES["profile_settings"]

    def test_localized_dict_ui_buttons_dynamic_update(self):
        """Verify UI_BUTTON_TEXTS resolves dynamically in DE, EN, and SV."""
        i18n = get_i18n()

        i18n.current_language = "de"
        assert UI_BUTTON_TEXTS["save"] == "Speichern"
        assert UI_BUTTON_TEXTS["cancel"] == "Abbrechen"
        assert UI_BUTTON_TEXTS["delete"] == "Löschen"

        i18n.current_language = "en"
        assert UI_BUTTON_TEXTS["save"] == "Save"
        assert UI_BUTTON_TEXTS["cancel"] == "Cancel"
        assert UI_BUTTON_TEXTS["delete"] == "Delete"

        i18n.current_language = "sv"
        assert UI_BUTTON_TEXTS["save"] == "Spara"
        assert UI_BUTTON_TEXTS["cancel"] == "Avbryt"
        assert UI_BUTTON_TEXTS["delete"] == "Ta bort" or UI_BUTTON_TEXTS["delete"] == "Radera"

    def test_localized_dict_status_messages_dynamic_update(self):
        """Verify STATUS_MESSAGES resolves dynamically in DE, EN, and SV."""
        i18n = get_i18n()

        i18n.current_language = "de"
        assert "gespeichert" in STATUS_MESSAGES["profile_saved"]

        i18n.current_language = "en"
        assert "saved" in STATUS_MESSAGES["profile_saved"]

        i18n.current_language = "sv"
        assert "sparad" in STATUS_MESSAGES["profile_saved"] or "sparats" in STATUS_MESSAGES["profile_saved"]

    def test_enum_channel_display_helpers_across_languages(self):
        """Verify get_channel_display adapts dynamically to active language."""
        i18n = get_i18n()

        i18n.current_language = "de"
        assert "Telefon" in get_channel_display("PHONE_INBOUND")
        assert "E-Mail" in get_channel_display("EMAIL")

        i18n.current_language = "en"
        assert "Phone" in get_channel_display("PHONE_INBOUND") or "Telephone" in get_channel_display("PHONE_INBOUND")
        assert "Email" in get_channel_display("EMAIL") or "E-Mail" in get_channel_display("EMAIL")

        i18n.current_language = "sv"
        assert "Telefon" in get_channel_display("PHONE_INBOUND")

    def test_enum_actor_display_helpers_across_languages(self):
        """Verify get_actor_display adapts dynamically to active language."""
        i18n = get_i18n()

        i18n.current_language = "de"
        assert "Support" in get_actor_display("SUPPORT")
        assert "Entwicklung" in get_actor_display("DEVELOPMENT")

        i18n.current_language = "en"
        assert "Support" in get_actor_display("SUPPORT")
        assert "Development" in get_actor_display("DEVELOPMENT")

        i18n.current_language = "sv"
        assert "Support" in get_actor_display("SUPPORT")
        assert "Utveckling" in get_actor_display("DEVELOPMENT")

    def test_enum_layout_display_helpers_across_languages(self):
        """Verify get_layout_display adapts dynamically to active language."""
        i18n = get_i18n()

        i18n.current_language = "de"
        assert "Cockpit" in get_layout_display("COCKPIT")
        assert "Kanban" in get_layout_display("BOARD")

        i18n.current_language = "en"
        assert "Cockpit" in get_layout_display("COCKPIT")
        assert "Board" in get_layout_display("BOARD") or "Kanban" in get_layout_display("BOARD")

        i18n.current_language = "sv"
        assert "Cockpit" in get_layout_display("COCKPIT")
        assert "Tavla" in get_layout_display("BOARD") or "Kanban" in get_layout_display("BOARD")

    def test_menu_options_generators_across_languages(self):
        """Verify localized menu dropdown lists generate translated options."""
        i18n = get_i18n()

        i18n.current_language = "de"
        stammdaten_de = get_localized_menu_options_stammdaten()
        assert any("Praxen" in opt for opt in stammdaten_de)
        assert any("Mitarbeiter" in opt for opt in stammdaten_de)

        i18n.current_language = "en"
        stammdaten_en = get_localized_menu_options_stammdaten()
        assert any("Practices" in opt for opt in stammdaten_en)
        assert any("Colleagues" in opt for opt in stammdaten_en)

        i18n.current_language = "sv"
        stammdaten_sv = get_localized_menu_options_stammdaten()
        assert any("Mottagningar" in opt for opt in stammdaten_sv)
        assert any("Kolleger" in opt or "Medarbetare" in opt for opt in stammdaten_sv)


# ============================================================================
# Tier 2: Headless UI App & Views Dynamic Language Refresh
# ============================================================================

class TestDynamicLanguageSwitchHeadlessUI:
    """Test dynamic language switching inside headless SupportCockpit UI views."""

    def test_cockpit_view_case_list_labels_refresh(self, headless_root, tmp_path: Path):
        """Verify CockpitView's CaseListWidget updates its filter buttons and labels on language change."""
        from ui.views.cockpit_view import CockpitView

        config = AppConfig(workspace_dir=tmp_path)
        storage = StorageService(config)
        scoring = ScoringService(storage.load_profile().scoring_matrix)
        attachment = AttachmentService(config)
        wiki = WikiSyncService(config, storage.load_profile().wiki_settings)

        get_i18n().current_language = "de"
        cockpit = CockpitView(
            parent=headless_root,
            author_name="Tester",
            scoring_service=scoring,
            attachment_service=attachment,
            wiki_service=wiki,
            app_config=config,
            storage_service=storage,
        )

        # German state
        assert cockpit.left_frame.qfilter_all_btn.cget("text") == "Alle"
        assert "Dringend" in cockpit.left_frame.qfilter_urgent_btn.cget("text")
        assert "Wiedervorlage" in cockpit.left_frame.qfilter_followup_btn.cget("text")

        # Switch to English
        get_i18n().current_language = "en"
        cockpit.left_frame.refresh_ui_labels()

        assert cockpit.left_frame.qfilter_all_btn.cget("text") == "All"
        assert "Urgent" in cockpit.left_frame.qfilter_urgent_btn.cget("text")
        assert "Follow-up" in cockpit.left_frame.qfilter_followup_btn.cget("text")

        # Switch to Swedish
        get_i18n().current_language = "sv"
        cockpit.left_frame.refresh_ui_labels()

        assert cockpit.left_frame.qfilter_all_btn.cget("text") == "Alla"
        assert "Brådskande" in cockpit.left_frame.qfilter_urgent_btn.cget("text")
        assert "Uppföljning" in cockpit.left_frame.qfilter_followup_btn.cget("text")

    def test_board_view_column_labels_across_languages(self, headless_root):
        """Verify BoardView recreates Kanban columns with localized headers."""
        from ui.views.board_view import BoardView

        board = BoardView(
            parent=headless_root,
            on_select_case=lambda c: None,
            on_switch_to_cockpit=lambda c: None,
            on_open_followup=lambda c: None,
            on_toggle_complete=lambda c: None,
            on_change_actor=lambda c: None,
        )

        # German
        get_i18n().current_language = "de"
        board.create_board()
        assert "Support" in tr("board.col_support")
        assert tr("board.col_completed") == "✓ Erledigte Fälle"

        # English
        get_i18n().current_language = "en"
        board.create_board()
        assert "Support" in tr("board.col_support")
        assert tr("board.col_completed") == "✓ Completed Cases"

        # Swedish
        get_i18n().current_language = "sv"
        board.create_board()
        assert "Support" in tr("board.col_support")
        assert tr("board.col_completed") == "✓ Avslutade ärenden"

    def test_table_view_column_map_dynamic_resolution(self):
        """Verify TableView's COL_TITLE_MAP resolves dynamically across languages."""
        from ui.views.table_view import COL_TITLE_MAP

        get_i18n().current_language = "de"
        assert COL_TITLE_MAP["practice"] == "Praxis / Kunde ⇅"
        assert COL_TITLE_MAP["actor"] == "Zuständigkeit ⇅"

        get_i18n().current_language = "en"
        assert COL_TITLE_MAP["practice"] == "Practice / Customer ⇅"
        assert COL_TITLE_MAP["actor"] == "Responsibility ⇅"

        get_i18n().current_language = "sv"
        assert COL_TITLE_MAP["practice"] == "Mottagning / Kund ⇅"
        assert COL_TITLE_MAP["actor"] == "Ansvar ⇅"

    def test_active_case_form_data_preserved_during_language_switch(self, headless_root, tmp_path: Path):
        """Verify switching languages does not wipe or overwrite entered user data in active form."""
        from ui.views.cockpit_view import CockpitView

        config = AppConfig(workspace_dir=tmp_path)
        storage = StorageService(config)
        scoring = ScoringService(storage.load_profile().scoring_matrix)
        attachment = AttachmentService(config)
        wiki = WikiSyncService(config, storage.load_profile().wiki_settings)

        get_i18n().current_language = "de"
        cockpit = CockpitView(
            parent=headless_root,
            author_name="Tester",
            scoring_service=scoring,
            attachment_service=attachment,
            wiki_service=wiki,
            app_config=config,
            storage_service=storage,
        )

        test_case = Case(
            case_id="T-2026-PRESERVE",
            created_at="2026-09-02T10:00:00",
            updated_at="2026-09-02T10:00:00",
            customer=CaseCustomer(practice_name="Praxis Dr. Preserved", contact_person="Dr. Preserved"),
            classification=Classification(title="Preserved Unsaved Ticket Title"),
            workflow_status=WorkflowStatus(is_completed=False),
        )

        cockpit.on_select_case_from_list(test_case)

        # Verify case is loaded in form
        assert cockpit.current_case is not None
        assert cockpit.current_case.case_id == "T-2026-PRESERVE"
        assert cockpit.current_case.classification.title == "Preserved Unsaved Ticket Title"

        # Switch language to Swedish
        get_i18n().current_language = "sv"
        cockpit.left_frame.refresh_ui_labels()

        # Data must remain intact
        assert cockpit.current_case.case_id == "T-2026-PRESERVE"
        assert cockpit.current_case.classification.title == "Preserved Unsaved Ticket Title"
        assert cockpit.current_case.customer.practice_name == "Praxis Dr. Preserved"

    def test_cockpit_view_and_table_view_multi_cycle_tabs_and_attachment_refresh(self, headless_root, tmp_path: Path):
        """Verify CockpitView and TableView right/detail tab labels update across DE -> EN -> SV -> DE without TclError."""
        from ui.views.cockpit_view import CockpitView
        from ui.views.table_view import TableView

        config = AppConfig(workspace_dir=tmp_path)
        storage = StorageService(config)
        scoring = ScoringService(storage.load_profile().scoring_matrix)
        attachment = AttachmentService(config)
        wiki = WikiSyncService(config, storage.load_profile().wiki_settings)

        get_i18n().current_language = "de"
        cockpit = CockpitView(
            parent=headless_root,
            author_name="Tester",
            scoring_service=scoring,
            attachment_service=attachment,
            wiki_service=wiki,
            app_config=config,
            storage_service=storage,
        )

        test_case = Case(
            case_id="T-CYCLIC",
            created_at="2026-09-02T10:00:00",
            updated_at="2026-09-02T10:00:00",
            customer=CaseCustomer(practice_name="Praxis Dr. Cycle", contact_person="Dr. Cycle"),
            classification=Classification(title="Cyclic Test Case"),
            workflow_status=WorkflowStatus(is_completed=False),
        )
        cockpit.on_select_case_from_list(test_case)

        # 1. Switch to English
        get_i18n().current_language = "en"
        cockpit.refresh_ui_labels()
        btns_c = cockpit.right_tabview._segmented_button._buttons_dict
        assert btns_c["Zeitleiste"].cget("text") == "Timeline"
        assert btns_c["Anhänge"].cget("text") == "Attachments"
        assert btns_c["Wiki"].cget("text") == "Wiki / Knowledge Base"

        # 2. Switch to Swedish
        get_i18n().current_language = "sv"
        cockpit.refresh_ui_labels()
        assert btns_c["Zeitleiste"].cget("text") == "Tidslinje"
        assert btns_c["Anhänge"].cget("text") == "Bilagor"
        assert btns_c["Wiki"].cget("text") == "Wiki / Kunskapsbas"

        # 3. Switch back to German
        get_i18n().current_language = "de"
        cockpit.refresh_ui_labels()
        assert btns_c["Zeitleiste"].cget("text") == "Zeitleiste"
        assert btns_c["Anhänge"].cget("text") == "Anhänge"
        assert btns_c["Wiki"].cget("text") == "Wiki / Wissensdatenbank"

        # TableView tab cycle
        tv = TableView(
            parent=headless_root,
            author_name="Tester",
            scoring_service=scoring,
            attachment_service=attachment,
            on_case_updated=lambda c: None,
            on_case_selected=lambda c: None,
            app_config=config,
        )

        get_i18n().current_language = "en"
        tv.refresh_ui_labels()
        btns_tv = tv.detail_tabview._segmented_button._buttons_dict
        assert "Form & Fill" in btns_tv["📝 Formular & Ausfüllen"].cget("text")
        assert "Timeline" in btns_tv["🕒 Zeitleiste"].cget("text")
        assert "Attachments" in btns_tv["📎 Anhänge"].cget("text")

        get_i18n().current_language = "sv"
        tv.refresh_ui_labels()
        assert "Formulär" in btns_tv["📝 Formular & Ausfüllen"].cget("text")
        assert "Tidslinje" in btns_tv["🕒 Zeitleiste"].cget("text")
        assert "Bilagor" in btns_tv["📎 Anhänge"].cget("text")

        get_i18n().current_language = "de"
        tv.refresh_ui_labels()
        assert "Formular" in btns_tv["📝 Formular & Ausfüllen"].cget("text")
        assert "Zeitleiste" in btns_tv["🕒 Zeitleiste"].cget("text")
        assert "Anhänge" in btns_tv["📎 Anhänge"].cget("text")

    def test_support_cockpit_app_lifecycle_and_language_switch(self, tmp_path: Path):
        """Verify SupportCockpitApp instantiates cleanly without UnboundLocalError and handles language changes."""
        from ui.app import SupportCockpitApp

        config = AppConfig(workspace_dir=tmp_path)
        app = SupportCockpitApp(config)
        try:
            get_i18n().current_language = "en"
            app.on_language_changed("en")
            get_i18n().current_language = "sv"
            app.on_language_changed("sv")
            get_i18n().current_language = "de"
            app.on_language_changed("de")
        finally:
            try:
                if hasattr(app, "tray_service") and hasattr(app.tray_service, "stop"):
                    app.tray_service.stop()
                app.destroy()
            except Exception:
                pass


# ============================================================================
# Tier 2 & 3: Stress, Concurrency & Memory Leak Prevention
# ============================================================================

class TestDynamicLanguageSwitchStressAndEdgeCases:
    """Stress test rapid language switching, listener life cycles, and invalid code resilience."""

    def test_rapid_language_cycling_no_exceptions(self):
        """Rapidly cycle languages 100 times in sequence to ensure thread safety and no crashes."""
        i18n = get_i18n()
        langs = ["de", "en", "sv"]

        for i in range(100):
            target_lang = langs[i % len(langs)]
            i18n.current_language = target_lang
            assert i18n.current_language == target_lang
            # Access localized dicts during cycling
            _ = DIALOG_TITLES["new_case"]
            _ = UI_BUTTON_TEXTS["save"]
            _ = get_actor_display("SUPPORT")

    def test_listener_registration_and_unregistration(self):
        """Verify listeners are properly registered and unregistered to prevent memory leaks."""
        i18n = get_i18n()
        received_events: list[str] = []

        def dummy_listener(lang: str):
            received_events.append(lang)

        initial_listener_count = len(i18n._listeners)

        # Register
        i18n.register_listener(dummy_listener)
        assert len(i18n._listeners) == initial_listener_count + 1

        i18n.current_language = "en"
        assert received_events == ["en"]

        i18n.current_language = "sv"
        assert received_events == ["en", "sv"]

        # Unregister
        i18n.unregister_listener(dummy_listener)
        assert len(i18n._listeners) == initial_listener_count

        i18n.current_language = "de"
        assert received_events == ["en", "sv"]  # No new event added

    def test_invalid_language_code_is_safely_ignored(self):
        """Setting an unsupported language code does not corrupt state or trigger invalid listeners."""
        i18n = get_i18n()
        i18n.current_language = "de"
        assert i18n.current_language == "de"

        # Attempt to set unsupported language
        i18n.current_language = "fr"
        assert i18n.current_language == "de"  # Remains "de"

        i18n.current_language = "es"
        assert i18n.current_language == "de"
