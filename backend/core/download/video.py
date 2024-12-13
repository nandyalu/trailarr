from datetime import datetime, timedelta, timezone
from typing import Any

from yt_dlp import YoutubeDL
from yt_dlp.utils import YoutubeDLError

from app_logger import ModuleLogger
from config.settings import app_settings

# For some reason, supplying a logger to YoutubeDL is not working with app_logger
# So, we are instead logging progress using progress hooks.

logger = ModuleLogger("TrailersDownloader")
last_log_time = datetime.now(timezone.utc) - timedelta(
    seconds=4
)  # For logging progress every 3 seconds


def _progress_hook(d):
    global last_log_time
    yt_id = "trailer"
    if "info_dict" in d:
        if "id" in d["info_dict"]:
            yt_id = d["info_dict"]["id"]
    if d["status"] == "downloading":
        current_time = datetime.now(timezone.utc)
        if current_time - last_log_time >= timedelta(seconds=3):
            logger.debug(
                f"[{yt_id}] Downloading {d['_percent_str']} of {d['_total_bytes_str']}"
            )
            last_log_time = current_time
    if d["status"] == "error":
        logger.debug(f"[{yt_id}] Error downloading {d['filename']}")
    if d["status"] == "finished":  # Guaranteed to call
        timetook = timedelta(seconds=d["elapsed"])
        data["filepath"] = d["filename"]
        logger.debug(
            f"[{yt_id}] Download completed in {timetook}! Size: {d['_total_bytes_str']} "
            f'Filepath: "{d["filename"]}"'
        )


def _postprocessor_hook(d):
    pprocessor = d["postprocessor"]
    yt_id = ""
    if "info_dict" in d:
        if "id" in d["info_dict"]:
            yt_id = d["info_dict"]["id"]
    status = ""
    if "status" in d:
        status = d["status"]
        # Check if the processor is already in data with same status
        # This makes sure we don't log the same status twice!
        if data and f"{pprocessor}" in data:
            if data[pprocessor]["status"] == status:
                return
    if status == "started":  # Guaranteed to call
        data[pprocessor] = {
            "starttime": datetime.now(timezone.utc),
            "status": "started",
            "endtime": None,
            "filepath": "",
        }
        logger.debug(f"[{yt_id}][{pprocessor}] Converting downloaded file...")
    if status == "processing":
        logger.debug(f"[{yt_id}][{pprocessor}] Conversion in progress...")
    if status == "finished":  # Guaranteed to call
        data[pprocessor]["status"] = "finished"
        data[pprocessor]["endtime"] = datetime.now(timezone.utc)
        timetook = data[pprocessor]["endtime"] - data[pprocessor]["starttime"]
        logger.debug(f"[{yt_id}][{pprocessor}] Done converting in {timetook}!")
        if "filepath" in d["info_dict"]:
            filepath = d["info_dict"]["filepath"]
            data[pprocessor]["filepath"] = filepath
            data["filepath"] = filepath
            logger.debug(f'[{yt_id}][{pprocessor}] Filepath: "{filepath}"')


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
        "ffmpeg_location": "/usr/local/bin/ffmpeg",
        "noplaylist": True,
        # "verbose": True,
        "extract_flat": "discard_in_playlist",
        "fragment_retries": 10,
        # Fix issue with youtube-dl not being able to download some videos
        # See https://github.com/yt-dlp/yt-dlp/issues/9554
        # "extractor_args": {"youtube": {"player_client": ["ios", "web"]}},
        "progress_hooks": [_progress_hook],
        "postprocessor_hooks": [_postprocessor_hook],
        "restrictfilenames": True,
        "noprogress": True,
        "no_warnings": True,
        "ignore_no_formats_error": True,
        "ignoreerrors": True,
        "quiet": True,
        "merge_output_format": app_settings.trailer_file_format,
        "postprocessors": [],
        "postprocessor_args": {},
    }
    if app_settings.yt_cookies_path:
        logger.debug(f"Using cookies file: {app_settings.yt_cookies_path}")
        ydl_options["cookiefile"] = f"{app_settings.yt_cookies_path}"
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

    # Apply audio volume level filter if enabled
    if app_settings.trailer_audio_volume_level != 100:
        volume_level = app_settings.trailer_audio_volume_level * 0.01
        output_options.append("-af")
        output_options.append(f"volume={volume_level}")

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

    # Set options to remove sponsorblock segments from the video
    if app_settings.trailer_remove_sponsorblocks:
        postprocessors.append(
            {
                "api": "https://sponsor.ajay.app",
                "categories": {"intro", "outro"},
                "key": "SponsorBlock",
                "when": "after_filter",
            }
        )
        postprocessors.append(
            {
                "force_keyframes": False,
                "key": "ModifyChapters",
                "remove_chapters_patterns": [],
                "remove_ranges": [],
                "remove_sponsor_segments": {"outro", "intro"},
                "sponsorblock_chapter_title": "[SponsorBlock]: %(category_names)l",
            }
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
        logger.debug(f"Downloading video from '{url}'")
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        if data and "filepath" in data:
            logger.debug(f"Downloaded video from '{url}' to: {data['filepath']}")
            return str(data["filepath"])
    except (YoutubeDLError, Exception) as e:
        logger.info(f"Error occurred while downloading video from {url}. Error: {e}")
    logger.debug(f"Failed to download video from {url}")
    return ""


# Uncomment below for testing, change logging level to DEBUG for additional logs
# if __name__ == "__main__":
#     # Random video
#     res = download_video("https://www.youtube.com/watch?v=WHXq62VCaCM")
#     # Age restricted video
#     res = download_video("https://www.youtube.com/watch?v=pLWda_RrQn4")
#     if res:
#         print(res)
