import threading

from config.logging_context import with_logging_context
import db.repos.connection as connection_repo
from db.models.connection import ConnectionRead
from app_logger import ModuleLogger
from services import connection_service
from services.image_service import refresh_images
from tasks.scheduler import scheduler
from ws.manager import ws_manager

logger = ModuleLogger("APIRefreshTasks")


async def api_refresh(_stop_event: threading.Event | None = None) -> None:
    logger.info("Refreshing data from APIs")
    connections = connection_repo.read_all()
    if len(connections) == 0:
        logger.warning("No connections found in the database")
        return
    for connection in connections:
        if _stop_event and _stop_event.is_set():
            logger.info("API Refresh stopped due to stop event.")
            return
        await connection_service.refresh_connection(connection)
    if _stop_event and _stop_event.is_set():
        logger.info("API Refresh stopped due to stop event.")
        return
    await refresh_images(recent_only=True, _stop_event=_stop_event)
    logger.info("API Refresh completed!")


async def api_refresh_by_id(
    connection: ConnectionRead,
    image_refresh: bool = True,
    _stop_event: threading.Event | None = None,
) -> None:
    await connection_service.refresh_connection(connection)
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


def api_refresh_by_id_job(connection_id: int) -> str:
    logger.info(f"Refreshing data from API for connection ID: {connection_id}")
    try:
        connection = connection_repo.read(connection_id)
    except Exception as e:
        msg = f"Failed to get connection with ID: {connection_id}"
        logger.error(f"{msg}. Error: {e}")
        return msg
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
    logger.info(f"Deleting connection '{connection_name}' (id={connection_id})")
    try:
        connection_repo.delete(connection_id)
        logger.info(f"Connection '{connection_name}' (id={connection_id}) deleted")
        await ws_manager.broadcast(
            f"Connection '{connection_name}' deleted successfully!",
            "Success",
            reload="connections,media",
        )
    except Exception as e:
        logger.error(f"Failed to delete connection '{connection_name}' (id={connection_id}): {e}")
        await ws_manager.broadcast(f"Failed to delete connection '{connection_name}'!", "Error")


def delete_connection_job(connection_id: int) -> str:
    connection = connection_repo.read(connection_id)  # raises if not found
    task_name = f"Delete Connection '{connection.name}'"
    logger.info(f"Scheduling deletion for connection '{connection.name}' (id={connection_id})")
    scheduler.add_task(
        task_name=task_name,
        func=_delete_connection_job,
        interval=86400.0,
        delay=1,
        run_once=True,
        args=(connection_id, connection.name),
    )
    return f"Connection '{connection.name}' deletion scheduled"
