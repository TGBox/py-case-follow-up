import customtkinter as ctk
from datetime import datetime, timedelta
from typing import Callable
from models.case import Case
from utils.datetime_utils import format_german_datetime, parse_iso, get_local_now, format_german_date


class FollowupFlyoutDialog(ctk.CTkToplevel):
    """Flyout list showing all due followups & deadlines with quick actions (+1 Tag, +1 Woche)."""

    def __init__(self, parent, due_cases: list[Case], on_case_selected: Callable[[Case], None], on_refresh: Callable[[], None]):
        super().__init__(parent)
        self.due_cases = due_cases
        self.on_case_selected = on_case_selected
        self.on_refresh = on_refresh

        self.title("🔔 Fällige Wiedervorlagen & Deadlines")
        self.geometry("620x520")
        self.minsize(560, 440)

        from utils.ui_utils import center_window
        center_window(self, 620, 520)

        self.transient(parent)
        self.grab_set()

        self.create_widgets()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        header = ctk.CTkLabel(
            main_frame,
            text=f"🔔 Fällige Wiedervorlagen ({len(self.due_cases)})",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header.pack(anchor="w", pady=(0, 10))

        scroll = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, pady=(0, 10))

        if not self.due_cases:
            ctk.CTkLabel(scroll, text="Keine fälligen Wiedervorlagen aktuell vorhanden.", font=ctk.CTkFont(size=13)).pack(pady=20)
        else:
            for case in self.due_cases:
                card = ctk.CTkFrame(scroll, fg_color=("gray85", "gray20"), corner_radius=6)
                card.pack(fill="x", pady=5, padx=2)

                top_row = ctk.CTkFrame(card, fg_color="transparent")
                top_row.pack(fill="x", padx=10, pady=(6, 2))

                title_str = f"[{case.case_id}] {case.classification.title}"
                lbl_title = ctk.CTkLabel(top_row, text=title_str, font=ctk.CTkFont(size=13, weight="bold"), anchor="w")
                lbl_title.pack(side="left", fill="x", expand=True)

                btn_select = ctk.CTkButton(top_row, text="👁️ Öffnen", width=80, command=lambda c=case: self.select_case(c))
                btn_select.pack(side="right")

                info_str = f"Kunde: {case.customer.practice_name} | Fällig seit: {format_german_datetime(case.workflow_status.followup_at)}"
                ctk.CTkLabel(card, text=info_str, font=ctk.CTkFont(size=11), text_color="darkorange", anchor="w").pack(fill="x", padx=10, pady=(0, 4))

                if case.workflow_status.followup_note:
                    ctk.CTkLabel(card, text=f"Notiz: {case.workflow_status.followup_note}", font=ctk.CTkFont(size=11), text_color=("gray30", "gray70"), anchor="w").pack(fill="x", padx=10, pady=(0, 6))

                # Action buttons row
                act_row = ctk.CTkFrame(card, fg_color="transparent")
                act_row.pack(fill="x", padx=10, pady=(0, 6))

                ctk.CTkButton(act_row, text="+ 1 Tag verschieben", width=140, fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40"), command=lambda c=case: self.snooze_case(c, 1)).pack(side="left", padx=2)
                ctk.CTkButton(act_row, text="+ 1 Woche verschieben", width=150, fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40"), command=lambda c=case: self.snooze_case(c, 7)).pack(side="left", padx=2)
                ctk.CTkButton(act_row, text="✓ Erledigt", width=90, fg_color="forestgreen", command=lambda c=case: self.complete_followup(c)).pack(side="right", padx=2)

        btn_close = ctk.CTkButton(main_frame, text="Schließen", fg_color=("gray70", "gray40"), hover_color=("gray60", "gray50"), command=self.destroy, width=100)
        btn_close.pack(side="right")

    def select_case(self, case: Case):
        self.on_case_selected(case)
        self.destroy()

    def snooze_case(self, case: Case, days: int):
        new_dt = get_local_now() + timedelta(days=days)
        case.workflow_status.followup_at = format_german_date(new_dt) + " 09:00"
        self.on_refresh()
        self.destroy()

    def complete_followup(self, case: Case):
        case.workflow_status.followup_at = ""
        case.workflow_status.followup_note = ""
        self.on_refresh()
        self.destroy()
