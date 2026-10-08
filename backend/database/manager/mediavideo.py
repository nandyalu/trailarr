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
    video_type: str | None = VIDEO_TYPE_TRAILER,
    season: int | None = None,
    _session: Session = None,  # type: ignore
) -> list[MediaVideoRead]:
    """Get the videos to try for one media item, in order.

    Args:
        media_id (int): The media item.
        language (str | None): The language the profile asks for. Only
            videos recorded in that language come back. None or empty
            means any language, and everything comes back.
        video_type (str | None): The type of video the caller wants,
            'trailer' by default. A profile passes its own type. None
            gives every type, for a caller that serves several profiles
            and filters per profile, as `upgrade_targets` does.
        season (int | None): NULL is the movie, or the series as a whole.

    Returns:
        list[MediaVideoRead]: The candidates, best first.
    """
    statement = select(MediaVideo).where(MediaVideo.media_id == media_id)
    if video_type is not None:
        statement = statement.where(MediaVideo.video_type == video_type)
    if season is None:
        statement = statement.where(col(MediaVideo.season).is_(None))
    else:
        statement = statement.where(MediaVideo.season == season)
    videos = [_to_read(v) for v in _session.exec(statement).all()]
    ordered = sort_candidates(videos)
    if not language:
        return ordered
    # A language is a filter, not an order. The resolver applies the same
    # rule; this keeps a caller that asks for one language from having to.
    return [v for v in ordered if (v.language or "") == language]


@read_session
def read_candidates_by_media(
    *,
    _session: Session = None,  # type: ignore
) -> dict[int, list[MediaVideoRead]]:
    """Get the known videos of every media item, in one query.

    A library-wide pass runs the satisfaction rule for each media item,
    and one query per item would be slow on a large library. Every source
    and every type is read, the same set that `read_candidates(media_id,
    video_type=None)` gives one item: the pass must decide an upgrade and
    a wait for TMDB from the same videos as the download task. The
    resolver filters by source where it must (`upgrade_targets` takes
    USER and TMDB rows only).

    Returns:
        dict[int, list[MediaVideoRead]]: The rows per media id, each list
            in resolution order. A media item with no rows is not a key.
    """
    statement = select(MediaVideo).where(col(MediaVideo.season).is_(None))
    by_media: dict[int, list[MediaVideoRead]] = {}
    for video in _session.exec(statement).all():
        by_media.setdefault(video.media_id, []).append(_to_read(video))
    return {
        media_id: sort_candidates(videos)
        for media_id, videos in by_media.items()
    }


@write_session
def replace_source_rows(
    media_id: int,
    source: VideoSource,
    videos: list[MediaVideoCreate],
    *,
    video_type: str | None = VIDEO_TYPE_TRAILER,
    season: int | None = None,
    _session: Session = None,  # type: ignore
) -> tuple[int, int, int]:
    """Give one source a new list of videos for one media item.

    Rows of other sources are not read and not changed. A row of this
    source that is not in `videos` is removed, because the source no
    longer offers it.

    With `video_type=None` the list covers every type at once, and each
    row takes the type of its incoming video. The TMDB refresh uses this:
    one TMDB call returns every type, and a video that TMDB moves from
    `Teaser` to `Trailer` must change its row instead of raising on the
    unique key `(media_id, video_id)`.

    Args:
        media_id (int): The media item.
        source (VideoSource): The source that owns the rows. USER is not
            allowed: the user owns those rows, not a task.
        videos (list[MediaVideoCreate]): What the source offers now.
        video_type (str | None): The type the list covers, or None for
            every type, with the type taken from each video.
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
    )
    if season is None:
        statement = statement.where(col(MediaVideo.season).is_(None))
    else:
        statement = statement.where(MediaVideo.season == season)
    same_source = _session.exec(statement).all()
    existing = {
        v.video_id: v
        for v in same_source
        if video_type is None or v.video_type == video_type
    }
    # A row of this source with another type is not in the list that
    # this call replaces, so it is left alone, unless the list offers
    # the same video: (media_id, video_id) is unique, so that row changes
    # type instead of raising. A search for a featurette that finds the
    # video an earlier trailer search found does this.
    retyped = {
        v.video_id: v
        for v in same_source
        if video_type is not None and v.video_type != video_type
    }

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
        row = (
            existing.get(incoming.video_id)
            or retyped.get(incoming.video_id)
            or claimable.get(incoming.video_id)
        )
        row_type = video_type or incoming.video_type or VIDEO_TYPE_TRAILER
        if row is not None and row.source != source:
            # Take the row over, with the better information this source
            # has: an Arr gives an id, and TMDB gives the title, the
            # language and whether the studio published it.
            row.source = source
            row.season = season
            row.video_type = row_type
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
                    video_type=row_type,
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
            or row.video_type != row_type
        )
        if changed:
            row.video_type = row_type
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
    language: str | None = None,
    video_type: str = VIDEO_TYPE_TRAILER,
    season: int | None = None,
    _session: Session = None,  # type: ignore
) -> MediaVideoRead:
    """Add the video that the user chose, or take over the row that another
    source made for the same video.

    Taking over is what the user asked for: the video they typed is now
    their choice, and no task may remove it.

    The language matters when a profile asks for one. Someone who wants an
    Italian trailer and an English one runs two profiles, and each takes
    the video recorded in its own language, so a user video with no
    language is only ever used by a profile that takes any language.
    """
    existing = _session.exec(
        select(MediaVideo)
        .where(MediaVideo.media_id == media_id)
        .where(MediaVideo.video_id == video_id)
    ).first()
    now = _now()
    if existing is not None:
        existing.source = VideoSource.USER
        # The person says what the video is. A trailer that TMDB listed
        # can be the featurette they want, and their choice wins.
        existing.video_type = video_type
        existing.updated_at = now
        if name:
            existing.name = name
        if language is not None:
            existing.language = language.strip() or None
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
        language=(language or "").strip() or None,
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
