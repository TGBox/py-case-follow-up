from typing import TYPE_CHECKING, Any
from collections.abc import Callable
import customtkinter as ctk

from constants import (
    BTN_WIDTH_NTFY_RANDOM,
    BTN_WIDTH_NTFY_TEST,
    COLOR_MUTED_GRAY_FG,
    COLOR_MUTED_GRAY_HOVER,
    COLOR_TEXT_WHITE,
    COLOR_TIP_TEXT,
    DEFAULT_COLUMN_WIDTHS,
    DEFAULT_NTFY_ENABLED,
    DEFAULT_NTFY_IDLE_MINUTES,
    DEFAULT_NTFY_NOTIFY_CUSTOMER_NOTES,
    DEFAULT_NTFY_NOTIFY_FOLLOWUPS,
    DEFAULT_NTFY_NOTIFY_HANDOVERS,
    DEFAULT_NTFY_NOTIFY_PRIO1,
    DEFAULT_NTFY_TOPIC,
    FONT_SIZE_BODY,
    FONT_SIZE_SM,
    FONT_SIZE_SUBTITLE,
    NTFY_IDLE_MINUTES_OPTIONS,
    NTFY_TAG_BELL,
    NTFY_TAG_TEST,
    PAD_MD,
    PAD_NONE,
    PAD_SM,
    PAD_TINY,
    PAD_XS,
    POPUP_DISPLAY_TARGETS,
    PROFILE_TAB_FIELD_WIDTH,
)
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


#: Key/default pairs for the popup target menu. Kept in one place so the
#: widget and its language refresh can never drift apart.
POPUP_TARGET_CHOICES = [
    ("profile.popup_target_app", "App-Bildschirm (aktuell/zuletzt)"),
    ("profile.popup_target_primary", "Hauptbildschirm"),
]


class UiSettingsTabMixin:
    """Mixin for Appearance, Layout, Font Scaling, and Column Widths."""

    if TYPE_CHECKING:
        profile: Any
        storage_service: Any
        status_lbl: ctk.CTkLabel
        on_profile_updated: Callable[[], None] | None
        register_i18n: Callable[..., Any]
        retranslate_choices: Callable[..., Any]
        selected_choice_index: Callable[..., int]
        winfo_toplevel: Callable[[], Any]
        _initial_font_scale: float
        _saved: bool

    def setup_ui_section(self, right_col: ctk.CTkFrame) -> None:
        self.appearance_hdr_lbl = self.register_i18n(
            ctk.CTkLabel(right_col, text=tr("profile.appearance_layout", "Erscheinungsbild & Layout"), font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight="bold")),
            "profile.appearance_layout",
            "Erscheinungsbild & Layout",
        )
        self.appearance_hdr_lbl.pack(anchor="w", pady=(PAD_SM, PAD_XS))

        self.lang_lbl = self.register_i18n(
            ctk.CTkLabel(right_col, text=tr("profile.language", "Sprache / Language:")),
            "profile.language",
            "Sprache / Language:",
        )
        self.lang_lbl.pack(anchor="w", pady=(PAD_XS, PAD_NONE))
        self.language_combo = ctk.CTkOptionMenu(
            right_col,
            values=list(SUPPORTED_LANGUAGES.values()),
            width=PROFILE_TAB_FIELD_WIDTH,
        )
        curr_lang = getattr(self.profile.ui_settings, "language", "de")
        self.language_combo.set(LANGUAGE_CODE_TO_DISPLAY.get(curr_lang, "Deutsch"))
        self.language_combo.pack(anchor="w", pady=(PAD_NONE, PAD_SM))

        self.theme_lbl = self.register_i18n(
            ctk.CTkLabel(right_col, text=tr("profile.theme", "Farb-Thema (Theme):")),
            "profile.theme",
            "Farb-Thema (Theme):",
        )
        self.theme_lbl.pack(anchor="w", pady=(PAD_XS, PAD_NONE))
        self.theme_combo = ctk.CTkOptionMenu(right_col, values=[get_theme_display(v) for v in ("Dark", "Light", "System")], width=PROFILE_TAB_FIELD_WIDTH)
        self.theme_combo.set(get_theme_display(self.profile.ui_settings.theme))
        self.theme_combo.pack(anchor="w", pady=(PAD_NONE, PAD_SM))

        self.font_scale_lbl = self.register_i18n(
            ctk.CTkLabel(right_col, text=tr("profile.font_scale", "Schriftgröße / Skalierung:")),
            "profile.font_scale",
            "Schriftgröße / Skalierung:",
        )
        self.font_scale_lbl.pack(anchor="w", pady=(PAD_XS, PAD_NONE))
        self.font_scale_combo = ctk.CTkOptionMenu(
            right_col,
            values=[get_font_scale_display(s) for s, _, _ in FONT_SCALE_OPTIONS],
            command=self.on_font_scale_preview,
            width=PROFILE_TAB_FIELD_WIDTH,
        )
        self.font_scale_combo.set(get_font_scale_display(getattr(self.profile.ui_settings, "font_scale", 1.0)))
        self.font_scale_combo.pack(anchor="w", pady=(PAD_NONE, PAD_SM))

        self.default_layout_lbl = self.register_i18n(
            ctk.CTkLabel(right_col, text=tr("profile.default_layout", "Standard-Layout beim Start:")),
            "profile.default_layout",
            "Standard-Layout beim Start:",
        )
        self.default_layout_lbl.pack(anchor="w", pady=(PAD_XS, PAD_NONE))
        self.layout_combo = ctk.CTkOptionMenu(
            right_col,
            values=list(LAYOUT_DISPLAY.values()),
            width=PROFILE_TAB_FIELD_WIDTH,
        )
        self.layout_combo.set(get_layout_display(self.profile.ui_settings.default_layout))
        self.layout_combo.pack(anchor="w", pady=(PAD_NONE, PAD_SM))

        self.popup_target_lbl = self.register_i18n(
            ctk.CTkLabel(right_col, text=tr("profile.popup_position", "Position zusätzlicher Fenster & Benachrichtigungen:")),
            "profile.popup_position",
            "Position zusätzlicher Fenster & Benachrichtigungen:",
        )
        self.popup_target_lbl.pack(anchor="w", pady=(PAD_XS, PAD_NONE))
        self.popup_target_combo = ctk.CTkOptionMenu(
            right_col,
            values=[tr(key, default) for key, default in POPUP_TARGET_CHOICES],
            width=PROFILE_TAB_FIELD_WIDTH,
        )
        curr_target = getattr(self.profile.ui_settings, "popup_display_target", "APP_SCREEN")
        self.popup_target_combo.set(tr("profile.popup_target_app", "App-Bildschirm (aktuell/zuletzt)") if curr_target == "APP_SCREEN" else tr("profile.popup_target_primary", "Hauptbildschirm"))
        self.popup_target_combo.pack(anchor="w", pady=(PAD_NONE, PAD_MD))

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
        self.demo_switch.pack(anchor="w", pady=(PAD_NONE, PAD_SM))

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
        self.os_popup_switch.pack(anchor="w", pady=(PAD_NONE, PAD_MD))

        # Smartphone Push (ntfy.sh) Section
        self.ntfy_hdr_lbl = self.register_i18n(
            ctk.CTkLabel(
                right_col,
                text=tr("ntfy.section_title", "📱 Smartphone-Push bei Abwesenheit (ntfy.sh)"),
                font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight="bold")
            ),
            "ntfy.section_title",
            "📱 Smartphone-Push bei Abwesenheit (ntfy.sh)",
        )
        self.ntfy_hdr_lbl.pack(anchor="w", pady=(PAD_SM, PAD_XS))

        self.ntfy_switch = self.register_i18n(
            ctk.CTkSwitch(  # type: ignore[attr-defined]
                right_col,
                text=tr("ntfy.enable_toggle", "📱 Smartphone-Push bei Abwesenheit aktivieren (ntfy.sh)"),
                command=self.on_toggle_ntfy,
            ),
            "ntfy.enable_toggle",
            "📱 Smartphone-Push bei Abwesenheit aktivieren (ntfy.sh)",
        )
        if getattr(self.profile.reminder_settings, "mobile_ntfy_enabled", DEFAULT_NTFY_ENABLED):
            self.ntfy_switch.select()
        else:
            self.ntfy_switch.deselect()
        self.ntfy_switch.pack(anchor="w", pady=(PAD_NONE, PAD_SM))

        self.ntfy_topic_lbl = self.register_i18n(
            ctk.CTkLabel(right_col, text=tr("ntfy.topic_label", "ntfy-Thema (Topic):")),
            "ntfy.topic_label",
            "ntfy-Thema (Topic):",
        )
        self.ntfy_topic_lbl.pack(anchor="w", pady=(PAD_XS, PAD_NONE))

        topic_frame = ctk.CTkFrame(right_col, fg_color="transparent")
        topic_frame.pack(anchor="w", fill="x", pady=(PAD_NONE, PAD_SM))

        self.ntfy_topic_entry = self.register_i18n(
            ctk.CTkEntry(
                topic_frame,
                placeholder_text=tr("ntfy.topic_placeholder", "z. B. desk-alert-8f2a9c"),
                width=170,
            ),
            "ntfy.topic_placeholder",
            "z. B. desk-alert-8f2a9c",
            attr="placeholder_text",
        )
        curr_topic = getattr(self.profile.reminder_settings, "mobile_ntfy_topic", DEFAULT_NTFY_TOPIC)
        if curr_topic:
            self.ntfy_topic_entry.insert(0, curr_topic)
        self.ntfy_topic_entry.pack(side="left", padx=(PAD_NONE, PAD_SM))

        self.ntfy_random_btn = self.register_i18n(
            ctk.CTkButton(
                topic_frame,
                text=tr("ntfy.btn_random_topic", "🎲 Zufall"),
                command=self.on_generate_random_ntfy_topic,
                width=BTN_WIDTH_NTFY_RANDOM,
                fg_color=COLOR_MUTED_GRAY_FG,
                hover_color=COLOR_MUTED_GRAY_HOVER,
            ),
            "ntfy.btn_random_topic",
            "🎲 Zufall",
        )
        self.ntfy_random_btn.pack(side="left", padx=(PAD_NONE, PAD_SM))

        self.ntfy_test_btn = self.register_i18n(
            ctk.CTkButton(
                topic_frame,
                text=tr("ntfy.btn_test_notification", "🔔 Testnachricht"),
                command=self.on_send_ntfy_test,
                width=BTN_WIDTH_NTFY_TEST,
                fg_color=COLOR_MUTED_GRAY_FG,
                hover_color=COLOR_MUTED_GRAY_HOVER,
            ),
            "ntfy.btn_test_notification",
            "🔔 Testnachricht",
        )
        self.ntfy_test_btn.pack(side="left")

        idle_frame = ctk.CTkFrame(right_col, fg_color="transparent")
        idle_frame.pack(anchor="w", fill="x", pady=(PAD_NONE, PAD_SM))

        self.ntfy_idle_lbl = self.register_i18n(
            ctk.CTkLabel(idle_frame, text=tr("ntfy.idle_threshold_label", "Aktivieren nach Inaktivität:")),
            "ntfy.idle_threshold_label",
            "Aktivieren nach Inaktivität:",
        )
        self.ntfy_idle_lbl.pack(side="left", padx=(PAD_NONE, PAD_SM))

        self.ntfy_idle_combo = ctk.CTkOptionMenu(
            idle_frame,
            values=[tr("ntfy.idle_minutes_format", "{minutes} Min.", minutes=m) for m in NTFY_IDLE_MINUTES_OPTIONS],
            width=100,
        )
        curr_mins = getattr(self.profile.reminder_settings, "mobile_ntfy_idle_minutes", DEFAULT_NTFY_IDLE_MINUTES)
        self.ntfy_idle_combo.set(tr("ntfy.idle_minutes_format", "{minutes} Min.", minutes=curr_mins))
        self.ntfy_idle_combo.pack(side="left")

        filter_frame = ctk.CTkFrame(right_col, fg_color="transparent")
        filter_frame.pack(anchor="w", fill="x", pady=(PAD_NONE, PAD_SM))

        self.ntfy_filter_hdr = self.register_i18n(
            ctk.CTkLabel(
                filter_frame,
                text=tr("ntfy.filter_header", "Benachrichtigen bei:"),
                font=ctk.CTkFont(size=FONT_SIZE_BODY, weight="bold"),
            ),
            "ntfy.filter_header",
            "Benachrichtigen bei:",
        )
        self.ntfy_filter_hdr.pack(anchor="w", pady=(PAD_XS, PAD_TINY))

        self.ntfy_cb_followups = self.register_i18n(
            ctk.CTkCheckBox(filter_frame, text=tr("ntfy.filter_followups", "Fällige Wiedervorlagen")),
            "ntfy.filter_followups",
            "Fällige Wiedervorlagen",
        )
        if getattr(self.profile.reminder_settings, "mobile_ntfy_notify_followups", DEFAULT_NTFY_NOTIFY_FOLLOWUPS):
            self.ntfy_cb_followups.select()
        else:
            self.ntfy_cb_followups.deselect()
        self.ntfy_cb_followups.pack(anchor="w", pady=(PAD_NONE, PAD_TINY))

        self.ntfy_cb_prio1 = self.register_i18n(
            ctk.CTkCheckBox(filter_frame, text=tr("ntfy.filter_prio1", "Dringlichkeit Notfall / Prio 1")),
            "ntfy.filter_prio1",
            "Dringlichkeit Notfall / Prio 1",
        )
        if getattr(self.profile.reminder_settings, "mobile_ntfy_notify_prio1", DEFAULT_NTFY_NOTIFY_PRIO1):
            self.ntfy_cb_prio1.select()
        else:
            self.ntfy_cb_prio1.deselect()
        self.ntfy_cb_prio1.pack(anchor="w", pady=(PAD_NONE, PAD_TINY))

        self.ntfy_cb_handovers = self.register_i18n(
            ctk.CTkCheckBox(filter_frame, text=tr("ntfy.filter_handovers", "Fall-Übergaben & Zuweisungen")),
            "ntfy.filter_handovers",
            "Fall-Übergaben & Zuweisungen",
        )
        if getattr(self.profile.reminder_settings, "mobile_ntfy_notify_handovers", DEFAULT_NTFY_NOTIFY_HANDOVERS):
            self.ntfy_cb_handovers.select()
        else:
            self.ntfy_cb_handovers.deselect()
        self.ntfy_cb_handovers.pack(anchor="w", pady=(PAD_NONE, PAD_TINY))

        self.ntfy_cb_notes = self.register_i18n(
            ctk.CTkCheckBox(filter_frame, text=tr("ntfy.filter_notes", "Neue Kunden-Notizen")),
            "ntfy.filter_notes",
            "Neue Kunden-Notizen",
        )
        if getattr(self.profile.reminder_settings, "mobile_ntfy_notify_customer_notes", DEFAULT_NTFY_NOTIFY_CUSTOMER_NOTES):
            self.ntfy_cb_notes.select()
        else:
            self.ntfy_cb_notes.deselect()
        self.ntfy_cb_notes.pack(anchor="w", pady=(PAD_NONE, PAD_TINY))

        self.ntfy_privacy_lbl = self.register_i18n(
            ctk.CTkLabel(
                right_col,
                text=tr("ntfy.privacy_tip", "🔒 Datensparsam: Keine Kunden- oder Patientendaten im Push-Payload."),
                font=ctk.CTkFont(size=FONT_SIZE_SM),
                text_color=COLOR_TIP_TEXT,
                justify="left",
                anchor="w",
            ),
            "ntfy.privacy_tip",
            "🔒 Datensparsam: Keine Kunden- oder Patientendaten im Push-Payload.",
        )
        self.ntfy_privacy_lbl.pack(anchor="w", pady=(PAD_NONE, PAD_MD))

        self.on_toggle_ntfy()

        # Column widths reset section
        self.col_widths_hdr_lbl = self.register_i18n(
            ctk.CTkLabel(right_col, text=tr("profile.saved_widths", "Gespeicherte Spaltenbreiten (Profile-Level)"), font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight="bold")),
            "profile.saved_widths",
            "Gespeicherte Spaltenbreiten (Profile-Level)",
        )
        self.col_widths_hdr_lbl.pack(anchor="w", pady=(PAD_SM, PAD_XS))

        widths = self.profile.ui_settings.column_widths
        w_str = self._build_widths_str(widths)
        self.widths_label = ctk.CTkLabel(right_col, text=w_str, font=ctk.CTkFont(size=FONT_SIZE_SM), text_color=COLOR_TIP_TEXT, justify="left", anchor="w")
        self.widths_label.pack(anchor="w", pady=(PAD_NONE, PAD_SM))

        self.btn_reset_widths = self.register_i18n(
            ctk.CTkButton(
                right_col,
                text=tr("profile.reset_widths_btn", "↻ Alle Spaltenbreiten auf Standard zurücksetzen"),
                command=self.on_reset_column_widths,
                fg_color=COLOR_MUTED_GRAY_FG,
                hover_color=COLOR_MUTED_GRAY_HOVER,
                text_color=COLOR_TEXT_WHITE,
                width=PROFILE_TAB_FIELD_WIDTH,
            ),
            "profile.reset_widths_btn",
            "↻ Alle Spaltenbreiten auf Standard zurücksetzen",
        )
        self.btn_reset_widths.pack(anchor="w", pady=(PAD_NONE, PAD_MD))

    def _build_widths_str(self, w_dict: dict) -> str:
        return tr(
            "profile.widths_summary",
            "• Cockpit: Links {left}px | Mitte {center}px | Rechts {right}px\n"
            "• Kanban-Board: Mindestspaltenbreite {board}px\n"
            "• Tabelle: ID {id}px | Praxis {prac}px | Titel {title}px | Score {score}px",
            left=w_dict.get('cockpit_left', DEFAULT_COLUMN_WIDTHS['cockpit_left']),
            center=w_dict.get('cockpit_center', DEFAULT_COLUMN_WIDTHS['cockpit_center']),
            right=w_dict.get('cockpit_right', DEFAULT_COLUMN_WIDTHS['cockpit_right']),
            board=w_dict.get('board_column', DEFAULT_COLUMN_WIDTHS['board_column']),
            id=w_dict.get('table_col_id', DEFAULT_COLUMN_WIDTHS['table_col_id']),
            prac=w_dict.get('table_col_practice', DEFAULT_COLUMN_WIDTHS['table_col_practice']),
            title=w_dict.get('table_col_title', DEFAULT_COLUMN_WIDTHS['table_col_title']),
            score=w_dict.get('table_col_score', DEFAULT_COLUMN_WIDTHS['table_col_score']),
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

    def on_toggle_ntfy(self) -> None:
        is_on = bool(self.ntfy_switch.get()) if hasattr(self, "ntfy_switch") else False
        state = "normal" if is_on else "disabled"
        for w in (
            getattr(self, "ntfy_topic_entry", None),
            getattr(self, "ntfy_random_btn", None),
            getattr(self, "ntfy_test_btn", None),
            getattr(self, "ntfy_idle_combo", None),
            getattr(self, "ntfy_cb_followups", None),
            getattr(self, "ntfy_cb_prio1", None),
            getattr(self, "ntfy_cb_handovers", None),
            getattr(self, "ntfy_cb_notes", None),
        ):
            if w is not None:
                w.configure(state=state)

    def on_generate_random_ntfy_topic(self) -> None:
        from services.ntfy_service import NtfyService
        rnd_topic = NtfyService.generate_random_topic()
        self.ntfy_topic_entry.delete(0, "end")
        self.ntfy_topic_entry.insert(0, rnd_topic)

    def on_send_ntfy_test(self) -> None:
        topic = self.ntfy_topic_entry.get().strip()
        if not topic:
            return
        from services.ntfy_service import NtfyService
        from ui.widgets.toast_notification import ToastNotification
        test_title = tr("ntfy.test_title", "🔔 Test: Support-Cockpit")
        test_msg = tr("ntfy.test_message", "Verbindung zu ntfy.sh erfolgreich! Smartphone-Push ist einsatzbereit.")
        success = NtfyService.send_notification(
            topic=topic,
            message=test_msg,
            title=test_title,
            tags=[NTFY_TAG_TEST, NTFY_TAG_BELL],
        )
        if success:
            ToastNotification(
                self.winfo_toplevel(),
                title=tr("ntfy.test_sent_toast_title", "📱 Testnachricht gesendet"),
                message=tr("ntfy.test_sent_toast_msg", "Testnachricht wurde an Thema '{topic}' gesendet.", topic=topic),
            )
        else:
            ToastNotification(
                self.winfo_toplevel(),
                title=tr("ntfy.test_failed_toast_title", "⚠ Testnachricht fehlgeschlagen"),
                message=tr("ntfy.test_failed_toast_msg", "Konnte Testnachricht nicht senden: {error}", error="Network error"),
            )

    def reload_ui_fields(self) -> None:
        if hasattr(self, "language_combo"):
            curr_lang = getattr(self.profile.ui_settings, "language", "de")
            self.language_combo.set(LANGUAGE_CODE_TO_DISPLAY.get(curr_lang, "Deutsch"))
        if hasattr(self, "theme_combo"):
            self.theme_combo.set(get_theme_display(self.profile.ui_settings.theme))
        if hasattr(self, "font_scale_combo"):
            self.font_scale_combo.set(get_font_scale_display(getattr(self.profile.ui_settings, "font_scale", 1.0)))
        if hasattr(self, "layout_combo"):
            self.layout_combo.set(get_layout_display(self.profile.ui_settings.default_layout))
        if hasattr(self, "popup_target_combo"):
            curr_target = getattr(self.profile.ui_settings, "popup_display_target", "APP_SCREEN")
            self.popup_target_combo.set(tr("profile.popup_target_app", "App-Bildschirm (aktuell/zuletzt)") if curr_target == "APP_SCREEN" else tr("profile.popup_target_primary", "Hauptbildschirm"))
        if hasattr(self, "demo_switch"):
            if self.profile.ui_settings.show_demo_data is True:
                self.demo_switch.select()
            else:
                self.demo_switch.deselect()
        if hasattr(self, "os_popup_switch"):
            if getattr(self.profile.reminder_settings, "os_popup_enabled", True):
                self.os_popup_switch.select()
            else:
                self.os_popup_switch.deselect()
        if hasattr(self, "ntfy_switch"):
            if getattr(self.profile.reminder_settings, "mobile_ntfy_enabled", DEFAULT_NTFY_ENABLED):
                self.ntfy_switch.select()
            else:
                self.ntfy_switch.deselect()
        if hasattr(self, "ntfy_topic_entry"):
            self.ntfy_topic_entry.delete(0, "end")
            self.ntfy_topic_entry.insert(0, getattr(self.profile.reminder_settings, "mobile_ntfy_topic", DEFAULT_NTFY_TOPIC))
        if hasattr(self, "ntfy_idle_combo"):
            curr_mins = getattr(self.profile.reminder_settings, "mobile_ntfy_idle_minutes", DEFAULT_NTFY_IDLE_MINUTES)
            self.ntfy_idle_combo.set(tr("ntfy.idle_minutes_format", "{minutes} Min.", minutes=curr_mins))
        if hasattr(self, "ntfy_cb_followups"):
            if getattr(self.profile.reminder_settings, "mobile_ntfy_notify_followups", DEFAULT_NTFY_NOTIFY_FOLLOWUPS):
                self.ntfy_cb_followups.select()
            else:
                self.ntfy_cb_followups.deselect()
        if hasattr(self, "ntfy_cb_prio1"):
            if getattr(self.profile.reminder_settings, "mobile_ntfy_notify_prio1", DEFAULT_NTFY_NOTIFY_PRIO1):
                self.ntfy_cb_prio1.select()
            else:
                self.ntfy_cb_prio1.deselect()
        if hasattr(self, "ntfy_cb_handovers"):
            if getattr(self.profile.reminder_settings, "mobile_ntfy_notify_handovers", DEFAULT_NTFY_NOTIFY_HANDOVERS):
                self.ntfy_cb_handovers.select()
            else:
                self.ntfy_cb_handovers.deselect()
        if hasattr(self, "ntfy_cb_notes"):
            if getattr(self.profile.reminder_settings, "mobile_ntfy_notify_customer_notes", DEFAULT_NTFY_NOTIFY_CUSTOMER_NOTES):
                self.ntfy_cb_notes.select()
            else:
                self.ntfy_cb_notes.deselect()
        self.on_toggle_ntfy()
        if hasattr(self, "widths_label"):
            widths = self.profile.ui_settings.column_widths
            self.widths_label.configure(text=self._build_widths_str(widths))

    def save_ui_settings(self) -> bool:
        import re
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
        if hasattr(self, "ntfy_switch"):
            self.profile.reminder_settings.mobile_ntfy_enabled = bool(self.ntfy_switch.get())
        if hasattr(self, "ntfy_topic_entry"):
            self.profile.reminder_settings.mobile_ntfy_topic = self.ntfy_topic_entry.get().strip()
        if hasattr(self, "ntfy_idle_combo"):
            raw_idle = self.ntfy_idle_combo.get()
            m = re.search(r"\d+", raw_idle)
            if m:
                self.profile.reminder_settings.mobile_ntfy_idle_minutes = int(m.group(0))
        if hasattr(self, "ntfy_cb_followups"):
            self.profile.reminder_settings.mobile_ntfy_notify_followups = bool(self.ntfy_cb_followups.get())
        if hasattr(self, "ntfy_cb_prio1"):
            self.profile.reminder_settings.mobile_ntfy_notify_prio1 = bool(self.ntfy_cb_prio1.get())
        if hasattr(self, "ntfy_cb_handovers"):
            self.profile.reminder_settings.mobile_ntfy_notify_handovers = bool(self.ntfy_cb_handovers.get())
        if hasattr(self, "ntfy_cb_notes"):
            self.profile.reminder_settings.mobile_ntfy_notify_customer_notes = bool(self.ntfy_cb_notes.get())
        if hasattr(self, "popup_target_combo"):
            # The menu shows translated labels; matching them against German text
            # picked APP_SCREEN for every non-German UI. The position is what
            # actually identifies the target, and POPUP_DISPLAY_TARGETS is kept
            # in the same order as POPUP_TARGET_CHOICES.
            index = self.selected_choice_index(self.popup_target_combo)
            self.profile.ui_settings.popup_display_target = POPUP_DISPLAY_TARGETS[
                min(index, len(POPUP_DISPLAY_TARGETS) - 1)
            ]
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
        if hasattr(self, "ntfy_hdr_lbl"):
            self.ntfy_hdr_lbl.configure(text=tr("ntfy.section_title", "📱 Smartphone-Push bei Abwesenheit (ntfy.sh)"))
        if hasattr(self, "ntfy_switch"):
            self.ntfy_switch.configure(text=tr("ntfy.enable_toggle", "📱 Smartphone-Push bei Abwesenheit aktivieren (ntfy.sh)"))
        if hasattr(self, "ntfy_topic_lbl"):
            self.ntfy_topic_lbl.configure(text=tr("ntfy.topic_label", "ntfy-Thema (Topic):"))
        if hasattr(self, "ntfy_random_btn"):
            self.ntfy_random_btn.configure(text=tr("ntfy.btn_random_topic", "🎲 Zufall"))
        if hasattr(self, "ntfy_test_btn"):
            self.ntfy_test_btn.configure(text=tr("ntfy.btn_test_notification", "🔔 Testnachricht"))
        if hasattr(self, "ntfy_idle_lbl"):
            self.ntfy_idle_lbl.configure(text=tr("ntfy.idle_threshold_label", "Aktivieren nach Inaktivität:"))
        if hasattr(self, "ntfy_idle_combo"):
            curr_mins = getattr(self.profile.reminder_settings, "mobile_ntfy_idle_minutes", DEFAULT_NTFY_IDLE_MINUTES)
            self.ntfy_idle_combo.configure(values=[tr("ntfy.idle_minutes_format", "{minutes} Min.", minutes=m) for m in NTFY_IDLE_MINUTES_OPTIONS])
            self.ntfy_idle_combo.set(tr("ntfy.idle_minutes_format", "{minutes} Min.", minutes=curr_mins))
        if hasattr(self, "ntfy_filter_hdr"):
            self.ntfy_filter_hdr.configure(text=tr("ntfy.filter_header", "Benachrichtigen bei:"))
        if hasattr(self, "ntfy_cb_followups"):
            self.ntfy_cb_followups.configure(text=tr("ntfy.filter_followups", "Fällige Wiedervorlagen"))
        if hasattr(self, "ntfy_cb_prio1"):
            self.ntfy_cb_prio1.configure(text=tr("ntfy.filter_prio1", "Dringlichkeit Notfall / Prio 1"))
        if hasattr(self, "ntfy_cb_handovers"):
            self.ntfy_cb_handovers.configure(text=tr("ntfy.filter_handovers", "Fall-Übergaben & Zuweisungen"))
        if hasattr(self, "ntfy_cb_notes"):
            self.ntfy_cb_notes.configure(text=tr("ntfy.filter_notes", "Neue Kunden-Notizen"))
        if hasattr(self, "ntfy_privacy_lbl"):
            self.ntfy_privacy_lbl.configure(text=tr("ntfy.privacy_tip", "🔒 Datensparsam: Keine Kunden- oder Patientendaten im Push-Payload."))
        if hasattr(self, "popup_target_lbl"):
            self.popup_target_lbl.configure(text=tr("profile.popup_position", "Position zusätzlicher Fenster & Benachrichtigungen:"))
        if hasattr(self, "popup_target_combo"):
            self.retranslate_choices(self.popup_target_combo, POPUP_TARGET_CHOICES)
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
