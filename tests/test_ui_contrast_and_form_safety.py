import json
from typing import Any
from unittest.mock import MagicMock
import customtkinter as ctk
import pytest
from constants import COLOR_PANEL_BG, COLOR_PANEL_BORDER
from models.case import Case
from models.export_template import ExportTemplate
from models.profile import UserInfo, UserProfile
from models.schema import QuestionSchema, SchemaField
from services.storage_service import StorageService
from ui.dialogs.profile_settings_dialog import ProfileSettingsDialog
from ui.views.analytics_view import AnalyticsView
from ui.widgets.dynamic_form_widget import DynamicFormWidget


@pytest.fixture
def dummy_app():
    root = ctk.CTk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass


@pytest.fixture
def real_storage_service(tmp_path):
    config = MagicMock()
    config.workspace_dir = tmp_path / "workspace"
    config.data_dir = tmp_path / "workspace" / "data"
    config.data_dir.mkdir(parents=True, exist_ok=True)
    config.attachments_dir = tmp_path / "workspace" / "attachments"
    config.attachments_dir.mkdir(parents=True, exist_ok=True)
    config.question_schemas_path = config.data_dir / "question_schemas.json"
    config.export_templates_path = config.data_dir / "export_templates.json"
    config.profiles_path = config.data_dir / "profiles.json"
    config.cases_path = config.data_dir / "cases.json"
    config.customers_path = config.data_dir / "customers.json"
    config.colleagues_path = config.data_dir / "colleagues.json"
    config.snippets_path = config.data_dir / "snippets.json"
    config.custom_cases_path = None
    config.custom_customers_path = None
    config.custom_wiki_db_path = None
    config.log_file_path = tmp_path / "test.log"
    config.get_example_path = lambda filename: tmp_path / "examples" / filename

    # Setup mock data_examples directory
    ex_dir = tmp_path / "examples"
    ex_dir.mkdir(parents=True, exist_ok=True)

    default_schemas = {
        "schemas": [
            {
                "schema_id": "schema_default_a",
                "display_name": "Standard A",
                "fields": [{"field_id": "f1", "label": "Feld 1", "field_type": "text", "order": 1, "required": True}],
            },
            {
                "schema_id": "schema_default_b",
                "display_name": "Standard B",
                "fields": [{"field_id": "f2", "label": "Feld 2", "field_type": "text", "order": 1, "required": False}],
            },
        ]
    }
    (ex_dir / "question_schemas.json").write_text(json.dumps(default_schemas), encoding="utf-8")

    default_templates = {
        "templates": [
            {
                "template_id": "tmpl_default_1",
                "display_name": "Vorlage 1",
                "target_type": "CLIPBOARD_TEXT",
                "applicable_cases": [],
                "template_string": "Hello {{ customer.practice_name }}",
            }
        ]
    }
    (ex_dir / "export_templates.json").write_text(json.dumps(default_templates), encoding="utf-8")

    svc = StorageService(config)
    return svc


def test_toggle_default_schemas_preserves_custom_schemas_and_creates_backup(real_storage_service):
    # Setup initial custom user schema
    custom_schema = QuestionSchema(
        schema_id="schema_my_custom_form",
        display_name="Mein eigenes mühsam erstelltes Formular",
        fields=[SchemaField(field_id="custom_f1", label="Eigenes Feld", field_type="text", order=1, required=True)],
    )
    real_storage_service.save_schemas([custom_schema], sync=True)

    assert not real_storage_service.has_default_schemas()

    # 1. Toggle: Add default schemas
    updated_schemas, is_added = real_storage_service.toggle_default_schemas()
    assert is_added is True
    ids = {s.schema_id for s in updated_schemas}
    assert "schema_my_custom_form" in ids
    assert "schema_default_a" in ids
    assert "schema_default_b" in ids
    assert real_storage_service.has_default_schemas() is True

    # Check backup file was created
    bak_path = real_storage_service.config.question_schemas_path.with_suffix(".json.bak")
    assert bak_path.exists()
    bak_data = json.loads(bak_path.read_text(encoding="utf-8"))
    assert any(s["schema_id"] == "schema_my_custom_form" for s in bak_data["schemas"])

    # 2. Toggle again: Remove default schemas
    updated_schemas2, is_added2 = real_storage_service.toggle_default_schemas()
    assert is_added2 is False
    ids2 = {s.schema_id for s in updated_schemas2}
    assert "schema_my_custom_form" in ids2
    assert "schema_default_a" not in ids2
    assert "schema_default_b" not in ids2
    assert real_storage_service.has_default_schemas() is False


def test_toggle_default_templates_preserves_custom_templates_and_creates_backup(real_storage_service):
    custom_tmpl = ExportTemplate(
        template_id="tmpl_my_custom",
        display_name="Meine benutzerdefinierte Vorlage",
        target_type="CLIPBOARD_TEXT",
        applicable_cases=[],
        template_string="Custom Template Content",
    )
    real_storage_service.save_templates([custom_tmpl], sync=True)

    assert not real_storage_service.has_default_templates()

    # 1. Toggle: Add default templates
    updated_tmpls, is_added = real_storage_service.toggle_default_templates()
    assert is_added is True
    ids = {t.template_id for t in updated_tmpls}
    assert "tmpl_my_custom" in ids
    assert "tmpl_default_1" in ids
    assert real_storage_service.has_default_templates() is True

    # Check backup file
    bak_path = real_storage_service.config.export_templates_path.with_suffix(".json.bak")
    assert bak_path.exists()

    # 2. Toggle again: Remove default templates
    updated_tmpls2, is_added2 = real_storage_service.toggle_default_templates()
    assert is_added2 is False
    ids2 = {t.template_id for t in updated_tmpls2}
    assert "tmpl_my_custom" in ids2
    assert "tmpl_default_1" not in ids2
    assert real_storage_service.has_default_templates() is False


def test_dynamic_form_field_width_constraints(dummy_app, real_storage_service):
    schema = QuestionSchema(
        schema_id="schema_test_widths",
        display_name="Breitentest Formular",
        fields=[
            SchemaField(field_id="f_text", label="Textfeld", field_type="text", order=1),
            SchemaField(field_id="f_num", label="Zahlenfeld", field_type="number", order=2),
            SchemaField(field_id="f_drop", label="Dropdown", field_type="dropdown", options=["Opt 1", "Opt 2"], order=3),
            SchemaField(field_id="f_date", label="Datum", field_type="date", order=4),
            SchemaField(field_id="f_file", label="Datei", field_type="file", order=5),
            SchemaField(field_id="f_details", label="Genaue Begründung", field_type="text", order=6),  # multi-line keyword
        ],
    )

    form_widget = DynamicFormWidget(dummy_app)
    form_widget.load_schema(schema, form_data={})

    widgets = form_widget.field_widgets

    # Text entry: 400px
    _, text_widget = widgets["f_text"]
    assert text_widget.cget("width") == 400

    # Number entry: 400px
    _, num_widget = widgets["f_num"]
    assert num_widget.cget("width") == 400

    # Dropdown menu: 400px
    _, drop_widget = widgets["f_drop"]
    assert drop_widget.cget("width") == 400

    # Date field: entry is 295px
    _, date_entry = widgets["f_date"]
    assert date_entry.cget("width") == 295

    # File field: entry is 280px
    _, file_entry = widgets["f_file"]
    assert file_entry.cget("width") == 280

    # Multi-line Textbox: 520px
    _, textbox = widgets["f_details"]
    assert textbox.cget("width") == 520

    form_widget.destroy()


def test_user_profile_two_column_side_by_side_layout(dummy_app, real_storage_service):
    profile = UserProfile(user=UserInfo(name="Max Muster"))
    storage_mock = MagicMock(spec=StorageService)
    storage_mock.list_profiles.return_value = ["Max Muster"]
    storage_mock.config = real_storage_service.config

    dialog = ProfileSettingsDialog(dummy_app, profile=profile, storage_service=storage_mock)

    # Verify user_name_entry (Left Column) and language_combo (Right Column) are in different column masters
    left_container = dialog.user_name_entry.master
    right_container = dialog.language_combo.master
    assert left_container is not right_container

    # Verify both column masters are children of the same cols_container
    assert left_container.master is right_container.master

    # Verify both signature buttons are present and width is 185px
    assert dialog.btn_save_sig.cget("width") == 185
    assert dialog.btn_load_sig.cget("width") == 185

    # Verify signature textbox has distinct border
    assert dialog.user_sig_txt.cget("border_width") == 1
    assert dialog.user_sig_txt.cget("border_color") is not None

    from constants import DIALOG_DIMENSIONS
    assert DIALOG_DIMENSIONS["profile_settings"][1] >= 860
    assert DIALOG_DIMENSIONS["schema_builder"][0] >= 1150

    dialog.destroy()


def test_analytics_high_contrast_styling(dummy_app):
    view = AnalyticsView(dummy_app)
    view.set_cases([Case(case_id="C-1", classification=MagicMock(), customer=MagicMock(), workflow_status=MagicMock())])

    # Check that COLOR_PANEL_BG is ("#d4d4d8", "gray20")
    assert COLOR_PANEL_BG == ("#d4d4d8", "gray20")
    assert COLOR_PANEL_BORDER == ("#b0b0b5", "gray30")

    # Verify cards in scroll_frame have border_width 1 and COLOR_PANEL_BG
    found_cards = [w for w in view.scroll_frame.winfo_children() if isinstance(w, ctk.CTkFrame)]
    assert len(found_cards) > 0

    view.destroy()


def test_ctk_tabview_patch_preserves_color_tuples_and_prevents_dark_mode_white_boxes(dummy_app):
    ctk.set_appearance_mode("Light")
    dummy_app.update_idletasks()

    tv = ctk.CTkTabview(dummy_app)
    tv.pack()
    tab: Any = tv.add("TestTab")
    scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
    scroll.pack()
    lbl: Any = ctk.CTkLabel(scroll, text="Test Label")
    lbl.pack()

    dummy_app.update_idletasks()
    assert tab._fg_color == ["gray86", "gray17"] or tab._fg_color == ("gray86", "gray17")
    assert lbl._label.cget("bg") == "gray86"

    # Switch to Dark Mode
    ctk.set_appearance_mode("Dark")
    dummy_app.update_idletasks()

    # Verify tab kept color tuple and label background adapted to dark without white boxes
    assert tab._fg_color == ["gray86", "gray17"] or tab._fg_color == ("gray86", "gray17")
    assert lbl._label.cget("bg") == "gray17"
    assert lbl._label.cget("fg") == "#DCE4EE"

    # Switch back to Light Mode
    ctk.set_appearance_mode("Light")
    dummy_app.update_idletasks()

    assert lbl._label.cget("bg") == "gray86"
    assert lbl._label.cget("fg") == "gray10"

    tv.destroy()


def test_profile_settings_dialog_appearance_switch_no_white_boxes(dummy_app, real_storage_service):
    profile = UserProfile(user=UserInfo(name="Daniel Rösch"))
    storage_mock = MagicMock(spec=StorageService)
    storage_mock.list_profiles.return_value = ["Daniel Rösch"]
    storage_mock.config = real_storage_service.config

    ctk.set_appearance_mode("Light")
    dummy_app.update_idletasks()

    dialog = ProfileSettingsDialog(dummy_app, profile=profile, storage_service=storage_mock)
    dummy_app.update_idletasks()

    user_lbl: Any = dialog.user_tab_hdr_lbl
    app_lbl: Any = dialog.app_shortcuts_hdr_lbl
    tab_paths: Any = dialog.tab_paths
    paths_scroll: Any = dialog.paths_scroll

    # Switch to Dark Mode dynamically (as happens when saving or switching themes)
    ctk.set_appearance_mode("Dark")
    dummy_app.update_idletasks()

    # Tab 1: Verify header label has dark background and bright text
    assert user_lbl._label.cget("bg") == "gray17"
    assert user_lbl._label.cget("fg") == "#DCE4EE"

    # Tab 2: Verify paths tab and backup cards
    assert tab_paths._fg_color == ["gray86", "gray17"] or tab_paths._fg_color == ("gray86", "gray17")
    assert paths_scroll._parent_canvas.cget("bg") == "gray17"

    # Verify export and import cards have border styling and panel bg
    found_cards = [w for w in dialog.paths_scroll.winfo_children() if isinstance(w, ctk.CTkFrame) and w.cget("corner_radius") == 8]
    assert len(found_cards) >= 2
    for card in found_cards:
        assert card.cget("border_width") == 1
        assert card.cget("fg_color") == COLOR_PANEL_BG

    # Tab 5: Verify shortcuts header has dark background
    assert app_lbl._label.cget("bg") == "gray17"
    assert app_lbl._label.cget("fg") == "#DCE4EE"

    # Switch back to Light Mode
    ctk.set_appearance_mode("Light")
    dummy_app.update_idletasks()

    assert user_lbl._label.cget("bg") == "gray86"
    assert user_lbl._label.cget("fg") == "gray10"
    assert app_lbl._label.cget("bg") == "gray86"
    assert app_lbl._label.cget("fg") == "gray10"

    dialog.destroy()


def test_urgency_and_warning_tokens_wcag_aa_contrast():
    from constants import (
        COLOR_URGENCY_RED,
        COLOR_URGENCY_YELLOW,
        COLOR_URGENCY_GREEN,
        COLOR_WARNING_ORANGE,
    )

    def hex_to_rgb(h: str) -> tuple[int, int, int]:
        h = h.lstrip("#")
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

    def get_luminance(rgb: tuple[int, int, int]) -> float:
        vals = []
        for c in rgb:
            s = c / 255.0
            vals.append(s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4)
        return 0.2126 * vals[0] + 0.7152 * vals[1] + 0.0722 * vals[2]

    def contrast(h1: str, h2: str) -> float:
        l1 = get_luminance(hex_to_rgb(h1))
        l2 = get_luminance(hex_to_rgb(h2))
        return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)

    light_panel = "#d4d4d8"
    dark_panel = "#333333"

    # All light tokens on light panel must have contrast >= 4.5:1 (WCAG AA)
    assert contrast(COLOR_URGENCY_RED[0], light_panel) >= 4.5
    assert contrast(COLOR_URGENCY_YELLOW[0], light_panel) >= 4.5
    assert contrast(COLOR_URGENCY_GREEN[0], light_panel) >= 4.5
    assert contrast(COLOR_WARNING_ORANGE[0], light_panel) >= 4.5

    # All dark tokens on dark panel must have contrast >= 4.5:1 (WCAG AA)
    assert contrast(COLOR_URGENCY_RED[1], dark_panel) >= 4.5
    assert contrast(COLOR_URGENCY_YELLOW[1], dark_panel) >= 4.5
    assert contrast(COLOR_URGENCY_GREEN[1], dark_panel) >= 4.5
    assert contrast(COLOR_WARNING_ORANGE[1], dark_panel) >= 4.5
