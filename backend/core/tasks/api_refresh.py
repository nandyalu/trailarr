from core.base.database.manager.connection import ConnectionDatabaseManager
from core.base.database.models.connection import ArrType, ConnectionRead
from core.radarr.connection_manager import RadarrConnectionManager
from core.sonarr.connection_manager import SonarrConnectionManager
from app_logger import logger
from core.tasks.image_refresh import refresh_images
from core.tasks.task_runner import TaskRunner


async def api_refresh():
    logger.info("Refreshing data from APIs")
    # Get all connections from database
    connnections = ConnectionDatabaseManager().read_all()
    if len(connnections) == 0:
        logger.warning("No connections found in the database")
        return
    # Refresh data from API for each connection
    for connection in connnections:
        logger.info(f"Refreshing data from API for connection: {connection.name}")
        # Call the API to get the latest data
        if connection.arr_type == ArrType.SONARR:
            connection_db_manager = SonarrConnectionManager(connection)
        elif connection.arr_type == ArrType.RADARR:
            connection_db_manager = RadarrConnectionManager(connection)
        else:
            logger.warning(
                f"Invalid connection type: {connection.arr_type} for connection: {connection}"
            )
            continue
        await connection_db_manager.refresh()
        logger.info(f"Data refreshed for connection: {connection.name}")
    # Refresh images after API refresh to download/update images for new media
    await refresh_images(recent_only=True)
    logger.info("API Refresh completed!")


async def _api_refresh_by_id(connection: ConnectionRead):
    # Call the API to get the latest data
    if connection.arr_type == ArrType.SONARR:
        connection_db_manager = SonarrConnectionManager(connection)
    elif connection.arr_type == ArrType.RADARR:
        connection_db_manager = RadarrConnectionManager(connection)
    else:
        logger.warning(
            f"Invalid connection type: {connection.arr_type} for connection: {connection}"
        )
        return
    await connection_db_manager.refresh()
    logger.info(f"Data refreshed for connection: {connection.name}")
    # Refresh images after API refresh to download/update images for new media
    await refresh_images(recent_only=True)
    logger.info("API Refresh completed!")


def api_refresh_by_id(connection_id: int):
    logger.info(f"Refreshing data from API for connection ID: {connection_id}")
    # Get connection from database
    try:
        connection = ConnectionDatabaseManager().read(connection_id)
    except Exception as e:
        msg = f"Failed to get connection with ID: {connection_id}"
        logger.error(f"{msg}. Error: {e}")
        return msg
    # Refresh data from API for the connection
    msg = f"Refreshing data from API for connection: {connection.name}"
    logger.info(msg)
    runner = TaskRunner()
    runner.run_task(_api_refresh_by_id, task_args=(connection,), delay=3)
    return msg
