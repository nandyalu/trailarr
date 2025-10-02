import asyncio
from datetime import datetime as dt
import hashlib
import os
from pathlib import Path
import re
import shutil
import aiofiles.os
from pydantic import BaseModel, Field
import unicodedata

from app_logger import ModuleLogger
from core.base.database.manager import trailerprofile

logger = ModuleLogger("FilesHandler")


class FileInfo(BaseModel):
    """Contains information about a file. \n
    Attrs:
        - type (str): Type of the entry (file).
        - name (str): Name of the file.
        - size (str): Size of the file in human-readable format (e.g. "10 KB").
        - created (str): Creation time of the file in "YYYY-MM-DD HH:MM:SS"
            format.
    """

    type: str = Field(default="file", description="Type of the entry (file).")
    name: str = Field(..., description="Name of the file.")
    size: str = Field(
        "0 KB",
        description=(
            "Size of the file in human-readable format (e.g. '10 KB')."
        ),
    )
    created: str = Field(
        ...,
        description=(
            "Creation time of the file in 'YYYY-MM-DD HH:MM:SS' format."
        ),
    )


class FolderInfo(BaseModel):
    """Contains information about files and (sub)folders in a given folder. \n
    Attrs:
        - type (str): Type of the entry (folder).
        - name (str): Name of the folder.
        - files (list[FileInfo | FolderInfo]): List of FileInfo or FolderInfo
            objects representing files and folders inside a given folder.
        - created (str): Creation time of the folder in "YYYY-MM-DD HH:MM:SS"
            format.
    """

    type: str = Field(
        default="folder", description="Type of the entry (file/folder)."
    )
    name: str = Field(..., description="Name of the file/folder.")
    size: str = Field(
        default="0 KB",
        description=(
            "Size of the file/folder in human-readable format (e.g. '10 KB')."
        ),
    )
    path: str = Field(
        ...,
        description="Path of the file/folder.",
    )
    files: list["FolderInfo"] = Field(
        default=[],
        description=(
            "List of FileInfo or FolderInfo objects representing files and"
            " folders         inside a given folder."
        ),
    )
    created: str = Field(
        ...,
        description=(
            "Creation time of the folder in 'YYYY-MM-DD HH:MM:SS' format."
        ),
    )

    def __lt__(self, other: "FileInfo"):
        if self.type == other.type:
            # If both are of the same type, sort by name
            return self.name < other.name
        type_values = {"file": 2, "folder": 1, "symlink": 1}
        if self.type not in type_values or other.type not in type_values:
            # If either type is not in the type_values, fallback to name comparison
            return self.name < other.name
        # Different types, sort by type
        # 'folder' < 'symlink' < 'file'
        return type_values[self.type] < type_values[other.type]


class FilesHandler:
    """Utility class to handle files and folders."""

    VIDEO_EXTENSIONS = tuple([".avi", ".mkv", ".mp4", ".webm"])

    @staticmethod
    def _convert_file_size(size_in_bytes: int | float) -> str:
        """Converts the size of the file to human-readable format (e.g. "10 KB")
        Args:
            size_in_bytes (int): The size of the file in bytes.
        Returns:
            str: The size of the file in human-readable format.
                Ex: '10 KB', '5.5 MB', '2.1 GB' etc."""
        units = ["B", "KB", "MB", "GB", "TB", "PB"]
        unit = "B"
        for unit in units:
            if size_in_bytes < 1024:
                break
            size_in_bytes /= 1024
        return f"{size_in_bytes:.2f} {unit}"

    @staticmethod
    async def _get_file_info(entry: os.DirEntry[str]) -> FolderInfo:
        info = await aiofiles.os.stat(entry.path)
        return FolderInfo(
            type="file",
            name=unicodedata.normalize("NFKD", entry.name),
            size=FilesHandler._convert_file_size(info.st_size),
            path=entry.path,
            created=dt.fromtimestamp(info.st_ctime).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        )

    @staticmethod
    async def get_folder_files(folder_path: str) -> FolderInfo | None:
        """Get information about all files and [sub]folders in a given \
            folder (recursively).\n
        Args:
            folder_path (str): Path of the folder to search.
        Returns:
            FolderInfo|None:
                - FolderInfo object representing files and folders \
                    inside a given folder.
                - None: If the folder is empty or does not exist."""
        _is_dir = await aiofiles.os.path.isdir(folder_path)
        if not _is_dir:
            return None
        dir_info: list[FolderInfo] = []
        for entry in await aiofiles.os.scandir(folder_path):
            if entry.is_file():
                dir_info.append(await FilesHandler._get_file_info(entry))
            elif entry.is_dir():
                child_dir_info = await FilesHandler.get_folder_files(
                    entry.path
                )
                if child_dir_info:
                    dir_info.append(child_dir_info)

        # Sort the list of files and folders by name, folders first and \
        # then files
        dir_info.sort(key=lambda x: x)
        # return dir_info
        dir_size = sum(p.stat().st_size for p in Path(folder_path).rglob("*"))
        dir_size_str = FilesHandler._convert_file_size(dir_size)
        return FolderInfo(
            type="folder",
            name=unicodedata.normalize("NFKD", os.path.basename(folder_path)),
            files=dir_info,
            size=dir_size_str,
            path=folder_path,
            created=dt.fromtimestamp(os.path.getctime(folder_path)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        )

    @staticmethod
    async def _get_file_fol_info(entry: os.DirEntry[str]) -> FolderInfo:
        """Get information about a file or folder.\n
        Args:
            entry (os.DirEntry): An entry from the filesystem. \n
        Returns:
            FolderInfo: FolderInfo object representing the file or folder."""
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
            created=dt.fromtimestamp(info.st_ctime).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            name=unicodedata.normalize("NFKD", entry.name),
            path=entry.path,
            size=FilesHandler._convert_file_size(_size),
            type=_type,
        )

    @staticmethod
    async def get_folder_files_simple(folder_path: str) -> list[FolderInfo]:
        """Get information about all files and folders in a given \
            folder (non-recursive).\n
        Args:
            folder_path (str): Path of the folder to search.
        Returns:
            list[FolderInfo]: List of FolderInfo objects representing files and folders \
                inside a given folder."""
        _is_dir = await aiofiles.os.path.isdir(folder_path)
        if not _is_dir:
            return []
        dir_info: list[FolderInfo] = []
        for entry in await aiofiles.os.scandir(folder_path):
            dir_info.append(await FilesHandler._get_file_fol_info(entry))
        # Sort the list of files and folders by created, folders first and then files
        dir_info.sort(key=lambda x: x)
        return dir_info

    @staticmethod
    def check_folder_exists(path: str) -> bool:
        """Check if a folder exists in the specified path.\n
        Args:
            path (str): Path to the folder to check.\n
        Returns:
            bool: True if the folder exists, False otherwise.
        """
        return os.path.isdir(path)

    @staticmethod
    def check_media_exists(path: str) -> bool:
        """Check if a media file exists in the specified folder.\n
        Media files are checked based on the following criteria:
        - File size is greater than 100 MB
        - File extension is one of: mp4, mkv, avi, webm\n
        Args:
            path (str): Folder path to check for a media file.\n
        Returns:
            bool: True if a media file exists in the folder, False otherwise.
        """
        _is_dir = os.path.isdir(path)
        if not _is_dir:
            return False
        for entry in os.scandir(path):
            if entry.is_dir():
                if FilesHandler.check_media_exists(entry.path):
                    return True
            if not entry.is_file():
                continue
            if not entry.name.endswith(FilesHandler.VIDEO_EXTENSIONS):
                continue
            if entry.stat().st_size < 100 * 1024 * 1024:  # 100 MB
                continue
            return True
        return False

    @staticmethod
    def is_video_file(file_name: str) -> bool:
        """Check if a file is a video file based on its name.\n
        Args:
            file_name (str): Name of the file to check.\n
        Returns:
            bool: True if the file is a video, False otherwise."""
        if not file_name:
            return False
        if not file_name.lower().endswith(FilesHandler.VIDEO_EXTENSIONS):
            return False
        return True

    @staticmethod
    def is_trailer_file(file_name: str) -> bool:
        """Check if a file is a trailer file based on its name.\n
        Args:
            file_name (str): Name of the file to check.\n
        Returns:
            bool: True if the file is a trailer, False otherwise."""
        if not FilesHandler.is_video_file(file_name):
            return False
        # Ensure file is not an episode file
        if re.search(r"s\d{1,2}e\d{1,2}", file_name, re.IGNORECASE):
            return False
        # Check if the file name contains 'trailer'
        if "trailer" in file_name.lower():
            return True
        return False

    @staticmethod
    def get_trailer_folders() -> set[str]:
        """Get a list of trailer folder names.\n
        Returns:
            set[str]: Set with trailer folder names."""
        # Get the trailer folders from the trailerprofile module
        trailer_folders = trailerprofile.get_trailer_folders()
        # Add 'trailer' and 'trailers' to the list
        trailer_folders.add("trailer")
        trailer_folders.add("trailers")
        trailer_folders = {
            folder.lower().strip() for folder in trailer_folders
        }
        return trailer_folders

    @staticmethod
    def is_trailer_folder(folder_name: str) -> bool:
        """Check if a folder is a trailer folder based on its name.\n
        Args:
            folder_name (str): Name of the folder to check.\n
        Returns:
            bool: True if the folder is a trailer, False otherwise."""
        if not folder_name:
            return False
        # Check if the folder name contains 'trailer'
        if folder_name.lower().strip() in FilesHandler.get_trailer_folders():
            return True
        return False

    @staticmethod
    async def _check_trailer_as_folder(path: str) -> bool:
        """Check if a trailer exists in the 'trailers' folder.\n
        Args:
            path (str): Folder path to check for a 'trailers' folder with a trailer file.\n
        Returns:
            bool: True if a trailer exists in the folder, False otherwise."""
        for entry in await aiofiles.os.scandir(path):
            # Check if the directory matches any of the trailers (case-insensitive)
            if not entry.is_dir():
                continue
            if not FilesHandler.is_trailer_folder(entry.name):
                continue
            # Check if 'trailer' exists in the 'trailers' directory
            if await FilesHandler._check_trailer_as_file(entry.path):
                return True
        # No trailer folder or no trailer file found
        return False

    @staticmethod
    async def _check_trailer_as_file(path: str) -> bool:
        """Check if a trailer file exists in the folder.\n
        Args:
            path (str): Folder path to check for a trailer file.\n
        Returns:
            bool: True if a trailer file exists in the folder, False otherwise.
        """
        for entry in await aiofiles.os.scandir(path):
            if not entry.is_file():
                continue
            if FilesHandler.is_trailer_file(entry.name):
                return True
        return False

    @staticmethod
    async def check_trailer_exists(path: str, check_inline_file=False) -> bool:
        """Checks if a trailer exists in the specified folder.\n
        Checks for a file with '-trailer.' in it's name or for a 'trailers' folder\n
        Only checks for video files with extensions '.mp4', '.mkv', '.avi'\n
        Args:
            path (str): The path to the folder to check for a trailer.\n
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

    @staticmethod
    def check_file_exists(folder_path: str, file_name: str) -> bool:
        """Check if a file exists in the specified folder.\n
        Args:
            folder_path (str): Path to the folder to check for the file.\n
            file_name (str): Name of the file to check for.\n
        Returns:
            bool: True if the file exists in the folder, False otherwise."""
        # Check if folder exists
        if not os.path.isdir(folder_path):
            return False

        # Check for file in the folder
        for entry in os.scandir(folder_path):
            if entry.is_dir():
                return FilesHandler().check_file_exists(entry.path, file_name)
            if entry.name == file_name:
                return True
        return False

    @staticmethod
    async def _get_inline_trailer_path(folder_path: str) -> str | None:
        """Get the path to the trailer file in the specified folder.\n
        Args:
            folder_path (str): Path to the folder containing the trailer file.\n
        Returns:
            str | None: Path to the trailer file if it exists, otherwise an empty string. \
                None if the folder does not exist or the trailer file is not found.
            """
        # Check if folder exists
        if not await aiofiles.os.path.isdir(folder_path):
            return None

        # Check for trailer as a file
        for entry in await aiofiles.os.scandir(folder_path):
            if not entry.is_file():
                continue
            if not FilesHandler.is_trailer_file(entry.name):
                continue
            return entry.path
        return None

    @staticmethod
    async def _get_folder_trailer_path(folder_path: str) -> str | None:
        """Get the path to the trailer file in the specified folder.\n
        Args:
            folder_path (str): Path to the folder containing the trailer file.\n
        Returns:
            str | None: Path to the trailer file if it exists, otherwise an empty string. \
                None if the folder does not exist or the trailer file is not found.
            """
        # Check if folder exists
        if not await aiofiles.os.path.isdir(folder_path):
            return None

        # Check for trailer as a folder
        for entry in await aiofiles.os.scandir(folder_path):
            if not entry.is_dir():
                continue
            if not FilesHandler.is_trailer_folder(entry.name):
                continue
            for sub_entry in await aiofiles.os.scandir(entry.path):
                if not sub_entry.is_file():
                    continue
                # Return file with `trailer` in name (if exists)
                if FilesHandler.is_trailer_file(sub_entry.name):
                    return sub_entry.path
                # Return video file path (if exists)
                if FilesHandler.is_video_file(sub_entry.name):
                    return sub_entry.path
        return None

    @staticmethod
    async def get_trailer_path(
        folder_path: str, check_inline_file=False
    ) -> str | None:
        """Get the path to the trailer file in the specified folder.\n
        Args:
            folder_path (str): Path to the folder containing the trailer file.\n
            check_inline_file (bool): If True, check for a trailer file in the given folder and \
            as a seperate file. If False (default), only checks for a 'trailers' folder \
            for a trailer file.\n
        Returns:
            str | None: Path to the trailer file if it exists, otherwise an empty string. \
                None if the folder does not exist or the trailer file is not found.
            """
        # Check if folder exists
        if not await aiofiles.os.path.isdir(folder_path):
            return None

        # Check for trailer in 'trailers' folder
        trailer_path = await FilesHandler._get_folder_trailer_path(folder_path)
        if trailer_path:
            return trailer_path

        # Check for trailer as an inline file, if specified
        if check_inline_file:
            trailer_path = await FilesHandler._get_inline_trailer_path(
                folder_path
            )
            if trailer_path:
                return trailer_path
        return None

    @staticmethod
    async def delete_file(file_path: str) -> bool:
        """Delete a file from the filesystem.\n
        Args:
            file_path (str): Path to the file to delete.\n
        Returns:
            bool: True if the file is deleted successfully, False otherwise."""
        # Make sure the path is at least 2 levels deep from the root
        if file_path.count("/") < 3:
            logger.error(f"Cannot delete top level file: {file_path}")
            return False
        try:
            await aiofiles.os.remove(file_path)
            logger.debug(f"File deleted: {file_path}")
            return True
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete file: {file_path}. Exception: {e}")
            return False

    @staticmethod
    async def delete_folder(folder_path: str) -> bool:
        """Delete a folder from the filesystem.\n
        Args:
            folder_path (str): Path to the folder to delete. \
                Should be at least 3 folders deep from root. \n
        Returns:
            bool: True if the folder is deleted successfully, False otherwise."""
        # Make sure we are not deleting the root folder or a top level folder
        if (
            folder_path == "/"
            or folder_path == ""
            or folder_path.count("/") < 3
        ):
            logger.error(f"Cannot delete root folder: {folder_path}")
            return False
        # Make sure the path is at least 3 levels deep from the root
        if folder_path.count("/") < 3:
            logger.error(f"Cannot delete top level folder: {folder_path}")
            return False
        try:
            shutil.rmtree(folder_path)
            logger.debug(f"Folder deleted: {folder_path}")
            return True
        except FileNotFoundError:
            logger.error(f"Folder not found: {folder_path}")
            return False
        except Exception as e:
            logger.error(
                f"Failed to delete folder: {folder_path}. Exception: {e}"
            )
            return False

    @staticmethod
    async def delete_trailer(folder_path: str) -> bool:
        """Delete a trailer from the specified folder.\n
        Args:
            folder_path (str): Path to the folder containing the trailer file.\n
        Returns:
            bool: True if the trailer is deleted successfully, False otherwise.
        """
        logger.debug(f"Deleting trailer from folder: {folder_path}")
        # Check for an inline trailer and delete
        trailer_path = await FilesHandler._get_inline_trailer_path(folder_path)
        if trailer_path:
            return await FilesHandler.delete_file(trailer_path)
        # Check for a trailer in the 'trailers' folder and delete
        trailer_path = await FilesHandler._get_folder_trailer_path(folder_path)
        if trailer_path:
            return await FilesHandler.delete_file(trailer_path)
        return False

    @staticmethod
    async def cleanup_tmp_dir() -> bool:
        """Cleanup any residual files left in the '/tmp' directory.\n
        Returns:
            bool: True if the '/tmp' directory is cleaned up successfully, False otherwise.
        """
        try:
            tmp_dir = "/var/lib/trailarr/tmp"
            if not os.path.exists(tmp_dir):
                tmp_dir = "/app/tmp"

            for entry in await aiofiles.os.scandir(tmp_dir):
                if entry.is_file():
                    await FilesHandler.delete_file(entry.path)
                elif entry.is_dir():
                    await FilesHandler.delete_folder(entry.path)
            logger.debug("Temporary directory cleaned up.")
            return True
        except Exception as e:
            logger.error(
                f"Failed to cleanup temporary directory. Exception: {e}"
            )
            return False

    @staticmethod
    async def scan_root_folders_for_trailers(root_media_dir: str) -> set[str]:
        """Find all folders containing trailers in the specified root folders.\n
        Finds trailers in the media folder and also in a 'trailer' folder\n
        Args:
            root_media_dir (str): The root directory to search for trailers.\n
        Returns:
            set[str]: Set of folder paths containing trailers."""
        logger.debug(f"Scanning '{root_media_dir}' for trailers.")
        if not FilesHandler.check_folder_exists(root_media_dir):
            logger.warning(
                f"Root media directory '{root_media_dir}' is not a directory."
            )
            return set()
        inline_trailers = set()
        folder_trailers = set()
        count = 0
        tasks = []
        media_folders = []

        semaphore = asyncio.Semaphore(10)  # Limit scanning 10 files at a time

        async def bounded(coro):
            async with semaphore:
                return await coro

        # Scan each immediate subfolder (media folder) in the root directory
        for media_folder in await aiofiles.os.scandir(root_media_dir):
            if not media_folder.is_dir():
                continue
            count += 1
            media_folders.append(media_folder)
            # Launch both checks concurrently for each media folder
            tasks.append(
                bounded(
                    FilesHandler._get_inline_trailer_path(media_folder.path)
                )
            )
            tasks.append(
                bounded(
                    FilesHandler._get_folder_trailer_path(media_folder.path)
                )
            )

        results = await asyncio.gather(*tasks)
        for idx, media_folder in enumerate(media_folders):
            inline_result = results[idx * 2]
            folder_result = results[idx * 2 + 1]
            if inline_result:
                inline_trailers.add(media_folder.path)
            if folder_result:
                folder_trailers.add(media_folder.path)
        msg = (
            f"Scanned Root folder '{root_media_dir}' ({count} media folders): "
            f"Found {len(folder_trailers)} (folder) and"
            f" {len(inline_trailers)} (inline) trailers."
        )
        logger.info(msg)
        return inline_trailers.union(folder_trailers)

    @staticmethod
    async def rename_file_fol(old_path: str, new_path: str) -> bool:
        """Rename a file or folder.\n
        Args:
            old_path (str): Path of the file/folder to rename.
            new_path (str): New path of the file/folder.
        Returns:
            bool: True if the file/folder is renamed successfully, False otherwise.
        """
        try:
            await aiofiles.os.rename(old_path, new_path)
            logger.debug(f"File/Folder renamed: {old_path} -> {new_path}")
            return True
        except FileNotFoundError:
            logger.error(f"File/Folder not found: {old_path}")
            return False
        except Exception as e:
            logger.error(
                f"Failed to rename file/folder: {old_path}. Exception: {e}"
            )
            return False

    @staticmethod
    async def delete_file_fol(path: str) -> bool:
        """Delete a file or folder from the filesystem.\n
        Args:
            path (str): Path to the file/folder to delete.\n
        Returns:
            bool: True if the file/folder is deleted successfully, False otherwise.
        """
        # Check if the path is a file or folder
        _is_dir = await aiofiles.os.path.isdir(path)
        if _is_dir:
            return await FilesHandler.delete_folder(path)
        else:
            return await FilesHandler.delete_file(path)

    @staticmethod
    def compute_file_hash(file_path) -> str:
        """Compute the SHA-256 hash of a file.\n
        Args:
            file_path (str): Path to the file to compute the hash for.\n
        Returns:
            str: SHA-256 hash of the file as a hexadecimal string.
        Raises:
            FileNotFoundError: If the file does not exist.
            PermissionError: If the file is not readable.
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        if not os.access(file_path, os.R_OK):
            raise PermissionError(f"Permission denied: {file_path}")
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
