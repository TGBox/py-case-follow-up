import customtkinter as ctk
from typing import Callable, Any
from models.case import Case
from enums import Actor, get_actor_display
from utils.datetime_utils import format_german_datetime


class KanbanCardWidget(ctk.CTkFrame):
    """Kanban card representation of a single case with quick actions and auto-wrapping."""

    def __init__(
        self,
        parent,
        case: Case,
        on_select_case: Callable[[Case], None],
        on_switch_to_cockpit: Callable[[Case], None],
        on_open_followup: Callable[[Case], None],
        on_toggle_complete: Callable[[Case], None],
        on_change_actor: Callable[[Case], None],
    ):
        super().__init__(parent, corner_radius=8, fg_color=("gray85", "gray20"))
        self.case = case
        self.on_select_case = on_select_case
        self.on_switch_to_cockpit = on_switch_to_cockpit
        self.on_open_followup = on_open_followup
        self.on_toggle_complete = on_toggle_complete
        self.on_change_actor = on_change_actor

        self.create_card()

    def create_card(self):
        # Header: ID + Urgency Score Badge
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(8, 2))

        id_lbl = ctk.CTkLabel(
            header_frame, text=self.case.case_id, font=ctk.CTkFont(weight="bold", size=13)
        )
        id_lbl.pack(side="left")

        # Score badge
        score = self.case.classification.calculated_score
        score_color = "firebrick" if score >= 100 else ("darkgoldenrod" if score >= 50 else "darkgreen")
        score_lbl = ctk.CTkLabel(
            header_frame,
            text=f"Score {score:.0f}",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="white",
            fg_color=score_color,
            corner_radius=4,
            width=65,
            height=20,
        )
        score_lbl.pack(side="right")

        # Customer Name + VIP (with auto-wrap)
        vip_str = " ★ VIP" if self.case.customer.is_vip else ""
        cust_str = f"🏥 {self.case.customer.practice_name}{vip_str}"
        cust_lbl = ctk.CTkLabel(
            self,
            text=cust_str,
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
            justify="left",
            wraplength=260,
            text_color=("gray20", "gray85"),
        )
        cust_lbl.pack(fill="x", padx=10, pady=(2, 2))

        # Case Title (with auto-wrap)
        title_lbl = ctk.CTkLabel(
            self,
            text=self.case.classification.title,
            font=ctk.CTkFont(size=11),
            anchor="w",
            wraplength=260,
            justify="left",
        )
        title_lbl.pack(fill="x", padx=10, pady=(0, 4))

        # Metadata Row: Actor + Followup
        meta_frame = ctk.CTkFrame(self, fg_color="transparent")
        meta_frame.pack(fill="x", padx=10, pady=(0, 6))

        actor_txt = f"👤 {get_actor_display(self.case.workflow_status.current_actor)}"
        ctk.CTkLabel(
            meta_frame,
            text=actor_txt,
            font=ctk.CTkFont(size=10),
            text_color=("gray40", "gray70"),
            anchor="w",
            justify="left",
        ).pack(side="left")

        if self.case.workflow_status.followup_at:
            fw_txt = f"🔔 {format_german_datetime(self.case.workflow_status.followup_at)}"
            ctk.CTkLabel(
                meta_frame,
                text=fw_txt,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=("darkblue", "lightblue"),
                anchor="e",
                justify="right",
            ).pack(side="right")

        # Action Buttons Row
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", padx=8, pady=(4, 8))

        ctk.CTkButton(
            action_frame,
            text="🎯 Cockpit",
            command=lambda: self.on_switch_to_cockpit(self.case),
            width=70,
            height=24,
            font=ctk.CTkFont(size=10),
            fg_color="gray35",
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            action_frame,
            text="👤 Übergeben",
            command=lambda: self.on_change_actor(self.case),
            width=80,
            height=24,
            font=ctk.CTkFont(size=10),
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            action_frame,
            text="🔔 Erinnere",
            command=lambda: self.on_open_followup(self.case),
            width=75,
            height=24,
            font=ctk.CTkFont(size=10),
            fg_color="darkblue",
        ).pack(side="left", padx=2)

        comp_text = "✓ Erledigt" if not self.case.workflow_status.is_completed else "✓ Öffnen"
        comp_color = "forestgreen" if not self.case.workflow_status.is_completed else "gray40"
        ctk.CTkButton(
            action_frame,
            text=comp_text,
            command=lambda: self.on_toggle_complete(self.case),
            width=70,
            height=24,
            font=ctk.CTkFont(size=10),
            fg_color=comp_color,
        ).pack(side="right", padx=2)


class BoardView(ctk.CTkFrame):
    """Interactive 4-column Kanban workflow board with individual column collapsing."""

    def __init__(
        self,
        parent,
        on_select_case: Callable[[Case], None],
        on_switch_to_cockpit: Callable[[Case], None],
        on_open_followup: Callable[[Case], None],
        on_toggle_complete: Callable[[Case], None],
        on_change_actor: Callable[[Case], None],
        app_config: Any | None = None,
    ):
        super().__init__(parent, fg_color="transparent")
        self.on_select_case = on_select_case
        self.on_switch_to_cockpit = on_switch_to_cockpit
        self.on_open_followup = on_open_followup
        self.on_toggle_complete = on_toggle_complete
        self.on_change_actor = on_change_actor
        self.app_config = app_config

        self.cases: list[Case] = []
        self.collapsed_states: dict[str, bool] = {
            "support": False,
            "dev": False,
            "followup": False,
            "completed": False,
        }

        # Load collapsed state from profile / app_config
        if self.app_config:
            if hasattr(self.app_config, "board_collapsed") and isinstance(self.app_config.board_collapsed, dict):
                self.collapsed_states.update(self.app_config.board_collapsed)
            elif hasattr(self.app_config, "ui_settings") and hasattr(self.app_config.ui_settings, "board_collapsed"):
                self.collapsed_states.update(self.app_config.ui_settings.board_collapsed)

        self.create_board()

    def create_board(self):
        # Clear existing children
        for child in self.winfo_children():
            child.destroy()

        self.grid_rowconfigure(0, weight=1)
        cols_def = [
            ("support", "📥 Support / In Bearbeitung"),
            ("dev", "💻 Entwickler / Dev-Team"),
            ("followup", "🔔 Wiedervorlage / Warten"),
            ("completed", "✓ Erledigte Fälle"),
        ]

        self.col_headers: dict[str, ctk.CTkLabel] = {}
        self.col_scrolls: dict[str, ctk.CTkScrollableFrame] = {}

        for idx, (col_key, col_title) in enumerate(cols_def):
            is_collapsed = self.collapsed_states.get(col_key, False)

            if is_collapsed:
                # Collapsed slim column
                self.grid_columnconfigure(idx, weight=0, minsize=42)
                col_frame = ctk.CTkFrame(self, width=42, fg_color=("gray80", "gray25"))
                col_frame.grid(row=0, column=idx, sticky="nsew", padx=2, pady=4)
                col_frame.grid_propagate(False)

                # Expand button
                btn_exp = ctk.CTkButton(
                    col_frame,
                    text="▶",
                    width=28,
                    height=28,
                    command=lambda k=col_key: self.toggle_column_collapse(k),
                    fg_color="gray35",
                    hover_color="gray50",
                )
                btn_exp.pack(anchor="n", pady=8, padx=6)

                lbl = ctk.CTkLabel(
                    col_frame,
                    text=f"{col_title.split(' ')[0]}\n({col_key[0].upper()})",
                    font=ctk.CTkFont(size=12, weight="bold"),
                )
                lbl.pack(pady=10)
                self.col_headers[col_key] = lbl
            else:
                # Expanded full column
                self.grid_columnconfigure(idx, weight=1, minsize=220)
                col_frame = ctk.CTkFrame(self)
                col_frame.grid(row=0, column=idx, sticky="nsew", padx=4, pady=4)

                header_frame = ctk.CTkFrame(col_frame, height=36, fg_color="transparent")
                header_frame.pack(fill="x", padx=6, pady=(6, 4))

                header_lbl = ctk.CTkLabel(
                    header_frame,
                    text=col_title,
                    font=ctk.CTkFont(size=13, weight="bold"),
                    anchor="w",
                )
                header_lbl.pack(side="left", padx=4)
                self.col_headers[col_key] = header_lbl

                # Collapse button
                btn_col = ctk.CTkButton(
                    header_frame,
                    text="◀ Zuklappen",
                    width=80,
                    height=24,
                    font=ctk.CTkFont(size=10),
                    command=lambda k=col_key: self.toggle_column_collapse(k),
                    fg_color="gray35",
                    hover_color="gray50",
                )
                btn_col.pack(side="right", padx=2)

                scroll = ctk.CTkScrollableFrame(col_frame)
                scroll.pack(fill="both", expand=True, padx=4, pady=4)
                self.col_scrolls[col_key] = scroll

    def toggle_column_collapse(self, col_key: str):
        curr = self.collapsed_states.get(col_key, False)
        self.collapsed_states[col_key] = not curr

        # Save to profile / app_config
        if self.app_config:
            if hasattr(self.app_config, "board_collapsed") and isinstance(self.app_config.board_collapsed, dict):
                self.app_config.board_collapsed[col_key] = not curr
            if hasattr(self.app_config, "ui_settings") and hasattr(self.app_config.ui_settings, "board_collapsed"):
                self.app_config.ui_settings.board_collapsed[col_key] = not curr

        self.create_board()
        self.refresh_board()

    def set_cases(self, cases: list[Case]):
        self.cases = cases
        self.refresh_board()

    def refresh_board(self):
        col_cases: dict[str, list[Case]] = {
            "support": [],
            "dev": [],
            "followup": [],
            "completed": [],
        }

        for c in self.cases:
            if c.workflow_status.is_completed:
                col_cases["completed"].append(c)
            elif c.workflow_status.followup_at:
                col_cases["followup"].append(c)
            elif c.workflow_status.current_actor in (Actor.DEVELOPMENT.value, Actor.TECH.value):
                col_cases["dev"].append(c)
            else:
                col_cases["support"].append(c)

        titles = {
            "support": f"📥 Support ({len(col_cases['support'])})",
            "dev": f"💻 Entwickler ({len(col_cases['dev'])})",
            "followup": f"🔔 Wiedervorlage ({len(col_cases['followup'])})",
            "completed": f"✓ Erledigt ({len(col_cases['completed'])})",
        }

        for k, title in titles.items():
            if k in self.col_headers:
                if self.collapsed_states.get(k, False):
                    short_icon = title.split(" ")[0]
                    cnt = title.split("(")[-1].replace(")", "")
                    self.col_headers[k].configure(text=f"{short_icon}\n({cnt})")
                else:
                    self.col_headers[k].configure(text=title)

        for col_key, c_list in col_cases.items():
            if col_key in self.col_scrolls:
                scroll = self.col_scrolls[col_key]
                for child in scroll.winfo_children():
                    child.destroy()

                c_list_sorted = sorted(c_list, key=lambda x: x.classification.calculated_score, reverse=True)
                for c in c_list_sorted:
                    card = KanbanCardWidget(
                        scroll,
                        case=c,
                        on_select_case=self.on_select_case,
                        on_switch_to_cockpit=self.on_switch_to_cockpit,
                        on_open_followup=self.on_open_followup,
                        on_toggle_complete=self.on_toggle_complete,
                        on_change_actor=self.on_change_actor,
                    )
                    card.pack(fill="x", pady=4, padx=2)
