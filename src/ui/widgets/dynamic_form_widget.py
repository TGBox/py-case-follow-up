import os
import shutil
import customtkinter as ctk
from tkinter import filedialog
from typing import Any
from collections.abc import Callable
from constants import (
    BORDER_COLOR_MISSING,
    BORDER_WIDTH_CARD,
    BORDER_WIDTH_MISSING,
    BTN_HEIGHT_ADD_CARD,
    BTN_HEIGHT_REMOVE_CARD,
    BTN_HEIGHT_TAG_QUICK,
    BTN_WIDTH_IMPORT_FILES,
    BTN_WIDTH_OPEN_FILE,
    BTN_WIDTH_REMOVE_CARD,
    BTN_WIDTH_TAG_QUICK,
    BYTES_PER_KB,
    CHECKBOX_TAG_WIDTH,
    COLOR_ACCENT_BLUE,
    COLOR_BELL_BTN,
    COLOR_BTN_SECONDARY,
    COLOR_CARD_BORDER_DEFAULT,
    COLOR_DANGER,
    COLOR_DANGER_HOVER,
    COLOR_MINI_ATTACH_BG,
    COLOR_MINI_ATTACH_ROW_BG,
    COLOR_MUTED_LABEL,
    COLOR_OPEN_FILE_BTN,
    COLOR_OPEN_FILE_BTN_HOVER,
    COLOR_REPEATABLE_CARD_BG,
    COLOR_RESIZE_HANDLE,
    COLOR_SUCCESS,
    COLOR_SUCCESS_HOVER,
    COLOR_USER_BTN_TEXT,
    CORNER_RADIUS_CARD,
    CURSOR_HAND,
    CURSOR_RESIZE_V,
    DEBOUNCE_KEY_TAG_SEARCH,
    DEFAULT_ATTACHMENTS_DIR,
    FILE_NAME_DATA_BACKUP,
    FONT_SIZE_BODY,
    FONT_SIZE_CONFIRM,
    FONT_SIZE_SM,
    FONT_SIZE_SUBTITLE,
    FONT_WEIGHT_BOLD,
    FONT_WEIGHT_NORMAL,
    HEIGHT_MINI_ATTACH_ROW,
    HEIGHT_MINI_ATTACH_SCROLL,
    HEIGHT_OPEN_FILE_BTN,
    HEIGHT_RESIZE_HANDLE,
    MOUSEWHEEL_DELTA_UNIT,
    PAD_10,
    PAD_2XL,
    PAD_CONTAINER,
    PAD_GAP,
    PAD_LG,
    PAD_MD,
    PAD_NONE,
    PAD_SM,
    PAD_XL,
    PAD_XS,
    POPUP_TAG_PICKER_GEOMETRY,
    POPUP_TAG_PICKER_HEIGHT,
    POPUP_TAG_PICKER_MIN_HEIGHT,
    POPUP_TAG_PICKER_MIN_WIDTH,
    POPUP_TAG_PICKER_WIDTH,
    SEARCH_DEBOUNCE_MS,
    SPACING_SM,
    TEXTBOX_DEFAULT_WIDTH,
    TEXTBOX_MAX_HEIGHT,
    TEXTBOX_MIN_HEIGHT,
    TEXTBOX_VISIBLE_THRESHOLD_BOTTOM,
    TEXTBOX_VISIBLE_THRESHOLD_TOP,
)
from enums import FieldType
from models.case import Case
from models.profile import UserProfile
from models.schema import QuestionSchema, SchemaField
from services.attachment_service import AttachmentService
from services.storage_service import StorageService
from ui.widgets.dynamic_form_field_renderers import FieldRendererMixin


class TextboxResizeHandle(ctk.CTkFrame):
    """Interactive drag handle underneath CTkTextbox to adjust height with the mouse and save to profile."""

    def __init__(
        self,
        parent,
        target_textbox: ctk.CTkTextbox,
        field_id: str,
        profile: UserProfile | None,
        storage_service: StorageService | None,
        width: int = TEXTBOX_DEFAULT_WIDTH,
    ):
        super().__init__(parent, fg_color=COLOR_RESIZE_HANDLE, height=HEIGHT_RESIZE_HANDLE, width=width, cursor=CURSOR_RESIZE_V)
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
        new_h = max(TEXTBOX_MIN_HEIGHT, min(TEXTBOX_MAX_HEIGHT, self.start_height + delta))
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
        from services.i18n_service import tr
        self.title(tr("dynamic_form.select_tags_dialog_title", "🧩 Programmbereiche auswählen"))
        self.geometry(POPUP_TAG_PICKER_GEOMETRY)
        self.minsize(POPUP_TAG_PICKER_MIN_WIDTH, POPUP_TAG_PICKER_MIN_HEIGHT)
        from utils.ui_utils import center_window
        center_window(self, POPUP_TAG_PICKER_WIDTH, POPUP_TAG_PICKER_HEIGHT)

        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        self.render_tag_checkboxes()

    def create_widgets(self):
        from services.i18n_service import tr

        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=PAD_LG, pady=(PAD_MD + PAD_XS, PAD_SM))

        ctk.CTkLabel(hdr, text=tr("dynamic_form.select_tags", "🧩 Programmbereiche auswählen:"), font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight=FONT_WEIGHT_BOLD)).pack(anchor="w")

        # Search Bar & Quick Action Buttons
        tools_frame = ctk.CTkFrame(self, fg_color="transparent")
        tools_frame.pack(fill="x", padx=PAD_LG, pady=(0, PAD_MD - PAD_XS))

        self.search_entry = ctk.CTkEntry(tools_frame, placeholder_text=tr("dynamic_form.search_tags", "🔍 Programmbereich suchen..."))
        self.search_entry.pack(fill="x", pady=(0, PAD_MD - PAD_XS))
        self.search_entry.bind("<KeyRelease>", self._on_tag_search_keyrelease)

        btn_row = ctk.CTkFrame(tools_frame, fg_color="transparent")
        btn_row.pack(fill="x")

        ctk.CTkButton(btn_row, text=tr("dynamic_form.select_all", "Alle auswählen"), width=BTN_WIDTH_TAG_QUICK, height=BTN_HEIGHT_TAG_QUICK, fg_color=COLOR_BTN_SECONDARY, command=self.select_all).pack(side="left", padx=(0, PAD_CONTAINER))
        ctk.CTkButton(btn_row, text=tr("dynamic_form.select_none", "Keine auswählen"), width=BTN_WIDTH_TAG_QUICK, height=BTN_HEIGHT_TAG_QUICK, fg_color=COLOR_BTN_SECONDARY, command=self.select_none).pack(side="left")

        # Scrollable List
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_CONTAINER)
        from utils.ui_utils import enable_auto_hiding_scrollbar
        enable_auto_hiding_scrollbar(self.scroll_frame)

        # Footer
        ftr = ctk.CTkFrame(self, fg_color="transparent")
        ftr.pack(fill="x", padx=PAD_LG, pady=(PAD_SM, PAD_MD + PAD_XS))

        ctk.CTkButton(ftr, text=tr("dynamic_form.apply_close", "Übernehmen & Schließen"), fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOVER, command=self.apply_and_close).pack(side="right")

    def _on_tag_search_keyrelease(self, event=None):
        """Debounces the tag filter so the checkbox list is rebuilt once per typing pause."""
        from utils.ui_utils import debounce
        debounce(self, DEBOUNCE_KEY_TAG_SEARCH, SEARCH_DEBOUNCE_MS, self.render_tag_checkboxes)

    def render_tag_checkboxes(self):
        from services.i18n_service import tr
        from utils.ui_utils import create_highlighted_label, bind_mouse_wheel_to_canvas

        for w in self.scroll_frame.winfo_children():
            w.destroy()

        raw_query = self.search_entry.get().strip() if hasattr(self, "search_entry") else ""
        query = raw_query.lower()
        filtered = [t for t in self.available_tags if query in t.lower()] if query else self.available_tags

        if not filtered:
            ctk.CTkLabel(self.scroll_frame, text=tr("dynamic_form.no_tags", "Kein Programmbereich gefunden."), text_color=COLOR_MUTED_LABEL).pack(pady=PAD_XL)
        else:
            for tag in filtered:
                is_on = tag in self.selected_tags
                bvar = ctk.BooleanVar(value=is_on)

                def make_chk_cb(t=tag, v=bvar):
                    if v.get():
                        self.selected_tags.add(t)
                    else:
                        self.selected_tags.discard(t)

                if raw_query and query in tag.lower():
                    row = ctk.CTkFrame(self.scroll_frame, fg_color="transparent", cursor=CURSOR_HAND)
                    row.pack(fill="x", pady=SPACING_SM, padx=PAD_CONTAINER)

                    def toggle_cb(e=None, t=tag, v=bvar):
                        new_val = not v.get()
                        v.set(new_val)
                        if new_val:
                            self.selected_tags.add(t)
                        else:
                            self.selected_tags.discard(t)

                    chk = ctk.CTkCheckBox(
                        row,
                        text="",
                        variable=bvar,
                        command=make_chk_cb,
                        width=CHECKBOX_TAG_WIDTH,
                    )
                    chk.pack(side="left", padx=0)

                    lbl = create_highlighted_label(
                        row,
                        text=tag,
                        query=raw_query,
                        font=ctk.CTkFont(size=FONT_SIZE_BODY),
                        text_color=COLOR_USER_BTN_TEXT,
                        bg_color="transparent",
                        wrap="none",
                        on_click=toggle_cb,
                        scroll_frame=self.scroll_frame,
                    )
                    lbl.pack(side="left", fill="x", expand=True)

                    row.bind("<Button-1>", toggle_cb)
                    bind_mouse_wheel_to_canvas(row, self.scroll_frame)
                else:
                    chk = ctk.CTkCheckBox(
                        self.scroll_frame,
                        text=tag,
                        variable=bvar,
                        command=make_chk_cb,
                        font=ctk.CTkFont(size=FONT_SIZE_BODY),
                    )
                    chk.pack(anchor="w", pady=SPACING_SM, padx=PAD_CONTAINER)
                    bind_mouse_wheel_to_canvas(chk, self.scroll_frame)

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


class DynamicFormWidget(FieldRendererMixin, ctk.CTkFrame):
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
        self._field_border_defaults: dict[str, tuple[Any, Any]] = {}
        self.create_widgets()

    def create_widgets(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=PAD_CONTAINER, pady=PAD_CONTAINER)
        from utils.ui_utils import enable_auto_hiding_scrollbar
        enable_auto_hiding_scrollbar(self.scroll_frame)

    def _scroll_form_canvas(self, delta: int):
        try:
            canvas = getattr(self.scroll_frame, "_parent_canvas", getattr(self.scroll_frame, "_canvas", None))
            if canvas and hasattr(canvas, "yview_scroll"):
                canvas.yview_scroll(int(-1 * (delta / MOUSEWHEEL_DELTA_UNIT)), "units")
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
                    all_text_visible = (top <= TEXTBOX_VISIBLE_THRESHOLD_TOP and bottom >= TEXTBOX_VISIBLE_THRESHOLD_BOTTOM)
                    if not all_text_visible:
                        can_scroll_up = (event.delta > 0 and top > TEXTBOX_VISIBLE_THRESHOLD_TOP)
                        can_scroll_down = (event.delta < 0 and bottom < TEXTBOX_VISIBLE_THRESHOLD_BOTTOM)
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

    def _extract_widget_value(self, ftype: str, widget: Any) -> Any:
        if ftype == "module_picker":
            selected = widget.get("selected", [])
            return ", ".join(selected)
        elif ftype in ("module_pills", "browser_pills"):
            selected = [k for k, bvar in widget.items() if bvar.get()]
            return ", ".join(selected)
        elif ftype == "textbox":
            return widget.get("1.0", "end-1c").strip()
        elif ftype == FieldType.BOOLEAN:
            return widget.get()
        elif ftype == FieldType.DROPDOWN:
            return widget.get()
        elif ftype == FieldType.NUMBER:
            txt = widget.get().strip()
            if txt:
                try:
                    return float(txt) if "." in txt else int(txt)
                except ValueError:
                    return txt
            else:
                return None
        else:
            return widget.get().strip()

    def render_single_field(
        self,
        parent_frame: ctk.CTkFrame,
        f: SchemaField,
        val: Any,
        target_widget_dict: dict[str, Any],
        missing_fields: list[str],
        case: Case | None = None,
    ):
        row_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        row_frame.pack(fill="x", pady=PAD_GAP, padx=PAD_CONTAINER)
        self.field_row_frames[f.field_id] = row_frame

        req_mark = " *" if f.required else ""
        label_text = f"{f.label}{req_mark}:"

        label_row = ctk.CTkFrame(row_frame, fg_color="transparent")
        label_row.pack(fill="x", anchor="w", pady=(PAD_NONE, PAD_XS))

        lbl = ctk.CTkLabel(
            label_row,
            text=label_text,
            anchor="w",
            font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD if f.required else FONT_WEIGHT_NORMAL),
        )
        lbl.pack(side="left")

        is_missing = f.field_id in missing_fields
        # The red border is applied after construction rather than through the
        # constructor, so _set_field_highlight can record each widget's real
        # default first. That is what makes the highlight removable later
        # without rebuilding the whole form.
        entry_kwargs: dict[str, Any] = {}

        fid_lower = f.field_id.lower()
        flabel_lower = f.label.lower()

        # Delegiert an FieldRendererMixin (ausgelagert nach dynamic_form_field_renderers.py):
        # je eine _render_*_field()-Methode pro Feldtyp-Zweig, gleiche Reihenfolge/Bedingungen wie zuvor.

        # 1. PROGRAMMBEREICH / MODULE TAGS COMPACT DROPDOWN POPUP
        if fid_lower in ("module_name", "programmbereich", "programmteil") or "programm" in flabel_lower or "bereich" in flabel_lower:
            self._render_module_tags_field(row_frame, label_row, f, val, target_widget_dict)

        # 2. BROWSER MULTISELECT WITH MUTUAL EXCLUSION FOR "UNBEKANNT"
        elif fid_lower in ("tested_browsers", "browser", "welcher_browser") or "browser" in flabel_lower:
            self._render_browser_multiselect_field(row_frame, f, val, target_widget_dict)

        # 3. DATE FIELD
        elif (
            f.field_type == FieldType.DATE
            or any(k in fid_lower or k in flabel_lower for k in ("datum", "date", "frist"))
        ) and f.field_type not in (FieldType.DROPDOWN, FieldType.BOOLEAN, FieldType.FILE):
            self._render_date_field(row_frame, f, val, target_widget_dict, entry_kwargs)

        # 4. DROPDOWN FIELD
        elif f.field_type == FieldType.DROPDOWN:
            self._render_dropdown_field(row_frame, f, val, target_widget_dict, is_missing)

        # 5. BOOLEAN / CHECKBOX FIELD
        elif f.field_type == FieldType.BOOLEAN:
            self._render_boolean_field(row_frame, f, val, target_widget_dict, entry_kwargs, case)

        # 6. FILE ATTACHMENT FIELD (FieldType.FILE)
        elif f.field_type == FieldType.FILE:
            self._render_file_field(row_frame, f, val, target_widget_dict, entry_kwargs)

        # 7. NUMBER FIELD
        elif f.field_type == FieldType.NUMBER:
            self._render_number_field(row_frame, f, val, target_widget_dict, entry_kwargs)

        # 8. MULTILINE TEXTBOX FIELD
        elif any(k in fid_lower or k in flabel_lower for k in (
            "error_message", "reproduction", "steps", "expected", "schritte", "beschreibung",
            "erklärung", "verhalten", "stack_trace", "log", "notiz", "details", "begründung",
            "dateien", "dateianfragen", "files", "anfragen", "liste", "korrekturdateien"
        )):
            self._render_textbox_field(row_frame, f, val, target_widget_dict, entry_kwargs)

        # 9. STANDARD SINGLE-LINE TEXT ENTRY
        else:
            self._render_text_entry_field(row_frame, f, val, target_widget_dict, entry_kwargs)

        entry = target_widget_dict.get(f.field_id)
        if entry is not None:
            self._set_field_highlight(entry[1], is_missing)

    def _set_field_highlight(self, widget: Any, is_missing: bool) -> None:
        """Marks or unmarks one field as a missing required field.

        The widget's own border settings are stored the first time it is marked,
        so unmarking restores exactly what the theme gave it instead of guessing
        a colour. Widgets without a border option (checkboxes, the module tag
        picker) are skipped.
        """
        if widget is None or not hasattr(widget, "configure"):
            return
        try:
            if not widget.winfo_exists():
                return
        except Exception:
            return

        key = str(widget)
        try:
            if is_missing:
                if key not in self._field_border_defaults:
                    self._field_border_defaults[key] = (widget.cget("border_color"), widget.cget("border_width"))
                widget.configure(border_color=BORDER_COLOR_MISSING, border_width=BORDER_WIDTH_MISSING)
            else:
                previous = self._field_border_defaults.pop(key, None)
                if previous is not None:
                    widget.configure(border_color=previous[0], border_width=previous[1])
        except Exception:
            # Not every field type has a border; nothing to highlight there.
            self._field_border_defaults.pop(key, None)

    def apply_missing_field_highlight(self, missing_fields: list[str] | None) -> None:
        """Updates the red required-field borders in place.

        Saving used to call load_schema() for this, rebuilding every widget of
        the form just to recolour a few borders - the single most expensive way
        to change a colour. This touches only the fields whose state changed.
        """
        self.missing_fields = list(missing_fields or [])
        missing = set(self.missing_fields)

        widget_dicts: list[dict[str, Any]] = [self.field_widgets]
        widget_dicts.extend(getattr(self, "card_field_widgets", []) or [])

        for widget_dict in widget_dicts:
            for field_id, entry in widget_dict.items():
                if not entry:
                    continue
                self._set_field_highlight(entry[1], field_id in missing)

    def load_schema(
        self,
        schema: QuestionSchema | None,
        form_data: dict[str, Any],
        missing_fields: list[str] | None = None,
        case: Case | None = None,
    ):
        self.schema = schema
        self.current_case = case
        self.missing_fields = missing_fields or []

        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.field_widgets.clear()
        # The old widgets are gone; their remembered borders would only keep
        # stale Tk paths alive.
        self._field_border_defaults.clear()
        self.card_field_widgets: list[dict[str, tuple[str, Any]]] = []
        self.field_row_frames: dict[str, ctk.CTkFrame] = {}

        if not schema or not schema.fields:
            from services.i18n_service import tr
            ctk.CTkLabel(self.scroll_frame, text=tr("form.no_fields", "Keine Formularfelder definiert.")).pack(pady=PAD_2XL)
            return

        sorted_fields = sorted(schema.fields, key=lambda f: f.order)

        if schema.is_repeatable_group and schema.repeatable_field_ids:
            rep_set = set(schema.repeatable_field_ids)
            top_fields = [f for f in sorted_fields if f.field_id not in rep_set]
            self.card_fields = [f for f in sorted_fields if f.field_id in rep_set]

            # 1. Top level non-repeatable fields
            for f in top_fields:
                self.render_single_field(
                    self.scroll_frame, f, form_data.get(f.field_id), self.field_widgets, self.missing_fields, case
                )

            # 2. Parse or initialize file_requests
            raw_reqs = form_data.get("file_requests")
            if isinstance(raw_reqs, list) and len(raw_reqs) > 0:
                self.current_file_requests = [dict(r) if isinstance(r, dict) else {} for r in raw_reqs]
            else:
                flat_req = {fid: form_data.get(fid) for fid in schema.repeatable_field_ids if form_data.get(fid) is not None}
                if flat_req:
                    self.current_file_requests = [flat_req]
                else:
                    self.current_file_requests = [{}]

            self.repeatable_container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
            self.repeatable_container.pack(fill="x", pady=PAD_10, padx=PAD_XS)
            self.render_repeatable_cards()

        else:
            for f in sorted_fields:
                self.render_single_field(
                    self.scroll_frame, f, form_data.get(f.field_id), self.field_widgets, self.missing_fields, case
                )

        self._bind_mouse_wheel_recursive(self.scroll_frame)
        self.update_conditional_visibility()

    def refresh_ui_labels(self):
        self.load_schema(getattr(self, "schema", None), self.get_form_data(), getattr(self, "missing_fields", []), getattr(self, "current_case", None))

    def render_repeatable_cards(self):
        if not hasattr(self, "repeatable_container"):
            return

        for w in self.repeatable_container.winfo_children():
            w.destroy()
        self.card_field_widgets = []

        from services.i18n_service import tr
        group_title = self.schema.repeatable_group_title if self.schema else tr("dynamic_form.repeatable_default_group_title", "Datei / Korrektur-Anforderung")

        for idx, req_data in enumerate(self.current_file_requests):
            card_frame = ctk.CTkFrame(
                self.repeatable_container,
                fg_color=COLOR_REPEATABLE_CARD_BG,
                corner_radius=CORNER_RADIUS_CARD,
                border_width=BORDER_WIDTH_CARD,
                border_color=COLOR_CARD_BORDER_DEFAULT,
            )
            card_frame.pack(fill="x", pady=PAD_MD, padx=PAD_SM)

            hdr = ctk.CTkFrame(card_frame, fg_color="transparent")
            hdr.pack(fill="x", padx=PAD_MD + PAD_XS, pady=(PAD_MD, PAD_SM))

            ctk.CTkLabel(
                hdr,
                text=f"📌 {group_title} #{idx + 1}",
                font=ctk.CTkFont(size=FONT_SIZE_CONFIRM, weight=FONT_WEIGHT_BOLD),
                text_color=COLOR_ACCENT_BLUE,
            ).pack(side="left")

            if len(self.current_file_requests) > 1:
                ctk.CTkButton(
                    hdr,
                    text=tr("dynamic_form.remove_card", "🗑 Anfrage #{idx} entfernen", idx=idx + 1),
                    height=BTN_HEIGHT_REMOVE_CARD,
                    width=BTN_WIDTH_REMOVE_CARD,
                    fg_color=COLOR_DANGER,
                    hover_color=COLOR_DANGER_HOVER,
                    command=lambda i=idx: self.remove_repeatable_card(i),
                ).pack(side="right")

            card_widgets_dict: dict[str, tuple[str, Any]] = {}
            card_body = ctk.CTkFrame(card_frame, fg_color="transparent")
            card_body.pack(fill="x", padx=PAD_MD + PAD_XS, pady=(0, PAD_MD))

            for f in self.card_fields:
                val = req_data.get(f.field_id)
                self.render_single_field(
                    card_body, f, val, card_widgets_dict, self.missing_fields, self.current_case
                )

            self.card_field_widgets.append(card_widgets_dict)

            btn_row = ctk.CTkFrame(self.repeatable_container, fg_color="transparent")
            btn_row.pack(fill="x", pady=(PAD_MD - PAD_XS, PAD_SM))

            ctk.CTkButton(
                btn_row,
                text=tr("dynamic_form.add_card", "➕ Weitere {title} anfordern", title=group_title),
                fg_color=COLOR_SUCCESS,
                hover_color=COLOR_SUCCESS_HOVER,
                height=BTN_HEIGHT_ADD_CARD,
                font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
                command=self.add_repeatable_card,
            ).pack(fill="x", padx=PAD_SM)

        self._bind_mouse_wheel_recursive(self.repeatable_container)

    def _sync_current_card_inputs(self):
        updated_reqs = []
        for card_dict in self.card_field_widgets:
            req_data = {}
            for fid, (ftype, widget) in card_dict.items():
                req_data[fid] = self._extract_widget_value(ftype, widget)
            updated_reqs.append(req_data)
        self.current_file_requests = updated_reqs

    def add_repeatable_card(self):
        self._sync_current_card_inputs()
        self.current_file_requests.append({})
        self.render_repeatable_cards()

    def remove_repeatable_card(self, idx: int):
        self._sync_current_card_inputs()
        if 0 <= idx < len(self.current_file_requests) and len(self.current_file_requests) > 1:
            self.current_file_requests.pop(idx)
            self.render_repeatable_cards()

    def update_conditional_visibility(self):
        """Dynamically evaluates depends_on_field_id conditions and updates field row visibility."""
        if not self.schema or not self.schema.fields:
            return

        current_data = self.get_form_data()

        for f in self.schema.fields:
            dep_id = getattr(f, "depends_on_field_id", "")
            row_frame = self.field_row_frames.get(f.field_id)
            if not row_frame or not dep_id:
                continue

            expected_val = getattr(f, "depends_on_value", "").strip()
            parent_val = current_data.get(dep_id)

            should_show = False
            if parent_val is not None:
                p_str = str(parent_val).strip()
                if not expected_val:
                    should_show = bool(parent_val) and p_str.lower() not in ("false", "0", "nein", "none")
                else:
                    valid_targets = [v.strip().lower() for v in expected_val.split(",")]
                    should_show = p_str.lower() in valid_targets or (isinstance(parent_val, bool) and parent_val and "true" in valid_targets)

            if should_show:
                row_frame.pack(fill="x", pady=PAD_GAP, padx=PAD_CONTAINER)
            else:
                row_frame.pack_forget()

    def _get_target_dir(self, case: Case) -> str:
        if self.attachment_service:
            return str(self.attachment_service.get_case_attachment_dir(case))
        elif case.attachment_directory:
            return case.attachment_directory
        else:
            return os.path.join(DEFAULT_ATTACHMENTS_DIR, case.case_id)

    # --- DB BACKUP IMPORT & MINI ATTACHMENT SECTION ---
    def import_db_backup_file(self, case: Case, bool_var: ctk.BooleanVar):
        from services.i18n_service import tr
        file_path = filedialog.askopenfilename(
            title=tr("dynamic_form.import_backup_dialog_title", "Datenbank-Backup (.backup) importieren"),
            filetypes=[
                (tr("dynamic_form.backup_filetypes", "Backup-Dateien (*.backup)"), "*.backup"),
                (tr("common.all_files", "Alle Dateien"), "*.*"),
            ],
        )
        if not file_path:
            return

        target_dir = self._get_target_dir(case)
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, FILE_NAME_DATA_BACKUP)

        shutil.copy2(file_path, target_path)
        bool_var.set(True)
        case.form_data["database_dump_provided"] = True

        if hasattr(self, "mini_attach_scroll"):
            self.refresh_mini_attachment_list(case)

    def render_mini_attachment_section(self, parent: Any, case: Case):
        attach_box = ctk.CTkFrame(parent, fg_color=COLOR_MINI_ATTACH_BG, corner_radius=CORNER_RADIUS_CARD)
        attach_box.pack(fill="x", pady=(PAD_MD - PAD_XS, PAD_SM))

        hdr_row = ctk.CTkFrame(attach_box, fg_color="transparent")
        hdr_row.pack(fill="x", padx=PAD_MD, pady=PAD_SM)

        from services.i18n_service import tr

        self.mini_attach_hdr_label = ctk.CTkLabel(
            hdr_row,
            text=tr("dynamic_form.no_files", "📎 Abgelegte Dateien im Fallordner: Keine (0)"),
            font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD),
        )
        self.mini_attach_hdr_label.pack(side="left")

        ctk.CTkButton(
            hdr_row,
            text=tr("dynamic_form.import_files", "+ Datei(en) importieren..."),
            height=BTN_HEIGHT_REMOVE_CARD,
            width=BTN_WIDTH_IMPORT_FILES,
            fg_color=COLOR_BTN_SECONDARY,
            hover_color=COLOR_BELL_BTN,
            command=lambda: self.import_general_files(case),
        ).pack(side="right")

        self.mini_attach_scroll = ctk.CTkScrollableFrame(attach_box, height=HEIGHT_MINI_ATTACH_SCROLL, fg_color="transparent")

        self.refresh_mini_attachment_list(case)

    def import_general_files(self, case: Case):
        from services.i18n_service import tr
        files = filedialog.askopenfilenames(title=tr("dynamic_form.import_title", "Dateien in Fallordner importieren"))
        if not files:
            return

        target_dir = self._get_target_dir(case)
        os.makedirs(target_dir, exist_ok=True)
        for f in files:
            shutil.copy2(f, os.path.join(target_dir, os.path.basename(f)))

        self.refresh_mini_attachment_list(case)

    def refresh_mini_attachment_list(self, case: Case):
        from services.i18n_service import tr
        if not hasattr(self, "mini_attach_scroll"):
            return

        for w in self.mini_attach_scroll.winfo_children():
            w.destroy()

        target_dir = self._get_target_dir(case)
        files = []
        if os.path.exists(target_dir):
            files = [f for f in os.listdir(target_dir) if os.path.isfile(os.path.join(target_dir, f))]

        if not files:
            self.mini_attach_hdr_label.configure(text=tr("dynamic_form.no_files", "📎 Abgelegte Dateien im Fallordner: Keine (0)"))
            self.mini_attach_scroll.pack_forget()
            return

        self.mini_attach_hdr_label.configure(text=f"📎 {tr('dynamic_form.files_attached', 'Abgelegte Dateien im Fallordner')} ({len(files)}):")
        self.mini_attach_scroll.pack(fill="both", expand=True, padx=PAD_CONTAINER, pady=(PAD_NONE, PAD_SM))

        for f_name in files:
            f_path = os.path.join(target_dir, f_name)
            size_kb = os.path.getsize(f_path) / BYTES_PER_KB

            frow = ctk.CTkFrame(self.mini_attach_scroll, fg_color=COLOR_MINI_ATTACH_ROW_BG, height=HEIGHT_MINI_ATTACH_ROW)
            frow.pack(fill="x", pady=PAD_XS)

            is_backup = f_name == FILE_NAME_DATA_BACKUP
            icon = "🗄" if is_backup else "📄"

            lbl_txt = f"{icon} {f_name} ({size_kb:.1f} KB)"
            ctk.CTkLabel(frow, text=lbl_txt, font=ctk.CTkFont(size=FONT_SIZE_SM), anchor="w").pack(side="left", padx=PAD_MD, expand=True, fill="x")

            ctk.CTkButton(
                frow,
                text=tr("common.open", "👁 Öffnen"),
                width=BTN_WIDTH_OPEN_FILE,
                height=HEIGHT_OPEN_FILE_BTN,
                fg_color=COLOR_OPEN_FILE_BTN,
                hover_color=COLOR_OPEN_FILE_BTN_HOVER,
                command=lambda p=f_path: self.open_file_external(p),
            ).pack(side="right", padx=PAD_SM)

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
            data[fid] = self._extract_widget_value(ftype, widget)

        schema = getattr(self, "schema", None)
        if schema and getattr(schema, "is_repeatable_group", False):
            file_requests = []
            for card_dict in getattr(self, "card_field_widgets", []):
                card_data = {}
                for fid, (ftype, widget) in card_dict.items():
                    card_data[fid] = self._extract_widget_value(ftype, widget)
                file_requests.append(card_data)

            data["file_requests"] = file_requests
            if file_requests:
                for k, v in file_requests[0].items():
                    data[k] = v

        return data
