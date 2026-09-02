from typing import Any
import customtkinter as ctk
from typing import Callable
from models.profile import UserProfile
from services.storage_service import StorageService
from enums import LayoutMode, SyncMode, get_layout_display, get_layout_val_from_display, LAYOUT_DISPLAY
from ui.dialogs.profile_settings_ai_tab import AiSettingsTabMixin
from constants import (
    DIALOG_DIMENSIONS,
    DIALOG_TITLES,
    DEFAULT_OLLAMA_URL,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_GEMINI_MODEL,
    AVAILABLE_GEMINI_MODELS,
    OLLAMA_DOWNLOAD_URL,
    OLLAMA_LIBRARY_QWEN_URL,
    OLLAMA_LIBRARY_LLAMA_URL,
    AI_STATUS_ONLINE_LOADED,
    AI_STATUS_ONLINE_STANDBY,
    AI_STATUS_ONLINE_DISABLED,
    AI_STATUS_OFFLINE_LABEL,
    AI_STATUS_GEMINI_ACTIVE,
    AI_STATUS_GEMINI_NO_KEY,
    AI_STATUS_CHECKING,
    AI_STATUS_UNLOADING,
    AI_STATUS_UNLOADED,
    AI_STATUS_ACTIVATED,
    AI_STATUS_STARTING,
    AI_STATUS_STOPPING,
    AI_NO_MODELS_TITLE,
    AI_NO_MODELS_DESC,
    AI_OFFLINE_DESC,
    AI_LABEL_BASE_RULES_TITLE,
    AI_LABEL_BASE_RULES_HINT,
    AI_LABEL_SELECT_MODEL,
    AI_LABEL_OLLAMA_URL,
    AI_BTN_GLOBAL_TOGGLE,
    AI_BTN_START_SERVER,
    AI_BTN_STOP_SERVER,
    AI_BTN_TEST_GEMINI_KEY,
    AI_BTN_DOWNLOAD_OLLAMA,
    AI_BTN_DOWNLOAD_QWEN,
    AI_BTN_DOWNLOAD_LLAMA,
    AI_BTN_CREATE_PVS_MODEL,
    AI_BTN_PRELOAD_MODEL,
    AI_BTN_UNLOAD_MODEL,
    TEXTBOX_SPACING1_PARAGRAPH,
    TEXTBOX_SPACING3_PARAGRAPH,
    TEXTBOX_SPACING2_PARAGRAPH,
    COLOR_SUCCESS,
    COLOR_SUCCESS_HOVER,
    COLOR_DANGER,
    COLOR_DANGER_HOVER,
    COLOR_TEXT_RED,
    COLOR_TEXT_GREEN,
    COLOR_TEXT_ORANGE,
    COLOR_TEXT_GRAY,
    COLOR_TEXT_BLUE,
    COLOR_PURPLE_DARK,
    COLOR_PRIMARY_BLUE,
    COLOR_BTN_GRAY,
    COLOR_MUTED_LABEL,
    COLOR_MUTED_DISABLED,
    HOTKEY_RECORDER_TITLE,
    HOTKEY_RECORDER_HEADER,
    HOTKEY_RECORDER_INFO,
    HOTKEY_RECORDER_CANCEL,
    HOTKEY_RECORDER_DIMENSIONS,
    HOTKEY_RECORDER_BUTTON,
    HOTKEY_ACTION_LABELS,
    STATUS_SHORTCUT_CONFLICT,
    STATUS_SHORTCUT_CONFLICT_GENERIC,
    LABEL_APP_SHORTCUTS_HEADER,
    LABEL_SNIPPET_SHORTCUTS_HEADER,
    LABEL_NO_SNIPPETS,
)


class HotkeyRecorderDialog(ctk.CTkToplevel):
    """Interactive modal dialog to capture pressed hotkeys and key combinations."""
    def __init__(self, parent, on_recorded: Callable[[str], None]):
        super().__init__(parent)
        self.on_recorded = on_recorded
        w, h = HOTKEY_RECORDER_DIMENSIONS
        self.title(HOTKEY_RECORDER_TITLE)
        self.geometry(f"{w}x{h}")
        self.resizable(False, False)

        from utils.ui_utils import center_window
        center_window(self, w, h)
        self.transient(parent)
        self.grab_set()

        ctk.CTkLabel(self, text=HOTKEY_RECORDER_HEADER, font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 5))
        self.info_lbl = ctk.CTkLabel(self, text=HOTKEY_RECORDER_INFO, text_color=("gray30", "gray70"))
        self.info_lbl.pack(pady=5)

        cancel_btn = ctk.CTkButton(self, text=HOTKEY_RECORDER_CANCEL, command=self.destroy, fg_color="gray40", width=120)
        cancel_btn.pack(pady=(10, 0))

        self.bind("<KeyPress>", self.on_key_press)
        self.focus_set()

    def on_key_press(self, event):
        keysym = event.keysym
        if keysym == "Escape":
            self.destroy()
            return

        if keysym in ("Control_L", "Control_R", "Alt_L", "Alt_R", "Shift_L", "Shift_R", "Win_L", "Win_R"):
            return

        state = event.state
        mods = []
        if state & 0x0004:
            mods.append("Control")
        if state & 0x0001:
            mods.append("Shift")
        if state & 0x20000 or state & 0x0008 or keysym.startswith("Alt"):
            mods.append("Alt")

        key_name = keysym
        if len(key_name) == 1:
            key_name = key_name.lower()

        if mods:
            formatted = f"<{'--'.join(mods + [key_name])}>".replace("--", "-")
        else:
            formatted = f"<{key_name}>" if len(key_name) > 1 else key_name

        self.on_recorded(formatted)
        self.destroy()


class ProfileSettingsDialog(AiSettingsTabMixin, ctk.CTkToplevel):
    def __init__(self, parent, profile: UserProfile, storage_service: StorageService, on_profile_updated: Callable[[], None] | None = None):
        super().__init__(parent)
        self.profile = profile
        self.storage_service = storage_service
        self.on_profile_updated = on_profile_updated

        from services.snippet_service import SnippetService
        self.snippet_service = getattr(parent, "snippet_service", None) or SnippetService(self.storage_service.config.workspace_dir)

        from services.i18n_service import tr

        w, h = DIALOG_DIMENSIONS["profile_settings"]
        self.title(tr("profile.title", DIALOG_TITLES["profile_settings"]))
        self.geometry(f"{w}x{h}")
        self.minsize(880, 680)
        from utils.ui_utils import center_window
        center_window(self, w, h)

        self.transient(parent)
        self.grab_set()

        self.create_widgets()

    def create_widgets(self):
        from services.i18n_service import tr

        # Top Header
        top_bar = ctk.CTkFrame(self, height=45, corner_radius=0)
        top_bar.pack(fill="x", side="top", padx=10, pady=(10, 5))

        self.top_header_lbl = ctk.CTkLabel(top_bar, text=tr("profile.header", "⚙ Profil & Anwendungseinstellungen"), font=ctk.CTkFont(size=16, weight="bold"))
        self.top_header_lbl.pack(side="left", padx=10)

        # Tabview
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        self._tab_keys = [
            ("tab_user", "profile.tab_user", "👤 Benutzerprofil"),
            ("tab_ui", "profile.tab_ui", "🎨 Erscheinungsbild"),
            ("tab_paths", "profile.tab_paths", "📁 Speicherort & Pfade"),
            ("tab_wiki", "profile.tab_wiki", "📚 BookStack Wiki"),
            ("tab_ai", "profile.tab_ai", "🤖 KI & NLP"),
            ("tab_scoring", "profile.tab_shortcuts", "⌨ Tastenkürzel & Scoring"),
            ("tab_backup", "profile.tab_backup", "💾 Datensicherung"),
        ]
        self._tab_name_map = {}
        for tab_id, key, default in self._tab_keys:
            orig_t = tr(key, default)
            self._tab_name_map[tab_id] = orig_t

        self.tab_user = self.tabview.add(self._tab_name_map["tab_user"])
        self.tab_ui = self.tabview.add(self._tab_name_map["tab_ui"])
        self.tab_paths = self.tabview.add(self._tab_name_map["tab_paths"])
        self.tab_wiki = self.tabview.add(self._tab_name_map["tab_wiki"])
        self.tab_ai = self.tabview.add(self._tab_name_map["tab_ai"])
        self.tab_scoring = self.tabview.add(self._tab_name_map["tab_scoring"])
        self.tab_backup = self.tabview.add(self._tab_name_map["tab_backup"])

        self.setup_user_tab()
        self.setup_ui_tab()
        self.setup_paths_tab()
        self.setup_wiki_tab()
        self.setup_ai_tab()
        self.setup_scoring_tab()
        self.setup_backup_tab()

        # Bottom Action Bar
        bottom_bar = ctk.CTkFrame(self, height=50, fg_color="transparent")
        bottom_bar.pack(fill="x", side="bottom", padx=15, pady=10)

        self.save_btn = ctk.CTkButton(bottom_bar, text=tr("profile.save_btn", "💾 Einstellungen Speichern"), command=self.save_settings, fg_color="forestgreen", width=180)
        self.save_btn.pack(side="right", padx=5)

        self.status_lbl = ctk.CTkLabel(bottom_bar, text="", text_color="green")
        self.status_lbl.pack(side="left", padx=5)

    def setup_user_tab(self):
        from services.i18n_service import tr

        self.user_tab_hdr_lbl = ctk.CTkLabel(self.tab_user, text=tr("profile.user_tab_header", "Mitarbeiter-Profil verwalten & wechseln"), font=ctk.CTkFont(size=14, weight="bold"))
        self.user_tab_hdr_lbl.pack(anchor="w", pady=(10, 5))

        prof_frame = ctk.CTkFrame(self.tab_user, fg_color="transparent")
        prof_frame.pack(fill="x", pady=(0, 15))

        self.active_prof_lbl = ctk.CTkLabel(prof_frame, text=tr("profile.active_profile", "Aktives Profil:"))
        self.active_prof_lbl.pack(side="left", padx=(0, 10))

        profiles_list = self.storage_service.list_profiles()
        self.profile_combo = ctk.CTkOptionMenu(
            prof_frame,
            values=profiles_list,
            command=self.on_switch_profile,
            width=220,
        )
        self.profile_combo.set(self.profile.user.name if self.profile.user.name in profiles_list else profiles_list[0])
        self.profile_combo.pack(side="left", padx=(0, 10))

        self.btn_new_prof = ctk.CTkButton(
            prof_frame,
            text=tr("profile.btn_new_profile", "➕ Neues Profil anlegen"),
            command=self.open_create_profile_dialog,
            fg_color="forestgreen",
            width=160,
        )
        self.btn_new_prof.pack(side="left")

        self.user_details_hdr_lbl = ctk.CTkLabel(self.tab_user, text=tr("profile.user_info_header", "Benutzerinformationen (Aktives Profil)"), font=ctk.CTkFont(size=14, weight="bold"))
        self.user_details_hdr_lbl.pack(anchor="w", pady=(15, 5))

        ctk.CTkLabel(self.tab_user, text=tr("profile.display_name", "Name / Anzeigename *:")).pack(anchor="w", pady=(5, 2))
        self.user_name_entry = ctk.CTkEntry(self.tab_user, placeholder_text=tr("profile.name_placeholder", "Ihr Name"))
        self.user_name_entry.insert(0, self.profile.user.name)
        self.user_name_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(self.tab_user, text=tr("profile.dept", "Abteilung / Department *:")).pack(anchor="w", pady=(5, 2))
        self.user_dept_entry = ctk.CTkEntry(self.tab_user, placeholder_text="z. B. Support, Entwicklung, Technik")
        self.user_dept_entry.insert(0, self.profile.user.department)
        self.user_dept_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(self.tab_user, text=tr("profile.ext", "Durchwahl / Extension:")).pack(anchor="w", pady=(5, 2))
        self.user_ext_entry = ctk.CTkEntry(self.tab_user, placeholder_text="z.B. 4012")
        self.user_ext_entry.insert(0, self.profile.user.extension)
        self.user_ext_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(self.tab_user, text=tr("profile.email", "E-Mail-Adresse:")).pack(anchor="w", pady=(5, 2))
        self.user_email_entry = ctk.CTkEntry(self.tab_user, placeholder_text="beispiel@support.de")
        self.user_email_entry.insert(0, self.profile.user.email)
        self.user_email_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(self.tab_user, text=tr("profile.mobile", "Mobiltelefon:")).pack(anchor="w", pady=(5, 2))
        self.user_mobile_entry = ctk.CTkEntry(self.tab_user, placeholder_text="0170 / 1234567")
        self.user_mobile_entry.insert(0, self.profile.user.mobile)
        self.user_mobile_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(self.tab_user, text=tr("profile.signature", "E-Mail Signatur (für E-Mail-Entwürfe):")).pack(anchor="w", pady=(5, 2))
        self.user_sig_entry = ctk.CTkEntry(self.tab_user, placeholder_text="z. B. Mit freundlichen Grüßen, Ihr Support-Team (Tel. 0800-12345)")
        self.user_sig_entry.insert(0, self.profile.user.email_signature)
        self.user_sig_entry.pack(fill="x", pady=(0, 10))

    def open_create_profile_dialog(self):
        dialog = ctk.CTkInputDialog(
            text="Geben Sie den Namen des neuen Mitarbeiters ein:",
            title="Neues Mitarbeiter-Profil anlegen",
        )
        name_input = dialog.get_input()
        if name_input and name_input.strip():
            new_name = name_input.strip()
            from models.profile import UserInfo, UserProfile
            new_profile = UserProfile(user=UserInfo(name=new_name))
            self.storage_service.save_profile(new_profile)

            # Refresh list & switch
            self.profile = new_profile
            profiles_list = self.storage_service.list_profiles()
            self.profile_combo.configure(values=profiles_list)
            self.profile_combo.set(new_name)
            self.reload_user_fields()
            self.status_lbl.configure(text=f"Profil '{new_name}' angelegt und aktiviert!")
            if self.on_profile_updated:
                self.on_profile_updated()

    def on_switch_profile(self, selected_name: str):
        self.profile = self.storage_service.load_profile_by_name(selected_name)
        self.storage_service.save_profile(self.profile)
        self.reload_user_fields()
        self.status_lbl.configure(text=f"Profil auf '{selected_name}' gewechselt.")
        if self.on_profile_updated:
            self.on_profile_updated()

    def reload_user_fields(self):
        self.user_name_entry.delete(0, "end")
        self.user_name_entry.insert(0, self.profile.user.name)

        self.user_dept_entry.delete(0, "end")
        self.user_dept_entry.insert(0, self.profile.user.department)

        self.user_ext_entry.delete(0, "end")
        self.user_ext_entry.insert(0, self.profile.user.extension)

        self.user_email_entry.delete(0, "end")
        self.user_email_entry.insert(0, self.profile.user.email)

        self.user_mobile_entry.delete(0, "end")
        self.user_mobile_entry.insert(0, self.profile.user.mobile)

        if hasattr(self, "user_sig_entry"):
            self.user_sig_entry.delete(0, "end")
            self.user_sig_entry.insert(0, self.profile.user.email_signature)

        self.theme_combo.set(self.profile.ui_settings.theme)
        self.layout_combo.set(get_layout_display(self.profile.ui_settings.default_layout))
        if hasattr(self, "popup_target_combo"):
            curr_target = getattr(self.profile.ui_settings, "popup_display_target", "APP_SCREEN")
            self.popup_target_combo.set("App-Bildschirm (aktuell/zuletzt)" if curr_target == "APP_SCREEN" else "Hauptbildschirm")

    def on_language_selected(self, selected_display_name: str):
        from services.i18n_service import LANGUAGE_DISPLAY_TO_CODE, get_i18n
        lang_code = LANGUAGE_DISPLAY_TO_CODE.get(selected_display_name, "de")
        self.profile.ui_settings.language = lang_code
        get_i18n().current_language = lang_code
        self.refresh_ui_labels()

    def refresh_ui_labels(self):
        from services.i18n_service import tr
        self.title(tr("dialog_titles.profile_settings", "⚙ Profil & Anwendungseinstellungen"))
        if hasattr(self, "top_header_lbl"):
            self.top_header_lbl.configure(text=tr("profile.header", "⚙ Profil & Anwendungseinstellungen"))
        if hasattr(self, "save_btn"):
            self.save_btn.configure(text=tr("profile.save_btn", "💾 Einstellungen Speichern"))

        if hasattr(self, "tabview") and hasattr(self.tabview, "_segmented_button") and hasattr(self.tabview._segmented_button, "_buttons_dict"):
            btns = self.tabview._segmented_button._buttons_dict
            for tab_id, key, default in getattr(self, "_tab_keys", []):
                orig_name = getattr(self, "_tab_name_map", {}).get(tab_id)
                if orig_name and orig_name in btns:
                    new_txt = tr(key, default)
                    btns[orig_name].configure(text=new_txt)

        if hasattr(self, "appearance_hdr_lbl"):
            self.appearance_hdr_lbl.configure(text=tr("profile.appearance_layout", "Erscheinungsbild & Layout"))
        if hasattr(self, "lang_lbl"):
            self.lang_lbl.configure(text=tr("profile.language", "Sprache / Language:"))
        if hasattr(self, "theme_lbl"):
            self.theme_lbl.configure(text=tr("profile.theme", "Farb-Thema (Theme):"))
        if hasattr(self, "default_layout_lbl"):
            self.default_layout_lbl.configure(text=tr("profile.default_layout", "Standard-Layout beim Start:"))
        if hasattr(self, "demo_switch"):
            self.demo_switch.configure(text=tr("profile.demo_data_toggle", "🧪 Beispieldaten (Demofälle & Demokunden) in allen Ansichten einblenden"))
        if hasattr(self, "os_popup_switch"):
            self.os_popup_switch.configure(text=tr("profile.os_popup_toggle", "🔔 Windows-Systembenachrichtigungen (OS Native Toast) aktivieren"))
        if hasattr(self, "popup_target_lbl"):
            self.popup_target_lbl.configure(text=tr("profile.popup_position", "Position zusätzlicher Fenster & Benachrichtigungen:"))
        if hasattr(self, "col_widths_hdr_lbl"):
            self.col_widths_hdr_lbl.configure(text=tr("profile.saved_widths", "Gespeicherte Spaltenbreiten (Profile-Level)"))
        if hasattr(self, "btn_reset_widths"):
            self.btn_reset_widths.configure(text=tr("profile.reset_widths_btn", "Alle Spaltenbreiten auf Standard zurücksetzen"))
        if hasattr(self, "user_tab_hdr_lbl"):
            self.user_tab_hdr_lbl.configure(text=tr("profile.user_tab_header", "Mitarbeiter-Profil verwalten & wechseln"))
        if hasattr(self, "active_prof_lbl"):
            self.active_prof_lbl.configure(text=tr("profile.active_profile", "Aktives Profil:"))
        if hasattr(self, "btn_new_prof"):
            self.btn_new_prof.configure(text=tr("profile.btn_new_profile", "➕ Neues Profil anlegen"))
        if hasattr(self, "user_details_hdr_lbl"):
            self.user_details_hdr_lbl.configure(text=tr("profile.user_info_header", "Benutzerinformationen (Aktives Profil)"))

    def setup_ui_tab(self):
        from services.i18n_service import tr, SUPPORTED_LANGUAGES, LANGUAGE_CODE_TO_DISPLAY

        self.appearance_hdr_lbl = ctk.CTkLabel(self.tab_ui, text=tr("profile.appearance_layout", "Erscheinungsbild & Layout"), font=ctk.CTkFont(size=14, weight="bold"))
        self.appearance_hdr_lbl.pack(anchor="w", pady=(10, 5))

        self.lang_lbl = ctk.CTkLabel(self.tab_ui, text=tr("profile.language", "Sprache / Language:"))
        self.lang_lbl.pack(anchor="w", pady=(5, 2))
        self.language_combo = ctk.CTkOptionMenu(
            self.tab_ui,
            values=list(SUPPORTED_LANGUAGES.values()),
            command=self.on_language_selected,
        )
        curr_lang = getattr(self.profile.ui_settings, "language", "de")
        self.language_combo.set(LANGUAGE_CODE_TO_DISPLAY.get(curr_lang, "Deutsch"))
        self.language_combo.pack(fill="x", pady=(0, 15))

        self.theme_lbl = ctk.CTkLabel(self.tab_ui, text=tr("profile.theme", "Farb-Thema (Theme):"))
        self.theme_lbl.pack(anchor="w", pady=(5, 2))
        self.theme_combo = ctk.CTkOptionMenu(self.tab_ui, values=["Dark", "Light", "System"])
        self.theme_combo.set(self.profile.ui_settings.theme)
        self.theme_combo.pack(fill="x", pady=(0, 15))

        self.default_layout_lbl = ctk.CTkLabel(self.tab_ui, text=tr("profile.default_layout", "Standard-Layout beim Start:"))
        self.default_layout_lbl.pack(anchor="w", pady=(5, 2))
        self.layout_combo = ctk.CTkOptionMenu(
            self.tab_ui,
            values=list(LAYOUT_DISPLAY.values())
        )
        self.layout_combo.set(get_layout_display(self.profile.ui_settings.default_layout))
        self.layout_combo.pack(fill="x", pady=(0, 15))

        self.demo_switch = ctk.CTkSwitch(  # type: ignore[attr-defined]
            self.tab_ui,
            text=tr("profile.demo_data_toggle", "🧪 Beispieldaten (Demofälle & Demokunden) in allen Ansichten einblenden")
        )
        if self.profile.ui_settings.show_demo_data is True:
            self.demo_switch.select()
        else:
            self.demo_switch.deselect()
        self.demo_switch.pack(anchor="w", pady=(0, 15))

        self.os_popup_switch = ctk.CTkSwitch(  # type: ignore[attr-defined]
            self.tab_ui,
            text=tr("profile.os_popup_toggle", "🔔 Windows-Systembenachrichtigungen (OS Native Toast) aktivieren")
        )
        if getattr(self.profile.reminder_settings, "os_popup_enabled", True):
            self.os_popup_switch.select()
        else:
            self.os_popup_switch.deselect()
        self.os_popup_switch.pack(anchor="w", pady=(0, 15))

        self.popup_target_lbl = ctk.CTkLabel(self.tab_ui, text=tr("profile.popup_position", "Position zusätzlicher Fenster & Benachrichtigungen:"))
        self.popup_target_lbl.pack(anchor="w", pady=(5, 2))
        self.popup_target_combo = ctk.CTkOptionMenu(
            self.tab_ui,
            values=[tr("profile.popup_target_app", "App-Bildschirm (aktuell/zuletzt)"), tr("profile.popup_target_primary", "Hauptbildschirm")]
        )
        curr_target = getattr(self.profile.ui_settings, "popup_display_target", "APP_SCREEN")
        self.popup_target_combo.set(tr("profile.popup_target_app", "App-Bildschirm (aktuell/zuletzt)") if curr_target == "APP_SCREEN" else tr("profile.popup_target_primary", "Hauptbildschirm"))
        self.popup_target_combo.pack(fill="x", pady=(0, 20))

        # Column widths reset section
        self.col_widths_hdr_lbl = ctk.CTkLabel(self.tab_ui, text=tr("profile.saved_widths", "Gespeicherte Spaltenbreiten (Profile-Level)"), font=ctk.CTkFont(size=14, weight="bold"))
        self.col_widths_hdr_lbl.pack(anchor="w", pady=(10, 5))

        widths = self.profile.ui_settings.column_widths
        w_str = (
            f"• Cockpit: Links {widths.get('cockpit_left', 300)}px | Mitte {widths.get('cockpit_center', 420)}px | Rechts {widths.get('cockpit_right', 320)}px\n"
            f"• Kanban-Board: Mindestspaltenbreite {widths.get('board_column', 280)}px\n"
            f"• Tabelle: ID {widths.get('table_col_id', 120)}px | Praxis {widths.get('table_col_practice', 220)}px | Titel {widths.get('table_col_title', 280)}px | Score {widths.get('table_col_score', 90)}px"
        )
        self.widths_label = ctk.CTkLabel(self.tab_ui, text=w_str, font=ctk.CTkFont(size=11), text_color=("gray40", "gray70"), justify="left", anchor="w")
        self.widths_label.pack(anchor="w", pady=(0, 12))

        from services.i18n_service import tr

        btn_reset_widths = ctk.CTkButton(
            self.tab_ui,
            text=tr("profile.reset_widths_btn", "🔄 Alle Spaltenbreiten auf Standard zurücksetzen"),
            command=self.on_reset_column_widths,
            fg_color="gray30",
            width=280,
        )
        btn_reset_widths.pack(anchor="w")

    def on_reset_column_widths(self):
        from services.i18n_service import tr

        self.profile.ui_settings.reset_column_widths()
        self.storage_service.save_profile(self.profile)
        widths = self.profile.ui_settings.column_widths
        w_str = (
            f"• Cockpit: Links {widths.get('cockpit_left', 300)}px | Mitte {widths.get('cockpit_center', 420)}px | Rechts {widths.get('cockpit_right', 320)}px\n"
            f"• Kanban-Board: Mindestspaltenbreite {widths.get('board_column', 280)}px\n"
            f"• Tabelle: ID {widths.get('table_col_id', 120)}px | Praxis {widths.get('table_col_practice', 220)}px | Titel {widths.get('table_col_title', 280)}px | Score {widths.get('table_col_score', 90)}px"
        )
        self.widths_label.configure(text=w_str)
        self.status_lbl.configure(text=tr("profile.widths_reset_msg", "Alle Spaltenbreiten aller Ansichten auf Standard zurückgesetzt!"))
        if self.on_profile_updated:
            self.on_profile_updated()

    def setup_paths_tab(self):
        from pathlib import Path
        from services.i18n_service import tr

        ctk.CTkLabel(self.tab_paths, text=tr("profile.paths_title", "Speicherort & Dateipfade (EXE / Externe Daten)"), font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))

        # Main Workspace Directory
        ctk.CTkLabel(self.tab_paths, text=tr("profile.workspace_label", "Arbeitsbereich / Datenordner-Pfad:")).pack(anchor="w", pady=(5, 2))
        ws_frame = ctk.CTkFrame(self.tab_paths, fg_color="transparent")
        ws_frame.pack(fill="x", pady=(0, 10))

        self.ws_entry = ctk.CTkEntry(ws_frame, placeholder_text="Pfad zum Datenordner...")
        self.ws_entry.insert(0, str(self.storage_service.config.workspace_dir))
        self.ws_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        btn_browse_ws = ctk.CTkButton(ws_frame, text=tr("profile.browse_folder", "📁 Ordner wählen"), command=self.on_browse_workspace, width=120)
        btn_browse_ws.pack(side="right")

        # Custom Individual File Path Overrides
        ctk.CTkLabel(self.tab_paths, text=tr("profile.custom_overrides", "Benutzerdefinierte Einzeldateipfade (Optional):"), font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(10, 5))

        # Cases Path Override
        row_cases = ctk.CTkFrame(self.tab_paths, fg_color="transparent")
        row_cases.pack(fill="x", pady=2)
        ctk.CTkLabel(row_cases, text=tr("profile.cases_file", "Fälle (cases.json):"), width=160, anchor="w").pack(side="left")
        self.path_cases_entry = ctk.CTkEntry(row_cases, placeholder_text=tr("profile.default_in_data", "Standard im Datenordner"))
        if self.storage_service.config.custom_cases_path:
            self.path_cases_entry.insert(0, str(self.storage_service.config.custom_cases_path))
        self.path_cases_entry.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(row_cases, text=tr("profile.file_browse", "Datei..."), command=lambda: self.on_browse_file(self.path_cases_entry, "*.json"), width=70).pack(side="right")

        # Customers Path Override
        row_cust = ctk.CTkFrame(self.tab_paths, fg_color="transparent")
        row_cust.pack(fill="x", pady=2)
        ctk.CTkLabel(row_cust, text=tr("profile.cust_file", "Kunden (customers.json):"), width=160, anchor="w").pack(side="left")
        self.path_cust_entry = ctk.CTkEntry(row_cust, placeholder_text=tr("profile.default_in_data", "Standard im Datenordner"))
        if self.storage_service.config.custom_customers_path:
            self.path_cust_entry.insert(0, str(self.storage_service.config.custom_customers_path))
        self.path_cust_entry.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(row_cust, text=tr("profile.file_browse", "Datei..."), command=lambda: self.on_browse_file(self.path_cust_entry, "*.json"), width=70).pack(side="right")

        # Wiki DB Path Override
        row_wiki = ctk.CTkFrame(self.tab_paths, fg_color="transparent")
        row_wiki.pack(fill="x", pady=2)
        ctk.CTkLabel(row_wiki, text=tr("profile.wiki_file", "Wiki DB (sqlite):"), width=160, anchor="w").pack(side="left")
        self.path_wiki_entry = ctk.CTkEntry(row_wiki, placeholder_text=tr("profile.default_in_data", "Standard im Datenordner"))
        if self.storage_service.config.custom_wiki_db_path:
            self.path_wiki_entry.insert(0, str(self.storage_service.config.custom_wiki_db_path))
        self.path_wiki_entry.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(row_wiki, text=tr("profile.file_browse", "Datei..."), command=lambda: self.on_browse_file(self.path_wiki_entry, "*.sqlite"), width=70).pack(side="right")

        # Reset button
        btn_reset_paths = ctk.CTkButton(self.tab_paths, text=tr("profile.reset_paths_btn", "🔄 Einzelpfade auf Standard zurücksetzen"), command=self.on_reset_paths, fg_color="gray40", width=240)
        btn_reset_paths.pack(anchor="w", pady=(15, 5))

    def on_browse_workspace(self):
        from tkinter import filedialog
        chosen = filedialog.askdirectory(title="Datenordner auswählen", initialdir=self.ws_entry.get().strip() or None)
        if chosen:
            self.ws_entry.delete(0, "end")
            self.ws_entry.insert(0, chosen)

    def on_browse_file(self, entry_widget: ctk.CTkEntry, file_pattern: str):
        from tkinter import filedialog
        chosen = filedialog.askopenfilename(title="Datei auswählen", filetypes=[("Datendatei", file_pattern), ("Alle Dateien", "*.*")])
        if chosen:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, chosen)

    def on_reset_paths(self):
        self.path_cases_entry.delete(0, "end")
        self.path_cust_entry.delete(0, "end")
        self.path_wiki_entry.delete(0, "end")

    def setup_wiki_tab(self):
        from services.i18n_service import tr

        ctk.CTkLabel(self.tab_wiki, text=tr("profile.wiki_title", "BookStack Server Konfiguration"), font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))

        ctk.CTkLabel(self.tab_wiki, text=tr("profile.wiki_url", "BookStack API URL:")).pack(anchor="w", pady=(5, 2))
        self.wiki_url_entry = ctk.CTkEntry(self.tab_wiki, placeholder_text="https://wiki.meinepraxis.de/api")
        self.wiki_url_entry.insert(0, self.profile.wiki_settings.api_url)
        self.wiki_url_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(self.tab_wiki, text=tr("profile.wiki_token_id", "API Token ID:")).pack(anchor="w", pady=(5, 2))
        self.wiki_token_id_entry = ctk.CTkEntry(self.tab_wiki, placeholder_text="Token ID")
        self.wiki_token_id_entry.insert(0, self.profile.wiki_settings.token_id)
        self.wiki_token_id_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(self.tab_wiki, text=tr("profile.wiki_token_secret", "API Token Secret:")).pack(anchor="w", pady=(5, 2))
        self.wiki_token_secret_entry = ctk.CTkEntry(self.tab_wiki, placeholder_text="Token Secret", show="*")
        self.wiki_token_secret_entry.insert(0, self.profile.wiki_settings.token_secret)
        self.wiki_token_secret_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(self.tab_wiki, text=tr("profile.wiki_sync_mode", "Synchronisations-Modus:")).pack(anchor="w", pady=(5, 2))
        self.sync_mode_combo = ctk.CTkOptionMenu(self.tab_wiki, values=[SyncMode.METADATA_ONLY.value, SyncMode.FULL_OFFLINE.value])
        self.sync_mode_combo.set(self.profile.wiki_settings.sync_mode)
        self.sync_mode_combo.pack(fill="x", pady=(0, 10))

        self.sync_startup_var = ctk.BooleanVar(value=self.profile.wiki_settings.sync_on_startup)
        ctk.CTkCheckBox(self.tab_wiki, text=tr("profile.wiki_sync_startup", "Wiki-Inhalte beim Anwendungsstart synchronisieren"), variable=self.sync_startup_var).pack(anchor="w", pady=5)

    def setup_scoring_tab(self):
        scroll = ctk.CTkScrollableFrame(self.tab_scoring, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=5)

        ctk.CTkLabel(scroll, text=LABEL_APP_SHORTCUTS_HEADER, font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(5, 5))

        self.shortcut_entries: dict[str, ctk.CTkEntry] = {}

        for attr_name, label_text in HOTKEY_ACTION_LABELS:
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=label_text, width=180, anchor="w").pack(side="left")

            val = getattr(self.profile.shortcuts, attr_name, "")
            entry = ctk.CTkEntry(row, width=140)
            entry.insert(0, val)
            entry.pack(side="left", padx=(5, 5))
            self.shortcut_entries[attr_name] = entry

            rec_btn = ctk.CTkButton(
                row,
                text=HOTKEY_RECORDER_BUTTON,
                width=120,
                fg_color="gray30",
                hover_color="gray45",
                command=lambda e=entry: self.open_hotkey_recorder(e)
            )
            rec_btn.pack(side="left")

            entry.bind("<KeyRelease>", lambda evt: self.validate_shortcut_conflicts())

        # --- Text-Makros (Snippets) Section ---
        ctk.CTkLabel(scroll, text=LABEL_SNIPPET_SHORTCUTS_HEADER, font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(20, 5))

        self.snippet_shortcut_entries: list[tuple[Any, ctk.CTkEntry]] = []
        all_snippets = self.snippet_service.get_all_snippets()

        if not all_snippets:
            ctk.CTkLabel(scroll, text=LABEL_NO_SNIPPETS, text_color="gray60").pack(anchor="w", pady=2)
        else:
            for snip in all_snippets:
                s_row = ctk.CTkFrame(scroll, fg_color="transparent")
                s_row.pack(fill="x", pady=2)

                title_lbl = ctk.CTkLabel(s_row, text=f"{snip.title[:30]} ({snip.snippet_id}):", width=220, anchor="w")
                title_lbl.pack(side="left")

                s_entry = ctk.CTkEntry(s_row, width=140)
                s_entry.insert(0, snip.shortcut or "")
                s_entry.pack(side="left", padx=(5, 5))
                self.snippet_shortcut_entries.append((snip, s_entry))

                s_rec_btn = ctk.CTkButton(
                    s_row,
                    text=HOTKEY_RECORDER_BUTTON,
                    width=120,
                    fg_color="gray30",
                    hover_color="gray45",
                    command=lambda e=s_entry: self.open_hotkey_recorder(e)
                )
                s_rec_btn.pack(side="left")

                s_entry.bind("<KeyRelease>", lambda evt: self.validate_shortcut_conflicts())

        # Conflict Warning Label
        self.conflict_warn_lbl = ctk.CTkLabel(scroll, text="", text_color="red", font=ctk.CTkFont(weight="bold"))
        self.conflict_warn_lbl.pack(fill="x", pady=(5, 5))

        # --- Prioritäts-Scoring Section ---
        ctk.CTkLabel(scroll, text="Prioritäts-Scoring Punkte", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(15, 5))

        row4 = ctk.CTkFrame(scroll, fg_color="transparent")
        row4.pack(fill="x", pady=3)
        ctk.CTkLabel(row4, text="VIP-Bonus (Punkte):").pack(side="left")
        self.vip_bonus_entry = ctk.CTkEntry(row4, width=80)
        self.vip_bonus_entry.insert(0, str(self.profile.scoring_matrix.vip_bonus_points))
        self.vip_bonus_entry.pack(side="right")

    def open_hotkey_recorder(self, target_entry: ctk.CTkEntry):
        def on_recorded(key_str: str):
            target_entry.delete(0, "end")
            target_entry.insert(0, key_str)
            self.validate_shortcut_conflicts()

        HotkeyRecorderDialog(self, on_recorded)

    def validate_shortcut_conflicts(self) -> bool:
        keys = []
        for entry in self.shortcut_entries.values():
            val = entry.get().strip()
            if val:
                keys.append(val)
        for _, entry in self.snippet_shortcut_entries:
            val = entry.get().strip()
            if val:
                keys.append(val)

        duplicates = set([k for k in keys if keys.count(k) > 1])
        if duplicates:
            dup_str = ", ".join(duplicates)
            self.conflict_warn_lbl.configure(text=STATUS_SHORTCUT_CONFLICT.format(dup_str=dup_str))
            return False
        else:
            self.conflict_warn_lbl.configure(text="")
            return True

    def save_settings(self):
        from pathlib import Path
        name = self.user_name_entry.get().strip()
        if not name:
            self.status_lbl.configure(text="⚠ Benutzername darf nicht leer sein!", text_color="red")
            return

        # Update User
        self.profile.user.name = name
        self.profile.user.department = self.user_dept_entry.get().strip() or "Support"
        self.profile.user.extension = self.user_ext_entry.get().strip()
        self.profile.user.email = self.user_email_entry.get().strip()
        self.profile.user.mobile = self.user_mobile_entry.get().strip()

        # Update UI Settings & Reminders
        if hasattr(self, "language_combo"):
            lang_display = self.language_combo.get()
            from services.i18n_service import LANGUAGE_DISPLAY_TO_CODE, get_i18n
            lang_code = LANGUAGE_DISPLAY_TO_CODE.get(lang_display, "de")
            self.profile.ui_settings.language = lang_code
            get_i18n().current_language = lang_code

        self.profile.ui_settings.theme = self.theme_combo.get()
        self.profile.ui_settings.default_layout = get_layout_val_from_display(self.layout_combo.get())
        if hasattr(self, "demo_switch"):
            self.profile.ui_settings.show_demo_data = bool(self.demo_switch.get())
        if hasattr(self, "os_popup_switch"):
            self.profile.reminder_settings.os_popup_enabled = bool(self.os_popup_switch.get())
        if hasattr(self, "popup_target_combo"):
            val = self.popup_target_combo.get()
            self.profile.ui_settings.popup_display_target = "PRIMARY_SCREEN" if "Hauptbildschirm" in val else "APP_SCREEN"

        # Update Workspace & Custom File Paths
        ws_path_str = self.ws_entry.get().strip()
        if ws_path_str:
            self.storage_service.config.workspace_dir = Path(ws_path_str)

        cases_override = self.path_cases_entry.get().strip()
        self.storage_service.config.custom_cases_path = Path(cases_override) if cases_override else None

        cust_override = self.path_cust_entry.get().strip()
        self.storage_service.config.custom_customers_path = Path(cust_override) if cust_override else None

        wiki_override = self.path_wiki_entry.get().strip()
        self.storage_service.config.custom_wiki_db_path = Path(wiki_override) if wiki_override else None

        self.storage_service.config.ensure_directories()
        self.storage_service.config.save_user_config()

        # Update Wiki Settings
        self.profile.wiki_settings.api_url = self.wiki_url_entry.get().strip()
        self.profile.wiki_settings.token_id = self.wiki_token_id_entry.get().strip()
        self.profile.wiki_settings.token_secret = self.wiki_token_secret_entry.get().strip()
        self.profile.wiki_settings.sync_mode = self.sync_mode_combo.get()
        self.profile.wiki_settings.sync_on_startup = self.sync_startup_var.get()

        # Update AI Settings
        provider_val = "GEMINI" if "GEMINI" in self.ai_provider_seg.get().upper() else "OLLAMA"
        self.profile.ai_settings.provider = provider_val
        self.profile.ai_settings.ollama_url = self.ai_url_entry.get().strip()
        self.profile.ai_settings.model_name = self.ai_model_entry.get().strip()
        self.profile.ai_settings.gemini_api_key = self.gemini_key_entry.get().strip()
        self.profile.ai_settings.gemini_model = self.gemini_model_combo.get()
        self.profile.ai_settings.enable_anonymization = self.anonymize_chk_var.get()
        self.profile.ai_settings.enable_ai = bool(self.ai_enable_chk.get())
        self.profile.ai_settings.use_modelfile_rules_for_gemini = self.gemini_modelfile_chk_var.get()
        raw_rules = self.ai_base_rules_txt.get("1.0", "end-1c").splitlines()
        self.profile.ai_settings.base_rules = [r.strip() for r in raw_rules if r.strip()]

        # Update Shortcuts & Snippet Macros with conflict validation
        if not self.validate_shortcut_conflicts():
            self.status_lbl.configure(text=STATUS_SHORTCUT_CONFLICT_GENERIC, text_color="red")
            return

        for attr_name, entry in self.shortcut_entries.items():
            setattr(self.profile.shortcuts, attr_name, entry.get().strip())

        for snip, entry in self.snippet_shortcut_entries:
            snip.shortcut = entry.get().strip()
            self.snippet_service.add_or_update_snippet(snip)

        try:
            self.profile.scoring_matrix.vip_bonus_points = int(self.vip_bonus_entry.get().strip())
        except ValueError:
            pass

        self.storage_service.save_profile(self.profile)
        self.status_lbl.configure(text="✅ Einstellungen & Pfade gespeichert!", text_color="green")

        if self.on_profile_updated:
            self.on_profile_updated()

    def setup_backup_tab(self):
        from tkinter import filedialog
        from pathlib import Path
        from services.zip_backup_service import ZipBackupService
        from ui.dialogs.zip_import_dialog import ZipImportPathDialog
        from services.i18n_service import tr

        ctk.CTkLabel(
            self.tab_backup,
            text=tr("profile.backup_title", "📦 Komplett-Datensicherung & ZIP-Archivierung"),
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", pady=(10, 5))

        desc_str = tr(
            "profile.backup_desc",
            "Exportieren Sie Ihren gesamten Datenbestand (alle Fälle, Kunden, Formulare, Exportvorlagen, Mitarbeiter "
            "und gespeicherten Anhang-Ordner) in eine komprimierte ZIP-Datei. Diese kann zur Sicherung oder für "
            "den Wechsel auf einen anderen Arbeitsplatz genutzt werden."
        )
        ctk.CTkLabel(
            self.tab_backup,
            text=desc_str,
            font=ctk.CTkFont(size=11),
            text_color=("gray30", "gray80"),
            justify="left",
            anchor="w",
            wraplength=800,
        ).pack(anchor="w", pady=(0, 15))

        # Section 1: Export
        exp_card = ctk.CTkFrame(self.tab_backup, corner_radius=8)
        exp_card.pack(fill="x", pady=(0, 15), padx=2)

        ctk.CTkLabel(
            exp_card,
            text=tr("profile.backup_exp_title", "1. Komplett-Datensatz als ZIP exportieren"),
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", padx=12, pady=(10, 2))

        ctk.CTkLabel(
            exp_card,
            text=tr("profile.backup_exp_desc", "Erzeugt ein Backup-Archiv inklusive allen Dateien in data/ und allen Dokumenten in attachments/."),
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray70"),
            anchor="w",
        ).pack(anchor="w", padx=12, pady=(0, 10))

        btn_export = ctk.CTkButton(
            exp_card,
            text=tr("profile.backup_exp_btn", "📦 Komplett-Backup als ZIP exportieren..."),
            command=self.on_click_export_zip,
            fg_color="dodgerblue",
            width=240,
        )
        btn_export.pack(anchor="w", padx=12, pady=(0, 12))

        # Section 2: Import
        imp_card = ctk.CTkFrame(self.tab_backup, corner_radius=8)
        imp_card.pack(fill="x", pady=(0, 15), padx=2)

        ctk.CTkLabel(
            imp_card,
            text=tr("profile.backup_imp_title", "2. Datensicherung aus ZIP-Datei importieren"),
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", padx=12, pady=(10, 2))

        ctk.CTkLabel(
            imp_card,
            text=tr("profile.backup_imp_desc", "Stellt Datensätze und Anhänge aus einem ZIP-Archiv an den von Ihnen gewählten Ziel-Speicherorten wieder her."),
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray70"),
            anchor="w",
        ).pack(anchor="w", padx=12, pady=(0, 10))

        btn_import = ctk.CTkButton(
            imp_card,
            text=tr("profile.backup_imp_btn", "📥 Datensicherung aus ZIP importieren..."),
            command=self.on_click_import_zip,
            fg_color="forestgreen",
            width=240,
        )
        btn_import.pack(anchor="w", padx=12, pady=(0, 12))

    def on_click_export_zip(self):
        from tkinter import filedialog
        from pathlib import Path
        from services.zip_backup_service import ZipBackupService

        dest_file = filedialog.asksaveasfilename(
            title="Datensicherung als ZIP speichern",
            defaultextension=".zip",
            filetypes=[("ZIP-Archiv", "*.zip")],
            initialfile="SupportCockpit_Backup.zip",
            parent=self,
        )
        if not dest_file:
            return

        res = ZipBackupService.export_backup_zip(self.storage_service, Path(dest_file))
        mb_size = res["total_bytes"] / (1024 * 1024)
        self.status_lbl.configure(
            text=f"✅ ZIP-Backup erfolgreich erstellt: {res['file_count']} Dateien ({mb_size:.2f} MB)",
            text_color="green",
        )

    def on_click_import_zip(self):
        from tkinter import filedialog
        from pathlib import Path
        from services.zip_backup_service import ZipBackupService
        from ui.dialogs.zip_import_dialog import ZipImportPathDialog

        zip_file = filedialog.askopenfilename(
            title="Datensicherung (ZIP-Datei) auswählen",
            filetypes=[("ZIP-Archiv", "*.zip")],
            parent=self,
        )
        if not zip_file:
            return

        zip_p = Path(zip_file)
        default_data = self.storage_service.config.data_dir
        default_att = self.storage_service.config.attachments_dir

        def on_confirmed(target_data: Path, target_att: Path):
            res = ZipBackupService.import_backup_zip(zip_p, target_data, target_att)

            # Update paths in config
            self.storage_service.config.custom_cases_path = target_data / "cases.json"
            self.storage_service.config.custom_customers_path = target_data / "customers.json"
            self.storage_service.config.ensure_directories()
            self.storage_service.config.save_user_config()

            self.status_lbl.configure(
                text=f"✅ Import abgeschlossen! {res['extracted_data_files']} Datendateien & {res['extracted_attachment_files']} Anhänge entpackt.",
                text_color="green",
            )
            if self.on_profile_updated:
                self.on_profile_updated()

        ZipImportPathDialog(
            self,
            zip_file_path=zip_p,
            default_data_dir=default_data,
            default_attachments_dir=default_att,
            on_import_confirmed=on_confirmed,
        )
