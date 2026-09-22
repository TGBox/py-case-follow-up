import customtkinter as ctk

from ui.dialogs.base_dialog import BaseDialog
from datetime import datetime, timedelta
from collections.abc import Callable
from models.case import Case, CaseCustomer, Classification, WorkflowStatus, TimelineEntry
from models.customer import Customer, Contact
from services.customer_service import CustomerService
from services.i18n_service import tr
from models.schema import QuestionSchema
from enums import BoardColumn, Actor, Channel
from utils.datetime_utils import now_iso, parse_iso, get_local_now, format_german_datetime
from constants import (
    BTN_WIDTH_ACTION,
    BTN_WIDTH_CLOSE,
    BTN_WIDTH_MD,
    CASE_ID_PREFIX,
    COLOR_BTN_CANCEL,
    COLOR_DANGER,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_SUCCESS,
    COLOR_TAG_PILL_ADD_BG,
    COLOR_TAG_PILL_ADD_HOVER,
    COLOR_TAG_PILL_DEFAULT,
    COLOR_TAG_PILL_DEFAULT_HOVER,
    COLOR_TAG_PILL_DEFAULT_TEXT,
    COLOR_TAG_PILL_SELECTED,
    COLOR_TAG_PILL_SELECTED_HOVER,
    COMBO_DEFAULT_WIDTH,
    COMBO_WIDTH_NEW_CASE_CHANNEL,
    DEFAULT_PRACTICE_DISPLAY,
    DEFAULT_PRACTICE_ID,
    DEFAULT_PRACTICE_NAME,
    DEFAULT_TAGS,
    DIALOG_DIMENSIONS,
    DIALOG_MIN_SIZE_NEW_CASE,
    DIALOG_TITLES,
    FONT_SIZE_BODY,
    FONT_SIZE_HEADER_BAR,
    FONT_SIZE_SM,
    FONT_SIZE_TITLE_SM,
    FONT_WEIGHT_BOLD,
    INITIAL_STATUS_CHANGE_NOTE,
    INTERNAL_ATTACHMENT_SUFFIX,
    INTERNAL_CUSTOMER_ID,
    INTERNAL_PRACTICE_NAME,
    PAD_10,
    PAD_15,
    PAD_2XL,
    PAD_CONTAINER,
    PAD_GAP,
    PAD_LG,
    PAD_MD,
    PAD_NONE,
    PAD_SM,
    PAD_TINY,
    PAD_XS,
    TAG_PILL_COLS,
    TAG_PILL_HEIGHT,
    TAG_PILL_PAD_X,
    TAG_PILL_PAD_Y,
    TAG_PILL_RADIUS,
    TEXTBOX_HEIGHT_INITIAL_NOTE,
    TIMESTAMP_FORMAT_CASE_ID,
)


class QuickAddCustomerDialog(BaseDialog):
    def __init__(self, parent, on_customer_created: Callable[[Customer], None]):
        super().__init__(parent)
        w, h = DIALOG_DIMENSIONS["quick_customer"]
        self.setup_window(
            parent,
            DIALOG_TITLES["quick_customer"],
            (w, h),
            resizable=False,
            title_factory=lambda: DIALOG_TITLES["quick_customer"],
        )

        self.on_customer_created = on_customer_created

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=PAD_2XL, pady=PAD_2XL)

        self.register_i18n(
            ctk.CTkLabel(
                main_frame,
                text=tr("quick_customer.header", "Neue Praxis anlegen"),
                font=ctk.CTkFont(size=FONT_SIZE_TITLE_SM, weight=FONT_WEIGHT_BOLD),
            ),
            "quick_customer.header",
            "Neue Praxis anlegen",
        ).pack(anchor="w", pady=(PAD_NONE, PAD_10))

        self.register_i18n(
            ctk.CTkLabel(main_frame, text=tr("quick_customer.practice_name", "Praxisname *:")),
            "quick_customer.practice_name",
            "Praxisname *:",
        ).pack(anchor="w", pady=(PAD_XS, PAD_NONE))
        self.name_entry = self.register_i18n(
            ctk.CTkEntry(main_frame, placeholder_text=tr("quick_customer.practice_name_placeholder", "z.B. Praxis Dr. Weber")),
            "quick_customer.practice_name_placeholder",
            "z.B. Praxis Dr. Weber",
            attr="placeholder_text",
        )
        self.name_entry.pack(fill="x", pady=(PAD_NONE, PAD_MD))

        self.register_i18n(
            ctk.CTkLabel(main_frame, text=tr("quick_customer.contact_person", "Ansprechpartner:")),
            "quick_customer.contact_person",
            "Ansprechpartner:",
        ).pack(anchor="w", pady=(PAD_XS, PAD_NONE))
        self.contact_entry = self.register_i18n(
            ctk.CTkEntry(main_frame, placeholder_text=tr("quick_customer.contact_placeholder", "z.B. Dr. Hans Weber")),
            "quick_customer.contact_placeholder",
            "z.B. Dr. Hans Weber",
            attr="placeholder_text",
        )
        self.contact_entry.pack(fill="x", pady=(PAD_NONE, PAD_MD))

        self.register_i18n(
            ctk.CTkLabel(main_frame, text=tr("quick_customer.phone", "Telefon:")),
            "quick_customer.phone",
            "Telefon:",
        ).pack(anchor="w", pady=(PAD_XS, PAD_NONE))
        self.phone_entry = self.register_i18n(
            ctk.CTkEntry(main_frame, placeholder_text=tr("quick_customer.phone_placeholder", "030 / 123456")),
            "quick_customer.phone_placeholder",
            "030 / 123456",
            attr="placeholder_text",
        )
        self.phone_entry.pack(fill="x", pady=(PAD_NONE, PAD_MD))

        self.vip_var = ctk.BooleanVar(value=False)
        self.register_i18n(
            ctk.CTkCheckBox(main_frame, text=tr("quick_customer.is_vip", "⭐ VIP-Praxis"), variable=self.vip_var),
            "quick_customer.is_vip",
            "⭐ VIP-Praxis",
        ).pack(anchor="w", pady=PAD_CONTAINER)

        self.err_lbl = ctk.CTkLabel(main_frame, text="", text_color=COLOR_DANGER)
        self.err_lbl.pack(anchor="w", pady=PAD_XS)

        btn_row = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_row.pack(fill="x", pady=(PAD_10, PAD_NONE))

        self.register_i18n(
            ctk.CTkButton(btn_row, text=tr("common.cancel", "Abbrechen"), fg_color=COLOR_BTN_CANCEL, command=self.destroy, width=BTN_WIDTH_MD),
            "common.cancel",
            "Abbrechen",
        ).pack(side="left")
        self.register_i18n(
            ctk.CTkButton(btn_row, text=tr("ui_buttons.create", "Erstellen"), fg_color=COLOR_SUCCESS, command=self.on_save, width=BTN_WIDTH_CLOSE),
            "ui_buttons.create",
            "Erstellen",
        ).pack(side="right")
        self.set_default_action(self.on_save)

    def on_save(self):
        name = self.name_entry.get().strip()
        if not name:
            self.err_lbl.configure(text=tr("quick_customer.err_name", "Bitte Praxisnamen eingeben."))
            return

        contact_name = self.contact_entry.get().strip()
        phone = self.phone_entry.get().strip()

        cust_id = f"CUST-{int(datetime.now().timestamp()) % 100000}"
        contacts = [Contact(name=contact_name, phone=phone)] if (contact_name or phone) else []

        new_cust = Customer(
            customer_id=cust_id,
            practice_name=name,
            contacts=contacts,
            is_vip=self.vip_var.get(),
        )
        self.on_customer_created(new_cust)
        self.destroy()


class NewCaseDialog(BaseDialog):
    def __init__(
        self,
        parent,
        customers: list[Customer],
        schemas: list[QuestionSchema],
        created_by: str,
        on_case_created: Callable[[Case], None],
        on_customer_added: Callable[[Customer], None] | None = None,
        available_tags: list[str] | None = None,
        on_tag_added: Callable[[str], None] | None = None,
    ):
        super().__init__(parent)
        w, h = DIALOG_DIMENSIONS["new_case"]
        self.setup_window(
            parent,
            DIALOG_TITLES["new_case"],
            (w, h),
            min_size=DIALOG_MIN_SIZE_NEW_CASE,
            title_factory=lambda: DIALOG_TITLES["new_case"],
        )

        self.customers = list(customers)
        self._customer_by_display: dict[str, Customer] = {}
        self.schemas = schemas
        self.created_by = created_by
        self.on_case_created = on_case_created
        self.on_customer_added = on_customer_added
        self.available_tags = list(available_tags) if available_tags else list(DEFAULT_TAGS)
        self.on_tag_added = on_tag_added

        self.selected_tags_vars: dict[str, ctk.BooleanVar] = {}
        self.created_case: Case | None = None

        self.create_widgets()
        # Closing now asks before throwing away a half-filled case.
        self.enable_unsaved_guard()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=PAD_15, pady=PAD_LG)

        # 1. Pinned Bottom Action Bar (ALWAYS 100% VISIBLE AT BOTTOM)
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", pady=(PAD_MD, PAD_NONE))

        cancel_btn = self.register_i18n(
            ctk.CTkButton(btn_frame, text=tr("common.cancel", "Abbrechen"), fg_color=COLOR_BTN_CANCEL, command=self.destroy, width=BTN_WIDTH_CLOSE),
            "common.cancel",
            "Abbrechen",
        )
        cancel_btn.pack(side="left")

        save_btn = self.register_i18n(
            ctk.CTkButton(
                btn_frame,
                text=tr("new_case_dialog.create_btn", "Fall anlegen"),
                command=self.on_save,
                width=BTN_WIDTH_ACTION,
                fg_color=COLOR_PRIMARY,
                hover_color=COLOR_PRIMARY_HOVER,
            ),
            "new_case_dialog.create_btn",
            "Fall anlegen",
        )
        save_btn.pack(side="right")

        # Error label pinned right above bottom buttons
        self.error_label = ctk.CTkLabel(main_frame, text="", text_color=COLOR_DANGER)
        self.error_label.pack(side="bottom", anchor="w", pady=(PAD_NONE, PAD_XS))

        # 2. Scrollable Form Inputs Area (Fills remaining height)
        form_scroll = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        form_scroll.pack(side="top", fill="both", expand=True)
        from utils.ui_utils import enable_auto_hiding_scrollbar
        enable_auto_hiding_scrollbar(form_scroll)

        # Header
        title_label = self.register_i18n(
            ctk.CTkLabel(
                form_scroll,
                text=tr("new_case_dialog.header", "Neuen Support-Fall erfassen"),
                font=ctk.CTkFont(size=FONT_SIZE_HEADER_BAR, weight=FONT_WEIGHT_BOLD),
            ),
            "new_case_dialog.header",
            "Neuen Support-Fall erfassen",
        )
        title_label.pack(anchor="w", pady=(PAD_NONE, PAD_MD))

        # Internal Task Checkbox
        self.is_internal_var = ctk.BooleanVar(value=False)
        self.chk_internal = self.register_i18n(
            ctk.CTkCheckBox(
                form_scroll,
                text=tr("new_case_dialog.is_internal", "🏢 Interner Vorgang (ohne Kundenelement)"),
                variable=self.is_internal_var,
                command=self.on_toggle_internal,
                font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
            ),
            "new_case_dialog.is_internal",
            "🏢 Interner Vorgang (ohne Kundenelement)",
        )
        self.chk_internal.pack(anchor="w", pady=(PAD_NONE, PAD_MD))

        # Customer selection row
        self.register_i18n(
            ctk.CTkLabel(
                form_scroll,
                text=tr("new_case_dialog.customer", "Kunde / Praxis:"),
                font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
            ),
            "new_case_dialog.customer",
            "Kunde / Praxis:",
        ).pack(anchor="w", pady=(PAD_SM, PAD_TINY))

        cust_row = ctk.CTkFrame(form_scroll, fg_color="transparent")
        cust_row.pack(fill="x", pady=(PAD_NONE, PAD_GAP))

        from ui.widgets.searchable_combobox import SearchableCombobox
        initial_cust_names = [f"{c.practice_name} ({c.customer_id})" for c in self.customers] if self.customers else [tr("new_case_dialog.no_customers", "Keine Kunden")]
        self.customer_combo = SearchableCombobox(
            cust_row,
            values=initial_cust_names,
            width=COMBO_DEFAULT_WIDTH,
            summary_provider=self._customer_match_summary,
        )
        self.customer_combo.pack(side="left", padx=(PAD_NONE, PAD_CONTAINER), fill="x", expand=True)

        self.add_cust_btn = self.register_i18n(
            ctk.CTkButton(
                cust_row,
                text=tr("new_case_dialog.add_practice_btn", "+ Neue Praxis"),
                command=self.open_quick_add_customer,
                fg_color=COLOR_SUCCESS,
                width=BTN_WIDTH_CLOSE,
            ),
            "new_case_dialog.add_practice_btn",
            "+ Neue Praxis",
        )
        self.add_cust_btn.pack(side="right")

        self.refresh_customer_combo()

        # Case Title
        self.register_i18n(
            ctk.CTkLabel(
                form_scroll,
                text=tr("new_case_dialog.title_label", "Titel / Kurzbeschreibung:"),
                font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
            ),
            "new_case_dialog.title_label",
            "Titel / Kurzbeschreibung:",
        ).pack(anchor="w", pady=(PAD_SM, PAD_TINY))
        self.title_entry = self.register_i18n(
            ctk.CTkEntry(
                form_scroll,
                placeholder_text=tr("new_case_dialog.title_placeholder", "z. B. Zuzahlungsdatei lässt sich nicht erzeugen"),
            ),
            "new_case_dialog.title_placeholder",
            "z. B. Zuzahlungsdatei lässt sich nicht erzeugen",
            attr="placeholder_text",
        )
        self.title_entry.pack(fill="x", pady=(PAD_NONE, PAD_GAP))

        # After picking a practice the cursor jumps straight into the title field
        self.customer_combo.set_next_focus_widget(self.title_entry)

        # Creation Date (defaulting to current time)
        self.register_i18n(
            ctk.CTkLabel(
                form_scroll,
                text=tr("new_case_dialog.created_at", "Erstellungsdatum / Vorgangsbeginn (TT.MM.JJJJ HH:MM):"),
                font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
            ),
            "new_case_dialog.created_at",
            "Erstellungsdatum / Vorgangsbeginn (TT.MM.JJJJ HH:MM):",
        ).pack(anchor="w", pady=(PAD_SM, PAD_TINY))
        from ui.widgets.date_picker import DatePickerWidget
        self.created_at_picker = self.register_i18n(
            DatePickerWidget(
                form_scroll,
                placeholder_text=tr("date_picker.placeholder_datetime_example", "z. B. 25.08.2026 09:30"),
                include_time=True,
                initial_value=format_german_datetime(now_iso()),
                width=COMBO_DEFAULT_WIDTH,
            ),
            "date_picker.placeholder_datetime_example",
            "z. B. 25.08.2026 09:30",
            attr="placeholder_text",
        )
        self.created_at_picker.pack(fill="x", pady=(PAD_NONE, PAD_GAP))

        # Schema selection
        self.register_i18n(
            ctk.CTkLabel(
                form_scroll,
                text=tr("new_case_dialog.schema", "Formular-Schema:"),
                font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
            ),
            "new_case_dialog.schema",
            "Formular-Schema:",
        ).pack(anchor="w", pady=(PAD_SM, PAD_TINY))
        from services.schema_i18n import schema_display_name
        schema_names = [f"{schema_display_name(s)} [{s.schema_id}]" for s in self.schemas]
        self.schema_combo = ctk.CTkOptionMenu(form_scroll, values=schema_names if schema_names else ["Standard"])
        quick_opt = next((name for name in schema_names if "schema_quick" in name or "Schnellerfassung" in name), None)
        if quick_opt:
            self.schema_combo.set(quick_opt)
        self.schema_combo.pack(fill="x", pady=(PAD_NONE, PAD_GAP))

        # Tags Selection
        self.register_i18n(
            ctk.CTkLabel(
                form_scroll,
                text=tr("new_case_dialog.tags", "Tags / Stichworte zuweisen:"),
                font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
            ),
            "new_case_dialog.tags",
            "Tags / Stichworte zuweisen:",
        ).pack(anchor="w", pady=(PAD_SM, PAD_TINY))

        self.tags_frame = ctk.CTkFrame(form_scroll, fg_color="transparent")
        self.tags_frame.pack(fill="x", pady=(PAD_NONE, PAD_GAP))

        self.render_tags_checkboxes()

        # Callback deadline (optional)
        self.register_i18n(
            ctk.CTkLabel(
                form_scroll,
                text=tr("new_case_dialog.deadline", "Rückruf-Deadline (optional, TT.MM.JJJJ HH:MM):"),
                font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
            ),
            "new_case_dialog.deadline",
            "Rückruf-Deadline (optional, TT.MM.JJJJ HH:MM):",
        ).pack(anchor="w", pady=(PAD_SM, PAD_TINY))
        from ui.widgets.date_picker import DatePickerWidget
        self.deadline_picker = self.register_i18n(
            DatePickerWidget(
                form_scroll,
                placeholder_text=tr("date_picker.placeholder_deadline_example", "z. B. 23.08.2026 16:00"),
                include_time=True,
                width=COMBO_DEFAULT_WIDTH,
            ),
            "date_picker.placeholder_deadline_example",
            "z. B. 23.08.2026 16:00",
            attr="placeholder_text",
        )
        self.deadline_picker.pack(fill="x", pady=(PAD_NONE, PAD_GAP))

        # Initial Timeline Note & Channel Selection
        note_hdr_row = ctk.CTkFrame(form_scroll, fg_color="transparent")
        note_hdr_row.pack(fill="x", pady=(PAD_SM, PAD_TINY))

        self.register_i18n(
            ctk.CTkLabel(
                note_hdr_row,
                text=tr("new_case_dialog.initial_note", "Initiale Notiz / Eingangskanal:"),
                font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
            ),
            "new_case_dialog.initial_note",
            "Initiale Notiz / Eingangskanal:",
        ).pack(side="left")

        from enums import CHANNEL_DISPLAY, get_channel_display
        channel_names = [get_channel_display(c) for c in CHANNEL_DISPLAY]
        self.channel_combo = ctk.CTkOptionMenu(
            note_hdr_row,
            values=channel_names,
            width=COMBO_WIDTH_NEW_CASE_CHANNEL,
            font=ctk.CTkFont(size=FONT_SIZE_SM),
        )
        self.channel_combo.set(get_channel_display(Channel.PHONE_INBOUND.value))
        self.channel_combo.pack(side="right")

        self.note_textbox = ctk.CTkTextbox(form_scroll, height=TEXTBOX_HEIGHT_INITIAL_NOTE)
        self.note_textbox.pack(fill="x", pady=(PAD_NONE, PAD_GAP))

        from utils.ui_utils import enable_textbox_cursor_autoscroll
        enable_textbox_cursor_autoscroll(self.note_textbox)

    def render_tags_checkboxes(self):
        for w in self.tags_frame.winfo_children():
            w.destroy()

        grid_frame = ctk.CTkFrame(self.tags_frame, fg_color="transparent")
        grid_frame.pack(fill="x", padx=PAD_XS, pady=PAD_TINY)

        num_cols = TAG_PILL_COLS
        for col in range(num_cols):
            grid_frame.grid_columnconfigure(col, weight=1, uniform="new_case_tag_pills")

        for idx, tag in enumerate(self.available_tags):
            if tag not in self.selected_tags_vars:
                self.selected_tags_vars[tag] = ctk.BooleanVar(value=False)

            is_selected = self.selected_tags_vars[tag].get()
            btn_text = f"✓ {tag}" if is_selected else tag
            btn_fg = COLOR_TAG_PILL_SELECTED if is_selected else COLOR_TAG_PILL_DEFAULT
            btn_hover = COLOR_TAG_PILL_SELECTED_HOVER if is_selected else COLOR_TAG_PILL_DEFAULT_HOVER
            btn_text_color = "white" if is_selected else COLOR_TAG_PILL_DEFAULT_TEXT

            r = idx // num_cols
            c = idx % num_cols

            btn = ctk.CTkButton(
                grid_frame,
                text=btn_text,
                height=TAG_PILL_HEIGHT,
                corner_radius=TAG_PILL_RADIUS,
                font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD if is_selected else "normal"),
                fg_color=btn_fg,
                hover_color=btn_hover,
                text_color=btn_text_color,
                command=lambda t=tag: self.toggle_tag(t),
            )
            btn.grid(row=r, column=c, padx=TAG_PILL_PAD_X, pady=TAG_PILL_PAD_Y, sticky="ew")

        # Place the + Tag button in the next slot
        next_idx = len(self.available_tags)
        r = next_idx // num_cols
        c = next_idx % num_cols

        add_tag_btn = self.register_i18n(
            ctk.CTkButton(
                grid_frame,
                text=tr("new_case.add_tag", "+ Tag"),
                height=TAG_PILL_HEIGHT,
                corner_radius=TAG_PILL_RADIUS,
                font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD),
                fg_color=COLOR_TAG_PILL_ADD_BG,
                hover_color=COLOR_TAG_PILL_ADD_HOVER,
                command=self.open_quick_add_tag,
            ),
            "new_case.add_tag",
            "+ Tag",
        )
        add_tag_btn.grid(row=r, column=c, padx=TAG_PILL_PAD_X, pady=TAG_PILL_PAD_Y, sticky="ew")

    def toggle_tag(self, tag_name: str):
        if tag_name in self.selected_tags_vars:
            curr = self.selected_tags_vars[tag_name].get()
            self.selected_tags_vars[tag_name].set(not curr)
            self.render_tags_checkboxes()

    def open_quick_add_tag(self):
        dialog = self.register_i18n(
            ctk.CTkInputDialog(
                text=tr("new_case.tag_input_prompt", "Geben Sie den Namen des neuen Tags ein:"),
                title=tr("new_case.tag_input_title", "Neuen Tag hinzufügen"),
            ),
            "new_case.tag_input_prompt",
            "Geben Sie den Namen des neuen Tags ein:",
        )
        new_tag = dialog.get_input()
        if new_tag and new_tag.strip():
            tag_name = new_tag.strip()
            if tag_name not in self.available_tags:
                self.available_tags.append(tag_name)
                self.selected_tags_vars[tag_name] = ctk.BooleanVar(value=True)
                if self.on_tag_added:
                    self.on_tag_added(tag_name)
                self.render_tags_checkboxes()

    @staticmethod
    def customer_display_name(cust: Customer) -> str:
        return f"{cust.practice_name} ({cust.customer_id})"

    @staticmethod
    def customer_search_fields(cust: Customer) -> list[str]:
        parts: list[str] = [
            cust.practice_name_old, cust.street, cust.zip_code, cust.city,
            cust.phone_main, cust.phone_direct, cust.mobile,
            cust.email_address, cust.website, cust.system_version,
        ]
        for num in (cust.vm_number, cust.instance_number):
            if num is not None:
                parts.append(str(num))
        for contact in cust.contacts:
            parts.extend([contact.name, contact.role, contact.email, contact.phone, contact.note])
        return [p for p in parts if p]

    @classmethod
    def customer_search_text(cls, cust: Customer) -> str:
        return " ".join(cls.customer_search_fields(cust))

    def _customer_match_summary(self, display_value: str, query: str) -> str | None:
        cust = self._customer_by_display.get(display_value)
        if cust is None:
            return None
        return CustomerService.summarize_matching_words(
            self.customer_search_fields(cust), query, exclude_text=display_value
        )

    def refresh_customer_combo(self):
        self._customer_by_display = {self.customer_display_name(c): c for c in self.customers}
        customer_names = list(self._customer_by_display)
        if not customer_names:
            customer_names = [DEFAULT_PRACTICE_DISPLAY]
        if hasattr(self, "customer_combo"):
            self.customer_combo.set_search_index({
                name: self.customer_search_text(c) for name, c in self._customer_by_display.items()
            })
            self.customer_combo.set_values(customer_names)

    def open_quick_add_customer(self):
        QuickAddCustomerDialog(self, on_customer_created=self.on_quick_customer_created)

    def on_quick_customer_created(self, new_cust: Customer):
        self.customers.append(new_cust)
        if self.on_customer_added:
            self.on_customer_added(new_cust)
        self.refresh_customer_combo()
        target_name = f"{new_cust.practice_name} ({new_cust.customer_id})"
        if hasattr(self, "customer_combo"):
            self.customer_combo.set_selected(target_name)

    def on_toggle_internal(self):
        is_int = self.is_internal_var.get()
        if is_int:
            if hasattr(self.customer_combo, "btn"):
                self.customer_combo.btn.configure(state="disabled")
            self.add_cust_btn.configure(state="disabled")
            # Select internal schema if available
            schema_names = self.schema_combo.cget("values")
            int_schema = next((s for s in schema_names if "schema_internal_task" in s or "Interne" in s), None)
            if int_schema:
                self.schema_combo.set(int_schema)
        else:
            if hasattr(self.customer_combo, "btn"):
                self.customer_combo.btn.configure(state="normal")
            self.add_cust_btn.configure(state="normal")

    def generate_case_id(self, ref_year: int | None = None) -> str:
        year = ref_year or datetime.now().year
        timestamp_part = datetime.now().strftime(TIMESTAMP_FORMAT_CASE_ID)
        return f"{CASE_ID_PREFIX}{year}-{timestamp_part}"

    def on_save(self):
        title = self.title_entry.get().strip()
        if not title:
            self.error_label.configure(text=tr("new_case.title_required", "Bitte einen Titel für den Fall eingeben."))
            return

        # Parse & validate creation date
        created_at_str = self.created_at_picker.get()
        if created_at_str:
            try:
                created_at_iso = self.created_at_picker.get_iso()
                if not created_at_iso:
                    self.error_label.configure(text=tr("new_case.invalid_date", "Ungültiges Erstellungsdatum-Format (z. B. TT.MM.JJJJ HH:MM)."))
                    return
                created_dt = parse_iso(created_at_iso)
            except Exception:
                self.error_label.configure(text=tr("new_case.invalid_date", "Ungültiges Erstellungsdatum-Format (z. B. TT.MM.JJJJ HH:MM)."))
                return
        else:
            created_at_iso = now_iso()
            created_dt = get_local_now()

        # Disallow future creation date (with 1 minute tolerance for clock drift)
        now_dt = get_local_now()
        if created_dt > now_dt + timedelta(minutes=1):
            self.error_label.configure(text=tr("new_case.future_date", "Das Erstellungsdatum darf nicht in der Zukunft liegen."))
            return

        is_internal = self.is_internal_var.get()
        case_id = self.generate_case_id(created_dt.year)

        if is_internal:
            case_customer = CaseCustomer(
                customer_id=INTERNAL_CUSTOMER_ID,
                practice_name=INTERNAL_PRACTICE_NAME,
                is_vip=False,
                contact_person="",
                phone="",
            )
            att_folder = f"attachments/{case_id}{INTERNAL_ATTACHMENT_SUFFIX}"
        else:
            selected_str = self.customer_combo.get()
            customer_obj = next((c for c in self.customers if f"{c.practice_name} ({c.customer_id})" == selected_str or c.customer_id in selected_str), None)
            if not customer_obj:
                customer_obj = self.customers[0] if self.customers else Customer(customer_id=DEFAULT_PRACTICE_ID, practice_name=DEFAULT_PRACTICE_NAME)

            case_customer = CaseCustomer(
                customer_id=customer_obj.customer_id,
                practice_name=customer_obj.practice_name,
                is_vip=customer_obj.is_vip,
                contact_person=customer_obj.contacts[0].name if customer_obj.contacts else "",
                phone=customer_obj.contacts[0].phone if customer_obj.contacts else "",
            )
            att_folder = f"attachments/{case_id}_{customer_obj.practice_name.replace(' ', '_')}"

        # Get selected schema
        selected_schema_idx = self.schema_combo.cget("values").index(self.schema_combo.get()) if self.schema_combo.get() in self.schema_combo.cget("values") else 0
        schema_obj = self.schemas[selected_schema_idx] if selected_schema_idx < len(self.schemas) else QuestionSchema(schema_id="default")

        # Get selected tags
        selected_tags = [tag for tag, var in self.selected_tags_vars.items() if var.get()]

        now_str = now_iso()

        initial_note = self.note_textbox.get("1.0", "end-1c").strip()
        timeline = []
        if initial_note:
            from enums import get_channel_val_from_display
            selected_chan_disp = self.channel_combo.get() if hasattr(self, "channel_combo") else "Telefon (Eingang)"
            selected_chan_val = get_channel_val_from_display(selected_chan_disp)
            timeline.append(TimelineEntry(
                timestamp=created_at_iso,
                author=self.created_by,
                channel=selected_chan_val,
                note=initial_note,
                status_change=INITIAL_STATUS_CHANGE_NOTE,
            ))

        new_case = Case(
            case_id=case_id,
            created_at=created_at_iso,
            updated_at=now_str,
            created_by=self.created_by,
            assigned_to=self.created_by,
            customer=case_customer,
            classification=Classification(
                schema_id=schema_obj.schema_id,
                title=title,
                deadline_callback=self.deadline_picker.get_iso(),
                tags=selected_tags,
            ),
            workflow_status=WorkflowStatus(
                is_completed=False,
                is_archived=False,
                board_column=BoardColumn.ACTION_REQUIRED,
                current_actor=Actor.SUPPORT,
                actor_since=created_at_iso,
            ),
            form_data={},
            missing_required_fields=[],
            attachment_directory=att_folder,
            timeline=timeline,
        )

        self.on_case_created(new_case)
        self.mark_clean()
        self.destroy()
