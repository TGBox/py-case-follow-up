from dataclasses import dataclass, field
from pathlib import Path
import os


@dataclass
class AppConfig:
    workspace_dir: Path = field(default_factory=lambda: Path.cwd())
    username: str = field(default_factory=lambda: os.getlogin() if hasattr(os, "getlogin") else "default_user")

    def __post_init__(self):
        if isinstance(self.workspace_dir, str):
            self.workspace_dir = Path(self.workspace_dir)

    @property
    def cases_path(self) -> Path:
        return self.workspace_dir / "cases.json"

    @property
    def archive_path(self) -> Path:
        return self.workspace_dir / "archive.json"

    @property
    def customers_path(self) -> Path:
        return self.workspace_dir / "customers.json"

    @property
    def app_profile_path(self) -> Path:
        return self.workspace_dir / "app_profile.json"

    @property
    def colleagues_path(self) -> Path:
        return self.workspace_dir / "colleagues.json"

    @property
    def question_schemas_path(self) -> Path:
        return self.workspace_dir / "question_schemas.json"

    @property
    def export_templates_path(self) -> Path:
        return self.workspace_dir / "export_templates.json"

    @property
    def wiki_db_path(self) -> Path:
        return self.workspace_dir / "wiki_index.sqlite"

    @property
    def log_file_path(self) -> Path:
        return self.workspace_dir / "app.log"

    @property
    def attachments_dir(self) -> Path:
        return self.workspace_dir / "attachments"

    @property
    def backups_dir(self) -> Path:
        return self.workspace_dir / "backups"

    def ensure_directories(self) -> None:
        """Ensures all necessary workspace directories exist."""
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.attachments_dir.mkdir(parents=True, exist_ok=True)
        self.backups_dir.mkdir(parents=True, exist_ok=True)
