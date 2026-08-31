import customtkinter as ctk
from typing import Callable, Any
from models.customer import Customer, Contact
from services.customer_service import CustomerService
from constants import DIALOG_DIMENSIONS, DIALOG_TITLES


class CustomerManagementDialog(ctk.CTkToplevel):
    def __init__(self, parent, customer_service: CustomerService, on_customers_updated: Callable[[], None] | None = None):
        super().__init__(parent)
        self.customer_service = customer_service
        self.on_customers_updated = on_customers_updated

        w, h = DIALOG_DIMENSIONS["customer_mgmt"]
        self.title(DIALOG_TITLES["customer_mgmt"])
        self.geometry(f"{w}x{h}")
        self.minsize(900, 600)
        from utils.ui_utils import center_window
        center_window(self, w, h)

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

        # Practice Name & Old Name Row
        name_row = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        name_row.pack(fill="x", padx=15, pady=(0, 10))

        name_left = ctk.CTkFrame(name_row, fg_color="transparent")
        name_left.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkLabel(name_left, text="Praxisname *:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 2))
        self.name_entry = ctk.CTkEntry(name_left, placeholder_text="z.B. Hausarztpraxis Dr. Med. Weber")
        self.name_entry.pack(fill="x")

        name_right = ctk.CTkFrame(name_row, fg_color="transparent")
        name_right.pack(side="right", fill="x", expand=True, padx=(5, 0))
        ctk.CTkLabel(name_right, text="Praxisname (Alt):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 2))
        self.name_old_entry = ctk.CTkEntry(name_right, placeholder_text="z.B. Ehem. Praxis Dr. Alt")
        self.name_old_entry.pack(fill="x")

        # Hauptansprechpartner (Anrede, Vorname, Nachname) Row
        contact_name_row = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        contact_name_row.pack(fill="x", padx=15, pady=(0, 10))

        salut_col = ctk.CTkFrame(contact_name_row, fg_color="transparent", width=100)
        salut_col.pack(side="left", fill="x", padx=(0, 4))
        ctk.CTkLabel(salut_col, text="Anrede:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 2))
        self.salut_entry = ctk.CTkEntry(salut_col, placeholder_text="Frau / Herr / Dr.", width=95)
        self.salut_entry.pack(fill="x")

        fname_col = ctk.CTkFrame(contact_name_row, fg_color="transparent")
        fname_col.pack(side="left", fill="x", expand=True, padx=4)
        ctk.CTkLabel(fname_col, text="Vorname:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 2))
        self.fname_entry = ctk.CTkEntry(fname_col, placeholder_text="Vorname...")
        self.fname_entry.pack(fill="x")

        lname_col = ctk.CTkFrame(contact_name_row, fg_color="transparent")
        lname_col.pack(side="left", fill="x", expand=True, padx=(4, 0))
        ctk.CTkLabel(lname_col, text="Nachname:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 2))
        self.lname_entry = ctk.CTkEntry(lname_col, placeholder_text="Nachname...")
        self.lname_entry.pack(fill="x")

        # Address Row (Straße, PLZ, Ort)
        addr_row = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        addr_row.pack(fill="x", padx=15, pady=(0, 10))

        street_col = ctk.CTkFrame(addr_row, fg_color="transparent")
        street_col.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkLabel(street_col, text="🏠 Straße & Hausnr.:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 2))
        self.street_entry = ctk.CTkEntry(street_col, placeholder_text="z.B. Hauptstr. 10")
        self.street_entry.pack(fill="x")

        zip_col = ctk.CTkFrame(addr_row, fg_color="transparent", width=90)
        zip_col.pack(side="left", fill="x", padx=4)
        ctk.CTkLabel(zip_col, text="PLZ:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 2))
        self.zip_entry = ctk.CTkEntry(zip_col, placeholder_text="12345", width=80)
        self.zip_entry.pack(fill="x")

        city_col = ctk.CTkFrame(addr_row, fg_color="transparent")
        city_col.pack(side="left", fill="x", expand=True, padx=(4, 0))
        ctk.CTkLabel(city_col, text="Ort:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 2))
        self.city_entry = ctk.CTkEntry(city_col, placeholder_text="Ort...")
        self.city_entry.pack(fill="x")

        # Phone Numbers Section
        phone_box = ctk.CTkFrame(self.right_frame, fg_color=("gray90", "gray18"), corner_radius=6)
        phone_box.pack(fill="x", padx=15, pady=(0, 10))
        ctk.CTkLabel(phone_box, text="📞 Telefonnummern (Cobra Export)", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(6, 4))

        pr1 = ctk.CTkFrame(phone_box, fg_color="transparent")
        pr1.pack(fill="x", padx=10, pady=(0, 4))

        p_main_col = ctk.CTkFrame(pr1, fg_color="transparent")
        p_main_col.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkLabel(p_main_col, text="Telefon Hauptnr.:").pack(anchor="w", pady=(0, 1))
        self.phone_m_entry = ctk.CTkEntry(p_main_col, placeholder_text="0711-...")
        self.phone_m_entry.pack(fill="x")

        p_dir_col = ctk.CTkFrame(pr1, fg_color="transparent")
        p_dir_col.pack(side="left", fill="x", expand=True, padx=4)
        ctk.CTkLabel(p_dir_col, text="Telefon direkt:").pack(anchor="w", pady=(0, 1))
        self.phone_dir_entry = ctk.CTkEntry(p_dir_col, placeholder_text="Durchwahl...")
        self.phone_dir_entry.pack(fill="x")

        p_priv_col = ctk.CTkFrame(pr1, fg_color="transparent")
        p_priv_col.pack(side="left", fill="x", expand=True, padx=(4, 0))
        ctk.CTkLabel(p_priv_col, text="Telefon privat:").pack(anchor="w", pady=(0, 1))
        self.phone_priv_entry = ctk.CTkEntry(p_priv_col, placeholder_text="Privat...")
        self.phone_priv_entry.pack(fill="x")

        pr2 = ctk.CTkFrame(phone_box, fg_color="transparent")
        pr2.pack(fill="x", padx=10, pady=(0, 6))

        p2_col = ctk.CTkFrame(pr2, fg_color="transparent")
        p2_col.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkLabel(p2_col, text="Telefon 2:").pack(anchor="w", pady=(0, 1))
        self.phone2_entry = ctk.CTkEntry(p2_col, placeholder_text="Zweitnr....")
        self.phone2_entry.pack(fill="x")

        p3_col = ctk.CTkFrame(pr2, fg_color="transparent")
        p3_col.pack(side="left", fill="x", expand=True, padx=4)
        ctk.CTkLabel(p3_col, text="Telefon 3:").pack(anchor="w", pady=(0, 1))
        self.phone3_entry = ctk.CTkEntry(p3_col, placeholder_text="Drittnr....")
        self.phone3_entry.pack(fill="x")

        mob_col = ctk.CTkFrame(pr2, fg_color="transparent")
        mob_col.pack(side="left", fill="x", expand=True, padx=4)
        ctk.CTkLabel(mob_col, text="Mobil:").pack(anchor="w", pady=(0, 1))
        self.mobile_entry = ctk.CTkEntry(mob_col, placeholder_text="0171-...")
        self.mobile_entry.pack(fill="x")

        mob_priv_col = ctk.CTkFrame(pr2, fg_color="transparent")
        mob_priv_col.pack(side="left", fill="x", expand=True, padx=(4, 0))
        ctk.CTkLabel(mob_priv_col, text="Mobil privat:").pack(anchor="w", pady=(0, 1))
        self.mobile_priv_entry = ctk.CTkEntry(mob_priv_col, placeholder_text="Mobil privat...")
        self.mobile_priv_entry.pack(fill="x")

        # Additional E-Mail Addresses (E-Mail 2, E-Mail 3) Row
        pr3 = ctk.CTkFrame(phone_box, fg_color="transparent")
        pr3.pack(fill="x", padx=10, pady=(0, 6))

        em2_col = ctk.CTkFrame(pr3, fg_color="transparent")
        em2_col.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkLabel(em2_col, text="✉ E-Mail 2:").pack(anchor="w", pady=(0, 1))
        self.email2_entry = ctk.CTkEntry(em2_col, placeholder_text="zweit-email@praxis.de")
        self.email2_entry.pack(fill="x")

        em3_col = ctk.CTkFrame(pr3, fg_color="transparent")
        em3_col.pack(side="left", fill="x", expand=True, padx=(4, 0))
        ctk.CTkLabel(em3_col, text="✉ E-Mail 3:").pack(anchor="w", pady=(0, 1))
        self.email3_entry = ctk.CTkEntry(em3_col, placeholder_text="dritt-email@praxis.de")
        self.email3_entry.pack(fill="x")

        # Practice Technical Details Row (Website, VM-Nummer, Instanznummer, DSC, DSCNEU)
        tech_row = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        tech_row.pack(fill="x", padx=15, pady=(0, 10))

        # Website Column
        web_col = ctk.CTkFrame(tech_row, fg_color="transparent")
        web_col.pack(side="left", fill="x", expand=True, padx=(0, 4))
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
        vm_col = ctk.CTkFrame(tech_row, fg_color="transparent", width=95)
        vm_col.pack(side="left", fill="x", padx=4)
        ctk.CTkLabel(vm_col, text="🖥 VM-Nr.:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 2))
        self.vm_entry = ctk.CTkEntry(vm_col, placeholder_text="104", width=85)
        self.vm_entry.pack(fill="x")

        # Instance Number Column
        inst_col = ctk.CTkFrame(tech_row, fg_color="transparent", width=95)
        inst_col.pack(side="left", fill="x", padx=4)
        ctk.CTkLabel(inst_col, text="🔢 Instanz-Nr.:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 2))
        self.instance_entry = ctk.CTkEntry(inst_col, placeholder_text="1", width=85)
        self.instance_entry.pack(fill="x")

        # DSC & DSCNEU Columns
        dsc_col = ctk.CTkFrame(tech_row, fg_color="transparent", width=100)
        dsc_col.pack(side="left", fill="x", padx=4)
        ctk.CTkLabel(dsc_col, text="🏷 DSC:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 2))
        self.dsc_entry = ctk.CTkEntry(dsc_col, placeholder_text="DSC...", width=90)
        self.dsc_entry.pack(fill="x")

        dsc_neu_col = ctk.CTkFrame(tech_row, fg_color="transparent", width=100)
        dsc_neu_col.pack(side="left", fill="x", padx=(4, 0))
        ctk.CTkLabel(dsc_neu_col, text="🏷 DSCNEU:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 2))
        self.dsc_neu_entry = ctk.CTkEntry(dsc_neu_col, placeholder_text="DSCNEU...", width=90)
        self.dsc_neu_entry.pack(fill="x")

        # Additional Contacts (Weitere Ansprechpartner) Box
        add_contact_box = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        add_contact_box.pack(fill="x", padx=15, pady=(0, 10))
        ctk.CTkLabel(add_contact_box, text="👥 Weitere Ansprechpartner (1 Name pro Zeile):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 2))
        self.additional_contacts_txt = ctk.CTkTextbox(add_contact_box, height=45)
        self.additional_contacts_txt.pack(fill="x")

        # General Notes row
        notes_row = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        notes_row.pack(fill="x", padx=15, pady=(0, 10))
        ctk.CTkLabel(notes_row, text="📝 Allgemeine Notizen:").pack(anchor="w", pady=(0, 2))
        self.notes_entry = ctk.CTkEntry(notes_row, placeholder_text="z.B. Erreichbarkeit, Wünsche...")
        self.notes_entry.pack(fill="x")

        # VIP Checkbox
        self.vip_var = ctk.BooleanVar(value=False)
        self.vip_chk = ctk.CTkCheckBox(self.right_frame, text="⭐ VIP-Kunde (erhöht den Dringlichkeits-Score um +30)", variable=self.vip_var)
        self.vip_chk.pack(anchor="w", padx=15, pady=(5, 10))

        # Praxisspezifische KI-Regeln
        rules_box = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        rules_box.pack(fill="x", padx=15, pady=(0, 15))
        ctk.CTkLabel(
            rules_box,
            text="⚡ Praxisspezifische KI-Regeln (haben VORRANG vor Basis-Regeln):",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", pady=(0, 2))
        ctk.CTkLabel(
            rules_box,
            text="1 Regel pro Zeile (z. B. 'Duzen erwünscht (Herr Schmidt)', 'Betreff mit [SCHMIDT] beginnen')",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray70"),
        ).pack(anchor="w", pady=(0, 4))
        self.custom_ai_rules_txt = ctk.CTkTextbox(rules_box, height=65)
        self.custom_ai_rules_txt.pack(fill="x")

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

        self.name_old_entry.delete(0, "end")
        self.name_old_entry.insert(0, c.practice_name_old)

        self.salut_entry.delete(0, "end")
        self.salut_entry.insert(0, c.salutation)

        self.fname_entry.delete(0, "end")
        self.fname_entry.insert(0, c.first_name)

        self.lname_entry.delete(0, "end")
        self.lname_entry.insert(0, c.last_name)

        self.street_entry.delete(0, "end")
        self.street_entry.insert(0, c.street)

        self.zip_entry.delete(0, "end")
        self.zip_entry.insert(0, c.zip_code)

        self.city_entry.delete(0, "end")
        self.city_entry.insert(0, c.city)

        self.phone_m_entry.delete(0, "end")
        self.phone_m_entry.insert(0, c.phone_main)

        self.phone_dir_entry.delete(0, "end")
        self.phone_dir_entry.insert(0, c.phone_direct)

        self.phone_priv_entry.delete(0, "end")
        self.phone_priv_entry.insert(0, c.phone_private)

        self.phone2_entry.delete(0, "end")
        self.phone2_entry.insert(0, c.phone2)

        self.phone3_entry.delete(0, "end")
        self.phone3_entry.insert(0, c.phone3)

        self.mobile_entry.delete(0, "end")
        self.mobile_entry.insert(0, c.mobile)

        self.mobile_priv_entry.delete(0, "end")
        self.mobile_priv_entry.insert(0, c.mobile_private)

        self.email2_entry.delete(0, "end")
        self.email2_entry.insert(0, c.email2)

        self.email3_entry.delete(0, "end")
        self.email3_entry.insert(0, c.email3)

        self.website_entry.delete(0, "end")
        self.website_entry.insert(0, c.website)

        self.vm_entry.delete(0, "end")
        if c.vm_number is not None:
            self.vm_entry.insert(0, str(c.vm_number))

        self.instance_entry.delete(0, "end")
        if c.instance_number is not None:
            self.instance_entry.insert(0, str(c.instance_number))

        self.dsc_entry.delete(0, "end")
        self.dsc_entry.insert(0, c.dsc)

        self.dsc_neu_entry.delete(0, "end")
        self.dsc_neu_entry.insert(0, c.dsc_neu)

        self.additional_contacts_txt.delete("1.0", "end")
        if c.additional_contacts:
            self.additional_contacts_txt.insert("1.0", "\n".join(c.additional_contacts))

        self.notes_entry.delete(0, "end")
        self.notes_entry.insert(0, c.general_notes)

        self.custom_ai_rules_txt.delete("1.0", "end")
        if c.custom_ai_rules:
            self.custom_ai_rules_txt.insert("1.0", "\n".join(c.custom_ai_rules))

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
        self.name_old_entry.delete(0, "end")
        self.salut_entry.delete(0, "end")
        self.fname_entry.delete(0, "end")
        self.lname_entry.delete(0, "end")
        self.street_entry.delete(0, "end")
        self.zip_entry.delete(0, "end")
        self.city_entry.delete(0, "end")
        self.phone_m_entry.delete(0, "end")
        self.phone_dir_entry.delete(0, "end")
        self.phone_priv_entry.delete(0, "end")
        self.phone2_entry.delete(0, "end")
        self.phone3_entry.delete(0, "end")
        self.mobile_entry.delete(0, "end")
        self.mobile_priv_entry.delete(0, "end")
        self.email2_entry.delete(0, "end")
        self.email3_entry.delete(0, "end")
        self.website_entry.delete(0, "end")
        self.vm_entry.delete(0, "end")
        self.instance_entry.delete(0, "end")
        self.dsc_entry.delete(0, "end")
        self.dsc_neu_entry.delete(0, "end")
        self.additional_contacts_txt.delete("1.0", "end")
        self.notes_entry.delete(0, "end")
        self.custom_ai_rules_txt.delete("1.0", "end")
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
        raw_rules = self.custom_ai_rules_txt.get("1.0", "end-1c").splitlines()
        custom_ai_rules = [r.strip() for r in raw_rules if r.strip()]
        sys_version = self.selected_customer.system_version if self.selected_customer else ""

        raw_add_contacts = self.additional_contacts_txt.get("1.0", "end-1c").splitlines()
        additional_contacts = [ac.strip() for ac in raw_add_contacts if ac.strip()]

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
            vnum1=cust_id if cust_id.isdigit() else (self.selected_customer.vnum1 if self.selected_customer else ""),
            practice_name=name,
            practice_name_old=self.name_old_entry.get().strip(),
            salutation=self.salut_entry.get().strip(),
            first_name=self.fname_entry.get().strip(),
            last_name=self.lname_entry.get().strip(),
            street=self.street_entry.get().strip(),
            zip_code=self.zip_entry.get().strip(),
            city=self.city_entry.get().strip(),
            phone_main=self.phone_m_entry.get().strip(),
            phone_direct=self.phone_dir_entry.get().strip(),
            phone_private=self.phone_priv_entry.get().strip(),
            phone2=self.phone2_entry.get().strip(),
            phone3=self.phone3_entry.get().strip(),
            mobile=self.mobile_entry.get().strip(),
            mobile_private=self.mobile_priv_entry.get().strip(),
            email_address=contacts[0].email if contacts else (self.selected_customer.email_address if self.selected_customer else ""),
            email2=self.email2_entry.get().strip(),
            email3=self.email3_entry.get().strip(),
            website=website,
            dsc=self.dsc_entry.get().strip(),
            dsc_neu=self.dsc_neu_entry.get().strip(),
            vm_number=vm_num,
            instance_number=inst_num,
            general_notes=general_notes,
            additional_contacts=additional_contacts,
            custom_ai_rules=custom_ai_rules,
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
