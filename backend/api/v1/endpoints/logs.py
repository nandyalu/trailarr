import collections
from datetime import datetime, timezone
import os
import re

import aiofiles
from aiofiles import os as async_os
from fastapi import APIRouter
from fastapi.responses import FileResponse

from api.v1.models import Log
from app_logger import ModuleLogger
from config.logs.manager import get_all_logs
from config.logs.model import AppLogRecordRead, LogLevel
from config.settings import app_settings

logger = ModuleLogger("LogsAPI")

logs_router = APIRouter(prefix="/logs", tags=["Logs"])


@logs_router.get("/download")
def download_file():
    logs_dir = os.path.abspath(os.path.join(app_settings.app_data_dir, "logs"))
    file_location = f"{logs_dir}/trailarr.log"
    if not os.path.exists(file_location):
        return {"message": "Logs file not found"}
    file_name = f"trailarr_logs_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
    return FileResponse(file_location, media_type="application/octet-stream", filename=file_name)


@logs_router.get("/raw")
async def get_raw_logs(
    level: LogLevel = LogLevel.INFO,
    offset: int = 0,
    limit: int = 1000,
    filter: str | None = None,
) -> list[AppLogRecordRead]:
    return await get_all_logs(level=level, offset=offset, limit=limit, filter=filter)


@logs_router.get("/", deprecated=True)
async def get_logs(page: int = 0, limit: int = 1000) -> list[Log]:
    logs_dir = os.path.abspath(os.path.join(app_settings.app_data_dir, "logs"))
    logs: collections.deque = collections.deque(maxlen=limit)
    if not await async_os.path.exists(logs_dir):
        return [
            Log(
                datetime=f"{datetime.now(timezone.utc)}",
                level="INFO",
                filename="Other",
                lineno=1,
                module="Other",
                message="No Logs Found",
                raw_log="No Logs Found",
            )
        ]
    log_ext = ".log"
    if page > 0:
        log_ext = f".log.{page}"
    for log_file in await async_os.listdir(logs_dir):
        if log_file.endswith(log_ext):
            file = await aiofiles.open(f"{logs_dir}/{log_file}", mode="r")
            async for line in file:
                logs.append(_convert_log(line))
    logs.reverse()
    return list(logs)


_LOG_REGEX = re.compile(
    r"^(?P<datetime>[^\s]+)\s\[(?P<level>[^\|]+)\|(?P<filename>[^\|]+)\|L(?P<lineno>\d+)\]"
    r":\s(?P<message>.*)$"
)
_LOG_MSG_REGEX = re.compile(r"^(?P<module>[\w]+):\s(?P<message>.*)$")


def _convert_log(log: str) -> Log:
    match_log = _LOG_REGEX.search(log)
    if match_log:
        module = "Other"
        message = match_log.group("message")
        match_module = _LOG_MSG_REGEX.search(message)
        if message.lower().startswith("job"):
            module = "Tasks"
        if match_module:
            module = match_module.group("module")
            message = match_module.group("message")
        return Log(
            datetime=match_log.group("datetime"),
            level=match_log.group("level"),
            filename=match_log.group("filename"),
            lineno=int(match_log.group("lineno")),
            module=module,
            message=message,
            raw_log=log,
        )
    return Log(
        datetime=f"{datetime.now(timezone.utc)}",
        level="INFO",
        filename="Other",
        lineno=1,
        module="Other",
        message=log,
        raw_log=log,
    )
