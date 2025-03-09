import logging

from fastapi import APIRouter, HTTPException, status

from api.v1 import websockets
from api.v1.models import BatchUpdate, ErrorResponse, SearchMedia
from core.base.database.manager.base import MediaDatabaseManager
from core.base.database.models.media import MediaRead
from core.download import trailer
from core.files_handler import FilesHandler, FolderInfo
from core.tasks.download_trailers import (
    batch_download_trailers,
    download_trailer_by_id,
)

media_router = APIRouter(prefix="/media", tags=["Media"])


@media_router.get("/all")
async def get_all_media(
    movies_only: bool | None = None,
    filter_by: str | None = "all",
    sort_by: str | None = None,
    sort_asc: bool = True,
) -> list[MediaRead]:
    """Get all media from the database. \n
    Optionally apply filters and sorting. \n
    Args:
        movies_only (bool, Optional=None):
            Flag to get only movies.
            - If `True`, it will return only `movies`.
            - If `False`, it will return only `series`.
            - If `None`, it will return all media items. \n
        filter_by (str, Optional=`all`):
            Filter the media items by a column value. Available filters are
            - `all`
            - `downloaded`
            - `monitored`
            - `missing`
            - `unmonitored`. \n
        sort_by (str, Optional=None): Sort the media items by `title`, `year`, \
            `added_at`, or `updated_at`. \n
        sort_asc (bool, Optional=True): Flag to sort in ascending order. \n
    Returns:
        list[MediaRead]: List of media objects. \n
    """
    db_handler = MediaDatabaseManager()
    media = db_handler.read_all(
        movies_only=movies_only,
        filter_by=filter_by,
        sort_by=sort_by,
        sort_asc=sort_asc,
    )
    return media


@media_router.get("/")
async def get_recent_media(
    limit: int = 30, offset: int = 0, movies_only: bool | None = None
) -> list[MediaRead]:
    """Get recent media from the database. \n
    Args:
        limit (int, Optional=30): Number of items to return.
        offset (int, Optional=0): Number of items to skip.
        movies_only (bool, Optional=None):
            Flag to get only movies.
            - If `True`, it will return only `movies`.
            - If `False`, it will return only `series`.
            - If `None`, it will return all media items. \n
    Returns:
    - list[MediaRead]: List of media objects.
    """
    db_handler = MediaDatabaseManager()
    media = db_handler.read_recent(limit, offset, movies_only=movies_only)
    return media


@media_router.get("/updated")
async def get_updated_after(seconds: int) -> list[MediaRead]:
    """Get media updated after a certain datetime. \n
    Args:
        timestamp (datetime): Timestamp to filter by. \n
    Returns:
        list[MediaRead]: List of media objects. \n
    """
    db_handler = MediaDatabaseManager()
    media = db_handler.read_updated_after(seconds)
    return media


@media_router.get("/downloaded")
async def get_recently_downloaded(
    limit: int = 30, offset: int = 0
) -> list[MediaRead]:
    """Get recently downloaded media from the database. \n
    Args:
        limit (int, Optional=30): Number of items to return.
        offset (int, Optional=0): Number of items to skip. \n
    Returns:
        list[MediaRead]: List of media objects. \n
    """
    db_handler = MediaDatabaseManager()
    media_list = db_handler.read_recently_downloaded(limit, offset)
    return media_list


@media_router.get("/search", tags=["Search"])
async def search_media(query: str) -> list[SearchMedia]:
    """Search media by query. \n
    Args:
        query (str): Search query. \n
    Returns:
        list[SearchMedia]: List of search media objects. \n
    """
    db_handler = MediaDatabaseManager()
    media_list = db_handler.search(query)
    search_media_list: list[SearchMedia] = []
    for media in media_list:
        media_data = media.model_dump()
        search_media = SearchMedia.model_validate(media_data)
        search_media_list.append(search_media)
    return search_media_list


@media_router.get(
    "/{media_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Media Not Found",
        }
    },
)
async def get_media_by_id(media_id: int) -> MediaRead:
    """Get media by ID. \n
    Args:
        media_id (int): ID of the media item. \n
    Returns:
        MediaRead: Media object. \n
    """
    db_handler = MediaDatabaseManager()
    try:
        media = db_handler.read(media_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    return media


@media_router.get(
    "/{media_id}/files",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Media Not Found",
        }
    },
)
async def get_media_files(media_id: int) -> FolderInfo | str:
    """Get media files by ID. \n
    Args:
        media_id (int): ID of the media item. \n
    Returns:
        FolderInfo|str: Folder information or error message. \n
    """
    db_handler = MediaDatabaseManager()
    try:
        media = db_handler.read(media_id)
        if not media.folder_path:
            raise Exception("Media has no folder path!")
        files_handler = FilesHandler()
        files = await files_handler.get_folder_files(media.folder_path)
        if not files:
            raise Exception("No files found in media folder!")
        return files
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@media_router.post(
    "/{media_id}/download",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Media Not Found",
        }
    },
)
async def download_media_trailer(media_id: int, yt_id: str = "") -> str:
    """Download trailer for media by ID. \n
    Args:
        media_id (int): ID of the media item.
        yt_id (str, Optional=""): YouTube ID of the trailer.\n
    Returns:
        str: Downloading trailer message.
    """
    msg = f"Downloading trailer for media with ID: {media_id}"
    if yt_id:
        msg += f" from [{yt_id}]"
    logging.info(msg)
    return download_trailer_by_id(media_id, yt_id)


@media_router.post(
    "/{media_id}/monitor",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Media Not Found",
        }
    },
)
async def monitor_media(media_id: int, monitor: bool = True) -> str:
    """Monitor media by ID. \n
    Args:
        media_id (int): ID of the media item.
        monitor (bool, Optional=True): Monitor status. \n
    Returns:
        str: Monitoring message.
    """
    logging.info(f"Monitoring media with ID: {media_id}")
    db_handler = MediaDatabaseManager()
    try:
        msg, is_success = db_handler.update_monitoring(media_id, monitor)
        logging.info(msg)
        await websockets.ws_manager.broadcast(
            msg, "Success" if is_success else "Error"
        )
        return msg
    except Exception as e:
        await websockets.ws_manager.broadcast(
            "Error changing Monitor status!", "Error"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@media_router.post(
    "/{media_id}/update",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Media Not Found",
        },
        status.HTTP_406_NOT_ACCEPTABLE: {
            "model": ErrorResponse,
            "description": "Invalid YouTube URL/ID",
        },
    },
)
async def update_yt_id(media_id: int, yt_id: str) -> str:
    """Update YouTube ID for media by ID. \n
    Args:
        media_id (int): ID of the media item.
        yt_id (str): YouTube ID of the trailer. \n
    Returns:
        str: Updating YouTube ID message.
    """
    logging.info(f"Updating YouTube ID for media with ID: {media_id}")
    # Check if yt_id is a URL and extract the ID
    if yt_id and yt_id.startswith("http"):
        _yt_id = trailer.extract_youtube_id(yt_id)
        if not _yt_id:
            msg = "Invalid YouTube URL/ID!"
            await websockets.ws_manager.broadcast(msg, "Error")
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="Invalid YouTube URL/ID!",
            )
        yt_id = _yt_id
    # If id is not empty, check if it is valid (length > 11)
    if yt_id and len(yt_id) < 11:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Invalid YouTube ID!",
        )
    db_handler = MediaDatabaseManager()
    try:
        db_handler.update_ytid(media_id, yt_id)
        msg = f"YouTube ID for media with ID: {media_id} has been updated."
        logging.info(msg)
        await websockets.ws_manager.broadcast(msg, "Success")
        return msg
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@media_router.post(
    "/{media_id}/search",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Media Not Found",
        }
    },
)
async def search_for_trailer(media_id: int) -> str:
    """Search for trailer for media by ID. \n
    Args:
        media_id (int): ID of the media item. \n
    Returns:
        str: Youtube ID of the trailer if found, else empty string. \n
    """
    logging.info(f"Searching for trailer for media with ID: {media_id}")
    db_handler = MediaDatabaseManager()
    media = db_handler.read(media_id)
    # mediaT = MediaTrailer(
    #     id=media.id,
    #     title=media.title,
    #     is_movie=media.is_movie,
    #     language=media.language,
    #     year=media.year,
    #     yt_id=media.youtube_trailer_id,
    #     folder_path=media.folder_path or "",
    # )
    if yt_id := trailer.search_yt_for_trailer(media):
        db_handler.update_ytid(media_id, yt_id)
        msg = (
            f"Trailer found for media '{media.title}' [{media.id}] as"
            f" [{yt_id}]"
        )
        logging.info(msg)
        await websockets.ws_manager.broadcast(msg, "Success")
        return yt_id
    msg = f"Unable to find a trailer for media '{media.title}' [{media.id}]"
    logging.info(msg)
    await websockets.ws_manager.broadcast(msg, "Error")
    return ""


@media_router.delete(
    "/{media_id}/trailer",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Media Not Found",
        }
    },
)
async def delete_media_trailer(media_id: int) -> str:
    """Delete trailer for media by ID. \n
    Args:
        media_id (int): ID of the media item. \n
    Returns:
        str: Deleting trailer message.
    """
    logging.info(f"Deleting trailer for media with ID: {media_id}")
    db_handler = MediaDatabaseManager()
    try:
        media = db_handler.read(media_id)
        if not media.trailer_exists:
            msg = (
                f"Media '{media.title}' [{media.id}] has no trailer to delete"
            )
            await websockets.ws_manager.broadcast(msg, "Error")
            return msg
        if not media.folder_path:
            msg = f"Media '{media.title}' [{media.id}] has no folder path"
            await websockets.ws_manager.broadcast(msg, "Error")
            return msg
        files_handler = FilesHandler()
        res = await files_handler.delete_trailer(media.folder_path)
        if not res:
            msg = (
                f"Failed to delete trailer for media '{media.title}'"
                f" [{media.id}]"
            )
            await websockets.ws_manager.broadcast(msg, "Error")
            return msg
        db_handler.update_trailer_exists(media_id, False)
        msg = (
            f"Trailer for media '{media.title}' [{media.id}] has been deleted."
        )
        logging.info(msg)
        await websockets.ws_manager.broadcast(msg, "Success")
        return msg
    except Exception as e:
        await websockets.ws_manager.broadcast(
            "Error deleting trailer!", "Error"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@media_router.post(
    "/batch_update",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Media Not Found",
        }
    },
)
async def batch_update_media(update: BatchUpdate) -> None:
    """Batch update media by their IDs. \n
    Available update types are: \n
    - monitor: Monitor media items. \n
    - unmonitor: Unmonitor media items. \n
    - delete: Delete media items. \n
    - download: Download trailers for media items. \n
    Args:
        update (BulkUpdate): Bulk update object with media ids and update type.
    Returns:
        str: Monitoring message.
    """
    logging.info(f"Monitoring media with IDs: {update.media_ids}")
    db_handler = MediaDatabaseManager()
    try:
        msg = ""
        if update.action == "monitor":
            db_handler.update_monitoring_bulk(update.media_ids, True)
            msg = f"{len(update.media_ids)} Media are now monitored"
        elif update.action == "unmonitor":
            db_handler.update_monitoring_bulk(update.media_ids, False)
            msg = f"{len(update.media_ids)} Media are now unmonitored"
        elif update.action == "delete":
            for media_id in update.media_ids:
                await delete_media_trailer(media_id)
        elif update.action == "download":
            batch_download_trailers(update.media_ids)
        if msg:
            logging.info(msg)
            await websockets.ws_manager.broadcast(msg, "Success")
            return
    except Exception as e:
        await websockets.ws_manager.broadcast("Error updating Media!", "Error")
        logging.error(e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
