"""Read the log, from the database or from the files on disk."""

from fastapi import APIRouter
from fastapi.responses import FileResponse

from api.v1.models import Log
from config.logs.manager import get_all_logs
from config.logs.model import AppLogRecordRead, LogLevel
from services import logs as logs_service

logs_router = APIRouter(prefix="/logs", tags=["Logs"])


@logs_router.get("/download")
def download_file():
    # Read logs from file and send it back
    file_location = logs_service.log_file_to_download()
    if not file_location:
        return {"message": "Logs file not found"}
    return FileResponse(
        file_location,
        media_type="application/octet-stream",
        filename=logs_service.download_file_name(),
    )


@logs_router.get("/raw")
async def get_raw_logs(
    level: LogLevel = LogLevel.INFO,
    offset: int = 0,
    limit: int = 1000,
    filter: str | None = None,
) -> list[AppLogRecordRead]:
    """Retrieve logs from the database.
    Args:
        level (LogLevel, optional=LogLevel.INFO): The minimum log level to retrieve.
        offset (int, optional=0): The number of logs to skip.
        limit (int, optional=1000): The maximum number of logs to retrieve.
        filter (str | None, optional=None): A filter string to search in log fields. \
            filter must be at least 3 characters long.
    Returns:
        list[AppLogRecordRead]: A list of log records.
    """
    return await get_all_logs(
        level=level, offset=offset, limit=limit, filter=filter
    )


@logs_router.get("/", deprecated=True)
async def get_logs(page: int = 0, limit: int = 1000) -> list[Log]:
    records = await logs_service.read_logs(page=page, limit=limit)
    return [Log(**record) for record in records]
