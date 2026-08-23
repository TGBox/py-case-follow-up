import customtkinter as ctk
from typing import Callable
from models.case import Case
from ui.widgets.case_list_widget import CaseListWidget


class SplitView(ctk.CTkFrame):
    def __init__(self, parent, on_case_selected: Callable[[Case], None], on_search_changed: Callable[[str], None]):
        super().__init__(parent, fg_color="transparent")
        self.on_case_selected = on_case_selected
        self.on_search_changed = on_search_changed

        self.grid_columnconfigure(0, weight=4)
        self.grid_columnconfigure(1, weight=6)
        self.grid_rowconfigure(0, weight=1)

        self.left_widget = CaseListWidget(self, on_case_selected=on_case_selected, on_search_changed=on_search_changed)
        self.left_widget.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.right_frame = ctk.CTkFrame(self)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        ctk.CTkLabel(self.right_frame, text="Split-View Arbeitsbereich", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=20)

    def set_cases(self, cases: list[Case]):
        self.left_widget.set_cases(cases)
