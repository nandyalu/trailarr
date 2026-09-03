"""The event history. Events are a permanent record and are never pruned."""

from fastapi import APIRouter, HTTPException, status

from api.v1.models import ErrorResponse
from app_logger import ModuleLogger
import database.manager.event as event_manager
from database.models.event import EventRead, EventSource, EventType
from exceptions import ItemNotFoundError

logger = ModuleLogger("EventsAPI")

events_router = APIRouter(prefix="/events", tags=["Events"])


@events_router.get("/")
async def get_events(
    limit: int = 100,
    offset: int = 0,
    event_type: EventType | None = None,
    event_source: EventSource | None = None,
    media_id: int | None = None,
) -> list[EventRead]:
    """Get events from the database with optional filtering. \n
    Args:
        limit (int, Optional=100): Maximum number of events to return.
        offset (int, Optional=0): Number of events to skip.
        event_type (EventType, Optional=None): Filter by event type.
            Available types
            - media_added
            - monitor_changed
            - youtube_id_changed
            - trailer_detected
            - trailer_downloaded
            - trailer_deleted
            - download_skipped
        event_source (EventSource, Optional=None): Filter by event source.
            Available sources: user, system
        media_id (int | None, Optional=None): Filter by media ID. \n
    Returns:
        list[EventRead]: List of events.
    """
    return event_manager.read_all(
        limit=limit,
        offset=offset,
        event_type=event_type,
        event_source=event_source,
        media_id=media_id,
    )


@events_router.get(
    "/{event_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Event Not Found",
        }
    },
)
async def get_event_by_id(event_id: int) -> EventRead:
    """Get event by ID. \n
    Args:
        event_id (int): ID of the event. \n
    Returns:
        EventRead: Event object. \n
    Raises:
        HTTPException (404): If the event is not found.
    """
    try:
        return event_manager.read(event_id)
    except ItemNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except Exception as e:
        logger.error(
            f"Trailarr could not read the event {event_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching the event.",
        )


@events_router.get("/media/{media_id}")
async def get_events_by_media_id(
    media_id: int, limit: int = 100, offset: int = 0
) -> list[EventRead]:
    """Get all events for a specific media item. \n
    Args:
        media_id (int): ID of the media item.
        limit (int, Optional=100): Maximum number of events to return.
        offset (int, Optional=0): Number of events to skip. \n
    Returns:
        list[EventRead]: List of events for the media item.
    """
    return event_manager.read_by_media_id(
        media_id=media_id, limit=limit, offset=offset
    )


# Not needed for now and can be added later if needed.
# @events_router.delete("/cleanup/old")
# async def delete_old_events(days: int = 90) -> str:
#     """Delete events older than specified number of days. \n
#     Args:
#         days (int, Optional=90): Delete events older than this many days. \n
#     Returns:
#         str: Cleanup confirmation message with count of deleted events.
#     """
#     count = event_manager.delete_old_events(days=days)
#     return f"Deleted {count} events older than {days} days"
