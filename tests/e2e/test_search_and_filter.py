"""E2E: a case for a specific practice is found via quick search, customer name/number and a quick filter, then opened."""

from models.case import Case, CaseCustomer, Classification, WorkflowStatus
from models.customer import Contact, Customer
from services.i18n_service import tr
from ui.dialogs.new_case_dialog import NewCaseDialog
from ui.widgets.searchable_combobox import SearchableCombobox

from e2e_helpers import (
    click, dialog_closed, find_button, find_dialog, fresh_storage, press_key, quit_via_menu, type_into,
    wait_until, walk,
)

ZANDER = Customer(customer_id="K-4711", practice_name="Praxis Dr. Zander", is_vip=True, city="Leipzig",
                  contacts=[Contact(name="Dr. Ina Zander", phone="0341 112233")])
MUELLER = Customer(customer_id="K-0815", practice_name="Praxis Müller", city="Halle")
MUELLER_CASE = Case(
    case_id="T-2026-MUE1",
    created_at="2026-10-01T09:00:00",
    updated_at="2026-10-01T09:00:00",
    customer=CaseCustomer(customer_id="K-0815", practice_name="Praxis Müller"),
    classification=Classification(title="Drucker druckt keine Rezepte"),
    workflow_status=WorkflowStatus(),
)
TITLE = "Kartenlesegerät wird nicht erkannt"


def _listed_ids(app) -> set[str]:
    return set(app.cockpit_view.left_frame._card_widgets)


def _search(app, text: str) -> set[str]:
    """Types into the case list's search field and waits until the debounced search really ran with it."""
    assert app.search_query != text, "same query again - waiting for it would prove nothing"
    entry = app.cockpit_view.left_frame.search_entry
    type_into(entry, text)
    press_key(entry, "<KeyRelease>")
    # The list only filters after the typing pause; waiting on the list alone could
    # return on the previous query's identical result.
    wait_until(app, lambda: app.search_query == text, what=f"search {text!r} to be applied")
    app.update()
    return _listed_ids(app)


def test_search_and_filter(tmp_path, start_app):
    seed = fresh_storage(tmp_path)
    seed.save_customers([MUELLER, ZANDER], sync=True)
    seed.save_cases([MUELLER_CASE], sync=True)

    app = start_app(tmp_path)
    left = app.cockpit_view.left_frame
    assert _listed_ids(app) == {MUELLER_CASE.case_id}

    # Create a case for Dr. Zander, picking the practice in the searchable customer picker.
    find_button(app.menu_frame, tr("menu.new_case", "+ Neuer Fall (Strg+N)")).invoke()
    dlg = find_dialog(app, NewCaseDialog)
    picker = next(w for w in walk(dlg) if isinstance(w, SearchableCombobox))
    assert picker.get() == "Praxis Müller (K-0815)"  # first practice preselected
    picker.btn.invoke()
    wait_until(app, lambda: picker._popover is not None and picker._popover.winfo_exists(), what="customer popover")
    type_into(picker.search_entry, "Zander")
    press_key(picker.search_entry, "<Return>")
    assert picker.get() == "Praxis Dr. Zander (K-4711)"
    type_into(dlg.title_entry, TITLE)
    find_button(dlg, tr("new_case_dialog.create_btn", "Fall anlegen")).invoke()
    dialog_closed(app, dlg)

    zander_case = next(c for c in app.cases if c.case_id != MUELLER_CASE.case_id)
    assert zander_case.customer.customer_id == "K-4711"
    assert _listed_ids(app) == {MUELLER_CASE.case_id, zander_case.case_id}

    # Show the Müller case in the cockpit first, so opening the hit visibly switches.
    click(left._card_widgets[MUELLER_CASE.case_id])
    assert app.cockpit_view.current_case.case_id == MUELLER_CASE.case_id

    expected = {
        "kartenlese": {zander_case.case_id},      # title words
        "Zander": {zander_case.case_id},          # customer name
        "K-4711": {zander_case.case_id},          # customer number
        "K-0815": {MUELLER_CASE.case_id},         # ... and the other customer's number
        "Halle": set(),                           # city is not part of the case snapshot
    }
    for query, ids in expected.items():
        assert _search(app, query) == ids, query
        assert left.count_label.cget("text") == tr("case_list.count_cases", "{count} Support-Fälle", count=len(ids))

    # Quick filter button "Dringend" (vip:true): only the VIP practice remains.
    assert _search(app, "") == {MUELLER_CASE.case_id, zander_case.case_id}
    left.qfilter_urgent_btn.invoke()
    assert left.search_entry.get() == "vip:true"
    assert _listed_ids(app) == {zander_case.case_id}

    # Open the hit: the cockpit shows the Zander case.
    click(left._card_widgets[zander_case.case_id])
    cockpit = app.cockpit_view
    assert cockpit.current_case.case_id == zander_case.case_id
    assert cockpit.case_title_label.cget("text") == f"{zander_case.case_id}: {TITLE}"
    assert "Praxis Dr. Zander (K-4711)" in cockpit.kunde_label.cget("text")
    assert "Dr. Ina Zander" in cockpit.ansprechpartner_label.cget("text")

    # "Alle" clears the filter again.
    left.qfilter_all_btn.invoke()
    assert left.search_entry.get() == ""
    assert _listed_ids(app) == {MUELLER_CASE.case_id, zander_case.case_id}

    # Restart on the same workspace: the new case is still found and opens.
    quit_via_menu(app)
    app2 = start_app(tmp_path)
    assert {c.case_id for c in fresh_storage(tmp_path).load_cases()} == {MUELLER_CASE.case_id, zander_case.case_id}
    assert _search(app2, "K-4711") == {zander_case.case_id}
    click(app2.cockpit_view.left_frame._card_widgets[zander_case.case_id])
    assert app2.cockpit_view.current_case.case_id == zander_case.case_id
    assert app2.cockpit_view.case_title_label.cget("text") == f"{zander_case.case_id}: {TITLE}"
