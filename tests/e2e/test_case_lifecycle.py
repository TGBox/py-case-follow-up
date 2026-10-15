"""E2E: a case from creation through note, follow-up, handover and completion survives an app restart."""

from datetime import date, timedelta

from enums import Actor, LayoutMode, get_actor_display, get_layout_display
from services.i18n_service import tr
from ui.dialogs.followup_dialog import FollowupDialog
from ui.dialogs.handover_dialog import HandoverDialog
from ui.dialogs.new_case_dialog import NewCaseDialog
from ui.views.board_view import KanbanCardWidget

from e2e_helpers import (
    choose, dialog_closed, find_button, find_dialog, fresh_storage, quit_via_menu,
    type_into, visible_texts, wait_until, walk,
)

TITLE = "Rezeptdruck bricht mit Fehler 0815 ab"
NOTE = "Kunde zurückgerufen, Logdatei angefordert"
FOLLOWUP_NOTE = "Logdatei prüfen"


def _board_card(app, case_id):
    cards = [w for w in walk(app.board_view) if isinstance(w, KanbanCardWidget) and w.case.case_id == case_id]
    return cards[0] if cards else None


def _board_column_of(app, case_id):
    for col_key, scroll in app.board_view.col_scrolls.items():
        if any(isinstance(w, KanbanCardWidget) and w.case.case_id == case_id for w in walk(scroll)):
            return col_key
    return None


def test_case_lifecycle(tmp_path, start_app):
    app = start_app(tmp_path)
    cockpit = app.cockpit_view

    # 1. New case via the menu bar button and the "new case" dialog.
    find_button(app.menu_frame, tr("menu.new_case", "+ Neuer Fall (Strg+N)")).invoke()
    dlg = find_dialog(app, NewCaseDialog)
    find_button(dlg, tr("new_case_dialog.create_btn", "Fall anlegen")).invoke()
    assert dlg.winfo_exists()  # title is required
    assert dlg.error_label.cget("text") == tr("new_case.title_required", "Bitte einen Titel für den Fall eingeben.")
    type_into(dlg.title_entry, TITLE)
    find_button(dlg, tr("new_case_dialog.create_btn", "Fall anlegen")).invoke()
    dialog_closed(app, dlg)

    assert len(app.cases) == 1
    case_id = app.cases[0].case_id
    assert cockpit.case_title_label.cget("text") == f"{case_id}: {TITLE}"

    # 2. Timeline note through the cockpit sidebar.
    find_button(cockpit.center_frame, tr("cockpit.note", "📝 Notiz")).invoke()
    type_into(cockpit.timeline_widget.note_textbox, NOTE)
    find_button(cockpit.timeline_widget, tr("cockpit.add_note_btn", "+ Notiz Hinzufügen")).invoke()
    app.update()
    assert NOTE in visible_texts(cockpit.timeline_widget.scroll_frame)

    # 3. Follow-up via the cockpit toolbar: "+ 1 Tag" preset plus a note.
    find_button(cockpit.center_frame, tr("cockpit.followup", "🔔 Wiedervorlage")).invoke()
    fdlg = find_dialog(app, FollowupDialog)
    find_button(fdlg, tr("followup.preset_1d", "+ 1 Tag")).invoke()
    type_into(fdlg.note_entry, FOLLOWUP_NOTE)
    find_button(fdlg, tr("followup.save_btn", "💾 Wiedervorlage Speichern")).invoke()
    dialog_closed(app, fdlg)
    assert FOLLOWUP_NOTE in cockpit.wv_note_label.cget("text")

    app.storage_service.flush_all_saves()
    on_disk = fresh_storage(tmp_path).load_cases()[0]
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    assert on_disk.workflow_status.followup_at.startswith(tomorrow)
    assert on_disk.workflow_status.followup_note == FOLLOWUP_NOTE
    assert [e.note for e in on_disk.timeline] == [NOTE]

    # 4. Board: the card sits in the follow-up column; hand it over to "Technik".
    choose(app.layout_combo, get_layout_display(LayoutMode.BOARD.value))
    assert app.active_view is app.board_view
    assert _board_column_of(app, case_id) == "followup"
    find_button(_board_card(app, case_id), tr("board.handover", "👤 Übergeben")).invoke()
    hdlg = find_dialog(app, HandoverDialog)
    choose(hdlg.actor_combo, get_actor_display(Actor.TECH))
    type_into(hdlg.note_entry, "Ticket an Technik")
    find_button(hdlg, tr("handover_dialog.confirm_btn", "🤝 Übergabe bestätigen")).invoke()
    dialog_closed(app, hdlg)
    assert f"👤 {get_actor_display(Actor.TECH)}" in visible_texts(_board_card(app, case_id))

    # 5. Complete it from the card: it moves to the "done" column.
    find_button(_board_card(app, case_id), tr("cockpit.complete", "✓ Erledigt")).invoke()
    wait_until(app, lambda: _board_column_of(app, case_id) == "completed", what="card in completed column")

    # 6. Quit through the menu bar, start again on the same workspace.
    quit_via_menu(app)
    app2 = start_app(tmp_path)

    reloaded = fresh_storage(tmp_path).load_cases()
    assert [c.case_id for c in reloaded] == [case_id]
    case = reloaded[0]
    assert case.classification.title == TITLE
    assert case.workflow_status.is_completed
    assert case.workflow_status.followup_at == ""  # completing clears the reminder date ...
    assert case.workflow_status.followup_note == FOLLOWUP_NOTE  # ... but keeps its note
    assert case.workflow_status.current_actor == Actor.TECH
    notes = [e.note for e in case.timeline]
    assert notes[0] == NOTE
    assert any("Ticket an Technik" in n for n in notes)
    assert notes[-1] == tr("timeline.case_completed", "Fall auf erledigt gesetzt.")

    # The restarted app opens on the board (last layout) with the card in "done".
    assert app2.active_view is app2.board_view
    assert _board_column_of(app2, case_id) == "completed"
    find_button(_board_card(app2, case_id), tr("board.cockpit_btn", "🎯 Cockpit")).invoke()
    app2.update()
    assert app2.active_view is app2.cockpit_view
    status = tr("cockpit.status_completed_tag", "✓ ERLEDIGT")
    assert app2.cockpit_view.case_title_label.cget("text") == f"{case_id}: {TITLE}  [{status}]"
    assert NOTE in visible_texts(app2.cockpit_view.timeline_widget.scroll_frame)
