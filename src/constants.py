"""Centralized application constants, design tokens, layout dimensions, default datasets, and system strings."""

from pathlib import Path

# --- App Metadata & Titles ---
APP_NAME = "SupportCockpit"
APP_TITLE = "🩺 Support-Cockpit"
APP_WINDOW_TITLE = "Support-Cockpit & Ticket Management"
APP_MIN_WIDTH = 900
APP_MIN_HEIGHT = 650

# --- Enum Display Names & Labels ---
DISPLAY_CHANNEL_NAMES = {
    "PHONE_INBOUND": "Telefon (Eingang)",
    "PHONE_OUTBOUND": "Telefon (Ausgang)",
    "EMAIL_IN": "E-Mail (Eingang)",
    "EMAIL_OUT": "E-Mail (Eingang)",
    "GITLAB_TICKET_CREATED": "GitLab-Ticket erstellt",
    "GITLAB_TICKET_UPDATED": "GitLab-Ticket geupdated",
    "GITLAB_TICKET_CLOSED": "GitLab-Ticket geschlossen",
    "INTERNAL_NOTE": "Interne Notiz",
    "OTHER": "Sonstiges"
}

DISPLAY_ACTOR_NAMES = {
    "SUPPORT": "Support / Hotline",
    "HOTLINE": "Hotline",
    "DEVELOPMENT": "Entwicklung",
    "TECH": "Technik",
    "CUSTOMER": "Kunde",
    "DATA_SUPPORT": "Data-AL Support / Hotline",
    "DATA_HOTLINE": "Data-AL Hotline",
    "DATA_DEVELOPMENT": "Data-AL Entwicklung",
    "DATA_TECH": "Data-AL Technik",
    "DATA_CUSTOMER": "Data-AL Kunde",
}

DISPLAY_LAYOUT_NAMES = {
    "COCKPIT": "Cockpit (Hauptansicht)",
    "BOARD": "Kanban-Board (Zuständigkeiten)",
    "TABLE": "Tabelle & Details (Sortier-Matrix)",
}

DISPLAY_BOARD_COLUMN_NAMES = {
    "NEW": "Neu",
    "ACTION_REQUIRED": "Aktion erforderlich",
    "WAITING": "Warten auf zuständige Stelle",
    "IN_PROGRESS": "In Bearbeitung",
    "DONE": "Erledigt",
}

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
}

# --- Sub-Header Labels inside Dialogs ---
DIALOG_HEADERS = {
    "email_import_hub": "📥 E-Mail Import Hub & Auto-Matching",
}

# --- Dropdown Menu & Navigation Option Lists ---
MENU_OPTIONS_STAMMDATEN = ["🏥 Praxen", "🐍 Cobra CRM Import", "👥 Mitarbeiter", "🏷 Tags", "🧩 Programmbereiche", "📝 Textbausteine"]
MENU_OPTIONS_VORLAGEN = ["🛠 Formulare", "📄 Vorlagen"]
MENU_OPTIONS_DATENAUSTAUSCH = ["📥 E-Mail Import", "📤 Export (Strg+E)", "📦 ZIP-Backup", "🔄 P2P-Sync", "📖 Hilfe (F1)"]

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
    "regenerate_summary": "🔄 Zusammenfassung neu generieren",
    "copy_clipboard": "📋 In Zwischenablage kopieren",
    "insert_timeline": "📌 In Fall-Zeitleiste einfügen",
    "rerun_solutions": "🔄 Lösungssuche erneut ausführen",
    "generate_draft": "🔄 Antwort-Entwurf generieren",
    "open_email_draft": "✉ In E-Mail-Entwurf öffnen",
}

# --- Status & Feedback Messages ---
STATUS_MESSAGES = {
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
}

# --- Validation Error Messages ---
VALIDATION_MESSAGES = {
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
    "convert_schema": (520, 400),
    "followup_flyout": (680, 560),
    "handover": (580, 520),
    "zip_import": (840, 620),
    "snippet_mgmt": (820, 600),
    "snippet_picker": (640, 480),
    "email_draft": (760, 640),
    "calendar_export": (640, 520),
    "help": (1080, 720),
    "cobra_import": (860, 680),
    "export": (820, 760),
    "p2p_diff": (920, 720),
    "email_calendar": (760, 660),
    "ai_assistant": (820, 580),
    "email_import": (850, 600),
}

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
AI_STATUS_CHECKING = "🔍 Prüfe Ollama-Status im Hintergrund..."
AI_STATUS_UNLOADING = "⏳ Deaktiviere KI global & entlade Modelle aus Arbeitsspeicher..."
AI_STATUS_UNLOADED = "⚡ KI global deaktiviert & Modelle aus Arbeitsspeicher entladen."
AI_STATUS_ACTIVATED = "✅ KI global aktiviert."
AI_STATUS_STARTING = "⏳ Versuche Ollama Server im Hintergrund zu starten..."
AI_STATUS_STOPPING = "⏳ Beende Ollama Server-Prozess..."

AI_NO_MODELS_TITLE = "⚠ Keine KI-Modelle in Ollama installiert!"
AI_NO_MODELS_DESC = "Bitte laden Sie ein Modell wie qwen2.5:7b oder llama3 über die Ollama-Bibliothek herunter:"

AI_BADGE_ACTIVE = "🟢 Ollama Local LLM aktiv ({model})"
AI_BADGE_STANDBY = "🔵 Ollama Standby ({model})"
AI_BADGE_DISABLED = "⚪ KI global deaktiviert (Schalter OFF)"
AI_BADGE_NLP_FALLBACK = "⚡ Regelbasierter NLP-Modus (Ollama offline)"

# --- AI Button Labels & UI Action Texts ---
AI_BTN_GENERATE_DRAFT = "🤖 KI-Entwurf generieren"
AI_BTN_GENERATE_DRAFT_DISABLED = "🤖 KI-Entwurf (KI global inaktiv)"
AI_BTN_GLOBAL_TOGGLE = "🤖 KI- & NLP-Unterstützung global aktivieren"
AI_BTN_GLOBAL_TOGGLE_HEADER = "🤖 KI Global Aktiv"
AI_BTN_START_SERVER = "▶ Ollama Server Starten"
AI_BTN_STOP_SERVER = "🛑 Server Beenden"
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
COLOR_PRIMARY = "#2563eb"
COLOR_PRIMARY_HOVER = "#1d4ed8"
COLOR_AI_PURPLE = "#6366f1"
COLOR_AI_PURPLE_HOVER = "#4f46e5"
COLOR_BADGE_GREEN = "forestgreen"
COLOR_BADGE_BLUE = "dodgerblue"
COLOR_BADGE_GRAY = "gray"
COLOR_SUCCESS = "forestgreen"
COLOR_SUCCESS_HOVER = "darkgreen"
COLOR_CANCEL = ("gray70", "gray40")
COLOR_CANCEL_HOVER = ("gray60", "gray50")
COLOR_DANGER = "crimson"
COLOR_DANGER_HOVER = "darkred"
COLOR_MUTED_GRAY = ("gray75", "gray30")
COLOR_MUTED_HOVER = ("gray65", "gray40")
COLOR_SASH_DARK = "#2b2b2b"
COLOR_SASH_LIGHT = "#d0d0d0"

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
COLOR_TEXT_BLUE = "dodgerblue"
COLOR_PURPLE_DARK = "darkviolet"
COLOR_PRIMARY_BLUE = "dodgerblue"
COLOR_BTN_GRAY = "gray40"
COLOR_MUTED_LABEL = ("gray40", "gray70")
COLOR_MUTED_DISABLED = ("gray50", "gray70")
COLOR_MUTED_BODY = ("gray30", "gray80")

COLOR_TOOLTIP_BG = ("gray20", "gray10")
COLOR_TOOLTIP_BORDER = ("gray60", "gray40")
COLOR_TOOLTIP_TEXT = ("gray95", "gray95")

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
    "Datenbank"
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

DEFAULT_SNIPPET_CATEGORY = "Allgemein"

# --- Cobra CRM Field Aliases ---
COBRA_FIELD_ALIAS_MAP = {
    "customer_id": ["kunden_nr", "kundennr", "kunden-nr", "id", "kdnr", "kunden_id", "customer_id", "kunden nummer", "debitor"],
    "practice_name": ["firma", "praxis", "praxisname", "name1", "name", "firmenname", "practice_name", "organisation", "unternehmen"],
    "contact_person": ["ansprechpartner", "ansprechpartnerin", "kontakt", "name2", "contact_person", "kontaktperson", "arzt", "ärztin"],
    "phone": ["telefon", "tel", "telefonnummer", "tel.nr", "fon", "phone", "mobil", "telefon_nr"],
    "email": ["email", "e-mail", "mail", "elektronische post", "e_mail"],
    "is_vip": ["vip", "wichtig", "priorität", "vip_kunde", "is_vip", "prio"],
    "system_version": ["version", "system", "systemversion", "pvs-version", "pvs_version", "release"],
    "vm_number": ["vm", "vm_nr", "vm-nr", "vm_nummer", "vm_number"],
    "instance_number": ["instanz", "instanz_nr", "mandant", "instance_number", "instanz_nummer"],
    "general_notes": ["notizen", "bemerkung", "kommentar", "hinweis", "general_notes", "memo", "beschreibung"],
}

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
    "toggle_theme": "<Control-t>",
}

HOTKEY_ACTION_LABELS = [
    ("new_case", "Neuer Fall:"),
    ("save_case", "Fall speichern:"),
    ("archive_case", "Fall archivieren:"),
    ("export_dialog", "Export Dialog:"),
    ("open_settings", "Einstellungen öffnen:"),
    ("snippet_picker", "Snippet-Picker öffnen:"),
    ("wiki_search", "Wiki-Suche fokussieren:"),
    ("search_customer", "Kundensuche fokussieren:"),
    ("view_cockpit", "Cockpit-Ansicht:"),
    ("view_board", "Board-Ansicht:"),
    ("view_table", "Tabelle-Ansicht:"),
    ("toggle_theme", "Theme umschalten:"),
]

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

