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

        ctk.CTkLabel(hdr_frame, text="🐍 Cobra CRM Praxen-Import Assistent", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(hdr_frame, text="Importieren Sie Praxen aus Cobra CRM Exporte-Dateien (.csv, .txt, .json).", font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w")

        # Step 1: File Picker Frame
        file_box = ctk.CTkFrame(main_frame)
        file_box.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(file_box, text="1. Cobra Export-Datei auswählen:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(8, 4))

        f_row = ctk.CTkFrame(file_box, fg_color="transparent")
        f_row.pack(fill="x", padx=10, pady=(0, 8))

        self.file_entry = ctk.CTkEntry(f_row, placeholder_text="Datei auswählen (*.csv, *.txt, *.json)...")
        self.file_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(f_row, text="📁 Durchsuchen...", width=130, command=self.on_browse_file).pack(side="right")

        # Scrollable Content Box for Mapping & Preview
        from utils.ui_utils import enable_auto_hiding_scrollbar
        self.content_scroll = ctk.CTkScrollableFrame(main_frame)
        self.content_scroll.pack(fill="both", expand=True, pady=(0, 10))
        enable_auto_hiding_scrollbar(self.content_scroll)

        # Section 2: Column Mapping
        ctk.CTkLabel(self.content_scroll, text="2. Cobra Spaltenzuordnung (Feld-Mapper):", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(4, 6))

        self.map_grid = ctk.CTkFrame(self.content_scroll, fg_color="transparent")
        self.map_grid.pack(fill="x", pady=(0, 10))

        # Section 3: Conflict Mode & Preview Summary
        ctk.CTkLabel(self.content_scroll, text="3. Konfliktbehandlung für bestehende Praxen:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(8, 4))

        self.mode_combo = ctk.CTkOptionMenu(
            self.content_scroll,
            values=["Bestehende Praxen aktualisieren (Update)", "Bestehende überspringen (Skip)", "Alle als neu anlegen"],
            width=320,
            command=lambda v: self.update_preview(),
        )
        self.mode_combo.pack(anchor="w", pady=(0, 8))

        self.summary_lbl = ctk.CTkLabel(self.content_scroll, text="Bitte wählen Sie eine Export-Datei aus.", font=ctk.CTkFont(size=11), text_color="dodgerblue", anchor="w")
        self.summary_lbl.pack(fill="x", pady=(0, 6))

        self.preview_box = ctk.CTkFrame(self.content_scroll, fg_color="transparent")
        self.preview_box.pack(fill="x", pady=(0, 10))

        # Action Buttons
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(5, 0))

        self.import_btn = ctk.CTkButton(
            btn_frame,
            text="🐍 Praxen importieren",
            fg_color="forestgreen",
            hover_color="darkgreen",
            command=self.on_click_import,
            state="disabled",
        )
        self.import_btn.pack(side="right", padx=(6, 0))

        ctk.CTkButton(btn_frame, text="Abbrechen", fg_color="gray50", command=self.destroy, width=90).pack(side="right")

    def on_browse_file(self):
        fp = filedialog.askopenfilename(
            title="Cobra CRM Export-Datei auswählen",
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
                self.summary_lbl.configure(text="⚠ Keine Datensätze in der Datei gefunden.", text_color="crimson")
                return

            self.mapping = CobraCrmImportService.auto_detect_mapping(self.headers)
            self.render_mapping_grid()
            self.update_preview()
            self.import_btn.configure(state="normal")
        except Exception as ex:
            self.summary_lbl.configure(text=f"❌ Fehler beim Lesen der Datei: {ex}", text_color="crimson")

    def render_mapping_grid(self):
        for w in self.map_grid.winfo_children():
            w.destroy()

        self.mapping_combos.clear()
        options = ["(Keine Zuordnung)"] + self.headers

        target_labels = {
            "customer_id": "Kunden-ID / Nr.",
            "practice_name": "Praxis- / Firmenname *",
            "contact_person": "Ansprechpartner",
            "phone": "Telefonnummer",
            "email": "E-Mail Adresse",
            "is_vip": "VIP-Status",
            "system_version": "System-Version",
            "vm_number": "VM-Nummer",
            "instance_number": "Instanz-Nummer",
            "general_notes": "Allgemeine Notizen",
        }

        row_idx = 0
        for field_key, label_text in target_labels.items():
            ctk.CTkLabel(self.map_grid, text=f"{label_text}:", font=ctk.CTkFont(size=11, weight="bold"), anchor="w", width=160).grid(row=row_idx, column=0, sticky="w", padx=4, pady=2)

            detected = self.mapping.get(field_key, "")
            default_val = detected if detected in self.headers else "(Keine Zuordnung)"

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
        val = "" if selected_value == "(Keine Zuordnung)" else selected_value
        self.mapping[field_key] = val
        self.update_preview()

    def update_preview(self):
        if not self.raw_rows:
            return

        self.mapped_customers = CobraCrmImportService.map_rows_to_customers(self.raw_rows, self.mapping)
        diff = CobraCrmImportService.compare_with_existing(self.mapped_customers, self.existing_customers)

        new_cnt = len(diff["new"])
        dup_cnt = len(diff["duplicates"])
        tot = len(self.mapped_customers)

        mode_str = self.mode_combo.get()

        msg = f"✓ {tot} Praxen erkannt  |  🆕 {new_cnt} neue Praxen  |  ⚠ {dup_cnt} bereits vorhandene Praxen (Duplikate)"
        self.summary_lbl.configure(text=msg, text_color="limegreen" if new_cnt > 0 else "dodgerblue")

        # Render preview items
        for w in self.preview_box.winfo_children():
            w.destroy()

        for c in self.mapped_customers[:15]:
            is_dup = any(d["imported"].customer_id == c.customer_id for d in diff["duplicates"])
            badge = "⚠ Duplikat" if is_dup else "🆕 Neu"
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
