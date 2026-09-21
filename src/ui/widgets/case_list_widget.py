from typing import Any
import customtkinter as ctk
from collections.abc import Callable
from models.case import Case
from enums import UrgencyLevel, get_actor_display
from constants import (
    BTN_WIDTH_FILTER_ALL,
    BTN_WIDTH_FILTER_DEEP,
    BTN_WIDTH_FILTER_FOLLOWUP,
    BTN_WIDTH_SM,
    CASE_LIST_BATCH_SIZE,
    CASE_LIST_PRACTICE_PREVIEW_LEN,
    CASE_LIST_SNIPPET_PREVIEW_LEN,
    CASE_LIST_TITLE_PREVIEW_LEN,
    CASE_LIST_WRAP_DEFAULT,
    CASE_LIST_WRAP_MIN,
    CASE_LIST_WRAP_OFFSET,
    CASE_LIST_WRAP_TOLERANCE,
    COLOR_BORDER_DARK,
    COLOR_CARD_BG,
    COLOR_CARD_BORDER,
    COLOR_CARD_DESELECTED_BG,
    COLOR_CARD_SELECTED_BG,
    COLOR_CARD_SELECTED_BORDER,
    COLOR_DEEP_ATTACHMENT,
    COLOR_DEEP_SEARCH_ACTIVE,
    COLOR_DEEP_SEARCH_ACTIVE_HOVER,
    COLOR_DEEP_SEARCH_INACTIVE,
    COLOR_DEEP_SEARCH_INACTIVE_HOVER,
    COLOR_DEEP_WIKI,
    COLOR_MUTED_GRAY,
    COLOR_MUTED_HOVER,
    COLOR_MUTED_LABEL,
    COLOR_SUBTITLE_MUTED,
    COLOR_SUCCESS,
    COLOR_TAG_BLUE,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_WHITE,
    COLOR_URGENCY_GREEN,
    COLOR_URGENCY_RED,
    COLOR_URGENCY_YELLOW,
    COLOR_WARNING_ORANGE,
    CORNER_RADIUS_CARD,
    CORNER_RADIUS_ENTRY,
    CORNER_RADIUS_MD,
    CORNER_RADIUS_SM,
    CORNER_RADIUS_XS,
    FONT_SIZE_BODY,
    FONT_SIZE_CONFIRM,
    FONT_SIZE_SM,
    FONT_SIZE_TITLE,
    FONT_SIZE_XS,
    INFO_FRAME_MIN_WIDTH_THRESHOLD,
    PAD_2XL,
    PAD_LG,
    PAD_MD,
    PAD_NONE,
    PAD_SM,
    PAD_XL,
    PAD_XS,
    SEARCH_DEBOUNCE_MS,
    TOOLTIP_LAZY_DELAY_MS,
    USER_COLOR_TILE_SIZE,
    VIP_TAG_DISPLAY,
)
from utils.ui_utils import create_highlighted_label, bind_mouse_wheel_to_canvas
from services.search_service import parse_search_query, SearchService


class CaseListWidget(ctk.CTkFrame):
    #: Cards built per slice. Roughly a screenful, so the first paint is fast
    #: while scrolling still never has to wait for a batch.
    RENDER_BATCH_SIZE = CASE_LIST_BATCH_SIZE

    def __init__(
        self,
        parent,
        on_case_selected: Callable[[Case], None],
        on_search_changed: Callable[[str], None],
        on_toggle_deep_search: Callable[[bool], None] | None = None,
        current_user_name: str = "",
        user_color: str | None = None,
        color_marker_enabled: bool = False,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)
        self.on_case_selected = on_case_selected
        self.on_search_changed = on_search_changed
        self.on_toggle_deep_search = on_toggle_deep_search
        self.current_user_name = current_user_name
        self.user_color = user_color
        self.color_marker_enabled = color_marker_enabled
        self.cases: list[Case] = []
        self.selected_case_id: str | None = None
        self.is_deep_search_active: bool = False
        self.deep_search_results: dict[str, dict] = {}
        self._card_widgets: dict[str, Any] = {}
        self._rendered_count: int = 0
        self._render_terms: list[str] = []
        self._render_wrap: int = CASE_LIST_WRAP_DEFAULT

        self.create_widgets()

    def set_user_color_settings(self, current_user_name: str, user_color: str | None, color_marker_enabled: bool):
        self.current_user_name = current_user_name
        self.user_color = user_color
        self.color_marker_enabled = color_marker_enabled
        if self.cases:
            self.render_list()

    def create_widgets(self):
        from services.i18n_service import tr

        # Search Bar
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=PAD_MD + PAD_XS, pady=PAD_MD + PAD_XS)

        self.search_entry = ctk.CTkEntry(
            search_frame, placeholder_text=tr("cockpit.search_placeholder", "🔍 Suche / Token (z. B. vip:true status:open)...")
        )
        self.search_entry.pack(fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", self._on_search_keyrelease)

        # Quick Filter Buttons Bar
        qfilter_frame = ctk.CTkFrame(self, fg_color="transparent")
        qfilter_frame.pack(fill="x", padx=PAD_MD + PAD_XS, pady=(PAD_NONE, CORNER_RADIUS_ENTRY))

        self.qfilter_all_btn = ctk.CTkButton(qfilter_frame, text=tr("cockpit.filter_all", "Alle"), width=BTN_WIDTH_FILTER_ALL, fg_color=COLOR_MUTED_GRAY, hover_color=COLOR_MUTED_HOVER, command=lambda: self.apply_quick_filter(""))
        self.qfilter_all_btn.pack(side="left", padx=PAD_XS)
        self.qfilter_urgent_btn = ctk.CTkButton(qfilter_frame, text=tr("cockpit.filter_urgent", "🔥 Dringend"), width=BTN_WIDTH_SM, fg_color=COLOR_MUTED_GRAY, hover_color=COLOR_MUTED_HOVER, command=lambda: self.apply_quick_filter("vip:true"))
        self.qfilter_urgent_btn.pack(side="left", padx=PAD_XS)
        self.qfilter_followup_btn = ctk.CTkButton(qfilter_frame, text=tr("cockpit.filter_followup", "🔔 Wiedervorlage"), width=BTN_WIDTH_FILTER_FOLLOWUP, fg_color=COLOR_MUTED_GRAY, hover_color=COLOR_MUTED_HOVER, command=lambda: self.apply_quick_filter("reminder:due"))
        self.qfilter_followup_btn.pack(side="left", padx=PAD_XS)

        self.deep_btn = ctk.CTkButton(
            qfilter_frame,
            text=tr("cockpit.filter_deep", "🔍 Tiefensuche"),
            width=BTN_WIDTH_FILTER_DEEP,
            fg_color=COLOR_DEEP_SEARCH_INACTIVE,
            hover_color=COLOR_DEEP_SEARCH_ACTIVE,
            command=self.toggle_deep_search,
        )
        self.deep_btn.pack(side="left", padx=PAD_XS)

        # Header Info
        self.count_label = ctk.CTkLabel(self, text=tr("case_list.zero_cases", "0 Fälle"), font=ctk.CTkFont(size=FONT_SIZE_BODY, weight="bold"), anchor="w")
        self.count_label.pack(fill="x", padx=PAD_XL - 1, pady=(PAD_NONE, PAD_SM + 1))

        # Scrollable Cases Container
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=PAD_SM + 1, pady=PAD_SM + 1)
        from utils.ui_utils import enable_auto_hiding_scrollbar
        enable_auto_hiding_scrollbar(self.scroll_frame)

        self.wrap_labels: list[ctk.CTkLabel] = []
        self._last_wrap_width: int = CASE_LIST_WRAP_DEFAULT
        self.bind("<Configure>", self._on_widget_configure)

    def refresh_ui_labels(self):
        from services.i18n_service import tr
        if hasattr(self, "search_entry"):
            self.search_entry.configure(placeholder_text=tr("cockpit.search_placeholder", "🔍 Suche / Token (z. B. vip:true status:open)..."))
        if hasattr(self, "qfilter_all_btn"):
            self.qfilter_all_btn.configure(text=tr("cockpit.filter_all", "Alle"))
        if hasattr(self, "qfilter_urgent_btn"):
            self.qfilter_urgent_btn.configure(text=tr("cockpit.filter_urgent", "🔥 Dringend"))
        if hasattr(self, "qfilter_followup_btn"):
            self.qfilter_followup_btn.configure(text=tr("cockpit.filter_followup", "🔔 Wiedervorlage"))
        if hasattr(self, "deep_btn"):
            self.deep_btn.configure(text=tr("cockpit.filter_deep", "🔍 Tiefensuche"))
        self.render_list()

    def _on_widget_configure(self, event=None):
        # Dragging the window edge fires this many times per second, and the
        # apply step touches every wrapped label in the list (several per case).
        # Coalescing into a single idle callback keeps one pass per resize burst
        # instead of one per event.
        if getattr(self, "_wrap_update_pending", False):
            return
        self._wrap_update_pending = True
        try:
            self.after_idle(self._apply_wrap_width)
        except Exception:
            self._wrap_update_pending = False
            self._apply_wrap_width()

    def _apply_wrap_width(self):
        self._wrap_update_pending = False
        try:
            w = self.winfo_width()
        except Exception:
            return
        if w <= INFO_FRAME_MIN_WIDTH_THRESHOLD:
            return
        target_wrap = max(CASE_LIST_WRAP_MIN, w - CASE_LIST_WRAP_OFFSET)
        if abs(target_wrap - self._last_wrap_width) <= CASE_LIST_WRAP_TOLERANCE:
            return
        self._last_wrap_width = target_wrap
        for lbl in self.wrap_labels:
            try:
                lbl.configure(wraplength=target_wrap)
            except Exception:
                pass

    def _on_search_keyrelease(self, event=None):
        """Debounces the search so the case list is re-rendered once per typing pause."""
        from utils.ui_utils import debounce
        debounce(self, "case_search", SEARCH_DEBOUNCE_MS, lambda: self.on_search_changed(self.search_entry.get()))

    def toggle_deep_search(self):
        self.is_deep_search_active = not self.is_deep_search_active
        if self.is_deep_search_active:
            self.deep_btn.configure(fg_color=COLOR_DEEP_SEARCH_ACTIVE, hover_color=COLOR_DEEP_SEARCH_ACTIVE_HOVER)
        else:
            self.deep_btn.configure(fg_color=COLOR_DEEP_SEARCH_INACTIVE, hover_color=COLOR_DEEP_SEARCH_INACTIVE_HOVER)

        if self.on_toggle_deep_search:
            self.on_toggle_deep_search(self.is_deep_search_active)
        self.on_search_changed(self.search_entry.get())

    def apply_quick_filter(self, filter_token: str):
        self.search_entry.delete(0, "end")
        if filter_token:
            self.search_entry.insert(0, filter_token)
        self.on_search_changed(filter_token)

    def set_cases(self, cases: list[Case], deep_results: dict[str, dict] | None = None):
        """Sets cases list sorted by score descending."""
        new_cases = sorted(cases, key=lambda c: c.classification.calculated_score, reverse=True)
        if deep_results is not None:
            self.deep_search_results = deep_results

        def sig(c):
            return (c.case_id, round(c.classification.calculated_score, 1), c.workflow_status.is_completed, c.workflow_status.followup_at, c.workflow_status.current_actor)

        old_sigs = [sig(c) for c in self.cases]
        new_sigs = [sig(c) for c in new_cases]

        self.cases = new_cases
        from services.i18n_service import tr
        self.count_label.configure(text=tr("case_list.count_cases", "{count} Support-Fälle", count=len(self.cases)))

        # Identical signatures mean the same cases in the same order, so only the
        # selection colour can differ. Cards not rendered yet simply get the right
        # colour when their batch is built.
        if old_sigs == new_sigs and self._card_widgets and self._rendered_count == min(self._rendered_count, len(new_cases)):
            for case in self.cases:
                is_selected = case.case_id == self.selected_case_id
                row_bg = COLOR_CARD_SELECTED_BG if is_selected else COLOR_CARD_DESELECTED_BG
                if case.case_id in self._card_widgets:
                    try:
                        self._card_widgets[case.case_id].configure(fg_color=row_bg)
                    except Exception:
                        pass
            return

        self.render_list()

    def render_list(self):
        from services.i18n_service import tr

        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.wrap_labels.clear()
        self._card_widgets: dict[str, Any] = {}

        if not self.cases:
            ctk.CTkLabel(self.scroll_frame, text=tr("case_list.no_cases", "Keine Fälle gefunden.")).pack(pady=PAD_2XL)
            return

        w = self.winfo_width()
        current_wrap = max(CASE_LIST_WRAP_MIN, (w - CASE_LIST_WRAP_OFFSET) if w > INFO_FRAME_MIN_WIDTH_THRESHOLD else CASE_LIST_WRAP_DEFAULT)
        self._last_wrap_width = current_wrap

        query_str = self.search_entry.get().strip() if hasattr(self, "search_entry") else ""
        parsed_q = parse_search_query(query_str) if query_str else None
        search_terms = parsed_q.free_text_terms if parsed_q else []

        self._render_terms = search_terms
        self._render_wrap = current_wrap
        self._rendered_count = 0
        self._render_next_batch()

        bind_mouse_wheel_to_canvas(self.scroll_frame)
        self._install_scroll_listener()

    def _scroll_canvas(self) -> Any:
        return getattr(self.scroll_frame, "_parent_canvas", getattr(self.scroll_frame, "_canvas", None))

    def _install_scroll_listener(self) -> None:
        """Hooks the batch top-up into the scroll position. Installed once per widget."""
        if getattr(self, "_scroll_listener_installed", False):
            return
        from utils.ui_utils import watch_scroll_position

        # Not <MouseWheel>: that event goes to the card under the pointer, and
        # dragging the scrollbar fires no event at all - see watch_scroll_position.
        watch_scroll_position(self.scroll_frame, lambda _first, _last: self._on_scrolled())

        canvas = self._scroll_canvas()
        if canvas is not None:
            try:
                # Resizing can uncover empty space below the last card.
                canvas.bind("<Configure>", self._on_scrolled, add="+")
            except Exception:
                pass
        self._scroll_listener_installed = True

    def _render_next_batch(self, _event: Any = None) -> None:
        """Builds the next slice of cards.

        A card costs roughly 20 ms to build, so rendering all of them on every
        keystroke is what made the search feel sluggish. Only a screenful is
        built up front; the rest follows as the user scrolls towards it.
        """
        total = len(self.cases)
        if self._rendered_count >= total:
            return

        end = min(self._rendered_count + self.RENDER_BATCH_SIZE, total)
        for case in self.cases[self._rendered_count:end]:
            self._build_card(case, self._render_terms, self._render_wrap)
        self._rendered_count = end

        # The viewport may still not be full (tall window, short cards), so keep
        # topping it up until it is - once idle, never in this call stack.
        if self._rendered_count < total:
            try:
                self.after_idle(self._fill_viewport)
            except Exception:
                pass

    def _fill_viewport(self) -> None:
        """Renders further batches while the list does not yet overflow the canvas."""
        if self._rendered_count >= len(self.cases):
            return
        canvas = self._scroll_canvas()
        if canvas is None:
            return
        try:
            if not canvas.winfo_exists():
                return
            top, bottom = canvas.yview()
        except Exception:
            return
        # bottom == 1.0 while content still remains means everything rendered so
        # far fits on screen - there is nothing to scroll to yet.
        if bottom >= 0.995 or (bottom - top) >= 0.999:
            self._render_next_batch()

    def _on_scrolled(self, _event: Any = None) -> None:
        """Pulls in the next batch once the user scrolls near the end."""
        if self._rendered_count >= len(self.cases):
            return
        canvas = self._scroll_canvas()
        if canvas is None:
            return
        try:
            _top, bottom = canvas.yview()
        except Exception:
            return
        if bottom >= 0.9:
            try:
                self.after_idle(self._render_next_batch)
            except Exception:
                self._render_next_batch()

    def _ensure_case_rendered(self, case_id: str) -> bool:
        """Renders forward until case_id has a card (used when selecting off-screen)."""
        guard = 0
        while case_id not in self._card_widgets and self._rendered_count < len(self.cases):
            self._render_next_batch()
            guard += 1
            if guard > 500:
                break
        return case_id in self._card_widgets

    def _build_card(self, case: Case, search_terms: list[str], current_wrap: int) -> None:
        """Builds one case card. Called per visible case, not for the whole list."""
        from services.i18n_service import tr

        is_selected = case.case_id == self.selected_case_id
        row_bg = COLOR_CARD_SELECTED_BG if is_selected else COLOR_CARD_BG
        border_col = COLOR_CARD_SELECTED_BORDER if is_selected else COLOR_CARD_BORDER

        card = ctk.CTkFrame(self.scroll_frame, fg_color=row_bg, corner_radius=CORNER_RADIUS_CARD, border_width=1, border_color=border_col, cursor="hand2")
        card.pack(fill="x", pady=PAD_SM, padx=(PAD_SM, CORNER_RADIUS_MD))
        self._card_widgets[case.case_id] = card

        # Click binding
        card.bind("<Button-1>", lambda e, c=case: self.select_case(c))

        top_row = ctk.CTkFrame(card, fg_color="transparent")
        top_row.pack(fill="x", padx=(PAD_MD, PAD_MD + PAD_XS), pady=(CORNER_RADIUS_MD, PAD_XS))
        top_row.bind("<Button-1>", lambda e, c=case: self.select_case(c))

        score_lbl = ctk.CTkLabel(top_row, text=tr("case_list.score_pts", "Pkt.: {score}", score=f"{case.classification.calculated_score:.0f}"), font=ctk.CTkFont(size=FONT_SIZE_SM), text_color=COLOR_MUTED_LABEL)
        score_lbl.pack(side="right", padx=(PAD_NONE, CORNER_RADIUS_MD))
        score_lbl.bind("<Button-1>", lambda e, c=case: self.select_case(c))

        # Urgency Dot Indicator
        urg = case.classification.urgency_level
        dot_color = (
            COLOR_URGENCY_RED
            if urg == UrgencyLevel.RED
            else (COLOR_URGENCY_YELLOW if urg == UrgencyLevel.YELLOW else COLOR_URGENCY_GREEN)
        )
        dot = ctk.CTkLabel(top_row, text=tr("common.dot", "●"), text_color=dot_color, font=ctk.CTkFont(size=FONT_SIZE_TITLE - 1))
        dot.pack(side="left", padx=(PAD_NONE, PAD_SM + 1))
        dot.bind("<Button-1>", lambda e, c=case: self.select_case(c))

        is_user_case = bool(
            self.current_user_name
            and (
                (case.assigned_to and case.assigned_to.strip().lower() == self.current_user_name.strip().lower())
                or (case.created_by and case.created_by.strip().lower() == self.current_user_name.strip().lower())
                or any(t.author and t.author.strip().lower() == self.current_user_name.strip().lower() for t in case.timeline)
            )
        )
        if is_user_case and self.color_marker_enabled and self.user_color:
            tile = ctk.CTkFrame(
                top_row,
                width=USER_COLOR_TILE_SIZE,
                height=USER_COLOR_TILE_SIZE,
                corner_radius=CORNER_RADIUS_XS,
                fg_color=self.user_color,
                border_width=1,
                border_color=COLOR_BORDER_DARK,
            )
            tile.pack(side="left", padx=(PAD_NONE, PAD_SM), pady=PAD_XS)
            tile.bind("<Button-1>", lambda e, c=case: self.select_case(c))

        if search_terms and any(t.lower() in case.case_id.lower() for t in search_terms):
            case_id_lbl = create_highlighted_label(
                top_row,
                text=case.case_id,
                query=search_terms,
                font=ctk.CTkFont(weight="bold", size=FONT_SIZE_CONFIRM),
                text_color=COLOR_TEXT_PRIMARY,
                bg_color=row_bg,
                wrap="none",
                on_click=lambda e, c=case: self.select_case(c),
                scroll_frame=self.scroll_frame,
            )
        else:
            case_id_lbl = ctk.CTkLabel(top_row, text=case.case_id, font=ctk.CTkFont(weight="bold", size=FONT_SIZE_CONFIRM))
            case_id_lbl.bind("<Button-1>", lambda e, c=case: self.select_case(c))
        case_id_lbl.pack(side="left")

        if case.workflow_status.is_completed:
            done_lbl = ctk.CTkLabel(
                top_row,
                text=tr("case_list.completed_badge", "✓ ERLEDIGT"),
                font=ctk.CTkFont(size=FONT_SIZE_XS, weight="bold"),
                text_color=COLOR_TEXT_WHITE,
                fg_color=COLOR_SUCCESS,
                corner_radius=CORNER_RADIUS_SM,
                padx=CORNER_RADIUS_MD,
                pady=1,
            )
            done_lbl.pack(side="left", padx=(PAD_MD, PAD_NONE))
            done_lbl.bind("<Button-1>", lambda e, c=case: self.select_case(c))

        # Practice Name / Internal Badge
        if case.is_internal:
            practice_str = tr("case_list.internal_task", "🏢 INTERNE AUFGABE / VORGANG")
            prac_color = "dodgerblue"
        else:
            practice_str = case.customer.practice_name
            if case.customer.is_vip:
                practice_str += VIP_TAG_DISPLAY
            prac_color = None

        disp_prac = practice_str if len(practice_str) <= CASE_LIST_PRACTICE_PREVIEW_LEN else practice_str[:CASE_LIST_PRACTICE_PREVIEW_LEN - 3] + "..."

        if search_terms and any(t.lower() in disp_prac.lower() for t in search_terms):
            prac_lbl = create_highlighted_label(
                card,
                text=disp_prac,
                query=search_terms,
                font=ctk.CTkFont(size=FONT_SIZE_BODY, weight="bold"),
                text_color=prac_color or ("black", "white"),
                bg_color=row_bg,
                wrap="word",
                on_click=lambda e, c=case: self.select_case(c),
                scroll_frame=self.scroll_frame,
            )
        else:
            prac_lbl = ctk.CTkLabel(
                card,
                text=disp_prac,
                anchor="w",
                justify="left",
                wraplength=current_wrap,
                font=ctk.CTkFont(size=FONT_SIZE_BODY, weight="bold"),
                text_color=prac_color,
            )
            prac_lbl.bind("<Button-1>", lambda e, c=case: self.select_case(c))
            self.wrap_labels.append(prac_lbl)
        prac_lbl.pack(fill="x", padx=PAD_LG, pady=(PAD_NONE, PAD_XS))

        # Title & Actor
        sub_str = f"{case.classification.title} | {tr('case_list.assigned_to', 'Zuständig:')} {get_actor_display(case.workflow_status.current_actor)}"
        disp_sub = sub_str if len(sub_str) <= CASE_LIST_TITLE_PREVIEW_LEN else sub_str[:CASE_LIST_TITLE_PREVIEW_LEN - 3] + "..."

        if search_terms and any(t.lower() in disp_sub.lower() for t in search_terms):
            sub_lbl = create_highlighted_label(
                card,
                text=disp_sub,
                query=search_terms,
                font=ctk.CTkFont(size=FONT_SIZE_SM),
                text_color=COLOR_MUTED_LABEL,
                bg_color=row_bg,
                wrap="word",
                on_click=lambda e, c=case: self.select_case(c),
                scroll_frame=self.scroll_frame,
            )
        else:
            sub_lbl = ctk.CTkLabel(
                card,
                text=disp_sub,
                anchor="w",
                justify="left",
                wraplength=current_wrap,
                font=ctk.CTkFont(size=FONT_SIZE_SM),
                text_color=COLOR_MUTED_LABEL,
            )
            sub_lbl.bind("<Button-1>", lambda e, c=case: self.select_case(c))
            self.wrap_labels.append(sub_lbl)
        sub_lbl.pack(fill="x", padx=PAD_LG, pady=(PAD_NONE, PAD_XS))

        # Matches in timeline / tags / notes / form fields
        if search_terms:
            case_match_summary = SearchService.extract_case_search_match_summary(case, search_terms)
            if case_match_summary:
                match_lbl = create_highlighted_label(
                    card,
                    text=case_match_summary,
                    query=search_terms,
                    font=ctk.CTkFont(size=FONT_SIZE_XS),
                    text_color=COLOR_SUBTITLE_MUTED,
                    bg_color=row_bg,
                    wrap="word",
                    on_click=lambda e, c=case: self.select_case(c),
                    scroll_frame=self.scroll_frame,
                )
                match_lbl.pack(fill="x", padx=PAD_LG, pady=(PAD_NONE, PAD_XS))

        # Deep Search Match Badges
        if self.is_deep_search_active and case.case_id in self.deep_search_results:
            res = self.deep_search_results[case.case_id]
            att_m = res.get("attachment_matches", [])
            wiki_m = res.get("wiki_matches", [])

            if att_m:
                m0 = att_m[0]
                att_text = f"📄 {m0['file_name']} ({tr('case_list.line_abbr', 'Z.')} {m0['line_number']}): \"{m0['snippet'][:CASE_LIST_SNIPPET_PREVIEW_LEN]}...\""
                if search_terms and any(t.lower() in att_text.lower() for t in search_terms):
                    att_lbl = create_highlighted_label(
                        card,
                        text=att_text,
                        query=search_terms,
                        font=ctk.CTkFont(size=FONT_SIZE_XS, weight="bold"),
                        text_color=COLOR_DEEP_ATTACHMENT,
                        bg_color=row_bg,
                        wrap="word",
                        on_click=lambda e, c=case: self.select_case(c),
                        scroll_frame=self.scroll_frame,
                    )
                else:
                    att_lbl = ctk.CTkLabel(
                        card,
                        text=att_text,
                        anchor="w",
                        justify="left",
                        wraplength=current_wrap,
                        font=ctk.CTkFont(size=FONT_SIZE_XS, weight="bold"),
                        text_color=COLOR_DEEP_ATTACHMENT,
                    )
                    att_lbl.bind("<Button-1>", lambda e, c=case: self.select_case(c))
                    self.wrap_labels.append(att_lbl)
                att_lbl.pack(fill="x", padx=PAD_LG, pady=(PAD_NONE, PAD_XS))

            if wiki_m:
                w0 = wiki_m[0]
                wiki_text = f"📖 {w0['title']} (Score: {w0['score']:.0f}): \"{w0['snippet'][:CASE_LIST_SNIPPET_PREVIEW_LEN]}...\""
                if search_terms and any(t.lower() in wiki_text.lower() for t in search_terms):
                    wiki_lbl = create_highlighted_label(
                        card,
                        text=wiki_text,
                        query=search_terms,
                        font=ctk.CTkFont(size=FONT_SIZE_XS, weight="bold"),
                        text_color=COLOR_DEEP_WIKI,
                        bg_color=row_bg,
                        wrap="word",
                        on_click=lambda e, c=case: self.select_case(c),
                        scroll_frame=self.scroll_frame,
                    )
                else:
                    wiki_lbl = ctk.CTkLabel(
                        card,
                        text=wiki_text,
                        anchor="w",
                        justify="left",
                        wraplength=current_wrap,
                        font=ctk.CTkFont(size=FONT_SIZE_XS, weight="bold"),
                        text_color=COLOR_DEEP_WIKI,
                    )
                    wiki_lbl.bind("<Button-1>", lambda e, c=case: self.select_case(c))
                    self.wrap_labels.append(wiki_lbl)
                wiki_lbl.pack(fill="x", padx=PAD_LG, pady=(PAD_NONE, PAD_XS))

        bind_mouse_wheel_to_canvas(card, self.scroll_frame)

        if case.workflow_status.followup_at:
            from utils.datetime_utils import format_german_date_with_relative, format_german_time
            fw_date_str = format_german_date_with_relative(case.workflow_status.followup_at)
            fw_time_str = format_german_time(case.workflow_status.followup_at, with_uhr=True)

            fw_frame = ctk.CTkFrame(card, fg_color="transparent")
            fw_frame.pack(fill="x", padx=PAD_LG, pady=(PAD_NONE, PAD_SM - 1))
            fw_frame.bind("<Button-1>", lambda e, c=case: self.select_case(c))

            lbl_h = ctk.CTkLabel(
                fw_frame,
                text=tr("case_list.followup_at", "🔔 Nachfragen am:"),
                height=0,
                anchor="w",
                justify="left",
                wraplength=current_wrap,
                font=ctk.CTkFont(size=FONT_SIZE_XS, weight="bold"),
                text_color=COLOR_WARNING_ORANGE,
            )
            lbl_h.pack(fill="x", pady=0)
            lbl_h.bind("<Button-1>", lambda e, c=case: self.select_case(c))
            self.wrap_labels.append(lbl_h)

            lbl_d = ctk.CTkLabel(
                fw_frame,
                text=f"  {fw_date_str}",
                height=0,
                anchor="w",
                justify="left",
                wraplength=current_wrap,
                font=ctk.CTkFont(size=FONT_SIZE_XS, weight="bold"),
                text_color=COLOR_WARNING_ORANGE,
            )
            lbl_d.pack(fill="x", pady=0)
            lbl_d.bind("<Button-1>", lambda e, c=case: self.select_case(c))
            self.wrap_labels.append(lbl_d)

            lbl_t = ctk.CTkLabel(
                fw_frame,
                text=f"  {fw_time_str}",
                height=0,
                anchor="w",
                justify="left",
                wraplength=current_wrap,
                font=ctk.CTkFont(size=FONT_SIZE_XS),
                text_color=COLOR_WARNING_ORANGE,
            )
            lbl_t.pack(fill="x", pady=0)
            lbl_t.bind("<Button-1>", lambda e, c=case: self.select_case(c))
            self.wrap_labels.append(lbl_t)

            if case.workflow_status.followup_note:
                lbl_n = ctk.CTkLabel(
                    fw_frame,
                    text=f"  {case.workflow_status.followup_note}",
                    height=0,
                    anchor="w",
                    justify="left",
                    wraplength=current_wrap,
                    font=ctk.CTkFont(size=FONT_SIZE_XS),
                    text_color=COLOR_WARNING_ORANGE,
                )
                lbl_n.pack(fill="x", pady=0)
                lbl_n.bind("<Button-1>", lambda e, c=case: self.select_case(c))
                self.wrap_labels.append(lbl_n)

        if case.classification.tags:
            tags_str = "🏷 " + ", ".join(case.classification.tags)
            tag_lbl = ctk.CTkLabel(
                card,
                text=tags_str,
                anchor="w",
                justify="left",
                wraplength=current_wrap,
                font=ctk.CTkFont(size=FONT_SIZE_XS, weight="bold"),
                text_color=COLOR_TAG_BLUE,
            )
            tag_lbl.pack(fill="x", padx=PAD_LG, pady=(PAD_NONE, CORNER_RADIUS_MD))
            tag_lbl.bind("<Button-1>", lambda e, c=case: self.select_case(c))
            self.wrap_labels.append(tag_lbl)

        # CTkTooltip hover overlay for full untruncated details
        from ui.widgets.ctk_tooltip import CTkTooltip
        def build_tooltip(c: Case = case) -> str:
            from services.i18n_service import tr
            lines = [
                tr("case_list.tooltip_case_header", "📌 Fall: {id} (Priorität: {score} Pkt.)", id=c.case_id, score=f"{c.classification.calculated_score:.0f}"),
            ]
            if c.is_internal:
                lines.append(tr("case_list.tooltip_customer_internal", "🏢 Kunde: INTERNE AUFGABE ({id})", id=c.customer.customer_id))
            else:
                vip_t = VIP_TAG_DISPLAY if c.customer.is_vip else ""
                lines.append(tr("case_list.tooltip_customer_practice", "🏥 Kunde: {name} ({id}){vip}", name=c.customer.practice_name, id=c.customer.customer_id, vip=vip_t))
                lines.append(tr("case_list.tooltip_contact", "👤 Ansprechpartner: {contact}", contact=c.customer.contact_person))

            lines.append(tr("case_list.tooltip_topic", "📋 Thema: {title}", title=c.classification.title))
            lines.append(tr("case_list.tooltip_assigned", "👤 Zuständig: {actor}", actor=get_actor_display(c.workflow_status.current_actor)))

            if c.workflow_status.followup_at:
                from utils.datetime_utils import format_german_date_with_relative, format_german_time
                fw_d = format_german_date_with_relative(c.workflow_status.followup_at)
                fw_tm = format_german_time(c.workflow_status.followup_at, with_uhr=True)
                note_t = f" ({c.workflow_status.followup_note})" if c.workflow_status.followup_note else ""
                lines.append(tr("case_list.tooltip_followup", "🔔 Wiedervorlage: {date} um {time}{note}", date=fw_d, time=fw_tm, note=note_t))

            if c.classification.tags:
                lines.append(tr("case_list.tooltip_tags", "🏷 Tags: {tags}", tags=', '.join(c.classification.tags)))

            return "\n".join(lines)

        CTkTooltip.attach_lazy(card, text_or_func=lambda c=case: build_tooltip(c), delay_ms=TOOLTIP_LAZY_DELAY_MS)

    def select_case(self, case: Case):
        from ui.widgets.ctk_tooltip import CTkTooltip
        CTkTooltip.dismiss_all()

        prev_id = self.selected_case_id
        self.selected_case_id = case.case_id

        # O(1) UI update if card frames exist. A case further down the list may
        # not be built yet, so render forward to it instead of rebuilding.
        if self._card_widgets and case.case_id not in self._card_widgets:
            self._ensure_case_rendered(case.case_id)

        if hasattr(self, "_card_widgets") and case.case_id in self._card_widgets:
            if prev_id and prev_id in self._card_widgets and prev_id != case.case_id:
                try:
                    prev_card: Any = self._card_widgets[prev_id]
                    prev_card.configure(fg_color=COLOR_CARD_DESELECTED_BG)
                except Exception:
                    pass
            try:
                curr_card: Any = self._card_widgets[case.case_id]
                curr_card.configure(fg_color=COLOR_CARD_SELECTED_BG)
            except Exception:
                pass
            self.on_case_selected(case)
        else:
            self.render_list()
            self.on_case_selected(case)
