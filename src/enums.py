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


CHANNEL_DISPLAY = {
    Channel.PHONE_INBOUND.value: "Telefon (Eingang)",
    Channel.PHONE_OUTBOUND.value: "Telefon (Ausgang)",
    Channel.EMAIL.value: "E-Mail",
    Channel.DEV_TICKET.value: "Entwickler-Ticket",
    Channel.INTERNAL_NOTE.value: "Interne Notiz",
}

ACTOR_DISPLAY = {
    Actor.SUPPORT.value: "Support",
    Actor.DEVELOPMENT.value: "Entwicklung",
    Actor.TECH.value: "Technik",
    Actor.CUSTOMER.value: "Kunde",
}

LAYOUT_DISPLAY = {
    LayoutMode.COCKPIT.value: "Cockpit (Einzel-Fall)",
    LayoutMode.BOARD.value: "Kanban-Board (Zuständigkeiten)",
    LayoutMode.TABLE.value: "Tabelle & Details (Sortier-Matrix)",
}

BOARD_COLUMN_DISPLAY = {
    BoardColumn.NEW.value: "Neu",
    BoardColumn.ACTION_REQUIRED.value: "Aktion erforderlich",
    BoardColumn.WAITING.value: "Warten auf Kunde",
    BoardColumn.IN_PROGRESS.value: "In Bearbeitung",
    BoardColumn.DONE.value: "Erledigt",
}


def get_channel_display(val: str) -> str:
    return CHANNEL_DISPLAY.get(val, val)


def get_actor_display(val: str) -> str:
    return ACTOR_DISPLAY.get(val, val)


def get_layout_display(val: str) -> str:
    return LAYOUT_DISPLAY.get(val, val)


def get_board_column_display(val: str) -> str:
    return BOARD_COLUMN_DISPLAY.get(val, val)


def get_actor_val_from_display(display: str) -> str:
    for k, v in ACTOR_DISPLAY.items():
        if v == display:
            return k
    return display


def get_channel_val_from_display(display: str) -> str:
    for k, v in CHANNEL_DISPLAY.items():
        if v == display:
            return k
    return display


def get_layout_val_from_display(display: str) -> str:
    for k, v in LAYOUT_DISPLAY.items():
        if v == display:
            return k
    return display
