import os

from fastapi import APIRouter, HTTPException, Response, status, Header

from app_logger import ModuleLogger
import db.repos.download as download_repo
import db.repos.file_info as file_info_repo
import db.repos.trailer_status as trailer_status_repo
from download import analysis as video_analysis
from services.files_service import FilesHandler, FolderInfo

logger = ModuleLogger("MediaFilesAPI")

files_router = APIRouter(prefix="/files", tags=["Files"])

CHUNK_SIZE = 1024 * 1024 * 5  # 5 MB

UNSAFE_PATHS = [".", "/app", "/bin", "/boot", "/etc", "/lib", "/sbin", "/usr", "/var"]


def _is_path_safe(path: str) -> bool:
    norm_path = os.path.normpath(path)
    abs_path = os.path.abspath(norm_path)
    for unsafe_path in UNSAFE_PATHS:
        if abs_path.startswith(unsafe_path):
            return False
    if abs_path.count("/") < 3:
        return False
    return True


@files_router.get("/files_raw")
async def get_all_media_files_raw() -> list[dict]:
    return file_info_repo.read_all_raw()


@files_router.get("/files_simple")
async def get_files_simple(path: str) -> list[FolderInfo]:
    try:
        files_handler = FilesHandler()
        return await files_handler.get_folder_files_simple(path)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@files_router.get("/video")
async def video_endpoint(file_path: str, range: str = Header(None)):
    if not _is_path_safe(file_path):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file path.")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="File not found.")
    _VALID_VIDEOS = [".mkv", ".mp4", ".avi", ".webm"]
    if not file_path.endswith(tuple(_VALID_VIDEOS)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not a video file.")
    start, end = range.replace("bytes=", "").split("-")
    filesize = os.path.getsize(file_path)
    start = int(start)
    end = int(end) if end else start + CHUNK_SIZE
    if end > filesize:
        end = filesize
    with open(file_path, "rb") as video:
        video.seek(start)
        data = video.read(end - start)
        headers = {
            "Content-Range": f"bytes {str(start)}-{str(end - 1)}/{filesize}",
            "Accept-Ranges": "bytes",
        }
        return Response(data, status_code=206, headers=headers, media_type="video/mp4")


@files_router.get("/read", status_code=status.HTTP_200_OK)
async def read_file(file_path: str) -> str:
    if not _is_path_safe(file_path):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file path.")
    file_ext = os.path.splitext(file_path)[1]
    VALID_FILE_TYPES = [".txt", ".srt", ".log", ".json", ".py", ".sh"]
    if file_ext not in VALID_FILE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type.")
    with open(file_path, "r") as file:
        return file.read().strip()


@files_router.get("/video_info", status_code=status.HTTP_200_OK)
def get_video_info(file_path: str) -> video_analysis.VideoInfo | None:
    if not _is_path_safe(file_path):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file path.")
    return video_analysis.get_media_info(file_path)


@files_router.post("/trim_video", status_code=status.HTTP_200_OK)
def trim_video(
    file_path: str,
    output_file: str,
    start_timestamp: int | float | str,
    end_timestamp: int | float | str,
) -> str:
    if not _is_path_safe(file_path):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file path.")
    try:
        res = video_analysis.trim_video(file_path, output_file, start_timestamp, end_timestamp)
    except Exception as e:
        logger.error(f"Error trimming video: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while trimming the video.",
        )
    return "Video trimmed successfully." if res else "Video trim failed."


@files_router.post("/rename", status_code=status.HTTP_200_OK)
async def rename_file_fol(old_path: str, new_path: str) -> bool:
    if not _is_path_safe(old_path) or not _is_path_safe(new_path):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file path.")
    return await FilesHandler.rename_file_fol(old_path, new_path)


@files_router.delete("/delete", status_code=status.HTTP_200_OK)
async def delete_file_fol(path: str, media_id: int = -1) -> bool:
    if not _is_path_safe(path):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file path.")
    deleted_status = await FilesHandler.delete_file_fol(path)
    if media_id != -1 and deleted_status:
        all_downloads = download_repo.read_by_media_id(media_id)
        is_trailer_file = False
        for d in all_downloads:
            if d.path == path:
                is_trailer_file = True
                download_repo.mark_as_deleted(d.id)
                trailer_status_repo.on_file_deleted(d.id)
        if is_trailer_file:
            logger.info(f"Trailer file deleted for media_id: {media_id}")
    return deleted_status
