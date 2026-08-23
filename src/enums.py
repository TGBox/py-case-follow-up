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
    TAB_VIEW = "TAB_VIEW"
    SPLIT_VIEW = "SPLIT_VIEW"
