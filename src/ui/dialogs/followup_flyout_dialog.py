import customtkinter as ctk
from datetime import datetime, timedelta
from typing import Callable
from models.case import Case
from utils.datetime_utils import format_german_datetime, parse_iso, get_local_now, format_german_date
from constants import DIALOG_DIMENSIONS, DIALOG_TITLES


class FollowupFlyoutDialog(ctk.CTkToplevel):
    """Flyout list showing all due followups & deadlines with quick actions (+1 Tag, +1 Woche)."""

    def __init__(self, parent, due_cases: list[Case], on_case_selected: Callable[[Case], None], on_refresh: Callable[[], None]):
        super().__init__(parent)
        self.due_cases = due_cases
        self.on_case_selected = on_case_selected
        self.on_refresh = on_refresh

        w, h = DIALOG_DIMENSIONS["followup_flyout"]
        self.title(DIALOG_TITLES["followup_flyout"])
        self.geometry(f"{w}x{h}")
        self.minsize(640, 480)

        from utils.ui_utils import center_window
        center_window(self, w, h)

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

                btn_select = ctk.CTkButton(top_row, text="👁 Öffnen", width=80, command=lambda c=case: self.select_case(c))
                btn_select.pack(side="right")

                info_str = f"Kunde: {case.customer.practice_name} | Fällig seit: {format_german_datetime(case.workflow_status.followup_at)}"
                ctk.CTkLabel(card, text=info_str, font=ctk.CTkFont(size=11), text_color="darkorange", anchor="w").pack(fill="x", padx=10, pady=(0, 4))

                if case.workflow_status.followup_note:
                    ctk.CTkLabel(card, text=f"Notiz: {case.workflow_status.followup_note}", font=ctk.CTkFont(size=11), text_color=("gray30", "gray70"), anchor="w").pack(fill="x", padx=10, pady=(0, 6))

                # Action buttons frame (2 clean compact rows)
                act_frame = ctk.CTkFrame(card, fg_color="transparent")
                act_frame.pack(fill="x", padx=10, pady=(0, 6))

                # Row 1: Short term shifts (+1h, +2h, Heute 16:30, Erledigt)
                act_row1 = ctk.CTkFrame(act_frame, fg_color="transparent")
                act_row1.pack(fill="x", pady=(0, 2))

                ctk.CTkButton(act_row1, text="+ 1 Std.", width=80, fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40"), command=lambda c=case: self.snooze_hours(c, 1)).pack(side="left", padx=2)
                ctk.CTkButton(act_row1, text="+ 2 Std.", width=80, fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40"), command=lambda c=case: self.snooze_hours(c, 2)).pack(side="left", padx=2)
                ctk.CTkButton(act_row1, text="Heute 16:30", width=110, fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40"), command=lambda c=case: self.set_preset_today_1630(c)).pack(side="left", padx=2)

                ctk.CTkButton(act_row1, text="✓ Erledigt", width=95, fg_color="forestgreen", command=lambda c=case: self.complete_followup(c)).pack(side="right", padx=2)

                # Row 2: Daily & Weekly shifts (Morgen 08:00, +1 Tag, +1 Woche)
                act_row2 = ctk.CTkFrame(act_frame, fg_color="transparent")
                act_row2.pack(fill="x", pady=(2, 0))

                ctk.CTkButton(act_row2, text="Morgen 08:00", width=120, fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40"), command=lambda c=case: self.set_preset_tomorrow_8am(c)).pack(side="left", padx=2)
                ctk.CTkButton(act_row2, text="+ 1 Tag", width=90, fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40"), command=lambda c=case: self.snooze_days(c, 1)).pack(side="left", padx=2)
                ctk.CTkButton(act_row2, text="+ 1 Woche", width=105, fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40"), command=lambda c=case: self.snooze_days(c, 7)).pack(side="left", padx=2)

        btn_close = ctk.CTkButton(main_frame, text="Schließen", fg_color=("gray70", "gray40"), hover_color=("gray60", "gray50"), command=self.safe_close, width=100)
        btn_close.pack(side="right")

    def select_case(self, case: Case):
        cb = self.on_case_selected
        try:
            self.grab_release()
        except Exception:
            pass
        if hasattr(self, "tk"):
            self.after(1, lambda: self._do_select_case(case, cb))
        else:
            self._do_select_case(case, cb)

    def _do_select_case(self, case: Case, cb: Callable[[Case], None] | None):
        try:
            self.destroy()
        except Exception:
            pass
        if cb:
            cb(case)

    def safe_close(self):
        try:
            self.grab_release()
        except Exception:
            pass
        if hasattr(self, "tk"):
            self.after(1, self._do_destroy)
        else:
            self._do_destroy()

    def _do_destroy(self):
        try:
            self.destroy()
        except Exception:
            pass

    def snooze_hours(self, case: Case, hours: int):
        new_dt = get_local_now() + timedelta(hours=hours)
        case.workflow_status.followup_at = format_german_datetime(new_dt)
        self.safe_close_and_refresh()

    def set_preset_today_1630(self, case: Case):
        now = get_local_now()
        case.workflow_status.followup_at = f"{format_german_date(now)} 16:30"
        self.safe_close_and_refresh()

    def set_preset_tomorrow_8am(self, case: Case):
        tmw = get_local_now() + timedelta(days=1)
        case.workflow_status.followup_at = f"{format_german_date(tmw)} 08:00"
        self.safe_close_and_refresh()

    def snooze_days(self, case: Case, days: int):
        new_dt = get_local_now() + timedelta(days=days)
        case.workflow_status.followup_at = f"{format_german_date(new_dt)} 09:00"
        self.safe_close_and_refresh()

    def safe_close_and_refresh(self):
        try:
            self.grab_release()
        except Exception:
            pass
        if hasattr(self, "tk"):
            self.after(1, self._do_close_and_refresh)
        else:
            self._do_close_and_refresh()

    def _do_close_and_refresh(self):
        try:
            self.destroy()
        except Exception:
            pass
        if self.on_refresh:
            self.on_refresh()

    def complete_followup(self, case: Case):
        case.workflow_status.followup_at = ""
        case.workflow_status.followup_note = ""
        self.safe_close_and_refresh()
