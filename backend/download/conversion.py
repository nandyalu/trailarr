import os
import platform

from app_logger import ModuleLogger
from config.settings import app_settings
from db.models.trailerprofile import TrailerProfileRead
from download.analysis import StreamInfo, get_media_info

logger = ModuleLogger("VideoConversion")

_AUDIO_CODECS = {
    "aac": "aac", "ac3": "ac3", "eac3": "eac3", "mp3": "libmp3lame",
    "flac": "flac", "vorbis": "libvorbis", "opus": "libopus", "copy": "copy",
}
_SUBTITLES_CODECS = {"mov_text": "mov_text", "srt": "srt", "vtt": "webvtt"}

_VIDEO_CODECS = {
    "h264": "libx264", "h265": "libx265", "vp8": "libvpx",
    "vp9": "libvpx-vp9", "av1": "libvpx-vp9",
}
_VIDEO_CODECS_NVIDIA = {
    "h264": "h264_nvenc", "h265": "hevc_nvenc", "av1": "av1_nvenc",
}
_VIDEO_CODECS_VAAPI = {
    "h264": "h264_vaapi", "h265": "hevc_vaapi", "vp8": "vp8_vaapi",
    "vp9": "vp9_vaapi", "av1": "av1_vaapi",
}
_VIDEO_CODECS_QSV = {
    "h264": "h264_qsv", "h265": "hevc_qsv", "vp9": "vp9_qsv", "av1": "av1_qsv",
}
_VIDEO_CODECS_AMF = {"h264": "h264_amf", "h265": "hevc_amf", "av1": "av1_amf"}
_VIDEO_CODECS_VIDEOTOOLBOX = {"h264": "h264_videotoolbox", "h265": "hevc_videotoolbox"}

_ACODEC_FALLBACK = "opus"
_VCODEC_FALLBACK = "vp9"
DEFAULT_VOLUME_LEVEL = 100


def _get_video_options_cpu(
    vcodec: str, input_file: str, video_stream: StreamInfo | None = None
) -> list[str]:
    ffmpeg_cmd: list[str] = ["-i", input_file, "-c:v"]
    if vcodec not in _VIDEO_CODECS:
        logger.error(f"Video codec '{vcodec}' not implemented, using {_VCODEC_FALLBACK}")
        vcodec = _VCODEC_FALLBACK
    _vencoder = _VIDEO_CODECS[vcodec]
    if video_stream is None or video_stream.codec_name != vcodec:
        ffmpeg_cmd.append(_vencoder)
        ffmpeg_cmd.extend(["-preset", "veryfast", "-crf", "22", "-vf", "format=yuv420p", "-pix_fmt", "yuv420p"])
    else:
        logger.debug(f"Video already in required codec: {vcodec}, copying stream")
        ffmpeg_cmd.append("copy")
    return ffmpeg_cmd


def _get_video_options_nvidia(
    vcodec: str, input_file: str, video_stream: StreamInfo | None = None
) -> list[str]:
    if vcodec not in _VIDEO_CODECS_NVIDIA:
        logger.warning(f"Video codec '{vcodec}' not supported by NVIDIA, falling back to CPU")
        return _get_video_options_cpu(vcodec, input_file, video_stream)
    vencoder = _VIDEO_CODECS_NVIDIA[vcodec]
    if video_stream is not None and video_stream.codec_name == vcodec:
        return ["-i", input_file, "-c:v", "copy"]
    video_options: list[str] = [
        "-hwaccel", "cuda", "-hwaccel_output_format", "cuda", "-i", input_file, "-c:v",
    ]
    video_options.append(vencoder)
    video_options.extend(["-preset", "fast", "-cq", "22", "-b:v", "0"])
    return video_options


def _get_video_options_videotoolbox(
    vcodec: str, input_file: str, video_stream: StreamInfo | None = None
) -> list[str]:
    if vcodec not in _VIDEO_CODECS_VIDEOTOOLBOX:
        logger.warning(f"Video codec '{vcodec}' not supported by VideoToolbox, using CPU")
        return _get_video_options_cpu(vcodec, input_file, video_stream)
    if video_stream is not None and video_stream.codec_name == vcodec:
        return ["-i", input_file, "-c:v", "copy"]
    return ["-i", input_file, "-c:v", _VIDEO_CODECS_VIDEOTOOLBOX[vcodec], "-q:v", "65", "-b:v", "0"]


def _get_video_options_qsv(
    vcodec: str, input_file: str, video_stream: StreamInfo | None = None
) -> list[str]:
    if vcodec not in _VIDEO_CODECS_QSV:
        logger.warning(f"Video codec '{vcodec}' not supported by Intel QSV, using CPU")
        return _get_video_options_cpu(vcodec, input_file, video_stream)
    if video_stream is not None and video_stream.codec_name == vcodec:
        return ["-i", input_file, "-c:v", "copy"]
    return ["-hwaccel", "qsv", "-i", input_file, "-c:v", _VIDEO_CODECS_QSV[vcodec], "-preset", "fast", "-global_quality", "22", "-b:v", "0"]


def _get_video_options_amf(
    vcodec: str, input_file: str, video_stream: StreamInfo | None = None
) -> list[str]:
    if vcodec not in _VIDEO_CODECS_AMF:
        logger.warning(f"Video codec '{vcodec}' not supported by AMD AMF, using CPU")
        return _get_video_options_cpu(vcodec, input_file, video_stream)
    if video_stream is not None and video_stream.codec_name == vcodec:
        return ["-i", input_file, "-c:v", "copy"]
    return ["-i", input_file, "-c:v", _VIDEO_CODECS_AMF[vcodec], "-quality", "balanced", "-b:v", "0"]


def _get_video_options_vaapi(
    vcodec: str, input_file: str, video_stream: StreamInfo | None = None
) -> list[str]:
    if platform.system() == "Darwin":
        return _get_video_options_videotoolbox(vcodec, input_file, video_stream)
    if platform.system() == "Windows":
        if app_settings.gpu_available_intel and app_settings.gpu_enabled_intel:
            return _get_video_options_qsv(vcodec, input_file, video_stream)
        if app_settings.gpu_available_amd and app_settings.gpu_enabled_amd:
            return _get_video_options_amf(vcodec, input_file, video_stream)
        return _get_video_options_cpu(vcodec, input_file, video_stream)
    if vcodec not in _VIDEO_CODECS_VAAPI:
        logger.warning(f"Video codec '{vcodec}' not supported by VAAPI, using CPU")
        return _get_video_options_cpu(vcodec, input_file, video_stream)
    device_path = "/dev/dri/renderD128"
    if app_settings.gpu_available_intel and app_settings.gpu_enabled_intel and os.environ.get("GPU_DEVICE_INTEL"):
        device_path = os.environ.get("GPU_DEVICE_INTEL")
    elif app_settings.gpu_available_amd and app_settings.gpu_enabled_amd and os.environ.get("GPU_DEVICE_AMD"):
        device_path = os.environ.get("GPU_DEVICE_AMD")
    if not device_path:
        device_path = "/dev/dri/renderD128"
    if video_stream is not None and video_stream.codec_name == vcodec:
        return ["-i", input_file, "-c:v", "copy"]
    video_options: list[str] = [
        "-hwaccel", "vaapi", "-hwaccel_device", device_path, "-vaapi_device", device_path,
        "-i", input_file, "-vf", "format=nv12,hwupload", "-c:v",
    ]
    video_options.append(_VIDEO_CODECS_VAAPI[vcodec])
    video_options.extend(["-qp", "22", "-b:v", "0", "-pix_fmt", "yuv420p"])
    return video_options


def _get_video_options(
    vcodec: str,
    input_file: str,
    use_nvidia: bool,
    use_vaapi: bool,
    video_stream: StreamInfo | None = None,
) -> list[str]:
    if vcodec == "copy" or (video_stream and video_stream.codec_name == vcodec):
        logger.debug("Copying video stream without converting")
        return ["-i", input_file, "-c:v", "copy"]
    if use_nvidia:
        return _get_video_options_nvidia(vcodec, input_file, video_stream)
    if use_vaapi:
        return _get_video_options_vaapi(vcodec, input_file, video_stream)
    return _get_video_options_cpu(vcodec, input_file, video_stream)


def _get_audio_options(
    acodec: str, volume_level: int, audio_stream: StreamInfo | None = None
) -> list[str]:
    if acodec not in _AUDIO_CODECS:
        logger.error(f"Audio codec '{acodec}' not implemented, using {_ACODEC_FALLBACK}")
        acodec = _ACODEC_FALLBACK
    _aencoder = _AUDIO_CODECS[acodec]
    if volume_level == DEFAULT_VOLUME_LEVEL:
        _COPY_COMMAND = ["-c:a", "copy"]
        if acodec == "copy":
            return _COPY_COMMAND
        if audio_stream and audio_stream.codec_name == acodec:
            return _COPY_COMMAND
        return ["-c:a", _aencoder, "-b:a", "128k"]
    _volume_level = volume_level * 0.01
    ffmpeg_cmd: list[str] = ["-af", f"volume={_volume_level}"]
    if acodec == "copy":
        if audio_stream:
            _aencoder = _AUDIO_CODECS.get(audio_stream.codec_name, _aencoder)
    ffmpeg_cmd.extend(["-c:a", _aencoder, "-b:a", "128k"])
    return ffmpeg_cmd


def _get_subtitle_options(scodec: str, stream: StreamInfo | None = None) -> list[str]:
    _scodec = _SUBTITLES_CODECS.get(scodec, "srt")
    if stream is not None and stream.codec_name == _scodec:
        _scodec = "copy"
    return ["-c:s", _scodec]


def get_ffmpeg_cmd(
    profile: TrailerProfileRead,
    input_file: str,
    output_file: str,
    fallback: bool = False,
) -> list[str]:
    if fallback:
        use_nvidia = False
        use_vaapi = False
    else:
        use_nvidia = app_settings.gpu_available_nvidia and app_settings.gpu_enabled_nvidia
        use_vaapi = (
            app_settings.gpu_available_intel and app_settings.gpu_enabled_intel
        ) or (app_settings.gpu_available_amd and app_settings.gpu_enabled_amd)

    _video_stream: StreamInfo | None = None
    _audio_stream: StreamInfo | None = None
    _subtitle_stream: StreamInfo | None = None
    media_info = get_media_info(input_file)
    if media_info is not None:
        for stream in media_info.streams:
            if stream.codec_type == "video":
                _video_stream = stream
            elif stream.codec_type == "audio":
                _audio_stream = stream
            elif stream.codec_type == "subtitle":
                _subtitle_stream = stream

    ffmpeg_cmd: list[str] = [app_settings.ffmpeg_path, "-hide_banner", "-y"]
    ffmpeg_cmd.extend(_get_video_options(profile.video_format, input_file, use_nvidia, use_vaapi, _video_stream))
    ffmpeg_cmd.extend(_get_audio_options(profile.audio_format, profile.audio_volume_level, _audio_stream))
    if profile.subtitles_enabled:
        _profile_subs = profile.subtitles_format
        if profile.file_format == "mp4" and profile.subtitles_format == "srt":
            _profile_subs = "mov_text"
        ffmpeg_cmd.extend(_get_subtitle_options(_profile_subs, _subtitle_stream))
    else:
        if _subtitle_stream:
            ffmpeg_cmd.extend(["-c:s", "copy"])
    ffmpeg_cmd.append(output_file)
    return ffmpeg_cmd
