import customtkinter as ctk
from typing import Callable, Any
from models.customer import Customer, Contact
from services.customer_service import CustomerService


class CustomerManagementDialog(ctk.CTkToplevel):
    def __init__(self, parent, customer_service: CustomerService, on_customers_updated: Callable[[], None] | None = None):
        super().__init__(parent)
        self.customer_service = customer_service
        self.on_customers_updated = on_customers_updated

        self.title("🏥 Praxis- & Kundenverwaltung")
        self.geometry("1024x720")
        self.minsize(900, 600)
        from utils.ui_utils import center_window
        center_window(self, 1024, 720)

        self.transient(parent)
        self.grab_set()

        self.customers: list[Customer] = []
        self.filtered_customers: list[Customer] = []
        self.selected_customer: Customer | None = None

        self.create_widgets()
        self.load_customers()

    def create_widgets(self):
        # Top Header
        top_bar = ctk.CTkFrame(self, height=45, corner_radius=0)
        top_bar.pack(fill="x", side="top", padx=10, pady=(10, 5))

        ctk.CTkLabel(top_bar, text="🏥 Registrierte Praxen", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10)

        new_btn = ctk.CTkButton(top_bar, text="+ Neue Praxis anlegen", command=self.on_click_new_customer, fg_color="forestgreen", width=160)
        new_btn.pack(side="right", padx=(5, 10))

        cobra_btn = ctk.CTkButton(
            top_bar,
            text="🐍 Cobra CRM Import...",
            command=self.on_click_cobra_import,
            fg_color="darkmagenta",
            hover_color="purple",
            width=165,
        )
        cobra_btn.pack(side="right", padx=5)

        # Body: Left list, Right edit form
        body_frame = ctk.CTkFrame(self, fg_color="transparent")
        body_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        # Left list
        left_frame = ctk.CTkFrame(body_frame, width=300)
        left_frame.pack(side="left", fill="y", padx=(0, 5), pady=0)
        left_frame.pack_propagate(False)

        self.search_entry = ctk.CTkEntry(left_frame, placeholder_text="🔍 Praxis / ID suchen...")
        self.search_entry.pack(fill="x", padx=10, pady=(10, 5))
        self.search_entry.bind("<KeyRelease>", self.on_search_changed)

        self.list_scroll = ctk.CTkScrollableFrame(left_frame, fg_color="transparent")
        self.list_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        # Right panel container
        right_container = ctk.CTkFrame(body_frame, fg_color="transparent")
        right_container.pack(side="right", fill="both", expand=True, padx=(5, 0), pady=0)

        # Fixed Save Button Bar at the bottom
        btn_row = ctk.CTkFrame(right_container, fg_color=("gray85", "gray20"), height=48, corner_radius=8)
        btn_row.pack(side="bottom", fill="x", padx=0, pady=(6, 0))

        self.save_btn = ctk.CTkButton(btn_row, text="💾 Praxis Speichern", command=self.save_current_customer, fg_color="forestgreen", width=160)
        self.save_btn.pack(side="left", padx=10, pady=8)

        self.status_lbl = ctk.CTkLabel(btn_row, text="", text_color="green", font=ctk.CTkFont(weight="bold"))
        self.status_lbl.pack(side="left", padx=10, pady=8)

        # Right scrollable form for fields
        self.right_frame = ctk.CTkScrollableFrame(right_container)
        self.right_frame.pack(side="top", fill="both", expand=True, padx=0, pady=0)

        # Form fields
        self.form_title_lbl = ctk.CTkLabel(self.right_frame, text="Praxis-Details", font=ctk.CTkFont(size=16, weight="bold"))
        self.form_title_lbl.pack(anchor="w", padx=15, pady=(15, 10))

        # Customer ID
        ctk.CTkLabel(self.right_frame, text="Kunden-ID (z.B. CUST-1001):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(5, 2))
        self.cust_id_entry = ctk.CTkEntry(self.right_frame, placeholder_text="CUST-...")
        self.cust_id_entry.pack(fill="x", padx=15, pady=(0, 10))

        # Practice Name
        ctk.CTkLabel(self.right_frame, text="Praxisname *:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(5, 2))
        self.name_entry = ctk.CTkEntry(self.right_frame, placeholder_text="z.B. Hausarztpraxis Dr. Med. Weber")
        self.name_entry.pack(fill="x", padx=15, pady=(0, 10))

        # Practice Technical Details Row (Website, VM-Nummer, Instanznummer)
        tech_row = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        tech_row.pack(fill="x", padx=15, pady=(0, 10))

        # Website Column
        web_col = ctk.CTkFrame(tech_row, fg_color="transparent")
        web_col.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkLabel(web_col, text="🌐 Webseite:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 2))

        web_sub = ctk.CTkFrame(web_col, fg_color="transparent")
        web_sub.pack(fill="x")

        self.website_entry = ctk.CTkEntry(web_sub, placeholder_text="https://praxis-beispiel.de")
        self.website_entry.pack(side="left", fill="x", expand=True, padx=(0, 4))

        open_web_btn = ctk.CTkButton(
            web_sub,
            text="🔗 Öffnen",
            width=75,
            fg_color="gray30",
            hover_color="dodgerblue",
            command=self.open_website_in_browser,
        )
        open_web_btn.pack(side="right")

        # VM Number Column
        vm_col = ctk.CTkFrame(tech_row, fg_color="transparent", width=110)
        vm_col.pack(side="left", fill="x", padx=5)
        ctk.CTkLabel(vm_col, text="🖥 VM-Nr.:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 2))
        self.vm_entry = ctk.CTkEntry(vm_col, placeholder_text="z.B. 104", width=90)
        self.vm_entry.pack(fill="x")

        # Instance Number Column
        inst_col = ctk.CTkFrame(tech_row, fg_color="transparent", width=110)
        inst_col.pack(side="left", fill="x", padx=(5, 0))
        ctk.CTkLabel(inst_col, text="🔢 Instanz-Nr.:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 2))
        self.instance_entry = ctk.CTkEntry(inst_col, placeholder_text="z.B. 1", width=90)
        self.instance_entry.pack(fill="x")

        # General Notes row
        notes_row = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        notes_row.pack(fill="x", padx=15, pady=(0, 10))
        ctk.CTkLabel(notes_row, text="📝 Allgemeine Notizen:").pack(anchor="w", pady=(0, 2))
        self.notes_entry = ctk.CTkEntry(notes_row, placeholder_text="z.B. Erreichbarkeit, Wünsche...")
        self.notes_entry.pack(fill="x")

        # VIP Checkbox
        self.vip_var = ctk.BooleanVar(value=False)
        self.vip_chk = ctk.CTkCheckBox(self.right_frame, text="⭐ VIP-Kunde (erhöht den Dringlichkeits-Score um +30)", variable=self.vip_var)
        self.vip_chk.pack(anchor="w", padx=15, pady=(5, 15))

        # --- Multiple Contacts Header ---
        contacts_header_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        contacts_header_frame.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkLabel(contacts_header_frame, text="👥 Ansprechpartner & Kontakte", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        add_contact_btn = ctk.CTkButton(contacts_header_frame, text="+ Kontakt hinzufügen", command=lambda: self.add_contact_row(), fg_color="gray30", width=140)
        add_contact_btn.pack(side="right")

        self.contacts_container = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.contacts_container.pack(fill="x", padx=15, pady=(0, 10))

        self.contact_rows: list[dict[str, Any]] = []

    def open_website_in_browser(self):
        url = self.website_entry.get().strip()
        if not url:
            self.status_lbl.configure(text="⚠ Keine Webseite eingetragen!", text_color="orange")
            return
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "https://" + url
        import webbrowser
        webbrowser.open(url)
        self.status_lbl.configure(text=f"🌐 Webseite geöffnet: {url}", text_color="green")

    def render_contact_rows(self, contacts: list[Contact]):
        for r in list(self.contact_rows):
            r["frame"].destroy()
        self.contact_rows.clear()

        if not contacts:
            self.add_contact_row()
        else:
            for c in contacts:
                self.add_contact_row(c)

    def add_contact_row(self, contact: Contact | None = None):
        c_data = contact or Contact()
        row_idx = len(self.contact_rows) + 1

        card = ctk.CTkFrame(self.contacts_container, corner_radius=6, fg_color=("gray85", "gray22"))
        card.pack(fill="x", pady=5)

        # Card header
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(6, 2))
        ctk.CTkLabel(header, text=f"Kontakt #{row_idx}", font=ctk.CTkFont(size=11, weight="bold"), text_color="gray60").pack(side="left")

        row_dict: dict[str, Any] = {"frame": card}

        remove_btn = ctk.CTkButton(
            header,
            text="🗑 Entfernen",
            width=80,
            height=22,
            fg_color="gray40",
            hover_color="darkred",
            command=lambda: self.remove_contact_row(row_dict),
        )
        remove_btn.pack(side="right")

        # Name & Role row
        r1 = ctk.CTkFrame(card, fg_color="transparent")
        r1.pack(fill="x", padx=10, pady=(0, 4))

        left_r1 = ctk.CTkFrame(r1, fg_color="transparent")
        left_r1.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkLabel(left_r1, text="Name *:").pack(anchor="w", pady=(0, 1))
        name_entry = ctk.CTkEntry(left_r1, placeholder_text="z.B. Dr. Hans Weber")
        name_entry.insert(0, c_data.name)
        name_entry.pack(fill="x")
        row_dict["name_entry"] = name_entry

        right_r1 = ctk.CTkFrame(r1, fg_color="transparent")
        right_r1.pack(side="right", fill="x", expand=True, padx=(4, 0))
        ctk.CTkLabel(right_r1, text="Rolle / Funktion:").pack(anchor="w", pady=(0, 1))
        role_entry = ctk.CTkEntry(right_r1, placeholder_text="z.B. Praxisinhaber, Abrechnung...")
        role_entry.insert(0, c_data.role)
        role_entry.pack(fill="x")
        row_dict["role_entry"] = role_entry

        # Email & Phone row
        r2 = ctk.CTkFrame(card, fg_color="transparent")
        r2.pack(fill="x", padx=10, pady=(0, 4))

        left_r2 = ctk.CTkFrame(r2, fg_color="transparent")
        left_r2.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkLabel(left_r2, text="E-Mail:").pack(anchor="w", pady=(0, 1))
        email_entry = ctk.CTkEntry(left_r2, placeholder_text="weber@praxis.de")
        email_entry.insert(0, c_data.email)
        email_entry.pack(fill="x")
        row_dict["email_entry"] = email_entry

        right_r2 = ctk.CTkFrame(r2, fg_color="transparent")
        right_r2.pack(side="right", fill="x", expand=True, padx=(4, 0))
        ctk.CTkLabel(right_r2, text="Telefon:").pack(anchor="w", pady=(0, 1))
        phone_entry = ctk.CTkEntry(right_r2, placeholder_text="030 / 1234567")
        phone_entry.insert(0, c_data.phone)
        phone_entry.pack(fill="x")
        row_dict["phone_entry"] = phone_entry

        # Note row
        r3 = ctk.CTkFrame(card, fg_color="transparent")
        r3.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkLabel(r3, text="Notiz:").pack(anchor="w", pady=(0, 1))
        note_entry = ctk.CTkEntry(r3, placeholder_text="z.B. Erreichbar Mo-Do Vormittag")
        note_entry.insert(0, c_data.note)
        note_entry.pack(fill="x")
        row_dict["note_entry"] = note_entry

        self.contact_rows.append(row_dict)

    def remove_contact_row(self, row_dict: dict[str, Any]):
        if len(self.contact_rows) <= 1:
            # Clear fields of the last row instead of deleting completely
            row_dict["name_entry"].delete(0, "end")
            row_dict["role_entry"].delete(0, "end")
            row_dict["email_entry"].delete(0, "end")
            row_dict["phone_entry"].delete(0, "end")
            row_dict["note_entry"].delete(0, "end")
            return

        row_dict["frame"].destroy()
        if row_dict in self.contact_rows:
            self.contact_rows.remove(row_dict)

        # Update contact headers
        for idx, r in enumerate(self.contact_rows, 1):
            for child in r["frame"].winfo_children():
                if isinstance(child, ctk.CTkFrame):
                    for sub in child.winfo_children():
                        if isinstance(sub, ctk.CTkLabel) and sub.cget("text").startswith("Kontakt #"):
                            sub.configure(text=f"Kontakt #{idx}")

    def load_customers(self):
        self.customers = self.customer_service.get_all_customers()
        self.on_search_changed()

        if self.customers:
            self.select_customer(self.customers[0].customer_id)
        else:
            self.on_click_new_customer()

    def render_list(self):
        for w in self.list_scroll.winfo_children():
            w.destroy()

        if not self.filtered_customers:
            ctk.CTkLabel(self.list_scroll, text="Keine Praxen gefunden.", text_color="gray").pack(pady=20)
            return

        for c in self.filtered_customers:
            is_selected = self.selected_customer and self.selected_customer.customer_id == c.customer_id
            fg_color = ("gray75", "gray30") if is_selected else ("gray85", "gray20")
            vip_prefix = "⭐ " if c.is_vip else ""
            title_txt = f"{vip_prefix}{c.practice_name}"
            sub_txt = f"ID: {c.customer_id}"

            btn_frame = ctk.CTkFrame(self.list_scroll, fg_color=fg_color, corner_radius=6)
            btn_frame.pack(fill="x", pady=3, padx=2)

            btn = ctk.CTkButton(
                btn_frame,
                text=f"{title_txt}\n({sub_txt})",
                anchor="w",
                fg_color="transparent",
                hover_color=("gray70", "gray35"),
                text_color=("black", "white"),
                command=lambda cid=c.customer_id: self.select_customer(cid)
            )
            btn.pack(fill="x", padx=5, pady=5)

    def select_customer(self, customer_id: str):
        c = self.customer_service.get_customer_by_id(customer_id)
        if not c:
            return

        self.selected_customer = c
        self.form_title_lbl.configure(text=f"Praxis bearbeiten: {c.practice_name}")

        self.cust_id_entry.configure(state="normal")
        self.cust_id_entry.delete(0, "end")
        self.cust_id_entry.insert(0, c.customer_id)
        self.cust_id_entry.configure(state="disabled")

        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, c.practice_name)

        self.website_entry.delete(0, "end")
        self.website_entry.insert(0, c.website)

        self.vm_entry.delete(0, "end")
        if c.vm_number is not None:
            self.vm_entry.insert(0, str(c.vm_number))

        self.instance_entry.delete(0, "end")
        if c.instance_number is not None:
            self.instance_entry.insert(0, str(c.instance_number))

        self.notes_entry.delete(0, "end")
        self.notes_entry.insert(0, c.general_notes)

        self.vip_var.set(c.is_vip)
        self.status_lbl.configure(text="")

        self.render_contact_rows(c.contacts)
        self.render_list()

    def on_click_new_customer(self):
        self.selected_customer = None
        self.form_title_lbl.configure(text="🆕 Neue Praxis anlegen")

        next_num = len(self.customers) + 1001
        new_id = f"CUST-{next_num}"

        self.cust_id_entry.configure(state="normal")
        self.cust_id_entry.delete(0, "end")
        self.cust_id_entry.insert(0, new_id)

        self.name_entry.delete(0, "end")
        self.website_entry.delete(0, "end")
        self.vm_entry.delete(0, "end")
        self.instance_entry.delete(0, "end")
        self.notes_entry.delete(0, "end")
        self.vip_var.set(False)

        self.status_lbl.configure(text="")
        self.render_contact_rows([])
        self.render_list()

    def save_current_customer(self):
        cust_id = self.cust_id_entry.get().strip()
        name = self.name_entry.get().strip()

        if not cust_id or not name:
            self.status_lbl.configure(text="⚠ ID und Praxisname erforderlich!", text_color="red")
            return

        website = self.website_entry.get().strip()
        
        vm_str = self.vm_entry.get().strip()
        vm_num = int(vm_str) if vm_str.isdigit() else None

        inst_str = self.instance_entry.get().strip()
        inst_num = int(inst_str) if inst_str.isdigit() else None

        general_notes = self.notes_entry.get().strip()
        sys_version = self.selected_customer.system_version if self.selected_customer else ""

        contacts: list[Contact] = []
        for r in self.contact_rows:
            c_name = r["name_entry"].get().strip()
            c_role = r["role_entry"].get().strip()
            c_email = r["email_entry"].get().strip()
            c_phone = r["phone_entry"].get().strip()
            c_note = r["note_entry"].get().strip()

            if c_name or c_email or c_phone or c_role or c_note:
                contacts.append(Contact(
                    name=c_name,
                    role=c_role,
                    email=c_email,
                    phone=c_phone,
                    note=c_note
                ))

        customer = Customer(
            customer_id=cust_id,
            practice_name=name,
            website=website,
            vm_number=vm_num,
            instance_number=inst_num,
            general_notes=general_notes,
            system_version=sys_version,
            contacts=contacts,
            is_vip=self.vip_var.get()
        )

        self.customer_service.save_customer(customer)
        self.customers = self.customer_service.get_all_customers()
        self.selected_customer = customer

        self.status_lbl.configure(text="✅ Praxis gespeichert!", text_color="green")
        self.on_search_changed()
        self.select_customer(cust_id)

        if self.on_customers_updated:
            self.on_customers_updated()

    def on_search_changed(self, event=None):
        query = self.search_entry.get().strip().lower()
        if not query:
            self.filtered_customers = list(self.customers)
        else:
            self.filtered_customers = self.customer_service.search_customers(query)
        self.render_list()

    def on_click_cobra_import(self):
        from ui.dialogs.cobra_import_dialog import CobraImportDialog
        CobraImportDialog(
            self,
            existing_customers=self.customers,
            on_import_completed=self.on_cobra_import_completed,
        )

    def on_cobra_import_completed(self, merged_customers: list[Customer]):
        for c in merged_customers:
            self.customer_service.save_customer(c)
        self.load_customers()
        if self.on_customers_updated:
            self.on_customers_updated()
