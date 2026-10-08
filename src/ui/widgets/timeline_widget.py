import customtkinter as ctk
from typing import Any
from collections.abc import Callable
from models.case import TimelineEntry
from enums import Channel, get_channel_display, get_channel_val_from_display, CHANNEL_DISPLAY
from constants import (
    BTN_HEIGHT_TIMELINE_EDIT,
    BTN_WIDTH_ACTION,
    BTN_WIDTH_TIMELINE_EDIT,
    BTN_WIDTH_SM,
    COLOR_CARD_BG,
    COLOR_CARD_BORDER,
    COLOR_MUTED_GRAY_FG,
    COLOR_MUTED_LABEL,
    COLOR_PURPLE_DARK,
    COLOR_SUBTITLE_MUTED,
    COLOR_TEXT_BODY,
    COLOR_TIMELINE_EDIT_HOVER,
    COLOR_TIMELINE_LINK,
    COMBO_WIDTH_SM,
    CORNER_RADIUS_MD,
    CORNER_RADIUS_XS,
    DATE_PICKER_WIDTH_TIMELINE,
    FONT_SIZE_BODY,
    FONT_SIZE_SM,
    FONT_SIZE_SUBTITLE,
    FONT_SIZE_XS,
    LABEL_HEIGHT_MD,
    LABEL_HEIGHT_SM,
    PAD_GAP,
    PAD_MD,
    PAD_NONE,
    PAD_SM,
    PAD_XS,
    TEXTBOX_HEIGHT_SM,
    TIMELINE_ACCENT_RAIL_WIDTH,
    TIMELINE_AUTHOR_CHIP_MIX_DARK,
    TIMELINE_AUTHOR_CHIP_MIX_LIGHT,
    TIMELINE_AUTHOR_CHIP_RADIUS,
    TIMELINE_EDIT_HOVER_MIX,
    TIMELINE_NOTE_HEIGHT_KEY,
    TIMELINE_NOTE_MAX_DISPLAY_LINES,
    TIMELINE_NOTE_MAX_HEIGHT,
    TIMELINE_NOTE_MIN_HEIGHT,
    TIMELINE_OWN_BORDER_MIX_DARK,
    TIMELINE_OWN_BORDER_MIX_LIGHT,
    TIMELINE_OWN_TINT_DARK,
    TIMELINE_OWN_TINT_LIGHT,
)
from utils.datetime_utils import (
    format_german_date,
    format_german_datetime,
    format_german_time,
    format_iso,
    now_iso,
    timeline_sort_key,
)


class TimelineWidget(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        author_name: str,
        on_timeline_updated: Callable[[list[TimelineEntry]], None],
        on_open_snippet_picker: Callable[[Callable[[str], None]], None] | None = None,
        user_color: str | None = None,
        color_marker_enabled: bool = False,
        profile: Any | None = None,
        storage_service: Any | None = None,
    ):
        super().__init__(parent)
        self.profile = profile
        self.storage_service = storage_service
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
            text=tr("cockpit.snippets_btn", "📝 Textbaustein"),
            width=BTN_WIDTH_SM + 10,
            fg_color=COLOR_MUTED_GRAY_FG,
            hover_color=COLOR_PURPLE_DARK,
            command=self.on_click_snippet,
        )
        self.snip_btn.pack(side="right")

        self.channel_combo = ctk.CTkOptionMenu(input_frame, values=[get_channel_display(c) for c in CHANNEL_DISPLAY], width=COMBO_WIDTH_SM)
        self.channel_combo.set(get_channel_display(Channel.PHONE_INBOUND.value))
        self.channel_combo.pack(anchor="w", padx=PAD_SM, pady=(PAD_NONE, PAD_SM))

        # Optional back-dating: empty means "now". The picker refuses the future,
        # a timeline documents what already happened.
        from ui.widgets.date_picker import DatePickerWidget
        time_row = ctk.CTkFrame(input_frame, fg_color="transparent")
        time_row.pack(fill="x", padx=PAD_SM, pady=(PAD_NONE, PAD_SM))
        self.time_lbl = ctk.CTkLabel(time_row, text=tr("timeline.time_lbl", "🕒 Zeitpunkt:"), font=ctk.CTkFont(size=FONT_SIZE_SM, weight="bold"))
        self.time_lbl.pack(side="left", padx=(PAD_NONE, PAD_SM))
        self.time_picker = DatePickerWidget(
            time_row,
            placeholder_text=tr("timeline.time_placeholder", "leer = jetzt"),
            include_time=True,
            width=DATE_PICKER_WIDTH_TIMELINE,
            time_bound="past",
        )
        self.time_picker.pack(side="left", fill="x", expand=True)

        self.note_textbox = ctk.CTkTextbox(input_frame, height=self._stored_note_height())
        self.note_textbox.pack(fill="x", padx=PAD_SM, pady=(PAD_NONE, PAD_XS))

        # Griff unter dem Feld: nach unten ziehen macht es hoeher. Die Hoehe
        # landet wie die Spaltenbreiten im Profil (ui_settings).
        from ui.widgets.dynamic_form_widget import TextboxResizeHandle
        self.note_resize_handle = TextboxResizeHandle(
            input_frame,
            target_textbox=self.note_textbox,
            field_id=TIMELINE_NOTE_HEIGHT_KEY,
            profile=self.profile,
            storage_service=self.storage_service,
            min_height=TIMELINE_NOTE_MIN_HEIGHT,
            max_height=TIMELINE_NOTE_MAX_HEIGHT,
            update_default_height=False,
        )
        self.note_resize_handle.pack(fill="x", padx=PAD_SM, pady=(PAD_NONE, PAD_SM))

        from utils.ui_utils import enable_textbox_cursor_autoscroll
        enable_textbox_cursor_autoscroll(self.note_textbox)

        self.add_btn = ctk.CTkButton(input_frame, text=tr("cockpit.add_note_btn", "+ Notiz Hinzufügen"), command=self.on_add_note, width=BTN_WIDTH_ACTION)
        self.add_btn.pack(side="right", padx=PAD_SM, pady=(PAD_NONE, PAD_SM))

    def _stored_note_height(self) -> int:
        ui = getattr(self.profile, "ui_settings", None)
        heights = getattr(ui, "custom_textbox_heights", None)
        if isinstance(heights, dict):
            try:
                h = int(heights.get(TIMELINE_NOTE_HEIGHT_KEY, TEXTBOX_HEIGHT_SM))
            except (TypeError, ValueError):
                h = TEXTBOX_HEIGHT_SM
            return max(TIMELINE_NOTE_MIN_HEIGHT, min(TIMELINE_NOTE_MAX_HEIGHT, h))
        return TEXTBOX_HEIGHT_SM

    def apply_stored_note_height(self, profile: Any | None = None) -> None:
        """Uebernimmt die gespeicherte Hoehe, z.B. nach "Spaltenbreiten zuruecksetzen"."""
        if profile is not None:
            self.profile = profile
            self.note_resize_handle.profile = profile
        self.note_textbox.configure(height=self._stored_note_height())

    def refresh_ui_labels(self):
        from services.i18n_service import tr
        if hasattr(self, "hdr_lbl"):
            self.hdr_lbl.configure(text=tr("cockpit.timeline_title", "Verlauf & Timeline Notizen"))
        if hasattr(self, "ctrl_lbl"):
            self.ctrl_lbl.configure(text=tr("cockpit.add_new_note", "Neue Notiz hinzufügen:"))
        if hasattr(self, "snip_btn"):
            self.snip_btn.configure(text=tr("cockpit.snippets_btn", "📝 Textbaustein"))
        if hasattr(self, "add_btn"):
            self.add_btn.configure(text=tr("cockpit.add_note_btn", "+ Notiz Hinzufügen"))
        if hasattr(self, "time_lbl"):
            self.time_lbl.configure(text=tr("timeline.time_lbl", "🕒 Zeitpunkt:"))
        if hasattr(self, "time_picker"):
            self.time_picker.refresh_ui_labels()
            if not self.time_picker.get():
                self.time_picker.entry.configure(placeholder_text=tr("timeline.time_placeholder", "leer = jetzt"))
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

    def _own_entry_palette(self) -> dict[str, Any] | None:
        """Card colours for the user's own entries, derived from their colour.

        Returns None when the colour marker is off or the stored colour is not
        a colour Tk understands - the card then simply stays neutral.
        """
        if not (self.color_marker_enabled and self.user_color):
            return None
        from utils.ui_utils import mix_colors, readable_variant
        color = self.user_color
        try:
            card_bg = (
                mix_colors(self, color, COLOR_CARD_BG[0], TIMELINE_OWN_TINT_LIGHT),
                mix_colors(self, color, COLOR_CARD_BG[1], TIMELINE_OWN_TINT_DARK),
            )
            chip_bg = (
                mix_colors(self, color, card_bg[0], TIMELINE_AUTHOR_CHIP_MIX_LIGHT),
                mix_colors(self, color, card_bg[1], TIMELINE_AUTHOR_CHIP_MIX_DARK),
            )
            return {
                "accent": color,
                "card_bg": card_bg,
                # Namens-Chip: leicht getoente Fuellung, der Name in einer
                # lesbaren Variante der Nutzerfarbe - erkennbar, ohne zu
                # leuchten (auch bei Gelb im Dark Mode).
                "chip_bg": chip_bg,
                "chip_text": (
                    readable_variant(self, color, chip_bg[0]),
                    readable_variant(self, color, chip_bg[1]),
                ),
                "edit_hover": (
                    mix_colors(self, color, card_bg[0], TIMELINE_EDIT_HOVER_MIX),
                    mix_colors(self, color, card_bg[1], TIMELINE_EDIT_HOVER_MIX),
                ),
                "border": (
                    mix_colors(self, color, COLOR_CARD_BORDER[0], TIMELINE_OWN_BORDER_MIX_LIGHT),
                    mix_colors(self, color, COLOR_CARD_BORDER[1], TIMELINE_OWN_BORDER_MIX_DARK),
                ),
            }
        except Exception:
            return None

    def _is_own_entry(self, entry: TimelineEntry) -> bool:
        return bool(
            self.author_name
            and entry.author
            and entry.author.strip().lower() == self.author_name.strip().lower()
        )

    def _card_fonts(self) -> dict[str, ctk.CTkFont]:
        """Fonts for the timeline cards, created once and shared by all cards.

        load_timeline rebuilds every card on each refresh (language switch,
        new note). Fresh CTkFonts per label piled up as garbage, and when the
        garbage collector finalised one on a background thread (CTkFont.__del__
        calls into Tcl) that thread blocked until the main thread answered.
        """
        if not hasattr(self, "_fonts"):
            self._fonts = {
                "xs": ctk.CTkFont(size=FONT_SIZE_XS),
                "channel": ctk.CTkFont(weight="bold", size=FONT_SIZE_SM),
                "body": ctk.CTkFont(size=FONT_SIZE_BODY),
                "chip": ctk.CTkFont(size=FONT_SIZE_XS, weight="bold"),
                "edit": ctk.CTkFont(size=FONT_SIZE_BODY),
            }
        return self._fonts

    def load_timeline(self, entries: list[TimelineEntry]):
        from utils.ui_utils import bind_mouse_wheel_to_canvas, create_highlighted_label, linkify_text_widget

        self.timeline_entries = list(entries)
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not self.timeline_entries:
            from services.i18n_service import tr
            ctk.CTkLabel(self.scroll_frame, text=tr("timeline.no_notes", "Keine Notizen vorhanden.")).pack(pady=PAD_MD)
            return

        own_palette = self._own_entry_palette()
        fonts = self._card_fonts()

        for entry in reversed(self.timeline_entries):
            palette = own_palette if own_palette and self._is_own_entry(entry) else None
            card_bg = palette["card_bg"] if palette else COLOR_CARD_BG
            card = ctk.CTkFrame(
                self.scroll_frame,
                fg_color=card_bg,
                corner_radius=CORNER_RADIUS_MD,
                border_width=1,
                border_color=palette["border"] if palette else COLOR_CARD_BORDER,
            )
            card.pack(fill="x", pady=PAD_XS, padx=PAD_SM)

            if palette:
                # Durchgehende Farbleiste am linken Rand: eigene Eintraege sind
                # beim Scrollen sofort zu erkennen, ohne den Text zu lesen.
                # height=1 + fill="y": die Leiste waechst mit der Karte mit,
                # statt ihr die CTk-Standardhoehe aufzuzwingen.
                rail = ctk.CTkFrame(
                    card,
                    width=TIMELINE_ACCENT_RAIL_WIDTH,
                    height=1,
                    corner_radius=CORNER_RADIUS_XS,
                    fg_color=palette["accent"],
                )
                rail.pack(side="left", fill="y", padx=(PAD_SM, PAD_NONE), pady=PAD_SM)

            content_row = ctk.CTkFrame(card, fg_color="transparent")
            content_row.pack(fill="x", padx=(PAD_SM if palette else PAD_MD, PAD_MD), pady=(PAD_SM, PAD_SM))

            # Right Column: Date, Time (directly below date), Author & color marker (no person icon)
            right_col = ctk.CTkFrame(content_row, fg_color="transparent")
            right_col.pack(side="right", anchor="ne", padx=(PAD_SM, PAD_NONE))

            formatted_d = format_german_date(entry.timestamp)
            formatted_t = format_german_time(entry.timestamp, include_seconds=True, with_uhr=True)

            ctk.CTkLabel(
                right_col,
                text=formatted_d,
                font=fonts["xs"],
                text_color=COLOR_MUTED_LABEL,
                height=LABEL_HEIGHT_SM,
            ).pack(anchor="e")

            ctk.CTkLabel(
                right_col,
                text=formatted_t,
                font=fonts["xs"],
                text_color=COLOR_MUTED_LABEL,
                height=LABEL_HEIGHT_SM,
            ).pack(anchor="e", pady=(PAD_XS, PAD_NONE))

            author_frame = ctk.CTkFrame(right_col, fg_color="transparent")
            author_frame.pack(anchor="e", pady=(PAD_XS, PAD_NONE))

            from services.i18n_service import tr
            # Nur der Stift, ohne eigene Flaeche: gehoert zur Karte statt als
            # grauer Block auf ihr zu liegen. Beim Ueberfahren leicht getoent.
            edit_btn = ctk.CTkButton(
                right_col,
                text=tr("timeline.edit_btn", "✏"),
                width=BTN_WIDTH_TIMELINE_EDIT,
                height=BTN_HEIGHT_TIMELINE_EDIT,
                font=fonts["edit"],
                fg_color="transparent",
                text_color=COLOR_MUTED_LABEL,
                hover_color=palette["edit_hover"] if palette else COLOR_TIMELINE_EDIT_HOVER,
                corner_radius=CORNER_RADIUS_MD,
                command=lambda e=entry: self.open_edit_dialog(e),
            )
            edit_btn.pack(anchor="e", pady=(PAD_XS, PAD_NONE))
            from ui.widgets.ctk_tooltip import CTkTooltip
            CTkTooltip(edit_btn, lambda: tr("timeline.edit_tooltip", "Eintrag bearbeiten"))

            if palette:
                # Ein einziges Label mit eigener runder Fuellung: kein Rahmen
                # (1-px-Ring auf der kleinen Pille wird unter Windows treppig)
                # und kein Kind-Widget, dessen Rechteck in die Rundung schneidet.
                ctk.CTkLabel(
                    author_frame,
                    text=entry.author,
                    font=fonts["chip"],
                    fg_color=palette["chip_bg"],
                    text_color=palette["chip_text"],
                    corner_radius=TIMELINE_AUTHOR_CHIP_RADIUS,
                    height=LABEL_HEIGHT_SM,
                    padx=PAD_GAP,
                ).pack(side="left")
            else:
                ctk.CTkLabel(
                    author_frame,
                    text=entry.author,
                    font=fonts["xs"],
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
                font=fonts["channel"],
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
                font=fonts["body"],
                text_color=COLOR_TEXT_BODY,
                bg_color=card_bg,
                wrap="word",
                scroll_frame=self.scroll_frame,
                max_display_lines=TIMELINE_NOTE_MAX_DISPLAY_LINES,
            )
            note_txt.pack(fill="x", anchor="w", pady=(PAD_XS, PAD_XS))
            self._enable_text_selection(note_txt)
            # Links in der Notiz: unterstrichen, Klick oeffnet im Browser.
            linkify_text_widget(note_txt, COLOR_TIMELINE_LINK)

            if entry.edited_at:
                from services.i18n_service import tr
                ctk.CTkLabel(
                    left_col,
                    text=tr(
                        "timeline.edited_hint",
                        "✏ bearbeitet {date} von {author}",
                        date=format_german_datetime(entry.edited_at),
                        author=entry.edited_by or "-",
                    ),
                    font=fonts["xs"],
                    text_color=COLOR_MUTED_LABEL,
                    height=LABEL_HEIGHT_SM,
                ).pack(anchor="w", pady=(PAD_XS, PAD_NONE))

        bind_mouse_wheel_to_canvas(self.scroll_frame)

    def on_add_note(self):
        text = self.note_textbox.get("1.0", "end-1c").strip()
        if not text:
            return

        timestamp = now_iso()
        if hasattr(self, "time_picker") and self.time_picker.get():
            picked = self.time_picker.get_datetime()
            if picked is None:
                # Unreadable time: keep the note so nothing typed gets lost.
                try:
                    self.time_picker.entry.focus_set()
                except Exception:
                    pass
                return
            timestamp = format_iso(picked)

        channel_val = get_channel_val_from_display(self.channel_combo.get())
        new_entry = TimelineEntry(
            timestamp=timestamp,
            author=self.author_name,
            channel=channel_val,
            note=text,
        )
        self.timeline_entries.append(new_entry)
        self.timeline_entries = self._sorted(self.timeline_entries)
        self.note_textbox.delete("1.0", "end")
        if hasattr(self, "time_picker"):
            self.time_picker.set_date("")
        self._commit_changes()

    @staticmethod
    def _sorted(entries: list[TimelineEntry]) -> list[TimelineEntry]:
        """Chronological order, so a back-dated or re-timed entry lands in place.

        Stable, so entries with the same timestamp keep their order. If any
        timestamp is unreadable, the stored order is kept untouched instead of
        guessing where that entry belongs.
        """
        keys = [timeline_sort_key(e.timestamp) for e in entries]
        if any(k == float("-inf") for k in keys):
            return list(entries)
        return [e for _, e in sorted(zip(keys, entries, strict=True), key=lambda pair: pair[0])]

    def _commit_changes(self) -> None:
        self.load_timeline(self.timeline_entries)
        self.on_timeline_updated(self.timeline_entries)

    def open_edit_dialog(self, entry: TimelineEntry):
        from ui.dialogs.timeline_entry_dialog import TimelineEntryDialog
        TimelineEntryDialog(
            self.winfo_toplevel(),
            entry,
            on_save=lambda dt, channel, note, e=entry: self.apply_entry_edit(e, dt, channel, note),
            on_delete=lambda e=entry: self.delete_entry(e),
        )

    def apply_entry_edit(self, entry: TimelineEntry, dt, channel: str, note: str) -> None:
        new_ts = format_iso(dt)
        # Only whole minutes are editable - keep the original seconds when the
        # user did not actually change the time.
        if entry.timestamp and entry.timestamp[:16] == new_ts[:16]:
            new_ts = entry.timestamp
        if new_ts == entry.timestamp and channel == entry.channel and note == entry.note:
            return
        entry.timestamp = new_ts
        entry.channel = channel
        entry.note = note
        entry.edited_at = now_iso()
        entry.edited_by = self.author_name
        if not any(existing is entry for existing in self.timeline_entries):
            return
        self.timeline_entries = self._sorted(self.timeline_entries)
        self._commit_changes()

    def delete_entry(self, entry: TimelineEntry) -> None:
        for idx, existing in enumerate(self.timeline_entries):
            if existing is entry:
                del self.timeline_entries[idx]
                self._commit_changes()
                return
