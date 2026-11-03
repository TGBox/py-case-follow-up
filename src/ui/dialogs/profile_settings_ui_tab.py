import threading
from typing import TYPE_CHECKING, Any
from collections.abc import Callable
import customtkinter as ctk

from constants import (
    BTN_WIDTH_NTFY_QR,
    BTN_WIDTH_NTFY_RANDOM,
    BTN_WIDTH_NTFY_TEST,
    COLOR_MUTED_GRAY_FG,
    COLOR_MUTED_GRAY_HOVER,
    COLOR_TEXT_WHITE,
    COLOR_TIP_TEXT,
    COMBO_WIDTH_NTFY_DIGEST,
    COMBO_WIDTH_NTFY_IDLE,
    DEFAULT_COLUMN_WIDTHS,
    DEFAULT_FOLLOWUP_REPEAT_MINUTES,
    DEFAULT_NTFY_DIGEST_ENABLED,
    DEFAULT_NTFY_DIGEST_MINUTES,
    DEFAULT_NTFY_ENABLED,
    DEFAULT_NTFY_IDLE_MINUTES,
    DEFAULT_NTFY_NOTIFY_CUSTOMER_NOTES,
    DEFAULT_NTFY_NOTIFY_FOLLOWUPS,
    DEFAULT_NTFY_NOTIFY_HANDOVERS,
    DEFAULT_NTFY_NOTIFY_PRIO1,
    DEFAULT_NTFY_ON_CALL,
    DEFAULT_NTFY_AUTO_PRESENCE,
    DEFAULT_NTFY_REMOTE_CONTROL,
    DEFAULT_NTFY_RESPONSE_TOPIC,
    DEFAULT_NTFY_TOPIC,
    DEFAULT_UNLOCK_NOTIFICATION_ENABLED,
    DEFAULT_UNLOCK_NOTIFICATION_TEXT,
    ENTRY_WIDTH_NTFY_TOPIC,
    ENTRY_WIDTH_UNLOCK_NOTIFICATION,
    FONT_SIZE_BODY,
    FONT_SIZE_SM,
    FONT_SIZE_SUBTITLE,
    FOLLOWUP_REPEAT_MINUTES_OPTIONS,
    NTFY_DIGEST_MINUTES_OPTIONS,
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
    CHECKOUT_AUTO_OPEN_MODE_CHOICES,
    CHECKOUT_AUTO_OPEN_MODE_KEYS,
    CHECKOUT_MODE_WEEKDAYS,
    ENTRY_WIDTH_CHECKOUT_NUMERIC,
    ENTRY_WIDTH_CHECKOUT_TIME,
    ENTRY_WIDTH_CHECKOUT_LEAD,
    ENTRY_WIDTH_CHECKOUT_PLACE,
    BTN_WIDTH_CHECK_STOP,
    COLOR_PANEL_BG,
    COLOR_PANEL_BORDER,
    COLOR_SETTINGS_NAV_HOVER,
    COLOR_SETTINGS_NAV_TEXT,
    COLOR_TRANSIT_COUNTDOWN_WARN,
    COLOR_TRANSIT_DELAY,
    COLOR_TRANSIT_ONTIME,
    CORNER_RADIUS_MD,
    SETTINGS_NAV_ITEM_HEIGHT,
    SETTINGS_STOP_STATUS_WRAP,
    TRANSIT_STOP_SEARCH_DEBOUNCE_MS,
    TRANSIT_STOP_SEARCH_MIN_CHARS,
)
from enums import get_layout_display, get_layout_val_from_display, LAYOUT_DISPLAY, get_theme_display, get_theme_val_from_display
from ui.widgets.collapsible_section import CollapsibleSection
from services.i18n_service import tr, SUPPORTED_LANGUAGES, LANGUAGE_CODE_TO_DISPLAY, LANGUAGE_DISPLAY_TO_CODE, get_i18n

FONT_SCALE_OPTIONS: list[tuple[float, str, str]] = [
    (0.9, "profile.font_scale_90", "90% (Kompakt)"),
    (1.0, "profile.font_scale_100", "100% (Standard)"),
    (1.1, "profile.font_scale_110", "110% (Mittel)"),
    (1.2, "profile.font_scale_120", "120% (Groß)"),
    (1.3, "profile.font_scale_130", "130% (Sehr groß)"),
]


def get_followup_repeat_display(minutes: int) -> str:
    if minutes <= 0:
        return tr("profile.followup_repeat_off", "Aus")
    return tr("ntfy.idle_minutes_format", "{minutes} Min.", minutes=minutes)


def get_followup_repeat_minutes_from_display(display_text: str) -> int | None:
    """Minutes for a repeat-menu entry, or None when the text is not an option."""
    for minutes in FOLLOWUP_REPEAT_MINUTES_OPTIONS:
        if display_text == get_followup_repeat_display(minutes):
            return minutes
    return None


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
        """Builds every section of this mixin into one frame (pre-sidebar layout)."""
        self.setup_appearance_section(right_col)
        self.setup_notifications_section(right_col)
        self.setup_ntfy_section(right_col)
        self.setup_column_widths_section(right_col)
        self.setup_checkout_section(right_col)

    def setup_appearance_section(self, right_col: ctk.CTkFrame) -> None:
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

    def setup_notifications_section(self, right_col: ctk.CTkFrame) -> None:
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
        self.os_popup_switch.pack(anchor="w", pady=(PAD_NONE, PAD_SM))

        repeat_frame = ctk.CTkFrame(right_col, fg_color="transparent")
        repeat_frame.pack(anchor="w", fill="x", pady=(PAD_NONE, PAD_MD))
        self.followup_repeat_lbl = self.register_i18n(
            ctk.CTkLabel(repeat_frame, text=tr("profile.followup_repeat_label", "Erneut erinnern, solange fällig:")),
            "profile.followup_repeat_label",
            "Erneut erinnern, solange fällig:",
        )
        self.followup_repeat_lbl.pack(side="left", padx=(PAD_NONE, PAD_SM))
        self.followup_repeat_combo = ctk.CTkOptionMenu(
            repeat_frame,
            values=[get_followup_repeat_display(m) for m in FOLLOWUP_REPEAT_MINUTES_OPTIONS],
            width=COMBO_WIDTH_NTFY_IDLE,
        )
        self.followup_repeat_combo.set(
            get_followup_repeat_display(getattr(self.profile.reminder_settings, "followup_repeat_minutes", DEFAULT_FOLLOWUP_REPEAT_MINUTES))
        )
        self.followup_repeat_combo.pack(side="left")

        # Workstation Unlock Notification
        self.unlock_notify_cb = self.register_i18n(
            ctk.CTkCheckBox(
                right_col,
                text=tr("ntfy.unlock_notification_toggle", "🖥 Benachrichtigung nach Entsperren des Bildschirms anzeigen"),
                command=self.on_toggle_unlock_notify,
            ),
            "ntfy.unlock_notification_toggle",
            "🖥 Benachrichtigung nach Entsperren des Bildschirms anzeigen",
        )
        if getattr(self.profile.reminder_settings, "unlock_notification_enabled", DEFAULT_UNLOCK_NOTIFICATION_ENABLED):
            self.unlock_notify_cb.select()
        else:
            self.unlock_notify_cb.deselect()
        self.unlock_notify_cb.pack(anchor="w", pady=(PAD_NONE, PAD_XS))

        self.unlock_notify_frame = ctk.CTkFrame(right_col, fg_color="transparent")
        self.unlock_notify_frame.pack(anchor="w", fill="x", pady=(PAD_NONE, PAD_MD))

        self.unlock_notify_lbl = self.register_i18n(
            ctk.CTkLabel(
                self.unlock_notify_frame,
                text=tr("ntfy.unlock_notification_text_label", "Eigener Benachrichtigungstext:"),
                font=ctk.CTkFont(size=FONT_SIZE_SM),
            ),
            "ntfy.unlock_notification_text_label",
            "Eigener Benachrichtigungstext:",
        )
        self.unlock_notify_lbl.pack(anchor="w", pady=(PAD_NONE, PAD_XS))

        self.unlock_notify_entry = ctk.CTkEntry(
            self.unlock_notify_frame,
            width=ENTRY_WIDTH_UNLOCK_NOTIFICATION,
            placeholder_text=tr(
                "ntfy.unlock_notification_placeholder",
                "z. B. Willkommen zurück! Bitte offene Wiedervorlagen prüfen.",
            ),
        )
        saved_unlock_text = getattr(self.profile.reminder_settings, "unlock_notification_text", DEFAULT_UNLOCK_NOTIFICATION_TEXT)
        if saved_unlock_text:
            self.unlock_notify_entry.insert(0, saved_unlock_text)
        self.unlock_notify_entry.pack(anchor="w", pady=(PAD_NONE, PAD_XS))
        if not getattr(self.profile.reminder_settings, "unlock_notification_enabled", DEFAULT_UNLOCK_NOTIFICATION_ENABLED):
            self.unlock_notify_entry.configure(state="disabled")

    def setup_ntfy_section(self, right_col: ctk.CTkFrame) -> None:
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
        self.ntfy_switch.pack(anchor="w", pady=(PAD_NONE, PAD_MD))

        # Everything below the switch only matters while push is on.
        self.ntfy_details_frame = ctk.CTkFrame(right_col, fg_color="transparent")
        details = self.ntfy_details_frame

        self.ntfy_topic_lbl = self.register_i18n(
            ctk.CTkLabel(details, text=tr("ntfy.topic_label", "ntfy-Thema (Topic):")),
            "ntfy.topic_label",
            "ntfy-Thema (Topic):",
        )
        self.ntfy_topic_lbl.pack(anchor="w", pady=(PAD_XS, PAD_NONE))

        topic_frame = ctk.CTkFrame(details, fg_color="transparent")
        topic_frame.pack(anchor="w", fill="x", pady=(PAD_NONE, PAD_SM))

        self.ntfy_topic_entry = self.register_i18n(
            ctk.CTkEntry(
                topic_frame,
                placeholder_text=tr("ntfy.topic_placeholder", "z. B. desk-alert-8f2a9c"),
                width=ENTRY_WIDTH_NTFY_TOPIC,
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
        self.ntfy_test_btn.pack(side="left", padx=(PAD_NONE, PAD_SM))

        self.ntfy_qr_btn = self.register_i18n(
            ctk.CTkButton(
                topic_frame,
                text=tr("ntfy.btn_qr_code", "📲 QR-Code"),
                command=self.on_show_ntfy_qr,
                width=BTN_WIDTH_NTFY_QR,
                fg_color=COLOR_MUTED_GRAY_FG,
                hover_color=COLOR_MUTED_GRAY_HOVER,
            ),
            "ntfy.btn_qr_code",
            "📲 QR-Code",
        )
        self.ntfy_qr_btn.pack(side="left")

        idle_frame = ctk.CTkFrame(details, fg_color="transparent")
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
            width=COMBO_WIDTH_NTFY_IDLE,
        )
        curr_mins = getattr(self.profile.reminder_settings, "mobile_ntfy_idle_minutes", DEFAULT_NTFY_IDLE_MINUTES)
        self.ntfy_idle_combo.set(tr("ntfy.idle_minutes_format", "{minutes} Min.", minutes=curr_mins))
        self.ntfy_idle_combo.pack(side="left")

        filter_frame = ctk.CTkFrame(details, fg_color="transparent")
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

        self.ntfy_cb_on_call = self.register_i18n(
            ctk.CTkCheckBox(
                filter_frame,
                text=tr("ntfy.filter_on_call", "Notdienst / Rufbereitschaft (Inaktivitätszwang übergehen)"),
            ),
            "ntfy.filter_on_call",
            "Notdienst / Rufbereitschaft (Inaktivitätszwang übergehen)",
        )
        if getattr(self.profile.reminder_settings, "mobile_ntfy_on_call", DEFAULT_NTFY_ON_CALL):
            self.ntfy_cb_on_call.select()
        else:
            self.ntfy_cb_on_call.deselect()
        self.ntfy_cb_on_call.pack(anchor="w", pady=(PAD_NONE, PAD_TINY))

        self.ntfy_cb_auto_presence = self.register_i18n(
            ctk.CTkCheckBox(
                filter_frame,
                text=tr("ntfy.filter_auto_presence", "Abwesenheitsstatus im Team bei Bildschirmsperre automatisch setzen"),
            ),
            "ntfy.filter_auto_presence",
            "Abwesenheitsstatus im Team bei Bildschirmsperre automatisch setzen",
        )
        if getattr(self.profile.reminder_settings, "mobile_ntfy_auto_presence", DEFAULT_NTFY_AUTO_PRESENCE):
            self.ntfy_cb_auto_presence.select()
        else:
            self.ntfy_cb_auto_presence.deselect()
        self.ntfy_cb_auto_presence.pack(anchor="w", pady=(PAD_NONE, PAD_TINY))

        # Rarely changed options stay folded away.
        self.ntfy_advanced_section = CollapsibleSection(
            details,
            title=tr("ntfy.advanced_heading", "Erweitert: Sammelbericht und Fernsteuerung"),
            expanded=bool(
                getattr(self.profile.reminder_settings, "mobile_ntfy_digest_enabled", DEFAULT_NTFY_DIGEST_ENABLED)
                or getattr(self.profile.reminder_settings, "mobile_ntfy_remote_control", DEFAULT_NTFY_REMOTE_CONTROL)
            ),
        )
        self.ntfy_advanced_section.pack(fill="x", pady=(PAD_SM, PAD_SM))
        advanced = self.ntfy_advanced_section.body

        # Smart Digest (Stufe 3)
        digest_frame = ctk.CTkFrame(advanced, fg_color="transparent")
        digest_frame.pack(fill="x", pady=(PAD_XS, PAD_NONE))

        self.ntfy_cb_digest = self.register_i18n(
            ctk.CTkCheckBox(
                digest_frame,
                text=tr("ntfy.digest_enable", "Sammelbericht für Routine-Ereignisse (Digest)"),
                command=self.on_toggle_ntfy,
            ),
            "ntfy.digest_enable",
            "Sammelbericht für Routine-Ereignisse (Digest)",
        )
        if getattr(self.profile.reminder_settings, "mobile_ntfy_digest_enabled", DEFAULT_NTFY_DIGEST_ENABLED):
            self.ntfy_cb_digest.select()
        else:
            self.ntfy_cb_digest.deselect()
        self.ntfy_cb_digest.pack(anchor="w", pady=(PAD_NONE, PAD_TINY))

        digest_cfg_frame = ctk.CTkFrame(digest_frame, fg_color="transparent")
        digest_cfg_frame.pack(fill="x", padx=(PAD_MD, PAD_NONE), pady=(PAD_NONE, PAD_TINY))

        self.ntfy_digest_interval_lbl = self.register_i18n(
            ctk.CTkLabel(
                digest_cfg_frame,
                text=tr("ntfy.digest_interval_lbl", "Intervall (Minuten):"),
                font=ctk.CTkFont(size=FONT_SIZE_BODY),
            ),
            "ntfy.digest_interval_lbl",
            "Intervall (Minuten):",
        )
        self.ntfy_digest_interval_lbl.pack(side="left", padx=(PAD_NONE, PAD_SM))

        self.ntfy_combo_digest_minutes = ctk.CTkOptionMenu(
            digest_cfg_frame,
            values=[str(m) for m in NTFY_DIGEST_MINUTES_OPTIONS],
            width=COMBO_WIDTH_NTFY_DIGEST,
        )
        current_digest_mins = getattr(self.profile.reminder_settings, "mobile_ntfy_digest_minutes", DEFAULT_NTFY_DIGEST_MINUTES)
        self.ntfy_combo_digest_minutes.set(str(current_digest_mins))
        self.ntfy_combo_digest_minutes.pack(side="left")

        self.ntfy_digest_hint_lbl = self.register_i18n(
            ctk.CTkLabel(
                digest_frame,
                text=tr("ntfy.digest_hint", "⚡ Prio-1 Notfälle umgehen den Sammelbericht und werden sofort gesendet."),
                font=ctk.CTkFont(size=FONT_SIZE_SM),
                text_color=COLOR_TIP_TEXT,
                justify="left",
                anchor="w",
            ),
            "ntfy.digest_hint",
            "⚡ Prio-1 Notfälle umgehen den Sammelbericht und werden sofort gesendet.",
        )
        self.ntfy_digest_hint_lbl.pack(anchor="w", padx=(PAD_MD, PAD_NONE), pady=(PAD_NONE, PAD_TINY))

        # Remote Control (Stufe 6)
        rc_frame = ctk.CTkFrame(advanced, fg_color="transparent")
        rc_frame.pack(fill="x", pady=(PAD_XS, PAD_NONE))

        self.ntfy_cb_remote_control = self.register_i18n(
            ctk.CTkCheckBox(
                rc_frame,
                text=tr("ntfy.remote_control_enable", "Fernsteuerung & Aktions-Buttons aktivieren"),
                command=self.on_toggle_ntfy,
            ),
            "ntfy.remote_control_enable",
            "Fernsteuerung & Aktions-Buttons aktivieren",
        )
        if getattr(self.profile.reminder_settings, "mobile_ntfy_remote_control", DEFAULT_NTFY_REMOTE_CONTROL):
            self.ntfy_cb_remote_control.select()
        else:
            self.ntfy_cb_remote_control.deselect()
        self.ntfy_cb_remote_control.pack(anchor="w", pady=(PAD_NONE, PAD_TINY))

        rc_cfg_frame = ctk.CTkFrame(rc_frame, fg_color="transparent")
        rc_cfg_frame.pack(fill="x", padx=(PAD_MD, PAD_NONE), pady=(PAD_NONE, PAD_TINY))

        self.ntfy_response_topic_lbl = self.register_i18n(
            ctk.CTkLabel(
                rc_cfg_frame,
                text=tr("ntfy.response_topic_label", "Befehls-Thema (optional):"),
                font=ctk.CTkFont(size=FONT_SIZE_BODY),
            ),
            "ntfy.response_topic_label",
            "Befehls-Thema (optional):",
        )
        self.ntfy_response_topic_lbl.pack(side="left", padx=(PAD_NONE, PAD_SM))

        self.ntfy_entry_response_topic = ctk.CTkEntry(
            rc_cfg_frame,
            width=ENTRY_WIDTH_NTFY_TOPIC,
            placeholder_text=tr("ntfy.response_topic_placeholder", "Standard: {topic}-cmd"),
        )
        saved_resp_topic = getattr(self.profile.reminder_settings, "mobile_ntfy_response_topic", DEFAULT_NTFY_RESPONSE_TOPIC)
        if saved_resp_topic:
            self.ntfy_entry_response_topic.insert(0, saved_resp_topic)
        self.ntfy_entry_response_topic.pack(side="left")

        self.ntfy_remote_control_hint_lbl = self.register_i18n(
            ctk.CTkLabel(
                rc_frame,
                text=tr("ntfy.remote_control_hint", "⚡ Ermöglicht Aktionen (Schlummern, Übernehmen) per Knopfdruck am Smartphone."),
                font=ctk.CTkFont(size=FONT_SIZE_SM),
                text_color=COLOR_TIP_TEXT,
                justify="left",
                anchor="w",
            ),
            "ntfy.remote_control_hint",
            "⚡ Ermöglicht Aktionen (Schlummern, Übernehmen) per Knopfdruck am Smartphone.",
        )
        self.ntfy_remote_control_hint_lbl.pack(anchor="w", padx=(PAD_MD, PAD_NONE), pady=(PAD_NONE, PAD_TINY))

        self.ntfy_privacy_lbl = self.register_i18n(
            ctk.CTkLabel(
                details,
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

    def setup_column_widths_section(self, right_col: ctk.CTkFrame) -> None:
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

    def setup_checkout_section(self, right_col: ctk.CTkFrame) -> None:
        cs = getattr(self.profile, "checkout_settings", None)
        if cs is None:
            from models.profile import CheckoutSettings
            cs = CheckoutSettings()
            self.profile.checkout_settings = cs

        # Enable panel; the schedule below it only matters while this is on.
        self.checkout_enable_var = ctk.BooleanVar(value=cs.enabled)
        self.checkout_enable_cb = self.register_i18n(
            ctk.CTkSwitch(  # type: ignore[attr-defined]
                right_col,
                text=tr("settings_checkout.enable_panel", "Feierabend-Panel aktivieren"),
                variable=self.checkout_enable_var,
                command=self._update_checkout_enabled_visibility,
            ),
            "settings_checkout.enable_panel",
            "Feierabend-Panel aktivieren",
        )
        self.checkout_enable_cb.pack(anchor="w", pady=(PAD_NONE, PAD_SM))

        # Independent of the schedule: a panel opened by hand stays open across restarts.
        self.checkout_remember_var = ctk.BooleanVar(value=bool(getattr(cs, "remember_visibility", False)))
        self.checkout_remember_cb = self.register_i18n(
            ctk.CTkSwitch(  # type: ignore[attr-defined]
                right_col,
                text=tr("settings_checkout.remember_visibility", "Nach dem Neustart wieder öffnen, wenn das Panel zuletzt offen war"),
                variable=self.checkout_remember_var,
            ),
            "settings_checkout.remember_visibility",
            "Nach dem Neustart wieder öffnen, wenn das Panel zuletzt offen war",
        )
        self.checkout_remember_cb.pack(anchor="w", pady=(PAD_NONE, PAD_MD))

        self.checkout_schedule_frame = ctk.CTkFrame(right_col, fg_color="transparent")
        schedule = self.checkout_schedule_frame

        self.checkout_auto_open_var = ctk.BooleanVar(value=cs.auto_open)
        self.checkout_auto_open_cb = self.register_i18n(
            ctk.CTkCheckBox(
                schedule,
                text=tr("settings_checkout.auto_open", "Automatisch zur Feierabendzeit einblenden"),
                variable=self.checkout_auto_open_var,
            ),
            "settings_checkout.auto_open",
            "Automatisch zur Feierabendzeit einblenden",
        )
        self.checkout_auto_open_cb.pack(anchor="w", pady=(PAD_NONE, PAD_MD))

        mode_row = ctk.CTkFrame(schedule, fg_color="transparent")
        mode_row.pack(anchor="w", fill="x", pady=(PAD_NONE, PAD_SM))

        self.checkout_mode_lbl = self.register_i18n(
            ctk.CTkLabel(mode_row, text=tr("settings_checkout.schedule_mode", "Zeitplan-Modus:")),
            "settings_checkout.schedule_mode",
            "Zeitplan-Modus:",
        )
        self.checkout_mode_lbl.pack(side="left", padx=(PAD_NONE, PAD_SM))

        mode_choices = [tr(k, d) for k, d in CHECKOUT_AUTO_OPEN_MODE_CHOICES]
        self.checkout_mode_combo = ctk.CTkOptionMenu(
            mode_row,
            values=mode_choices,
            width=PROFILE_TAB_FIELD_WIDTH,
            command=self._on_checkout_mode_changed,
        )
        init_mode = (
            mode_choices[1]
            if cs.auto_open_mode == CHECKOUT_MODE_WEEKDAYS
            else mode_choices[0]
        )
        self.checkout_mode_combo.set(init_mode)
        self.checkout_mode_combo.pack(side="left")

        # One slot for the time inputs, so switching the mode never moves them
        # below the rest of the page.
        time_slot = ctk.CTkFrame(schedule, fg_color="transparent")
        time_slot.pack(anchor="w", fill="x", pady=(PAD_NONE, PAD_MD))

        self.checkout_uniform_frame = ctk.CTkFrame(time_slot, fg_color="transparent")
        self.checkout_uniform_lbl = self.register_i18n(
            ctk.CTkLabel(self.checkout_uniform_frame, text=tr("settings_checkout.uniform_time", "Uhrzeit:")),
            "settings_checkout.uniform_time",
            "Uhrzeit:",
        )
        self.checkout_uniform_lbl.pack(side="left", padx=(PAD_NONE, PAD_SM))
        self.checkout_uniform_entry = ctk.CTkEntry(
            self.checkout_uniform_frame,
            width=ENTRY_WIDTH_CHECKOUT_TIME,
            placeholder_text="16:30",
        )
        self.checkout_uniform_entry.insert(0, cs.auto_open_uniform_time)
        self.checkout_uniform_entry.pack(side="left")

        self.checkout_weekdays_frame = ctk.CTkFrame(time_slot, fg_color="transparent")
        self.checkout_weekday_entries = {}
        day_keys = [
            ("monday", "settings_checkout.day_monday", "Montag"),
            ("tuesday", "settings_checkout.day_tuesday", "Dienstag"),
            ("wednesday", "settings_checkout.day_wednesday", "Mittwoch"),
            ("thursday", "settings_checkout.day_thursday", "Donnerstag"),
            ("friday", "settings_checkout.day_friday", "Freitag"),
        ]
        for col, (day_id, tr_key, default_lbl) in enumerate(day_keys):
            lbl = self.register_i18n(
                ctk.CTkLabel(self.checkout_weekdays_frame, text=tr(tr_key, default_lbl), font=ctk.CTkFont(size=FONT_SIZE_SM), text_color=COLOR_TIP_TEXT, anchor="w"),
                tr_key,
                default_lbl,
            )
            lbl.grid(row=0, column=col, sticky="w", padx=(PAD_NONE, PAD_MD))
            entry = ctk.CTkEntry(self.checkout_weekdays_frame, width=ENTRY_WIDTH_CHECKOUT_NUMERIC)
            entry.insert(0, cs.auto_open_weekday_times.get(day_id, cs.auto_open_uniform_time))
            entry.grid(row=1, column=col, sticky="w", padx=(PAD_NONE, PAD_MD))
            self.checkout_weekday_entries[day_id] = entry

        # Commute: folded away unless the leave-now alarm is in use.
        self.checkout_transit_section = CollapsibleSection(
            right_col,
            title=tr("settings_checkout.commute_heading", "Heimweg mit Bus und Bahn"),
            expanded=bool(cs.alarm_enabled),
        )
        self.checkout_transit_section.pack(fill="x", pady=(PAD_NONE, PAD_SM))
        self.checkout_transit_hdr = self.checkout_transit_section
        commute = self.checkout_transit_section.body

        stop_name = cs.stops[0].get("name", "Ulm Ehinger Tor") if cs.stops else "Ulm Ehinger Tor"
        stop_place = cs.stops[0].get("place", "Ulm") if cs.stops else "Ulm"

        stop_grid = ctk.CTkFrame(commute, fg_color="transparent")
        stop_grid.pack(anchor="w", fill="x", pady=(PAD_NONE, PAD_MD))

        self.checkout_stop_name_lbl = self.register_i18n(
            ctk.CTkLabel(stop_grid, text=tr("settings_checkout.transit_stop_name", "Haltestellen-Name:")),
            "settings_checkout.transit_stop_name",
            "Haltestellen-Name:",
        )
        self.checkout_stop_name_lbl.grid(row=0, column=0, sticky="w", padx=(PAD_NONE, PAD_MD))
        self.checkout_stop_name_entry = ctk.CTkEntry(stop_grid, width=PROFILE_TAB_FIELD_WIDTH, placeholder_text=tr("settings_checkout.stop_placeholder", "Edisonallee"))
        self.checkout_stop_name_entry.insert(0, stop_name)
        self.checkout_stop_name_entry.grid(row=1, column=0, sticky="w", padx=(PAD_NONE, PAD_MD))

        self.checkout_stop_place_lbl = self.register_i18n(
            ctk.CTkLabel(stop_grid, text=tr("settings_checkout.transit_stop_place", "Ort / Gemeinde:")),
            "settings_checkout.transit_stop_place",
            "Ort / Gemeinde:",
        )
        self.checkout_stop_place_lbl.grid(row=0, column=1, sticky="w")
        self.checkout_stop_place_entry = ctk.CTkEntry(stop_grid, width=ENTRY_WIDTH_CHECKOUT_PLACE)
        self.checkout_stop_place_entry.insert(0, stop_place)
        self.checkout_stop_place_entry.grid(row=1, column=1, sticky="w")

        # Suggestions from the stop finder appear right under the two fields.
        self.checkout_stop_suggestions = ctk.CTkFrame(
            stop_grid, fg_color=COLOR_PANEL_BG, border_width=1, border_color=COLOR_PANEL_BORDER, corner_radius=CORNER_RADIUS_MD
        )
        self._stop_suggestion_buttons: list[ctk.CTkButton] = []
        self._stop_request_id = 0
        self._stop_last_query = ""
        self._stop_checked_value: tuple[str, str] | None = None

        self.checkout_stop_name_entry.bind("<KeyRelease>", self._on_stop_name_typed, add="+")
        for entry in (self.checkout_stop_name_entry, self.checkout_stop_place_entry):
            entry.bind("<FocusOut>", lambda _e: self._schedule_stop_check(), add="+")
            entry.bind("<Return>", lambda _e: self.on_check_stop(), add="+")

        status_row = ctk.CTkFrame(commute, fg_color="transparent")
        status_row.pack(anchor="w", fill="x", pady=(PAD_NONE, PAD_MD))
        self.checkout_stop_check_btn = self.register_i18n(
            ctk.CTkButton(
                status_row,
                text=tr("settings_checkout.btn_check_stop", "Abfahrten prüfen"),
                command=self.on_check_stop,
                fg_color=COLOR_MUTED_GRAY_FG,
                hover_color=COLOR_MUTED_GRAY_HOVER,
                width=BTN_WIDTH_CHECK_STOP,
            ),
            "settings_checkout.btn_check_stop",
            "Abfahrten prüfen",
        )
        self.checkout_stop_check_btn.pack(side="left", padx=(PAD_NONE, PAD_MD))
        self.checkout_stop_status_lbl = ctk.CTkLabel(
            status_row,
            text=tr("settings_checkout.stop_hint", "Tippe den Namen der Haltestelle und wähle einen Vorschlag."),
            text_color=COLOR_TIP_TEXT,
            anchor="w",
            justify="left",
            wraplength=SETTINGS_STOP_STATUS_WRAP,
        )
        self.checkout_stop_status_lbl.pack(side="left", fill="x", expand=True)

        # Lead time before departure, in the order the steps happen:
        # shut down + pack up + walk + buffer = minutes before the bus leaves.
        self.checkout_lead_lbl = self.register_i18n(
            ctk.CTkLabel(commute, text=tr("settings_checkout.lead_time_label", "Vorlauf vor der Abfahrt")),
            "settings_checkout.lead_time_label",
            "Vorlauf vor der Abfahrt",
        )
        self.checkout_lead_lbl.pack(anchor="w", pady=(PAD_NONE, PAD_XS))

        lead_grid = ctk.CTkFrame(commute, fg_color="transparent")
        lead_grid.pack(anchor="w", fill="x", pady=(PAD_NONE, PAD_MD))

        lead_fields = [
            ("logout", "settings_checkout.lead_logout", "Herunterfahren", cs.logout_time_minutes),
            ("pack", "settings_checkout.lead_pack", "Packen", cs.pack_time_minutes),
            ("walk", "settings_checkout.lead_walk", "Fußweg", cs.walk_time_minutes),
            ("buffer", "settings_checkout.lead_buffer", "Puffer", cs.buffer_time_minutes),
        ]
        lead_widgets: dict[str, tuple[ctk.CTkLabel, ctk.CTkEntry]] = {}
        for i, (attr, key, default, minutes) in enumerate(lead_fields):
            col = i * 2
            lbl = self.register_i18n(
                ctk.CTkLabel(lead_grid, text=tr(key, default), font=ctk.CTkFont(size=FONT_SIZE_SM), text_color=COLOR_TIP_TEXT, anchor="w"),
                key,
                default,
            )
            lbl.grid(row=0, column=col, sticky="w")
            entry = ctk.CTkEntry(lead_grid, width=ENTRY_WIDTH_CHECKOUT_LEAD, justify="right")
            entry.insert(0, str(minutes))
            entry.grid(row=1, column=col, sticky="ew")
            entry.bind("<KeyRelease>", lambda _e: self._update_checkout_lead_total(), add="+")
            lead_widgets[attr] = (lbl, entry)
            if i < len(lead_fields) - 1:
                ctk.CTkLabel(lead_grid, text="+", text_color=COLOR_TIP_TEXT).grid(row=1, column=col + 1, padx=PAD_SM)

        self.checkout_logout_lbl, self.checkout_logout_entry = lead_widgets["logout"]
        self.checkout_pack_lbl, self.checkout_pack_entry = lead_widgets["pack"]
        self.checkout_walk_lbl, self.checkout_walk_entry = lead_widgets["walk"]
        self.checkout_buffer_lbl, self.checkout_buffer_entry = lead_widgets["buffer"]

        self.checkout_lead_total_lbl = ctk.CTkLabel(lead_grid, text="", font=ctk.CTkFont(size=FONT_SIZE_BODY, weight="bold"))
        self.checkout_lead_total_lbl.grid(row=1, column=len(lead_fields) * 2, sticky="w", padx=(PAD_MD, PAD_NONE))
        self._update_checkout_lead_total()

        self.checkout_alarm_var = ctk.BooleanVar(value=cs.alarm_enabled)
        self.checkout_alarm_cb = self.register_i18n(
            ctk.CTkCheckBox(
                commute,
                text=tr("settings_checkout.alarm_enable", "Akustischen / visuellen Geh-Wecker aktivieren"),
                variable=self.checkout_alarm_var,
            ),
            "settings_checkout.alarm_enable",
            "Akustischen / visuellen Geh-Wecker aktivieren",
        )
        self.checkout_alarm_cb.pack(anchor="w", pady=(PAD_NONE, PAD_SM))

        self._update_checkout_mode_visibility()
        self._update_checkout_enabled_visibility()

    # ------------------------------------------------------------------
    # Stop search and live check (end-of-day page)
    # ------------------------------------------------------------------
    def _set_stop_status(self, text: str, color: Any = COLOR_TIP_TEXT) -> None:
        if hasattr(self, "checkout_stop_status_lbl") and self.checkout_stop_status_lbl.winfo_exists():
            self.checkout_stop_status_lbl.configure(text=text, text_color=color)

    def _current_stop(self) -> tuple[str, str]:
        return self.checkout_stop_name_entry.get().strip(), self.checkout_stop_place_entry.get().strip()

    def _on_stop_name_typed(self, event: Any = None) -> None:
        keysym = getattr(event, "keysym", "")
        if keysym in ("Return", "Tab", "Escape", "Up", "Down", "Left", "Right"):
            if keysym == "Escape":
                self._hide_stop_suggestions()
            return
        self._stop_checked_value = None
        query = self.checkout_stop_name_entry.get().strip()
        if len(query) < TRANSIT_STOP_SEARCH_MIN_CHARS:
            self._hide_stop_suggestions()
            return
        from utils.ui_utils import debounce

        debounce(self.checkout_stop_name_entry, "stop_search", TRANSIT_STOP_SEARCH_DEBOUNCE_MS, self._start_stop_search)

    def _start_stop_search(self) -> None:
        query = self.checkout_stop_name_entry.get().strip()
        if len(query) < TRANSIT_STOP_SEARCH_MIN_CHARS or query == self._stop_last_query:
            return
        self._stop_last_query = query
        self._stop_request_id += 1
        request_id = self._stop_request_id
        self._set_stop_status(tr("settings_checkout.stop_searching", "Suche Haltestellen …"))

        def worker() -> None:
            from services.ding_transit_service import DingTransitService

            results = DingTransitService.find_stops(query)
            self._deliver_stop_result(lambda: self._on_stop_suggestions(request_id, results))

        threading.Thread(target=worker, daemon=True).start()

    def _deliver_stop_result(self, callback: Callable[[], None]) -> None:
        """Hands a worker result back to the Tk thread, if the dialog still exists."""
        try:
            if self.winfo_toplevel().winfo_exists():
                self.winfo_toplevel().after(0, callback)
        except Exception:
            pass

    def _on_stop_suggestions(self, request_id: int, results: list[Any] | None) -> None:
        if request_id != self._stop_request_id or not self.checkout_stop_suggestions.winfo_exists():
            return
        if results is None:
            self._hide_stop_suggestions()
            self._set_stop_status(
                tr("settings_checkout.stop_check_error", "Fahrplanauskunft nicht erreichbar. Prüfe die Internetverbindung."),
                COLOR_TRANSIT_DELAY,
            )
            return
        if not results:
            self._hide_stop_suggestions()
            self._set_stop_status(
                tr("settings_checkout.stop_no_suggestions", "Keine passende Haltestelle gefunden. Prüfe die Schreibweise."),
                COLOR_TRANSIT_COUNTDOWN_WARN,
            )
            return
        self._show_stop_suggestions(results)
        self._set_stop_status(tr("settings_checkout.stop_pick_hint", "Wähle deine Haltestelle aus der Liste."))

    def _show_stop_suggestions(self, stops: list[Any]) -> None:
        for btn in self._stop_suggestion_buttons:
            btn.destroy()
        self._stop_suggestion_buttons = []
        for stop in stops:
            label = f"{stop.name}, {stop.place}" if stop.place else stop.name
            btn = ctk.CTkButton(
                self.checkout_stop_suggestions,
                text=label,
                anchor="w",
                height=SETTINGS_NAV_ITEM_HEIGHT,
                fg_color="transparent",
                hover_color=COLOR_SETTINGS_NAV_HOVER,
                text_color=COLOR_SETTINGS_NAV_TEXT,
                command=lambda s=stop: self.on_pick_stop(s),
            )
            btn.pack(fill="x", padx=PAD_XS, pady=PAD_TINY)
            self._stop_suggestion_buttons.append(btn)
        self.checkout_stop_suggestions.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(PAD_XS, PAD_NONE))

    def _hide_stop_suggestions(self) -> None:
        if hasattr(self, "checkout_stop_suggestions") and self.checkout_stop_suggestions.winfo_manager():
            self.checkout_stop_suggestions.grid_remove()

    def on_pick_stop(self, stop: Any) -> None:
        """Fills name and place from a suggestion and checks it right away."""
        self.checkout_stop_name_entry.delete(0, "end")
        self.checkout_stop_name_entry.insert(0, stop.name)
        if stop.place:
            self.checkout_stop_place_entry.delete(0, "end")
            self.checkout_stop_place_entry.insert(0, stop.place)
        self._stop_last_query = stop.name
        self._hide_stop_suggestions()
        self.on_check_stop()

    def _schedule_stop_check(self) -> None:
        name, place = self._current_stop()
        if not name or self._stop_checked_value == (name, place):
            return
        from utils.ui_utils import debounce

        debounce(self.checkout_stop_name_entry, "stop_check", TRANSIT_STOP_SEARCH_DEBOUNCE_MS, self._run_pending_stop_check)

    def _run_pending_stop_check(self) -> None:
        # A suggestion may have been picked (and checked) while this was pending.
        if self._current_stop() != self._stop_checked_value:
            self.on_check_stop()

    def on_check_stop(self) -> None:
        """Asks the live timetable whether the entered stop resolves and has departures."""
        name, place = self._current_stop()
        if not name:
            self._set_stop_status(
                tr("settings_checkout.stop_enter_name", "Gib zuerst den Namen der Haltestelle ein."),
                COLOR_TRANSIT_COUNTDOWN_WARN,
            )
            return
        self._stop_checked_value = (name, place)
        self._stop_request_id += 1
        request_id = self._stop_request_id
        self._set_stop_status(tr("settings_checkout.stop_check_running", "Prüfe Abfahrten …"))

        def worker() -> None:
            from services.ding_transit_service import DingTransitService

            result = DingTransitService.check_stop(name, place)
            self._deliver_stop_result(lambda: self._on_stop_checked(request_id, result))

        threading.Thread(target=worker, daemon=True).start()

    def _on_stop_checked(self, request_id: int, result: Any) -> None:
        if request_id != self._stop_request_id:
            return
        if result.status == "ok":
            self._set_stop_status(
                tr(
                    "settings_checkout.stop_check_ok",
                    "Gefunden: {stop}. Nächste {count} Abfahrten werden angezeigt.",
                    stop=result.resolved_name,
                    count=result.departure_count,
                ),
                COLOR_TRANSIT_ONTIME,
            )
        elif result.status == "no_departures":
            self._set_stop_status(
                tr(
                    "settings_checkout.stop_check_no_departures",
                    "Haltestelle {stop} gefunden, aber gerade fährt dort nichts ab.",
                    stop=result.resolved_name,
                ),
                COLOR_TRANSIT_COUNTDOWN_WARN,
            )
        elif result.status == "ambiguous":
            self._show_stop_suggestions(result.candidates)
            self._set_stop_status(
                tr("settings_checkout.stop_check_ambiguous", "Mehrere Haltestellen passen. Wähle eine aus der Liste."),
                COLOR_TRANSIT_COUNTDOWN_WARN,
            )
        elif result.status == "not_found":
            self._set_stop_status(
                tr("settings_checkout.stop_check_not_found", "Keine Haltestelle unter diesem Namen gefunden. Prüfe Schreibweise und Ort."),
                COLOR_TRANSIT_DELAY,
            )
        else:
            self._set_stop_status(
                tr("settings_checkout.stop_check_error", "Fahrplanauskunft nicht erreichbar. Prüfe die Internetverbindung."),
                COLOR_TRANSIT_DELAY,
            )

    def _update_checkout_lead_total(self) -> None:
        """Shows how many minutes before departure the leave-now alarm rings."""
        if not hasattr(self, "checkout_lead_total_lbl"):
            return
        total = 0
        for attr in ("checkout_logout_entry", "checkout_pack_entry", "checkout_walk_entry", "checkout_buffer_entry"):
            entry = getattr(self, attr, None)
            if entry is None:
                continue
            try:
                total += max(0, int(entry.get().strip()))
            except ValueError:
                pass
        self.checkout_lead_total_lbl.configure(
            text=tr("settings_checkout.lead_total", "= {minutes} Min. vor Abfahrt", minutes=total)
        )

    def _update_checkout_enabled_visibility(self) -> None:
        frame = getattr(self, "checkout_schedule_frame", None)
        if frame is None:
            return
        if self.checkout_enable_var.get():
            if not frame.winfo_manager():
                frame.pack(anchor="w", fill="x", after=self.checkout_remember_cb)
        elif frame.winfo_manager():
            frame.pack_forget()

    def _on_checkout_mode_changed(self, choice: str) -> None:
        self._update_checkout_mode_visibility()

    def _update_checkout_mode_visibility(self) -> None:
        if not hasattr(self, "checkout_mode_combo"):
            return
        idx = self.selected_choice_index(self.checkout_mode_combo)
        if idx == 1:
            self.checkout_uniform_frame.pack_forget()
            self.checkout_weekdays_frame.pack(anchor="w", fill="x")
        else:
            self.checkout_weekdays_frame.pack_forget()
            self.checkout_uniform_frame.pack(anchor="w", fill="x")

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
        details = getattr(self, "ntfy_details_frame", None)
        if details is not None:
            if is_on and not details.winfo_manager():
                details.pack(anchor="w", fill="x", after=self.ntfy_switch)
            elif not is_on and details.winfo_manager():
                details.pack_forget()
        for w in (
            getattr(self, "ntfy_topic_entry", None),
            getattr(self, "ntfy_random_btn", None),
            getattr(self, "ntfy_test_btn", None),
            getattr(self, "ntfy_qr_btn", None),
            getattr(self, "ntfy_idle_combo", None),
            getattr(self, "ntfy_cb_followups", None),
            getattr(self, "ntfy_cb_prio1", None),
            getattr(self, "ntfy_cb_handovers", None),
            getattr(self, "ntfy_cb_notes", None),
            getattr(self, "ntfy_cb_on_call", None),
            getattr(self, "ntfy_cb_auto_presence", None),
            getattr(self, "ntfy_cb_digest", None),
            getattr(self, "ntfy_cb_remote_control", None),
        ):
            if w is not None:
                w.configure(state=state)

        digest_on = is_on and bool(getattr(self, "ntfy_cb_digest", None) and self.ntfy_cb_digest.get())
        digest_combo = getattr(self, "ntfy_combo_digest_minutes", None)
        if digest_combo is not None:
            digest_combo.configure(state="normal" if digest_on else "disabled")

        rc_on = is_on and bool(getattr(self, "ntfy_cb_remote_control", None) and self.ntfy_cb_remote_control.get())
        rc_entry = getattr(self, "ntfy_entry_response_topic", None)
        if rc_entry is not None:
            rc_entry.configure(state="normal" if rc_on else "disabled")

    def on_toggle_unlock_notify(self) -> None:
        """Enables or disables the custom unlock notification text entry."""
        if hasattr(self, "unlock_notify_cb") and hasattr(self, "unlock_notify_entry"):
            is_enabled = bool(self.unlock_notify_cb.get())
            self.unlock_notify_entry.configure(state="normal" if is_enabled else "disabled")

    def on_generate_random_ntfy_topic(self) -> None:
        from services.ntfy_service import NtfyService
        rnd_topic = NtfyService.generate_random_topic()
        self.ntfy_topic_entry.delete(0, "end")
        self.ntfy_topic_entry.insert(0, rnd_topic)

    def on_show_ntfy_qr(self) -> None:
        topic = self.ntfy_topic_entry.get().strip()
        if not topic:
            from ui.widgets.toast_notification import ToastNotification

            ToastNotification(
                self.winfo_toplevel(),
                title=tr("ntfy.qr_dialog_title", "Smartphone koppeln (ntfy)"),
                message=tr("ntfy.qr_no_topic_toast", "Bitte trage zuerst ein Thema ein oder klicke auf 'Zufall'."),
            )
            return
        from ui.dialogs.ntfy_qr_dialog import NtfyQrDialog

        NtfyQrDialog(self.winfo_toplevel(), topic=topic)

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
        if hasattr(self, "followup_repeat_combo"):
            self.followup_repeat_combo.set(
                get_followup_repeat_display(getattr(self.profile.reminder_settings, "followup_repeat_minutes", DEFAULT_FOLLOWUP_REPEAT_MINUTES))
            )
        if hasattr(self, "unlock_notify_cb"):
            if getattr(self.profile.reminder_settings, "unlock_notification_enabled", DEFAULT_UNLOCK_NOTIFICATION_ENABLED):
                self.unlock_notify_cb.select()
            else:
                self.unlock_notify_cb.deselect()
        if hasattr(self, "unlock_notify_entry"):
            self.unlock_notify_entry.configure(state="normal")
            self.unlock_notify_entry.delete(0, "end")
            saved_unlock_text = getattr(self.profile.reminder_settings, "unlock_notification_text", DEFAULT_UNLOCK_NOTIFICATION_TEXT)
            if saved_unlock_text:
                self.unlock_notify_entry.insert(0, saved_unlock_text)
            self.on_toggle_unlock_notify()
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
        if hasattr(self, "ntfy_cb_on_call"):
            if getattr(self.profile.reminder_settings, "mobile_ntfy_on_call", DEFAULT_NTFY_ON_CALL):
                self.ntfy_cb_on_call.select()
            else:
                self.ntfy_cb_on_call.deselect()
        if hasattr(self, "ntfy_cb_auto_presence"):
            if getattr(self.profile.reminder_settings, "mobile_ntfy_auto_presence", DEFAULT_NTFY_AUTO_PRESENCE):
                self.ntfy_cb_auto_presence.select()
            else:
                self.ntfy_cb_auto_presence.deselect()
        if hasattr(self, "ntfy_cb_digest"):
            if getattr(self.profile.reminder_settings, "mobile_ntfy_digest_enabled", DEFAULT_NTFY_DIGEST_ENABLED):
                self.ntfy_cb_digest.select()
            else:
                self.ntfy_cb_digest.deselect()
        if hasattr(self, "ntfy_combo_digest_minutes"):
            self.ntfy_combo_digest_minutes.set(str(getattr(self.profile.reminder_settings, "mobile_ntfy_digest_minutes", DEFAULT_NTFY_DIGEST_MINUTES)))
        if hasattr(self, "ntfy_cb_remote_control"):
            if getattr(self.profile.reminder_settings, "mobile_ntfy_remote_control", DEFAULT_NTFY_REMOTE_CONTROL):
                self.ntfy_cb_remote_control.select()
            else:
                self.ntfy_cb_remote_control.deselect()
        if hasattr(self, "ntfy_entry_response_topic"):
            self.ntfy_entry_response_topic.delete(0, "end")
            saved_resp = getattr(self.profile.reminder_settings, "mobile_ntfy_response_topic", DEFAULT_NTFY_RESPONSE_TOPIC)
            if saved_resp:
                self.ntfy_entry_response_topic.insert(0, saved_resp)
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
        if hasattr(self, "followup_repeat_combo"):
            chosen_repeat = get_followup_repeat_minutes_from_display(self.followup_repeat_combo.get())
            if chosen_repeat is not None:
                self.profile.reminder_settings.followup_repeat_minutes = chosen_repeat
        if hasattr(self, "unlock_notify_cb"):
            self.profile.reminder_settings.unlock_notification_enabled = bool(self.unlock_notify_cb.get())
        if hasattr(self, "unlock_notify_entry"):
            self.profile.reminder_settings.unlock_notification_text = self.unlock_notify_entry.get().strip()
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
        if hasattr(self, "ntfy_cb_on_call"):
            self.profile.reminder_settings.mobile_ntfy_on_call = bool(self.ntfy_cb_on_call.get())
        if hasattr(self, "ntfy_cb_auto_presence"):
            self.profile.reminder_settings.mobile_ntfy_auto_presence = bool(self.ntfy_cb_auto_presence.get())
        if hasattr(self, "ntfy_cb_digest"):
            self.profile.reminder_settings.mobile_ntfy_digest_enabled = bool(self.ntfy_cb_digest.get())
        if hasattr(self, "ntfy_combo_digest_minutes"):
            try:
                self.profile.reminder_settings.mobile_ntfy_digest_minutes = int(self.ntfy_combo_digest_minutes.get().strip())
            except ValueError:
                self.profile.reminder_settings.mobile_ntfy_digest_minutes = DEFAULT_NTFY_DIGEST_MINUTES
        if hasattr(self, "ntfy_cb_remote_control"):
            self.profile.reminder_settings.mobile_ntfy_remote_control = bool(self.ntfy_cb_remote_control.get())
        if hasattr(self, "ntfy_entry_response_topic"):
            self.profile.reminder_settings.mobile_ntfy_response_topic = self.ntfy_entry_response_topic.get().strip()
        if hasattr(self, "popup_target_combo"):
            # The menu shows translated labels; matching them against German text
            # picked APP_SCREEN for every non-German UI. The position is what
            # actually identifies the target, and POPUP_DISPLAY_TARGETS is kept
            # in the same order as POPUP_TARGET_CHOICES.
            index = self.selected_choice_index(self.popup_target_combo)
            self.profile.ui_settings.popup_display_target = POPUP_DISPLAY_TARGETS[
                min(index, len(POPUP_DISPLAY_TARGETS) - 1)
            ]

        if hasattr(self, "checkout_enable_cb"):
            cs = self.profile.checkout_settings
            cs.enabled = self.checkout_enable_var.get()
            cs.auto_open = self.checkout_auto_open_var.get()
            cs.remember_visibility = bool(self.checkout_remember_var.get())
            idx = self.selected_choice_index(self.checkout_mode_combo)
            cs.auto_open_mode = CHECKOUT_AUTO_OPEN_MODE_KEYS[
                min(idx, len(CHECKOUT_AUTO_OPEN_MODE_KEYS) - 1)
            ]
            cs.auto_open_uniform_time = self.checkout_uniform_entry.get().strip() or "16:30"
            for day_id, entry in getattr(self, "checkout_weekday_entries", {}).items():
                cs.auto_open_weekday_times[day_id] = entry.get().strip() or cs.auto_open_uniform_time

            stop_name = self.checkout_stop_name_entry.get().strip() or "Ulm Ehinger Tor"
            stop_place = self.checkout_stop_place_entry.get().strip() or "Ulm"
            cs.stops = [{"name": stop_name, "place": stop_place}]
            cs.weather_city = stop_place

            try:
                cs.walk_time_minutes = int(self.checkout_walk_entry.get().strip())
            except ValueError:
                pass
            try:
                cs.logout_time_minutes = int(self.checkout_logout_entry.get().strip())
            except ValueError:
                pass
            try:
                cs.pack_time_minutes = int(self.checkout_pack_entry.get().strip())
            except ValueError:
                pass
            try:
                cs.buffer_time_minutes = int(self.checkout_buffer_entry.get().strip())
            except ValueError:
                pass
            cs.alarm_enabled = self.checkout_alarm_var.get()

        return True

    def refresh_ui_tab_labels(self) -> None:
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
        if hasattr(self, "followup_repeat_lbl"):
            self.followup_repeat_lbl.configure(text=tr("profile.followup_repeat_label", "Erneut erinnern, solange fällig:"))
        if hasattr(self, "followup_repeat_combo"):
            self.followup_repeat_combo.configure(values=[get_followup_repeat_display(m) for m in FOLLOWUP_REPEAT_MINUTES_OPTIONS])
            self.followup_repeat_combo.set(
                get_followup_repeat_display(getattr(self.profile.reminder_settings, "followup_repeat_minutes", DEFAULT_FOLLOWUP_REPEAT_MINUTES))
            )
        if hasattr(self, "unlock_notify_cb"):
            self.unlock_notify_cb.configure(text=tr("ntfy.unlock_notification_toggle", "🖥 Benachrichtigung nach Entsperren des Bildschirms anzeigen"))
        if hasattr(self, "unlock_notify_lbl"):
            self.unlock_notify_lbl.configure(text=tr("ntfy.unlock_notification_text_label", "Eigener Benachrichtigungstext:"))
        if hasattr(self, "unlock_notify_entry"):
            self.unlock_notify_entry.configure(placeholder_text=tr("ntfy.unlock_notification_placeholder", "z. B. Willkommen zurück! Bitte offene Wiedervorlagen prüfen."))
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
        if hasattr(self, "ntfy_cb_on_call"):
            self.ntfy_cb_on_call.configure(text=tr("ntfy.filter_on_call", "Notdienst / Rufbereitschaft (Inaktivitätszwang übergehen)"))
        if hasattr(self, "ntfy_cb_auto_presence"):
            self.ntfy_cb_auto_presence.configure(text=tr("ntfy.filter_auto_presence", "Abwesenheitsstatus im Team bei Bildschirmsperre automatisch setzen"))
        if hasattr(self, "ntfy_cb_digest"):
            self.ntfy_cb_digest.configure(text=tr("ntfy.digest_enable", "Sammelbericht für Routine-Ereignisse (Digest)"))
        if hasattr(self, "ntfy_digest_interval_lbl"):
            self.ntfy_digest_interval_lbl.configure(text=tr("ntfy.digest_interval_lbl", "Intervall (Minuten):"))
        if hasattr(self, "ntfy_digest_hint_lbl"):
            self.ntfy_digest_hint_lbl.configure(text=tr("ntfy.digest_hint", "⚡ Prio-1 Notfälle umgehen den Sammelbericht und werden sofort gesendet."))
        if hasattr(self, "ntfy_cb_remote_control"):
            self.ntfy_cb_remote_control.configure(text=tr("ntfy.remote_control_enable", "Fernsteuerung & Aktions-Buttons aktivieren"))
        if hasattr(self, "ntfy_response_topic_lbl"):
            self.ntfy_response_topic_lbl.configure(text=tr("ntfy.response_topic_label", "Befehls-Thema (optional):"))
        if hasattr(self, "ntfy_entry_response_topic"):
            self.ntfy_entry_response_topic.configure(placeholder_text=tr("ntfy.response_topic_placeholder", "Standard: {topic}-cmd"))
        if hasattr(self, "ntfy_remote_control_hint_lbl"):
            self.ntfy_remote_control_hint_lbl.configure(text=tr("ntfy.remote_control_hint", "⚡ Ermöglicht Aktionen (Schlummern, Übernehmen) per Knopfdruck am Smartphone."))
        if hasattr(self, "ntfy_advanced_section"):
            self.ntfy_advanced_section.set_title(tr("ntfy.advanced_heading", "Erweitert: Sammelbericht und Fernsteuerung"))
        if hasattr(self, "ntfy_privacy_lbl"):
            self.ntfy_privacy_lbl.configure(text=tr("ntfy.privacy_tip", "🔒 Datensparsam: Keine Kunden- oder Patientendaten im Push-Payload."))
        if hasattr(self, "popup_target_lbl"):
            self.popup_target_lbl.configure(text=tr("profile.popup_position", "Position zusätzlicher Fenster & Benachrichtigungen:"))
        if hasattr(self, "popup_target_combo"):
            self.retranslate_choices(self.popup_target_combo, POPUP_TARGET_CHOICES)
        if hasattr(self, "checkout_mode_combo"):
            self.retranslate_choices(self.checkout_mode_combo, CHECKOUT_AUTO_OPEN_MODE_CHOICES)
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
