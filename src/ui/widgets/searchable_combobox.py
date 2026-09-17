import customtkinter as ctk
from typing import Any
from collections.abc import Callable

from constants import (
    BORDER_WIDTH_CARD,
    COLOR_BORDER_POPOVER,
    COLOR_COMBO_BTN_BG,
    COLOR_COMBO_BTN_HOVER,
    COLOR_ITEM_HOVER,
    COLOR_ITEM_SELECTED,
    COLOR_MUTED_LABEL,
    COLOR_POPOVER_BG,
    COLOR_SUBTITLE_MUTED,
    COLOR_TEXT_PRIMARY,
    COMBO_DEFAULT_HEIGHT,
    COMBO_DEFAULT_WIDTH,
    CORNER_RADIUS_MD,
    CORNER_RADIUS_SM,
    CURSOR_HAND,
    DEBOUNCE_KEY_COMBOBOX_SEARCH,
    DELAY_FOCUS_RESTORE_MS,
    DELAY_POPOVER_CLOSE_MS,
    FONT_SIZE_BODY,
    FONT_SIZE_SM,
    FONT_SIZE_XS,
    HEIGHT_COMBO_OPTION,
    HEIGHT_SEARCH_ENTRY,
    PAD_MD,
    PAD_SM,
    PAD_TINY,
    PAD_XL,
    PAD_XS,
    POPOVER_HEADER_HEIGHT,
    POPOVER_ITEM_HEIGHT,
    POPOVER_MAX_HEIGHT,
    POPOVER_MIN_HEIGHT,
    POPOVER_MIN_WIDTH,
    SEARCH_DEBOUNCE_MS,
)


class SearchableCombobox(ctk.CTkFrame):
    """Searchable & scrollable dropdown picker widget for CustomTkinter."""

    def __init__(
        self,
        master: Any,
        values: list[str] | None = None,
        command: Callable[[str], None] | None = None,
        width: int = COMBO_DEFAULT_WIDTH,
        height: int = COMBO_DEFAULT_HEIGHT,
        placeholder_text: str | None = None,
        search_index: dict[str, str] | None = None,
        summary_provider: Callable[[str, str], str | None] | None = None,
        **kwargs: Any
    ):
        """search_index maps a display value to extra text that should also be
        searchable (contacts, website, customer numbers - anything not visible in
        the label itself). summary_provider returns a short "matched here" line
        for a value, so a hit in one of those hidden fields is explained instead
        of looking like an unrelated entry.

        Both are optional: without them the widget behaves exactly as before,
        matching on the display strings and rendering plain buttons.
        """
        super().__init__(master, fg_color="transparent", width=width, height=height, **kwargs)
        self.pack_propagate(False)

        from services.i18n_service import tr
        self._values: list[str] = list(values) if values else []
        self._command = command
        self._selected_value: str = ""
        self._search_index: dict[str, str] = dict(search_index) if search_index else {}
        self._summary_provider = summary_provider
        self.placeholder_text = placeholder_text if placeholder_text is not None else tr("common.please_select", "– Bitte auswählen –")
        self._popover: ctk.CTkToplevel | None = None
        self._focus_next: Any | None = None

        # Display Button
        self.btn = ctk.CTkButton(
            self,
            text=self.placeholder_text,
            width=width,
            height=height,
            anchor="w",
            fg_color=COLOR_COMBO_BTN_BG,
            hover_color=COLOR_COMBO_BTN_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            font=ctk.CTkFont(size=FONT_SIZE_BODY),
            command=self.toggle_popover,
        )
        self.btn.pack(fill="both", expand=True)

        if self._values:
            self.set_selected(self._values[0])

    def set_next_focus_widget(self, widget: Any) -> None:
        """Widget that should receive the keyboard focus after an item was picked.

        Without this the focus lands back on the picker button, which is fine but
        costs the user an extra click on the field they want to fill in next.
        """
        self._focus_next = widget

    def set_search_index(self, search_index: dict[str, str] | None) -> None:
        """Replaces the hidden searchable text, e.g. after the value list changed."""
        self._search_index = dict(search_index) if search_index else {}

    @property
    def _rich_results(self) -> bool:
        """Rich rows are only used where extra search data was actually supplied."""
        return bool(self._search_index or self._summary_provider)

    def _haystack(self, value: str) -> str:
        extra = self._search_index.get(value, "")
        return f"{value} {extra}".lower() if extra else value.lower()

    def _matches(self, value: str, query_lower: str) -> bool:
        return query_lower in self._haystack(value)

    def _filtered(self, query_lower: str) -> list[str]:
        if not query_lower:
            return self._values
        return [v for v in self._values if self._matches(v, query_lower)]

    def set_values(self, values: list[str], default_value: str | None = None) -> None:
        self._values = list(values)
        if default_value and default_value in self._values:
            self.set_selected(default_value)
        elif self._values:
            self.set_selected(self._values[0])
        else:
            self.set_selected("")

    def set_selected(self, val: str) -> None:
        self._selected_value = val
        display_str = val if val else self.placeholder_text
        self.btn.configure(text=f"  {display_str}  ▼")

    def set(self, val: str) -> None:
        """Alias for set_selected to ensure CTkComboBox/CTkOptionMenu API compatibility."""
        self.set_selected(val)

    def get(self) -> str:
        return self._selected_value

    def toggle_popover(self) -> None:
        if self._popover and self._popover.winfo_exists():
            self.close_popover()
        else:
            self.open_popover()

    def open_popover(self) -> None:
        if not self._values:
            return

        top_app = self.winfo_toplevel()

        self._popover = ctk.CTkToplevel(self)
        self._popover.overrideredirect(True)
        self._popover.attributes("-topmost", True)
        self._popover.transient(top_app)

        # Position popover directly below the button
        self.update_idletasks()
        btn_x = self.btn.winfo_rootx()
        btn_y = self.btn.winfo_rooty()
        btn_w = max(self.btn.winfo_width(), POPOVER_MIN_WIDTH)
        btn_h = self.btn.winfo_height()

        pop_w = btn_w
        pop_h = min(POPOVER_MAX_HEIGHT, max(POPOVER_MIN_HEIGHT, len(self._values) * POPOVER_ITEM_HEIGHT + POPOVER_HEADER_HEIGHT))
        pop_x = btn_x
        pop_y = btn_y + btn_h + PAD_XS

        self._popover.geometry(f"{pop_w}x{pop_h}+{pop_x}+{pop_y}")

        # Outer Frame
        outer = ctk.CTkFrame(
            self._popover,
            fg_color=COLOR_POPOVER_BG,
            border_width=BORDER_WIDTH_CARD,
            border_color=COLOR_BORDER_POPOVER,
            corner_radius=CORNER_RADIUS_MD,
        )
        outer.pack(fill="both", expand=True)

        # Search Entry
        from services.i18n_service import tr

        self.search_entry = ctk.CTkEntry(
            outer,
            placeholder_text=tr("searchable_combo.placeholder", "🔍 Buchstaben eintippen zum Suchen..."),
            height=HEIGHT_SEARCH_ENTRY,
            font=ctk.CTkFont(size=FONT_SIZE_SM),
        )
        self.search_entry.pack(fill="x", padx=CORNER_RADIUS_MD, pady=(CORNER_RADIUS_MD, PAD_SM))
        self.search_entry.bind("<KeyRelease>", self._on_search_keyrelease)
        self.search_entry.bind("<Return>", self._on_enter_pressed)
        self.search_entry.bind("<Escape>", lambda e: self.close_popover())  # focus returns to the picker button

        # Scrollable Options List
        self.options_scroll = ctk.CTkScrollableFrame(outer, fg_color="transparent")
        self.options_scroll.pack(fill="both", expand=True, padx=PAD_SM, pady=(0, CORNER_RADIUS_MD))

        from utils.ui_utils import enable_auto_hiding_scrollbar
        enable_auto_hiding_scrollbar(self.options_scroll)

        self._render_options(self._values)

        # An overrideredirect toplevel is not activated by Windows on its own,
        # so claim the keyboard explicitly - otherwise typing in the search
        # field silently goes to the window underneath.
        self._activate_popover()

        # Close popover when clicking outside
        self._popover.bind("<FocusOut>", self._on_focus_out)

    def _activate_popover(self) -> None:
        def _do():
            pop = self._popover
            if pop is None or not pop.winfo_exists():
                return
            try:
                pop.lift()
                pop.focus_force()
                self.search_entry.focus_set()
            except Exception:
                pass

        try:
            self.after(DELAY_FOCUS_RESTORE_MS, _do)
        except Exception:
            _do()

    def _on_focus_out(self, event=None) -> None:
        if self._popover and self._popover.winfo_exists():
            # Check if focus moved to a child of popover
            focused = self._popover.focus_get()
            if not focused or not str(focused).startswith(str(self._popover)):
                # Focus went somewhere else on purpose (another field or even
                # another application) - just close, never pull it back.
                self.after(DELAY_POPOVER_CLOSE_MS, lambda: self.close_popover(restore_focus=False))

    def close_popover(self, restore_focus: bool = True, focus_target: Any | None = None) -> None:
        # Das Suchfeld gehoert dem Popover, die Verzoegerung haengt aber am
        # Widget, das weiterlebt. Ohne Abbruch liefe die wartende Suche nach
        # dem Schliessen auf ein zerstoertes Eingabefeld.
        from utils.ui_utils import cancel_debounce
        cancel_debounce(self, DEBOUNCE_KEY_COMBOBOX_SEARCH)

        pop = self._popover
        self._popover = None

        top = None
        prev_grab = None
        if pop is not None and pop.winfo_exists():
            try:
                top = self.winfo_toplevel()
                prev_grab = top.grab_current()
            except Exception:
                top = None
            try:
                pop.destroy()
            except Exception:
                pass

        if restore_focus and top is not None:
            self._restore_parent_focus(top, prev_grab, focus_target)

    def _restore_parent_focus(self, top: Any, prev_grab: Any, focus_target: Any | None) -> None:
        """Hands the keyboard back to the owning window after the popover died.

        On Windows the destroyed overrideredirect popover leaves the dialog
        without keyboard activation: mouse clicks still arrive, but entries
        ignore every keystroke until the user clicks another window and back.
        Re-activating the toplevel (and re-arming a modal grab that was lost
        with the popover) restores normal typing right away.
        """
        def _do():
            try:
                if not top.winfo_exists():
                    return
                top.lift()
                top.focus_force()
            except Exception:
                pass

            try:
                if prev_grab is not None and not top.grab_current():
                    prev_grab.grab_set()
            except Exception:
                pass

            target = focus_target
            try:
                if target is None or not target.winfo_exists():
                    target = self.btn
            except Exception:
                target = self.btn

            try:
                target.focus_set()
            except Exception:
                pass

        try:
            self.after(DELAY_FOCUS_RESTORE_MS, _do)
        except Exception:
            _do()

    def _on_search_keyrelease(self, event=None) -> None:
        """Wartet die Tipppause ab, statt bei jedem Buchstaben neu zu filtern."""
        from utils.ui_utils import debounce
        debounce(self, DEBOUNCE_KEY_COMBOBOX_SEARCH, SEARCH_DEBOUNCE_MS, self._on_search_changed)

    def _on_search_changed(self, event=None) -> None:
        raw_query = self.search_entry.get().strip()
        self._render_options(self._filtered(raw_query.lower()), raw_query)

    def _on_enter_pressed(self, event=None) -> None:
        filtered = self._filtered(self.search_entry.get().strip().lower())
        if filtered:
            self._select_item(filtered[0])

    def _render_options(self, items: list[str], query: str = "") -> None:
        for w in self.options_scroll.winfo_children():
            w.destroy()

        if not items:
            from services.i18n_service import tr

            ctk.CTkLabel(
                self.options_scroll,
                text=tr("searchable_combo.no_results", "Keine Praxen gefunden"),
                font=ctk.CTkFont(size=FONT_SIZE_SM),
                text_color=COLOR_MUTED_LABEL,
            ).pack(pady=PAD_MD + PAD_XS)
            return

        if query and self._rich_results:
            self._render_rich_options(items, query)
            return

        for item in items:
            is_selected = item == self._selected_value
            fg = COLOR_ITEM_SELECTED if is_selected else "transparent"
            tc = "white" if is_selected else COLOR_TEXT_PRIMARY

            btn = ctk.CTkButton(
                self.options_scroll,
                text=item,
                anchor="w",
                height=HEIGHT_COMBO_OPTION,
                fg_color=fg,
                hover_color=COLOR_ITEM_HOVER,
                text_color=tc,
                font=ctk.CTkFont(size=FONT_SIZE_SM),
                command=lambda val=item: self._select_item(val),
            )
            btn.pack(fill="x", pady=PAD_TINY, padx=PAD_XS)

    def _render_rich_options(self, items: list[str], query: str) -> None:
        """Renders one row per hit with the matched text highlighted.

        A hit in a hidden field (a contact, the website, a VM number) gets a
        second line naming what actually matched - otherwise the row looks like
        it has nothing to do with the query the user typed.
        """
        from utils.ui_utils import create_highlighted_label, bind_mouse_wheel_to_canvas

        for item in items:
            is_selected = item == self._selected_value
            row_bg = COLOR_ITEM_SELECTED if is_selected else COLOR_POPOVER_BG
            text_col = ("white", "white") if is_selected else COLOR_TEXT_PRIMARY

            row = ctk.CTkFrame(self.options_scroll, fg_color=row_bg, corner_radius=CORNER_RADIUS_SM, cursor=CURSOR_HAND)
            row.pack(fill="x", pady=PAD_TINY, padx=PAD_XS)

            def on_click(_event=None, val=item):
                self._select_item(val)

            row.bind("<Button-1>", on_click)

            create_highlighted_label(
                row,
                text=item,
                query=query,
                font=ctk.CTkFont(size=FONT_SIZE_SM),
                text_color=text_col,
                bg_color=row_bg,
                wrap="none",
                on_click=on_click,
                scroll_frame=self.options_scroll,
            ).pack(fill="x", anchor="w", padx=PAD_MD, pady=(PAD_SM, 0))

            summary = None
            if self._summary_provider is not None:
                try:
                    summary = self._summary_provider(item, query)
                except Exception:
                    summary = None

            if summary:
                create_highlighted_label(
                    row,
                    text=f"↳ {summary}",
                    query=query,
                    font=ctk.CTkFont(size=FONT_SIZE_XS),
                    text_color=COLOR_SUBTITLE_MUTED if not is_selected else ("white", "white"),
                    bg_color=row_bg,
                    wrap="word",
                    on_click=on_click,
                    scroll_frame=self.options_scroll,
                ).pack(fill="x", anchor="w", padx=(PAD_XL, PAD_MD), pady=(0, PAD_SM))
            else:
                ctk.CTkFrame(row, fg_color="transparent", height=PAD_SM).pack()

            bind_mouse_wheel_to_canvas(row, self.options_scroll)

    def _select_item(self, val: str) -> None:
        self.set_selected(val)
        self.close_popover(focus_target=self._focus_next)
        if self._command:
            self._command(val)

    def refresh_ui_labels(self):
        from services.i18n_service import tr
        self.placeholder_text = tr("common.please_select", "– Bitte auswählen –")
        if not self._selected_value:
            self.btn.configure(text=f"  {self.placeholder_text}  ▼")
