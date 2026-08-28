from fastapi import APIRouter, HTTPException, status

from api.v1.models import ErrorResponse
from app_logger import ModuleLogger
import database.manager.notificationchannel as channel_manager
from database.models.notificationchannel import (
    NotificationChannelCreate,
    NotificationChannelRead,
)
from services.notifications import dispatcher
from exceptions import ItemNotFoundError

logger = ModuleLogger("NotificationsAPI")

notifications_router = APIRouter(prefix="/notifications", tags=["Notifications"])


@notifications_router.get("/")
async def get_channels() -> list[NotificationChannelRead]:
    """Get all notification channels. Apprise URLs are write-only and
    returned masked."""
    return channel_manager.read_all()


@notifications_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Invalid channel data",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Unexpected error creating the channel",
        },
    },
)
async def create_channel(
    channel: NotificationChannelCreate,
) -> NotificationChannelRead:
    """Create a notification channel. \n
    Args:
        channel (NotificationChannelCreate): Name, Apprise URL, subscribed
            event types (EventType names) and options. \n
    Returns:
        NotificationChannelRead: The created channel (URL masked).
    """
    try:
        return channel_manager.create(channel)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except Exception as e:
        # Log only the exception type — the message/traceback of a DB error
        # here (e.g. IntegrityError on the unique name) can include the
        # statement's bound parameters, which would leak the Apprise URL.
        logger.warning(f"Failed to create notification channel: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create notification channel",
        )


@notifications_router.put(
    "/{channel_id}",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Channel Not Found",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Unexpected error updating the channel",
        },
    },
)
async def update_channel(
    channel_id: int, channel: NotificationChannelCreate
) -> NotificationChannelRead:
    """Update a channel. An empty url keeps the stored one."""
    try:
        return channel_manager.update(channel_id, channel)
    except ItemNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except Exception as e:
        # Log only the exception type — see create_channel for why the
        # message/traceback must not be logged here.
        logger.warning(f"Failed to update notification channel: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification channel",
        )


@notifications_router.delete(
    "/{channel_id}",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Channel Not Found",
        }
    },
)
async def delete_channel(channel_id: int) -> str:
    """Delete a channel."""
    try:
        channel_manager.delete(channel_id)
        return "Notification channel deleted"
    except ItemNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@notifications_router.post(
    "/{channel_id}/test",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Channel Not Found",
        },
        status.HTTP_502_BAD_GATEWAY: {
            "model": ErrorResponse,
            "description": "Test notification failed to send",
        },
    },
)
async def test_channel(channel_id: int) -> str:
    """Send a test notification to a channel immediately."""
    try:
        success = await dispatcher.send_test(channel_id)
    except ItemNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except Exception as e:
        logger.warning(f"Test notification errored: {type(e).__name__}")
        success = False
    if not success:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Test notification failed — check the Apprise URL for this"
                " channel"
            ),
        )
    return "Test notification sent!"
