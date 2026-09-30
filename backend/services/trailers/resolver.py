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
from config.settings import app_settings
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

    Two profile settings decide what survives:

    - `Always Search` returns nothing at all, so the caller searches.
    - `Trailer Language`, when it names a language, keeps only the videos
      recorded in that language. A video of another language is not what
      was asked for, and a video with no recorded language cannot be shown
      to be what was asked for. A profile that takes any language leaves
      the field empty and keeps everything.

    Args:
        candidates (list[MediaVideoRead]): The rows for this media item,
            already in source order.
        profile (TrailerProfileRead): The profile that asks for a trailer.
        exclude (list[str] | None): Ids not to offer, such as the video of
            a trailer that is already on disk.
        last_tried (str | None): The candidate that the last run used. It
            goes to the end of the list, so a new run tries something else
            first and still returns to it when nothing else works.

    Returns:
        list[MediaVideoRead]: What to try, in order. Can be empty.
    """
    if profile.always_search:
        # `Always Search` means what it says: do not take an id from any
        # source, search YouTube with the search query of the profile.
        # That is what it did before the candidates table existed — it
        # cleared `media.youtube_trailer_id`, the only source there was —
        # and the documentation has always said it ignores an id you set
        # by hand. A profile that wants one video keeps this off and adds
        # that video; a profile that wants Trailarr to look every time
        # turns it on.
        return []

    excluded = set(exclude or [])
    wanted = effective_language(profile)
    chosen: list[MediaVideoRead] = []
    for candidate in candidates:
        if candidate.video_id in excluded:
            continue
        if wanted and (candidate.language or "") != wanted:
            # The profile asks for one language, so a video in another
            # language is not an answer, and a video whose language nobody
            # recorded — an id from Radarr, or an old search result — is
            # not an answer either. Trailarr searches instead, with the
            # search query of the profile, which the user writes and can
            # aim at their language.
            continue
        chosen.append(candidate)

    if last_tried:
        # Wargame W5: the video of the last attempt may be deleted from
        # YouTube. Try the others first, but keep it, because the failure
        # may have been the network.
        chosen.sort(key=lambda c: c.video_id == last_tried)
    return chosen


# The sources whose videos an upgrade accepts. A video the user chose is
# never something to replace, and a TMDB trailer is what the upgrade is for.
UPGRADE_SOURCES = (VideoSource.USER, VideoSource.TMDB)


def upgrade_targets(
    candidates: list[MediaVideoRead],
    profile: TrailerProfileRead,
    *,
    exclude: list[str] | None = None,
    last_tried: str | None = None,
) -> list[MediaVideoRead]:
    """The videos that a profile with `Upgrade To TMDB Trailer` accepts.

    A trailer on disk that is one of these videos stays. A trailer that is
    not one of them is replaced by the first of them that downloads. The
    language filter of `choose_candidates` applies, so any TMDB trailer in
    the language of the profile is a match, not only the first one.

    Args:
        candidates (list[MediaVideoRead]): The rows for this media item,
            already in source order.
        profile (TrailerProfileRead): The profile to check.
        exclude (list[str] | None): Ids not to offer, as for
            `choose_candidates`.
        last_tried (str | None): The candidate that the last run used, as
            for `choose_candidates`.

    Returns:
        list[MediaVideoRead]: The accepted videos, best first. Empty when
            the setting is off, when there is no TMDB key, when `Always
            Search` is on, or when TMDB lists nothing for the profile.
    """
    if not profile.upgrade_to_tmdb or not app_settings.tmdb_api_key:
        return []
    return choose_candidates(
        [c for c in candidates if c.source in UPGRADE_SOURCES],
        profile,
        exclude=exclude,
        last_tried=last_tried,
    )


def upgrade_keeps(
    candidates: list[MediaVideoRead],
    targets: list[MediaVideoRead],
) -> set[str]:
    """The video ids whose trailer an upgrade keeps.

    That is every target, and every video the user chose, in any
    language. The language filter decides what an upgrade downloads. It
    does not make Trailarr delete a video that a person picked: a video
    added with no language, or in another language, is still their choice.

    Args:
        candidates (list[MediaVideoRead]): The rows for this media item.
        targets (list[MediaVideoRead]): What `upgrade_targets` gave.

    Returns:
        set[str]: The video ids to keep.
    """
    kept = {target.video_id for target in targets}
    kept.update(
        c.video_id for c in candidates if c.source == VideoSource.USER
    )
    return kept


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


def effective_language(profile: TrailerProfileRead) -> str:
    """The trailer language this profile can really ask for.

    Only TMDB records which language a trailer is in, so without a TMDB
    API key no video in the table has one, and a language would match
    nothing at all: every download would fall through to a search. So a
    language without a key means any language, which is what the profile
    did before the field existed.

    The profile page disables the field for the same reason, and says why.

    Args:
        profile (TrailerProfileRead): The profile that asks for a trailer.

    Returns:
        str: The language to filter by, or an empty string for any.
    """
    if not app_settings.tmdb_api_key:
        return ""
    return (profile.language or "").strip()
