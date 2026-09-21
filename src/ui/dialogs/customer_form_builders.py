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
from typing import TYPE_CHECKING, Any
from collections.abc import Callable

from constants import (
    BTN_WIDTH_COBRA_IMPORT,
    BTN_WIDTH_LG,
    BTN_WIDTH_OPEN_WEB,
    BTN_WIDTH_SORT_DIR,
    BTN_WIDTH_TAG_APPLY,
    COLOR_BTN_SECONDARY,
    COLOR_BTN_SECONDARY_HOVER,
    COLOR_CARD_BG_ALT,
    COLOR_MAGENTA_HOVER,
    COLOR_MUTED_LABEL,
    COLOR_POPOVER_BG,
    COLOR_PURPLE_HOVER,
    COLOR_SUCCESS,
    COLOR_SUCCESS_ALT,
    COLOR_WIKI_LINK,
    COMBO_WIDTH_SORT,
    CORNER_RADIUS_CARD,
    CORNER_RADIUS_MD,
    CORNER_RADIUS_NONE,
    CUSTOMER_LIST_PANEL_WIDTH,
    ENTRY_WIDTH_DSC,
    ENTRY_WIDTH_DSC_COL,
    ENTRY_WIDTH_SALUTATION,
    ENTRY_WIDTH_SALUTATION_COL,
    ENTRY_WIDTH_VM,
    ENTRY_WIDTH_VM_COL,
    ENTRY_WIDTH_ZIP,
    ENTRY_WIDTH_ZIP_COL,
    FONT_SIZE_BODY,
    FONT_SIZE_SM,
    FONT_SIZE_SUBTITLE,
    FONT_SIZE_TITLE,
    FONT_WEIGHT_BOLD,
    HEIGHT_HEADER_BAR,
    HEIGHT_SAVE_BAR,
    PAD_LG,
    PAD_MD,
    PAD_NONE,
    PAD_SM,
    PAD_TINY,
    PAD_XS,
    TEXTBOX_HEIGHT_RULES,
    TEXTBOX_HEIGHT_SM,
)

class CustomerFormBuilderMixin:
    """Baut die Widgets von CustomerManagementDialog auf. Nur zusammen mit
    CustomerManagementDialog (bzw. einer Klasse mit denselben self.right_frame /
    self.save_current_customer / ... Attributen und Methoden) nutzbar.
    """

    if TYPE_CHECKING:
        # Provided by BaseDialog once mixed into CustomerManagementDialog.
        # Declared, not defined: a real stub here would sit before BaseDialog in
        # the MRO and shadow the actual implementation at runtime.
        register_i18n: Callable[..., Any]

    def on_click_new_customer(self) -> None: ...
    def on_click_cobra_import(self) -> None: ...
    def _on_search_keyrelease(self, event: Any = None) -> None: ...
    def on_search_changed(self, event: Any = None) -> None: ...
    def on_sort_changed(self) -> None: ...
    def toggle_sort_direction(self) -> None: ...
    def save_current_customer(self) -> None: ...
    def open_website_in_browser(self) -> None: ...
    def add_contact_row(self, contact: Any = None) -> None: ...

    def _build_top_bar(self):
        from services.i18n_service import tr

        # Top Header
        top_bar = ctk.CTkFrame(self, height=HEIGHT_HEADER_BAR, corner_radius=CORNER_RADIUS_NONE)
        top_bar.pack(fill="x", side="top", padx=PAD_MD + PAD_XS, pady=(PAD_MD + PAD_XS, PAD_SM + 1))

        self.register_i18n(ctk.CTkLabel(top_bar, text=tr("customer_mgmt.header", "🏥 Registrierte Praxen"), font=ctk.CTkFont(size=FONT_SIZE_TITLE, weight=FONT_WEIGHT_BOLD)), "customer_mgmt.header", "🏥 Registrierte Praxen").pack(side="left", padx=PAD_MD + PAD_XS)

        new_btn = self.register_i18n(ctk.CTkButton(top_bar, text=tr("customer_mgmt.new_practice_btn", "+ Neue Praxis anlegen"), command=self.on_click_new_customer, fg_color=COLOR_SUCCESS_ALT, width=BTN_WIDTH_TAG_APPLY), "customer_mgmt.new_practice_btn", "+ Neue Praxis anlegen")
        new_btn.pack(side="right", padx=(PAD_SM + 1, PAD_MD + PAD_XS))

        cobra_btn = self.register_i18n(ctk.CTkButton(
            top_bar,
            text=tr("customer_mgmt.cobra_import_btn", "🐍 Cobra CRM Import..."),
            command=self.on_click_cobra_import,
            fg_color=COLOR_MAGENTA_HOVER,
            hover_color=COLOR_PURPLE_HOVER,
            width=BTN_WIDTH_COBRA_IMPORT,
        ), "customer_mgmt.cobra_import_btn", "🐍 Cobra CRM Import...")
        cobra_btn.pack(side="right", padx=PAD_SM + 1)

    def _build_customer_list_panel(self, body_frame: ctk.CTkFrame):
        from services.i18n_service import tr
        from enums import get_sort_criterion_display

        # Left list
        left_frame = ctk.CTkFrame(body_frame, width=CUSTOMER_LIST_PANEL_WIDTH)
        left_frame.pack(side="left", fill="y", padx=(PAD_NONE, PAD_SM + 1), pady=PAD_NONE)
        left_frame.pack_propagate(False)

        self.search_entry = self.register_i18n(ctk.CTkEntry(left_frame, placeholder_text=tr("customer_mgmt.search_placeholder", "🔍 Praxis / ID suchen...")), "customer_mgmt.search_placeholder", "🔍 Praxis / ID suchen...", attr="placeholder_text")
        self.search_entry.pack(fill="x", padx=PAD_MD + PAD_XS, pady=(PAD_MD + PAD_XS, PAD_SM))
        self.search_entry.bind("<KeyRelease>", self._on_search_keyrelease)

        # Sort Controls Bar
        sort_bar = ctk.CTkFrame(left_frame, fg_color="transparent")
        sort_bar.pack(fill="x", padx=PAD_MD + PAD_XS, pady=(PAD_NONE, PAD_SM + 1))

        self.sort_criterion_combo = ctk.CTkOptionMenu(
            sort_bar,
            values=[get_sort_criterion_display(c) for c in ("name", "id", "contact")],
            width=COMBO_WIDTH_SORT,
            command=lambda v: self.on_sort_changed(),
            font=ctk.CTkFont(size=FONT_SIZE_SM),
        )
        self.sort_criterion_combo.pack(side="left", padx=(PAD_NONE, PAD_SM))

        self.sort_asc_var = True
        self.sort_dir_btn = self.register_i18n(ctk.CTkButton(
            sort_bar,
            text=tr("customer_mgmt.sort_asc", "↑ Aufst."),
            width=BTN_WIDTH_SORT_DIR,
            fg_color=COLOR_BTN_SECONDARY,
            hover_color=COLOR_BTN_SECONDARY_HOVER,
            font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD),
            command=self.toggle_sort_direction,
        ), "customer_mgmt.sort_asc", "↑ Aufst.")
        self.sort_dir_btn.pack(side="right")

        self.list_scroll = ctk.CTkScrollableFrame(left_frame, fg_color="transparent")
        self.list_scroll.pack(fill="both", expand=True, padx=PAD_SM + 1, pady=PAD_SM + 1)

    def _build_customer_form_panel(self, body_frame: ctk.CTkFrame):
        from services.i18n_service import tr

        # Right panel container
        right_container = ctk.CTkFrame(body_frame, fg_color="transparent")
        right_container.pack(side="right", fill="both", expand=True, padx=(PAD_SM + 1, PAD_NONE), pady=PAD_NONE)

        # Fixed Save Button Bar at the bottom
        btn_row = ctk.CTkFrame(right_container, fg_color=COLOR_CARD_BG_ALT, height=HEIGHT_SAVE_BAR, corner_radius=CORNER_RADIUS_CARD)
        btn_row.pack(side="bottom", fill="x", padx=PAD_NONE, pady=(PAD_MD - PAD_XS, PAD_NONE))

        self.save_btn = self.register_i18n(ctk.CTkButton(btn_row, text=tr("customer_mgmt.save_practice_btn", "💾 Praxis Speichern"), command=self.save_current_customer, fg_color=COLOR_SUCCESS_ALT, width=BTN_WIDTH_TAG_APPLY), "customer_mgmt.save_practice_btn", "💾 Praxis Speichern")
        self.save_btn.pack(side="left", padx=PAD_MD + PAD_XS, pady=PAD_MD)

        self.status_lbl = ctk.CTkLabel(btn_row, text="", text_color=COLOR_SUCCESS, font=ctk.CTkFont(weight=FONT_WEIGHT_BOLD))
        self.status_lbl.pack(side="left", padx=PAD_MD + PAD_XS, pady=PAD_MD)

        # Right scrollable form for fields
        self.right_frame = ctk.CTkScrollableFrame(right_container)
        self.right_frame.pack(side="top", fill="both", expand=True, padx=PAD_NONE, pady=PAD_NONE)
        self._build_basic_info_fields()
        self._build_phone_and_email_fields()
        self._build_technical_details_fields()
        self._build_notes_and_rules_fields()
        self._build_contacts_section()

    def _build_basic_info_fields(self):
        from services.i18n_service import tr
        # Form fields
        self.form_title_lbl = self.register_i18n(ctk.CTkLabel(self.right_frame, text=tr("customer_mgmt.details_title", "Praxis-Details"), font=ctk.CTkFont(size=FONT_SIZE_TITLE, weight=FONT_WEIGHT_BOLD)), "customer_mgmt.details_title", "Praxis-Details")
        self.form_title_lbl.pack(anchor="w", padx=PAD_LG + 3, pady=(PAD_LG + 3, PAD_MD + PAD_XS))

        # Customer ID
        self.register_i18n(ctk.CTkLabel(self.right_frame, text=tr("customer_mgmt.cust_id_lbl", "Kunden-ID (z.B. CUST-1001):"), font=ctk.CTkFont(weight=FONT_WEIGHT_BOLD)), "customer_mgmt.cust_id_lbl", "Kunden-ID (z.B. CUST-1001):").pack(anchor="w", padx=PAD_LG + 3, pady=(PAD_SM + 1, PAD_XS))
        self.cust_id_entry = self.register_i18n(ctk.CTkEntry(self.right_frame, placeholder_text=tr("customer_mgmt.cust_id_placeholder", "CUST-...")), "customer_mgmt.cust_id_placeholder", "CUST-...", attr="placeholder_text")
        self.cust_id_entry.pack(fill="x", padx=PAD_LG + 3, pady=(PAD_NONE, PAD_MD + PAD_XS))

        # Practice Name & Old Name Row
        name_row = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        name_row.pack(fill="x", padx=PAD_LG + 3, pady=(PAD_NONE, PAD_MD + PAD_XS))

        name_left = ctk.CTkFrame(name_row, fg_color="transparent")
        name_left.pack(side="left", fill="x", expand=True, padx=(PAD_NONE, PAD_SM + 1))
        self.register_i18n(ctk.CTkLabel(name_left, text=tr("customer_mgmt.practice_name_lbl", "Praxisname *:"), font=ctk.CTkFont(weight=FONT_WEIGHT_BOLD)), "customer_mgmt.practice_name_lbl", "Praxisname *:").pack(anchor="w", pady=(PAD_NONE, PAD_XS))
        self.name_entry = self.register_i18n(ctk.CTkEntry(name_left, placeholder_text=tr("customer_mgmt.practice_name_placeholder", "z.B. Hausarztpraxis Dr. Med. Weber")), "customer_mgmt.practice_name_placeholder", "z.B. Hausarztpraxis Dr. Med. Weber", attr="placeholder_text")
        self.name_entry.pack(fill="x")

        name_right = ctk.CTkFrame(name_row, fg_color="transparent")
        name_right.pack(side="right", fill="x", expand=True, padx=(PAD_SM + 1, PAD_NONE))
        self.register_i18n(ctk.CTkLabel(name_right, text=tr("customer_mgmt.practice_name_old_lbl", "Praxisname (Alt):"), font=ctk.CTkFont(weight=FONT_WEIGHT_BOLD)), "customer_mgmt.practice_name_old_lbl", "Praxisname (Alt):").pack(anchor="w", pady=(PAD_NONE, PAD_XS))
        self.name_old_entry = self.register_i18n(ctk.CTkEntry(name_right, placeholder_text=tr("customer_mgmt.practice_name_old_placeholder", "z.B. Ehem. Praxis Dr. Alt")), "customer_mgmt.practice_name_old_placeholder", "z.B. Ehem. Praxis Dr. Alt", attr="placeholder_text")
        self.name_old_entry.pack(fill="x")

        # Hauptansprechpartner (Anrede, Vorname, Nachname) Row
        contact_name_row = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        contact_name_row.pack(fill="x", padx=PAD_LG + 3, pady=(PAD_NONE, PAD_MD + PAD_XS))

        salut_col = ctk.CTkFrame(contact_name_row, fg_color="transparent", width=ENTRY_WIDTH_SALUTATION_COL)
        salut_col.pack(side="left", fill="x", padx=(PAD_NONE, PAD_SM))
        self.register_i18n(ctk.CTkLabel(salut_col, text=tr("customer_mgmt.salut_lbl", "Anrede:"), font=ctk.CTkFont(weight=FONT_WEIGHT_BOLD)), "customer_mgmt.salut_lbl", "Anrede:").pack(anchor="w", pady=(PAD_NONE, PAD_XS))
        self.salut_entry = self.register_i18n(ctk.CTkEntry(salut_col, placeholder_text=tr("customer_mgmt.salut_placeholder", "Frau / Herr / Dr."), width=ENTRY_WIDTH_SALUTATION), "customer_mgmt.salut_placeholder", "Frau / Herr / Dr.", attr="placeholder_text")
        self.salut_entry.pack(fill="x")

        fname_col = ctk.CTkFrame(contact_name_row, fg_color="transparent")
        fname_col.pack(side="left", fill="x", expand=True, padx=PAD_SM)
        self.register_i18n(ctk.CTkLabel(fname_col, text=tr("customer_mgmt.fname_lbl", "Vorname:"), font=ctk.CTkFont(weight=FONT_WEIGHT_BOLD)), "customer_mgmt.fname_lbl", "Vorname:").pack(anchor="w", pady=(PAD_NONE, PAD_XS))
        self.fname_entry = self.register_i18n(ctk.CTkEntry(fname_col, placeholder_text=tr("customer_mgmt.fname_placeholder", "Vorname...")), "customer_mgmt.fname_placeholder", "Vorname...", attr="placeholder_text")
        self.fname_entry.pack(fill="x")

        lname_col = ctk.CTkFrame(contact_name_row, fg_color="transparent")
        lname_col.pack(side="left", fill="x", expand=True, padx=(PAD_SM, PAD_NONE))
        self.register_i18n(ctk.CTkLabel(lname_col, text=tr("customer_mgmt.lname_lbl", "Nachname:"), font=ctk.CTkFont(weight=FONT_WEIGHT_BOLD)), "customer_mgmt.lname_lbl", "Nachname:").pack(anchor="w", pady=(PAD_NONE, PAD_XS))
        self.lname_entry = self.register_i18n(ctk.CTkEntry(lname_col, placeholder_text=tr("customer_mgmt.lname_placeholder", "Nachname...")), "customer_mgmt.lname_placeholder", "Nachname...", attr="placeholder_text")
        self.lname_entry.pack(fill="x")

        # Address Row (Straße, PLZ, Ort)
        addr_row = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        addr_row.pack(fill="x", padx=PAD_LG + 3, pady=(PAD_NONE, PAD_MD + PAD_XS))

        street_col = ctk.CTkFrame(addr_row, fg_color="transparent")
        street_col.pack(side="left", fill="x", expand=True, padx=(PAD_NONE, PAD_SM))
        self.register_i18n(ctk.CTkLabel(street_col, text=tr("customer_mgmt.street_lbl", "🏠 Straße & Hausnr.:"), font=ctk.CTkFont(weight=FONT_WEIGHT_BOLD)), "customer_mgmt.street_lbl", "🏠 Straße & Hausnr.:").pack(anchor="w", pady=(PAD_NONE, PAD_XS))
        self.street_entry = self.register_i18n(ctk.CTkEntry(street_col, placeholder_text=tr("customer_mgmt.street_placeholder", "z.B. Hauptstr. 10")), "customer_mgmt.street_placeholder", "z.B. Hauptstr. 10", attr="placeholder_text")
        self.street_entry.pack(fill="x")

        zip_col = ctk.CTkFrame(addr_row, fg_color="transparent", width=ENTRY_WIDTH_ZIP_COL)
        zip_col.pack(side="left", fill="x", padx=PAD_SM)
        self.register_i18n(ctk.CTkLabel(zip_col, text=tr("customer_mgmt.zip_lbl", "PLZ:"), font=ctk.CTkFont(weight=FONT_WEIGHT_BOLD)), "customer_mgmt.zip_lbl", "PLZ:").pack(anchor="w", pady=(PAD_NONE, PAD_XS))
        self.zip_entry = self.register_i18n(ctk.CTkEntry(zip_col, placeholder_text=tr("customer_mgmt.zip_placeholder", "12345"), width=ENTRY_WIDTH_ZIP), "customer_mgmt.zip_placeholder", "12345", attr="placeholder_text")
        self.zip_entry.pack(fill="x")

        city_col = ctk.CTkFrame(addr_row, fg_color="transparent")
        city_col.pack(side="left", fill="x", expand=True, padx=(PAD_SM, PAD_NONE))
        self.register_i18n(ctk.CTkLabel(city_col, text=tr("customer_mgmt.city_lbl", "Ort:"), font=ctk.CTkFont(weight=FONT_WEIGHT_BOLD)), "customer_mgmt.city_lbl", "Ort:").pack(anchor="w", pady=(PAD_NONE, PAD_XS))
        self.city_entry = self.register_i18n(ctk.CTkEntry(city_col, placeholder_text=tr("customer_mgmt.city_placeholder", "Ort...")), "customer_mgmt.city_placeholder", "Ort...", attr="placeholder_text")
        self.city_entry.pack(fill="x")

    def _build_phone_and_email_fields(self):
        from services.i18n_service import tr
        # Phone Numbers Section
        phone_box = ctk.CTkFrame(self.right_frame, fg_color=COLOR_POPOVER_BG, corner_radius=CORNER_RADIUS_MD)
        phone_box.pack(fill="x", padx=PAD_LG + 3, pady=(PAD_NONE, PAD_MD + PAD_XS))
        self.register_i18n(ctk.CTkLabel(phone_box, text=tr("customer_mgmt.phone_section_header", "📞 Telefonnummern (Cobra Export)"), font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD)), "customer_mgmt.phone_section_header", "📞 Telefonnummern (Cobra Export)").pack(anchor="w", padx=PAD_MD + PAD_XS, pady=(PAD_MD - PAD_XS, PAD_SM))

        pr1 = ctk.CTkFrame(phone_box, fg_color="transparent")
        pr1.pack(fill="x", padx=PAD_MD + PAD_XS, pady=(PAD_NONE, PAD_SM))

        p_main_col = ctk.CTkFrame(pr1, fg_color="transparent")
        p_main_col.pack(side="left", fill="x", expand=True, padx=(PAD_NONE, PAD_SM))
        self.register_i18n(ctk.CTkLabel(p_main_col, text=tr("customer_mgmt.phone_main_lbl", "Telefon Hauptnr.:")), "customer_mgmt.phone_main_lbl", "Telefon Hauptnr.:").pack(anchor="w", pady=(PAD_NONE, PAD_TINY))
        self.phone_m_entry = self.register_i18n(ctk.CTkEntry(p_main_col, placeholder_text=tr("customer_mgmt.phone_main_placeholder", "0711-...")), "customer_mgmt.phone_main_placeholder", "0711-...", attr="placeholder_text")
        self.phone_m_entry.pack(fill="x")

        p_dir_col = ctk.CTkFrame(pr1, fg_color="transparent")
        p_dir_col.pack(side="left", fill="x", expand=True, padx=PAD_SM)
        self.register_i18n(ctk.CTkLabel(p_dir_col, text=tr("customer_mgmt.phone_direct_lbl", "Telefon direkt:")), "customer_mgmt.phone_direct_lbl", "Telefon direkt:").pack(anchor="w", pady=(PAD_NONE, PAD_TINY))
        self.phone_dir_entry = self.register_i18n(ctk.CTkEntry(p_dir_col, placeholder_text=tr("customer_mgmt.phone_direct_placeholder", "Durchwahl...")), "customer_mgmt.phone_direct_placeholder", "Durchwahl...", attr="placeholder_text")
        self.phone_dir_entry.pack(fill="x")

        p_priv_col = ctk.CTkFrame(pr1, fg_color="transparent")
        p_priv_col.pack(side="left", fill="x", expand=True, padx=(PAD_SM, PAD_NONE))
        self.register_i18n(ctk.CTkLabel(p_priv_col, text=tr("customer_mgmt.phone_priv_lbl", "Telefon privat:")), "customer_mgmt.phone_priv_lbl", "Telefon privat:").pack(anchor="w", pady=(PAD_NONE, PAD_TINY))
        self.phone_priv_entry = self.register_i18n(ctk.CTkEntry(p_priv_col, placeholder_text=tr("customer_mgmt.phone_priv_placeholder", "Privat...")), "customer_mgmt.phone_priv_placeholder", "Privat...", attr="placeholder_text")
        self.phone_priv_entry.pack(fill="x")

        pr2 = ctk.CTkFrame(phone_box, fg_color="transparent")
        pr2.pack(fill="x", padx=PAD_MD + PAD_XS, pady=(PAD_NONE, PAD_MD - PAD_XS))

        p2_col = ctk.CTkFrame(pr2, fg_color="transparent")
        p2_col.pack(side="left", fill="x", expand=True, padx=(PAD_NONE, PAD_SM))
        self.register_i18n(ctk.CTkLabel(p2_col, text=tr("customer_mgmt.phone2_lbl", "Telefon 2:")), "customer_mgmt.phone2_lbl", "Telefon 2:").pack(anchor="w", pady=(PAD_NONE, PAD_TINY))
        self.phone2_entry = self.register_i18n(ctk.CTkEntry(p2_col, placeholder_text=tr("customer_mgmt.phone2_placeholder", "Zweitnr....")), "customer_mgmt.phone2_placeholder", "Zweitnr....", attr="placeholder_text")
        self.phone2_entry.pack(fill="x")

        p3_col = ctk.CTkFrame(pr2, fg_color="transparent")
        p3_col.pack(side="left", fill="x", expand=True, padx=PAD_SM)
        self.register_i18n(ctk.CTkLabel(p3_col, text=tr("customer_mgmt.phone3_lbl", "Telefon 3:")), "customer_mgmt.phone3_lbl", "Telefon 3:").pack(anchor="w", pady=(PAD_NONE, PAD_TINY))
        self.phone3_entry = self.register_i18n(ctk.CTkEntry(p3_col, placeholder_text=tr("customer_mgmt.phone3_placeholder", "Drittnr....")), "customer_mgmt.phone3_placeholder", "Drittnr....", attr="placeholder_text")
        self.phone3_entry.pack(fill="x")

        mob_col = ctk.CTkFrame(pr2, fg_color="transparent")
        mob_col.pack(side="left", fill="x", expand=True, padx=PAD_SM)
        self.register_i18n(ctk.CTkLabel(mob_col, text=tr("customer_mgmt.mobile_lbl", "Mobil:")), "customer_mgmt.mobile_lbl", "Mobil:").pack(anchor="w", pady=(PAD_NONE, PAD_TINY))
        self.mobile_entry = self.register_i18n(ctk.CTkEntry(mob_col, placeholder_text=tr("customer_mgmt.mobile_placeholder", "0171-...")), "customer_mgmt.mobile_placeholder", "0171-...", attr="placeholder_text")
        self.mobile_entry.pack(fill="x")

        mob_priv_col = ctk.CTkFrame(pr2, fg_color="transparent")
        mob_priv_col.pack(side="left", fill="x", expand=True, padx=(PAD_SM, PAD_NONE))
        self.register_i18n(ctk.CTkLabel(mob_priv_col, text=tr("customer_mgmt.mobile_priv_lbl", "Mobil privat:")), "customer_mgmt.mobile_priv_lbl", "Mobil privat:").pack(anchor="w", pady=(PAD_NONE, PAD_TINY))
        self.mobile_priv_entry = self.register_i18n(ctk.CTkEntry(mob_priv_col, placeholder_text=tr("customer_mgmt.mobile_priv_placeholder", "Mobil privat...")), "customer_mgmt.mobile_priv_placeholder", "Mobil privat...", attr="placeholder_text")
        self.mobile_priv_entry.pack(fill="x")

        # Additional E-Mail Addresses (E-Mail 2, E-Mail 3) Row
        pr3 = ctk.CTkFrame(phone_box, fg_color="transparent")
        pr3.pack(fill="x", padx=PAD_MD + PAD_XS, pady=(PAD_NONE, PAD_MD - PAD_XS))

        em2_col = ctk.CTkFrame(pr3, fg_color="transparent")
        em2_col.pack(side="left", fill="x", expand=True, padx=(PAD_NONE, PAD_SM))
        self.register_i18n(ctk.CTkLabel(em2_col, text=tr("customer_mgmt.email2_lbl", "✉ E-Mail 2:")), "customer_mgmt.email2_lbl", "✉ E-Mail 2:").pack(anchor="w", pady=(PAD_NONE, PAD_TINY))
        self.email2_entry = self.register_i18n(ctk.CTkEntry(em2_col, placeholder_text=tr("customer_mgmt.email2_placeholder", "zweit-email@praxis.de")), "customer_mgmt.email2_placeholder", "zweit-email@praxis.de", attr="placeholder_text")
        self.email2_entry.pack(fill="x")

        em3_col = ctk.CTkFrame(pr3, fg_color="transparent")
        em3_col.pack(side="left", fill="x", expand=True, padx=(PAD_SM, PAD_NONE))
        self.register_i18n(ctk.CTkLabel(em3_col, text=tr("customer_mgmt.email3_lbl", "✉ E-Mail 3:")), "customer_mgmt.email3_lbl", "✉ E-Mail 3:").pack(anchor="w", pady=(PAD_NONE, PAD_TINY))
        self.email3_entry = self.register_i18n(ctk.CTkEntry(em3_col, placeholder_text=tr("customer_mgmt.email3_placeholder", "dritt-email@praxis.de")), "customer_mgmt.email3_placeholder", "dritt-email@praxis.de", attr="placeholder_text")
        self.email3_entry.pack(fill="x")

    def _build_technical_details_fields(self):
        from services.i18n_service import tr
        # Practice Technical Details Row (Website, VM-Nummer, Instanznummer, DSC, DSCNEU)
        tech_row = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        tech_row.pack(fill="x", padx=PAD_LG + 3, pady=(PAD_NONE, PAD_MD + PAD_XS))

        # Website Column
        web_col = ctk.CTkFrame(tech_row, fg_color="transparent")
        web_col.pack(side="left", fill="x", expand=True, padx=(PAD_NONE, PAD_SM))
        self.register_i18n(ctk.CTkLabel(web_col, text=tr("customer_mgmt.website_lbl", "🌐 Webseite:"), font=ctk.CTkFont(weight=FONT_WEIGHT_BOLD)), "customer_mgmt.website_lbl", "🌐 Webseite:").pack(anchor="w", pady=(PAD_NONE, PAD_XS))

        web_sub = ctk.CTkFrame(web_col, fg_color="transparent")
        web_sub.pack(fill="x")

        self.website_entry = self.register_i18n(ctk.CTkEntry(web_sub, placeholder_text=tr("customer_mgmt.website_placeholder", "https://praxis-beispiel.de")), "customer_mgmt.website_placeholder", "https://praxis-beispiel.de", attr="placeholder_text")
        self.website_entry.pack(side="left", fill="x", expand=True, padx=(PAD_NONE, PAD_SM))

        open_web_btn = self.register_i18n(ctk.CTkButton(
            web_sub,
            text=tr("customer_mgmt.open_website_btn", "🔗 Öffnen"),
            width=BTN_WIDTH_OPEN_WEB,
            fg_color=COLOR_BTN_SECONDARY,
            hover_color=COLOR_WIKI_LINK,
            command=self.open_website_in_browser,
        ), "customer_mgmt.open_website_btn", "🔗 Öffnen")
        open_web_btn.pack(side="right")

        # VM Number Column
        vm_col = ctk.CTkFrame(tech_row, fg_color="transparent", width=ENTRY_WIDTH_VM_COL)
        vm_col.pack(side="left", fill="x", padx=PAD_SM)
        self.register_i18n(ctk.CTkLabel(vm_col, text=tr("customer_mgmt.vm_num_lbl", "🖥 VM-Nr.:"), font=ctk.CTkFont(weight=FONT_WEIGHT_BOLD)), "customer_mgmt.vm_num_lbl", "🖥 VM-Nr.:").pack(anchor="w", pady=(PAD_NONE, PAD_XS))
        self.vm_entry = self.register_i18n(ctk.CTkEntry(vm_col, placeholder_text=tr("customer_mgmt.vm_placeholder", "104"), width=ENTRY_WIDTH_VM), "customer_mgmt.vm_placeholder", "104", attr="placeholder_text")
        self.vm_entry.pack(fill="x")

        # Instance Number Column
        inst_col = ctk.CTkFrame(tech_row, fg_color="transparent", width=ENTRY_WIDTH_VM_COL)
        inst_col.pack(side="left", fill="x", padx=PAD_SM)
        self.register_i18n(ctk.CTkLabel(inst_col, text=tr("customer_mgmt.instance_num_lbl", "🔢 Instanz-Nr.:"), font=ctk.CTkFont(weight=FONT_WEIGHT_BOLD)), "customer_mgmt.instance_num_lbl", "🔢 Instanz-Nr.:").pack(anchor="w", pady=(PAD_NONE, PAD_XS))
        self.instance_entry = self.register_i18n(ctk.CTkEntry(inst_col, placeholder_text=tr("customer_mgmt.instance_placeholder", "1"), width=ENTRY_WIDTH_VM), "customer_mgmt.instance_placeholder", "1", attr="placeholder_text")
        self.instance_entry.pack(fill="x")

        # DSC & DSCNEU Columns
        dsc_col = ctk.CTkFrame(tech_row, fg_color="transparent", width=ENTRY_WIDTH_DSC_COL)
        dsc_col.pack(side="left", fill="x", padx=PAD_SM)
        self.register_i18n(ctk.CTkLabel(dsc_col, text=tr("customer_mgmt.dsc_lbl", "🏷 DSC:"), font=ctk.CTkFont(weight=FONT_WEIGHT_BOLD)), "customer_mgmt.dsc_lbl", "🏷 DSC:").pack(anchor="w", pady=(PAD_NONE, PAD_XS))
        self.dsc_entry = self.register_i18n(ctk.CTkEntry(dsc_col, placeholder_text=tr("customer_mgmt.dsc_placeholder", "DSC..."), width=ENTRY_WIDTH_DSC), "customer_mgmt.dsc_placeholder", "DSC...", attr="placeholder_text")
        self.dsc_entry.pack(fill="x")

        dsc_neu_col = ctk.CTkFrame(tech_row, fg_color="transparent", width=ENTRY_WIDTH_DSC_COL)
        dsc_neu_col.pack(side="left", fill="x", padx=(PAD_SM, PAD_NONE))
        self.register_i18n(ctk.CTkLabel(dsc_neu_col, text=tr("customer_mgmt.dsc_neu_lbl", "🏷 DSCNEU:"), font=ctk.CTkFont(weight=FONT_WEIGHT_BOLD)), "customer_mgmt.dsc_neu_lbl", "🏷 DSCNEU:").pack(anchor="w", pady=(PAD_NONE, PAD_XS))
        self.dsc_neu_entry = self.register_i18n(ctk.CTkEntry(dsc_neu_col, placeholder_text=tr("customer_mgmt.dsc_neu_placeholder", "DSCNEU..."), width=ENTRY_WIDTH_DSC), "customer_mgmt.dsc_neu_placeholder", "DSCNEU...", attr="placeholder_text")
        self.dsc_neu_entry.pack(fill="x")

    def _build_notes_and_rules_fields(self):
        from services.i18n_service import tr
        # Additional Contacts (Weitere Ansprechpartner) Box
        add_contact_box = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        add_contact_box.pack(fill="x", padx=PAD_LG + 3, pady=(PAD_NONE, PAD_MD + PAD_XS))
        self.register_i18n(ctk.CTkLabel(add_contact_box, text=tr("customer_mgmt.additional_contacts_lbl", "👥 Weitere Ansprechpartner (1 Name pro Zeile):"), font=ctk.CTkFont(weight=FONT_WEIGHT_BOLD)), "customer_mgmt.additional_contacts_lbl", "👥 Weitere Ansprechpartner (1 Name pro Zeile):").pack(anchor="w", pady=(PAD_NONE, PAD_XS))
        self.additional_contacts_txt = ctk.CTkTextbox(add_contact_box, height=TEXTBOX_HEIGHT_SM)
        self.additional_contacts_txt.pack(fill="x")

        # General Notes row
        notes_row = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        notes_row.pack(fill="x", padx=PAD_LG + 3, pady=(PAD_NONE, PAD_MD + PAD_XS))
        self.register_i18n(ctk.CTkLabel(notes_row, text=tr("customer_mgmt.general_notes_lbl", "📝 Allgemeine Notizen:")), "customer_mgmt.general_notes_lbl", "📝 Allgemeine Notizen:").pack(anchor="w", pady=(PAD_NONE, PAD_XS))
        self.notes_entry = self.register_i18n(ctk.CTkEntry(notes_row, placeholder_text=tr("customer_mgmt.notes_placeholder", "z.B. Erreichbarkeit, Wünsche...")), "customer_mgmt.notes_placeholder", "z.B. Erreichbarkeit, Wünsche...", attr="placeholder_text")
        self.notes_entry.pack(fill="x")

        # VIP Checkbox
        self.vip_var = ctk.BooleanVar(value=False)
        self.vip_chk = self.register_i18n(ctk.CTkCheckBox(self.right_frame, text=tr("customer_mgmt.vip_customer_chk", "⭐ VIP-Kunde (erhöht den Dringlichkeits-Score um +30)"), variable=self.vip_var), "customer_mgmt.vip_customer_chk", "⭐ VIP-Kunde (erhöht den Dringlichkeits-Score um +30)")
        self.vip_chk.pack(anchor="w", padx=PAD_LG + 3, pady=(PAD_SM + 1, PAD_MD + PAD_XS))

        # Praxisspezifische KI-Regeln
        rules_box = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        rules_box.pack(fill="x", padx=PAD_LG + 3, pady=(PAD_NONE, PAD_LG + 3))
        self.register_i18n(ctk.CTkLabel(
            rules_box,
            text=tr("customer_mgmt.custom_ai_rules_header", "⚡ Praxisspezifische KI-Regeln (haben VORRANG vor Basis-Regeln):"),
            font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
        ), "customer_mgmt.custom_ai_rules_header", "⚡ Praxisspezifische KI-Regeln (haben VORRANG vor Basis-Regeln):").pack(anchor="w", pady=(PAD_NONE, PAD_XS))
        self.register_i18n(ctk.CTkLabel(
            rules_box,
            text=tr("customer_mgmt.custom_ai_rules_sub", "1 Regel pro Zeile (z. B. 'Duzen erwünscht (Herr Schmidt)', 'Betreff mit [SCHMIDT] beginnen')"),
            font=ctk.CTkFont(size=FONT_SIZE_SM),
            text_color=COLOR_MUTED_LABEL,
        ), "customer_mgmt.custom_ai_rules_sub", "1 Regel pro Zeile (z. B. 'Duzen erwünscht (Herr Schmidt)', 'Betreff mit [SCHMIDT] beginnen')").pack(anchor="w", pady=(PAD_NONE, PAD_SM))
        self.custom_ai_rules_txt = ctk.CTkTextbox(rules_box, height=TEXTBOX_HEIGHT_RULES)
        self.custom_ai_rules_txt.pack(fill="x")

    def _build_contacts_section(self):
        from services.i18n_service import tr
        # --- Multiple Contacts Header ---
        contacts_header_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        contacts_header_frame.pack(fill="x", padx=PAD_LG + 3, pady=(PAD_MD + PAD_XS, PAD_SM + 1))

        self.register_i18n(ctk.CTkLabel(contacts_header_frame, text=tr("customer_mgmt.contacts_header", "👥 Ansprechpartner & Kontakte"), font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight=FONT_WEIGHT_BOLD)), "customer_mgmt.contacts_header", "👥 Ansprechpartner & Kontakte").pack(side="left")
        add_contact_btn = self.register_i18n(ctk.CTkButton(contacts_header_frame, text=tr("customer_mgmt.add_contact_btn", "+ Kontakt hinzufügen"), command=lambda: self.add_contact_row(), fg_color=COLOR_BTN_SECONDARY, width=BTN_WIDTH_LG), "customer_mgmt.add_contact_btn", "+ Kontakt hinzufügen")
        add_contact_btn.pack(side="right")

        self.contacts_container = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.contacts_container.pack(fill="x", padx=PAD_LG + 3, pady=(PAD_NONE, PAD_MD + PAD_XS))

        self.contact_rows: list[dict[str, Any]] = []
