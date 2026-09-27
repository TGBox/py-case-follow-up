import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from config import AppConfig
from models.case import Case

# Reserved names in Windows
RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
}


def sanitize_filename(name: str) -> str:
    """Sanitizes a string for safe Windows folder/file naming."""
    if not name:
        return "unnamed"
    # Replace invalid chars with underscore
    sanitized = re.sub(r'[<>:"/\\|?*\s]+', '_', name.strip())
    sanitized = sanitized.strip("._")
    if not sanitized or sanitized.upper() in RESERVED_NAMES:
        sanitized = f"safe_{sanitized}"
    return sanitized[:50]


class AttachmentService:
    def __init__(self, config: AppConfig):
        self.config = config

    def get_case_attachment_dir(self, case: Case) -> Path:
        """Returns Path to the case attachment directory, creating it if needed."""
        if case.attachment_directory:
            p = Path(case.attachment_directory)
            if p.is_absolute():
                case_dir = p
            else:
                norm_att = case.attachment_directory.replace("\\", "/")
                if norm_att.startswith("attachments/"):
                    old_path = self.config.workspace_dir / case.attachment_directory
                    new_rel = f"data/{norm_att}"
                    new_path = self.config.workspace_dir / new_rel
                    if old_path.exists() and not new_path.exists():
                        try:
                            new_path.parent.mkdir(parents=True, exist_ok=True)
                            shutil.move(str(old_path), str(new_path))
                        except Exception:
                            pass
                    case.attachment_directory = new_rel
                    case_dir = new_path
                else:
                    case_dir = self.config.workspace_dir / case.attachment_directory
        else:
            safe_practice = sanitize_filename(case.customer.practice_name or "Praxis")
            dir_name = f"{case.case_id}_{safe_practice}"
            case_dir = self.config.attachments_dir / dir_name
            case.attachment_directory = str(case_dir.relative_to(self.config.workspace_dir))

        case_dir.mkdir(parents=True, exist_ok=True)
        return case_dir

    def list_attachments(self, case: Case) -> list[Path]:
        """Lists files in the case attachment directory."""
        dir_path = self.get_case_attachment_dir(case)
        if not dir_path.exists():
            return []
        return [f for f in dir_path.iterdir() if f.is_file()]

    def copy_attachment(self, case: Case, file_path: Path) -> Path:
        """Copies an external file into the case attachment directory."""
        dir_path = self.get_case_attachment_dir(case)
        dest_path = dir_path / file_path.name

        # Handle collision
        if dest_path.exists():
            timestamp = datetime.now().strftime("%H%M%S")
            dest_path = dir_path / f"{file_path.stem}_{timestamp}{file_path.suffix}"

        shutil.copy2(file_path, dest_path)
        return dest_path

    def save_clipboard_image(self, case: Case) -> Path | None:
        """Saves image from Windows clipboard as PNG in case attachment directory."""
        dir_path = self.get_case_attachment_dir(case)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        dest_path = dir_path / f"{timestamp}_clipboard.png"

        try:
            from PIL import Image, ImageGrab  # type: ignore
            img = ImageGrab.grabclipboard()
            if isinstance(img, Image.Image):
                img.save(dest_path, "PNG")
                return dest_path
        except Exception:
            pass
        return None

    def open_in_explorer(self, case: Case) -> None:
        """Opens the case attachment directory in Windows Explorer."""
        dir_path = self.get_case_attachment_dir(case)
        if hasattr(os, "startfile"):
            os.startfile(str(dir_path))
        else:
            subprocess.run(["explorer", str(dir_path)])
