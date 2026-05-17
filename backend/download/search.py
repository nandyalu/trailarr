from functools import partial
import os
import re
from typing import Any

from yt_dlp import YoutubeDL

from app_logger import ModuleLogger
from config.settings import app_settings
from db.models.media import MediaRead
from db.models.helpers import language_names
from db.models.trailerprofile import TrailerProfileRead
from download.cli import cli_to_api
from download.utils import extract_youtube_id

logger = ModuleLogger("TrailersDownloader")


def __replace_media_options(query: str, media: MediaRead) -> str:
    if not query or not media:
        return query
    format_opts = media.model_dump()
    format_opts["is_movie"] = "movie" if media.is_movie else "series"
    format_opts["year"] = "" if media.year == 0 else media.year
    _filename_wo_ext, _ = os.path.splitext(media.media_filename)
    format_opts["media_filename"] = _filename_wo_ext
    format_opts["language"] = language_names.get(media.language, media.language)
    _query = query.format(**format_opts)
    _query = re.sub(r"\s+", " ", _query).strip()
    return _query


def __has_all_words(words: list[str], title: str) -> bool:
    for word in words:
        if not word.strip():
            continue
        if "||" in word:
            subwords = word.split("||")
            if not __has_any_words(subwords, title):
                return False
        elif word.lower().strip() not in title.lower():
            return False
    return True


def __has_any_words(words: list[str], title: str) -> bool:
    for word in words:
        if not word.strip():
            if len(words) == 1:
                return True
            continue
        if "&&" in word:
            subwords = word.split("&&")
            if __has_all_words(subwords, title):
                return True
        elif word.lower().strip() in title.lower():
            return True
    return False


def __has_included_words(include_words: str, title: str) -> bool:
    if not include_words:
        return True
    include_list = [w.strip() for w in include_words.split(",") if w.strip()]
    if not include_list:
        return True
    return __has_all_words(include_list, title)


def __has_excluded_words(exclude_words: str, title: str) -> bool:
    if not exclude_words:
        return False
    exclude_list = [w.strip() for w in exclude_words.split(",") if w.strip()]
    if not exclude_list:
        return False
    return __has_any_words(exclude_list, title)


def __is_allowed_uploader(info: dict, uploader_ids: str, id: str) -> bool:
    allowed = [u.strip() for u in uploader_ids.split(",") if u.strip()]
    if not allowed:
        return True
    video_uploader_id = str(info.get("uploader_id", ""))
    video_channel_id = str(info.get("channel_id", ""))
    if not any(u in (video_uploader_id, video_channel_id) for u in allowed):
        logger.debug(f"Skipping video from non-allowed uploader: {id}")
        return False
    return True


def _yt_search_filter(
    info: dict,
    *,
    incomplete,
    media: MediaRead,
    profile: TrailerProfileRead,
    exclude: list[str] | None,
):
    id = info.get("id")
    if not id:
        return None
    if not exclude:
        exclude = []
    if id in exclude:
        logger.debug(f"Skipping video in excluded list: {id}")
        return "Video in excluded list"
    duration = int(info.get("duration", 0))
    min_duration = profile.min_duration
    if duration and duration < min_duration:
        logger.debug(f"Skipping short video (<{min_duration}): {id}")
        return f"The video is shorter than {min_duration} seconds"
    max_duration = profile.max_duration
    if duration and duration > max_duration:
        logger.debug(f"Skipping long video (>{max_duration}): {id}")
        return f"The video is longer than {max_duration} seconds"
    url = str(info.get("url", ""))
    if "/shorts/" in url:
        logger.debug(f"Skipping vertical (Shorts) video: {id}")
        return "The video is a vertical (Shorts) video"
    if not __is_allowed_uploader(info, profile.uploader_ids, id):
        return "The video uploader is not in the allowed list"
    title = str(info.get("title", ""))
    if "review" in title.lower():
        logger.debug(f"Skipping review video: {id}")
        return "The video is a review"
    _include_words = __replace_media_options(profile.include_words, media)
    if not __has_included_words(_include_words, title):
        logger.debug(f"Skipping video missing included words: {id}")
        return "The video does not contain all of the included words"
    _exclude_words = __replace_media_options(profile.exclude_words, media)
    if __has_excluded_words(_exclude_words, title):
        logger.debug(f"Skipping video containing excluded words: {id}")
        return "The video contains an excluded word"


def get_search_query(media: MediaRead, profile: TrailerProfileRead, search_length: int = 10) -> str:
    search_query = __replace_media_options(profile.search_query, media)
    if search_length < 10:
        search_length = 10
    return f"ytsearch{search_length}: {search_query}"


def add_extra_options(current_options: dict[str, Any], addl_options: str) -> None:
    if not current_options:
        return
    extra_options = cli_to_api(addl_options.split(), cli_defaults=False)
    for key, value in extra_options.items():
        if key in current_options:
            logger.warning(f"Cannot override default YT-DLP option '{key}' provided in Profile")
        else:
            current_options[key] = value


def search_yt_for_trailer(
    media: MediaRead,
    profile: TrailerProfileRead,
    exclude: list[str] | None = None,
    search_length: int = 10,
) -> str | None:
    logger.debug(f"Searching youtube for trailer for '{media.title}'...")
    filter_func = partial(_yt_search_filter, media=media, profile=profile, exclude=exclude)
    options = {
        "format": "bv*+ba/b",
        "match_filter": filter_func,
        "noplaylist": True,
        "extract_flat": "discard_in_playlist",
        "fragment_retries": 10,
        "noprogress": True,
        "no_warnings": app_settings.log_level != "DEBUG",
        "quiet": app_settings.log_level != "DEBUG",
        "verbose": app_settings.log_level == "DEBUG",
    }
    if app_settings.yt_cookies_path:
        logger.debug(f"Using cookies file: {app_settings.yt_cookies_path}")
        options["cookiefile"] = f"{app_settings.yt_cookies_path}"
    if profile.ytdlp_extra_options:
        logger.debug(f"Using extra options: {profile.ytdlp_extra_options}")
        add_extra_options(options, profile.ytdlp_extra_options)
    search_query = get_search_query(media, profile, search_length)
    logger.debug(f"Using Search query: {search_query}")
    with YoutubeDL(options) as ydl:  # type: ignore
        search_results = ydl.extract_info(search_query, download=False, process=True)
    if (
        not search_results
        or not isinstance(search_results, dict)
        or "entries" not in search_results
    ):
        return None
    if not exclude:
        exclude = []
    for result in search_results["entries"]:  # type: ignore
        if result["id"] in exclude:
            logger.debug(f"Skipping excluded video: {result['id']}")
            continue
        logger.debug(f"Found trailer for {media.title}: {result['id']}")
        return str(result["id"])
    return None


def get_video_id(
    media: MediaRead,
    profile: TrailerProfileRead,
    exclude: list[str] | None = None,
    search_length: int = 10,
) -> str | None:
    video_id = ""
    if media.youtube_trailer_id:
        if "youtu" in media.youtube_trailer_id:
            video_id = extract_youtube_id(media.youtube_trailer_id)
        else:
            video_id = media.youtube_trailer_id
    if video_id:
        media.youtube_trailer_id = video_id
        return video_id
    video_id = search_yt_for_trailer(media, profile, exclude, search_length=search_length)
    if not video_id:
        if search_length >= 30:
            logger.warning(
                f"No trailer found for '{media.title}' with profile"
                f" '{profile.customfilter.filter_name}'. Giving up after {search_length} search results."
            )
            return None
        logger.debug(
            f"No trailer found for '{media.title}' with profile"
            f" '{profile.customfilter.filter_name}'. Retrying with longer search length."
        )
        video_id = get_video_id(media, profile, exclude, search_length=search_length + 10)
    if video_id:
        media.youtube_trailer_id = video_id
    return video_id
