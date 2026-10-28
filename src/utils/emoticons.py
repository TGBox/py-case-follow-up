"""Turns typed emoticons like :D, :) or :( into emojis in note text boxes.

Only what is typed is replaced, not pasted text, and only when the emoticon
starts a line or follows whitespace - "Termin:)" or a URL stays untouched.
A Backspace right after a replacement brings the typed emoticon back, so
anyone who really wanted ":)" gets it with one key.
"""

from __future__ import annotations

import re
from typing import Any

from constants import EMOTICON_REPLACEMENTS

# Longest first so ":-D" is not read as "-D" after a colon.
_TOKENS = sorted(EMOTICON_REPLACEMENTS, key=len, reverse=True)
_PATTERN = re.compile(r"(?:^|(?<=\s))(" + "|".join(re.escape(t) for t in _TOKENS) + r")$")
_TRIGGER_CHARS = {t[-1] for t in _TOKENS}

_START_MARK = "emoticon_start"
_END_MARK = "emoticon_end"


def find_emoticon(text_before_cursor: str) -> str | None:
    """Returns the emoticon that ends text_before_cursor, or None."""
    m = _PATTERN.search(text_before_cursor)
    return m.group(1) if m else None


class EmoticonAutoReplace:
    """Keeps the per-textbox state: which replacement Backspace would undo."""

    def __init__(self, text: Any) -> None:
        self.text = text
        self._undo_original: str | None = None

    def on_key(self, event: Any) -> str | None:
        keysym = getattr(event, "keysym", "")
        if keysym == "BackSpace" and self._undo_original is not None:
            return self.undo_last()
        if keysym in ("Shift_L", "Shift_R", "ISO_Level3_Shift", "Alt_R", "Control_L", "Control_R"):
            return None  # modifier for the next char, keep a pending undo alive
        self._undo_original = None
        if getattr(event, "char", "") in _TRIGGER_CHARS:
            # The class binding inserts the char after this handler; check then.
            self.text.after_idle(self.replace_at_cursor)
        return None

    def forget_undo(self, _event: Any = None) -> None:
        self._undo_original = None

    def replace_at_cursor(self) -> bool:
        try:
            before = self.text.get("insert linestart", "insert")
        except Exception:
            return False
        token = find_emoticon(before)
        if token is None:
            return False
        start = f"insert -{len(token)}c"
        self.text.delete(start, "insert")
        self.text.mark_set(_START_MARK, "insert")
        self.text.mark_gravity(_START_MARK, "left")
        self.text.insert("insert", EMOTICON_REPLACEMENTS[token])
        self.text.mark_set(_END_MARK, "insert")
        self._undo_original = token
        return True

    def undo_last(self) -> str | None:
        original, self._undo_original = self._undo_original, None
        try:
            if original is None or self.text.compare("insert", "!=", _END_MARK):
                return None
            if self.text.get(_START_MARK, _END_MARK) != EMOTICON_REPLACEMENTS[original]:
                return None
            self.text.delete(_START_MARK, _END_MARK)
            self.text.insert(_START_MARK, original)
        except Exception:
            return None
        return "break"


def enable_emoticon_autoreplace(textbox: Any) -> EmoticonAutoReplace:
    """Attaches the replacement to a CTkTextbox (or a plain tk.Text)."""
    inner = getattr(textbox, "_textbox", textbox)
    handler = EmoticonAutoReplace(inner)
    inner.bind("<KeyPress>", handler.on_key, add="+")
    inner.bind("<Button-1>", handler.forget_undo, add="+")
    textbox._emoticon_autoreplace = handler
    return handler
