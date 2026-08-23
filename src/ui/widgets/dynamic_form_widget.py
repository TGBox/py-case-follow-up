import customtkinter as ctk
from typing import Any
from src.models.schema import QuestionSchema
from src.enums import FieldType


class DynamicFormWidget(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.schema: QuestionSchema | None = None
        self.field_widgets: dict[str, Any] = {}
        self.create_widgets()

    def create_widgets(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

    def load_schema(self, schema: QuestionSchema | None, form_data: dict[str, Any], missing_fields: list[str] | None = None):
        self.schema = schema
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
            row_frame.pack(fill="x", pady=5, padx=5)

            # Label
            req_mark = " *" if f.required else ""
            label_text = f"{f.label}{req_mark}:"
            lbl = ctk.CTkLabel(row_frame, text=label_text, anchor="w", font=ctk.CTkFont(size=12, weight="bold" if f.required else "normal"))
            lbl.pack(anchor="w", pady=(0, 2))

            val = form_data.get(f.field_id)
            is_missing = f.field_id in missing_fields

            border_kwargs = {"border_color": "red", "border_width": 2} if is_missing else {}

            if f.field_type == FieldType.DROPDOWN:
                options = f.options if f.options else [""]
                combo = ctk.CTkOptionMenu(row_frame, values=options, **border_kwargs)
                if val and str(val) in options:
                    combo.set(str(val))
                combo.pack(fill="x")
                self.field_widgets[f.field_id] = (f.field_type, combo)

            elif f.field_type == FieldType.BOOLEAN:
                bool_var = ctk.BooleanVar(value=bool(val) if val is not None else False)
                chk = ctk.CTkCheckBox(row_frame, text=f.label, variable=bool_var, **border_kwargs)
                chk.pack(anchor="w")
                self.field_widgets[f.field_id] = (f.field_type, bool_var)

            elif f.field_type == FieldType.NUMBER:
                entry = ctk.CTkEntry(row_frame, placeholder_text="Zahl...", **border_kwargs)
                if val is not None:
                    entry.insert(0, str(val))
                entry.pack(fill="x")
                self.field_widgets[f.field_id] = (f.field_type, entry)

            else:
                # Text
                entry = ctk.CTkEntry(row_frame, placeholder_text=f.placeholder or "Text...", **border_kwargs)
                if val:
                    entry.insert(0, str(val))
                entry.pack(fill="x")
                self.field_widgets[f.field_id] = (f.field_type, entry)

    def get_form_data(self) -> dict[str, Any]:
        data = {}
        for fid, (ftype, widget) in self.field_widgets.items():
            if ftype == FieldType.BOOLEAN:
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
