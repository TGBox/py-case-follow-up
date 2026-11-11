import zipfile
import shutil
from pathlib import Path, PurePosixPath
from typing import Any
from constants import APP_LOG_FILENAME, ATTACHMENTS_DIRNAME, DATA_DIRNAME
from services.storage_service import StorageService

_TEMP_SUFFIX = ".tmp.json"
_DATA_PREFIX = f"{DATA_DIRNAME}/"
_ATTACHMENTS_PREFIX = f"{ATTACHMENTS_DIRNAME}/"


class UnsafeZipEntryError(ValueError):
    """A ZIP entry would be written outside the chosen target folders."""

    def __init__(self, entry_name: str):
        self.entry_name = entry_name
        super().__init__(f"ZIP entry leaves the target folder: {entry_name!r}")


def _is_export_noise(file_path: Path, data_dir: Path, attachments_dir: Path, backups_dir: Path) -> bool:
    """Files below data_dir that do not belong in the data part of a backup ZIP.

    - attachments: attachments_dir lies inside data_dir and is packed on its
      own under "attachments/" - walking it here as well stored every
      attachment twice.
    - backups: the daily copies and safety snapshots of the very files that
      are in the ZIP anyway; they only multiplied its size.
    - log files and half-written temp files: not data.
    """
    if file_path.name.endswith(_TEMP_SUFFIX):
        return True
    if file_path.name == APP_LOG_FILENAME or file_path.name.startswith(f"{APP_LOG_FILENAME}."):
        return True
    return file_path.is_relative_to(attachments_dir) or file_path.is_relative_to(backups_dir)


def _safe_destination(base_dir: Path, relative_name: str, entry_name: str) -> Path:
    """Where a ZIP entry lands below base_dir - or UnsafeZipEntryError.

    Entry names come from the archive and are not trustworthy: "../" segments,
    an absolute path or a drive letter would otherwise make the import write
    anywhere the user may write ("Zip Slip").
    """
    parts = PurePosixPath(relative_name).parts
    # ":" covers drive letters ("C:") and NTFS alternate data streams.
    if not parts or any(part in ("..", "") or ":" in part for part in parts):
        raise UnsafeZipEntryError(entry_name)
    base = base_dir.resolve()
    dest = (base / Path(*parts)).resolve()
    if dest == base or not dest.is_relative_to(base):
        raise UnsafeZipEntryError(entry_name)
    return dest


class ZipBackupService:
    """Service to export and import complete app backups including data files and attachments."""

    @staticmethod
    def export_backup_zip(storage_service: StorageService, output_zip_path: Path) -> dict[str, Any]:
        """Packs the data files and the attachments into a zip archive.

        Layout: "data/<file>" for everything in data_dir except attachments,
        backups, logs and temp files; "attachments/<case folder>/<file>" for
        the attachments - each file exactly once.
        """
        storage_service.flush_all_saves()
        config = storage_service.config
        config.ensure_directories()

        data_dir = config.data_dir
        attachments_dir = config.attachments_dir
        backups_dir = config.backups_dir

        file_count = 0
        total_bytes = 0

        with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # 1. Add the data files
            if data_dir.exists():
                for file_path in data_dir.rglob("*"):
                    if not file_path.is_file() or _is_export_noise(file_path, data_dir, attachments_dir, backups_dir):
                        continue
                    rel_path = Path(DATA_DIRNAME) / file_path.relative_to(data_dir)
                    zf.write(file_path, arcname=str(rel_path))
                    file_count += 1
                    total_bytes += file_path.stat().st_size

            # 2. Add all attachments_dir files
            if attachments_dir.exists():
                for file_path in attachments_dir.rglob("*"):
                    if file_path.is_file():
                        rel_path = Path(ATTACHMENTS_DIRNAME) / file_path.relative_to(attachments_dir)
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
    def _plan_import(
        zf: zipfile.ZipFile,
        target_data_dir: Path,
        target_attachments_dir: Path,
    ) -> list[tuple[zipfile.ZipInfo, Path, bool]]:
        """Maps every entry to its destination as (entry, destination, is_attachment).

        Done for the whole archive before anything is written, so an archive
        with a single unsafe entry is rejected as a whole instead of being
        half imported.
        """
        plan: list[tuple[zipfile.ZipInfo, Path, bool]] = []
        for info in zf.infolist():
            if info.is_dir():
                continue

            fn = info.filename.replace("\\", "/")

            if fn.startswith(_DATA_PREFIX):
                rel = fn[len(_DATA_PREFIX):]
                if rel and not rel.endswith(_TEMP_SUFFIX):
                    plan.append((info, _safe_destination(target_data_dir, rel, info.filename), False))
            elif fn.startswith(_ATTACHMENTS_PREFIX):
                rel = fn[len(_ATTACHMENTS_PREFIX):]
                if rel:
                    plan.append((info, _safe_destination(target_attachments_dir, rel, info.filename), True))
            else:
                # Generic root files in zip -> default to target_data_dir
                plan.append((info, _safe_destination(target_data_dir, fn, info.filename), False))
        return plan

    @staticmethod
    def import_backup_zip(
        zip_file_path: Path,
        target_data_dir: Path,
        target_attachments_dir: Path,
    ) -> dict[str, Any]:
        """Unpacks backup zip into specified target_data_dir and target_attachments_dir.

        Raises UnsafeZipEntryError - before writing anything - if an entry
        would land outside the two target folders.
        """
        extracted_data = 0
        extracted_attachments = 0

        with zipfile.ZipFile(zip_file_path, "r") as zf:
            plan = ZipBackupService._plan_import(zf, target_data_dir, target_attachments_dir)

            target_data_dir.mkdir(parents=True, exist_ok=True)
            target_attachments_dir.mkdir(parents=True, exist_ok=True)

            for info, dest, is_attachment in plan:
                dest.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info) as src, open(dest, "wb") as out:
                    shutil.copyfileobj(src, out)
                if is_attachment:
                    extracted_attachments += 1
                else:
                    extracted_data += 1

        return {
            "extracted_data_files": extracted_data,
            "extracted_attachment_files": extracted_attachments,
            "target_data_dir": str(target_data_dir),
            "target_attachments_dir": str(target_attachments_dir),
        }
