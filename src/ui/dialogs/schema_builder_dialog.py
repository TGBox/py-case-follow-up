import customtkinter as ctk

from ui.dialogs.base_dialog import BaseDialog
from collections.abc import Callable
from models.schema import QuestionSchema, SchemaField
from enums import FieldType
from services.schema_service import SchemaService
from services.i18n_service import tr
from constants import (
    BORDER_WIDTH_PANEL,
    BTN_WIDTH_ADOPT_SCHEMA,
    BTN_WIDTH_ARROW,
    BTN_WIDTH_CLOSE,
    BTN_WIDTH_DELETE_SCHEMA,
    BTN_WIDTH_MD,
    BTN_WIDTH_NEW_SCHEMA,
    BTN_WIDTH_TOGGLE_DEFAULTS,
    BTN_WIDTH_TOGGLE_REQUIRED,
    BTN_WIDTH_WIDE,
    CHECKBOX_WIDTH_REQUIRED,
    COLOR_BTN_CANCEL,
    COLOR_BTN_TOGGLE_DEFAULTS,
    COLOR_BTN_TOGGLE_DEFAULTS_HOVER,
    COLOR_DANGER,
    COLOR_DARKRED_HOVER,
    COLOR_PANEL_ALT_BG,
    COLOR_PANEL_BG,
    COLOR_PANEL_BORDER,
    COLOR_PRIMARY_BLUE,
    COLOR_SUCCESS,
    COMBO_WIDTH_FIELD_TYPE,
    COMBO_WIDTH_SCHEMA_SELECT,
    CORNER_RADIUS_CARD,
    CORNER_RADIUS_MD,
    DIALOG_DIMENSIONS,
    DIALOG_MIN_SIZE_SCHEMA_BUILDER,
    DIALOG_TITLES,
    ENTRY_WIDTH_CONDITIONAL,
    ENTRY_WIDTH_EXTS,
    ENTRY_WIDTH_FIELD_ID,
    ENTRY_WIDTH_LABEL,
    FONT_SIZE_BODY,
    FONT_SIZE_HEADER_BAR,
    FONT_SIZE_SM,
    FONT_WEIGHT_BOLD,
    ICON_DELETE_X,
    PAD_10,
    PAD_15,
    PAD_2XL,
    PAD_CONTAINER,
    PAD_GAP,
    PAD_MD,
    PAD_NONE,
    PAD_SM,
    PAD_XS,
    SCHEMA_ID_PREFIX,
    SCROLL_HEIGHT_SCHEMA_FIELDS,
    SCROLL_WIDTH_SCHEMA_FIELDS,
)


class NewSchemaDialog(BaseDialog):
    def __init__(self, parent, on_schema_created: Callable[[QuestionSchema], None]):
        super().__init__(parent)
        w, h = DIALOG_DIMENSIONS["new_schema"]
        self.setup_window(
            parent,
            tr("schema_builder.new_schema_title", "🆕 Neues Formular (Schema) erstellen"),
            (w, h),
            resizable=False,
            title_factory=lambda: tr("schema_builder.new_schema_title", "🆕 Neues Formular (Schema) erstellen"),
        )

        self.on_schema_created = on_schema_created

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=PAD_2XL, pady=PAD_2XL)

        self.register_i18n(
            ctk.CTkLabel(
                main_frame,
                text=tr("schema_builder.define_new_schema", "Neues Formular-Schema definieren"),
                font=ctk.CTkFont(size=FONT_SIZE_HEADER_BAR, weight=FONT_WEIGHT_BOLD),
            ),
            "schema_builder.define_new_schema",
            "Neues Formular-Schema definieren",
        ).pack(anchor="w", pady=(PAD_NONE, PAD_10))

        self.register_i18n(
            ctk.CTkLabel(main_frame, text=tr("schema_builder.display_name_lbl", "Anzeigename (Titel) *:")),
            "schema_builder.display_name_lbl",
            "Anzeigename (Titel) *:",
        ).pack(anchor="w", pady=(PAD_XS, PAD_NONE))
        self.name_entry = self.register_i18n(
            ctk.CTkEntry(main_frame, placeholder_text=tr("schema_builder.name_placeholder", "z. B. Abrechnung & Tarife")),
            "schema_builder.name_placeholder",
            "z. B. Abrechnung & Tarife",
            attr="placeholder_text",
        )
        self.name_entry.pack(fill="x", pady=(PAD_NONE, PAD_MD))

        self.register_i18n(
            ctk.CTkLabel(main_frame, text=tr("schema_builder.schema_id_lbl", "Schema-ID (optional):")),
            "schema_builder.schema_id_lbl",
            "Schema-ID (optional):",
        ).pack(anchor="w", pady=(PAD_XS, PAD_NONE))
        self.id_entry = self.register_i18n(
            ctk.CTkEntry(main_frame, placeholder_text=tr("schema_builder.id_placeholder", "z. B. schema_abrechnung")),
            "schema_builder.id_placeholder",
            "z. B. schema_abrechnung",
            attr="placeholder_text",
        )
        self.id_entry.pack(fill="x", pady=(PAD_NONE, PAD_MD))

        self.register_i18n(
            ctk.CTkLabel(main_frame, text=tr("schema_builder.desc_lbl", "Beschreibung:")),
            "schema_builder.desc_lbl",
            "Beschreibung:",
        ).pack(anchor="w", pady=(PAD_XS, PAD_NONE))
        self.desc_entry = self.register_i18n(
            ctk.CTkEntry(main_frame, placeholder_text=tr("schema_builder.desc_placeholder", "Optionale Beschreibung des Formulars")),
            "schema_builder.desc_placeholder",
            "Optionale Beschreibung des Formulars",
            attr="placeholder_text",
        )
        self.desc_entry.pack(fill="x", pady=(PAD_NONE, PAD_10))

        self.err_lbl = ctk.CTkLabel(main_frame, text="", text_color=COLOR_DANGER)
        self.err_lbl.pack(anchor="w", pady=PAD_XS)

        btn_row = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_row.pack(fill="x", pady=(PAD_10, PAD_NONE))

        self.register_i18n(
            ctk.CTkButton(btn_row, text=tr("common.cancel", "Abbrechen"), fg_color=COLOR_BTN_CANCEL, command=self.destroy, width=BTN_WIDTH_MD),
            "common.cancel",
            "Abbrechen",
        ).pack(side="left")
        self.register_i18n(
            ctk.CTkButton(btn_row, text=tr("ui_buttons.create", "Erstellen"), fg_color=COLOR_SUCCESS, command=self.on_save, width=BTN_WIDTH_WIDE),
            "ui_buttons.create",
            "Erstellen",
        ).pack(side="right")
        self.set_default_action(self.on_save)

    def on_save(self):
        name = self.name_entry.get().strip()
        if not name:
            self.err_lbl.configure(text=tr("schema_builder.enter_display_name", "Bitte Anzeigenamen eingeben."))
            return

        schema_id = self.id_entry.get().strip()
        if not schema_id:
            import re
            schema_id = f"{SCHEMA_ID_PREFIX}{re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())}"

        desc = self.desc_entry.get().strip()

        new_schema = QuestionSchema(
            schema_id=schema_id,
            display_name=name,
            description=desc,
            fields=[],
        )
        self.on_schema_created(new_schema)
        self.destroy()


class SchemaBuilderDialog(BaseDialog):
    def __init__(
        self,
        parent,
        schemas: list[QuestionSchema],
        schema_service: SchemaService,
        on_schemas_updated: Callable[[list[QuestionSchema]], None],
    ):
        super().__init__(parent)
        w, h = DIALOG_DIMENSIONS["schema_builder"]
        self.setup_window(
            parent,
            DIALOG_TITLES["schema_builder"],
            (w, h),
            min_size=DIALOG_MIN_SIZE_SCHEMA_BUILDER,
            title_factory=lambda: DIALOG_TITLES["schema_builder"],
        )

        self.schemas = schemas
        self.schema_service = schema_service
        self.on_schemas_updated = on_schemas_updated

        self.selected_schema = self.schemas[0] if self.schemas else None
        self.selected_field_id: str | None = None

        self.create_widgets()
        self.refresh_fields_list()
        # Closing now asks before throwing away an edited schema.
        self.enable_unsaved_guard()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=PAD_2XL, pady=PAD_2XL)

        # Header & Schema Selector
        top_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        top_frame.pack(fill="x", pady=(PAD_NONE, PAD_15))

        self.register_i18n(
            ctk.CTkLabel(
                top_frame,
                text=tr("schema_builder.select_form_lbl", "Formular auswählen:"),
                font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
            ),
            "schema_builder.select_form_lbl",
            "Formular auswählen:",
        ).pack(side="left", padx=(PAD_NONE, PAD_10))

        schema_names = [s.display_name for s in self.schemas] if self.schemas else [tr("schema_builder.no_form", "Kein Formular")]
        self.schema_combo = ctk.CTkOptionMenu(
            top_frame,
            values=schema_names,
            command=self.on_schema_selected,
            width=COMBO_WIDTH_SCHEMA_SELECT,
        )
        self.schema_combo.pack(side="left", padx=(PAD_NONE, PAD_MD))

        add_schema_btn = self.register_i18n(
            ctk.CTkButton(
                top_frame,
                text=tr("schema_builder.new_form", "+ Neues Formular"),
                command=self.open_new_schema_dialog,
                fg_color=COLOR_SUCCESS,
                width=BTN_WIDTH_NEW_SCHEMA,
            ),
            "schema_builder.new_form",
            "+ Neues Formular",
        )
        add_schema_btn.pack(side="left", padx=(PAD_NONE, PAD_GAP))

        self.adopt_schema_btn = self.register_i18n(
            ctk.CTkButton(
                top_frame,
                text=tr("schema_builder.adopt_schema", "📥 Zu Realdaten übernehmen"),
                command=self.on_adopt_schema,
                fg_color=COLOR_PRIMARY_BLUE,
                width=BTN_WIDTH_ADOPT_SCHEMA,
            ),
            "schema_builder.adopt_schema",
            "📥 Zu Realdaten übernehmen",
        )
        self.adopt_schema_btn.pack(side="left", padx=(PAD_NONE, PAD_GAP))

        self.toggle_schema_btn = ctk.CTkButton(
            top_frame,
            text=self._get_toggle_schemas_text(),
            command=self.on_toggle_default_schemas,
            fg_color=COLOR_BTN_TOGGLE_DEFAULTS,
            hover_color=COLOR_BTN_TOGGLE_DEFAULTS_HOVER,
            width=BTN_WIDTH_TOGGLE_DEFAULTS,
        )
        self.toggle_schema_btn.pack(side="left", padx=(PAD_NONE, PAD_GAP))

        del_schema_btn = self.register_i18n(
            ctk.CTkButton(
                top_frame,
                text=tr("common.delete", "🗑 Löschen"),
                command=self.confirm_delete_schema,
                fg_color=COLOR_DANGER,
                hover_color=COLOR_DARKRED_HOVER,
                width=BTN_WIDTH_DELETE_SCHEMA,
            ),
            "common.delete",
            "🗑 Löschen",
        )
        del_schema_btn.pack(side="right")

        self.refresh_schema_combo()

        # Fields List Frame
        self.register_i18n(
            ctk.CTkLabel(
                main_frame,
                text=tr("schema_builder.fields_header", "Enthaltene Formularfelder:"),
                font=ctk.CTkFont(weight=FONT_WEIGHT_BOLD),
            ),
            "schema_builder.fields_header",
            "Enthaltene Formularfelder:",
        ).pack(anchor="w", pady=(PAD_CONTAINER, PAD_CONTAINER))

        self.fields_scroll = ctk.CTkScrollableFrame(
            main_frame,
            width=SCROLL_WIDTH_SCHEMA_FIELDS,
            height=SCROLL_HEIGHT_SCHEMA_FIELDS,
            fg_color=COLOR_PANEL_BG,
            border_width=BORDER_WIDTH_PANEL,
            border_color=COLOR_PANEL_BORDER,
        )
        self.fields_scroll.pack(fill="both", expand=True, pady=(PAD_NONE, PAD_15))

        # Field Addition Form
        add_frame = ctk.CTkFrame(
            main_frame,
            fg_color=COLOR_PANEL_BG,
            border_width=BORDER_WIDTH_PANEL,
            border_color=COLOR_PANEL_BORDER,
            corner_radius=CORNER_RADIUS_CARD,
        )
        add_frame.pack(fill="x", pady=(PAD_NONE, PAD_15), padx=PAD_CONTAINER)

        self.register_i18n(
            ctk.CTkLabel(
                add_frame,
                text=tr("schema_builder.add_field_header", "Neues Feld hinzufügen (V2 mit bedingter Logik):"),
                font=ctk.CTkFont(weight=FONT_WEIGHT_BOLD),
            ),
            "schema_builder.add_field_header",
            "Neues Feld hinzufügen (V2 mit bedingter Logik):",
        ).pack(anchor="w", padx=PAD_10, pady=(PAD_CONTAINER, PAD_CONTAINER))

        inputs_row = ctk.CTkFrame(add_frame, fg_color="transparent")
        inputs_row.pack(fill="x", padx=PAD_10, pady=(PAD_NONE, PAD_SM))

        self.new_id_entry = self.register_i18n(
            ctk.CTkEntry(inputs_row, placeholder_text=tr("schema_builder.field_id_ph", "Feld-ID (z. B. reason_detail)"), width=ENTRY_WIDTH_FIELD_ID),
            "schema_builder.field_id_ph",
            "Feld-ID (z. B. reason_detail)",
            attr="placeholder_text",
        )
        self.new_id_entry.pack(side="left", padx=(PAD_NONE, PAD_MD))

        self.new_label_entry = self.register_i18n(
            ctk.CTkEntry(inputs_row, placeholder_text=tr("schema_builder.label_ph", "Beschriftung (Label)"), width=ENTRY_WIDTH_LABEL),
            "schema_builder.label_ph",
            "Beschriftung (Label)",
            attr="placeholder_text",
        )
        self.new_label_entry.pack(side="left", padx=(PAD_NONE, PAD_MD))

        field_types = [t.value for t in FieldType]
        self.new_type_combo = ctk.CTkOptionMenu(inputs_row, values=field_types, width=COMBO_WIDTH_FIELD_TYPE)
        self.new_type_combo.pack(side="left", padx=(PAD_NONE, PAD_MD))

        self.new_req_chk = self.register_i18n(
            ctk.CTkCheckBox(inputs_row, text=tr("schema_builder.required_chk", "Pflicht"), width=CHECKBOX_WIDTH_REQUIRED),
            "schema_builder.required_chk",
            "Pflicht",
        )
        self.new_req_chk.pack(side="left", padx=(PAD_NONE, PAD_MD))

        add_btn = self.register_i18n(
            ctk.CTkButton(inputs_row, text=tr("schema_builder.add_btn", "+ Hinzufügen"), command=self.on_add_field, width=BTN_WIDTH_MD),
            "schema_builder.add_btn",
            "+ Hinzufügen",
        )
        add_btn.pack(side="right")

        # Row 2: V2 Conditional Logic & File Extension Inputs
        v2_row = ctk.CTkFrame(add_frame, fg_color="transparent")
        v2_row.pack(fill="x", padx=PAD_10, pady=(PAD_NONE, PAD_MD))

        self.register_i18n(
            ctk.CTkLabel(v2_row, text=tr("schema_builder.conditional_logic_lbl", "↳ Bedingte Logik (If/Else):"), font=ctk.CTkFont(size=FONT_SIZE_SM)),
            "schema_builder.conditional_logic_lbl",
            "↳ Bedingte Logik (If/Else):",
        ).pack(side="left", padx=(PAD_NONE, PAD_SM))

        self.new_dep_id_entry = self.register_i18n(
            ctk.CTkEntry(v2_row, placeholder_text=tr("schema_builder.dep_id_placeholder", "Abhängig von Feld-ID"), width=ENTRY_WIDTH_CONDITIONAL),
            "schema_builder.dep_id_placeholder",
            "Abhängig von Feld-ID",
            attr="placeholder_text",
        )
        self.new_dep_id_entry.pack(side="left", padx=(PAD_NONE, PAD_GAP))

        self.new_dep_val_entry = self.register_i18n(
            ctk.CTkEntry(v2_row, placeholder_text=tr("schema_builder.dep_val_placeholder", "Bei Wert (z. B. Sonstiges)"), width=ENTRY_WIDTH_CONDITIONAL),
            "schema_builder.dep_val_placeholder",
            "Bei Wert (z. B. Sonstiges)",
            attr="placeholder_text",
        )
        self.new_dep_val_entry.pack(side="left", padx=(PAD_NONE, PAD_10))

        self.register_i18n(
            ctk.CTkLabel(v2_row, text=tr("schema_builder.file_types_lbl", "↳ Dateitypen:"), font=ctk.CTkFont(size=FONT_SIZE_SM)),
            "schema_builder.file_types_lbl",
            "↳ Dateitypen:",
        ).pack(side="left", padx=(PAD_NONE, PAD_SM))
        self.new_exts_entry = self.register_i18n(
            ctk.CTkEntry(v2_row, placeholder_text=tr("schema_builder.file_ext_placeholder", ".pdf, .log, .png"), width=ENTRY_WIDTH_EXTS),
            "schema_builder.file_ext_placeholder",
            ".pdf, .log, .png",
            attr="placeholder_text",
        )
        self.new_exts_entry.pack(side="left")

        # Status & Action Buttons
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x")

        close_btn = self.register_i18n(
            ctk.CTkButton(btn_frame, text=tr("common.close", "Schließen"), fg_color=COLOR_BTN_CANCEL, command=self.destroy, width=BTN_WIDTH_CLOSE),
            "common.close",
            "Schließen",
        )
        close_btn.pack(side="left")

        save_btn = self.register_i18n(
            ctk.CTkButton(btn_frame, text=tr("cockpit.save", "Änderungen Speichern"), command=self.on_save, width=BTN_WIDTH_NEW_SCHEMA + CHECKBOX_WIDTH_REQUIRED),
            "cockpit.save",
            "Änderungen Speichern",
        )
        save_btn.pack(side="right")

    def _get_toggle_schemas_text(self) -> str:
        storage_service = getattr(self.master, "storage_service", None)
        has_defaults = storage_service.has_default_schemas() if storage_service else False
        if has_defaults:
            return tr("schema_builder.remove_defaults", "➖ Standard-Formulare entfernen")
        return tr("schema_builder.add_defaults", "➕ Standard-Formulare laden")

    def on_toggle_default_schemas(self):
        storage_service = getattr(self.master, "storage_service", None)
        if storage_service:
            self.schemas, _is_added = storage_service.toggle_default_schemas()
            if self.selected_schema not in self.schemas:
                self.selected_schema = self.schemas[0] if self.schemas else None
            self.refresh_schema_combo()
            self.refresh_fields_list()
            self.on_schemas_updated(self.schemas)
            if hasattr(self, "toggle_schema_btn"):
                self.toggle_schema_btn.configure(text=self._get_toggle_schemas_text())

    def on_reset_schemas(self):
        self.on_toggle_default_schemas()

    def refresh_schema_combo(self):
        schema_names = [s.display_name for s in self.schemas]
        if not schema_names:
            schema_names = [tr("schema_builder.no_form", "Kein Formular")]
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

    def confirm_delete_schema(self):
        """Asks before deleting a form, and explains why the last one is protected."""
        from ui.dialogs.confirm_dialog import ask_confirmation, show_notice
        if not self.selected_schema:
            return
        if len(self.schemas) <= 1:
            show_notice(self, tr("confirm.schema_last_hint", "Das letzte verbleibende Formular kann nicht gelöscht werden."))
            return
        if ask_confirmation(
            self,
            tr("confirm.delete_schema", "Formular „{name}“ wirklich löschen? Bereits erfasste Fälle behalten ihre Daten.", name=self.selected_schema.display_name),
            title=tr("confirm.delete_title", "Löschen bestätigen"),
            confirm_text=tr("confirm.yes_delete", "🗑 Ja, löschen"),
        ):
            self.on_delete_schema()

    def on_delete_schema(self):
        if self.selected_schema and len(self.schemas) > 1:
            self.schemas.remove(self.selected_schema)
            self.selected_schema = self.schemas[0]
            self.refresh_schema_combo()
            self.refresh_fields_list()

    def check_adopt_status(self):
        storage_service = getattr(self.master, "storage_service", None)
        if not storage_service or not self.selected_schema:
            self.adopt_schema_btn.configure(state="disabled", text=tr("template_mgmt.adopt_to_real_data", "📥 Zu Realdaten übernehmen"), fg_color=COLOR_BTN_CANCEL)
            return

        saved_schemas = storage_service.load_schemas()
        is_already_saved = False
        for s in saved_schemas:
            if s.schema_id == self.selected_schema.schema_id:
                if len(s.fields) == len(self.selected_schema.fields):
                    if all(f1.field_id == f2.field_id and f1.label == f2.label for f1, f2 in zip(s.fields, self.selected_schema.fields, strict=True)):
                        is_already_saved = True
                        break

        if is_already_saved:
            self.adopt_schema_btn.configure(text=tr("template_mgmt.already_in_real_data", "✓ In Realdaten enthalten"), state="disabled", fg_color=COLOR_BTN_CANCEL)
        else:
            self.adopt_schema_btn.configure(text=tr("template_mgmt.adopt_to_real_data", "📥 Zu Realdaten übernehmen"), state="normal", fg_color=COLOR_PRIMARY_BLUE)

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
            f_frame = ctk.CTkFrame(self.fields_scroll, fg_color=COLOR_PANEL_ALT_BG if idx % 2 == 0 else "transparent", corner_radius=CORNER_RADIUS_MD)
            f_frame.pack(fill="x", pady=PAD_XS, padx=PAD_CONTAINER)

            req_str = tr("schema_builder.badge_required", "[PFLICHT]") if f.required else tr("schema_builder.badge_optional", "[OPTIONAL]")
            dep_str = f" [IF {f.depends_on_field_id}=='{f.depends_on_value}']" if f.depends_on_field_id else ""
            ext_str = f" [{', '.join(f.allowed_extensions)}]" if f.allowed_extensions else ""
            text_str = f"#{f.order}  {f.label} ({f.field_id})  —  Typ: {f.field_type}{ext_str}  {req_str}{dep_str}"

            lbl = ctk.CTkLabel(f_frame, text=text_str, anchor="w", font=ctk.CTkFont(size=FONT_SIZE_BODY))
            lbl.pack(side="left", padx=PAD_10, expand=True, fill="x")

            # Actions: Up, Down, Toggle Required, Delete
            up_btn = self.register_i18n(ctk.CTkButton(f_frame, text=tr("common.arrow_up", "▲"), width=BTN_WIDTH_ARROW, command=lambda fid=f.field_id: self.on_move(fid, "up")), "common.arrow_up", "▲")
            up_btn.pack(side="left", padx=PAD_XS)

            down_btn = self.register_i18n(ctk.CTkButton(f_frame, text=tr("common.arrow_down", "▼"), width=BTN_WIDTH_ARROW, command=lambda fid=f.field_id: self.on_move(fid, "down")), "common.arrow_down", "▼")
            down_btn.pack(side="left", padx=PAD_XS)

            req_btn = self.register_i18n(ctk.CTkButton(f_frame, text=tr("schema_builder.toggle_required", "Pflicht +/-"), width=BTN_WIDTH_TOGGLE_REQUIRED, command=lambda fid=f.field_id: self.on_toggle(fid)), "schema_builder.toggle_required", "Pflicht +/-")
            req_btn.pack(side="left", padx=PAD_XS)

            del_btn = ctk.CTkButton(f_frame, text=ICON_DELETE_X, width=BTN_WIDTH_ARROW, fg_color=COLOR_DANGER, hover_color=COLOR_DARKRED_HOVER, command=lambda fid=f.field_id: self.on_delete(fid))
            del_btn.pack(side="left", padx=PAD_XS)

    def on_add_field(self):
        if not self.selected_schema:
            return
        field_id = self.new_id_entry.get().strip()
        label = self.new_label_entry.get().strip()
        if not field_id or not label:
            return

        field_type = self.new_type_combo.get()
        is_required = self.new_req_chk.get() == 1
        dep_id = self.new_dep_id_entry.get().strip()
        dep_val = self.new_dep_val_entry.get().strip()
        exts_raw = self.new_exts_entry.get().strip()
        exts = [e.strip() if e.strip().startswith(".") else f".{e.strip()}" for e in exts_raw.split(",") if e.strip()] if exts_raw else []

        new_field = SchemaField(
            field_id=field_id,
            label=label,
            field_type=field_type,
            required=is_required,
            depends_on_field_id=dep_id,
            depends_on_value=dep_val,
            allowed_extensions=exts,
        )
        SchemaService.add_field(self.selected_schema, new_field)

        self.new_id_entry.delete(0, "end")
        self.new_label_entry.delete(0, "end")
        self.new_dep_id_entry.delete(0, "end")
        self.new_dep_val_entry.delete(0, "end")
        self.new_exts_entry.delete(0, "end")
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
