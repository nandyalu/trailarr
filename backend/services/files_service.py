"""Files service — FilesHandler filesystem utilities and trailer delete action.

FilesHandler operates on the filesystem only.
delete_trailer_download() is a service action that deletes the file and marks
the Download record, so it lives here rather than in FilesHandler itself.
"""
from datetime import datetime as dt
import hashlib
import os
import re
import shutil
import string
import sys
import unicodedata
import zoneinfo

import aiofiles.os
from pydantic import BaseModel, Field

import db.repos.download as download_repo
from app_logger import ModuleLogger

logger = ModuleLogger("FilesService")


class FolderInfo(BaseModel):
    type: str = Field(default="folder")
    name: str
    size: str = Field(default="0 KB")
    path: str
    files: list["FolderInfo"] = Field(default=[])
    created: str

    def __lt__(self, other: "FolderInfo"):
        if self.type == other.type:
            return self.name < other.name
        type_values = {"file": 2, "folder": 1, "symlink": 1}
        if self.type not in type_values or other.type not in type_values:
            return self.name < other.name
        return type_values[self.type] < type_values[other.type]


class FilesHandler:
    VIDEO_EXTENSIONS = tuple([".avi", ".mkv", ".mp4", ".webm"])
    TRAILER_MAX_SIZE_BYTES = 250 * 1024 * 1024  # 250 MB

    @staticmethod
    def _convert_file_size(size_in_bytes: int | float) -> str:
        units = ["B", "KB", "MB", "GB", "TB", "PB"]
        unit = "B"
        for unit in units:
            if size_in_bytes < 1024:
                break
            size_in_bytes /= 1024
        return f"{size_in_bytes:.2f} {unit}"

    @staticmethod
    def _get_system_timezone():
        return zoneinfo.ZoneInfo(os.environ.get("TZ", "UTC"))

    @staticmethod
    def _format_dt(timestamp: float) -> str:
        return dt.fromtimestamp(timestamp, tz=FilesHandler._get_system_timezone()).isoformat()

    @staticmethod
    async def _get_file_fol_info(entry: os.DirEntry) -> FolderInfo:
        info = await aiofiles.os.stat(entry.path)
        _type = "folder"
        _size = 0
        if entry.is_dir():
            _type = "folder"
        elif entry.is_file():
            _type = "file"
            _size = info.st_size
        elif entry.is_symlink():
            _type = "symlink"
        return FolderInfo(
            created=FilesHandler._format_dt(info.st_ctime),
            name=unicodedata.normalize("NFKD", entry.name),
            path=entry.path,
            size=FilesHandler._convert_file_size(_size),
            type=_type,
        )

    @staticmethod
    def _list_windows_drives() -> list[FolderInfo]:
        import ctypes
        bitmask: int = ctypes.windll.kernel32.GetLogicalDrives()  # type: ignore
        drives: list[FolderInfo] = []
        for i, letter in enumerate(string.ascii_uppercase):
            if bitmask & (1 << i):
                drive = f"{letter}:/"
                drives.append(FolderInfo(type="folder", name=f"{letter}:", path=drive, size="0 KB", created=""))
        return drives

    @staticmethod
    async def get_folder_files_simple(folder_path: str) -> list[FolderInfo]:
        if sys.platform == "win32":
            folder_path = folder_path.replace("\\", "/")
            if folder_path in ("/", ""):
                return FilesHandler._list_windows_drives()
        if not await aiofiles.os.path.isdir(folder_path):
            return []
        dir_info: list[FolderInfo] = []
        for entry in await aiofiles.os.scandir(folder_path):
            dir_info.append(await FilesHandler._get_file_fol_info(entry))
        dir_info.sort()
        return dir_info

    @staticmethod
    def check_folder_exists(path: str) -> bool:
        return os.path.isdir(path)

    @staticmethod
    def check_media_exists(path: str) -> bool:
        if not os.path.isdir(path):
            return False
        for entry in os.scandir(path):
            if entry.is_dir():
                if FilesHandler.check_media_exists(entry.path):
                    return True
            if not entry.is_file():
                continue
            if not entry.name.endswith(FilesHandler.VIDEO_EXTENSIONS):
                continue
            if entry.stat().st_size < 100 * 1024 * 1024:
                continue
            return True
        return False

    @staticmethod
    def is_video_file(file_name: str) -> bool:
        return bool(file_name) and file_name.lower().endswith(FilesHandler.VIDEO_EXTENSIONS)

    @staticmethod
    def is_trailer_file(file_name: str, file_size_bytes: int | None = None) -> bool:
        if not FilesHandler.is_video_file(file_name):
            return False
        if re.search(r"s\d{1,2}e\d{1,2}", file_name, re.IGNORECASE):
            return False
        if "trailer" in file_name.lower():
            if file_size_bytes is not None and file_size_bytes >= FilesHandler.TRAILER_MAX_SIZE_BYTES:
                return False
            return True
        return False

    @staticmethod
    def get_trailer_folders() -> set[str]:
        from db.repos.trailer_profile import get_trailer_folders
        folders = get_trailer_folders()
        folders.add("trailer")
        folders.add("trailers")
        return {f.lower().strip() for f in folders}

    @staticmethod
    def is_trailer_folder(folder_name: str) -> bool:
        return bool(folder_name) and folder_name.lower().strip() in FilesHandler.get_trailer_folders()

    @staticmethod
    async def _check_trailer_as_folder(path: str) -> bool:
        for entry in await aiofiles.os.scandir(path):
            if not entry.is_dir() or not FilesHandler.is_trailer_folder(entry.name):
                continue
            if await FilesHandler._check_trailer_as_file(entry.path):
                return True
        return False

    @staticmethod
    async def _check_trailer_as_file(path: str) -> bool:
        for entry in await aiofiles.os.scandir(path):
            if entry.is_file() and FilesHandler.is_trailer_file(entry.name, entry.stat().st_size):
                return True
        return False

    @staticmethod
    async def check_trailer_exists(path: str, check_inline_file: bool = False) -> bool:
        if not await aiofiles.os.path.isdir(path):
            return False
        if await FilesHandler._check_trailer_as_folder(path):
            return True
        if check_inline_file and await FilesHandler._check_trailer_as_file(path):
            return True
        return False

    @staticmethod
    async def _get_inline_trailer_path(folder_path: str) -> str | None:
        if not await aiofiles.os.path.isdir(folder_path):
            return None
        for entry in await aiofiles.os.scandir(folder_path):
            if entry.is_file() and FilesHandler.is_trailer_file(entry.name, entry.stat().st_size):
                return entry.path
        return None

    @staticmethod
    async def delete_trailers_for_media(folder_path: str) -> bool:
        if not await aiofiles.os.path.isdir(folder_path):
            return False
        deleted = False
        inline = await FilesHandler._get_inline_trailer_path(folder_path)
        if inline and await FilesHandler.delete_file(inline):
            deleted = True
        for entry in await aiofiles.os.scandir(folder_path):
            if entry.is_dir() and FilesHandler.is_trailer_folder(entry.name):
                if await FilesHandler.delete_folder(entry.path):
                    deleted = True
        return deleted

    @staticmethod
    async def delete_file(file_path: str) -> bool:
        if file_path.count("/") < 3:
            logger.error(f"Cannot delete top level file: {file_path}")
            return False
        try:
            await aiofiles.os.remove(file_path)
            return True
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False

    @staticmethod
    async def delete_folder(folder_path: str) -> bool:
        if not folder_path or folder_path == "/" or folder_path.count("/") < 3:
            logger.error(f"Cannot delete root/top-level folder: {folder_path}")
            return False
        try:
            shutil.rmtree(folder_path)
            return True
        except FileNotFoundError:
            logger.error(f"Folder not found: {folder_path}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete folder {folder_path}: {e}")
            return False

    @staticmethod
    async def rename_file_fol(old_path: str, new_path: str) -> bool:
        try:
            await aiofiles.os.rename(old_path, new_path)
            return True
        except FileNotFoundError:
            logger.error(f"File/Folder not found: {old_path}")
            return False
        except Exception as e:
            logger.error(f"Failed to rename {old_path}: {e}")
            return False

    @staticmethod
    async def delete_file_fol(path: str) -> bool:
        if await aiofiles.os.path.isdir(path):
            return await FilesHandler.delete_folder(path)
        return await FilesHandler.delete_file(path)

    @staticmethod
    def compute_file_hash(file_path: str) -> str:
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        if not os.access(file_path, os.R_OK):
            raise PermissionError(f"Permission denied: {file_path}")
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()


async def delete_trailer_download(trailer_path: str, download_id: int) -> None:
    """Delete the trailer file from disk and mark its Download record as deleted."""
    await FilesHandler.delete_file(trailer_path)
    download_repo.mark_as_deleted(download_id)
