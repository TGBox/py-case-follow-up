from dataclasses import dataclass, field, asdict
from typing import Any
from enums import SyncMode, LayoutMode
from utils.security import normalize_url
from constants import DEFAULT_COLUMN_WIDTHS, DEFAULT_TAGS, DEFAULT_MODULE_TAGS, VALIDATION_MESSAGES


@dataclass
class UserInfo:
    name: str = "Support Agent"
    department: str = "Support"
    extension: str = ""
    email: str = ""
    mobile: str = ""
    email_signature: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserInfo":
        return cls(
            name=data.get("name", "Support Agent"),
            department=data.get("department", "Support"),
            extension=data.get("extension", ""),
            email=data.get("email", ""),
            mobile=data.get("mobile", ""),
            email_signature=data.get("email_signature", ""),
        )


@dataclass
class UISettings:
    theme: str = "SYSTEM"
    default_layout: str = LayoutMode.COCKPIT
    column_widths: dict[str, int] = field(
        default_factory=lambda: dict(DEFAULT_COLUMN_WIDTHS)
    )
    board_collapsed: dict[str, bool] = field(
        default_factory=lambda: {"support": False, "dev": False, "followup": False, "completed": False}
    )
    table_column_widths: dict[str, int] = field(
        default_factory=lambda: {"case_id": 120, "practice": 220, "title": 280, "actor": 130, "followup": 150, "score": 90}
    )
    table_column_order: list[str] = field(
        default_factory=lambda: ["case_id", "practice", "title", "actor", "followup", "score"]
    )
    show_demo_data: bool | None = None
    textbox_height: int = 90
    custom_textbox_heights: dict[str, int] = field(default_factory=dict)

    def reset_column_widths(self) -> None:
        self.column_widths = dict(DEFAULT_COLUMN_WIDTHS)
        self.board_collapsed = {"support": False, "dev": False, "followup": False, "completed": False}
        self.table_column_widths = {"case_id": 120, "practice": 220, "title": 280, "actor": 130, "followup": 150, "score": 90}
        self.table_column_order = ["case_id", "practice", "title", "actor", "followup", "score"]
        self.textbox_height = 90
        self.custom_textbox_heights = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "theme": self.theme,
            "default_layout": self.default_layout,
            "column_widths": self.column_widths,
            "board_collapsed": self.board_collapsed,
            "table_column_widths": self.table_column_widths,
            "table_column_order": self.table_column_order,
            "show_demo_data": self.show_demo_data,
            "textbox_height": self.textbox_height,
            "custom_textbox_heights": self.custom_textbox_heights,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UISettings":
        widths = data.get("column_widths", {})
        default_widths = dict(DEFAULT_COLUMN_WIDTHS)
        if isinstance(widths, dict):
            default_widths.update({k: int(v) for k, v in widths.items() if isinstance(v, (int, float))})

        b_collapsed = {"support": False, "dev": False, "followup": False, "completed": False}
        if isinstance(data.get("board_collapsed"), dict):
            b_collapsed.update(data["board_collapsed"])

        t_widths = {"case_id": 120, "practice": 220, "title": 280, "actor": 130, "followup": 150, "score": 90}
        if isinstance(data.get("table_column_widths"), dict):
            t_widths.update({k: int(v) for k, v in data["table_column_widths"].items() if isinstance(v, (int, float))})

        def_order = ["case_id", "practice", "title", "actor", "followup", "score"]
        t_order = list(data.get("table_column_order", def_order)) if isinstance(data.get("table_column_order"), list) else def_order

        s_demo = data.get("show_demo_data")
        if not isinstance(s_demo, bool):
            s_demo = None

        tb_height = int(data.get("textbox_height", 90))
        cust_tb_heights = dict(data.get("custom_textbox_heights", {})) if isinstance(data.get("custom_textbox_heights"), dict) else {}

        return cls(
            theme=data.get("theme", "SYSTEM"),
            default_layout=data.get("default_layout", LayoutMode.COCKPIT),
            column_widths=default_widths,
            board_collapsed=b_collapsed,
            table_column_widths=t_widths,
            table_column_order=t_order,
            show_demo_data=s_demo,
            textbox_height=tb_height,
            custom_textbox_heights=cust_tb_heights,
        )


@dataclass
class ShortcutSettings:
    new_case: str = "<Control-n>"
    search_customer: str = "<Control-f>"
    wiki_search: str = "<Control-w>"
    export_dialog: str = "<Control-e>"
    save_case: str = "<Control-s>"
    archive_case: str = "<Control-Shift-A>"
    open_settings: str = "<Control-p>"
    snippet_picker: str = "<Control-m>"
    view_cockpit: str = "<Control-1>"
    view_board: str = "<Control-2>"
    view_table: str = "<Control-3>"
    toggle_theme: str = "<Control-t>"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ShortcutSettings":
        return cls(
            new_case=data.get("new_case", "<Control-n>"),
            search_customer=data.get("search_customer", "<Control-f>"),
            wiki_search=data.get("wiki_search", "<Control-w>"),
            export_dialog=data.get("export_dialog", "<Control-e>"),
            save_case=data.get("save_case", "<Control-s>"),
            archive_case=data.get("archive_case", "<Control-Shift-A>"),
            open_settings=data.get("open_settings", "<Control-p>"),
            snippet_picker=data.get("snippet_picker", "<Control-m>"),
            view_cockpit=data.get("view_cockpit", "<Control-1>"),
            view_board=data.get("view_board", "<Control-2>"),
            view_table=data.get("view_table", "<Control-3>"),
            toggle_theme=data.get("toggle_theme", "<Control-t>"),
        )


@dataclass
class ReminderSettings:
    notification_level: str = "LEVEL_A"
    audio_enabled: bool = False
    os_popup_enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReminderSettings":
        return cls(
            notification_level=data.get("notification_level", "LEVEL_A"),
            audio_enabled=bool(data.get("audio_enabled", False)),
            os_popup_enabled=bool(data.get("os_popup_enabled", True)),
        )


@dataclass
class ScoringMatrix:
    vip_bonus_points: int = 50
    points_per_idle_day: int = 15
    deadline_close_hours: int = 2
    deadline_close_bonus: int = 40
    deadline_overdue_bonus: int = 100
    threshold_yellow: int = 50
    threshold_red: int = 100

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScoringMatrix":
        return cls(
            vip_bonus_points=int(data.get("vip_bonus_points", 50)),
            points_per_idle_day=int(data.get("points_per_idle_day", 15)),
            deadline_close_hours=int(data.get("deadline_close_hours", 2)),
            deadline_close_bonus=int(data.get("deadline_close_bonus", 40)),
            deadline_overdue_bonus=int(data.get("deadline_overdue_bonus", 100)),
            threshold_yellow=int(data.get("threshold_yellow", 50)),
            threshold_red=int(data.get("threshold_red", 100)),
        )


@dataclass
class WikiSettings:
    api_url: str = ""
    token_id: str = "ENV_BOOKSTACK_TOKEN_ID"
    token_secret: str = "ENV_BOOKSTACK_TOKEN_SECRET"
    sync_mode: str = SyncMode.METADATA_ONLY
    sync_on_startup: bool = True

    def __post_init__(self):
        self.api_url = normalize_url(self.api_url)

    def to_dict(self) -> dict[str, Any]:
        return {
            "api_url": self.api_url,
            "token_id": self.token_id,
            "token_secret": self.token_secret,
            "sync_mode": self.sync_mode,
            "sync_on_startup": self.sync_on_startup,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WikiSettings":
        return cls(
            api_url=normalize_url(data.get("api_url", "")),
            token_id=data.get("token_id", "ENV_BOOKSTACK_TOKEN_ID"),
            token_secret=data.get("token_secret", "ENV_BOOKSTACK_TOKEN_SECRET"),
            sync_mode=data.get("sync_mode", SyncMode.METADATA_ONLY),
            sync_on_startup=bool(data.get("sync_on_startup", True)),
        )


from constants import DEFAULT_OLLAMA_URL, DEFAULT_OLLAMA_MODEL


@dataclass
class AiSettings:
    ollama_url: str = DEFAULT_OLLAMA_URL
    model_name: str = DEFAULT_OLLAMA_MODEL
    enable_ai: bool = True
    auto_summarize_on_open: bool = False
    base_rules: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AiSettings":
        rules_raw = data.get("base_rules", [])
        rules = list(rules_raw) if isinstance(rules_raw, list) else []
        return cls(
            ollama_url=data.get("ollama_url", DEFAULT_OLLAMA_URL),
            model_name=data.get("model_name", DEFAULT_OLLAMA_MODEL),
            enable_ai=bool(data.get("enable_ai", True)),
            auto_summarize_on_open=bool(data.get("auto_summarize_on_open", False)),
            base_rules=rules,
        )


DEFAULT_MODULE_TAGS = [
    "Fakturaübersicht",
    "Rezeptdruck",
    "Labor",
    "eRezept / Verordnung",
    "EGK-Kartenleser",
    "GKV-Export",
    "PVS-Schnittstelle",
    "Terminkalender",
    "Stammdaten",
    "System / Allgemeine GUI",
]


@dataclass
class UserProfile:
    user: UserInfo = field(default_factory=UserInfo)
    ui_settings: UISettings = field(default_factory=UISettings)
    shortcuts: ShortcutSettings = field(default_factory=ShortcutSettings)
    reminder_settings: ReminderSettings = field(default_factory=ReminderSettings)
    scoring_matrix: ScoringMatrix = field(default_factory=ScoringMatrix)
    wiki_settings: WikiSettings = field(default_factory=WikiSettings)
    ai_settings: AiSettings = field(default_factory=AiSettings)
    available_tags: list[str] = field(default_factory=lambda: list(DEFAULT_TAGS))
    available_module_tags: list[str] = field(default_factory=lambda: list(DEFAULT_MODULE_TAGS))

    def to_dict(self) -> dict[str, Any]:
        return {
            "user": self.user.to_dict(),
            "ui_settings": self.ui_settings.to_dict(),
            "shortcuts": self.shortcuts.to_dict(),
            "reminder_settings": self.reminder_settings.to_dict(),
            "scoring_matrix": self.scoring_matrix.to_dict(),
            "wiki_settings": self.wiki_settings.to_dict(),
            "ai_settings": self.ai_settings.to_dict(),
            "available_tags": self.available_tags,
            "available_module_tags": self.available_module_tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserProfile":
        tags_raw = data.get("available_tags", DEFAULT_TAGS)
        tags = list(tags_raw) if isinstance(tags_raw, list) else list(DEFAULT_TAGS)
        mod_tags_raw = data.get("available_module_tags", DEFAULT_MODULE_TAGS)
        mod_tags = list(mod_tags_raw) if isinstance(mod_tags_raw, list) else list(DEFAULT_MODULE_TAGS)
        return cls(
            user=UserInfo.from_dict(data.get("user", {})),
            ui_settings=UISettings.from_dict(data.get("ui_settings", {})),
            shortcuts=ShortcutSettings.from_dict(data.get("shortcuts", {})),
            reminder_settings=ReminderSettings.from_dict(data.get("reminder_settings", {})),
            scoring_matrix=ScoringMatrix.from_dict(data.get("scoring_matrix", {})),
            wiki_settings=WikiSettings.from_dict(data.get("wiki_settings", {})),
            ai_settings=AiSettings.from_dict(data.get("ai_settings", {})),
            available_tags=tags,
            available_module_tags=mod_tags,
        )


@dataclass
class Colleague:
    username: str = ""
    name: str = ""
    department: str = "Support"
    extension: str = ""
    email: str = ""
    mobile: str = ""
    notes: str = ""
    cases_path: str = ""
    is_absent: bool = False
    absence_reason: str = ""

    def validate(self) -> list[str]:
        errors = []
        if not self.username.strip():
            errors.append(VALIDATION_MESSAGES["username_required"])
        if not self.name.strip():
            errors.append(VALIDATION_MESSAGES["name_required"])
        return errors

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Colleague":
        return cls(
            username=data.get("username", ""),
            name=data.get("name", ""),
            department=data.get("department", "Support"),
            extension=data.get("extension", ""),
            email=data.get("email", ""),
            mobile=data.get("mobile", ""),
            notes=data.get("notes", ""),
            cases_path=data.get("cases_path", ""),
            is_absent=data.get("is_absent", False),
            absence_reason=data.get("absence_reason", ""),
        )
