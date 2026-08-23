import customtkinter as ctk
from typing import Callable
from src.models.case import Case


class TabView(ctk.CTkFrame):
    def __init__(self, parent, on_select_case: Callable[[Case], None]):
        super().__init__(parent, fg_color="transparent")
        self.on_select_case = on_select_case
        self.cases: list[Case] = []

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True)

        self.overview_tab = self.tabview.add("Fälle Übersicht")
        self.create_overview_table()

    def create_overview_table(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self.overview_tab)
        self.scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

    def set_cases(self, cases: list[Case]):
        self.cases = cases
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        # Header row
        h_frame = ctk.CTkFrame(self.scroll_frame, fg_color="gray30")
        h_frame.pack(fill="x", pady=2)

        ctk.CTkLabel(h_frame, text="ID", width=110, font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkLabel(h_frame, text="Praxis", width=220, font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkLabel(h_frame, text="Titel", width=260, font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkLabel(h_frame, text="Actor", width=120, font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkLabel(h_frame, text="Score", width=80, font=ctk.CTkFont(weight="bold")).pack(side="left")

        for c in cases:
            row = ctk.CTkFrame(self.scroll_frame, fg_color="gray20", cursor="hand2")
            row.pack(fill="x", pady=2)
            row.bind("<Button-1>", lambda e, case=c: self.on_select_case(case))

            ctk.CTkLabel(row, text=c.case_id, width=110, font=ctk.CTkFont(weight="bold")).pack(side="left")
            ctk.CTkLabel(row, text=c.customer.practice_name, width=220, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=c.classification.title, width=260, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=c.workflow_status.current_actor, width=120).pack(side="left")
            ctk.CTkLabel(row, text=f"{c.classification.calculated_score:.0f}", width=80).pack(side="left")
