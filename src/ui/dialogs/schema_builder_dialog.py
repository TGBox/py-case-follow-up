import customtkinter as ctk
from typing import Callable
from models.schema import QuestionSchema, SchemaField
from enums import FieldType
from services.schema_service import SchemaService


class NewSchemaDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_schema_created: Callable[[QuestionSchema], None]):
        super().__init__(parent)
        self.title("🆕 Neues Formular (Schema) erstellen")
        self.geometry("440x320")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.on_schema_created = on_schema_created

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(main_frame, text="Neues Formular-Schema definieren", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(main_frame, text="Anzeigename (Titel) *:").pack(anchor="w", pady=(2, 0))
        self.name_entry = ctk.CTkEntry(main_frame, placeholder_text="z. B. Abrechnung & Tarife")
        self.name_entry.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(main_frame, text="Schema-ID (optional):").pack(anchor="w", pady=(2, 0))
        self.id_entry = ctk.CTkEntry(main_frame, placeholder_text="z. B. schema_abrechnung")
        self.id_entry.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(main_frame, text="Beschreibung:").pack(anchor="w", pady=(2, 0))
        self.desc_entry = ctk.CTkEntry(main_frame, placeholder_text="Optionale Beschreibung des Formulars")
        self.desc_entry.pack(fill="x", pady=(0, 10))

        self.err_lbl = ctk.CTkLabel(main_frame, text="", text_color="red")
        self.err_lbl.pack(anchor="w", pady=2)

        btn_row = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_row.pack(fill="x", pady=(10, 0))

        ctk.CTkButton(btn_row, text="Abbrechen", fg_color="gray", command=self.destroy, width=100).pack(side="left")
        ctk.CTkButton(btn_row, text="Erstellen", fg_color="forestgreen", command=self.on_save, width=140).pack(side="right")

    def on_save(self):
        name = self.name_entry.get().strip()
        if not name:
            self.err_lbl.configure(text="Bitte Anzeigenamen eingeben.")
            return

        schema_id = self.id_entry.get().strip()
        if not schema_id:
            import re
            schema_id = f"schema_{re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())}"

        desc = self.desc_entry.get().strip()

        new_schema = QuestionSchema(
            schema_id=schema_id,
            display_name=name,
            description=desc,
            fields=[]
        )
        self.on_schema_created(new_schema)
        self.destroy()


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
        self.geometry("780x640")
        from utils.ui_utils import center_window
        center_window(self, 780, 640)

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

        ctk.CTkLabel(top_frame, text="Formular auswählen:", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=(0, 10))
        
        self.schema_combo = ctk.CTkOptionMenu(
            top_frame,
            values=[],
            command=self.on_schema_selected,
            width=280,
        )
        self.schema_combo.pack(side="left", padx=(0, 10))

        add_schema_btn = ctk.CTkButton(top_frame, text="+ Neues Formular", command=self.open_new_schema_dialog, fg_color="forestgreen", width=130)
        add_schema_btn.pack(side="left", padx=(0, 5))

        self.adopt_schema_btn = ctk.CTkButton(
            top_frame,
            text="📥 Zu Realdaten übernehmen",
            command=self.on_adopt_schema,
            fg_color="dodgerblue",
            width=200,
        )
        self.adopt_schema_btn.pack(side="left", padx=(0, 5))

        reset_schema_btn = ctk.CTkButton(top_frame, text="🔄 Standard-Formulare", command=self.on_reset_schemas, fg_color="gray30", width=150)
        reset_schema_btn.pack(side="left", padx=(0, 5))

        del_schema_btn = ctk.CTkButton(top_frame, text="🗑️ Löschen", command=self.on_delete_schema, fg_color="red", hover_color="darkred", width=90)
        del_schema_btn.pack(side="right")

        self.refresh_schema_combo()

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

    def on_reset_schemas(self):
        storage_service = getattr(self.master, "storage_service", None)
        if storage_service:
            self.schemas = storage_service.reset_schemas_to_defaults()
            self.selected_schema = self.schemas[0] if self.schemas else None
            self.refresh_schema_combo()
            self.refresh_fields_list()
            self.on_schemas_updated(self.schemas)

    def refresh_schema_combo(self):
        schema_names = [s.display_name for s in self.schemas]
        if not schema_names:
            schema_names = ["Kein Formular"]
            self.selected_schema = None
        elif self.selected_schema not in self.schemas:
            self.selected_schema = self.schemas[0]

        self.schema_combo.configure(values=schema_names)
        if self.selected_schema:
            self.schema_combo.set(self.selected_schema.display_name)
        else:
            self.schema_combo.set(schema_names[0])

    def open_new_schema_dialog(self):
        NewSchemaDialog(self, on_schema_created=self.on_schema_created)

    def on_schema_created(self, new_schema: QuestionSchema):
        self.schemas.append(new_schema)
        self.selected_schema = new_schema
        self.refresh_schema_combo()
        self.refresh_fields_list()

    def on_delete_schema(self):
        if self.selected_schema and len(self.schemas) > 1:
            self.schemas.remove(self.selected_schema)
            self.selected_schema = self.schemas[0]
            self.refresh_schema_combo()
            self.refresh_fields_list()

    def check_adopt_status(self):
        storage_service = getattr(self.master, "storage_service", None)
        if not storage_service or not self.selected_schema:
            self.adopt_schema_btn.configure(state="disabled", text="📥 Zu Realdaten übernehmen", fg_color="gray40")
            return

        saved_schemas = storage_service.load_schemas()
        is_already_saved = False
        for s in saved_schemas:
            if s.schema_id == self.selected_schema.schema_id:
                if len(s.fields) == len(self.selected_schema.fields):
                    if all(f1.field_id == f2.field_id and f1.label == f2.label for f1, f2 in zip(s.fields, self.selected_schema.fields)):
                        is_already_saved = True
                        break

        if is_already_saved:
            self.adopt_schema_btn.configure(text="✓ In Realdaten enthalten", state="disabled", fg_color="gray40")
        else:
            self.adopt_schema_btn.configure(text="📥 Zu Realdaten übernehmen", state="normal", fg_color="dodgerblue")

    def on_adopt_schema(self):
        storage_service = getattr(self.master, "storage_service", None)
        if storage_service and self.selected_schema:
            saved_schemas = storage_service.load_schemas()
            idx = next((i for i, s in enumerate(saved_schemas) if s.schema_id == self.selected_schema.schema_id), -1)
            if idx >= 0:
                saved_schemas[idx] = self.selected_schema
            else:
                saved_schemas.append(self.selected_schema)

            storage_service.save_schemas(saved_schemas)
            self.schemas = saved_schemas
            self.on_schemas_updated(saved_schemas)
            self.refresh_schema_combo()
            self.check_adopt_status()

    def on_schema_selected(self, name: str):
        self.selected_schema = next((s for s in self.schemas if s.display_name == name), None)
        self.refresh_fields_list()

    def refresh_fields_list(self):
        self.check_adopt_status()
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
