"""Entry with live stop suggestions from the EFA stop finder.

Used for the trip destination in the checkout panel and on the end-of-day
settings page. Typing at least TRANSIT_STOP_SEARCH_MIN_CHARS characters
searches (debounced) and lists matching stops right under the entry;
clicking one fills the field and reports the stop through on_pick.
"""

from __future__ import annotations

import logging
import queue
import threading
from collections.abc import Callable
from typing import Any

import customtkinter as ctk

from constants import (
    CHECKOUT_BACKGROUND_POLL_MS,
    COLOR_PANEL_BG,
    COLOR_PANEL_BORDER,
    COLOR_SETTINGS_NAV_HOVER,
    COLOR_SETTINGS_NAV_TEXT,
    CORNER_RADIUS_MD,
    PAD_NONE,
    PAD_TINY,
    PAD_XS,
    TRANSIT_STOP_SEARCH_DEBOUNCE_MS,
    TRANSIT_STOP_SEARCH_MIN_CHARS,
)
from services.ding_transit_service import DingTransitService, TransitStop

logger = logging.getLogger("SupportCockpit.transit")


def format_stop(stop: dict[str, str] | TransitStop | None) -> str:
    """'Name, Ort' as shown in the field; just the name when no place is known."""
    if stop is None:
        return ""
    if isinstance(stop, TransitStop):
        name, place = stop.name, stop.place
    else:
        name, place = stop.get("name", ""), stop.get("place", "")
    name, place = (name or "").strip(), (place or "").strip()
    return f"{name}, {place}" if name and place else name


class StopSearchField(ctk.CTkFrame):
    """A CTkEntry plus a suggestion list that opens below it."""

    def __init__(
        self,
        master: Any,
        on_pick: Callable[[TransitStop], None] | None = None,
        on_status: Callable[[str], None] | None = None,
        placeholder_text: str = "",
        entry_width: int = 140,
        entry_height: int = 28,
        font: Any = None,
        suggestion_height: int = 26,
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)
        self.on_pick = on_pick
        # Called with "searching" / "none" / "error" / "results" so the owner can show a hint
        self.on_status = on_status
        self._suggestion_height = suggestion_height
        self._request_id = 0
        self._last_query = ""
        self._poll_jobs: set[str] = set()
        self._buttons: list[ctk.CTkButton] = []

        entry_kwargs: dict[str, Any] = {"width": entry_width, "height": entry_height, "placeholder_text": placeholder_text}
        if font is not None:
            entry_kwargs["font"] = font
        self.entry = ctk.CTkEntry(self, **entry_kwargs)
        self.entry.pack(fill="x")
        self.entry.bind("<KeyRelease>", self._on_typed, add="+")

        self.suggestions = ctk.CTkFrame(
            self, fg_color=COLOR_PANEL_BG, border_width=1, border_color=COLOR_PANEL_BORDER, corner_radius=CORNER_RADIUS_MD
        )

    # -- value -----------------------------------------------------------
    def get(self) -> str:
        return self.entry.get().strip()

    def set_text(self, text: str) -> None:
        self.entry.delete(0, "end")
        if text:
            self.entry.insert(0, text)
        self._last_query = text.strip()
        self.hide_suggestions()

    # -- search ----------------------------------------------------------
    def _on_typed(self, event: Any = None) -> None:
        keysym = getattr(event, "keysym", "")
        if keysym in ("Return", "KP_Enter", "Tab", "Up", "Down", "Left", "Right"):
            return
        if keysym == "Escape":
            self.hide_suggestions()
            return
        query = self.get()
        if len(query) < TRANSIT_STOP_SEARCH_MIN_CHARS:
            self.hide_suggestions()
            return
        from utils.ui_utils import debounce

        debounce(self.entry, "stop_search_field", TRANSIT_STOP_SEARCH_DEBOUNCE_MS, self._start_search)

    def _start_search(self) -> None:
        query = self.get()
        if len(query) < TRANSIT_STOP_SEARCH_MIN_CHARS or query == self._last_query:
            return
        self._last_query = query
        self._request_id += 1
        request_id = self._request_id
        self._report("searching")
        results: queue.SimpleQueue[Any] = queue.SimpleQueue()

        def worker() -> None:
            try:
                results.put(DingTransitService.find_stops(query))
            except Exception as e:  # never leave the poll waiting
                logger.warning("Stop search failed: %s", e)
                results.put(None)

        def poll() -> None:
            self._poll_jobs.discard(job[0])
            try:
                found = results.get_nowait()
            except queue.Empty:
                job[0] = self.after(CHECKOUT_BACKGROUND_POLL_MS, poll)
                self._poll_jobs.add(job[0])
                return
            self._on_results(request_id, found)

        threading.Thread(target=worker, daemon=True).start()
        job = [self.after(CHECKOUT_BACKGROUND_POLL_MS, poll)]
        self._poll_jobs.add(job[0])

    def _on_results(self, request_id: int, found: list[TransitStop] | None) -> None:
        if request_id != self._request_id or not self.winfo_exists():
            return
        if found is None:
            self.hide_suggestions()
            self._report("error")
        elif not found:
            self.hide_suggestions()
            self._report("none")
        else:
            self.show_suggestions(found)
            self._report("results")

    def _report(self, status: str) -> None:
        if self.on_status:
            self.on_status(status)

    # -- suggestion list -------------------------------------------------
    def show_suggestions(self, stops: list[TransitStop]) -> None:
        for btn in self._buttons:
            btn.destroy()
        self._buttons = []
        for stop in stops:
            btn = ctk.CTkButton(
                self.suggestions,
                text=format_stop(stop),
                anchor="w",
                height=self._suggestion_height,
                fg_color="transparent",
                hover_color=COLOR_SETTINGS_NAV_HOVER,
                text_color=COLOR_SETTINGS_NAV_TEXT,
                command=lambda s=stop: self._pick(s),
            )
            btn.pack(fill="x", padx=PAD_XS, pady=PAD_TINY)
            self._buttons.append(btn)
        if not self.suggestions.winfo_manager():
            self.suggestions.pack(fill="x", pady=(PAD_XS, PAD_NONE))

    def hide_suggestions(self) -> None:
        if self.suggestions.winfo_manager():
            self.suggestions.pack_forget()

    def _pick(self, stop: TransitStop) -> None:
        self.set_text(format_stop(stop))
        if self.on_pick:
            self.on_pick(stop)

    def destroy(self) -> None:
        for job in list(self._poll_jobs):
            try:
                self.after_cancel(job)
            except Exception:
                pass
        self._poll_jobs = set()
        super().destroy()
