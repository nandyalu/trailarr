"""Turning what TMDB lists into the candidates Trailarr can download.

TMDB returns every video it knows for a title: trailers, teasers, clips,
featurettes and more, mixed together. Phase 8 downloads trailers, so only
the trailers become rows. Phase 9 adds the other types, and the
`video_type` column is already there for them.

The order of the TMDB list is not the order Trailarr wants. The first four
videos of The Matrix (TMDB 603) are featurettes, and the first trailer of
Inception (TMDB 27205) in TMDB order is `35mm Theatrical Trailer #3`,
which is not official, while two official trailers come after it. So an
official trailer goes before a trailer that is not official, and inside
each group the order of TMDB stays.
"""

from app_logger import ModuleLogger
from database.models.mediavideo import (
    VIDEO_TYPE_TRAILER,
    MediaVideoCreate,
    VideoSource,
)
from services.tmdb.models import TMDBVideo

logger = ModuleLogger("TMDBVideos")

# The TMDB type that Phase 8 stores. TMDB writes it exactly like this.
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
        list[MediaVideoCreate]: The trailers, best first, with `sequence`
            set to the position. An empty list when TMDB lists no trailer.
    """
    trailers = [
        (index, video)
        for index, video in enumerate(videos)
        if video.type.strip().lower() == TMDB_TYPE_TRAILER.lower()
    ]
    # False sorts before True, so `not official` puts an official trailer
    # first. The index of TMDB breaks the tie and keeps its order.
    trailers.sort(key=lambda pair: (not pair[1].official, pair[0]))

    candidates: list[MediaVideoCreate] = []
    for sequence, (_, video) in enumerate(trailers):
        candidates.append(
            MediaVideoCreate(
                media_id=media_id,
                video_id=video.key.strip(),
                source=VideoSource.TMDB,
                season=season,
                video_type=VIDEO_TYPE_TRAILER,
                sequence=sequence,
                language=video.language,
                name=video.name,
                official=video.official,
                published_at=video.published_at,
            )
        )
    return candidates
