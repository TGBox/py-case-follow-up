import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from typing import Callable, Any
from models.case import Case
from models.schema import QuestionSchema
from services.scoring_service import ScoringService
from services.attachment_service import AttachmentService
from services.schema_service import SchemaService
from ui.widgets.dynamic_form_widget import DynamicFormWidget
from ui.widgets.timeline_widget import TimelineWidget
from ui.widgets.attachment_widget import AttachmentWidget
from enums import get_actor_display
from utils.datetime_utils import format_german_datetime


COL_TITLE_MAP = {
    "case_id": "ID ⇅",
    "practice": "Praxis / Kunde ⇅",
    "title": "Titel / Betreff ⇅",
    "actor": "Zuständigkeit ⇅",
    "followup": "Wiedervorlage ⇅",
    "score": "Score ⇅",
}


class TableView(ctk.CTkFrame):
    """Data Matrix Table View with native mouse-resizable & reorderable ttk.Treeview columns."""

    def __init__(
        self,
        parent,
        author_name: str,
        scoring_service: ScoringService,
        attachment_service: AttachmentService,
        on_case_updated: Callable[[Case], None],
        on_case_selected: Callable[[Case], None],
        app_config: Any | None = None,
    ):
        super().__init__(parent, fg_color="transparent")
        self.author_name = author_name
        self.scoring_service = scoring_service
        self.attachment_service = attachment_service
        self.on_case_updated = on_case_updated
        self.on_case_selected = on_case_selected
        self.app_config = app_config

        self.cases: list[Case] = []
        self.schemas: list[QuestionSchema] = []
        self.selected_case: Case | None = None

        self.sort_column: str = "score"
        self.sort_reverse: bool = True

        # Load saved column widths and order from profile
        self.column_widths: dict[str, int] = {
            "case_id": 120,
            "practice": 220,
            "title": 280,
            "actor": 130,
            "followup": 150,
            "score": 90,
        }
        self.column_order: list[str] = ["case_id", "practice", "title", "actor", "followup", "score"]

        if self.app_config:
            if hasattr(self.app_config, "table_column_widths") and isinstance(self.app_config.table_column_widths, dict):
                self.column_widths.update(self.app_config.table_column_widths)
            elif hasattr(self.app_config, "ui_settings") and hasattr(self.app_config.ui_settings, "table_column_widths"):
                self.column_widths.update(self.app_config.ui_settings.table_column_widths)

            if hasattr(self.app_config, "table_column_order") and isinstance(self.app_config.table_column_order, list):
                self.column_order = list(self.app_config.table_column_order)
            elif hasattr(self.app_config, "ui_settings") and hasattr(self.app_config.ui_settings, "table_column_order"):
                self.column_order = list(self.app_config.ui_settings.table_column_order)

        self.create_layout()

    def set_schemas(self, schemas: list[QuestionSchema]):
        self.schemas = schemas

    def create_layout(self):
        self.grid_rowconfigure(0, weight=5)  # Top: Table Treeview
        self.grid_rowconfigure(1, weight=5)  # Bottom: Details Panel
        self.grid_columnconfigure(0, weight=1)

        # 1. Top Section: Data Table Frame with ttk.Treeview
        top_frame = ctk.CTkFrame(self)
        top_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=(5, 2))

        # Setup ttk Style for Dark/Light Mode
        self.setup_treeview_style()

        # Treeview Widget
        cols = tuple(self.column_order)
        self.tree = ttk.Treeview(
            top_frame,
            columns=cols,
            show="headings",
            selectmode="browse",
            style="Matrix.Treeview",
        )

        # Scrollbars
        vsb = ttk.Scrollbar(top_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(top_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        top_frame.grid_rowconfigure(0, weight=1)
        top_frame.grid_columnconfigure(0, weight=1)

        # Configure columns & headings
        self.configure_tree_columns()

        # Bind events
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<ButtonRelease-1>", self.on_header_mouse_release)

        # 2. Bottom Section: Collapsible Detail Panel
        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=(2, 5))

        # Detail Header & Save Button
        bottom_header = ctk.CTkFrame(bottom_frame, height=38, fg_color="transparent")
        bottom_header.pack(fill="x", padx=10, pady=(6, 2))

        self.detail_title_label = ctk.CTkLabel(
            bottom_header,
            text="📋 Falldetails & Formular (Wählen Sie einen Fall aus der Tabelle)",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        )
        self.detail_title_label.pack(side="left")

        self.save_btn = ctk.CTkButton(
            bottom_header,
            text="💾 Ändern & Speichern",
            command=self.on_click_save,
            fg_color="forestgreen",
            width=150,
            state="disabled",
        )
        self.save_btn.pack(side="right")

        # Detail Tabs (Form, Timeline, Attachments)
        self.detail_tabview = ctk.CTkTabview(bottom_frame)
        self.detail_tabview.pack(fill="both", expand=True, padx=5, pady=(0, 5))

        tab_form = self.detail_tabview.add("📝 Formular & Ausfüllen")
        tab_timeline = self.detail_tabview.add("🕒 Zeitleiste")
        tab_attachments = self.detail_tabview.add("📎 Anhänge")

        self.form_widget = DynamicFormWidget(tab_form)
        self.form_widget.pack(fill="both", expand=True, padx=5, pady=5)

        self.timeline_widget = TimelineWidget(tab_timeline, self.author_name, self.on_timeline_updated)
        self.timeline_widget.pack(fill="both", expand=True)

        self.attachment_widget = AttachmentWidget(tab_attachments, self.attachment_service)
        self.attachment_widget.pack(fill="both", expand=True)

    def setup_treeview_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        is_dark = ctk.get_appearance_mode().lower() == "dark"
        bg_color = "#2b2b2b" if is_dark else "#f0f0f0"
        fg_color = "#ffffff" if is_dark else "#000000"
        hdr_bg = "#383838" if is_dark else "#d9d9d9"
        sel_bg = "#1f538d"

        style.configure(
            "Matrix.Treeview",
            background=bg_color,
            foreground=fg_color,
            fieldbackground=bg_color,
            rowheight=32,
            font=("Segoe UI", 10),
            borderwidth=0,
        )
        style.map("Matrix.Treeview", background=[("selected", sel_bg)], foreground=[("selected", "#ffffff")])

        style.configure(
            "Matrix.Treeview.Heading",
            background=hdr_bg,
            foreground=fg_color,
            font=("Segoe UI", 10, "bold"),
            borderwidth=1,
            relief="raised",
        )
        style.map("Matrix.Treeview.Heading", background=[("active", "#4a4a4a" if is_dark else "#bfbfbf")])

    def configure_tree_columns(self):
        for col_key in self.column_order:
            title_txt = COL_TITLE_MAP.get(col_key, col_key)
            w = self.column_widths.get(col_key, 150)

            self.tree.heading(
                col_key,
                text=title_txt,
                command=lambda k=col_key: self.on_header_click(k),
                anchor="w",
            )
            self.tree.column(col_key, width=w, minwidth=60, stretch=True, anchor="w")

    def on_header_click(self, col_key: str):
        if self.sort_column == col_key:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = col_key
            self.sort_reverse = True
        self.render_rows()

    def on_header_mouse_release(self, event=None):
        # Save updated widths and display order after drag
        for col_key in self.column_order:
            try:
                w = self.tree.column(col_key, "width")
                if isinstance(w, (int, float)):
                    self.column_widths[col_key] = int(w)
            except Exception:
                pass

        if self.app_config:
            if hasattr(self.app_config, "table_column_widths") and isinstance(self.app_config.table_column_widths, dict):
                self.app_config.table_column_widths.update(self.column_widths)
            if hasattr(self.app_config, "ui_settings") and hasattr(self.app_config.ui_settings, "table_column_widths"):
                self.app_config.ui_settings.table_column_widths.update(self.column_widths)

    def set_cases(self, cases: list[Case]):
        self.cases = cases
        self.render_rows()

    def render_rows(self):
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not self.cases:
            return

        def get_sort_key(c: Case):
            if self.sort_column == "case_id":
                return c.case_id
            elif self.sort_column == "practice":
                return c.customer.practice_name.lower()
            elif self.sort_column == "title":
                return c.classification.title.lower()
            elif self.sort_column == "actor":
                return c.workflow_status.current_actor
            elif self.sort_column == "followup":
                return c.workflow_status.followup_at or ""
            else:  # score
                return c.classification.calculated_score

        sorted_cases = sorted(self.cases, key=get_sort_key, reverse=self.sort_reverse)

        for c in sorted_cases:
            vip_str = " ★ VIP" if c.customer.is_vip else ""
            fw_str = format_german_datetime(c.workflow_status.followup_at) if c.workflow_status.followup_at else "-"
            score = c.classification.calculated_score

            values_map = {
                "case_id": c.case_id,
                "practice": f"{c.customer.practice_name}{vip_str}",
                "title": c.classification.title,
                "actor": get_actor_display(c.workflow_status.current_actor),
                "followup": fw_str,
                "score": f"{score:.0f}",
            }

            row_values = tuple(values_map.get(k, "") for k in self.column_order)
            item_id = self.tree.insert("", "end", iid=c.case_id, values=row_values)

            if self.selected_case and self.selected_case.case_id == c.case_id:
                self.tree.selection_set(item_id)

    def on_tree_select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        case_id = sel[0]
        case = next((c for c in self.cases if c.case_id == case_id), None)
        if case:
            self.select_case(case)

    def select_case(self, case: Case):
        self.selected_case = case
        self.on_case_selected(case)

        # Update bottom detail panel
        self.detail_title_label.configure(
            text=f"📋 Falldetails: {case.case_id} - {case.customer.practice_name} ({case.classification.title})"
        )
        self.save_btn.configure(state="normal")

        # Schema & Form
        schema = next((s for s in self.schemas if s.schema_id == case.classification.schema_id), None)
        if schema:
            SchemaService.update_case_completion(case, schema)
        self.form_widget.load_schema(schema, case.form_data, case.missing_required_fields)

        # Right tabs
        self.timeline_widget.load_timeline(case.timeline)
        self.attachment_widget.load_attachments(case)

    def on_click_save(self):
        if not self.selected_case:
            return
        form_data = self.form_widget.get_form_data()
        self.selected_case.form_data = form_data

        schema = next((s for s in self.schemas if s.schema_id == self.selected_case.classification.schema_id), None)
        if schema:
            SchemaService.update_case_completion(self.selected_case, schema)

        self.scoring_service.update_case_scoring(self.selected_case)
        self.on_case_updated(self.selected_case)
        self.render_rows()

    def on_timeline_updated(self, timeline: list[Any] | None = None):
        if self.selected_case:
            self.on_click_save()
