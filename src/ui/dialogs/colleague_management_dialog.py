import customtkinter as ctk

from ui.dialogs.base_dialog import BaseDialog
from collections.abc import Callable
from models.profile import Colleague
from services.storage_service import StorageService
from constants import (
    BTN_WIDTH_ACTION,
    BTN_WIDTH_MD,
    BTN_WIDTH_NEW_COLLEAGUE,
    COLLEAGUE_LIST_PANEL_WIDTH,
    COLLEAGUE_NOTES_SNIPPET_MAX_CHARS,
    COLOR_COLLEAGUE_ACTIVE,
    COLOR_COLLEAGUE_INACTIVE,
    COLOR_DANGER,
    COLOR_DANGER_ALT,
    COLOR_DARKGREEN_HOVER,
    COLOR_DARKRED_HOVER,
    COLOR_MUTED_LABEL,
    COLOR_SUBTITLE_MUTED,
    COLOR_SUCCESS,
    COLOR_TEXT_PRIMARY,
    CORNER_RADIUS_NONE,
    CURSOR_HAND,
    DEBOUNCE_KEY_COLLEAGUE_SEARCH,
    DEFAULT_DEPARTMENTS,
    DIALOG_DIMENSIONS,
    DIALOG_MIN_SIZE_COLLEAGUE_MGMT,
    DIALOG_TITLES,
    FONT_SIZE_BODY,
    FONT_SIZE_HEADER_BAR,
    FONT_SIZE_SUBTITLE,
    FONT_SIZE_XS,
    FONT_WEIGHT_BOLD,
    HEIGHT_TOP_BAR_SM,
    ICON_WARNING,
    PAD_2XL,
    PAD_LG,
    PAD_MD,
    PAD_NONE,
    PAD_SM,
    PAD_TINY,
    PAD_XL,
    PAD_XS,
    SEARCH_DEBOUNCE_MS,
    get_localized_departments,
)
from utils.ui_utils import create_highlighted_label, bind_mouse_wheel_to_canvas, debounce

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
            min_size=DIALOG_MIN_SIZE_COLLEAGUE_MGMT,
            title_factory=lambda: DIALOG_TITLES["colleague_mgmt"],
        )

        self.colleagues: list[Colleague] = []
        self.filtered_colleagues: list[Colleague] = []
        self.selected_colleague: Colleague | None = None

        self.create_widgets()
        self.load_colleagues()
        # Closing now asks before throwing away an edited colleague. The search
        # box only narrows the list, so it must not count as input.
        self.exclude_from_unsaved_guard(getattr(self, "search_entry", None))
        self.enable_unsaved_guard()

    def create_widgets(self):
        from services.i18n_service import tr

        departments = get_localized_departments()

        # Header Bar
        top_bar = ctk.CTkFrame(self, height=HEIGHT_TOP_BAR_SM, corner_radius=CORNER_RADIUS_NONE)
        top_bar.pack(fill="x", side="top", padx=PAD_MD + PAD_XS, pady=(PAD_MD + PAD_XS, PAD_SM + 1))

        self.register_i18n(ctk.CTkLabel(
            top_bar,
            text=tr("colleague_mgmt.header", "👥 Mitarbeiter- & Kollegeneinträge"),
            font=ctk.CTkFont(size=FONT_SIZE_HEADER_BAR, weight=FONT_WEIGHT_BOLD),
        ), "colleague_mgmt.header", "👥 Mitarbeiter- & Kollegeneinträge").pack(side="left", padx=PAD_MD + PAD_XS)

        new_btn = self.register_i18n(ctk.CTkButton(
            top_bar,
            text=tr("colleague_mgmt.new_colleague_btn", "+ Neuen Mitarbeiter anlegen"),
            command=self.on_click_new_colleague,
            fg_color=COLOR_SUCCESS,
            width=BTN_WIDTH_NEW_COLLEAGUE,
        ), "colleague_mgmt.new_colleague_btn", "+ Neuen Mitarbeiter anlegen")
        new_btn.pack(side="right", padx=PAD_MD + PAD_XS)

        # Body Frame
        body_frame = ctk.CTkFrame(self, fg_color="transparent")
        body_frame.pack(fill="both", expand=True, padx=PAD_MD + PAD_XS, pady=(PAD_SM + 1, PAD_MD + PAD_XS))

        # Left list panel
        left_frame = ctk.CTkFrame(body_frame, width=COLLEAGUE_LIST_PANEL_WIDTH)
        left_frame.pack(side="left", fill="y", padx=(PAD_NONE, PAD_SM + 1), pady=PAD_NONE)
        left_frame.pack_propagate(False)

        self.search_entry = self.register_i18n(ctk.CTkEntry(
            left_frame, placeholder_text=tr("colleague_mgmt.search_placeholder", "🔍 Name, Kürzel, Abteilung...")
        ), "colleague_mgmt.search_placeholder", "🔍 Name, Kürzel, Abteilung...", attr="placeholder_text")
        self.search_entry.pack(fill="x", padx=PAD_MD + PAD_XS, pady=(PAD_MD + PAD_XS, PAD_SM + 1))
        self.search_entry.bind("<KeyRelease>", self._on_search_keyrelease)

        self.list_scroll = ctk.CTkScrollableFrame(left_frame, fg_color="transparent")
        self.list_scroll.pack(fill="both", expand=True, padx=PAD_SM + 1, pady=PAD_SM + 1)

        # Right editor panel
        right_frame = ctk.CTkFrame(body_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=(PAD_SM + 1, PAD_NONE), pady=PAD_NONE)

        self.form_header_lbl = self.register_i18n(ctk.CTkLabel(
            right_frame,
            text=tr("colleague_mgmt.details_header", "Mitarbeiterdetails"),
            font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight=FONT_WEIGHT_BOLD),
            anchor="w",
        ), "colleague_mgmt.details_header", "Mitarbeiterdetails")
        self.form_header_lbl.pack(fill="x", padx=PAD_XL - 1, pady=(PAD_LG, PAD_MD))

        form_scroll = ctk.CTkScrollableFrame(right_frame, fg_color="transparent")
        form_scroll.pack(fill="both", expand=True, padx=PAD_MD + PAD_XS, pady=(PAD_NONE, PAD_MD + PAD_XS))

        # Fields
        self.register_i18n(ctk.CTkLabel(form_scroll, text=tr("colleague_mgmt.username", "Kürzel / Username *:")), "colleague_mgmt.username", "Kürzel / Username *:").pack(anchor="w", pady=(PAD_SM, PAD_XS))
        self.username_entry = self.register_i18n(ctk.CTkEntry(form_scroll, placeholder_text=tr("colleague_mgmt.username_placeholder", "z. B. mmueller")), "colleague_mgmt.username_placeholder", "z. B. mmueller", attr="placeholder_text")
        self.username_entry.pack(fill="x", pady=(PAD_NONE, PAD_MD + PAD_XS))

        self.register_i18n(ctk.CTkLabel(form_scroll, text=tr("colleague_mgmt.name", "Name / Anzeigename *:")), "colleague_mgmt.name", "Name / Anzeigename *:").pack(anchor="w", pady=(PAD_SM, PAD_XS))
        self.name_entry = self.register_i18n(ctk.CTkEntry(form_scroll, placeholder_text=tr("colleague_mgmt.name_placeholder", "z. B. Max Müller")), "colleague_mgmt.name_placeholder", "z. B. Max Müller", attr="placeholder_text")
        self.name_entry.pack(fill="x", pady=(PAD_NONE, PAD_MD + PAD_XS))

        self.register_i18n(ctk.CTkLabel(form_scroll, text=tr("colleague_mgmt.department", "Abteilung / Department:")), "colleague_mgmt.department", "Abteilung / Department:").pack(anchor="w", pady=(PAD_SM, PAD_XS))
        self.dept_combo = ctk.CTkOptionMenu(form_scroll, values=departments)
        self.dept_combo.set(departments[0])
        self.dept_combo.pack(fill="x", pady=(PAD_NONE, PAD_MD + PAD_XS))

        self.register_i18n(ctk.CTkLabel(form_scroll, text=tr("colleague_mgmt.phone", "Durchwahl / Telefon:")), "colleague_mgmt.phone", "Durchwahl / Telefon:").pack(anchor="w", pady=(PAD_SM, PAD_XS))
        self.ext_entry = self.register_i18n(ctk.CTkEntry(form_scroll, placeholder_text=tr("colleague_mgmt.phone_placeholder", "z. B. 4012")), "colleague_mgmt.phone_placeholder", "z. B. 4012", attr="placeholder_text")
        self.ext_entry.pack(fill="x", pady=(PAD_NONE, PAD_MD + PAD_XS))

        self.register_i18n(ctk.CTkLabel(form_scroll, text=tr("colleague_mgmt.email", "E-Mail-Adresse:")), "colleague_mgmt.email", "E-Mail-Adresse:").pack(anchor="w", pady=(PAD_SM, PAD_XS))
        self.email_entry = self.register_i18n(ctk.CTkEntry(form_scroll, placeholder_text=tr("colleague_mgmt.email_placeholder", "z. B. m.mueller@praxis.de")), "colleague_mgmt.email_placeholder", "z. B. m.mueller@praxis.de", attr="placeholder_text")
        self.email_entry.pack(fill="x", pady=(PAD_NONE, PAD_MD + PAD_XS))

        self.register_i18n(ctk.CTkLabel(form_scroll, text=tr("colleague_mgmt.mobile", "Mobiltelefon:")), "colleague_mgmt.mobile", "Mobiltelefon:").pack(anchor="w", pady=(PAD_SM, PAD_XS))
        self.mobile_entry = self.register_i18n(ctk.CTkEntry(form_scroll, placeholder_text=tr("colleague_mgmt.mobile_placeholder", "z. B. 0170 1234567")), "colleague_mgmt.mobile_placeholder", "z. B. 0170 1234567", attr="placeholder_text")
        self.mobile_entry.pack(fill="x", pady=(PAD_NONE, PAD_MD + PAD_XS))

        self.register_i18n(ctk.CTkLabel(form_scroll, text=tr("colleague_mgmt.notes", "Aufgabengebiet / Notizen:")), "colleague_mgmt.notes", "Aufgabengebiet / Notizen:").pack(anchor="w", pady=(PAD_SM, PAD_XS))
        self.notes_entry = self.register_i18n(ctk.CTkEntry(form_scroll, placeholder_text=tr("colleague_mgmt.notes_placeholder", "z. B. Zuständig für PVS-Schnittstellen...")), "colleague_mgmt.notes_placeholder", "z. B. Zuständig für PVS-Schnittstellen...", attr="placeholder_text")
        self.notes_entry.pack(fill="x", pady=(PAD_NONE, PAD_MD + PAD_XS))

        # Absence / Vacation settings
        self.is_absent_var = ctk.BooleanVar(value=False)
        self.chk_absent = self.register_i18n(ctk.CTkCheckBox(
            form_scroll, text=tr("colleague_mgmt.absent_chk", "⚠ Kollege ist aktuell abwesend (Urlaub / Krankheit)"), variable=self.is_absent_var
        ), "colleague_mgmt.absent_chk", "⚠ Kollege ist aktuell abwesend (Urlaub / Krankheit)")
        self.chk_absent.pack(anchor="w", pady=(PAD_SM + 1, PAD_SM + 1))

        self.absence_reason_entry = self.register_i18n(ctk.CTkEntry(form_scroll, placeholder_text=tr("colleague_mgmt.absence_reason_placeholder", "Abwesenheitsgrund (z. B. Urlaub bis 30.08.)...")), "colleague_mgmt.absence_reason_placeholder", "Abwesenheitsgrund (z. B. Urlaub bis 30.08.)...", attr="placeholder_text")
        self.absence_reason_entry.pack(fill="x", pady=(PAD_NONE, PAD_XL - 1))

        self.err_lbl = ctk.CTkLabel(form_scroll, text="", text_color=COLOR_DANGER, anchor="w")
        self.err_lbl.pack(fill="x", pady=(PAD_NONE, PAD_SM + 1))

        # Bottom Action Bar
        action_bar = ctk.CTkFrame(right_frame, height=HEIGHT_TOP_BAR_SM, fg_color="transparent")
        action_bar.pack(fill="x", side="bottom", padx=PAD_XL - 1, pady=PAD_MD + PAD_XS)

        self.delete_btn = self.register_i18n(ctk.CTkButton(
            action_bar,
            text=tr("common.delete", "🗑 Löschen"),
            command=self.confirm_click_delete,
            fg_color=COLOR_DANGER_ALT,
            hover_color=COLOR_DARKRED_HOVER,
            width=BTN_WIDTH_MD,
            state="disabled",
        ), "common.delete", "🗑 Löschen")
        self.delete_btn.pack(side="left")

        self.save_btn = self.register_i18n(ctk.CTkButton(
            action_bar,
            text=tr("cockpit.save", "💾 Speichern"),
            command=self.on_click_save,
            fg_color=COLOR_SUCCESS,
            hover_color=COLOR_DARKGREEN_HOVER,
            width=BTN_WIDTH_ACTION,
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
            self.register_i18n(ctk.CTkLabel(self.list_scroll, text=tr("colleague_mgmt.no_entries", "Keine Einträge gefunden."), text_color=COLOR_MUTED_LABEL), "colleague_mgmt.no_entries", "Keine Einträge gefunden.").pack(pady=PAD_2XL)
            return

        raw_query = self.search_entry.get().strip() if hasattr(self, "search_entry") else ""

        for col in self.filtered_colleagues:
            is_sel = self.selected_colleague and self.selected_colleague.username == col.username
            bg = COLOR_COLLEAGUE_ACTIVE if is_sel else COLOR_COLLEAGUE_INACTIVE

            card = ctk.CTkFrame(self.list_scroll, fg_color=bg, cursor=CURSOR_HAND)
            card.pack(fill="x", pady=PAD_XS + 1, padx=PAD_XS)
            card.bind("<Button-1>", lambda e, c=col: self.select_colleague(c))

            name_text = f"{col.name} ({col.username})"
            if raw_query and raw_query.lower() in name_text.lower():
                lbl_name = create_highlighted_label(
                    card,
                    text=name_text,
                    query=raw_query,
                    font=ctk.CTkFont(weight=FONT_WEIGHT_BOLD, size=FONT_SIZE_BODY),
                    text_color=COLOR_TEXT_PRIMARY,
                    bg_color=bg,
                    wrap="none",
                    on_click=lambda e, c=col: self.select_colleague(c),
                    scroll_frame=self.list_scroll,
                )
            else:
                lbl_name = ctk.CTkLabel(card, text=name_text, font=ctk.CTkFont(weight=FONT_WEIGHT_BOLD, size=FONT_SIZE_BODY), anchor="w")
                lbl_name.bind("<Button-1>", lambda e, c=col: self.select_colleague(c))
            lbl_name.pack(fill="x", padx=PAD_MD, pady=(PAD_SM + 1, PAD_TINY))

            sub_txt = f"🏢 {col.department}"
            if col.extension:
                sub_txt += f" | 📞 {col.extension}"
            if raw_query and raw_query.lower() in sub_txt.lower():
                lbl_sub = create_highlighted_label(
                    card,
                    text=sub_txt,
                    query=raw_query,
                    font=ctk.CTkFont(size=FONT_SIZE_XS),
                    text_color=COLOR_MUTED_LABEL,
                    bg_color=bg,
                    wrap="none",
                    on_click=lambda e, c=col: self.select_colleague(c),
                    scroll_frame=self.list_scroll,
                )
            else:
                lbl_sub = ctk.CTkLabel(card, text=sub_txt, font=ctk.CTkFont(size=FONT_SIZE_XS), text_color=COLOR_MUTED_LABEL, anchor="w")
                lbl_sub.bind("<Button-1>", lambda e, c=col: self.select_colleague(c))
            lbl_sub.pack(fill="x", padx=PAD_MD, pady=(PAD_NONE, PAD_SM + 1))

            if raw_query and raw_query.lower() in col.notes.lower() and raw_query.lower() not in name_text.lower() and raw_query.lower() not in sub_txt.lower():
                matched_words = [w.strip(",;:()[]{}<>\"'\t\r\n") for w in col.notes.split() if raw_query.lower() in w.lower()]
                seen_words: set[str] = set()
                uniq_words: list[str] = []
                for w in matched_words:
                    if w.lower() not in seen_words:
                        seen_words.add(w.lower())
                        uniq_words.append(w)
                if uniq_words:
                    # Truncate on word boundaries: a blind [:45] slice could cut
                    # through the matched substring, leaving a "match" line with
                    # nothing highlighted in it.
                    shown: list[str] = []
                    used = 0
                    for w in uniq_words[:3]:
                        add = len(w) + (2 if shown else 0)
                        if shown and used + add > COLLEAGUE_NOTES_SNIPPET_MAX_CHARS:
                            break
                        shown.append(w)
                        used += add
                    if not shown:
                        shown = [uniq_words[0][:COLLEAGUE_NOTES_SNIPPET_MAX_CHARS]]
                    notes_summary = ", ".join(shown)
                    if len(shown) < len(uniq_words):
                        notes_summary += "..."
                    notes_lbl = create_highlighted_label(
                        card,
                        text=f"📝 {notes_summary}",
                        query=raw_query,
                        font=ctk.CTkFont(size=FONT_SIZE_XS),
                        text_color=COLOR_SUBTITLE_MUTED,
                        bg_color=bg,
                        wrap="word",
                        on_click=lambda e, c=col: self.select_colleague(c),
                        scroll_frame=self.list_scroll,
                    )
                    notes_lbl.pack(fill="x", padx=PAD_MD, pady=(PAD_NONE, PAD_SM))

            bind_mouse_wheel_to_canvas(card, self.list_scroll)

    def _on_search_keyrelease(self, event=None):
        """Wartet die Tipppause ab, statt bei jedem Buchstaben neu zu filtern."""
        debounce(self, DEBOUNCE_KEY_COLLEAGUE_SEARCH, SEARCH_DEBOUNCE_MS, self.on_search_changed)

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
        # The form now mirrors the selected colleague (or is empty for a new
        # one), so this is the clean baseline. Saving ends here too, which makes
        # the post-save state clean as well.
        self.mark_clean()

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
            self.err_lbl.configure(text=f"{ICON_WARNING} {errs[0]}")
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
