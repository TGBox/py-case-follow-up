"""Checkout & Departure Companion Panel widget and floating window.

Provides an integrated, collapsible or undockable right-hand companion
with 6 dedicated tabs:
1. Tasks (daily recurring & dated checkout checklist)
2. ÖPNV (live departures for DING Ulm/Neu-Ulm & commute lead-time alarm)
3. Daily Note (free-text scratchpad with badge indicator & midnight reset)
4. Tomorrow (preview of upcoming follow-ups and deadlines)
5. Work Time (working time tracking & end-of-day projection)
6. Weather (commute weather & umbrella recommendation)
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from datetime import date, datetime, timedelta
from typing import Any

import customtkinter as ctk

from constants import (
    BORDER_WIDTH_CARD,
    BTN_HEIGHT_CHECKOUT_ACTION,
    BTN_HEIGHT_CHECKOUT_TINY,
    BTN_WIDTH_ACTION_SM,
    BTN_WIDTH_CHECKOUT_ACTION,
    BTN_WIDTH_CHECKOUT_TINY,
    CHECKOUT_FLOATING_MIN_HEIGHT,
    CHECKOUT_FLOATING_MIN_WIDTH,
    CHECKOUT_HEADER_BTN_SIZE,
    COLOR_CANCEL_FG,
    COLOR_CANCEL_HOVER,
    COLOR_CARD_BG,
    COLOR_CHECKOUT_BORDER,
    COLOR_CHECKOUT_CARD_BG,
    COLOR_MUTED_LABEL,
    COLOR_SUCCESS,
    COLOR_SUCCESS_HOVER,
    COLOR_THEME_BTN,
    COLOR_TRANSIT_COUNTDOWN_OK,
    COLOR_TRANSIT_COUNTDOWN_URGENT,
    COLOR_TRANSIT_COUNTDOWN_WARN,
    COLOR_TRANSIT_DELAY,
    COLOR_TRANSIT_ONTIME,
    COLOR_TRANSPARENT,
    CORNER_RADIUS_CARD,
    CORNER_RADIUS_MD,
    CORNER_RADIUS_SM,
    FONT_SIZE_BODY,
    FONT_SIZE_H2,
    FONT_SIZE_SM,
    FONT_WEIGHT_BOLD,
    ICON_DELETE_X,
    ICON_KEY_CHECKOUT,
    ICON_KEY_DOCK,
    ICON_KEY_UNDOCK,
    ICON_SIZE_ACTION,
    LABEL_WIDTH_TRANSIT_LINE,
    PAD_MD,
    PAD_SM,
    PAD_XS,
    TRANSIT_REFRESH_INTERVAL_MS,
)
from models.case import Case
from models.profile import UserProfile
from services.checkout_task_service import CheckoutTaskService
from services.ding_transit_service import DingTransitService, TransitDeparture
from services.i18n_service import tr
from services.weather_service import WeatherInfo, WeatherService
from utils.icon_utils import get_icon

logger = logging.getLogger(__name__)


class CheckoutFloatingWindow(ctk.CTkToplevel):
    """Floating tool window for the Checkout panel on multi-monitor setups.

    Marked as transient(master) and -topmost, so it does not clutter the Windows
    taskbar while staying pinned on top across screens.
    """

    def __init__(
        self,
        master: Any,
        on_dock_callback: Callable[[], None],
        on_close_callback: Callable[[], None],
    ) -> None:
        super().__init__(master)
        self.transient(master)
        self.attributes("-topmost", True)
        self.resizable(True, True)
        self.title(tr("checkout_panel.title", "Feierabend- & Checkout-Begleiter"))

        self.minsize(CHECKOUT_FLOATING_MIN_WIDTH, CHECKOUT_FLOATING_MIN_HEIGHT)
        self.protocol("WM_DELETE_WINDOW", on_close_callback)
        self.on_dock_callback = on_dock_callback
        self.on_close_callback = on_close_callback


class CheckoutPanelWidget(ctk.CTkFrame):
    """Main Checkout & Departure Companion panel."""

    def __init__(
        self,
        master: Any,
        profile: UserProfile,
        on_dock_toggle: Callable[[], None],
        on_close: Callable[[], None],
        cases_provider: Callable[[], list[Case]] | None = None,
        on_persist_callback: Callable[[], None] | None = None,
        is_floating: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            master,
            corner_radius=CORNER_RADIUS_CARD,
            border_width=BORDER_WIDTH_CARD,
            border_color=COLOR_CHECKOUT_BORDER,
            **kwargs,
        )
        self.profile = profile
        self.settings = profile.checkout_settings
        self.on_dock_toggle = on_dock_toggle
        self.on_close = on_close
        self.cases_provider = cases_provider or (lambda: [])
        self.on_persist_callback = on_persist_callback
        self.is_floating = is_floating

        self._transit_departures: list[TransitDeparture] = []
        self._weather_info: WeatherInfo | None = None
        self._is_fetching_transit = False
        self._note_debounce_timer: Any = None
        self._transit_refresh_job: Any = None

        # Perform midnight reset check
        if CheckoutTaskService.check_and_perform_midnight_reset(self.settings):
            self._persist_settings()

        self._build_header()
        self._build_tabs()

        # Initial background fetches
        self.refresh_transit_data(force=True)
        self.refresh_weather_data(force=False)
        self._schedule_next_transit_refresh()

    def _persist_settings(self) -> None:
        if self.on_persist_callback:
            try:
                self.on_persist_callback()
            except Exception as e:
                logger.warning("Failed to persist checkout settings: %s", e)

    def set_floating_state(self, is_floating: bool) -> None:
        """Update undock/dock button visual icon and tooltip."""
        self.is_floating = is_floating
        icon_key = ICON_KEY_DOCK if is_floating else ICON_KEY_UNDOCK
        tooltip_text = (
            tr("checkout_panel.btn_dock", "Wieder andocken")
            if is_floating
            else tr("checkout_panel.btn_undock", "Entkoppeln")
        )
        self.dock_btn.configure(image=get_icon(icon_key, size=ICON_SIZE_ACTION))
        from ui.widgets.ctk_tooltip import CTkTooltip

        if hasattr(self, "_dock_tooltip"):
            self._dock_tooltip.set_text(tooltip_text)
        else:
            self._dock_tooltip = CTkTooltip(self.dock_btn, tooltip_text)

    # -------------------------------------------------------------------------
    # Header UI
    # -------------------------------------------------------------------------
    def _build_header(self) -> None:
        self.header_frame = ctk.CTkFrame(self, fg_color=COLOR_TRANSPARENT)
        self.header_frame.pack(fill="x", padx=PAD_SM, pady=(PAD_SM, PAD_XS))

        # Title with checkout icon
        title_box = ctk.CTkFrame(self.header_frame, fg_color=COLOR_TRANSPARENT)
        title_box.pack(side="left", fill="x", expand=True)

        self.title_icon_lbl = ctk.CTkLabel(
            title_box,
            text="",
            image=get_icon(ICON_KEY_CHECKOUT, size=ICON_SIZE_ACTION),
        )
        self.title_icon_lbl.pack(side="left", padx=(PAD_XS, PAD_XS))

        self.title_lbl = ctk.CTkLabel(
            title_box,
            text=tr("checkout_panel.title", "Feierabend- & Checkout-Begleiter"),
            font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
            anchor="w",
        )
        self.title_lbl.pack(side="left", fill="x", expand=True)

        # Right control buttons
        btn_box = ctk.CTkFrame(self.header_frame, fg_color=COLOR_TRANSPARENT)
        btn_box.pack(side="right")

        # Dock / Undock button
        dock_icon_key = ICON_KEY_DOCK if self.is_floating else ICON_KEY_UNDOCK
        self.dock_btn = ctk.CTkButton(
            btn_box,
            text="",
            image=get_icon(dock_icon_key, size=ICON_SIZE_ACTION),
            command=self.on_dock_toggle,
            width=CHECKOUT_HEADER_BTN_SIZE,
            height=CHECKOUT_HEADER_BTN_SIZE,
            fg_color=COLOR_THEME_BTN,
        )
        self.dock_btn.pack(side="left", padx=PAD_XS)
        from ui.widgets.ctk_tooltip import CTkTooltip

        dock_tooltip_text = (
            tr("checkout_panel.btn_dock", "Wieder andocken")
            if self.is_floating
            else tr("checkout_panel.btn_undock", "Entkoppeln")
        )
        self._dock_tooltip = CTkTooltip(self.dock_btn, dock_tooltip_text)

        # Close button
        self.close_btn = ctk.CTkButton(
            btn_box,
            text=ICON_DELETE_X,
            command=self.on_close,
            width=CHECKOUT_HEADER_BTN_SIZE,
            height=CHECKOUT_HEADER_BTN_SIZE,
            fg_color=COLOR_CANCEL_FG,
            hover_color=COLOR_CANCEL_HOVER,
        )
        self.close_btn.pack(side="left", padx=PAD_XS)

    # -------------------------------------------------------------------------
    # Tabs Setup
    # -------------------------------------------------------------------------
    def _build_tabs(self) -> None:
        self.tabview = ctk.CTkTabview(self, corner_radius=CORNER_RADIUS_MD)
        self.tabview.pack(fill="both", expand=True, padx=PAD_XS, pady=PAD_XS)

        # Define 6 tabs
        self.tab_name_tasks = tr("checkout_panel.tab_tasks", "Tasks")
        self.tab_name_transit = tr("checkout_panel.tab_transit", "ÖPNV")
        self.tab_name_note = (
            tr("checkout_panel.tab_note_badged", "Tagesnotiz ●")
            if self.settings.daily_note_text.strip()
            else tr("checkout_panel.tab_note", "Tagesnotiz")
        )
        self.tab_name_tomorrow = tr("checkout_panel.tab_tomorrow", "Morgen")
        self.tab_name_worktime = tr("checkout_panel.tab_worktime", "Arbeitszeit")
        self.tab_name_weather = tr("checkout_panel.tab_weather", "Wetter")

        self.tab_tasks = self.tabview.add(self.tab_name_tasks)
        self.tab_transit = self.tabview.add(self.tab_name_transit)
        self.tab_note = self.tabview.add(self.tab_name_note)
        self.tab_tomorrow = self.tabview.add(self.tab_name_tomorrow)
        self.tab_worktime = self.tabview.add(self.tab_name_worktime)
        self.tab_weather = self.tabview.add(self.tab_name_weather)

        self._setup_tasks_tab()
        self._setup_transit_tab()
        self._setup_note_tab()
        self._setup_tomorrow_tab()
        self._setup_worktime_tab()
        self._setup_weather_tab()

    # -------------------------------------------------------------------------
    # TAB 1: Tasks (Checklist)
    # -------------------------------------------------------------------------
    def _setup_tasks_tab(self) -> None:
        tab = self.tab_tasks

        # Scrollable container
        self.tasks_scroll = ctk.CTkScrollableFrame(tab, fg_color=COLOR_TRANSPARENT)
        self.tasks_scroll.pack(fill="both", expand=True, padx=PAD_XS, pady=PAD_XS)

        # Add task input row at the bottom
        add_box = ctk.CTkFrame(tab, fg_color=COLOR_TRANSPARENT)
        add_box.pack(fill="x", padx=PAD_XS, pady=PAD_XS)

        self.new_task_entry = ctk.CTkEntry(
            add_box,
            placeholder_text=tr("checkout_panel.tasks_add_placeholder", "Neue Aufgabe eingeben..."),
            font=ctk.CTkFont(size=FONT_SIZE_SM),
        )
        self.new_task_entry.pack(side="left", fill="x", expand=True, padx=(0, PAD_XS))
        self.new_task_entry.bind("<Return>", lambda e: self._on_add_task())

        self.new_task_btn = ctk.CTkButton(
            add_box,
            text=tr("checkout_panel.tasks_btn_add", "Hinzufügen"),
            command=self._on_add_task,
            width=BTN_WIDTH_ACTION_SM,
            fg_color=COLOR_SUCCESS,
            hover_color=COLOR_SUCCESS_HOVER,
        )
        self.new_task_btn.pack(side="right")

        self.render_tasks()

    def render_tasks(self) -> None:
        """Render recurring and dated tasks into the scrollable view."""
        for widget in self.tasks_scroll.winfo_children():
            widget.destroy()

        today_str = date.today().isoformat()
        recs, dated = CheckoutTaskService.get_tasks_for_date(self.settings, today_str)

        # 1. Recurring section
        rec_hdr = ctk.CTkLabel(
            self.tasks_scroll,
            text=tr("checkout_panel.tasks_section_recurring", "Tägliche Routine vor Dienstende"),
            font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD),
            anchor="w",
        )
        rec_hdr.pack(fill="x", padx=PAD_XS, pady=(PAD_XS, PAD_XS))

        for task in recs:
            self._render_task_item(task, is_recurring=True)

        # 2. Dated tasks section
        dated_hdr = ctk.CTkLabel(
            self.tasks_scroll,
            text=tr("checkout_panel.tasks_section_dated", "Termingebundene Aufgaben für heute"),
            font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD),
            anchor="w",
        )
        dated_hdr.pack(fill="x", padx=PAD_XS, pady=(PAD_MD, PAD_XS))

        if not dated:
            empty_lbl = ctk.CTkLabel(
                self.tasks_scroll,
                text=tr("checkout_panel.tasks_empty", "Keine Aufgaben für heute eingetragen."),
                font=ctk.CTkFont(size=FONT_SIZE_SM),
                text_color=COLOR_MUTED_LABEL,
                anchor="w",
            )
            empty_lbl.pack(fill="x", padx=PAD_SM, pady=PAD_XS)
        else:
            for task in dated:
                self._render_task_item(task, is_recurring=False)

    def _render_task_item(self, task: dict[str, Any], is_recurring: bool) -> None:
        row = ctk.CTkFrame(self.tasks_scroll, fg_color=COLOR_CHECKOUT_CARD_BG, corner_radius=CORNER_RADIUS_SM)
        row.pack(fill="x", padx=PAD_XS, pady=PAD_XS)

        var = ctk.BooleanVar(value=bool(task.get("done", False)))

        def on_toggle():
            CheckoutTaskService.toggle_task(self.settings, task["id"])
            self._persist_settings()

        cb = ctk.CTkCheckBox(
            row,
            text=task.get("text", ""),
            variable=var,
            command=on_toggle,
            font=ctk.CTkFont(size=FONT_SIZE_SM),
        )
        cb.pack(side="left", fill="x", expand=True, padx=PAD_SM, pady=PAD_SM)

        # Delete button for dated tasks
        del_btn = ctk.CTkButton(
            row,
            text=ICON_DELETE_X,
            command=lambda tid=task["id"]: self._on_delete_task(tid),
            width=BTN_WIDTH_CHECKOUT_TINY,
            height=BTN_HEIGHT_CHECKOUT_TINY,
            fg_color=COLOR_TRANSPARENT,
            text_color=COLOR_MUTED_LABEL,
            hover_color=COLOR_CANCEL_HOVER,
        )
        del_btn.pack(side="right", padx=PAD_XS)

    def _on_add_task(self) -> None:
        text = self.new_task_entry.get().strip()
        if not text:
            return
        CheckoutTaskService.add_dated_task(self.settings, text, date.today().isoformat())
        self.new_task_entry.delete(0, "end")
        self._persist_settings()
        self.render_tasks()

    def _on_delete_task(self, task_id: str) -> None:
        CheckoutTaskService.delete_task(self.settings, task_id)
        self._persist_settings()
        self.render_tasks()

    # -------------------------------------------------------------------------
    # TAB 2: ÖPNV (Live DING Ulm/Neu-Ulm)
    # -------------------------------------------------------------------------
    def _setup_transit_tab(self) -> None:
        tab = self.tab_transit

        # Top info & commute summary card
        self.transit_card = ctk.CTkFrame(tab, fg_color=COLOR_CARD_BG, corner_radius=CORNER_RADIUS_MD)
        self.transit_card.pack(fill="x", padx=PAD_XS, pady=PAD_XS)

        stop_name = self.settings.stops[0].get("name", "Ulm Ehinger Tor") if self.settings.stops else "Ulm Ehinger Tor"
        self.transit_stop_lbl = ctk.CTkLabel(
            self.transit_card,
            text=f"🚏 {stop_name}",
            font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
            anchor="w",
        )
        self.transit_stop_lbl.pack(fill="x", padx=PAD_SM, pady=(PAD_SM, 0))

        # Commute calculation text
        lead_time = (
            self.settings.walk_time_minutes
            + self.settings.logout_time_minutes
            + self.settings.pack_time_minutes
            + self.settings.buffer_time_minutes
        )
        self.transit_lead_lbl = ctk.CTkLabel(
            self.transit_card,
            text=tr("checkout_panel.transit_total_lead", "Benötigter Vorlauf: {minutes} Min.").format(minutes=lead_time),
            font=ctk.CTkFont(size=FONT_SIZE_SM),
            text_color=COLOR_MUTED_LABEL,
            anchor="w",
        )
        self.transit_lead_lbl.pack(fill="x", padx=PAD_SM, pady=(0, PAD_SM))

        # Refresh row
        refresh_row = ctk.CTkFrame(tab, fg_color=COLOR_TRANSPARENT)
        refresh_row.pack(fill="x", padx=PAD_XS, pady=PAD_XS)

        self.transit_status_lbl = ctk.CTkLabel(
            refresh_row,
            text="",
            font=ctk.CTkFont(size=FONT_SIZE_SM),
            anchor="w",
        )
        self.transit_status_lbl.pack(side="left", fill="x", expand=True)

        self.transit_refresh_btn = ctk.CTkButton(
            refresh_row,
            text="🔄",
            command=lambda: self.refresh_transit_data(force=True),
            width=BTN_WIDTH_CHECKOUT_ACTION,
            height=BTN_HEIGHT_CHECKOUT_ACTION,
            fg_color=COLOR_THEME_BTN,
        )
        self.transit_refresh_btn.pack(side="right")

        # Scrollable departures table
        self.transit_scroll = ctk.CTkScrollableFrame(tab, fg_color=COLOR_TRANSPARENT)
        self.transit_scroll.pack(fill="both", expand=True, padx=PAD_XS, pady=PAD_XS)

    def refresh_transit_data(self, force: bool = False) -> None:
        """Fetch departures in a background thread and update UI."""
        if self._is_fetching_transit:
            return
        self._is_fetching_transit = True
        self.transit_status_lbl.configure(text=tr("checkout_panel.transit_refreshing", "Aktualisiere Abfahrten..."))

        stop = self.settings.stops[0] if self.settings.stops else {"name": "Ulm Ehinger Tor", "place": "Ulm"}
        stop_name = stop.get("name", "Ulm Ehinger Tor")
        stop_place = stop.get("place", "Ulm")

        def worker():
            deps = DingTransitService.fetch_departures(stop_name, stop_place, force_refresh=force)
            if self.winfo_exists():
                self.after(0, lambda: self._on_transit_data_loaded(deps))

        threading.Thread(target=worker, daemon=True).start()

    def _on_transit_data_loaded(self, deps: list[TransitDeparture]) -> None:
        self._is_fetching_transit = False
        self._transit_departures = deps
        now_str = datetime.now().strftime("%H:%M")
        self.transit_status_lbl.configure(text=f"Stand: {now_str} Uhr")
        self._render_departures()
        self._check_commute_alarms()

    def _render_departures(self) -> None:
        for widget in self.transit_scroll.winfo_children():
            widget.destroy()

        if not self._transit_departures:
            no_dep_lbl = ctk.CTkLabel(
                self.transit_scroll,
                text=tr("checkout_panel.transit_no_departures", "Aktuell keine Abfahrten gefunden."),
                font=ctk.CTkFont(size=FONT_SIZE_SM),
                text_color=COLOR_MUTED_LABEL,
            )
            no_dep_lbl.pack(pady=PAD_MD)
            return

        for dep in self._transit_departures[:12]:
            row = ctk.CTkFrame(self.transit_scroll, fg_color=COLOR_CHECKOUT_CARD_BG, corner_radius=CORNER_RADIUS_SM)
            row.pack(fill="x", padx=PAD_XS, pady=PAD_XS)

            # Line badge
            badge = ctk.CTkLabel(
                row,
                text=f" {dep.line} ",
                font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD),
                fg_color=COLOR_THEME_BTN,
                corner_radius=CORNER_RADIUS_SM,
                width=LABEL_WIDTH_TRANSIT_LINE,
            )
            badge.pack(side="left", padx=(PAD_SM, PAD_XS), pady=PAD_SM)

            # Destination & Platform
            info_box = ctk.CTkFrame(row, fg_color=COLOR_TRANSPARENT)
            info_box.pack(side="left", fill="x", expand=True, padx=PAD_XS)

            dest_lbl = ctk.CTkLabel(
                info_box,
                text=dep.destination,
                font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD),
                anchor="w",
            )
            dest_lbl.pack(fill="x")

            plat_str = f"{dep.platform}" if dep.platform else ""
            if dep.delay_minutes > 0:
                time_str = f"{dep.real_time_str} (+{dep.delay_minutes} Min.) {plat_str}".strip()
                time_color = COLOR_TRANSIT_DELAY
            else:
                time_str = f"{dep.real_time_str} ({tr('checkout_panel.transit_status_ontime', 'Pünktlich')}) {plat_str}".strip()
                time_color = COLOR_TRANSIT_ONTIME

            sub_lbl = ctk.CTkLabel(
                info_box,
                text=time_str,
                font=ctk.CTkFont(size=FONT_SIZE_SM),
                text_color=time_color,
                anchor="w",
            )
            sub_lbl.pack(fill="x")

            # Countdown badge
            cd_color = (
                COLOR_TRANSIT_COUNTDOWN_URGENT
                if dep.countdown_minutes <= 3
                else COLOR_TRANSIT_COUNTDOWN_WARN
                if dep.countdown_minutes <= 10
                else COLOR_TRANSIT_COUNTDOWN_OK
            )
            cd_lbl = ctk.CTkLabel(
                row,
                text=f"{dep.countdown_minutes} Min.",
                font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD),
                text_color=cd_color,
            )
            cd_lbl.pack(side="right", padx=(PAD_XS, PAD_SM))

    def _check_commute_alarms(self) -> None:
        """Check if any departure has reached leave time and trigger toast alarm."""
        if not self.settings.alarm_enabled or not self._transit_departures:
            return

        for dep in self._transit_departures:
            info = DingTransitService.calculate_leave_info(
                dep,
                walk_min=self.settings.walk_time_minutes,
                logout_min=self.settings.logout_time_minutes,
                pack_min=self.settings.pack_time_minutes,
                buffer_min=self.settings.buffer_time_minutes,
            )
            if info.get("is_alarm_due"):
                from ui.widgets.toast_notification import ToastNotification

                title = tr("checkout_panel.transit_alarm_toast_title", "Zeit zum Aufbruch!")
                msg = tr(
                    "checkout_panel.transit_alarm_toast_msg",
                    "Bus/Bahn fährt um {dep_time} Uhr ({line} nach {dest}).",
                ).format(
                    dep_time=dep.real_time_str,
                    line=dep.line,
                    dest=dep.destination,
                )
                ToastNotification(self.winfo_toplevel(), title=title, message=msg)
                break

    def _schedule_next_transit_refresh(self) -> None:
        if self._transit_refresh_job is not None:
            try:
                self.after_cancel(self._transit_refresh_job)
            except Exception:
                pass
        self._transit_refresh_job = self.after(TRANSIT_REFRESH_INTERVAL_MS, self._periodic_transit_refresh)

    def _periodic_transit_refresh(self) -> None:
        self.refresh_transit_data(force=False)
        self._schedule_next_transit_refresh()

    # -------------------------------------------------------------------------
    # TAB 3: Daily Note (with dynamic badge)
    # -------------------------------------------------------------------------
    def _setup_note_tab(self) -> None:
        tab = self.tab_note

        self.note_textbox = ctk.CTkTextbox(tab, font=ctk.CTkFont(size=FONT_SIZE_BODY))
        self.note_textbox.pack(fill="both", expand=True, padx=PAD_XS, pady=(PAD_XS, PAD_SM))
        self.note_textbox.insert("1.0", self.settings.daily_note_text)
        self.note_textbox.bind("<KeyRelease>", self._on_note_key_release)

        # Bottom row with Keep-overnight checkbox
        bottom_box = ctk.CTkFrame(tab, fg_color=COLOR_TRANSPARENT)
        bottom_box.pack(fill="x", padx=PAD_XS, pady=PAD_XS)

        self.keep_overnight_var = ctk.BooleanVar(value=self.settings.daily_note_keep_overnight)

        def on_toggle_keep():
            self.settings.daily_note_keep_overnight = self.keep_overnight_var.get()
            self._persist_settings()

        self.keep_overnight_cb = ctk.CTkCheckBox(
            bottom_box,
            text=tr("checkout_panel.note_keep_overnight", "Über Nacht behalten (nicht um 00:00 Uhr löschen)"),
            variable=self.keep_overnight_var,
            command=on_toggle_keep,
            font=ctk.CTkFont(size=FONT_SIZE_SM),
        )
        self.keep_overnight_cb.pack(side="left", fill="x", expand=True)

    def _on_note_key_release(self, event: Any = None) -> None:
        text = self.note_textbox.get("1.0", "end-1c")
        self.settings.daily_note_text = text
        self._update_note_tab_badge(bool(text.strip()))

        # Debounced persist
        if self._note_debounce_timer is not None:
            self.after_cancel(self._note_debounce_timer)
        self._note_debounce_timer = self.after(500, self._persist_settings)

    def _update_note_tab_badge(self, has_content: bool) -> None:
        """Update note tab button title to show or hide the green/dot indicator."""
        title = (
            tr("checkout_panel.tab_note_badged", "Tagesnotiz ●")
            if has_content
            else tr("checkout_panel.tab_note", "Tagesnotiz")
        )
        # CTkTabview internal segmented button rename
        try:
            if hasattr(self.tabview, "_segmented_button"):
                btns = getattr(self.tabview._segmented_button, "_buttons_dict", {})
                for key, btn in btns.items():
                    if key == self.tab_name_note or "Tagesnotiz" in key:
                        btn.configure(text=title)
        except Exception as e:
            logger.debug("Could not rename note tab button: %s", e)

    # -------------------------------------------------------------------------
    # TAB 4: Tomorrow (Follow-ups & preview)
    # -------------------------------------------------------------------------
    def _setup_tomorrow_tab(self) -> None:
        tab = self.tab_tomorrow
        self.tomorrow_scroll = ctk.CTkScrollableFrame(tab, fg_color=COLOR_TRANSPARENT)
        self.tomorrow_scroll.pack(fill="both", expand=True, padx=PAD_XS, pady=PAD_XS)
        self.render_tomorrow_preview()

    def render_tomorrow_preview(self) -> None:
        for widget in self.tomorrow_scroll.winfo_children():
            widget.destroy()

        tomorrow = date.today() + timedelta(days=1)
        tomorrow_str = tomorrow.isoformat()

        hdr = ctk.CTkLabel(
            self.tomorrow_scroll,
            text=f"📅 {tr('checkout_panel.tomorrow_followups', 'Fällige Wiedervorlagen')} ({tomorrow.strftime('%d.%m.%Y')})",
            font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD),
            anchor="w",
        )
        hdr.pack(fill="x", padx=PAD_XS, pady=(PAD_XS, PAD_SM))

        all_cases = self.cases_provider()
        tomorrow_cases = [
            c
            for c in all_cases
            if (
                c.workflow_status.followup_at
                and c.workflow_status.followup_at.startswith(tomorrow_str)
            )
            or (
                c.classification.deadline_callback
                and c.classification.deadline_callback.startswith(tomorrow_str)
            )
        ]

        if not tomorrow_cases:
            empty_lbl = ctk.CTkLabel(
                self.tomorrow_scroll,
                text=tr("checkout_panel.tomorrow_no_followups", "Keine Wiedervorlagen für morgen eingetragen."),
                font=ctk.CTkFont(size=FONT_SIZE_SM),
                text_color=COLOR_MUTED_LABEL,
                anchor="w",
            )
            empty_lbl.pack(fill="x", padx=PAD_SM, pady=PAD_XS)
        else:
            for case in tomorrow_cases:
                card = ctk.CTkFrame(
                    self.tomorrow_scroll, fg_color=COLOR_CHECKOUT_CARD_BG, corner_radius=CORNER_RADIUS_SM
                )
                card.pack(fill="x", padx=PAD_XS, pady=PAD_XS)

                cust_name = (
                    case.customer.practice_name
                    or case.customer.contact_person
                    or "Unbekannt"
                )
                c_lbl = ctk.CTkLabel(
                    card,
                    text=f"#{case.case_id} - {cust_name}",
                    font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD),
                    anchor="w",
                )
                c_lbl.pack(fill="x", padx=PAD_SM, pady=(PAD_XS, 0))

                desc_text = (
                    case.classification.title
                    or case.workflow_status.followup_note
                    or ""
                )
                desc_lbl = ctk.CTkLabel(
                    card,
                    text=f"Prio: {case.classification.urgency_level} | {desc_text[:60]}",
                    font=ctk.CTkFont(size=FONT_SIZE_SM),
                    text_color=COLOR_MUTED_LABEL,
                    anchor="w",
                )
                desc_lbl.pack(fill="x", padx=PAD_SM, pady=(0, PAD_XS))

    # -------------------------------------------------------------------------
    # TAB 5: Work Time (Working hours & forecast)
    # -------------------------------------------------------------------------
    def _setup_worktime_tab(self) -> None:
        tab = self.tab_worktime
        card = ctk.CTkFrame(tab, fg_color=COLOR_CARD_BG, corner_radius=CORNER_RADIUS_MD)
        card.pack(fill="x", padx=PAD_XS, pady=PAD_XS)

        now = datetime.now()
        start_parts = self.settings.work_start_time.split(":")
        try:
            start_dt = now.replace(
                hour=int(start_parts[0]), minute=int(start_parts[1]), second=0, microsecond=0
            )
        except Exception:
            start_dt = now.replace(hour=8, minute=0, second=0, microsecond=0)

        # Net working time elapsed
        elapsed_minutes = max(0, int((now - start_dt).total_seconds() / 60) - self.settings.work_break_minutes)
        elapsed_hours = elapsed_minutes // 60
        elapsed_mins_rem = elapsed_minutes % 60

        # Projected end of day = start + target_hours + break_minutes
        target_minutes = int(self.settings.work_target_hours * 60) + self.settings.work_break_minutes
        projected_end = start_dt + timedelta(minutes=target_minutes)

        time_box = ctk.CTkLabel(
            card,
            text=tr(
                "checkout_panel.worktime_current_net",
                "Heutige Netto-Arbeitszeit: {hours} Std. {minutes} Min.",
            ).format(hours=elapsed_hours, minutes=elapsed_mins_rem),
            font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
            anchor="w",
        )
        time_box.pack(fill="x", padx=PAD_SM, pady=(PAD_SM, PAD_XS))

        end_box = ctk.CTkLabel(
            card,
            text=tr(
                "checkout_panel.worktime_projected_end",
                "Voraussichtlicher Feierabend: {time} Uhr",
            ).format(time=projected_end.strftime("%H:%M")),
            font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
            text_color=COLOR_SUCCESS,
            anchor="w",
        )
        end_box.pack(fill="x", padx=PAD_SM, pady=(0, PAD_SM))

        # Warning if over 10h
        if elapsed_minutes >= 600:
            warn_lbl = ctk.CTkLabel(
                card,
                text=tr(
                    "checkout_panel.worktime_max_warn",
                    "Achtung: Gesetzliche Höchstarbeitszeit von 10 Stunden naht!",
                ),
                font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD),
                text_color=COLOR_CANCEL_FG,
                anchor="w",
            )
            warn_lbl.pack(fill="x", padx=PAD_SM, pady=(0, PAD_SM))

    # -------------------------------------------------------------------------
    # TAB 6: Weather
    # -------------------------------------------------------------------------
    def _setup_weather_tab(self) -> None:
        tab = self.tab_weather
        self.weather_card = ctk.CTkFrame(tab, fg_color=COLOR_CARD_BG, corner_radius=CORNER_RADIUS_MD)
        self.weather_card.pack(fill="x", padx=PAD_XS, pady=PAD_XS)

        city = self.settings.weather_city or "Ulm"
        self.weather_city_lbl = ctk.CTkLabel(
            self.weather_card,
            text=tr("checkout_panel.weather_title", "Wetter für den Heimweg ({city})").format(city=city),
            font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
            anchor="w",
        )
        self.weather_city_lbl.pack(fill="x", padx=PAD_SM, pady=(PAD_SM, PAD_XS))

        self.weather_temp_lbl = ctk.CTkLabel(
            self.weather_card,
            text="...",
            font=ctk.CTkFont(size=FONT_SIZE_H2, weight=FONT_WEIGHT_BOLD),
            anchor="w",
        )
        self.weather_temp_lbl.pack(fill="x", padx=PAD_SM, pady=PAD_XS)

        self.weather_desc_lbl = ctk.CTkLabel(
            self.weather_card,
            text="",
            font=ctk.CTkFont(size=FONT_SIZE_SM),
            anchor="w",
        )
        self.weather_desc_lbl.pack(fill="x", padx=PAD_SM, pady=PAD_XS)

        self.weather_umbrella_lbl = ctk.CTkLabel(
            self.weather_card,
            text="",
            font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
            anchor="w",
        )
        self.weather_umbrella_lbl.pack(fill="x", padx=PAD_SM, pady=(PAD_XS, PAD_SM))

    def refresh_weather_data(self, force: bool = False) -> None:
        def worker():
            w = WeatherService.fetch_weather(force_refresh=force)
            if self.winfo_exists():
                self.after(0, lambda: self._on_weather_data_loaded(w))

        threading.Thread(target=worker, daemon=True).start()

    def _on_weather_data_loaded(self, weather: WeatherInfo) -> None:
        self._weather_info = weather
        self.weather_temp_lbl.configure(text=f"{weather.temperature:.1f} °C")
        self.weather_desc_lbl.configure(
            text=f"{weather.condition_text} | Regenrisiko: {weather.rain_probability_max}%"
        )
        if weather.umbrella_recommended:
            self.weather_umbrella_lbl.configure(
                text=tr("checkout_panel.weather_umbrella_yes", "🌧 Regenschirm empfohlen!"),
                text_color=COLOR_CANCEL_FG,
            )
        else:
            self.weather_umbrella_lbl.configure(
                text=tr("checkout_panel.weather_umbrella_no", "Kein Regen gemeldet."),
                text_color=COLOR_SUCCESS,
            )

    def destroy(self) -> None:
        """Cancel background scheduled timers on destruction."""
        if self._transit_refresh_job is not None:
            try:
                self.after_cancel(self._transit_refresh_job)
            except Exception:
                pass
            self._transit_refresh_job = None
        super().destroy()
