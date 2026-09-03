from enum import Enum, StrEnum


class UrgencyLevel(StrEnum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"


class BoardColumn(StrEnum):
    NEW = "NEW"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    WAITING = "WAITING"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class Actor(StrEnum):
    SUPPORT = "SUPPORT"
    DEVELOPMENT = "DEVELOPMENT"
    TECH = "TECH"
    CUSTOMER = "CUSTOMER"


class FieldType(StrEnum):
    TEXT = "text"
    DROPDOWN = "dropdown"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    FILE = "file"


class SyncMode(StrEnum):
    METADATA_ONLY = "METADATA_ONLY"
    FULL_OFFLINE = "FULL_OFFLINE"


class TargetType(StrEnum):
    CLIPBOARD_TEXT = "CLIPBOARD_TEXT"
    FILE_EXPORT = "FILE_EXPORT"


class Channel(StrEnum):
    PHONE_INBOUND = "PHONE_INBOUND"
    PHONE_OUTBOUND = "PHONE_OUTBOUND"
    EMAIL = "EMAIL"
    DEV_TICKET = "DEV_TICKET"
    INTERNAL_NOTE = "INTERNAL_NOTE"


class LayoutMode(StrEnum):
    COCKPIT = "COCKPIT"
    BOARD = "BOARD"
    TABLE = "TABLE"
    ANALYTICS = "ANALYTICS"


from constants import (
    DISPLAY_CHANNEL_NAMES,
    DISPLAY_ACTOR_NAMES,
    DISPLAY_LAYOUT_NAMES,
    DISPLAY_BOARD_COLUMN_NAMES,
    DISPLAY_THEME_NAMES,
    DISPLAY_SORT_CRITERION_NAMES,
)

CHANNEL_DISPLAY = DISPLAY_CHANNEL_NAMES
ACTOR_DISPLAY = DISPLAY_ACTOR_NAMES
LAYOUT_DISPLAY = DISPLAY_LAYOUT_NAMES
BOARD_COLUMN_DISPLAY = DISPLAY_BOARD_COLUMN_NAMES
THEME_DISPLAY = DISPLAY_THEME_NAMES
SORT_CRITERION_DISPLAY = DISPLAY_SORT_CRITERION_NAMES


def get_channel_display(val: str) -> str:
    from services.i18n_service import tr
    key_map = {
        "PHONE_INBOUND": "channels.phone",
        "EMAIL": "channels.email",
        "INTERNAL_NOTE": "channels.internal_note",
    }
    default = CHANNEL_DISPLAY.get(val, val)
    return tr(key_map.get(val, ""), default=default)


def get_actor_display(val: str) -> str:
    from services.i18n_service import tr
    key_map = {
        "SUPPORT": "actors.support_team",
        "CUSTOMER": "actors.practice",
        "DEVELOPMENT": "actors.dev",
        "TECH": "actors.third_party",
    }
    default = ACTOR_DISPLAY.get(val, val)
    return tr(key_map.get(val, ""), default=default)


def get_layout_display(val: str) -> str:
    from services.i18n_service import tr
    key_map = {
        "COCKPIT": "layouts.cockpit",
        "BOARD": "layouts.board",
        "TABLE": "layouts.table",
        "ANALYTICS": "layouts.analytics",
    }
    default = LAYOUT_DISPLAY.get(val, val)
    return tr(key_map.get(val, ""), default=default)


def get_board_column_display(val: str) -> str:
    return BOARD_COLUMN_DISPLAY.get(val, val)


def get_theme_display(val: str) -> str:
    """Translates the internal theme mode ("Dark"/"Light"/"System", as passed to
    ctk.set_appearance_mode() and stored in profile.ui_settings.theme) into the
    label shown in the theme dropdown. The stored/internal value never changes."""
    from services.i18n_service import tr
    key_map = {
        "Dark": "theme_modes.dark",
        "Light": "theme_modes.light",
        "System": "theme_modes.system",
    }
    default = THEME_DISPLAY.get(val, val)
    return tr(key_map.get(val, ""), default=default)


def get_sort_criterion_display(val: str) -> str:
    """Translates the internal sort-criterion code ("name"/"id"/"contact") into the
    label shown in the Praxisverwaltung sort dropdown."""
    from services.i18n_service import tr
    key_map = {
        "name": "sort_criteria.name",
        "id": "sort_criteria.id",
        "contact": "sort_criteria.contact",
    }
    default = SORT_CRITERION_DISPLAY.get(val, val)
    return tr(key_map.get(val, ""), default=default)


def get_actor_val_from_display(display: str) -> str:
    for k in ACTOR_DISPLAY:
        if get_actor_display(k) == display or ACTOR_DISPLAY[k] == display:
            return k
    return display


def get_channel_val_from_display(display: str) -> str:
    for k in CHANNEL_DISPLAY:
        if get_channel_display(k) == display or CHANNEL_DISPLAY[k] == display:
            return k
    return display


def get_layout_val_from_display(display: str) -> str:
    for k in LAYOUT_DISPLAY:
        if get_layout_display(k) == display or LAYOUT_DISPLAY[k] == display:
            return k
    return display


def get_theme_val_from_display(display: str) -> str:
    for k in THEME_DISPLAY:
        if get_theme_display(k) == display or THEME_DISPLAY[k] == display:
            return k
    return display


def get_sort_criterion_val_from_display(display: str) -> str:
    for k in SORT_CRITERION_DISPLAY:
        if get_sort_criterion_display(k) == display or SORT_CRITERION_DISPLAY[k] == display:
            return k
    return display
