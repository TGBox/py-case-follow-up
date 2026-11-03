"""Turns typed text smileys such as :) or ;-) into emoji while the user writes notes.

The replacement happens when the smiley is "finished": on the next space,
line break or punctuation key, or when focus or mouse leave the field. A smiley only
counts when it stands on its own (start of line, or after a space or an
opening bracket), so times, paths and URLs like "10:30)" or "C:D" stay as
they are.
"""

from typing import Any

from constants import SMILEY_SHORTCUTS, SMILEY_TRIGGER_CHARS

# Longest codes first, so ":-)" is not mistaken for a trailing ":)"-like match.
_CODES = sorted(SMILEY_SHORTCUTS, key=len, reverse=True)
_ALLOWED_BEFORE = (" ", "\t", "(", "[", "\n")


def find_smiley_at_end(text: str) -> tuple[str, str] | None:
    """Returns (code, emoji) when ``text`` ends with a standalone smiley code."""
    for code in _CODES:
        if text.endswith(code):
            before = text[: -len(code)]
            if not before or before.endswith(_ALLOWED_BEFORE):
                return code, SMILEY_SHORTCUTS[code]
    return None


def convert_smiley_before_cursor(text_widget: Any) -> bool:
    """Replaces a finished smiley directly before the insert cursor of a tk.Text."""
    try:
        line = text_widget.get("insert linestart", "insert")
    except Exception:
        return False
    match = find_smiley_at_end(line)
    if not match:
        return False
    code, emoji = match
    text_widget.delete(f"insert-{len(code)}c", "insert")
    text_widget.insert("insert", emoji)
    return True


def enable_smiley_shortcuts(textbox: Any) -> None:
    """Wires a CTkTextbox (or tk.Text) so typed smiley codes become emoji."""
    inner = getattr(textbox, "_textbox", textbox)

    def _on_key(event: Any = None) -> None:
        # Runs before Tk inserts the typed character, so the space or
        # punctuation simply follows the emoji.
        if getattr(event, "char", "") in SMILEY_TRIGGER_CHARS:
            convert_smiley_before_cursor(inner)

    def _on_finish(_event: Any = None) -> None:
        convert_smiley_before_cursor(inner)

    try:
        inner.bind("<KeyPress>", _on_key, add="+")
        # Leaving the field (focus or mouse, e.g. on the way to a Save button,
        # which does not take focus) also finishes a smiley at the very end.
        inner.bind("<FocusOut>", _on_finish, add="+")
        inner.bind("<Leave>", _on_finish, add="+")
    except Exception:
        pass
