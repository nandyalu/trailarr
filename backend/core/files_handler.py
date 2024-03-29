from datetime import datetime as dt
import os
import aiofiles.os
from typing import Union
from pydantic import BaseModel, Field
import unicodedata


class FileInfo(BaseModel):
    """Contains information about a file. \n
    Attrs:
        - type (str): Type of the entry (file).
        - name (str): Name of the file.
        - size (str): Size of the file in human-readable format (e.g. "10 KB").
        - created (str): Creation time of the file in "YYYY-MM-DD HH:MM:SS" format."""

    type: str = Field(default="file", description="Type of the entry (file).")
    name: str = Field(..., description="Name of the file.")
    size: str = Field(
        "0 KB",
        description="Size of the file in human-readable format (e.g. '10 KB').",
    )
    created: str = Field(
        ...,
        description="Creation time of the file in 'YYYY-MM-DD HH:MM:SS' format.",
    )


class FolderInfo(BaseModel):
    """Contains information about files and (sub)folders in a given folder. \n
    Attrs:
        - type (str): Type of the entry (folder).
        - name (str): Name of the folder.
        - files (list[FileInfo | FolderInfo]): List of FileInfo or FolderInfo objects
            representing files and folders inside a given folder.
        - created (str): Creation time of the folder in "YYYY-MM-DD HH:MM:SS" format.
    """

    type: str = Field(default="folder", description="Type of the entry (folder).")
    name: str = Field(..., description="Name of the folder.")
    files: list[Union[FileInfo, "FolderInfo"]] = Field(
        ...,
        description="List of FileInfo or FolderInfo objects representing files and folders \
        inside a given folder.",
    )
    created: str = Field(
        ...,
        description="Creation time of the folder in 'YYYY-MM-DD HH:MM:SS' format.",
    )


class FilesHandler:
    """Utility class to handle files and folders."""

    @staticmethod
    def _convert_file_size(size_in_bytes: int) -> str:
        """Converts the size of the file to human-readable format (e.g. "10 KB") \n
        Args:
            size_in_bytes (int): The size of the file in bytes.
        Returns:
            str: The size of the file in human-readable format.
                Ex: '10 KB', '5.5 MB', '2.1 GB' etc."""
        kb = size_in_bytes / 1024
        mb = kb / 1024
        gb = mb / 1024

        if gb >= 1:
            return "{:.2f} GB".format(gb)
        elif mb >= 1:
            return "{:.2f} MB".format(mb)
        else:
            return "{:.2f} KB".format(kb)

    @staticmethod
    async def _get_file_info(entry: os.DirEntry[str]) -> FileInfo:
        info = await aiofiles.os.stat(entry.path)
        return FileInfo(
            name=unicodedata.normalize("NFKD", entry.name),
            size=FilesHandler._convert_file_size(info.st_size),
            created=dt.fromtimestamp(info.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
        )

    @staticmethod
    async def _get_folder_info(entry: os.DirEntry[str]) -> FolderInfo:
        return FolderInfo(
            name=unicodedata.normalize("NFKD", entry.name),
            files=await FilesHandler.get_folder_files(entry.path),
            created=dt.fromtimestamp(entry.stat().st_ctime).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        )

    @staticmethod
    async def get_folder_files(folder_path: str) -> list[FileInfo | FolderInfo]:
        """Get information about all files and [sub]folders in a given folder (recursively).\n
        Args:
            folder_path (str): Path of the folder to search.
        Returns:
            - list[FileInfo | FolderInfo]: List of FileInfo or FolderInfo objects
            representing files and folders inside a given folder."""
        _is_dir = await aiofiles.os.path.isdir(folder_path)
        if not _is_dir:
            return []
        dir_info: list[FileInfo | FolderInfo] = []
        for entry in await aiofiles.os.scandir(folder_path):
            if entry.is_file():
                dir_info.append(await FilesHandler._get_file_info(entry))
            elif entry.is_dir():
                dir_info.append(await FilesHandler._get_folder_info(entry))
        return dir_info

    @staticmethod
    async def _check_trailer_as_folder(path: str) -> bool:
        """Check if a trailer exists in the 'trailers' folder.\n
        Args:
            path (str): Folder path to check for a 'trailers' folder with a trailer file.\n
        Returns:
            bool: True if a trailer exists in the folder, False otherwise."""
        for entry in await aiofiles.os.scandir(path):
            # Check if the directory is named 'Trailers' (case-insensitive)
            if not entry.is_dir():
                continue
            if not entry.name.lower() == "trailers":
                continue
            # Check if any video files exist in the 'trailers' directory
            for sub_entry in await aiofiles.os.scandir(entry.path):
                if not sub_entry.is_file():
                    continue
                if sub_entry.name.endswith((".mp4", ".mkv", ".avi")):
                    return True
        return False

    @staticmethod
    async def _check_trailer_as_file(path: str) -> bool:
        """Check if a trailer file exists in the folder.\n
        Args:
            path (str): Folder path to check for a trailer file.\n
        Returns:
            bool: True if a trailer file exists in the folder, False otherwise."""
        for entry in await aiofiles.os.scandir(path):
            if not entry.is_file():
                continue
            if not entry.name.endswith((".mp4", ".mkv", ".avi")):
                continue
            if "-trailer." not in entry.name:
                continue
            return True
        return False

    @staticmethod
    async def check_trailer_exists(path: str, check_inline_file=False) -> bool:
        """Checks if a trailer exists in the specified folder.\n
        Checks for a file with '-trailer.' in it's name or for a 'trailers' folder\n
        Only checks for video files with extensions '.mp4', '.mkv', '.avi'\n
        Args:
            path (str): The path to the folder to check for a movie trailer.\n
            check_inline_file (bool): If True, check for a trailer file in the given folder and \
            as a seperate file. If False (default), only checks for a 'trailers' folder \
            for a trailer file.\n
        Returns:
            bool: True if a movie trailer exists in the folder, False otherwise."""
        # Check if folder exists
        if not await aiofiles.os.path.isdir(path):
            return False

        # Check for trailer as a folder
        if await FilesHandler._check_trailer_as_folder(path):
            return True

        # Check for trailer as a file
        if check_inline_file:
            if await FilesHandler._check_trailer_as_file(path):
                return True
        return False
