from datetime import datetime as dt
import logging
import os
from pathlib import Path
import shutil
import aiofiles.os
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

    type: str = Field(default="folder", description="Type of the entry (file/folder).")
    name: str = Field(..., description="Name of the file/folder.")
    size: str = Field(
        default="0 KB",
        description="Size of the file/folder in human-readable format (e.g. '10 KB').",
    )
    files: list["FolderInfo"] = Field(
        default=[],
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
    def _convert_file_size(size_in_bytes: int | float) -> str:
        """Converts the size of the file to human-readable format (e.g. "10 KB") \n
        Args:
            size_in_bytes (int): The size of the file in bytes.
        Returns:
            str: The size of the file in human-readable format.
                Ex: '10 KB', '5.5 MB', '2.1 GB' etc."""
        units = ["B", "KB", "MB", "GB", "TB", "PB"]
        for unit in units:
            if size_in_bytes < 1024:
                break
            size_in_bytes /= 1024
        return f"{size_in_bytes:.2f} {unit}"
        # kb = size_in_bytes / 1024
        # mb = kb / 1024
        # gb = mb / 1024

        # if gb >= 1:
        #     return "{:.2f} GB".format(gb)
        # elif mb >= 1:
        #     return "{:.2f} MB".format(mb)
        # else:
        #     return "{:.2f} KB".format(kb)

    @staticmethod
    async def _get_file_info(entry: os.DirEntry[str]) -> FolderInfo:
        info = await aiofiles.os.stat(entry.path)
        return FolderInfo(
            type="file",
            name=unicodedata.normalize("NFKD", entry.name),
            size=FilesHandler._convert_file_size(info.st_size),
            created=dt.fromtimestamp(info.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
        )

    # @staticmethod
    # async def _get_folder_info(entry: os.DirEntry[str]) -> FolderInfo:
    #     return FolderInfo(
    #         name=unicodedata.normalize("NFKD", entry.name),
    #         files=await FilesHandler.get_folder_files(entry.path),
    #         created=dt.fromtimestamp(entry.stat().st_ctime).strftime(
    #             "%Y-%m-%d %H:%M:%S"
    #         ),
    #     )

    @staticmethod
    async def get_folder_files(folder_path: str) -> FolderInfo | None:
        """Get information about all files and [sub]folders in a given folder (recursively).\n
        Args:
            folder_path (str): Path of the folder to search.
        Returns:
            - FolderInfo: FolderInfo object representing files and folders inside a given folder.
            - None: If the folder is empty or does not exist."""
        _is_dir = await aiofiles.os.path.isdir(folder_path)
        if not _is_dir:
            return None
        dir_info: list[FolderInfo] = []
        for entry in await aiofiles.os.scandir(folder_path):
            if entry.is_file():
                dir_info.append(await FilesHandler._get_file_info(entry))
            elif entry.is_dir():
                child_dir_info = await FilesHandler.get_folder_files(entry.path)
                if child_dir_info:
                    dir_info.append(child_dir_info)
                # dir_info.append(await FilesHandler.get_folder_files(entry.path))
        # Sort the list of files and folders by name, folders first and then files
        dir_info.sort(key=lambda x: (x.type, x.name))
        # return dir_info
        dir_size = sum(p.stat().st_size for p in Path(folder_path).rglob("*"))
        dir_size_str = FilesHandler._convert_file_size(dir_size)
        return FolderInfo(
            type="folder",
            name=unicodedata.normalize("NFKD", os.path.basename(folder_path)),
            files=dir_info,
            size=dir_size_str,
            created=dt.fromtimestamp(os.path.getctime(folder_path)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        )

    @staticmethod
    def check_media_exists(path: str) -> bool:
        """Check if a media file exists in the specified folder.\n
        Media files are checked based on the following criteria:
        - File size is greater than 100 MB
        - File extension is one of: mp4, mkv, avi, webm\n
        Args:
            path (str): Folder path to check for a media file.\n
        Returns:
            bool: True if a media file exists in the folder, False otherwise."""
        _is_dir = os.path.isdir(path)
        if not _is_dir:
            return False
        for entry in os.scandir(path):
            if entry.is_dir():
                if FilesHandler.check_media_exists(entry.path):
                    return True
            if not entry.is_file():
                continue
            if not entry.name.endswith((".mp4", ".mkv", ".avi", ".webm")):
                continue
            if entry.stat().st_size < 100 * 1024 * 1024:  # 100 MB
                continue
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
            # Check if the directory is named 'Trailers' (case-insensitive)
            if not entry.is_dir():
                continue
            if not entry.name.lower() == "trailers":
                continue
            # Check if any video files exist in the 'trailers' directory
            for sub_entry in await aiofiles.os.scandir(entry.path):
                if not sub_entry.is_file():
                    continue
                if sub_entry.name.endswith((".mp4", ".mkv", ".avi", ".webm")):
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
            if not entry.name.endswith((".mp4", ".mkv", ".avi", ".webm")):
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
            if not entry.name.endswith((".mp4", ".mkv", ".avi", ".webm")):
                continue
            if "-trailer." not in entry.name:
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
            if not entry.name.lower() == "trailers":
                continue
            for sub_entry in await aiofiles.os.scandir(entry.path):
                if not sub_entry.is_file():
                    continue
                if sub_entry.name.endswith((".mp4", ".mkv", ".avi", ".webm")):
                    return sub_entry.path
        return None

    @staticmethod
    async def get_trailer_path(folder_path: str, check_inline_file=False) -> str | None:
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
            trailer_path = await FilesHandler._get_inline_trailer_path(folder_path)
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
        try:
            await aiofiles.os.remove(file_path)
            logging.debug(f"File deleted: {file_path}")
            return True
        except FileNotFoundError:
            logging.error(f"File not found: {file_path}")
            return False
        except Exception as e:
            logging.error(f"Failed to delete file: {file_path}. Exception: {e}")
            return False

    @staticmethod
    async def delete_folder(folder_path: str) -> bool:
        """Delete a folder from the filesystem.\n
        Args:
            folder_path (str): Path to the folder to delete.\n
        Returns:
            bool: True if the folder is deleted successfully, False otherwise."""
        try:
            shutil.rmtree(folder_path)
            logging.debug(f"Folder deleted: {folder_path}")
            return True
        except FileNotFoundError:
            logging.error(f"Folder not found: {folder_path}")
            return False
        except Exception as e:
            logging.error(f"Failed to delete folder: {folder_path}. Exception: {e}")
            return False

    @staticmethod
    async def delete_trailer(folder_path: str) -> bool:
        """Delete a trailer from the specified folder.\n
        Args:
            folder_path (str): Path to the folder containing the trailer file.\n
        Returns:
            bool: True if the trailer is deleted successfully, False otherwise."""
        logging.debug(f"Deleting trailer from folder: {folder_path}")
        if await FilesHandler._check_trailer_as_file(folder_path):
            for entry in await aiofiles.os.scandir(folder_path):
                if not entry.is_file():
                    continue
                if not entry.name.endswith((".mp4", ".mkv", ".avi", ".webm")):
                    continue
                if "-trailer." not in entry.name:
                    continue
                return await FilesHandler.delete_file(entry.path)

        if await FilesHandler._check_trailer_as_folder(folder_path):
            for entry in await aiofiles.os.scandir(folder_path):
                if not entry.is_dir():
                    continue
                if not entry.name.lower() == "trailers":
                    continue
                return await FilesHandler.delete_folder(entry.path)
        return False

    @staticmethod
    async def cleanup_tmp_dir() -> bool:
        """Cleanup any residual files left in the '/tmp' directory.\n
        Returns:
            bool: True if the '/tmp' directory is cleaned up successfully, False otherwise.
        """
        try:
            for entry in await aiofiles.os.scandir("/tmp"):
                if entry.is_file():
                    await FilesHandler.delete_file(entry.path)
                elif entry.is_dir():
                    await FilesHandler.delete_folder(entry.path)
            logging.debug("Temporary directory cleaned up.")
            return True
        except Exception as e:
            logging.error(f"Failed to cleanup temporary directory. Exception: {e}")
            return False
