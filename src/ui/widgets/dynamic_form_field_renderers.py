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
from typing import Any, Callable, TYPE_CHECKING
from models.schema import SchemaField
from models.case import Case
from constants import DEFAULT_MODULE_TAGS

if TYPE_CHECKING:
    from models.profile import UserProfile
    from services.storage_service import StorageService


class FieldRendererMixin:
    """Rendert je einen Feldtyp in render_single_field(). Nur zusammen mit
    DynamicFormWidget (bzw. einer Klasse mit denselben self.profile /
    self.current_case / self.update_conditional_visibility / ... Attributen
    und Methoden) nutzbar.
    """
    profile: Any = None
    storage_service: Any = None
    current_case: Case | None = None
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
                width=140,
                height=22,
                fg_color=("gray75", "gray30"),
                hover_color=("gray65", "gray40"),
                command=self.on_manage_module_tags,
            ).pack(side="right", padx=5)

        available_mods = self.profile.available_module_tags if self.profile else list(DEFAULT_MODULE_TAGS)
        selected_mods = [m.strip() for m in str(val).split(",") if m.strip()] if val else []

        mod_container = ctk.CTkFrame(row_frame, fg_color="transparent")
        mod_container.pack(fill="x", pady=2)

        mod_selected_holder = {"selected": selected_mods}

        def format_mod_btn_text(sel_list: list[str]) -> str:
            if not sel_list:
                return "🧩 Keinen Programmbereich ausgewählt ▾"
            elif len(sel_list) == 1:
                return f"🧩 {sel_list[0]} ▾"
            elif len(sel_list) <= 2:
                return f"🧩 {', '.join(sel_list)} ▾"
            else:
                return f"🧩 {sel_list[0]}, {sel_list[1]} (+{len(sel_list)-2} weitere) ▾"

        btn_text = format_mod_btn_text(selected_mods)
        picker_btn = ctk.CTkButton(
            mod_container,
            text=btn_text,
            height=32,
            anchor="w",
            fg_color=("gray85", "gray25"),
            hover_color=("gray75", "gray35"),
            text_color=("gray10", "white"),
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
        browser_options = ["Firefox", "Edge", "Chrome", "Unbekannt"]
        raw_val = str(val) if val else ""
        selected_browsers = [b.strip() for b in raw_val.split(",") if b.strip()]

        b_frame = ctk.CTkFrame(row_frame, fg_color=("gray90", "gray20"), corner_radius=6)
        b_frame.pack(fill="x", pady=2)

        b_pills_box = ctk.CTkFrame(b_frame, fg_color="transparent")
        b_pills_box.pack(fill="x", padx=6, pady=4)

        b_vars: dict[str, ctk.BooleanVar] = {}
        b_btns: dict[str, ctk.CTkButton] = {}

        def update_browser_pills_ui():
            for b_opt, b_v in b_vars.items():
                is_sel = b_v.get()
                b_btns[b_opt].configure(
                    fg_color="dodgerblue" if is_sel else ("gray80", "gray30"),
                    text_color="white" if is_sel else ("gray10", "white"),
                )
            self.update_conditional_visibility()

        def on_browser_click(clicked_opt: str):
            if clicked_opt == "Unbekannt":
                new_state = not b_vars["Unbekannt"].get()
                b_vars["Unbekannt"].set(new_state)
                if new_state:
                    for o in ["Firefox", "Edge", "Chrome"]:
                        b_vars[o].set(False)
            else:
                new_state = not b_vars[clicked_opt].get()
                b_vars[clicked_opt].set(new_state)
                if new_state:
                    b_vars["Unbekannt"].set(False)

            update_browser_pills_ui()

        for b_opt in browser_options:
            is_b_on = b_opt in selected_browsers
            b_var = ctk.BooleanVar(value=is_b_on)
            b_vars[b_opt] = b_var

            btn = ctk.CTkButton(
                b_pills_box,
                text=b_opt,
                height=26,
                fg_color="dodgerblue" if is_b_on else ("gray80", "gray30"),
                hover_color="deepskyblue",
                text_color="white" if is_b_on else ("gray10", "white"),
                command=lambda opt=b_opt: on_browser_click(opt),
            )
            btn.pack(side="left", padx=4, pady=3)
            b_btns[b_opt] = btn

        target_widget_dict[f.field_id] = ("browser_pills", b_vars)

    def _render_date_field(self, row_frame: ctk.CTkFrame, f: SchemaField, val: Any, target_widget_dict: dict[str, Any], entry_kwargs: dict[str, Any]):
        entry_row = ctk.CTkFrame(row_frame, fg_color="transparent")
        entry_row.pack(fill="x")

        entry = ctk.CTkEntry(entry_row, placeholder_text=f.placeholder or "TT.MM.JJJJ", **entry_kwargs)
        if val:
            entry.insert(0, str(val))
        entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        from services.i18n_service import tr

        cal_btn = ctk.CTkButton(
            entry_row,
            text=tr("cockpit.calendar", "📅 Kalender"),
            width=95,
            fg_color="gray30",
            hover_color="gray40",
            command=lambda e=entry: self.open_calendar_picker(e),
        )
        cal_btn.pack(side="right")
        target_widget_dict[f.field_id] = (f.field_type, entry)

    def _render_dropdown_field(self, row_frame: ctk.CTkFrame, f: SchemaField, val: Any, target_widget_dict: dict[str, Any], is_missing: bool):
        options = f.options if f.options else ["-"]
        opt_kwargs: dict[str, Any] = {"button_color": "darkred", "fg_color": "firebrick"} if is_missing else {}
        combo = ctk.CTkOptionMenu(
            row_frame,
            values=options,
            command=lambda _val: self.update_conditional_visibility(),
            **opt_kwargs,
        )
        if val and str(val) in options:
            combo.set(str(val))
        combo.pack(fill="x")
        target_widget_dict[f.field_id] = (f.field_type, combo)

    def _render_boolean_field(self, row_frame: ctk.CTkFrame, f: SchemaField, val: Any, target_widget_dict: dict[str, Any], entry_kwargs: dict[str, Any], case: Case | None):
        fid_lower = f.field_id.lower()
        flabel_lower = f.label.lower()

        bool_var = ctk.BooleanVar(value=bool(val) if val is not None else False)
        chk_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        chk_frame.pack(fill="x")

        chk = ctk.CTkCheckBox(
            chk_frame,
            text=f.label,
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
                width=190,
                fg_color="darkblue",
                hover_color="blue",
                command=lambda c=case, v=bool_var: self.import_db_backup_file(c, v),
            )
            import_db_btn.pack(side="left", padx=15)

        target_widget_dict[f.field_id] = (f.field_type, bool_var)

        if is_db_backup_field and case:
            self.render_mini_attachment_section(row_frame, case)

    def _render_file_field(self, row_frame: ctk.CTkFrame, f: SchemaField, val: Any, target_widget_dict: dict[str, Any], entry_kwargs: dict[str, Any]):
        file_row = ctk.CTkFrame(row_frame, fg_color="transparent")
        file_row.pack(fill="x")

        file_entry = ctk.CTkEntry(
            file_row,
            placeholder_text=f.placeholder or "Keine Datei ausgewählt...",
            **entry_kwargs,
        )
        if val:
            file_entry.insert(0, str(val))
        file_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        def open_file_picker(e=file_entry, f_item=f):
            exts = f_item.allowed_extensions
            ftypes = [("Dateien", " ".join(f"*{x}" for x in exts))] if exts else [("Alle Dateien", "*.*")]
            chosen = filedialog.askopenfilename(title=f"Datei auswählen für '{f_item.label}'", filetypes=ftypes)
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

        from services.i18n_service import tr
        ctk.CTkButton(
            file_row,
            text=tr("dynamic_form.choose_file", "📁 Datei wählen..."),
            width=120,
            fg_color="dodgerblue",
            hover_color="deepskyblue",
            command=open_file_picker,
        ).pack(side="right")

        target_widget_dict[f.field_id] = (f.field_type, file_entry)

    def _render_number_field(self, row_frame: ctk.CTkFrame, f: SchemaField, val: Any, target_widget_dict: dict[str, Any], entry_kwargs: dict[str, Any]):
        from services.i18n_service import tr
        entry = ctk.CTkEntry(row_frame, placeholder_text=tr("dynamic_form.number_placeholder", "Zahl..."), **entry_kwargs)
        if val is not None:
            entry.insert(0, str(val))
        entry.pack(fill="x")
        target_widget_dict[f.field_id] = (f.field_type, entry)

    def _render_textbox_field(self, row_frame: ctk.CTkFrame, f: SchemaField, val: Any, target_widget_dict: dict[str, Any], entry_kwargs: dict[str, Any]):
        saved_height = 90
        if self.profile and self.profile.ui_settings:
            saved_height = self.profile.ui_settings.custom_textbox_heights.get(f.field_id, self.profile.ui_settings.textbox_height)

        textbox = ctk.CTkTextbox(row_frame, height=saved_height, **entry_kwargs)
        if val:
            textbox.insert("1.0", str(val))
        textbox.pack(fill="x", expand=True)

        from utils.ui_utils import enable_textbox_cursor_autoscroll
        enable_textbox_cursor_autoscroll(textbox)

        from ui.widgets.dynamic_form_widget import TextboxResizeHandle
        handle = TextboxResizeHandle(
            row_frame,
            target_textbox=textbox,
            field_id=f.field_id,
            profile=self.profile,
            storage_service=self.storage_service,
        )
        handle.pack(fill="x", pady=(2, 0))

        target_widget_dict[f.field_id] = ("textbox", textbox)

    def _render_text_entry_field(self, row_frame: ctk.CTkFrame, f: SchemaField, val: Any, target_widget_dict: dict[str, Any], entry_kwargs: dict[str, Any]):
        entry = ctk.CTkEntry(row_frame, placeholder_text=f.placeholder or "Text...", **entry_kwargs)
        if val:
            entry.insert(0, str(val))
        entry.pack(fill="x")
        target_widget_dict[f.field_id] = (f.field_type, entry)
