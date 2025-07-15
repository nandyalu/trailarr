from app_logger import ModuleLogger

from config.settings import app_settings
from core.base.database.models.trailerprofile import TrailerProfileRead
from core.download.video_analysis import StreamInfo, get_media_info

logger = ModuleLogger("VideoConversion")

# CPU
# ffmpeg -i input.mkv -c:v libx264 -preset veryfast -crf 22 -c:a aac -b:a 128k -c:s srt -movflags +faststart -tune zerolatency output1-converted3-264-aac-srt-cpu-fast.mkv  # noqa: E501
# ffmpeg -i temp_2206-trailer.mkv -c:v libaom-av1 -preset veryfast -crf 22 -c:a copy output1.mkv  # noqa: E501

# NVIDIA - web optimized options not working
# ffmpeg -hwaccel cuda -hwaccel_output_format cuda -i input.mkv -c:v h264_nvenc -preset fast -cq 22 -c:a aac -b:a 128k -c:s srt output1-converted3-264-aac-srt-nvenc.mkv  # noqa: E501
# ffmpeg -hwaccel cuda -hwaccel_output_format cuda -i test.webm -c:v h264_nvenc -preset fast -cq 22 -af volume=1.5 -c:a aac -b:a 128k -c:s srt -movflags +faststart -tune zerolatency test-264-af-aac-srt-fs-nvenc.mkv  # noqa: E501

# VAAPI (Intel) - Optimized implementation with auto-detection and performance improvements
# ffmpeg -init_hw_device vaapi=intel -filter_hw_device intel -i output1.mkv -vf 'format=nv12,hwupload' -c:v h264_vaapi -crf 22 -async_depth 4 -c:a aac -b:a 128k -c:s srt output1-converted3-264-aac-srt-i916hw-fast.mkv  # noqa: E501

# AMF (AMD) - Optimized implementation with presets and quality settings
# ffmpeg -i output1.mkv -c:v h264_amf -crf 22 -preset balanced -quality balanced -usage transcoding -c:a aac -b:a 128k -c:s srt output1-converted3-264-aac-srt-amf-balanced.mkv  # noqa: E501


# -movflags +faststart - only applicable to mp4 containers
# -tune zerolatency - applicable to libx264 only, to set different options for different encoders

_AUDIO_CODECS = {
    "aac": "aac",
    "ac3": "ac3",
    "eac3": "eac3",
    "mp3": "libmp3lame",
    "flac": "flac",
    "vorbis": "libvorbis",
    "opus": "libopus",
    "copy": "copy",
}

_VIDEO_CODECS = {
    "h264": "libx264",
    "h265": "libx265",
    "vp8": "libvpx",
    "vp9": "libvpx-vp9",
    # "av1": "libaom-av1",
    # if av1 is selected and downloaded video is not in av1 codec, then convert to vp9
    "av1": "libvpx-vp9",
}

_VIDEO_CODECS_NVIDIA = {
    "h264": "h264_nvenc",
    "h265": "hevc_nvenc",
    # "vp8": "libvpx",  # hw encoder not available
    # "vp9": "libvpx-vp9",  # hw encoder not available
    # "av1": "av1_nvenc",
}

_VIDEO_CODECS_INTEL = {
    "h264": "h264_vaapi",
    "h265": "hevc_vaapi",
    # "vp8": "libvpx",  # hw encoder not available
    # "vp9": "libvpx-vp9",  # hw encoder not available
    # "av1": "av1_vaapi",
}

_VIDEO_CODECS_AMD = {
    "h264": "h264_amf",
    "h265": "hevc_amf",
    # "vp8": "libvpx",  # hw encoder not available
    # "vp9": "libvpx-vp9",  # hw encoder not available
    # "av1": "av1_amf",
}

_ACODEC_FALLBACK = "opus"
_VCODEC_FALLBACK = "vp9"

# _VIDEO_CODECS_VAAPI = {
#     "h264": "h264_vaapi",
#     "h265": "hevc_vaapi",
#     "vp8": "vp8_vaapi",
#     "vp9": "vp9_vaapi",
#     "av1": "av1_vaapi",
# }

DEFAULT_VOLUME_LEVEL = 100


def _get_video_options_cpu(
    vcodec: str, input_file: str, video_stream: StreamInfo | None = None
) -> list[str]:
    """Generate the ffmpeg video options for CPU. \n
    Args:
        vcodec (str): Video codec to convert to
        input_file (str): Input video file path
        video_stream (StreamInfo, Optional=None): Video stream info
    Returns:
        list[str]: FFMPEG command list."""
    ffmpeg_cmd: list[str] = ["-i", input_file, "-c:v"]
    if vcodec not in _VIDEO_CODECS:
        logger.error(
            f"Video codec '{vcodec}' not implemented in Trailer, using h265"
            " codec"
        )
        vcodec = _VCODEC_FALLBACK
    _vencoder = _VIDEO_CODECS[vcodec]

    # Convert video if current codec is not detected or different
    if video_stream is None or video_stream.codec_name != vcodec:
        if video_stream is None:
            logger.debug(f"Converting video to '{vcodec}' codec")
        else:
            logger.debug(
                f"Converting video from '{video_stream.codec_name}' to"
                f" '{vcodec}' codec"
            )
        ffmpeg_cmd.append(_vencoder)
        ffmpeg_cmd.extend(["-preset", "veryfast", "-crf", "22"])
    else:
        logger.debug(
            f"Downloaded video is already in required codec: {vcodec}, "
            "copying stream without converting"
        )
        ffmpeg_cmd.append("copy")

    return ffmpeg_cmd


def _get_video_options_nvidia(
    vcodec: str, input_file: str, video_stream: StreamInfo | None = None
) -> list[str]:
    """Generate the ffmpeg video options for NVIDIA.
    Args:
        vcodec (str): Video codec to convert to
        input_file (str): Input video file path
        video_stream (StreamInfo, Optional=None): Video stream info
    Returns:
        list[str]: FFMPEG command list."""
    if vcodec not in _VIDEO_CODECS_NVIDIA:
        logger.warning(
            f"Video codec '{vcodec}' not supported by NVIDIA hardware encoder,"
            " using CPU"
        )
        return _get_video_options_cpu(vcodec, input_file, video_stream)

    vencoder = _VIDEO_CODECS_NVIDIA[vcodec]
    video_options: list[str] = [
        "-hwaccel",
        "cuda",
        "-hwaccel_output_format",
        "cuda",
        "-i",
        input_file,
        "-c:v",
    ]

    if video_stream is None:
        logger.debug(f"Converting video to '{vcodec}' codec")
        video_options.append(vencoder)
        video_options.extend(["-preset", "fast", "-cq", "22"])
        return video_options

    if video_stream.codec_name == vcodec:
        logger.debug(
            f"Downloaded video is already in required codec: '{vcodec}', "
            "copying stream without converting"
        )
        video_options.append("copy")
    else:
        logger.debug(
            f"Converting video from '{video_stream.codec_name}' to"
            f" '{vcodec}' codec"
        )
        video_options.append(vencoder)
        video_options.extend(["-preset", "fast", "-cq", "22"])

    return video_options


def _get_video_options_intel(
    vcodec: str, input_file: str, video_stream: StreamInfo | None = None
) -> list[str]:
    """Generate the ffmpeg video options for Intel GPU (VAAPI).
    Args:
        vcodec (str): Video codec to convert to
        input_file (str): Input video file path
        video_stream (StreamInfo, Optional=None): Video stream info
    Returns:
        list[str]: FFMPEG command list."""
    if vcodec not in _VIDEO_CODECS_INTEL:
        logger.error(
            f"Video codec '{vcodec}' not supported by Intel hardware encoder,"
            " using CPU"
        )
        return _get_video_options_cpu(vcodec, input_file, video_stream)

    vencoder = _VIDEO_CODECS_INTEL[vcodec]
    video_options: list[str] = [
        "-init_hw_device",
        "vaapi=intel",  # Auto-detect Intel GPU device
        "-filter_hw_device",
        "intel",
        "-i",
        input_file,
        "-vf",
        "format=nv12,hwupload",
        "-c:v",
    ]

    if video_stream is None:
        logger.debug(f"Converting video to '{vcodec}' codec")
        video_options.append(vencoder)
        video_options.extend(["-crf", "22", "-async_depth", "4"])
        return video_options

    if video_stream.codec_name == vcodec:
        logger.debug(
            f"Downloaded video is already in required codec: '{vcodec}', "
            "copying stream without converting"
        )
        video_options.append("copy")
    else:
        logger.debug(
            f"Converting video from '{video_stream.codec_name}' to"
            f" '{vcodec}' codec"
        )
        video_options.append(vencoder)
        video_options.extend(["-crf", "22", "-async_depth", "4"])

    return video_options


def _get_video_options_amd(
    vcodec: str, input_file: str, video_stream: StreamInfo | None = None
) -> list[str]:
    """Generate the ffmpeg video options for AMD GPU (AMF).
    Args:
        vcodec (str): Video codec to convert to
        input_file (str): Input video file path
        video_stream (StreamInfo, Optional=None): Video stream info
    Returns:
        list[str]: FFMPEG command list."""
    if vcodec not in _VIDEO_CODECS_AMD:
        logger.error(
            f"Video codec '{vcodec}' not supported by AMD hardware encoder,"
            " using CPU"
        )
        return _get_video_options_cpu(vcodec, input_file, video_stream)

    vencoder = _VIDEO_CODECS_AMD[vcodec]
    video_options: list[str] = [
        "-i",
        input_file,
        "-c:v",
    ]

    if video_stream is None:
        logger.debug(f"Converting video to '{vcodec}' codec")
        video_options.append(vencoder)
        video_options.extend(
            [
                "-crf",
                "22",
                "-preset",
                "balanced",
                "-quality",
                "balanced",
                "-usage",
                "transcoding",
            ]
        )
        return video_options

    if video_stream.codec_name == vcodec:
        logger.debug(
            f"Downloaded video is already in required codec: '{vcodec}', "
            "copying stream without converting"
        )
        video_options.append("copy")
    else:
        logger.debug(
            f"Converting video from '{video_stream.codec_name}' to"
            f" '{vcodec}' codec"
        )
        video_options.append(vencoder)
        video_options.extend(
            [
                "-crf",
                "22",
                "-preset",
                "balanced",
                "-quality",
                "balanced",
                "-usage",
                "transcoding",
            ]
        )

    return video_options


def _get_video_options(
    vcodec: str,
    input_file: str,
    use_nvidia: bool,
    use_intel: bool,
    use_amd: bool,
    video_stream: StreamInfo | None = None,
) -> list[str]:
    if vcodec == "copy":
        ffmpeg_cmd: list[str] = ["-i", input_file, "-c:v", "copy"]
        logger.debug("Copying video stream without converting")
        return ffmpeg_cmd
    # First priority: NVIDIA
    if use_nvidia:
        return _get_video_options_nvidia(vcodec, input_file, video_stream)
    # Second priority: AMD
    if use_amd:
        return _get_video_options_amd(vcodec, input_file, video_stream)
    # Third priority: Intel
    if use_intel:
        return _get_video_options_intel(vcodec, input_file, video_stream)
    return _get_video_options_cpu(vcodec, input_file, video_stream)


def _get_audio_options(
    acodec: str, volume_level: int, audio_stream: StreamInfo | None = None
) -> list[str]:
    """Get the audio options for the ffmpeg command.
    Args:
        acodec (str): Audio codec to convert to.
        volume_level (int): Audio volume level.
        audio_stream (StreamInfo, Optional=None): Audio stream info.
    Returns:
        list[str]: FFMPEG command list for audio."""

    # Resolve the audio codec
    if acodec not in _AUDIO_CODECS:
        logger.error(
            f"Audio codec '{acodec}' not implemented, using"
            f" {_ACODEC_FALLBACK} codec"
        )
        acodec = _ACODEC_FALLBACK
    _aencoder = _AUDIO_CODECS[acodec]

    if volume_level == DEFAULT_VOLUME_LEVEL:
        _COPY_COMMAND = ["-c:a", "copy"]
        # Case 1: Copy audio stream without conversion
        if acodec == "copy":
            logger.debug("Copying audio stream without converting")
            return _COPY_COMMAND
        # Case 2: No volume change, same codec
        if audio_stream and audio_stream.codec_name == acodec:
            logger.debug(
                f"Audio already in '{acodec}', copying stream without"
                " converting"
            )
            return _COPY_COMMAND
    # Case 3: Apply audio volume level filter if enabled
    # Volume level setting is between 1 and 200
    # FFMPEG volume filter expects a value between 0.01 and 10.0
    _volume_level = volume_level * 0.01
    ffmpeg_cmd: list[str] = []
    logger.debug(f"Applying volume level filter: 'volume={_volume_level}'")
    ffmpeg_cmd.extend(["-af", f"volume={_volume_level}"])

    # Case 4: Copy is requested but volume change is needed
    if acodec == "copy":
        if audio_stream:
            _aencoder = _AUDIO_CODECS.get(audio_stream.codec_name, _aencoder)
        logger.debug(
            "Cannot apply volume level filter to 'copy' audio stream, "
            f"converting audio to '{_aencoder}' codec"
        )
    else:
        # Case 5: Convert audio codec with volume change
        logger.debug(f"Converting audio to '{_aencoder}' codec")
    ffmpeg_cmd.extend(["-c:a", _aencoder, "-b:a", "128k"])
    return ffmpeg_cmd


def _get_subtitle_options(
    scodec: str, stream: StreamInfo | None = None
) -> list[str]:
    """Get the subtitle options for the ffmpeg command.
    Args:
        scodec (str): Subtitle codec to convert to.
        stream (StreamInfo, Optional=None): Subtitle stream info.
    Returns:
        list[str]: FFMPEG command list for subtitles."""
    ffmpeg_cmd: list[str] = []
    if stream is None:
        logger.debug(f"Converting subtitles to {scodec} format")
    else:
        logger.debug(
            f"Converting subtitles from {stream.codec_name} to {scodec} format"
        )
    ffmpeg_cmd.append("-c:s")
    ffmpeg_cmd.append(scodec)
    return ffmpeg_cmd


# def _get_web_optimized_options() -> list[str]:
#     """Get the web optimized options for the ffmpeg command."""
#     ffmpeg_cmd: list[str] = []
#     # Add web optimized options if enabled
#     if not app_settings.trailer_web_optimized:
#         return ffmpeg_cmd
#     # Web optimized options are only applicable to mp4 containers
#     if app_settings.trailer_file_format != "mp4":
#         logger.warning(
#             "Web optimized options are only applicable to mp4 containers, "
#             "skipping web optimization"
#         )
#         return ffmpeg_cmd
#     logger.debug("Converting to a web optimized format")
#     ffmpeg_cmd.append("-movflags")
#     ffmpeg_cmd.append("+faststart")
#     return ffmpeg_cmd


def get_ffmpeg_cmd(
    profile: TrailerProfileRead,
    input_file: str,
    output_file: str,
    fallback=False,
) -> list[str]:
    """Generate the ffmpeg command based on the app settings and media streams.
    Args:
        profile (TrailerProfileRead): Trailer profile to use.
        input_file (str): Input video file path.
        output_file (str): Output video file path.
        fallback (bool): If True, hardware acceleration is not used.
    Returns:
        list[str]: FFMPEG command list."""
    # Check if hardware acceleration is enabled
    if fallback:
        logger.debug("Falling back to CPU for conversion")
        use_nvidia = False
        use_intel = False
        use_amd = False
    else:
        use_nvidia = (
            app_settings.nvidia_gpu_available
            and app_settings.trailer_hardware_acceleration
        )
        use_intel = (
            app_settings.intel_gpu_available
            and app_settings.trailer_hardware_acceleration
        )
        use_amd = (
            app_settings.amd_gpu_available
            and app_settings.trailer_hardware_acceleration
        )
    _video_stream: StreamInfo | None = None
    _audio_stream: StreamInfo | None = None
    _subtitle_stream: StreamInfo | None = None
    # Get the media streams information
    media_info = get_media_info(input_file)
    if media_info is not None:
        for stream in media_info.streams:
            if stream.codec_type == "video":
                _video_stream = stream
            elif stream.codec_type == "audio":
                _audio_stream = stream
            elif stream.codec_type == "subtitle":
                _subtitle_stream = stream
    ffmpeg_cmd: list[str] = [
        "ffmpeg",
        "-hide_banner",
        # "-loglevel",
        # "repeat+level+warning",
    ]
    # Set video specific options
    ffmpeg_cmd.extend(
        _get_video_options(
            profile.video_format,
            input_file,
            use_nvidia,
            use_intel,
            use_amd,
            _video_stream,
        )
    )
    # Set audio specific options
    ffmpeg_cmd.extend(
        _get_audio_options(
            profile.audio_format, profile.audio_volume_level, _audio_stream
        )
    )
    # Set subtitle specific options
    if profile.subtitles_enabled:
        ffmpeg_cmd.extend(
            _get_subtitle_options(profile.subtitles_format, _subtitle_stream)
        )
    # # Add web optimized options if enabled
    # ffmpeg_cmd.extend(_get_web_optimized_options())
    # Add output file
    ffmpeg_cmd.append(output_file)

    return ffmpeg_cmd
