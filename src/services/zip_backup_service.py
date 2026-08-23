import zipfile
import shutil
from pathlib import Path
from typing import Any
from services.storage_service import StorageService


class ZipBackupService:
    """Service to export and import complete app backups including data files and attachments."""

    @staticmethod
    def export_backup_zip(storage_service: StorageService, output_zip_path: Path) -> dict[str, Any]:
        """Packs all files in data_dir and attachments_dir into a zip archive."""
        config = storage_service.config
        config.ensure_directories()

        data_dir = config.data_dir
        attachments_dir = config.attachments_dir

        file_count = 0
        total_bytes = 0

        with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # 1. Add all data_dir files
            if data_dir.exists():
                for file_path in data_dir.rglob("*"):
                    if file_path.is_file() and not file_path.name.endswith(".tmp.json"):
                        rel_path = Path("data") / file_path.relative_to(data_dir)
                        zf.write(file_path, arcname=str(rel_path))
                        file_count += 1
                        total_bytes += file_path.stat().st_size

            # 2. Add all attachments_dir files
            if attachments_dir.exists():
                for file_path in attachments_dir.rglob("*"):
                    if file_path.is_file():
                        rel_path = Path("attachments") / file_path.relative_to(attachments_dir)
                        zf.write(file_path, arcname=str(rel_path))
                        file_count += 1
                        total_bytes += file_path.stat().st_size

        return {
            "zip_path": str(output_zip_path),
            "file_count": file_count,
            "total_bytes": total_bytes,
        }

    @staticmethod
    def inspect_backup_zip(zip_file_path: Path) -> dict[str, Any]:
        """Inspects contents of a backup zip archive."""
        data_files = 0
        attachment_files = 0
        total_bytes = 0

        with zipfile.ZipFile(zip_file_path, "r") as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                total_bytes += info.file_size
                if info.filename.startswith("data/") or info.filename.startswith("data\\"):
                    data_files += 1
                elif info.filename.startswith("attachments/") or info.filename.startswith("attachments\\"):
                    attachment_files += 1

        return {
            "total_files": data_files + attachment_files,
            "data_files": data_files,
            "attachment_files": attachment_files,
            "total_bytes": total_bytes,
        }

    @staticmethod
    def import_backup_zip(
        zip_file_path: Path,
        target_data_dir: Path,
        target_attachments_dir: Path,
    ) -> dict[str, Any]:
        """Unpacks backup zip into specified target_data_dir and target_attachments_dir."""
        target_data_dir.mkdir(parents=True, exist_ok=True)
        target_attachments_dir.mkdir(parents=True, exist_ok=True)

        extracted_data = 0
        extracted_attachments = 0

        with zipfile.ZipFile(zip_file_path, "r") as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue

                fn = info.filename.replace("\\", "/")

                if fn.startswith("data/"):
                    rel = fn[len("data/"):]
                    if rel and not rel.endswith(".tmp.json"):
                        dest = target_data_dir / rel
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(info) as src, open(dest, "wb") as out:
                            shutil.copyfileobj(src, out)
                        extracted_data += 1

                elif fn.startswith("attachments/"):
                    rel = fn[len("attachments/"):]
                    if rel:
                        dest = target_attachments_dir / rel
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(info) as src, open(dest, "wb") as out:
                            shutil.copyfileobj(src, out)
                        extracted_attachments += 1

                else:
                    # Generic root files in zip -> default to target_data_dir
                    dest = target_data_dir / fn
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(info) as src, open(dest, "wb") as out:
                        shutil.copyfileobj(src, out)
                    extracted_data += 1

        return {
            "extracted_data_files": extracted_data,
            "extracted_attachment_files": extracted_attachments,
            "target_data_dir": str(target_data_dir),
            "target_attachments_dir": str(target_attachments_dir),
        }
