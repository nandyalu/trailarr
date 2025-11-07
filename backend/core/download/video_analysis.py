from datetime import datetime
import os
import re
import subprocess
import json

from pydantic import BaseModel

from config.settings import app_settings
from app_logger import ModuleLogger

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
    format_name: str
    duration_seconds: int = 0
    duration: str = "0:00:00"
    size: int = 0
    bitrate: str = "0 bps"
    streams: list[StreamInfo]
    youtube_id: str | None = None


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
        " format_tags=comment,description,synopsis,YouTube,youtube_id :"
        " stream=index,codec_type,codec_name,coded_height,coded_width,channels,sample_rate"
        " : stream_tags=language,duration,name"
    )
    ffprobe_cmd = [
        "/usr/local/bin/ffprobe",
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
        format: dict[str, str] = info.get("format", {})
        format_tags: dict[str, str] = format.get("tags", {})
        
        # Extract YouTube ID from format tags (comment, description, synopsis, or YouTube field)
        youtube_id = None
        for tag_key in ["youtube_id", "YouTube", "comment", "description", "synopsis"]:
            tag_value = format_tags.get(tag_key, "")
            if tag_value:
                # Try to extract YouTube video ID from the tag value
                # YouTube IDs are 11 characters long
                import re
                match = re.search(r'(?:v=|/)([A-Za-z0-9_-]{11})', tag_value)
                if match:
                    youtube_id = match.group(1)
                    break
        
        # Create VideoInfo object
        video_info = VideoInfo(
            name=os.path.basename(file_path),
            format_name=str(format.get("format_name", "N/A")),
            duration_seconds=int(float(format.get("duration", "0"))),
            duration=convert_duration(format.get("duration", "0")),
            size=int(format.get("size", "0")),
            bitrate=convert_bitrate(format.get("bit_rate", "0")),
            streams=[],
            youtube_id=youtube_id,
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
        logger.error(f"Error extracting video info: {str(e)}")
    return None


def verify_trailer_streams(trailer_path: str):
    """
    Check if the trailer has audio and video streams. \n
    Args:
        trailer_path (str): Path to the trailer file. \n
    Returns:
        bool: True if the trailer has audio and video streams, False otherwise.
    """
    # Check trailer file exists
    logger.debug(f"Verifying trailer streams for: {trailer_path}")
    if not trailer_path:
        return False
    # Get media analysis for the trailer
    media_info = get_media_info(trailer_path)
    if media_info is None:
        logger.debug(f"No media info found for the trailer: {trailer_path}")
        return False
    # Varify the trailer duration is within the limits
    if media_info.duration_seconds < app_settings.trailer_min_duration:
        logger.debug(
            "Trailer duration less than 10 seconds:"
            f" {media_info.duration_seconds}"
        )
        return False
    if media_info.duration_seconds > app_settings.trailer_max_duration:
        logger.debug(
            "Trailer duration more than 60 seconds:"
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
    # time = datetime.now()
    logger.debug(f"Getting silence timestamps for: {file_path}")
    try:
        # Get silence timestamps using ffmpeg silencedetect filter
        logger.debug(f"Running ffmpeg silencedetect for: {file_path}")
        result = subprocess.run(
            [
                "/usr/local/bin/ffmpeg",
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
        logger.debug(
            f"Silence detection completed for: {file_path}, parsing results..."
        )
        for line in result.stderr.split("\n"):
            if "silence_start" in line:
                silence_start = float(
                    re.search(r"silence_start: (\d+\.\d+)", line).group(1)  # type: ignore
                )
            if "silence_end" in line:
                silence_end = float(
                    re.search(r"silence_end: (\d+\.\d+)", line).group(1)  # type: ignore
                )
            if silence_start is not None and silence_end is not None:
                logger.debug(
                    "Silence detected at end of video. "
                    f"Timestamps Start: {silence_start}, End: {silence_end}"
                )
                break
        # Add 2 seconds to silence start to avoid cutting the audio abruptly
        silence_start = (
            silence_start + 2.0 if silence_start is not None else None
        )
        return silence_start, silence_end
    except Exception as e:
        logger.error(f"Exception while detecting silence in video: {str(e)}")
    # timeTook = datetime.now() - time
    # print(f"Time took: {timeTook}")
    return None, None


def trim_video_at_end(
    file_path: str, output_file: str, end_timestamp: int | float | str
) -> bool:
    """Trim the video at the end using ffmpeg. \n
    Args:
        file_path (str): Path to the video file.
        output_file (str): Path to save the output file.
        end_timestamp (int | float | str): End timestamp to trim the video. \n
    Returns:
        bool: True if video trimmed successfully, False otherwise.
    Raises:
        Exception: If error occurs while trimming video.
    """
    time = datetime.now()
    logger.debug(f"Trimming video to end (at {end_timestamp}): {file_path}")
    try:
        # Remove silence part from end of video
        logger.debug(f"Running ffmpeg trim command on video: {file_path}")
        remove_cmd = [
            "/usr/local/bin/ffmpeg",
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
    output_file = f"/app/tmp/trimmed_{os.path.basename(file_path)}"
    # file_name, file_ext = os.path.splitext(file_path)
    # output_srt = f"/app/tmp/trimmed_{os.path.basename(file_name)}.srt"
    try:
        logger.info(
            "Silence detected at end of video. Trimming video at"
            f" {silence_start}"
        )
        trim_video_at_end(file_path, output_file, silence_start)
    except Exception as e:
        logger.error(f"Exception while removing silence from video: {str(e)}")
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
