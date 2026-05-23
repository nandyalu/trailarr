import shlex
import subprocess
import threading
import time
from pathlib import Path

from app_logger import ModuleLogger
from config.settings import app_settings
from db.models.trailerprofile import TrailerProfileRead
from download.conversion import get_ffmpeg_cmd
from exceptions import ConversionFailedError, DownloadFailedError, StopEventSetError

logger = ModuleLogger("TrailersDownloader")

YTDLP_TIMEOUT = 900  # 15 minutes
FFMPEG_TIMEOUT = app_settings.ffmpeg_timeout * 60  # minutes → seconds


def _get_ytdl_options(profile: TrailerProfileRead) -> list[str]:
    _options: list[str] = []
    _options.extend(["--ffmpeg-location", app_settings.ffmpeg_path])
    _options.append("--no-playlist")
    _options.extend(["--progress-delta", "3"])
    _options.append("--force-overwrites")

    _options.append("-f")
    _vres = f"[height<=?{profile.video_resolution}]"
    _vcodec = f"[vcodec={profile.video_format}]"
    if profile.video_format == "copy":
        _vcodec = ""
    if profile.video_format == "av1":
        _vcodec = "[vcodec^=av]"
    _acodec = f"[acodec={profile.audio_format}]"
    if profile.audio_format == "copy":
        _acodec = ""
    _format = f"bestvideo{_vres}{_vcodec}+bestaudio{_acodec}"
    _format += f"/bestvideo{_vres}+bestaudio{_acodec}"
    _format += f"/bestvideo{_vres}+bestaudio"
    _format += "/bestvideo*+bestaudio/best"
    if profile.video_resolution == 0:
        _format = "bestvideo*+bestaudio/best"
    _options.append(_format)
    logger.debug(f"Using format: {_format}")

    if profile.subtitles_enabled:
        _options.append("--write-auto-subs")
        _options.append("--embed-subs")
        _options.extend(["--sub-langs", profile.subtitles_language])
        _options.extend(["--sleep-subtitles", "15"])
    _options.append("--restrict-filenames")
    _options.extend(["--merge-output-format", profile.file_format])
    if app_settings.yt_cookies_path:
        logger.debug(f"Using cookies file: {app_settings.yt_cookies_path}")
        _options.extend(["--cookies", app_settings.yt_cookies_path])
    if profile.embed_metadata:
        _options.append("--embed-metadata")
    user_options = profile.ytdlp_extra_options
    if user_options:
        user_args = shlex.split(user_options)
        _options.extend(user_args)
    return _options


def _find_downloaded_file(file_path: str | Path) -> str | None:
    file_path = Path(file_path)
    dir_path = file_path.parent
    base_name = file_path.name.replace("%(ext)s", "")
    VIDEO_EXTENSIONS = tuple([".avi", ".mkv", ".mp4", ".webm"])
    if dir_path.exists():
        for file in dir_path.iterdir():
            if file.name.startswith(base_name) and file.name.endswith(VIDEO_EXTENSIONS):
                return str(file)
    return None


def _download_with_ytdlp(url: str, file_path: str, profile: TrailerProfileRead) -> str:
    ytdlp_cmd: list[str] = [app_settings.ytdlp_path, "-o", file_path]
    ytdlp_cmd.extend(_get_ytdl_options(profile))
    ytdlp_cmd.append(url)
    logger.debug(f"Downloading video with options: {ytdlp_cmd}")
    try:
        result = subprocess.run(
            ytdlp_cmd,
            capture_output=True,
            text=True,
            timeout=YTDLP_TIMEOUT,
            encoding="utf-8",
            errors="replace",
        )
        combined_output = ""
        if result.stdout:
            combined_output += f"STDOUT:\n{result.stdout}\n"
        if result.stderr:
            combined_output += f"STDERR:\n{result.stderr}"
        if result.stderr:
            stderr_lower = result.stderr.lower()
            if "sign in" in stderr_lower:
                msg = "Sign in required to download video"
                if "age restricted" in stderr_lower:
                    msg = "Video is age restricted, sign in to download"
                elif "not a bot" in stderr_lower:
                    msg = "Youtube bot detection kicked in, sign in to download"
                raise DownloadFailedError(msg, output=combined_output)
        if result.returncode != 0:
            msg = f"yt-dlp command failed with exit code {result.returncode}"
            raise DownloadFailedError(f"Error downloading video. {msg}", output=combined_output)
        downloaded_file = _find_downloaded_file(file_path)
        if not downloaded_file:
            raise DownloadFailedError("Downloaded file not found", output=combined_output)
        if combined_output:
            logger.debug(f"YT-DLP Output::\n{combined_output}")
    except subprocess.TimeoutExpired:
        raise DownloadFailedError("yt-dlp download timed out after 15 minutes")
    except Exception as e:
        raise DownloadFailedError(f"Error running yt-dlp process: {str(e)}")
    logger.info("Video downloaded successfully")
    return downloaded_file


def _convert_video(
    profile: TrailerProfileRead, input_file: str, output_file: str, retry: bool = True
) -> str:
    ffmpeg_cmd = get_ffmpeg_cmd(profile, input_file, output_file, fallback=not retry)
    logger.debug(f"Converting video with options: {ffmpeg_cmd}")
    try:
        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True,
            timeout=FFMPEG_TIMEOUT,
            encoding="utf-8",
            errors="replace",
        )
        combined_output = ""
        if result.stdout:
            combined_output += f"STDOUT:\n{result.stdout}\n"
        if result.stderr:
            combined_output += f"STDERR:\n{result.stderr}"
        if result.returncode != 0:
            if retry:
                logger.warning(
                    f"FFmpeg conversion failed with exit code {result.returncode},"
                    " retrying without hardware acceleration"
                )
                if combined_output:
                    logger.warning(f"FFMPEG Output::\n{combined_output}")
                return _convert_video(profile, input_file, output_file, retry=False)
            msg = f"FFmpeg command failed with exit code {result.returncode}"
            raise ConversionFailedError(f"Error converting video. {msg}", output=combined_output)
        if combined_output:
            logger.debug(f"FFMPEG Output::\n{combined_output}")
    except subprocess.TimeoutExpired:
        raise ConversionFailedError("FFmpeg conversion timed out after 15 minutes")
    except Exception as e:
        raise ConversionFailedError(f"Error running FFmpeg process: {str(e)}")
    logger.info("Video converted successfully")
    return "Video converted successfully"


def download_video(
    url: str,
    file_path: str | Path,
    profile: TrailerProfileRead,
    _stop_event: threading.Event | None = None,
) -> str:
    file_path = Path(file_path)
    file_name = file_path.name
    temp_file_path = str(file_path.with_name(f"temp_{file_name}"))

    start_time = time.perf_counter()
    download_file_path = _download_with_ytdlp(url, temp_file_path, profile)
    end_time = time.perf_counter()
    logger.debug(f"Trailer downloaded in {end_time - start_time:.2f}s")

    if _stop_event and _stop_event.is_set():
        logger.info(f"Stop Event set, stopping download for {url}")
        raise StopEventSetError("Stop event set during video download")

    converted_file_path = str(file_path).replace("%(ext)s", profile.file_format)
    _convert_video(profile, download_file_path, converted_file_path)
    logger.debug(f"Trailer converted in {time.perf_counter() - end_time:.2f}s")
    Path(download_file_path).unlink()
    logger.info("Video download and conversion completed successfully")
    return converted_file_path
