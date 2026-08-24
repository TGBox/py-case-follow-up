import customtkinter as ctk
from typing import Callable
from models.case import Case, TimelineEntry
from enums import Channel, get_channel_display, get_channel_val_from_display, CHANNEL_DISPLAY
from utils.datetime_utils import now_iso


class TimelineWidget(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        author_name: str,
        on_timeline_updated: Callable[[list[TimelineEntry]], None],
        on_open_snippet_picker: Callable[[Callable[[str], None]], None] | None = None,
    ):
        super().__init__(parent)
        self.author_name = author_name
        self.on_timeline_updated = on_timeline_updated
        self.on_open_snippet_picker = on_open_snippet_picker
        self.timeline_entries: list[TimelineEntry] = []

        self.create_widgets()

    def create_widgets(self):
        # Header
        ctk.CTkLabel(self, text="Verlauf & Timeline Notizen", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))

        # Scrollable list
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        from utils.ui_utils import enable_auto_hiding_scrollbar
        enable_auto_hiding_scrollbar(self.scroll_frame)

        # Input Area for New Note
        input_frame = ctk.CTkFrame(self)
        input_frame.pack(fill="x", padx=5, pady=5)

        ctrl_row = ctk.CTkFrame(input_frame, fg_color="transparent")
        ctrl_row.pack(fill="x", padx=5, pady=(5, 2))

        ctk.CTkLabel(ctrl_row, text="Neue Notiz hinzufügen:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")

        snip_btn = ctk.CTkButton(
            ctrl_row,
            text="🧩 Textbaustein",
            width=110,
            fg_color="gray30",
            hover_color="darkmagenta",
            command=self.on_click_snippet,
        )
        snip_btn.pack(side="right")

        self.channel_combo = ctk.CTkOptionMenu(input_frame, values=list(CHANNEL_DISPLAY.values()), width=200)
        self.channel_combo.set(get_channel_display(Channel.PHONE_INBOUND.value))
        self.channel_combo.pack(anchor="w", padx=5, pady=(0, 5))

        self.note_textbox = ctk.CTkTextbox(input_frame, height=60)
        self.note_textbox.pack(fill="x", padx=5, pady=(0, 5))

        add_btn = ctk.CTkButton(input_frame, text="+ Notiz Hinzufügen", command=self.on_add_note, width=140)
        add_btn.pack(side="right", padx=5, pady=(0, 5))

    def on_click_snippet(self):
        if self.on_open_snippet_picker:
            self.on_open_snippet_picker(self.insert_snippet_text)

    def insert_snippet_text(self, text: str):
        if text:
            curr_text = self.note_textbox.get("1.0", "end-1c")
            sep = "\n" if curr_text.strip() else ""
            self.note_textbox.insert("end", f"{sep}{text}")

    def load_timeline(self, entries: list[TimelineEntry]):
        self.timeline_entries = list(entries)
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not self.timeline_entries:
            ctk.CTkLabel(self.scroll_frame, text="Keine Notizen vorhanden.").pack(pady=10)
            return

        for entry in reversed(self.timeline_entries):
            card = ctk.CTkFrame(self.scroll_frame, fg_color=("gray85", "gray20"), corner_radius=6)
            card.pack(fill="x", pady=4, padx=4)

            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=8, pady=(4, 2))

            header_str = f"👤 {entry.author}  [{get_channel_display(entry.channel)}]"
            ctk.CTkLabel(top_row, text=header_str, font=ctk.CTkFont(weight="bold", size=11)).pack(side="left")
            from utils.datetime_utils import format_german_datetime
            formatted_ts = format_german_datetime(entry.timestamp, include_seconds=True)
            ctk.CTkLabel(top_row, text=formatted_ts, font=ctk.CTkFont(size=10), text_color=("gray40", "gray70")).pack(side="right")

            note_lbl = ctk.CTkLabel(card, text=entry.note, anchor="w", justify="left", font=ctk.CTkFont(size=12), wraplength=300)
            note_lbl.pack(fill="x", padx=10, pady=(0, 6))

            if entry.status_change:
                sc_lbl = ctk.CTkLabel(card, text=f"Status: {entry.status_change}", font=ctk.CTkFont(size=10), text_color="dodgerblue")
                sc_lbl.pack(anchor="w", padx=10, pady=(0, 4))

    def on_add_note(self):
        text = self.note_textbox.get("1.0", "end-1c").strip()
        if not text:
            return

        channel_val = get_channel_val_from_display(self.channel_combo.get())
        new_entry = TimelineEntry(
            timestamp=now_iso(),
            author=self.author_name,
            channel=channel_val,
            note=text,
        )
        self.timeline_entries.append(new_entry)
        self.note_textbox.delete("1.0", "end")
        self.load_timeline(self.timeline_entries)
        self.on_timeline_updated(self.timeline_entries)
