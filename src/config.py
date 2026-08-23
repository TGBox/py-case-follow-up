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
    def data_dir(self) -> Path:
        return self.workspace_dir / "data"

    @property
    def example_data_dir(self) -> Path:
        return self.workspace_dir / "data_examples"

    @property
    def cases_path(self) -> Path:
        return self.data_dir / "cases.json"

    @property
    def archive_path(self) -> Path:
        return self.data_dir / "archive.json"

    @property
    def customers_path(self) -> Path:
        return self.data_dir / "customers.json"

    @property
    def app_profile_path(self) -> Path:
        return self.data_dir / "app_profile.json"

    @property
    def colleagues_path(self) -> Path:
        return self.data_dir / "colleagues.json"

    @property
    def question_schemas_path(self) -> Path:
        return self.data_dir / "question_schemas.json"

    @property
    def export_templates_path(self) -> Path:
        return self.data_dir / "export_templates.json"

    @property
    def wiki_db_path(self) -> Path:
        return self.data_dir / "wiki_index.sqlite"

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
