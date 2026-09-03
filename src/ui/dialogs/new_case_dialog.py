import customtkinter as ctk
from datetime import datetime, timedelta
from typing import Callable
from models.case import Case, CaseCustomer, Classification, WorkflowStatus, TimelineEntry
from models.customer import Customer, Contact
from models.schema import QuestionSchema
from enums import BoardColumn, Actor, UrgencyLevel, Channel
from utils.datetime_utils import now_iso, parse_iso, get_local_now, format_german_datetime
from constants import DEFAULT_TAGS, DIALOG_DIMENSIONS


class QuickAddCustomerDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_customer_created: Callable[[Customer], None]):
        super().__init__(parent)
        from services.i18n_service import tr

        w, h = DIALOG_DIMENSIONS["quick_customer"]
        self.title(tr("dialog_titles.quick_customer", "🏥 Neue Praxis schnell anlegen"))
        self.geometry(f"{w}x{h}")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.on_customer_created = on_customer_created

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(main_frame, text=tr("quick_customer.header", "Neue Praxis anlegen"), font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(main_frame, text=tr("quick_customer.practice_name", "Praxisname *:")).pack(anchor="w", pady=(2, 0))
        self.name_entry = ctk.CTkEntry(main_frame, placeholder_text=tr("quick_customer.practice_name_placeholder", "z.B. Praxis Dr. Weber"))
        self.name_entry.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(main_frame, text=tr("quick_customer.contact_person", "Ansprechpartner:")).pack(anchor="w", pady=(2, 0))
        self.contact_entry = ctk.CTkEntry(main_frame, placeholder_text=tr("quick_customer.contact_placeholder", "z.B. Dr. Hans Weber"))
        self.contact_entry.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(main_frame, text=tr("quick_customer.phone", "Telefon:")).pack(anchor="w", pady=(2, 0))
        self.phone_entry = ctk.CTkEntry(main_frame, placeholder_text=tr("quick_customer.phone_placeholder", "030 / 123456"))
        self.phone_entry.pack(fill="x", pady=(0, 8))

        self.vip_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(main_frame, text=tr("quick_customer.is_vip", "⭐ VIP-Praxis"), variable=self.vip_var).pack(anchor="w", pady=5)

        self.err_lbl = ctk.CTkLabel(main_frame, text="", text_color="red")
        self.err_lbl.pack(anchor="w", pady=2)

        btn_row = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_row.pack(fill="x", pady=(10, 0))

        ctk.CTkButton(btn_row, text=tr("common.cancel", "Abbrechen"), fg_color="gray", command=self.destroy, width=100).pack(side="left")
        ctk.CTkButton(btn_row, text=tr("ui_buttons.create", "Erstellen"), fg_color="forestgreen", command=self.on_save, width=120).pack(side="right")

    def on_save(self):
        from services.i18n_service import tr
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
            is_vip=self.vip_var.get()
        )
        self.on_customer_created(new_cust)
        self.destroy()


class NewCaseDialog(ctk.CTkToplevel):
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
        from services.i18n_service import tr

        w, h = DIALOG_DIMENSIONS["new_case"]
        self.title(tr("dialog_titles.new_case", "Neuen Support-Fall anlegen"))
        self.geometry(f"{w}x{h}")
        self.minsize(700, 780)
        from utils.ui_utils import center_window
        center_window(self, w, h)

        self.customers = list(customers)
        self.schemas = schemas
        self.created_by = created_by
        self.on_case_created = on_case_created
        self.on_customer_added = on_customer_added
        self.available_tags = list(available_tags) if available_tags else list(DEFAULT_TAGS)
        self.on_tag_added = on_tag_added

        self.selected_tags_vars: dict[str, ctk.BooleanVar] = {}
        self.created_case: Case | None = None

        self.grab_set()  # Modal
        self.create_widgets()

    def create_widgets(self):
        from services.i18n_service import tr

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=12)

        # 1. Pinned Bottom Action Bar (ALWAYS 100% VISIBLE AT BOTTOM)
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", pady=(8, 0))

        cancel_btn = ctk.CTkButton(btn_frame, text=tr("common.cancel", "Abbrechen"), fg_color="gray", command=self.destroy, width=120)
        cancel_btn.pack(side="left")

        save_btn = ctk.CTkButton(btn_frame, text=tr("new_case_dialog.create_btn", "Fall anlegen"), command=self.on_save, width=160, fg_color="#2563eb", hover_color="#1d4ed8")
        save_btn.pack(side="right")

        # Error label pinned right above bottom buttons
        self.error_label = ctk.CTkLabel(main_frame, text="", text_color="red")
        self.error_label.pack(side="bottom", anchor="w", pady=(0, 2))

        # 2. Scrollable Form Inputs Area (Fills remaining height)
        form_scroll = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        form_scroll.pack(side="top", fill="both", expand=True)
        from utils.ui_utils import enable_auto_hiding_scrollbar
        enable_auto_hiding_scrollbar(form_scroll)

        # Header
        title_label = ctk.CTkLabel(form_scroll, text=tr("new_case_dialog.header", "Neuen Support-Fall erfassen"), font=ctk.CTkFont(size=18, weight="bold"))
        title_label.pack(anchor="w", pady=(0, 8))

        # Internal Task Checkbox
        self.is_internal_var = ctk.BooleanVar(value=False)
        self.chk_internal = ctk.CTkCheckBox(
            form_scroll,
            text=tr("new_case_dialog.is_internal", "🏢 Interner Vorgang (ohne Kundenelement)"),
            variable=self.is_internal_var,
            command=self.on_toggle_internal,
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.chk_internal.pack(anchor="w", pady=(0, 8))

        # Customer selection row
        ctk.CTkLabel(form_scroll, text=tr("new_case_dialog.customer", "Kunde / Praxis:"), font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(4, 1))
        
        cust_row = ctk.CTkFrame(form_scroll, fg_color="transparent")
        cust_row.pack(fill="x", pady=(0, 6))

        from ui.widgets.searchable_combobox import SearchableCombobox
        initial_cust_names = [f"{c.practice_name} ({c.customer_id})" for c in self.customers] if self.customers else [tr("new_case_dialog.no_customers", "Keine Kunden")]
        self.customer_combo = SearchableCombobox(cust_row, values=initial_cust_names, width=380)
        self.customer_combo.pack(side="left", padx=(0, 5), fill="x", expand=True)

        self.add_cust_btn = ctk.CTkButton(cust_row, text=tr("new_case_dialog.add_practice_btn", "+ Neue Praxis"), command=self.open_quick_add_customer, fg_color="forestgreen", width=120)
        self.add_cust_btn.pack(side="right")

        self.refresh_customer_combo()

        # Case Title
        ctk.CTkLabel(form_scroll, text=tr("new_case_dialog.title_label", "Titel / Kurzbeschreibung:"), font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(4, 1))
        self.title_entry = ctk.CTkEntry(form_scroll, placeholder_text=tr("new_case_dialog.title_placeholder", "z. B. Zuzahlungsdatei lässt sich nicht erzeugen"))
        self.title_entry.pack(fill="x", pady=(0, 6))

        # Creation Date (defaulting to current time)
        ctk.CTkLabel(form_scroll, text=tr("new_case_dialog.created_at", "Erstellungsdatum / Vorgangsbeginn (TT.MM.JJJJ HH:MM):"), font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(4, 1))
        from ui.widgets.date_picker import DatePickerWidget
        self.created_at_picker = DatePickerWidget(
            form_scroll,
            placeholder_text=tr("date_picker.placeholder_datetime_example", "z. B. 25.08.2026 09:30"),
            include_time=True,
            initial_value=format_german_datetime(now_iso()),
            width=380,
        )
        self.created_at_picker.pack(fill="x", pady=(0, 6))

        # Schema selection
        ctk.CTkLabel(form_scroll, text=tr("new_case_dialog.schema", "Formular-Schema:"), font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(4, 1))
        schema_names = [f"{s.display_name} [{s.schema_id}]" for s in self.schemas]
        self.schema_combo = ctk.CTkOptionMenu(form_scroll, values=schema_names if schema_names else ["Standard"])
        quick_opt = next((name for name in schema_names if "schema_quick" in name or "Schnellerfassung" in name), None)
        if quick_opt:
            self.schema_combo.set(quick_opt)
        self.schema_combo.pack(fill="x", pady=(0, 6))

        # Tags Selection
        ctk.CTkLabel(form_scroll, text=tr("new_case_dialog.tags", "Tags / Stichworte zuweisen:"), font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(4, 1))
        
        self.tags_frame = ctk.CTkFrame(form_scroll, fg_color="transparent")
        self.tags_frame.pack(fill="x", pady=(0, 6))

        self.render_tags_checkboxes()

        # Callback deadline (optional)
        ctk.CTkLabel(form_scroll, text=tr("new_case_dialog.deadline", "Rückruf-Deadline (optional, TT.MM.JJJJ HH:MM):"), font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(4, 1))
        from ui.widgets.date_picker import DatePickerWidget
        self.deadline_picker = DatePickerWidget(form_scroll, placeholder_text=tr("date_picker.placeholder_deadline_example", "z. B. 23.08.2026 16:00"), include_time=True, width=380)
        self.deadline_picker.pack(fill="x", pady=(0, 6))

        # Initial Timeline Note & Channel Selection
        note_hdr_row = ctk.CTkFrame(form_scroll, fg_color="transparent")
        note_hdr_row.pack(fill="x", pady=(4, 1))

        ctk.CTkLabel(note_hdr_row, text=tr("new_case_dialog.initial_note", "Initiale Notiz / Eingangskanal:"), font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")

        from enums import CHANNEL_DISPLAY, get_channel_display, Channel
        channel_names = [get_channel_display(c) for c in CHANNEL_DISPLAY]
        self.channel_combo = ctk.CTkOptionMenu(note_hdr_row, values=channel_names, width=175, font=ctk.CTkFont(size=11))
        self.channel_combo.set(get_channel_display(Channel.PHONE_INBOUND.value))
        self.channel_combo.pack(side="right")

        self.note_textbox = ctk.CTkTextbox(form_scroll, height=65)
        self.note_textbox.pack(fill="x", pady=(0, 6))

        from utils.ui_utils import enable_textbox_cursor_autoscroll
        enable_textbox_cursor_autoscroll(self.note_textbox)

    def render_tags_checkboxes(self):
        for w in self.tags_frame.winfo_children():
            w.destroy()

        grid_frame = ctk.CTkFrame(self.tags_frame, fg_color="transparent")
        grid_frame.pack(fill="x", padx=2, pady=1)

        num_cols = 4
        for col in range(num_cols):
            grid_frame.grid_columnconfigure(col, weight=1, uniform="new_case_tag_pills")

        for idx, tag in enumerate(self.available_tags):
            if tag not in self.selected_tags_vars:
                self.selected_tags_vars[tag] = ctk.BooleanVar(value=False)

            is_selected = self.selected_tags_vars[tag].get()
            btn_text = f"✓ {tag}" if is_selected else tag
            btn_fg = ("#2563eb", "#1d4ed8") if is_selected else ("gray85", "gray28")
            btn_hover = ("#1d4ed8", "#1e40af") if is_selected else ("gray75", "gray38")
            btn_text_color = "white" if is_selected else ("gray20", "gray85")

            r = idx // num_cols
            c = idx % num_cols

            btn = ctk.CTkButton(
                grid_frame,
                text=btn_text,
                height=28,
                corner_radius=14,
                font=ctk.CTkFont(size=11, weight="bold" if is_selected else "normal"),
                fg_color=btn_fg,
                hover_color=btn_hover,
                text_color=btn_text_color,
                command=lambda t=tag: self.toggle_tag(t),
            )
            btn.grid(row=r, column=c, padx=3, pady=2, sticky="ew")

        # Place the + Tag button in the next slot
        next_idx = len(self.available_tags)
        r = next_idx // num_cols
        c = next_idx % num_cols

        from services.i18n_service import tr

        add_tag_btn = ctk.CTkButton(
            grid_frame,
            text=tr("new_case.add_tag", "+ Tag"),
            height=28,
            corner_radius=14,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=("gray75", "gray35"),
            hover_color=("gray65", "gray45"),
            command=self.open_quick_add_tag,
        )
        add_tag_btn.grid(row=r, column=c, padx=3, pady=2, sticky="ew")

    def toggle_tag(self, tag_name: str):
        if tag_name in self.selected_tags_vars:
            curr = self.selected_tags_vars[tag_name].get()
            self.selected_tags_vars[tag_name].set(not curr)
            self.render_tags_checkboxes()

    def open_quick_add_tag(self):
        from services.i18n_service import tr
        dialog = ctk.CTkInputDialog(text=tr("new_case.tag_input_prompt", "Geben Sie den Namen des neuen Tags ein:"), title=tr("new_case.tag_input_title", "Neuen Tag hinzufügen"))
        new_tag = dialog.get_input()
        if new_tag and new_tag.strip():
            tag_name = new_tag.strip()
            if tag_name not in self.available_tags:
                self.available_tags.append(tag_name)
                self.selected_tags_vars[tag_name] = ctk.BooleanVar(value=True)
                if self.on_tag_added:
                    self.on_tag_added(tag_name)
                self.render_tags_checkboxes()

    def refresh_customer_combo(self):
        customer_names = [f"{c.practice_name} ({c.customer_id})" for c in self.customers]
        if not customer_names:
            customer_names = ["Standard Praxis (K-10000)"]
        if hasattr(self, "customer_combo"):
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
        timestamp_part = datetime.now().strftime("%M%S")
        return f"T-{year}-{timestamp_part}"

    def on_save(self):
        from services.i18n_service import tr
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
                customer_id="INTERNAL",
                practice_name="Intern / Keine Praxis",
                is_vip=False,
                contact_person="",
                phone="",
            )
            att_folder = f"attachments/{case_id}_Intern"
        else:
            selected_str = self.customer_combo.get()
            customer_obj = next((c for c in self.customers if f"{c.practice_name} ({c.customer_id})" == selected_str or c.customer_id in selected_str), None)
            if not customer_obj:
                customer_obj = self.customers[0] if self.customers else Customer(customer_id="K-10000", practice_name="Standard Praxis")

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
            from enums import get_channel_val_from_display, Channel
            selected_chan_disp = self.channel_combo.get() if hasattr(self, "channel_combo") else "Telefon (Eingang)"
            selected_chan_val = get_channel_val_from_display(selected_chan_disp)
            timeline.append(TimelineEntry(
                timestamp=created_at_iso,
                author=self.created_by,
                channel=selected_chan_val,
                note=initial_note,
                status_change="NEW -> ACTION_REQUIRED (SUPPORT)",
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
        self.destroy()
