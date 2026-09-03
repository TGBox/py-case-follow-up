import os
import customtkinter as ctk
from tkinter import filedialog
from typing import Callable, Any
from models.customer import Customer
from services.cobra_crm_import_service import CobraCrmImportService, FIELD_ALIAS_MAP
from constants import DIALOG_DIMENSIONS, DIALOG_TITLES


class CobraImportDialog(ctk.CTkToplevel):
    """Import wizard for Cobra CRM customer export files (.csv, .txt, .json)."""

    def __init__(self, parent, existing_customers: list[Customer], on_import_completed: Callable[[list[Customer]], None]):
        super().__init__(parent)
        self.existing_customers = existing_customers
        self.on_import_completed = on_import_completed

        w, h = DIALOG_DIMENSIONS["cobra_import"]
        self.title(DIALOG_TITLES["cobra_import"])
        self.geometry(f"{w}x{h}")
        self.minsize(760, 540)

        from utils.ui_utils import center_window
        center_window(self, w, h)

        self.transient(parent)
        self.grab_set()

        self.file_path: str = ""
        self.raw_rows: list[dict[str, str]] = []
        self.headers: list[str] = []
        self.mapping: dict[str, str] = {}
        self.mapped_customers: list[Customer] = []
        self.mapping_combos: dict[str, ctk.CTkOptionMenu] = {}

        self.create_widgets()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Header
        hdr_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        hdr_frame.pack(fill="x", pady=(0, 10))

        from services.i18n_service import tr

        ctk.CTkLabel(hdr_frame, text=tr("cobra_import.header", "🐍 Cobra CRM Praxen-Import Assistent"), font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(hdr_frame, text=tr("cobra_import.header_desc", "Importieren Sie Praxen aus Cobra CRM Exporte-Dateien (.csv, .txt, .json)."), font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w")

        file_box = ctk.CTkFrame(main_frame)
        file_box.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(file_box, text=tr("cobra_import.step1_lbl", "1. Cobra Export-Datei auswählen:"), font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(8, 4))

        f_row = ctk.CTkFrame(file_box, fg_color="transparent")
        f_row.pack(fill="x", padx=10, pady=(0, 8))

        self.file_entry = ctk.CTkEntry(f_row, placeholder_text=tr("cobra_import.file_placeholder", "Datei auswählen (*.csv, *.txt, *.json)..."))
        self.file_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(f_row, text=tr("cobra_import.browse_btn", "📁 Durchsuchen..."), width=130, command=self.on_browse_file).pack(side="right")

        # Scrollable Content Box for Mapping & Preview
        from utils.ui_utils import enable_auto_hiding_scrollbar
        self.content_scroll = ctk.CTkScrollableFrame(main_frame)
        self.content_scroll.pack(fill="both", expand=True, pady=(0, 10))
        enable_auto_hiding_scrollbar(self.content_scroll)

        # Section 2: Column Mapping
        ctk.CTkLabel(self.content_scroll, text=tr("cobra_import.step2_lbl", "2. Cobra Spaltenzuordnung (Feld-Mapper):"), font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(4, 6))

        self.map_grid = ctk.CTkFrame(self.content_scroll, fg_color="transparent")
        self.map_grid.pack(fill="x", pady=(0, 10))

        # Section 3: Conflict Mode & Preview Summary
        ctk.CTkLabel(self.content_scroll, text=tr("cobra_import.step3_lbl", "3. Konfliktbehandlung für bestehende Praxen:"), font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(8, 4))

        mode_options = [
            tr("cobra_import.mode_update", "Bestehende Praxen aktualisieren (Update)"),
            tr("cobra_import.mode_skip", "Bestehende überspringen (Skip)"),
            tr("cobra_import.mode_all_new", "Alle als neu anlegen"),
        ]
        self.mode_combo = ctk.CTkOptionMenu(
            self.content_scroll,
            values=mode_options,
            width=320,
            command=lambda v: self.update_preview(),
        )
        self.mode_combo.pack(anchor="w", pady=(0, 8))

        self.summary_lbl = ctk.CTkLabel(self.content_scroll, text=tr("cobra_import.initial_summary", "Bitte wählen Sie eine Export-Datei aus."), font=ctk.CTkFont(size=11), text_color="dodgerblue", anchor="w")
        self.summary_lbl.pack(fill="x", pady=(0, 6))

        self.preview_box = ctk.CTkFrame(self.content_scroll, fg_color="transparent")
        self.preview_box.pack(fill="x", pady=(0, 10))

        # Action Buttons
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(5, 0))

        self.import_btn = ctk.CTkButton(
            btn_frame,
            text=tr("cobra_import.import_btn", "🐍 Praxen importieren"),
            fg_color="forestgreen",
            hover_color="darkgreen",
            command=self.on_click_import,
            state="disabled",
        )
        self.import_btn.pack(side="right", padx=(6, 0))

        ctk.CTkButton(btn_frame, text=tr("common.cancel", "Abbrechen"), fg_color="gray50", command=self.destroy, width=90).pack(side="right")

    def on_browse_file(self):
        from services.i18n_service import tr
        fp = filedialog.askopenfilename(
            title=tr("cobra_import.file_dialog_title", "Cobra CRM Export-Datei auswählen"),
            filetypes=[("Cobra / CSV Dateien (*.csv, *.txt, *.json)", "*.csv;*.txt;*.json"), ("Alle Dateien", "*.*")],
        )
        if not fp:
            return

        self.file_path = fp
        self.file_entry.delete(0, "end")
        self.file_entry.insert(0, fp)

        try:
            self.raw_rows, self.headers = CobraCrmImportService.parse_file(fp)
            if not self.raw_rows:
                self.summary_lbl.configure(text=tr("cobra_import.no_records_found", "⚠ Keine Datensätze in der Datei gefunden."), text_color="crimson")
                return

            self.mapping = CobraCrmImportService.auto_detect_mapping(self.headers)
            self.render_mapping_grid()
            self.update_preview()
            self.import_btn.configure(state="normal")
        except Exception as ex:
            self.summary_lbl.configure(text=tr("cobra_import.read_error", "❌ Fehler beim Lesen der Datei: {error}", error=ex), text_color="crimson")

    def render_mapping_grid(self):
        for w in self.map_grid.winfo_children():
            w.destroy()

        from services.i18n_service import tr
        self.mapping_combos.clear()
        no_mapping_text = tr("cobra_import.no_mapping", "(Keine Zuordnung)")
        options = [no_mapping_text] + self.headers

        target_labels = {
            "customer_id": tr("cobra_import.field_customer_id", "Kunden-ID / Nr."),
            "vnum1": tr("cobra_import.field_vnum1", "VNUM1 (VM / KdNr 1)"),
            "practice_name": tr("cobra_import.field_practice_name", "Praxis- / Firmenname *"),
            "practice_name_old": tr("cobra_import.field_practice_name_old", "Praxisname (Alt)"),
            "salutation": tr("cobra_import.field_salutation", "Anrede"),
            "first_name": tr("cobra_import.field_first_name", "Vorname"),
            "last_name": tr("cobra_import.field_last_name", "Nachname"),
            "street": tr("cobra_import.field_street", "Straße & Hausnr."),
            "zip_code": tr("cobra_import.field_zip_code", "Postleitzahl (PLZ)"),
            "city": tr("cobra_import.field_city", "Ort / Stadt"),
            "phone_main": tr("cobra_import.field_phone_main", "Telefon Hauptnr."),
            "phone_direct": tr("cobra_import.field_phone_direct", "Telefon direkt (Durchwahl)"),
            "phone_private": tr("cobra_import.field_phone_private", "Telefon privat"),
            "phone2": tr("cobra_import.field_phone2", "Telefon 2"),
            "phone3": tr("cobra_import.field_phone3", "Telefon 3"),
            "mobile": tr("cobra_import.field_mobile", "Mobilnummer"),
            "mobile_private": tr("cobra_import.field_mobile_private", "Mobil privat"),
            "email_address": tr("cobra_import.field_email_address", "E-Mail Hauptadresse"),
            "email2": tr("cobra_import.field_email2", "E-Mail Adresse 2"),
            "email3": tr("cobra_import.field_email3", "E-Mail Adresse 3"),
            "system_version": tr("cobra_import.field_system_version", "System-Version"),
            "dsc": tr("cobra_import.field_dsc", "DSC (Alt-Code)"),
            "dsc_neu": tr("cobra_import.field_dsc_neu", "DSCNEU (Neu-Code)"),
            "is_vip": tr("cobra_import.field_is_vip", "VIP-Status"),
            "vm_number": tr("cobra_import.field_vm_number", "VM-Nummer"),
            "instance_number": tr("cobra_import.field_instance_number", "Instanz-Nummer"),
            "general_notes": tr("cobra_import.field_general_notes", "Allgemeine Notizen"),
        }

        row_idx = 0
        for field_key, label_text in target_labels.items():
            ctk.CTkLabel(self.map_grid, text=f"{label_text}:", font=ctk.CTkFont(size=11, weight="bold"), anchor="w", width=160).grid(row=row_idx, column=0, sticky="w", padx=4, pady=2)

            detected = self.mapping.get(field_key, "")
            default_val = detected if detected in self.headers else no_mapping_text

            combo = ctk.CTkOptionMenu(
                self.map_grid,
                values=options,
                width=240,
                command=lambda v, k=field_key: self.on_mapping_changed(k, v),
            )
            combo.set(default_val)
            combo.grid(row=row_idx, column=1, sticky="w", padx=4, pady=2)
            self.mapping_combos[field_key] = combo

            row_idx += 1

    def on_mapping_changed(self, field_key: str, selected_value: str):
        from services.i18n_service import tr
        no_mapping_text = tr("cobra_import.no_mapping", "(Keine Zuordnung)")
        val = "" if selected_value == no_mapping_text else selected_value
        self.mapping[field_key] = val
        self.update_preview()

    def update_preview(self):
        from services.i18n_service import tr
        if not self.raw_rows:
            return

        self.mapped_customers = CobraCrmImportService.map_rows_to_customers(self.raw_rows, self.mapping)
        diff = CobraCrmImportService.compare_with_existing(self.mapped_customers, self.existing_customers)

        new_cnt = len(diff["new"])
        dup_cnt = len(diff["duplicates"])
        tot = len(self.mapped_customers)

        mode_str = self.mode_combo.get()

        msg = tr("cobra_import.preview_summary", "✓ {tot} Praxen erkannt  |  🆕 {new} neue Praxen  |  ⚠ {dup} bereits vorhandene Praxen (Duplikate)", tot=tot, new=new_cnt, dup=dup_cnt)
        self.summary_lbl.configure(text=msg, text_color="limegreen" if new_cnt > 0 else "dodgerblue")

        # Render preview items
        for w in self.preview_box.winfo_children():
            w.destroy()

        for c in self.mapped_customers[:15]:
            is_dup = any(d["imported"].customer_id == c.customer_id for d in diff["duplicates"])
            badge = tr("cobra_import.badge_duplicate", "⚠ Duplikat") if is_dup else tr("cobra_import.badge_new", "🆕 Neu")
            badge_color = "darkorange" if is_dup else "limegreen"

            row_f = ctk.CTkFrame(self.preview_box, fg_color=("gray90", "gray15"), corner_radius=4)
            row_f.pack(fill="x", pady=2, padx=2)

            ctk.CTkLabel(row_f, text=badge, text_color=badge_color, font=ctk.CTkFont(size=10, weight="bold"), width=80).pack(side="left", padx=5)
            ctk.CTkLabel(row_f, text=f"{c.customer_id}: {c.practice_name}", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=5)
            contact_str = f"| Ansprechpartner: {c.contact_person}" if c.contact_person else ""
            email_str = f"| {c.email}" if c.email else ""
            ctk.CTkLabel(row_f, text=f"{contact_str} {email_str}", font=ctk.CTkFont(size=10), text_color="gray").pack(side="left", padx=5)

    def on_click_import(self):
        if not self.mapped_customers:
            return

        raw_mode = self.mode_combo.get()
        mode = "update"
        if "überspringen" in raw_mode.lower():
            mode = "skip"
        elif "alle" in raw_mode.lower():
            mode = "all_new"

        merged = CobraCrmImportService.merge_customers(self.existing_customers, self.mapped_customers, mode=mode)
        self.on_import_completed(merged)
        self.destroy()
