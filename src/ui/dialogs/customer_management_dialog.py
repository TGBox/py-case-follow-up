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
        new_btn.pack(side="right", padx=10)

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

        # Right form
        self.right_frame = ctk.CTkScrollableFrame(body_frame)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0), pady=0)

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

        # Main Contact Name
        ctk.CTkLabel(self.right_frame, text="Hauptansprechpartner:").pack(anchor="w", padx=15, pady=(5, 2))
        self.contact_name_entry = ctk.CTkEntry(self.right_frame, placeholder_text="z.B. Dr. Hans Weber")
        self.contact_name_entry.pack(fill="x", padx=15, pady=(0, 10))

        # Contact Email & Phone
        contact_row = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        contact_row.pack(fill="x", padx=15, pady=(0, 10))

        left_c = ctk.CTkFrame(contact_row, fg_color="transparent")
        left_c.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkLabel(left_c, text="E-Mail:").pack(anchor="w", pady=(0, 2))
        self.email_entry = ctk.CTkEntry(left_c, placeholder_text="praxis@beispiel.de")
        self.email_entry.pack(fill="x")

        right_c = ctk.CTkFrame(contact_row, fg_color="transparent")
        right_c.pack(side="right", fill="x", expand=True, padx=(5, 0))
        ctk.CTkLabel(right_c, text="Telefon:").pack(anchor="w", pady=(0, 2))
        self.phone_entry = ctk.CTkEntry(right_c, placeholder_text="030 / 1234567")
        self.phone_entry.pack(fill="x")

        # VIP Checkbox
        self.vip_var = ctk.BooleanVar(value=False)
        self.vip_chk = ctk.CTkCheckBox(self.right_frame, text="⭐ VIP-Kunde (erhöht den Dringlichkeits-Score um +30)", variable=self.vip_var)
        self.vip_chk.pack(anchor="w", padx=15, pady=(5, 15))

        # Action buttons
        btn_row = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=10)

        self.save_btn = ctk.CTkButton(btn_row, text="💾 Praxis Speichern", command=self.save_current_customer, fg_color="forestgreen", width=150)
        self.save_btn.pack(side="left", padx=(0, 10))

        self.status_lbl = ctk.CTkLabel(btn_row, text="", text_color="green")
        self.status_lbl.pack(side="left", padx=10)

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

        main_contact = c.contacts[0] if c.contacts else Contact()
        self.contact_name_entry.delete(0, "end")
        self.contact_name_entry.insert(0, main_contact.name)

        self.email_entry.delete(0, "end")
        self.email_entry.insert(0, main_contact.email)

        self.phone_entry.delete(0, "end")
        self.phone_entry.insert(0, main_contact.phone)

        self.vip_var.set(c.is_vip)
        self.status_lbl.configure(text="")
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
        self.contact_name_entry.delete(0, "end")
        self.email_entry.delete(0, "end")
        self.phone_entry.delete(0, "end")
        self.vip_var.set(False)

        self.status_lbl.configure(text="")
        self.render_list()

    def save_current_customer(self):
        cust_id = self.cust_id_entry.get().strip()
        name = self.name_entry.get().strip()

        if not cust_id or not name:
            self.status_lbl.configure(text="⚠️ ID und Praxisname erforderlich!", text_color="red")
            return

        contact_name = self.contact_name_entry.get().strip()
        email = self.email_entry.get().strip()
        phone = self.phone_entry.get().strip()

        contact = Contact(name=contact_name, email=email, phone=phone, role="Hauptansprechpartner")

        customer = Customer(
            customer_id=cust_id,
            practice_name=name,
            contacts=[contact] if (contact_name or email or phone) else [],
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
