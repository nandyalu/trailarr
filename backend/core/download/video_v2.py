import os
import shlex
import subprocess
import time
from app_logger import ModuleLogger

from config.settings import app_settings
from core.base.database.models.trailerprofile import TrailerProfileRead
from core.download.video_conversion import get_ffmpeg_cmd
from exceptions import ConversionFailedError, DownloadFailedError

logger = ModuleLogger("TrailersDownloader")

SUBPROCESS_TIMEOUT = 900  # 15 minutes timeout for subprocesses

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


def _get_ytdl_options(profile: TrailerProfileRead) -> list[str]:
    """Get the YoutubeDL options for downloading the video"""
    _options: list[str] = []
    _options.append("--ffmpeg-location")
    _options.append(app_settings.ffmpeg_path)
    # _options.append("--no-warnings")
    _options.append("--no-playlist")
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
    _format += "/bestvideo*+bestaudio*/best"
    _options.append(_format)
    logger.debug(f"Using format: {_format}")

    # Subtitle options
    if profile.subtitles_enabled:
        _options.append("--write-auto-subs")
        _options.append("--embed-subs")
        _options.append("--sub-langs")
        _options.append(profile.subtitles_language)
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
        _options.extend(user_args)
    return _options


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
            timeout=SUBPROCESS_TIMEOUT,  # 15 minutes timeout
            encoding="utf-8",
            errors="replace",
        )

        # Log all output in a single call and check for sign-in errors
        combined_output = ""
        if result.stdout:
            combined_output += f"STDOUT:\n{result.stdout}\n"
        if result.stderr:
            combined_output += f"STDERR:\n{result.stderr}"

        if combined_output:
            logger.debug(f"YT-DLP Output::\n{combined_output}")

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
                raise DownloadFailedError(msg)

        if result.returncode != 0:
            msg = f"yt-dlp command failed with exit code {result.returncode}"
            raise DownloadFailedError(f"Error downloading video. {msg}")

    except subprocess.TimeoutExpired:
        msg = "yt-dlp download timed out after 15 minutes"
        raise DownloadFailedError(msg)
    except Exception as e:
        msg = f"Error running yt-dlp process: {str(e)}"
        raise DownloadFailedError(msg)

    logger.info("Video downloaded successfully")
    return file_path.replace("%(ext)s", profile.file_format)
    # return "Video downloaded successfully"


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
            timeout=SUBPROCESS_TIMEOUT,  # 15 minutes timeout
            encoding="utf-8",
            errors="replace",
        )

        # Log all output in a single call
        combined_output = ""
        if result.stdout:
            combined_output += f"STDOUT:\n{result.stdout}\n"
        if result.stderr:
            combined_output += f"STDERR:\n{result.stderr}"

        if combined_output:
            logger.debug(f"FFMPEG Output::\n{combined_output}")

        if result.returncode != 0:
            # If the conversion fails, retry without hardware acceleration
            if retry:
                logger.warning(
                    "FFmpeg conversion failed with exit code"
                    f" {result.returncode}, retrying without hardware"
                    " acceleration (if enabled)"
                )
                # Retry the conversion with fallback
                return _convert_video(
                    profile, input_file, output_file, retry=False
                )
            # If the conversion fails again, raise an exception
            msg = f"FFmpeg command failed with exit code {result.returncode}"
            raise ConversionFailedError(f"Error converting video. {msg}")

    except subprocess.TimeoutExpired:
        msg = "FFmpeg conversion timed out after 15 minutes"
        raise ConversionFailedError(msg)
    except Exception as e:
        msg = f"Error running FFmpeg process: {str(e)}"
        raise ConversionFailedError(msg)

    logger.info("Video converted successfully")
    return "Video converted successfully"


def _cleanup_files(file_path: str):
    """Cleanup the temporary files created during the download and conversion"""
    # Check if a file already exists at the given path, delete it
    dir_name = os.path.dirname(file_path)
    if os.path.exists(dir_name):
        for file in os.listdir(dir_name):
            file_name_wo_ext, file_ext = os.path.splitext(file)
            if file_name_wo_ext in file:
                os.remove(os.path.join(dir_name, file))


def download_video(
    url: str, file_path: str, profile: TrailerProfileRead
) -> str:
    """Download the video from the given URL
    Args:
        url (str): URL of the video
        file_path (str): Output file path template with %(ext)s
        profile (TrailerProfileRead): Trailer profile used for downloading
    Raises:
        DownloadFailedError: Error while downloading video
        ConversionFailedError: Error while converting video
    Returns:
        str: Success message if the video is downloaded successfully
    """
    # try:
    # Get the file name from the file path
    file_name = os.path.basename(file_path)
    temp_file_path = file_path.replace(file_name, f"temp_{file_name}")
    # Cleanup the temporary files
    _cleanup_files(file_path)

    # Download the video using yt-dlp
    start_time = time.perf_counter()  # Download start time
    download_file_path = _download_with_ytdlp(url, temp_file_path, profile)
    end_time = time.perf_counter()  # Download end time / Conversion start time
    logger.debug(f"Trailer downloaded in {end_time - start_time:.2f}s")

    # Add the file extension from download file to the output file
    converted_file_path = file_path.replace(
        "%(ext)s", download_file_path.split(".")[-1]
    )
    # Convert the video to the desired format
    _convert_video(profile, download_file_path, converted_file_path)
    logger.debug(f"Trailer converted in {time.perf_counter() - end_time:.2f}s")
    os.remove(download_file_path)
    # except Exception as e:
    #     logger.error(f"Error downloading video: {e}")
    #     return ""
    logger.info("Video download and conversion completed successfully")
    return converted_file_path
