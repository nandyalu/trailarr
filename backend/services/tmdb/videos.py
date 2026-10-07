"""Turning what TMDB lists into the candidates Trailarr can download.

TMDB returns every video it knows for a title: trailers, teasers, clips,
featurettes and more, mixed together. Every type becomes a row, with the
type that TMDB gives mapped to a `VideoType` (Phase 9). A profile of a
type then reads the rows of that type only.

The order of the TMDB list is not the order Trailarr wants. The first four
videos of The Matrix (TMDB 603) are featurettes, and the first trailer of
Inception (TMDB 27205) in TMDB order is `35mm Theatrical Trailer #3`,
which is not official, while two official trailers come after it. So an
official trailer goes before a trailer that is not official, and inside
each group the order of TMDB stays.
"""

from app_logger import ModuleLogger
from database.models.mediavideo import MediaVideoCreate, VideoSource
from database.models.video_type import video_type_from_tmdb
from services.tmdb.models import TMDBVideo

logger = ModuleLogger("TMDBVideos")

# The TMDB type of a trailer. TMDB writes it exactly like this.
TMDB_TYPE_TRAILER = "Trailer"


def to_candidates(
    videos: list[TMDBVideo],
    media_id: int,
    *,
    season: int | None = None,
) -> list[MediaVideoCreate]:
    """Turn the TMDB list into rows for one media item.

    Args:
        videos (list[TMDBVideo]): What the client got from TMDB, in the
            order TMDB gave.
        media_id (int): The media item the videos belong to.
        season (int | None): The season, when the list is a season list.

    Returns:
        list[MediaVideoCreate]: The videos of every type, best first
            inside each type, with `sequence` set to the position inside
            the type. An empty list when TMDB lists nothing.
    """
    typed = [
        (index, video_type_from_tmdb(video.type).value, video)
        for index, video in enumerate(videos)
    ]
    # Group by type, then official first: False sorts before True, so
    # `not official` puts an official video first. The index of TMDB
    # breaks the tie and keeps its order.
    typed.sort(key=lambda item: (item[1], not item[2].official, item[0]))

    candidates: list[MediaVideoCreate] = []
    sequence = 0
    last_type: str | None = None
    for _, video_type, video in typed:
        if video_type != last_type:
            sequence = 0
            last_type = video_type
        candidates.append(
            MediaVideoCreate(
                media_id=media_id,
                video_id=video.key.strip(),
                source=VideoSource.TMDB,
                season=season,
                video_type=video_type,
                sequence=sequence,
                language=video.language,
                name=video.name,
                official=video.official,
                published_at=video.published_at,
            )
        )
        sequence += 1
    return candidates
