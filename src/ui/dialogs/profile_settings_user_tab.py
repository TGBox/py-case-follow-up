from typing import TYPE_CHECKING, Any, cast
from collections.abc import Callable
import tkinter as tk
import customtkinter as ctk

from constants import (
    BORDER_WIDTH_COLOR_SELECTED,
    BTN_WIDTH_LG,
    BTN_WIDTH_MD,
    BTN_WIDTH_SIGNATURE,
    COLOR_BORDER_DARK,
    COLOR_DANGER,
    COLOR_MUTED_GRAY_FG,
    COLOR_MUTED_GRAY_HOVER,
    COLOR_NOTE_TEXT,
    COLOR_PRESET_BORDER_SELECTED,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_SIGNATURE_BG,
    COLOR_SIGNATURE_BORDER,
    COLOR_SUCCESS,
    COLOR_TEXT_WHITE,
    CORNER_RADIUS_ENTRY,
    CORNER_RADIUS_SM,
    DEFAULT_DEPARTMENT,
    DEFAULT_SIGNATURE_FILENAME,
    DEFAULT_USER_COLOR,
    ENTRY_WIDTH_COMPACT,
    ENTRY_WIDTH_MD,
    FONT_SIZE_SM,
    FONT_SIZE_SUBTITLE,
    FONT_SIZE_XS,
    PAD_MD,
    PAD_NONE,
    PAD_SM,
    PAD_XS,
    PROFILE_TAB_FIELD_WIDTH,
    TEXTBOX_HEIGHT_SIGNATURE,
    USER_COLOR_PRESETS,
    USER_COLOR_PRESET_TILE_SIZE,
    USER_COLOR_PREVIEW_TILE_SIZE,
    get_file_types_signature_export,
    get_file_types_signature_import,
)
from models.profile import UserInfo, UserProfile
from services.i18n_service import tr


class UserSettingsTabMixin:
    """Mixin for User Profile management, personal data, and signature export/import."""

    if TYPE_CHECKING:
        master: Any
        profile: Any
        storage_service: Any
        status_lbl: ctk.CTkLabel
        on_profile_updated: Callable[[], None] | None
        register_i18n: Callable[..., Any]
        reload_ui_fields: Callable[[], None]
        # Als Methoden deklariert, nicht als Callable-Attribute: ProfileSettingsDialog
        # erbt diesen Mixin und definiert beide selbst - gegen ein Attribut waere
        # das fuer pyright ein unvertraeglicher Override.
        def save_settings_quietly(self) -> bool: ...
        def reload_all_tabs(self) -> None: ...

    def setup_user_section(self, left_col: ctk.CTkFrame) -> None:
        left_col.columnconfigure(0, weight=1, uniform="left_subcols")
        left_col.columnconfigure(1, weight=1, uniform="left_subcols")

        # Section 1: Profil verwalten & wechseln
        self.user_tab_hdr_lbl = self.register_i18n(
            ctk.CTkLabel(left_col, text=tr("profile.user_tab_header", "Mitarbeiter-Profil verwalten & wechseln"), font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight="bold")),
            "profile.user_tab_header",
            "Mitarbeiter-Profil verwalten & wechseln",
        )
        self.user_tab_hdr_lbl.grid(row=0, column=0, columnspan=2, sticky="w", pady=(PAD_SM, PAD_XS))

        prof_frame = ctk.CTkFrame(left_col, fg_color="transparent")
        prof_frame.grid(row=1, column=0, columnspan=2, sticky="w", pady=(PAD_NONE, PAD_MD))

        self.active_prof_lbl = self.register_i18n(
            ctk.CTkLabel(prof_frame, text=tr("profile.active_profile", "Aktives Profil:")),
            "profile.active_profile",
            "Aktives Profil:",
        )
        self.active_prof_lbl.pack(side="left", padx=(PAD_NONE, PAD_MD))

        profiles_list = self.storage_service.list_profiles()
        self.profile_combo = ctk.CTkOptionMenu(
            prof_frame,
            values=profiles_list,
            command=self.on_switch_profile,
            width=ENTRY_WIDTH_MD,
        )
        self.profile_combo.set(self.profile.user.name if self.profile.user.name in profiles_list else profiles_list[0])
        self.profile_combo.pack(side="left", padx=(PAD_NONE, PAD_MD))

        self.btn_new_prof = self.register_i18n(
            ctk.CTkButton(
                prof_frame,
                text=tr("profile.btn_new_profile", "Neues Profil"),
                command=self.open_create_profile_dialog,
                fg_color=COLOR_SUCCESS,
                width=BTN_WIDTH_LG,
            ),
            "profile.btn_new_profile",
            "Neues Profil",
        )
        self.btn_new_prof.pack(side="left")

        # Section 2: Persönliche Angaben & Kontaktdaten (Kompakte 2-Spalten-Anordnung)
        self.user_details_hdr_lbl = self.register_i18n(
            ctk.CTkLabel(left_col, text=tr("profile.user_info_header", "Benutzerinformationen (Aktives Profil)"), font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight="bold")),
            "profile.user_info_header",
            "Benutzerinformationen (Aktives Profil)",
        )
        self.user_details_hdr_lbl.grid(row=2, column=0, columnspan=2, sticky="w", pady=(PAD_MD, PAD_XS))

        # Row 3: Name Label (Col 0) | Abteilung Label (Col 1)
        self.user_name_lbl = self.register_i18n(
            ctk.CTkLabel(left_col, text=tr("profile.display_name", "Name / Anzeigename *:")),
            "profile.display_name",
            "Name / Anzeigename *:",
        )
        self.user_name_lbl.grid(row=3, column=0, sticky="w", padx=(PAD_NONE, PAD_SM), pady=(PAD_XS, PAD_XS))

        self.user_dept_lbl = self.register_i18n(
            ctk.CTkLabel(left_col, text=tr("profile.dept", "Abteilung / Department *:")),
            "profile.dept",
            "Abteilung / Department *:",
        )
        self.user_dept_lbl.grid(row=3, column=1, sticky="w", padx=(PAD_SM, PAD_NONE), pady=(PAD_XS, PAD_XS))

        # Row 4: Name Entry (Col 0) | Abteilung Entry (Col 1)
        self.user_name_entry = self.register_i18n(
            ctk.CTkEntry(left_col, placeholder_text=tr("profile.name_placeholder", "Ihr Name"), width=ENTRY_WIDTH_COMPACT),
            "profile.name_placeholder",
            "Ihr Name",
            attr="placeholder_text",
        )
        self.user_name_entry.insert(0, self.profile.user.name)
        self.user_name_entry.grid(row=4, column=0, sticky="ew", padx=(PAD_NONE, PAD_SM), pady=(PAD_NONE, PAD_SM))

        self.user_dept_entry = self.register_i18n(
            ctk.CTkEntry(left_col, placeholder_text=tr("profile.dept_placeholder", "z. B. Support, Technik"), width=ENTRY_WIDTH_COMPACT),
            "profile.dept_placeholder",
            "z. B. Support, Technik",
            attr="placeholder_text",
        )
        self.user_dept_entry.insert(0, self.profile.user.department)
        self.user_dept_entry.grid(row=4, column=1, sticky="ew", padx=(PAD_SM, PAD_NONE), pady=(PAD_NONE, PAD_SM))

        # Row 5: Durchwahl Label (Col 0) | Mobiltelefon Label (Col 1)
        self.user_ext_lbl = self.register_i18n(
            ctk.CTkLabel(left_col, text=tr("profile.ext", "Durchwahl / Extension:")),
            "profile.ext",
            "Durchwahl / Extension:",
        )
        self.user_ext_lbl.grid(row=5, column=0, sticky="w", padx=(PAD_NONE, PAD_SM), pady=(PAD_XS, PAD_XS))

        self.user_mobile_lbl = self.register_i18n(
            ctk.CTkLabel(left_col, text=tr("profile.mobile", "Mobiltelefon:")),
            "profile.mobile",
            "Mobiltelefon:",
        )
        self.user_mobile_lbl.grid(row=5, column=1, sticky="w", padx=(PAD_SM, PAD_NONE), pady=(PAD_XS, PAD_XS))

        # Row 6: Durchwahl Entry (Col 0) | Mobiltelefon Entry (Col 1)
        self.user_ext_entry = self.register_i18n(
            ctk.CTkEntry(left_col, placeholder_text=tr("profile.ext_placeholder", "z.B. 4012"), width=ENTRY_WIDTH_COMPACT),
            "profile.ext_placeholder",
            "z.B. 4012",
            attr="placeholder_text",
        )
        self.user_ext_entry.insert(0, self.profile.user.extension)
        self.user_ext_entry.grid(row=6, column=0, sticky="ew", padx=(PAD_NONE, PAD_SM), pady=(PAD_NONE, PAD_SM))

        self.user_mobile_entry = self.register_i18n(
            ctk.CTkEntry(left_col, placeholder_text=tr("profile.mobile_placeholder", "0170 / 1234567"), width=ENTRY_WIDTH_COMPACT),
            "profile.mobile_placeholder",
            "0170 / 1234567",
            attr="placeholder_text",
        )
        self.user_mobile_entry.insert(0, self.profile.user.mobile)
        self.user_mobile_entry.grid(row=6, column=1, sticky="ew", padx=(PAD_SM, PAD_NONE), pady=(PAD_NONE, PAD_SM))

        # Row 7 & 8: E-Mail-Adresse (Volle Breite)
        self.user_email_lbl = self.register_i18n(
            ctk.CTkLabel(left_col, text=tr("profile.email", "E-Mail-Adresse:")),
            "profile.email",
            "E-Mail-Adresse:",
        )
        self.user_email_lbl.grid(row=7, column=0, columnspan=2, sticky="w", pady=(PAD_XS, PAD_XS))

        self.user_email_entry = self.register_i18n(
            ctk.CTkEntry(left_col, placeholder_text=tr("profile.email_placeholder", "beispiel@support.de"), width=PROFILE_TAB_FIELD_WIDTH),
            "profile.email_placeholder",
            "beispiel@support.de",
            attr="placeholder_text",
        )
        self.user_email_entry.insert(0, self.profile.user.email)
        self.user_email_entry.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(PAD_NONE, PAD_SM))

        # Section 3: E-Mail Signatur (Kompakte Höhe + Datei Export/Import)
        self.sig_lbl = self.register_i18n(
            ctk.CTkLabel(left_col, text=tr("profile.signature", "E-Mail Signatur (für E-Mail-Entwürfe):")),
            "profile.signature",
            "E-Mail Signatur (für E-Mail-Entwürfe):",
        )
        self.sig_lbl.grid(row=9, column=0, columnspan=2, sticky="w", pady=(PAD_SM, PAD_XS))

        self.user_sig_txt = ctk.CTkTextbox(
            left_col,
            width=PROFILE_TAB_FIELD_WIDTH,
            height=TEXTBOX_HEIGHT_SIGNATURE,
            wrap="word",
            corner_radius=CORNER_RADIUS_ENTRY,
            border_width=1,
            border_color=COLOR_SIGNATURE_BORDER,
            fg_color=COLOR_SIGNATURE_BG,
        )
        self.user_sig_txt.insert("1.0", self.profile.user.email_signature or "")
        self.user_sig_txt.grid(row=10, column=0, columnspan=2, sticky="ew", pady=(PAD_NONE, PAD_SM))

        # Safe wrappers for backward compatibility with CTkEntry
        orig_get = self.user_sig_txt.get
        self.user_sig_txt.get = lambda index1="1.0", index2="end-1c": orig_get(index1, index2)  # type: ignore[assignment]
        orig_del = self.user_sig_txt.delete
        self.user_sig_txt.delete = lambda index1="1.0", index2="end": orig_del("1.0" if index1 in (0, "0") else index1, index2)  # type: ignore[assignment]
        orig_ins = self.user_sig_txt.insert
        self.user_sig_txt.insert = lambda index, text, *args: orig_ins("1.0" if index in (0, "0") else index, text, *args)  # type: ignore[assignment]
        self.user_sig_entry: Any = self.user_sig_txt

        sig_btn_frame = ctk.CTkFrame(left_col, fg_color="transparent")
        sig_btn_frame.grid(row=11, column=0, columnspan=2, sticky="w", pady=(PAD_NONE, PAD_MD))

        self.btn_save_sig = self.register_i18n(
            ctk.CTkButton(
                sig_btn_frame,
                text=tr("profile.btn_export_signature", "Signatur speichern..."),
                command=self.on_export_signature,
                fg_color=COLOR_MUTED_GRAY_FG,
                hover_color=COLOR_MUTED_GRAY_HOVER,
                text_color=COLOR_TEXT_WHITE,
                width=BTN_WIDTH_SIGNATURE,
            ),
            "profile.btn_export_signature",
            "Signatur speichern...",
        )
        self.btn_save_sig.pack(side="left", padx=(PAD_NONE, PAD_MD))

        self.btn_load_sig = self.register_i18n(
            ctk.CTkButton(
                sig_btn_frame,
                text=tr("profile.btn_import_signature", "Signatur laden..."),
                command=self.on_import_signature,
                fg_color=COLOR_MUTED_GRAY_FG,
                hover_color=COLOR_MUTED_GRAY_HOVER,
                text_color=COLOR_TEXT_WHITE,
                width=BTN_WIDTH_SIGNATURE,
            ),
            "profile.btn_import_signature",
            "Signatur laden...",
        )
        self.btn_load_sig.pack(side="left")

        # Section 4: P2P-Kollegen-Synchronisation (Kompakt nebeneinander)
        self.p2p_hdr_lbl = self.register_i18n(
            ctk.CTkLabel(left_col, text=tr("profile.p2p_sync_header", "P2P-Kollegen-Synchronisation"), font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight="bold")),
            "profile.p2p_sync_header",
            "P2P-Kollegen-Synchronisation",
        )
        self.p2p_hdr_lbl.grid(row=12, column=0, columnspan=2, sticky="w", pady=(PAD_SM, PAD_XS))

        self.btn_open_p2p = self.register_i18n(
            ctk.CTkButton(
                left_col,
                text=tr("profile.btn_open_p2p_sync", "P2P-Sync öffnen..."),
                command=self.on_open_p2p_sync_dialog,
                fg_color=COLOR_PRIMARY,
                hover_color=COLOR_PRIMARY_HOVER,
                width=ENTRY_WIDTH_COMPACT,
            ),
            "profile.btn_open_p2p_sync",
            "P2P-Sync öffnen...",
        )
        self.btn_open_p2p.grid(row=13, column=0, sticky="w", padx=(PAD_NONE, PAD_SM), pady=(PAD_NONE, PAD_SM))

        self.p2p_desc_lbl = self.register_i18n(
            ctk.CTkLabel(
                left_col,
                text=tr("profile.p2p_sync_desc", "Vergleichen Sie Ihre Fälle direkt mit den Daten Ihrer Kollegen im Netzwerk und übernehmen Sie Aktualisierungen."),
                font=ctk.CTkFont(size=FONT_SIZE_XS),
                text_color=COLOR_NOTE_TEXT,
                wraplength=ENTRY_WIDTH_COMPACT,
                justify="left",
            ),
            "profile.p2p_sync_desc",
            "Vergleichen Sie Ihre Fälle direkt mit den Daten Ihrer Kollegen im Netzwerk und übernehmen Sie Aktualisierungen.",
        )
        self.p2p_desc_lbl.grid(row=13, column=1, sticky="w", padx=(PAD_SM, PAD_NONE), pady=(PAD_NONE, PAD_SM))

        # Section 5: Persönliche Farbmarkierung (Kompakte Zeile)
        self.color_marker_hdr_lbl = self.register_i18n(
            ctk.CTkLabel(left_col, text=tr("profile.color_marker_header", "Persönliche Farbmarkierung"), font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight="bold")),
            "profile.color_marker_header",
            "Persönliche Farbmarkierung",
        )
        self.color_marker_hdr_lbl.grid(row=14, column=0, columnspan=2, sticky="w", pady=(PAD_SM, PAD_XS))

        self.selected_user_color: str = getattr(self.profile.user, "user_color", DEFAULT_USER_COLOR) or DEFAULT_USER_COLOR

        self.color_marker_switch = self.register_i18n(
            ctk.CTkSwitch(
                left_col,
                text=tr("profile.color_marker_enable", "Eigene Einträge & Fälle farblich hervorheben"),
                command=self.on_toggle_color_marker,
            ),
            "profile.color_marker_enable",
            "Eigene Einträge & Fälle farblich hervorheben",
        )
        if getattr(self.profile.user, "color_marker_enabled", False):
            self.color_marker_switch.select()
        else:
            self.color_marker_switch.deselect()
        self.color_marker_switch.grid(row=15, column=0, columnspan=2, sticky="w", pady=(PAD_NONE, PAD_SM))

        color_row_frame = ctk.CTkFrame(left_col, fg_color="transparent")
        color_row_frame.grid(row=16, column=0, columnspan=2, sticky="w", pady=(PAD_NONE, PAD_SM))

        self._color_presets = list(USER_COLOR_PRESETS)
        self._preset_buttons = []
        for color in self._color_presets:
            btn = ctk.CTkButton(
                color_row_frame,
                text="",
                width=USER_COLOR_PRESET_TILE_SIZE,
                height=USER_COLOR_PRESET_TILE_SIZE,
                corner_radius=CORNER_RADIUS_SM,
                fg_color=color,
                hover_color=color,
                border_width=BORDER_WIDTH_COLOR_SELECTED if color.lower() == self.selected_user_color.lower() else 1,
                border_color=COLOR_PRESET_BORDER_SELECTED if color.lower() == self.selected_user_color.lower() else COLOR_BORDER_DARK,
                command=lambda c=color: self.set_selected_user_color(c),
            )
            btn.pack(side="left", padx=(PAD_NONE, PAD_SM))
            self._preset_buttons.append((color, btn))

        self.btn_pick_color = self.register_i18n(
            ctk.CTkButton(
                color_row_frame,
                text=tr("profile.color_marker_select", "Farbe wählen..."),
                width=BTN_WIDTH_MD,
                command=self.on_pick_custom_color,
                fg_color=COLOR_MUTED_GRAY_FG,
                hover_color=COLOR_MUTED_GRAY_HOVER,
                text_color=COLOR_TEXT_WHITE,
            ),
            "profile.color_marker_select",
            "Farbe wählen...",
        )
        self.btn_pick_color.pack(side="left", padx=(PAD_SM, PAD_NONE))

        preview_row_frame = ctk.CTkFrame(left_col, fg_color="transparent")
        preview_row_frame.grid(row=17, column=0, columnspan=2, sticky="w", pady=(PAD_XS, PAD_SM))

        self.preview_lbl = self.register_i18n(
            ctk.CTkLabel(preview_row_frame, text=tr("profile.color_marker_preview", "Vorschau:"), font=ctk.CTkFont(size=FONT_SIZE_SM)),
            "profile.color_marker_preview",
            "Vorschau:",
        )
        self.preview_lbl.pack(side="left", padx=(PAD_NONE, PAD_MD))

        self.preview_tile = ctk.CTkFrame(
            preview_row_frame,
            width=USER_COLOR_PREVIEW_TILE_SIZE,
            height=USER_COLOR_PREVIEW_TILE_SIZE,
            corner_radius=CORNER_RADIUS_SM,
            fg_color=self.selected_user_color,
            border_width=1,
            border_color=COLOR_BORDER_DARK,
        )
        self.preview_tile.pack(side="left", padx=(PAD_NONE, PAD_MD), pady=PAD_XS)

        self.preview_sample_lbl = ctk.CTkLabel(
            preview_row_frame,
            text=f"{tr('profile.color_marker_sample', 'Eigener Eintrag')} ({self.profile.user.name or 'Benutzer'})",
            font=ctk.CTkFont(size=FONT_SIZE_SM),
            text_color=COLOR_NOTE_TEXT,
        )
        self.preview_sample_lbl.pack(side="left")

    def on_toggle_color_marker(self) -> None:
        if hasattr(self, "color_marker_switch"):
            self.profile.user.color_marker_enabled = bool(self.color_marker_switch.get())

    def set_selected_user_color(self, color: str) -> None:
        self.selected_user_color = color
        self.profile.user.user_color = color
        if hasattr(self, "preview_tile"):
            self.preview_tile.configure(fg_color=color)
        if hasattr(self, "_preset_buttons"):
            for c, btn in self._preset_buttons:
                is_selected = (c.lower() == color.lower())
                btn.configure(
                    border_width=BORDER_WIDTH_COLOR_SELECTED if is_selected else 1,
                    border_color=COLOR_PRESET_BORDER_SELECTED if is_selected else COLOR_BORDER_DARK,
                )

    def on_pick_custom_color(self) -> None:
        from tkinter import colorchooser
        res = colorchooser.askcolor(
            color=getattr(self, "selected_user_color", DEFAULT_USER_COLOR),
            title=tr("profile.color_marker_select", "Farbe wählen..."),
            parent=cast(tk.Misc, self),
        )
        if res and res[1]:
            self.set_selected_user_color(res[1])

    def on_open_p2p_sync_dialog(self) -> None:
        parent = getattr(self, "master", None) or getattr(self, "_parent", None)
        open_fn = getattr(parent, "open_p2p_dialog", None)
        if callable(open_fn):
            open_fn()
        else:
            from ui.dialogs.p2p_diff_dialog import P2PDiffDialog
            from services.p2p_sync_service import P2PSyncService
            p2p_service = getattr(parent, "p2p_service", None) or getattr(parent, "p2p_sync_service", None) or P2PSyncService(self.storage_service)
            colleagues = getattr(parent, "colleagues", None) or self.storage_service.load_colleagues()
            on_sync_completed = getattr(parent, "on_p2p_sync_completed", lambda: None)
            P2PDiffDialog(
                self,
                colleagues=colleagues,
                p2p_service=p2p_service,
                on_sync_completed=on_sync_completed,
            )

    def on_export_signature(self) -> None:
        from tkinter import filedialog
        current_sig = self.user_sig_txt.get("1.0", "end-1c") if hasattr(self, "user_sig_txt") else ""
        file_path = filedialog.asksaveasfilename(
            title=tr("profile.title_save_sig", "Signatur in Datei speichern"),
            defaultextension=".txt",
            filetypes=get_file_types_signature_export(),
            initialfile=DEFAULT_SIGNATURE_FILENAME,
            parent=cast(tk.Misc, self),
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(current_sig)
                self.status_lbl.configure(text=tr("profile.sig_saved_success", "✅ Signatur erfolgreich gespeichert!"), text_color=COLOR_SUCCESS)
            except Exception as e:
                self.status_lbl.configure(text=tr("profile.sig_saved_error", "⚠ Fehler beim Speichern der Signatur: {error}", error=str(e)), text_color=COLOR_DANGER)

    def on_import_signature(self) -> None:
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title=tr("profile.title_load_sig", "Signatur aus Datei laden"),
            filetypes=get_file_types_signature_import(),
            parent=cast(tk.Misc, self),
        )
        if file_path:
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
                self.user_sig_txt.delete("1.0", "end")
                self.user_sig_txt.insert("1.0", content)
                self.status_lbl.configure(text=tr("profile.sig_loaded_success", "✅ Signatur geladen!"), text_color=COLOR_SUCCESS)
            except Exception as e:
                self.status_lbl.configure(text=tr("profile.sig_loaded_error", "⚠ Fehler beim Laden der Signatur: {error}", error=str(e)), text_color=COLOR_DANGER)

    def open_create_profile_dialog(self) -> None:
        dialog = self.register_i18n(
            ctk.CTkInputDialog(
                text=tr("profile.input_new_user_text", "Geben Sie den Namen des neuen Mitarbeiters ein:"),
                title=tr("profile.input_new_user_title", "Neues Mitarbeiter-Profil anlegen"),
            ),
            "profile.input_new_user_text",
            "Geben Sie den Namen des neuen Mitarbeiters ein:",
        )
        name_input = dialog.get_input()
        if name_input and name_input.strip():
            new_name = name_input.strip()

            # Auto-save current profile before creating new profile
            if hasattr(self, "save_settings_quietly"):
                self.save_settings_quietly()

            from config import get_default_workspace_dir
            from models.profile import PathSettings
            new_profile = UserProfile(
                user=UserInfo(name=new_name),
                path_settings=PathSettings(workspace_dir=str(get_default_workspace_dir())),
            )
            self.storage_service.save_profile(new_profile, sync=True)
            self.storage_service.apply_profile_paths(new_profile)

            # Refresh list & switch
            self.profile = new_profile
            profiles_list = self.storage_service.list_profiles()
            self.profile_combo.configure(values=profiles_list)
            self.profile_combo.set(new_name)

            if hasattr(self, "reload_all_tabs"):
                self.reload_all_tabs()
            else:
                self.reload_user_fields()

            self.status_lbl.configure(text=tr("profile.created_and_activated", "Profil '{name}' angelegt und aktiviert!", name=new_name), text_color=COLOR_SUCCESS)
            if self.on_profile_updated:
                self.on_profile_updated()

    def on_switch_profile(self, selected_name: str) -> None:
        if selected_name == self.profile.user.name:
            return

        # Auto-save current profile before switching
        if hasattr(self, "save_settings_quietly"):
            self.save_settings_quietly()

        self.profile = self.storage_service.load_profile_by_name(selected_name)
        self.storage_service.save_profile(self.profile, sync=True)
        self.storage_service.apply_profile_paths(self.profile)

        if hasattr(self, "reload_all_tabs"):
            self.reload_all_tabs()
        else:
            self.reload_user_fields()

        self.status_lbl.configure(text=tr("profile.switched_to", "Profil auf '{name}' gewechselt.", name=selected_name), text_color=COLOR_SUCCESS)
        if self.on_profile_updated:
            self.on_profile_updated()

    def reload_user_fields(self) -> None:
        if hasattr(self, "profile_combo"):
            profiles_list = self.storage_service.list_profiles()
            self.profile_combo.configure(values=profiles_list)
            if self.profile.user.name in profiles_list:
                self.profile_combo.set(self.profile.user.name)

        if hasattr(self, "user_name_entry"):
            self.user_name_entry.delete(0, "end")
            self.user_name_entry.insert(0, self.profile.user.name)

        if hasattr(self, "user_dept_entry"):
            self.user_dept_entry.delete(0, "end")
            self.user_dept_entry.insert(0, self.profile.user.department)

        if hasattr(self, "user_ext_entry"):
            self.user_ext_entry.delete(0, "end")
            self.user_ext_entry.insert(0, self.profile.user.extension)

        if hasattr(self, "user_email_entry"):
            self.user_email_entry.delete(0, "end")
            self.user_email_entry.insert(0, self.profile.user.email)

        if hasattr(self, "user_mobile_entry"):
            self.user_mobile_entry.delete(0, "end")
            self.user_mobile_entry.insert(0, self.profile.user.mobile)

        if hasattr(self, "user_sig_txt"):
            self.user_sig_txt.delete("1.0", "end")
            self.user_sig_txt.insert("1.0", self.profile.user.email_signature or "")

        if hasattr(self, "color_marker_switch"):
            if getattr(self.profile.user, "color_marker_enabled", False):
                self.color_marker_switch.select()
            else:
                self.color_marker_switch.deselect()

        if hasattr(self, "preview_tile"):
            self.set_selected_user_color(getattr(self.profile.user, "user_color", DEFAULT_USER_COLOR))

        if hasattr(self, "preview_sample_lbl"):
            self.preview_sample_lbl.configure(
                text=f"{tr('profile.color_marker_sample', 'Eigener Eintrag')} ({self.profile.user.name or 'Benutzer'})"
            )

        if hasattr(self, "reload_ui_fields"):
            self.reload_ui_fields()

    def save_user_settings(self) -> bool:
        name = self.user_name_entry.get().strip()
        if not name:
            self.status_lbl.configure(text=tr("profile.username_empty", "⚠ Benutzername darf nicht leer sein!"), text_color=COLOR_DANGER)
            return False

        self.profile.user.name = name
        self.profile.user.department = self.user_dept_entry.get().strip() or DEFAULT_DEPARTMENT
        self.profile.user.extension = self.user_ext_entry.get().strip()
        self.profile.user.email = self.user_email_entry.get().strip()
        self.profile.user.mobile = self.user_mobile_entry.get().strip()
        if hasattr(self, "user_sig_txt"):
            self.profile.user.email_signature = self.user_sig_txt.get("1.0", "end-1c").strip()
        if hasattr(self, "color_marker_switch"):
            self.profile.user.color_marker_enabled = bool(self.color_marker_switch.get())
        if hasattr(self, "selected_user_color"):
            self.profile.user.user_color = self.selected_user_color
        return True

    def refresh_user_tab_labels(self) -> None:
        if hasattr(self, "user_tab_hdr_lbl"):
            self.user_tab_hdr_lbl.configure(text=tr("profile.user_tab_header", "Mitarbeiter-Profil verwalten & wechseln"))
        if hasattr(self, "active_prof_lbl"):
            self.active_prof_lbl.configure(text=tr("profile.active_profile", "Aktives Profil:"))
        if hasattr(self, "btn_new_prof"):
            self.btn_new_prof.configure(text=tr("profile.btn_new_profile", "Neues Profil anlegen"))
        if hasattr(self, "user_details_hdr_lbl"):
            self.user_details_hdr_lbl.configure(text=tr("profile.user_info_header", "Benutzerinformationen (Aktives Profil)"))
        if hasattr(self, "user_name_lbl"):
            self.user_name_lbl.configure(text=tr("profile.display_name", "Name / Anzeigename *:"))
        if hasattr(self, "user_dept_lbl"):
            self.user_dept_lbl.configure(text=tr("profile.dept", "Abteilung / Department *:"))
        if hasattr(self, "user_ext_lbl"):
            self.user_ext_lbl.configure(text=tr("profile.ext", "Durchwahl / Extension:"))
        if hasattr(self, "user_mobile_lbl"):
            self.user_mobile_lbl.configure(text=tr("profile.mobile", "Mobiltelefon:"))
        if hasattr(self, "user_email_lbl"):
            self.user_email_lbl.configure(text=tr("profile.email", "E-Mail-Adresse:"))
        if hasattr(self, "sig_lbl"):
            self.sig_lbl.configure(text=tr("profile.signature", "E-Mail Signatur (für E-Mail-Entwürfe):"))
        if hasattr(self, "btn_save_sig"):
            self.btn_save_sig.configure(text=tr("profile.btn_export_signature", "Signatur speichern..."))
        if hasattr(self, "btn_load_sig"):
            self.btn_load_sig.configure(text=tr("profile.btn_import_signature", "Signatur laden..."))
        if hasattr(self, "p2p_hdr_lbl"):
            self.p2p_hdr_lbl.configure(text=tr("profile.p2p_sync_header", "P2P-Kollegen-Synchronisation"))
        if hasattr(self, "p2p_desc_lbl"):
            self.p2p_desc_lbl.configure(text=tr("profile.p2p_sync_desc", "Vergleichen Sie Ihre Fälle direkt mit den Daten Ihrer Kollegen im Netzwerk und übernehmen Sie Aktualisierungen."))
        if hasattr(self, "btn_open_p2p"):
            self.btn_open_p2p.configure(text=tr("profile.btn_open_p2p_sync", "P2P-Sync öffnen..."))
        if hasattr(self, "color_marker_hdr_lbl"):
            self.color_marker_hdr_lbl.configure(text=tr("profile.color_marker_header", "Persönliche Farbmarkierung"))
        if hasattr(self, "color_marker_switch"):
            self.color_marker_switch.configure(text=tr("profile.color_marker_enable", "Eigene Einträge & Fälle farblich hervorheben"))
        if hasattr(self, "btn_pick_color"):
            self.btn_pick_color.configure(text=tr("profile.color_marker_select", "Farbe wählen..."))
        if hasattr(self, "preview_lbl"):
            self.preview_lbl.configure(text=tr("profile.color_marker_preview", "Vorschau:"))
        if hasattr(self, "preview_sample_lbl"):
            self.preview_sample_lbl.configure(
                text=f"{tr('profile.color_marker_sample', 'Eigener Eintrag')} ({self.profile.user.name or 'Benutzer'})"
            )
