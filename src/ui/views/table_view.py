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


class TableView(ctk.CTkFrame):
    """Sortable Data Matrix Table View with interactive column width adjustment and text wrapping."""

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
        self.show_width_controls: bool = False

        self.create_layout()

    def set_schemas(self, schemas: list[QuestionSchema]):
        self.schemas = schemas

    def get_col_w(self, key: str, default: int) -> int:
        if self.app_config:
            if hasattr(self.app_config, "column_widths") and isinstance(self.app_config.column_widths, dict):
                return self.app_config.column_widths.get(f"table_col_{key}", default)
            elif hasattr(self.app_config, "ui_settings") and hasattr(self.app_config.ui_settings, "column_widths"):
                return self.app_config.ui_settings.column_widths.get(f"table_col_{key}", default)
        return default

    def set_col_w(self, key: str, value: int):
        if self.app_config:
            if hasattr(self.app_config, "column_widths") and isinstance(self.app_config.column_widths, dict):
                self.app_config.column_widths[f"table_col_{key}"] = value
            if hasattr(self.app_config, "ui_settings") and hasattr(self.app_config.ui_settings, "column_widths"):
                self.app_config.ui_settings.column_widths[f"table_col_{key}"] = value

    def create_layout(self):
        self.grid_rowconfigure(0, weight=5)  # Top: Table
        self.grid_rowconfigure(1, weight=5)  # Bottom: Details
        self.grid_columnconfigure(0, weight=1)

        # 1. Top Section: Data Table Frame
        top_frame = ctk.CTkFrame(self)
        top_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=(5, 2))

        # Top Control Bar (Toggle Column Width Controls)
        top_ctrl_bar = ctk.CTkFrame(top_frame, height=32, fg_color="transparent")
        top_ctrl_bar.pack(fill="x", side="top", padx=5, pady=(4, 2))

        ctk.CTkLabel(
            top_ctrl_bar,
            text="📊 Datenmatrix",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="left", padx=5)

        self.btn_toggle_ctrls = ctk.CTkButton(
            top_ctrl_bar,
            text="📐 Spaltenbreiten anpassen",
            command=self.toggle_width_controls,
            width=170,
            height=24,
            font=ctk.CTkFont(size=11),
            fg_color="gray35",
        )
        self.btn_toggle_ctrls.pack(side="right", padx=5)

        # Collapsible Column Width Controls Bar
        self.ctrl_panel = ctk.CTkFrame(top_frame, fg_color=("gray85", "gray25"))
        # Initially hidden

        # Table Header
        self.h_frame = ctk.CTkFrame(top_frame, height=36, fg_color=("gray75", "gray25"))
        self.h_frame.pack(fill="x", side="top", padx=5, pady=(2, 2))

        self.header_buttons: dict[str, ctk.CTkButton] = {}
        self.render_headers()

        # Scrollable Rows Container
        self.table_scroll = ctk.CTkScrollableFrame(top_frame)
        self.table_scroll.pack(fill="both", expand=True, padx=5, pady=(0, 5))

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

    def toggle_width_controls(self):
        self.show_width_controls = not self.show_width_controls
        if self.show_width_controls:
            self.btn_toggle_ctrls.configure(fg_color="darkblue", text="✖ Regler ausblenden")
            self.build_ctrl_panel()
            self.ctrl_panel.pack(fill="x", side="top", padx=5, pady=(2, 4), before=self.h_frame)
        else:
            self.btn_toggle_ctrls.configure(fg_color="gray35", text="📐 Spaltenbreiten anpassen")
            self.ctrl_panel.pack_forget()

    def build_ctrl_panel(self):
        for child in self.ctrl_panel.winfo_children():
            child.destroy()

        sliders_def = [
            ("id", "ID", 80, 250, 120),
            ("practice", "Praxis", 140, 450, 220),
            ("title", "Titel", 180, 600, 280),
            ("actor", "Zuständigkeit", 100, 250, 130),
            ("followup", "Wiedervorlage", 100, 250, 150),
            ("score", "Score", 60, 150, 90),
        ]

        row_f = ctk.CTkFrame(self.ctrl_panel, fg_color="transparent")
        row_f.pack(fill="x", padx=5, pady=5)

        for col_key, label_txt, min_v, max_v, def_v in sliders_def:
            curr_w = self.get_col_w(col_key, def_v)

            col_box = ctk.CTkFrame(row_f, fg_color="transparent")
            col_box.pack(side="left", expand=True, padx=4)

            lbl = ctk.CTkLabel(col_box, text=f"{label_txt}: {curr_w}px", font=ctk.CTkFont(size=10, weight="bold"))
            lbl.pack(anchor="w")

            def make_cmd(k=col_key, l=lbl, t=label_txt):
                return lambda val: self.on_col_slider_changed(k, val, l, t)

            slider = ctk.CTkSlider(  # type: ignore[attr-defined]
                col_box,
                from_=min_v,
                to=max_v,
                number_of_steps=(max_v - min_v) // 5,
                width=110,
                height=16,
                command=make_cmd(),
            )
            slider.set(curr_w)
            slider.pack(anchor="w", pady=(2, 0))

    def on_col_slider_changed(self, col_key: str, val: float, label_widget: ctk.CTkLabel, title_txt: str):
        new_w = int(val)
        label_widget.configure(text=f"{title_txt}: {new_w}px")
        self.set_col_w(col_key, new_w)
        self.render_headers()
        self.render_rows()

    def render_headers(self):
        for child in self.h_frame.winfo_children():
            child.destroy()

        cols = [
            ("case_id", "ID ⇅", self.get_col_w("id", 120)),
            ("practice", "Praxis / Kunde ⇅", self.get_col_w("practice", 220)),
            ("title", "Titel / Betreff ⇅", self.get_col_w("title", 280)),
            ("actor", "Zuständigkeit ⇅", self.get_col_w("actor", 130)),
            ("followup", "Wiedervorlage ⇅", self.get_col_w("followup", 150)),
            ("score", "Score ⇅", self.get_col_w("score", 90)),
        ]

        for col_key, col_label, width in cols:
            btn = ctk.CTkButton(
                self.h_frame,
                text=col_label,
                font=ctk.CTkFont(weight="bold", size=11),
                command=lambda k=col_key: self.on_header_click(k),
                width=width,
                fg_color="transparent",
                hover_color=("gray65", "gray35"),
                anchor="w",
            )
            btn.pack(side="left", padx=2, pady=2)
            self.header_buttons[col_key] = btn

    def on_header_click(self, col_key: str):
        if self.sort_column == col_key:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = col_key
            self.sort_reverse = True
        self.render_rows()

    def set_cases(self, cases: list[Case]):
        self.cases = cases
        self.render_rows()

    def render_rows(self):
        for child in self.table_scroll.winfo_children():
            child.destroy()

        if not self.cases:
            ctk.CTkLabel(self.table_scroll, text="Keine Fälle vorhanden.", text_color="gray").pack(pady=20)
            return

        # Sort cases according to sort_column
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

        w_id = self.get_col_w("id", 120)
        w_pr = self.get_col_w("practice", 220)
        w_tt = self.get_col_w("title", 280)
        w_ac = self.get_col_w("actor", 130)
        w_fw = self.get_col_w("followup", 150)
        w_sc = self.get_col_w("score", 90)

        for c in sorted_cases:
            is_sel = self.selected_case and self.selected_case.case_id == c.case_id
            bg_color = ("gray75", "gray35") if is_sel else ("gray85", "gray20")

            row = ctk.CTkFrame(self.table_scroll, fg_color=bg_color, cursor="hand2")
            row.pack(fill="x", pady=2, padx=2)
            row.bind("<Button-1>", lambda e, case=c: self.select_case(case))

            vip_str = " ★ VIP" if c.customer.is_vip else ""
            fw_str = format_german_datetime(c.workflow_status.followup_at) if c.workflow_status.followup_at else "-"

            # Columns with text wrapping support
            id_l = ctk.CTkLabel(
                row,
                text=c.case_id,
                width=w_id,
                wraplength=max(60, w_id - 6),
                font=ctk.CTkFont(weight="bold"),
                anchor="w",
                justify="left",
            )
            id_l.pack(side="left", padx=2, pady=4)
            id_l.bind("<Button-1>", lambda e, case=c: self.select_case(case))

            pr_l = ctk.CTkLabel(
                row,
                text=f"{c.customer.practice_name}{vip_str}",
                width=w_pr,
                wraplength=max(100, w_pr - 6),
                anchor="w",
                justify="left",
            )
            pr_l.pack(side="left", padx=2, pady=4)
            pr_l.bind("<Button-1>", lambda e, case=c: self.select_case(case))

            tt_l = ctk.CTkLabel(
                row,
                text=c.classification.title,
                width=w_tt,
                wraplength=max(140, w_tt - 6),
                anchor="w",
                justify="left",
            )
            tt_l.pack(side="left", padx=2, pady=4)
            tt_l.bind("<Button-1>", lambda e, case=c: self.select_case(case))

            ac_l = ctk.CTkLabel(
                row,
                text=get_actor_display(c.workflow_status.current_actor),
                width=w_ac,
                wraplength=max(80, w_ac - 6),
                anchor="w",
                justify="left",
            )
            ac_l.pack(side="left", padx=2, pady=4)
            ac_l.bind("<Button-1>", lambda e, case=c: self.select_case(case))

            fw_l = ctk.CTkLabel(
                row,
                text=fw_str,
                width=w_fw,
                wraplength=max(80, w_fw - 6),
                anchor="w",
                justify="left",
            )
            fw_l.pack(side="left", padx=2, pady=4)
            fw_l.bind("<Button-1>", lambda e, case=c: self.select_case(case))

            score = c.classification.calculated_score
            sc_color = "firebrick" if score >= 100 else ("darkgoldenrod" if score >= 50 else "darkgreen")
            sc_l = ctk.CTkLabel(
                row,
                text=f"{score:.0f}",
                width=w_sc,
                wraplength=max(40, w_sc - 6),
                font=ctk.CTkFont(weight="bold"),
                text_color=sc_color,
                anchor="w",
                justify="left",
            )
            sc_l.pack(side="left", padx=2, pady=4)
            sc_l.bind("<Button-1>", lambda e, case=c: self.select_case(case))

    def select_case(self, case: Case):
        self.selected_case = case
        self.on_case_selected(case)
        self.render_rows()

        # Update bottom detail panel
        self.detail_title_label.configure(text=f"📋 Falldetails: {case.case_id} - {case.customer.practice_name} ({case.classification.title})")
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
