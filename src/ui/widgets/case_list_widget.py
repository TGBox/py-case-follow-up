import customtkinter as ctk
from typing import Callable
from models.case import Case
from enums import UrgencyLevel


class CaseListWidget(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        on_case_selected: Callable[[Case], None],
        on_search_changed: Callable[[str], None],
    ):
        super().__init__(parent)
        self.on_case_selected = on_case_selected
        self.on_search_changed = on_search_changed
        self.cases: list[Case] = []
        self.selected_case_id: str | None = None

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

        # Header Info
        self.count_label = ctk.CTkLabel(self, text="0 Fälle", font=ctk.CTkFont(size=12, weight="bold"), anchor="w")
        self.count_label.pack(fill="x", padx=15, pady=(0, 5))

        # Scrollable Cases Container
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

    def set_cases(self, cases: list[Case]):
        """Sets cases list sorted by score descending."""
        self.cases = sorted(cases, key=lambda c: c.classification.calculated_score, reverse=True)
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

            # Practice Name
            practice_str = case.customer.practice_name
            if case.customer.is_vip:
                practice_str += " ★ VIP"
            prac_lbl = ctk.CTkLabel(card, text=practice_str, anchor="w", font=ctk.CTkFont(size=12, weight="bold"))
            prac_lbl.pack(fill="x", padx=12, pady=(0, 2))
            prac_lbl.bind("<Button-1>", lambda e, c=case: self.select_case(c))

            # Title & Actor
            sub_str = f"{case.classification.title} | Actor: {case.workflow_status.current_actor}"
            sub_lbl = ctk.CTkLabel(card, text=sub_str, anchor="w", font=ctk.CTkFont(size=11), text_color=("gray40", "gray70"))
            sub_lbl.pack(fill="x", padx=12, pady=(0, 6))
            sub_lbl.bind("<Button-1>", lambda e, c=case: self.select_case(c))

    def select_case(self, case: Case):
        self.selected_case_id = case.case_id
        self.render_list()
        self.on_case_selected(case)
