import logging

from fastapi import APIRouter, HTTPException, status

from api.v1.models import ErrorResponse
from core.files_handler import FilesHandler, FolderInfo
from core.sonarr.database_manager import SeriesDatabaseManager
from core.sonarr.models import SeriesRead, SeriesUpdate
from core.tasks.download_trailers import download_trailer_by_id


series_router = APIRouter(prefix="/series", tags=["Series"])


@series_router.get("/")
async def get_recent_series(limit: int = 30, offset: int = 0) -> list[SeriesRead]:
    db_handler = SeriesDatabaseManager()
    all_series = db_handler.read_recent(limit, offset)
    return all_series


@series_router.get(
    "/{series_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Series Not Found",
        }
    },
)
async def get_series_by_id(series_id: int) -> SeriesRead:
    db_handler = SeriesDatabaseManager()
    try:
        series = db_handler.read(series_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return series


@series_router.get(
    "/{series_id}/files",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Series Not Found",
        }
    },
)
async def get_series_files(series_id: int) -> FolderInfo | str:
    db_handler = SeriesDatabaseManager()
    try:
        series = db_handler.read(series_id)
        if not series.folder_path:
            return "Series has no folder path!"
        files_handler = FilesHandler()
        files = await files_handler.get_folder_files(series.folder_path)
        if not files:
            return "No files found in series folder!"
        return files
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@series_router.post(
    "/{series_id}/download",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Series Not Found",
        }
    },
)
async def download_series_trailer(series_id: int, yt_id: str = "") -> str:
    msg = f"Downloading trailer for series with ID: {series_id}"
    if yt_id:
        msg += f" from [{yt_id}]"
    logging.info(msg)
    return download_trailer_by_id(series_id, is_movie=False, yt_id=yt_id)


@series_router.post(
    "/{series_id}/monitor",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Series Not Found",
        }
    },
)
async def monitor_series(series_id: int, monitor: bool = True) -> str:
    logging.info(f"Updating monitor status for series with ID: {series_id}")
    db_handler = SeriesDatabaseManager()
    try:
        series = db_handler.read(series_id)
        if series.trailer_exists and monitor:
            return f"Series '{series.title}' [{series.id}] already has a trailer!"
        series_update = SeriesUpdate(monitor=monitor)
        db_handler.update(series_id, series_update)
        if monitor:
            msg = f"Series '{series.title}' [{series.id}] is now monitored"
        else:
            msg = f"Series '{series.title}' [{series.id}] is no longer monitored"
        logging.info(msg)
        return msg
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@series_router.delete(
    "/{series_id}/trailer",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Series Not Found",
        }
    },
)
async def delete_series_trailer(series_id: int) -> str:
    logging.info(f"Deleting trailer for series with ID: {series_id}")
    db_handler = SeriesDatabaseManager()
    try:
        series = db_handler.read(series_id)
        if not series.trailer_exists:
            return f"Series '{series.title}' [{series.id}] has no trailer to delete!"
        if not series.folder_path:
            return f"Series '{series.title}' [{series.id}] has no folder path!"
        files_handler = FilesHandler()
        res = await files_handler.delete_trailer(series.folder_path)
        if not res:
            return f"Failed to delete trailer for series '{series.title}' [{series.id}]"
        series_update = SeriesUpdate(trailer_exists=False)
        db_handler.update(series_id, series_update)
        msg = f"Trailer for series '{series.title}' [{series.id}] has been deleted."
        logging.info(msg)
        return msg
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@series_router.get("/search/{query}")
async def search_series(query: str) -> list[SeriesRead]:
    db_handler = SeriesDatabaseManager()
    series = db_handler.search(query)
    return series
