from typing import TYPE_CHECKING, Any, cast
from collections.abc import Callable
import tkinter as tk
import customtkinter as ctk

from models.profile import UserInfo, UserProfile
from services.i18n_service import tr


class UserSettingsTabMixin:
    """Mixin for User Profile management, personal data, and signature export/import."""

    if TYPE_CHECKING:
        profile: Any
        storage_service: Any
        status_lbl: ctk.CTkLabel
        on_profile_updated: Callable[[], None] | None
        register_i18n: Callable[..., Any]
        reload_ui_fields: Callable[[], None]

    def setup_user_section(self, left_col: ctk.CTkFrame) -> None:
        # Section 1: Profil verwalten & wechseln
        self.user_tab_hdr_lbl = self.register_i18n(
            ctk.CTkLabel(left_col, text=tr("profile.user_tab_header", "Mitarbeiter-Profil verwalten & wechseln"), font=ctk.CTkFont(size=14, weight="bold")),
            "profile.user_tab_header",
            "Mitarbeiter-Profil verwalten & wechseln",
        )
        self.user_tab_hdr_lbl.pack(anchor="w", pady=(5, 5))

        prof_frame = ctk.CTkFrame(left_col, fg_color="transparent")
        prof_frame.pack(anchor="w", pady=(0, 15))

        self.active_prof_lbl = self.register_i18n(
            ctk.CTkLabel(prof_frame, text=tr("profile.active_profile", "Aktives Profil:")),
            "profile.active_profile",
            "Aktives Profil:",
        )
        self.active_prof_lbl.pack(side="left", padx=(0, 10))

        profiles_list = self.storage_service.list_profiles()
        self.profile_combo = ctk.CTkOptionMenu(
            prof_frame,
            values=profiles_list,
            command=self.on_switch_profile,
            width=210,
        )
        self.profile_combo.set(self.profile.user.name if self.profile.user.name in profiles_list else profiles_list[0])
        self.profile_combo.pack(side="left", padx=(0, 10))

        self.btn_new_prof = self.register_i18n(
            ctk.CTkButton(
                prof_frame,
                text=tr("profile.btn_new_profile", "➕ Neues Profil"),
                command=self.open_create_profile_dialog,
                fg_color="forestgreen",
                width=130,
            ),
            "profile.btn_new_profile",
            "➕ Neues Profil",
        )
        self.btn_new_prof.pack(side="left")

        # Section 2: Persönliche Angaben & Kontaktdaten
        self.user_details_hdr_lbl = self.register_i18n(
            ctk.CTkLabel(left_col, text=tr("profile.user_info_header", "Benutzerinformationen (Aktives Profil)"), font=ctk.CTkFont(size=14, weight="bold")),
            "profile.user_info_header",
            "Benutzerinformationen (Aktives Profil)",
        )
        self.user_details_hdr_lbl.pack(anchor="w", pady=(8, 4))

        self.register_i18n(
            ctk.CTkLabel(left_col, text=tr("profile.display_name", "Name / Anzeigename *:")),
            "profile.display_name",
            "Name / Anzeigename *:",
        ).pack(anchor="w", pady=(4, 2))
        self.user_name_entry = self.register_i18n(
            ctk.CTkEntry(left_col, placeholder_text=tr("profile.name_placeholder", "Ihr Name"), width=380),
            "profile.name_placeholder",
            "Ihr Name",
            attr="placeholder_text",
        )
        self.user_name_entry.insert(0, self.profile.user.name)
        self.user_name_entry.pack(anchor="w", pady=(0, 7))

        self.register_i18n(
            ctk.CTkLabel(left_col, text=tr("profile.dept", "Abteilung / Department *:")),
            "profile.dept",
            "Abteilung / Department *:",
        ).pack(anchor="w", pady=(4, 2))
        self.user_dept_entry = self.register_i18n(
            ctk.CTkEntry(left_col, placeholder_text=tr("profile.dept_placeholder", "z. B. Support, Entwicklung, Technik"), width=380),
            "profile.dept_placeholder",
            "z. B. Support, Entwicklung, Technik",
            attr="placeholder_text",
        )
        self.user_dept_entry.insert(0, self.profile.user.department)
        self.user_dept_entry.pack(anchor="w", pady=(0, 7))

        self.register_i18n(
            ctk.CTkLabel(left_col, text=tr("profile.ext", "Durchwahl / Extension:")),
            "profile.ext",
            "Durchwahl / Extension:",
        ).pack(anchor="w", pady=(4, 2))
        self.user_ext_entry = self.register_i18n(
            ctk.CTkEntry(left_col, placeholder_text=tr("profile.ext_placeholder", "z.B. 4012"), width=380),
            "profile.ext_placeholder",
            "z.B. 4012",
            attr="placeholder_text",
        )
        self.user_ext_entry.insert(0, self.profile.user.extension)
        self.user_ext_entry.pack(anchor="w", pady=(0, 7))

        self.register_i18n(
            ctk.CTkLabel(left_col, text=tr("profile.email", "E-Mail-Adresse:")),
            "profile.email",
            "E-Mail-Adresse:",
        ).pack(anchor="w", pady=(4, 2))
        self.user_email_entry = self.register_i18n(
            ctk.CTkEntry(left_col, placeholder_text=tr("profile.email_placeholder", "beispiel@support.de"), width=380),
            "profile.email_placeholder",
            "beispiel@support.de",
            attr="placeholder_text",
        )
        self.user_email_entry.insert(0, self.profile.user.email)
        self.user_email_entry.pack(anchor="w", pady=(0, 7))

        self.register_i18n(
            ctk.CTkLabel(left_col, text=tr("profile.mobile", "Mobiltelefon:")),
            "profile.mobile",
            "Mobiltelefon:",
        ).pack(anchor="w", pady=(4, 2))
        self.user_mobile_entry = self.register_i18n(
            ctk.CTkEntry(left_col, placeholder_text=tr("profile.mobile_placeholder", "0170 / 1234567"), width=380),
            "profile.mobile_placeholder",
            "0170 / 1234567",
            attr="placeholder_text",
        )
        self.user_mobile_entry.insert(0, self.profile.user.mobile)
        self.user_mobile_entry.pack(anchor="w", pady=(0, 7))

        # Section 3: E-Mail Signatur (mehrzeilig + Datei Export/Import)
        self.sig_lbl = self.register_i18n(
            ctk.CTkLabel(left_col, text=tr("profile.signature", "E-Mail Signatur (für E-Mail-Entwürfe):")),
            "profile.signature",
            "E-Mail Signatur (für E-Mail-Entwürfe):",
        )
        self.sig_lbl.pack(anchor="w", pady=(4, 2))

        self.user_sig_txt = ctk.CTkTextbox(
            left_col,
            width=380,
            height=95,
            wrap="word",
            corner_radius=6,
            border_width=1,
            border_color=("gray65", "gray35"),
            fg_color=("#F8F9FA", "gray17"),
        )
        self.user_sig_txt.insert("1.0", self.profile.user.email_signature or "")
        self.user_sig_txt.pack(anchor="w", pady=(0, 6))

        # Safe wrappers for backward compatibility with CTkEntry
        orig_get = self.user_sig_txt.get
        self.user_sig_txt.get = lambda index1="1.0", index2="end-1c": orig_get(index1, index2)  # type: ignore[assignment]
        orig_del = self.user_sig_txt.delete
        self.user_sig_txt.delete = lambda index1="1.0", index2="end": orig_del("1.0" if index1 in (0, "0") else index1, index2)  # type: ignore[assignment]
        orig_ins = self.user_sig_txt.insert
        self.user_sig_txt.insert = lambda index, text, *args: orig_ins("1.0" if index in (0, "0") else index, text, *args)  # type: ignore[assignment]
        self.user_sig_entry: Any = self.user_sig_txt

        sig_btn_frame = ctk.CTkFrame(left_col, fg_color="transparent")
        sig_btn_frame.pack(anchor="w", pady=(0, 8))

        self.btn_save_sig = self.register_i18n(
            ctk.CTkButton(
                sig_btn_frame,
                text=tr("profile.btn_export_signature", "💾 Signatur speichern..."),
                command=self.on_export_signature,
                fg_color=("gray45", "gray35"),
                hover_color=("gray35", "gray45"),
                text_color="white",
                width=185,
            ),
            "profile.btn_export_signature",
            "💾 Signatur speichern...",
        )
        self.btn_save_sig.pack(side="left", padx=(0, 10))

        self.btn_load_sig = self.register_i18n(
            ctk.CTkButton(
                sig_btn_frame,
                text=tr("profile.btn_import_signature", "📂 Signatur laden..."),
                command=self.on_import_signature,
                fg_color=("gray45", "gray35"),
                hover_color=("gray35", "gray45"),
                text_color="white",
                width=185,
            ),
            "profile.btn_import_signature",
            "📂 Signatur laden...",
        )
        self.btn_load_sig.pack(side="left")

    def on_export_signature(self) -> None:
        from tkinter import filedialog
        current_sig = self.user_sig_txt.get("1.0", "end-1c") if hasattr(self, "user_sig_txt") else ""
        file_path = filedialog.asksaveasfilename(
            title=tr("profile.title_save_sig", "Signatur in Datei speichern"),
            defaultextension=".txt",
            filetypes=[
                ("Textdatei (*.txt)", "*.txt"),
                ("HTML-Datei (*.html)", "*.html"),
                ("Markdown (*.md)", "*.md"),
                ("Alle Dateien (*.*)", "*.*"),
            ],
            initialfile="email_signature.txt",
            parent=cast(tk.Misc, self),
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(current_sig)
                self.status_lbl.configure(text=tr("profile.sig_saved_success", "✅ Signatur erfolgreich gespeichert!"), text_color="green")
            except Exception as e:
                self.status_lbl.configure(text=f"⚠ Fehler beim Speichern der Signatur: {e}", text_color="red")

    def on_import_signature(self) -> None:
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title=tr("profile.title_load_sig", "Signatur aus Datei laden"),
            filetypes=[
                ("Text- & Web-Dateien (*.txt, *.html, *.md)", "*.txt *.html *.htm *.md"),
                ("Textdatei (*.txt)", "*.txt"),
                ("HTML-Datei (*.html, *.htm)", "*.html *.htm"),
                ("Markdown (*.md)", "*.md"),
                ("Alle Dateien (*.*)", "*.*"),
            ],
            parent=cast(tk.Misc, self),
        )
        if file_path:
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
                self.user_sig_txt.delete("1.0", "end")
                self.user_sig_txt.insert("1.0", content)
                self.status_lbl.configure(text=tr("profile.sig_loaded_success", "✅ Signatur geladen!"), text_color="green")
            except Exception as e:
                self.status_lbl.configure(text=f"⚠ Fehler beim Laden der Signatur: {e}", text_color="red")

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
            new_profile = UserProfile(user=UserInfo(name=new_name))
            self.storage_service.save_profile(new_profile)

            # Refresh list & switch
            self.profile = new_profile
            profiles_list = self.storage_service.list_profiles()
            self.profile_combo.configure(values=profiles_list)
            self.profile_combo.set(new_name)
            self.reload_user_fields()
            self.status_lbl.configure(text=tr("profile.created_and_activated", "Profil '{name}' angelegt und aktiviert!", name=new_name))
            if self.on_profile_updated:
                self.on_profile_updated()

    def on_switch_profile(self, selected_name: str) -> None:
        self.profile = self.storage_service.load_profile_by_name(selected_name)
        self.storage_service.save_profile(self.profile)
        self.reload_user_fields()
        self.status_lbl.configure(text=tr("profile.switched_to", "Profil auf '{name}' gewechselt.", name=selected_name))
        if self.on_profile_updated:
            self.on_profile_updated()

    def reload_user_fields(self) -> None:
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

        if hasattr(self, "user_sig_txt"):
            self.user_sig_txt.delete("1.0", "end")
            self.user_sig_txt.insert("1.0", self.profile.user.email_signature or "")

        if hasattr(self, "reload_ui_fields"):
            self.reload_ui_fields()

    def save_user_settings(self) -> bool:
        name = self.user_name_entry.get().strip()
        if not name:
            self.status_lbl.configure(text=tr("profile.username_empty", "⚠ Benutzername darf nicht leer sein!"), text_color="red")
            return False

        self.profile.user.name = name
        self.profile.user.department = self.user_dept_entry.get().strip() or "Support"
        self.profile.user.extension = self.user_ext_entry.get().strip()
        self.profile.user.email = self.user_email_entry.get().strip()
        self.profile.user.mobile = self.user_mobile_entry.get().strip()
        if hasattr(self, "user_sig_txt"):
            self.profile.user.email_signature = self.user_sig_txt.get("1.0", "end-1c").strip()
        return True

    def refresh_user_tab_labels(self) -> None:
        if hasattr(self, "user_tab_hdr_lbl"):
            self.user_tab_hdr_lbl.configure(text=tr("profile.user_tab_header", "Mitarbeiter-Profil verwalten & wechseln"))
        if hasattr(self, "active_prof_lbl"):
            self.active_prof_lbl.configure(text=tr("profile.active_profile", "Aktives Profil:"))
        if hasattr(self, "btn_new_prof"):
            self.btn_new_prof.configure(text=tr("profile.btn_new_profile", "➕ Neues Profil anlegen"))
        if hasattr(self, "user_details_hdr_lbl"):
            self.user_details_hdr_lbl.configure(text=tr("profile.user_info_header", "Benutzerinformationen (Aktives Profil)"))
        if hasattr(self, "sig_lbl"):
            self.sig_lbl.configure(text=tr("profile.signature", "E-Mail Signatur (für E-Mail-Entwürfe):"))
        if hasattr(self, "btn_save_sig"):
            self.btn_save_sig.configure(text=tr("profile.btn_export_signature", "💾 Signatur speichern..."))
        if hasattr(self, "btn_load_sig"):
            self.btn_load_sig.configure(text=tr("profile.btn_import_signature", "📂 Signatur laden..."))
