import calendar
from datetime import datetime, timedelta
from typing import Callable
import customtkinter as ctk
from utils.datetime_utils import format_german_date, format_german_datetime, parse_german_date, parse_iso, get_local_now


class CalendarDialog(ctk.CTkToplevel):
    """Interactive CustomTkinter calendar date picker dialog."""

    def __init__(
        self,
        parent,
        initial_date: str = "",
        include_time: bool = True,
        on_date_selected: Callable[[str], None] | None = None,
    ):
        super().__init__(parent)
        self.on_date_selected = on_date_selected
        self.include_time = include_time

        self.title("📅 Datum auswählen")
        self.geometry("380x440" if include_time else "380x380")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Parse initial date or default to now
        now = get_local_now()
        self.selected_dt = now
        if initial_date:
            try:
                if "." in initial_date:
                    parsed_iso = parse_german_date(initial_date)
                    self.selected_dt = parse_iso(parsed_iso)
                else:
                    self.selected_dt = parse_iso(initial_date)
            except Exception:
                self.selected_dt = now

        self.current_year = self.selected_dt.year
        self.current_month = self.selected_dt.month
        self.selected_day = self.selected_dt.day

        self.hour_var = ctk.StringVar(value=f"{self.selected_dt.hour:02d}")
        self.minute_var = ctk.StringVar(value=f"{self.selected_dt.minute:02d}")

        self.create_widgets()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Header Month/Year Navigation
        nav_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        nav_frame.pack(fill="x", pady=(0, 10))

        btn_prev = ctk.CTkButton(nav_frame, text="◀", width=36, command=self.prev_month, fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40"))
        btn_prev.pack(side="left")

        self.month_label = ctk.CTkLabel(
            nav_frame, text="", font=ctk.CTkFont(size=15, weight="bold")
        )
        self.month_label.pack(side="left", expand=True)

        btn_next = ctk.CTkButton(nav_frame, text="▶", width=36, command=self.next_month, fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40"))
        btn_next.pack(side="right")

        # Weekdays Header (Mo - So)
        weekdays_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        weekdays_frame.pack(fill="x", pady=(0, 5))
        weekdays = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
        for day in weekdays:
            lbl = ctk.CTkLabel(
                weekdays_frame,
                text=day,
                width=45,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="gray" if day in ("Sa", "So") else None,
            )
            lbl.pack(side="left", padx=1)

        # Days Grid Frame
        self.days_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        self.days_frame.pack(fill="both", expand=True)

        # Time Picker Row if enabled
        if self.include_time:
            time_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            time_frame.pack(fill="x", pady=(10, 5))

            ctk.CTkLabel(time_frame, text="Uhrzeit:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(5, 10))

            hours = [f"{h:02d}" for h in range(24)]
            self.hour_menu = ctk.CTkOptionMenu(
                time_frame, values=hours, variable=self.hour_var, width=70
            )
            self.hour_menu.pack(side="left", padx=2)

            ctk.CTkLabel(time_frame, text=":", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=2)

            minutes = [f"{m:02d}" for m in range(0, 60, 5)]
            if self.minute_var.get() not in minutes:
                minutes.append(self.minute_var.get())
                minutes.sort()
            self.min_menu = ctk.CTkOptionMenu(
                time_frame, values=minutes, variable=self.minute_var, width=70
            )
            self.min_menu.pack(side="left", padx=2)

        # Presets Rows
        presets_frame1 = ctk.CTkFrame(main_frame, fg_color="transparent")
        presets_frame1.pack(fill="x", pady=(2, 2))

        ctk.CTkButton(presets_frame1, text="Heute 11:30 (vor Mittag)", width=170, fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40"), command=self.set_today_before_lunch).pack(side="left", padx=2)
        ctk.CTkButton(presets_frame1, text="Heute 13:30 (nach Mittag)", width=170, fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40"), command=self.set_today_after_lunch).pack(side="left", padx=2)

        presets_frame2 = ctk.CTkFrame(main_frame, fg_color="transparent")
        presets_frame2.pack(fill="x", pady=(2, 8))

        ctk.CTkButton(presets_frame2, text="Morgen 08:00", width=110, fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40"), command=self.set_tomorrow_8am).pack(side="left", padx=2)
        ctk.CTkButton(presets_frame2, text="+ 1 Tag", width=110, fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40"), command=lambda: self.add_days(1)).pack(side="left", padx=2)
        ctk.CTkButton(presets_frame2, text="+ 1 Woche", width=110, fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40"), command=lambda: self.add_days(7)).pack(side="left", padx=2)

        # Bottom Actions
        action_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        action_frame.pack(fill="x", side="bottom")

        btn_cancel = ctk.CTkButton(action_frame, text="Abbrechen", fg_color=("gray70", "gray40"), hover_color=("gray60", "gray50"), command=self.destroy, width=100)
        btn_cancel.pack(side="left")

        btn_apply = ctk.CTkButton(action_frame, text="Übernehmen", fg_color="forestgreen", command=self.on_apply, width=140)
        btn_apply.pack(side="right")

        self.render_calendar()

    def render_calendar(self):
        for widget in self.days_frame.winfo_children():
            widget.destroy()

        month_names = [
            "", "Januar", "Februar", "März", "April", "Mai", "Juni",
            "Juli", "August", "September", "Oktober", "November", "Dezember"
        ]
        self.month_label.configure(text=f"{month_names[self.current_month]} {self.current_year}")

        cal = calendar.monthcalendar(self.current_year, self.current_month)

        today = get_local_now()

        for row_idx, week in enumerate(cal):
            row_frame = ctk.CTkFrame(self.days_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=1)

            for col_idx, day in enumerate(week):
                if day == 0:
                    lbl = ctk.CTkLabel(row_frame, text="", width=45)
                    lbl.pack(side="left", padx=1)
                else:
                    is_selected = (
                        day == self.selected_day
                        and self.current_month == self.selected_dt.month
                        and self.current_year == self.selected_dt.year
                    )
                    is_today = (
                        day == today.day
                        and self.current_month == today.month
                        and self.current_year == today.year
                    )

                    fg_col = "dodgerblue" if is_selected else ("gray25" if is_today else "transparent")
                    border_col = "gold" if is_today and not is_selected else None

                    btn = ctk.CTkButton(
                        row_frame,
                        text=str(day),
                        width=45,
                        height=28,
                        fg_color=fg_col,
                        hover_color="royalblue" if not is_selected else None,
                        border_width=1 if border_col else 0,
                        border_color=border_col,
                        command=lambda d=day: self.select_day(d),
                    )
                    btn.pack(side="left", padx=1)

    def select_day(self, day: int):
        self.selected_day = day
        self.selected_dt = datetime(
            self.current_year,
            self.current_month,
            day,
            int(self.hour_var.get()),
            int(self.minute_var.get()),
        )
        self.render_calendar()

    def prev_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.render_calendar()

    def next_month(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.render_calendar()

    def set_today(self):
        now = get_local_now()
        self.current_year = now.year
        self.current_month = now.month
        self.selected_day = now.day
        self.selected_dt = now
        self.hour_var.set(f"{now.hour:02d}")
        self.minute_var.set(f"{now.minute:02d}")
        self.render_calendar()

    def set_today_before_lunch(self):
        now = get_local_now()
        self.current_year = now.year
        self.current_month = now.month
        self.selected_day = now.day
        self.selected_dt = datetime(now.year, now.month, now.day, 11, 30)
        self.hour_var.set("11")
        self.minute_var.set("30")
        self.render_calendar()

    def set_today_after_lunch(self):
        now = get_local_now()
        self.current_year = now.year
        self.current_month = now.month
        self.selected_day = now.day
        self.selected_dt = datetime(now.year, now.month, now.day, 13, 30)
        self.hour_var.set("13")
        self.minute_var.set("30")
        self.render_calendar()

    def set_tomorrow_8am(self):
        tmw = get_local_now() + timedelta(days=1)
        self.current_year = tmw.year
        self.current_month = tmw.month
        self.selected_day = tmw.day
        self.selected_dt = datetime(tmw.year, tmw.month, tmw.day, 8, 0)
        self.hour_var.set("08")
        self.minute_var.set("00")
        self.render_calendar()

    def add_days(self, days: int):
        dt = self.selected_dt + timedelta(days=days)
        self.current_year = dt.year
        self.current_month = dt.month
        self.selected_day = dt.day
        self.selected_dt = dt
        self.render_calendar()

    def safe_destroy(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.after(1, self._do_destroy)

    def _do_destroy(self):
        try:
            self.destroy()
        except Exception:
            pass

    def on_apply(self):
        h = int(self.hour_var.get())
        m = int(self.minute_var.get())
        final_dt = datetime(self.current_year, self.current_month, self.selected_day, h, m)

        if self.include_time:
            result_str = format_german_datetime(final_dt)
        else:
            result_str = format_german_date(final_dt)

        if self.on_date_selected:
            self.on_date_selected(result_str)
        self.safe_destroy()


class DatePickerWidget(ctk.CTkFrame):
    """Reusable CustomTkinter input field with calendar picker button."""

    def __init__(
        self,
        parent,
        placeholder_text: str = "DD.MM.YYYY HH:MM",
        include_time: bool = True,
        initial_value: str = "",
        width: int = 240,
        **kwargs,
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.include_time = include_time

        self.entry = ctk.CTkEntry(self, placeholder_text=placeholder_text, width=width)
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        if initial_value:
            if "." in initial_value:
                self.entry.insert(0, initial_value)
            else:
                formatted = format_german_datetime(initial_value) if include_time else format_german_date(initial_value)
                self.entry.insert(0, formatted)

        self.cal_btn = ctk.CTkButton(
            self, text="📅 Kalender", width=95, command=self.open_calendar, fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40")
        )
        self.cal_btn.pack(side="right")

    def open_calendar(self):
        curr_val = self.get()
        CalendarDialog(
            self.winfo_toplevel(),
            initial_date=curr_val,
            include_time=self.include_time,
            on_date_selected=self.set_date,
        )

    def set_date(self, date_str: str):
        self.entry.delete(0, "end")
        self.entry.insert(0, date_str)

    def get(self) -> str:
        return self.entry.get().strip()

    def get_iso(self) -> str:
        val = self.get()
        return parse_german_date(val) if val else ""
