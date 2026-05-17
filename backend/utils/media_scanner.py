from datetime import datetime as dt
import os
from pathlib import Path
import re
import unicodedata
import zoneinfo

import aiofiles.os

from db.models.filefolderinfo import FileFolderInfoCreate, FileFolderType
import db.repos.trailer_profile as trailer_profile_repo


class MediaScanner:
    """Handles scanning of folders and files of media."""

    VIDEO_EXTENSIONS = tuple([".avi", ".mkv", ".mp4", ".webm"])
    TRAILER_MAX_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB

    def __init__(self) -> None:
        self.tz = self._get_system_timezone()
        self.trailer_folders = self.get_trailer_folders()

    @staticmethod
    def _get_system_timezone() -> zoneinfo.ZoneInfo:
        tz_env = os.environ.get("TZ", "UTC")
        return zoneinfo.ZoneInfo(tz_env)

    @staticmethod
    def get_trailer_folders() -> set[str]:
        trailer_folders = trailer_profile_repo.get_trailer_folders()
        trailer_folders.add("trailer")
        trailer_folders.add("trailers")
        return {folder.lower().strip() for folder in trailer_folders}

    def is_trailer_file(self, file_name: str, file_size_bytes: int | None = None) -> bool:
        if not file_name:
            return False
        if not file_name.lower().endswith(self.VIDEO_EXTENSIONS):
            return False
        if re.search(r"s\d{1,2}e\d{1,2}", file_name, re.IGNORECASE):
            return False
        if "trailer" in file_name.lower():
            if file_size_bytes is not None and file_size_bytes >= self.TRAILER_MAX_SIZE_BYTES:
                return False
            return True
        folder_name = Path(file_name).parent.name.lower().strip()
        if folder_name and folder_name in self.trailer_folders:
            return True
        return False

    async def _get_file_info(self, entry: os.DirEntry[str], media_id: int) -> FileFolderInfoCreate:
        info = await aiofiles.os.stat(entry.path)
        is_trailer = self.is_trailer_file(entry.name, info.st_size)
        return FileFolderInfoCreate(
            type=FileFolderType.FILE,
            name=unicodedata.normalize("NFKD", entry.name),
            size=info.st_size,
            path=entry.path,
            modified=dt.fromtimestamp(info.st_ctime, tz=self.tz),
            is_trailer=is_trailer,
            media_id=media_id,
        )

    async def get_folder_files(self, folder_path: str, media_id: int) -> FileFolderInfoCreate | None:
        _is_dir = await aiofiles.os.path.isdir(folder_path)
        if not _is_dir:
            return None
        dir_info: list[FileFolderInfoCreate] = []
        for entry in await aiofiles.os.scandir(folder_path):
            if entry.is_file():
                dir_info.append(await self._get_file_info(entry, media_id))
            elif entry.is_dir():
                child_dir_info = await self.get_folder_files(entry.path, media_id)
                if child_dir_info:
                    dir_info.append(child_dir_info)
        dir_info.sort(key=lambda x: x)
        dir_size = sum(p.stat().st_size for p in Path(folder_path).rglob("*"))
        dir_path = Path(folder_path)
        return FileFolderInfoCreate(
            type=FileFolderType.FOLDER,
            name=unicodedata.normalize("NFKD", dir_path.name),
            children=dir_info,
            size=dir_size,
            path=folder_path,
            modified=dt.fromtimestamp(dir_path.stat().st_ctime, tz=self.tz),
            media_id=media_id,
        )

    def _has_media_file(self, folder_info: FileFolderInfoCreate) -> bool:
        for child in folder_info.children:
            if child.type == FileFolderType.FILE:
                if child.size >= self.TRAILER_MAX_SIZE_BYTES and child.name.lower().endswith(self.VIDEO_EXTENSIONS):
                    return True
            elif child.type == FileFolderType.FOLDER:
                if self._has_media_file(child):
                    return True
        return False

    async def check_media_exists(
        self,
        folder_info: FileFolderInfoCreate | None,
        folder_path: str = "",
        media_id: int = 0,
    ) -> bool:
        if folder_info is None:
            if not folder_path:
                return False
            folder_info = await self.get_folder_files(folder_path, media_id)
            if folder_info is None:
                return False
        return self._has_media_file(folder_info)

    def get_trailer_paths(self, folder_info: FileFolderInfoCreate) -> set[str]:
        trailer_paths: set[str] = set()

        def _scan_folder(info: FileFolderInfoCreate) -> None:
            for child in info.children:
                if child.type == FileFolderType.FILE and child.is_trailer:
                    trailer_paths.add(child.path)
                elif child.type == FileFolderType.FOLDER:
                    _scan_folder(child)

        _scan_folder(folder_info)
        return trailer_paths
