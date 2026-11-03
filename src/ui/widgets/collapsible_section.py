"""A titled block whose body can be folded away.

Used in the settings dialog to keep rarely touched options (advanced push
features, the commute block of the end-of-day panel) out of sight until they
are needed. The body is a normal frame: callers pack or grid their widgets
into ``section.body``.
"""

from typing import Any
from collections.abc import Callable

import customtkinter as ctk

from constants import (
    COLOR_SETTINGS_NAV_HOVER,
    COLOR_SETTINGS_NAV_TEXT,
    COLOR_TRANSPARENT,
    FONT_SIZE_BODY,
    FONT_WEIGHT_BOLD,
    ICON_CHEVRON_COLLAPSED,
    ICON_CHEVRON_EXPANDED,
    PAD_MD,
    PAD_NONE,
    PAD_SM,
    PAD_XS,
)


class CollapsibleSection(ctk.CTkFrame):
    """Header button plus a body frame that is shown or hidden on click."""

    def __init__(
        self,
        master: Any,
        title: str,
        expanded: bool = False,
        on_toggle: Callable[[bool], None] | None = None,
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("fg_color", COLOR_TRANSPARENT)
        super().__init__(master, **kwargs)
        self._expanded = expanded
        self._on_toggle = on_toggle

        self.header_btn = ctk.CTkButton(
            self,
            text=self._header_text(title),
            anchor="w",
            fg_color=COLOR_TRANSPARENT,
            hover_color=COLOR_SETTINGS_NAV_HOVER,
            text_color=COLOR_SETTINGS_NAV_TEXT,
            font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
            command=self.toggle,
        )
        self.header_btn.pack(fill="x", pady=(PAD_NONE, PAD_XS))
        self._title = title

        self.body = ctk.CTkFrame(self, fg_color=COLOR_TRANSPARENT)
        if expanded:
            self._pack_body()

    def _header_text(self, title: str) -> str:
        chevron = ICON_CHEVRON_EXPANDED if self._expanded else ICON_CHEVRON_COLLAPSED
        return f"{chevron}  {title}"

    def _pack_body(self) -> None:
        self.body.pack(fill="x", padx=(PAD_MD + PAD_SM, PAD_NONE), pady=(PAD_NONE, PAD_SM))

    @property
    def expanded(self) -> bool:
        return self._expanded

    def set_title(self, title: str) -> None:
        self._title = title
        self.header_btn.configure(text=self._header_text(title))

    def set_expanded(self, expanded: bool) -> None:
        if expanded == self._expanded:
            return
        self._expanded = expanded
        if expanded:
            self._pack_body()
        else:
            self.body.pack_forget()
        self.header_btn.configure(text=self._header_text(self._title))
        if self._on_toggle:
            self._on_toggle(expanded)

    def toggle(self) -> None:
        self.set_expanded(not self._expanded)
