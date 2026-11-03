"""Typed text smileys turn into emoji in note fields."""

import customtkinter as ctk
import pytest

from utils.smiley_utils import convert_smiley_before_cursor, enable_smiley_shortcuts, find_smiley_at_end


@pytest.mark.parametrize(
    "text, expected",
    [
        (":)", (":)", "🙂")),
        ("Danke :-)", (":-)", "🙂")),
        ("Alles klar ;)", (";)", "😉")),
        ("Super :D", (":D", "😄")),
        ("Schade :(", (":(", "🙁")),
        ("(Spaß :P", (":P", "😛")),
        ("Oh :O", (":O", "😮")),
    ],
)
def test_standalone_codes_are_found(text, expected):
    assert find_smiley_at_end(text) == expected


@pytest.mark.parametrize("text", ["10:30)", "C:D", "Laufwerk D:(", "siehe:)", "http://x.de/a:)", "", "Hallo"])
def test_codes_glued_to_other_text_stay_untouched(text):
    assert find_smiley_at_end(text) is None


def _textbox(root, content: str) -> ctk.CTkTextbox:
    tb = ctk.CTkTextbox(root)
    tb.pack()
    enable_smiley_shortcuts(tb)
    tb.insert("1.0", content)
    tb._textbox.mark_set("insert", "end-1c")
    return tb


def test_smiley_before_the_cursor_is_converted_where_typing_continues(root):
    tb = _textbox(root, "Danke dir :) und tschüss")
    try:
        inner = tb._textbox
        inner.mark_set("insert", "1.12")  # right after ":)"
        assert convert_smiley_before_cursor(inner) is True
        assert tb.get("1.0", "end-1c") == "Danke dir 🙂 und tschüss"
        assert convert_smiley_before_cursor(inner) is False  # nothing left to convert
        # Space, punctuation and Enter are wired to trigger the conversion
        assert inner.bind("<KeyPress>") and inner.bind("<FocusOut>") and inner.bind("<Leave>")
    finally:
        tb.destroy()


def test_leaving_the_field_converts_a_trailing_smiley_but_not_times(root):
    tb = _textbox(root, "Termin 10:30) ok ;-)")
    try:
        tb._textbox.event_generate("<Leave>")
        root.update()
        assert tb.get("1.0", "end-1c") == "Termin 10:30) ok 😉"
    finally:
        tb.destroy()
