"""Dialog zum nachträglichen Wechseln der Praxis eines bestehenden Falls.

Der Dialog bietet:
  - SearchableCombobox über alle bekannten Kunden (analog NewCaseDialog)
  - Button zum Schnellanlegen einer neuen Praxis
  - Optionales Freitextfeld für eine Timeline-Notiz
  - Explizite Bestätigung via ConfirmDialog bevor die Änderung angewendet wird
"""
import customtkinter as ctk
from collections.abc import Callable
from typing import Any

from models.case import Case, CaseCustomer
from models.customer import Customer
from services.customer_service import CustomerService
from services.i18n_service import tr
from ui.dialogs.base_dialog import BaseDialog
from constants import (
    BTN_WIDTH_ACTION,
    BTN_WIDTH_CLOSE,
    BTN_WIDTH_MD,
    COLOR_BTN_CANCEL,
    COLOR_DANGER,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_SUCCESS,
    COMBO_DEFAULT_WIDTH,
    DIALOG_DIMENSIONS,
    DIALOG_TITLES,
    FONT_SIZE_BODY,
    FONT_WEIGHT_BOLD,
    PAD_GAP,
    PAD_LG,
    PAD_MD,
    PAD_NONE,
    PAD_SM,
    PAD_TINY,
    PAD_XS,
    TEXTBOX_HEIGHT_INITIAL_NOTE,
)


class ChangePracticeDialog(BaseDialog):
    """Ermöglicht das nachträgliche Ändern der Praxis eines Falls.

    on_practice_changed wird aufgerufen mit (new_customer: CaseCustomer, note: str)
    wenn der Nutzer bestätigt hat.
    """

    def __init__(
        self,
        parent,
        case: Case,
        customers: list[Customer],
        on_practice_changed: Callable[[CaseCustomer, str], None],
        on_customer_added: Callable[[Customer], None] | None = None,
    ):
        super().__init__(parent)
        self.case = case
        self.customers = list(customers)
        self.on_practice_changed = on_practice_changed
        self.on_customer_added = on_customer_added
        self._customer_by_display: dict[str, Customer] = {}

        w, h = DIALOG_DIMENSIONS["change_practice"]
        self.setup_window(
            parent,
            DIALOG_TITLES["change_practice"],
            (w, h),
            resizable=False,
            title_factory=lambda: DIALOG_TITLES["change_practice"],
        )

        self._build_ui(w)
        self.set_default_action(self.on_confirm)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self, dialog_width: int) -> None:
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_LG)

        # Header
        ctk.CTkLabel(
            main,
            text=tr("change_practice.header", "Neue Praxis für diesen Fall auswählen:"),
            font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
            anchor="w",
        ).pack(fill="x", pady=(PAD_NONE, PAD_TINY))

        # Current practice info
        current_name = self.case.customer.practice_name or self.case.customer.customer_id
        ctk.CTkLabel(
            main,
            text=tr("change_practice.current", "Aktuelle Praxis: {name}", name=current_name),
            anchor="w",
            text_color=("gray50", "gray60"),
        ).pack(fill="x", pady=(PAD_NONE, PAD_SM))

        # Customer search row
        cust_row = ctk.CTkFrame(main, fg_color="transparent")
        cust_row.pack(fill="x", pady=(PAD_NONE, PAD_GAP))

        from ui.widgets.searchable_combobox import SearchableCombobox
        self.customer_combo = SearchableCombobox(
            cust_row,
            values=[],
            width=COMBO_DEFAULT_WIDTH,
            summary_provider=self._customer_match_summary,
        )
        self.customer_combo.pack(side="left", fill="x", expand=True, padx=(PAD_NONE, PAD_SM))

        ctk.CTkButton(
            cust_row,
            text=tr("new_case_dialog.add_practice_btn", "+ Neue Praxis"),
            command=self._open_quick_add_customer,
            fg_color=COLOR_SUCCESS,
            width=BTN_WIDTH_CLOSE,
        ).pack(side="right")

        self._refresh_customer_combo()

        # Optional note
        ctk.CTkLabel(
            main,
            text=tr("change_practice.note_label", "Notiz zum Praxiswechsel (optional):"),
            font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
            anchor="w",
        ).pack(fill="x", pady=(PAD_SM, PAD_TINY))

        self.note_textbox = ctk.CTkTextbox(main, height=TEXTBOX_HEIGHT_INITIAL_NOTE)
        self.note_textbox.pack(fill="x", pady=(PAD_NONE, PAD_MD))

        # Error label
        self.error_label = ctk.CTkLabel(main, text="", text_color=COLOR_DANGER)
        self.error_label.pack(anchor="w", pady=(PAD_NONE, PAD_XS))

        # Buttons
        btn_row = ctk.CTkFrame(main, fg_color="transparent")
        btn_row.pack(fill="x", side="bottom", pady=(PAD_SM, PAD_NONE))

        ctk.CTkButton(
            btn_row,
            text=tr("common.cancel", "Abbrechen"),
            fg_color=COLOR_BTN_CANCEL,
            width=BTN_WIDTH_MD,
            command=self.request_close,
        ).pack(side="left")

        ctk.CTkButton(
            btn_row,
            text=tr("change_practice.confirm_btn", "Praxis wechseln"),
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            width=BTN_WIDTH_ACTION,
            command=self.on_confirm,
        ).pack(side="right")

    # ------------------------------------------------------------------
    # Customer combo helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _customer_display_name(cust: Customer) -> str:
        return f"{cust.practice_name} ({cust.customer_id})"

    @staticmethod
    def _customer_search_fields(cust: Customer) -> list[str]:
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
    def _customer_search_text(cls, cust: Customer) -> str:
        return " ".join(cls._customer_search_fields(cust))

    def _customer_match_summary(self, display_value: str, query: str) -> str | None:
        cust = self._customer_by_display.get(display_value)
        if cust is None:
            return None
        return CustomerService.summarize_matching_words(
            self._customer_search_fields(cust), query, exclude_text=display_value
        )

    def _refresh_customer_combo(self) -> None:
        self._customer_by_display = {self._customer_display_name(c): c for c in self.customers}
        names = list(self._customer_by_display)
        if not names:
            names = [tr("new_case_dialog.no_customers", "Keine Kunden")]
        self.customer_combo.set_search_index({
            name: self._customer_search_text(c)
            for name, c in self._customer_by_display.items()
        })
        self.customer_combo.set_values(names)

    # ------------------------------------------------------------------
    # Quick-add customer
    # ------------------------------------------------------------------

    def _open_quick_add_customer(self) -> None:
        from ui.dialogs.new_case_dialog import QuickAddCustomerDialog
        QuickAddCustomerDialog(self, on_customer_created=self._on_quick_customer_created)

    def _on_quick_customer_created(self, new_cust: Customer) -> None:
        self.customers.append(new_cust)
        if self.on_customer_added:
            self.on_customer_added(new_cust)
        self._refresh_customer_combo()
        target_name = self._customer_display_name(new_cust)
        self.customer_combo.set_selected(target_name)

    # ------------------------------------------------------------------
    # Confirm
    # ------------------------------------------------------------------

    def on_confirm(self) -> None:
        selected = self.customer_combo.get().strip()
        chosen_customer = self._customer_by_display.get(selected)

        if chosen_customer is None:
            self.error_label.configure(
                text=tr("change_practice.no_customer", "Bitte eine Praxis auswählen.")
            )
            return

        # Explicit confirmation dialog
        from ui.dialogs.confirm_dialog import ask_confirmation
        old_name = self.case.customer.practice_name or self.case.customer.customer_id
        new_name = chosen_customer.practice_name
        confirmed = ask_confirmation(
            self,
            message=tr(
                "change_practice.confirm_msg",
                'Alle Kundendaten dieses Falls werden durch die Daten der neu '
                'gewählten Praxis "{new}" ersetzt. Fortfahren?',
                old=old_name,
                new=new_name,
            ),
            title=DIALOG_TITLES["change_practice"],
            confirm_text=tr("change_practice.confirm_btn", "Praxis wechseln"),
        )
        if not confirmed:
            return

        # Build a CaseCustomer snapshot from the full Customer record
        primary_contact: Any | None = None
        if chosen_customer.contacts:
            primary_contact = chosen_customer.contacts[0]

        new_case_customer = CaseCustomer(
            customer_id=chosen_customer.customer_id,
            practice_name=chosen_customer.practice_name,
            is_vip=chosen_customer.is_vip,
            contact_person=primary_contact.name if primary_contact else "",
            phone=primary_contact.phone if primary_contact else (chosen_customer.phone_main or ""),
            email=primary_contact.email if primary_contact else (chosen_customer.email_address or ""),
        )

        note_text = self.note_textbox.get("1.0", "end").strip()
        self.on_practice_changed(new_case_customer, note_text)
        self.close_dialog()
