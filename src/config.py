import json
import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("SupportCockpit")


def get_global_config_dir() -> Path:
    """Returns the persistent user appdata folder for SupportCockpit."""
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path.home() / ".config"
    config_dir = base / "SupportCockpit"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_global_config_file() -> Path:
    return get_global_config_dir() / "user_config.json"


def is_frozen_app() -> bool:
    """Checks if running inside a compiled PyInstaller / single-file EXE."""
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def get_default_workspace_dir() -> Path:
    """Gets default workspace directory depending on execution mode."""
    if is_frozen_app():
        return Path.home() / "Documents" / "SupportCockpitData"
    return Path.cwd()


@dataclass
class AppConfig:
    workspace_dir: Path = field(default_factory=get_default_workspace_dir)
    username: str = field(default_factory=lambda: os.getlogin() if hasattr(os, "getlogin") else "default_user")

    # Optional individual file path overrides
    custom_cases_path: Path | None = None
    custom_archive_path: Path | None = None
    custom_customers_path: Path | None = None
    custom_app_profile_path: Path | None = None
    custom_colleagues_path: Path | None = None
    custom_question_schemas_path: Path | None = None
    custom_export_templates_path: Path | None = None
    custom_wiki_db_path: Path | None = None
    column_widths: dict[str, int] = field(
        default_factory=lambda: {
            "cockpit_left": 300,
            "cockpit_center": 420,
            "cockpit_right": 320,
            "board_column": 280,
        }
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
        return self.workspace_dir / "data"

    @property
    def example_data_dir(self) -> Path:
        if is_frozen_app():
            meipass_examples = Path(getattr(sys, "_MEIPASS")) / "data_examples"
            if meipass_examples.exists():
                return meipass_examples
        return self.workspace_dir / "data_examples"

    @property
    def cases_path(self) -> Path:
        return self.custom_cases_path or (self.data_dir / "cases.json")

    @property
    def archive_path(self) -> Path:
        return self.custom_archive_path or (self.data_dir / "archive.json")

    @property
    def customers_path(self) -> Path:
        return self.custom_customers_path or (self.data_dir / "customers.json")

    @property
    def app_profile_path(self) -> Path:
        return self.custom_app_profile_path or (self.data_dir / "app_profile.json")

    @property
    def colleagues_path(self) -> Path:
        return self.custom_colleagues_path or (self.data_dir / "colleagues.json")

    @property
    def question_schemas_path(self) -> Path:
        return self.custom_question_schemas_path or (self.data_dir / "question_schemas.json")

    @property
    def export_templates_path(self) -> Path:
        return self.custom_export_templates_path or (self.data_dir / "export_templates.json")

    @property
    def wiki_db_path(self) -> Path:
        return self.custom_wiki_db_path or (self.data_dir / "wiki_index.sqlite")

    @property
    def log_file_path(self) -> Path:
        return self.data_dir / "app.log"

    @property
    def attachments_dir(self) -> Path:
        return self.data_dir / "attachments"

    @property
    def backups_dir(self) -> Path:
        return self.data_dir / "backups"

    @property
    def colleagues_dir(self) -> Path:
        return self.data_dir / "colleagues"

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
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved global user config to {config_file}")
        except Exception as e:
            logger.error(f"Failed to save user config: {e}")

    @classmethod
    def load_user_config(cls, cli_workspace: str | Path | None = None) -> "AppConfig":
        """Loads AppConfig with persisted global settings if present."""
        if cli_workspace:
            ws_dir = Path(cli_workspace)
            return cls(workspace_dir=ws_dir)

        config_file = get_global_config_file()
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                ws_path_str = data.get("workspace_dir")
                ws_dir = Path(ws_path_str) if ws_path_str else get_default_workspace_dir()
                if not ws_dir.exists():
                    logger.warning(f"Configured workspace_dir '{ws_dir}' does not exist. Falling back to default workspace.")
                    ws_dir = get_default_workspace_dir()

                col_widths = data.get("column_widths", {})
                default_widths = {"cockpit_left": 300, "cockpit_center": 420, "cockpit_right": 320, "board_column": 280}
                if isinstance(col_widths, dict):
                    default_widths.update(col_widths)

                return cls(
                    workspace_dir=ws_dir,
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
