"""Formular-Aufbau fuer CustomerManagementDialog: die komplette Widget-Konstruktion
aus dem ehemals ~317-zeiligen create_widgets() (Kopfleiste, Praxis-Liste links,
Formularfelder rechts in mehreren fachlichen Gruppen, Kontakte-Sektion).

CustomerFormBuilderMixin wird per Mixin-Vererbung in CustomerManagementDialog
eingemischt, sodass `self` weiterhin dieselbe Dialog-Instanz ist und alle hier
gesetzten self.-Attribute (self.right_frame, self.name_entry, self.search_entry,
usw.) wie gewohnt von den uebrigen Methoden (select_customer, save_current_customer,
...) weiterverwendet werden koennen. create_widgets() selbst bleibt in
customer_management_dialog.py und baut nur noch body_frame auf, bevor es an die
passenden _build_*()-Methoden hier delegiert - reines Verschieben von Code,
keine Verhaltensaenderung.
"""
import customtkinter as ctk
from typing import Any

class CustomerFormBuilderMixin:
    """Baut die Widgets von CustomerManagementDialog auf. Nur zusammen mit
    CustomerManagementDialog (bzw. einer Klasse mit denselben self.right_frame /
    self.save_current_customer / ... Attributen und Methoden) nutzbar.
    """

    def on_click_new_customer(self) -> None: ...
    def on_click_cobra_import(self) -> None: ...
    def on_search_changed(self, event: Any = None) -> None: ...
    def on_sort_changed(self) -> None: ...
    def toggle_sort_direction(self) -> None: ...
    def save_current_customer(self) -> None: ...
    def open_website_in_browser(self) -> None: ...
    def add_contact_row(self, contact: Any = None) -> None: ...

    def _build_top_bar(self):
        from services.i18n_service import tr

        # Top Header
        top_bar = ctk.CTkFrame(self, height=45, corner_radius=0)
        top_bar.pack(fill="x", side="top", padx=10, pady=(10, 5))

        ctk.CTkLabel(top_bar, text=tr("customer_mgmt.header", "🏥 Registrierte Praxen"), font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10)

        new_btn = ctk.CTkButton(top_bar, text=tr("customer_mgmt.new_practice_btn", "+ Neue Praxis anlegen"), command=self.on_click_new_customer, fg_color="forestgreen", width=160)
        new_btn.pack(side="right", padx=(5, 10))

        cobra_btn = ctk.CTkButton(
            top_bar,
            text=tr("customer_mgmt.cobra_import_btn", "🐍 Cobra CRM Import..."),
            command=self.on_click_cobra_import,
            fg_color="darkmagenta",
            hover_color="purple",
            width=165,
        )
        cobra_btn.pack(side="right", padx=5)

    def _build_customer_list_panel(self, body_frame: ctk.CTkFrame):
        from services.i18n_service import tr
        from enums import get_sort_criterion_display

        # Left list
        left_frame = ctk.CTkFrame(body_frame, width=300)
        left_frame.pack(side="left", fill="y", padx=(0, 5), pady=0)
        left_frame.pack_propagate(False)

        self.search_entry = ctk.CTkEntry(left_frame, placeholder_text=tr("customer_mgmt.search_placeholder", "🔍 Praxis / ID suchen..."))
        self.search_entry.pack(fill="x", padx=10, pady=(10, 4))
        self.search_entry.bind("<KeyRelease>", self.on_search_changed)

        # Sort Controls Bar
        sort_bar = ctk.CTkFrame(left_frame, fg_color="transparent")
        sort_bar.pack(fill="x", padx=10, pady=(0, 5))

        self.sort_criterion_combo = ctk.CTkOptionMenu(
            sort_bar,
            values=[get_sort_criterion_display(c) for c in ("name", "id", "contact")],
            width=170,
            command=lambda v: self.on_sort_changed(),
            font=ctk.CTkFont(size=11),
        )
        self.sort_criterion_combo.pack(side="left", padx=(0, 4))

        self.sort_asc_var = True
        self.sort_dir_btn = ctk.CTkButton(
            sort_bar,
            text=tr("customer_mgmt.sort_asc", "↑ Aufst."),
            width=85,
            fg_color="gray30",
            hover_color="gray40",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.toggle_sort_direction,
        )
        self.sort_dir_btn.pack(side="right")

        self.list_scroll = ctk.CTkScrollableFrame(left_frame, fg_color="transparent")
        self.list_scroll.pack(fill="both", expand=True, padx=5, pady=5)

    def _build_customer_form_panel(self, body_frame: ctk.CTkFrame):
        from services.i18n_service import tr

        # Right panel container
        right_container = ctk.CTkFrame(body_frame, fg_color="transparent")
        right_container.pack(side="right", fill="both", expand=True, padx=(5, 0), pady=0)

        # Fixed Save Button Bar at the bottom
        btn_row = ctk.CTkFrame(right_container, fg_color=("gray85", "gray20"), height=48, corner_radius=8)
        btn_row.pack(side="bottom", fill="x", padx=0, pady=(6, 0))

        self.save_btn = ctk.CTkButton(btn_row, text=tr("customer_mgmt.save_practice_btn", "💾 Praxis Speichern"), command=self.save_current_customer, fg_color="forestgreen", width=160)
        self.save_btn.pack(side="left", padx=10, pady=8)

        self.status_lbl = ctk.CTkLabel(btn_row, text="", text_color="green", font=ctk.CTkFont(weight="bold"))
        self.status_lbl.pack(side="left", padx=10, pady=8)

        # Right scrollable form for fields
        self.right_frame = ctk.CTkScrollableFrame(right_container)
        self.right_frame.pack(side="top", fill="both", expand=True, padx=0, pady=0)
        self._build_basic_info_fields()
        self._build_phone_and_email_fields()
        self._build_technical_details_fields()
        self._build_notes_and_rules_fields()
        self._build_contacts_section()

    def _build_basic_info_fields(self):
        from services.i18n_service import tr
        # Form fields
        self.form_title_lbl = ctk.CTkLabel(self.right_frame, text=tr("customer_mgmt.details_title", "Praxis-Details"), font=ctk.CTkFont(size=16, weight="bold"))
        self.form_title_lbl.pack(anchor="w", padx=15, pady=(15, 10))

        # Customer ID
        ctk.CTkLabel(self.right_frame, text=tr("customer_mgmt.cust_id_lbl", "Kunden-ID (z.B. CUST-1001):"), font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(5, 2))
        self.cust_id_entry = ctk.CTkEntry(self.right_frame, placeholder_text=tr("customer_mgmt.cust_id_placeholder", "CUST-..."))
        self.cust_id_entry.pack(fill="x", padx=15, pady=(0, 10))

        # Practice Name & Old Name Row
        name_row = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        name_row.pack(fill="x", padx=15, pady=(0, 10))

        name_left = ctk.CTkFrame(name_row, fg_color="transparent")
        name_left.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkLabel(name_left, text=tr("customer_mgmt.practice_name_lbl", "Praxisname *:"), font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 2))
        self.name_entry = ctk.CTkEntry(name_left, placeholder_text=tr("customer_mgmt.practice_name_placeholder", "z.B. Hausarztpraxis Dr. Med. Weber"))
        self.name_entry.pack(fill="x")

        name_right = ctk.CTkFrame(name_row, fg_color="transparent")
        name_right.pack(side="right", fill="x", expand=True, padx=(5, 0))
        ctk.CTkLabel(name_right, text=tr("customer_mgmt.practice_name_old_lbl", "Praxisname (Alt):"), font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 2))
        self.name_old_entry = ctk.CTkEntry(name_right, placeholder_text=tr("customer_mgmt.practice_name_old_placeholder", "z.B. Ehem. Praxis Dr. Alt"))
        self.name_old_entry.pack(fill="x")

        # Hauptansprechpartner (Anrede, Vorname, Nachname) Row
        contact_name_row = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        contact_name_row.pack(fill="x", padx=15, pady=(0, 10))

        salut_col = ctk.CTkFrame(contact_name_row, fg_color="transparent", width=100)
        salut_col.pack(side="left", fill="x", padx=(0, 4))
        ctk.CTkLabel(salut_col, text=tr("customer_mgmt.salut_lbl", "Anrede:"), font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 2))
        self.salut_entry = ctk.CTkEntry(salut_col, placeholder_text=tr("customer_mgmt.salut_placeholder", "Frau / Herr / Dr."), width=95)
        self.salut_entry.pack(fill="x")

        fname_col = ctk.CTkFrame(contact_name_row, fg_color="transparent")
        fname_col.pack(side="left", fill="x", expand=True, padx=4)
        ctk.CTkLabel(fname_col, text=tr("customer_mgmt.fname_lbl", "Vorname:"), font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 2))
        self.fname_entry = ctk.CTkEntry(fname_col, placeholder_text=tr("customer_mgmt.fname_placeholder", "Vorname..."))
        self.fname_entry.pack(fill="x")

        lname_col = ctk.CTkFrame(contact_name_row, fg_color="transparent")
        lname_col.pack(side="left", fill="x", expand=True, padx=(4, 0))
        ctk.CTkLabel(lname_col, text=tr("customer_mgmt.lname_lbl", "Nachname:"), font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 2))
        self.lname_entry = ctk.CTkEntry(lname_col, placeholder_text=tr("customer_mgmt.lname_placeholder", "Nachname..."))
        self.lname_entry.pack(fill="x")

        # Address Row (Straße, PLZ, Ort)
        addr_row = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        addr_row.pack(fill="x", padx=15, pady=(0, 10))

        street_col = ctk.CTkFrame(addr_row, fg_color="transparent")
        street_col.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkLabel(street_col, text=tr("customer_mgmt.street_lbl", "🏠 Straße & Hausnr.:"), font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 2))
        self.street_entry = ctk.CTkEntry(street_col, placeholder_text=tr("customer_mgmt.street_placeholder", "z.B. Hauptstr. 10"))
        self.street_entry.pack(fill="x")

        zip_col = ctk.CTkFrame(addr_row, fg_color="transparent", width=90)
        zip_col.pack(side="left", fill="x", padx=4)
        ctk.CTkLabel(zip_col, text=tr("customer_mgmt.zip_lbl", "PLZ:"), font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 2))
        self.zip_entry = ctk.CTkEntry(zip_col, placeholder_text=tr("customer_mgmt.zip_placeholder", "12345"), width=80)
        self.zip_entry.pack(fill="x")

        city_col = ctk.CTkFrame(addr_row, fg_color="transparent")
        city_col.pack(side="left", fill="x", expand=True, padx=(4, 0))
        ctk.CTkLabel(city_col, text=tr("customer_mgmt.city_lbl", "Ort:"), font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 2))
        self.city_entry = ctk.CTkEntry(city_col, placeholder_text=tr("customer_mgmt.city_placeholder", "Ort..."))
        self.city_entry.pack(fill="x")

    def _build_phone_and_email_fields(self):
        from services.i18n_service import tr
        # Phone Numbers Section
        phone_box = ctk.CTkFrame(self.right_frame, fg_color=("gray90", "gray18"), corner_radius=6)
        phone_box.pack(fill="x", padx=15, pady=(0, 10))
        ctk.CTkLabel(phone_box, text=tr("customer_mgmt.phone_section_header", "📞 Telefonnummern (Cobra Export)"), font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(6, 4))

        pr1 = ctk.CTkFrame(phone_box, fg_color="transparent")
        pr1.pack(fill="x", padx=10, pady=(0, 4))

        p_main_col = ctk.CTkFrame(pr1, fg_color="transparent")
        p_main_col.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkLabel(p_main_col, text=tr("customer_mgmt.phone_main_lbl", "Telefon Hauptnr.:")).pack(anchor="w", pady=(0, 1))
        self.phone_m_entry = ctk.CTkEntry(p_main_col, placeholder_text=tr("customer_mgmt.phone_main_placeholder", "0711-..."))
        self.phone_m_entry.pack(fill="x")

        p_dir_col = ctk.CTkFrame(pr1, fg_color="transparent")
        p_dir_col.pack(side="left", fill="x", expand=True, padx=4)
        ctk.CTkLabel(p_dir_col, text=tr("customer_mgmt.phone_direct_lbl", "Telefon direkt:")).pack(anchor="w", pady=(0, 1))
        self.phone_dir_entry = ctk.CTkEntry(p_dir_col, placeholder_text=tr("customer_mgmt.phone_direct_placeholder", "Durchwahl..."))
        self.phone_dir_entry.pack(fill="x")

        p_priv_col = ctk.CTkFrame(pr1, fg_color="transparent")
        p_priv_col.pack(side="left", fill="x", expand=True, padx=(4, 0))
        ctk.CTkLabel(p_priv_col, text=tr("customer_mgmt.phone_priv_lbl", "Telefon privat:")).pack(anchor="w", pady=(0, 1))
        self.phone_priv_entry = ctk.CTkEntry(p_priv_col, placeholder_text=tr("customer_mgmt.phone_priv_placeholder", "Privat..."))
        self.phone_priv_entry.pack(fill="x")

        pr2 = ctk.CTkFrame(phone_box, fg_color="transparent")
        pr2.pack(fill="x", padx=10, pady=(0, 6))

        p2_col = ctk.CTkFrame(pr2, fg_color="transparent")
        p2_col.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkLabel(p2_col, text=tr("customer_mgmt.phone2_lbl", "Telefon 2:")).pack(anchor="w", pady=(0, 1))
        self.phone2_entry = ctk.CTkEntry(p2_col, placeholder_text=tr("customer_mgmt.phone2_placeholder", "Zweitnr...."))
        self.phone2_entry.pack(fill="x")

        p3_col = ctk.CTkFrame(pr2, fg_color="transparent")
        p3_col.pack(side="left", fill="x", expand=True, padx=4)
        ctk.CTkLabel(p3_col, text=tr("customer_mgmt.phone3_lbl", "Telefon 3:")).pack(anchor="w", pady=(0, 1))
        self.phone3_entry = ctk.CTkEntry(p3_col, placeholder_text=tr("customer_mgmt.phone3_placeholder", "Drittnr...."))
        self.phone3_entry.pack(fill="x")

        mob_col = ctk.CTkFrame(pr2, fg_color="transparent")
        mob_col.pack(side="left", fill="x", expand=True, padx=4)
        ctk.CTkLabel(mob_col, text=tr("customer_mgmt.mobile_lbl", "Mobil:")).pack(anchor="w", pady=(0, 1))
        self.mobile_entry = ctk.CTkEntry(mob_col, placeholder_text=tr("customer_mgmt.mobile_placeholder", "0171-..."))
        self.mobile_entry.pack(fill="x")

        mob_priv_col = ctk.CTkFrame(pr2, fg_color="transparent")
        mob_priv_col.pack(side="left", fill="x", expand=True, padx=(4, 0))
        ctk.CTkLabel(mob_priv_col, text=tr("customer_mgmt.mobile_priv_lbl", "Mobil privat:")).pack(anchor="w", pady=(0, 1))
        self.mobile_priv_entry = ctk.CTkEntry(mob_priv_col, placeholder_text=tr("customer_mgmt.mobile_priv_placeholder", "Mobil privat..."))
        self.mobile_priv_entry.pack(fill="x")

        # Additional E-Mail Addresses (E-Mail 2, E-Mail 3) Row
        pr3 = ctk.CTkFrame(phone_box, fg_color="transparent")
        pr3.pack(fill="x", padx=10, pady=(0, 6))

        em2_col = ctk.CTkFrame(pr3, fg_color="transparent")
        em2_col.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkLabel(em2_col, text=tr("customer_mgmt.email2_lbl", "✉ E-Mail 2:")).pack(anchor="w", pady=(0, 1))
        self.email2_entry = ctk.CTkEntry(em2_col, placeholder_text=tr("customer_mgmt.email2_placeholder", "zweit-email@praxis.de"))
        self.email2_entry.pack(fill="x")

        em3_col = ctk.CTkFrame(pr3, fg_color="transparent")
        em3_col.pack(side="left", fill="x", expand=True, padx=(4, 0))
        ctk.CTkLabel(em3_col, text=tr("customer_mgmt.email3_lbl", "✉ E-Mail 3:")).pack(anchor="w", pady=(0, 1))
        self.email3_entry = ctk.CTkEntry(em3_col, placeholder_text=tr("customer_mgmt.email3_placeholder", "dritt-email@praxis.de"))
        self.email3_entry.pack(fill="x")

    def _build_technical_details_fields(self):
        from services.i18n_service import tr
        # Practice Technical Details Row (Website, VM-Nummer, Instanznummer, DSC, DSCNEU)
        tech_row = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        tech_row.pack(fill="x", padx=15, pady=(0, 10))

        # Website Column
        web_col = ctk.CTkFrame(tech_row, fg_color="transparent")
        web_col.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkLabel(web_col, text=tr("customer_mgmt.website_lbl", "🌐 Webseite:"), font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 2))

        web_sub = ctk.CTkFrame(web_col, fg_color="transparent")
        web_sub.pack(fill="x")

        self.website_entry = ctk.CTkEntry(web_sub, placeholder_text=tr("customer_mgmt.website_placeholder", "https://praxis-beispiel.de"))
        self.website_entry.pack(side="left", fill="x", expand=True, padx=(0, 4))

        open_web_btn = ctk.CTkButton(
            web_sub,
            text=tr("customer_mgmt.open_website_btn", "🔗 Öffnen"),
            width=75,
            fg_color="gray30",
            hover_color="dodgerblue",
            command=self.open_website_in_browser,
        )
        open_web_btn.pack(side="right")

        # VM Number Column
        vm_col = ctk.CTkFrame(tech_row, fg_color="transparent", width=95)
        vm_col.pack(side="left", fill="x", padx=4)
        ctk.CTkLabel(vm_col, text=tr("customer_mgmt.vm_num_lbl", "🖥 VM-Nr.:"), font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 2))
        self.vm_entry = ctk.CTkEntry(vm_col, placeholder_text=tr("customer_mgmt.vm_placeholder", "104"), width=85)
        self.vm_entry.pack(fill="x")

        # Instance Number Column
        inst_col = ctk.CTkFrame(tech_row, fg_color="transparent", width=95)
        inst_col.pack(side="left", fill="x", padx=4)
        ctk.CTkLabel(inst_col, text=tr("customer_mgmt.instance_num_lbl", "🔢 Instanz-Nr.:"), font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 2))
        self.instance_entry = ctk.CTkEntry(inst_col, placeholder_text=tr("customer_mgmt.instance_placeholder", "1"), width=85)
        self.instance_entry.pack(fill="x")

        # DSC & DSCNEU Columns
        dsc_col = ctk.CTkFrame(tech_row, fg_color="transparent", width=100)
        dsc_col.pack(side="left", fill="x", padx=4)
        ctk.CTkLabel(dsc_col, text=tr("customer_mgmt.dsc_lbl", "🏷 DSC:"), font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 2))
        self.dsc_entry = ctk.CTkEntry(dsc_col, placeholder_text=tr("customer_mgmt.dsc_placeholder", "DSC..."), width=90)
        self.dsc_entry.pack(fill="x")

        dsc_neu_col = ctk.CTkFrame(tech_row, fg_color="transparent", width=100)
        dsc_neu_col.pack(side="left", fill="x", padx=(4, 0))
        ctk.CTkLabel(dsc_neu_col, text=tr("customer_mgmt.dsc_neu_lbl", "🏷 DSCNEU:"), font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 2))
        self.dsc_neu_entry = ctk.CTkEntry(dsc_neu_col, placeholder_text=tr("customer_mgmt.dsc_neu_placeholder", "DSCNEU..."), width=90)
        self.dsc_neu_entry.pack(fill="x")

    def _build_notes_and_rules_fields(self):
        from services.i18n_service import tr
        # Additional Contacts (Weitere Ansprechpartner) Box
        add_contact_box = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        add_contact_box.pack(fill="x", padx=15, pady=(0, 10))
        ctk.CTkLabel(add_contact_box, text=tr("customer_mgmt.additional_contacts_lbl", "👥 Weitere Ansprechpartner (1 Name pro Zeile):"), font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 2))
        self.additional_contacts_txt = ctk.CTkTextbox(add_contact_box, height=45)
        self.additional_contacts_txt.pack(fill="x")

        # General Notes row
        notes_row = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        notes_row.pack(fill="x", padx=15, pady=(0, 10))
        ctk.CTkLabel(notes_row, text=tr("customer_mgmt.general_notes_lbl", "📝 Allgemeine Notizen:")).pack(anchor="w", pady=(0, 2))
        self.notes_entry = ctk.CTkEntry(notes_row, placeholder_text=tr("customer_mgmt.notes_placeholder", "z.B. Erreichbarkeit, Wünsche..."))
        self.notes_entry.pack(fill="x")

        # VIP Checkbox
        self.vip_var = ctk.BooleanVar(value=False)
        self.vip_chk = ctk.CTkCheckBox(self.right_frame, text=tr("customer_mgmt.vip_customer_chk", "⭐ VIP-Kunde (erhöht den Dringlichkeits-Score um +30)"), variable=self.vip_var)
        self.vip_chk.pack(anchor="w", padx=15, pady=(5, 10))

        # Praxisspezifische KI-Regeln
        rules_box = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        rules_box.pack(fill="x", padx=15, pady=(0, 15))
        ctk.CTkLabel(
            rules_box,
            text=tr("customer_mgmt.custom_ai_rules_header", "⚡ Praxisspezifische KI-Regeln (haben VORRANG vor Basis-Regeln):"),
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", pady=(0, 2))
        ctk.CTkLabel(
            rules_box,
            text=tr("customer_mgmt.custom_ai_rules_sub", "1 Regel pro Zeile (z. B. 'Duzen erwünscht (Herr Schmidt)', 'Betreff mit [SCHMIDT] beginnen')"),
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray70"),
        ).pack(anchor="w", pady=(0, 4))
        self.custom_ai_rules_txt = ctk.CTkTextbox(rules_box, height=65)
        self.custom_ai_rules_txt.pack(fill="x")

    def _build_contacts_section(self):
        from services.i18n_service import tr
        # --- Multiple Contacts Header ---
        contacts_header_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        contacts_header_frame.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkLabel(contacts_header_frame, text=tr("customer_mgmt.contacts_header", "👥 Ansprechpartner & Kontakte"), font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        add_contact_btn = ctk.CTkButton(contacts_header_frame, text=tr("customer_mgmt.add_contact_btn", "+ Kontakt hinzufügen"), command=lambda: self.add_contact_row(), fg_color="gray30", width=140)
        add_contact_btn.pack(side="right")

        self.contacts_container = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.contacts_container.pack(fill="x", padx=15, pady=(0, 10))

        self.contact_rows: list[dict[str, Any]] = []
