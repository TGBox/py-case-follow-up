"""Search: query parsing/filtering, search-text cache, deep search, match summaries and highlighted result rendering."""

from datetime import datetime, timedelta
import json
from pathlib import Path
import tkinter as tk

import customtkinter as ctk
import pytest

from enums import Actor, UrgencyLevel, BoardColumn
from models.case import Case, CaseCustomer, Classification, WorkflowStatus, TimelineEntry
from models.customer import Customer, Contact
from models.profile import Colleague, UserProfile
from models.snippet import Snippet
from services.customer_service import CustomerService
from services.deep_search_service import DeepSearchService
from services.search_service import SearchService, parse_search_query
from utils.datetime_utils import format_iso
from utils.ui_utils import create_highlighted_label

NOW = datetime(2026, 8, 23, 14, 0, 0)
LABEL_STYLE = dict(font=("Segoe UI", 11), text_color=("black", "white"), bg_color=("gray85", "gray20"))


def _text_contents(widget) -> list[str]:
    """Content of every highlighted tk.Text below widget (recursive)."""
    out = []
    for child in widget.winfo_children():
        if isinstance(child, tk.Text):
            out.append(child.get("1.0", "end - 1 chars"))
        out.extend(_text_contents(child))
    return out


def _label_texts(widget) -> list[str]:
    out = []
    for child in widget.winfo_children():
        if isinstance(child, ctk.CTkLabel):
            out.append(child.cget("text"))
        out.extend(_label_texts(child))
    return out


def _frames(container) -> list:
    return [w for w in container.winfo_children() if isinstance(w, ctk.CTkFrame)]


# --- Query parsing and filtering -------------------------------------------------

def test_parse_search_query_tokens_and_free_text():
    q = parse_search_query("vip:true actor:dev status:open error:ERR_902 Praxis Müller")
    assert (q.vip, q.actor, q.status, q.error) == (True, "dev", "open", "ERR_902")
    assert q.free_text_terms == ["Praxis", "Müller"]
    # identical strings are served from the LRU cache
    assert parse_search_query("vip:true status:open") is parse_search_query("vip:true status:open")


@pytest.fixture
def search_cases():
    return [
        Case(
            case_id="T-001",
            customer=CaseCustomer(customer_id="K-100", practice_name="Praxis Alpha", is_vip=True,
                                  contact_person="Dr. Sabine Weber", phone="+49 731 123456"),
            classification=Classification(title="Zuzahlungsfehler", tags=["Abrechnung", "pvs"],
                                          deadline_callback=format_iso(NOW + timedelta(hours=1))),
            workflow_status=WorkflowStatus(current_actor=Actor.DEVELOPMENT,
                                           followup_at="2026-08-22T09:00:00", followup_note="Beim Dev nachfragen"),
            form_data={"error_code": "ERR_DB_902"},
            timeline=[TimelineEntry(note="Abbruch beim Import")],
        ),
        Case(
            case_id="T-002",
            customer=CaseCustomer(customer_id="K-200", practice_name="Praxis Beta"),
            classification=Classification(title="Rezeptdruck", tags=["Hardware", "Drucker"],
                                          deadline_callback=format_iso(NOW - timedelta(hours=1))),
            workflow_status=WorkflowStatus(current_actor=Actor.SUPPORT, is_completed=True),
            form_data={"error_code": "ERR_PRINT_01"},
            timeline=[TimelineEntry(note="Drucker antwortet nicht")],
        ),
        Case(
            case_id="T-003",
            customer=CaseCustomer(customer_id="INTERNAL", practice_name="Intern / Keine Praxis"),
            classification=Classification(title="Server-Wartung DB-Migration"),
            workflow_status=WorkflowStatus(is_archived=True),
        ),
    ]


@pytest.mark.parametrize("query, expected", [
    ("vip:true", ["T-001"]),
    ("actor:dev", ["T-001"]),
    ("error:ERR_PRINT_01", ["T-002"]),
    ("deadline:overdue", ["T-002"]),
    ("deadline:<2h", ["T-001"]),
    ("tag:Abrechnung", ["T-001"]),
    ("tag:pvs", ["T-001"]),
    ("status:open", ["T-001"]),
    ("status:done", ["T-002"]),
    ("status:archived", ["T-003"]),
    ("reminder:due", ["T-001"]),
    ("reminder:false", ["T-002", "T-003"]),
    ("is:internal", ["T-003"]),
    ("is:customer", ["T-001", "T-002"]),
    ("internal:true", ["T-003"]),
    ("Import", ["T-001"]),
    ("Drucker", ["T-002"]),
    ("Dev nachfragen", ["T-001"]),
    ("Sabine", ["T-001"]),
    ("123456", ["T-001"]),
    ("NichtVorhanden", []),
    ("vip:true actor:dev Zuzahlung", ["T-001"]),
    ("unknown_key:Alpha", ["T-001"]),  # unknown token falls back to free text
    ("", ["T-001", "T-002", "T-003"]),
    ("   ", ["T-001", "T-002", "T-003"]),
])
def test_filter_cases(search_cases, query, expected):
    assert [c.case_id for c in SearchService.filter_cases(search_cases, query, NOW)] == expected


def test_searchable_text_is_cached_until_invalidated(storage):
    case = Case(case_id="T-1001")
    case.classification.title = "Druckerprobleme in Praxis"
    case.customer.practice_name = "Praxis Dr. Med"
    case.timeline.append(TimelineEntry(note="Netzwerkkabel getauscht", author="Dani"))

    text = case.get_searchable_text()
    for part in ("t-1001", "druckerprobleme in praxis", "praxis dr. med", "netzwerkkabel getauscht"):
        assert part in text
    assert SearchService.matches_query(case, parse_search_query("Netzwerkkabel"))

    case.classification.title = "Neue Scanner Installation"
    assert "scanner" not in case.get_searchable_text()  # stale until invalidated
    case.invalidate_search_cache()
    assert "neue scanner installation" in case.get_searchable_text()
    assert not {"_searchable_text", "searchable_text"} & set(case.to_dict())

    # StorageService.update_single_case invalidates the cache itself
    storage.save_cases([case], sync=True)
    case.classification.title = "Aktualisierter Titel"
    storage.update_single_case(case)
    assert "aktualisierter titel" in case.get_searchable_text()


def test_internal_case_validation_and_persistence(storage):
    assert CaseCustomer(customer_id="INTERNAL", practice_name="Intern / Keine Praxis").validate() == []
    assert len(CaseCustomer(customer_id="", practice_name="").validate()) >= 1
    assert Case(customer=CaseCustomer(customer_id="K-1", practice_name="Praxis")).is_internal is False

    storage.save_cases([Case(
        case_id="T-INT-999",
        customer=CaseCustomer(customer_id="INTERNAL", practice_name="Intern / Keine Praxis"),
        classification=Classification(schema_id="schema_internal_task", title="Prozess-Dokumentation erstellen"),
    )])
    loaded = storage.load_cases()
    assert len(loaded) == 1 and loaded[0].is_internal is True
    assert loaded[0].classification.title == "Prozess-Dokumentation erstellen"


# --- Deep search -----------------------------------------------------------------

def test_deep_search_attachments_with_line_cache(tmp_path: Path):
    service = DeepSearchService(workspace_dir=tmp_path)
    att_dir = tmp_path / "data" / "attachments" / "T-2026-1001"
    att_dir.mkdir(parents=True)
    log_file = att_dir / "error_trace.log"
    log_file.write_text(
        "2026-08-24 10:00:00 [INFO] System started.\n"
        "2026-08-24 10:05:22 [ERROR] Fatal Exception: DB Connection Timeout (ErrCode AL-99)\n",
        encoding="utf-8",
    )
    (att_dir / "dump.sql").write_text("SELECT * FROM dbo.Kunden WHERE fehler='x';", encoding="utf-8")
    case = Case(case_id="T-2026-1001", attachment_directory=str(att_dir))

    matches = service.search_case_attachments(case, "AL-99")
    assert [(m["file_name"], m["line_number"]) for m in matches] == [("error_trace.log", 2)]
    assert "ErrCode AL-99" in matches[0]["snippet"]
    assert len(service.search_case_attachments(case, "AL-99")) == 1  # served from line cache

    # a rewritten file is re-read, not served stale
    log_file.write_text("Line 1: No issue\nLine 2: Critical Error\n", encoding="utf-8")
    res = service.search_case_attachments(case, "Critical")
    assert len(res) == 1 and "Line 2" in res[0]["snippet"]

    results = service.perform_deep_search([case], "dbo.Kunden")
    assert [m["file_name"] for m in results["T-2026-1001"]["attachment_matches"]] == ["dump.sql"]


def test_deep_search_wiki_cache(tmp_path: Path):
    service = DeepSearchService(workspace_dir=tmp_path)
    wiki_file = tmp_path / "wiki_cache.json"
    wiki_file.write_text(json.dumps([{
        "article_id": "W-01",
        "title": "Abrechnung Zuzahlung AL-99 Notfallanleitung",
        "content": "Tritt der Fehler AL-99 beim Export auf, muss der Server neugestartet werden.",
        "tags": ["abrechnung", "al-99"],
    }]), encoding="utf-8")

    matches = service.search_wiki_cache("AL-99", wiki_cache_file=wiki_file)
    assert [m["article_id"] for m in matches] == ["W-01"]


# --- Match summaries -------------------------------------------------------------

def test_case_match_summary():
    c = Case(
        case_id="2026-001",
        customer=CaseCustomer(customer_id="C1", practice_name="Praxis Alpha",
                              email="dr.mueller@med-center.de", phone="04502-8899"),
        classification=Classification(title="Installation", tags=["Wichtig", "Krankentransport"]),
        workflow_status=WorkflowStatus(followup_note="Bitte Rückruf bei Schwester Katrin durchführen."),
        timeline=[TimelineEntry(note="Katrin war telefonisch nicht erreichbar.", author="Support")],
    )
    assert SearchService.extract_case_search_match_summary(c, []) is None
    assert SearchService.extract_case_search_match_summary(c, [""]) is None
    assert SearchService.extract_case_search_match_summary(c, ["alpha"]) is None  # already on the card
    assert SearchService.extract_case_search_match_summary(c, ["katrin"]) == "Katrin"
    assert SearchService.extract_case_search_match_summary(c, ["kranken"]) == "Krankentransport"
    both = SearchService.extract_case_search_match_summary(c, ["katrin", "mueller"])
    assert "Katrin" in both and "dr.mueller@med-center.de" in both

    many = Case(classification=Classification(tags=["TagEins", "TagZwei", "TagDrei", "TagVier"]),
                workflow_status=WorkflowStatus(followup_note="TagFunf TagSechs"))
    assert SearchService.extract_case_search_match_summary(many, ["tag"], max_matches=3, max_chars=100) \
        == "TagEins, TagZwei, TagDrei..."


WELZ = Customer(customer_id="00109", practice_name="Praxis Welz", contacts=[
    Contact(name="Frau Katrin Schmidt", role="Praxisleiterin / Therapeutin",
            email="katrin.schmidt@ergotherapie-nwm.de", phone="015236188954"),
    Contact(name="Praxis in Wismar/Neukloster", role="Praxis",
            email="katrin.schmidt@ergotherapie-nwm.de", phone="03841213471"),
])
ZEGLIN = Customer(customer_id="00062", practice_name="Praxis Zeglin Alte Post", contacts=[
    Contact(name="Herr Uwe Zeglin", role="Inhaber"),
    Contact(name="Praxis in Travemünde", role="Praxis", phone="04502889881"),
])


@pytest.mark.parametrize("customer, query, kwargs, expected", [
    (WELZ, "", {}, None),
    (WELZ, "   ", {}, None),
    (WELZ, "Welz", {}, None),  # only in practice_name, nothing extra to show
    (ZEGLIN, "tr", {}, "Travemünde"),
    (WELZ, "tr", {}, "Katrin, katrin.schmidt@ergotherapie-nwm.de"),  # duplicate email deduplicated
    (Customer(customer_id="1", practice_name="P", contacts=[
        Contact(name="Dr. Petra Tron"), Contact(name="Extra Info"), Contact(name="Krankentransport")]),
     "tr", dict(max_matches=3, max_chars=100), "Petra, Tron, Extra..."),
    (Customer(customer_id="1", practice_name="P", contacts=[
        Contact(name="Katrin", email="katrin.schmidt@ergotherapie-nwm.de")]),
     "tr", dict(max_matches=5, max_chars=20), "Katrin..."),
])
def test_customer_match_summary(customer, query, kwargs, expected):
    assert CustomerService.extract_customer_search_match_summary(customer, query, **kwargs) == expected


def test_customer_match_summary_truncates_overlong_first_word():
    cust = Customer(customer_id="1", practice_name="P", contacts=[Contact(name="Supercalifragilisticexpialidocioustron")])
    res = CustomerService.extract_customer_search_match_summary(cust, "tr", max_matches=3, max_chars=25)
    assert res.endswith("...") and len(res) <= 25


def test_summarize_matching_words():
    """A summary that just repeats the label explains nothing."""
    summary = CustomerService.summarize_matching_words(
        ["Ulbricht", "Fr.Ulbricht", "https://www.ulbricht.example"], "ulbricht", exclude_text="Ulbricht (00120)")
    assert not summary.startswith("Ulbricht,") and "Fr.Ulbricht" in summary
    for fields, q in ((["Praxis Welz"], ""), (["Praxis Welz"], "   "), (["Praxis Welz"], "zzz"), ([], "welz")):
        assert CustomerService.summarize_matching_words(fields, q) is None


def test_new_case_dialog_customer_search_covers_hidden_fields():
    """The practice picker must find a customer by address, contact and numbers."""
    from ui.dialogs.new_case_dialog import NewCaseDialog

    cust = Customer(customer_id="00109", practice_name="Praxis Welz", city="Rommerskirchen",
                    phone_main="02183416034", vm_number=41569,
                    contacts=[Contact(name="Frau Katrin Schmidt", role="Leitende MFA")])
    haystack = NewCaseDialog.customer_search_text(cust).lower()
    for needle in ("rommerskirchen", "02183416034", "41569", "katrin", "leitende mfa"):
        assert needle in haystack, f"{needle!r} waere nicht auffindbar"

    summary = CustomerService.summarize_matching_words(
        NewCaseDialog.customer_search_fields(cust), "rommerskirchen",
        exclude_text=NewCaseDialog.customer_display_name(cust))
    assert "Rommerskirchen" in summary


# --- Highlighted labels ----------------------------------------------------------

def test_highlighted_label_tags_matches_and_clicks(root):
    clicks = []
    lbl = create_highlighted_label(root, text="Frau Katrin Schmidt", query="tr",
                                   on_click=lambda e: clicks.append(1), **LABEL_STYLE)
    assert lbl.get("1.0", "end - 1 chars") == "Frau Katrin Schmidt"
    assert str(lbl.cget("state")) == "disabled"
    assert "match" in lbl.tag_names("1.7") and "match" in lbl.tag_names("1.8")
    assert "normal" in lbl.tag_names("1.5")
    lbl.event_generate("<Button-1>", x=5, y=5)
    assert clicks == [1]

    multi = create_highlighted_label(root, text="Dr. Katrin Welz Praxis Travemünde", query=["katrin", "trave"], **LABEL_STYLE)
    content = multi.get("1.0", "end - 1 chars")
    for idx in (4, 9, content.find("Trave")):
        assert "match" in multi.tag_names(f"1.{idx}")


def test_highlighted_label_has_no_duplicate_click_bindings(root):
    """on_click must be bound once, on the widget only.

    Tk invokes tag bindings in addition to the widget binding, so binding on_click
    to the 'normal'/'match' tags as well fired it twice per real click.
    """
    lbl = create_highlighted_label(root, text="Praxis Welz Travemünde", query=["welz"],
                                   on_click=lambda e: None, **LABEL_STYLE)
    assert lbl.bind("<Button-1>")
    for tag in ("normal", "match"):
        assert str(lbl.tk.call(lbl._w, "tag", "bind", tag, "<Button-1>")) == ""  # type: ignore[attr-defined]


def test_highlighted_label_is_wired_for_auto_sizing(root):
    """A wrapped label sizes itself via <Configure> (was a hardcoded 2 lines that swallowed text)."""
    wrapped = create_highlighted_label(root, text="Der Druckertreiber muss nach einem Update neu installiert werden.",
                                       query=["treiber"], wrap="word", **LABEL_STYLE)
    assert wrapped.bind("<Configure>")
    flat = create_highlighted_label(root, text="T-2026-1042", query=["2026"], wrap="none", **LABEL_STYLE)
    assert int(flat.cget("height")) == 1


def test_auto_hiding_scrollbar_is_installed_only_once(root):
    """AutoScrollableFrame must not end up with two competing scrollbar controllers."""
    from utils.ui_utils import AutoScrollableFrame, enable_auto_hiding_scrollbar

    frame = AutoScrollableFrame(root, width=200, height=150)
    frame.pack()
    root.update()
    assert getattr(frame, "_auto_hide_scrollbar_installed", False) is True
    canvas = getattr(frame, "_parent_canvas", getattr(frame, "_canvas", None))
    before = len(canvas.bind("<Configure>").splitlines())
    enable_auto_hiding_scrollbar(frame)
    assert len(canvas.bind("<Configure>").splitlines()) == before


# --- Highlighting in search result lists ----------------------------------------

def test_case_list_highlights_secondary_match(root):
    from ui.widgets.case_list_widget import CaseListWidget

    c1 = Case(case_id="2026-0001", customer=CaseCustomer(customer_id="C1", practice_name="Praxis Nord"),
              classification=Classification(title="Netzwerkfehler"),
              workflow_status=WorkflowStatus(followup_note="Warten auf Router Lieferung"))
    widget = CaseListWidget(root, on_case_selected=lambda c: None, on_search_changed=lambda s: None)
    widget.pack()
    widget.search_entry.insert(0, "router")
    widget.set_cases([c1])

    card = _frames(widget.scroll_frame)[0]
    assert any("2026-0001" in t for t in _label_texts(card) + _text_contents(card))
    assert any("Router" in t for t in _text_contents(card))


def test_wiki_widget_highlights_results(root):
    from unittest.mock import MagicMock
    from ui.widgets.wiki_widget import WikiWidget

    wiki = MagicMock()
    wiki.search.return_value = [{"id": "doc1", "title": "Drucker Handbuch",
                                 "snippet": "Anleitung zur Installation von CUPS", "url": "http://example.com/1"}]
    widget = WikiWidget(root, wiki)
    widget.pack()
    widget.search_entry.insert(0, "Drucker")
    widget.on_search()

    cards = _frames(widget.scroll_frame)
    assert len(cards) == 1
    assert any("Drucker" in t for t in _text_contents(cards[0]))


def test_colleague_dialog_highlights_notes_match(root, storage):
    from ui.dialogs.colleague_management_dialog import ColleagueManagementDialog

    storage.save_colleagues([
        Colleague(name="Max Mustermann", username="mmuster", department="Support", extension="123", notes="Experte für Drucker"),
        Colleague(name="Erika Musterfrau", username="emuster", department="Vertrieb", extension="124"),
    ])
    dialog = ColleagueManagementDialog(root, storage_service=storage)
    dialog.search_entry.insert(0, "Drucker")
    dialog.on_search_changed()

    cards = _frames(dialog.list_scroll)
    assert len(cards) == 1
    assert any("Drucker" in t for t in _text_contents(cards[0]))
    dialog.destroy()


def test_snippet_picker_highlights_match(root, tmp_path):
    from services.snippet_service import SnippetService
    from ui.dialogs.snippet_picker_dialog import SnippetPickerDialog

    svc = SnippetService(workspace_dir=tmp_path)
    svc.snippets = [
        Snippet(snippet_id="S-1", title="Drucker Reset", shortcut="!prt", content="Drucker aus und ein.", category="Allgemein"),
        Snippet(snippet_id="S-2", title="Mail Vorlage", shortcut="!mail", content="Sehr geehrte Damen", category="Allgemein"),
    ]
    svc.save_snippets()
    dialog = SnippetPickerDialog(root, snippet_service=svc, on_snippet_selected=lambda text: None)
    dialog.search_entry.insert(0, "Reset")
    dialog.refresh_snippet_list()

    cards = _frames(dialog.list_scroll)
    assert len(cards) == 1
    assert any("Reset" in t for t in _text_contents(cards[0]))
    dialog.destroy()


def test_help_dialog_highlights_navigation(root):
    from ui.dialogs.help_dialog import HelpDialog

    dialog = HelpDialog(root)
    dialog.search_entry.insert(0, "Hilfe")
    dialog.on_search_changed()
    assert any(_text_contents(card) for card in _frames(dialog.nav_scroll))
    dialog.destroy()


@pytest.mark.parametrize("tab, attr, entry, render, scroll, query, expected", [
    ("tags", "available_tags", "search_tag_entry", "render_tags_list", "tags_scroll", "druck", "Rezeptdruck"),
    ("modules", "available_module_tags", "search_mod_entry", "render_modules_list", "modules_scroll", "kalender", "Terminkalender"),
])
def test_tag_management_dialog_highlights_and_keeps_delete_button(root, storage, tab, attr, entry, render, scroll, query, expected):
    from ui.dialogs.tag_management_dialog import TagManagementDialog

    profile = UserProfile(**{attr: ["Dringend", "Rezeptdruck", "Terminkalender"]})
    dialog = TagManagementDialog(root, profile=profile, storage_service=storage, initial_tab=tab)

    def search(text):
        getattr(dialog, entry).delete(0, "end")
        getattr(dialog, entry).insert(0, text)
        getattr(dialog, render)()
        dialog.update()
        rows = _frames(getattr(dialog, scroll))
        assert len(rows) == 1
        texts = [w for w in rows[0].winfo_children() if isinstance(w, tk.Text)]
        buttons = [w for w in rows[0].winfo_children() if isinstance(w, ctk.CTkButton)]
        assert len(texts) == 1 and len(buttons) == 1
        assert buttons[0].winfo_width() == 90 and buttons[0].winfo_x() > texts[0].winfo_x()
        return texts[0].get("1.0", "end - 1 chars")

    assert expected in search(query)
    if tab == "tags":
        # a very long tag must not crush or hide the delete button
        profile.available_tags.append("Ein extrem langer Tag-Name fuer spezielle Abrechnung und Druckvorgaenge")
        assert "Druckvorgaenge" in search("Druckvorgaenge")
    dialog.destroy()


def test_module_tag_picker_highlights_and_label_click_toggles(root):
    from ui.widgets.dynamic_form_widget import ModuleTagPickerPopup

    popup = ModuleTagPickerPopup(root, available_tags=["Abrechnung", "Rezeptdruck", "Dokumentation"],
                                 selected_tags=[], on_apply=lambda tags: None)
    popup.update()
    boxes = [w for w in popup.scroll_frame.winfo_children() if isinstance(w, ctk.CTkCheckBox)]
    assert len(boxes) == 3
    expected_height = boxes[0].winfo_height()

    popup.search_entry.insert(0, "druck")
    popup.render_tag_checkboxes()
    popup.update()
    rows = _frames(popup.scroll_frame)
    assert len(rows) == 1 and rows[0].winfo_height() == expected_height
    text = [w for w in rows[0].winfo_children() if isinstance(w, tk.Text)][0]
    assert text.get("1.0", "end - 1 chars") == "Rezeptdruck"
    text.event_generate("<Button-1>", x=5, y=5)
    assert "Rezeptdruck" in popup.selected_tags
    popup.destroy()


def test_customer_dialog_shows_match_summary_line(root, storage):
    from ui.dialogs.customer_management_dialog import CustomerManagementDialog

    service = CustomerService(storage)
    service.save_customer(Customer(customer_id="00109", practice_name="Praxis Welz", contacts=WELZ.contacts))
    service.save_customer(Customer(customer_id="00062", practice_name="Praxis Zeglin Alte Post", contacts=ZEGLIN.contacts))
    dialog = CustomerManagementDialog(root, service)
    dialog.on_search_changed()
    assert len(_frames(dialog.list_scroll)) == 2

    dialog.search_entry.insert(0, "tr")
    dialog.on_search_changed()
    cards = {}
    for card in _frames(dialog.list_scroll):
        texts = _text_contents(card) + _label_texts(card)
        cards["welz" if any("Welz" in t for t in texts) else "zeglin"] = texts
    assert any("Katrin, katrin.schmidt@ergotherapie-nwm.de" in t for t in cards["welz"])
    assert any("Travemünde" in t for t in cards["zeglin"])

    dialog.select_customer("00109")
    assert dialog.selected_customer.customer_id == "00109"
    dialog.destroy()


def test_customer_search_finds_by_name(storage):
    storage.save_customers([Customer(customer_id=f"CUST-{i:03d}", practice_name=f"Praxis Dr. Benchmark {i}",
                                     contacts=[Contact(name=f"Dr. Contact {i}")]) for i in range(1, 6)])
    results = CustomerService(storage).search_customers("Benchmark 4")
    assert [c.customer_id for c in results] == ["CUST-004"]


# --- Case list renders in batches instead of rebuilding everything per keystroke ---

def _bulk_cases(count: int) -> list[Case]:
    return [Case(
        case_id=f"BULK-CASE-{i:04d}",
        customer=CaseCustomer(customer_id="INTERNAL" if i % 7 == 0 else f"CUST-{i:03d}",
                              practice_name=f"Praxis Dr. Benchmark {i % 100}", is_vip=(i % 10 == 0)),
        classification=Classification(title=f"Performance Test Case Title {i}",
                                      urgency_level=[UrgencyLevel.GREEN, UrgencyLevel.YELLOW, UrgencyLevel.RED][i % 3],
                                      tags=["Abrechnung"] if i % 2 else ["Hardware"]),
        workflow_status=WorkflowStatus(board_column=[BoardColumn.NEW, BoardColumn.WAITING, BoardColumn.DONE][i % 3],
                                       current_actor=[Actor.SUPPORT, Actor.DEVELOPMENT, Actor.TECH, Actor.CUSTOMER][i % 4]),
        timeline=[TimelineEntry(timestamp="2026-08-20T10:00:00", author="agent1", note=f"Initial note {i}")],
    ) for i in range(1, count + 1)]


@pytest.fixture
def case_list(root):
    from ui.widgets.case_list_widget import CaseListWidget

    root.geometry("400x700")

    def make(count):
        widget = CaseListWidget(root, on_case_selected=lambda c: None, on_search_changed=lambda q: None)
        widget.pack(fill="both", expand=True)
        widget.cases = _bulk_cases(count)
        widget.render_list()
        root.update()
        return widget
    return make


def test_render_list_builds_only_a_batch_and_scrolling_loads_the_rest(root, case_list):
    """Building every card per keystroke is what made the search feel sluggish."""
    from ui.widgets.case_list_widget import CaseListWidget

    widget = case_list(40)
    assert 0 < widget._rendered_count <= CaseListWidget.RENDER_BATCH_SIZE * 3
    assert widget._rendered_count < 40
    assert len(widget._card_widgets) == widget._rendered_count

    # scroll like the user does (not calling _on_scrolled directly); each step loads one batch
    canvas = widget._scroll_canvas()
    for _ in range(40):
        canvas.yview_moveto(1.0)
        root.update()
        if widget._rendered_count >= 40:
            break
    assert set(widget._card_widgets) == {c.case_id for c in widget.cases}


def test_selecting_a_case_below_the_fold_renders_it_first(root, case_list):
    widget = case_list(60)
    picked: list[str] = []
    widget.on_case_selected = lambda c: picked.append(c.case_id)
    target = widget.cases[-1]
    assert target.case_id not in widget._card_widgets

    widget.select_case(target)
    root.update()
    assert target.case_id in widget._card_widgets
    assert picked == [target.case_id]


def test_card_tooltip_binds_only_on_first_hover(root, case_list):
    """CTkTooltip binds nine events per descendant - far too much per keystroke."""
    from ui.widgets.ctk_tooltip import CTkTooltip

    widget = case_list(20)
    card = next(iter(widget._card_widgets.values()))
    label = [c for c in card.winfo_children() if isinstance(c, ctk.CTkLabel)][0]

    def enter_bindings(w) -> int:
        return len([ln for ln in (w.bind("<Enter>") or "").splitlines() if ln.strip()])

    try:
        assert enter_bindings(label._label) == 0
        card._canvas.event_generate("<Enter>", x=5, y=5)
        root.update()
        assert enter_bindings(label._label) > 0

        # an open tooltip is closed by dismiss_all (pointer faked inside the widget)
        tip = CTkTooltip(label, "Hinweis", delay_ms=0)
        label.winfo_pointerx = lambda: label.winfo_rootx() + 1
        label.winfo_pointery = lambda: label.winfo_rooty() + 1
        tip.show_tooltip()
        assert tip.tooltip_window is not None
        CTkTooltip.dismiss_all()
        assert tip.tooltip_window is None
    finally:
        CTkTooltip.dismiss_all()
