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
OLLAMA_TIMEOUT_STATUS = 1.5
OLLAMA_TIMEOUT_GENERATE = 8.0
AI_USER_AGENT = "SupportCockpit/1.0"

AI_SYSTEM_ROLE_DEFAULT = "Du bist ein hochqualifizierter IT-Support-Assistent für Arztpraxis-Software im deutschen Gesundheitswesen."
AI_SYSTEM_ROLE_EMAIL = "Du bist ein freundlicher IT-Support-Mitarbeiter im deutschen Gesundheitswesen."

AI_PROMPT_BASE_RULES_HEADER = "--- GLOBALE BASIS-REGELN ---"
AI_PROMPT_PRACTICE_RULES_HEADER = "--- PRAXIS-SPEZIFISCHE REGELN (VORRANGIG UND BINDEND!) ---"
AI_PROMPT_OVERRIDE_NOTICE = "WICHTIGER HINWEIS: Die folgenden Praxis-Regeln haben IMMER Vorrang vor den globalen Basis-Regeln! Falls eine Praxis-Regel einer Basis-Regel widerspricht, musst du dich ZWINGEND an die Praxis-Regel halten:"

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

# --- Date & Time Formats ---
GERMAN_DATE_FORMAT = "%d.%m.%Y"
GERMAN_DATETIME_FORMAT = "%d.%m.%Y %H:%M"
ISO_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
