import customtkinter as ctk

from ui.dialogs.base_dialog import BaseDialog
from datetime import timedelta
from collections.abc import Callable
from models.case import Case
from ui.widgets.date_picker import DatePickerWidget
from utils.datetime_utils import format_german_datetime, parse_followup_datetime, get_local_now, format_german_date
from constants import DIALOG_DIMENSIONS, DIALOG_TITLES, COLOR_CARD_BG, COLOR_CARD_BORDER


class FollowupFlyoutDialog(BaseDialog):
    """Flyout list showing all due followups & deadlines with quick actions (+1 Tag, +1 Woche)."""

    def __init__(self, parent, due_cases: list[Case], on_case_selected: Callable[[Case], None], on_refresh: Callable[[], None]):
        super().__init__(parent)
        self.due_cases = due_cases
        self.on_case_selected = on_case_selected
        self.on_refresh = on_refresh

        w, h = DIALOG_DIMENSIONS["followup_flyout"]
        self.setup_window(
            parent,
            DIALOG_TITLES["followup_flyout"],
            (w, h),
            min_size=(640, 480),

            title_factory=lambda: DIALOG_TITLES["followup_flyout"],
        )

        self.create_widgets()

    def create_widgets(self):
        for child in self.winfo_children():
            try:
                child.destroy()
            except Exception:
                pass

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        from services.i18n_service import tr

        header = self.register_i18n(ctk.CTkLabel(
            main_frame,
            text=tr("followup.due_header", "🔔 Fällige Wiedervorlagen ({count})", count=len(self.due_cases)),
            font=ctk.CTkFont(size=16, weight="bold")
        ), "followup.due_header", "🔔 Fällige Wiedervorlagen ({count})", count=len(self.due_cases))
        header.pack(anchor="w", pady=(0, 10))

        self.scroll = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, pady=(0, 10))
        scroll = self.scroll

        if not self.due_cases:
            self.register_i18n(ctk.CTkLabel(scroll, text=tr("followup.no_due_cases", "Keine fälligen Wiedervorlagen aktuell vorhanden."), font=ctk.CTkFont(size=13)), "followup.no_due_cases", "Keine fälligen Wiedervorlagen aktuell vorhanden.").pack(pady=20)
        else:
            for case in self.due_cases:
                card = ctk.CTkFrame(scroll, fg_color=COLOR_CARD_BG, corner_radius=6, border_width=1, border_color=COLOR_CARD_BORDER)
                card.pack(fill="x", pady=5, padx=2)

                top_row = ctk.CTkFrame(card, fg_color="transparent")
                top_row.pack(fill="x", padx=10, pady=(6, 2))

                btn_select = self.register_i18n(ctk.CTkButton(top_row, text=tr("common.open", "👁 Öffnen"), width=80, command=lambda c=case: self.select_case(c)), "common.open", "👁 Öffnen")
                btn_select.pack(side="right", padx=(8, 0))

                title_str = f"[{case.case_id}] {case.classification.title}"
                disp_title = self._truncate_title_to_two_lines(title_str)
                lbl_title = ctk.CTkLabel(top_row, text=disp_title, font=ctk.CTkFont(size=13, weight="bold"), anchor="w", justify="left", wraplength=520)
                lbl_title.pack(side="left", fill="x", expand=True)

                info_str = tr("followup.due_card_info", "Kunde: {customer} | Fällig seit: {time}", customer=case.customer.practice_name, time=format_german_datetime(case.workflow_status.followup_at))
                ctk.CTkLabel(card, text=info_str, font=ctk.CTkFont(size=11), text_color="darkorange", anchor="w").pack(fill="x", padx=10, pady=(0, 4))

                if case.workflow_status.followup_note:
                    self.register_i18n(ctk.CTkLabel(card, text=tr("followup.note_prefix", "Notiz: {note}", note=case.workflow_status.followup_note), font=ctk.CTkFont(size=11), text_color=("gray30", "gray70"), anchor="w"), "followup.note_prefix", "Notiz: {note}", note=case.workflow_status.followup_note).pack(fill="x", padx=10, pady=(0, 6))

                # Action buttons frame (2 preset rows + the date/time field they act on)
                act_frame = ctk.CTkFrame(card, fg_color="transparent")
                act_frame.pack(fill="x", padx=10, pady=(0, 6))

                # The date/time field lives BELOW the preset rows (created here so the
                # preset button commands below can already close over it), matching the
                # layout of the general Wiedervorlage dialog.
                picker_row = ctk.CTkFrame(act_frame, fg_color="transparent")
                btn_apply = self.register_i18n(
                    ctk.CTkButton(
                        picker_row,
                        text=tr("ui_buttons.apply", "✓ Übernehmen"),
                        width=95,
                        fg_color="forestgreen",
                        hover_color="darkgreen",
                        state="disabled",
                        command=lambda c=case, p=None: None,
                    ),
                    "ui_buttons.apply",
                    "✓ Übernehmen",
                )
                btn_apply.pack(side="right")

                def make_on_change(btn=btn_apply):
                    def _on_change(val: str):
                        btn.configure(state="normal" if val.strip() else "disabled")
                    return _on_change

                picker = DatePickerWidget(picker_row, include_time=True, width=150, on_change=make_on_change(btn_apply))
                btn_apply.configure(command=lambda c=case, p=picker: self.apply_new_time(c, p))

                # Row 1: Short term shifts (+1h, +2h, Heute 16:30, Erledigt)
                act_row1 = ctk.CTkFrame(act_frame, fg_color="transparent")
                act_row1.pack(fill="x", pady=(0, 2))

                self.register_i18n(ctk.CTkButton(act_row1, text=tr("followup.preset_1h", "+ 1 Std."), width=80, fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40"), command=lambda p=picker: self.bump_hours(p, 1)), "followup.preset_1h", "+ 1 Std.").pack(side="left", padx=2)
                self.register_i18n(ctk.CTkButton(act_row1, text=tr("followup.preset_2h", "+ 2 Std."), width=80, fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40"), command=lambda p=picker: self.bump_hours(p, 2)), "followup.preset_2h", "+ 2 Std.").pack(side="left", padx=2)
                self.register_i18n(ctk.CTkButton(act_row1, text=tr("followup.preset_today_1630", "Heute 16:30"), width=110, fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40"), command=lambda p=picker: self.set_field_today_1630(p)), "followup.preset_today_1630", "Heute 16:30").pack(side="left", padx=2)

                self.register_i18n(ctk.CTkButton(act_row1, text=tr("cockpit.complete", "✓ Erledigt"), width=95, fg_color="forestgreen", command=lambda c=case: self.complete_followup(c)), "cockpit.complete", "✓ Erledigt").pack(side="right", padx=2)

                # Row 2: Daily & Weekly shifts (Morgen 08:00, +1 Tag, +1 Woche)
                act_row2 = ctk.CTkFrame(act_frame, fg_color="transparent")
                act_row2.pack(fill="x", pady=(2, 0))

                self.register_i18n(ctk.CTkButton(act_row2, text=tr("followup.preset_tomorrow_8am", "Morgen 08:00"), width=120, fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40"), command=lambda p=picker: self.set_field_tomorrow_8am(p)), "followup.preset_tomorrow_8am", "Morgen 08:00").pack(side="left", padx=2)
                self.register_i18n(ctk.CTkButton(act_row2, text=tr("followup.preset_1d", "+ 1 Tag"), width=90, fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40"), command=lambda p=picker: self.set_field_days(p, 1)), "followup.preset_1d", "+ 1 Tag").pack(side="left", padx=2)
                self.register_i18n(ctk.CTkButton(act_row2, text=tr("followup.preset_1w", "+ 1 Woche"), width=105, fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40"), command=lambda p=picker: self.set_field_days(p, 7)), "followup.preset_1w", "+ 1 Woche").pack(side="left", padx=2)

                # Row 3: the date/time field the presets above write into, plus the button
                # that actually commits it as the case's new follow-up time.
                picker_row.pack(fill="x", pady=(4, 0))
                self.register_i18n(ctk.CTkLabel(picker_row, text=tr("followup.new_time_lbl", "🕒 Neue Zeit:"), font=ctk.CTkFont(size=11, weight="bold")), "followup.new_time_lbl", "🕒 Neue Zeit:").pack(side="left", padx=(0, 6))
                picker.pack(side="left", fill="x", expand=True, padx=(0, 6))

        btn_close = self.register_i18n(ctk.CTkButton(main_frame, text=tr("common.close", "Schließen"), fg_color=("gray70", "gray40"), hover_color=("gray60", "gray50"), command=self.safe_close, width=100), "common.close", "Schließen")
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
            if hasattr(self, "master") and self.master:
                top = self.master.winfo_toplevel()
                if hasattr(top, "bring_to_foreground"):
                    # Same custom-app-root duck-typing as toast_notification.py.
                    top.bring_to_foreground()  # pyright: ignore[reportAttributeAccessIssue]
                elif top:
                    if top.state() == "iconic" or not top.winfo_viewable():
                        top.deiconify()
                    top.lift()
                    top.focus_force()
        except Exception:
            pass
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

    def _on_action_completed(self, case: Case):
        if case in self.due_cases:
            self.due_cases.remove(case)
        if self.on_refresh:
            self.on_refresh()
        if not self.due_cases:
            self.safe_close()
        else:
            self.create_widgets()

    def bump_hours(self, picker: DatePickerWidget, hours: int):
        # If the field already shows a date/time, add the increment on top of it (so
        # repeated clicks stack up); only fall back to "now" when the field is empty
        # or its content can't be parsed.
        base_dt = parse_followup_datetime(picker.get()) or get_local_now()
        picker.set_date(format_german_datetime(base_dt + timedelta(hours=hours)))

    def set_field_today_1630(self, picker: DatePickerWidget):
        now = get_local_now()
        picker.set_date(f"{format_german_date(now)} 16:30")

    def set_field_tomorrow_8am(self, picker: DatePickerWidget):
        tmw = get_local_now() + timedelta(days=1)
        picker.set_date(f"{format_german_date(tmw)} 08:00")

    def set_field_days(self, picker: DatePickerWidget, days: int):
        new_dt = get_local_now() + timedelta(days=days)
        picker.set_date(f"{format_german_date(new_dt)} 09:00")

    @staticmethod
    def _truncate_title_to_two_lines(text: str, line_length: int = 55) -> str:
        import textwrap
        lines = textwrap.wrap(text, width=line_length)
        if not lines:
            return ""
        if len(lines) <= 2:
            return "\n".join(lines)
        line2 = lines[1]
        if len(line2) > line_length - 3:
            line2 = line2[:line_length - 3] + "..."
        else:
            line2 = line2 + "..."
        return f"{lines[0]}\n{line2}"

    def apply_new_time(self, case: Case, picker: DatePickerWidget):
        from utils.datetime_utils import parse_flexible_followup_input
        raw_val = picker.get()
        if not raw_val:
            return
        dt = parse_flexible_followup_input(raw_val)
        if not dt:
            return
        case.workflow_status.followup_at = format_german_datetime(dt)
        self._on_action_completed(case)

    def complete_followup(self, case: Case):
        case.workflow_status.followup_at = ""
        case.workflow_status.followup_note = ""
        self._on_action_completed(case)
