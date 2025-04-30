from app_logger import ModuleLogger
from config.settings import app_settings
from core.download.video_analysis import StreamInfo, get_media_info

logger = ModuleLogger("VideoConversion")

# CPU
# ffmpeg -i input.mkv -c:v libx264 -preset veryfast -crf 22 -c:a aac -b:a 128k -c:s srt -movflags +faststart -tune zerolatency output1-converted3-264-aac-srt-cpu-fast.mkv  # noqa: E501
# ffmpeg -i temp_2206-trailer.mkv -c:v libaom-av1 -preset veryfast -crf 22 -c:a copy output1.mkv  # noqa: E501

# NVIDIA - web optimized options not working
# ffmpeg -hwaccel cuda -hwaccel_output_format cuda -i input.mkv -c:v h264_nvenc -preset fast -cq 22 -c:a aac -b:a 128k -c:s srt output1-converted3-264-aac-srt-nvenc.mkv  # noqa: E501
# ffmpeg -hwaccel cuda -hwaccel_output_format cuda -i test.webm -c:v h264_nvenc -preset fast -cq 22 -af volume=1.5 -c:a aac -b:a 128k -c:s srt -movflags +faststart -tune zerolatency test-264-af-aac-srt-fs-nvenc.mkv  # noqa: E501

# VAAPI (Intel) - Not implementing as I'm not sure how and need help with development for this.
# ffmpeg -init_hw_device vaapi=foo:/dev/dri/renderD128 -filter_hw_device foo -i output1.mkv -vf 'format=nv12,hwupload' -c:v h264_vaapi -qp 22 -c:a aac -b:a 128k -c:s srt output1-converted3-264-aac-srt-i916hw-fast.mkv  # noqa: E501


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

# _VIDEO_CODECS_VAAPI = {
#     "h264": "h264_vaapi",
#     "h265": "hevc_vaapi",
#     "vp8": "vp8_vaapi",
#     "vp9": "vp9_vaapi",
#     "av1": "av1_vaapi",
# }


def _get_video_options_cpu(
    input_file: str, video_stream: StreamInfo | None = None
) -> list[str]:
    """Generate the ffmpeg video options for CPU. \n
    Args:
        input_file (str): Input video file path
        video_stream (StreamInfo, Optional=None): Video stream info
    Returns:
        list[str]: FFMPEG command list."""
    ffmpeg_cmd: list[str] = [
        "-i",
        input_file,
        "-c:v",
    ]
    _vcodec = app_settings.trailer_video_format
    if _vcodec not in _VIDEO_CODECS:
        logger.error(
            f"Video codec '{_vcodec}' not implemented in Trailer, using h265"
            " codec"
        )
        _vcodec = "h265"
    _vencoder = _VIDEO_CODECS[_vcodec]

    if video_stream is None or video_stream.codec_name == _vcodec:
        if video_stream is None:
            logger.debug(f"Converting video to {_vcodec} codec")
        else:
            logger.debug(
                f"Downloaded video is already in required codec: {_vcodec}, "
                "copying stream without converting"
            )
        ffmpeg_cmd.append("copy" if video_stream else _vencoder)
    else:
        logger.debug(
            f"Converting video from {video_stream.codec_name} to"
            f" {_vcodec} codec"
        )
        ffmpeg_cmd.append(_vencoder)
        ffmpeg_cmd.extend(["-preset", "veryfast", "-crf", "22"])

    return ffmpeg_cmd


def _get_video_options_nvidia(
    input_file: str, video_stream: StreamInfo | None = None
) -> list[str]:
    """Generate the ffmpeg video options for NVIDIA.
    Args:
        input_file (str): Input video file path
        video_stream (StreamInfo, Optional=None): Video stream info
    Returns:
        list[str]: FFMPEG command list."""
    vcodec = app_settings.trailer_video_format
    if vcodec not in _VIDEO_CODECS_NVIDIA:
        logger.error(
            f"Video codec '{vcodec}' not supported by NVIDIA hardware encoder,"
            " using CPU"
        )
        return _get_video_options_cpu(input_file, video_stream)

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
        logger.debug(f"Converting video to {vcodec} codec")
        video_options.append(vencoder)
        video_options.extend(["-preset", "fast", "-cq", "22"])
        return video_options

    if video_stream.codec_name == vcodec:
        logger.debug(
            f"Downloaded video is already in required codec: {vcodec}, "
            "copying stream without converting"
        )
        video_options.append("copy")
    else:
        logger.debug(
            f"Converting video from {video_stream.codec_name} to"
            f" {vcodec} codec"
        )
        video_options.append(vencoder)
        video_options.extend(["-preset", "fast", "-cq", "22"])

    return video_options


def _get_video_options(
    input_file: str, use_nvidia: bool, video_stream: StreamInfo | None = None
) -> list[str]:
    if use_nvidia:
        return _get_video_options_nvidia(input_file, video_stream)
    return _get_video_options_cpu(input_file, video_stream)


def _get_audio_options(audio_stream: StreamInfo | None = None) -> list[str]:
    """Get the audio options for the ffmpeg command.
    Args:
        audio_stream (StreamInfo, Optional=None): Audio stream info.
    Returns:
        list[str]: FFMPEG command list for audio."""
    ffmpeg_cmd: list[str] = []
    _acodec = app_settings.trailer_audio_format
    _aencoder = _AUDIO_CODECS[_acodec]

    # Apply audio volume level filter if enabled
    volume_level = app_settings.trailer_audio_volume_level * 0.01
    if volume_level != 1:
        logger.debug(
            f"Applying audio volume level filter: '-af volume={volume_level}'"
        )
        ffmpeg_cmd.extend(["-af", f"volume={volume_level}"])

    if audio_stream is None:
        logger.debug(f"Converting audio to {_acodec} codec")
        ffmpeg_cmd.extend(["-c:a", _aencoder, "-b:a", "128k"])
        return ffmpeg_cmd

    if audio_stream.codec_name == _acodec and volume_level == 1:
        logger.debug(
            f"Downloaded audio is already in required codec: {_acodec}, "
            "copying stream without converting"
        )
        ffmpeg_cmd.append("-c:a")
        ffmpeg_cmd.append("copy")
    else:
        logger.debug(
            f"Converting audio from {audio_stream.codec_name} to"
            f" {_acodec} codec"
        )
        ffmpeg_cmd.extend(["-c:a", _aencoder, "-b:a", "128k"])

    return ffmpeg_cmd


def _get_subtitle_options(stream: StreamInfo | None = None) -> list[str]:
    """Get the subtitle options for the ffmpeg command.
    Args:
        stream (StreamInfo, Optional=None): Subtitle stream info.
    Returns:
        list[str]: FFMPEG command list for subtitles."""
    if not app_settings.trailer_subtitles_enabled:
        return []
    ffmpeg_cmd: list[str] = []
    scodec = app_settings.trailer_subtitles_format
    if stream is None:
        logger.debug(f"Converting subtitles to {scodec} format")
    else:
        logger.debug(
            f"Converting subtitles from {stream.codec_name} to {scodec} format"
        )
    ffmpeg_cmd.append("-c:s")
    ffmpeg_cmd.append(scodec)
    return ffmpeg_cmd


def _get_web_optimized_options() -> list[str]:
    """Get the web optimized options for the ffmpeg command."""
    ffmpeg_cmd: list[str] = []
    # Add web optimized options if enabled
    if not app_settings.trailer_web_optimized:
        return ffmpeg_cmd
    # Web optimized options are only applicable to mp4 containers
    if app_settings.trailer_file_format != "mp4":
        logger.warning(
            "Web optimized options are only applicable to mp4 containers, "
            "skipping web optimization"
        )
        return ffmpeg_cmd
    logger.debug("Converting to a web optimized format")
    ffmpeg_cmd.append("-movflags")
    ffmpeg_cmd.append("+faststart")
    return ffmpeg_cmd


def get_ffmpeg_cmd(
    input_file: str, output_file: str, fallback=False
) -> list[str]:
    """Generate the ffmpeg command based on the app settings and media streams.
    Args:
        input_file (str): Input video file path.
        output_file (str): Output video file path.
        fallback (bool): If True, hardware acceleration is not used.
    Returns:
        list[str]: FFMPEG command list."""
    # Check if NVIDIA hardware acceleration is enabled
    if fallback:
        logger.debug("Fallback mode enabled, using CPU for conversion")
        use_nvidia = False
    else:
        use_nvidia = (
            app_settings.nvidia_gpu_available
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
        _get_video_options(input_file, use_nvidia, _video_stream)
    )
    # Set audio specific options
    ffmpeg_cmd.extend(_get_audio_options(_audio_stream))
    # Set subtitle specific options
    ffmpeg_cmd.extend(_get_subtitle_options(_subtitle_stream))
    # Add web optimized options if enabled
    ffmpeg_cmd.extend(_get_web_optimized_options())
    # Add output file
    ffmpeg_cmd.append(output_file)

    return ffmpeg_cmd
