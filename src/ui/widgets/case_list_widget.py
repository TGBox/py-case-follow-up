import customtkinter as ctk
from typing import Callable
from models.case import Case
from enums import UrgencyLevel, get_actor_display


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

        self.create_widgets()

    def create_widgets(self):
        # Search Bar
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=10, pady=10)

        self.search_entry = ctk.CTkEntry(
            search_frame, placeholder_text="🔍 Suche / Token (z. B. vip:true status:open)..."
        )
        self.search_entry.pack(fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", lambda e: self.on_search_changed(self.search_entry.get()))

        # Quick Filter Buttons Bar
        qfilter_frame = ctk.CTkFrame(self, fg_color="transparent")
        qfilter_frame.pack(fill="x", padx=10, pady=(0, 6))

        ctk.CTkButton(qfilter_frame, text="Alle", width=45, fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40"), command=lambda: self.apply_quick_filter("")).pack(side="left", padx=2)
        ctk.CTkButton(qfilter_frame, text="🔥 Dringend", width=80, fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40"), command=lambda: self.apply_quick_filter("vip:true")).pack(side="left", padx=2)
        ctk.CTkButton(qfilter_frame, text="🔔 Wiedervorlage", width=105, fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40"), command=lambda: self.apply_quick_filter("reminder:due")).pack(side="left", padx=2)
        
        self.deep_btn = ctk.CTkButton(
            qfilter_frame,
            text="🔍 Tiefensuche",
            width=100,
            fg_color="gray30",
            hover_color="darkmagenta",
            command=self.toggle_deep_search,
        )
        self.deep_btn.pack(side="left", padx=2)

    def toggle_deep_search(self):
        self.is_deep_search_active = not self.is_deep_search_active
        if self.is_deep_search_active:
            self.deep_btn.configure(fg_color="darkmagenta", hover_color="purple")
        else:
            self.deep_btn.configure(fg_color="gray30", hover_color="gray40")

        if self.on_toggle_deep_search:
            self.on_toggle_deep_search(self.is_deep_search_active)
        self.on_search_changed(self.search_entry.get())

        # Header Info
        self.count_label = ctk.CTkLabel(self, text="0 Fälle", font=ctk.CTkFont(size=12, weight="bold"), anchor="w")
        self.count_label.pack(fill="x", padx=15, pady=(0, 5))

        # Scrollable Cases Container
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        from utils.ui_utils import enable_auto_hiding_scrollbar
        enable_auto_hiding_scrollbar(self.scroll_frame)

    def apply_quick_filter(self, filter_token: str):
        self.search_entry.delete(0, "end")
        if filter_token:
            self.search_entry.insert(0, filter_token)
        self.on_search_changed(filter_token)

    def set_cases(self, cases: list[Case], deep_results: dict[str, dict] | None = None):
        """Sets cases list sorted by score descending."""
        self.cases = sorted(cases, key=lambda c: c.classification.calculated_score, reverse=True)
        if deep_results is not None:
            self.deep_search_results = deep_results
        self.count_label.configure(text=f"{len(self.cases)} Support-Fälle")
        self.render_list()

    def render_list(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not self.cases:
            ctk.CTkLabel(self.scroll_frame, text="Keine Fälle gefunden.").pack(pady=20)
            return

        for case in self.cases:
            is_selected = case.case_id == self.selected_case_id
            row_bg = ("gray80", "gray25") if is_selected else ("gray92", "gray15")

            card = ctk.CTkFrame(self.scroll_frame, fg_color=row_bg, corner_radius=6, cursor="hand2")
            card.pack(fill="x", pady=4, padx=4)

            # Click binding
            card.bind("<Button-1>", lambda e, c=case: self.select_case(c))

            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=8, pady=(6, 2))
            top_row.bind("<Button-1>", lambda e, c=case: self.select_case(c))

            # Urgency Dot Indicator
            urg = case.classification.urgency_level
            dot_color = "red" if urg == UrgencyLevel.RED else ("gold" if urg == UrgencyLevel.YELLOW else "limegreen")
            dot = ctk.CTkLabel(top_row, text="●", text_color=dot_color, font=ctk.CTkFont(size=16))
            dot.pack(side="left", padx=(0, 5))

            case_id_lbl = ctk.CTkLabel(top_row, text=case.case_id, font=ctk.CTkFont(weight="bold", size=13))
            case_id_lbl.pack(side="left")
            case_id_lbl.bind("<Button-1>", lambda e, c=case: self.select_case(c))

            score_lbl = ctk.CTkLabel(top_row, text=f"Pts: {case.classification.calculated_score:.0f}", font=ctk.CTkFont(size=11), text_color=("gray40", "gray70"))
            score_lbl.pack(side="right")

            # Practice Name / Internal Badge
            if case.is_internal:
                practice_str = "🏢 INTERNE AUFGABE / VORGANG"
                prac_color = "dodgerblue"
            else:
                practice_str = case.customer.practice_name
                if case.customer.is_vip:
                    practice_str += " ★ VIP"
                prac_color = None

            prac_lbl = ctk.CTkLabel(
                card,
                text=practice_str,
                anchor="w",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=prac_color,
            )
            prac_lbl.pack(fill="x", padx=12, pady=(0, 2))
            prac_lbl.bind("<Button-1>", lambda e, c=case: self.select_case(c))

            # Title & Actor
            sub_str = f"{case.classification.title} | Zuständig: {get_actor_display(case.workflow_status.current_actor)}"
            sub_lbl = ctk.CTkLabel(card, text=sub_str, anchor="w", font=ctk.CTkFont(size=11), text_color=("gray40", "gray70"))
            sub_lbl.pack(fill="x", padx=12, pady=(0, 2))
            sub_lbl.bind("<Button-1>", lambda e, c=case: self.select_case(c))

            # Deep Search Match Badges
            if self.is_deep_search_active and case.case_id in self.deep_search_results:
                res = self.deep_search_results[case.case_id]
                att_m = res.get("attachment_matches", [])
                wiki_m = res.get("wiki_matches", [])

                if att_m:
                    m0 = att_m[0]
                    att_text = f"📄 {m0['file_name']} (Z. {m0['line_number']}): \"{m0['snippet'][:35]}...\""
                    att_lbl = ctk.CTkLabel(
                        card,
                        text=att_text,
                        anchor="w",
                        font=ctk.CTkFont(size=10, weight="bold"),
                        text_color="plum",
                    )
                    att_lbl.pack(fill="x", padx=12, pady=(0, 2))
                    att_lbl.bind("<Button-1>", lambda e, c=case: self.select_case(c))

                if wiki_m:
                    w0 = wiki_m[0]
                    wiki_text = f"📚 Wiki: {w0['title']}"
                    wiki_lbl = ctk.CTkLabel(
                        card,
                        text=wiki_text,
                        anchor="w",
                        font=ctk.CTkFont(size=10, weight="bold"),
                        text_color="orchid",
                    )
                    wiki_lbl.pack(fill="x", padx=12, pady=(0, 2))
                    wiki_lbl.bind("<Button-1>", lambda e, c=case: self.select_case(c))

            if case.workflow_status.followup_at:
                from utils.datetime_utils import format_german_datetime
                fw_dt_str = format_german_datetime(case.workflow_status.followup_at)
                fw_lbl = ctk.CTkLabel(
                    card,
                    text=f"🔔 Nachfragen am: {fw_dt_str}",
                    anchor="w",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color="darkorange"
                )
                fw_lbl.pack(fill="x", padx=12, pady=(0, 2))
                fw_lbl.bind("<Button-1>", lambda e, c=case: self.select_case(c))

            if case.classification.tags:
                tags_str = "🏷️ " + ", ".join(case.classification.tags)
                tag_lbl = ctk.CTkLabel(card, text=tags_str, anchor="w", font=ctk.CTkFont(size=10, weight="bold"), text_color=("dodgerblue", "cyan"))
                tag_lbl.pack(fill="x", padx=12, pady=(0, 6))
                tag_lbl.bind("<Button-1>", lambda e, c=case: self.select_case(c))

    def select_case(self, case: Case):
        self.selected_case_id = case.case_id
        self.render_list()
        self.on_case_selected(case)
