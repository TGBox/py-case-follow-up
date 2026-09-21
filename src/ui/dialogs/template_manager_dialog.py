from collections.abc import Callable
import customtkinter as ctk

from ui.dialogs.base_dialog import BaseDialog
from models.export_template import ExportTemplate
from models.schema import QuestionSchema
from models.case import Case
from enums import TargetType
from services.export_service import ExportService
from services.storage_service import StorageService
from constants import (
    BORDER_WIDTH_CARD,
    BTN_WIDTH_ACTION,
    BTN_WIDTH_ADOPT,
    BTN_WIDTH_CANCEL,
    BTN_WIDTH_FILTER_DEEP,
    BTN_WIDTH_NEW_COLLEAGUE,
    BTN_WIDTH_SM,
    BTN_WIDTH_TAG_APPLY,
    BTN_WIDTH_TOGGLE_DEFAULTS,
    COLOR_BTN_CANCEL,
    COLOR_BTN_CANCEL_HOVER,
    COLOR_BTN_GRAY,
    COLOR_BTN_TOGGLE_DEFAULTS,
    COLOR_BTN_TOGGLE_DEFAULTS_HOVER,
    COLOR_CARD_ALT_BG,
    COLOR_DANGER,
    COLOR_MUTED_BODY,
    COLOR_MUTED_LABEL,
    COLOR_PANEL_BG,
    COLOR_PANEL_BORDER,
    COLOR_PRIMARY_BLUE,
    COLOR_SUCCESS,
    COLOR_TEXT_GRAY,
    CORNER_RADIUS_MD,
    CORNER_RADIUS_NONE,
    DIALOG_DIMENSIONS,
    DIALOG_MIN_SIZE_EDIT_TEMPLATE,
    DIALOG_MIN_SIZE_TEMPLATE_MGMT,
    FONT_FAMILY_MONO,
    FONT_SIZE_BODY,
    FONT_SIZE_CONFIRM,
    FONT_SIZE_HEADER_BAR,
    FONT_SIZE_SM,
    FONT_WEIGHT_BOLD,
    HEIGHT_BOTTOM_BAR,
    HEIGHT_TOP_BAR,
    LABEL_WIDTH_TEMPLATE_FIELD,
    PAD_10,
    PAD_15,
    PAD_2XL,
    PAD_CONTAINER,
    PAD_GAP,
    PAD_MD,
    PAD_NONE,
    PAD_SM,
    PAD_XS,
    TEXTBOX_HEIGHT_PREVIEW,
    TEXTBOX_HEIGHT_TEMPLATE,
)


class EditTemplateDialog(BaseDialog):
    def __init__(
        self,
        parent,
        template: ExportTemplate | None,
        schemas: list[QuestionSchema],
        export_service: ExportService,
        on_save: Callable[[ExportTemplate], None],
    ):
        super().__init__(parent)
        self.template = template
        self.schemas = schemas
        self.export_service = export_service
        self.on_save = on_save

        from services.i18n_service import tr
        w, h = DIALOG_DIMENSIONS["edit_template"]
        self.setup_window(
            parent,
            tr("template_mgmt.edit_title", "📄 Export-Vorlage bearbeiten") if template else tr("template_mgmt.new_title", "📄 Neue Export-Vorlage erstellen"),
            (w, h),
            min_size=DIALOG_MIN_SIZE_EDIT_TEMPLATE,

            title_factory=lambda: tr("template_mgmt.edit_title", "📄 Export-Vorlage bearbeiten") if template else tr("template_mgmt.new_title", "📄 Neue Export-Vorlage erstellen"),
        )

        self.schema_vars: dict[str, ctk.BooleanVar] = {}
        self.field_vars: dict[str, ctk.BooleanVar] = {}

        self.create_widgets(is_new=template is None)
        # Closing now asks before throwing away an edited export template.
        self.enable_unsaved_guard()

    def create_widgets(self, is_new: bool = False):
        from services.i18n_service import tr
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=PAD_15, pady=PAD_15)

        # Header
        hdr_text = tr("template_mgmt.edit_title", "📄 Export-Vorlage bearbeiten") if not is_new else tr("template_mgmt.new_title", "📄 Neue Export-Vorlage erstellen")
        ctk.CTkLabel(main_frame, text=hdr_text, font=ctk.CTkFont(size=FONT_SIZE_HEADER_BAR, weight=FONT_WEIGHT_BOLD)).pack(anchor="w", pady=(PAD_NONE, PAD_10))

        scroll_frame = ctk.CTkScrollableFrame(self)
        scroll_frame.pack(fill="both", expand=True, padx=PAD_15, pady=PAD_CONTAINER)

        # Template ID & Display Name
        row1 = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        row1.pack(fill="x", pady=PAD_SM)

        self.register_i18n(ctk.CTkLabel(row1, text=tr("template_mgmt.id_lbl", "Vorlage-ID *:"), width=LABEL_WIDTH_TEMPLATE_FIELD, anchor="w"), "template_mgmt.id_lbl", "Vorlage-ID *:").pack(side="left")
        self.id_entry = self.register_i18n(ctk.CTkEntry(row1, placeholder_text=tr("template_mgmt.id_placeholder", "z. B. gitlab_dev_ticket")), "template_mgmt.id_placeholder", "z. B. gitlab_dev_ticket", attr="placeholder_text")
        if self.template:
            self.id_entry.insert(0, self.template.template_id)
            if not is_new:
                self.id_entry.configure(state="disabled")
        self.id_entry.pack(side="left", fill="x", expand=True)

        row2 = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        row2.pack(fill="x", pady=PAD_SM)

        self.register_i18n(ctk.CTkLabel(row2, text=tr("template_mgmt.name_lbl", "Anzeigename *:"), width=LABEL_WIDTH_TEMPLATE_FIELD, anchor="w"), "template_mgmt.name_lbl", "Anzeigename *:").pack(side="left")
        self.name_entry = self.register_i18n(ctk.CTkEntry(row2, placeholder_text=tr("template_mgmt.name_placeholder", "z. B. GitLab / Dev-Ticket")), "template_mgmt.name_placeholder", "z. B. GitLab / Dev-Ticket", attr="placeholder_text")
        if self.template:
            self.name_entry.insert(0, self.template.display_name)
        self.name_entry.pack(side="left", fill="x", expand=True)

        # Description & Target Type
        row3 = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        row3.pack(fill="x", pady=PAD_SM)

        self.register_i18n(ctk.CTkLabel(row3, text=tr("template_mgmt.desc_lbl", "Beschreibung:"), width=LABEL_WIDTH_TEMPLATE_FIELD, anchor="w"), "template_mgmt.desc_lbl", "Beschreibung:").pack(side="left")
        self.desc_entry = self.register_i18n(ctk.CTkEntry(row3, placeholder_text=tr("template_mgmt.desc_placeholder", "Kurze Beschreibung des Formats...")), "template_mgmt.desc_placeholder", "Kurze Beschreibung des Formats...", attr="placeholder_text")
        if self.template:
            self.desc_entry.insert(0, self.template.description)
        self.desc_entry.pack(side="left", fill="x", expand=True)

        row4 = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        row4.pack(fill="x", pady=PAD_SM)

        self.register_i18n(ctk.CTkLabel(row4, text=tr("template_mgmt.target_type_lbl", "Ziel-Aktion / Typ:"), width=LABEL_WIDTH_TEMPLATE_FIELD, anchor="w"), "template_mgmt.target_type_lbl", "Ziel-Aktion / Typ:").pack(side="left")
        self.type_combo = ctk.CTkOptionMenu(row4, values=[TargetType.CLIPBOARD_TEXT.value, TargetType.FILE_EXPORT.value])
        if self.template:
            self.type_combo.set(self.template.target_type)
        self.type_combo.pack(side="left")

        # Applicable Schemas Checkboxes
        self.register_i18n(ctk.CTkLabel(scroll_frame, text=tr("template_mgmt.applicable_schemas_lbl", "Zugeordnete Formular-Schemas:"), font=ctk.CTkFont(weight=FONT_WEIGHT_BOLD, size=FONT_SIZE_BODY)), "template_mgmt.applicable_schemas_lbl", "Zugeordnete Formular-Schemas:").pack(anchor="w", pady=(PAD_10, PAD_XS))
        schemas_frame = ctk.CTkFrame(scroll_frame, fg_color=COLOR_CARD_ALT_BG)
        schemas_frame.pack(fill="x", pady=(PAD_NONE, PAD_10), padx=PAD_XS)

        for s in self.schemas:
            var = ctk.BooleanVar(value=bool(self.template and s.schema_id in self.template.applicable_cases))
            self.schema_vars[s.schema_id] = var
            cb = ctk.CTkCheckBox(schemas_frame, text=f"{s.display_name} ({s.schema_id})", variable=var)
            cb.pack(anchor="w", padx=PAD_MD, pady=PAD_SM)

        # Required Fields Checkboxes
        self.register_i18n(ctk.CTkLabel(scroll_frame, text=tr("template_mgmt.req_fields_lbl", "Erforderliche Pflichtfelder vor Export:"), font=ctk.CTkFont(weight=FONT_WEIGHT_BOLD, size=FONT_SIZE_BODY)), "template_mgmt.req_fields_lbl", "Erforderliche Pflichtfelder vor Export:").pack(anchor="w", pady=(PAD_CONTAINER, PAD_XS))
        fields_frame = ctk.CTkFrame(scroll_frame, fg_color=COLOR_CARD_ALT_BG)
        fields_frame.pack(fill="x", pady=(PAD_NONE, PAD_10), padx=PAD_XS)

        all_fields: dict[str, str] = {}
        for s in self.schemas:
            for f in s.fields:
                all_fields[f.field_id] = f.label

        if not all_fields and self.template:
            for f_id in self.template.required_schema_fields:
                all_fields[f_id] = f_id

        for f_id, f_label in all_fields.items():
            var = ctk.BooleanVar(value=bool(self.template and f_id in self.template.required_schema_fields))
            self.field_vars[f_id] = var
            cb = ctk.CTkCheckBox(fields_frame, text=f"{f_label} [{f_id}]", variable=var)
            cb.pack(anchor="w", padx=PAD_MD, pady=PAD_SM)

        # Jinja2 Template Markup Editor
        self.register_i18n(ctk.CTkLabel(scroll_frame, text=tr("template_mgmt.jinja_lbl", "Jinja2 Template Text (Markdown / Text):"), font=ctk.CTkFont(weight=FONT_WEIGHT_BOLD, size=FONT_SIZE_BODY)), "template_mgmt.jinja_lbl", "Jinja2 Template Text (Markdown / Text):").pack(anchor="w", pady=(PAD_CONTAINER, PAD_XS))
        self.template_textbox = ctk.CTkTextbox(scroll_frame, height=TEXTBOX_HEIGHT_TEMPLATE, font=ctk.CTkFont(family=FONT_FAMILY_MONO, size=FONT_SIZE_BODY))
        self.template_textbox.pack(fill="x", pady=(PAD_NONE, PAD_10))
        if self.template:
            self.template_textbox.insert("1.0", self.template.template_string)

        from services.i18n_service import tr

        # Live Preview Panel
        preview_btn = self.register_i18n(ctk.CTkButton(scroll_frame, text=tr("template_editor.preview_btn", "👁 Live-Vorschau rendern"), command=self.render_preview, fg_color=COLOR_PRIMARY_BLUE), "template_editor.preview_btn", "👁 Live-Vorschau rendern")
        preview_btn.pack(anchor="w", pady=PAD_SM)

        self.preview_textbox = ctk.CTkTextbox(scroll_frame, height=TEXTBOX_HEIGHT_PREVIEW, font=ctk.CTkFont(family=FONT_FAMILY_MONO, size=FONT_SIZE_SM))
        self.preview_textbox.pack(fill="x", pady=(PAD_NONE, PAD_10))
        self.preview_textbox.configure(state="disabled")

        # Bottom Action Bar
        bottom_bar = ctk.CTkFrame(self, height=HEIGHT_BOTTOM_BAR, fg_color="transparent")
        bottom_bar.pack(fill="x", side="bottom", padx=PAD_15, pady=PAD_10)

        self.register_i18n(ctk.CTkButton(bottom_bar, text=tr("ui_buttons.save_template", "💾 Vorlage Speichern"), command=self.save, fg_color=COLOR_SUCCESS, width=BTN_WIDTH_TAG_APPLY), "ui_buttons.save_template", "💾 Vorlage Speichern").pack(side="right", padx=PAD_CONTAINER)
        self.register_i18n(ctk.CTkButton(bottom_bar, text=tr("common.cancel", "Abbrechen"), command=self.destroy, fg_color=COLOR_BTN_CANCEL, hover_color=COLOR_BTN_CANCEL_HOVER, width=BTN_WIDTH_CANCEL), "common.cancel", "Abbrechen").pack(side="left", padx=PAD_CONTAINER)

    def render_preview(self):
        tmpl_str = self.template_textbox.get("1.0", "end-1c")
        sample_case = Case(
            case_id="T-2026-DEMO",
            created_by="Support-Agent",
            form_data={"billing_quarter": "2026-Q2", "error_code": "ERR_DEMO_101", "database_dump_provided": True},
            attachment_directory="attachments/T-2026-DEMO_Praxis",
        )
        sample_case.customer.practice_name = "Musterpraxis Dr. Test"
        sample_case.customer.customer_id = "K-99999"
        sample_case.customer.is_vip = True
        sample_case.classification.title = "Beispiel-Fall für Vorschau"

        test_template = ExportTemplate(
            template_id="preview",
            display_name="Preview",
            target_type=self.type_combo.get(),
            template_string=tmpl_str,
        )

        success, missing, res = self.export_service.render_template(sample_case, test_template)
        self.preview_textbox.configure(state="normal")
        self.preview_textbox.delete("1.0", "end")
        self.preview_textbox.insert("1.0", res)
        self.preview_textbox.configure(state="disabled")

    def save(self):
        t_id = self.id_entry.get().strip()
        t_name = self.name_entry.get().strip()
        if not t_id or not t_name:
            return

        applicable = [s_id for s_id, v in self.schema_vars.items() if v.get()]
        required = [f_id for f_id, v in self.field_vars.items() if v.get()]
        tmpl_str = self.template_textbox.get("1.0", "end-1c")

        new_template = ExportTemplate(
            template_id=t_id,
            display_name=t_name,
            target_type=self.type_combo.get(),
            applicable_cases=applicable,
            description=self.desc_entry.get().strip(),
            required_schema_fields=required,
            template_string=tmpl_str,
        )

        self.on_save(new_template)
        self.destroy()


class TemplateManagerDialog(BaseDialog):
    def __init__(
        self,
        parent,
        templates: list[ExportTemplate],
        schemas: list[QuestionSchema],
        storage_service: StorageService,
        export_service: ExportService,
        on_templates_updated: Callable[[list[ExportTemplate]], None] | None = None,
    ):
        super().__init__(parent)
        self.templates = list(templates)
        self.schemas = schemas
        self.storage_service = storage_service
        self.export_service = export_service
        self.on_templates_updated = on_templates_updated

        w, h = DIALOG_DIMENSIONS["template_mgmt"]
        from services.i18n_service import tr
        self.setup_window(
            parent,
            tr("dialog_titles.template_mgmt", "📄 Export-Vorlagen verwalten"),
            (w, h),
            min_size=DIALOG_MIN_SIZE_TEMPLATE_MGMT,

            title_factory=lambda: tr("dialog_titles.template_mgmt", "📄 Export-Vorlagen verwalten"),
        )

        self.create_widgets()

    def create_widgets(self):
        from services.i18n_service import tr

        top_bar = ctk.CTkFrame(self, height=HEIGHT_TOP_BAR, corner_radius=CORNER_RADIUS_NONE)
        top_bar.pack(fill="x", side="top", padx=PAD_10, pady=(PAD_10, PAD_CONTAINER))

        self.register_i18n(ctk.CTkLabel(top_bar, text=tr("template_mgmt.header", "📄 Export-Vorlagen-Verwaltung"), font=ctk.CTkFont(size=FONT_SIZE_HEADER_BAR, weight=FONT_WEIGHT_BOLD)), "template_mgmt.header", "📄 Export-Vorlagen-Verwaltung").pack(side="left", padx=PAD_10)

        btn_new = self.register_i18n(ctk.CTkButton(top_bar, text=tr("template_mgmt.new_template", "+ Neue Vorlage"), command=self.on_add_template, fg_color=COLOR_SUCCESS, width=BTN_WIDTH_ACTION), "template_mgmt.new_template", "+ Neue Vorlage")
        btn_new.pack(side="right", padx=PAD_CONTAINER)

        self.btn_toggle_defaults = ctk.CTkButton(
            top_bar,
            text=self._get_toggle_defaults_text(),
            command=self.on_toggle_default_templates,
            fg_color=COLOR_BTN_TOGGLE_DEFAULTS,
            hover_color=COLOR_BTN_TOGGLE_DEFAULTS_HOVER,
            width=BTN_WIDTH_TOGGLE_DEFAULTS,
        )
        self.btn_toggle_defaults.pack(side="right", padx=PAD_CONTAINER)

        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=PAD_10, pady=PAD_CONTAINER)

        self.render_list()

    def _get_toggle_defaults_text(self) -> str:
        from services.i18n_service import tr
        if self.storage_service.has_default_templates():
            return tr("template_mgmt.remove_defaults", "➖ Standard-Vorlagen entfernen")
        return tr("template_mgmt.add_defaults", "➕ Standard-Vorlagen laden")

    def on_toggle_default_templates(self):
        self.templates, is_added = self.storage_service.toggle_default_templates()
        if hasattr(self, "btn_toggle_defaults"):
            self.btn_toggle_defaults.configure(text=self._get_toggle_defaults_text())
        self.render_list()
        if self.on_templates_updated:
            self.on_templates_updated(self.templates)

    def on_reset_templates(self):
        self.on_toggle_default_templates()

    def render_list(self):
        from services.i18n_service import tr

        for w in self.scroll_frame.winfo_children():
            w.destroy()

        display_templates = list(self.templates)
        saved_templates = self.storage_service.load_templates()

        if not display_templates:
            self.register_i18n(ctk.CTkLabel(self.scroll_frame, text=tr("template_mgmt.no_templates", "Keine Vorlagen vorhanden."), text_color=COLOR_TEXT_GRAY), "template_mgmt.no_templates", "Keine Vorlagen vorhanden.").pack(pady=PAD_2XL)
            return

        for tmpl in display_templates:
            card = ctk.CTkFrame(self.scroll_frame, fg_color=COLOR_PANEL_BG, border_width=BORDER_WIDTH_CARD, border_color=COLOR_PANEL_BORDER, corner_radius=CORNER_RADIUS_MD)
            card.pack(fill="x", pady=PAD_CONTAINER, padx=PAD_CONTAINER)

            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=PAD_10, pady=(PAD_GAP, PAD_XS))

            name_lbl = ctk.CTkLabel(top_row, text=f"📄 {tmpl.display_name}", font=ctk.CTkFont(weight=FONT_WEIGHT_BOLD, size=FONT_SIZE_CONFIRM))
            name_lbl.pack(side="left")

            id_lbl = ctk.CTkLabel(top_row, text=f"[{tmpl.template_id}]", font=ctk.CTkFont(size=FONT_SIZE_SM), text_color=COLOR_MUTED_LABEL)
            id_lbl.pack(side="left", padx=PAD_MD)

            btn_del = self.register_i18n(ctk.CTkButton(top_row, text=tr("common.delete", "🗑 Löschen"), width=BTN_WIDTH_SM, fg_color=COLOR_DANGER, command=lambda t=tmpl: self.confirm_delete_template(t)), "common.delete", "🗑 Löschen")
            btn_del.pack(side="right", padx=PAD_SM)

            btn_edit = self.register_i18n(ctk.CTkButton(top_row, text=tr("common.edit", "✏ Bearbeiten"), width=BTN_WIDTH_FILTER_DEEP, command=lambda t=tmpl: self.on_edit_template(t)), "common.edit", "✏ Bearbeiten")
            btn_edit.pack(side="right", padx=PAD_SM)

            is_already_saved = any(
                s.template_id == tmpl.template_id and s.template_string == tmpl.template_string and s.display_name == tmpl.display_name
                for s in saved_templates
            )

            if is_already_saved:
                btn_adopt = self.register_i18n(ctk.CTkButton(top_row, text=tr("template_mgmt.already_in_real_data", "✓ In Realdaten enthalten"), width=BTN_WIDTH_ADOPT, state="disabled", fg_color=COLOR_BTN_GRAY), "template_mgmt.already_in_real_data", "✓ In Realdaten enthalten")
            else:
                btn_adopt = self.register_i18n(ctk.CTkButton(top_row, text=tr("template_mgmt.adopt_to_real_data", "📥 Zu Realdaten übernehmen"), width=BTN_WIDTH_NEW_COLLEAGUE, fg_color=COLOR_PRIMARY_BLUE, command=lambda t=tmpl: self.on_adopt_template(t)), "template_mgmt.adopt_to_real_data", "📥 Zu Realdaten übernehmen")
            btn_adopt.pack(side="right", padx=PAD_SM)

            desc_txt = tmpl.description or tr("template_mgmt.no_desc", "Keine Beschreibung")
            req_txt = tr("template_mgmt.req_fields_summary", "Pflichtfelder: {fields}", fields=', '.join(tmpl.required_schema_fields)) if tmpl.required_schema_fields else tr("template_mgmt.no_req_fields", "Keine Pflichtfelder")
            sub_lbl = ctk.CTkLabel(card, text=f"{desc_txt}  •  {req_txt}", anchor="w", font=ctk.CTkFont(size=FONT_SIZE_SM), text_color=COLOR_MUTED_BODY)
            sub_lbl.pack(fill="x", padx=PAD_10, pady=(PAD_NONE, PAD_GAP))

    def on_adopt_template(self, tmpl: ExportTemplate):
        saved_templates = self.storage_service.load_templates()
        idx = next((i for i, t in enumerate(saved_templates) if t.template_id == tmpl.template_id), -1)
        if idx >= 0:
            saved_templates[idx] = tmpl
        else:
            saved_templates.append(tmpl)

        self.storage_service.save_templates(saved_templates)
        self.templates = saved_templates
        self.render_list()
        if self.on_templates_updated:
            self.on_templates_updated(self.templates)

    def on_add_template(self):
        EditTemplateDialog(self, None, self.schemas, self.export_service, self.save_template)

    def on_edit_template(self, tmpl: ExportTemplate):
        EditTemplateDialog(self, tmpl, self.schemas, self.export_service, self.save_template)

    def confirm_delete_template(self, tmpl: ExportTemplate):
        """Asks before deleting the export template."""
        from services.i18n_service import tr
        from ui.dialogs.confirm_dialog import ask_confirmation
        if ask_confirmation(
            self,
            tr("confirm.delete_template", "Export-Vorlage „{name}“ wirklich dauerhaft löschen?", name=tmpl.display_name),
            title=tr("confirm.delete_title", "Löschen bestätigen"),
            confirm_text=tr("confirm.yes_delete", "🗑 Ja, löschen"),
        ):
            self.on_delete_template(tmpl)

    def on_delete_template(self, tmpl: ExportTemplate):
        self.templates = [t for t in self.templates if t.template_id != tmpl.template_id]
        self.storage_service.save_templates(self.templates)
        self.render_list()
        if self.on_templates_updated:
            self.on_templates_updated(self.templates)

    def save_template(self, updated_tmpl: ExportTemplate):
        idx = next((i for i, t in enumerate(self.templates) if t.template_id == updated_tmpl.template_id), -1)
        if idx >= 0:
            self.templates[idx] = updated_tmpl
        else:
            self.templates.append(updated_tmpl)

        self.storage_service.save_templates(self.templates)
        self.render_list()
        if self.on_templates_updated:
            self.on_templates_updated(self.templates)
