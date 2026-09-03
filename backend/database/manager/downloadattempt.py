"""Failed download attempts, and the backoff they cause.

A failed attempt for a media and profile pair delays the next try. The delay
doubles with each failure, up to a cap, so a title that cannot be downloaded
does not run on every pass.
"""

from datetime import datetime, timezone

from sqlmodel import Session, col, delete, select

from database.models.downloadattempt import (
    DEFAULT_UNIT,
    MAX_ERROR_LENGTH,
    DownloadAttempt,
    DownloadAttemptRead,
)
from database.engine import read_session, write_session
from utils.error_classify import classified_error


def _to_read(attempt: DownloadAttempt) -> DownloadAttemptRead:
    return DownloadAttemptRead.model_validate(attempt)


@read_session
def read_all(
    *,
    _session: Session = None,  # type: ignore
) -> list[DownloadAttemptRead]:
    """Get every download attempt row — used by the library-wide pending
    view so it never issues per-media attempt queries."""
    statement = select(DownloadAttempt)
    return [_to_read(a) for a in _session.exec(statement).all()]


@read_session
def read_for_media(
    media_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> list[DownloadAttemptRead]:
    """Get all download attempts for a media item."""
    statement = select(DownloadAttempt).where(
        DownloadAttempt.media_id == media_id
    )
    return [_to_read(a) for a in _session.exec(statement).all()]


@write_session
def record_failure(
    media_id: int,
    profile_id: int,
    error: str,
    unit: str = DEFAULT_UNIT,
    *,
    _session: Session = None,  # type: ignore
) -> DownloadAttemptRead:
    """Record a failed download attempt for (media, profile, unit) —
    creates the row or increments its counter. Only real attempted-and-failed
    downloads belong here; validation skips (missing folder etc.) do not."""
    statement = select(DownloadAttempt).where(
        DownloadAttempt.media_id == media_id,
        DownloadAttempt.profile_id == profile_id,
        DownloadAttempt.unit == unit,
    )
    attempt = _session.exec(statement).first()
    if attempt is None:
        attempt = DownloadAttempt(
            media_id=media_id, profile_id=profile_id, unit=unit
        )
    attempt.attempt_count += 1
    attempt.last_attempt_at = datetime.now(timezone.utc)
    # Known yt-dlp failures are stored as a plain-language reason with
    # the fix (for example, "YouTube requires a sign-in... Set up a cookies
    # file"), with the raw error line kept in brackets for bug reports.
    if error:
        error = classified_error(error)
    attempt.last_error = error[:MAX_ERROR_LENGTH] if error else None
    _session.add(attempt)
    _session.commit()
    _session.refresh(attempt)
    return _to_read(attempt)


@write_session
def clear(
    media_id: int,
    profile_id: int,
    unit: str = DEFAULT_UNIT,
    *,
    _session: Session = None,  # type: ignore
) -> None:
    """Delete the attempt row for (media, profile, unit) — called on a
    successful download so future runs start clean."""
    statement = delete(DownloadAttempt).where(
        col(DownloadAttempt.media_id) == media_id,
        col(DownloadAttempt.profile_id) == profile_id,
        col(DownloadAttempt.unit) == unit,
    )
    _session.exec(statement)  # type: ignore[call-overload]
    _session.commit()


@write_session
def prune_for_missing_profiles(
    valid_profile_ids: set[int],
    *,
    _session: Session = None,  # type: ignore
) -> int:
    """Delete attempt rows whose profile no longer exists (profiles are not
    FK-linked on purpose). Called lazily at download-task start."""
    statement = select(DownloadAttempt)
    if valid_profile_ids:
        statement = statement.where(
            col(DownloadAttempt.profile_id).notin_(valid_profile_ids)
        )
    stale = _session.exec(statement).all()
    for attempt in stale:
        _session.delete(attempt)
    if stale:
        _session.commit()
    return len(stale)
