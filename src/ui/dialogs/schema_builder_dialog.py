import customtkinter as ctk
from typing import Callable
from src.models.schema import QuestionSchema, SchemaField
from src.enums import FieldType
from src.services.schema_service import SchemaService


class SchemaBuilderDialog(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        schemas: list[QuestionSchema],
        schema_service: SchemaService,
        on_schemas_updated: Callable[[list[QuestionSchema]], None],
    ):
        super().__init__(parent)
        self.title("In-App Formular-Baukasten (Schemata verwalten)")
        self.geometry("720x620")

        self.schemas = schemas
        self.schema_service = schema_service
        self.on_schemas_updated = on_schemas_updated

        self.selected_schema = self.schemas[0] if self.schemas else None
        self.selected_field_id: str | None = None

        self.grab_set()
        self.create_widgets()
        self.refresh_fields_list()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header & Schema Selector
        top_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        top_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(top_frame, text="Schema auswählen:", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=(0, 10))
        schema_names = [s.display_name for s in self.schemas]
        self.schema_combo = ctk.CTkOptionMenu(
            top_frame,
            values=schema_names if schema_names else ["Kein Schema"],
            command=self.on_schema_selected,
            width=360,
        )
        if self.selected_schema:
            self.schema_combo.set(self.selected_schema.display_name)
        self.schema_combo.pack(side="left")

        # Fields List Frame
        ctk.CTkLabel(main_frame, text="Enthaltene Formularfelder:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 5))
        
        self.fields_scroll = ctk.CTkScrollableFrame(main_frame, width=680, height=300)
        self.fields_scroll.pack(fill="both", expand=True, pady=(0, 15))

        # Field Addition Form
        add_frame = ctk.CTkFrame(main_frame)
        add_frame.pack(fill="x", pady=(0, 15), padx=5)

        ctk.CTkLabel(add_frame, text="Neues Feld hinzufügen:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(5, 5))
        
        inputs_row = ctk.CTkFrame(add_frame, fg_color="transparent")
        inputs_row.pack(fill="x", padx=10, pady=(0, 10))

        self.new_id_entry = ctk.CTkEntry(inputs_row, placeholder_text="Feld-ID (z. B. patient_id)", width=160)
        self.new_id_entry.pack(side="left", padx=(0, 10))

        self.new_label_entry = ctk.CTkEntry(inputs_row, placeholder_text="Beschriftung (Label)", width=200)
        self.new_label_entry.pack(side="left", padx=(0, 10))

        field_types = [t.value for t in FieldType]
        self.new_type_combo = ctk.CTkOptionMenu(inputs_row, values=field_types, width=120)
        self.new_type_combo.pack(side="left", padx=(0, 10))

        self.new_req_chk = ctk.CTkCheckBox(inputs_row, text="Pflicht", width=70)
        self.new_req_chk.pack(side="left", padx=(0, 10))

        add_btn = ctk.CTkButton(inputs_row, text="+ Feld Hinzufügen", command=self.on_add_field, width=120)
        add_btn.pack(side="right")

        # Status & Action Buttons
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x")

        close_btn = ctk.CTkButton(btn_frame, text="Schließen", fg_color="gray", command=self.destroy, width=120)
        close_btn.pack(side="left")

        save_btn = ctk.CTkButton(btn_frame, text="Änderungen Speichern", command=self.on_save, width=180)
        save_btn.pack(side="right")

    def on_schema_selected(self, name: str):
        self.selected_schema = next((s for s in self.schemas if s.display_name == name), None)
        self.refresh_fields_list()

    def refresh_fields_list(self):
        for widget in self.fields_scroll.winfo_children():
            widget.destroy()

        if not self.selected_schema:
            return

        for idx, f in enumerate(self.selected_schema.fields):
            f_frame = ctk.CTkFrame(self.fields_scroll, fg_color="gray20" if idx % 2 == 0 else "transparent")
            f_frame.pack(fill="x", pady=2, padx=5)

            req_str = "[PFLICHT]" if f.required else "[OPTIONAL]"
            text_str = f"#{f.order}  {f.label} ({f.field_id})  —  Typ: {f.field_type}  {req_str}"

            lbl = ctk.CTkLabel(f_frame, text=text_str, anchor="w", font=ctk.CTkFont(size=12))
            lbl.pack(side="left", padx=10, expand=True, fill="x")

            # Actions: Up, Down, Toggle Required, Delete
            up_btn = ctk.CTkButton(f_frame, text="▲", width=30, command=lambda fid=f.field_id: self.on_move(fid, "up"))
            up_btn.pack(side="left", padx=2)

            down_btn = ctk.CTkButton(f_frame, text="▼", width=30, command=lambda fid=f.field_id: self.on_move(fid, "down"))
            down_btn.pack(side="left", padx=2)

            req_btn = ctk.CTkButton(f_frame, text="Pflicht +/-", width=80, command=lambda fid=f.field_id: self.on_toggle(fid))
            req_btn.pack(side="left", padx=2)

            del_btn = ctk.CTkButton(f_frame, text="✕", width=30, fg_color="red", hover_color="darkred", command=lambda fid=f.field_id: self.on_delete(fid))
            del_btn.pack(side="left", padx=2)

    def on_add_field(self):
        if not self.selected_schema:
            return
        field_id = self.new_id_entry.get().strip()
        label = self.new_label_entry.get().strip()
        if not field_id or not label:
            return

        field_type = self.new_type_combo.get()
        is_required = self.new_req_chk.get() == 1

        new_field = SchemaField(field_id=field_id, label=label, field_type=field_type, required=is_required)
        SchemaService.add_field(self.selected_schema, new_field)

        self.new_id_entry.delete(0, "end")
        self.new_label_entry.delete(0, "end")
        self.refresh_fields_list()

    def on_move(self, field_id: str, direction: str):
        if self.selected_schema:
            SchemaService.move_field(self.selected_schema, field_id, direction)
            self.refresh_fields_list()

    def on_toggle(self, field_id: str):
        if self.selected_schema:
            SchemaService.toggle_required(self.selected_schema, field_id)
            self.refresh_fields_list()

    def on_delete(self, field_id: str):
        if self.selected_schema:
            SchemaService.remove_field(self.selected_schema, field_id)
            self.refresh_fields_list()

    def on_save(self):
        self.schema_service.save_schema_changes(self.schemas)
        self.on_schemas_updated(self.schemas)
        self.destroy()
