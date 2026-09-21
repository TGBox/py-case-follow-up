import json
import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

from constants import (
    APP_LOG_FILENAME,
    APP_NAME,
    APP_PROFILE_FILENAME,
    ARCHIVE_FILENAME,
    ATTACHMENTS_DIRNAME,
    BACKUPS_DIRNAME,
    CASES_FILENAME,
    COLLEAGUES_DIRNAME,
    COLLEAGUES_FILENAME,
    CUSTOMERS_FILENAME,
    DATA_DIRNAME,
    DATA_EXAMPLES_DIRNAME,
    DEFAULT_COLUMN_WIDTHS,
    DEFAULT_FROZEN_WORKSPACE_NAME,
    DEFAULT_USER_NAME,
    ENV_SUPPORTCOCKPIT_CONFIG_DIR,
    EXPORT_TEMPLATES_FILENAME,
    JSON_INDENT,
    QUESTION_SCHEMAS_FILENAME,
    USER_CONFIG_FILENAME,
    WIKI_DB_FILENAME,
)

logger = logging.getLogger("SupportCockpit")


def get_global_config_dir() -> Path:
    """Returns the persistent user appdata folder for SupportCockpit."""
    if ENV_SUPPORTCOCKPIT_CONFIG_DIR in os.environ and os.environ[ENV_SUPPORTCOCKPIT_CONFIG_DIR].strip():
        config_dir = Path(os.environ[ENV_SUPPORTCOCKPIT_CONFIG_DIR])
    elif os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home()))
        config_dir = base / APP_NAME
    else:
        base = Path.home() / ".config"
        config_dir = base / APP_NAME
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_global_config_file() -> Path:
    return get_global_config_dir() / USER_CONFIG_FILENAME


def is_frozen_app() -> bool:
    """Checks if running inside a compiled PyInstaller / single-file EXE."""
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def get_default_workspace_dir() -> Path:
    """Gets default workspace directory depending on execution mode."""
    if is_frozen_app():
        return Path.home() / "Documents" / DEFAULT_FROZEN_WORKSPACE_NAME
    return Path.cwd()


@dataclass
class AppConfig:
    workspace_dir: Path = field(default_factory=get_default_workspace_dir)
    username: str = field(default_factory=lambda: os.getlogin() if hasattr(os, "getlogin") else DEFAULT_USER_NAME)

    # Optional individual file path overrides
    active_profile_name: str | None = None
    custom_cases_path: Path | None = None
    custom_archive_path: Path | None = None
    custom_customers_path: Path | None = None
    custom_app_profile_path: Path | None = None
    custom_colleagues_path: Path | None = None
    custom_question_schemas_path: Path | None = None
    custom_export_templates_path: Path | None = None
    custom_wiki_db_path: Path | None = None
    # Set when --workspace named the directory. Not persisted: it describes how
    # this one start was invoked, and it keeps the profile's stored workspace
    # from overriding what the user asked for on the command line.
    workspace_from_cli: bool = False
    column_widths: dict[str, int] = field(
        default_factory=lambda: dict(DEFAULT_COLUMN_WIDTHS)
    )

    def __post_init__(self):
        if isinstance(self.workspace_dir, str):
            self.workspace_dir = Path(self.workspace_dir)
        for attr in [
            "custom_cases_path", "custom_archive_path", "custom_customers_path",
            "custom_app_profile_path", "custom_colleagues_path",
            "custom_question_schemas_path", "custom_export_templates_path", "custom_wiki_db_path"
        ]:
            val = getattr(self, attr)
            if isinstance(val, str) and val.strip():
                setattr(self, attr, Path(val))

        from utils.security import load_env_file
        load_env_file(self.workspace_dir / ".env")

    @property
    def data_dir(self) -> Path:
        return self.workspace_dir / DATA_DIRNAME

    @property
    def example_data_dir(self) -> Path:
        if is_frozen_app():
            # sys._MEIPASS is injected by PyInstaller at runtime for frozen builds -
            # it isn't in typeshed for any platform (unlike os.startfile/ctypes.windll,
            # which pythonPlatform="Windows" covers), so pyright never knows about it
            # regardless of platform config. is_frozen_app() already confirms
            # hasattr(sys, "_MEIPASS") above; getattr() here just avoids needing a
            # pyright suppression comment for something already runtime-guarded.
            meipass_examples = Path(getattr(sys, "_MEIPASS", "")) / DATA_EXAMPLES_DIRNAME
            if meipass_examples.exists():
                return meipass_examples
        return self.workspace_dir / DATA_EXAMPLES_DIRNAME

    @property
    def cases_path(self) -> Path:
        return self.custom_cases_path or (self.data_dir / CASES_FILENAME)

    @property
    def archive_path(self) -> Path:
        return self.custom_archive_path or (self.data_dir / ARCHIVE_FILENAME)

    @property
    def customers_path(self) -> Path:
        return self.custom_customers_path or (self.data_dir / CUSTOMERS_FILENAME)

    @property
    def app_profile_path(self) -> Path:
        return self.custom_app_profile_path or (self.data_dir / APP_PROFILE_FILENAME)

    @property
    def colleagues_path(self) -> Path:
        return self.custom_colleagues_path or (self.data_dir / COLLEAGUES_FILENAME)

    @property
    def question_schemas_path(self) -> Path:
        return self.custom_question_schemas_path or (self.data_dir / QUESTION_SCHEMAS_FILENAME)

    @property
    def export_templates_path(self) -> Path:
        return self.custom_export_templates_path or (self.data_dir / EXPORT_TEMPLATES_FILENAME)

    @property
    def wiki_db_path(self) -> Path:
        return self.custom_wiki_db_path or (self.data_dir / WIKI_DB_FILENAME)

    @property
    def log_file_path(self) -> Path:
        return self.data_dir / APP_LOG_FILENAME

    @property
    def attachments_dir(self) -> Path:
        return self.data_dir / ATTACHMENTS_DIRNAME

    @property
    def backups_dir(self) -> Path:
        return self.data_dir / BACKUPS_DIRNAME

    @property
    def colleagues_dir(self) -> Path:
        return self.data_dir / COLLEAGUES_DIRNAME

    def get_example_path(self, filename: str) -> Path:
        return self.example_data_dir / filename

    def ensure_directories(self) -> None:
        """Ensures all necessary workspace directories exist."""
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.attachments_dir.mkdir(parents=True, exist_ok=True)
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        self.colleagues_dir.mkdir(parents=True, exist_ok=True)

        for path in [
            self.cases_path, self.archive_path, self.customers_path,
            self.app_profile_path, self.colleagues_path,
            self.question_schemas_path, self.export_templates_path, self.wiki_db_path
        ]:
            path.parent.mkdir(parents=True, exist_ok=True)

    def save_user_config(self) -> None:
        """Persists custom workspace and file path settings globally."""
        config_file = get_global_config_file()
        data = {
            "workspace_dir": str(self.workspace_dir),
            "active_profile_name": self.active_profile_name,
            "custom_cases_path": str(self.custom_cases_path) if self.custom_cases_path else None,
            "custom_archive_path": str(self.custom_archive_path) if self.custom_archive_path else None,
            "custom_customers_path": str(self.custom_customers_path) if self.custom_customers_path else None,
            "custom_app_profile_path": str(self.custom_app_profile_path) if self.custom_app_profile_path else None,
            "custom_colleagues_path": str(self.custom_colleagues_path) if self.custom_colleagues_path else None,
            "custom_question_schemas_path": str(self.custom_question_schemas_path) if self.custom_question_schemas_path else None,
            "custom_export_templates_path": str(self.custom_export_templates_path) if self.custom_export_templates_path else None,
            "custom_wiki_db_path": str(self.custom_wiki_db_path) if self.custom_wiki_db_path else None,
            "column_widths": self.column_widths,
        }
        try:
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=JSON_INDENT, ensure_ascii=False)
            logger.info(f"Saved global user config to {config_file}")
        except Exception as e:
            logger.error(f"Failed to save user config: {e}")

    @classmethod
    def load_user_config(cls, cli_workspace: str | Path | None = None) -> AppConfig:
        """Loads AppConfig with persisted global settings if present."""
        if cli_workspace:
            ws_dir = Path(cli_workspace)
            return cls(workspace_dir=ws_dir, workspace_from_cli=True)

        config_file = get_global_config_file()
        if config_file.exists():
            try:
                with open(config_file, encoding="utf-8") as f:
                    data = json.load(f)

                ws_path_str = data.get("workspace_dir")
                ws_dir = Path(ws_path_str) if ws_path_str else get_default_workspace_dir()
                if not ws_dir.exists():
                    logger.warning(f"Configured workspace_dir '{ws_dir}' does not exist. Falling back to default workspace.")
                    ws_dir = get_default_workspace_dir()

                col_widths = data.get("column_widths", {})
                default_widths = dict(DEFAULT_COLUMN_WIDTHS)
                if isinstance(col_widths, dict):
                    default_widths.update(col_widths)

                active_prof = data.get("active_profile_name")
                return cls(
                    workspace_dir=ws_dir,
                    active_profile_name=str(active_prof) if active_prof else None,
                    custom_cases_path=Path(data["custom_cases_path"]) if data.get("custom_cases_path") else None,
                    custom_archive_path=Path(data["custom_archive_path"]) if data.get("custom_archive_path") else None,
                    custom_customers_path=Path(data["custom_customers_path"]) if data.get("custom_customers_path") else None,
                    custom_app_profile_path=Path(data["custom_app_profile_path"]) if data.get("custom_app_profile_path") else None,
                    custom_colleagues_path=Path(data["custom_colleagues_path"]) if data.get("custom_colleagues_path") else None,
                    custom_question_schemas_path=Path(data["custom_question_schemas_path"]) if data.get("custom_question_schemas_path") else None,
                    custom_export_templates_path=Path(data["custom_export_templates_path"]) if data.get("custom_export_templates_path") else None,
                    custom_wiki_db_path=Path(data["custom_wiki_db_path"]) if data.get("custom_wiki_db_path") else None,
                    column_widths=default_widths,
                )
            except Exception as e:
                logger.error(f"Error loading global user config: {e}")

        return cls()
