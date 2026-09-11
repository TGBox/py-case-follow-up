import customtkinter as ctk

from ui.dialogs.base_dialog import BaseDialog
from collections.abc import Callable
from models.profile import Colleague
from services.storage_service import StorageService
from constants import DEFAULT_DEPARTMENTS, DIALOG_DIMENSIONS, DIALOG_TITLES
from utils.ui_utils import create_highlighted_label, bind_mouse_wheel_to_canvas

DEPARTMENTS = DEFAULT_DEPARTMENTS


class ColleagueManagementDialog(BaseDialog):
    """Modal dialog for managing reference employees / colleagues (CRUD)."""

    def __init__(
        self,
        parent,
        storage_service: StorageService,
        on_colleagues_updated: Callable[[], None] | None = None,
    ):
        super().__init__(parent)
        self.storage_service = storage_service
        self.on_colleagues_updated = on_colleagues_updated

        w, h = DIALOG_DIMENSIONS["colleague_mgmt"]
        self.setup_window(
            parent,
            DIALOG_TITLES["colleague_mgmt"],
            (w, h),
            min_size=(900, 600),

            title_factory=lambda: DIALOG_TITLES["colleague_mgmt"],
        )

        self.colleagues: list[Colleague] = []
        self.filtered_colleagues: list[Colleague] = []
        self.selected_colleague: Colleague | None = None

        self.create_widgets()
        self.load_colleagues()

    def create_widgets(self):
        from services.i18n_service import tr
        from constants import get_localized_departments

        departments = get_localized_departments()

        # Header Bar
        top_bar = ctk.CTkFrame(self, height=45, corner_radius=0)
        top_bar.pack(fill="x", side="top", padx=10, pady=(10, 5))

        self.register_i18n(ctk.CTkLabel(
            top_bar,
            text=tr("colleague_mgmt.header", "👥 Mitarbeiter- & Kollegeneinträge"),
            font=ctk.CTkFont(size=16, weight="bold"),
        ), "colleague_mgmt.header", "👥 Mitarbeiter- & Kollegeneinträge").pack(side="left", padx=10)

        new_btn = self.register_i18n(ctk.CTkButton(
            top_bar,
            text=tr("colleague_mgmt.new_colleague_btn", "+ Neuen Mitarbeiter anlegen"),
            command=self.on_click_new_colleague,
            fg_color="forestgreen",
            width=180,
        ), "colleague_mgmt.new_colleague_btn", "+ Neuen Mitarbeiter anlegen")
        new_btn.pack(side="right", padx=10)

        # Body Frame
        body_frame = ctk.CTkFrame(self, fg_color="transparent")
        body_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        # Left list panel
        left_frame = ctk.CTkFrame(body_frame, width=320)
        left_frame.pack(side="left", fill="y", padx=(0, 5), pady=0)
        left_frame.pack_propagate(False)

        self.search_entry = self.register_i18n(ctk.CTkEntry(
            left_frame, placeholder_text=tr("colleague_mgmt.search_placeholder", "🔍 Name, Kürzel, Abteilung...")
        ), "colleague_mgmt.search_placeholder", "🔍 Name, Kürzel, Abteilung...", attr="placeholder_text")
        self.search_entry.pack(fill="x", padx=10, pady=(10, 5))
        self.search_entry.bind("<KeyRelease>", self.on_search_changed)

        self.list_scroll = ctk.CTkScrollableFrame(left_frame, fg_color="transparent")
        self.list_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        # Right editor panel
        right_frame = ctk.CTkFrame(body_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0), pady=0)

        self.form_header_lbl = self.register_i18n(ctk.CTkLabel(
            right_frame,
            text=tr("colleague_mgmt.details_header", "Mitarbeiterdetails"),
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        ), "colleague_mgmt.details_header", "Mitarbeiterdetails")
        self.form_header_lbl.pack(fill="x", padx=15, pady=(12, 8))

        form_scroll = ctk.CTkScrollableFrame(right_frame, fg_color="transparent")
        form_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Fields
        self.register_i18n(ctk.CTkLabel(form_scroll, text=tr("colleague_mgmt.username", "Kürzel / Username *:")), "colleague_mgmt.username", "Kürzel / Username *:").pack(anchor="w", pady=(4, 2))
        self.username_entry = self.register_i18n(ctk.CTkEntry(form_scroll, placeholder_text=tr("colleague_mgmt.username_placeholder", "z. B. mmueller")), "colleague_mgmt.username_placeholder", "z. B. mmueller", attr="placeholder_text")
        self.username_entry.pack(fill="x", pady=(0, 10))

        self.register_i18n(ctk.CTkLabel(form_scroll, text=tr("colleague_mgmt.name", "Name / Anzeigename *:")), "colleague_mgmt.name", "Name / Anzeigename *:").pack(anchor="w", pady=(4, 2))
        self.name_entry = self.register_i18n(ctk.CTkEntry(form_scroll, placeholder_text=tr("colleague_mgmt.name_placeholder", "z. B. Max Müller")), "colleague_mgmt.name_placeholder", "z. B. Max Müller", attr="placeholder_text")
        self.name_entry.pack(fill="x", pady=(0, 10))

        self.register_i18n(ctk.CTkLabel(form_scroll, text=tr("colleague_mgmt.department", "Abteilung / Department:")), "colleague_mgmt.department", "Abteilung / Department:").pack(anchor="w", pady=(4, 2))
        self.dept_combo = ctk.CTkOptionMenu(form_scroll, values=departments)
        self.dept_combo.set(departments[0])
        self.dept_combo.pack(fill="x", pady=(0, 10))

        self.register_i18n(ctk.CTkLabel(form_scroll, text=tr("colleague_mgmt.phone", "Durchwahl / Telefon:")), "colleague_mgmt.phone", "Durchwahl / Telefon:").pack(anchor="w", pady=(4, 2))
        self.ext_entry = self.register_i18n(ctk.CTkEntry(form_scroll, placeholder_text=tr("colleague_mgmt.phone_placeholder", "z. B. 4012")), "colleague_mgmt.phone_placeholder", "z. B. 4012", attr="placeholder_text")
        self.ext_entry.pack(fill="x", pady=(0, 10))

        self.register_i18n(ctk.CTkLabel(form_scroll, text=tr("colleague_mgmt.email", "E-Mail-Adresse:")), "colleague_mgmt.email", "E-Mail-Adresse:").pack(anchor="w", pady=(4, 2))
        self.email_entry = self.register_i18n(ctk.CTkEntry(form_scroll, placeholder_text=tr("colleague_mgmt.email_placeholder", "z. B. m.mueller@praxis.de")), "colleague_mgmt.email_placeholder", "z. B. m.mueller@praxis.de", attr="placeholder_text")
        self.email_entry.pack(fill="x", pady=(0, 10))

        self.register_i18n(ctk.CTkLabel(form_scroll, text=tr("colleague_mgmt.mobile", "Mobiltelefon:")), "colleague_mgmt.mobile", "Mobiltelefon:").pack(anchor="w", pady=(4, 2))
        self.mobile_entry = self.register_i18n(ctk.CTkEntry(form_scroll, placeholder_text=tr("colleague_mgmt.mobile_placeholder", "z. B. 0170 1234567")), "colleague_mgmt.mobile_placeholder", "z. B. 0170 1234567", attr="placeholder_text")
        self.mobile_entry.pack(fill="x", pady=(0, 10))

        self.register_i18n(ctk.CTkLabel(form_scroll, text=tr("colleague_mgmt.notes", "Aufgabengebiet / Notizen:")), "colleague_mgmt.notes", "Aufgabengebiet / Notizen:").pack(anchor="w", pady=(4, 2))
        self.notes_entry = self.register_i18n(ctk.CTkEntry(form_scroll, placeholder_text=tr("colleague_mgmt.notes_placeholder", "z. B. Zuständig für PVS-Schnittstellen...")), "colleague_mgmt.notes_placeholder", "z. B. Zuständig für PVS-Schnittstellen...", attr="placeholder_text")
        self.notes_entry.pack(fill="x", pady=(0, 10))

        # Absence / Vacation settings
        self.is_absent_var = ctk.BooleanVar(value=False)
        self.chk_absent = self.register_i18n(ctk.CTkCheckBox(
            form_scroll, text=tr("colleague_mgmt.absent_chk", "⚠ Kollege ist aktuell abwesend (Urlaub / Krankheit)"), variable=self.is_absent_var
        ), "colleague_mgmt.absent_chk", "⚠ Kollege ist aktuell abwesend (Urlaub / Krankheit)")
        self.chk_absent.pack(anchor="w", pady=(5, 5))

        self.absence_reason_entry = self.register_i18n(ctk.CTkEntry(form_scroll, placeholder_text=tr("colleague_mgmt.absence_reason_placeholder", "Abwesenheitsgrund (z. B. Urlaub bis 30.08.)...")), "colleague_mgmt.absence_reason_placeholder", "Abwesenheitsgrund (z. B. Urlaub bis 30.08.)...", attr="placeholder_text")
        self.absence_reason_entry.pack(fill="x", pady=(0, 15))

        self.err_lbl = ctk.CTkLabel(form_scroll, text="", text_color="red", anchor="w")
        self.err_lbl.pack(fill="x", pady=(0, 5))

        # Bottom Action Bar
        action_bar = ctk.CTkFrame(right_frame, height=45, fg_color="transparent")
        action_bar.pack(fill="x", side="bottom", padx=15, pady=10)

        self.delete_btn = self.register_i18n(ctk.CTkButton(
            action_bar,
            text=tr("common.delete", "🗑 Löschen"),
            command=self.confirm_click_delete,
            fg_color="firebrick",
            hover_color="darkred",
            width=110,
            state="disabled",
        ), "common.delete", "🗑 Löschen")
        self.delete_btn.pack(side="left")

        self.save_btn = self.register_i18n(ctk.CTkButton(
            action_bar,
            text=tr("cockpit.save", "💾 Speichern"),
            command=self.on_click_save,
            fg_color="forestgreen",
            hover_color="darkgreen",
            width=140,
        ), "cockpit.save", "💾 Speichern")
        self.save_btn.pack(side="right")

    def load_colleagues(self):
        self.colleagues = self.storage_service.load_colleagues()
        self.filter_and_render_list()

    def filter_and_render_list(self):
        q = self.search_entry.get().strip().lower() if hasattr(self, "search_entry") else ""
        if q:
            self.filtered_colleagues = [
                c for c in self.colleagues
                if q in c.name.lower() or q in c.username.lower() or q in c.department.lower() or q in c.notes.lower()
            ]
        else:
            self.filtered_colleagues = list(self.colleagues)

        for child in self.list_scroll.winfo_children():
            child.destroy()

        from services.i18n_service import tr
        if not self.filtered_colleagues:
            self.register_i18n(ctk.CTkLabel(self.list_scroll, text=tr("colleague_mgmt.no_entries", "Keine Einträge gefunden."), text_color="gray"), "colleague_mgmt.no_entries", "Keine Einträge gefunden.").pack(pady=20)
            return

        raw_query = self.search_entry.get().strip() if hasattr(self, "search_entry") else ""

        for col in self.filtered_colleagues:
            is_sel = self.selected_colleague and self.selected_colleague.username == col.username
            bg = ("gray75", "gray35") if is_sel else ("gray85", "gray20")

            card = ctk.CTkFrame(self.list_scroll, fg_color=bg, cursor="hand2")
            card.pack(fill="x", pady=3, padx=2)
            card.bind("<Button-1>", lambda e, c=col: self.select_colleague(c))

            name_text = f"{col.name} ({col.username})"
            if raw_query and raw_query.lower() in name_text.lower():
                lbl_name = create_highlighted_label(
                    card,
                    text=name_text,
                    query=raw_query,
                    font=ctk.CTkFont(weight="bold", size=12),
                    text_color=("black", "white") if is_sel else ("gray10", "gray90"),
                    bg_color=bg,
                    wrap="none",
                    on_click=lambda e, c=col: self.select_colleague(c),
                    scroll_frame=self.list_scroll,
                )
            else:
                lbl_name = ctk.CTkLabel(card, text=name_text, font=ctk.CTkFont(weight="bold", size=12), anchor="w")
                lbl_name.bind("<Button-1>", lambda e, c=col: self.select_colleague(c))
            lbl_name.pack(fill="x", padx=8, pady=(5, 1))

            sub_txt = f"🏢 {col.department}"
            if col.extension:
                sub_txt += f" | 📞 {col.extension}"
            if raw_query and raw_query.lower() in sub_txt.lower():
                lbl_sub = create_highlighted_label(
                    card,
                    text=sub_txt,
                    query=raw_query,
                    font=ctk.CTkFont(size=10),
                    text_color=("gray40", "gray70"),
                    bg_color=bg,
                    wrap="none",
                    on_click=lambda e, c=col: self.select_colleague(c),
                    scroll_frame=self.list_scroll,
                )
            else:
                lbl_sub = ctk.CTkLabel(card, text=sub_txt, font=ctk.CTkFont(size=10), text_color=("gray40", "gray70"), anchor="w")
                lbl_sub.bind("<Button-1>", lambda e, c=col: self.select_colleague(c))
            lbl_sub.pack(fill="x", padx=8, pady=(0, 5))

            if raw_query and raw_query.lower() in col.notes.lower() and raw_query.lower() not in name_text.lower() and raw_query.lower() not in sub_txt.lower():
                matched_words = [w.strip(",;:()[]{}<>\"'\t\r\n") for w in col.notes.split() if raw_query.lower() in w.lower()]
                seen_words: set[str] = set()
                uniq_words: list[str] = []
                for w in matched_words:
                    if w.lower() not in seen_words:
                        seen_words.add(w.lower())
                        uniq_words.append(w)
                if uniq_words:
                    notes_summary = ", ".join(uniq_words[:3])
                    if len(uniq_words) > 3 or len(notes_summary) > 45:
                        notes_summary = notes_summary[:45] + "..."
                    notes_lbl = create_highlighted_label(
                        card,
                        text=f"📝 {notes_summary}",
                        query=raw_query,
                        font=ctk.CTkFont(size=10),
                        text_color=("gray45", "gray65"),
                        bg_color=bg,
                        wrap="word",
                        on_click=lambda e, c=col: self.select_colleague(c),
                        scroll_frame=self.list_scroll,
                    )
                    notes_lbl.pack(fill="x", padx=8, pady=(0, 4))

            bind_mouse_wheel_to_canvas(card, self.list_scroll)

    def on_search_changed(self, event=None):
        self.filter_and_render_list()

    def select_colleague(self, col: Colleague | None):
        from services.i18n_service import tr
        self.selected_colleague = col
        self.err_lbl.configure(text="")

        if col:
            self.form_header_lbl.configure(text=tr("colleague_mgmt.edit_header", "✏ Bearbeiten: {name}", name=col.name))
            self.username_entry.delete(0, "end")
            self.username_entry.insert(0, col.username)
            self.name_entry.delete(0, "end")
            self.name_entry.insert(0, col.name)
            self.dept_combo.set(col.department if col.department in DEPARTMENTS else DEPARTMENTS[0])
            self.ext_entry.delete(0, "end")
            self.ext_entry.insert(0, col.extension)
            self.email_entry.delete(0, "end")
            self.email_entry.insert(0, col.email)
            self.mobile_entry.delete(0, "end")
            self.mobile_entry.insert(0, col.mobile)
            self.notes_entry.delete(0, "end")
            self.notes_entry.insert(0, col.notes)
            self.is_absent_var.set(col.is_absent)
            self.absence_reason_entry.delete(0, "end")
            self.absence_reason_entry.insert(0, col.absence_reason)
            self.delete_btn.configure(state="normal")
        else:
            self.form_header_lbl.configure(text=tr("colleague_mgmt.create_header", "➕ Neuen Mitarbeiter anlegen"))
            self.username_entry.delete(0, "end")
            self.name_entry.delete(0, "end")
            self.dept_combo.set(DEPARTMENTS[0])
            self.ext_entry.delete(0, "end")
            self.email_entry.delete(0, "end")
            self.mobile_entry.delete(0, "end")
            self.notes_entry.delete(0, "end")
            self.is_absent_var.set(False)
            self.absence_reason_entry.delete(0, "end")
            self.delete_btn.configure(state="disabled")

        self.filter_and_render_list()

    def on_click_new_colleague(self):
        self.select_colleague(None)

    def on_click_save(self):
        username = self.username_entry.get().strip()
        name = self.name_entry.get().strip()
        department = self.dept_combo.get()
        extension = self.ext_entry.get().strip()
        email = self.email_entry.get().strip()
        mobile = self.mobile_entry.get().strip()
        notes = self.notes_entry.get().strip()
        is_absent = self.is_absent_var.get()
        absence_reason = self.absence_reason_entry.get().strip()

        col = Colleague(
            username=username,
            name=name,
            department=department,
            extension=extension,
            email=email,
            mobile=mobile,
            notes=notes,
            is_absent=is_absent,
            absence_reason=absence_reason,
        )

        errs = col.validate()
        if errs:
            self.err_lbl.configure(text=f"⚠ {errs[0]}")
            return

        # Update existing or add new
        existing_idx = next((i for i, c in enumerate(self.colleagues) if c.username.lower() == username.lower()), -1)
        if existing_idx >= 0:
            self.colleagues[existing_idx] = col
        else:
            self.colleagues.append(col)

        self.storage_service.save_colleagues(self.colleagues)
        self.select_colleague(col)

        if self.on_colleagues_updated:
            self.on_colleagues_updated()

    def confirm_click_delete(self):
        """Asks before removing the selected colleague from the list."""
        from services.i18n_service import tr
        from ui.dialogs.confirm_dialog import ask_confirmation
        if not self.selected_colleague:
            return
        display_name = self.selected_colleague.name or self.selected_colleague.username
        if ask_confirmation(
            self,
            tr("confirm.delete_colleague", "„{name}“ wirklich aus der Mitarbeiterliste entfernen?", name=display_name),
            title=tr("confirm.delete_title", "Löschen bestätigen"),
            confirm_text=tr("confirm.yes_delete", "🗑 Ja, löschen"),
        ):
            self.on_click_delete()

    def on_click_delete(self):
        if not self.selected_colleague:
            return
        username_to_del = self.selected_colleague.username
        self.colleagues = [c for c in self.colleagues if c.username != username_to_del]
        self.storage_service.save_colleagues(self.colleagues)
        self.select_colleague(None)

        if self.on_colleagues_updated:
            self.on_colleagues_updated()
