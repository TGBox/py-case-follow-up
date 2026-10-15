"""E2E: profile settings (name, signature, font scale) and the switch DE -> EN apply live and survive a restart."""

import customtkinter as ctk
import pytest

from services.i18n_service import get_i18n, tr
from ui.dialogs.new_case_dialog import NewCaseDialog
from ui.dialogs.profile_settings_dialog import ProfileSettingsDialog

from e2e_helpers import (
    choose, dialog_closed, find_button, find_dialog, fresh_storage, quit_via_menu, type_into, visible_texts,
)


class KnownBug(AssertionError):
    """Raised only for the known bugs below, so any other failure of this flow still fails the test."""


NAME = "Dana Hotline"
SIGNATURE = "Viele Grüße\nDana Hotline\nSupport-Team"


def _open_profile_settings(app) -> ProfileSettingsDialog:
    app.user_btn.invoke()
    return find_dialog(app, ProfileSettingsDialog)


def _assert_english_ui(app):
    """Menu bar, the active cockpit view and a freshly opened dialog all speak English."""
    menu = visible_texts(app.menu_frame)
    assert "+ New Case (Ctrl+N)" in menu and "Exit" in menu and "Help" in menu
    assert app.stammdaten_combo.get() == "⚙ Master Data"

    cockpit = app.cockpit_view
    assert app.active_view is cockpit
    assert cockpit.case_title_label.cget("text") == "Please select a case"
    assert cockpit.followup_btn.cget("text") == "🔔 Follow-up"
    assert cockpit.complete_btn.cget("text") == "✓ Done"

    find_button(app.menu_frame, "+ New Case (Ctrl+N)").invoke()
    dlg = find_dialog(app, NewCaseDialog)
    texts = visible_texts(dlg)
    assert "Record New Support Case" in texts and "Create Case" in texts and "Cancel" in texts
    find_button(dlg, "Cancel").invoke()
    dialog_closed(app, dlg)


@pytest.mark.xfail(
    raises=KnownBug,
    strict=True,
    reason=(
        "BUG 1: saving a new font scale together with a language switch drops the font scale. "
        "save_ui_settings() sets the language first; that fires the dialog's refresh_ui_tab_labels(), which "
        "resets font_scale_combo to the stored profile value, and only then is the combo read. "
        "Repro: profile settings -> 110% + English -> save -> profile.ui_settings.font_scale == 1.0. "
        "BUG 2: after a restart in English the window title stays German ('Support-Cockpit & ...'): "
        "SupportCockpitApp.__init__ sets the title before it applies the profile language."
    ),
)
def test_language_and_profile(tmp_path, start_app):
    known_bugs: list[str] = []  # collected along the flow, raised at the very end

    def check_font_scale(where: str, actual) -> None:
        if actual != 1.1:
            known_bugs.append(f"font scale lost ({where}: {actual!r})")

    def check_title(app) -> None:
        if app.title() != "Support Cockpit & Ticket Management":
            known_bugs.append(f"window title not English: {app.title()!r}")

    app = start_app(tmp_path)
    assert get_i18n().current_language == "de"
    assert find_button(app.menu_frame, "+ Neuer Fall (Strg+N)")

    # Change name, signature, font scale and language in the profile settings and save.
    dlg = _open_profile_settings(app)
    type_into(dlg.user_name_entry, NAME)
    type_into(dlg.user_sig_txt, SIGNATURE)
    choose(dlg.font_scale_combo, tr("profile.font_scale_110", "110% (Mittel)"))
    assert ctk.ScalingTracker.widget_scaling == 1.1  # live preview while choosing
    choose(dlg.language_combo, "English")
    find_button(dlg, tr("profile.save_btn", "💾 Einstellungen Speichern")).invoke()

    # The open settings dialog itself switched to English, too.
    assert dlg.status_lbl.cget("text") == "✅ Settings & paths saved!"
    assert dlg.save_btn.cget("text") == "💾 Save Settings"
    find_button(dlg, "Close").invoke()
    dialog_closed(app, dlg)

    assert get_i18n().current_language == "en"
    assert app.user_btn.cget("text") == NAME
    check_font_scale("scaling after save", ctk.ScalingTracker.widget_scaling)
    _assert_english_ui(app)
    check_title(app)

    on_disk = fresh_storage(tmp_path).load_profile()
    assert (on_disk.user.name, on_disk.user.email_signature) == (NAME, SIGNATURE)
    assert on_disk.ui_settings.language == "en"
    check_font_scale("saved font_scale", on_disk.ui_settings.font_scale)

    # Restart: language, scaling and profile values come back from disk.
    quit_via_menu(app)
    get_i18n().current_language = "de"  # a new process starts with the default language
    ctk.set_widget_scaling(1.0)
    app2 = start_app(tmp_path)

    assert get_i18n().current_language == "en"
    check_font_scale("scaling after restart", ctk.ScalingTracker.widget_scaling)
    assert app2.user_btn.cget("text") == NAME
    _assert_english_ui(app2)
    check_title(app2)

    dlg = _open_profile_settings(app2)
    assert dlg.user_name_entry.get() == NAME
    assert dlg.user_sig_txt.get("1.0", "end-1c") == SIGNATURE
    assert dlg.language_combo.get() == "English"
    if dlg.font_scale_combo.get() != "110% (Medium)":
        known_bugs.append(f"font scale lost (settings after restart: {dlg.font_scale_combo.get()!r})")
    find_button(dlg, "Close").invoke()
    dialog_closed(app2, dlg)

    if known_bugs:
        raise KnownBug("; ".join(known_bugs))
