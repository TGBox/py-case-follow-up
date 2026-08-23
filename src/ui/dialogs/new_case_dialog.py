import customtkinter as ctk
from datetime import datetime
from typing import Callable
from models.case import Case, CaseCustomer, Classification, WorkflowStatus, TimelineEntry
from models.customer import Customer, Contact
from models.schema import QuestionSchema
from enums import BoardColumn, Actor, UrgencyLevel, Channel
from utils.datetime_utils import now_iso


class QuickAddCustomerDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_customer_created: Callable[[Customer], None]):
        super().__init__(parent)
        self.title("🏥 Neue Praxis schnell anlegen")
        self.geometry("420x360")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.on_customer_created = on_customer_created

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(main_frame, text="Neue Praxis anlegen", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(main_frame, text="Praxisname *:").pack(anchor="w", pady=(2, 0))
        self.name_entry = ctk.CTkEntry(main_frame, placeholder_text="z.B. Praxis Dr. Weber")
        self.name_entry.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(main_frame, text="Ansprechpartner:").pack(anchor="w", pady=(2, 0))
        self.contact_entry = ctk.CTkEntry(main_frame, placeholder_text="z.B. Dr. Hans Weber")
        self.contact_entry.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(main_frame, text="Telefon:").pack(anchor="w", pady=(2, 0))
        self.phone_entry = ctk.CTkEntry(main_frame, placeholder_text="030 / 123456")
        self.phone_entry.pack(fill="x", pady=(0, 8))

        self.vip_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(main_frame, text="⭐ VIP-Praxis", variable=self.vip_var).pack(anchor="w", pady=5)

        self.err_lbl = ctk.CTkLabel(main_frame, text="", text_color="red")
        self.err_lbl.pack(anchor="w", pady=2)

        btn_row = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_row.pack(fill="x", pady=(10, 0))

        ctk.CTkButton(btn_row, text="Abbrechen", fg_color="gray", command=self.destroy, width=100).pack(side="left")
        ctk.CTkButton(btn_row, text="Erstellen", fg_color="forestgreen", command=self.on_save, width=120).pack(side="right")

    def on_save(self):
        name = self.name_entry.get().strip()
        if not name:
            self.err_lbl.configure(text="Bitte Praxisnamen eingeben.")
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
    ):
        super().__init__(parent)
        self.title("Neuen Support-Fall anlegen")
        self.geometry("560x600")
        self.resizable(False, False)

        self.customers = list(customers)
        self.schemas = schemas
        self.created_by = created_by
        self.on_case_created = on_case_created
        self.on_customer_added = on_customer_added
        self.created_case: Case | None = None

        self.grab_set()  # Modal
        self.create_widgets()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        title_label = ctk.CTkLabel(main_frame, text="Neuen Support-Fall erfassen", font=ctk.CTkFont(size=18, weight="bold"))
        title_label.pack(anchor="w", pady=(0, 15))

        # Customer selection row
        ctk.CTkLabel(main_frame, text="Kunde / Praxis:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(5, 2))
        
        cust_row = ctk.CTkFrame(main_frame, fg_color="transparent")
        cust_row.pack(fill="x", pady=(0, 10))

        self.customer_combo = ctk.CTkOptionMenu(cust_row, values=[], width=360)
        self.customer_combo.pack(side="left", padx=(0, 5))

        add_cust_btn = ctk.CTkButton(cust_row, text="+ Neue Praxis", command=self.open_quick_add_customer, fg_color="forestgreen", width=120)
        add_cust_btn.pack(side="right")

        self.refresh_customer_combo()

        # Case Title
        ctk.CTkLabel(main_frame, text="Titel / Kurzbeschreibung:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(5, 2))
        self.title_entry = ctk.CTkEntry(main_frame, placeholder_text="z. B. Zuzahlungsdatei lässt sich nicht erzeugen", width=490)
        self.title_entry.pack(anchor="w", pady=(0, 10))

        # Schema selection
        ctk.CTkLabel(main_frame, text="Formular-Schema:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(5, 2))
        schema_names = [f"{s.display_name} [{s.schema_id}]" for s in self.schemas]
        self.schema_combo = ctk.CTkOptionMenu(main_frame, values=schema_names if schema_names else ["Standard"], width=490)
        self.schema_combo.pack(anchor="w", pady=(0, 10))

        # Callback deadline (optional)
        ctk.CTkLabel(main_frame, text="Rückruf-Deadline (ISO, optional YYYY-MM-DDTHH:MM:SS):", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(5, 2))
        self.deadline_entry = ctk.CTkEntry(main_frame, placeholder_text="z. B. 2026-08-23T16:00:00", width=490)
        self.deadline_entry.pack(anchor="w", pady=(0, 10))

        # Initial Timeline Note
        ctk.CTkLabel(main_frame, text="Initiale Notiz / Eingangskanal:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(5, 2))
        self.note_textbox = ctk.CTkTextbox(main_frame, width=490, height=80)
        self.note_textbox.pack(anchor="w", pady=(0, 15))

        # Error label
        self.error_label = ctk.CTkLabel(main_frame, text="", text_color="red")
        self.error_label.pack(anchor="w", pady=(0, 10))

        # Buttons
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(10, 0))

        cancel_btn = ctk.CTkButton(btn_frame, text="Abbrechen", fg_color="gray", command=self.destroy, width=120)
        cancel_btn.pack(side="left")

        save_btn = ctk.CTkButton(btn_frame, text="Fall anlegen", command=self.on_save, width=160)
        save_btn.pack(side="right")

    def refresh_customer_combo(self):
        customer_names = [f"{c.practice_name} ({c.customer_id})" for c in self.customers]
        if not customer_names:
            customer_names = ["Standard Praxis (K-10000)"]
        self.customer_combo.configure(values=customer_names)
        self.customer_combo.set(customer_names[0])

    def open_quick_add_customer(self):
        QuickAddCustomerDialog(self, on_customer_created=self.on_quick_customer_created)

    def on_quick_customer_created(self, new_cust: Customer):
        self.customers.append(new_cust)
        if self.on_customer_added:
            self.on_customer_added(new_cust)
        self.refresh_customer_combo()
        target_name = f"{new_cust.practice_name} ({new_cust.customer_id})"
        self.customer_combo.set(target_name)

    def generate_case_id(self) -> str:
        year = datetime.now().year
        timestamp_part = datetime.now().strftime("%M%S")
        return f"T-{year}-{timestamp_part}"

    def on_save(self):
        title = self.title_entry.get().strip()
        if not title:
            self.error_label.configure(text="Bitte einen Titel für den Fall eingeben.")
            return

        # Get selected customer
        selected_cust_idx = self.customer_combo.cget("values").index(self.customer_combo.get()) if self.customer_combo.get() in self.customer_combo.cget("values") else 0
        customer_obj = self.customers[selected_cust_idx] if selected_cust_idx < len(self.customers) else Customer(customer_id="K-10000", practice_name="Standard Praxis")

        # Get selected schema
        selected_schema_idx = self.schema_combo.cget("values").index(self.schema_combo.get()) if self.schema_combo.get() in self.schema_combo.cget("values") else 0
        schema_obj = self.schemas[selected_schema_idx] if selected_schema_idx < len(self.schemas) else QuestionSchema(schema_id="default")

        now_str = now_iso()
        case_id = self.generate_case_id()

        initial_note = self.note_textbox.get("1.0", "end-1c").strip()
        timeline = []
        if initial_note:
            timeline.append(TimelineEntry(
                timestamp=now_str,
                author=self.created_by,
                channel=Channel.PHONE_INBOUND,
                note=initial_note,
                status_change="NEW -> ACTION_REQUIRED (SUPPORT)",
            ))

        new_case = Case(
            case_id=case_id,
            created_at=now_str,
            updated_at=now_str,
            created_by=self.created_by,
            assigned_to=self.created_by,
            customer=CaseCustomer(
                customer_id=customer_obj.customer_id,
                practice_name=customer_obj.practice_name,
                is_vip=customer_obj.is_vip,
                contact_person=customer_obj.contacts[0].name if customer_obj.contacts else "",
                phone=customer_obj.contacts[0].phone if customer_obj.contacts else "",
            ),
            classification=Classification(
                schema_id=schema_obj.schema_id,
                title=title,
                deadline_callback=self.deadline_entry.get().strip(),
            ),
            workflow_status=WorkflowStatus(
                is_completed=False,
                is_archived=False,
                board_column=BoardColumn.ACTION_REQUIRED,
                current_actor=Actor.SUPPORT,
                actor_since=now_str,
            ),
            form_data={},
            missing_required_fields=[],
            attachment_directory=f"attachments/{case_id}_{customer_obj.practice_name.replace(' ', '_')}",
            timeline=timeline,
        )

        self.on_case_created(new_case)
        self.destroy()
