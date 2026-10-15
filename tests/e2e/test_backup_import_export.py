"""E2E: ZIP backup of a seeded workspace, import into an empty one, then export/print a case to a file."""

import zipfile
from html.parser import HTMLParser
from tkinter import filedialog

import pytest

from services.i18n_service import tr
from services.seed_service import SeedService
from ui.dialogs.export_dialog import ExportDialog
from ui.dialogs.new_case_dialog import NewCaseDialog
from ui.dialogs.profile_settings_dialog import ProfileSettingsDialog
from ui.dialogs.zip_import_dialog import ZipImportPathDialog

from e2e_helpers import (
    choose, click, dialog_closed, find_button, find_dialog, fresh_storage, quit_via_menu, type_into,
)


class KnownBug(AssertionError):
    """Raised only for the known import bug, so any other failure of this flow still fails the test."""


def _rendered_text(html_doc: str) -> str:
    """The text a browser shows for an HTML document (tags dropped, entities resolved)."""
    parts: list[str] = []
    parser = HTMLParser(convert_charrefs=True)
    parser.handle_data = parts.append
    parser.feed(html_doc)
    return " ".join(parts)


def _open_profile_settings(app) -> ProfileSettingsDialog:
    app.user_btn.invoke()
    return find_dialog(app, ProfileSettingsDialog)


def _import_zip(app, workspace) -> None:
    """Profile settings -> "📥 Datensicherung aus ZIP importieren..." -> unpack into the current workspace."""
    dlg = _open_profile_settings(app)
    find_button(dlg, tr("profile.backup_imp_btn", "📥 Datensicherung aus ZIP importieren...")).invoke()
    imp = find_dialog(app, ZipImportPathDialog)
    assert imp.root_entry.get() == str(workspace)  # default target: the current workspace
    find_button(imp, tr("zip_import.unpack_btn", "📥 Daten entpacken & importieren")).invoke()
    dialog_closed(app, imp)
    assert dlg.status_lbl.cget("text").startswith("✅")
    find_button(dlg, tr("common.close", "Schließen")).invoke()
    dialog_closed(app, dlg)


@pytest.mark.xfail(
    raises=KnownBug,
    strict=True,
    reason=(
        "BUG: ZIP import via profile settings unpacks the files, but the running app keeps StorageService's "
        "cached (empty) cases/customers - on_profile_updated() reloads from cache. The imported cases only "
        "appear after a restart, and creating a case before that overwrites the imported cases.json "
        "(9 imported cases -> 1). Repro: empty workspace -> import ZIP -> app.cases == [] -> new case -> "
        "cases.json holds only the new case."
    ),
)
def test_backup_import_export(tmp_path, start_app, monkeypatch):
    ws_a, ws_b = tmp_path / "ws_a", tmp_path / "ws_b"
    zip_path = tmp_path / "Komplett_Backup.zip"
    SeedService(fresh_storage(ws_a)).run_seed(force=True)

    save_dialogs: list[dict] = []
    save_targets = iter([zip_path, tmp_path / "Fallbericht.html", tmp_path / "export.md"])

    def fake_save_dialog(**kwargs):
        save_dialogs.append(kwargs)
        return str(next(save_targets))

    monkeypatch.setattr(filedialog, "asksaveasfilename", fake_save_dialog)
    monkeypatch.setattr(filedialog, "askopenfilename", lambda **kwargs: str(zip_path))

    # 1. Export: profile settings -> "Speicherort & Datenexport" -> ZIP backup.
    app_a = start_app(ws_a)
    assert len(app_a.cockpit_view.left_frame._card_widgets) > 0  # demo cases are on screen
    dlg = _open_profile_settings(app_a)
    find_button(dlg, tr("profile.backup_exp_btn", "📦 Komplett-Backup als ZIP exportieren...")).invoke()
    assert save_dialogs[0]["defaultextension"] == ".zip"
    assert dlg.status_lbl.cget("text").startswith("✅")
    with zipfile.ZipFile(zip_path) as zf:
        names = {n.replace("\\", "/") for n in zf.namelist()}
    assert {"data/cases.json", "data/customers.json", "data/app_profile.json"} <= names
    find_button(dlg, tr("common.close", "Schließen")).invoke()
    dialog_closed(app_a, dlg)
    quit_via_menu(app_a)

    # What the backup must carry: the workspace as app A left it (startup moved
    # old completed demo cases to the archive).
    source = fresh_storage(ws_a)
    active_ids = {c.case_id for c in source.load_cases()}
    archived_ids = {c.case_id for c in source.load_archive()}
    customer_ids = {c.customer_id for c in source.load_customers()}
    assert len(active_ids | archived_ids) == 12 and active_ids and customer_ids

    # 2. Import into an empty workspace through the import dialog.
    app_b = start_app(ws_b)
    assert app_b.cases == []
    _import_zip(app_b, ws_b)

    on_disk = fresh_storage(ws_b)
    assert {c.case_id for c in on_disk.load_cases()} == active_ids
    assert {c.case_id for c in on_disk.load_archive()} == archived_ids
    assert {c.customer_id for c in on_disk.load_customers()} == customer_ids

    # Known bug (collected here, raised at the very end): the running app keeps its
    # stale, empty case list, and a case created now overwrites the imported cases.json.
    known_bugs: list[str] = []
    if {c.case_id for c in app_b.cases} != active_ids:
        known_bugs.append(f"app shows {len(app_b.cases)} cases right after the import instead of {len(active_ids)}")
    find_button(app_b.menu_frame, tr("menu.new_case", "+ Neuer Fall (Strg+N)")).invoke()
    new_dlg = find_dialog(app_b, NewCaseDialog)
    type_into(new_dlg.title_entry, "Neuer Fall nach dem Import")
    find_button(new_dlg, tr("new_case_dialog.create_btn", "Fall anlegen")).invoke()
    dialog_closed(app_b, new_dlg)
    new_id = next(c.case_id for c in app_b.cases if c.classification.title == "Neuer Fall nach dem Import")
    quit_via_menu(app_b)
    after_new_case = {c.case_id for c in fresh_storage(ws_b).load_cases()}
    assert new_id in after_new_case
    if after_new_case != active_ids | {new_id}:
        known_bugs.append(f"creating a case after the import left {len(after_new_case)} cases in cases.json "
                          f"instead of {len(active_ids) + 1} - the imported cases were overwritten")

    # Recover like a user would: import the backup once more (it overwrites cases.json).
    app_r = start_app(ws_b)
    _import_zip(app_r, ws_b)
    quit_via_menu(app_r)

    # 3. Restart on the imported workspace, open one case and export it via "Export & Übergabe".
    app_c = start_app(ws_b)
    assert {c.case_id for c in app_c.cases} == active_ids
    left = app_c.cockpit_view.left_frame
    case = next(c for c in app_c.cases if c.timeline and c.case_id in left._card_widgets)
    click(left._card_widgets[case.case_id])
    cockpit = app_c.cockpit_view
    assert cockpit.current_case.case_id == case.case_id
    choose(cockpit.more_actions_combo, tr("cockpit.export_handover", "📤 Export & Übergabe"))
    exp = find_dialog(app_c, ExportDialog)

    # Print tab: "💾 Speichern..." writes the HTML case report.
    exp.tabview.set(tr("export_dialog.tab_print", "Drucken & Akte"))
    find_button(exp, tr("case_print.save_btn", "💾 Speichern...")).invoke()
    assert save_dialogs[1]["initialfile"] == f"Fallbericht_{case.case_id}.html"
    report = _rendered_text((tmp_path / "Fallbericht.html").read_text(encoding="utf-8"))
    for expected in (case.case_id, case.classification.title, case.customer.practice_name, case.timeline[0].note.splitlines()[0]):
        assert expected in report
    dialog_closed(app_c, exp)  # saving the report closes the dialog

    # Export tab: "In Datei speichern..." writes the rendered template.
    choose(cockpit.more_actions_combo, tr("cockpit.export_handover", "📤 Export & Übergabe"))
    exp = find_dialog(app_c, ExportDialog)
    exp.force_chk.toggle()  # "export despite missing fields" - re-renders the preview
    preview = exp.preview_textbox.get("1.0", "end-1c")
    assert case.customer.practice_name in preview and case.customer.customer_id in preview
    find_button(exp, tr("export_dialog.save_file_btn", "In Datei speichern...")).invoke()
    assert (tmp_path / "export.md").read_text(encoding="utf-8") == preview

    if known_bugs:
        raise KnownBug("; ".join(known_bugs))
