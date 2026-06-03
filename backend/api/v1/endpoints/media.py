from fastapi import APIRouter, Body, HTTPException, status

from api.v1.models import BatchUpdate, ErrorResponse, SearchMedia
from app_logger import ModuleLogger
import db.repos.download as download_repo
import db.repos.file_info as file_info_repo
import db.repos.media as media_repo
import db.repos.trailer_profile as trailer_profile_repo
import db.repos.trailer_status as trailer_status_repo
import db.repos.video_id as video_id_repo
from db.models.download import DownloadRead
from db.models.event import EventSource
from db.models.filefolderinfo import FileFolderInfoRead
from db.models.media import MediaRead
from db.models.mediatrailerstatus import MediaTrailerStatusRead, TrailerStatusEnum
from db.models.videoid import VideoIdCreate, VideoIdRead
from download import search as trailer_search
from download.pipeline import download_trailer_by_id, batch_download_trailers
from download.utils import extract_youtube_id
from services import event_service
from services.files_service import FilesHandler
from services.scan_service import scan_media_folder
from ws.manager import ws_manager

logger = ModuleLogger("MediaAPI")

media_router = APIRouter(prefix="/media", tags=["Media"])


@media_router.get("/all", deprecated=True)
async def get_all_media(
    movies_only: bool | None = None,
    filter_by: str | None = "all",
    sort_by: str | None = None,
    sort_asc: bool = True,
) -> list[MediaRead]:
    return media_repo.read_all(
        movies_only=movies_only,
        filter_by=filter_by,
        sort_by=sort_by,
        sort_asc=sort_asc,
    )


@media_router.get("/all_raw")
async def get_all_media_raw() -> list[dict]:
    return media_repo.read_all_raw()


@media_router.get("/trailer-statuses-raw")
async def get_all_trailer_statuses_raw() -> list[dict]:
    return trailer_status_repo.get_all_rows()


@media_router.get("/downloads_raw")
async def get_all_downloads_raw() -> list[dict]:
    return download_repo.read_all_raw()


@media_router.get("/", deprecated=True)
async def get_recent_media(
    limit: int = 30, offset: int = 0, movies_only: bool | None = None
) -> list[MediaRead]:
    return media_repo.read_recent(limit, offset, movies_only=movies_only)


@media_router.get("/updated", deprecated=True)
async def get_updated_after(seconds: int) -> list[MediaRead]:
    return media_repo.read_updated_after(seconds)


@media_router.get("/downloaded", deprecated=True)
async def get_recently_downloaded(limit: int = 30, offset: int = 0) -> list[MediaRead]:
    return media_repo.read_recently_downloaded(limit, offset)


@media_router.get("/search", tags=["Search"])
async def search_media(query: str) -> list[SearchMedia]:
    media_list = media_repo.search(query)
    return [SearchMedia.model_validate(m.model_dump()) for m in media_list]


@media_router.get(
    "/{media_id}",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Media Not Found"}},
)
async def get_media_by_id(media_id: int) -> MediaRead:
    try:
        return media_repo.read(media_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@media_router.get(
    "/{media_id}/downloads",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Media Not Found"}},
)
async def get_media_downloads(media_id: int) -> list[DownloadRead]:
    try:
        media_repo.read(media_id)  # verify exists
        return download_repo.read_by_media_id(media_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@media_router.get(
    "/{media_id}/files",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Media Not Found"}},
)
async def get_media_files(media_id: int) -> FileFolderInfoRead:
    try:
        media = media_repo.read(media_id)
        if not media.folder_path:
            raise Exception("Media has no folder path!")
        files = file_info_repo.read_by_media_id(media_id)
        if not files:
            raise Exception("No files found in media folder!")
        return files
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@media_router.post("/{media_id}/rescan_files", status_code=status.HTTP_200_OK)
async def rescan_media_files(media_id: int) -> str:
    try:
        media = media_repo.read(media_id)
        if not media.folder_path:
            raise Exception("Media has no folder path!")
        await scan_media_folder(media)
        msg = f"Rescanned files for media with ID: {media_id}"
        logger.info(msg)
        await ws_manager.broadcast(msg, "Success", reload="files")
        return msg
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@media_router.post(
    "/{media_id}/download",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Media Not Found"}},
)
async def download_media_trailer(media_id: int, profile_id: int, yt_id: str = "") -> str:
    msg = f"Downloading trailer for media with ID: [{media_id}]"
    if yt_id:
        msg += f" from ({yt_id})"
    logger.info(msg)
    return download_trailer_by_id(media_id, profile_id, yt_id)


@media_router.post(
    "/{media_id}/monitor",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Media Not Found"}},
)
async def monitor_media(media_id: int, monitor: bool = True) -> str:
    logger.info(f"Monitoring media with ID: {media_id}")
    try:
        media = media_repo.read(media_id)
        old_monitor = media.monitor
        msg, is_success = media_repo.update_monitoring(media_id, monitor)
        logger.info(msg)
        if is_success:
            event_service.track_monitor_changed(
                media_id=media_id,
                old_monitor=old_monitor,
                new_monitor=monitor,
                source=EventSource.USER,
            )
        await ws_manager.broadcast(msg, "Success" if is_success else "Error", reload="media")
        return msg
    except Exception as e:
        await ws_manager.broadcast("Error changing Monitor status!", "Error", reload="media")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@media_router.post(
    "/{media_id}/update",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Media Not Found"},
        status.HTTP_406_NOT_ACCEPTABLE: {"model": ErrorResponse, "description": "Invalid YouTube URL/ID"},
    },
)
async def update_yt_id(media_id: int, yt_id: str) -> str:
    logger.info(f"Updating YouTube ID for media with ID: {media_id}")
    if yt_id and yt_id.startswith("http"):
        _yt_id = extract_youtube_id(yt_id)
        if not _yt_id:
            await ws_manager.broadcast("Invalid YouTube URL/ID!", "Error")
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Invalid YouTube URL/ID!")
        yt_id = _yt_id
    if yt_id and len(yt_id) < 11:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Invalid YouTube ID!")
    try:
        media = media_repo.read(media_id)
        old_yt_id = media.youtube_trailer_id
        media_repo.update_ytid(media_id, yt_id)
        if old_yt_id != yt_id:
            event_service.track_youtube_id_changed(
                media_id=media_id,
                old_yt_id=old_yt_id,
                new_yt_id=yt_id,
                source=EventSource.USER,
                source_detail="UserInput",
            )
        msg = f"YouTube ID for media with ID: {media_id} has been updated."
        logger.info(msg)
        await ws_manager.broadcast(msg, "Success", reload="media")
        return msg
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@media_router.post(
    "/{media_id}/search",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Media Not Found"}},
)
async def search_for_trailer(media_id: int, profile_id: int) -> str:
    logger.info(f"Searching for trailer for media with ID: {media_id}")
    media = media_repo.read(media_id)
    profile = trailer_profile_repo.read(profile_id)
    if yt_id := trailer_search.search_yt_for_trailer(media, profile):
        media_repo.update_ytid(media_id, yt_id)
        event_service.track_youtube_id_changed(
            media_id=media_id,
            old_yt_id=media.youtube_trailer_id,
            new_yt_id=yt_id,
            source=EventSource.USER,
            source_detail="UserSearch",
        )
        msg = f"Trailer found for media '{media.title}' [{media.id}] as ({yt_id})"
        logger.info(msg)
        await ws_manager.broadcast(msg, "Success", reload="media")
        return yt_id
    msg = f"Unable to find a trailer for media '{media.title}' [{media.id}]"
    logger.info(msg)
    await ws_manager.broadcast(msg, "Error", reload="media")
    return ""


@media_router.delete(
    "/{media_id}/trailer",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Media Not Found"}},
    deprecated=True,
)
async def delete_media_trailer(media_id: int) -> str:
    logger.info(f"Deleting trailer for media with ID: {media_id}")
    try:
        media = media_repo.read(media_id)
        downloads = download_repo.read_by_media_id(media_id)
        live = [d for d in downloads if d.file_exists]
        if not live:
            msg = f"No trailer files found for media '{media.title}' [{media.id}]"
            await ws_manager.broadcast(msg, "Error")
            return msg
        for d in live:
            await FilesHandler.delete_file(d.path)
            download_repo.mark_as_deleted(d.id)
            trailer_status_repo.on_file_deleted(d.id)
        event_service.track_trailer_deleted(
            media_id=media_id,
            reason="user_request",
            source=EventSource.USER,
        )
        msg = f"Trailer for media '{media.title}' [{media.id}] has been deleted."
        logger.info(msg)
        await ws_manager.broadcast(msg, "Success", reload="media")
        return msg
    except Exception as e:
        await ws_manager.broadcast("Error deleting trailer!", "Error", reload="media")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@media_router.post(
    "/batch_update",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Media Not Found"}},
)
async def batch_update_media(update: BatchUpdate) -> None:
    logger.info(f"Batch update for media IDs: {update.media_ids}")
    try:
        msg = ""
        if update.action == "monitor":
            media_repo.update_monitoring_bulk(update.media_ids, True)
            msg = f"{len(update.media_ids)} Media are now monitored"
        elif update.action == "unmonitor":
            media_repo.update_monitoring_bulk(update.media_ids, False)
            msg = f"{len(update.media_ids)} Media are now unmonitored"
        elif update.action == "delete":
            for media_id in update.media_ids:
                await delete_media_trailer(media_id)
        elif update.action == "download":
            if not update.profile_id or update.profile_id <= 0:
                msg = "No trailer profile ID provided!"
                await ws_manager.broadcast(msg, "Error")
                return
            batch_download_trailers(update.profile_id, update.media_ids)
        if msg:
            logger.info(msg)
            await ws_manager.broadcast(msg, "Success", reload="media")
    except Exception as e:
        await ws_manager.broadcast(f"Error updating Media! {e}", "Error", reload="media")
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@media_router.get("/{media_id}/trailer-statuses")
async def get_trailer_statuses(media_id: int) -> list[MediaTrailerStatusRead]:
    return trailer_status_repo.get_rows_for_media(media_id)


@media_router.patch("/trailer-status/{row_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_trailer_status(row_id: int, new_status: TrailerStatusEnum):
    updated = trailer_status_repo.update_row_status(row_id, new_status)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MediaTrailerStatus row {row_id} not found",
        )


# ─── Video IDs ────────────────────────────────────────────────────────────────

@media_router.get("/{media_id}/video-ids", tags=["VideoIds"])
async def get_video_ids(media_id: int) -> list[VideoIdRead]:
    """Return all VideoId records for a media item."""
    return video_id_repo.get_for_media(media_id)


@media_router.post("/{media_id}/video-ids", status_code=status.HTTP_201_CREATED, tags=["VideoIds"])
async def create_video_id(
    media_id: int,
    video_type: str = Body(...),
    language: str = Body(default=""),
    youtube_id: str = Body(...),
) -> VideoIdRead:
    """Create a user-provided VideoId record for a media item."""
    from download.utils import extract_youtube_id
    clean_id = extract_youtube_id(youtube_id) or youtube_id
    return video_id_repo.create_user(
        media_id=media_id,
        video_type=video_type,
        language=language,
        youtube_id=clean_id,
    )


@media_router.delete("/{media_id}/video-ids/{video_id_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["VideoIds"])
async def delete_video_id(media_id: int, video_id_id: int):
    """Delete a user-provided VideoId record."""
    deleted = video_id_repo.delete(video_id_id=video_id_id, media_id=media_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VideoId {video_id_id} not found or not user-created",
        )
