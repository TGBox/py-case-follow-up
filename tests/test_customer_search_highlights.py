import pytest
from pathlib import Path
import tkinter as tk
import customtkinter as ctk

from models.customer import Customer, Contact
from services.customer_service import CustomerService
from services.storage_service import StorageService, AppConfig
from utils.ui_utils import create_highlighted_label


def test_extract_customer_search_match_summary_empty():
    cust = Customer(
        customer_id="00109",
        practice_name="Praxis Welz",
        contacts=[Contact(name="Frau Katrin Schmidt", email="katrin.schmidt@ergotherapie-nwm.de")]
    )
    assert CustomerService.extract_customer_search_match_summary(cust, "") is None
    assert CustomerService.extract_customer_search_match_summary(cust, "   ") is None


def test_extract_customer_search_match_summary_single_word():
    cust = Customer(
        customer_id="00062",
        practice_name="Praxis Zeglin Alte Post",
        contacts=[
            Contact(name="Herr Uwe Zeglin", role="Inhaber"),
            Contact(name="Praxis in Travemünde", role="Praxis", phone="04502889881")
        ]
    )
    # Search for "tr" -> should extract "Travemünde"
    res = CustomerService.extract_customer_search_match_summary(cust, "tr")
    assert res == "Travemünde"


def test_extract_customer_search_match_summary_welz_screenshot_example():
    cust = Customer(
        customer_id="00109",
        practice_name="Praxis Welz",
        contacts=[
            Contact(
                name="Frau Katrin Schmidt",
                role="Praxisleiterin / Therapeutin",
                email="katrin.schmidt@ergotherapie-nwm.de",
                phone="015236188954"
            ),
            Contact(
                name="Praxis in Wismar/Neukloster",
                role="Praxis",
                email="katrin.schmidt@ergotherapie-nwm.de",
                phone="03841213471"
            )
        ]
    )
    # In Contact #1: "Katrin" matches "tr", email matches "tr".
    # In Contact #2: duplicate email is deduplicated.
    res = CustomerService.extract_customer_search_match_summary(cust, "tr")
    assert res == "Katrin, katrin.schmidt@ergotherapie-nwm.de"


def test_extract_customer_search_match_summary_truncation_count():
    cust = Customer(
        customer_id="00001",
        practice_name="Praxis Multi",
        contacts=[
            Contact(name="Dr. Petra Tron"),
            Contact(name="Extra Info"),
            Contact(name="Krankentransport")
        ]
    )
    # 4 distinct matching words: "Petra", "Tron", "Extra", "Krankentransport"
    # Max matches is 3 -> Petra, Tron, Extra...
    res = CustomerService.extract_customer_search_match_summary(cust, "tr", max_matches=3, max_chars=100)
    assert res == "Petra, Tron, Extra..."


def test_extract_customer_search_match_summary_truncation_chars():
    cust = Customer(
        customer_id="00001",
        practice_name="Praxis Long",
        contacts=[
            Contact(name="Katrin", email="katrin.schmidt@ergotherapie-nwm.de")
        ]
    )
    # Length of "Katrin, katrin.schmidt@ergotherapie-nwm.de" is 43 chars.
    # If max_chars is 20, it should stop and append "..."
    res = CustomerService.extract_customer_search_match_summary(cust, "tr", max_matches=5, max_chars=20)
    assert res == "Katrin..."


def test_extract_customer_search_match_summary_first_word_longer_than_max_chars():
    cust = Customer(
        customer_id="00001",
        practice_name="Praxis Superlong",
        contacts=[
            Contact(name="Supercalifragilisticexpialidocioustron")
        ]
    )
    res = CustomerService.extract_customer_search_match_summary(cust, "tr", max_matches=3, max_chars=25)
    assert res is not None
    assert res.endswith("...")
    assert len(res) <= 25


def test_extract_customer_search_match_summary_no_external_matches():
    cust = Customer(
        customer_id="00109",
        practice_name="Praxis Welz",
        contacts=[Contact(name="Dr. Peter Meier", role="Arzt")]
    )
    # "Welz" is only in practice_name, not in contacts
    res = CustomerService.extract_customer_search_match_summary(cust, "Welz")
    assert res is None


def test_create_highlighted_label_tags_and_events():
    root = ctk.CTk()
    root.withdraw()
    try:
        clicks = []
        lbl = create_highlighted_label(
            root,
            text="Frau Katrin Schmidt",
            query="tr",
            font=("Segoe UI", 11),
            text_color=("black", "white"),
            bg_color=("gray85", "gray20"),
            on_click=lambda e: clicks.append(1)
        )
        assert isinstance(lbl, tk.Text)
        assert str(lbl.cget("state")) == "disabled"
        
        # Verify text content
        content = lbl.get("1.0", "end - 1 chars")
        assert content == "Frau Katrin Schmidt"

        # Verify that "tr" in Katrin was tagged with "match"
        # "Frau Ka" is 7 chars (0-6). "tr" is index 7-8.
        tag_t = lbl.tag_names("1.7")
        tag_r = lbl.tag_names("1.8")
        assert "match" in tag_t
        assert "match" in tag_r
        
        tag_k = lbl.tag_names("1.5")
        assert "normal" in tag_k

        # Verify click event
        lbl.event_generate("<Button-1>", x=5, y=5)
        assert len(clicks) == 1
    finally:
        root.destroy()


def test_customer_management_dialog_search_highlights(tmp_path: Path):
    from ui.dialogs.customer_management_dialog import CustomerManagementDialog

    root = ctk.CTk()
    root.withdraw()
    try:
        config = AppConfig(workspace_dir=tmp_path)
        storage = StorageService(config)
        service = CustomerService(storage)

        # Setup exact test data matching user screenshot
        c_welz = Customer(
            customer_id="00109",
            practice_name="Praxis Welz",
            contacts=[
                Contact(name="Frau Katrin Schmidt", role="Praxisleiterin / Therapeutin", email="katrin.schmidt@ergotherapie-nwm.de"),
                Contact(name="Praxis in Wismar/Neukloster", role="Praxis", email="katrin.schmidt@ergotherapie-nwm.de")
            ]
        )
        c_zeglin = Customer(
            customer_id="00062",
            practice_name="Praxis Zeglin Alte Post",
            contacts=[
                Contact(name="Herr Uwe Zeglin", role="Inhaber / Therapeut"),
                Contact(name="Praxis in Travemünde", role="Praxis")
            ]
        )
        service.save_customer(c_welz)
        service.save_customer(c_zeglin)

        dialog = CustomerManagementDialog(root, service)
        dialog.withdraw()

        # Initially, no search: 2 cards, standard labels, no line 3
        dialog.search_entry.delete(0, "end")
        dialog.on_search_changed()

        cards = [w for w in dialog.list_scroll.winfo_children() if isinstance(w, ctk.CTkFrame)]
        assert len(cards) == 2

        # Simulate search for "tr"
        dialog.search_entry.insert(0, "tr")
        dialog.on_search_changed()

        cards_after = [w for w in dialog.list_scroll.winfo_children() if isinstance(w, ctk.CTkFrame)]
        assert len(cards_after) == 2

        # Find card for Praxis Welz
        # Inside card, find txt_box children
        welz_card = None
        zeglin_card = None
        for card in cards_after:
            text_widgets = []
            for child in card.winfo_children():
                if isinstance(child, ctk.CTkFrame): # txt_box
                    for grand in child.winfo_children():
                        if isinstance(grand, tk.Text):
                            text_widgets.append(grand.get("1.0", "end - 1 chars"))
                        elif isinstance(grand, ctk.CTkLabel):
                            text_widgets.append(grand.cget("text"))
            if any("Welz" in t for t in text_widgets):
                welz_card = text_widgets
            elif any("Zeglin" in t for t in text_widgets):
                zeglin_card = text_widgets

        assert welz_card is not None
        assert zeglin_card is not None

        # Check that Line 3 contains the extracted matches
        assert any("Katrin, katrin.schmidt@ergotherapie-nwm.de" in t for t in welz_card)
        assert any("Travemünde" in t for t in zeglin_card)

        # Test clicking to select
        dialog.select_customer("00109")
        assert dialog.selected_customer is not None
        assert dialog.selected_customer.customer_id == "00109"

        dialog.destroy()
    finally:
        root.destroy()
