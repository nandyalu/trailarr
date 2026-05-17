from fastapi import APIRouter, HTTPException, status

from api.v1.models import ErrorResponse
from app_logger import ModuleLogger
import db.repos.event as event_repo
from db.models.event import EventRead, EventSource, EventType
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
    return event_repo.read_all(
        limit=limit,
        offset=offset,
        event_type=event_type,
        event_source=event_source,
        media_id=media_id,
    )


@events_router.get(
    "/{event_id}",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Event Not Found"}},
)
async def get_event_by_id(event_id: int) -> EventRead:
    try:
        return event_repo.read(event_id)
    except ItemNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching event with ID {event_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching the event.",
        )


@events_router.get("/media/{media_id}")
async def get_events_by_media_id(media_id: int, limit: int = 100, offset: int = 0) -> list[EventRead]:
    return event_repo.read_by_media_id(media_id=media_id, limit=limit, offset=offset)
