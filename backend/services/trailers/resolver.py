"""Choosing which video to download for a media item.

Before Phase 8 there was one id per media item, in
`media.youtube_trailer_id`, and a YouTube search when it was empty. Now
there is a list of candidates, and this module picks from it.

The order comes from the source: what the user chose, then the curated
list of TMDB, then the id that Radarr or Sonarr gave, then a result that a
search stored earlier. Inside one source the order that the source gave
decides, and a trailer in the language of the profile comes first.

Nothing here talks to YouTube. The caller tries the ids in the order this
module gives, and falls back to a live search when the list runs out.
"""

from app_logger import ModuleLogger
from database.models.media import MediaRead
from database.models.mediavideo import MediaVideoRead, VideoSource
from database.models.trailerprofile import TrailerProfileRead

logger = ModuleLogger("TrailerResolver")


def choose_candidates(
    candidates: list[MediaVideoRead],
    profile: TrailerProfileRead,
    *,
    exclude: list[str] | None = None,
    last_tried: str | None = None,
) -> list[MediaVideoRead]:
    """Give back the candidates to try, best first.

    Args:
        candidates (list[MediaVideoRead]): The rows for this media item,
            already in source and language order.
        profile (TrailerProfileRead): The profile that asks for a trailer.
        exclude (list[str] | None): Ids not to offer, such as the video of
            a trailer that is already on disk.
        last_tried (str | None): The candidate that the last run used. It
            goes to the end of the list, so a new run tries something else
            first and still returns to it when nothing else works.

    Returns:
        list[MediaVideoRead]: What to try, in order. Can be empty.
    """
    excluded = set(exclude or [])
    chosen: list[MediaVideoRead] = []
    for candidate in candidates:
        if candidate.video_id in excluded:
            continue
        # `Always Search` means "do not reuse what a search found before".
        # It does not throw away the choice of the user, the list of TMDB,
        # or the id from Radarr or Sonarr: those are not search results.
        if profile.always_search and candidate.source == VideoSource.SEARCH:
            continue
        chosen.append(candidate)

    if last_tried:
        # Wargame W5: the video of the last attempt may be deleted from
        # YouTube. Try the others first, but keep it, because the failure
        # may have been the network.
        chosen.sort(key=lambda c: c.video_id == last_tried)
    return chosen


def describe_choice(media: MediaRead, candidate: MediaVideoRead) -> str:
    """The log line that says where a video came from.

    The exit criterion of Phase 8 is that a log line names the source of
    every resolution, so that a user can see TMDB working.
    """
    where = {
        VideoSource.USER: "the video you chose",
        VideoSource.TMDB: "the TMDB list",
        VideoSource.ARR: "the id from Radarr or Sonarr",
        VideoSource.SEARCH: "an earlier YouTube search",
    }.get(candidate.source, "an unknown source")
    return (
        f"Trailarr takes the trailer for '{media.title}' from {where}"
        f" ({candidate.video_id})."
    )
