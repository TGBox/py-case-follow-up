import pytest
from pathlib import Path
import tkinter as tk
import customtkinter as ctk

from models.case import Case, CaseCustomer, Classification, WorkflowStatus, TimelineEntry
from models.snippet import Snippet
from models.profile import Colleague
from services.search_service import SearchService
from utils.ui_utils import create_highlighted_label


def test_create_highlighted_label_multi_query():
    root = ctk.CTk()
    root.withdraw()
    try:
        lbl = create_highlighted_label(
            root,
            text="Dr. Katrin Welz Praxis Travemünde",
            query=["katrin", "trave"],
            font=("Segoe UI", 11),
            text_color=("black", "white"),
            bg_color=("gray85", "gray20"),
        )
        assert isinstance(lbl, tk.Text)
        content = lbl.get("1.0", "end - 1 chars")
        assert content == "Dr. Katrin Welz Praxis Travemünde"

        # "Dr. " is 4 chars (0-3). "Katrin" is 4..10 -> "katrin" match
        assert "match" in lbl.tag_names("1.4")
        assert "match" in lbl.tag_names("1.9")

        # "Travemünde" starts around index 23 -> "trave" match
        idx_t = content.find("Trave")
        assert "match" in lbl.tag_names(f"1.{idx_t}")
    finally:
        root.destroy()


def test_extract_case_search_match_summary_empty():
    c = Case(
        case_id="2026-001",
        customer=CaseCustomer(customer_id="C1", practice_name="Praxis Alpha"),
        classification=Classification(title="Test Fall"),
    )
    assert SearchService.extract_case_search_match_summary(c, []) is None
    assert SearchService.extract_case_search_match_summary(c, [""]) is None


def test_extract_case_search_match_summary_secondary_fields():
    c = Case(
        case_id="2026-001",
        customer=CaseCustomer(
            customer_id="C1",
            practice_name="Praxis Alpha",
            email="dr.mueller@med-center.de",
            phone="04502-8899"
        ),
        classification=Classification(title="Installation", tags=["Wichtig", "Krankentransport"]),
        workflow_status=WorkflowStatus(followup_note="Bitte Rückruf bei Schwester Katrin durchführen."),
        timeline=[TimelineEntry(note="Katrin war telefonisch nicht erreichbar.", author="Support")]
    )

    # If search is "alpha" -> matches primary field customer.practice_name ("Praxis Alpha"), so secondary summary is None
    assert SearchService.extract_case_search_match_summary(c, ["alpha"]) is None

    # Search for "katrin" -> present in followup_note and timeline
    res = SearchService.extract_case_search_match_summary(c, ["katrin"])
    assert res == "Katrin"

    # Search for "kranken" -> in tags
    res2 = SearchService.extract_case_search_match_summary(c, ["kranken"])
    assert res2 == "Krankentransport"

    # Multiple search terms: "katrin", "mueller"
    res3 = SearchService.extract_case_search_match_summary(c, ["katrin", "mueller"])
    assert res3 is not None
    assert "Katrin" in res3
    assert "dr.mueller@med-center.de" in res3


def test_extract_case_search_match_summary_truncation():
    c = Case(
        case_id="2026-002",
        customer=CaseCustomer(customer_id="C2", practice_name="Praxis Beta"),
        classification=Classification(title="Druckerproblem", tags=["TagEins", "TagZwei", "TagDrei", "TagVier"]),
        workflow_status=WorkflowStatus(followup_note="TagFunf TagSechs")
    )
    # Search for "tag"
    res = SearchService.extract_case_search_match_summary(c, ["tag"], max_matches=3, max_chars=100)
    assert res == "TagEins, TagZwei, TagDrei..."


def test_case_list_widget_search_highlighting():
    from ui.widgets.case_list_widget import CaseListWidget

    root = ctk.CTk()
    root.withdraw()
    try:
        c1 = Case(
            case_id="2026-0001",
            customer=CaseCustomer(customer_id="C1", practice_name="Praxis Nord"),
            classification=Classification(title="Netzwerkfehler"),
            workflow_status=WorkflowStatus(followup_note="Warten auf Router Lieferung")
        )
        c2 = Case(
            case_id="2026-0002",
            customer=CaseCustomer(customer_id="C2", practice_name="Praxis Süd"),
            classification=Classification(title="Software Update"),
            workflow_status=WorkflowStatus(followup_note="Alles erledigt")
        )

        widget = CaseListWidget(
            root,
            on_case_selected=lambda c: None,
            on_search_changed=lambda s: None,
        )
        widget.pack()

        # Search for "router"
        widget.search_entry.delete(0, "end")
        widget.search_entry.insert(0, "router")
        widget.set_cases([c1])

        # Check rendered widget elements
        cards = [w for w in widget.scroll_frame.winfo_children() if isinstance(w, ctk.CTkFrame)]
        assert len(cards) >= 1

        # Verify text elements inside card
        texts = []
        highlighted_texts = []
        for child in cards[0].winfo_children():
            if isinstance(child, tk.Text):
                txt = child.get("1.0", "end - 1 chars")
                texts.append(txt)
                highlighted_texts.append(txt)
            elif isinstance(child, ctk.CTkLabel):
                texts.append(child.cget("text"))
            elif isinstance(child, ctk.CTkFrame):
                for grand in child.winfo_children():
                    if isinstance(grand, tk.Text):
                        txt = grand.get("1.0", "end - 1 chars")
                        texts.append(txt)
                        highlighted_texts.append(txt)
                    elif isinstance(grand, ctk.CTkLabel):
                        texts.append(grand.cget("text"))

        # Line 1: ID (CTkLabel), Line 4: Router match summary (tk.Text highlighted)
        assert any("2026-0001" in t for t in texts)
        assert any("Router" in t for t in highlighted_texts)

        widget.destroy()
    finally:
        root.destroy()


def test_wiki_widget_search_highlighting():
    from ui.widgets.wiki_widget import WikiWidget
    from unittest.mock import MagicMock

    root = ctk.CTk()
    root.withdraw()
    try:
        mock_wiki = MagicMock()
        mock_wiki.search.return_value = [
            {"id": "doc1", "title": "Drucker Handbuch", "snippet": "Anleitung zur Installation von CUPS", "url": "http://example.com/1"}
        ]

        widget = WikiWidget(root, mock_wiki)
        widget.pack()

        widget.search_entry.delete(0, "end")
        widget.search_entry.insert(0, "Drucker")
        widget.on_search()

        cards = [w for w in widget.scroll_frame.winfo_children() if isinstance(w, ctk.CTkFrame)]
        assert len(cards) == 1

        # Check highlighted title text widget
        has_highlighted_text = any(isinstance(child, tk.Text) for child in cards[0].winfo_children())
        assert has_highlighted_text

        widget.destroy()
    finally:
        root.destroy()


def test_colleague_management_dialog_search_highlighting(tmp_path: Path):
    from ui.dialogs.colleague_management_dialog import ColleagueManagementDialog
    from services.storage_service import StorageService, AppConfig

    root = ctk.CTk()
    root.withdraw()
    try:
        config = AppConfig(workspace_dir=tmp_path)
        storage = StorageService(config)
        colleagues = [
            Colleague(name="Max Mustermann", username="mmuster", department="Support", extension="123", notes="Experte für Drucker"),
            Colleague(name="Erika Musterfrau", username="emuster", department="Vertrieb", extension="124")
        ]
        storage.save_colleagues(colleagues)

        dialog = ColleagueManagementDialog(root, storage_service=storage)
        dialog.withdraw()

        dialog.search_entry.delete(0, "end")
        dialog.search_entry.insert(0, "Drucker")
        dialog.on_search_changed()

        # Should find Max Mustermann because of notes
        cards = [w for w in dialog.list_scroll.winfo_children() if isinstance(w, ctk.CTkFrame)]
        assert len(cards) == 1

        # Check for highlighted label widgets directly in card
        text_widgets = [w for w in cards[0].winfo_children() if isinstance(w, tk.Text)]
        assert len(text_widgets) >= 1
        # Check notes line matches
        assert any("Drucker" in w.get("1.0", "end - 1 chars") for w in text_widgets)

        dialog.destroy()
    finally:
        root.destroy()


def test_snippet_picker_dialog_search_highlighting(tmp_path: Path):
    from ui.dialogs.snippet_picker_dialog import SnippetPickerDialog
    from services.snippet_service import SnippetService

    root = ctk.CTk()
    root.withdraw()
    try:
        svc = SnippetService(workspace_dir=tmp_path)
        svc.snippets = [
            Snippet(snippet_id="S-1", title="Drucker Reset", shortcut="!prt", content="Schalten Sie den Drucker aus und wieder ein.", category="Allgemein"),
            Snippet(snippet_id="S-2", title="Mail Vorlage", shortcut="!mail", content="Sehr geehrte Damen und Herren,", category="Allgemein")
        ]
        svc.save_snippets()

        dialog = SnippetPickerDialog(root, snippet_service=svc, on_snippet_selected=lambda text: None)
        dialog.withdraw()

        dialog.search_entry.delete(0, "end")
        dialog.search_entry.insert(0, "Reset")
        dialog.refresh_snippet_list()

        cards = [w for w in dialog.list_scroll.winfo_children() if isinstance(w, ctk.CTkFrame)]
        assert len(cards) == 1

        # Check text widgets
        text_widgets = []
        for child in cards[0].winfo_children():
            if isinstance(child, tk.Text):
                text_widgets.append(child)
            elif isinstance(child, ctk.CTkFrame):
                for grand in child.winfo_children():
                    if isinstance(grand, tk.Text):
                        text_widgets.append(grand)

        assert any("Reset" in w.get("1.0", "end - 1 chars") for w in text_widgets)

        dialog.destroy()
    finally:
        root.destroy()


def test_help_dialog_search_highlighting():
    from ui.dialogs.help_dialog import HelpDialog

    root = ctk.CTk()
    root.withdraw()
    try:
        dialog = HelpDialog(root)
        dialog.withdraw()

        dialog.search_entry.delete(0, "end")
        dialog.search_entry.insert(0, "Hilfe")
        dialog.on_search_changed()

        # Navigation scroll should contain card frames with highlighted labels
        cards = [w for w in dialog.nav_scroll.winfo_children() if isinstance(w, ctk.CTkFrame)]
        assert len(cards) >= 1

        text_widgets = []
        for card in cards:
            for child in card.winfo_children():
                if isinstance(child, tk.Text):
                    text_widgets.append(child.get("1.0", "end - 1 chars"))

        assert len(text_widgets) >= 1

        dialog.destroy()
    finally:
        root.destroy()


def test_tag_management_dialog_tags_highlighting(tmp_path: Path):
    from ui.dialogs.tag_management_dialog import TagManagementDialog
    from services.storage_service import StorageService, AppConfig
    from models.profile import UserProfile

    root = ctk.CTk()
    root.withdraw()
    try:
        config = AppConfig(workspace_dir=tmp_path)
        storage = StorageService(config)
        profile = UserProfile(available_tags=["Dringend", "Rezeptdruck", "Installation"])

        dialog = TagManagementDialog(root, profile=profile, storage_service=storage, initial_tab="tags")
        dialog.withdraw()

        dialog.search_tag_entry.delete(0, "end")
        dialog.search_tag_entry.insert(0, "druck")
        dialog.render_tags_list()

        rows = [w for w in dialog.tags_scroll.winfo_children() if isinstance(w, ctk.CTkFrame)]
        assert len(rows) == 1

        text_widgets = [w for w in rows[0].winfo_children() if isinstance(w, tk.Text)]
        assert len(text_widgets) == 1
        content = text_widgets[0].get("1.0", "end - 1 chars")
        assert "Rezeptdruck" in content

        dialog.destroy()
    finally:
        root.destroy()


def test_tag_management_dialog_modules_highlighting(tmp_path: Path):
    from ui.dialogs.tag_management_dialog import TagManagementDialog
    from services.storage_service import StorageService, AppConfig
    from models.profile import UserProfile

    root = ctk.CTk()
    root.withdraw()
    try:
        config = AppConfig(workspace_dir=tmp_path)
        storage = StorageService(config)
        profile = UserProfile(available_module_tags=["Abrechnung", "Terminkalender", "Schnittstelle"])

        dialog = TagManagementDialog(root, profile=profile, storage_service=storage, initial_tab="modules")
        dialog.withdraw()

        dialog.search_mod_entry.delete(0, "end")
        dialog.search_mod_entry.insert(0, "kalender")
        dialog.render_modules_list()

        rows = [w for w in dialog.modules_scroll.winfo_children() if isinstance(w, ctk.CTkFrame)]
        assert len(rows) == 1

        text_widgets = [w for w in rows[0].winfo_children() if isinstance(w, tk.Text)]
        assert len(text_widgets) == 1
        content = text_widgets[0].get("1.0", "end - 1 chars")
        assert "Terminkalender" in content

        dialog.destroy()
    finally:
        root.destroy()


def test_module_tag_picker_popup_highlighting():
    from ui.widgets.dynamic_form_widget import ModuleTagPickerPopup

    root = ctk.CTk()
    root.withdraw()
    try:
        applied: list[list[str]] = []
        popup = ModuleTagPickerPopup(
            root,
            available_tags=["Abrechnung", "Rezeptdruck", "Dokumentation"],
            selected_tags=[],
            on_apply=lambda tags: applied.append(tags)
        )
        popup.withdraw()

        popup.search_entry.delete(0, "end")
        popup.search_entry.insert(0, "druck")
        popup.render_tag_checkboxes()

        rows = [w for w in popup.scroll_frame.winfo_children() if isinstance(w, ctk.CTkFrame)]
        assert len(rows) == 1

        text_widgets = [w for w in rows[0].winfo_children() if isinstance(w, tk.Text)]
        assert len(text_widgets) == 1
        assert text_widgets[0].get("1.0", "end - 1 chars") == "Rezeptdruck"

        # Check clicking the label toggles selection
        text_widgets[0].event_generate("<Button-1>", x=5, y=5)
        assert "Rezeptdruck" in popup.selected_tags

        popup.destroy()
    finally:
        root.destroy()

