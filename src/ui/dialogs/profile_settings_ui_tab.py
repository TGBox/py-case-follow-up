from typing import TYPE_CHECKING, Any
from collections.abc import Callable
import customtkinter as ctk

from enums import get_layout_display, get_layout_val_from_display, LAYOUT_DISPLAY, get_theme_display, get_theme_val_from_display
from services.i18n_service import tr, SUPPORTED_LANGUAGES, LANGUAGE_CODE_TO_DISPLAY, LANGUAGE_DISPLAY_TO_CODE, get_i18n

FONT_SCALE_OPTIONS: list[tuple[float, str, str]] = [
    (0.9, "profile.font_scale_90", "90% (Kompakt)"),
    (1.0, "profile.font_scale_100", "100% (Standard)"),
    (1.1, "profile.font_scale_110", "110% (Mittel)"),
    (1.2, "profile.font_scale_120", "120% (Groß)"),
    (1.3, "profile.font_scale_130", "130% (Sehr groß)"),
]


def get_font_scale_display(scale: float) -> str:
    for s, key, default in FONT_SCALE_OPTIONS:
        if abs(s - scale) < 0.04:
            return tr(key, default)
    pct = round(scale * 100)
    return f"{pct}%"


def get_font_scale_val_from_display(display_text: str) -> float:
    for s, key, default in FONT_SCALE_OPTIONS:
        if display_text == tr(key, default) or display_text == default:
            return s
    try:
        val = float(display_text.split("%")[0].strip()) / 100.0
        if 0.7 <= val <= 2.0:
            return val
    except Exception:
        pass
    return 1.0


class UiSettingsTabMixin:
    """Mixin for Appearance, Layout, Font Scaling, and Column Widths."""

    if TYPE_CHECKING:
        profile: Any
        storage_service: Any
        status_lbl: ctk.CTkLabel
        on_profile_updated: Callable[[], None] | None
        register_i18n: Callable[..., Any]
        _initial_font_scale: float
        _saved: bool

    def setup_ui_section(self, right_col: ctk.CTkFrame) -> None:
        self.appearance_hdr_lbl = self.register_i18n(
            ctk.CTkLabel(right_col, text=tr("profile.appearance_layout", "Erscheinungsbild & Layout"), font=ctk.CTkFont(size=14, weight="bold")),
            "profile.appearance_layout",
            "Erscheinungsbild & Layout",
        )
        self.appearance_hdr_lbl.pack(anchor="w", pady=(5, 5))

        self.lang_lbl = self.register_i18n(
            ctk.CTkLabel(right_col, text=tr("profile.language", "Sprache / Language:")),
            "profile.language",
            "Sprache / Language:",
        )
        self.lang_lbl.pack(anchor="w", pady=(5, 2))
        self.language_combo = ctk.CTkOptionMenu(
            right_col,
            values=list(SUPPORTED_LANGUAGES.values()),
            width=380,
        )
        curr_lang = getattr(self.profile.ui_settings, "language", "de")
        self.language_combo.set(LANGUAGE_CODE_TO_DISPLAY.get(curr_lang, "Deutsch"))
        self.language_combo.pack(anchor="w", pady=(0, 12))

        self.theme_lbl = self.register_i18n(
            ctk.CTkLabel(right_col, text=tr("profile.theme", "Farb-Thema (Theme):")),
            "profile.theme",
            "Farb-Thema (Theme):",
        )
        self.theme_lbl.pack(anchor="w", pady=(5, 2))
        self.theme_combo = ctk.CTkOptionMenu(right_col, values=[get_theme_display(v) for v in ("Dark", "Light", "System")], width=380)
        self.theme_combo.set(get_theme_display(self.profile.ui_settings.theme))
        self.theme_combo.pack(anchor="w", pady=(0, 12))

        self.font_scale_lbl = self.register_i18n(
            ctk.CTkLabel(right_col, text=tr("profile.font_scale", "Schriftgröße / Skalierung:")),
            "profile.font_scale",
            "Schriftgröße / Skalierung:",
        )
        self.font_scale_lbl.pack(anchor="w", pady=(5, 2))
        self.font_scale_combo = ctk.CTkOptionMenu(
            right_col,
            values=[get_font_scale_display(s) for s, _, _ in FONT_SCALE_OPTIONS],
            command=self.on_font_scale_preview,
            width=380,
        )
        self.font_scale_combo.set(get_font_scale_display(getattr(self.profile.ui_settings, "font_scale", 1.0)))
        self.font_scale_combo.pack(anchor="w", pady=(0, 12))

        self.default_layout_lbl = self.register_i18n(
            ctk.CTkLabel(right_col, text=tr("profile.default_layout", "Standard-Layout beim Start:")),
            "profile.default_layout",
            "Standard-Layout beim Start:",
        )
        self.default_layout_lbl.pack(anchor="w", pady=(5, 2))
        self.layout_combo = ctk.CTkOptionMenu(
            right_col,
            values=list(LAYOUT_DISPLAY.values()),
            width=380,
        )
        self.layout_combo.set(get_layout_display(self.profile.ui_settings.default_layout))
        self.layout_combo.pack(anchor="w", pady=(0, 12))

        self.popup_target_lbl = self.register_i18n(
            ctk.CTkLabel(right_col, text=tr("profile.popup_position", "Position zusätzlicher Fenster & Benachrichtigungen:")),
            "profile.popup_position",
            "Position zusätzlicher Fenster & Benachrichtigungen:",
        )
        self.popup_target_lbl.pack(anchor="w", pady=(5, 2))
        self.popup_target_combo = ctk.CTkOptionMenu(
            right_col,
            values=[tr("profile.popup_target_app", "App-Bildschirm (aktuell/zuletzt)"), tr("profile.popup_target_primary", "Hauptbildschirm")],
            width=380,
        )
        curr_target = getattr(self.profile.ui_settings, "popup_display_target", "APP_SCREEN")
        self.popup_target_combo.set(tr("profile.popup_target_app", "App-Bildschirm (aktuell/zuletzt)") if curr_target == "APP_SCREEN" else tr("profile.popup_target_primary", "Hauptbildschirm"))
        self.popup_target_combo.pack(anchor="w", pady=(0, 15))

        self.demo_switch = self.register_i18n(
            ctk.CTkSwitch(  # type: ignore[attr-defined]
                right_col,
                text=tr("profile.demo_data_toggle", "🧪 Beispieldaten (Demofälle & Demokunden) einblenden")
            ),
            "profile.demo_data_toggle",
            "🧪 Beispieldaten (Demofälle & Demokunden) einblenden",
        )
        if self.profile.ui_settings.show_demo_data is True:
            self.demo_switch.select()
        else:
            self.demo_switch.deselect()
        self.demo_switch.pack(anchor="w", pady=(0, 12))

        self.os_popup_switch = self.register_i18n(
            ctk.CTkSwitch(  # type: ignore[attr-defined]
                right_col,
                text=tr("profile.os_popup_toggle", "🔔 Windows-Systembenachrichtigungen (Toast) aktivieren")
            ),
            "profile.os_popup_toggle",
            "🔔 Windows-Systembenachrichtigungen (Toast) aktivieren",
        )
        if getattr(self.profile.reminder_settings, "os_popup_enabled", True):
            self.os_popup_switch.select()
        else:
            self.os_popup_switch.deselect()
        self.os_popup_switch.pack(anchor="w", pady=(0, 15))

        # Column widths reset section
        self.col_widths_hdr_lbl = self.register_i18n(
            ctk.CTkLabel(right_col, text=tr("profile.saved_widths", "Gespeicherte Spaltenbreiten (Profile-Level)"), font=ctk.CTkFont(size=14, weight="bold")),
            "profile.saved_widths",
            "Gespeicherte Spaltenbreiten (Profile-Level)",
        )
        self.col_widths_hdr_lbl.pack(anchor="w", pady=(5, 5))

        widths = self.profile.ui_settings.column_widths
        w_str = self._build_widths_str(widths)
        self.widths_label = ctk.CTkLabel(right_col, text=w_str, font=ctk.CTkFont(size=11), text_color=("gray40", "gray70"), justify="left", anchor="w")
        self.widths_label.pack(anchor="w", pady=(0, 10))

        self.btn_reset_widths = self.register_i18n(
            ctk.CTkButton(
                right_col,
                text=tr("profile.reset_widths_btn", "↻ Alle Spaltenbreiten auf Standard zurücksetzen"),
                command=self.on_reset_column_widths,
                fg_color=("gray45", "gray35"),
                hover_color=("gray35", "gray45"),
                text_color="white",
                width=380,
            ),
            "profile.reset_widths_btn",
            "↻ Alle Spaltenbreiten auf Standard zurücksetzen",
        )
        self.btn_reset_widths.pack(anchor="w", pady=(0, 10))

    def _build_widths_str(self, w_dict: dict) -> str:
        return tr(
            "profile.widths_summary",
            "• Cockpit: Links {left}px | Mitte {center}px | Rechts {right}px\n"
            "• Kanban-Board: Mindestspaltenbreite {board}px\n"
            "• Tabelle: ID {id}px | Praxis {prac}px | Titel {title}px | Score {score}px",
            left=w_dict.get('cockpit_left', 300),
            center=w_dict.get('cockpit_center', 420),
            right=w_dict.get('cockpit_right', 320),
            board=w_dict.get('board_column', 280),
            id=w_dict.get('table_col_id', 120),
            prac=w_dict.get('table_col_practice', 220),
            title=w_dict.get('table_col_title', 280),
            score=w_dict.get('table_col_score', 90),
        )

    def on_font_scale_preview(self, val: str) -> None:
        scale = get_font_scale_val_from_display(val)
        ctk.set_widget_scaling(scale)

    def on_reset_column_widths(self) -> None:
        self.profile.ui_settings.reset_column_widths()
        self.storage_service.save_profile(self.profile)
        widths = self.profile.ui_settings.column_widths
        self.widths_label.configure(text=self._build_widths_str(widths))
        self.status_lbl.configure(text=tr("profile.widths_reset_msg", "Alle Spaltenbreiten aller Ansichten auf Standard zurückgesetzt!"))
        if self.on_profile_updated:
            self.on_profile_updated()

    def reload_ui_fields(self) -> None:
        self.theme_combo.set(get_theme_display(self.profile.ui_settings.theme))
        if hasattr(self, "font_scale_combo"):
            self.font_scale_combo.set(get_font_scale_display(getattr(self.profile.ui_settings, "font_scale", 1.0)))
        self.layout_combo.set(get_layout_display(self.profile.ui_settings.default_layout))
        if hasattr(self, "popup_target_combo"):
            curr_target = getattr(self.profile.ui_settings, "popup_display_target", "APP_SCREEN")
            self.popup_target_combo.set(tr("profile.popup_target_app", "App-Bildschirm (aktuell/zuletzt)") if curr_target == "APP_SCREEN" else tr("profile.popup_target_primary", "Hauptbildschirm"))

    def save_ui_settings(self) -> bool:
        if hasattr(self, "language_combo"):
            lang_display = self.language_combo.get()
            lang_code = LANGUAGE_DISPLAY_TO_CODE.get(lang_display, "de")
            self.profile.ui_settings.language = lang_code
            get_i18n().current_language = lang_code

        self.profile.ui_settings.theme = get_theme_val_from_display(self.theme_combo.get())
        if hasattr(self, "font_scale_combo"):
            chosen_scale = get_font_scale_val_from_display(self.font_scale_combo.get())
            self.profile.ui_settings.font_scale = chosen_scale
            ctk.set_widget_scaling(chosen_scale)
            self._initial_font_scale = chosen_scale
        self._saved = True
        self.profile.ui_settings.default_layout = get_layout_val_from_display(self.layout_combo.get())
        if hasattr(self, "demo_switch"):
            self.profile.ui_settings.show_demo_data = bool(self.demo_switch.get())
        if hasattr(self, "os_popup_switch"):
            self.profile.reminder_settings.os_popup_enabled = bool(self.os_popup_switch.get())
        if hasattr(self, "popup_target_combo"):
            val = self.popup_target_combo.get()
            self.profile.ui_settings.popup_display_target = "PRIMARY_SCREEN" if "Hauptbildschirm" in val else "APP_SCREEN"
        return True

    def refresh_ui_tab_labels(self) -> None:
        if hasattr(self, "appearance_hdr_lbl"):
            self.appearance_hdr_lbl.configure(text=tr("profile.appearance_layout", "Erscheinungsbild & Layout"))
        if hasattr(self, "lang_lbl"):
            self.lang_lbl.configure(text=tr("profile.language", "Sprache / Language:"))
        if hasattr(self, "theme_lbl"):
            self.theme_lbl.configure(text=tr("profile.theme", "Farb-Thema (Theme):"))
        if hasattr(self, "font_scale_lbl"):
            self.font_scale_lbl.configure(text=tr("profile.font_scale", "Schriftgröße / Skalierung:"))
        if hasattr(self, "font_scale_combo"):
            curr_scale = getattr(self.profile.ui_settings, "font_scale", 1.0)
            self.font_scale_combo.configure(values=[get_font_scale_display(s) for s, _, _ in FONT_SCALE_OPTIONS])
            self.font_scale_combo.set(get_font_scale_display(curr_scale))
        if hasattr(self, "default_layout_lbl"):
            self.default_layout_lbl.configure(text=tr("profile.default_layout", "Standard-Layout beim Start:"))
        if hasattr(self, "demo_switch"):
            self.demo_switch.configure(text=tr("profile.demo_data_toggle", "🧪 Beispieldaten (Demofälle & Demokunden) in allen Ansichten einblenden"))
        if hasattr(self, "os_popup_switch"):
            self.os_popup_switch.configure(text=tr("profile.os_popup_toggle", "🔔 Windows-Systembenachrichtigungen (OS Native Toast) aktivieren"))
        if hasattr(self, "popup_target_lbl"):
            self.popup_target_lbl.configure(text=tr("profile.popup_position", "Position zusätzlicher Fenster & Benachrichtigungen:"))
        if hasattr(self, "popup_target_combo"):
            curr_target = getattr(self.profile.ui_settings, "popup_display_target", "APP_SCREEN")
            opt_app = tr("profile.popup_target_app", "App-Bildschirm (aktuell/zuletzt)")
            opt_pri = tr("profile.popup_target_primary", "Hauptbildschirm")
            self.popup_target_combo.configure(values=[opt_app, opt_pri])
            self.popup_target_combo.set(opt_app if curr_target == "APP_SCREEN" else opt_pri)
        if hasattr(self, "col_widths_hdr_lbl"):
            self.col_widths_hdr_lbl.configure(text=tr("profile.saved_widths", "Gespeicherte Spaltenbreiten (Profile-Level)"))
        if hasattr(self, "btn_reset_widths"):
            self.btn_reset_widths.configure(text=tr("profile.reset_widths_btn", "↻ Alle Spaltenbreiten auf Standard zurücksetzen"))
        if hasattr(self, "widths_label"):
            widths = self.profile.ui_settings.column_widths
            self.widths_label.configure(text=self._build_widths_str(widths))

    def setup_ui_tab(self) -> None:
        """Integrated into setup_user_tab; retained for backward compatibility."""
        pass
