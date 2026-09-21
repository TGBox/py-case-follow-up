from enum import StrEnum

from constants import (
    ACTOR_KEY_MAP,
    CHANNEL_KEY_MAP,
    DISPLAY_ACTOR_NAMES,
    DISPLAY_BOARD_COLUMN_NAMES,
    DISPLAY_CHANNEL_NAMES,
    DISPLAY_LAYOUT_NAMES,
    DISPLAY_SORT_CRITERION_NAMES,
    DISPLAY_THEME_NAMES,
    LAYOUT_KEY_MAP,
    LEGACY_ACTOR_MAP,
    SORT_CRITERION_KEY_MAP,
    THEME_KEY_MAP,
)


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


CHANNEL_DISPLAY = DISPLAY_CHANNEL_NAMES
ACTOR_DISPLAY = DISPLAY_ACTOR_NAMES
LAYOUT_DISPLAY = DISPLAY_LAYOUT_NAMES
BOARD_COLUMN_DISPLAY = DISPLAY_BOARD_COLUMN_NAMES
THEME_DISPLAY = DISPLAY_THEME_NAMES


def get_channel_display(val: str) -> str:
    from services.i18n_service import tr
    default = CHANNEL_DISPLAY.get(val, val)
    return tr(CHANNEL_KEY_MAP.get(val, ""), default=default)


def get_actor_display(val: str) -> str:
    from services.i18n_service import tr
    default = ACTOR_DISPLAY.get(val, val)
    return tr(ACTOR_KEY_MAP.get(val, ""), default=default)


def get_layout_display(val: str) -> str:
    from services.i18n_service import tr
    default = LAYOUT_DISPLAY.get(val, val)
    return tr(LAYOUT_KEY_MAP.get(val, ""), default=default)


def get_board_column_display(val: str) -> str:
    return BOARD_COLUMN_DISPLAY.get(val, val)


def get_theme_display(val: str) -> str:
    from services.i18n_service import tr
    default = THEME_DISPLAY.get(val, val)
    return tr(THEME_KEY_MAP.get(val, ""), default=default)


def get_sort_criterion_display(val: str) -> str:
    from services.i18n_service import tr
    default = DISPLAY_SORT_CRITERION_NAMES.get(val, val)
    return tr(SORT_CRITERION_KEY_MAP.get(val, ""), default=default)


def get_actor_val_from_display(display: str) -> str:
    for k in ACTOR_DISPLAY:
        if get_actor_display(k) == display or ACTOR_DISPLAY[k] == display:
            return k
    disp_lower = display.lower().strip()
    if disp_lower in LEGACY_ACTOR_MAP:
        return LEGACY_ACTOR_MAP[disp_lower]
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
