from fastapi import APIRouter, HTTPException, status

from api.v1 import websockets
from api.v1 import errors
from api.v1.models import (
    BatchUpdate,
    ErrorResponse,
    InflightDownload,
    SearchMedia,
)
from app_logger import ModuleLogger
from database.manager import trailerprofile
import database.manager.download as download_manager
import database.manager.event as event_manager
import database.manager.filefolderinfo as files_manager
import database.manager.media as media_manager
from services import media as media_service
from database.models.event import EventSource
from database.models.filefolderinfo import FileFolderInfoRead
from database.models.download import DownloadRead
from database.models.media import MediaRead
from services.trailers import trailer_search
from services.trailers.inflight import inflight_registry
from services.trailers.trailers import utils as trailer_utils
from services.trailers.trailers.pending import (
    MediaPendingView,
    PendingSummary,
    compute_library_pending,
    compute_media_pending,
)
from tasks.files_scan import scan_media_folder
from tasks.download_trailers import (
    batch_download_trailers,
    download_trailer_by_id,
)
from exceptions import ItemNotFoundError

logger = ModuleLogger("MediaAPI")

media_router = APIRouter(prefix="/media", tags=["Media"])


@media_router.get("/all", deprecated=True)
async def get_all_media(
    movies_only: bool | None = None,
    filter_by: str | None = "all",
    sort_by: str | None = None,
    sort_asc: bool = True,
) -> list[MediaRead]:
    """Get all media from the database. \n
    Optionally apply filters and sorting.
    ## Warning:
        🚨Deprecated, use `/all_raw` instead.🚨\n
    Args:
        movies_only (bool, Optional=None): Flag to get only movies.
            - If `True`, it will return only `movies`.
            - If `False`, it will return only `series`.
            - If `None`, it will return all media items.
        filter_by (str, Optional=`all`): Filter the media items by a \
            column value. Available filters
            - all
            - downloaded
            - monitored
            - missing
            - unmonitored
        sort_by (str, Optional=None): Sort the media items by `title`, `year`, \
            `added_at`, or `updated_at`.
        sort_asc (bool, Optional=True): Flag to sort in ascending order.
    Returns:
        list[MediaRead]: List of media objects.
    """
    media = media_manager.read_all(
        movies_only=movies_only,
        filter_by=filter_by,
        sort_by=sort_by,
        sort_asc=sort_asc,
    )
    return media


@media_router.get("/all_raw")
async def get_all_media_raw() -> list[dict]:
    """Get all media from the database as raw JSON objects. \n
    The raw media objects include all columns but doesn't have any related
    objects (downloads, files, etc.) included or validated. \n
    Returns:
        list[dict]: List of media objects as JSON. \n
    """
    media_raw = media_manager.read_all_raw()
    return media_raw


@media_router.get("/downloading")
async def get_downloading() -> list[InflightDownload]:
    """Get the media items with a trailer download currently in flight. \n
    Runtime state from the in-memory registry — pushed over the websocket
    with `reload="downloading"` whenever it changes. \n
    Returns:
        list[InflightDownload]: In-flight (media_id, profile_id) pairs. \n
    """
    return [
        InflightDownload(media_id=media_id, profile_id=profile_id)
        for media_id, profile_id in inflight_registry.snapshot().items()
    ]


@media_router.get("/pending")
async def get_library_pending(
    limit: int = 100, offset: int = 0
) -> PendingSummary:
    """Library-wide pending downloads — the download task's work list. \n
    For every monitored media item and enabled matching profile that has no
    active download of its own: whether it would download now ("pending") or
    is waiting out failure backoff ("backoff"). Computed with the exact
    satisfaction rule the download task uses; performs no writes. \n
    Args:
        limit (int, Optional=100): Max items to return (1-1000).
        offset (int, Optional=0): Offset into the item list. \n
    Returns:
        PendingSummary: Counts plus the paginated (media, profile) list. \n
    """
    return compute_library_pending(limit=limit, offset=offset)


@media_router.get("/downloads_raw")
async def get_all_downloads_raw() -> list[dict]:
    """Get all downloads from the database as raw JSON objects. \n
    The raw download objects include all columns but doesn't have any related
    media objects included or validated. \n
    Returns:
        list[dict]: List of download objects as JSON. \n
    """
    downloads_raw = download_manager.read_all_raw()
    return downloads_raw


@media_router.get("/", deprecated=True)
async def get_recent_media(
    limit: int = 30, offset: int = 0, movies_only: bool | None = None
) -> list[MediaRead]:
    """Get recent media from the database. \n
    ## Warning:
        🚨Deprecated, use `/all_raw` instead.🚨
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


@media_router.get("/updated", deprecated=True)
async def get_updated_after(seconds: int) -> list[MediaRead]:
    """Get media updated after a certain datetime.
    ## Warning:
        🚨Deprecated, use `/all_raw` instead.🚨
    Args:
        seconds (int): Seconds since epoch to filter media.
    Returns:
        list[MediaRead]: List of media objects.
    """
    media = media_manager.read_updated_after(seconds)
    return media


@media_router.get("/downloaded", deprecated=True)
async def get_recently_downloaded(
    limit: int = 30, offset: int = 0
) -> list[MediaRead]:
    """Get recently downloaded media from the database.
    ## Warning:
        🚨Deprecated, use `/all_raw` instead.🚨
    Args:
        limit (int, Optional=30): Number of items to return.
        offset (int, Optional=0): Number of items to skip.
    Returns:
        list[MediaRead]: List of media objects.
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
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Unexpected error",
        },
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
        raise errors.as_http_error(
            e, logger=logger, action="Read media",
            safe_status=status.HTTP_404_NOT_FOUND,
        )
    return media


@media_router.get(
    "/{media_id}/downloads",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Unexpected error",
        },
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
        raise errors.as_http_error(
            e, logger=logger, action="Read the downloads of media",
            safe_status=status.HTTP_404_NOT_FOUND,
        )


@media_router.get(
    "/{media_id}/pending",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Unexpected error",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Media Not Found",
        }
    },
)
async def get_media_pending(media_id: int) -> MediaPendingView:
    """Get the per-profile download matrix for a media item. \n
    For every profile: whether it matches this media, whether it is
    satisfied (and by which download — own, claimed, or a stop-monitoring
    profile's), or pending/backing-off with attempt info. This is the same
    satisfaction rule the download task uses — the UI and the task can
    never disagree. \n
    Args:
        media_id (int): The ID of the media item. \n
    Returns:
        MediaPendingView: Profile matrix for the media item. \n
    """
    try:
        media = media_manager.read(media_id)
    except Exception as e:
        raise errors.as_http_error(
            e, logger=logger, action="Read the pending trailers of media",
            safe_status=status.HTTP_404_NOT_FOUND,
        )
    profiles = trailerprofile.get_trailerprofiles()
    return compute_media_pending(media, profiles)


@media_router.put(
    "/{media_id}/downloads/{download_id}/profile",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Media, Download or Profile Not Found",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Unexpected error updating the download",
        },
    },
)
async def update_download_profile(
    media_id: int, download_id: int, profile_id: int
) -> str:
    """Set the trailer profile that owns a download. \n
    Used to manually attribute downloads recorded without a profile
    (profile_id=0), e.g. trailers found on disk that couldn't be linked
    to a profile automatically. \n
    Args:
        media_id (int): The ID of the media item the download belongs to.
        download_id (int): The ID of the download to update.
        profile_id (int): The ID of the trailer profile to attribute it to. \n
    Returns:
        str: Message indicating the result.
    """
    logger.info(
        f"Assigning download {download_id} to trailer profile"
        f" {profile_id}.",
        **logger.media(media_id),
    )
    try:
        download = download_manager.read(download_id)
        if download.media_id != media_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Download with id {download_id} does not belong to"
                    f" media {media_id}"
                ),
            )
        profile = trailerprofile.get_trailerprofile(profile_id)
        download_manager.update_profile_id(download_id, profile_id)
        event_manager.track_download_attributed(
            media_id=media_id,
            download_name=download.file_name,
            profile_name=profile.customfilter.filter_name,
            source=EventSource.USER,
            source_detail="MediaDetails",
        )
        msg = (
            f"Download '{download.file_name}' assigned to profile"
            f" '{profile.customfilter.filter_name}'"
        )
        await websockets.ws_manager.broadcast(
            msg, "Success", reload="downloads"
        )
        return msg
    except HTTPException:
        raise
    except ItemNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except Exception as e:
        logger.exception(
            f"Could not assign download {download_id} to trailer profile"
            f" {profile_id}: {e}",
            **logger.media(media_id),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update download profile",
        )


@media_router.get(
    "/{media_id}/files",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Unexpected error",
        },
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
        raise errors.as_http_error(
            e, logger=logger, action="Read the files of media",
            safe_status=status.HTTP_404_NOT_FOUND,
        )


@media_router.post(
    "/{media_id}/rescan_files",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Media Not Found",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Unexpected error",
        },
    },
)
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
        raise errors.as_http_error(
            e, logger=logger, action="Rescan the media files",
            safe_status=status.HTTP_404_NOT_FOUND,
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
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Unexpected error",
        },
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
    logger.info(
        f"Trailarr changes the monitor status of this media item.",
        **logger.media(media_id),
    )
    try:
        result = media_service.set_monitoring(media_id, monitor)
        await websockets.ws_manager.broadcast(
            result.message,
            "Success" if result.ok else "Error",
            reload=result.reload,
        )
        return result.message
    except Exception as e:
        await websockets.ws_manager.broadcast(
            "Error changing Monitor status!", "Error", reload="media"
        )
        raise errors.as_http_error(
            e, logger=logger, action="Change the monitor status",
            safe_status=status.HTTP_404_NOT_FOUND,
        )


@media_router.post(
    "/{media_id}/update",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Unexpected error",
        },
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
    logger.info(
        f"Trailarr updates the YouTube ID of this media item.",
        **logger.media(media_id),
    )
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
        msg = media_service.set_youtube_id(media_id, yt_id)
        await websockets.ws_manager.broadcast(msg, "Success", reload="media")
        return msg
    except Exception as e:
        raise errors.as_http_error(
            e, logger=logger, action="Update the YouTube ID",
            safe_status=status.HTTP_404_NOT_FOUND,
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
    logger.info(
        f"Trailarr searches for a trailer for this media item.",
        **logger.media(media_id),
    )
    media = media_manager.read(media_id)
    profile = trailerprofile.get_trailerprofile(profile_id)

    if yt_id := trailer_search.search_yt_for_trailer(media, profile):
        media_manager.update_ytid(media_id, yt_id)
        event_manager.track_youtube_id_changed(
            media_id=media_id,
            old_yt_id=media.youtube_trailer_id,
            new_yt_id=yt_id,
            source=EventSource.USER,
            source_detail="UserSearch",
        )
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


async def _delete_trailer_and_report(media_id: int) -> str:
    """Delete the trailers of one media item and tell the user.

    The batch action shares this, so a batch delete still sends one message
    per item. It is a plain function rather than the endpoint itself: a
    route handler calling another route handler hides where the work is.
    """
    logger.info(
        f"Trailarr deletes the trailers of this media item.",
        **logger.media(media_id),
    )
    try:
        result = await media_service.delete_trailers(media_id)
        await websockets.ws_manager.broadcast(
            result.message,
            "Success" if result.ok else "Error",
            reload=result.reload,
        )
        return result.message
    except Exception as e:
        await websockets.ws_manager.broadcast(
            "Error deleting trailer!", "Error", reload="media"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@media_router.delete(
    "/{media_id}/trailer",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Media Not Found",
        }
    },
    deprecated=True,
)
async def delete_media_trailer(media_id: int) -> str:
    """Delete all trailers for media by ID. \n
    ## Warning:
        🚨Deprecated, use `/files/delete` instead.🚨
    Args:
        media_id (int): ID of the media item. \n
    Returns:
        str: Deleting trailer message.
    """
    return await _delete_trailer_and_report(media_id)


@media_router.post(
    "/batch_update",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Unexpected error",
        },
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
    logger.info(
        f"Trailarr updates {len(update.media_ids)} media items."
    )
    try:
        msg = ""
        if update.action == "monitor":
            msg = media_service.set_monitoring_bulk(update.media_ids, True)
        elif update.action == "unmonitor":
            msg = media_service.set_monitoring_bulk(update.media_ids, False)
        elif update.action == "delete":
            for media_id in update.media_ids:
                await _delete_trailer_and_report(media_id)
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
        raise errors.as_http_error(
            e, logger=logger, action="Update media",
            safe_status=status.HTTP_404_NOT_FOUND,
        )
