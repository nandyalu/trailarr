from datetime import datetime, timezone
import os
from pathlib import Path
import re
import subprocess
import json
from typing import Any

from pydantic import BaseModel

from app_logger import ModuleLogger
from config.settings import app_settings
from core.download.trailers.utils import extract_youtube_id

logger = ModuleLogger("VideoAnalysis")


class StreamInfo(BaseModel):

    index: int
    codec_type: str
    codec_name: str
    coded_height: int = 0
    coded_width: int = 0
    audio_channels: int = 0
    sample_rate: int = 0
    language: str = ""
    duration: str = ""


class VideoInfo(BaseModel):

    name: str
    file_path: str
    format_name: str
    duration_seconds: int = 0
    duration: str = "0:00:00"
    size: int = 0
    bitrate: str = "0 bps"
    streams: list[StreamInfo]
    youtube_id: str | None = None
    youtube_channel: str = "unknownchannel"
    created_at: datetime
    updated_at: datetime


def convert_duration(duration_seconds: str) -> str:
    duration = int(float(duration_seconds))
    hours, remainder = divmod(duration, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}:{minutes:02}:{seconds:02}"


def convert_bitrate(bit_rate: str) -> str:
    # Convert to human readable format
    value = int(bit_rate)
    _rate = 1000 * 1000 * 1000  # 1 Gbps
    if value > _rate:
        return f"{value / _rate:.2f} Gbps"
    _rate = 1000 * 1000  # 1 Mbps
    if value > _rate:
        return f"{value / _rate:.2f} Mbps"
    _rate = 1000  # 1 Kbps
    if value > _rate:
        return f"{value / _rate:.2f} kbps"
    return f"{value} bps"


def get_media_info(file_path: str) -> VideoInfo | None:
    """
    Get media information using ffprobe. \n
    Args:
        file_path (str): Path to the media file. \n
    Returns:
        VideoInfo|None: VideoInfo object if successful, None otherwise.
    """
    entries_required = (
        "format=format_name,duration,size,bit_rate :"
        " format_tags=comment,purl,artist,description,synopsis,YouTube,youtube_id,creation_time"
        " : stream=index,codec_type,codec_name,coded_height,coded_width,channels,sample_rate"
        " : stream_tags=language,duration,name"
    )
    ffprobe_cmd = [
        app_settings.ffprobe_path,
        "-v",
        "error",
        "-show_entries",
        entries_required,
        "-of",
        "json",
        file_path,
    ]
    try:
        logger.debug(f"Running media analysis for: {file_path}")
        # Run ffprobe command to get media info
        result = subprocess.run(
            ffprobe_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        # Return None if command failed
        if result.returncode != 0:
            logger.error(f"Error: {result.stderr}")
            return None

        # If command ran successfully, parse the output
        info = json.loads(result.stdout)
        format: dict[str, Any] = info.get("format", {})
        format_tags: dict[str, str] = format.get("tags", {})

        # Extract YouTube ID from format tags
        youtube_id = None
        youtube_channel = "unknownchannel"
        for tag_key, tag_value in format_tags.items():
            if tag_key.lower().strip() == "artist":
                youtube_channel = tag_value or "unknownchannel"
                continue
            if not youtube_id:
                youtube_id = extract_youtube_id(tag_value)
            if youtube_id and youtube_channel != "unknownchannel":
                break

        # Get file timestamps
        file_path_obj = Path(file_path)
        file_stat = file_path_obj.stat()
        created_at = datetime.fromtimestamp(
            file_stat.st_mtime, tz=timezone.utc
        ) or datetime.now(timezone.utc)
        updated_at = datetime.fromtimestamp(
            file_stat.st_ctime, tz=timezone.utc
        ) or datetime.now(timezone.utc)

        # Create VideoInfo object
        video_info = VideoInfo(
            name=os.path.basename(file_path),
            file_path=file_path,
            format_name=os.path.splitext(file_path)[1].lower().strip("."),
            duration_seconds=int(float(format.get("duration", "0"))),
            duration=convert_duration(format.get("duration", "0")),
            size=int(format.get("size", "0")),
            bitrate=convert_bitrate(format.get("bit_rate", "0")),
            streams=[],
            youtube_id=youtube_id,
            youtube_channel=youtube_channel,
            created_at=created_at,
            updated_at=updated_at,
        )
        # Loop through streams and create StreamInfo objects
        for stream in info["streams"]:
            _language = ""
            if "tags" in stream and "language" in stream["tags"]:
                _language = stream["tags"]["language"]
            _duration = "0"
            if "tags" in stream and "DURATION" in stream["tags"]:
                _duration = stream["tags"]["DURATION"]
            if "tags" in stream and "duration" in stream["tags"]:
                _duration = stream["tags"]["duration"]
            stream_info = StreamInfo(
                index=int(stream.get("index", 0)),
                codec_type=str(stream.get("codec_type", "N/A")),
                codec_name=str(stream.get("codec_name", "N/A")),
                coded_height=int(stream.get("coded_height", 0)),
                coded_width=int(stream.get("coded_width", 0)),
                audio_channels=int(stream.get("channels", 0)),
                sample_rate=int(stream.get("sample_rate", 0)),
                language=_language,
                duration=_duration,
            )
            video_info.streams.append(stream_info)
        return video_info
    except Exception as e:
        logger.exception(f"Error extracting video info: {str(e)}")
    return None


def verify_trailer_streams(
    trailer_path: str, min_duration: int = 10, max_duration: int = 1200
) -> bool | None:
    """
    Check if the trailer has audio and video streams. \n
    Args:
        trailer_path (str): Path to the trailer file.
        min_duration (int): Minimum duration of the trailer in seconds. \
            Default is 10 seconds.
        max_duration (int): Maximum duration of the trailer in seconds. \
            Default is 1200 seconds (20 minutes).
    Returns:
        Result (bool | None):
            - True: Trailer has both audio and video streams within duration limits.
            - False: Trailer is missing audio or video streams, or duration is out of bounds.
            - None: File missing, could not be analyzed, duration is zero.
    """
    # Check trailer file exists
    logger.debug(f"Verifying trailer streams for: {trailer_path}")
    if not trailer_path:
        return None
    # Get media analysis for the trailer
    media_info = get_media_info(trailer_path)
    if media_info is None:
        logger.debug(f"No media info found for the trailer: {trailer_path}")
        return None
    # Verify the trailer duration is within the limits
    if not media_info.duration_seconds:
        logger.debug(f"Trailer duration is zero: {trailer_path}")
        return None
    if media_info.duration_seconds < min_duration:
        logger.debug(
            f"Trailer duration less than {min_duration} seconds:"
            f" {media_info.duration_seconds}"
        )
        return False
    if media_info.duration_seconds > max_duration:
        logger.debug(
            f"Trailer duration more than {max_duration} seconds:"
            f" {media_info.duration_seconds}"
        )
        return False
    # Verify the trailer has audio and video streams
    streams = media_info.streams
    if len(streams) == 0:
        logger.debug(f"No streams found in the trailer: {trailer_path}")
        return False
    audio_exists = False
    video_exists = False
    for stream in streams:
        if stream.codec_type == "audio":
            audio_exists = True
        if stream.codec_type == "video":
            video_exists = True
    if not audio_exists:
        logger.debug(f"No audio stream found in the trailer: {trailer_path}")
        return False
    if not video_exists:
        logger.debug(f"No video stream found in the trailer: {trailer_path}")
        return False
    logger.debug(f"Trailer streams verified for: {trailer_path}")
    return True


def get_silence_timestamps(
    file_path: str,
) -> tuple[float | None, float | None]:
    """
    Get silence timestamps using ffmpeg silencedetect filter. \n
    Args:
        file_path (str): Path to the video file. \n
    Returns:
        timestamps (tuple[float|None, float|None]): Silence start and end timestamps \
            if found, None otherwise.
    """
    logger.debug(f"Getting silence timestamps for: {file_path}")
    try:
        # Get silence timestamps using ffmpeg silencedetect filter
        logger.debug(f"Running ffmpeg silencedetect for: {file_path}")
        result = subprocess.run(
            [
                app_settings.ffmpeg_path,
                "-i",
                file_path,
                "-af",
                "silencedetect=noise=-30dB:d=3",
                "-f",
                "null",
                "-",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        silence_start = None
        silence_end = None
        duration = None
        logger.debug(
            f"Silence detection completed for: {file_path}, parsing results..."
        )
        for line in result.stderr.split("\n"):
            line = line.lower().strip()
            if duration is None and "duration" in line:
                duration_match = re.search(
                    r"duration: (\d+):(\d+):(\d+\.\d+)", line
                )
                if duration_match:
                    hours = int(duration_match.group(1))
                    minutes = int(duration_match.group(2))
                    seconds = float(duration_match.group(3))
                    duration = (hours * 3600) + (minutes * 60) + seconds
            if "silence_start" in line:
                silence_start = float(
                    re.search(r"silence_start: (\d+\.\d+)", line).group(1)  # type: ignore
                )
            if "silence_end" in line:
                silence_end = float(
                    re.search(r"silence_end: (\d+\.\d+)", line).group(1)  # type: ignore
                )
        if not silence_start or not silence_end or not duration:
            logger.debug(f"No silence detected in the video: {file_path}")
            return None, None

        # If silence is not found within the last 30 seconds, set silence timestamps to None
        if silence_end < duration - 30.0:
            logger.debug(
                "Silence end timestamp is not within the last 30 seconds of"
                f" the video: {file_path}. Ignoring detected silence."
            )
            return None, None

        # Add 2 seconds to silence start to avoid cutting the audio abruptly
        silence_start = silence_start + 2.0

        # If detected silence is less than 3 seconds from the end, ignore it
        if duration - silence_start < 3.0:
            logger.debug(
                "Silence end timestamp is less than 3 seconds from the"
                f" end of the video: {file_path}. Ignoring detected silence."
            )
            return None, None

        logger.debug(
            f"Silence detected from {silence_start} to {silence_end} "
            f"in video: {file_path} of duration {duration}"
        )
        return silence_start, silence_end
    except Exception as e:
        logger.exception(
            f"Exception while detecting silence in video: {str(e)}"
        )
    return None, None


def trim_video(
    file_path: str,
    output_file: str,
    start_timestamp: int | float | str,
    end_timestamp: int | float | str,
) -> bool:
    """Trim the video at the end using ffmpeg. \n
    Args:
        file_path (str): Path to the video file.
        output_file (str): Path to save the output file.
        start_timestamp (int | float | str): Start timestamp to trim the video.
        end_timestamp (int | float | str): End timestamp to trim the video. \n
    Returns:
        bool: True if video trimmed successfully, False otherwise.
    Raises:
        Exception: If error occurs while trimming video.
    """
    time = datetime.now()
    logger.debug(
        f"Trimming video from {start_timestamp} to {end_timestamp}:"
        f" {file_path}"
    )
    try:
        # Remove silence part from end of video
        logger.debug(f"Running ffmpeg trim command on video: {file_path}")
        remove_cmd = [
            app_settings.ffmpeg_path,
            "-ss",
            str(start_timestamp),
            "-i",
            file_path,
            "-to",
            str(end_timestamp),
            "-c:v",
            "copy",
            "-c:a",
            "copy",
            "-c:s",
            "copy",
            output_file,
        ]
        remove_result = subprocess.run(
            remove_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if remove_result.returncode == 0:
            # print("STDERR:")
            # print(remove_result.stderr)
            timeTook = datetime.now() - time
            logger.debug(
                f"Video trimmed successfully in {timeTook} and saved to:"
                f" {output_file}"
            )
            return True
        else:
            raise Exception(f"FFMPEG Exception: {remove_result.stderr}")
            # print(f"Error: {remove_result.stderr}")
    except Exception as e:
        raise Exception(f"Exception while trimming video: {str(e)}")
    # timeTook = datetime.now() - time
    # print(f"Time took: {timeTook}")
    return False


def remove_silence_at_end(file_path: str) -> str:
    """
    Remove silence from the end of the video. \n
    Args:
        file_path (str): Path to the video file. \n
    Returns:
        str: Path to the trimmed video file.
    """
    logger.info(f"Detecting silence at end of video: {file_path}")
    # Get silence timestamps
    silence_start, silence_end = get_silence_timestamps(file_path)
    if silence_start is None or silence_end is None:
        logger.info("No silence detected at end of video")
        return file_path
    # Remove silence from the end of the video
    tmp_dir = "/var/lib/trailarr/tmp"
    if not os.path.exists(tmp_dir):
        tmp_dir = "/app/tmp"
    output_file = f"{tmp_dir}/trimmed_{os.path.basename(file_path)}"
    # file_name, file_ext = os.path.splitext(file_path)
    # output_srt = f"/app/tmp/trimmed_{os.path.basename(file_name)}.srt"
    try:
        logger.info(
            "Silence detected at end of video. Trimming video at"
            f" {silence_start}"
        )
        trim_video(file_path, output_file, 0, silence_start)
    except Exception as e:
        # Log error with traceback but return original file to continue processing
        logger.exception(
            f"Exception while removing silence from video: {str(e)}"
        )
        return file_path
    silence_time = silence_end - silence_start
    logger.info(
        f"Silence removed ({silence_time:.2f}s) from end of video: {file_path}"
    )
    return output_file


# folder = "/media/movies/all/Pechi (2024) {imdb-tt33034505}"
# input_file = f"{folder}/Pechi - Trailer-trailer.webm"
# output_file = f"{folder}/Pechi - Trailer 1-trailer.mkv"
# res = get_media_info(input_file)
# print(res)
# if not res:
#     print("No media info")
#     exit(0)
# streams = res.streams
# if not any(stream.codec_type == "audio" for stream in streams):
#     # No audio stream, delete the trailer file
#     print("No audio stream")
# silence_start, silence_end = get_silence_timestamps(input_file)
# We will use the start time of the silence to remove the silent part from the video
# if silence_start is not None and silence_end is not None:
#     detect_silence(
#         input_file,
#         output_file,
#         silence_start,
#     )
# else:
#     print("No silence detected")
