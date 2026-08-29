"""Run yt-dlp and ffmpeg, and report what they did.

Both tools run as a subprocess with a timeout. Their output is logged
behind a marker that the log handler moves into the traceback column, so a
wall of tool output does not fill the Logs page.
"""

import shlex
import subprocess
import tempfile
import threading
import time
from pathlib import Path

from app_logger import ModuleLogger

from config.settings import app_settings
from database.models.trailerprofile import TrailerProfileRead
from services.trailers.video_conversion import get_ffmpeg_cmd
from exceptions import (
    ConversionFailedError,
    DownloadFailedError,
    StopEventSetError,
)

logger = ModuleLogger("TrailersDownloader")

YTDLP_TIMEOUT = 900  # 15 minutes timeout for subprocesses
FFMPEG_TIMEOUT = app_settings.ffmpeg_timeout * 60  # Convert minutes to seconds

# ffmpeg -i output1.mkv -c:v libx264 -c:a aac -c:s srt output1-converted3-264-aac-srt-cpu.mkv
# 3m44.35s - 53.29MB
# ffmpeg -i output1.mkv -c:v libx264 -preset veryfast -crf 22 -c:a aac -b:a 128k -c:s srt output1-converted3-264-aac-srt-cpu-fast.mkv  # noqa: E501
# 1m33.28s - 51.02MB
_VIDEO_CODECS = {
    "h264": "libx264",
    "h265": "libx265",
    "vp8": "libvpx",
    "vp9": "libvpx-vp9",
    "av1": "libaom-av1",
}
# Verify the codecs for NVIDIA, QSV and AMD
# ffmpeg -i output1.mkv -c:v h264_nvenc -c:a aac -b:a 128k -c:s srt output1-converted3-264-aac-srt-nvenc.mkv  # noqa: E501
# 15.82s - 49.70MB  # noqa: E501
# veryfast doesn't work with nvenc, use fast instead, crf needs to be changed to cq
# ffmpeg -i output1.mkv -c:v h264_nvenc -preset fast -cq 22 -c:a aac -b:a 128k -c:s srt output1-converted3-264-aac-srt-nvenc-fast.mkv  # noqa: E501
# 17.09s - 109.49MB
_VIDEO_CODECS_NVIDIA = {
    "h264": "h264_nvenc",
    "h265": "hevc_nvenc",
    "vp8": "libvpx",  # hw encoder not available
    "vp9": "libvpx-vp9",  # hw encoder not available
    "av1": "av1_nvenc",
}
# ffmpeg -init_hw_device vaapi=foo:/dev/dri/renderD128 -filter_hw_device foo -i output1.mkv -vf 'format=nv12,hwupload' -c:v h264_vaapi -c:a aac -c:s srt output1-converted3-264-aac-srt-i916hw.mkv  # noqa: E501
# 26.42s - 85.81MB
# preset doesn't work with vaapi, crf needs to be changed to qp
# ffmpeg -init_hw_device vaapi=foo:/dev/dri/renderD128 -filter_hw_device foo -i output1.mkv -vf 'format=nv12,hwupload' -c:v h264_vaapi -qp 22 -c:a aac -b:a 128k -c:s srt output1-converted3-264-aac-srt-i916hw-fast.mkv  # noqa: E501
# 27.10s - 62.67MB
_VIDEO_CODECS_QSV = {
    "h264": "h264_qsv",
    "h265": "hevc_qsv",
    "vp8": "libvpx",  # hw encoder not available
    "vp9": "libvpx-vp9",  # hw encoder not available
    "av1": "libaom-av1",  # hw encoder not available
}
_VIDEO_CODECS_AMD = {
    "h264": "h264_amf",
    "h265": "hevc_amf",
    "vp8": "libvpx",  # hw encoder not available
    "vp9": "libvpx-vp9",  # hw encoder not available
    "av1": "av1_amf",
}
_AUDIO_CODECS = {
    "aac": "aac",
    "ac3": "ac3",
    "eac3": "eac3",
    "mp3": "libmp3lame",
    "flac": "flac",
    "vorbis": "libvorbis",
    "opus": "libopus",
}


# Long/short forms of the same yt-dlp option, mapped to one canonical form
_YTDLP_OPTION_ALIASES = {
    "--format": "-f",
    "--output": "-o",
}


def _warn_user_overrides(
    trailarr_options: list[str], user_args: list[str]
) -> None:
    """Warn when profile extra options repeat an option Trailarr sets.

    Trailarr appends the profile's extra options after its own, and
    yt-dlp uses the last value of a repeated option. The user value
    stays active — this only makes the override visible in the logs.
    """

    def canonical(arg: str) -> str:
        arg = arg.split("=", 1)[0]  # normalize '--format=...' form
        return _YTDLP_OPTION_ALIASES.get(arg, arg)

    trailarr_flags = {
        canonical(arg) for arg in trailarr_options if arg.startswith("-")
    }
    # '-o' is set outside _get_ytdl_options, but Trailarr always sets it
    trailarr_flags.add("-o")
    for arg in user_args:
        if not arg.startswith("-"):
            continue
        if canonical(arg) in trailarr_flags:
            logger.warning(
                f"Profile yt-dlp extra option '{arg}' overrides an option"
                " that Trailarr sets. Trailarr uses the profile value."
            )


def _get_ytdl_options(profile: TrailerProfileRead) -> list[str]:
    """Get the YoutubeDL options for downloading the video"""
    _options: list[str] = []
    _options.append("--ffmpeg-location")
    _options.append(app_settings.ffmpeg_path)
    # _options.append("--no-warnings")
    _options.append("--no-playlist")
    # Livestreams have no end and would download until the subprocess
    # timeout, leaving multi-GB partial files behind (#626)
    _options.append("--match-filter")
    _options.append("!is_live & !is_upcoming")
    _options.append("--progress-delta")
    _options.append("3")  # Update progress every 3 seconds
    _options.append("--force-overwrites")  # Override files if exists

    # Add Format preferences
    _options.append("-f")
    _vres = f"[height<=?{profile.video_resolution}]"
    _vcodec = f"[vcodec={profile.video_format}]"
    if profile.video_format == "copy":
        # If the video format is copy, we will not filter by codec
        _vcodec = ""
    # Most of the current hardware struggles with av1 conversion
    # So, we will try and download from YT in av1 format directly if available
    if profile.video_format == "av1":
        _vcodec = "[vcodec^=av]"
    _acodec = f"[acodec={profile.audio_format}]"
    if profile.audio_format == "copy":
        # If the audio format is copy, we will not filter by codec
        _acodec = ""
    # Format 1: Best video and audio with the given resolution and codecs
    _format = f"bestvideo{_vres}{_vcodec}+bestaudio{_acodec}"
    # Format 2: Best video and audio with the given resolution and audio codec
    _format += f"/bestvideo{_vres}+bestaudio{_acodec}"
    # Format 3: Best video and audio with the given resolution and any codecs
    _format += f"/bestvideo{_vres}+bestaudio"
    # Format 4: Best video and audio with any resolution and codecs
    _format += "/bestvideo*+bestaudio/best"
    if profile.video_resolution == 0:
        # If resolution is best (0), use a simpler format
        _format = "bestvideo*+bestaudio/best"
    _options.append(_format)
    logger.debug(f"Using format: {_format}")

    # Subtitle options
    if profile.subtitles_enabled:
        # Uploader-provided subtitles
        _options.append("--write-subs")
        if profile.subtitles_auto_generated:
            # Also accept YouTube auto-generated subtitles. When both are
            # requested, yt-dlp prefers uploader subtitles for a language
            # and uses the auto-generated ones only as a fallback.
            _options.append("--write-auto-subs")
        _options.append("--embed-subs")
        _options.append("--sub-langs")
        _options.append(profile.subtitles_language)
        # Sleep for 15 seconds to reduce subtitles failures
        _options.append("--sleep-subtitles")
        _options.append("15")
    # Fragment retries option - Not needed as default is 10
    # _options.append("--fragment-retries")
    # _options.append("10")
    # Restrict filenames to avoid special characters
    _options.append("--restrict-filenames")
    # Merge output format
    _options.append("--merge-output-format")
    _options.append(profile.file_format)
    # Add cookies if available
    if app_settings.yt_cookies_path:
        logger.debug(f"Using cookies file: {app_settings.yt_cookies_path}")
        _options.append("--cookies")
        _options.append(app_settings.yt_cookies_path)
    # Embed metadata if enabled
    if profile.embed_metadata:
        _options.append("--embed-metadata")
    # Add Sponsorblock segments removal options if enabled
    # if app_settings.trailer_remove_sponsorblocks:
    #     _options.append("--sponsorblock-remove")
    #     _options.append("intro,outro")
    user_options = profile.ytdlp_extra_options
    if user_options:
        user_args = shlex.split(user_options)
        _warn_user_overrides(_options, user_args)
        _options.extend(user_args)
    return _options


def _find_downloaded_file(file_path: str | Path) -> str | None:
    """Find the downloaded file with the given file path.\n
    File extension should be one of:
        `.avi`, `.mkv`, `.mp4`, `.webm`
    Args:
        file_path (str | Path): Output file path template with %(ext)s
    Returns:
        str|None: The downloaded file path if found, None otherwise
    """
    file_path = Path(file_path)
    dir_path = file_path.parent
    base_name = file_path.name.replace("%(ext)s", "")
    VIDEO_EXTENSIONS = tuple([".avi", ".mkv", ".mp4", ".webm"])

    if dir_path.exists():
        for file in dir_path.iterdir():
            if file.name.startswith(base_name) and file.name.endswith(
                VIDEO_EXTENSIONS
            ):
                return str(file)
    return None


def cleanup_stale_temp_downloads() -> None:
    """Remove leftover files from the trailer temp download directory.

    Called at app startup — no download is in flight then, so anything in
    the directory is an orphan from a previous run, e.g. a partial file
    from a download that was killed mid-write (#626).
    """
    tmp_dir = Path(tempfile.gettempdir()) / "trailarr"
    if not tmp_dir.is_dir():
        return
    removed, freed = 0, 0
    for file in tmp_dir.iterdir():
        if not file.is_file():
            continue
        try:
            freed += file.stat().st_size
            file.unlink()
            removed += 1
        except OSError as e:
            logger.warning(
                f"Trailarr could not remove the old temporary file '{file}':"
                f" {e}"
            )
    if removed:
        logger.info(
            f"Trailarr removed {removed} old temporary download files and"
            f" freed {freed / 2**20:.1f} MB."
        )


def _cleanup_partial_downloads(file_path: str | Path) -> None:
    """Remove any files yt-dlp left behind for the given output template.

    A failed or timed-out yt-dlp process leaves `.part` (and intermediate
    format) files in place; on live content these can be many GB (#626).
    """
    path = Path(file_path)
    if "%(ext)s" in path.name:
        base_name = path.name.replace("%(ext)s", "").rstrip(".")
    else:
        # Literal name (e.g. temp_311-trailer.mkv) — match on the stem so
        # intermediate/partial variants (.mkv.part, .f616.mp4.part) match too
        base_name = path.stem
    if not base_name or not path.parent.is_dir():
        return
    for file in path.parent.iterdir():
        # Require a "." delimiter after the base name (.mkv, .mkv.part,
        # .f616.mp4.part) so e.g. "temp_311-trailer2.mkv" never matches
        if file.name != base_name and not file.name.startswith(
            f"{base_name}."
        ):
            continue
        try:
            file.unlink()
            logger.info(
                f"Trailarr removed the incomplete download file '{file}'."
            )
        except OSError as e:
            logger.warning(
                f"Trailarr could not remove the incomplete file '{file}': {e}"
            )


def _download_with_ytdlp(
    url: str, file_path: str, profile: TrailerProfileRead
) -> str:
    """Download the video using yt-dlp from the given URL
    Args:
        url (str): URL of the video
        file_path (str): Output file path
        profile (TrailerProfileRead): Trailer profile used for downloading
    Raises:
        DownloadFailedError: Error while downloading video
    Returns:
        str: Success message if the video is downloaded successfully
    """
    ytdlp_cmd: list[str] = [app_settings.ytdlp_path, "-o", file_path]
    ytdlp_cmd.extend(_get_ytdl_options(profile))
    ytdlp_cmd.append(url)
    # Download the video
    logger.debug(f"Downloading video with options: {ytdlp_cmd}")

    try:
        result = subprocess.run(
            ytdlp_cmd,
            capture_output=True,
            text=True,
            timeout=YTDLP_TIMEOUT,  # 15 minutes timeout
            encoding="utf-8",
            errors="replace",
        )

        # Collect output for error reporting
        combined_output = ""
        if result.stdout:
            combined_output += f"STDOUT:\n{result.stdout}\n"
        if result.stderr:
            combined_output += f"STDERR:\n{result.stderr}"

        # Check for sign-in errors in stderr
        if result.stderr:
            stderr_lower = result.stderr.lower()
            if "sign in" in stderr_lower:
                msg = "Sign in required to download video"
                if "age restricted" in stderr_lower:
                    msg = "Video is age restricted, sign in to download"
                elif "not a bot" in stderr_lower:
                    msg = (
                        "Youtube bot detection kicked in, sign in to download"
                    )
                raise DownloadFailedError(msg, output=combined_output)

        if result.returncode != 0:
            msg = f"yt-dlp command failed with exit code {result.returncode}"
            raise DownloadFailedError(
                f"Error downloading video. {msg}", output=combined_output
            )

        # Find the downloaded file
        downloaded_file = _find_downloaded_file(file_path)
        if not downloaded_file:
            if "does not pass filter" in combined_output:
                raise DownloadFailedError(
                    "Video skipped: livestream/premiere or filtered out",
                    output=combined_output,
                )
            raise DownloadFailedError(
                "Downloaded file not found", output=combined_output
            )

        # Only log the full output on success (errors carry it in the exception)
        if combined_output:
            logger.debug(f"YT-DLP Output::\n{combined_output}")

    except subprocess.TimeoutExpired:
        _cleanup_partial_downloads(file_path)
        msg = "yt-dlp download timed out after 15 minutes"
        raise DownloadFailedError(msg)
    except DownloadFailedError:
        _cleanup_partial_downloads(file_path)
        raise
    except FileNotFoundError:
        _cleanup_partial_downloads(file_path)
        msg = (
            "yt-dlp executable not found at"
            f" '{app_settings.ytdlp_path}'. Set YTDLP_PATH in the .env"
            " file in APP_DATA_DIR to the full path of the yt-dlp"
            " executable."
        )
        raise DownloadFailedError(msg)
    except Exception as e:
        _cleanup_partial_downloads(file_path)
        msg = f"Error running yt-dlp process: {str(e)}"
        raise DownloadFailedError(msg)

    logger.info(
        "Trailarr downloaded the video."
    )
    return downloaded_file


def _convert_video(
    profile: TrailerProfileRead, input_file: str, output_file: str, retry=True
) -> str:
    """Convert the video to the desired format
    Args:
        profile (TrailerProfileRead): Trailer profile used for conversion
        input_file (str): Input video file path
        output_file (str): Output video file path
        retry (bool, Optional=True): Retry the conversion without hardware acceleration. \
            If conversion fails, retry without hardware acceleration once
    Raises:
        ConversionFailedError: Error while converting video
    Returns:
        str: Success message if the video is converted successfully
    """
    # Get the ffmpeg command for conversion
    ffmpeg_cmd = get_ffmpeg_cmd(
        profile, input_file, output_file, fallback=not retry
    )
    # Convert the video
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

        # Collect output for error reporting
        combined_output = ""
        if result.stdout:
            combined_output += f"STDOUT:\n{result.stdout}\n"
        if result.stderr:
            combined_output += f"STDERR:\n{result.stderr}"

        if result.returncode != 0:
            # If the conversion fails, retry without hardware acceleration
            if retry:
                logger.warning(
                    "The conversion with FFmpeg failed with exit code"
                    f" {result.returncode}. Trailarr tries again without hardware"
                    " acceleration."
                )
                if combined_output:
                    logger.warning(f"FFMPEG Output::\n{combined_output}")
                # Retry the conversion with fallback
                return _convert_video(
                    profile, input_file, output_file, retry=False
                )
            # If the conversion fails again, raise an exception
            msg = f"FFmpeg command failed with exit code {result.returncode}"
            raise ConversionFailedError(
                f"Error converting video. {msg}", output=combined_output
            )

        # Only log the full output on success (errors carry it in the exception)
        if combined_output:
            logger.debug(f"FFMPEG Output::\n{combined_output}")

    except subprocess.TimeoutExpired:
        msg = "FFmpeg conversion timed out after 15 minutes"
        raise ConversionFailedError(msg)
    except FileNotFoundError:
        msg = (
            "ffmpeg executable not found at"
            f" '{app_settings.ffmpeg_path}'. Set FFMPEG_PATH in the .env"
            " file in APP_DATA_DIR to the full path of the ffmpeg"
            " executable."
        )
        raise ConversionFailedError(msg)
    except Exception as e:
        msg = f"Error running FFmpeg process: {str(e)}"
        raise ConversionFailedError(msg)

    logger.info(
        "Trailarr converted the video."
    )
    return "Video converted successfully"


def download_video(
    url: str,
    file_path: str | Path,
    profile: TrailerProfileRead,
    _stop_event: threading.Event | None = None,
) -> str:
    """Download the video from the given URL
    Args:
        url (str): URL of the video
        file_path (str | Path): Output file path template with %(ext)s
        profile (TrailerProfileRead): Trailer profile used for downloading
        _stop_event (threading.Event, optional=None): Event to signal stopping the download.
    Returns:
        str: The downloaded (and converted) video file path
    Raises:
        DownloadFailedError: Error while downloading video
        ConversionFailedError: Error while converting video
        StopEventSetError: If the stop event is set during the download.
    """
    file_path = Path(file_path)
    file_name = file_path.name
    temp_file_path = str(file_path.with_name(f"temp_{file_name}"))

    # Download the video using yt-dlp
    start_time = time.perf_counter()  # Download start time
    download_file_path = _download_with_ytdlp(url, temp_file_path, profile)
    end_time = time.perf_counter()  # Download end time / Conversion start time
    logger.debug(f"Trailer downloaded in {end_time - start_time:.2f}s")

    # Stop if stop event is set
    if _stop_event and _stop_event.is_set():
        logger.info(
            f"Trailarr stopped the download of {url}. A stop was requested."
        )
        raise StopEventSetError("Stop event set during video download")

    # Add the file extension from download file to the output file
    converted_file_path = str(file_path).replace(
        "%(ext)s", profile.file_format
    )

    # Convert the video to the desired format
    _convert_video(profile, download_file_path, converted_file_path)
    logger.debug(f"Trailer converted in {time.perf_counter() - end_time:.2f}s")
    Path(download_file_path).unlink()
    logger.info(
        "Trailarr downloaded and converted the video."
    )
    return converted_file_path
