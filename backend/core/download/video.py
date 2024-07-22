from datetime import datetime, timedelta, timezone
import logging
from typing import Any

from yt_dlp import YoutubeDL

from config.settings import app_settings

# For some reason, supplying a logger to YoutubeDL is not working with app_logger
# So, we are instead logging progress using progress hooks.


def _progress_hook(d):
    if d["status"] == "downloading":
        if d["_percent_str"] in ["25.0%", "50.0%", "75.0%", "100.0%"]:
            logging.debug(
                f"'Trailers': Downloading {d['_percent_str']} of {d['_total_bytes_str']}"
            )
        # logging.debug(
        #     f"'Trailers': Downloading {d['_percent_str']} of {d['_total_bytes_str']}"
        # )
    if d["status"] == "error":
        logging.info(f"'Trailers': Error downloading {d['filename']}")
    if d["status"] == "finished":  # Guaranteed to call
        timetook = timedelta(seconds=d["elapsed"])
        data["filepath"] = d["filename"]
        logging.debug(
            f"'Trailers': Download completed in {timetook}! Size: {d['_total_bytes_str']} "
            f'Filepath: "{d["filename"]}"'
        )


def _postprocessor_hook(d):
    pprocessor = d["postprocessor"]
    if d["status"] == "started":  # Guaranteed to call
        data[pprocessor] = {
            "starttime": datetime.now(timezone.utc),
            "status": "started",
            "endtime": None,
            "filepath": "",
        }
        logging.debug(f"'Trailers': [{pprocessor}] Converting downloaded file...")
    if d["status"] == "processing":
        logging.debug(f"'Trailers': [{pprocessor}] Conversion in progress...")
    if d["status"] == "finished":  # Guaranteed to call
        data[pprocessor]["status"] = "finished"
        data[pprocessor]["endtime"] = datetime.now(timezone.utc)
        timetook = data[pprocessor]["endtime"] - data[pprocessor]["starttime"]
        logging.debug(f"'Trailers': [{pprocessor}] Done converting in {timetook}!")
        if "filepath" in d["info_dict"]:
            filepath = d["info_dict"]["filepath"]
            data[pprocessor]["filepath"] = filepath
            data["filepath"] = filepath
            logging.debug(f"'Trailers': [{pprocessor}] Filepath: \"{filepath}\"")


data: dict[str, Any] = {}
data["filepath"] = ""

_VIDEO_CODECS = {
    "h264": "libx264",
    "h265": "libx265",
    "vp9": "libvpx-vp9",
    "vp8": "libvpx",
    "av1": "libaom-av1",
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


def _get_ytdl_options() -> dict[str, Any]:
    """Returns the options for youtube-dl to download trailers based on app config."""
    # Set generic options for youtube-dl
    ydl_options = {
        "compat_opts": {"no-keep-subs"},
        "ffmpeg_location": "/usr/local/bin/ffmpeg",  # ?figure out how to get this from os
        "noplaylist": True,
        # "verbose": True,
        "extract_flat": "discard_in_playlist",
        "fragment_retries": 10,
        # Fix issue with youtube-dl not being able to download some videos
        # See https://github.com/yt-dlp/yt-dlp/issues/9554
        "extractor_args": {"youtube": {"player_client": ["ios", "web"]}},
        "progress_hooks": [_progress_hook],
        "postprocessor_hooks": [_postprocessor_hook],
        "restrictfilenames": True,
        "noprogress": True,
        "no_warnings": True,
        "quiet": True,
        "merge_output_format": app_settings.trailer_file_format,
        "postprocessors": [],
        "postprocessor_args": {},
    }
    postprocessors: list[dict] = []
    output_options: list[str] = []

    # Set video specific options
    _format = f"bestvideo[height<=?{app_settings.trailer_resolution}]+bestaudio"
    ydl_options["format"] = _format
    if app_settings.trailer_embed_metadata:
        postprocessors.append({"key": "FFmpegMetadata", "add_metadata": True})
    video_format = _VIDEO_CODECS[app_settings.trailer_video_format]
    output_options.append("-c:v")
    output_options.append(video_format)
    output_options.append("-preset")
    output_options.append("veryfast")
    output_options.append("-crf")
    output_options.append("22")

    # Set audio specific options
    audio_format = _AUDIO_CODECS[app_settings.trailer_audio_format]
    output_options.append("-c:a")
    output_options.append(audio_format)
    output_options.append("-b:a")
    output_options.append("128k")

    # Set subtitle specific options
    if app_settings.trailer_subtitles_enabled:
        ydl_options["writeautomaticsub"] = True
        ydl_options["writesubtitles"] = True
        ydl_options["subtitleslangs"] = [app_settings.trailer_subtitles_language]
        postprocessors.append(
            {
                "key": "FFmpegSubtitlesConvertor",
                "format": app_settings.trailer_subtitles_format,
                "when": "before_dl",
            }
        )
        postprocessors.append(
            {"key": "FFmpegEmbedSubtitle", "already_have_subtitle": False},
        )

    # Set remaining options
    if app_settings.trailer_web_optimized:
        # Below options are for fast straming, but might increase filesize
        output_options.append("-movflags")
        output_options.append("+faststart")
        output_options.append("-tune")
        output_options.append("zerolatency")
    postprocessors.append({"key": "FFmpegCopyStream"})
    if len(postprocessors) > 0:
        ydl_options["postprocessors"] = postprocessors
    ydl_options["postprocessor_args"] = {"copystream": output_options}
    return ydl_options


def download_video(url: str, file_path: str | None = None) -> str:
    # Download the video from the given URL to the given path
    global data
    data = {}
    if not file_path:
        file_path = "/tmp/%(title)s.%(ext)s"
    ydl_opts = _get_ytdl_options()
    ydl_opts["outtmpl"] = file_path
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception:
        logging.exception(f"Failed to download video from {url}")
    return str(data["filepath"])
