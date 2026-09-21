"""Centralized application constants, design tokens, layout dimensions, default datasets, and system strings."""

import os
from services.i18n_service import LocalizedDict


# --- App Metadata & Titles ---
APP_NAME = "SupportCockpit"
APP_TITLE = "🩺 Support-Cockpit"
APP_WINDOW_TITLE = "Support-Cockpit & Ticket Management"
APP_MIN_WIDTH = 900
APP_MIN_HEIGHT = 650
APP_DEFAULT_GEOMETRY = "1440x880"
DEFAULT_THEME = "System"
THEME_DARK = "Dark"
THEME_LIGHT = "Light"
DEFAULT_FONT_SCALE = 1.0
DEFAULT_LANGUAGE = "de"
WINDOW_STATE_ZOOMED = "zoomed"
WINDOW_STATE_ICONIC = "iconic"
PAD_CONTAINER = 5
WIKI_STARTUP_SYNC_DELAY_MS = 1000
SPLASH_DIMENSIONS = (420, 150)
COLOR_SPLASH_BG = ("gray95", "gray12")
COLOR_SPLASH_BORDER = "dodgerblue"
FONT_SIZE_SPLASH = 22
PAD_SPLASH_TITLE = (38, 8)
MENU_BAR_HEIGHT = 48
COMBO_WIDTH_LAYOUT = 120
BTN_WIDTH_NEW_CASE = 150
COMBO_WIDTH_STAMMDATEN = 150
COMBO_WIDTH_VORLAGEN = 165
COMBO_WIDTH_DATENAUSTAUSCH = 145
BTN_WIDTH_QUIT = 90
COLOR_QUIT_BTN = "#8B0000"
COLOR_QUIT_BTN_HOVER = "#B22222"
COLOR_THEME_BTN = ("gray70", "gray30")
BTN_WIDTH_HELP = 85
COLOR_BELL_BTN = "gray30"
COLOR_BELL_BTN_HOVER = "darkred"
BTN_WIDTH_USER = 130
COLOR_USER_BTN_HOVER = ("gray80", "gray25")
COLOR_USER_BTN_TEXT = ("gray10", "gray90")
DEFAULT_SHORTCUT_VIEW_ANALYTICS = "<Control-4>"
FONT_SCALE_STEP = 0.1
FONT_SCALE_MIN = 0.8
FONT_SCALE_MAX = 1.5
HOURLY_SCORING_INTERVAL_SECONDS = 3600
FOLLOWUP_CHECK_INTERVAL_MS = 60000
FILE_EXT_ZIP = ".zip"



# --- Enum Display Names & Labels ---
DISPLAY_CHANNEL_NAMES = LocalizedDict("channels", {
    "PHONE_INBOUND": "Telefon (Eingang)",
    "PHONE_OUTBOUND": "Telefon (Ausgang)",
    "EMAIL_IN": "E-Mail (Eingang)",
    "EMAIL_OUT": "E-Mail (Ausgang)",
    "GITLAB_TICKET_CREATED": "GitLab-Ticket erstellt",
    "GITLAB_TICKET_UPDATED": "GitLab-Ticket geupdated",
    "GITLAB_TICKET_CLOSED": "GitLab-Ticket geschlossen",
    "INTERNAL_NOTE": "Interne Notiz",
    "OTHER": "Sonstiges"
})

DISPLAY_ACTOR_NAMES = LocalizedDict("actors", {
    "SUPPORT": "Hotline",
    "TECH": "Technik",
    "DEVELOPMENT": "Entwicklung",
    "CUSTOMER": "Kunde",
})

DISPLAY_LAYOUT_NAMES = LocalizedDict("layouts", {
    "COCKPIT": "Cockpit (Hauptansicht)",
    "BOARD": "Kanban-Board (Zuständigkeiten)",
    "TABLE": "Tabelle & Details (Sortier-Matrix)",
    "ANALYTICS": "Auswertungen & Kennzahlen",
})

DISPLAY_BOARD_COLUMN_NAMES = LocalizedDict("board_columns", {
    "NEW": "Neu",
    "ACTION_REQUIRED": "Aktion erforderlich",
    "WAITING": "Warten auf zuständige Stelle",
    "IN_PROGRESS": "In Bearbeitung",
    "DONE": "Erledigt",
})

DISPLAY_THEME_NAMES = LocalizedDict("theme", {
    "Dark": "Dunkel",
    "Light": "Hell",
    "System": "System",
})

DISPLAY_SORT_CRITERION_NAMES = LocalizedDict("customer_mgmt", {
    "name": "Name (A-Z)",
    "id": "Praxisnummer / ID",
    "contact": "Zeit seit letztem Kontakt",
})

CHANNEL_KEY_MAP = {
    "PHONE_INBOUND": "channels.phone",
    "EMAIL": "channels.email",
    "INTERNAL_NOTE": "channels.internal_note",
}

ACTOR_KEY_MAP = {
    "SUPPORT": "actors.support_team",
    "CUSTOMER": "actors.practice",
    "DEVELOPMENT": "actors.dev",
    "TECH": "actors.third_party",
}

LAYOUT_KEY_MAP = {
    "COCKPIT": "layouts.cockpit",
    "BOARD": "layouts.board",
    "TABLE": "layouts.table",
    "ANALYTICS": "layouts.analytics",
}

THEME_KEY_MAP = {
    "Dark": "theme.dark",
    "Light": "theme.light",
    "System": "theme.system",
}

SORT_CRITERION_KEY_MAP = {
    "name": "customer_mgmt.sort_name",
    "id": "customer_mgmt.sort_id",
    "contact": "customer_mgmt.sort_contact",
}

LEGACY_ACTOR_MAP = {
    "support / hotline": "SUPPORT",
    "support": "SUPPORT",
    "hotline": "SUPPORT",
    "data-al support / hotline": "SUPPORT",
    "data-al hotline": "SUPPORT",
    "data-al support": "SUPPORT",
    "technik": "TECH",
    "tech": "TECH",
    "tech support": "TECH",
    "data-al technik": "TECH",
    "data-al tech": "TECH",
    "entwicklung": "DEVELOPMENT",
    "development": "DEVELOPMENT",
    "utveckling": "DEVELOPMENT",
    "data-al entwicklung": "DEVELOPMENT",
    "kunde": "CUSTOMER",
    "customer": "CUSTOMER",
    "kund": "CUSTOMER",
    "data-al kunde": "CUSTOMER",
}


class LocalizedHotkeyDict(LocalizedDict):
    """LocalizedDict that supports iterating as (key, value) pairs for backward compatibility."""

    def __iter__(self):
        return iter([(k, self[k]) for k in self.keys()])



# --- Dialog Titles & Window Headers ---
DIALOG_TITLES = LocalizedDict("dialog_titles", {
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
    "convert_schema": "🔄 Formular-Schema umwandeln",
    "followup_flyout": "🔔 Fällige Wiedervorlagen & Deadlines",
    "handover": "👤 Zuständigkeit übergeben",
    "zip_import": "📥 Datensicherung Importieren — Zielpfade festlegen",
    "snippet_mgmt": "📝 Textbausteine verwalten",
    "snippet_picker": "🧩 Textbaustein auswählen & einfügen",
    "email_draft": "✉ E-Mail verfassen",
    "calendar_export": "📅 Kalendereintrag (.ics) erstellen",
    "help": "📖 Handbuch & Anwendungsdokumentation",
    "cobra_import": "🐍 Cobra CRM Praxen-Import (CSV / TXT / JSON)",
    "export": "Übergabe- & Export-Assistent",
    "p2p_diff": "Multi-User P2P-Sync & Kollegendaten-Abgleich",
    "email_calendar": "✉ E-Mail & 📅 Kalender-Entwurf",
    "ai_assistant": "🤖 KI- & Support-Assistent",
    "email_import": "📥 E-Mail Posteingang & Import Hub",
})

# --- Sub-Header Labels inside Dialogs ---
DIALOG_HEADERS = LocalizedDict("dialog_headers", {
    "email_import_hub": "📥 E-Mail Import Hub & Auto-Matching",
})

# --- Dropdown Menu & Navigation Option Lists ---
def get_localized_menu_options_stammdaten() -> list[str]:
    from services.i18n_service import tr
    return [
        tr("menu.opt_practices", "🏥 Praxen"),
        tr("menu.opt_colleagues", "👥 Mitarbeiter"),
        tr("menu.opt_modules", "🧩 Programmbereiche"),
        tr("menu.opt_tags", "🏷 Tags"),
    ]

def get_localized_menu_options_vorlagen() -> list[str]:
    from services.i18n_service import tr
    return [
        tr("menu.opt_forms", "🛠 Formulare"),
        tr("menu.opt_templates", "📄 Vorlagen"),
        tr("menu.opt_snippets", "📝 Textbausteine"),
    ]

def get_localized_menu_options_datenaustausch() -> list[str]:
    from services.i18n_service import tr
    return [
        tr("menu.opt_email_import", "📥 E-Mail Import"),
        tr("menu.opt_cobra", "🐍 Cobra CRM Import"),
        tr("menu.opt_export", "📤 Export & Übergabe (Strg+E)"),
    ]

# --- Button Labels & UI Action Texts ---
UI_BUTTON_TEXTS = LocalizedDict("ui_buttons", {
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
    "regenerate_summary": "🔄 Zusammenfassung neu generieren",
    "copy_clipboard": "📋 In Zwischenablage kopieren",
    "insert_timeline": "📌 In Fall-Zeitleiste einfügen",
    "rerun_solutions": "🔄 Lösungssuche erneut ausführen",
    "generate_draft": "🔄 Antwort-Entwurf generieren",
    "open_email_draft": "✉ In E-Mail-Entwurf öffnen",
})

# --- Status & Feedback Messages ---
STATUS_MESSAGES = LocalizedDict("status_messages", {
    "snippet_saved": "✓ Textbaustein gespeichert.",
    "snippet_deleted": "✓ Textbaustein gelöscht.",
    "customer_saved": "✓ Praxis-Eintrag erfolgreich gespeichert.",
    "colleague_saved": "✓ Kollegendaten erfolgreich gespeichert.",
    "tags_updated": "✓ Tags erfolgreich aktualisiert.",
    "profile_saved": "✓ Profil & Einstellungen gespeichert.",
    "ai_summary_generated": "✓ Zusammenfassung erfolgreich generiert.",
    "ai_summary_copied": "✓ Zusammenfassung in Zwischenablage kopiert.",
    "ai_summary_timeline_saved": "✓ KI-Zusammenfassung als Zeitleisten-Eintrag gespeichert.",
    "ai_draft_generated": "✓ E-Mail-Antwort-Entwurf generiert.",
    "ai_ollama_online": "🟢 Ollama Local LLM aktiv ({model})",
    "ai_ollama_offline": "⚡ Regelbasierter NLP-Modus (Ollama offline)",
    "ai_processing": "🤖 KI verarbeitet Anfrage...",
})

# --- Validation Error Messages ---
VALIDATION_MESSAGES = LocalizedDict("validation_messages", {
    "snippet_id_required": "Snippet ID is required.",
    "snippet_title_required": "Snippet title is required.",
    "snippet_content_required": "Snippet content cannot be empty.",
    "contact_name_required": "Contact name is required.",
    "customer_id_required": "Customer ID is required.",
    "practice_name_required": "Practice name is required.",
    "case_customer_id_required": "Case customer_id is required.",
    "case_practice_name_required": "Case practice_name is required.",
    "timeline_timestamp_required": "Timeline entry timestamp is required.",
    "timeline_author_required": "Timeline entry author is required.",
    "schema_id_required": "schema_id is required.",
    "title_required": "title is required.",
    "username_required": "Kürzel / Username ist erforderlich.",
    "name_required": "Name ist erforderlich.",
    "field_id_required": "Field ID is required.",
    "label_required": "Label is required.",
    "schema_id_caps_required": "Schema ID is required.",
    "display_name_required": "Display name is required.",
    "case_id_required": "Case ID cannot be empty.",
})


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

# --- Design Tokens: UI Colors ---
COLOR_PRIMARY = "#2563eb"
COLOR_PRIMARY_HOVER = "#1d4ed8"
COLOR_SUCCESS = "forestgreen"
COLOR_SUCCESS_HOVER = "darkgreen"
COLOR_DANGER = "#dc2626"
COLOR_DANGER_HOVER = "#b91c1c"
COLOR_WARNING = "orange"
COLOR_INFO = "dodgerblue"
COLOR_MUTED_GRAY_FG = ("gray75", "gray30")
COLOR_MUTED_GRAY_HOVER = ("gray65", "gray40")
COLOR_PANED_PANE_BG = ("gray92", "#2b2b2b")

# --- Layout & Pane Sizing Tokens ---
PANED_MIN_TOTAL_WIDTH = 100
PANED_PANE_MIN_WIDTH = 100
COCKPIT_SIDEBAR_MIN_WIDTH = 120
COCKPIT_CENTER_MIN_WIDTH = 150
SASH_RESTORE_DELAY_FAST_MS = 100
SASH_RESTORE_DELAY_SLOW_MS = 500
INFO_FRAME_RESIZE_DELTA = 8
WIEDERVORLAGE_MIN_WRAP_WIDTH = 180
WIEDERVORLAGE_WRAP_OFFSET = 10
INFO_FRAME_MIN_WIDTH_THRESHOLD = 50
WIEDERVORLAGE_FALLBACK_MIN_WIDTH = 250
WIEDERVORLAGE_FALLBACK_DEFAULT_WIDTH = 380
WIEDERVORLAGE_MIN_WIDTH = 200
VIP_TAG_DISPLAY = " ★ VIP"
DEFAULT_SIDEBAR_TAB_TIMELINE = "Zeitleiste"
DEFAULT_SIDEBAR_TAB_ATTACHMENTS = "Anhänge"
DEFAULT_SIDEBAR_TAB_WIKI = "Wiki"

# --- User Profile & Color Presets ---
DEFAULT_USER_NAME = "Support Agent"
DEFAULT_USER_COLOR = "#3b82f6"
USER_COLOR_PRESETS = ["#3b82f6", "#10b981", "#8b5cf6", "#f59e0b", "#ef4444", "#06b6d4"]
DEFAULT_DEPARTMENT = "Support"
DEFAULT_SIGNATURE_FILENAME = "email_signature.txt"
#: Timeline author for entries an Outlook/IMAP import created. A technical
#: marker that is stored in the case file, so it stays language independent.
DEFAULT_AUTHOR_EMAIL_IMPORT = "E-Mail Import"
DEFAULT_UI_THEME = "SYSTEM"
DEFAULT_BOARD_COLLAPSED = {"support": False, "dev": False, "followup": False, "completed": False}
DEFAULT_TABLE_COLUMN_WIDTHS = {"case_id": 120, "practice": 220, "title": 280, "actor": 130, "followup": 150, "score": 90}
DEFAULT_TABLE_COLUMN_ORDER = ["case_id", "practice", "title", "actor", "followup", "score"]
DEFAULT_TEXTBOX_HEIGHT = 90
DEFAULT_POPUP_DISPLAY_TARGET = "APP_SCREEN"
POPUP_DISPLAY_TARGETS = ("APP_SCREEN", "PRIMARY_SCREEN")
SUPPORTED_LANGUAGES = ("de", "en", "sv")
FONT_SCALE_PROFILE_MIN = 0.7
FONT_SCALE_PROFILE_MAX = 2.0
DEFAULT_NOTIFICATION_LEVEL = "LEVEL_A"
DEFAULT_POINTS_PER_IDLE_DAY = 15
DEFAULT_DEADLINE_CLOSE_HOURS = 2
DEFAULT_DEADLINE_CLOSE_BONUS = 40
DEFAULT_DEADLINE_OVERDUE_BONUS = 100
DEFAULT_THRESHOLD_YELLOW = 50
DEFAULT_THRESHOLD_RED = 100
DEFAULT_BOOKSTACK_TOKEN_ID = "ENV_BOOKSTACK_TOKEN_ID"
DEFAULT_BOOKSTACK_TOKEN_SECRET = "ENV_BOOKSTACK_TOKEN_SECRET"
DEFAULT_AI_PROVIDER = "OLLAMA"


# --- Design Tokens: Typography ---
FONT_WEIGHT_BOLD = "bold"
FONT_WEIGHT_NORMAL = "normal"
FONT_SIZE_TITLE = 17
FONT_SIZE_SUBTITLE = 14
FONT_SIZE_BODY = 12
FONT_SIZE_CONFIRM = 13
FONT_SIZE_SM = 11
FONT_SIZE_XS = 10
CONFIRM_DIALOG_TEXT_PADDING = 70

# --- Design Tokens: UI Spacing, Padding & Sizing ---
PAD_NONE = 0
PAD_TINY = 1
PAD_XS = 2
PAD_SM = 4
PAD_GAP = 6
PAD_MD = 8
PAD_10 = 10
PAD_LG = 12
PAD_15 = 15
PAD_XL = 16
PAD_2XL = 20
PAD_3XL = 24
PAD_CARD_INSET = 12

SPACING_XS = 2
SPACING_SM = 4
SPACING_MD = 8
SPACING_LG = 12
SPACING_XL = 16
SPACING_2XL = 20

CORNER_RADIUS_NONE = 0
CORNER_RADIUS_XS = 2
CORNER_RADIUS_SM = 4
CORNER_RADIUS_MD = 6
CORNER_RADIUS_LG = 8
CORNER_RADIUS_XL = 12
CORNER_RADIUS_CARD = 8
CORNER_RADIUS_BUTTON = 6
CORNER_RADIUS_ENTRY = 6

BTN_HEIGHT_SM = 24
BTN_HEIGHT_MD = 28
BTN_HEIGHT_LG = 32
BTN_WIDTH_XS = 65
BTN_WIDTH_SM = 80
BTN_WIDTH_RECORDER = 100
BTN_WIDTH_MD = 110
BTN_WIDTH_CLOSE = 120
BTN_WIDTH_LG = 140
BTN_WIDTH_XL = 175
BTN_WIDTH_SIGNATURE = 185
BTN_WIDTH_WIDE = 240

ENTRY_HEIGHT_MD = 28
ENTRY_WIDTH_NUMERIC = 70
ENTRY_WIDTH_SHORTCUT = 110
ENTRY_WIDTH_SM = 140
ENTRY_WIDTH_COMPACT = 185
ENTRY_WIDTH_MD = 220
ENTRY_WIDTH_LG = 320
ENTRY_WIDTH_XL = 360

COMBO_WIDTH_SM = 200
COMBO_WIDTH_MD = 280
LABEL_WIDTH_MD = 140
LABEL_WIDTH_VIP = 150
LABEL_WIDTH_LG = 180
LABEL_WIDTH_XL = 280
PROFILE_TAB_FIELD_WIDTH = 380
SCROLL_FRAME_HEIGHT_SM = 190
TEXTBOX_HEIGHT_SM = 45
BTN_WIDTH_ACTION = 140
USER_COLOR_TILE_SIZE = 10
COLOR_BORDER_DARK = "#18181b"
TIMELINE_NOTE_WRAP_DEFAULT = 280
TIMELINE_NOTE_WRAP_MIN = 180
TIMELINE_NOTE_WRAP_OFFSET = 120
TOOLBAR_BREAK_WIDTH = 640
BTN_WIDTH_ACTION_SM = 95
TOOLTIP_SHORT_DELAY_MS = 250
PRINT_AUTO_DELAY_MS = 400
REPORT_FIELD_LONG_TEXT_THRESHOLD = 80

DEFAULT_VIP_BONUS_POINTS = 50
SNIPPET_TITLE_PREVIEW_LEN = 24

# --- Backup Retention Defaults ---
DEFAULT_BACKUP_DAILY_DAYS = 7
DEFAULT_BACKUP_WEEKLY_WEEKS = 4
DEFAULT_BACKUP_MONTHLY_MONTHS = 6
DEFAULT_BACKUP_ZIP_FILENAME = "SupportCockpit_Backup.zip"

# --- System Data Filenames ---
FILENAME_CASES = "cases.json"
FILENAME_ARCHIVE = "archive.json"
FILENAME_CUSTOMERS = "customers.json"
FILENAME_APP_PROFILE = "app_profile.json"
FILENAME_COLLEAGUES = "colleagues.json"
FILENAME_QUESTION_SCHEMAS = "question_schemas.json"
FILENAME_EXPORT_TEMPLATES = "export_templates.json"
FILENAME_WIKI_INDEX = "wiki_index.sqlite"

# Dialog Sizes (Width x Height)
DIALOG_DIMENSIONS = {
    "new_case": (760, 860),
    "quick_customer": (420, 360),
    "print_report": (680, 600),
    "customer_mgmt": (1024, 720),
    "colleague_mgmt": (1024, 720),
    "tag_mgmt": (620, 520),
    "profile_settings": (1050, 880),
    "template_mgmt": (980, 720),
    "edit_template": (880, 740),
    "schema_builder": (1180, 750),
    "new_schema": (440, 320),
    "convert_schema": (520, 400),
    "followup_flyout": (680, 560),
    "handover": (580, 520),
    "zip_import": (840, 620),
    "snippet_mgmt": (900, 750),
    "snippet_picker": (640, 480),
    "email_draft": (760, 640),
    "calendar_export": (640, 520),
    "help": (1080, 720),
    "cobra_import": (860, 680),
    "export": (820, 860),
    "p2p_diff": (920, 720),
    "email_calendar": (760, 660),
    "ai_assistant": (820, 580),
    "email_import": (850, 600),
    "confirm": (470, 215),
    "followup": (500, 385),
}

DIALOG_MIN_DIMENSIONS = {
    "export": (760, 720),
    "profile_settings": (920, 780),
    "print_report": (620, 500),
    "handover": (520, 460),
    "followup": (460, 350),
    "followup_flyout": (640, 480),
}
FONT_SIZE_TITLE_SM = 16
COLOR_ABSENCE_WARNING = "darkorange"


CASE_PRINT_NOTE_PREVIEW_LEN = 60
SCROLL_HEIGHT_PRINT_TIMELINE = 220
BTN_WIDTH_PRINT = 175
BTN_WIDTH_HTML = 135
COLOR_CANCEL_FG = ("gray70", "gray40")
COLOR_CANCEL_HOVER = ("gray60", "gray50")
FILE_EXT_HTML = ".html"
REPORT_FILENAME_TEMPLATE = "Fallbericht_{case_id}.html"
REPORT_PRINT_FILENAME_TEMPLATE = "Fallbericht_{case_id}_Print.html"

# --- AI & LLM Service Configuration & Prompts ---
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "qwen3.5:9b"
DEFAULT_MODELFILE_PATH = "ollama/Modelfile"
DEFAULT_PVS_MODEL_NAME = "pvs-support"
OLLAMA_FALLBACK_BASE_MODELS = ["qwen3.5:9b", "llama3:latest", "llama3"]
OLLAMA_DOWNLOAD_URL = "https://ollama.com/download"
OLLAMA_LIBRARY_QWEN_URL = "https://ollama.com/library/qwen2.5"
OLLAMA_LIBRARY_LLAMA_URL = "https://ollama.com/library/llama3"
OLLAMA_TIMEOUT_STATUS = 1.5
OLLAMA_TIMEOUT_GENERATE = 120.0
AI_USER_AGENT = "SupportCockpit/1.0"

# --- Gemini API Configuration ---
DEFAULT_GEMINI_MODEL = "gemini-3.6-flash"
AVAILABLE_GEMINI_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-2.5-flash",
    "gemini-flash-latest",
    "gemini-2.5-pro",
    "gemini-2.5-flash-lite",
]
GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

AI_SYSTEM_ROLE_DEFAULT = "Du bist ein hochqualifizierter IT-Support-Assistent für Arztpraxis-Software im deutschen Gesundheitswesen."
AI_SYSTEM_ROLE_EMAIL = "Du bist ein freundlicher IT-Support-Mitarbeiter im deutschen Gesundheitswesen."

AI_PROMPT_BASE_RULES_HEADER = "--- GLOBALE BASIS-REGELN ---"
AI_PROMPT_PRACTICE_RULES_HEADER = "--- PRAXIS-SPEZIFISCHE REGELN (VORRANGIG UND BINDEND!) ---"
AI_PROMPT_OVERRIDE_NOTICE = "WICHTIGER HINWEIS: Die folgenden Praxis-Regeln haben IMMER Vorrang vor den globalen Basis-Regeln! Falls eine Praxis-Regel einer Basis-Regel widerspricht, musst du dich ZWINGEND an die Praxis-Regel halten:"
AI_PROMPT_CUSTOM_INSTRUCTION_HEADER = "--- BENUTZERDEFINIERTE SONDERANWEISUNG (ALLERHÖCHSTE PRIORITÄT!) ---"
AI_PROMPT_CUSTOM_INSTRUCTION_NOTICE = "WICHTIGER HINWEIS: Die folgende Anweisung wurde vom Benutzer für diesen Generierungslauf vorgegeben. Sie hat ALLERHÖCHSTE PRIORITÄT und übersteuert im Konfliktfall sowohl Basis-Regeln als auch Praxis-Regeln. Du MUSST dich strikt daran halten:"

# --- AI Status & Action Messages ---
AI_STATUS_ONLINE_LOADED = "🟢 Ollama Server Online ({count} Modelle installiert | Geladen im Speicher: {models})"
AI_STATUS_ONLINE_STANDBY = "🔵 Ollama Server Online ({count} Modelle installiert | Standby — Kein Modell im Speicher)"
AI_STATUS_ONLINE_DISABLED = "⚪ Ollama Server Online ({count} Modelle installiert | KI global deaktiviert)"
AI_STATUS_OFFLINE_LABEL = "🔴 Ollama Server nicht erreichbar / Offline (unter {url})"
AI_STATUS_GEMINI_ACTIVE = "🟢 Google Gemini API aktiv ({model} | DSGVO-Anonymisiert)"
AI_STATUS_GEMINI_NO_KEY = "🔴 Google Gemini API Key fehlt oder ungültig"
AI_STATUS_CHECKING = "🔍 Prüfe KI-Status im Hintergrund..."
AI_STATUS_UNLOADING = "⏳ Deaktiviere KI global & entlade Modelle aus Arbeitsspeicher..."
AI_STATUS_UNLOADED = "⚡ KI global deaktiviert & Modelle aus Arbeitsspeicher entladen."
AI_STATUS_ACTIVATED = "✅ KI global aktiviert."
AI_STATUS_STARTING = "⏳ Versuche Ollama Server im Hintergrund zu starten..."
AI_STATUS_STOPPING = "⏳ Beende Ollama Server-Prozess..."

AI_NO_MODELS_TITLE = "⚠ Keine KI-Modelle in Ollama installiert!"
AI_NO_MODELS_DESC = "Bitte laden Sie ein Modell wie qwen2.5:7b oder llama3 über die Ollama-Bibliothek herunter:"

AI_BADGE_ACTIVE = "🟢 Ollama Local LLM aktiv ({model})"
AI_BADGE_GEMINI_ACTIVE = "🟢 Google Gemini aktiv ({model} | Anonymisiert)"
AI_BADGE_STANDBY = "🔵 Ollama Standby ({model})"
AI_BADGE_DISABLED = "⚪ KI global deaktiviert (Schalter OFF)"
AI_BADGE_NLP_FALLBACK = "⚡ Regelbasierter NLP-Modus (KI Offline/Ohne Key)"

# --- AI Button Labels & UI Action Texts ---
AI_BTN_GENERATE_DRAFT = "🤖 KI-Entwurf generieren"
AI_BTN_GENERATE_DRAFT_DISABLED = "🤖 KI-Entwurf (KI global inaktiv)"
AI_BTN_GLOBAL_TOGGLE = "🤖 KI- & NLP-Unterstützung global aktivieren"
AI_BTN_GLOBAL_TOGGLE_HEADER = "🤖 KI Global Aktiv"
AI_BTN_START_SERVER = "▶ Ollama Server Starten"
AI_BTN_STOP_SERVER = "🛑 Server Beenden"
AI_BTN_TEST_GEMINI_KEY = "🔑 Gemini Key Testen"
AI_BTN_DOWNLOAD_OLLAMA = "🌐 Ollama Herunterladen & Installieren (ollama.com/download)"
AI_BTN_DOWNLOAD_QWEN = "🌐 qwen2.5 Download (ollama.com/library/qwen2.5)"
AI_BTN_DOWNLOAD_LLAMA = "🌐 llama3 Download (ollama.com/library/llama3)"
AI_BTN_CREATE_PVS_MODEL = "⚡ PVS-Support Modell aus Modelfile erstellen"
AI_BTN_PRELOAD_MODEL = "▶ Modell Laden (Preload)"
AI_BTN_UNLOAD_MODEL = "⏹ Modell Entladen"

# --- Text Widget Paragraph Line Spacing ---
TEXTBOX_SPACING1_PARAGRAPH = 4
TEXTBOX_SPACING3_PARAGRAPH = 6
TEXTBOX_SPACING2_PARAGRAPH = 1

# --- Design System Color Tokens ---
COLOR_AI_PURPLE = "#6366f1"
COLOR_AI_PURPLE_HOVER = "#4f46e5"
COLOR_BADGE_GREEN = "forestgreen"
COLOR_BADGE_BLUE = "dodgerblue"
COLOR_BADGE_GRAY = "gray"
COLOR_CANCEL = ("gray70", "gray40")
COLOR_MUTED_GRAY = ("gray75", "gray30")
COLOR_MUTED_HOVER = ("gray65", "gray40")
COLOR_SASH_DARK = "#2b2b2b"
COLOR_SASH_LIGHT = "#ebebeb"
COLOR_PANEL_BG = ("#ffffff", "gray23")
COLOR_PANEL_BORDER = ("gray75", "gray38")
COLOR_PANEL_ALT_BG = ("#f4f4f5", "gray26")

COLOR_CARD_BG = ("#ffffff", "gray23")
COLOR_CARD_BORDER = ("gray75", "gray38")
COLOR_CARD_HOVER = ("#f3f4f6", "gray28")
COLOR_CARD_SELECTED = ("#e0e7ff", "gray30")
COLOR_CARD_SELECTED_BG = ("gray80", "gray28")
COLOR_CARD_DESELECTED_BG = ("gray92", "gray15")
COLOR_CARD_SELECTED_BORDER = ("dodgerblue", "dodgerblue")
COLOR_DEEP_SEARCH_ACTIVE = "darkmagenta"
COLOR_DEEP_SEARCH_ACTIVE_HOVER = "purple"
COLOR_DEEP_SEARCH_INACTIVE = "gray30"
COLOR_DEEP_SEARCH_INACTIVE_HOVER = "gray40"
COLOR_DEEP_ATTACHMENT = "plum"
COLOR_DEEP_WIKI = "orchid"
COLOR_TAG_BLUE = ("dodgerblue", "cyan")

# --- Case List Dimensions & Tokens ---
CASE_LIST_BATCH_SIZE = 12
CASE_LIST_WRAP_DEFAULT = 250
CASE_LIST_WRAP_MIN = 160
CASE_LIST_WRAP_OFFSET = 40
CASE_LIST_WRAP_TOLERANCE = 6
BTN_WIDTH_FILTER_ALL = 45
BTN_WIDTH_FILTER_FOLLOWUP = 105
BTN_WIDTH_FILTER_DEEP = 100
CASE_LIST_PRACTICE_PREVIEW_LEN = 60
CASE_LIST_TITLE_PREVIEW_LEN = 80
CASE_LIST_SNIPPET_PREVIEW_LEN = 35
TOOLTIP_LAZY_DELAY_MS = 400

# --- Board View Tokens ---
BOARD_CARD_WRAP_WIDTH = 260
BTN_WIDTH_CARD_ACTION = 70
BTN_WIDTH_BOARD_REMIND = 75
BADGE_HEIGHT_SM = 20
BOARD_COLLAPSED_COL_WIDTH = 42
BOARD_EXPANDED_COL_MIN_WIDTH = 170
BOARD_HEADER_HEIGHT = 36
COLOR_SCORE_HIGH = "firebrick"
COLOR_SCORE_MEDIUM = "darkgoldenrod"
COLOR_SCORE_LOW = "darkgreen"
COLOR_COLLAPSED_COL_BG = ("gray80", "gray25")
COLOR_BTN_GRAY = "gray50"
COLOR_BTN_GRAY_HOVER = ("gray65", "gray45")
COLOR_BTN_EXPAND_HOVER = ("gray65", "gray50")
COLOR_BOARD_REMIND = "darkblue"
COLOR_FOLLOWUP_FG = ("darkblue", "lightblue")
COLOR_CARD_TITLE_FG = ("gray20", "gray85")
COLOR_MUTED_LABEL = ("gray50", "gray60")
COLOR_COMPLETED_GRAY = "gray40"


# --- Additional AI UI Labels & Instructions ---
AI_OFFLINE_DESC = (
    "Ollama Server ist auf diesem PC (unter http://localhost:11434) aktuell offline oder nicht erreichbar.\n"
    "Sie können den Server direkt starten oder Ollama kostenlos herunterladen:"
)
AI_LABEL_BASE_RULES_TITLE = "📋 Globale Basis-Regeln & Prompt-Anweisungen (1 Regel pro Zeile):"
AI_LABEL_BASE_RULES_HINT = "z. B. 'Immer im Sie-Stil antworten', 'Keine internen Fachbegriffe ohne Erklärung nutzen', 'Freundliche E-Mail-Signatur verwenden'"
AI_LABEL_SELECT_MODEL = "Installiertes Modell auswählen:"
AI_LABEL_OLLAMA_URL = "Ollama URL:"
AI_LABEL_CUSTOM_INSTRUCTION = "⚡ Priorisierte KI-Sonderanweisung für diesen Lauf:"
AI_HINT_CUSTOM_INSTRUCTION = "z.B. Nur Stichpunkte verwenden, bestimmte Grüße erzwingen, Tonfall anpassen..."
AI_LABEL_EMAIL_CUSTOM_INSTRUCTION = "⚡ Priorisierte KI-Sonderanweisung:"
AI_HINT_EMAIL_CUSTOM_INSTRUCTION = "z.B. Stichpunkte verwenden, bestimmte Grüße erzwingen, Tonfall anpassen..."
AI_STATUS_DISABLED_HINT = "⚠ KI global deaktiviert (Schalter oben rechts auf OFF). Buttons deaktiviert."

AI_BTN_SUMMARY = "🤖 KI-Zusammenfassung generieren"
AI_BTN_SOLUTIONS = "💡 Lösungsansätze suchen"
AI_BTN_DRAFT = "✉ Antwort-Entwurf erstellen"
AI_BTN_SUMMARY_RERUN = "🔄 Zusammenfassung neu generieren"
AI_BTN_COPY = "📋 Kopieren"
AI_BTN_TIMELINE = "📌 In Zeitleiste"
AI_BTN_OPEN_ASSISTANT = "🤖 KI-Assistent öffnen"

# --- Additional Color Tokens ---
COLOR_TEXT_RED = "red"
COLOR_TEXT_GREEN = "green"
COLOR_TEXT_ORANGE = "orange"
COLOR_TEXT_GRAY = "gray"
COLOR_TEXT_WHITE = "white"
COLOR_TEXT_BLUE = "dodgerblue"
COLOR_PURPLE_DARK = "darkviolet"
COLOR_PRIMARY_BLUE = "dodgerblue"
COLOR_MUTED_DISABLED = ("gray50", "gray70")
COLOR_MUTED_BODY = ("gray30", "gray80")

COLOR_TOOLTIP_BG = ("gray20", "gray10")
COLOR_TOOLTIP_BORDER = ("gray60", "gray40")
COLOR_TOOLTIP_TEXT = ("gray95", "gray95")

COLOR_URGENCY_RED = ("#991b1b", "#f87171")
COLOR_URGENCY_YELLOW = ("#92400e", "#fbbf24")
COLOR_URGENCY_GREEN = ("#166534", "#4ade80")
COLOR_WARNING_ORANGE = ("#9a3412", "#fb923c")

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
    "Zuzahlungsnachforderung",
    "Kunde Wütend",
    "Kundenwunsch",
    "Fragen",
    "Rückmeldung",
    "Informationen",
    "HelloCloud"
]

DEFAULT_MODULE_TAGS = [
    "Fakturaübersicht",
    "Terminkalender",
    "System allgemein",
    "Benutzerverwaltung und Einstellungen",
    "Go2Doc",
    "Heilmittelkatalog",
    "Kostenträgerliste",
    "Heilmittelpreisliste",
    "Fabius",
    "Termed",
    "Benutzerrechte",
    "Patientenstamm",
    "Terminabrechnung",
    "Rezeptnachvervollgung",
    "Ausgangsbelege",
    "Kassenbuch",
    "Statistiken",
    "Kartei",
    "Terminarten",
    "Ressourcen",
    "Datenbank",
    "ESOL Dateien",
    "Abrechnung",
]

DEFAULT_INTERNAL_TASK_CATEGORIES = [
    "Fernwartung",
    "Datenaustausch",
    "Dokumentation",
    "Entwicklungsaufgabe",
    "Prozessverbesserung",
    "Bugfix",
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

DEFAULT_HANDOVER_CHANNELS = [
    "Persönliche Absprache",
    "E-Mail",
    "Telefonanruf",
    "Slacknachricht",
    "GitLab Issue",
    "Sonstiges",
]


def get_localized_departments() -> list[str]:
    from services.i18n_service import tr
    return [tr(f"departments.{d}", default=d) for d in DEFAULT_DEPARTMENTS]


def get_localized_handover_channels() -> list[str]:
    from services.i18n_service import tr
    return [tr(f"handover_channels.{c}", default=c) for c in DEFAULT_HANDOVER_CHANNELS]


def get_localized_task_categories() -> list[str]:
    from services.i18n_service import tr
    return [tr(f"internal_task_categories.{c}", default=c) for c in DEFAULT_INTERNAL_TASK_CATEGORIES]

DEFAULT_SNIPPET_CATEGORY = "Allgemein"

# --- Cobra CRM Field Aliases ---
COBRA_FIELD_ALIAS_MAP = {
    "customer_id": ["vnum1", "kunden_nr", "kundennr", "kunden-nr", "id", "kdnr", "kunden_id", "customer_id", "kunden nummer", "debitor"],
    "vnum1": ["vnum1", "vnum", "vnum_1"],
    "practice_name": ["praxisname", "firma", "praxis", "name1", "name", "firmenname", "practice_name", "organisation", "unternehmen"],
    "practice_name_old": ["praxisname_alt", "praxisname alt", "altname", "firma_alt", "name_alt"],
    "salutation": ["anrede", "salutation", "titel"],
    "first_name": ["vorname", "firstname", "first_name"],
    "last_name": ["nachname", "lastname", "last_name"],
    "contact_person": ["ansprechpartner", "ansprechpartnerin", "kontakt", "name2", "contact_person", "kontaktperson", "arzt", "ärztin"],
    "street": ["straße", "strasse", "str.", "str", "street", "anschrift"],
    "zip_code": ["plz", "postleitzahl", "zip", "zip_code"],
    "city": ["ort", "stadt", "city"],
    "phone": ["telefon", "tel", "telefonnummer", "tel.nr", "fon", "phone", "telefon_nr"],
    "phone_main": ["telefon", "tel", "telefonnummer", "tel.nr", "fon", "phone", "telefon_nr"],
    "phone_direct": ["telefon direkt", "tel direkt", "teldirekt", "durchwahl", "telefon_direkt"],
    "phone_private": ["telefon privat", "tel privat", "telprivat", "telefon_privat"],
    "phone2": ["telefon2", "telefon 2", "tel2", "tel 2"],
    "phone3": ["telefon3", "telefon 3", "tel3", "tel 3"],
    "mobile": ["mobil", "handy", "mobile", "mobiltelefon"],
    "mobile_private": ["mobil privat", "handy privat", "mobil_privat"],
    "email": ["email", "e-mail", "mail", "elektronische post", "e_mail", "email_address", "email1", "e-mail 1"],
    "email_address": ["email", "e-mail", "mail", "elektronische post", "e_mail", "email_address", "email1", "e-mail 1"],
    "email2": ["email2", "e-mail 2", "email 2", "e-mail2", "mail 2", "mail2", "e-mail privat", "email privat", "email_2", "e_mail2"],
    "email3": ["email3", "e-mail 3", "email 3", "e-mail3", "mail 3", "mail3", "e-mail alt", "email alt", "email_3", "e_mail3"],
    "system_version": ["systemversion", "version", "system", "pvs-version", "pvs_version", "release"],
    "dsc": ["dsc", "dsc_alt", "dsc-alt"],
    "dsc_neu": ["dscneu", "dsc_neu", "dsc-neu"],
    "is_vip": ["vip", "wichtig", "priorität", "vip_kunde", "is_vip", "prio"],
    "vm_number": ["vm", "vm_nr", "vm-nr", "vm_nummer", "vm_number"],
    "instance_number": ["instanz", "instanz_nr", "mandant", "instance_number", "instanz_nummer"],
    "general_notes": ["notizen", "bemerkung", "kommentar", "hinweis", "general_notes", "memo", "beschreibung"],
}

# --- Supported File Extensions & Types ---
IMAGE_FILE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
TEXT_FILE_EXTENSIONS = {".txt", ".log", ".json", ".sql", ".xml", ".csv", ".ini", ".md"}
FILE_EXT_ICS = ".ics"
ICS_FILENAME_TEMPLATE_APPOINTMENT = "Termin_Fall_{case_id}.ics"
ICS_FILENAME_TEMPLATE_CALLBACK = "Rueckruf_Fall_{case_id}.ics"

# The file-dialog type descriptions are user-visible, so they are built on demand
# instead of being frozen at import time - a module-level list would keep the
# language the app happened to start in. The glob patterns stay untranslated.
def get_file_types_markdown_export() -> list[tuple[str, str]]:
    from services.i18n_service import tr
    return [
        (tr("file_types.markdown", "Markdown"), "*.md"),
        (tr("file_types.text", "Text"), "*.txt"),
        (tr("file_types.all_files", "Alle Dateien"), "*.*"),
    ]

def get_file_types_html_report() -> list[tuple[str, str]]:
    from services.i18n_service import tr
    return [
        (tr("file_types.html_report", "HTML-Bericht (für PDF-Druck)"), "*.html"),
        (tr("file_types.all_files", "Alle Dateien"), "*.*"),
    ]

def get_file_types_zip() -> list[tuple[str, str]]:
    from services.i18n_service import tr
    return [(tr("file_types.zip_archive", "ZIP-Archiv"), "*.zip")]

def get_file_types_ics() -> list[tuple[str, str]]:
    from services.i18n_service import tr
    return [
        (tr("file_types.ics", "iCalendar-Dateien (*.ics)"), "*.ics"),
        (tr("file_types.all_files", "Alle Dateien"), "*.*"),
    ]

def get_file_types_cobra_export() -> list[tuple[str, str]]:
    from services.i18n_service import tr
    return [
        (tr("file_types.cobra_export", "Cobra / CSV Dateien (*.csv, *.txt, *.json)"), "*.csv;*.txt;*.json"),
        (tr("file_types.all_files", "Alle Dateien"), "*.*"),
    ]

def get_file_types_data_file(file_pattern: str) -> list[tuple[str, str]]:
    from services.i18n_service import tr
    return [
        (tr("file_types.data_file", "Datendatei"), file_pattern),
        (tr("file_types.all_files", "Alle Dateien"), "*.*"),
    ]

def get_file_types_signature_export() -> list[tuple[str, str]]:
    from services.i18n_service import tr
    return [
        (tr("file_types.text_file", "Textdatei (*.txt)"), "*.txt"),
        (tr("file_types.html_file", "HTML-Datei (*.html)"), "*.html"),
        (tr("file_types.markdown_file", "Markdown (*.md)"), "*.md"),
        (tr("file_types.all_files_pattern", "Alle Dateien (*.*)"), "*.*"),
    ]

def get_file_types_signature_import() -> list[tuple[str, str]]:
    from services.i18n_service import tr
    return [
        (tr("file_types.signature_combined", "Text- & Web-Dateien (*.txt, *.html, *.md)"), "*.txt *.html *.htm *.md"),
        (tr("file_types.text_file", "Textdatei (*.txt)"), "*.txt"),
        (tr("file_types.html_htm_file", "HTML-Datei (*.html, *.htm)"), "*.html *.htm"),
        (tr("file_types.markdown_file", "Markdown (*.md)"), "*.md"),
        (tr("file_types.all_files_pattern", "Alle Dateien (*.*)"), "*.*"),
    ]

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
# How often the app looks for a case handed over by a clicked notification.
# The second process is already gone by then, so this interval is all the delay
# the user perceives between the click and the case appearing.
OPEN_CASE_POLL_INTERVAL_MS = 800
# Wartezeit nach dem letzten Tastendruck, bevor eine Suche ausgefuehrt wird.
# Ohne sie loest jeder einzelne Buchstabe eine vollstaendige Filterung samt
# Neuaufbau der Trefferliste aus - beim Tippen von drei Buchstaben dreimal,
# wobei der zweite Tastendruck erst nach der ersten Liste ueberhaupt ankommt.
SEARCH_DEBOUNCE_MS = 220
TOAST_DURATION_DEFAULT_MS = 5000
TOOLTIP_DEFAULT_DELAY_MS = 300
TOOLTIP_POINTER_OFFSET_X = 15
TOOLTIP_POINTER_OFFSET_Y = 15

# --- Date & Time Formats ---
GERMAN_DATE_FORMAT = "%d.%m.%Y"
GERMAN_DATETIME_FORMAT = "%d.%m.%Y %H:%M"
ISO_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"

# --- Default Keyboard Shortcuts & Hotkey Recorder UI Strings ---
DEFAULT_SHORTCUTS = {
    "new_case": "<Control-n>",
    "search_customer": "<Control-f>",
    "wiki_search": "<Control-w>",
    "export_dialog": "<Control-e>",
    "save_case": "<Control-s>",
    "archive_case": "<Control-Shift-A>",
    "open_settings": "<Control-p>",
    "snippet_picker": "<Control-m>",
    "view_cockpit": "<Control-1>",
    "view_board": "<Control-2>",
    "view_table": "<Control-3>",
    "view_analytics": "<Control-4>",
    "toggle_theme": "<Control-t>",
}

HOTKEY_ACTION_LABELS = LocalizedHotkeyDict("hotkey_actions", {
    "new_case": "Neuer Fall:",
    "save_case": "Fall speichern:",
    "archive_case": "Fall archivieren:",
    "export_dialog": "Export Dialog:",
    "open_settings": "Einstellungen öffnen:",
    "snippet_picker": "Snippet-Picker öffnen:",
    "wiki_search": "Wiki-Suche fokussieren:",
    "search_customer": "Kundensuche fokussieren:",
    "view_cockpit": "Cockpit-Ansicht:",
    "view_board": "Board-Ansicht:",
    "view_table": "Tabelle-Ansicht:",
    "view_analytics": "Auswertungs-Ansicht:",
    "toggle_theme": "Theme umschalten:",
})

HOTKEY_ACTION_LABELS_MAP = HOTKEY_ACTION_LABELS


def get_localized_hotkey_action_labels() -> list[tuple[str, str]]:
    return list(HOTKEY_ACTION_LABELS.items())


HOTKEY_RECORDER_TITLE = "⌨ Hotkey aufnehmen"
HOTKEY_RECORDER_HEADER = "⌨ Tastenkombination drücken"
HOTKEY_RECORDER_INFO = "Drücken Sie Ihre Tasten (z.B. Strg+S, Alt+1)..."
HOTKEY_RECORDER_CANCEL = "Abbrechen (Esc)"
HOTKEY_RECORDER_DIMENSIONS = (380, 160)
HOTKEY_RECORDER_BUTTON = "🎙 Taste erfassen"

STATUS_SHORTCUT_CONFLICT = "⚠ Shortcut-Konflikt: Folgende Hotkeys sind mehrfach zugewiesen: {dup_str}"
STATUS_SHORTCUT_CONFLICT_GENERIC = "⚠ Shortcut-Konflikt: Hotkeys dürfen nicht mehrfach zugewiesen werden!"

LABEL_APP_SHORTCUTS_HEADER = "⚡ App-Aktionen Tastenkürzel (Hotkeys)"
LABEL_SNIPPET_SHORTCUTS_HEADER = "📝 Textbaustein-Makros (Snippet Shortcuts)"
LABEL_NO_SNIPPETS = "Keine Textbausteine vorhanden."
LABEL_SNIPPET_SHORTCUT_FIELD = "Tastenkürzel / Macro (z. B. <Control-Alt-1>):"
TOAST_SNIPPET_MACRO_TITLE = "Textbaustein Macro"
TOAST_SNIPPET_NO_FOCUS = "Kein fokussiertes Eingabefeld vorhanden."

# --- UI Utility Tokens ---
SCROLLBAR_HYSTERESIS_PX = 24
SCROLLBAR_MAX_FLIPS = 12
SCROLLBAR_CHECK_DELAYS_MS = (50, 150, 350)
MIN_WINDOW_VISIBLE_DIM = 50
MINIMIZED_WINDOW_COORD_THRESHOLD = -32000
WINDOW_CENTER_FALLBACK_WIDTH = 800
WINDOW_CENTER_FALLBACK_HEIGHT = 600
MOUSEWHEEL_DELTA_UNIT = 120
DEFAULT_TEXT_WRAP_WIDTH = 300
DEFAULT_TEXT_WRAP_MAX_LINES = 2
DEFAULT_ELLIPSIS = "..."
FALLBACK_CHAR_PIXEL_WIDTH = 7
COLOR_SEARCH_HIGHLIGHT = ("#D97706", "#F59E0B")
HIGHLIGHT_LABEL_MAX_CHARS = 35
HIGHLIGHT_LABEL_MAX_LINES = 6
COLOR_FALLBACK_TEXT_BG = ("#ebebeb", "#2b2b2b")
DEFAULT_FONT_FAMILY_FALLBACK = "Segoe UI"
DEFAULT_FONT_SIZE_FALLBACK = 11
CUSTOMER_SEARCH_MAX_MATCHES = 3
CUSTOMER_SEARCH_MAX_CHARS = 50
SEARCH_STRIP_PUNCTUATION = ",;:()[]{}<>\"'\t\r\n"
SEPARATOR_COMMA_SPACE = ", "

# --- Wiki Widget Tokens ---
BTN_WIDTH_WIKI_SYNC = 100
WIKI_SNIPPET_WRAP_LENGTH = 280
COLOR_WIKI_LINK = "dodgerblue"
COLOR_WIKI_SNIPPET = ("gray30", "gray80")
DEBOUNCE_KEY_WIKI_SEARCH = "wiki_search"
ICON_DOC = "📄"
ICON_SUCCESS = "✅"
ICON_WARNING = "⚠"
ICON_WAITING = "⏳"
BORDER_WIDTH_CARD = 1

# --- Toast Notification Tokens ---
TOAST_WIDTH_DEFAULT = 360
TOAST_WIDTH_ACTION = 420
TOAST_HEIGHT = 84
TOAST_OFFSET_X = 20
TOAST_OFFSET_Y = 60
COLOR_TOAST_BG = ("gray90", "gray20")
COLOR_TOAST_BORDER = "dodgerblue"
BORDER_WIDTH_TOAST = 2
COLOR_TOAST_BTN_HOVER = "deepskyblue"
COLOR_TOAST_MSG = ("gray10", "white")
SYSTEM_APP_ID = "Support-Cockpit"
WINOTIFY_DURATION_SHORT = "short"

# --- Dynamic Form Tokens ---
COLOR_RESIZE_HANDLE = ("gray75", "gray35")
HEIGHT_RESIZE_HANDLE = 7
CURSOR_RESIZE_V = "sb_v_double_arrow"
CURSOR_HAND = "hand2"
TEXTBOX_MIN_HEIGHT = 50
TEXTBOX_MAX_HEIGHT = 600
TEXTBOX_DEFAULT_HEIGHT = 90
TEXTBOX_DEFAULT_WIDTH = 520
TEXTBOX_VISIBLE_THRESHOLD_TOP = 0.001
TEXTBOX_VISIBLE_THRESHOLD_BOTTOM = 0.999

POPUP_TAG_PICKER_GEOMETRY = "450x440"
POPUP_TAG_PICKER_WIDTH = 450
POPUP_TAG_PICKER_HEIGHT = 440
POPUP_TAG_PICKER_MIN_WIDTH = 380
POPUP_TAG_PICKER_MIN_HEIGHT = 320

BTN_WIDTH_TAG_QUICK = 110
BTN_HEIGHT_TAG_QUICK = 24
BTN_WIDTH_TAG_APPLY = 160
CHECKBOX_TAG_WIDTH = 24
COLOR_BTN_SECONDARY = "gray30"
COLOR_BTN_SECONDARY_HOVER = "gray40"

BORDER_COLOR_MISSING = "red"
BORDER_WIDTH_MISSING = 2

COLOR_REPEATABLE_CARD_BG = ("gray90", "gray22")
COLOR_CARD_BORDER_DEFAULT = ("gray75", "gray35")
COLOR_ACCENT_BLUE = ("dodgerblue", "deepskyblue")
BTN_WIDTH_REMOVE_CARD = 140
BTN_HEIGHT_REMOVE_CARD = 24
BTN_HEIGHT_ADD_CARD = 32

FILE_NAME_DATA_BACKUP = "data-al.backup"
DEFAULT_ATTACHMENTS_DIR = os.path.join("data", "attachments")

COLOR_MINI_ATTACH_BG = ("gray92", "gray18")
COLOR_MINI_ATTACH_ROW_BG = ("gray85", "gray25")
HEIGHT_MINI_ATTACH_SCROLL = 90
HEIGHT_MINI_ATTACH_ROW = 24
BTN_WIDTH_IMPORT_FILES = 150
BTN_WIDTH_OPEN_FILE = 65
HEIGHT_OPEN_FILE_BTN = 20
COLOR_OPEN_FILE_BTN = "gray35"
COLOR_OPEN_FILE_BTN_HOVER = "gray45"

BYTES_PER_KB = 1024.0

BTN_WIDTH_MANAGE_TAGS = 140
BTN_HEIGHT_MANAGE_TAGS = 22
COLOR_BTN_MANAGE_TAGS = ("gray75", "gray30")
COLOR_BTN_MANAGE_TAGS_HOVER = ("gray65", "gray40")

COLOR_TAG_PICKER_BTN_BG = ("gray85", "gray25")
COLOR_TAG_PICKER_BTN_HOVER = ("gray75", "gray35")
COLOR_TAG_PICKER_BTN_TEXT = ("gray10", "white")
HEIGHT_TAG_PICKER_BTN = 32

DEFAULT_BROWSER_OPTIONS = ("Firefox", "Edge", "Chrome", "Unbekannt")
BROWSER_OPTION_UNKNOWN = "Unbekannt"
COLOR_PILL_BOX_BG = ("gray90", "gray20")
COLOR_PILL_ACTIVE = "dodgerblue"
COLOR_PILL_INACTIVE = ("gray80", "gray30")
COLOR_PILL_HOVER = "deepskyblue"
COLOR_PILL_TEXT_ACTIVE = "white"
COLOR_PILL_TEXT_INACTIVE = ("gray10", "white")
HEIGHT_BROWSER_PILL = 26

ENTRY_WIDTH_DATE = 295
BTN_WIDTH_CALENDAR = 95
COMBO_WIDTH_FORM = 400
COLOR_DROPDOWN_MISSING_BTN = "darkred"
COLOR_DROPDOWN_MISSING_BG = "firebrick"
BTN_WIDTH_IMPORT_BACKUP = 190
COLOR_BTN_IMPORT_BACKUP = "darkblue"
COLOR_BTN_IMPORT_BACKUP_HOVER = "blue"

ENTRY_WIDTH_FILE = 280
BTN_WIDTH_CHOOSE_FILE = 110
ENTRY_WIDTH_FORM_DEFAULT = 400

DEBOUNCE_KEY_TAG_SEARCH = "tag_search"
DEBOUNCE_KEY_COMBOBOX_SEARCH = "combobox_search"

# SearchableCombobox Design Tokens
COMBO_DEFAULT_WIDTH = 380
COMBO_DEFAULT_HEIGHT = 32
COLOR_COMBO_BTN_BG = ("gray85", "gray25")
COLOR_COMBO_BTN_HOVER = ("gray75", "gray32")
POPOVER_MIN_WIDTH = 360
POPOVER_MIN_HEIGHT = 120
POPOVER_MAX_HEIGHT = 280
POPOVER_ITEM_HEIGHT = 32
POPOVER_HEADER_HEIGHT = 45
COLOR_POPOVER_BG = ("gray90", "gray18")
COLOR_BORDER_POPOVER = "dodgerblue"
COLOR_TEXT_PRIMARY = ("black", "white")
HEIGHT_SEARCH_ENTRY = 30
HEIGHT_COMBO_OPTION = 28
COLOR_ITEM_SELECTED = ("#2563eb", "#1d4ed8")
COLOR_ITEM_HOVER = ("gray75", "gray35")
COLOR_SUBTITLE_MUTED = ("gray45", "gray65")
DELAY_FOCUS_RESTORE_MS = 10
DELAY_POPOVER_CLOSE_MS = 100

# Tag Management Dialog Design Tokens
DIALOG_MIN_SIZE_TAG_MGMT = (580, 520)
HEIGHT_HEADER_BAR = 45
COLOR_BTN_ADD_TAG = "forestgreen"
COLOR_ROW_ALT = ("gray90", "gray20")
DEBOUNCE_KEY_MODULE_SEARCH = "module_search"
DELAY_SCROLL_RESET_SHORT_MS = 50
DELAY_SCROLL_RESET_LONG_MS = 200

# Snippet Picker Dialog Design Tokens
DIALOG_MIN_SIZE_SNIPPET_PICKER = (680, 480)
DEBOUNCE_KEY_SNIPPET_SEARCH = "snippet_search"
COMBO_WIDTH_CATEGORY = 160
SNIPPET_PICKER_COL0_MIN_WIDTH = 300
SNIPPET_PICKER_COL1_MIN_WIDTH = 340
COLOR_SNIPPET_CARD_SEL = ("gray80", "gray25")
COLOR_SNIPPET_CARD_BG = ("gray90", "gray15")
COLOR_SNIPPET_PREVIEW_TEXT = ("gray40", "gray70")
SNIPPET_PREVIEW_MAX_LEN = 60

# Help Dialog Design Tokens
DIALOG_MIN_SIZE_HELP = (960, 600)
HEIGHT_HELP_TOP_BAR = 50
HELP_NAV_SIDEBAR_WIDTH = 280
FONT_SIZE_HELP_TITLE = 18
COLOR_HELP_NAV_ACTIVE = ("gray75", "gray30")
COLOR_HELP_NAV_INACTIVE = ("gray85", "gray20")
COLOR_HELP_NAV_HOVER = ("gray70", "gray35")
HELP_SNIPPET_PRE_LEN = 20
HELP_SNIPPET_POST_LEN = 30
COLOR_TABLE_BG = ("gray85", "gray20")
COLOR_TABLE_HDR_BG = ("gray70", "gray30")
COLOR_TABLE_ROW_ALT = ("gray90", "gray22")
COLOR_TABLE_ROW_BG = ("gray85", "gray25")
HEIGHT_HR = 2
COLOR_SEPARATOR = ("gray75", "gray35")
FONT_SIZE_H3 = 15
COLOR_ACCENT_HEADING = ("dodgerblue", "#4dabf7")
COLOR_BULLET = ("dodgerblue", "cyan")
BULLET_PREFIX_WIDTH = 20
HELP_BULLET_WRAP_LEN = 560
HELP_PARA_WRAP_LEN = 580
DEBOUNCE_KEY_HELP_SEARCH = "help_search"

# Email Draft Dialog Design Tokens
DIALOG_MIN_SIZE_EMAIL_DRAFT = (700, 520)
BTN_WIDTH_PRAXISKARTEI = 135
BTN_WIDTH_SUGGESTION_CLOSE = 70
BTN_HEIGHT_SUGGESTION_CLOSE = 20
HEIGHT_SUGGESTIONS_SCROLL = 130
MAX_SUGGESTIONS_COUNT = 20
COLOR_SUGGESTIONS_BG = ("gray88", "gray22")
COLOR_CARD_BG_SUGGESTION = ("gray80", "gray28")
BTN_HEIGHT_PILL = 26
COLOR_MAGENTA_HOVER = "darkmagenta"
COLOR_CARD_ALT_BG = ("gray90", "gray20")
BTN_WIDTH_GENERATE_AI = 180
TEXTBOX_HEIGHT_EMAIL_BODY = 210
COLOR_OUTLOOK_BLUE = "royalblue"
COLOR_OUTLOOK_HOVER = "blue"
COLOR_BTN_CANCEL = ("gray70", "gray40")
COLOR_BTN_CANCEL_HOVER = ("gray60", "gray50")
BTN_WIDTH_CANCEL = 90
COLOR_OVERLAY_BG = ("gray95", "gray15")
OVERLAY_CARD_WIDTH = 380
OVERLAY_CARD_HEIGHT = 120
PROGRESS_BAR_WIDTH_MD = 280
COLOR_PROGRESS_INDETERMINATE = "#6366f1"
COLOR_SUCCESS_ALT = "forestgreen"
COLOR_DANGER_ALT = "firebrick"
COLOR_WARNING_ALT = "darkorange"
DEBOUNCE_KEY_RECIPIENT_SEARCH = "recipient_search"

# Customer Management Dialog Design Tokens
DIALOG_MIN_SIZE_CUSTOMER_MGMT = (900, 600)
COLOR_PURPLE_HOVER = "purple"
BTN_WIDTH_COBRA_IMPORT = 165
CUSTOMER_LIST_PANEL_WIDTH = 300
COMBO_WIDTH_SORT = 170
BTN_WIDTH_SORT_DIR = 85
COLOR_CARD_BG_ALT = ("gray85", "gray20")
HEIGHT_SAVE_BAR = 48
ENTRY_WIDTH_SALUTATION_COL = 100
ENTRY_WIDTH_SALUTATION = 95
ENTRY_WIDTH_ZIP_COL = 90
ENTRY_WIDTH_ZIP = 80
BTN_WIDTH_OPEN_WEB = 75
ENTRY_WIDTH_VM_COL = 95
ENTRY_WIDTH_VM = 85
ENTRY_WIDTH_DSC_COL = 100
ENTRY_WIDTH_DSC = 90
TEXTBOX_HEIGHT_RULES = 65
COLOR_LABEL_GRAY60 = "gray60"
COLOR_BTN_GRAY_40 = "gray40"
DEBOUNCE_KEY_CUSTOMER_SEARCH = "customer_search"

# Colleague Management Dialog Design Tokens
DIALOG_MIN_SIZE_COLLEAGUE_MGMT = (900, 600)
HEIGHT_TOP_BAR_SM = 45
FONT_SIZE_HEADER_BAR = 16
BTN_WIDTH_NEW_COLLEAGUE = 180
COLLEAGUE_LIST_PANEL_WIDTH = 320
COLOR_COLLEAGUE_ACTIVE = ("gray75", "gray35")
COLOR_COLLEAGUE_INACTIVE = ("gray85", "gray20")
COLLEAGUE_NOTES_SNIPPET_MAX_CHARS = 45
DEBOUNCE_KEY_COLLEAGUE_SEARCH = "colleague_search"
COLOR_DARKRED_HOVER = "darkred"
COLOR_DARKGREEN_HOVER = "darkgreen"
# Base Dialog Design Tokens
MAX_I18N_WIDGETS_REGISTRY = 400

# Storage Service Tokens & File Constants
LOG_MAX_BYTES = 5_000_000
LOG_BACKUP_COUNT = 3
JSON_INDENT = 2
DEBOUNCE_DELAY_STORAGE_SAVE = 0.15
TIMEOUT_STORAGE_WRITE_COND = 0.5
DEFAULT_AUTO_ARCHIVE_THRESHOLD_DAYS = 30
DAYS_PER_WEEK = 7
DAYS_PER_MONTH = 30
REGEX_CASES_BACKUP = r"^cases_(\d{4}-\d{2}-\d{2})\.json$"

# Instance Service & Protocol Handler Constants
URI_SCHEME = "supportcockpit"
LOCK_FILENAME = "instance.lock"
REQUEST_FILENAME = "open_case_request.json"
HEARTBEAT_INTERVAL_SECONDS = 30
LOCK_STALE_SECONDS = 150
REQUEST_MAX_AGE_SECONDS = 120
PROTOCOL_HANDLER_DESCRIPTION = "URL:Support-Cockpit Protocol"

# Configuration & System File Identifiers
ENV_SUPPORTCOCKPIT_CONFIG_DIR = "SUPPORTCOCKPIT_CONFIG_DIR"
USER_CONFIG_FILENAME = "user_config.json"
DEFAULT_FROZEN_WORKSPACE_NAME = "SupportCockpitData"
CASES_FILENAME = "cases.json"
ARCHIVE_FILENAME = "archive.json"
CUSTOMERS_FILENAME = "customers.json"
APP_PROFILE_FILENAME = "app_profile.json"
COLLEAGUES_FILENAME = "colleagues.json"
QUESTION_SCHEMAS_FILENAME = "question_schemas.json"
EXPORT_TEMPLATES_FILENAME = "export_templates.json"
WIKI_DB_FILENAME = "wiki_index.sqlite"
APP_LOG_FILENAME = "app.log"
ATTACHMENTS_DIRNAME = "attachments"
BACKUPS_DIRNAME = "backups"
COLLEAGUES_DIRNAME = "colleagues"
DATA_DIRNAME = "data"
DATA_EXAMPLES_DIRNAME = "data_examples"

# AI Settings Tab Tokens
COLOR_PANEL_MUTED_BG = ("gray90", "gray25")
COLOR_BTN_GRAY30 = "gray30"
BTN_WIDTH_ICON_SM = 35
BTN_WIDTH_DOWNLOAD_MODEL = 260
BTN_WIDTH_START_OLLAMA = 200
ENTRY_WIDTH_GEMINI_KEY = 280
COMBO_WIDTH_GEMINI_MODEL = 200
BTN_WIDTH_SCAN_OLLAMA = 180
BTN_WIDTH_DOWNLOAD_OLLAMA = 360
COMBO_WIDTH_OLLAMA_MODEL = 220
ENTRY_WIDTH_OLLAMA_MODEL = 160
BTN_WIDTH_CREATE_PVS = 260
BTN_WIDTH_PRELOAD = 160
ENTRY_WIDTH_OLLAMA_URL = 200
DELAY_OLLAMA_STATUS_SCAN_MS = 1500
MODELFILE_SYSTEM_RULES_MARKER = "--- MODELFILE SYSTEM-REGELN ---"
MODELFILE_SYSTEM_PREFIX = 'SYSTEM """'
MODELFILE_SYSTEM_SUFFIX = '"""'
PASSWORD_CHAR_MASK = "*"
PASSWORD_CHAR_SHOW = ""
ICON_PASSWORD_SHOW = "👁"
ICON_PASSWORD_HIDE = "🔒"
ICON_STATUS_SUCCESS = "✅"
ICON_STATUS_ERROR = "❌"
ICON_STATUS_WARNING = "⚠"
ICON_STATUS_FLASH = "⚡"

# Tooltip & Window Event Tokens
BORDER_WIDTH_TOOLTIP = 1
WINDOW_ATTR_TOPMOST = "-topmost"
ANCHOR_WEST = "w"
JUSTIFY_LEFT = "left"
EVENT_ENTER = "<Enter>"
EVENT_LEAVE = "<Leave>"
EVENT_FOCUS_OUT = "<FocusOut>"
EVENT_UNMAP = "<Unmap>"
EVENT_BUTTON_1 = "<Button-1>"
EVENT_BUTTON_2 = "<Button-2>"
EVENT_BUTTON_3 = "<Button-3>"
EVENT_BUTTON_RELEASE_1 = "<ButtonRelease-1>"
EVENT_DESTROY = "<Destroy>"
EVENT_BUTTON_PRESS = "<ButtonPress>"

# Template Manager Dialog Design Tokens
DIALOG_MIN_SIZE_EDIT_TEMPLATE = (700, 600)
DIALOG_MIN_SIZE_TEMPLATE_MGMT = (880, 640)
LABEL_WIDTH_TEMPLATE_FIELD = 130
TEXTBOX_HEIGHT_TEMPLATE = 160
TEXTBOX_HEIGHT_PREVIEW = 120
HEIGHT_TOP_BAR = 50
HEIGHT_BOTTOM_BAR = 50
BTN_WIDTH_TOGGLE_DEFAULTS = 210
BTN_WIDTH_ADOPT = 170
FONT_FAMILY_MONO = "Consolas"
COLOR_BTN_TOGGLE_DEFAULTS = ("gray75", "gray30")
COLOR_BTN_TOGGLE_DEFAULTS_HOVER = ("gray65", "gray40")

# Snippet Management Dialog Design Tokens
DIALOG_MIN_SIZE_SNIPPET_MGMT = (720, 500)
SNIPPET_LIST_MIN_WIDTH = 320
SNIPPET_FORM_MIN_WIDTH = 380
TEXTBOX_HEIGHT_SNIPPET_CONTENT = 180
COLOR_BTN_GRAY45 = "gray45"
COLOR_DEEPSKYBLUE_HOVER = "deepskyblue"
COLOR_SNIPPET_CARD_ACTIVE = ("gray80", "gray25")
COLOR_SNIPPET_CARD_INACTIVE = ("gray90", "gray15")
COLOR_LABEL_GRAY70 = "gray70"

# Schema Builder Dialog Design Tokens
DIALOG_MIN_SIZE_SCHEMA_BUILDER = (1080, 640)
COMBO_WIDTH_SCHEMA_SELECT = 260
BTN_WIDTH_NEW_SCHEMA = 125
BTN_WIDTH_ADOPT_SCHEMA = 190
BTN_WIDTH_TOGGLE_SCHEMAS = 220
BTN_WIDTH_DELETE_SCHEMA = 85
BTN_WIDTH_ARROW = 30
BTN_WIDTH_TOGGLE_REQUIRED = 80
CHECKBOX_WIDTH_REQUIRED = 65
ENTRY_WIDTH_FIELD_ID = 160
ENTRY_WIDTH_LABEL = 180
COMBO_WIDTH_FIELD_TYPE = 110
ENTRY_WIDTH_CONDITIONAL = 140
ENTRY_WIDTH_EXTS = 140
SCROLL_WIDTH_SCHEMA_FIELDS = 680
SCROLL_HEIGHT_SCHEMA_FIELDS = 300
BORDER_WIDTH_PANEL = 1
SCHEMA_ID_PREFIX = "schema_"
ICON_DELETE_X = "✕"

# New Case Dialog Design Tokens
DIALOG_MIN_SIZE_NEW_CASE = (700, 780)
TEXTBOX_HEIGHT_INITIAL_NOTE = 65
TAG_PILL_COLS = 4
TAG_PILL_HEIGHT = 28
TAG_PILL_RADIUS = 14
TAG_PILL_PAD_X = 3
TAG_PILL_PAD_Y = 2
COLOR_TAG_PILL_SELECTED = ("#2563eb", "#1d4ed8")
COLOR_TAG_PILL_SELECTED_HOVER = ("#1d4ed8", "#1e40af")
COLOR_TAG_PILL_DEFAULT = ("gray85", "gray28")
COLOR_TAG_PILL_DEFAULT_HOVER = ("gray75", "gray38")
COLOR_TAG_PILL_DEFAULT_TEXT = ("gray20", "gray85")
COLOR_TAG_PILL_ADD_BG = ("gray75", "gray35")
COLOR_TAG_PILL_ADD_HOVER = ("gray65", "gray45")
CASE_ID_PREFIX = "T-"
INTERNAL_CUSTOMER_ID = "INTERNAL"
INTERNAL_PRACTICE_NAME = "Intern / Keine Praxis"
INTERNAL_ATTACHMENT_SUFFIX = "_Intern"
DEFAULT_IDLE_WARNING_DAYS = 1
TIMESTAMP_FORMAT_CASE_ID = "%M%S"
INITIAL_STATUS_CHANGE_NOTE = "NEW -> ACTION_REQUIRED (SUPPORT)"
DEFAULT_PRACTICE_DISPLAY = "Standard Praxis (K-10000)"
DEFAULT_PRACTICE_ID = "K-10000"
DEFAULT_PRACTICE_NAME = "Standard Praxis"
COMBO_WIDTH_NEW_CASE_CHANNEL = 175

# Followup Dialog Design Tokens
DIALOG_SIZE_FOLLOWUP = (500, 385)
DIALOG_MIN_SIZE_FOLLOWUP = (460, 350)
HEIGHT_TOP_BAR_FOLLOWUP = 40
FOLLOWUP_PRESET_COLS = 4
FOLLOWUP_PRESET_UNIFORM = "fw_presets"
BTN_HEIGHT_PRESET = 28
CORNER_RADIUS_PRESET = 12
COLOR_PRESET_BTN = ("gray75", "gray30")
COLOR_PRESET_BTN_HOVER = ("gray65", "gray40")
COLOR_TRANSPARENT = "transparent"
COLOR_DARKRED = "darkred"
DATE_PICKER_WIDTH_FOLLOWUP = 260
BTN_WIDTH_SAVE_FOLLOWUP = 180
BTN_WIDTH_CLEAR_FOLLOWUP = 100
BTN_WIDTH_CANCEL_FOLLOWUP = 85
BTN_HEIGHT_ACTION = 30
FOLLOWUP_DEFAULT_TIME = "09:00"
FOLLOWUP_TIME_1630 = "16:30"
FOLLOWUP_TIME_1130 = "11:30"
FOLLOWUP_TIME_1330 = "13:30"
FOLLOWUP_TIME_0800 = "08:00"
FOLLOWUP_DEFAULT_DAYS_AHEAD = 2
FOLLOWUP_PRESET_HOURS_1 = 1
FOLLOWUP_PRESET_HOURS_2 = 2
FOLLOWUP_PRESET_DAYS_1 = 1
FOLLOWUP_PRESET_DAYS_2 = 2
FOLLOWUP_PRESET_DAYS_3 = 3
FOLLOWUP_PRESET_DAYS_7 = 7
FOLLOWUP_DELAY_DESTROY_MS = 1
ENTRY_START_INDEX = 0

# Tray Service Design Tokens
APP_ID_NOTIFICATION = "Support-Cockpit"
NOTIFICATION_DURATION_SHORT = "short"
TRAY_ICON_SIZE = 64
TRAY_BADGE_RADIUS = 12
TRAY_BG_COLOR = (38, 130, 130, 255)
TRAY_CROSS_COLOR = (255, 255, 255, 255)
TRAY_BADGE_COLOR = (220, 38, 38, 255)
TRAY_BADGE_MAX_COUNT = 99
TRAY_BADGE_OVERFLOW_TEXT = "99+"
TRAY_BADGE_FONT_NAME = "arial.ttf"
TRAY_BADGE_FONT_SIZE_SM = 10
TRAY_BADGE_FONT_SIZE_LG = 13
TRAY_IMAGE_MODE = "RGBA"
TRAY_TRANSPARENT_PIXEL = (0, 0, 0, 0)
TRAY_BASE_RECT = [4, 4, 60, 60]
TRAY_BASE_RADIUS = 12
TRAY_CROSS_VBAR = [26, 14, 38, 50]
TRAY_CROSS_HBAR = [14, 26, 50, 38]
TRAY_BADGE_OFFSET = 2

# Followup Flyout Dialog Design Tokens
FLYOUT_TITLE_WRAPLENGTH = 520
COLOR_WARNING_TEXT = "darkorange"
COLOR_NOTE_TEXT = ("gray30", "gray70")
DATE_PICKER_WIDTH_FLYOUT = 150
BTN_WIDTH_PRESET_110 = 110
BTN_WIDTH_PRESET_105 = 105
FLYOUT_TITLE_MAX_LINE_LENGTH = 55
FLYOUT_TITLE_MAX_LINES = 2

# Attachment Widget Design Tokens
ICON_IMAGE = "🖼"
ICON_DELETE_TRASH = "🗑"
SHORTCUT_PASTE = "<Control-v>"
TEXT_START_INDEX = "1.0"
COLOR_FIREBRICK_HOVER = "firebrick"
COLOR_PANEL_PREVIEW_BG = ("gray90", "gray15")
COLOR_TIP_TEXT = ("gray40", "gray70")
SCROLL_HEIGHT_ATTACHMENTS = 130
TEXTBOX_HEIGHT_FILE_PREVIEW = 90
PREVIEW_TEXT_MAX_CHARS = 500
TEXT_PREVIEW_EXTENSIONS = {".txt", ".log", ".json", ".csv", ".md", ".py"}
BTN_WIDTH_ADD_FILE = 150
BTN_WIDTH_OPEN_EXPLORER = 120
BTN_WIDTH_ICON_DELETE = 30
CMD_XDG_OPEN = "xdg-open"
STATE_DISABLED = "disabled"
STATE_NORMAL = "normal"

# Search Service Tokens
SEARCH_CACHE_MAXSIZE = 256
SEARCH_TOKEN_SEPARATOR = ":"
TRUTHY_SEARCH_VALUES = ("true", "1", "yes", "ja")
FALSY_SEARCH_VALUES = ("false", "nein", "none")
REMINDER_SET_VALUES = ("true", "set", "ja", "due")
SEARCH_KEY_VIP = "vip"
SEARCH_KEYS_TYPE = ("is", "type")
SEARCH_VALUES_INTERNAL = ("internal", "intern")
SEARCH_VALUES_CUSTOMER = ("customer", "kunde", "praxis")
SEARCH_KEY_INTERNAL = "internal"
SEARCH_KEY_ACTOR = "actor"
SEARCH_KEY_STATUS = "status"
SEARCH_KEY_ERROR = "error"
SEARCH_KEY_DEADLINE = "deadline"
SEARCH_KEYS_TAG = ("tag", "tags")
SEARCH_KEYS_REMINDER = ("reminder", "followup", "wiedervorlage")
STATUS_SEARCH_OPEN = "open"
STATUS_SEARCH_DONE = "done"
STATUS_SEARCH_ARCHIVED = "archived"
DEADLINE_SEARCH_OVERDUE = "overdue"
DEADLINE_SEARCH_NEAR = ("<2h", "2h")
REMINDER_SEARCH_DUE = "due"
ACTOR_ALIAS_DEV = "dev"
ACTOR_DEV_FULL = "development"
FIELD_ERROR_CODE = "error_code"
DEADLINE_WARNING_HOURS = 2.0


# ============================================================================
# Design Tokens – Ergänzungen aus dem Konstanten-Refactoring (Abschluss)
# ============================================================================

# --- Design Tokens: Typography & Spacing (Ergänzungen) ---
FONT_SIZE_2XS = 8
FONT_SIZE_H2 = 18
PAD_3 = 3
PAD_4XL = 40
LABEL_HEIGHT_SM = 13
LABEL_HEIGHT_MD = 15
BTN_WIDTH_APPLY = 120
BTN_WIDTH_BROWSE = 130
BTN_WIDTH_CLOSE_SM = 100
COLOR_BTN_NEUTRAL = "gray"
COLOR_BADGE_MUTED = "gray30"
COLOR_CARD_BG_SUBTLE = ("gray85", "gray22")
COLOR_WARNING_NOTE = ("darkgoldenrod", "gold")

# --- Date Picker / Calendar Dialog Tokens ---
DATE_PICKER_DIALOG_WIDTH = 390
DATE_PICKER_DIALOG_HEIGHT = 440
DATE_PICKER_DIALOG_HEIGHT_DATE_ONLY = 350
DATE_PICKER_WIDTH_DEFAULT = 240
DATE_PICKER_NAV_BTN_WIDTH = 32
DATE_PICKER_NAV_BTN_HEIGHT = 26
DATE_PICKER_DAY_CELL_WIDTH = 48
DATE_PICKER_DAY_CELL_HEIGHT = 26
DATE_PICKER_STEPPER_BTN_WIDTH = 52
DATE_PICKER_STEPPER_BTN_HEIGHT = 13
DATE_PICKER_TIME_MENU_WIDTH = 54
DATE_PICKER_TIME_MENU_HEIGHT = 22
DATE_PICKER_TIME_MENU_CORNER_RADIUS = 3
DATE_PICKER_PRESET_BTN_HEIGHT = 25
COLOR_DATE_PICKER_STEPPER_BG = ("gray80", "gray25")
COLOR_DATE_PICKER_STEPPER_BORDER = ("gray70", "gray35")
COLOR_DATE_PICKER_STEPPER_TEXT = ("gray20", "gray90")
COLOR_DATE_PICKER_TIME_MENU = ("dodgerblue", "#1f538d")
COLOR_DATE_PICKER_TODAY_BG = ("gray80", "gray25")
COLOR_DATE_PICKER_DAY_HOVER = "royalblue"
COLOR_DATE_PICKER_DAY_TEXT = ("gray10", "#DCE4EE")

# --- AI Assistant Dialog Tokens ---
DIALOG_MIN_SIZE_AI_ASSISTANT = (720, 480)
BTN_WIDTH_AI_REGENERATE = 210
BTN_WIDTH_AI_ACTION = 190
OVERLAY_CARD_HEIGHT_LG = 140

# --- AI Service Request Timeouts (Ergänzungen) ---
OLLAMA_TIMEOUT_PRELOAD = 60.0
OLLAMA_TIMEOUT_UNLOAD = 10.0
GEMINI_TIMEOUT_STATUS = 5.0
GEMINI_TIMEOUT_GENERATE = 30.0

# --- Analytics View Tokens ---
ANALYTICS_CARD_WIDTH = 130
BTN_WIDTH_COPY_REPORT = 190

# --- Cockpit Toolbar Tokens ---
BTN_WIDTH_EMAIL_AI = 130
COMBO_WIDTH_ACTOR = 105
COMBO_WIDTH_MORE_ACTIONS = 165

# --- Table View Tokens ---
HEIGHT_TABLE_DETAIL_HEADER = 38
BTN_WIDTH_SAVE_TABLE = 150

# --- ZIP Import Dialog Tokens ---
DIALOG_MIN_SIZE_ZIP_IMPORT = (760, 540)
BTN_WIDTH_ZIP_MODE = 230
ENTRY_WIDTH_IMPORT_PATH = 480
ZIP_IMPORT_WARN_WRAPLENGTH = 680

# --- E-Mail Import Dialog Tokens ---
DIALOG_MIN_SIZE_EMAIL_IMPORT = (750, 500)
BTN_WIDTH_REFRESH_INBOX = 170
EMAIL_IMPORT_MAX_FETCH_COUNT = 15
EMAIL_RECEIVED_TIME_PREVIEW_LEN = 16
EMAIL_BODY_PREVIEW_LEN = 180
COLOR_EMAIL_SUBJECT_FG = ("gray20", "gray90")

# --- Wiki Sync Service Tokens ---
WIKI_API_TIMEOUT_SECONDS = 10
WIKI_SEARCH_SNIPPET_MAX_CHARS = 120
WIKI_PAGE_SNIPPET_MAX_CHARS = 150

# --- Cobra CRM Import Dialog Tokens ---
#: Key/default pairs for the conflict-mode menu, and the stable mode keys the
#: import service expects - same order, so the selected position maps straight
#: onto a key without ever comparing translated label text.
COBRA_CONFLICT_MODE_CHOICES = [
    ("cobra_import.mode_update", "Bestehende Praxen aktualisieren (Update)"),
    ("cobra_import.mode_skip", "Bestehende überspringen (Skip)"),
    ("cobra_import.mode_all_new", "Alle als neu anlegen"),
]
COBRA_CONFLICT_MODE_KEYS = ("update", "skip", "all_new")
DIALOG_MIN_SIZE_COBRA_IMPORT = (760, 540)
COMBO_WIDTH_CONFLICT_MODE = 320
COMBO_WIDTH_COBRA_MAPPING = 240
LABEL_WIDTH_COBRA_FIELD = 160
LABEL_WIDTH_IMPORT_BADGE = 80
COLOR_IMPORT_NEW = "limegreen"

# --- E-Mail & Calendar Dialog Tokens ---
DIALOG_MIN_SIZE_EMAIL_CALENDAR = (720, 540)
TEXTBOX_HEIGHT_EMAIL_CALENDAR_BODY = 200
COLOR_STATUS_SUCCESS_TEXT = "lightgreen"

# --- Export Dialog Tokens ---
TEXTBOX_WIDTH_EXPORT_PREVIEW = 640
TEXTBOX_HEIGHT_EXPORT_PREVIEW = 200

# --- Calendar Export Dialog Tokens ---
DIALOG_MIN_SIZE_CALENDAR_EXPORT = (580, 440)
TEXTBOX_HEIGHT_CALENDAR_DESC = 140

# --- P2P Diff Dialog Tokens ---
DIALOG_MIN_SIZE_P2P_DIFF = (820, 620)
BTN_WIDTH_RELOAD_COMPARE = 180
CHECKBOX_WIDTH_P2P_SELECT = 30
LABEL_WIDTH_STATUS_BADGE = 130
SCROLL_WIDTH_P2P_DIFF = 780
SCROLL_HEIGHT_P2P_DIFF = 440

# --- Convert Schema Dialog Tokens ---
BTN_WIDTH_CONVERT_SCHEMA = 160
CONVERT_NOTICE_WRAPLENGTH = 460
COLOR_NOTICE_INFO_BG = ("lightblue", "#1e293b")

# --- Profile Settings Tokens (Ergänzungen) ---
PROFILE_DESC_WRAPLENGTH = 420
PROFILE_CARD_DESC_WRAPLENGTH = 400
TEXTBOX_HEIGHT_SIGNATURE = 52
USER_COLOR_PRESET_TILE_SIZE = 22
USER_COLOR_PREVIEW_TILE_SIZE = 16
BORDER_WIDTH_COLOR_SELECTED = 2
COLOR_SIGNATURE_BORDER = ("gray65", "gray35")
COLOR_SIGNATURE_BG = ("#F8F9FA", "gray17")
COLOR_PRESET_BORDER_SELECTED = "#ffffff"
