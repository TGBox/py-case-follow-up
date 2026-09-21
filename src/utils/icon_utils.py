"""Icon utility module for generating high-DPI, pixel-perfect CTkImage icons.

Provides in-memory rendered icons with supersampling and exact vertical/horizontal
centering, eliminating font-fallback baseline misalignment on Windows.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont

from constants import (
    COLOR_ICON_DARK_DEFAULT,
    COLOR_ICON_LIGHT_DEFAULT,
    COLOR_ICON_WHITE,
    ICON_KEY_BELL,
    ICON_KEY_COPY,
    ICON_KEY_HELP,
    ICON_KEY_QUIT,
    ICON_KEY_THEME,
    ICON_KEY_USER,
    ICON_SIZE_HEADER,
    ICON_SUPERSAMPLE_CANVAS_SIZE,
)

_PIL_ICON_CACHE: dict[tuple[str, tuple[int, int], str, str], tuple[Any, Any]] = {}

WINDIR = os.environ.get("WINDIR", "C:\\Windows")
MDL2_PATH = os.path.join(WINDIR, "Fonts", "segmdl2.ttf")

MDL2_GLYPHS: dict[str, str] = {
    ICON_KEY_USER: "\uE77B",  # Contact / User silhouette
    ICON_KEY_BELL: "\uEA8F",  # ActionCenter / Notification bell
    ICON_KEY_HELP: "\uE897",  # Help question mark
    ICON_KEY_THEME: "\uE771",  # Brightness / Contrast / Theme
    ICON_KEY_QUIT: "\uE711",  # ChromeClose / Cancel X
    ICON_KEY_COPY: "\uE8C8",  # Copy clipboard / two pages
}


def _draw_user_procedural(draw: Any, s: int, color: str) -> None:
    # Head
    draw.ellipse([s * 0.35, s * 0.14, s * 0.65, s * 0.44], fill=color)
    # Shoulders
    draw.chord([s * 0.18, s * 0.52, s * 0.82, s * 1.05], start=180, end=0, fill=color)


def _draw_bell_procedural(draw: Any, s: int, color: str) -> None:
    w = max(2, int(s * 0.08))
    # Top ring
    draw.ellipse([s * 0.44, s * 0.10, s * 0.56, s * 0.20], outline=color, width=w)
    # Bell body
    points = [
        (s * 0.50, s * 0.18),
        (s * 0.32, s * 0.38),
        (s * 0.26, s * 0.64),
        (s * 0.20, s * 0.72),
        (s * 0.80, s * 0.72),
        (s * 0.74, s * 0.64),
        (s * 0.68, s * 0.38),
    ]
    draw.polygon(points, fill=color)
    # Clapper
    draw.ellipse([s * 0.42, s * 0.74, s * 0.58, s * 0.86], fill=color)


def _draw_help_procedural(draw: Any, s: int, color: str) -> None:
    w = max(2, int(s * 0.09))
    box = [s * 0.12, s * 0.12, s * 0.88, s * 0.88]
    draw.ellipse(box, outline=color, width=w)
    # Question mark hook
    hook_box = [s * 0.35, s * 0.24, s * 0.65, s * 0.48]
    draw.arc(hook_box, start=180, end=0, fill=color, width=w)
    draw.line(
        [(s * 0.65, s * 0.36), (s * 0.50, s * 0.46), (s * 0.50, s * 0.56)],
        fill=color,
        width=w,
    )
    # Dot
    dot_r = s * 0.045
    draw.ellipse(
        [s * 0.5 - dot_r, s * 0.69 - dot_r, s * 0.5 + dot_r, s * 0.69 + dot_r],
        fill=color,
    )


def _draw_theme_procedural(draw: Any, s: int, color: str) -> None:
    w = max(2, int(s * 0.08))
    box = [s * 0.15, s * 0.15, s * 0.85, s * 0.85]
    draw.ellipse(box, outline=color, width=w)
    draw.pieslice(box, start=-90, end=90, fill=color)


def _draw_quit_procedural(draw: Any, s: int, color: str) -> None:
    w = max(2, int(s * 0.13))
    pad = s * 0.22
    draw.line([(pad, pad), (s - pad, s - pad)], fill=color, width=w)
    draw.line([(pad, s - pad), (s - pad, pad)], fill=color, width=w)


def _draw_copy_procedural(draw: Any, s: int, color: str) -> None:
    w = max(2, int(s * 0.08))
    # Back page
    draw.rectangle([s * 0.32, s * 0.14, s * 0.82, s * 0.68], outline=color, width=w)
    # Front page
    draw.rectangle(
        [s * 0.18, s * 0.32, s * 0.68, s * 0.86],
        fill=(0, 0, 0, 0),
        outline=color,
        width=w,
    )


_PROCEDURAL_DRAWERS: dict[
    str, Callable[[Any, int, str], None]
] = {
    ICON_KEY_USER: _draw_user_procedural,
    ICON_KEY_BELL: _draw_bell_procedural,
    ICON_KEY_HELP: _draw_help_procedural,
    ICON_KEY_THEME: _draw_theme_procedural,
    ICON_KEY_QUIT: _draw_quit_procedural,
    ICON_KEY_COPY: _draw_copy_procedural,
}


def _render_supersampled_image(name: str, color: str, canvas_size: int) -> Any:
    """Renders a single high-resolution supersampled image for the given icon and color."""
    img = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Prefer Segoe MDL2 Assets on Windows if present and key is mapped
    glyph = MDL2_GLYPHS.get(name)
    rendered_with_font = False
    if glyph and os.path.exists(MDL2_PATH):
        try:
            font_size = int(canvas_size * 0.72)
            font = ImageFont.truetype(MDL2_PATH, font_size)
            bbox = draw.textbbox((0, 0), glyph, font=font)
            gw = bbox[2] - bbox[0]
            gh = bbox[3] - bbox[1]
            x = (canvas_size - gw) // 2 - bbox[0]
            y = (canvas_size - gh) // 2 - bbox[1]
            draw.text((x, y), glyph, font=font, fill=color)
            rendered_with_font = True
        except Exception:
            rendered_with_font = False

    if not rendered_with_font:
        drawer = _PROCEDURAL_DRAWERS.get(name)
        if drawer is not None:
            drawer(draw, canvas_size, color)

    return img


class RobustCTkImage(ctk.CTkImage):
    """Subclass of CTkImage that binds PhotoImages to the caller widget's Tk root.

    CustomTkinter's default CTkImage calls `ImageTk.PhotoImage(...)` without a `master`
    argument, defaulting to `tkinter._default_root`. In test suites or multi-window
    environments where multiple `ctk.CTk` instances exist, this can cause
    `_tkinter.TclError: image 'pyimageX' does not exist`. `RobustCTkImage` resolves the
    calling widget to supply the proper `master` to each `PhotoImage`.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._robust_photo_cache: dict[tuple[tuple[int, int], Any, str], Any] = {}

    def _resolve_master(self) -> Any:
        import sys

        for i in range(1, 5):
            try:
                frame = sys._getframe(i)
                w = frame.f_locals.get("self")
                if hasattr(w, "winfo_toplevel"):
                    return w
            except Exception:
                pass
        return None

    def _get_scaled_light_photo_image(self, scaled_size: tuple[int, int]) -> Any:
        from PIL import ImageTk

        master = self._resolve_master()
        master_key = getattr(master, "_w", None)
        key = (scaled_size, master_key, "light")
        if key in self._robust_photo_cache:
            return self._robust_photo_cache[key]

        img = self._light_image.resize(scaled_size) if self._light_image else None
        photo = ImageTk.PhotoImage(img, master=master) if img else None
        self._robust_photo_cache[key] = photo
        return photo

    def _get_scaled_dark_photo_image(self, scaled_size: tuple[int, int]) -> Any:
        from PIL import ImageTk

        master = self._resolve_master()
        master_key = getattr(master, "_w", None)
        key = (scaled_size, master_key, "dark")
        if key in self._robust_photo_cache:
            return self._robust_photo_cache[key]

        img = self._dark_image.resize(scaled_size) if self._dark_image else None
        photo = ImageTk.PhotoImage(img, master=master) if img else None
        self._robust_photo_cache[key] = photo
        return photo


def get_icon(
    name: str,
    size: tuple[int, int] = ICON_SIZE_HEADER,
    light_color: str | None = None,
    dark_color: str | None = None,
) -> ctk.CTkImage:
    """Returns a cached CTkImage for the specified icon key and size.

    Parameters
    ----------
    name : str
        Icon identifier (e.g. ICON_KEY_USER, ICON_KEY_BELL, ICON_KEY_HELP,
        ICON_KEY_THEME, ICON_KEY_QUIT, ICON_KEY_COPY).
    size : tuple[int, int]
        Destination dimensions (w, h) in pixels.
    light_color : str, optional
        Color override for light theme.
    dark_color : str, optional
        Color override for dark theme.

    Returns
    -------
    ctk.CTkImage
        CustomTkinter image ready to be bound to a widget's `image` parameter.
    """
    if name == ICON_KEY_QUIT:
        eff_light = light_color or COLOR_ICON_WHITE
        eff_dark = dark_color or COLOR_ICON_WHITE
    else:
        eff_light = light_color or COLOR_ICON_LIGHT_DEFAULT
        eff_dark = dark_color or COLOR_ICON_DARK_DEFAULT

    cache_key = (name, size, eff_light, eff_dark)
    cached_images = _PIL_ICON_CACHE.get(cache_key)
    if cached_images is not None:
        img_light, img_dark = cached_images
    else:
        img_light_hi = _render_supersampled_image(
            name, eff_light, ICON_SUPERSAMPLE_CANVAS_SIZE
        )
        img_dark_hi = _render_supersampled_image(
            name, eff_dark, ICON_SUPERSAMPLE_CANVAS_SIZE
        )

        img_light = img_light_hi.resize(size, Image.Resampling.LANCZOS)
        img_dark = img_dark_hi.resize(size, Image.Resampling.LANCZOS)
        _PIL_ICON_CACHE[cache_key] = (img_light, img_dark)

    return RobustCTkImage(
        light_image=img_light, dark_image=img_dark, size=size
    )


def clear_icon_cache() -> None:
    """Clears the icon cache."""
    _PIL_ICON_CACHE.clear()
