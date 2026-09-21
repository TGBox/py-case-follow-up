import customtkinter as ctk
from typing import Any
from collections.abc import Callable
from models.case import TimelineEntry
from enums import Channel, get_channel_display, get_channel_val_from_display, CHANNEL_DISPLAY
from constants import (
    BTN_WIDTH_ACTION,
    BTN_WIDTH_SM,
    COLOR_BORDER_DARK,
    COLOR_CARD_BG,
    COLOR_CARD_BORDER,
    COLOR_INFO,
    COLOR_MUTED_GRAY_FG,
    COLOR_MUTED_LABEL,
    COLOR_PURPLE_DARK,
    COLOR_SUBTITLE_MUTED,
    COLOR_TEXT_BODY,
    COMBO_WIDTH_SM,
    CORNER_RADIUS_MD,
    CORNER_RADIUS_XS,
    FONT_SIZE_BODY,
    FONT_SIZE_SM,
    FONT_SIZE_SUBTITLE,
    FONT_SIZE_XS,
    LABEL_HEIGHT_MD,
    LABEL_HEIGHT_SM,
    PAD_MD,
    PAD_NONE,
    PAD_SM,
    PAD_XS,
    TEXTBOX_HEIGHT_SM,
    TIMELINE_NOTE_MAX_DISPLAY_LINES,
    USER_COLOR_TILE_SIZE,
)
from utils.datetime_utils import now_iso, format_german_date, format_german_time


class TimelineWidget(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        author_name: str,
        on_timeline_updated: Callable[[list[TimelineEntry]], None],
        on_open_snippet_picker: Callable[[Callable[[str], None]], None] | None = None,
        user_color: str | None = None,
        color_marker_enabled: bool = False,
    ):
        super().__init__(parent)
        self.author_name = author_name
        self.on_timeline_updated = on_timeline_updated
        self.on_open_snippet_picker = on_open_snippet_picker
        self.user_color = user_color
        self.color_marker_enabled = color_marker_enabled
        self.timeline_entries: list[TimelineEntry] = []

        self.create_widgets()

    def set_user_color_settings(self, user_color: str | None, color_marker_enabled: bool):
        self.user_color = user_color
        self.color_marker_enabled = color_marker_enabled
        if self.timeline_entries:
            self.load_timeline(self.timeline_entries)

    def create_widgets(self):
        from services.i18n_service import tr

        # Header
        self.hdr_lbl = ctk.CTkLabel(self, text=tr("cockpit.timeline_title", "Verlauf & Timeline Notizen"), font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight="bold"))
        self.hdr_lbl.pack(anchor="w", padx=PAD_MD, pady=(PAD_MD, PAD_SM))

        # Scrollable list
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=PAD_SM, pady=PAD_SM)
        from utils.ui_utils import enable_auto_hiding_scrollbar
        enable_auto_hiding_scrollbar(self.scroll_frame)

        # Input Area for New Note
        input_frame = ctk.CTkFrame(self)
        input_frame.pack(fill="x", padx=PAD_SM, pady=PAD_SM)

        ctrl_row = ctk.CTkFrame(input_frame, fg_color="transparent")
        ctrl_row.pack(fill="x", padx=PAD_SM, pady=(PAD_SM, PAD_XS))

        self.ctrl_lbl = ctk.CTkLabel(ctrl_row, text=tr("cockpit.add_new_note", "Neue Notiz hinzufügen:"), font=ctk.CTkFont(size=FONT_SIZE_SM, weight="bold"))
        self.ctrl_lbl.pack(side="left")

        self.snip_btn = ctk.CTkButton(
            ctrl_row,
            text=tr("cockpit.snippets_btn", "❖ Textbaustein"),
            width=BTN_WIDTH_SM + 10,
            fg_color=COLOR_MUTED_GRAY_FG,
            hover_color=COLOR_PURPLE_DARK,
            command=self.on_click_snippet,
        )
        self.snip_btn.pack(side="right")

        self.channel_combo = ctk.CTkOptionMenu(input_frame, values=[get_channel_display(c) for c in CHANNEL_DISPLAY], width=COMBO_WIDTH_SM)
        self.channel_combo.set(get_channel_display(Channel.PHONE_INBOUND.value))
        self.channel_combo.pack(anchor="w", padx=PAD_SM, pady=(PAD_NONE, PAD_SM))

        self.note_textbox = ctk.CTkTextbox(input_frame, height=TEXTBOX_HEIGHT_SM)
        self.note_textbox.pack(fill="x", padx=PAD_SM, pady=(PAD_NONE, PAD_SM))

        from utils.ui_utils import enable_textbox_cursor_autoscroll
        enable_textbox_cursor_autoscroll(self.note_textbox)

        self.add_btn = ctk.CTkButton(input_frame, text=tr("cockpit.add_note_btn", "+ Notiz Hinzufügen"), command=self.on_add_note, width=BTN_WIDTH_ACTION)
        self.add_btn.pack(side="right", padx=PAD_SM, pady=(PAD_NONE, PAD_SM))

    def refresh_ui_labels(self):
        from services.i18n_service import tr
        if hasattr(self, "hdr_lbl"):
            self.hdr_lbl.configure(text=tr("cockpit.timeline_title", "Verlauf & Timeline Notizen"))
        if hasattr(self, "ctrl_lbl"):
            self.ctrl_lbl.configure(text=tr("cockpit.add_new_note", "Neue Notiz hinzufügen:"))
        if hasattr(self, "snip_btn"):
            self.snip_btn.configure(text=tr("cockpit.snippets_btn", "❖ Textbaustein"))
        if hasattr(self, "add_btn"):
            self.add_btn.configure(text=tr("cockpit.add_note_btn", "+ Notiz Hinzufügen"))
        if hasattr(self, "channel_combo"):
            curr_val = get_channel_val_from_display(self.channel_combo.get())
            self.channel_combo.configure(values=[get_channel_display(c) for c in CHANNEL_DISPLAY])
            self.channel_combo.set(get_channel_display(curr_val))
        self.load_timeline(self.timeline_entries)

    def on_click_snippet(self):
        if self.on_open_snippet_picker:
            self.on_open_snippet_picker(self.insert_snippet_text)

    def insert_snippet_text(self, text: str):
        if text:
            curr_text = self.note_textbox.get("1.0", "end-1c")
            sep = "\n" if curr_text.strip() else ""
            self.note_textbox.insert("end", f"{sep}{text}")

    @staticmethod
    def _enable_text_selection(note_txt: Any) -> None:
        """Lets a read-only note be selected and copied.

        create_highlighted_label leaves the widget disabled and takefocus=0, and
        Tk's own Button-1 binding only calls focus on a Text whose state is
        normal. Selecting with the mouse already works while disabled - the
        selection tag is not an edit - but without focus the Ctrl+C that follows
        goes somewhere else, so the note could be highlighted and not copied.
        """
        def _focus(_event: Any = None) -> None:
            try:
                note_txt.focus_set()
            except Exception:
                pass

        note_txt.bind("<Button-1>", _focus, add="+")

    def load_timeline(self, entries: list[TimelineEntry]):
        from utils.ui_utils import bind_mouse_wheel_to_canvas, create_highlighted_label

        self.timeline_entries = list(entries)
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not self.timeline_entries:
            from services.i18n_service import tr
            ctk.CTkLabel(self.scroll_frame, text=tr("timeline.no_notes", "Keine Notizen vorhanden.")).pack(pady=PAD_MD)
            return

        for entry in reversed(self.timeline_entries):
            card = ctk.CTkFrame(self.scroll_frame, fg_color=COLOR_CARD_BG, corner_radius=CORNER_RADIUS_MD, border_width=1, border_color=COLOR_CARD_BORDER)
            card.pack(fill="x", pady=PAD_XS, padx=PAD_SM)

            content_row = ctk.CTkFrame(card, fg_color="transparent")
            content_row.pack(fill="x", padx=PAD_MD, pady=(PAD_SM, PAD_SM))

            # Right Column: Date, Time (directly below date), Author & color marker (no person icon)
            right_col = ctk.CTkFrame(content_row, fg_color="transparent")
            right_col.pack(side="right", anchor="ne", padx=(PAD_SM, PAD_NONE))

            formatted_d = format_german_date(entry.timestamp)
            formatted_t = format_german_time(entry.timestamp, include_seconds=True, with_uhr=True)

            ctk.CTkLabel(
                right_col,
                text=formatted_d,
                font=ctk.CTkFont(size=FONT_SIZE_XS),
                text_color=COLOR_MUTED_LABEL,
                height=LABEL_HEIGHT_SM,
            ).pack(anchor="e")

            ctk.CTkLabel(
                right_col,
                text=formatted_t,
                font=ctk.CTkFont(size=FONT_SIZE_XS),
                text_color=COLOR_MUTED_LABEL,
                height=LABEL_HEIGHT_SM,
            ).pack(anchor="e", pady=(PAD_XS, PAD_NONE))

            author_frame = ctk.CTkFrame(right_col, fg_color="transparent")
            author_frame.pack(anchor="e", pady=(PAD_XS, PAD_NONE))

            is_own_entry = bool(
                self.author_name
                and entry.author
                and entry.author.strip().lower() == self.author_name.strip().lower()
            )
            if is_own_entry and self.color_marker_enabled and self.user_color:
                color_tile = ctk.CTkFrame(
                    author_frame,
                    width=USER_COLOR_TILE_SIZE,
                    height=USER_COLOR_TILE_SIZE,
                    corner_radius=CORNER_RADIUS_XS,
                    fg_color=self.user_color,
                    border_width=1,
                    border_color=COLOR_BORDER_DARK,
                )
                color_tile.pack(side="left", padx=(PAD_NONE, PAD_SM))

            ctk.CTkLabel(
                author_frame,
                text=entry.author,
                font=ctk.CTkFont(size=FONT_SIZE_XS),
                text_color=COLOR_SUBTITLE_MUTED,
                height=LABEL_HEIGHT_SM,
            ).pack(side="left")

            # Left Column: Channel Title, Note text (directly below title), Status change
            left_col = ctk.CTkFrame(content_row, fg_color="transparent")
            left_col.pack(side="left", fill="both", expand=True)

            channel_text = get_channel_display(entry.channel)
            ctk.CTkLabel(
                left_col,
                text=channel_text,
                font=ctk.CTkFont(weight="bold", size=FONT_SIZE_SM),
                height=LABEL_HEIGHT_MD,
            ).pack(anchor="w")

            # The shared highlight-label helper, because a note has to be both
            # fully visible and selectable. A CTkLabel cannot be selected and a
            # CTkTextbox is a scrolling viewport that has to be told its pixel
            # height - computing that from wrapped lines kept leaving the last
            # lines hidden. The helper sizes a raw tk.Text in *lines*, which is
            # the unit Tk itself uses, and re-measures on every resize.
            note_txt = create_highlighted_label(
                left_col,
                text=entry.note,
                query="",
                font=ctk.CTkFont(size=FONT_SIZE_BODY),
                text_color=COLOR_TEXT_BODY,
                bg_color=COLOR_CARD_BG,
                wrap="word",
                scroll_frame=self.scroll_frame,
                max_display_lines=TIMELINE_NOTE_MAX_DISPLAY_LINES,
            )
            note_txt.pack(fill="x", anchor="w", pady=(PAD_XS, PAD_XS))
            self._enable_text_selection(note_txt)

            if entry.status_change:
                from services.i18n_service import tr
                sc_lbl = ctk.CTkLabel(
                    left_col,
                    text=tr("timeline.status_prefix", "Status: {status}", status=entry.status_change),
                    font=ctk.CTkFont(size=FONT_SIZE_XS),
                    text_color=COLOR_INFO,
                    height=LABEL_HEIGHT_SM,
                )
                sc_lbl.pack(anchor="w", pady=(PAD_XS, PAD_NONE))

        bind_mouse_wheel_to_canvas(self.scroll_frame)

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
