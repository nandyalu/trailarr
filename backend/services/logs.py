"""Reading and parsing the log files on disk.

The database-backed log reader lives in `config/logs/manager.py`. This
module is for the files themselves: the download, and the older endpoint
that reads and parses `trailarr.log`.

Functions here give back plain dictionaries, not API models. `Log` is a
response model in `api/v1/models.py`, and a service must not import the api
layer to build one — the handler maps the fields.
"""

import collections
import os
import re
from datetime import datetime, timezone

import aiofiles
from aiofiles import os as async_os

from app_logger import ModuleLogger
from config.settings import app_settings

logger = ModuleLogger("LogsAPI")

LOG_REGEX = re.compile(
    r"^(?P<datetime>[^\s]+)\s\[(?P<level>[^\|]+)\|(?P<filename>[^\|]+)\|L(?P<lineno>\d+)\]"
    r":\s(?P<message>.*)$"
)
LOG_MSG_REGEX = re.compile(r"^(?P<module>[\w]+):\s(?P<message>.*)$")


def logs_dir() -> str:
    """The folder that holds the log files."""
    return os.path.abspath(os.path.join(app_settings.app_data_dir, "logs"))


def log_file_to_download() -> str | None:
    """The path of the current log file, or None when there is none yet."""
    file_location = f"{logs_dir()}/trailarr.log"
    if not os.path.exists(file_location):
        return None
    return file_location


def download_file_name() -> str:
    """A file name for the download, stamped with the current time."""
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f"trailarr_logs_{stamp}.log"


def parse_log_line(log: str) -> dict:
    """Split one log line into its fields.

    A line that does not match the format becomes an INFO record that keeps
    the whole line as the message, so nothing is dropped.

    Args:
        log (str): The raw line.

    Returns:
        dict: The fields of a log record.
    """
    match_log = LOG_REGEX.search(log)
    if match_log:
        module = "Other"
        message = match_log.group("message")
        match_module = LOG_MSG_REGEX.search(message)
        if message.lower().startswith("job"):
            module = "Tasks"
        if match_module:
            module = match_module.group("module")
            message = match_module.group("message")
        return {
            "datetime": match_log.group("datetime"),
            "level": match_log.group("level"),
            "filename": match_log.group("filename"),
            "lineno": int(match_log.group("lineno")),
            "module": module,
            "message": message,
            "raw_log": log,
        }
    return {
        "datetime": f"{datetime.now(timezone.utc)}",
        "level": "INFO",
        "filename": "Other",
        "lineno": 1,
        "module": "Other",
        "message": log,
        "raw_log": log,
    }


def no_logs_record() -> dict:
    """The single record returned when the logs folder is missing."""
    return {
        "datetime": f"{datetime.now(timezone.utc)}",
        "level": "INFO",
        "filename": "Other",
        "lineno": 1,
        "module": "Other",
        "message": "No Logs Found",
        "raw_log": "No Logs Found",
    }


async def read_logs(page: int = 0, limit: int = 1000) -> list[dict]:
    """Read the log files and parse every line.

    Page 0 reads the current file. A higher page reads the rotated file with
    that number.

    Args:
        page (int): Which rotated file to read. 0 is the current one.
        limit (int): The most records to keep, counted from the end.

    Returns:
        list[dict]: The records, newest first.
    """
    directory = logs_dir()
    logs: collections.deque = collections.deque(maxlen=limit)
    if not await async_os.path.exists(directory):
        logger.info("Logs directory does not exist")
        return [no_logs_record()]
    log_ext = ".log"
    if page > 0:
        # If page is greater than 0, then read logs from the log file with page number
        log_ext = f".log.{page}"
    for log_file in await async_os.listdir(directory):
        if log_file.endswith(log_ext):
            file = await aiofiles.open(f"{directory}/{log_file}", mode="r")
            async for line in file:
                logs.append(parse_log_line(line))

    logs.reverse()
    return list(logs)
