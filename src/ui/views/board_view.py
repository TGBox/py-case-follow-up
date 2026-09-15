import customtkinter as ctk
from typing import Any
from collections.abc import Callable
from models.case import Case
from enums import Actor, get_actor_display
from constants import COLOR_CARD_BG, COLOR_CARD_BORDER
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
        super().__init__(parent, corner_radius=8, fg_color=COLOR_CARD_BG, border_width=1, border_color=COLOR_CARD_BORDER)
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
        from services.i18n_service import tr
        score = self.case.classification.calculated_score
        score_color = "firebrick" if score >= 100 else ("darkgoldenrod" if score >= 50 else "darkgreen")
        score_lbl = ctk.CTkLabel(
            header_frame,
            text=f"{tr('board.score', 'Score')} {score:.0f}",
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
        if self.case.is_internal:
            cust_str = f"🏢 {tr('cockpit.internal_task_title', 'INTERNE AUFGABE / VORGANG')}{vip_str}"
        else:
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

        from services.i18n_service import tr

        ctk.CTkButton(
            action_frame,
            text=tr("board.cockpit_btn", "🎯 Cockpit"),
            command=lambda: self.on_switch_to_cockpit(self.case),
            width=70,
            height=24,
            font=ctk.CTkFont(size=10),
            fg_color=("gray75", "gray35"),
            hover_color=("gray65", "gray45"),
        ).pack(side="left", padx=2)

        from services.i18n_service import tr

        ctk.CTkButton(
            action_frame,
            text=tr("board.handover", "👤 Übergeben"),
            command=lambda: self.on_change_actor(self.case),
            width=80,
            height=24,
            font=ctk.CTkFont(size=10),
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            action_frame,
            text=tr("board.remind", "🔔 Erinnere"),
            command=lambda: self.on_open_followup(self.case),
            width=75,
            height=24,
            font=ctk.CTkFont(size=10),
            fg_color="darkblue",
        ).pack(side="left", padx=2)

        comp_text = tr("cockpit.complete", "✓ Erledigt") if not self.case.workflow_status.is_completed else tr("board.reopen", "✓ Öffnen")
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

    # Cards per batch, per column. Mirrors CaseListWidget.RENDER_BATCH_SIZE - a
    # column is about this tall on a normal window.
    RENDER_BATCH_SIZE = 12

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
        self._col_signatures: dict[str, list] = {}
        # Was noch zu rendern ist, je Spalte, und wie weit sie schon ist.
        self._pending_cases: dict[str, list[Case]] = {}
        self._rendered_counts: dict[str, int] = {}
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

    def _columns_def(self) -> list[tuple[str, str]]:
        from services.i18n_service import tr
        return [
            ("support", tr("board.col_support_header", "📥 Support / In Bearbeitung")),
            ("dev", tr("board.col_dev_header", "💻 Entwickler / Dev-Team")),
            ("followup", tr("board.col_followup_header", "🔔 Wiedervorlage / Warten")),
            ("completed", tr("board.col_completed_header", "✓ Erledigte Fälle")),
        ]

    def create_board(self):
        # Clear existing children
        for child in self.winfo_children():
            child.destroy()

        self.grid_rowconfigure(0, weight=1)

        self.col_headers: dict[str, ctk.CTkLabel] = {}
        self.col_scrolls: dict[str, ctk.CTkScrollableFrame] = {}
        self.col_frames: dict[str, ctk.CTkFrame] = {}
        # Columns are new, so every cached card signature is stale.
        self._col_signatures: dict[str, list] = {}

        for idx, (col_key, col_title) in enumerate(self._columns_def()):
            self._build_column(idx, col_key, col_title)

    def _build_column(self, idx: int, col_key: str, col_title: str) -> None:
        """Builds exactly one board column, collapsed or expanded.

        Split out of create_board() so collapsing a column can replace that
        one column instead of tearing down and rebuilding all four.
        """
        from services.i18n_service import tr

        is_collapsed = self.collapsed_states.get(col_key, False)

        if is_collapsed:
            # Collapsed slim column
            self.grid_columnconfigure(idx, weight=0, minsize=42)
            col_frame = ctk.CTkFrame(self, width=42, fg_color=("gray80", "gray25"))
            col_frame.grid(row=0, column=idx, sticky="nsew", padx=2, pady=4)
            col_frame.grid_propagate(False)
            self.col_frames[col_key] = col_frame

            # Expand button
            btn_exp = ctk.CTkButton(
                col_frame,
                text=tr("board.expand_btn", "▶"),
                width=28,
                height=28,
                command=lambda k=col_key: self.toggle_column_collapse(k),
                fg_color=("gray75", "gray35"),
                hover_color=("gray65", "gray50"),
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
            self.col_frames[col_key] = col_frame

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
                text=tr("board.collapse_btn", "◀ Zuklappen"),
                width=80,
                height=24,
                font=ctk.CTkFont(size=10),
                command=lambda k=col_key: self.toggle_column_collapse(k),
                fg_color=("gray75", "gray35"),
                hover_color=("gray65", "gray50"),
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

        # Only this column changed. create_board() would destroy and rebuild all
        # four columns, and because it also wipes the card signatures every card
        # of every column would be re-rendered on top of that - for one toggle.
        columns = self._columns_def()
        entry = next(((i, key, title) for i, (key, title) in enumerate(columns) if key == col_key), None)
        if entry is None or not getattr(self, "col_frames", None):
            self.create_board()
            self.refresh_board()
            return

        idx, _key, col_title = entry
        old_frame = self.col_frames.pop(col_key, None)
        self.col_headers.pop(col_key, None)
        self.col_scrolls.pop(col_key, None)
        # This column's cards are gone with its frame, the other three are not.
        self._col_signatures.pop(col_key, None)
        if old_frame is not None:
            try:
                old_frame.destroy()
            except Exception:
                pass

        self._build_column(idx, col_key, col_title)
        self.refresh_board()

    def set_cases(self, cases: list[Case]):
        self.cases = cases
        self.refresh_board()

    @staticmethod
    def _card_signature(case: Case) -> tuple:
        """Everything a Kanban card puts on screen. Two equal signatures mean the
        rendered card would be pixel-identical, so it can be left alone."""
        customer = case.customer
        return (
            case.case_id,
            round(case.classification.calculated_score, 1),
            case.classification.title,
            case.workflow_status.current_actor,
            case.workflow_status.is_completed,
            case.workflow_status.followup_at,
            getattr(case, "is_internal", False),
            getattr(customer, "practice_name", "") if customer else "",
            bool(getattr(customer, "is_vip", False)) if customer else False,
        )

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

        from services.i18n_service import tr
        titles = {
            "support": f"📥 {tr('board.title_support', 'Support')} ({len(col_cases['support'])})",
            "dev": f"💻 {tr('board.title_dev', 'Entwickler')} ({len(col_cases['dev'])})",
            "followup": f"🔔 {tr('board.title_followup', 'Wiedervorlage')} ({len(col_cases['followup'])})",
            "completed": f"✓ {tr('board.title_completed', 'Erledigt')} ({len(col_cases['completed'])})",
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
                c_list_sorted = sorted(c_list, key=lambda x: x.classification.calculated_score, reverse=True)

                # Rebuilding a column means destroying and recreating ~12 widgets
                # per card. Skip it entirely when nothing this column displays has
                # changed - that is the common case for a refresh triggered by a
                # search keystroke, a theme toggle or the hourly scoring run.
                signature = [self._card_signature(c) for c in c_list_sorted]
                if self._col_signatures.get(col_key) == signature:
                    continue
                self._col_signatures[col_key] = signature

                scroll = self.col_scrolls[col_key]
                for child in scroll.winfo_children():
                    child.destroy()

                # Only a screenful up front; the rest follows on scroll. A card
                # costs roughly 15 ms to build, so rendering every case of every
                # column made the first switch to the board scale with the case
                # count - measured 880 ms at 31 cases and 2.7 s at 100.
                self._pending_cases[col_key] = c_list_sorted
                self._rendered_counts[col_key] = 0
                self._render_next_batch(col_key)
                self._install_scroll_listener(col_key)

    # --- Kartenrendering in Haeppchen, je Spalte ---

    def _col_canvas(self, col_key: str) -> Any:
        scroll = self.col_scrolls.get(col_key)
        if scroll is None:
            return None
        return getattr(scroll, "_parent_canvas", getattr(scroll, "_canvas", None))

    def _build_card(self, col_key: str, case: Case) -> None:
        card = KanbanCardWidget(
            self.col_scrolls[col_key],
            case=case,
            on_select_case=self.on_select_case,
            on_switch_to_cockpit=self.on_switch_to_cockpit,
            on_open_followup=self.on_open_followup,
            on_toggle_complete=self.on_toggle_complete,
            on_change_actor=self.on_change_actor,
        )
        card.pack(fill="x", pady=4, padx=2)

    def _render_next_batch(self, col_key: str, _event: Any = None) -> None:
        """Builds the next slice of cards for one column."""
        cases = self._pending_cases.get(col_key, [])
        done = self._rendered_counts.get(col_key, 0)
        if done >= len(cases) or col_key not in self.col_scrolls:
            return

        end = min(done + self.RENDER_BATCH_SIZE, len(cases))
        for case in cases[done:end]:
            self._build_card(col_key, case)
        self._rendered_counts[col_key] = end

        # A tall window may still leave the column half empty, so keep topping it
        # up until it overflows - once idle, never inside this call stack.
        if end < len(cases):
            try:
                self.after_idle(lambda k=col_key: self._fill_viewport(k))
            except Exception:
                pass

    def _fill_viewport(self, col_key: str) -> None:
        """Renders further batches while the column does not yet overflow."""
        cases = self._pending_cases.get(col_key, [])
        if self._rendered_counts.get(col_key, 0) >= len(cases):
            return
        canvas = self._col_canvas(col_key)
        if canvas is None:
            return
        try:
            if not canvas.winfo_exists():
                return
            top, bottom = canvas.yview()
        except Exception:
            return
        # bottom == 1.0 with cases left means what is rendered still fits.
        if bottom >= 0.995 or (bottom - top) >= 0.999:
            self._render_next_batch(col_key)

    def _on_scrolled(self, col_key: str, _event: Any = None) -> None:
        """Pulls in the next batch once the user scrolls near the end."""
        cases = self._pending_cases.get(col_key, [])
        if self._rendered_counts.get(col_key, 0) >= len(cases):
            return
        canvas = self._col_canvas(col_key)
        if canvas is None:
            return
        try:
            _top, bottom = canvas.yview()
        except Exception:
            return
        if bottom >= 0.9:
            try:
                self.after_idle(lambda k=col_key: self._render_next_batch(k))
            except Exception:
                self._render_next_batch(col_key)

    def _install_scroll_listener(self, col_key: str) -> None:
        """Binds the top-up to scrolling. Installed once per column widget."""
        canvas = self._col_canvas(col_key)
        if canvas is None or getattr(canvas, "_board_scroll_listener", False):
            return
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>", "<Configure>"):
            try:
                canvas.bind(seq, lambda e, k=col_key: self._on_scrolled(k, e), add="+")
            except Exception:
                pass
        try:
            canvas._board_scroll_listener = True
        except Exception:
            pass

    def render_all_cards(self, col_key: str | None = None) -> None:
        """Renders every remaining card. For tests and anything counting cards."""
        keys = [col_key] if col_key else list(self._pending_cases.keys())
        for key in keys:
            guard = 0
            while self._rendered_counts.get(key, 0) < len(self._pending_cases.get(key, [])):
                self._render_next_batch(key)
                guard += 1
                if guard > 500:
                    break

    def refresh_ui_labels(self):
        self.create_board()
        self.refresh_board()
