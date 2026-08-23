import pytest
from models.profile import Colleague, ShortcutSettings
from services.search_service import SearchService, parse_search_query
from models.case import Case, CaseCustomer


def test_colleague_absence_fields():
    col = Colleague(
        username="mmueller",
        name="Max Müller",
        department="Support",
        is_absent=True,
        absence_reason="Urlaub bis 30.08.",
    )
    col_dict = col.to_dict()
    assert col_dict["is_absent"] is True
    assert col_dict["absence_reason"] == "Urlaub bis 30.08."

    loaded_col = Colleague.from_dict(col_dict)
    assert loaded_col.is_absent is True
    assert loaded_col.absence_reason == "Urlaub bis 30.08."


def test_hotkey_conflict_validation():
    shortcuts = ShortcutSettings(
        new_case="<Control-n>",
        export_dialog="<Control-e>",
        wiki_search="<Control-w>",
    )
    keys = [shortcuts.new_case, shortcuts.export_dialog, shortcuts.wiki_search]
    assert len(keys) == len(set(keys))

    # Duplicate shortcut detection
    duplicate_keys = ["<Control-n>", "<Control-n>", "<Control-w>"]
    assert len(duplicate_keys) != len(set(duplicate_keys))


def test_quick_filter_search_tokens():
    search_svc = SearchService()

    c_vip = Case(case_id="T-01", customer=CaseCustomer(is_vip=True))
    c_int = Case(case_id="T-02", customer=CaseCustomer(customer_id="INTERNAL", practice_name="Intern"))
    c_norm = Case(case_id="T-03", customer=CaseCustomer(is_vip=False))

    cases = [c_vip, c_int, c_norm]

    # Test is:internal
    res_int = search_svc.filter_cases(cases, "is:internal")
    assert len(res_int) == 1
    assert res_int[0].case_id == "T-02"

    # Test vip:true
    res_vip = search_svc.filter_cases(cases, "vip:true")
    assert len(res_vip) == 1
    assert res_vip[0].case_id == "T-01"
