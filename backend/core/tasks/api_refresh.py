import threading

from config.logging_context import with_logging_context
import core.base.database.manager.connection as connection_manager
from core.base.database.models.connection import ArrType, ConnectionRead
from core.plex.connection_manager import PlexConnectionManager
from core.radarr.connection_manager import RadarrConnectionManager
from core.sonarr.connection_manager import SonarrConnectionManager
from app_logger import ModuleLogger
from api.v1.websockets import ws_manager
from core.tasks.image_refresh import refresh_images
from core.tasks import scheduler

logger = ModuleLogger("APIRefreshTasks")


async def api_refresh(_stop_event: threading.Event | None = None) -> None:
    logger.info("Refreshing data from APIs")
    # Get all connections from database
    connections = connection_manager.read_all()
    if len(connections) == 0:
        logger.warning("No connections found in the database")
        return

    # Refresh data from API for each connection
    for connection in connections:
        if _stop_event and _stop_event.is_set():
            logger.info("API Refresh stopped due to stop event.")
            return
        await api_refresh_by_id(connection, image_refresh=False)

    # Refresh images after API refresh to download/update images for new media
    if _stop_event and _stop_event.is_set():
        logger.info("API Refresh stopped due to stop event.")
        return
    await refresh_images(recent_only=True, _stop_event=_stop_event)
    logger.info("API Refresh completed!")


async def api_refresh_by_id(
    connection: ConnectionRead,
    image_refresh=True,
    _stop_event: threading.Event | None = None,
) -> None:
    logger.info(f"Refreshing data from API for connection: {connection.name}")
    # Get connection manager based on connection type
    if connection.arr_type == ArrType.SONARR:
        connection_db_manager = SonarrConnectionManager(connection)
    elif connection.arr_type == ArrType.RADARR:
        connection_db_manager = RadarrConnectionManager(connection)
    elif connection.arr_type == ArrType.PLEX:
        connection_db_manager = PlexConnectionManager(connection)
    else:
        logger.warning(
            f"Invalid connection type: {connection.arr_type} for connection:"
            f" {connection}"
        )
        return

    # Refresh data from API
    await connection_db_manager.refresh()
    logger.info(f"Data refreshed for connection: {connection.name}")

    # Refresh images after API refresh to download/update images for new media
    if image_refresh:
        await refresh_images(recent_only=True, _stop_event=_stop_event)
        logger.info("Images refreshed")
        logger.info("API Refresh completed!")


@with_logging_context
async def _api_refresh_by_id_job(
    connection: ConnectionRead,
    *,
    _job_id: str | None = None,
    _stop_event: threading.Event | None = None,
):
    await api_refresh_by_id(connection, _stop_event=_stop_event)
    return None


def api_refresh_by_id_job(connection_id: int):

    logger.info(f"Refreshing data from API for connection ID: {connection_id}")
    # Get connection from database
    try:
        connection = connection_manager.read(connection_id)
    except Exception as e:
        msg = f"Failed to get connection with ID: {connection_id}"
        logger.error(f"{msg}. Error: {e}")
        return msg

    # Refresh data from API for the connection
    msg = f"Refreshing data from API for connection: {connection.name}"
    logger.info(msg)
    scheduler.add_task(
        task_name=f"Arr Data Refresh for {connection.name}",
        func=_api_refresh_by_id_job,
        interval=86400.0,
        delay=1,
        run_once=True,
        args=(connection,),
    )
    return msg


@with_logging_context
async def _delete_connection_job(
    connection_id: int,
    connection_name: str,
    *,
    _job_id: str | None = None,
    _stop_event: threading.Event | None = None,
) -> None:
    """Background task: delete a connection and all its cascaded data."""
    logger.info(
        f"Deleting connection '{connection_name}' (id={connection_id})"
    )
    try:
        connection_manager.delete(connection_id)
        logger.info(
            f"Connection '{connection_name}' (id={connection_id}) deleted"
        )
        await ws_manager.broadcast(
            f"Connection '{connection_name}' deleted successfully!",
            "Success",
            reload="connections,media",
        )
    except Exception as e:
        logger.error(
            f"Failed to delete connection '{connection_name}'"
            f" (id={connection_id}): {e}"
        )
        await ws_manager.broadcast(
            f"Failed to delete connection '{connection_name}'!", "Error"
        )


def delete_connection_job(connection_id: int) -> str:
    """Validate that *connection_id* exists, then schedule its deletion.

    Returns a human-readable message suitable for the HTTP response.
    Raises the underlying exception (e.g. ItemNotFoundError) if the
    connection cannot be found so the caller can return a 404.
    """
    connection = connection_manager.read(connection_id)  # raises if not found
    task_name = f"Delete Connection '{connection.name}'"
    logger.info(
        f"Scheduling deletion for connection '{connection.name}'"
        f" (id={connection_id})"
    )
    scheduler.add_task(
        task_name=task_name,
        func=_delete_connection_job,
        interval=86400.0,
        delay=1,
        run_once=True,
        args=(connection_id, connection.name),
    )
    return f"Connection '{connection.name}' deletion scheduled"
