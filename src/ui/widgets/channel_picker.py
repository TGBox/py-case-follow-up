"""Kanal-Auswahl fuer Timeline-Eintraege: erst das Medium, dann die Richtung.

Ersetzt das eine lange Dropdown (13 Kontaktarten) durch zwei kurze Reihen:

    Kanal:    [Tel.] [Mail] [Slack] [WhatsApp]
              [GitLab] [Notiz] [Sonst.]          <- bricht um, wenn es nicht passt
    Richtung: [Eingang] [Ausgang]                <- nur bei Medien mit mehreren Codes

Gespeichert wird weiterhin genau ein Code pro Eintrag (z. B. "SLACK_IN"),
die Gruppierung ist reine Darstellung (constants.CHANNEL_PICKER_GROUPS).

Die Reihen brechen gemessen um statt nach fester Spaltenzahl: die rechte
Cockpit-Spalte ist standardmaessig nur ~320 px breit, und je nach Sprache,
Windows-Skalierung und Schriftzoom passen dort mal sieben, mal vier Buttons
in eine Zeile.

Alt-Codes ohne Richtung ("EMAIL", "DEV_TICKET", ...) zeigen ihr Medium, aber
keine Richtung, und get() liefert sie unveraendert zurueck, bis der Nutzer
selbst eine Richtung waehlt. So schreibt das Bearbeiten eines alten Eintrags
dessen Kanal nie stillschweigend um.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

import tkinter as tk

import customtkinter as ctk

from constants import (
    CHANNEL_CHIP_GAP,
    CHANNEL_CHIP_HEIGHT,
    CHANNEL_PICKER_DEFAULT,
    CHANNEL_PICKER_GROUPS,
    CHANNEL_PICKER_HINT_WRAP,
    CHANNEL_PICKER_LEGACY_GROUPS,
    CHANNEL_PICKER_VARIANTS,
    COLOR_MUTED_LABEL,
    FONT_SIZE_SM,
    PAD_NONE,
    PAD_SM,
    PAD_XS,
)
from services.i18n_service import tr

# German defaults for every label key; tr() picks the active language.
_GROUP_LABELS = {
    "phone": "Tel.", "email": "Mail", "slack": "Slack", "whatsapp": "WhatsApp",
    "gitlab": "GitLab", "note": "Notiz", "other": "Sonst.",
}
_GROUP_TIPS = {
    "phone": "Telefon", "email": "E-Mail", "slack": "Slack", "whatsapp": "WhatsApp",
    "gitlab": "GitLab-Ticket", "note": "Interne Notiz", "other": "Sonstiges",
}
_VARIANT_LABELS = {
    "in": "Eingang", "out": "Ausgang",
    "created": "erstellt", "updated": "aktualisiert", "closed": "geschlossen",
}

_GROUP_CODES: dict[str, tuple[str, ...]] = dict(CHANNEL_PICKER_GROUPS)
_CODE_GROUP: dict[str, str] = {code: gid for gid, codes in CHANNEL_PICKER_GROUPS for code in codes}


def group_of(code: str) -> str | None:
    """Medium a stored code belongs to, including old codes without a direction."""
    return _CODE_GROUP.get(code) or CHANNEL_PICKER_LEGACY_GROUPS.get(code)


def group_label(group_id: str) -> str:
    return tr(f"channel_picker.group_{group_id}", _GROUP_LABELS[group_id])


def group_tip(group_id: str) -> str:
    return tr(f"channel_picker.tip_{group_id}", _GROUP_TIPS[group_id])


def variant_label(code: str) -> str:
    key = CHANNEL_PICKER_VARIANTS[code]
    return tr(f"channel_picker.variant_{key}", _VARIANT_LABELS[key])


def _seg_color(name: str) -> Any:
    """Colours of CustomTkinter's own segmented button, so the chips look like one."""
    try:
        return ctk.ThemeManager.theme["CTkSegmentedButton"][name]
    except Exception:
        return None


class ChipRow(ctk.CTkFrame):
    """Single-choice row of buttons that wraps onto further lines when narrow.

    Items are (key, label). select(key) highlights one (None: none). The
    buttons are packed into one line frame per visual line; a <Configure>
    re-flows them only when the line breaks actually change, so a resize that
    keeps the same breaks costs nothing.
    """

    def __init__(self, master: Any, on_select: Callable[[str], None], **kwargs: Any) -> None:
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)
        self._on_select = on_select
        self._buttons: dict[str, ctk.CTkButton] = {}
        self._order: list[str] = []
        self._lines: list[ctk.CTkFrame] = []
        self._breaks: tuple[int, ...] | None = None
        self._selected: str | None = None
        self._reflow_job: str | None = None
        self._destroying = False
        self._font = ctk.CTkFont(size=FONT_SIZE_SM)
        self._requested: tuple[int, int] | None = None
        # The row must take the width it is given, not ask for the width of
        # all chips side by side: before the first wrap that is one long line,
        # and asking for it made Tk widen the whole right cockpit column
        # (pinned at 320 px, it came out at 464) - after which nothing wrapped
        # any more. So the lines do not size the row; _apply_requested_size()
        # asks for one chip's width and the height of the wrapped lines.
        tk.Misc.pack_propagate(self, False)
        # tk.Misc.bind: CTkFrame.bind() forwards to its internal canvas, whose
        # <Configure> is not the frame's own.
        tk.Misc.bind(self, "<Configure>", self._on_configure, add="+")

    def set_items(self, items: list[tuple[str, str]]) -> None:
        if [(k, self._buttons[k].cget("text")) for k in self._order if k in self._buttons] == items:
            return
        keys = [k for k, _ in items]
        for key in list(self._buttons):
            if key not in keys:
                self._buttons.pop(key).destroy()
        for key, label in items:
            btn = self._buttons.get(key)
            if btn is None:
                btn = ctk.CTkButton(
                    self,
                    text=label,
                    width=0,
                    height=CHANNEL_CHIP_HEIGHT,
                    font=self._font,
                    corner_radius=_seg_color("corner_radius") or 6,
                    command=lambda k=key: self._clicked(k),
                )
                # A chip that changes size (font zoom, language) may no longer
                # fit its line even though the row itself kept its width.
                tk.Misc.bind(btn, "<Configure>", self._schedule_reflow, add="+")
                self._buttons[key] = btn
            elif btn.cget("text") != label:
                btn.configure(text=label)
        self._order = keys
        self._breaks = None
        self._paint()
        self._reflow()

    def buttons(self) -> dict[str, ctk.CTkButton]:
        return dict(self._buttons)

    def select(self, key: str | None) -> None:
        if key == self._selected:
            return
        self._selected = key
        self._paint()

    def selected(self) -> str | None:
        return self._selected

    def line_count(self) -> int:
        return len(self._breaks or ()) + 1 if self._order else 0

    # -------------------------------------------------------------- internals

    def _clicked(self, key: str) -> None:
        self._on_select(key)

    def _paint(self) -> None:
        sel, sel_hover = _seg_color("selected_color"), _seg_color("selected_hover_color")
        unsel, unsel_hover = _seg_color("unselected_color"), _seg_color("unselected_hover_color")
        for key, btn in self._buttons.items():
            if key == self._selected:
                btn.configure(fg_color=sel, hover_color=sel_hover)
            else:
                btn.configure(fg_color=unsel, hover_color=unsel_hover)

    def _available_width(self) -> int:
        w = self.winfo_width()
        if w > 1:
            return w
        # Not laid out yet: the parent's width is the best guess, and 0 means
        # "unknown" (everything on one line until the first <Configure>).
        try:
            return max(0, self.master.winfo_width())
        except Exception:
            return 0

    def _compute_breaks(self, width: int) -> tuple[int, ...]:
        if width <= 1:
            return ()
        gap = round(CHANNEL_CHIP_GAP * self._scaling())
        breaks: list[int] = []
        used = 0
        for i, key in enumerate(self._order):
            w = self._buttons[key].winfo_reqwidth()
            need = w if used == 0 else used + gap + w
            if used > 0 and need > width:
                breaks.append(i)
                used = w
            else:
                used = need
        return tuple(breaks)

    def _scaling(self) -> float:
        try:
            return float(ctk.ScalingTracker.get_widget_scaling(self)) or 1.0
        except Exception:
            return 1.0

    def _apply_requested_size(self) -> None:
        """Requests the widest single chip as width and the wrapped lines' height."""
        if not self._order:
            return
        gap = round(CHANNEL_CHIP_GAP * self._scaling())
        starts = [0, *(self._breaks or ())]
        ends = [*(self._breaks or ()), len(self._order)]
        height = 0
        for idx, (a, b) in enumerate(zip(starts, ends, strict=True)):
            line_h = max(self._buttons[k].winfo_reqheight() for k in self._order[a:b])
            height += line_h + (gap if idx else 0)
        width = max(self._buttons[k].winfo_reqwidth() for k in self._order)
        if (width, height) == self._requested:
            return
        self._requested = (width, height)
        scale = self._scaling()
        # CTkFrame takes logical sizes and applies the scaling itself.
        ctk.CTkFrame.configure(self, width=max(1, round(width / scale)), height=max(1, round(height / scale)))

    def destroy(self) -> None:
        """No reflow once the row is going down.

        On Windows, Tk services pending events while it destroys a window:
        destroying the chips fires their <Configure> and the scheduled
        reflow before the row itself is gone. That reflow then measured the
        half-destroyed chips, wrapped them onto new line frames, and those
        frames - created after tkinter had listed the children to destroy -
        were killed by Tk only, never by Python. They stayed registered in
        CustomTkinter's scaling tracker, and the next font zoom raised
        "invalid command name".
        """
        self._destroying = True
        if self._reflow_job is not None:
            try:
                self.after_cancel(self._reflow_job)
            except Exception:
                pass
            self._reflow_job = None
        for line in self._lines:
            try:
                line.destroy()
            except Exception:
                pass
        self._lines.clear()
        super().destroy()

    def _reflow(self) -> None:
        if self._destroying:
            return
        breaks = self._compute_breaks(self._available_width())
        if breaks == self._breaks:
            self._apply_requested_size()
            return
        self._breaks = breaks
        for line in self._lines:
            for child in line.winfo_children():
                child.pack_forget()
        starts = [0, *breaks]
        ends = [*breaks, len(self._order)]
        while len(self._lines) < len(starts):
            self._lines.append(ctk.CTkFrame(self, fg_color="transparent"))
        for idx, line in enumerate(self._lines):
            if idx >= len(starts):
                line.pack_forget()
                continue
            line.pack(fill="x", anchor="w", pady=(PAD_NONE if idx == 0 else CHANNEL_CHIP_GAP, PAD_NONE))
            for pos, key in enumerate(self._order[starts[idx]:ends[idx]]):
                btn = self._buttons[key]
                btn.pack(in_=line, side="left", padx=(PAD_NONE if pos == 0 else CHANNEL_CHIP_GAP, PAD_NONE))
                # The buttons are siblings of the line frames (Tk cannot move a
                # widget to another parent), so they have to be stacked above
                # the frame they are packed into or it would cover them.
                tk.Misc.tkraise(btn, line)
        self._apply_requested_size()

    def _on_configure(self, event: Any = None) -> None:
        if event is not None and getattr(event, "widget", self) is not self:
            return
        self._reflow()

    def _schedule_reflow(self, _event: Any = None) -> None:
        # Several chips resize at once (zoom); one reflow after them is enough.
        if self._reflow_job is not None or self._destroying:
            return
        try:
            self._reflow_job = self.after_idle(self._run_scheduled_reflow)
        except Exception:
            self._reflow_job = None

    def _run_scheduled_reflow(self) -> None:
        self._reflow_job = None
        try:
            if self.winfo_exists():
                self._reflow()
        except Exception:
            pass


class ChannelPicker(ctk.CTkFrame):
    """Channel selector: medium chips plus a direction/event row. get()/set() use stored codes."""

    def __init__(
        self,
        master: Any,
        value: str = CHANNEL_PICKER_DEFAULT,
        command: Callable[[str], None] | None = None,
        show_labels: bool = True,
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)
        self._command = command
        self._show_labels = show_labels
        self._value: str = CHANNEL_PICKER_DEFAULT
        self._group: str | None = None
        self._tooltips: dict[str, Any] = {}

        self.columnconfigure(1, weight=1)
        small_bold = ctk.CTkFont(size=FONT_SIZE_SM, weight="bold")

        self.channel_lbl = ctk.CTkLabel(self, text="", font=small_bold, anchor="nw")
        self._label_sizer = ctk.CTkLabel(self, text="", font=small_bold)  # never gridded, see _pin_label_column
        self._measured_label_texts: tuple[str, ...] = ()
        self.group_row = ChipRow(self, on_select=self._on_group_clicked)
        self.group_row.grid(row=0, column=1, sticky="ew", pady=(PAD_NONE, PAD_XS))

        self.variant_lbl = ctk.CTkLabel(self, text="", font=small_bold, anchor="nw")
        self.variant_row = ChipRow(self, on_select=self._on_variant_clicked)
        self.legacy_lbl = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=FONT_SIZE_SM), text_color=COLOR_MUTED_LABEL, anchor="w", justify="left",
            wraplength=CHANNEL_PICKER_HINT_WRAP,
        )

        if show_labels:
            self.channel_lbl.grid(row=0, column=0, sticky="nw", padx=(PAD_NONE, PAD_SM))

        self.refresh_labels()
        self.set(value)

    # ------------------------------------------------------------------ API

    def get(self) -> str:
        """The stored channel code currently selected."""
        return self._value

    def set(self, code: str | None) -> None:
        code = code or CHANNEL_PICKER_DEFAULT
        self._value = code
        # Unknown codes (removed channel, foreign data) select nothing but
        # keep their value, so they round-trip untouched.
        self._group = group_of(code)
        self.group_row.select(self._group)
        self._render_variants()

    def configure(self, require_redraw: bool = False, **kwargs: Any) -> None:  # type: ignore[override]
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if kwargs or require_redraw:
            super().configure(require_redraw=require_redraw, **kwargs)

    def refresh_labels(self) -> None:
        """Re-reads every label from the active language (language switch)."""
        self.channel_lbl.configure(text=tr("channel_picker.label_channel", "Kanal:"))
        self.group_row.set_items([(gid, group_label(gid)) for gid, _ in CHANNEL_PICKER_GROUPS])
        self._attach_group_tooltips()
        self._render_variants()

    # ------------------------------------------------------------- internals

    def _on_group_clicked(self, group: str) -> None:
        if group == self._group and self._value in _GROUP_CODES[group]:
            return
        codes = _GROUP_CODES[group]
        # Keep the direction when switching medium (inbound phone -> inbound
        # Slack), the usual case when correcting a wrongly picked medium.
        current_variant = CHANNEL_PICKER_VARIANTS.get(self._value)
        same_variant = next((c for c in codes if CHANNEL_PICKER_VARIANTS.get(c) == current_variant), None)
        self._group = group
        self._value = same_variant or codes[0]
        self.group_row.select(group)
        self._render_variants()
        self._notify()

    def _on_variant_clicked(self, code: str) -> None:
        if code == self._value:
            return
        self._value = code
        self._render_variants()
        self._notify()

    def _pin_label_column(self) -> None:
        """Label column as wide as its longest possible label.

        Otherwise it is as wide as the labels shown right now, and the chips
        jump sideways whenever the second row (and its label) comes or goes -
        a few pixels are enough to move a chip onto the next line.
        Measured with a label that is never shown, so the CTkLabel's own inner
        padding and the current scaling are part of the number.
        """
        if not self._show_labels:
            return
        try:
            texts = (
                tr("channel_picker.label_channel", "Kanal:"),
                tr("channel_picker.label_variant", "Richtung:"),
                tr("channel_picker.label_event", "Ticket:"),
            )
            if texts == self._measured_label_texts:
                return
            # The inner tk.Label computes its requested size synchronously on
            # configure(). Asking the CTkLabel instead would need
            # update_idletasks(), which flushes the idle queue of the whole
            # app - run during the cockpit build, that disturbed the restore
            # of the column widths (the right column came out 290 or 464 px
            # instead of 320 in half of the starts).
            inner = getattr(self._label_sizer, "_label", self._label_sizer)
            widest = 0
            for text in texts:
                self._label_sizer.configure(text=text)
                widest = max(widest, inner.winfo_reqwidth())
            pad = round(PAD_SM * float(ctk.ScalingTracker.get_widget_scaling(self)))
            self.grid_columnconfigure(0, minsize=widest + pad)
            self._measured_label_texts = texts
        except Exception:
            pass

    def _render_variants(self) -> None:
        self._pin_label_column()
        codes = _GROUP_CODES.get(self._group or "", ())
        if len(codes) < 2:
            self.variant_lbl.grid_remove()
            self.variant_row.grid_remove()
            self.legacy_lbl.grid_remove()
            return
        is_ticket = self._group == "gitlab"
        self.variant_lbl.configure(
            text=tr("channel_picker.label_event", "Ticket:") if is_ticket else tr("channel_picker.label_variant", "Richtung:")
        )
        self.variant_row.set_items([(c, variant_label(c)) for c in codes])
        legacy = self._value not in codes
        self.variant_row.select(None if legacy else self._value)
        if self._show_labels:
            self.variant_lbl.grid(row=1, column=0, sticky="nw", padx=(PAD_NONE, PAD_SM))
        self.variant_row.grid(row=1, column=1, sticky="ew")
        if legacy:
            self.legacy_lbl.configure(text=tr("channel_picker.legacy_hint", "Alter Eintrag ohne Richtung – zum Ändern eine Richtung wählen."))
            self.legacy_lbl.grid(row=2, column=0, columnspan=2, sticky="w", pady=(PAD_XS, PAD_NONE))
        else:
            self.legacy_lbl.grid_remove()

    def _attach_group_tooltips(self) -> None:
        """Full medium names on hover; the chips themselves carry short labels."""
        from ui.widgets.ctk_tooltip import CTkTooltip

        for gid, btn in self.group_row.buttons().items():
            if gid not in self._tooltips:
                self._tooltips[gid] = CTkTooltip(btn, lambda g=gid: group_tip(g))

    def _notify(self) -> None:
        if self._command is not None:
            try:
                self._command(self._value)
            except Exception:
                pass
