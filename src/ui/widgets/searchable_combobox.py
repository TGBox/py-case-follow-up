import customtkinter as ctk
from typing import Callable, Any


class SearchableCombobox(ctk.CTkFrame):
    """Searchable & scrollable dropdown picker widget for CustomTkinter."""

    def __init__(
        self,
        master: Any,
        values: list[str] | None = None,
        command: Callable[[str], None] | None = None,
        width: int = 380,
        height: int = 32,
        placeholder_text: str = "– Bitte auswählen –",
        **kwargs: Any
    ):
        super().__init__(master, fg_color="transparent", width=width, height=height, **kwargs)
        self.pack_propagate(False)

        self._values: list[str] = list(values) if values else []
        self._command = command
        self._selected_value: str = ""
        self.placeholder_text = placeholder_text
        self._popover: ctk.CTkToplevel | None = None

        # Display Button
        self.btn = ctk.CTkButton(
            self,
            text=self.placeholder_text,
            width=width,
            height=height,
            anchor="w",
            fg_color=("gray85", "gray25"),
            hover_color=("gray75", "gray32"),
            text_color=("black", "white"),
            font=ctk.CTkFont(size=12),
            command=self.toggle_popover,
        )
        self.btn.pack(fill="both", expand=True)

        if self._values:
            self.set_selected(self._values[0])

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
        btn_w = max(self.btn.winfo_width(), 360)
        btn_h = self.btn.winfo_height()

        pop_w = btn_w
        pop_h = min(280, max(120, len(self._values) * 32 + 45))
        pop_x = btn_x
        pop_y = btn_y + btn_h + 2

        self._popover.geometry(f"{pop_w}x{pop_h}+{pop_x}+{pop_y}")

        # Outer Frame
        outer = ctk.CTkFrame(
            self._popover,
            fg_color=("gray90", "gray18"),
            border_width=2,
            border_color="dodgerblue",
            corner_radius=6,
        )
        outer.pack(fill="both", expand=True)

        # Search Entry
        self.search_entry = ctk.CTkEntry(
            outer,
            placeholder_text="🔍 Buchstaben eintippen zum Suchen...",
            height=30,
            font=ctk.CTkFont(size=11),
        )
        self.search_entry.pack(fill="x", padx=6, pady=(6, 4))
        self.search_entry.bind("<KeyRelease>", self._on_search_changed)
        self.search_entry.bind("<Return>", self._on_enter_pressed)
        self.search_entry.bind("<Escape>", lambda e: self.close_popover())

        # Scrollable Options List
        self.options_scroll = ctk.CTkScrollableFrame(outer, fg_color="transparent")
        self.options_scroll.pack(fill="both", expand=True, padx=4, pady=(0, 6))

        from utils.ui_utils import enable_auto_hiding_scrollbar
        enable_auto_hiding_scrollbar(self.options_scroll)

        self._render_options(self._values)
        self.search_entry.focus_set()

        # Close popover when clicking outside
        self._popover.bind("<FocusOut>", self._on_focus_out)

    def _on_focus_out(self, event=None) -> None:
        if self._popover and self._popover.winfo_exists():
            # Check if focus moved to a child of popover
            focused = self._popover.focus_get()
            if not focused or not str(focused).startswith(str(self._popover)):
                self.after(100, self.close_popover)

    def close_popover(self) -> None:
        if self._popover and self._popover.winfo_exists():
            try:
                self._popover.destroy()
            except Exception:
                pass
            self._popover = None

    def _on_search_changed(self, event=None) -> None:
        query = self.search_entry.get().strip().lower()
        if not query:
            filtered = self._values
        else:
            filtered = [v for v in self._values if query in v.lower()]
        self._render_options(filtered)

    def _on_enter_pressed(self, event=None) -> None:
        query = self.search_entry.get().strip().lower()
        filtered = [v for v in self._values if query in v.lower()] if query else self._values
        if filtered:
            self._select_item(filtered[0])

    def _render_options(self, items: list[str]) -> None:
        for w in self.options_scroll.winfo_children():
            w.destroy()

        if not items:
            ctk.CTkLabel(
                self.options_scroll,
                text="Keine Praxen gefunden",
                font=ctk.CTkFont(size=11),
                text_color="gray",
            ).pack(pady=10)
            return

        for item in items:
            is_selected = item == self._selected_value
            fg = ("#2563eb", "#1d4ed8") if is_selected else "transparent"
            tc = "white" if is_selected else ("black", "white")

            btn = ctk.CTkButton(
                self.options_scroll,
                text=item,
                anchor="w",
                height=28,
                fg_color=fg,
                hover_color=("gray75", "gray35"),
                text_color=tc,
                font=ctk.CTkFont(size=11),
                command=lambda val=item: self._select_item(val),
            )
            btn.pack(fill="x", pady=1, padx=2)

    def _select_item(self, val: str) -> None:
        self.set_selected(val)
        self.close_popover()
        if self._command:
            self._command(val)
