import os
import shutil
import customtkinter as ctk
from tkinter import filedialog
from typing import Any, Callable
from models.schema import QuestionSchema
from models.case import Case
from models.profile import UserProfile
from services.storage_service import StorageService
from services.attachment_service import AttachmentService
from enums import FieldType
from constants import DEFAULT_MODULE_TAGS


class TextboxResizeHandle(ctk.CTkFrame):
    """Interactive drag handle underneath CTkTextbox to adjust height with the mouse and save to profile."""

    def __init__(
        self,
        parent,
        target_textbox: ctk.CTkTextbox,
        field_id: str,
        profile: UserProfile | None,
        storage_service: StorageService | None,
    ):
        super().__init__(parent, fg_color=("gray75", "gray35"), height=7, cursor="sb_v_double_arrow")
        self.target_textbox = target_textbox
        self.field_id = field_id
        self.profile = profile
        self.storage_service = storage_service
        self.start_y = 0
        self.start_height = 0

        self.bind("<Button-1>", self.on_press)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.on_release)

    def on_press(self, event):
        self.start_y = event.y_root
        self.start_height = self.target_textbox.winfo_height()

    def on_drag(self, event):
        delta = event.y_root - self.start_y
        new_h = max(50, min(600, self.start_height + delta))
        self.target_textbox.configure(height=new_h)

    def on_release(self, event):
        final_h = self.target_textbox.winfo_height()
        if self.profile:
            self.profile.ui_settings.custom_textbox_heights[self.field_id] = final_h
            self.profile.ui_settings.textbox_height = final_h
            if self.storage_service:
                self.storage_service.save_profile(self.profile)


class ModuleTagPickerPopup(ctk.CTkToplevel):
    """Clean, searchable multiselect popup dialog for choosing Programmbereich tags."""

    def __init__(self, parent, available_tags: list[str], selected_tags: list[str], on_apply: Callable[[list[str]], None]):
        super().__init__(parent)
        self.available_tags = available_tags
        self.selected_tags = set(selected_tags)
        self.on_apply = on_apply

        self.title("🧩 Programmbereiche auswählen")
        self.geometry("450x440")
        self.minsize(380, 320)
        from utils.ui_utils import center_window
        center_window(self, 450, 440)

        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        self.render_tag_checkboxes()

    def create_widgets(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(hdr, text="🧩 Programmbereiche auswählen:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")

        # Search Bar & Quick Action Buttons
        tools_frame = ctk.CTkFrame(self, fg_color="transparent")
        tools_frame.pack(fill="x", padx=12, pady=(0, 6))

        self.search_entry = ctk.CTkEntry(tools_frame, placeholder_text="🔍 Programmbereich suchen...")
        self.search_entry.pack(fill="x", pady=(0, 6))
        self.search_entry.bind("<KeyRelease>", lambda e: self.render_tag_checkboxes())

        btn_row = ctk.CTkFrame(tools_frame, fg_color="transparent")
        btn_row.pack(fill="x")

        ctk.CTkButton(btn_row, text="Alle auswählen", width=110, height=24, fg_color="gray30", command=self.select_all).pack(side="left", padx=(0, 5))
        ctk.CTkButton(btn_row, text="Keine auswählen", width=110, height=24, fg_color="gray30", command=self.select_none).pack(side="left")

        # Scrollable List
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=12, pady=5)
        from utils.ui_utils import enable_auto_hiding_scrollbar
        enable_auto_hiding_scrollbar(self.scroll_frame)

        # Footer
        ftr = ctk.CTkFrame(self, fg_color="transparent")
        ftr.pack(fill="x", padx=12, pady=(4, 10))

        ctk.CTkButton(ftr, text="✓ Übernehmen & Schließen", fg_color="forestgreen", command=self.apply_and_close).pack(side="right")

    def render_tag_checkboxes(self):
        for w in self.scroll_frame.winfo_children():
            w.destroy()

        query = self.search_entry.get().strip().lower()
        filtered = [t for t in self.available_tags if query in t.lower()] if query else self.available_tags

        if not filtered:
            ctk.CTkLabel(self.scroll_frame, text="Kein Programmbereich gefunden.", text_color="gray").pack(pady=15)
        else:
            for tag in filtered:
                is_on = tag in self.selected_tags
                bvar = ctk.BooleanVar(value=is_on)

                def make_chk_cb(t=tag, v=bvar):
                    if v.get():
                        self.selected_tags.add(t)
                    else:
                        self.selected_tags.discard(t)

                chk = ctk.CTkCheckBox(
                    self.scroll_frame,
                    text=tag,
                    variable=bvar,
                    command=make_chk_cb,
                    font=ctk.CTkFont(size=12),
                )
                chk.pack(anchor="w", pady=4, padx=5)

        canvas = getattr(self.scroll_frame, "_parent_canvas", getattr(self.scroll_frame, "_canvas", None))
        if canvas:
            canvas.yview_moveto(0.0)

    def select_all(self):
        for t in self.available_tags:
            self.selected_tags.add(t)
        self.render_tag_checkboxes()

    def select_none(self):
        self.selected_tags.clear()
        self.render_tag_checkboxes()

    def apply_and_close(self):
        self.on_apply(sorted(list(self.selected_tags)))
        self.destroy()


class DynamicFormWidget(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        profile: UserProfile | None = None,
        storage_service: StorageService | None = None,
        attachment_service: AttachmentService | None = None,
        on_manage_module_tags: Callable[[], None] | None = None,
    ):
        super().__init__(parent)
        self.schema: QuestionSchema | None = None
        self.profile = profile
        self.storage_service = storage_service
        self.attachment_service = attachment_service
        self.on_manage_module_tags = on_manage_module_tags
        self.current_case: Case | None = None

        self.field_widgets: dict[str, Any] = {}
        self.create_widgets()

    def create_widgets(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        from utils.ui_utils import enable_auto_hiding_scrollbar
        enable_auto_hiding_scrollbar(self.scroll_frame)

    def _scroll_form_canvas(self, delta: int):
        try:
            canvas = getattr(self.scroll_frame, "_parent_canvas", getattr(self.scroll_frame, "_canvas", None))
            if canvas and hasattr(canvas, "yview_scroll"):
                canvas.yview_scroll(int(-1 * (delta / 120)), "units")
        except Exception:
            pass

    def _bind_mouse_wheel_recursive(self, widget):
        """Recursively binds mouse wheel scrolling so the form stays 100% responsive everywhere, including over textboxes."""
        def _on_mouse_wheel(event):
            self._scroll_form_canvas(event.delta)

        def _on_textbox_mouse_wheel(event, textbox):
            try:
                tk_text = getattr(textbox, "_textbox", None)
                if tk_text:
                    top, bottom = tk_text.yview()
                    all_text_visible = (top <= 0.001 and bottom >= 0.999)
                    if not all_text_visible:
                        can_scroll_up = (event.delta > 0 and top > 0.001)
                        can_scroll_down = (event.delta < 0 and bottom < 0.999)
                        if can_scroll_up or can_scroll_down:
                            return  # Allow inner textbox text scrolling ONLY when text exceeds visible lines
                # Scroll the main view whenever text fits inside the visible textbox display
                self._scroll_form_canvas(event.delta)
                return "break"
            except Exception:
                pass

        if isinstance(widget, ctk.CTkTextbox):
            tb_target = getattr(widget, "_textbox", widget)
            try:
                tb_target.bind("<MouseWheel>", lambda e, tb=widget: _on_textbox_mouse_wheel(e, tb))
            except Exception:
                pass
        else:
            for w in (widget, getattr(widget, "_label", None), getattr(widget, "_canvas", None), getattr(widget, "_entry", None)):
                if w and hasattr(w, "bind"):
                    try:
                        w.bind("<MouseWheel>", _on_mouse_wheel)
                    except Exception:
                        pass

        if hasattr(widget, "winfo_children"):
            for child in widget.winfo_children():
                self._bind_mouse_wheel_recursive(child)

    def load_schema(
        self,
        schema: QuestionSchema | None,
        form_data: dict[str, Any],
        missing_fields: list[str] | None = None,
        case: Case | None = None,
    ):
        self.schema = schema
        self.current_case = case
        missing_fields = missing_fields or []

        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.field_widgets.clear()

        if not schema or not schema.fields:
            ctk.CTkLabel(self.scroll_frame, text="Keine Formularfelder definiert.").pack(pady=20)
            return

        sorted_fields = sorted(schema.fields, key=lambda f: f.order)

        for f in sorted_fields:
            row_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=6, padx=5)

            req_mark = " *" if f.required else ""
            label_text = f"{f.label}{req_mark}:"

            label_row = ctk.CTkFrame(row_frame, fg_color="transparent")
            label_row.pack(fill="x", anchor="w", pady=(0, 2))

            lbl = ctk.CTkLabel(
                label_row,
                text=label_text,
                anchor="w",
                font=ctk.CTkFont(size=12, weight="bold" if f.required else "normal"),
            )
            lbl.pack(side="left")

            val = form_data.get(f.field_id)
            is_missing = f.field_id in missing_fields
            entry_kwargs: dict[str, Any] = {"border_color": "red", "border_width": 2} if is_missing else {}

            fid_lower = f.field_id.lower()
            flabel_lower = f.label.lower()

            # 1. PROGRAMMBEREICH / MODULE TAGS COMPACT DROPDOWN POPUP
            if fid_lower in ("module_name", "programmbereich", "programmteil") or "programm" in flabel_lower or "bereich" in flabel_lower:
                if self.on_manage_module_tags:
                    ctk.CTkButton(
                        label_row,
                        text="⚙ Programmbereiche verwalten",
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

                    ModuleTagPickerPopup(
                        self.winfo_toplevel(),
                        available_tags=available_mods,
                        selected_tags=holder["selected"],
                        on_apply=on_apply_mods,
                    )

                picker_btn.configure(command=open_mod_picker)
                self.field_widgets[f.field_id] = ("module_picker", mod_selected_holder)

            # 2. BROWSER MULTISELECT WITH MUTUAL EXCLUSION FOR "UNBEKANNT"
            elif fid_lower in ("tested_browsers", "browser", "welcher_browser") or "browser" in flabel_lower:
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

                self.field_widgets[f.field_id] = ("browser_pills", b_vars)

            # 3. DATE FIELD
            elif (
                f.field_type == FieldType.DATE
                or any(k in fid_lower or k in flabel_lower for k in ("datum", "date", "frist"))
            ) and f.field_type not in (FieldType.DROPDOWN, FieldType.BOOLEAN):
                entry_row = ctk.CTkFrame(row_frame, fg_color="transparent")
                entry_row.pack(fill="x")

                entry = ctk.CTkEntry(entry_row, placeholder_text=f.placeholder or "TT.MM.JJJJ", **entry_kwargs)
                if val:
                    entry.insert(0, str(val))
                entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

                cal_btn = ctk.CTkButton(
                    entry_row,
                    text="📅 Kalender",
                    width=95,
                    fg_color="gray30",
                    hover_color="gray40",
                    command=lambda e=entry: self.open_calendar_picker(e),
                )
                cal_btn.pack(side="right")
                self.field_widgets[f.field_id] = (f.field_type, entry)

            # 4. DROPDOWN FIELD
            elif f.field_type == FieldType.DROPDOWN:
                options = f.options if f.options else ["-"]
                opt_kwargs: dict[str, Any] = {"button_color": "darkred", "fg_color": "firebrick"} if is_missing else {}
                combo = ctk.CTkOptionMenu(row_frame, values=options, **opt_kwargs)
                if val and str(val) in options:
                    combo.set(str(val))
                combo.pack(fill="x")
                self.field_widgets[f.field_id] = (f.field_type, combo)

            # 5. BOOLEAN / CHECKBOX FIELD
            elif f.field_type == FieldType.BOOLEAN:
                bool_var = ctk.BooleanVar(value=bool(val) if val is not None else False)
                chk_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
                chk_frame.pack(fill="x")

                chk = ctk.CTkCheckBox(chk_frame, text=f.label, variable=bool_var, **entry_kwargs)
                chk.pack(side="left", anchor="w")

                is_db_backup_field = "database_dump" in fid_lower or "backup" in fid_lower or "datenbank" in flabel_lower

                if is_db_backup_field and case:
                    import_db_btn = ctk.CTkButton(
                        chk_frame,
                        text="📁 .backup-Datei importieren...",
                        width=190,
                        fg_color="darkblue",
                        hover_color="blue",
                        command=lambda c=case, v=bool_var: self.import_db_backup_file(c, v),
                    )
                    import_db_btn.pack(side="left", padx=15)

                self.field_widgets[f.field_id] = (f.field_type, bool_var)

                if is_db_backup_field and case:
                    self.render_mini_attachment_section(row_frame, case)

            # 6. NUMBER FIELD
            elif f.field_type == FieldType.NUMBER:
                entry = ctk.CTkEntry(row_frame, placeholder_text="Zahl...", **entry_kwargs)
                if val is not None:
                    entry.insert(0, str(val))
                entry.pack(fill="x")
                self.field_widgets[f.field_id] = (f.field_type, entry)

            # 7. MULTILINE TEXTBOX FIELD
            elif any(k in fid_lower or k in flabel_lower for k in (
                "error_message", "reproduction", "steps", "expected", "schritte", "beschreibung",
                "erklärung", "verhalten", "stack_trace", "log", "notiz", "details", "begründung",
                "dateien", "dateianfragen", "files", "anfragen", "liste", "korrekturdateien"
            )):
                saved_height = 90
                if self.profile and self.profile.ui_settings:
                    saved_height = self.profile.ui_settings.custom_textbox_heights.get(f.field_id, self.profile.ui_settings.textbox_height)

                textbox = ctk.CTkTextbox(row_frame, height=saved_height, **entry_kwargs)
                if val:
                    textbox.insert("1.0", str(val))
                textbox.pack(fill="x", expand=True)

                handle = TextboxResizeHandle(
                    row_frame,
                    target_textbox=textbox,
                    field_id=f.field_id,
                    profile=self.profile,
                    storage_service=self.storage_service,
                )
                handle.pack(fill="x", pady=(2, 0))

                self.field_widgets[f.field_id] = ("textbox", textbox)

            # 8. STANDARD SINGLE-LINE TEXT ENTRY
            else:
                entry = ctk.CTkEntry(row_frame, placeholder_text=f.placeholder or "Text...", **entry_kwargs)
                if val:
                    entry.insert(0, str(val))
                entry.pack(fill="x")
                self.field_widgets[f.field_id] = (f.field_type, entry)

        # Bind mouse wheel recursively so form is 100% responsive when scrolling
        self._bind_mouse_wheel_recursive(self.scroll_frame)

    def _get_target_dir(self, case: Case) -> str:
        if self.attachment_service:
            return str(self.attachment_service.get_case_attachment_dir(case))
        elif case.attachment_directory:
            return case.attachment_directory
        else:
            return os.path.join("data", "attachments", case.case_id)

    # --- DB BACKUP IMPORT & MINI ATTACHMENT SECTION ---
    def import_db_backup_file(self, case: Case, bool_var: ctk.BooleanVar):
        file_path = filedialog.askopenfilename(
            title="Datenbank-Backup (.backup) importieren",
            filetypes=[("Backup-Dateien (*.backup)", "*.backup"), ("Alle Dateien", "*.*")],
        )
        if not file_path:
            return

        target_dir = self._get_target_dir(case)
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, "data-al.backup")

        shutil.copy2(file_path, target_path)
        bool_var.set(True)
        case.form_data["database_dump_provided"] = True

        if hasattr(self, "mini_attach_scroll"):
            self.refresh_mini_attachment_list(case)

    def render_mini_attachment_section(self, parent_frame, case: Case):
        attach_box = ctk.CTkFrame(parent_frame, fg_color=("gray92", "gray18"), corner_radius=6)
        attach_box.pack(fill="x", pady=(6, 4))

        hdr_row = ctk.CTkFrame(attach_box, fg_color="transparent")
        hdr_row.pack(fill="x", padx=8, pady=4)

        self.mini_attach_hdr_label = ctk.CTkLabel(
            hdr_row,
            text="📎 Abgelegte Dateien im Fallordner: Keine (0)",
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        self.mini_attach_hdr_label.pack(side="left")

        ctk.CTkButton(
            hdr_row,
            text="+ Datei(en) importieren...",
            height=24,
            width=150,
            fg_color="gray30",
            hover_color="gray40",
            command=lambda: self.import_general_files(case),
        ).pack(side="right")

        self.mini_attach_scroll = ctk.CTkScrollableFrame(attach_box, height=90, fg_color="transparent")

        self.refresh_mini_attachment_list(case)

    def import_general_files(self, case: Case):
        files = filedialog.askopenfilenames(title="Dateien in Fallordner importieren")
        if not files:
            return

        target_dir = self._get_target_dir(case)
        os.makedirs(target_dir, exist_ok=True)
        for f in files:
            shutil.copy2(f, os.path.join(target_dir, os.path.basename(f)))

        self.refresh_mini_attachment_list(case)

    def refresh_mini_attachment_list(self, case: Case):
        if not hasattr(self, "mini_attach_scroll"):
            return

        for w in self.mini_attach_scroll.winfo_children():
            w.destroy()

        target_dir = self._get_target_dir(case)
        files = []
        if os.path.exists(target_dir):
            files = [f for f in os.listdir(target_dir) if os.path.isfile(os.path.join(target_dir, f))]

        if not files:
            self.mini_attach_hdr_label.configure(text="📎 Abgelegte Dateien im Fallordner: Keine (0)")
            self.mini_attach_scroll.pack_forget()
            return

        self.mini_attach_hdr_label.configure(text=f"📎 Abgelegte Dateien im Fallordner ({len(files)}):")
        self.mini_attach_scroll.pack(fill="both", expand=True, padx=5, pady=(0, 4))

        for f_name in files:
            f_path = os.path.join(target_dir, f_name)
            size_kb = os.path.getsize(f_path) / 1024.0

            frow = ctk.CTkFrame(self.mini_attach_scroll, fg_color=("gray85", "gray25"), height=24)
            frow.pack(fill="x", pady=2)

            is_backup = f_name == "data-al.backup"
            icon = "🗄" if is_backup else "📄"

            lbl_txt = f"{icon} {f_name} ({size_kb:.1f} KB)"
            ctk.CTkLabel(frow, text=lbl_txt, font=ctk.CTkFont(size=11), anchor="w").pack(side="left", padx=8, expand=True, fill="x")

            ctk.CTkButton(
                frow,
                text="👁 Öffnen",
                width=65,
                height=20,
                fg_color="gray35",
                hover_color="gray45",
                command=lambda p=f_path: self.open_file_external(p),
            ).pack(side="right", padx=4)

    def open_file_external(self, filepath: str):
        try:
            os.startfile(filepath)
        except Exception:
            pass

    def open_calendar_picker(self, entry: ctk.CTkEntry):
        from ui.widgets.date_picker import CalendarDialog
        curr_val = entry.get().strip()

        def on_sel(d_str: str):
            entry.delete(0, "end")
            entry.insert(0, d_str)

        CalendarDialog(
            self.winfo_toplevel(),
            initial_date=curr_val,
            include_time=True if ":" in curr_val or "uhr" in curr_val.lower() else False,
            on_date_selected=on_sel,
        )

    def get_form_data(self) -> dict[str, Any]:
        data = {}
        for fid, (ftype, widget) in self.field_widgets.items():
            if ftype == "module_picker":
                # dict with 'selected' list
                selected = widget.get("selected", [])
                data[fid] = ", ".join(selected)
            elif ftype == "module_pills":
                selected = [m for m, bvar in widget.items() if bvar.get()]
                data[fid] = ", ".join(selected)
            elif ftype == "browser_pills":
                selected = [b for b, bvar in widget.items() if bvar.get()]
                data[fid] = ", ".join(selected)
            elif ftype == "textbox":
                data[fid] = widget.get("1.0", "end-1c").strip()
            elif ftype == FieldType.BOOLEAN:
                data[fid] = widget.get()
            elif ftype == FieldType.DROPDOWN:
                data[fid] = widget.get()
            elif ftype == FieldType.NUMBER:
                txt = widget.get().strip()
                if txt:
                    try:
                        data[fid] = float(txt) if "." in txt else int(txt)
                    except ValueError:
                        data[fid] = txt
                else:
                    data[fid] = None
            else:
                data[fid] = widget.get().strip()
        return data
