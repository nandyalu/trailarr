from config.settings import app_settings

# CPU
# ffmpeg -i input.mkv -c:v libx264 -preset veryfast -crf 22 -c:a aac -b:a 128k -c:s srt -movflags +faststart -tune zerolatency output1-converted3-264-aac-srt-cpu-fast.mkv  # noqa: E501
# ffmpeg -i temp_2206-trailer.mkv -c:v libaom-av1 -preset veryfast -crf 22 -c:a copy output1.mkv  # noqa: E501

# NVIDIA - web optimized options not working
# ffmpeg -hwaccel cuda -hwaccel_output_format cuda -i input.mkv -c:v h264_nvenc -preset fast -cq 22 -c:a aac -b:a 128k -c:s srt output1-converted3-264-aac-srt-nvenc.mkv  # noqa: E501

# VAAPI (Intel) - Not implementing as it requires a lot of setup, maybe in future
# ffmpeg -init_hw_device vaapi=foo:/dev/dri/renderD128 -filter_hw_device foo -i output1.mkv -vf 'format=nv12,hwupload' -c:v h264_vaapi -qp 22 -c:a aac -b:a 128k -c:s srt output1-converted3-264-aac-srt-i916hw-fast.mkv  # noqa: E501

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


def _get_video_options_cpu(input_file: str) -> list[str]:
    return [
        "ffmpeg",
        "-i",
        input_file,
        "-c:v",
        _VIDEO_CODECS[app_settings.trailer_video_format],
        "-preset",
        "veryfast",
        "-crf",
        "22",
        "-c:a",
        _AUDIO_CODECS[app_settings.trailer_audio_format],
        "-b:a",
        "128k",
        "-c:s",
        "srt",
        "-movflags",
        "+faststart",
        "-tune",
        "zerolatency",
    ]


def _get_video_options():
    pass
