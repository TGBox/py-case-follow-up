import customtkinter as ctk
from typing import Callable
from models.case import Case, TimelineEntry
from models.schema import QuestionSchema
from enums import Channel
from utils.datetime_utils import now_iso
from constants import DIALOG_DIMENSIONS, DIALOG_TITLES


class ConvertSchemaDialog(ctk.CTkToplevel):
    """Dialog to convert a case from its current form schema to another schema."""

    def __init__(
        self,
        parent,
        case: Case,
        schemas: list[QuestionSchema],
        author_name: str,
        on_schema_converted: Callable[[Case, QuestionSchema], None],
    ):
        super().__init__(parent)
        self.case = case
        self.schemas = schemas
        self.author_name = author_name
        self.on_schema_converted = on_schema_converted

        w, h = DIALOG_DIMENSIONS["convert_schema"]
        self.title(DIALOG_TITLES["convert_schema"])
        self.geometry(f"{w}x{h}")
        self.resizable(False, False)
        from utils.ui_utils import center_window
        center_window(self, w, h)

        self.transient(parent)
        self.grab_set()

        self.current_schema = next((s for s in schemas if s.schema_id == case.classification.schema_id), None)
        self.other_schemas = [s for s in schemas if s.schema_id != case.classification.schema_id]

        self.create_widgets()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        ctk.CTkLabel(
            main_frame, text="🔄 Formular-Schema umwandeln", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(0, 10))

        # Case info
        curr_schema_name = self.current_schema.display_name if self.current_schema else self.case.classification.schema_id
        info_box = ctk.CTkFrame(main_frame, fg_color=("gray90", "gray20"))
        info_box.pack(fill="x", pady=(0, 12), padx=2)

        info_inner = ctk.CTkFrame(info_box, fg_color="transparent")
        info_inner.pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(
            info_inner,
            text=f"Fall-ID: {self.case.case_id} — {self.case.classification.title}",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
        ).pack(fill="x")

        ctk.CTkLabel(
            info_inner,
            text=f"Aktuelles Formular: {curr_schema_name}",
            text_color="gray",
            anchor="w",
        ).pack(fill="x", pady=(2, 0))

        # Target Schema selection
        ctk.CTkLabel(
            main_frame, text="Neues Ziel-Formular auswählen:", font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", pady=(4, 2))

        schema_options = [f"{s.display_name} [{s.schema_id}]" for s in self.schemas]
        self.schema_combo = ctk.CTkOptionMenu(main_frame, values=schema_options if schema_options else ["Keine Schemas"])
        self.schema_combo.pack(fill="x", pady=(0, 12))

        # Pre-select first non-current schema if available
        if self.other_schemas:
            target_default = f"{self.other_schemas[0].display_name} [{self.other_schemas[0].schema_id}]"
            self.schema_combo.set(target_default)

        # Info Box about data preservation
        notice_frame = ctk.CTkFrame(main_frame, fg_color=("lightblue", "#1e293b"))
        notice_frame.pack(fill="x", pady=(0, 15))

        notice_text = (
            "ℹ Datensicherung:\n"
            "Beim Umwandeln werden bisher eingegebene Formular-Informationen als neue "
            "Notiz in die Zeitleiste übernommen, sodass kein Inhalt verloren geht. "
            "Gemeinsame Felder (z. B. Programmbereich) werden ins neue Formular übertragen."
        )
        ctk.CTkLabel(
            notice_frame, text=notice_text, font=ctk.CTkFont(size=11), justify="left", wraplength=460
        ).pack(padx=10, pady=8, anchor="w")

        self.error_label = ctk.CTkLabel(main_frame, text="", text_color="red")
        self.error_label.pack(anchor="w", pady=(0, 5))

        # Bottom Buttons
        btn_row = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_row.pack(fill="x", side="bottom")

        ctk.CTkButton(
            btn_row, text="Abbrechen", fg_color="gray", command=self.destroy, width=110
        ).pack(side="left")

        ctk.CTkButton(
            btn_row,
            text="Formular umwandeln",
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            command=self.on_convert,
            width=160,
        ).pack(side="right")

    def on_convert(self):
        selected_val = self.schema_combo.get()
        target_schema = next((s for s in self.schemas if f"[{s.schema_id}]" in selected_val), None)
        if not target_schema:
            self.error_label.configure(text="Bitte ein gültiges Ziel-Formular auswählen.")
            return

        if target_schema.schema_id == self.case.classification.schema_id:
            self.error_label.configure(text="Der Fall verwendet bereits dieses Formular-Schema.")
            return

        # 1. Prepare timeline backup of existing form data
        backup_items = []
        for k, v in self.case.form_data.items():
            if v and str(v).strip():
                label = k
                if self.current_schema:
                    f_obj = next((f for f in self.current_schema.fields if f.field_id == k), None)
                    if f_obj:
                        label = f_obj.label
                backup_items.append(f"• {label}: {v}")

        curr_schema_name = self.current_schema.display_name if self.current_schema else self.case.classification.schema_id
        if backup_items:
            data_summary = "\n".join(backup_items)
            timeline_note = (
                f"🔄 Formular umgewandelt von '{curr_schema_name}' zu '{target_schema.display_name}'.\n"
                f"--- Gesicherte Formular-Daten ---\n{data_summary}"
            )
        else:
            timeline_note = (
                f"🔄 Formular umgewandelt von '{curr_schema_name}' zu '{target_schema.display_name}'."
            )

        self.case.timeline.append(
            TimelineEntry(
                timestamp=now_iso(),
                author=self.author_name,
                channel=Channel.INTERNAL_NOTE,
                note=timeline_note,
                status_change=f"SCHEMA: {self.case.classification.schema_id} -> {target_schema.schema_id}",
            )
        )

        # 2. Preserve matching fields in target schema
        new_form_data = {}
        target_field_ids = {f.field_id for f in target_schema.fields}
        for k, v in self.case.form_data.items():
            if k in target_field_ids:
                new_form_data[k] = v

        self.case.form_data = new_form_data
        self.case.classification.schema_id = target_schema.schema_id

        # Call callback & close
        self.on_schema_converted(self.case, target_schema)
        self.destroy()
