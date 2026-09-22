"""Feld-Renderer fuer DynamicFormWidget: je eine Methode pro Feldtyp-Zweig,
ausgelagert aus dem ehemals ~310-zeiligen render_single_field() (if/elif-Kette
ueber Modultags, Browser-Multiselect, Datum, Dropdown, Boolean, Datei, Zahl,
Mehrzeilentext und Standardtext).

FieldRendererMixin wird per Mixin-Vererbung in DynamicFormWidget eingemischt,
sodass `self` weiterhin dieselbe Widget-Instanz ist und alle hier verwendeten
self.-Attribute (self.profile, self.storage_service, self.current_case, usw.)
sowie self.update_conditional_visibility()/self.open_calendar_picker()/... wie
gewohnt funktionieren. render_single_field() selbst bleibt in dynamic_form_widget.py
und baut nur noch row_frame/label_row/entry_kwargs auf, bevor es an die passende
_render_*_field()-Methode hier delegiert - reines Verschieben von Code, keine
Verhaltensaenderung.
"""
import os
import shutil
import customtkinter as ctk
from tkinter import filedialog
from typing import Any
from collections.abc import Callable
from models.schema import QuestionSchema, SchemaField
from services.schema_i18n import schema_field_label
from models.case import Case
from constants import (
    BROWSER_OPTION_UNKNOWN,
    BTN_HEIGHT_MANAGE_TAGS,
    BTN_WIDTH_CALENDAR,
    BTN_WIDTH_CHOOSE_FILE,
    BTN_WIDTH_IMPORT_BACKUP,
    BTN_WIDTH_MANAGE_TAGS,
    COLOR_BTN_IMPORT_BACKUP,
    COLOR_BTN_IMPORT_BACKUP_HOVER,
    COLOR_BTN_MANAGE_TAGS,
    COLOR_BTN_MANAGE_TAGS_HOVER,
    COLOR_BTN_SECONDARY,
    COLOR_BTN_SECONDARY_HOVER,
    COLOR_DROPDOWN_MISSING_BG,
    COLOR_DROPDOWN_MISSING_BTN,
    COLOR_PILL_ACTIVE,
    COLOR_PILL_BOX_BG,
    COLOR_PILL_HOVER,
    COLOR_PILL_INACTIVE,
    COLOR_PILL_TEXT_ACTIVE,
    COLOR_PILL_TEXT_INACTIVE,
    COLOR_TAG_PICKER_BTN_BG,
    COLOR_TAG_PICKER_BTN_HOVER,
    COLOR_TAG_PICKER_BTN_TEXT,
    COMBO_WIDTH_FORM,
    CORNER_RADIUS_MD,
    DEFAULT_BROWSER_OPTIONS,
    DEFAULT_MODULE_TAGS,
    ENTRY_WIDTH_DATE,
    ENTRY_WIDTH_FILE,
    ENTRY_WIDTH_FORM_DEFAULT,
    HEIGHT_BROWSER_PILL,
    HEIGHT_TAG_PICKER_BTN,
    PAD_CONTAINER,
    PAD_MD,
    PAD_SM,
    PAD_XS,
    TEXTBOX_DEFAULT_HEIGHT,
    TEXTBOX_DEFAULT_WIDTH,
)


class FieldRendererMixin:
    """Rendert je einen Feldtyp in render_single_field(). Nur zusammen mit
    DynamicFormWidget (bzw. einer Klasse mit denselben self.profile /
    self.current_case / self.update_conditional_visibility / ... Attributen
    und Methoden) nutzbar.
    """
    profile: Any = None
    storage_service: Any = None
    current_case: Case | None = None
    schema: QuestionSchema | None = None
    on_manage_module_tags: Callable[[], None] | None = None

    def update_conditional_visibility(self) -> None:
        pass

    def open_calendar_picker(self, entry: Any) -> None:
        pass

    def import_db_backup_file(self, case: Case, bool_var: Any) -> None:
        pass

    def render_mini_attachment_section(self, parent: Any, case: Case) -> None:
        pass

    def _get_target_dir(self, case: Case) -> str:
        return ""

    def refresh_mini_attachment_list(self, case: Case) -> None:
        pass

    def winfo_toplevel(self) -> Any:
        pass

    def _render_module_tags_field(self, row_frame: ctk.CTkFrame, label_row: ctk.CTkFrame, f: SchemaField, val: Any, target_widget_dict: dict[str, Any]):
        if self.on_manage_module_tags:
            from services.i18n_service import tr
            ctk.CTkButton(
                label_row,
                text=tr("dynamic_form.manage_tags", "⚙ Programmbereiche verwalten"),
                width=BTN_WIDTH_MANAGE_TAGS,
                height=BTN_HEIGHT_MANAGE_TAGS,
                fg_color=COLOR_BTN_MANAGE_TAGS,
                hover_color=COLOR_BTN_MANAGE_TAGS_HOVER,
                command=self.on_manage_module_tags,
            ).pack(side="right", padx=PAD_CONTAINER)

        available_mods = self.profile.available_module_tags if self.profile else list(DEFAULT_MODULE_TAGS)
        selected_mods = [m.strip() for m in str(val).split(",") if m.strip()] if val else []

        mod_container = ctk.CTkFrame(row_frame, fg_color="transparent")
        mod_container.pack(fill="x", pady=PAD_XS)

        mod_selected_holder = {"selected": selected_mods}

        from services.i18n_service import tr

        def format_mod_btn_text(sel_list: list[str]) -> str:
            if not sel_list:
                return tr("dynamic_form.no_mod_selected", "🧩 Keinen Programmbereich ausgewählt ▾")
            elif len(sel_list) == 1:
                return f"🧩 {sel_list[0]} ▾"
            elif len(sel_list) <= 2:
                return f"🧩 {', '.join(sel_list)} ▾"
            else:
                return f"🧩 {sel_list[0]}, {sel_list[1]} ({tr('dynamic_form.more_mods_suffix', '+{count} weitere', count=len(sel_list)-2)}) ▾"

        btn_text = format_mod_btn_text(selected_mods)
        picker_btn = ctk.CTkButton(
            mod_container,
            text=btn_text,
            height=HEIGHT_TAG_PICKER_BTN,
            anchor="w",
            fg_color=COLOR_TAG_PICKER_BTN_BG,
            hover_color=COLOR_TAG_PICKER_BTN_HOVER,
            text_color=COLOR_TAG_PICKER_BTN_TEXT,
        )
        picker_btn.pack(fill="x", expand=True)

        def open_mod_picker(b=picker_btn, holder=mod_selected_holder):
            def on_apply_mods(new_selected: list[str]):
                holder["selected"] = new_selected
                b.configure(text=format_mod_btn_text(new_selected))
                self.update_conditional_visibility()

            from ui.widgets.dynamic_form_widget import ModuleTagPickerPopup
            ModuleTagPickerPopup(
                self.winfo_toplevel(),
                available_tags=available_mods,
                selected_tags=holder["selected"],
                on_apply=on_apply_mods,
            )

        picker_btn.configure(command=open_mod_picker)
        target_widget_dict[f.field_id] = ("module_picker", mod_selected_holder)

    def _render_browser_multiselect_field(self, row_frame: ctk.CTkFrame, f: SchemaField, val: Any, target_widget_dict: dict[str, Any]):
        browser_options = list(DEFAULT_BROWSER_OPTIONS)
        raw_val = str(val) if val else ""
        selected_browsers = [b.strip() for b in raw_val.split(",") if b.strip()]

        b_frame = ctk.CTkFrame(row_frame, fg_color=COLOR_PILL_BOX_BG, corner_radius=CORNER_RADIUS_MD)
        b_frame.pack(fill="x", pady=PAD_XS)

        b_pills_box = ctk.CTkFrame(b_frame, fg_color="transparent")
        b_pills_box.pack(fill="x", padx=CORNER_RADIUS_MD, pady=PAD_SM)

        b_vars: dict[str, ctk.BooleanVar] = {}
        b_btns: dict[str, ctk.CTkButton] = {}

        def update_browser_pills_ui():
            for b_opt, b_v in b_vars.items():
                is_sel = b_v.get()
                b_btns[b_opt].configure(
                    fg_color=COLOR_PILL_ACTIVE if is_sel else COLOR_PILL_INACTIVE,
                    text_color=COLOR_PILL_TEXT_ACTIVE if is_sel else COLOR_PILL_TEXT_INACTIVE,
                )
            self.update_conditional_visibility()

        def on_browser_click(clicked_opt: str):
            if clicked_opt == BROWSER_OPTION_UNKNOWN:
                new_state = not b_vars[BROWSER_OPTION_UNKNOWN].get()
                b_vars[BROWSER_OPTION_UNKNOWN].set(new_state)
                if new_state:
                    for o in browser_options:
                        if o != BROWSER_OPTION_UNKNOWN:
                            b_vars[o].set(False)
            else:
                new_state = not b_vars[clicked_opt].get()
                b_vars[clicked_opt].set(new_state)
                if new_state:
                    b_vars[BROWSER_OPTION_UNKNOWN].set(False)

            update_browser_pills_ui()

        for b_opt in browser_options:
            is_b_on = b_opt in selected_browsers
            b_var = ctk.BooleanVar(value=is_b_on)
            b_vars[b_opt] = b_var

            btn = ctk.CTkButton(
                b_pills_box,
                text=b_opt,
                height=HEIGHT_BROWSER_PILL,
                fg_color=COLOR_PILL_ACTIVE if is_b_on else COLOR_PILL_INACTIVE,
                hover_color=COLOR_PILL_HOVER,
                text_color=COLOR_PILL_TEXT_ACTIVE if is_b_on else COLOR_PILL_TEXT_INACTIVE,
                command=lambda opt=b_opt: on_browser_click(opt),
            )
            btn.pack(side="left", padx=PAD_SM, pady=PAD_SM - 1)
            b_btns[b_opt] = btn

        target_widget_dict[f.field_id] = ("browser_pills", b_vars)

    def _render_date_field(self, row_frame: ctk.CTkFrame, f: SchemaField, val: Any, target_widget_dict: dict[str, Any], entry_kwargs: dict[str, Any]):
        entry_row = ctk.CTkFrame(row_frame, fg_color="transparent")
        entry_row.pack(anchor="w")

        from services.i18n_service import tr
        entry = ctk.CTkEntry(entry_row, placeholder_text=f.placeholder or tr("common.date_placeholder", "TT.MM.JJJJ"), width=ENTRY_WIDTH_DATE, **entry_kwargs)
        if val:
            entry.insert(0, str(val))
        entry.pack(side="left", padx=(0, PAD_MD + PAD_XS))

        from services.i18n_service import tr

        cal_btn = ctk.CTkButton(
            entry_row,
            text=tr("cockpit.calendar", "📅 Kalender"),
            width=BTN_WIDTH_CALENDAR,
            fg_color=COLOR_BTN_SECONDARY,
            hover_color=COLOR_BTN_SECONDARY_HOVER,
            command=lambda e=entry: self.open_calendar_picker(e),
        )
        cal_btn.pack(side="left")
        target_widget_dict[f.field_id] = (f.field_type, entry)

    def _render_dropdown_field(self, row_frame: ctk.CTkFrame, f: SchemaField, val: Any, target_widget_dict: dict[str, Any], is_missing: bool):
        options = f.options if f.options else ["-"]
        opt_kwargs: dict[str, Any] = {"button_color": COLOR_DROPDOWN_MISSING_BTN, "fg_color": COLOR_DROPDOWN_MISSING_BG} if is_missing else {}
        combo = ctk.CTkOptionMenu(
            row_frame,
            values=options,
            command=lambda _val: self.update_conditional_visibility(),
            width=COMBO_WIDTH_FORM,
            **opt_kwargs,
        )
        if val and str(val) in options:
            combo.set(str(val))
        combo.pack(anchor="w", pady=(0, PAD_XS))
        target_widget_dict[f.field_id] = (f.field_type, combo)

    def _render_boolean_field(self, row_frame: ctk.CTkFrame, f: SchemaField, val: Any, target_widget_dict: dict[str, Any], entry_kwargs: dict[str, Any], case: Case | None):
        fid_lower = f.field_id.lower()
        flabel_lower = f.label.lower()

        bool_var = ctk.BooleanVar(value=bool(val) if val is not None else False)
        chk_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        chk_frame.pack(fill="x")

        schema_id = self.schema.schema_id if self.schema else ""
        chk = ctk.CTkCheckBox(
            chk_frame,
            text=schema_field_label(schema_id, f),
            variable=bool_var,
            command=self.update_conditional_visibility,
            **entry_kwargs,
        )
        chk.pack(side="left", anchor="w")


        is_db_backup_field = "database_dump" in fid_lower or "backup" in fid_lower or "datenbank" in flabel_lower

        if is_db_backup_field and case:
            from services.i18n_service import tr
            import_db_btn = ctk.CTkButton(
                chk_frame,
                text=tr("dynamic_form.import_backup", "📁 .backup-Datei importieren..."),
                width=BTN_WIDTH_IMPORT_BACKUP,
                fg_color=COLOR_BTN_IMPORT_BACKUP,
                hover_color=COLOR_BTN_IMPORT_BACKUP_HOVER,
                command=lambda c=case, v=bool_var: self.import_db_backup_file(c, v),
            )
            import_db_btn.pack(side="left", padx=PAD_MD + PAD_CONTAINER + PAD_XS)

        target_widget_dict[f.field_id] = (f.field_type, bool_var)

        if is_db_backup_field and case:
            self.render_mini_attachment_section(row_frame, case)

    def _render_file_field(self, row_frame: ctk.CTkFrame, f: SchemaField, val: Any, target_widget_dict: dict[str, Any], entry_kwargs: dict[str, Any]):
        from services.i18n_service import tr
        file_row = ctk.CTkFrame(row_frame, fg_color="transparent")
        file_row.pack(anchor="w")
        file_entry = ctk.CTkEntry(
            file_row,
            placeholder_text=f.placeholder or tr("dynamic_form.no_file_selected", "Keine Datei ausgewählt..."),
            width=ENTRY_WIDTH_FILE,
            **entry_kwargs,
        )
        if val:
            file_entry.insert(0, str(val))
        file_entry.pack(side="left", padx=(0, PAD_MD + PAD_XS))

        def open_file_picker(e=file_entry, f_item=f):
            exts = f_item.allowed_extensions
            ftypes = [(tr("common.files", "Dateien"), " ".join(f"*{x}" for x in exts))] if exts else [(tr("common.all_files", "Alle Dateien"), "*.*")]
            schema_id = self.schema.schema_id if self.schema else ""
            chosen = filedialog.askopenfilename(title=tr("dynamic_form.select_file_for", "Datei auswählen für '{label}'", label=schema_field_label(schema_id, f_item)), filetypes=ftypes)
            if chosen:
                e.delete(0, "end")
                e.insert(0, chosen)
                if self.current_case:
                    try:
                        t_dir = self._get_target_dir(self.current_case)
                        os.makedirs(t_dir, exist_ok=True)
                        dest_p = os.path.join(t_dir, os.path.basename(chosen))
                        shutil.copy2(chosen, dest_p)
                        if hasattr(self, "mini_attach_scroll"):
                            self.refresh_mini_attachment_list(self.current_case)
                    except Exception:
                        pass

        ctk.CTkButton(
            file_row,
            text=tr("dynamic_form.choose_file", "📁 Datei wählen..."),
            width=BTN_WIDTH_CHOOSE_FILE,
            fg_color=COLOR_BTN_SECONDARY,
            hover_color=COLOR_BTN_SECONDARY_HOVER,
            command=open_file_picker,
        ).pack(side="left")

        target_widget_dict[f.field_id] = ("file", file_entry)

    def _render_number_field(self, row_frame: ctk.CTkFrame, f: SchemaField, val: Any, target_widget_dict: dict[str, Any], entry_kwargs: dict[str, Any]):
        from services.i18n_service import tr
        entry = ctk.CTkEntry(row_frame, placeholder_text=f.placeholder or tr("dynamic_form.number_placeholder", "Zahl..."), width=ENTRY_WIDTH_FORM_DEFAULT, **entry_kwargs)
        if val is not None:
            entry.insert(0, str(val))
        entry.pack(anchor="w", pady=(0, PAD_XS))
        target_widget_dict[f.field_id] = (f.field_type, entry)

    def _render_textbox_field(self, row_frame: ctk.CTkFrame, f: SchemaField, val: Any, target_widget_dict: dict[str, Any], entry_kwargs: dict[str, Any] | None = None):
        from ui.widgets.dynamic_form_widget import TextboxResizeHandle
        custom_height = TEXTBOX_DEFAULT_HEIGHT
        if self.profile:
            ui = getattr(self.profile, "ui_settings", None)
            cust_heights = getattr(ui, "custom_textbox_heights", None) or getattr(self.profile, "textbox_heights", None)
            if isinstance(cust_heights, dict) and f.field_id in cust_heights:
                custom_height = cust_heights[f.field_id]
            elif ui and getattr(ui, "textbox_height", None):
                custom_height = ui.textbox_height

        textbox = ctk.CTkTextbox(row_frame, width=TEXTBOX_DEFAULT_WIDTH, height=custom_height, wrap="word", **(entry_kwargs or {}))
        if val:
            textbox.insert("1.0", str(val))
        textbox.pack(anchor="w", pady=(0, PAD_XS))

        handle = TextboxResizeHandle(
            row_frame,
            target_textbox=textbox,
            field_id=f.field_id,
            profile=self.profile,
            storage_service=self.storage_service,
            width=TEXTBOX_DEFAULT_WIDTH,
        )
        handle.pack(anchor="w", pady=(PAD_XS, 0))

        target_widget_dict[f.field_id] = ("textbox", textbox)

    def _render_text_entry_field(self, row_frame: ctk.CTkFrame, f: SchemaField, val: Any, target_widget_dict: dict[str, Any], entry_kwargs: dict[str, Any]):
        from services.i18n_service import tr
        entry = ctk.CTkEntry(row_frame, placeholder_text=f.placeholder or tr("dynamic_form.text_placeholder", "Text..."), width=ENTRY_WIDTH_FORM_DEFAULT, **entry_kwargs)
        if val:
            entry.insert(0, str(val))
        entry.pack(anchor="w", pady=(0, PAD_XS))
        target_widget_dict[f.field_id] = (f.field_type, entry)
