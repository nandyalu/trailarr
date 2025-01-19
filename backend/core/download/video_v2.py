import os
import subprocess
from app_logger import ModuleLogger
from config.settings import app_settings


logger = ModuleLogger("TrailersDownloader2")
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


def _get_ytdl_options() -> list[str]:
    """Get the YoutubeDL options for downloading the video"""
    _options: list[str] = []
    _options.append("--ffmpeg-location")
    _options.append("/usr/local/bin/ffmpeg")
    # _options.append("--no-warnings")
    _options.append("--no-playlist")
    _options.append("--progress-delta")
    _options.append("3")  # Update progress every 3 seconds
    # Add Format
    _options.append("-f")
    _options.append(f"bestvideo[height<=?{app_settings.trailer_resolution}]+bestaudio")
    # Subtitle options
    if app_settings.trailer_subtitles_enabled:
        _options.append("--write-auto-subs")
        _options.append("--embed-subs")
        _options.append("--sub-lang")
        _options.append(app_settings.trailer_subtitles_language)
        # _options.append("--sub-format")
        # if app_settings.trailer_subtitles_format:
        #     _options.append(app_settings.trailer_subtitles_format)
        # else:
        #     _options.append("srt")
    # Fragment retries option - Not needed as default is 10
    # _options.append("--fragment-retries")
    # _options.append("10")
    # Restrict filenames to avoid special characters
    _options.append("--restrict-filenames")
    # Merge output format
    _options.append("--merge-output-format")
    _options.append(app_settings.trailer_file_format)
    # Add cookies if available
    if app_settings.yt_cookies_path:
        logger.info(f"Using cookies file: {app_settings.yt_cookies_path}")
        # _options.append("--cookies")
        # _options.append(app_settings.yt_cookies_path)
    _options.append("--cookies")
    _options.append("/config/cookies.txt")
    # Embed metadata if enabled
    if app_settings.trailer_embed_metadata:
        _options.append("--embed-metadata")
    # Add Sponsorblock segments removal options if enabled
    # if app_settings.trailer_remove_sponsorblocks:
    #     _options.append("--sponsorblock-remove")
    #     _options.append("intro,outro")
    return _options


def _download_with_ytdlp(url: str, file_path: str) -> str:
    """Download the video using yt-dlp from the given URL
    Args:
        url (str): URL of the video
        file_path (str): Output file path
    Raises:
        Exception: Error starting the process
        Exception: Error downloading video
    Returns:
        str: Success message if the video is downloaded successfully
    """
    ytdlp_cmd: list[str] = ["yt-dlp", "-o", file_path]
    ytdlp_cmd.extend(_get_ytdl_options())
    ytdlp_cmd.append(url)
    # Download the video
    logger.debug(f"Downloading video with options: {ytdlp_cmd}")
    with subprocess.Popen(
        ytdlp_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    ) as process:
        if not process.stdout or not process.stderr:
            # logger.error("Failed to start yt-dlp process")
            raise Exception("Failed to start yt-dlp process")
        for line in process.stdout:
            logger.debug(line.strip())
        for line in process.stderr:
            line = line.strip()
            if "sign in" in line.lower():
                msg = line.strip()
                if "age restricted" in line.lower():
                    msg = "Video is age restricted, sign in to download"
                if "not a bot" in line.lower():
                    msg = "Youtube bot detection kicked in, sign in to download"
                logger.error(msg)
                raise Exception(msg)
            logger.debug(line.strip())
            # raise Exception("Error downloading video")
    # Check if the process is successful
    if process.returncode != 0:
        logger.error(f"Command failed with exit code {process.returncode}")
        raise Exception("Error downloading video")
    logger.info("Video downloaded successfully")
    return file_path.replace("%(ext)s", app_settings.trailer_file_format)
    # return "Video downloaded successfully"


def _get_ffmpeg_cmd(input_file: str, output_file: str) -> list[str]:
    """Generate the ffmpeg command based on the environment and settings"""
    ffmpeg_cmd: list[str] = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "warning",
        "-i",
        input_file,
        "-c:v",
    ]
    # Remove the NVIDIA and QSV options - producing more errors
    # if int(os.getenv("NVIDIA_GPU_AVAILABLE", "0")):
    #     ffmpeg_cmd.append(_VIDEO_CODECS_NVIDIA[app_settings.trailer_video_format])
    # elif int(os.getenv("QSV_GPU_AVAILABLE", "0")):
    #     # ffmpeg -init_hw_device vaapi=foo:/dev/dri/renderD128 -filter_hw_device foo -i output1.mkv -vf 'format=nv12,hwupload' -c:v h264_vaapi -c:a aac -b:a 128k -c:s srt output.mkv  # noqa: E501
    #     ffmpeg_cmd = [
    #         "ffmpeg",
    #         "-hide_banner",
    #         "-loglevel",
    #         "warning",
    #         "-init_hw_device",
    #         "vaapi=foo:/dev/dri/renderD128",
    #         "-filter_hw_device",
    #         "foo",
    #         "-i",
    #         input_file,
    #         "-vf",
    #         "format=nv12,hwupload",
    #         "-c:v",
    #     ]
    #     ffmpeg_cmd.append(_VIDEO_CODECS_QSV[app_settings.trailer_video_format])
    #     ffmpeg_cmd.append("-qp")
    #     ffmpeg_cmd.append("22")
    # else:
    ffmpeg_cmd.append(_VIDEO_CODECS[app_settings.trailer_video_format])
    ffmpeg_cmd.append("-preset")
    ffmpeg_cmd.append("veryfast")
    ffmpeg_cmd.append("-crf")
    ffmpeg_cmd.append("22")

    # Apply audio volume level filter if enabled
    if app_settings.trailer_audio_volume_level != 100:
        volume_level = app_settings.trailer_audio_volume_level * 0.01
        ffmpeg_cmd.append("-af")
        ffmpeg_cmd.append(f"volume={volume_level}")
    # Set audio specific options
    ffmpeg_cmd.append("-c:a")
    ffmpeg_cmd.append(_AUDIO_CODECS[app_settings.trailer_audio_format])
    ffmpeg_cmd.append("-b:a")
    ffmpeg_cmd.append("128k")
    # Set subtitle specific options
    if app_settings.trailer_subtitles_enabled:
        ffmpeg_cmd.append("-c:s")
        ffmpeg_cmd.append(app_settings.trailer_subtitles_format)
    # Add web optimized options if enabled
    if app_settings.trailer_web_optimized:
        # Below options are for fast streaming, but might increase filesize
        ffmpeg_cmd.append("-movflags")
        ffmpeg_cmd.append("+faststart")
        ffmpeg_cmd.append("-tune")
        ffmpeg_cmd.append("zerolatency")
    ffmpeg_cmd.append(output_file)

    return ffmpeg_cmd


def _convert_video(input_file: str, output_file: str) -> str:
    """Convert the video to the desired format
    Args:
        input_file (str): Input video file path
        output_file (str): Output video file path
    Raises:
        Exception: Error converting video
    Returns:
        str: Success message if the video is converted successfully
    """
    ffmpeg_cmd = _get_ffmpeg_cmd(input_file, output_file)
    # Convert the video
    logger.debug(f"Converting video with options: {ffmpeg_cmd}")
    with subprocess.Popen(
        ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    ) as process:
        if not process.stdout or not process.stderr:
            # logger.error("Failed to start ffmpeg process")
            raise Exception("Failed to start ffmpeg process")
        for line in process.stdout:
            logger.debug(line.strip())
        for line in process.stderr:
            logger.debug(line.strip())

    if process.returncode != 0:
        logger.error(f"Command failed with exit code {process.returncode}")
        raise Exception("Error converting video")
    logger.info("Video converted successfully")
    return "Video converted successfully"


def download_video(url: str, file_path: str) -> str:
    """Download the video from the given URL
    Args:
        url (str): URL of the video
        file_path (str): Output file path template with %(ext)s
    Raises:
        Exception: Error downloading/converting video
    Returns:
        str: Success message if the video is downloaded successfully
    """
    try:
        # Download the video using yt-dlp
        file_name = os.path.basename(file_path)
        temp_file_path = file_path.replace(file_name, f"temp_{file_name}")
        download_file_path = _download_with_ytdlp(url, temp_file_path)
        # Add the file extension from download file to the output file
        converted_file_path = file_path.replace(
            "%(ext)s", download_file_path.split(".")[-1]
        )
        # Convert the video to the desired format
        _convert_video(download_file_path, converted_file_path)
        os.remove(temp_file_path)
    except Exception as e:
        logger.error(f"Error downloading video: {e}")
        return ""
    logger.info("Video downloaded successfully")
    return converted_file_path


# if __name__ == "__main__":
# download_video("https://www.youtube.com/watch?v=WHXq62VCaCM", "output.mkv")
# Age restricted video
# download_video("https://www.youtube.com/watch?v=pLWda_RrQn4", "output2.mkv")
# download_video("https://www.youtube.com/watch?v=IS_-maoP9Qs", "output3.mkv")
# _convert_video("temp_output2.mkv", "output2-converted.mkv")