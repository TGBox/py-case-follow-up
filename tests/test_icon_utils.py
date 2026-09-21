"""Unit tests for icon_utils module."""

import customtkinter as ctk
import pytest
from unittest.mock import patch

from constants import (
    COLOR_ICON_WHITE,
    ICON_KEY_BELL,
    ICON_KEY_COPY,
    ICON_KEY_HELP,
    ICON_KEY_QUIT,
    ICON_KEY_THEME,
    ICON_KEY_USER,
    ICON_SIZE_ACTION,
    ICON_SIZE_HEADER,
)
from utils.icon_utils import clear_icon_cache, get_icon


@pytest.fixture(autouse=True)
def reset_cache():
    clear_icon_cache()
    yield
    clear_icon_cache()


def test_get_icon_returns_ctk_image_for_all_keys():
    keys = [
        ICON_KEY_USER,
        ICON_KEY_BELL,
        ICON_KEY_HELP,
        ICON_KEY_THEME,
        ICON_KEY_QUIT,
        ICON_KEY_COPY,
    ]
    for key in keys:
        img = get_icon(key, size=ICON_SIZE_HEADER)
        assert isinstance(img, ctk.CTkImage)
        assert img._size == ICON_SIZE_HEADER


def test_get_icon_caching():
    img1 = get_icon(ICON_KEY_USER, size=ICON_SIZE_HEADER)
    img2 = get_icon(ICON_KEY_USER, size=ICON_SIZE_HEADER)
    assert img1._light_image is img2._light_image
    assert img1._dark_image is img2._dark_image

    # Different size produces different object
    img3 = get_icon(ICON_KEY_USER, size=(24, 24))
    assert img3._light_image is not img1._light_image
    assert img3._size == (24, 24)


def test_get_icon_quit_defaults_to_white():
    img = get_icon(ICON_KEY_QUIT, size=ICON_SIZE_HEADER)
    assert isinstance(img, ctk.CTkImage)


def test_get_icon_custom_colors():
    img = get_icon(
        ICON_KEY_BELL,
        size=ICON_SIZE_HEADER,
        light_color=COLOR_ICON_WHITE,
        dark_color=COLOR_ICON_WHITE,
    )
    assert isinstance(img, ctk.CTkImage)


def test_get_icon_procedural_fallback():
    with patch("utils.icon_utils.MDL2_PATH", "C:\\nonexistent_path\\segmdl2.ttf"):
        clear_icon_cache()
        for key in [
            ICON_KEY_USER,
            ICON_KEY_BELL,
            ICON_KEY_HELP,
            ICON_KEY_THEME,
            ICON_KEY_QUIT,
            ICON_KEY_COPY,
        ]:
            img = get_icon(key, size=ICON_SIZE_ACTION)
            assert isinstance(img, ctk.CTkImage)
            assert img._size == ICON_SIZE_ACTION


def test_clear_icon_cache():
    img1 = get_icon(ICON_KEY_HELP, size=ICON_SIZE_HEADER)
    clear_icon_cache()
    img2 = get_icon(ICON_KEY_HELP, size=ICON_SIZE_HEADER)
    assert img1._light_image is not img2._light_image
