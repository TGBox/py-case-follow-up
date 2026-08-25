"""Centralized application constants, design tokens, layout dimensions, default datasets, and system strings."""

from pathlib import Path

# --- App Metadata & Titles ---
APP_NAME = "SupportCockpit"
APP_TITLE = "🩺 Support-Cockpit"
APP_WINDOW_TITLE = "Support-Cockpit & Ticket Management"
APP_MIN_WIDTH = 900
APP_MIN_HEIGHT = 650

# --- Dialog Titles & Window Headers ---
DIALOG_TITLES = {
    "new_case": "Neuen Support-Fall anlegen",
    "quick_customer": "🏥 Neue Praxis schnell anlegen",
    "print_report": "🖨 Fall-Akte Druck- & HTML Export",
    "customer_mgmt": "🏥 Praxis- & Kundenverwaltung",
    "colleague_mgmt": "👥 Mitarbeiter- & Kollegeneinträge",
    "tag_mgmt": "🏷 Tags & Programmbereiche Verwaltung",
    "profile_settings": "⚙ Profil & Einstellungen",
    "template_mgmt": "📄 Export-Vorlagen verwalten",
    "edit_template": "✏ Vorlage bearbeiten",
    "new_template": "➕ Neue Export-Vorlage",
    "schema_builder": "In-App Formular-Baukasten (Schemata verwalten)",
    "new_schema": "🆕 Neues Formular (Schema) erstellen",
    "convert_schema": "🔄 Fall in anderes Formular konvertieren",
    "followup_flyout": "⏰ Wiedervorlage & Frist verwalten",
    "handover": "🤝 Fall an Kollege / Abteilung übergeben",
    "zip_import": "📦 Datenbanksicherung (ZIP) importieren",
    "snippet_mgmt": "📝 Textbausteine verwalten",
    "snippet_picker": "🧩 Textbaustein auswählen & einfügen",
    "email_draft": "✉ E-Mail verfassen & Vorschau",
    "calendar_export": "📅 Kalendereintrag (.ics) erstellen",
    "help": "❓ Support-Cockpit Hilfe & Dokumentation",
    "cobra_import": "🐍 COBRA CRM Import",
}

# --- Button Labels & UI Action Texts ---
UI_BUTTON_TEXTS = {
    "save": "Speichern",
    "cancel": "Abbrechen",
    "delete": "Löschen",
    "close": "Schließen",
    "create": "Erstellen",
    "apply": "Übernehmen",
    "search": "Suchen",
    "import": "Importieren",
    "export": "Exportieren",
    "new_case": "+ Neuer Fall",
    "new_snippet": "+ Neuer Textbaustein",
    "new_customer": "+ Neue Praxis",
    "new_colleague": "+ Kollege",
    "print_pdf": "🖨 PDF-Bericht drucken",
    "open_html": "🌐 HTML-Bericht",
    "save_file": "💾 Speichern...",
}

# --- Status & Feedback Messages ---
STATUS_MESSAGES = {
    "snippet_saved": "✓ Textbaustein gespeichert.",
    "snippet_deleted": "✓ Textbaustein gelöscht.",
    "customer_saved": "✓ Praxis-Eintrag erfolgreich gespeichert.",
    "colleague_saved": "✓ Kollegendaten erfolgreich gespeichert.",
    "tags_updated": "✓ Tags erfolgreich aktualisiert.",
    "profile_saved": "✓ Profil & Einstellungen gespeichert.",
}

# --- Default Layout Dimensions & Column Widths ---
DEFAULT_COLUMN_WIDTHS = {
    "cockpit_left": 300,
    "cockpit_center": 420,
    "cockpit_right": 320,
    "board_column": 280,
    "table_col_id": 120,
    "table_col_practice": 220,
    "table_col_title": 280,
    "table_col_actor": 130,
    "table_col_followup": 150,
    "table_col_score": 90,
}

# Dialog Sizes (Width x Height)
DIALOG_DIMENSIONS = {
    "new_case": (760, 860),
    "quick_customer": (420, 360),
    "print_report": (680, 600),
    "customer_mgmt": (1024, 720),
    "colleague_mgmt": (1024, 720),
    "tag_mgmt": (620, 520),
    "profile_settings": (960, 780),
    "template_mgmt": (980, 720),
    "edit_template": (880, 740),
    "schema_builder": (940, 720),
    "new_schema": (440, 320),
    "convert_schema": (580, 520),
    "followup_flyout": (650, 480),
    "handover": (520, 460),
    "zip_import": (560, 380),
    "snippet_mgmt": (820, 600),
    "snippet_picker": (640, 480),
    "email_draft": (720, 640),
    "calendar_export": (540, 420),
    "help": (760, 620),
    "cobra_import": (640, 480),
}

# --- Design System Color Tokens ---
COLOR_PRIMARY = "#2563eb"
COLOR_PRIMARY_HOVER = "#1d4ed8"
COLOR_SUCCESS = "forestgreen"
COLOR_SUCCESS_HOVER = "darkgreen"
COLOR_CANCEL = ("gray70", "gray40")
COLOR_CANCEL_HOVER = ("gray60", "gray50")
COLOR_DANGER = "crimson"
COLOR_MUTED_GRAY = ("gray75", "gray30")
COLOR_MUTED_HOVER = ("gray65", "gray40")
COLOR_SASH_DARK = "#2b2b2b"
COLOR_SASH_LIGHT = "#d0d0d0"

COLOR_URGENCY_RED = "#dc2626"
COLOR_URGENCY_YELLOW = "#d97706"
COLOR_URGENCY_GREEN = "#16a34a"

# --- Default Application Tags & Lists ---
DEFAULT_TAGS = [
    "Abrechnung",
    "Hardware",
    "Berechtigung",
    "Windows",
    "Schnittstelle",
    "Dringend",
    "Kürzung",
    "Ablehnung",
    "Verordnung",
    "Netzwerk",
    "Datenbank",
    "Fehler",
    "Rechnung",
    "Kündigung",
    "Rückmeldung",
    "Informationen",
    "Rezept",
    "PVS",
]

DEFAULT_MODULE_TAGS = [
    "Fakturaübersicht",
    "Rezeptdruck",
    "Labor",
    "eRezept / Verordnung",
    "System",
    "Terminkalender",
    "Patientenkartei",
]

DEFAULT_INTERNAL_TASK_CATEGORIES = [
    "Systemwartung",
    "Dokumentation",
    "Entwicklungsaufgabe",
    "Prozessverbesserung",
    "Sonstiges",
]

DEFAULT_DEPARTMENTS = [
    "Support",
    "Entwicklung",
    "Technik",
    "Vertrieb",
    "Buchhaltung",
    "Geschäftsführung",
    "Sonstige",
]

# --- Supported File Extensions ---
IMAGE_FILE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
TEXT_FILE_EXTENSIONS = {".txt", ".log", ".json", ".sql", ".xml", ".csv", ".ini", ".md"}

# --- Default Scoring Matrix ---
DEFAULT_SCORING_MATRIX = {
    "vip_bonus_points": 50,
    "points_per_idle_day": 15,
    "deadline_close_hours": 2,
    "deadline_close_bonus": 40,
    "deadline_overdue_bonus": 100,
    "threshold_yellow": 50,
    "threshold_red": 100,
}

# --- System Timeouts & Thresholds ---
AUTO_ARCHIVE_THRESHOLD_DAYS = 30
HOURLY_TIMER_MS = 3600000
FOLLOWUP_CHECK_INITIAL_DELAY_MS = 2000
TOAST_DURATION_DEFAULT_MS = 5000

# --- Date & Time Formats ---
GERMAN_DATE_FORMAT = "%d.%m.%Y"
GERMAN_DATETIME_FORMAT = "%d.%m.%Y %H:%M"
ISO_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
