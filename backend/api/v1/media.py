from fastapi import APIRouter, HTTPException, status

from api.v1 import websockets
from api.v1.models import BatchUpdate, ErrorResponse, SearchMedia
from app_logger import ModuleLogger
from core.base.database.manager import trailerprofile
import core.base.database.manager.download as download_manager
import core.base.database.manager.filefolderinfo as files_manager
import core.base.database.manager.media as media_manager
from core.base.database.models.filefolderinfo import FileFolderInfoRead
from core.base.database.models.download import DownloadRead
from core.base.database.models.media import MediaRead
from core.download import trailer_search
from core.download.trailers import utils as trailer_utils
from core.files_handler import FilesHandler
from backend.core.tasks.files_scan import scan_media_folder
from core.tasks.download_trailers import (
    batch_download_trailers,
    download_trailer_by_id,
)

logger = ModuleLogger("MediaAPI")

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
    media = media_manager.read_all(
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
    media = media_manager.read_recent(limit, offset, movies_only=movies_only)
    return media


@media_router.get("/updated")
async def get_updated_after(seconds: int) -> list[MediaRead]:
    """Get media updated after a certain datetime. \n
    Args:
        seconds (int): Seconds since epoch to filter media.
    Returns:
        list[MediaRead]: List of media objects. \n
    """
    media = media_manager.read_updated_after(seconds)
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
    media = media_manager.read_recently_downloaded(limit, offset)
    return media


@media_router.get("/search", tags=["Search"])
async def search_media(query: str) -> list[SearchMedia]:
    """Search media by query. \n
    Args:
        query (str): Search query. \n
    Returns:
        list[SearchMedia]: List of search media objects. \n
    """
    media_list = media_manager.search(query)
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
    try:
        media = media_manager.read(media_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    return media


@media_router.get(
    "/{media_id}/downloads",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Media Not Found",
        }
    },
)
async def get_media_downloads(media_id: int) -> list[DownloadRead]:
    """Get all downloads for a specific media item.
    Args:
        media_id (int): The ID of the media item.
    Returns:
        list[DownloadRead]: List of download objects for the media item.
    """
    try:
        # Verify media exists first
        media = media_manager.read(media_id)
        if not media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Media with id {media_id} not found",
            )

        # Get downloads for this media using dedicated download manager
        downloads = download_manager.read_by_media_id(media_id)
        return downloads

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


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
async def get_media_files(media_id: int) -> FileFolderInfoRead:
    """Get media files by ID. \n
    Args:
        media_id (int): ID of the media item. \n
    Returns:
        FileFolderInfoRead: Folder information. \n
    Raises:
        HTTPException (404): If the media or files are not found. \n
    """
    try:
        media = media_manager.read(media_id)
        if not media.folder_path:
            raise Exception("Media has no folder path!")
        files = files_manager.read_by_media_id(media_id)
        if not files:
            raise Exception("No files found in media folder!")
        return files
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@media_router.post("/{media_id}/rescan_files", status_code=status.HTTP_200_OK)
async def rescan_media_files(media_id: int) -> str:
    """Rescan media files by ID. \n
    Args:
        media_id (int): ID of the media item. \n
    Returns:
        str: Rescanning media files message. \n
    """
    try:
        media = media_manager.read(media_id)
        if not media.folder_path:
            raise Exception("Media has no folder path!")
        await scan_media_folder(media)
        msg = f"Rescanned files for media with ID: {media_id}"
        logger.info(msg)
        await websockets.ws_manager.broadcast(msg, "Success", reload="files")
        return msg
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
async def download_media_trailer(
    media_id: int, profile_id: int, yt_id: str = ""
) -> str:
    """Download trailer for media by ID. \n
    Args:
        media_id (int): ID of the media item.
        profile_id (int): ID of the trailer profile to use for downloading.
        yt_id (str, Optional=""): YouTube ID of the trailer.\n
    Returns:
        str: Downloading trailer message.
    """
    msg = f"Downloading trailer for media with ID: [{media_id}]"
    if yt_id:
        msg += f" from ({yt_id})"
    logger.info(msg)
    return download_trailer_by_id(media_id, profile_id, yt_id)


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
    logger.info(f"Monitoring media with ID: {media_id}")
    try:
        msg, is_success = media_manager.update_monitoring(media_id, monitor)
        logger.info(msg)
        await websockets.ws_manager.broadcast(
            msg, "Success" if is_success else "Error", reload="media"
        )
        return msg
    except Exception as e:
        await websockets.ws_manager.broadcast(
            "Error changing Monitor status!", "Error", reload="media"
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
    logger.info(f"Updating YouTube ID for media with ID: {media_id}")
    # Check if yt_id is a URL and extract the ID
    if yt_id and yt_id.startswith("http"):
        _yt_id = trailer_utils.extract_youtube_id(yt_id)
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
    try:
        media_manager.update_ytid(media_id, yt_id)
        msg = f"YouTube ID for media with ID: {media_id} has been updated."
        logger.info(msg)
        await websockets.ws_manager.broadcast(msg, "Success", reload="media")
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
async def search_for_trailer(media_id: int, profile_id: int) -> str:
    """Search for trailer for media by ID. \n
    Args:
        media_id (int): ID of the media item.
        profile_id (int): ID of the trailer profile to use.\n
    Returns:
        str: Youtube ID of the trailer if found, else empty string. \n
    """
    logger.info(f"Searching for trailer for media with ID: {media_id}")
    media = media_manager.read(media_id)
    profile = trailerprofile.get_trailerprofile(profile_id)

    if yt_id := trailer_search.search_yt_for_trailer(media, profile):
        media_manager.update_ytid(media_id, yt_id)
        msg = (
            f"Trailer found for media '{media.title}' [{media.id}] as"
            f" ({yt_id})"
        )
        logger.info(msg)
        await websockets.ws_manager.broadcast(msg, "Success", reload="media")
        return yt_id
    msg = f"Unable to find a trailer for media '{media.title}' [{media.id}]"
    logger.info(msg)
    await websockets.ws_manager.broadcast(msg, "Error", reload="media")
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
    logger.info(f"Deleting trailer for media with ID: {media_id}")
    try:
        media = media_manager.read(media_id)
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
        media_manager.update_trailer_exists(media_id, False)
        msg = (
            f"Trailer for media '{media.title}' [{media.id}] has been deleted."
        )
        logger.info(msg)
        await websockets.ws_manager.broadcast(msg, "Success", reload="media")
        return msg
    except Exception as e:
        await websockets.ws_manager.broadcast(
            "Error deleting trailer!", "Error", reload="media"
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
    logger.info(f"Monitoring media with IDs: {update.media_ids}")
    try:
        msg = ""
        if update.action == "monitor":
            media_manager.update_monitoring_bulk(update.media_ids, True)
            msg = f"{len(update.media_ids)} Media are now monitored"
        elif update.action == "unmonitor":
            media_manager.update_monitoring_bulk(update.media_ids, False)
            msg = f"{len(update.media_ids)} Media are now unmonitored"
        elif update.action == "delete":
            for media_id in update.media_ids:
                await delete_media_trailer(media_id)
        elif update.action == "download":
            if not update.profile_id or update.profile_id <= 0:
                msg = "No trailer profile ID provided!"
                await websockets.ws_manager.broadcast(msg, "Error")
                return
            batch_download_trailers(update.profile_id, update.media_ids)
        if msg:
            logger.info(msg)
            await websockets.ws_manager.broadcast(
                msg, "Success", reload="media"
            )
            return
    except Exception as e:
        await websockets.ws_manager.broadcast(
            f"Error updating Media! {e}", "Error", reload="media"
        )
        logger.error(e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
