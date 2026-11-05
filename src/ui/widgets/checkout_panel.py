"""Checkout & Departure Companion Panel widget and floating window.

Provides an integrated, collapsible or undockable right-hand companion
with 6 dedicated tabs:
1. Tasks (daily recurring & dated checkout checklist)
2. ÖPNV (live departures for DING Ulm/Neu-Ulm, or trips to a destination, & commute lead-time alarm)
3. Daily Note (free-text scratchpad with badge indicator & midnight reset)
4. Tomorrow (preview of upcoming follow-ups and deadlines)
5. Work Time (working time tracking & end-of-day projection)
6. Weather (commute weather & umbrella recommendation)
"""

from __future__ import annotations

import logging
import queue
import re
import sys
import threading
from collections.abc import Callable
from datetime import date, datetime, timedelta
from datetime import time as dt_time
from typing import Any

import customtkinter as ctk

from constants import (
    BORDER_WIDTH_CARD,
    BORDER_WIDTH_TRANSIT_SELECTED,
    BTN_HEIGHT_CHECKOUT_ACTION,
    BTN_HEIGHT_CHECKOUT_TINY,
    BTN_WIDTH_ACTION_SM,
    BTN_WIDTH_CHECKOUT_ACTION,
    BTN_WIDTH_CHECKOUT_TINY,
    BTN_WIDTH_CHECKOUT_UNSELECT,
    CHECKOUT_BACKGROUND_POLL_MS,
    CHECKOUT_FLOATING_MIN_HEIGHT,
    CHECKOUT_FLOATING_MIN_WIDTH,
    CHECKOUT_FLOATING_RESIZE_BORDER,
    CHECKOUT_HEADER_BTN_SIZE,
    CHECKOUT_HINT_WRAPLENGTH,
    COLOR_CANCEL_FG,
    COLOR_CANCEL_HOVER,
    COLOR_CARD_BG,
    COLOR_CHECKOUT_BORDER,
    COLOR_CHECKOUT_CARD_BG,
    COLOR_DANGER,
    COLOR_MUTED_LABEL,
    COLOR_SUCCESS,
    COLOR_SUCCESS_HOVER,
    COLOR_THEME_BTN,
    COLOR_TRANSIT_COUNTDOWN_OK,
    COLOR_TRANSIT_COUNTDOWN_URGENT,
    COLOR_TRANSIT_COUNTDOWN_WARN,
    COLOR_TRANSIT_DELAY,
    COLOR_TRANSIT_ONTIME,
    COLOR_TRANSIT_SELECTED_BG,
    COLOR_TRANSIT_SELECTED_BORDER,
    COLOR_TRANSIT_SELECTED_TEXT,
    COLOR_TRANSPARENT,
    CORNER_RADIUS_CARD,
    CORNER_RADIUS_MD,
    CORNER_RADIUS_SM,
    FONT_SIZE_BODY,
    FONT_SIZE_H2,
    FONT_SIZE_SM,
    FONT_WEIGHT_BOLD,
    ICON_DELETE_X,
    ICON_RESET_DEFAULT,
    ICON_KEY_CHECKOUT,
    ICON_KEY_DOCK,
    ICON_KEY_SETTINGS,
    ICON_KEY_UNDOCK,
    ICON_SIZE_ACTION,
    LABEL_WIDTH_TRANSIT_LINE,
    PAD_MD,
    PAD_NONE,
    PAD_SM,
    PAD_TINY,
    PAD_XS,
    TRANSIT_PLANNED_WINDOW_BEFORE_MINUTES,
    TRANSIT_REFRESH_INTERVAL_MS,
    ENTRY_WIDTH_CHECKOUT_LEAD,
    FONT_SIZE_TITLE,
    CHECKOUT_TAB_MAX_DEPARTURES,
    CHECKOUT_STACK_MAX_DEPARTURES,
    CHECKOUT_STACK_NOTE_HEIGHT,
)
from models.case import Case
from models.profile import UserProfile
from services.checkout_task_service import CheckoutTaskService
from services.ding_transit_service import DingTransitService, TransitDeparture, TransitTrip
from services.i18n_service import tr
from services.weather_service import WeatherInfo, WeatherService
from ui.widgets.collapsible_section import CollapsibleSection
from ui.widgets.stop_search_field import StopSearchField, format_stop
from utils.icon_utils import get_icon

logger = logging.getLogger("SupportCockpit.checkout")


class CheckoutFloatingWindow(ctk.CTkToplevel):
    """Borderless floating window for the Checkout panel on multi-monitor setups.

    The native title bar is removed (overrideredirect): the panel already has
    its own header with title and close button, so the OS bar only duplicated
    both. Moving works by dragging the panel header, resizing by dragging any
    window edge or corner - both are handled here because Windows no longer
    does it for a window without a frame.

    -topmost keeps it pinned on top across screens; without a frame it has no
    taskbar button of its own either.

    Deliberately *not* transient(master). Windows hides an owned window
    together with its owner, so the undocked panel used to vanish whenever
    the main window went to the tray (or was minimized) - exactly when the
    panel is meant to stay on screen on its own.
    """

    # Edge flags -> cursor shown while hovering that edge (Tk cursor names that
    # map to the native resize cursors on Windows, macOS and X11).
    _EDGE_CURSORS: dict[tuple[bool, bool, bool, bool], str] = {
        (True, False, True, False): "top_left_corner",
        (False, True, False, True): "bottom_right_corner",
        (False, True, True, False): "top_right_corner",
        (True, False, False, True): "bottom_left_corner",
        (True, False, False, False): "sb_h_double_arrow",
        (False, True, False, False): "sb_h_double_arrow",
        (False, False, True, False): "sb_v_double_arrow",
        (False, False, False, True): "sb_v_double_arrow",
    }

    def __init__(
        self,
        master: Any,
        on_dock_callback: Callable[[], None],
        on_close_callback: Callable[[], None],
    ) -> None:
        super().__init__(master)
        # macOS gives an overrideredirect window no keyboard focus at all, so
        # the native frame stays there.
        self._frameless = sys.platform != "darwin"
        if self._frameless:
            self.overrideredirect(True)
        elif sys.platform == "win32":
            try:
                self.attributes("-toolwindow", True)
            except Exception:
                pass
        self.attributes("-topmost", True)
        self.resizable(True, True)
        self.title(tr("checkout_panel.title", "Feierabend- & Checkout-Begleiter"))

        self.minsize(CHECKOUT_FLOATING_MIN_WIDTH, CHECKOUT_FLOATING_MIN_HEIGHT)
        self.protocol("WM_DELETE_WINDOW", on_close_callback)
        self.on_dock_callback = on_dock_callback
        self.on_close_callback = on_close_callback

        self._drag_areas: set[Any] = set()
        self._drag_excludes: set[Any] = set()
        self._edge: tuple[bool, bool, bool, bool] | None = None  # left, right, top, bottom
        self._mode: str | None = None  # "move" | "resize" while the mouse button is held
        self._press: tuple[int, int, int, int, int, int] = (0, 0, 0, 0, 0, 0)
        self._cursor = ""

        if self._frameless:
            # Bound on the toplevel's bindtag, which every child widget carries,
            # so the handlers see clicks anywhere in the window.
            self.bind("<Motion>", self._on_motion, add="+")
            self.bind("<ButtonPress-1>", self._on_press, add="+")
            self.bind("<B1-Motion>", self._on_drag, add="+")
            self.bind("<ButtonRelease-1>", self._on_release, add="+")

    def register_drag_area(self, area: Any, exclude: tuple[Any, ...] = ()) -> None:
        """Lets the user move the window by dragging *area* (minus *exclude*, e.g. its buttons)."""
        self._drag_areas.add(area)
        self._drag_excludes.update(exclude)

    def _is_drag_handle(self, widget: Any) -> bool:
        # Walk up from the clicked tk widget (CTk widgets are built from inner
        # canvases and labels) until we hit a registered area or an exclusion.
        w = widget
        while w is not None and w is not self:
            if w in self._drag_excludes:
                return False
            if w in self._drag_areas:
                return True
            w = getattr(w, "master", None)
        return False

    def _edge_at(self, x_root: int, y_root: int) -> tuple[bool, bool, bool, bool] | None:
        x = x_root - self.winfo_rootx()
        y = y_root - self.winfo_rooty()
        w, h, b = self.winfo_width(), self.winfo_height(), CHECKOUT_FLOATING_RESIZE_BORDER
        edge = (x < b, x >= w - b, y < b, y >= h - b)
        return edge if any(edge) else None

    def _set_cursor(self, cursor: str) -> None:
        if cursor != self._cursor:
            self._cursor = cursor
            try:
                self.configure(cursor=cursor)
            except Exception:
                pass

    def _on_motion(self, event: Any) -> None:
        if self._mode is None:
            edge = self._edge_at(event.x_root, event.y_root)
            self._set_cursor(self._EDGE_CURSORS.get(edge, "") if edge else "")

    def _on_press(self, event: Any) -> None:
        # A frameless window is not activated by Windows reliably, so claim the
        # keyboard ourselves - otherwise typing into the task entry goes to the
        # window underneath.
        try:
            focused = self.focus_get()
            if focused is None or focused.winfo_toplevel() is not self:
                target = event.widget
                if target.winfo_class() in ("Entry", "Text"):
                    target.focus_force()
                else:
                    self.focus_force()
        except Exception:
            pass

        self._edge = self._edge_at(event.x_root, event.y_root)
        if self._edge:
            self._mode = "resize"
        elif self._is_drag_handle(event.widget):
            self._mode = "move"
        else:
            self._mode = None
            return
        self._press = (
            event.x_root, event.y_root,
            self.winfo_x(), self.winfo_y(),
            self.winfo_width(), self.winfo_height(),
        )

    def _on_drag(self, event: Any) -> None:
        if self._mode is None:
            return
        px, py, x, y, w, h = self._press
        dx, dy = event.x_root - px, event.y_root - py
        # wm_geometry, not geometry(): CTk's geometry() rescales by the DPI
        # factor, while winfo_* above already returns physical pixels.
        if self._mode == "move":
            self.wm_geometry(f"+{x + dx}+{y + dy}")
            return

        scale = float(ctk.ScalingTracker.get_window_scaling(self))
        min_w = round(CHECKOUT_FLOATING_MIN_WIDTH * scale)
        min_h = round(CHECKOUT_FLOATING_MIN_HEIGHT * scale)
        left, right, top, bottom = self._edge or (False, False, False, False)
        if right:
            w = max(min_w, w + dx)
        if bottom:
            h = max(min_h, h + dy)
        if left:
            new_w = max(min_w, w - dx)
            x += w - new_w
            w = new_w
        if top:
            new_h = max(min_h, h - dy)
            y += h - new_h
            h = new_h
        self.wm_geometry(f"{w}x{h}+{x}+{y}")

    def _on_release(self, event: Any) -> None:
        self._mode = None
        self._on_motion(event)


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
        on_open_settings: Callable[[], None] | None = None,
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
        self.on_open_settings = on_open_settings

        self._transit_departures: list[TransitDeparture] = []
        # Trips to the destination; filled instead of plain departures while a destination is set
        self._transit_trips: list[TransitTrip] = []
        # Destination the current list was planned for ({"name": "", ...} = none, all departures)
        self._applied_destination: dict[str, str] = self.settings.effective_destination()
        self._selected_dep_key: str | None = None
        self._selected_departure: TransitDeparture | None = None
        self._notified_stages: set[str] = set()
        self._weather_info: WeatherInfo | None = None
        self._is_fetching_transit = False
        self._transit_refetch_pending = False
        # Planned departure time for the ÖPNV list; None = next departures from now
        self._planned_departure: dt_time | None = None
        self._note_debounce_timer: Any = None
        self._transit_refresh_job: Any = None
        self._background_polls: set[str] = set()

        # Perform midnight reset check
        if CheckoutTaskService.check_and_perform_midnight_reset(self.settings):
            self._persist_settings()

        self._build_header()
        self._build_tabs()

        # Undocked, the header doubles as the title bar of the frameless window.
        top = self.winfo_toplevel()
        if isinstance(top, CheckoutFloatingWindow):
            top.register_drag_area(self.header_frame, exclude=(self.header_btn_box,))

        # Initial background fetches
        self.refresh_transit_data(force=True)
        self.refresh_weather_data(force=False)
        self._schedule_next_transit_refresh()

    def set_closable(self, closable: bool) -> None:
        """Shows or hides the close button (hidden while the panel is set to always show)."""
        if not hasattr(self, "close_btn"):
            return
        if closable and not self.close_btn.winfo_manager():
            self.close_btn.pack(side="left", padx=PAD_XS)
        elif not closable and self.close_btn.winfo_manager():
            self.close_btn.pack_forget()

    def rebind_profile(self, profile: UserProfile) -> None:
        """Switches to a reloaded profile so changed settings (e.g. the stop) apply right away."""
        old_stop = self.settings.stops[0] if self.settings.stops else None
        self.profile = profile
        self.settings = profile.checkout_settings
        new_stop = self.settings.stops[0] if self.settings.stops else None
        if new_stop != old_stop:
            self._selected_dep_key = None
            self._selected_departure = None
            self.refresh_transit_data(force=True)
        elif self.settings.effective_destination() != self._applied_destination:
            self.refresh_transit_data(force=True)

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
        self.header_btn_box = btn_box

        from ui.widgets.ctk_tooltip import CTkTooltip

        # Settings shortcut: opens the profile dialog on the end-of-day page
        if self.on_open_settings is not None:
            self.settings_btn = ctk.CTkButton(
                btn_box,
                text="",
                image=get_icon(ICON_KEY_SETTINGS, size=ICON_SIZE_ACTION),
                command=self.on_open_settings,
                width=CHECKOUT_HEADER_BTN_SIZE,
                height=CHECKOUT_HEADER_BTN_SIZE,
                fg_color=COLOR_THEME_BTN,
            )
            self.settings_btn.pack(side="left", padx=PAD_XS)
            self._settings_tooltip = CTkTooltip(
                self.settings_btn, tr("settings_checkout.open_settings", "Feierabend-Einstellungen")
            )

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
        # Docked next to the cases the panel is tall and narrow: tabs would leave
        # most of it empty, so everything is shown at once in one column.
        if not self.is_floating:
            self._build_stack()
            return
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
    # Docked layout: summary strip plus collapsible sections in one column
    # -------------------------------------------------------------------------
    def _build_stack(self) -> None:
        self.tabview = None
        self._sections: dict[str, CollapsibleSection] = {}
        self.stack_scroll = ctk.CTkScrollableFrame(self, fg_color=COLOR_TRANSPARENT)
        self.stack_scroll.pack(fill="both", expand=True, padx=PAD_XS, pady=(PAD_NONE, PAD_XS))

        self._setup_summary_strip(self.stack_scroll)

        note_title = (
            tr("checkout_panel.tab_note_badged", "Tagesnotiz ●")
            if self.settings.daily_note_text.strip()
            else tr("checkout_panel.tab_note", "Tagesnotiz")
        )
        self.tab_name_note = note_title
        self.tab_transit = self._add_stack_section("transit", tr("checkout_panel.tab_transit", "ÖPNV"))
        self.tab_tasks = self._add_stack_section("tasks", tr("checkout_panel.tab_tasks", "Tasks"))
        self.tab_note = self._add_stack_section("note", note_title)
        self.tab_tomorrow = self._add_stack_section("tomorrow", tr("checkout_panel.tab_tomorrow", "Morgen"))

        self._setup_transit_tab()
        self._setup_tasks_tab()
        self._setup_note_tab()
        self._setup_tomorrow_tab()

    def _add_stack_section(self, section_id: str, title: str) -> ctk.CTkFrame:
        collapsed = section_id in self.settings.collapsed_sections
        section = CollapsibleSection(
            self.stack_scroll,
            title=title,
            expanded=not collapsed,
            on_toggle=lambda expanded, sid=section_id: self._on_section_toggled(sid, expanded),
        )
        section.pack(fill="x", pady=(PAD_SM, PAD_NONE))
        self._sections[section_id] = section
        return section.body

    def _on_section_toggled(self, section_id: str, expanded: bool) -> None:
        collapsed = [s for s in self.settings.collapsed_sections if s != section_id]
        if not expanded:
            collapsed.append(section_id)
        self.settings.collapsed_sections = collapsed
        self._persist_settings()

    def _list_container(self, parent: Any) -> Any:
        """A scrollable list inside a tab; a plain frame in the docked column, which scrolls as a whole."""
        if self.is_floating:
            return ctk.CTkScrollableFrame(parent, fg_color=COLOR_TRANSPARENT)
        return ctk.CTkFrame(parent, fg_color=COLOR_TRANSPARENT)

    def _setup_summary_strip(self, parent: Any) -> None:
        """Weather and working time in two short lines at the top of the docked panel."""
        card = ctk.CTkFrame(parent, fg_color=COLOR_CARD_BG, corner_radius=CORNER_RADIUS_MD)
        card.pack(fill="x", pady=(PAD_XS, PAD_NONE))

        weather_row = ctk.CTkFrame(card, fg_color=COLOR_TRANSPARENT)
        weather_row.pack(fill="x", padx=PAD_SM, pady=(PAD_XS, PAD_NONE))
        city = self.settings.weather_city or "Ulm"
        # Kept for the shared weather update; the city sits in the tooltip here.
        self.weather_city_lbl = ctk.CTkLabel(
            weather_row,
            text=tr("checkout_panel.weather_title", "Wetter für den Heimweg ({city})").format(city=city),
        )
        self.weather_temp_lbl = ctk.CTkLabel(
            weather_row, text="...", font=ctk.CTkFont(size=FONT_SIZE_TITLE, weight=FONT_WEIGHT_BOLD), anchor="w"
        )
        self.weather_temp_lbl.pack(side="left", padx=(PAD_NONE, PAD_SM))
        self.weather_desc_lbl = ctk.CTkLabel(
            weather_row, text="", font=ctk.CTkFont(size=FONT_SIZE_SM), text_color=COLOR_MUTED_LABEL, anchor="w"
        )
        self.weather_desc_lbl.pack(side="left", fill="x", expand=True)
        self.weather_umbrella_lbl = ctk.CTkLabel(
            card, text="", font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD), anchor="w"
        )
        self.weather_umbrella_lbl.pack(fill="x", padx=PAD_SM)

        work_row = ctk.CTkFrame(card, fg_color=COLOR_TRANSPARENT)
        work_row.pack(fill="x", padx=PAD_SM, pady=(PAD_NONE, PAD_XS))
        elapsed_minutes, projected_end = self._compute_worktime()
        self.worktime_net_lbl = ctk.CTkLabel(
            work_row,
            text=tr("checkout_panel.summary_net", "Netto {hours}:{minutes:02d} Std.").format(
                hours=elapsed_minutes // 60, minutes=elapsed_minutes % 60
            ),
            font=ctk.CTkFont(size=FONT_SIZE_SM),
            text_color=COLOR_CANCEL_FG if elapsed_minutes >= 600 else COLOR_MUTED_LABEL,
            anchor="w",
        )
        self.worktime_net_lbl.pack(side="left")
        self.worktime_end_lbl = ctk.CTkLabel(
            work_row,
            text=tr("checkout_panel.summary_end", "Feierabend ca. {time} Uhr").format(time=projected_end.strftime("%H:%M")),
            font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD),
            text_color=COLOR_SUCCESS,
            anchor="e",
        )
        self.worktime_end_lbl.pack(side="right")

    def _compute_worktime(self) -> tuple[int, datetime]:
        """Net minutes worked so far today and the projected end of the working day."""
        now = datetime.now()
        start_parts = self.settings.work_start_time.split(":")
        try:
            start_dt = now.replace(hour=int(start_parts[0]), minute=int(start_parts[1]), second=0, microsecond=0)
        except Exception:
            start_dt = now.replace(hour=8, minute=0, second=0, microsecond=0)
        elapsed_minutes = max(0, int((now - start_dt).total_seconds() / 60) - self.settings.work_break_minutes)
        target_minutes = int(self.settings.work_target_hours * 60) + self.settings.work_break_minutes
        return elapsed_minutes, start_dt + timedelta(minutes=target_minutes)

    # -------------------------------------------------------------------------
    # TAB 1: Tasks (Checklist)
    # -------------------------------------------------------------------------
    def _setup_tasks_tab(self) -> None:
        tab = self.tab_tasks

        # Scrollable container
        self.tasks_scroll = self._list_container(tab)
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

        # Compact header: stop and refresh on one row, lead time and status on the next,
        # so the departure list starts high up even in a small panel.
        self.transit_card = ctk.CTkFrame(tab, fg_color=COLOR_CARD_BG, corner_radius=CORNER_RADIUS_MD)
        self.transit_card.pack(fill="x", padx=PAD_XS, pady=(PAD_XS, PAD_NONE))

        top_row = ctk.CTkFrame(self.transit_card, fg_color=COLOR_TRANSPARENT)
        top_row.pack(fill="x", padx=PAD_SM, pady=(PAD_XS, PAD_NONE))

        stop_name = self.settings.stops[0].get("name", "Ulm Ehinger Tor") if self.settings.stops else "Ulm Ehinger Tor"
        self.transit_stop_lbl = ctk.CTkLabel(
            top_row,
            text=f"🚏 {stop_name}",
            font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
            anchor="w",
        )
        self.transit_stop_lbl.pack(side="left", fill="x", expand=True)

        self.transit_refresh_btn = ctk.CTkButton(
            top_row,
            text="🔄",
            command=lambda: self.refresh_transit_data(force=True),
            width=BTN_WIDTH_CHECKOUT_ACTION,
            height=BTN_HEIGHT_CHECKOUT_ACTION,
            fg_color=COLOR_THEME_BTN,
        )
        self.transit_refresh_btn.pack(side="right")

        from ui.widgets.ctk_tooltip import CTkTooltip

        # Planned departure: show the buses around this time instead of the next ones
        self.transit_time_reset_btn = ctk.CTkButton(
            top_row,
            text=ICON_DELETE_X,
            command=self._clear_planned_departure,
            width=BTN_WIDTH_CHECKOUT_TINY,
            height=BTN_HEIGHT_CHECKOUT_TINY,
            fg_color=COLOR_CANCEL_FG,
            hover_color=COLOR_CANCEL_HOVER,
        )
        CTkTooltip(
            self.transit_time_reset_btn,
            tr("checkout_panel.transit_planned_reset", "Zurück zu den nächsten Abfahrten"),
        )

        self.transit_time_entry = ctk.CTkEntry(
            top_row,
            width=ENTRY_WIDTH_CHECKOUT_LEAD,
            height=BTN_HEIGHT_CHECKOUT_ACTION,
            placeholder_text=tr("checkout_panel.transit_planned_placeholder", "hh:mm"),
            font=ctk.CTkFont(size=FONT_SIZE_SM),
            justify="center",
        )
        self.transit_time_entry.pack(side="right", padx=(PAD_XS, PAD_XS))
        self.transit_time_entry.bind("<Return>", lambda _e: self._apply_planned_departure())
        self.transit_time_entry.bind("<KP_Enter>", lambda _e: self._apply_planned_departure())
        self.transit_time_entry.bind("<Escape>", lambda _e: self._clear_planned_departure())
        self._transit_time_border = self.transit_time_entry.cget("border_color")
        CTkTooltip(
            self.transit_time_entry,
            tr(
                "checkout_panel.transit_planned_tooltip",
                "Geplante Abfahrt (z. B. 17:05) + Enter zeigt die Fahrten um diese Uhrzeit. Leer + Enter = nächste Abfahrten.",
            ),
        )

        # Destination: with one the list holds only connections that get there, with arrival time.
        dest_row = ctk.CTkFrame(self.transit_card, fg_color=COLOR_TRANSPARENT)
        dest_row.pack(fill="x", padx=PAD_SM, pady=(PAD_XS, PAD_NONE))
        self.transit_dest_icon_lbl = ctk.CTkLabel(
            dest_row, text="🏁", font=ctk.CTkFont(size=FONT_SIZE_BODY), width=BTN_WIDTH_CHECKOUT_TINY
        )
        self.transit_dest_icon_lbl.pack(side="left", anchor="n", padx=(PAD_NONE, PAD_XS))

        self.transit_dest_reset_btn = ctk.CTkButton(
            dest_row,
            text=ICON_RESET_DEFAULT,
            command=self._reset_destination_to_default,
            width=BTN_WIDTH_CHECKOUT_TINY,
            height=BTN_HEIGHT_CHECKOUT_ACTION,
            fg_color=COLOR_THEME_BTN,
        )
        CTkTooltip(
            self.transit_dest_reset_btn,
            lambda: tr("checkout_panel.transit_destination_reset", "Zurück zum Standardziel: {stop}").format(
                stop=format_stop(self.settings.destination)
            ),
        )
        self.transit_dest_clear_btn = ctk.CTkButton(
            dest_row,
            text=ICON_DELETE_X,
            command=self._clear_destination_today,
            width=BTN_WIDTH_CHECKOUT_TINY,
            height=BTN_HEIGHT_CHECKOUT_ACTION,
            fg_color=COLOR_CANCEL_FG,
            hover_color=COLOR_CANCEL_HOVER,
        )
        CTkTooltip(
            self.transit_dest_clear_btn,
            tr("checkout_panel.transit_destination_clear", "Heute ohne Ziel: alle Abfahrten zeigen"),
        )

        self.transit_dest_field = StopSearchField(
            dest_row,
            on_pick=self._on_destination_picked,
            on_status=self._on_destination_search_status,
            placeholder_text=tr("checkout_panel.transit_destination_placeholder", "Ziel (optional)"),
            entry_height=BTN_HEIGHT_CHECKOUT_ACTION,
            font=ctk.CTkFont(size=FONT_SIZE_SM),
        )
        self.transit_dest_field.pack(side="left", fill="x", expand=True)
        self.transit_dest_field.entry.bind("<Return>", lambda _e: self._submit_destination_text(), add="+")
        self.transit_dest_field.entry.bind("<KP_Enter>", lambda _e: self._submit_destination_text(), add="+")
        CTkTooltip(
            self.transit_dest_field.entry,
            tr(
                "checkout_panel.transit_destination_tooltip",
                "Ziel eintippen und Vorschlag wählen (oder Enter): Es erscheinen nur Verbindungen dorthin, "
                "auch mit Umstieg, samt Ankunftszeit. Gilt für heute; das Standardziel steht in den Einstellungen.",
            ),
        )
        self._sync_destination_controls()

        info_row = ctk.CTkFrame(self.transit_card, fg_color=COLOR_TRANSPARENT)
        info_row.pack(fill="x", padx=PAD_SM, pady=(PAD_NONE, PAD_XS))

        lead_time = (
            self.settings.walk_time_minutes
            + self.settings.logout_time_minutes
            + self.settings.pack_time_minutes
            + self.settings.buffer_time_minutes
        )
        self.transit_lead_lbl = ctk.CTkLabel(
            info_row,
            text=tr("checkout_panel.transit_total_lead", "Benötigter Vorlauf: {minutes} Min.").format(minutes=lead_time),
            font=ctk.CTkFont(size=FONT_SIZE_SM),
            text_color=COLOR_MUTED_LABEL,
            anchor="w",
        )
        self.transit_lead_lbl.pack(side="left")

        self.transit_status_lbl = ctk.CTkLabel(
            info_row,
            text="",
            font=ctk.CTkFont(size=FONT_SIZE_SM),
            text_color=COLOR_MUTED_LABEL,
            anchor="e",
        )
        self.transit_status_lbl.pack(side="right")

        # Hint, only while nothing is selected (the selection card takes its place)
        self.transit_hint_lbl = ctk.CTkLabel(
            tab,
            text=tr("checkout_panel.transit_double_click_hint", "💡 Doppelklick auf eine Fahrt wählt diese aus und stellt die Wecker."),
            font=ctk.CTkFont(size=FONT_SIZE_SM),
            text_color=COLOR_MUTED_LABEL,
            anchor="w",
            wraplength=CHECKOUT_HINT_WRAPLENGTH,
            justify="left",
        )
        self.transit_hint_lbl.pack(fill="x", padx=PAD_SM, pady=(PAD_XS, PAD_NONE))

        # Selected transit & multi-stage alarm card (packed only once a departure is chosen)
        self.selected_transit_card = ctk.CTkFrame(
            tab,
            fg_color=COLOR_CHECKOUT_CARD_BG,
            border_width=BORDER_WIDTH_TRANSIT_SELECTED,
            border_color=COLOR_TRANSIT_SELECTED_BORDER,
            corner_radius=CORNER_RADIUS_CARD,
        )

        sel_top_row = ctk.CTkFrame(self.selected_transit_card, fg_color=COLOR_TRANSPARENT)
        sel_top_row.pack(fill="x", padx=PAD_SM, pady=(PAD_SM, PAD_XS))

        self.selected_transit_title_lbl = ctk.CTkLabel(
            sel_top_row,
            text=f"🎯 {tr('checkout_panel.transit_selected_title', 'Gewählte Fahrt & Wecker')}",
            font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD),
            text_color=COLOR_TRANSIT_SELECTED_TEXT,
            anchor="w",
        )
        self.selected_transit_title_lbl.pack(side="left", fill="x", expand=True)

        self.transit_unselect_btn = ctk.CTkButton(
            sel_top_row,
            text=tr("checkout_panel.transit_unselect_btn", "Abwählen"),
            width=BTN_WIDTH_CHECKOUT_UNSELECT,
            height=BTN_HEIGHT_CHECKOUT_TINY,
            fg_color=COLOR_CANCEL_FG,
            hover_color=COLOR_CANCEL_HOVER,
            command=self._clear_selected_departure,
        )
        self.transit_unselect_btn.pack(side="right")

        self.selected_transit_desc_lbl = ctk.CTkLabel(
            self.selected_transit_card,
            text="",
            font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD),
            anchor="w",
        )
        self.selected_transit_desc_lbl.pack(fill="x", padx=PAD_SM, pady=(PAD_NONE, PAD_XS))

        milestones_box = ctk.CTkFrame(self.selected_transit_card, fg_color=COLOR_TRANSPARENT)
        milestones_box.pack(fill="x", padx=PAD_SM, pady=(PAD_NONE, PAD_SM))

        self.stage_pack_lbl = ctk.CTkLabel(
            milestones_box,
            text="",
            font=ctk.CTkFont(size=FONT_SIZE_SM),
            anchor="w",
        )
        self.stage_pack_lbl.pack(fill="x", pady=PAD_TINY)

        self.stage_logout_lbl = ctk.CTkLabel(
            milestones_box,
            text="",
            font=ctk.CTkFont(size=FONT_SIZE_SM),
            anchor="w",
        )
        self.stage_logout_lbl.pack(fill="x", pady=PAD_TINY)

        self.stage_walk_lbl = ctk.CTkLabel(
            milestones_box,
            text="",
            font=ctk.CTkFont(size=FONT_SIZE_SM),
            anchor="w",
        )
        self.stage_walk_lbl.pack(fill="x", pady=PAD_TINY)

        self.stage_dep_lbl = ctk.CTkLabel(
            milestones_box,
            text="",
            font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD),
            anchor="w",
        )
        self.stage_dep_lbl.pack(fill="x", pady=PAD_TINY)

        # Shown only for a trip to a destination
        self.stage_arrival_lbl = ctk.CTkLabel(
            milestones_box,
            text="",
            font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD),
            text_color=COLOR_TRANSIT_SELECTED_TEXT,
            anchor="w",
        )

        # Scrollable departures table
        self.transit_scroll = self._list_container(tab)
        self.transit_scroll.pack(fill="both", expand=True, padx=PAD_XS, pady=(PAD_XS, PAD_XS))

    def refresh_transit_data(self, force: bool = False) -> None:
        """Fetch departures in a background thread and update UI."""
        if self._is_fetching_transit:
            # A changed stop or planned time must not be dropped: fetch again once this one is back.
            self._transit_refetch_pending = self._transit_refetch_pending or force
            return
        self._is_fetching_transit = True
        self.transit_status_lbl.configure(text=tr("checkout_panel.transit_refreshing", "Aktualisiere Abfahrten..."))

        stop = self.settings.stops[0] if self.settings.stops else {"name": "Ulm Ehinger Tor", "place": "Ulm"}
        stop_name = stop.get("name", "Ulm Ehinger Tor")
        stop_place = stop.get("place", "Ulm")

        departure_time = self._planned_request_time()
        destination = self.settings.effective_destination()
        if destination != self._applied_destination:
            self._applied_destination = destination
            self._sync_destination_controls()
        dest_name = destination.get("name", "").strip()
        if dest_name:
            dest_place = destination.get("place", "").strip()
            limit = CHECKOUT_TAB_MAX_DEPARTURES if self.is_floating else CHECKOUT_STACK_MAX_DEPARTURES
            self._run_in_background(
                lambda: DingTransitService.fetch_trips(
                    stop_name,
                    stop_place,
                    dest_name,
                    dest_place,
                    limit=limit,
                    force_refresh=force,
                    departure_time=departure_time,
                ),
                lambda trips: self._on_transit_data_loaded([t.departure for t in trips], trips),
            )
            return
        self._run_in_background(
            lambda: DingTransitService.fetch_departures(
                stop_name, stop_place, force_refresh=force, departure_time=departure_time
            ),
            self._on_transit_data_loaded,
        )

    # -------------------------------------------------------------------------
    # Destination (trip planning)
    # -------------------------------------------------------------------------
    def _has_destination(self) -> bool:
        return bool(self._applied_destination.get("name", "").strip())

    def _sync_destination_controls(self) -> None:
        """Shows the applied destination in the field and the clear / back-to-default buttons that fit."""
        if not hasattr(self, "transit_dest_field"):
            return
        self.transit_dest_field.set_text(format_stop(self._applied_destination))
        default = dict(self.settings.destination)
        has_default = bool(default.get("name", "").strip())
        show_clear = self._has_destination()
        show_reset = has_default and self._applied_destination != default
        # pack order from the right: clear (outermost), then reset
        for btn in (self.transit_dest_clear_btn, self.transit_dest_reset_btn):
            if btn.winfo_manager():
                btn.pack_forget()
        self.transit_dest_field.pack_forget()
        if show_clear:
            self.transit_dest_clear_btn.pack(side="right", anchor="n", padx=(PAD_XS, PAD_NONE))
        if show_reset:
            self.transit_dest_reset_btn.pack(side="right", anchor="n", padx=(PAD_XS, PAD_NONE))
        self.transit_dest_field.pack(side="left", fill="x", expand=True)

    def _set_destination_today(self, destination: dict[str, str]) -> None:
        """Applies a destination for the rest of today and plans the list again."""
        self.settings.destination_today = {
            "name": destination.get("name", "").strip(),
            "place": destination.get("place", "").strip(),
        }
        self.settings.destination_today_date = date.today().isoformat()
        self._persist_settings()
        # Set here, not only in refresh: a fetch still running makes refresh return early (and refetch later).
        self._applied_destination = self.settings.effective_destination()
        self._sync_destination_controls()
        self.refresh_transit_data(force=True)

    def _on_destination_picked(self, stop: Any) -> None:
        self._set_destination_today({"name": stop.name, "place": stop.place})

    def _submit_destination_text(self) -> None:
        """Enter in the field: typed text becomes the destination (EFA resolves the name), empty = none."""
        text = self.transit_dest_field.get()
        self.transit_dest_field.hide_suggestions()
        if text == format_stop(self._applied_destination):
            return
        self._set_destination_today({"name": text, "place": ""})

    def _clear_destination_today(self) -> None:
        self._set_destination_today({"name": "", "place": ""})

    def _reset_destination_to_default(self) -> None:
        self._set_destination_today(dict(self.settings.destination))

    def _on_destination_search_status(self, status: str) -> None:
        texts = {
            "searching": tr("checkout_panel.transit_destination_searching", "Suche Ziel …"),
            "none": tr("checkout_panel.transit_destination_none", "Kein passendes Ziel gefunden."),
            "error": tr("checkout_panel.transit_destination_error", "Fahrplanauskunft nicht erreichbar."),
        }
        if status in texts:
            self.transit_status_lbl.configure(text=texts[status])

    def _selected_trip(self) -> TransitTrip | None:
        if not self._selected_dep_key or not self._has_destination():
            return None
        return next(
            (t for t in self._transit_trips if self._dep_key(t.departure) == self._selected_dep_key),
            None,
        )

    @staticmethod
    def _dep_key(dep: TransitDeparture) -> str:
        return f"{dep.line}_{dep.planned_time_str}_{dep.destination}"

    @staticmethod
    def _changes_text(count: int) -> str:
        if count <= 0:
            return tr("checkout_panel.transit_trip_direct", "Direkt")
        if count == 1:
            return tr("checkout_panel.transit_trip_one_change", "1 Umstieg")
        return tr("checkout_panel.transit_trip_changes", "{count} Umstiege").format(count=count)

    # -------------------------------------------------------------------------
    # Planned departure time
    # -------------------------------------------------------------------------
    @staticmethod
    def _parse_planned_time(text: str) -> dt_time | None:
        """Parses "17", "1705", "17:05" or "17.05". Empty -> None; anything else raises ValueError."""
        text = text.strip()
        if not text:
            return None
        m = re.fullmatch(r"(\d{1,2})(?:[:.]?(\d{2}))?", text)
        if not m:
            raise ValueError(text)
        return dt_time(int(m.group(1)), int(m.group(2) or 0))  # ValueError for 25:00 / 17:70

    def _planned_request_time(self) -> datetime | None:
        """Start of the requested window: a little before the planned time, so earlier buses show too."""
        if self._planned_departure is None:
            return None
        planned = datetime.combine(date.today(), self._planned_departure)
        return planned - timedelta(minutes=TRANSIT_PLANNED_WINDOW_BEFORE_MINUTES)

    def _apply_planned_departure(self) -> None:
        try:
            planned = self._parse_planned_time(self.transit_time_entry.get())
        except ValueError:
            self.transit_time_entry.configure(border_color=COLOR_DANGER)
            return
        self.transit_time_entry.configure(border_color=self._transit_time_border)
        if planned is None:
            self._clear_planned_departure()
            return
        self.transit_time_entry.delete(0, "end")
        self.transit_time_entry.insert(0, planned.strftime("%H:%M"))
        self._planned_departure = planned
        if not self.transit_time_reset_btn.winfo_manager():
            self.transit_time_reset_btn.pack(side="right", before=self.transit_time_entry)
        self.refresh_transit_data(force=True)

    def _clear_planned_departure(self) -> None:
        self.transit_time_entry.configure(border_color=self._transit_time_border)
        self.transit_time_entry.delete(0, "end")
        self.focus_set()  # brings the placeholder back
        if self.transit_time_reset_btn.winfo_manager():
            self.transit_time_reset_btn.pack_forget()
        if self._planned_departure is not None:
            self._planned_departure = None
            self.refresh_transit_data(force=True)

    def _on_transit_data_loaded(
        self, deps: list[TransitDeparture], trips: list[TransitTrip] | None = None
    ) -> None:
        self._is_fetching_transit = False
        if self._transit_refetch_pending:
            # The stop, destination or planned time changed while this request ran: its result is stale.
            self._transit_refetch_pending = False
            self.refresh_transit_data(force=True)
            return
        self._transit_departures = deps
        self._transit_trips = list(trips or [])
        now_str = datetime.now().strftime("%H:%M")
        status = f"Stand: {now_str} Uhr"
        if self._planned_departure is not None:
            status = tr("checkout_panel.transit_planned_status", "🕒 {time} · {status}").format(
                time=self._planned_departure.strftime("%H:%M"), status=status
            )
        self.transit_status_lbl.configure(text=status)

        if self._selected_dep_key:
            matched = next(
                (
                    d
                    for d in deps
                    if f"{d.line}_{d.planned_time_str}_{d.destination}" == self._selected_dep_key
                ),
                None,
            )
            if matched:
                self._selected_departure = matched

        self._update_selected_card()
        self._render_departures()
        self._check_commute_alarms()

    def _bind_double_click_recursive(self, widget: Any, callback: Callable[[], None]) -> None:
        """Bind double-click event to widget and all child elements."""
        def _on_dbl(_event: Any = None) -> None:
            callback()

        try:
            widget.bind("<Double-Button-1>", _on_dbl, add="+")
        except Exception:
            pass
        for child in widget.winfo_children():
            self._bind_double_click_recursive(child, callback)

    def _on_departure_double_clicked(self, dep: TransitDeparture) -> None:
        """Toggle selection of a transit departure for commute alarms and countdowns."""
        dep_key = f"{dep.line}_{dep.planned_time_str}_{dep.destination}"
        if self._selected_dep_key == dep_key:
            self._clear_selected_departure()
            return

        self._selected_dep_key = dep_key
        self._selected_departure = dep
        self._notified_stages.clear()
        self._update_selected_card()
        self._render_departures()
        self._check_commute_alarms()

    def _clear_selected_departure(self) -> None:
        """Clear active departure selection and hide detail card."""
        self._selected_dep_key = None
        self._selected_departure = None
        self._notified_stages.clear()
        self._show_transit_hint()
        self._render_departures()

    def _update_selected_card(self) -> None:
        """Update information and milestones on the selected transit card."""
        if not self._selected_departure or not hasattr(self, "selected_transit_card"):
            self._show_transit_hint()
            return

        dep = self._selected_departure
        info = DingTransitService.calculate_leave_info(
            dep,
            walk_min=self.settings.walk_time_minutes,
            logout_min=self.settings.logout_time_minutes,
            pack_min=self.settings.pack_time_minutes,
            buffer_min=self.settings.buffer_time_minutes,
        )

        trip = self._selected_trip()
        if trip is not None:
            desc_text = tr(
                "checkout_panel.transit_selected_trip_desc",
                "Linie {lines} um {time} Uhr · {changes}",
            ).format(lines=" › ".join(trip.lines), time=dep.real_time_str, changes=self._changes_text(trip.interchanges))
        else:
            desc_text = tr(
                "checkout_panel.transit_selected_desc",
                "Linie {line} nach {dest} um {time} Uhr",
            ).format(
                line=dep.line,
                dest=dep.destination,
                time=dep.real_time_str,
            )
        self.selected_transit_desc_lbl.configure(text=desc_text)

        pack_diff = info.get("minutes_until_pack", 0)
        pack_status = f"(in {pack_diff} Min.)" if pack_diff > 0 else "(Jetzt!)"
        self.stage_pack_lbl.configure(
            text=f"🎒 {tr('checkout_panel.transit_stage_pack', '1. Garderobe & Packen')}: {info.get('pack_time_str')} Uhr {pack_status}"
        )

        logout_diff = info.get("minutes_until_logout", 0)
        logout_status = f"(in {logout_diff} Min.)" if logout_diff > 0 else "(Jetzt!)"
        self.stage_logout_lbl.configure(
            text=f"💻 {tr('checkout_panel.transit_stage_logout', '2. PC abmelden & ausschalten')}: {info.get('logout_time_str')} Uhr {logout_status}"
        )

        walk_diff = info.get("minutes_until_walk", 0)
        walk_status = f"(in {walk_diff} Min.)" if walk_diff > 0 else "(Jetzt!)"
        self.stage_walk_lbl.configure(
            text=f"🚶 {tr('checkout_panel.transit_stage_walk', '3. Aufbrechen & Losgehen')}: {info.get('walk_time_str')} Uhr {walk_status}"
        )

        dep_diff = info.get("minutes_until_dep", 0)
        dep_status = f"(in {dep_diff} Min.)" if dep_diff > 0 else "(Abfahrt!)"
        self.stage_dep_lbl.configure(
            text=f"🚏 Abfahrt: {dep.real_time_str} Uhr {dep_status}"
        )

        if trip is not None and trip.arrival_real_str:
            self.stage_arrival_lbl.configure(
                text="🏁 "
                + tr("checkout_panel.transit_stage_arrival", "Ankunft {stop}: {time} Uhr").format(
                    stop=trip.arrival_stop or format_stop(self._applied_destination), time=trip.arrival_real_str
                )
            )
            if not self.stage_arrival_lbl.winfo_manager():
                self.stage_arrival_lbl.pack(fill="x", pady=PAD_TINY)
        elif self.stage_arrival_lbl.winfo_manager():
            self.stage_arrival_lbl.pack_forget()

        if self.transit_hint_lbl.winfo_manager():
            self.transit_hint_lbl.pack_forget()
        if not self.selected_transit_card.winfo_manager():
            self.selected_transit_card.pack(fill="x", padx=PAD_XS, pady=(PAD_XS, PAD_NONE), after=self.transit_card)

    def _show_transit_hint(self) -> None:
        """Hides the selection card and shows the double-click hint in its place."""
        if not hasattr(self, "selected_transit_card"):
            return
        if self.selected_transit_card.winfo_manager():
            self.selected_transit_card.pack_forget()
        if not self.transit_hint_lbl.winfo_manager():
            self.transit_hint_lbl.pack(fill="x", padx=PAD_SM, pady=(PAD_XS, PAD_NONE), after=self.transit_card)

    def _render_departures(self) -> None:
        from ui.widgets.ctk_tooltip import CTkTooltip

        for widget in self.transit_scroll.winfo_children():
            widget.destroy()

        if not self._transit_departures:
            if self._has_destination():
                empty_text = tr(
                    "checkout_panel.transit_no_trips",
                    "Keine Verbindungen nach {dest} gefunden. Stimmt das Ziel?",
                ).format(dest=format_stop(self._applied_destination))
            else:
                empty_text = tr("checkout_panel.transit_no_departures", "Aktuell keine Abfahrten gefunden.")
            no_dep_lbl = ctk.CTkLabel(
                self.transit_scroll,
                text=empty_text,
                wraplength=CHECKOUT_HINT_WRAPLENGTH,
                font=ctk.CTkFont(size=FONT_SIZE_SM),
                text_color=COLOR_MUTED_LABEL,
            )
            no_dep_lbl.pack(pady=PAD_MD)
            return

        limit = CHECKOUT_TAB_MAX_DEPARTURES if self.is_floating else CHECKOUT_STACK_MAX_DEPARTURES
        trips_by_key = {self._dep_key(t.departure): t for t in self._transit_trips} if self._has_destination() else {}
        for dep in self._transit_departures[:limit]:
            dep_key = f"{dep.line}_{dep.planned_time_str}_{dep.destination}"
            is_selected = (self._selected_dep_key == dep_key)

            row_bg = COLOR_TRANSIT_SELECTED_BG if is_selected else COLOR_CHECKOUT_CARD_BG
            row_bw = BORDER_WIDTH_TRANSIT_SELECTED if is_selected else 0
            row_bc = COLOR_TRANSIT_SELECTED_BORDER if is_selected else COLOR_CHECKOUT_BORDER

            row = ctk.CTkFrame(
                self.transit_scroll,
                fg_color=row_bg,
                border_width=row_bw,
                border_color=row_bc,
                corner_radius=CORNER_RADIUS_SM,
            )
            row.pack(fill="x", padx=PAD_XS, pady=PAD_XS)

            # Line badge
            trip = trips_by_key.get(dep_key)
            badge = ctk.CTkLabel(
                row,
                text=f" {' › '.join(trip.lines) if trip else dep.line} ",
                font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD),
                fg_color=COLOR_THEME_BTN,
                corner_radius=CORNER_RADIUS_SM,
                width=LABEL_WIDTH_TRANSIT_LINE,
            )
            badge.pack(side="left", padx=(PAD_SM, PAD_XS), pady=PAD_SM)

            # Destination & Platform
            info_box = ctk.CTkFrame(row, fg_color=COLOR_TRANSPARENT)
            info_box.pack(side="left", fill="x", expand=True, padx=PAD_XS)

            dest_text = dep.destination
            if trip is not None:
                dest_text = tr("checkout_panel.transit_trip_times", "{dep} → {arr} Uhr · {minutes} Min.").format(
                    dep=dep.real_time_str, arr=trip.arrival_real_str or "?", minutes=trip.duration_minutes
                )
            if is_selected:
                dest_text = f"{dest_text}  {tr('checkout_panel.transit_selected_badge', '🎯 Gewählt')}"

            dest_lbl = ctk.CTkLabel(
                info_box,
                text=dest_text,
                font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD),
                anchor="w",
            )
            dest_lbl.pack(fill="x")

            plat_str = f"{dep.platform}" if dep.platform else ""
            if trip is not None:
                # Times are in the line above; here: punctuality, changes, direction of the first bus
                punctual = (
                    f"+{dep.delay_minutes} Min."
                    if dep.delay_minutes > 0
                    else tr("checkout_panel.transit_status_ontime", "Pünktlich")
                )
                parts = [punctual, self._changes_text(trip.interchanges)]
                if dep.destination:
                    parts.append(
                        tr("checkout_panel.transit_trip_direction", "Ri. {dest}").format(dest=dep.destination)
                    )
                if plat_str:
                    parts.append(plat_str)
                time_str = " · ".join(parts)
                time_color = COLOR_TRANSIT_DELAY if dep.delay_minutes > 0 else COLOR_TRANSIT_ONTIME
            elif dep.delay_minutes > 0:
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

            CTkTooltip(row, tr("checkout_panel.transit_row_tooltip", "Doppelklick zum Auswählen dieser Fahrt für Wecker"))
            self._bind_double_click_recursive(
                row,
                lambda d=dep: self._on_departure_double_clicked(d),
            )

    def _check_commute_alarms(self) -> None:
        """Raises the pack / log-out / leave toasts for the departure the user selected."""
        if not self.settings.alarm_enabled:
            return

        from ui.widgets.toast_notification import ToastNotification

        # Alarms only run for a departure the user picked by double-click;
        # nothing is chosen or announced on their behalf.
        if not self._selected_departure:
            return
        self._update_selected_card()
        dep = self._selected_departure
        info = DingTransitService.calculate_leave_info(
            dep,
            walk_min=self.settings.walk_time_minutes,
            logout_min=self.settings.logout_time_minutes,
            pack_min=self.settings.pack_time_minutes,
            buffer_min=self.settings.buffer_time_minutes,
        )

        # Stage 1: Pack alarm
        if info.get("minutes_until_pack", 999) <= 0 and "pack" not in self._notified_stages:
            self._notified_stages.add("pack")
            total_rem = (
                self.settings.pack_time_minutes
                + self.settings.logout_time_minutes
                + self.settings.walk_time_minutes
            )
            title = tr("checkout_panel.transit_toast_pack_title", "🎒 Zeit zum Packen!")
            msg = tr(
                "checkout_panel.transit_toast_pack_msg",
                "In {minutes} Min. fährt Linie {line} nach {dest}. Bitte Sachen zusammenpacken.",
            ).format(
                minutes=total_rem,
                line=dep.line,
                dest=dep.destination,
            )
            ToastNotification(self.winfo_toplevel(), title=title, message=msg)

        # Stage 2: Logout alarm
        if info.get("minutes_until_logout", 999) <= 0 and "logout" not in self._notified_stages:
            self._notified_stages.add("logout")
            rem = self.settings.logout_time_minutes + self.settings.walk_time_minutes
            title = tr("checkout_panel.transit_toast_logout_title", "💻 Zeit zum Abmelden!")
            msg = tr(
                "checkout_panel.transit_toast_logout_msg",
                "In {minutes} Min. fährt Linie {line} nach {dest}. Bitte PC herunterfahren.",
            ).format(
                minutes=rem,
                line=dep.line,
                dest=dep.destination,
            )
            ToastNotification(self.winfo_toplevel(), title=title, message=msg)

        # Stage 3: Walk alarm
        if info.get("minutes_until_walk", 999) <= 0 and "walk" not in self._notified_stages:
            self._notified_stages.add("walk")
            title = tr("checkout_panel.transit_toast_walk_title", "🚶 Zeit zum Aufbrechen!")
            msg = tr(
                "checkout_panel.transit_toast_walk_msg",
                "Jetzt losgehen! Linie {line} nach {dest} fährt um {dep_time} Uhr.",
            ).format(
                line=dep.line,
                dest=dep.destination,
                dep_time=dep.real_time_str,
            )
            trip = self._selected_trip()
            if trip is not None and trip.arrival_real_str:
                msg = f"{msg} " + tr(
                    "checkout_panel.transit_toast_arrival", "Ankunft {stop}: {time} Uhr."
                ).format(stop=trip.arrival_stop or format_stop(self._applied_destination), time=trip.arrival_real_str)
            ToastNotification(self.winfo_toplevel(), title=title, message=msg)

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

        if self.is_floating:
            self.note_textbox = ctk.CTkTextbox(tab, font=ctk.CTkFont(size=FONT_SIZE_BODY))
            self.note_textbox.pack(fill="both", expand=True, padx=PAD_XS, pady=(PAD_XS, PAD_SM))
        else:
            self.note_textbox = ctk.CTkTextbox(tab, font=ctk.CTkFont(size=FONT_SIZE_BODY), height=CHECKOUT_STACK_NOTE_HEIGHT)
            self.note_textbox.pack(fill="x", padx=PAD_XS, pady=(PAD_XS, PAD_NONE))
        self.note_textbox.insert("1.0", self.settings.daily_note_text)
        self.note_textbox.bind("<KeyRelease>", self._on_note_key_release)
        from utils.smiley_utils import enable_smiley_shortcuts
        enable_smiley_shortcuts(self.note_textbox)

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
        section = getattr(self, "_sections", {}).get("note")
        if section is not None:
            section.set_title(title)
            return
        # CTkTabview internal segmented button rename
        try:
            seg = getattr(self.tabview, "_segmented_button", None)
            if seg is not None:
                btns = getattr(seg, "_buttons_dict", {})
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
        self.tomorrow_scroll = self._list_container(tab)
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

        elapsed_minutes, projected_end = self._compute_worktime()
        elapsed_hours = elapsed_minutes // 60
        elapsed_mins_rem = elapsed_minutes % 60

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
        self._run_in_background(lambda: WeatherService.fetch_weather(force_refresh=force), self._on_weather_data_loaded)

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

    def _run_in_background(self, work: Callable[[], Any], on_done: Callable[[Any], None]) -> None:
        """Runs work() in a daemon thread and hands its result to on_done on the Tk thread.

        The worker never touches Tk: tkinter may only be called from the main
        thread. The old workers called winfo_exists()/after() themselves, which
        raised "main thread is not in main loop" whenever no mainloop was running
        (tests, shutdown). The main thread polls the result instead.
        """
        results: queue.SimpleQueue[tuple[bool, Any]] = queue.SimpleQueue()

        def worker() -> None:
            try:
                results.put((True, work()))
            except Exception as e:  # never leave the poll loop waiting forever
                logger.warning("Background fetch failed: %s", e)
                results.put((False, None))

        def poll() -> None:
            self._background_polls.discard(poll_id[0])
            try:
                ok, value = results.get_nowait()
            except queue.Empty:
                poll_id[0] = self.after(CHECKOUT_BACKGROUND_POLL_MS, poll)
                self._background_polls.add(poll_id[0])
                return
            if ok:
                on_done(value)

        threading.Thread(target=worker, daemon=True).start()
        poll_id = [self.after(CHECKOUT_BACKGROUND_POLL_MS, poll)]
        self._background_polls.add(poll_id[0])

    def destroy(self) -> None:
        """Cancel background scheduled timers on destruction."""
        for job in list(getattr(self, "_background_polls", ())):
            try:
                self.after_cancel(job)
            except Exception:
                pass
        self._background_polls = set()
        if self._transit_refresh_job is not None:
            try:
                self.after_cancel(self._transit_refresh_job)
            except Exception:
                pass
            self._transit_refresh_job = None
        super().destroy()
