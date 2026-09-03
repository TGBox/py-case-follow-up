from typing import Any
import customtkinter as ctk
from typing import Callable
from models.case import Case
from enums import UrgencyLevel, get_actor_display
from constants import COLOR_MUTED_GRAY, COLOR_MUTED_HOVER


class CaseListWidget(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        on_case_selected: Callable[[Case], None],
        on_search_changed: Callable[[str], None],
        on_toggle_deep_search: Callable[[bool], None] | None = None,
    ):
        super().__init__(parent)
        self.on_case_selected = on_case_selected
        self.on_search_changed = on_search_changed
        self.on_toggle_deep_search = on_toggle_deep_search
        self.cases: list[Case] = []
        self.selected_case_id: str | None = None
        self.is_deep_search_active: bool = False
        self.deep_search_results: dict[str, dict] = {}
        self._card_widgets: dict[str, Any] = {}

        self.create_widgets()

    def create_widgets(self):
        from services.i18n_service import tr

        # Search Bar
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=10, pady=10)

        self.search_entry = ctk.CTkEntry(
            search_frame, placeholder_text=tr("cockpit.search_placeholder", "🔍 Suche / Token (z. B. vip:true status:open)...")
        )
        self.search_entry.pack(fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", lambda e: self.on_search_changed(self.search_entry.get()))

        # Quick Filter Buttons Bar
        qfilter_frame = ctk.CTkFrame(self, fg_color="transparent")
        qfilter_frame.pack(fill="x", padx=10, pady=(0, 6))

        self.qfilter_all_btn = ctk.CTkButton(qfilter_frame, text=tr("cockpit.filter_all", "Alle"), width=45, fg_color=COLOR_MUTED_GRAY, hover_color=COLOR_MUTED_HOVER, command=lambda: self.apply_quick_filter(""))
        self.qfilter_all_btn.pack(side="left", padx=2)
        self.qfilter_urgent_btn = ctk.CTkButton(qfilter_frame, text=tr("cockpit.filter_urgent", "🔥 Dringend"), width=80, fg_color=COLOR_MUTED_GRAY, hover_color=COLOR_MUTED_HOVER, command=lambda: self.apply_quick_filter("vip:true"))
        self.qfilter_urgent_btn.pack(side="left", padx=2)
        self.qfilter_followup_btn = ctk.CTkButton(qfilter_frame, text=tr("cockpit.filter_followup", "🔔 Wiedervorlage"), width=105, fg_color=COLOR_MUTED_GRAY, hover_color=COLOR_MUTED_HOVER, command=lambda: self.apply_quick_filter("reminder:due"))
        self.qfilter_followup_btn.pack(side="left", padx=2)
        
        self.deep_btn = ctk.CTkButton(
            qfilter_frame,
            text=tr("cockpit.filter_deep", "🔍 Tiefensuche"),
            width=100,
            fg_color="gray30",
            hover_color="darkmagenta",
            command=self.toggle_deep_search,
        )
        self.deep_btn.pack(side="left", padx=2)

        # Header Info
        self.count_label = ctk.CTkLabel(self, text=tr("case_list.zero_cases", "0 Fälle"), font=ctk.CTkFont(size=12, weight="bold"), anchor="w")
        self.count_label.pack(fill="x", padx=15, pady=(0, 5))

        # Scrollable Cases Container
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        from utils.ui_utils import enable_auto_hiding_scrollbar
        enable_auto_hiding_scrollbar(self.scroll_frame)

        self.wrap_labels: list[ctk.CTkLabel] = []
        self._last_wrap_width: int = 250
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
        w = self.winfo_width()
        if w > 50:
            target_wrap = max(160, w - 40)
            if abs(target_wrap - self._last_wrap_width) > 6:
                self._last_wrap_width = target_wrap
                for lbl in self.wrap_labels:
                    try:
                        lbl.configure(wraplength=target_wrap)
                    except Exception:
                        pass

    def toggle_deep_search(self):
        self.is_deep_search_active = not self.is_deep_search_active
        if self.is_deep_search_active:
            self.deep_btn.configure(fg_color="darkmagenta", hover_color="purple")
        else:
            self.deep_btn.configure(fg_color="gray30", hover_color="gray40")

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

        sig = lambda c: (c.case_id, round(c.classification.calculated_score, 1), c.workflow_status.is_completed, c.workflow_status.followup_at, c.workflow_status.current_actor)
        old_sigs = [sig(c) for c in self.cases]
        new_sigs = [sig(c) for c in new_cases]

        self.cases = new_cases
        from services.i18n_service import tr
        self.count_label.configure(text=tr("case_list.count_cases", "{count} Support-Fälle", count=len(self.cases)))

        if old_sigs == new_sigs and hasattr(self, "_card_widgets") and self._card_widgets and len(self._card_widgets) == len(new_cases):
            for case in self.cases:
                is_selected = case.case_id == self.selected_case_id
                row_bg = ("gray80", "gray25") if is_selected else ("gray92", "gray15")
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
            ctk.CTkLabel(self.scroll_frame, text=tr("case_list.no_cases", "Keine Fälle gefunden.")).pack(pady=20)
            return

        w = self.winfo_width()
        current_wrap = max(160, (w - 40) if w > 50 else 250)
        self._last_wrap_width = current_wrap

        for case in self.cases:
            is_selected = case.case_id == self.selected_case_id
            row_bg = ("gray80", "gray25") if is_selected else ("gray92", "gray15")

            card = ctk.CTkFrame(self.scroll_frame, fg_color=row_bg, corner_radius=6, cursor="hand2")
            card.pack(fill="x", pady=4, padx=(4, 6))
            self._card_widgets[case.case_id] = card

            # Click binding
            card.bind("<Button-1>", lambda e, c=case: self.select_case(c))

            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=(8, 10), pady=(6, 2))
            top_row.bind("<Button-1>", lambda e, c=case: self.select_case(c))

            score_lbl = ctk.CTkLabel(top_row, text=tr("case_list.score_pts", "Pkt.: {score}", score=f"{case.classification.calculated_score:.0f}"), font=ctk.CTkFont(size=11), text_color=("gray40", "gray70"))
            score_lbl.pack(side="right", padx=(0, 6))
            score_lbl.bind("<Button-1>", lambda e, c=case: self.select_case(c))

            # Urgency Dot Indicator
            urg = case.classification.urgency_level
            dot_color = "red" if urg == UrgencyLevel.RED else ("gold" if urg == UrgencyLevel.YELLOW else "limegreen")
            dot = ctk.CTkLabel(top_row, text=tr("common.dot", "●"), text_color=dot_color, font=ctk.CTkFont(size=16))
            dot.pack(side="left", padx=(0, 5))
            dot.bind("<Button-1>", lambda e, c=case: self.select_case(c))

            case_id_lbl = ctk.CTkLabel(top_row, text=case.case_id, font=ctk.CTkFont(weight="bold", size=13))
            case_id_lbl.pack(side="left")
            case_id_lbl.bind("<Button-1>", lambda e, c=case: self.select_case(c))

            if case.workflow_status.is_completed:
                done_lbl = ctk.CTkLabel(
                    top_row,
                    text=tr("case_list.completed_badge", "✓ ERLEDIGT"),
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color="white",
                    fg_color="forestgreen",
                    corner_radius=4,
                    padx=6,
                    pady=1,
                )
                done_lbl.pack(side="left", padx=(8, 0))
                done_lbl.bind("<Button-1>", lambda e, c=case: self.select_case(c))

            # Practice Name / Internal Badge
            if case.is_internal:
                practice_str = tr("case_list.internal_task", "🏢 INTERNE AUFGABE / VORGANG")
                prac_color = "dodgerblue"
            else:
                practice_str = case.customer.practice_name
                if case.customer.is_vip:
                    practice_str += " ★ VIP"
                prac_color = None

            disp_prac = practice_str if len(practice_str) <= 60 else practice_str[:57] + "..."

            prac_lbl = ctk.CTkLabel(
                card,
                text=disp_prac,
                anchor="w",
                justify="left",
                wraplength=current_wrap,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=prac_color,
            )
            prac_lbl.pack(fill="x", padx=12, pady=(0, 2))
            prac_lbl.bind("<Button-1>", lambda e, c=case: self.select_case(c))
            self.wrap_labels.append(prac_lbl)

            # Title & Actor
            sub_str = f"{case.classification.title} | {tr('case_list.assigned_to', 'Zuständig:')} {get_actor_display(case.workflow_status.current_actor)}"
            disp_sub = sub_str if len(sub_str) <= 80 else sub_str[:77] + "..."

            sub_lbl = ctk.CTkLabel(
                card,
                text=disp_sub,
                anchor="w",
                justify="left",
                wraplength=current_wrap,
                font=ctk.CTkFont(size=11),
                text_color=("gray40", "gray70"),
            )
            sub_lbl.pack(fill="x", padx=12, pady=(0, 2))
            sub_lbl.bind("<Button-1>", lambda e, c=case: self.select_case(c))
            self.wrap_labels.append(sub_lbl)

            # Deep Search Match Badges
            if self.is_deep_search_active and case.case_id in self.deep_search_results:
                res = self.deep_search_results[case.case_id]
                att_m = res.get("attachment_matches", [])
                wiki_m = res.get("wiki_matches", [])

                if att_m:
                    m0 = att_m[0]
                    att_text = f"📄 {m0['file_name']} ({tr('case_list.line_abbr', 'Z.')} {m0['line_number']}): \"{m0['snippet'][:35]}...\""
                    att_lbl = ctk.CTkLabel(
                        card,
                        text=att_text,
                        anchor="w",
                        justify="left",
                        wraplength=current_wrap,
                        font=ctk.CTkFont(size=10, weight="bold"),
                        text_color="plum",
                    )
                    att_lbl.pack(fill="x", padx=12, pady=(0, 2))
                    att_lbl.bind("<Button-1>", lambda e, c=case: self.select_case(c))
                    self.wrap_labels.append(att_lbl)

                if wiki_m:
                    w0 = wiki_m[0]
                    wiki_text = f"📖 {w0['title']} (Score: {w0['score']:.0f}): \"{w0['snippet'][:35]}...\""
                    wiki_lbl = ctk.CTkLabel(
                        card,
                        text=wiki_text,
                        anchor="w",
                        justify="left",
                        wraplength=current_wrap,
                        font=ctk.CTkFont(size=10, weight="bold"),
                        text_color="orchid",
                    )
                    wiki_lbl.pack(fill="x", padx=12, pady=(0, 2))
                    wiki_lbl.bind("<Button-1>", lambda e, c=case: self.select_case(c))
                    self.wrap_labels.append(wiki_lbl)

            if case.workflow_status.followup_at:
                from utils.datetime_utils import format_german_date_with_relative, format_german_time
                fw_date_str = format_german_date_with_relative(case.workflow_status.followup_at)
                fw_time_str = format_german_time(case.workflow_status.followup_at, with_uhr=True)

                fw_frame = ctk.CTkFrame(card, fg_color="transparent")
                fw_frame.pack(fill="x", padx=12, pady=(0, 3))
                fw_frame.bind("<Button-1>", lambda e, c=case: self.select_case(c))

                lbl_h = ctk.CTkLabel(
                    fw_frame,
                    text=tr("case_list.followup_at", "🔔 Nachfragen am:"),
                    height=0,
                    anchor="w",
                    justify="left",
                    wraplength=current_wrap,
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color="darkorange"
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
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color="darkorange"
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
                    font=ctk.CTkFont(size=10),
                    text_color="darkorange"
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
                        font=ctk.CTkFont(size=10),
                        text_color="darkorange"
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
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color=("dodgerblue", "cyan"),
                )
                tag_lbl.pack(fill="x", padx=12, pady=(0, 6))
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
                    vip_t = " ★ VIP" if c.customer.is_vip else ""
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

            CTkTooltip(card, text_or_func=lambda c=case: build_tooltip(c), delay_ms=400)

        from utils.ui_utils import bind_mouse_wheel_to_canvas
        bind_mouse_wheel_to_canvas(self.scroll_frame)

    def select_case(self, case: Case):
        from ui.widgets.ctk_tooltip import CTkTooltip
        CTkTooltip.dismiss_all()

        prev_id = self.selected_case_id
        self.selected_case_id = case.case_id

        # O(1) UI update if card frames exist
        if hasattr(self, "_card_widgets") and case.case_id in self._card_widgets:
            if prev_id and prev_id in self._card_widgets and prev_id != case.case_id:
                try:
                    prev_card: Any = self._card_widgets[prev_id]
                    prev_card.configure(fg_color=("gray92", "gray15"))
                except Exception:
                    pass
            try:
                curr_card: Any = self._card_widgets[case.case_id]
                curr_card.configure(fg_color=("gray80", "gray25"))
            except Exception:
                pass
            self.on_case_selected(case)
        else:
            self.render_list()
            self.on_case_selected(case)
