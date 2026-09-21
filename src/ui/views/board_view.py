from collections.abc import Callable
from typing import Any
import customtkinter as ctk

from constants import (
    BADGE_HEIGHT_SM,
    BOARD_CARD_WRAP_WIDTH,
    BOARD_COLLAPSED_COL_WIDTH,
    BOARD_EXPANDED_COL_MIN_WIDTH,
    BOARD_HEADER_HEIGHT,
    BTN_HEIGHT_MD,
    BTN_HEIGHT_SM,
    BTN_WIDTH_BOARD_REMIND,
    BTN_WIDTH_CARD_ACTION,
    BTN_WIDTH_SM,
    BTN_WIDTH_XS,
    CASE_LIST_BATCH_SIZE,
    COLOR_BOARD_REMIND,
    COLOR_BORDER_DARK,
    COLOR_BTN_EXPAND_HOVER,
    COLOR_BTN_GRAY,
    COLOR_BTN_GRAY_HOVER,
    COLOR_CARD_BG,
    COLOR_CARD_BORDER,
    COLOR_CARD_TITLE_FG,
    COLOR_COLLAPSED_COL_BG,
    COLOR_COMPLETED_GRAY,
    COLOR_FOLLOWUP_FG,
    COLOR_MUTED_LABEL,
    COLOR_SCORE_HIGH,
    COLOR_SCORE_LOW,
    COLOR_SCORE_MEDIUM,
    COLOR_SUCCESS,
    COLOR_TEXT_WHITE,
    CORNER_RADIUS_CARD,
    CORNER_RADIUS_SM,
    CORNER_RADIUS_XS,
    FONT_SIZE_BODY,
    FONT_SIZE_CONFIRM,
    FONT_SIZE_SM,
    FONT_SIZE_XS,
    PAD_LG,
    PAD_MD,
    PAD_SM,
    PAD_XS,
    USER_COLOR_TILE_SIZE,
    VIP_TAG_DISPLAY,
)
from enums import Actor, get_actor_display
from models.case import Case
from services.i18n_service import tr
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
        current_user_name: str = "",
        user_color: str | None = None,
        color_marker_enabled: bool = False,
    ):
        super().__init__(
            parent,
            corner_radius=CORNER_RADIUS_CARD,
            fg_color=COLOR_CARD_BG,
            border_width=1,
            border_color=COLOR_CARD_BORDER,
        )
        self.case = case
        self.on_select_case = on_select_case
        self.on_switch_to_cockpit = on_switch_to_cockpit
        self.on_open_followup = on_open_followup
        self.on_toggle_complete = on_toggle_complete
        self.on_change_actor = on_change_actor
        self.current_user_name = current_user_name
        self.user_color = user_color
        self.color_marker_enabled = color_marker_enabled

        self.create_card()

    def create_card(self):
        # Header: ID + Urgency Score Badge
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=PAD_LG, pady=(PAD_MD, PAD_XS))

        is_user_case = bool(
            self.current_user_name
            and (
                (self.case.assigned_to and self.case.assigned_to.strip().lower() == self.current_user_name.strip().lower())
                or (self.case.created_by and self.case.created_by.strip().lower() == self.current_user_name.strip().lower())
                or any(t.author and t.author.strip().lower() == self.current_user_name.strip().lower() for t in self.case.timeline)
            )
        )
        if is_user_case and self.color_marker_enabled and self.user_color:
            tile = ctk.CTkFrame(
                header_frame,
                width=USER_COLOR_TILE_SIZE,
                height=USER_COLOR_TILE_SIZE,
                corner_radius=CORNER_RADIUS_XS,
                fg_color=self.user_color,
                border_width=1,
                border_color=COLOR_BORDER_DARK,
            )
            tile.pack(side="left", padx=(0, PAD_SM), pady=PAD_XS)

        id_lbl = ctk.CTkLabel(
            header_frame, text=self.case.case_id, font=ctk.CTkFont(weight="bold", size=FONT_SIZE_CONFIRM)
        )
        id_lbl.pack(side="left")

        # Score badge
        score = self.case.classification.calculated_score
        score_color = COLOR_SCORE_HIGH if score >= 100 else (COLOR_SCORE_MEDIUM if score >= 50 else COLOR_SCORE_LOW)
        score_lbl = ctk.CTkLabel(
            header_frame,
            text=f"{tr('board.score', 'Score')} {score:.0f}",
            font=ctk.CTkFont(size=FONT_SIZE_XS, weight="bold"),
            text_color=COLOR_TEXT_WHITE,
            fg_color=score_color,
            corner_radius=CORNER_RADIUS_SM,
            width=BTN_WIDTH_XS,
            height=BADGE_HEIGHT_SM,
        )
        score_lbl.pack(side="right")

        # Customer Name + VIP (with auto-wrap)
        vip_str = VIP_TAG_DISPLAY if self.case.customer.is_vip else ""
        if self.case.is_internal:
            cust_str = f"🏢 {tr('cockpit.internal_task_title', 'INTERNE AUFGABE / VORGANG')}{vip_str}"
        else:
            cust_str = f"🏥 {self.case.customer.practice_name}{vip_str}"
        cust_lbl = ctk.CTkLabel(
            self,
            text=cust_str,
            font=ctk.CTkFont(size=FONT_SIZE_BODY, weight="bold"),
            anchor="w",
            justify="left",
            wraplength=BOARD_CARD_WRAP_WIDTH,
            text_color=COLOR_CARD_TITLE_FG,
        )
        cust_lbl.pack(fill="x", padx=PAD_LG, pady=(PAD_XS, PAD_XS))

        # Case Title (with auto-wrap)
        title_lbl = ctk.CTkLabel(
            self,
            text=self.case.classification.title,
            font=ctk.CTkFont(size=FONT_SIZE_SM),
            anchor="w",
            wraplength=BOARD_CARD_WRAP_WIDTH,
            justify="left",
        )
        title_lbl.pack(fill="x", padx=PAD_LG, pady=(0, PAD_SM))

        # Metadata Row: Actor + Followup
        meta_frame = ctk.CTkFrame(self, fg_color="transparent")
        meta_frame.pack(fill="x", padx=PAD_LG, pady=(0, PAD_MD))

        actor_txt = f"👤 {get_actor_display(self.case.workflow_status.current_actor)}"
        ctk.CTkLabel(
            meta_frame,
            text=actor_txt,
            font=ctk.CTkFont(size=FONT_SIZE_XS),
            text_color=COLOR_MUTED_LABEL,
            anchor="w",
            justify="left",
        ).pack(side="left")

        if self.case.workflow_status.followup_at:
            fw_txt = f"🔔 {format_german_datetime(self.case.workflow_status.followup_at)}"
            ctk.CTkLabel(
                meta_frame,
                text=fw_txt,
                font=ctk.CTkFont(size=FONT_SIZE_XS, weight="bold"),
                text_color=COLOR_FOLLOWUP_FG,
                anchor="e",
                justify="right",
            ).pack(side="right")

        # Action Buttons Row
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", padx=PAD_MD, pady=(PAD_SM, PAD_MD))

        ctk.CTkButton(
            action_frame,
            text=tr("board.cockpit_btn", "🎯 Cockpit"),
            command=lambda: self.on_switch_to_cockpit(self.case),
            width=BTN_WIDTH_CARD_ACTION,
            height=BTN_HEIGHT_SM,
            font=ctk.CTkFont(size=FONT_SIZE_XS),
            fg_color=COLOR_BTN_GRAY,
            hover_color=COLOR_BTN_GRAY_HOVER,
        ).pack(side="left", padx=PAD_XS)

        ctk.CTkButton(
            action_frame,
            text=tr("board.handover", "👤 Übergeben"),
            command=lambda: self.on_change_actor(self.case),
            width=BTN_WIDTH_SM,
            height=BTN_HEIGHT_SM,
            font=ctk.CTkFont(size=FONT_SIZE_XS),
        ).pack(side="left", padx=PAD_XS)

        ctk.CTkButton(
            action_frame,
            text=tr("board.remind", "🔔 Erinnere"),
            command=lambda: self.on_open_followup(self.case),
            width=BTN_WIDTH_BOARD_REMIND,
            height=BTN_HEIGHT_SM,
            font=ctk.CTkFont(size=FONT_SIZE_XS),
            fg_color=COLOR_BOARD_REMIND,
        ).pack(side="left", padx=PAD_XS)

        comp_text = (
            tr("cockpit.complete", "✓ Erledigt")
            if not self.case.workflow_status.is_completed
            else tr("board.reopen", "✓ Öffnen")
        )
        comp_color = COLOR_SUCCESS if not self.case.workflow_status.is_completed else COLOR_COMPLETED_GRAY
        ctk.CTkButton(
            action_frame,
            text=comp_text,
            command=lambda: self.on_toggle_complete(self.case),
            width=BTN_WIDTH_CARD_ACTION,
            height=BTN_HEIGHT_SM,
            font=ctk.CTkFont(size=FONT_SIZE_XS),
            fg_color=comp_color,
        ).pack(side="right", padx=PAD_XS)


class BoardView(ctk.CTkFrame):
    """Interactive 4-column Kanban workflow board with individual column collapsing."""

    # Cards per batch, per column. Mirrors CaseListWidget.RENDER_BATCH_SIZE - a
    # column is about this tall on a normal window.
    RENDER_BATCH_SIZE = CASE_LIST_BATCH_SIZE

    def __init__(
        self,
        parent,
        on_select_case: Callable[[Case], None],
        on_switch_to_cockpit: Callable[[Case], None],
        on_open_followup: Callable[[Case], None],
        on_toggle_complete: Callable[[Case], None],
        on_change_actor: Callable[[Case], None],
        app_config: Any | None = None,
        current_user_name: str = "",
        user_color: str | None = None,
        color_marker_enabled: bool = False,
    ):
        super().__init__(parent, fg_color="transparent")
        self.on_select_case = on_select_case
        self.on_switch_to_cockpit = on_switch_to_cockpit
        self.on_open_followup = on_open_followup
        self.on_toggle_complete = on_toggle_complete
        self.on_change_actor = on_change_actor
        self.app_config = app_config
        self.current_user_name = current_user_name
        self.user_color = user_color
        self.color_marker_enabled = color_marker_enabled

        self.cases: list[Case] = []
        self._col_signatures: dict[str, list] = {}
        # Was noch zu rendern ist, je Spalte, und wie weit sie schon ist.
        self._pending_cases: dict[str, list[Case]] = {}
        self._rendered_counts: dict[str, int] = {}
        self.collapsed_states: dict[str, bool] = {
            "hotline": False,
            "tech": False,
            "dev": False,
            "customer": False,
            "followup": False,
            "completed": False,
        }

        # Load collapsed state from profile / app_config
        if self.app_config:
            if hasattr(self.app_config, "board_collapsed") and isinstance(self.app_config.board_collapsed, dict):
                self.collapsed_states.update(self.app_config.board_collapsed)
            elif hasattr(self.app_config, "ui_settings") and hasattr(self.app_config.ui_settings, "board_collapsed"):
                self.collapsed_states.update(self.app_config.ui_settings.board_collapsed)

        # Map legacy "support" key if present
        if "support" in self.collapsed_states:
            self.collapsed_states["hotline"] = self.collapsed_states.pop("support")

        self.create_board()

    def set_user_color_settings(self, current_user_name: str, user_color: str | None, color_marker_enabled: bool):
        self.current_user_name = current_user_name
        self.user_color = user_color
        self.color_marker_enabled = color_marker_enabled
        self._col_signatures.clear()
        if self.cases:
            self.refresh_board()

    def _columns_def(self) -> list[tuple[str, str]]:
        return [
            ("hotline", tr("board.col_hotline_header", "📞 Hotline")),
            ("tech", tr("board.col_tech_header", "🔧 Technik")),
            ("dev", tr("board.col_dev_header", "💻 Entwicklung")),
            ("customer", tr("board.col_customer_header", "👤 Kunde")),
            ("followup", tr("board.col_followup_header", "🔔 Wiedervorlage")),
            ("completed", tr("board.col_completed_header", "✓ Erledigt")),
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
        is_collapsed = self.collapsed_states.get(col_key, False)

        if is_collapsed:
            # Collapsed slim column
            self.grid_columnconfigure(idx, weight=0, minsize=BOARD_COLLAPSED_COL_WIDTH)
            col_frame = ctk.CTkFrame(self, width=BOARD_COLLAPSED_COL_WIDTH, fg_color=COLOR_COLLAPSED_COL_BG)
            col_frame.grid(row=0, column=idx, sticky="nsew", padx=PAD_XS, pady=PAD_SM)
            col_frame.grid_propagate(False)
            self.col_frames[col_key] = col_frame

            # Expand button
            btn_exp = ctk.CTkButton(
                col_frame,
                text=tr("board.expand_btn", "▶"),
                width=BTN_HEIGHT_MD,
                height=BTN_HEIGHT_MD,
                command=lambda k=col_key: self.toggle_column_collapse(k),
                fg_color=COLOR_BTN_GRAY,
                hover_color=COLOR_BTN_EXPAND_HOVER,
            )
            btn_exp.pack(anchor="n", pady=PAD_MD, padx=PAD_MD)

            lbl = ctk.CTkLabel(
                col_frame,
                text=f"{col_title.split(' ')[0]}\n({col_key[0].upper()})",
                font=ctk.CTkFont(size=FONT_SIZE_BODY, weight="bold"),
            )
            lbl.pack(pady=PAD_LG)
            self.col_headers[col_key] = lbl
        else:
            # Expanded full column
            self.grid_columnconfigure(idx, weight=1, minsize=BOARD_EXPANDED_COL_MIN_WIDTH)
            col_frame = ctk.CTkFrame(self)
            col_frame.grid(row=0, column=idx, sticky="nsew", padx=PAD_SM, pady=PAD_SM)
            self.col_frames[col_key] = col_frame

            header_frame = ctk.CTkFrame(col_frame, height=BOARD_HEADER_HEIGHT, fg_color="transparent")
            header_frame.pack(fill="x", padx=PAD_MD, pady=(PAD_MD, PAD_SM))

            header_lbl = ctk.CTkLabel(
                header_frame,
                text=col_title,
                font=ctk.CTkFont(size=FONT_SIZE_CONFIRM, weight="bold"),
                anchor="w",
            )
            header_lbl.pack(side="left", padx=PAD_SM)
            self.col_headers[col_key] = header_lbl

            # Collapse button
            btn_col = ctk.CTkButton(
                header_frame,
                text=tr("board.collapse_btn", "◀ Zuklappen"),
                width=BTN_WIDTH_SM,
                height=BTN_HEIGHT_SM,
                font=ctk.CTkFont(size=FONT_SIZE_XS),
                command=lambda k=col_key: self.toggle_column_collapse(k),
                fg_color=COLOR_BTN_GRAY,
                hover_color=COLOR_BTN_EXPAND_HOVER,
            )
            btn_col.pack(side="right", padx=PAD_XS)

            scroll = ctk.CTkScrollableFrame(col_frame)
            scroll.pack(fill="both", expand=True, padx=PAD_SM, pady=PAD_SM)
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
            "hotline": [],
            "tech": [],
            "dev": [],
            "customer": [],
            "followup": [],
            "completed": [],
        }

        for c in self.cases:
            if c.workflow_status.is_completed:
                col_cases["completed"].append(c)
            elif c.workflow_status.followup_at:
                col_cases["followup"].append(c)
            elif c.workflow_status.current_actor in (Actor.DEVELOPMENT.value, "DEVELOPMENT", "DATA_DEVELOPMENT"):
                col_cases["dev"].append(c)
            elif c.workflow_status.current_actor in (Actor.TECH.value, "TECH", "DATA_TECH"):
                col_cases["tech"].append(c)
            elif c.workflow_status.current_actor in (Actor.CUSTOMER.value, "CUSTOMER", "DATA_CUSTOMER"):
                col_cases["customer"].append(c)
            else:
                col_cases["hotline"].append(c)

        from services.i18n_service import tr
        titles = {
            "hotline": f"📞 {tr('board.title_hotline', 'Hotline')} ({len(col_cases['hotline'])})",
            "tech": f"🔧 {tr('board.title_tech', 'Technik')} ({len(col_cases['tech'])})",
            "dev": f"💻 {tr('board.title_dev', 'Entwicklung')} ({len(col_cases['dev'])})",
            "customer": f"👤 {tr('board.title_customer', 'Kunde')} ({len(col_cases['customer'])})",
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
            current_user_name=self.current_user_name,
            user_color=self.user_color,
            color_marker_enabled=self.color_marker_enabled,
        )
        card.pack(fill="x", pady=PAD_SM, padx=PAD_XS)

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
        """Hooks the top-up into the column's scroll position. Once per column."""
        from utils.ui_utils import watch_scroll_position

        scroll = self.col_scrolls.get(col_key)
        if scroll is None:
            return
        watch_scroll_position(scroll, lambda _first, _last, k=col_key: self._on_scrolled(k))

        # Resizing the column can uncover empty space below the last card.
        canvas = self._col_canvas(col_key)
        if canvas is None or getattr(canvas, "_board_resize_listener", False):
            return
        try:
            canvas.bind("<Configure>", lambda e, k=col_key: self._on_scrolled(k, e), add="+")
            canvas._board_resize_listener = True
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
