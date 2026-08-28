from datetime import datetime, timezone

from sqlmodel import Session, select

from database.models.notificationchannel import (
    NotificationChannel,
    NotificationChannelCreate,
    NotificationChannelRead,
    mask_apprise_url,
)
from database.engine import read_session, write_session
from exceptions import ItemNotFoundError


def _to_read(channel: NotificationChannel) -> NotificationChannelRead:
    read = NotificationChannelRead(
        id=channel.id,  # type: ignore[arg-type]
        name=channel.name,
        enabled=channel.enabled,
        event_types=channel.event_types,
        include_user_events=channel.include_user_events,
        url_masked=mask_apprise_url(channel.url),
        added_at=channel.added_at,
        updated_at=channel.updated_at,
    )
    return read


def _get(channel_id: int, _session: Session) -> NotificationChannel:
    channel = _session.get(NotificationChannel, channel_id)
    if channel is None:
        raise ItemNotFoundError("NotificationChannel", channel_id)
    return channel


@read_session
def read_all(
    *,
    _session: Session = None,  # type: ignore
) -> list[NotificationChannelRead]:
    """Get all notification channels (URLs masked)."""
    channels = _session.exec(select(NotificationChannel)).all()
    return [_to_read(c) for c in channels]


@read_session
def get_url(
    channel_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> str:
    """Get the raw Apprise URL — for the dispatcher/test-send ONLY.
    Never expose through the API."""
    return _get(channel_id, _session).url


@write_session
def create(
    channel: NotificationChannelCreate,
    *,
    _session: Session = None,  # type: ignore
) -> NotificationChannelRead:
    """Create a notification channel. URL is required on create."""
    if not channel.url:
        raise ValueError("An Apprise URL is required to create a channel")
    db_channel = NotificationChannel(
        name=channel.name,
        url=channel.url,
        enabled=channel.enabled,
        event_types=channel.event_types,
        include_user_events=channel.include_user_events,
    )
    _session.add(db_channel)
    _session.commit()
    _session.refresh(db_channel)
    return _to_read(db_channel)


@write_session
def update(
    channel_id: int,
    channel: NotificationChannelCreate,
    *,
    _session: Session = None,  # type: ignore
) -> NotificationChannelRead:
    """Update a channel. An empty url keeps the stored one (the API never
    echoes URLs back, so edit forms submit blank for 'unchanged')."""
    db_channel = _get(channel_id, _session)
    db_channel.name = channel.name
    db_channel.enabled = channel.enabled
    db_channel.event_types = channel.event_types
    db_channel.include_user_events = channel.include_user_events
    if channel.url:
        db_channel.url = channel.url
    db_channel.updated_at = datetime.now(timezone.utc)
    _session.add(db_channel)
    _session.commit()
    _session.refresh(db_channel)
    return _to_read(db_channel)


@write_session
def delete(
    channel_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> None:
    """Delete a channel."""
    db_channel = _get(channel_id, _session)
    _session.delete(db_channel)
    _session.commit()


@read_session
def subscribed_channels(
    event_type_name: str,
    is_user_event: bool,
    *,
    _session: Session = None,  # type: ignore
) -> list[tuple[int, str]]:
    """(channel_id, url) pairs for enabled channels subscribed to the event
    type — dispatcher use only (raw URLs)."""
    channels = _session.exec(
        select(NotificationChannel).where(
            NotificationChannel.enabled == True  # noqa: E712
        )
    ).all()
    result: list[tuple[int, str]] = []
    for channel in channels:
        if event_type_name not in channel.event_types:
            continue
        if is_user_event and not channel.include_user_events:
            continue
        result.append((channel.id, channel.url))  # type: ignore[arg-type]
    return result
