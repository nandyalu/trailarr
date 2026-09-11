"""The videos that Trailarr knows about for a media item.

Each source owns its own rows, and this module is where that rule lives:

- `replace_source_rows` gives one source a new list for one media item. It
  adds what is new, updates what changed, and removes the rows of THAT
  source that the source no longer offers. It never looks at a row of
  another source.
- USER rows are the choice of the user. No automation writes or removes
  one. `replace_source_rows` refuses to take USER as its source, so a
  mistake in a task cannot delete them.

`read_candidates` returns the videos to try, in the order the resolver
wants: the source precedence first, then the order inside the source.
"""

from datetime import datetime, timezone

from sqlmodel import Session, col, select

from database.engine import read_session, write_session
from database.models.mediavideo import (
    SOURCE_PRECEDENCE,
    VIDEO_TYPE_TRAILER,
    MediaVideo,
    MediaVideoCreate,
    MediaVideoRead,
    VideoSource,
)


def _to_read(video: MediaVideo) -> MediaVideoRead:
    return MediaVideoRead.model_validate(video)


def _now() -> datetime:
    return datetime.now(timezone.utc)


@read_session
def read_for_media(
    media_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> list[MediaVideoRead]:
    """Get every video known for a media item, in resolution order."""
    statement = select(MediaVideo).where(MediaVideo.media_id == media_id)
    videos = [_to_read(v) for v in _session.exec(statement).all()]
    return sort_candidates(videos)


def sort_candidates(videos: list[MediaVideoRead]) -> list[MediaVideoRead]:
    """Put the videos in the order the resolver tries them.

    The source decides first (USER, then TMDB, then ARR, then SEARCH), and
    inside one source the sequence that the source gave decides. The id is
    the last key, so the order never depends on the order rows come back
    from the database.
    """
    return sorted(
        videos,
        key=lambda v: (
            SOURCE_PRECEDENCE.get(v.source.value, len(SOURCE_PRECEDENCE)),
            v.sequence,
            v.id,
        ),
    )


@read_session
def read_candidates(
    media_id: int,
    *,
    language: str | None = None,
    video_type: str = VIDEO_TYPE_TRAILER,
    season: int | None = None,
    _session: Session = None,  # type: ignore
) -> list[MediaVideoRead]:
    """Get the videos to try for one media item, in order.

    Args:
        media_id (int): The media item.
        language (str | None): The language the profile asks for. A video
            in that language comes first, then a video with no language,
            then the rest. None keeps the source order only.
        video_type (str): Only 'trailer' exists until Phase 9.
        season (int | None): NULL is the movie, or the series as a whole.

    Returns:
        list[MediaVideoRead]: The candidates, best first.
    """
    statement = (
        select(MediaVideo)
        .where(MediaVideo.media_id == media_id)
        .where(MediaVideo.video_type == video_type)
    )
    if season is None:
        statement = statement.where(col(MediaVideo.season).is_(None))
    else:
        statement = statement.where(MediaVideo.season == season)
    videos = [_to_read(v) for v in _session.exec(statement).all()]
    if not language:
        return sort_candidates(videos)

    # A language is a preference, not a filter: a trailer in another
    # language is better than no trailer. So the list keeps everything and
    # only changes the order.
    #
    # The source still decides first. Sorting by language across sources
    # would let a TMDB trailer in the asked language beat the video that
    # the user chose, which is the one thing the order must never do — a
    # USER row carries no language, because a person pasted a link.
    def language_rank(video: MediaVideoRead) -> int:
        if video.language == language:
            return 0
        if video.language is None:
            return 1
        if video.language == "en":
            return 2
        return 3

    return sorted(
        videos,
        key=lambda v: (
            SOURCE_PRECEDENCE.get(v.source.value, len(SOURCE_PRECEDENCE)),
            language_rank(v),
            v.sequence,
            v.id,
        ),
    )


@write_session
def replace_source_rows(
    media_id: int,
    source: VideoSource,
    videos: list[MediaVideoCreate],
    *,
    video_type: str = VIDEO_TYPE_TRAILER,
    season: int | None = None,
    _session: Session = None,  # type: ignore
) -> tuple[int, int, int]:
    """Give one source a new list of videos for one media item.

    Rows of other sources are not read and not changed. A row of this
    source that is not in `videos` is removed, because the source no
    longer offers it.

    Args:
        media_id (int): The media item.
        source (VideoSource): The source that owns the rows. USER is not
            allowed: the user owns those rows, not a task.
        videos (list[MediaVideoCreate]): What the source offers now.
        video_type (str): The type the list covers.
        season (int | None): The season the list covers.

    Returns:
        tuple[int, int, int]: How many rows were added, updated and removed.

    Raises:
        ValueError: If the source is USER.
    """
    if source == VideoSource.USER:
        raise ValueError(
            "A task cannot replace the videos that the user chose."
            " Use add_user_video or delete_video instead."
        )

    statement = (
        select(MediaVideo)
        .where(MediaVideo.media_id == media_id)
        .where(MediaVideo.source == source)
        .where(MediaVideo.video_type == video_type)
    )
    if season is None:
        statement = statement.where(col(MediaVideo.season).is_(None))
    else:
        statement = statement.where(MediaVideo.season == season)
    existing = {v.video_id: v for v in _session.exec(statement).all()}

    # A video can be offered by more than one source, and (media_id,
    # video_id) is unique, so only one row can exist for it. The better
    # source takes the row.
    #
    # This is not a detail. On a real library of 3,704 titles, 1,822 of the
    # ids that Radarr and Sonarr report are the very trailer that TMDB
    # lists. Leaving those rows with the Arr meant two things: the list
    # showed a row with no title, because an Arr reports an id and nothing
    # else, and the trailer that both sources agree on sorted below TMDB's
    # other trailers, so Trailarr downloaded the second-best one.
    #
    # A row that the user owns is never taken. That is the invariant of
    # decision 5b: their choice outranks every source, including this one.
    others = {
        v.video_id: v
        for v in _session.exec(
            select(MediaVideo).where(MediaVideo.media_id == media_id)
        ).all()
        if v.source != source
    }
    incoming_rank = SOURCE_PRECEDENCE.get(source.value, len(SOURCE_PRECEDENCE))
    taken = {
        video_id
        for video_id, row in others.items()
        if row.source == VideoSource.USER
        or SOURCE_PRECEDENCE.get(row.source.value, len(SOURCE_PRECEDENCE))
        <= incoming_rank
    }
    claimable = {
        video_id: row
        for video_id, row in others.items()
        if video_id not in taken
    }

    added = updated = removed = 0
    seen: set[str] = set()
    now = _now()
    for incoming in videos:
        if not incoming.video_id or incoming.video_id in seen:
            continue
        seen.add(incoming.video_id)
        if incoming.video_id in taken:
            continue
        row = existing.get(incoming.video_id) or claimable.get(
            incoming.video_id
        )
        if row is not None and row.source != source:
            # Take the row over, with the better information this source
            # has: an Arr gives an id, and TMDB gives the title, the
            # language and whether the studio published it.
            row.source = source
            row.season = season
            row.video_type = video_type
            row.updated_at = now
            # Added explicitly rather than left to the dirty tracking of
            # the session: when the rest of the row happens to match, the
            # block below writes nothing, and the new source still has to
            # be saved.
            _session.add(row)
            existing[incoming.video_id] = row
        if row is None:
            _session.add(
                MediaVideo(
                    media_id=media_id,
                    video_id=incoming.video_id,
                    source=source,
                    season=season,
                    video_type=video_type,
                    sequence=incoming.sequence,
                    language=incoming.language,
                    name=incoming.name,
                    official=incoming.official,
                    published_at=incoming.published_at,
                    added_at=now,
                    updated_at=now,
                )
            )
            added += 1
            continue
        changed = (
            row.sequence != incoming.sequence
            or row.language != incoming.language
            or row.name != incoming.name
            or row.official != incoming.official
            or row.published_at != incoming.published_at
        )
        if changed:
            row.sequence = incoming.sequence
            row.language = incoming.language
            row.name = incoming.name
            row.official = incoming.official
            row.published_at = incoming.published_at
            row.updated_at = now
            _session.add(row)
            updated += 1

    for video_id, row in existing.items():
        if video_id not in seen:
            _session.delete(row)
            removed += 1

    _session.commit()
    return added, updated, removed


@write_session
def add_user_video(
    media_id: int,
    video_id: str,
    *,
    name: str = "",
    video_type: str = VIDEO_TYPE_TRAILER,
    season: int | None = None,
    _session: Session = None,  # type: ignore
) -> MediaVideoRead:
    """Add the video that the user chose, or take over the row that another
    source made for the same video.

    Taking over is what the user asked for: the video they typed is now
    their choice, and no task may remove it.
    """
    existing = _session.exec(
        select(MediaVideo)
        .where(MediaVideo.media_id == media_id)
        .where(MediaVideo.video_id == video_id)
    ).first()
    now = _now()
    if existing is not None:
        existing.source = VideoSource.USER
        existing.updated_at = now
        if name:
            existing.name = name
        _session.add(existing)
        _session.commit()
        _session.refresh(existing)
        return _to_read(existing)

    row = MediaVideo(
        media_id=media_id,
        video_id=video_id,
        source=VideoSource.USER,
        season=season,
        video_type=video_type,
        sequence=0,
        language=None,
        name=name,
        official=False,
        published_at=None,
        added_at=now,
        updated_at=now,
    )
    _session.add(row)
    _session.commit()
    _session.refresh(row)
    return _to_read(row)


@write_session
def delete_video(
    media_id: int,
    video_id: str,
    *,
    _session: Session = None,  # type: ignore
) -> bool:
    """Remove one video from a media item.

    Returns False when the media item did not have that video.
    """
    row = _session.exec(
        select(MediaVideo)
        .where(MediaVideo.media_id == media_id)
        .where(MediaVideo.video_id == video_id)
    ).first()
    if row is None:
        return False
    _session.delete(row)
    _session.commit()
    return True


@write_session
def relabel_as_user(
    media_id: int,
    video_id: str,
    *,
    _session: Session = None,  # type: ignore
) -> bool:
    """Mark an ARR row as the choice of the user.

    The upgrade recovery of decision 5: a stored id that no longer matches
    what Radarr or Sonarr reports was almost certainly typed by the user
    before Phase 8 existed, so it becomes a USER row and no task removes it.
    """
    row = _session.exec(
        select(MediaVideo)
        .where(MediaVideo.media_id == media_id)
        .where(MediaVideo.video_id == video_id)
    ).first()
    if row is None or row.source == VideoSource.USER:
        return False
    row.source = VideoSource.USER
    row.updated_at = _now()
    _session.add(row)
    _session.commit()
    return True
